"""
Background session processor using threading.

This module provides a simple background processing mechanism that:
1. Triggers immediately after session is queued
2. Runs in a separate thread to not block the HTTP response
3. Uses database as source of truth for recovery
4. Handles failures gracefully

For PoC deployment. Can be replaced with dedicated worker later.
"""

import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

def trigger_session_processing(app, session_id):
    """
    Trigger background processing for a session.
    
    This spawns a daemon thread that processes the session outside
    the HTTP request lifecycle.
    
    Args:
        app: Flask application instance (for app context)
        session_id: ID of session to process
    """
    thread = threading.Thread(
        target=_process_session_background,
        args=(app, session_id),
        daemon=True
    )
    thread.start()
    logger.info(f"[PROCESSING] Background thread started for session {session_id}")


def _process_session_background(app, session_id):
    """
    Background thread worker that processes a single session.
    
    Runs in separate thread with its own database session.
    """
    # Import here to avoid circular imports
    from app import db
    from models import Session
    from coaching.context import build_coaching_context
    from coaching.engine import load_pathway
    from coaching.prompts import build_extraction_prompt
    from coaching.ai_service import AIService, AIServiceError
    from coaching.validator import ExtractionValidator
    from coaching.persistence import apply_extraction_updates
    
    # Small delay to ensure HTTP response completes
    time.sleep(0.5)
    
    start_time = time.time()
    
    with app.app_context():
        try:
            logger.info(f"[PROCESSING] Session {session_id} processing started")
            
            # Load session
            session = db.session.get(Session, session_id)
            if not session:
                logger.error(f"[PROCESSING] Session {session_id} not found")
                return
            
            # Check if already processed (idempotency)
            if session.processing_status == 'complete':
                logger.info(f"[PROCESSING] Session {session_id} already processed, skipping")
                return
            
            # Mark as processing
            session.processing_status = 'processing'
            db.session.commit()
            logger.info(f"[PROCESSING] Session {session_id} status: pending → processing")
            
            engagement = session.engagement
            
            logger.info(f"[EXTRACTION] Processing session {session_id}, engagement {engagement.id}")
            
            # Build context
            context = build_coaching_context(engagement.id)
            pathway_data = load_pathway(engagement.pathway_id)
            
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in session.messages
            ]
            
            logger.info(f"[EXTRACTION] Session has {len(messages)} messages")
            logger.info(f"[EXTRACTION] Open commitments: {len(context.get('open_commitments', []))}")
            logger.info(f"[EXTRACTION] Current risks: {len(context.get('current_risks', []))}")
            
            # Check if session is too short
            if len(messages) < 2:
                logger.info("[EXTRACTION] Session too short for extraction")
                session.summary = "Brief session - no significant updates"
                session.processing_status = 'complete'
                db.session.commit()
                
                elapsed = time.time() - start_time
                logger.info(f"[PERFORMANCE] Extraction session={session_id}: {elapsed:.1f}s (brief)")
                logger.info(f"[PROCESSING] Session {session_id} processing complete (brief)")
                return
            
            # AI extraction
            ai_service = AIService()
            extraction_prompt = build_extraction_prompt()
            
            logger.info("[EXTRACTION] Calling AI service for extraction")
            extraction_start = time.time()
            
            extraction = ai_service.extract_session_outcomes(
                messages=messages,
                context=context,
                extraction_prompt=extraction_prompt
            )
            
            extraction_elapsed = time.time() - extraction_start
            logger.info(f"[PERFORMANCE] AI extraction session={session_id}: {extraction_elapsed:.1f}s")
            
            logger.info(f"[EXTRACTION] Extraction result keys: {list(extraction.keys())}")
            logger.info(f"[EXTRACTION] Session summary: {extraction.get('session_summary', 'MISSING')[:100]}")
            logger.info(f"[EXTRACTION] New commitments: {len(extraction.get('new_commitments', []))}")
            logger.info(f"[EXTRACTION] Commitment updates: {len(extraction.get('commitment_updates', []))}")
            logger.info(f"[EXTRACTION] New risks: {len(extraction.get('new_risks', []))}")
            logger.info(f"[EXTRACTION] Risk updates: {len(extraction.get('risk_updates', []))}")
            logger.info(f"[EXTRACTION] New observations: {len(extraction.get('new_observations', []))}")
            logger.info(f"[EXTRACTION] Observation updates: {len(extraction.get('observation_updates', []))}")
            logger.info(f"[EXTRACTION] Advisor attention items: {len(extraction.get('advisor_attention_items', []))}")
            logger.info(f"[EXTRACTION] Attention item updates: {len(extraction.get('attention_item_updates', []))}")
            
            # Validation
            validator = ExtractionValidator(engagement.id, pathway_data, context)
            is_valid, errors = validator.validate_extraction(extraction)
            
            if not is_valid:
                logger.error(f"[EXTRACTION] Validation failed: {errors}")
                session.summary = "Session completed - validation errors prevented some updates"
                session.processing_status = 'failed'
                db.session.commit()
                
                elapsed = time.time() - start_time
                logger.info(f"[PERFORMANCE] Total processing session={session_id}: {elapsed:.1f}s (validation failed)")
                logger.error(f"[PROCESSING] Session {session_id} processing failed: validation errors")
                return
            
            logger.info("[EXTRACTION] Validation passed, applying updates")
            reconciliation_start = time.time()
            
            # Apply updates
            changes = apply_extraction_updates(engagement.id, extraction)
            
            reconciliation_elapsed = time.time() - reconciliation_start
            logger.info(f"[PERFORMANCE] Reconciliation session={session_id}: {reconciliation_elapsed:.1f}s")
            
            # Persist session summary
            session_summary = extraction.get('session_summary', 'Session completed')
            session.summary = session_summary
            session.processing_status = 'complete'
            db.session.commit()
            
            logger.info(f"[EXTRACTION] Session extraction complete. Changes: {changes}")
            logger.info(f"[EXTRACTION] Session summary persisted: {session_summary[:100]}")
            logger.info(f"[EXTRACTION] Persistence complete")
            
            elapsed = time.time() - start_time
            logger.info(f"[PERFORMANCE] Total post-session processing session={session_id}: {elapsed:.1f}s")
            logger.info(f"[PROCESSING] Session {session_id} processing complete")
            logger.info(f"[PROCESSING] Session {session_id} status: processing → complete")
            
        except AIServiceError as e:
            logger.error(f"[PROCESSING] AI service error during extraction: {str(e)}")
            try:
                session = db.session.get(Session, session_id)
                if session:
                    session.summary = "Session completed - AI extraction unavailable"
                    session.processing_status = 'failed'
                    db.session.commit()
            except Exception as commit_error:
                logger.error(f"[PROCESSING] Failed to update session status: {str(commit_error)}")
            
            elapsed = time.time() - start_time
            logger.info(f"[PERFORMANCE] Total processing session={session_id}: {elapsed:.1f}s (AI error)")
            logger.error(f"[PROCESSING] Session {session_id} processing failed: AI service error")
            
        except Exception as e:
            logger.error(f"[PROCESSING] Unexpected error during extraction: {str(e)}", exc_info=True)
            try:
                session = db.session.get(Session, session_id)
                if session:
                    session.summary = "Session completed - processing error"
                    session.processing_status = 'failed'
                    db.session.commit()
            except Exception as commit_error:
                logger.error(f"[PROCESSING] Failed to update session status: {str(commit_error)}")
            
            elapsed = time.time() - start_time
            logger.info(f"[PERFORMANCE] Total processing session={session_id}: {elapsed:.1f}s (error)")
            logger.error(f"[PROCESSING] Session {session_id} processing failed: {str(e)}")


def process_pending_sessions_once(app):
    """
    Process all pending sessions once.
    
    This can be called on application startup or manually to recover
    sessions that were left in 'pending' state.
    
    Args:
        app: Flask application instance
    """
    from app import db
    from models import Session
    
    with app.app_context():
        pending_sessions = Session.query.filter_by(
            status='completed',
            processing_status='pending'
        ).order_by(Session.ended_at).all()
        
        if not pending_sessions:
            logger.info("[PROCESSING] No pending sessions found")
            return 0
        
        logger.info(f"[PROCESSING] Found {len(pending_sessions)} pending sessions, triggering processing")
        
        for session in pending_sessions:
            trigger_session_processing(app, session.id)
        
        return len(pending_sessions)

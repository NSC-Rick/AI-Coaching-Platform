"""
Background worker for processing completed coaching sessions.

This worker polls for sessions with processing_status='pending' and
executes the AI extraction/reconciliation pipeline asynchronously.
"""

import os
import sys
import time
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Import Flask app and models
from app import app, db
from models import Session
from coaching.context import build_coaching_context
from coaching.engine import load_pathway
from coaching.prompts import build_extraction_prompt
from coaching.ai_service import AIService, AIServiceError
from coaching.validator import ExtractionValidator
from coaching.persistence import apply_extraction_updates

def process_pending_sessions():
    """
    Find and process sessions with processing_status='pending'.
    """
    with app.app_context():
        # Find sessions that need processing
        pending_sessions = Session.query.filter_by(
            status='completed',
            processing_status='pending'
        ).order_by(Session.ended_at).all()
        
        if not pending_sessions:
            return 0
        
        logger.info(f"[PROCESSING] Found {len(pending_sessions)} pending sessions")
        
        processed_count = 0
        for session in pending_sessions:
            try:
                process_session_extraction(session.id)
                processed_count += 1
            except Exception as e:
                logger.error(f"[PROCESSING] Failed to process session {session.id}: {str(e)}")
                # Continue processing other sessions
        
        return processed_count


def process_session_extraction(session_id):
    """
    Process session extraction and persist updates.
    This is the core post-session processing pipeline.
    """
    start_time = time.time()
    
    session = db.session.get(Session, session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    # Check idempotency - don't reprocess completed sessions
    if session.processing_status == 'complete':
        logger.info(f"[PROCESSING] Session {session_id} already processed, skipping")
        return
    
    # Mark as processing
    session.processing_status = 'processing'
    db.session.commit()
    
    logger.info(f"[PROCESSING] Session {session_id} extraction started")
    
    engagement = session.engagement
    
    logging.info(f"[EXTRACTION] Processing session {session_id}, engagement {engagement.id}")
    
    try:
        context = build_coaching_context(engagement.id)
        pathway_data = load_pathway(engagement.pathway_id)
        
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages
        ]
        
        logging.info(f"[EXTRACTION] Session has {len(messages)} messages")
        logging.info(f"[EXTRACTION] Open commitments: {len(context.get('open_commitments', []))}")
        logging.info(f"[EXTRACTION] Current risks: {len(context.get('current_risks', []))}")
        
        if len(messages) < 2:
            logging.info("[EXTRACTION] Session too short for extraction")
            session.summary = "Brief session - no significant updates"
            session.processing_status = 'complete'
            db.session.commit()
            
            elapsed = time.time() - start_time
            logger.info(f"[PERFORMANCE] Extraction session={session_id}: {elapsed:.1f}s (brief)")
            return
        
        ai_service = AIService()
        extraction_prompt = build_extraction_prompt()
        
        logging.info("[EXTRACTION] Calling AI service for extraction")
        extraction_start = time.time()
        
        extraction = ai_service.extract_session_outcomes(
            messages=messages,
            context=context,
            extraction_prompt=extraction_prompt
        )
        
        extraction_elapsed = time.time() - extraction_start
        logger.info(f"[PERFORMANCE] AI extraction session={session_id}: {extraction_elapsed:.1f}s")
        
        logging.info(f"[EXTRACTION] Extraction result keys: {list(extraction.keys())}")
        logging.info(f"[EXTRACTION] Session summary: {extraction.get('session_summary', 'MISSING')[:100]}")
        logging.info(f"[EXTRACTION] New commitments: {len(extraction.get('new_commitments', []))}")
        logging.info(f"[EXTRACTION] Commitment updates: {len(extraction.get('commitment_updates', []))}")
        logging.info(f"[EXTRACTION] New risks: {len(extraction.get('new_risks', []))}")
        logging.info(f"[EXTRACTION] Risk updates: {len(extraction.get('risk_updates', []))}")
        logging.info(f"[EXTRACTION] New observations: {len(extraction.get('new_observations', []))}")
        logging.info(f"[EXTRACTION] Observation updates: {len(extraction.get('observation_updates', []))}")
        logging.info(f"[EXTRACTION] Advisor attention items: {len(extraction.get('advisor_attention_items', []))}")
        logging.info(f"[EXTRACTION] Attention item updates: {len(extraction.get('attention_item_updates', []))}")
        
        validator = ExtractionValidator(engagement.id, pathway_data, context)
        is_valid, errors = validator.validate_extraction(extraction)
        
        if not is_valid:
            logging.error(f"[EXTRACTION] Validation failed: {errors}")
            session.summary = "Session completed - validation errors prevented some updates"
            session.processing_status = 'failed'
            db.session.commit()
            
            elapsed = time.time() - start_time
            logger.info(f"[PERFORMANCE] Total processing session={session_id}: {elapsed:.1f}s (validation failed)")
            return
        
        logging.info("[EXTRACTION] Validation passed, applying updates")
        reconciliation_start = time.time()
        
        changes = apply_extraction_updates(engagement.id, extraction)
        
        reconciliation_elapsed = time.time() - reconciliation_start
        logger.info(f"[PERFORMANCE] Reconciliation session={session_id}: {reconciliation_elapsed:.1f}s")
        
        session_summary = extraction.get('session_summary', 'Session completed')
        session.summary = session_summary
        session.processing_status = 'complete'
        db.session.commit()
        
        logging.info(f"[EXTRACTION] Session extraction complete. Changes: {changes}")
        logging.info(f"[EXTRACTION] Session summary persisted: {session_summary[:100]}")
        
        elapsed = time.time() - start_time
        logger.info(f"[PERFORMANCE] Total post-session processing session={session_id}: {elapsed:.1f}s")
        logger.info(f"[PROCESSING] Session {session_id} extraction complete")
        
    except AIServiceError as e:
        logging.error(f"AI service error during extraction: {str(e)}")
        session.summary = "Session completed - AI extraction unavailable"
        session.processing_status = 'failed'
        db.session.commit()
        
        elapsed = time.time() - start_time
        logger.info(f"[PERFORMANCE] Total processing session={session_id}: {elapsed:.1f}s (AI error)")
        logger.error(f"[PROCESSING] Session {session_id} extraction failed: AI service error")
        raise
        
    except Exception as e:
        logging.error(f"Unexpected error during extraction: {str(e)}")
        session.summary = "Session completed - processing error"
        session.processing_status = 'failed'
        db.session.commit()
        
        elapsed = time.time() - start_time
        logger.info(f"[PERFORMANCE] Total processing session={session_id}: {elapsed:.1f}s (error)")
        logger.error(f"[PROCESSING] Session {session_id} extraction failed: {str(e)}")
        raise


def run_worker(poll_interval=5):
    """
    Main worker loop.
    
    Args:
        poll_interval: Seconds to wait between polling for pending sessions
    """
    logger.info("[WORKER] Background session processor starting")
    logger.info(f"[WORKER] Poll interval: {poll_interval}s")
    
    while True:
        try:
            processed = process_pending_sessions()
            if processed > 0:
                logger.info(f"[WORKER] Processed {processed} sessions")
            
            time.sleep(poll_interval)
            
        except KeyboardInterrupt:
            logger.info("[WORKER] Shutting down gracefully")
            break
        except Exception as e:
            logger.error(f"[WORKER] Error in worker loop: {str(e)}")
            time.sleep(poll_interval)


if __name__ == '__main__':
    run_worker()

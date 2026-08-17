import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from models import db, User, Advisor, Client, Business, Engagement, PathwayState, Commitment, Risk, SignificantEvent, LearningRecord, CoachingObservation, Session, AdvisorGuidance, AdvisorAttention, SessionMessage
from coaching.ai_service import AIService, AIServiceError
from coaching.context import build_coaching_context, format_context_for_display
from coaching.engine import load_pathway
from coaching.prompts import build_coaching_system_prompt, build_extraction_prompt
from coaching.validator import ExtractionValidator, ValidationError
from coaching.persistence import apply_extraction_updates, PersistenceError
from background_processor import trigger_session_processing

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Normalize DATABASE_URL for SQLAlchemy with psycopg 3
    # Render provides postgres:// or postgresql://, but we need postgresql+psycopg://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/coaching.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def require_role(role):
    def decorator(f):
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role != role:
                flash('Access denied.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'CLIENT':
            return redirect(url_for('client_home'))
        elif current_user.role == 'ADVISOR':
            return redirect(url_for('advisor_home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.is_active():
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/client/home')
@require_role('CLIENT')
def client_home():
    client = current_user.client
    engagement = Engagement.query.filter_by(client_id=client.id, status='active').first()
    
    if not engagement:
        return render_template('client_home.html', client=client, engagement=None)
    
    pathway_state = engagement.pathway_state
    business = client.business
    
    pathway_data = load_pathway(engagement.pathway_id)
    
    open_commitments = Commitment.query.filter_by(
        engagement_id=engagement.id,
        status='open'
    ).order_by(Commitment.due_date).all()
    
    recent_learning = LearningRecord.query.filter_by(
        engagement_id=engagement.id,
        status='recommended'
    ).order_by(LearningRecord.recommended_at.desc()).limit(3).all()
    
    learning_resources = []
    if recent_learning:
        resources_data = pathway_data.get('resources', {}).get('resources', [])
        for lr in recent_learning:
            resource = next((r for r in resources_data if r['resource_id'] == lr.resource_id), None)
            if resource:
                learning_resources.append({
                    'record': lr,
                    'resource': resource
                })
    
    return render_template('client_home.html',
                         client=client,
                         business=business,
                         engagement=engagement,
                         pathway_state=pathway_state,
                         pathway_data=pathway_data,
                         open_commitments=open_commitments,
                         learning_resources=learning_resources)

@app.route('/voice/coaching/<int:engagement_id>')
@require_role('CLIENT')
def voice_coaching(engagement_id):
    """
    Voice coaching page - Build 003.
    Renders the voice interface for ElevenLabs integration.
    """
    engagement = db.session.get(Engagement, engagement_id)
    
    if not engagement or engagement.client_id != current_user.client.id:
        flash('Access denied.', 'error')
        return redirect(url_for('client_home'))
    
    pathway_data = load_pathway(engagement.pathway_id)
    pathway_state = engagement.pathway_state
    
    return render_template('voice_coaching.html',
                         engagement=engagement,
                         pathway_data=pathway_data,
                         pathway_state=pathway_state)

@app.route('/advisor/home')
@require_role('ADVISOR')
def advisor_home():
    advisor = current_user.advisor
    
    engagements = Engagement.query.filter_by(
        advisor_id=advisor.id,
        status='active'
    ).all()
    
    client_data = []
    for engagement in engagements:
        client = engagement.client
        business = client.business
        pathway_state = engagement.pathway_state
        
        pathway_data = load_pathway(engagement.pathway_id)
        
        open_commitments_count = Commitment.query.filter_by(
            engagement_id=engagement.id,
            status='open'
        ).count()
        
        highest_risk = Risk.query.filter_by(
            engagement_id=engagement.id,
            status='open'
        ).order_by(
            db.case(
                (Risk.severity == 'critical', 1),
                (Risk.severity == 'high', 2),
                (Risk.severity == 'moderate', 3),
                (Risk.severity == 'low', 4),
                else_=5
            )
        ).first()
        
        attention_items = AdvisorAttention.query.filter_by(
            engagement_id=engagement.id,
            status='open'
        ).count()
        
        client_data.append({
            'engagement': engagement,
            'client': client,
            'business': business,
            'pathway_state': pathway_state,
            'pathway_name': pathway_data['manifest']['name'],
            'open_commitments_count': open_commitments_count,
            'highest_risk': highest_risk,
            'attention_items': attention_items
        })
    
    return render_template('advisor_home.html',
                         advisor=advisor,
                         client_data=client_data)

@app.route('/advisor/client/<int:engagement_id>')
@require_role('ADVISOR')
def client_detail(engagement_id):
    engagement = db.session.get(Engagement, engagement_id)
    
    if not engagement or engagement.advisor_id != current_user.advisor.id:
        flash('Client not found or access denied.', 'error')
        return redirect(url_for('advisor_home'))
    
    client = engagement.client
    business = client.business
    pathway_state = engagement.pathway_state
    
    pathway_data = load_pathway(engagement.pathway_id)
    
    commitments = Commitment.query.filter_by(
        engagement_id=engagement.id
    ).order_by(Commitment.created_at.desc()).all()
    
    risks = Risk.query.filter_by(
        engagement_id=engagement.id
    ).order_by(Risk.created_at.desc()).all()
    
    significant_events = SignificantEvent.query.filter_by(
        engagement_id=engagement.id
    ).order_by(SignificantEvent.event_date.desc()).all()
    
    learning_records = LearningRecord.query.filter_by(
        engagement_id=engagement.id
    ).order_by(LearningRecord.recommended_at.desc()).all()
    
    # Get active observations first, then historical
    active_observations = CoachingObservation.query.filter_by(
        engagement_id=engagement.id,
        status='active'
    ).order_by(CoachingObservation.created_at.desc()).all()
    
    historical_observations = CoachingObservation.query.filter(
        CoachingObservation.engagement_id == engagement.id,
        CoachingObservation.status.in_(['resolved', 'superseded'])
    ).order_by(CoachingObservation.created_at.desc()).limit(5).all()
    
    coaching_observations = active_observations + historical_observations
    
    advisor_guidance = AdvisorGuidance.query.filter_by(
        engagement_id=engagement.id
    ).order_by(AdvisorGuidance.created_at.desc()).all()
    
    # Get open attention items first, then resolved
    open_attention_items = AdvisorAttention.query.filter_by(
        engagement_id=engagement.id,
        status='open'
    ).order_by(AdvisorAttention.created_at.desc()).all()
    
    resolved_attention_items = AdvisorAttention.query.filter_by(
        engagement_id=engagement.id,
        status='resolved'
    ).order_by(AdvisorAttention.created_at.desc()).limit(5).all()
    
    attention_items = open_attention_items + resolved_attention_items
    
    sessions = Session.query.filter_by(
        engagement_id=engagement.id
    ).order_by(Session.started_at.desc()).limit(5).all()
    
    context = build_coaching_context(engagement_id)
    context_display = format_context_for_display(context)
    
    return render_template('client_detail.html',
                         engagement=engagement,
                         client=client,
                         business=business,
                         pathway_state=pathway_state,
                         pathway_data=pathway_data,
                         commitments=commitments,
                         risks=risks,
                         significant_events=significant_events,
                         learning_records=learning_records,
                         coaching_observations=coaching_observations,
                         advisor_guidance=advisor_guidance,
                         attention_items=attention_items,
                         sessions=sessions,
                         context_display=context_display)

@app.route('/advisor/client/<int:engagement_id>/add_guidance', methods=['POST'])
@require_role('ADVISOR')
def add_guidance(engagement_id):
    engagement = db.session.get(Engagement, engagement_id)
    
    if not engagement or engagement.advisor_id != current_user.advisor.id:
        flash('Client not found or access denied.', 'error')
        return redirect(url_for('advisor_home'))
    
    guidance_text = request.form.get('guidance')
    priority = request.form.get('priority', 'normal')
    
    if guidance_text:
        guidance = AdvisorGuidance(
            engagement_id=engagement_id,
            advisor_id=current_user.advisor.id,
            guidance=guidance_text,
            priority=priority,
            status='active'
        )
        db.session.add(guidance)
        db.session.commit()
        flash('Guidance added successfully.', 'success')
    
    return redirect(url_for('client_detail', engagement_id=engagement_id))

@app.route('/session/start/<int:engagement_id>', methods=['POST'])
@require_role('CLIENT')
def start_session(engagement_id):
    import time
    start_time = time.time()
    
    engagement = db.session.get(Engagement, engagement_id)
    
    if not engagement or engagement.client_id != current_user.client.id:
        flash('Access denied.', 'error')
        return redirect(url_for('client_home'))
    
    try:
        ai_service = AIService()
    except AIServiceError as e:
        flash(f'AI service not available: {str(e)}', 'error')
        return redirect(url_for('client_home'))
    
    session = Session(
        engagement_id=engagement_id,
        started_at=datetime.utcnow(),
        interaction_type='text',
        status='active'
    )
    db.session.add(session)
    db.session.commit()
    
    context = build_coaching_context(engagement_id)
    pathway_data = load_pathway(engagement.pathway_id)
    system_prompt = build_coaching_system_prompt(context, pathway_data)
    
    try:
        ai_start = time.time()
        initial_message = ai_service.generate_coaching_response(
            messages=[],
            system_prompt=system_prompt
        )
        ai_elapsed = time.time() - ai_start
        logging.info(f"[PERFORMANCE] Coaching initial response: {ai_elapsed:.1f}s")
        
        # DIAGNOSTIC CHECKPOINT 3A: Before Persistence
        print(f"[DIAGNOSTIC] Initial Message Type: {type(initial_message)}")
        print(f"[DIAGNOSTIC] Initial Message Length: {len(initial_message) if initial_message else 0}")
        print(f"[DIAGNOSTIC] Initial Message Preview: {repr(initial_message[:100] if initial_message else initial_message)}")
        
        assistant_msg = SessionMessage(
            session_id=session.id,
            role='assistant',
            content=initial_message
        )
        db.session.add(assistant_msg)
        db.session.commit()
        
        # DIAGNOSTIC CHECKPOINT 3B: After Persistence
        persisted_msg = db.session.get(SessionMessage, assistant_msg.id)
        print(f"[DIAGNOSTIC] Persisted Message ID: {persisted_msg.id}")
        print(f"[DIAGNOSTIC] Persisted Role: {persisted_msg.role}")
        print(f"[DIAGNOSTIC] Persisted Content Type: {type(persisted_msg.content)}")
        print(f"[DIAGNOSTIC] Persisted Content Length: {len(persisted_msg.content) if persisted_msg.content else 0}")
        print(f"[DIAGNOSTIC] Persisted Content Preview: {repr(persisted_msg.content[:100] if persisted_msg.content else persisted_msg.content)}")
        
    except AIServiceError as e:
        logging.error(f"Failed to generate initial message: {str(e)}")
        flash('Failed to start coaching session. Please try again.', 'error')
        db.session.delete(session)
        db.session.commit()
        return redirect(url_for('client_home'))
    
    return redirect(url_for('coaching_session', session_id=session.id))

@app.route('/session/<int:session_id>')
@require_role('CLIENT')
def coaching_session(session_id):
    session = db.session.get(Session, session_id)
    
    if not session or session.engagement.client_id != current_user.client.id:
        flash('Session not found or access denied.', 'error')
        return redirect(url_for('client_home'))
    
    if session.status != 'active':
        flash('This session has ended.', 'info')
        return redirect(url_for('client_home'))
    
    engagement = session.engagement
    pathway_state = engagement.pathway_state
    pathway_data = load_pathway(engagement.pathway_id)
    
    messages = SessionMessage.query.filter_by(session_id=session_id).order_by(SessionMessage.created_at).all()
    
    return render_template('coaching_session.html',
                         session=session,
                         engagement=engagement,
                         pathway_state=pathway_state,
                         pathway_data=pathway_data,
                         messages=messages)

@app.route('/session/<int:session_id>/message', methods=['POST'])
@require_role('CLIENT')
def send_message(session_id):
    import time
    start_time = time.time()
    
    session = db.session.get(Session, session_id)
    
    if not session or session.engagement.client_id != current_user.client.id:
        flash('Session not found or access denied.', 'error')
        return redirect(url_for('client_home'))
    
    if session.status != 'active':
        flash('This session has ended.', 'info')
        return redirect(url_for('client_home'))
    
    message_content = request.form.get('message', '').strip()
    
    if not message_content:
        flash('Message cannot be empty.', 'error')
        return redirect(url_for('coaching_session', session_id=session_id))
    
    user_msg = SessionMessage(
        session_id=session_id,
        role='user',
        content=message_content
    )
    db.session.add(user_msg)
    db.session.commit()
    
    try:
        ai_service = AIService()
        
        engagement = session.engagement
        context = build_coaching_context(engagement.id)
        pathway_data = load_pathway(engagement.pathway_id)
        system_prompt = build_coaching_system_prompt(context, pathway_data)
        
        conversation_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages
        ]
        
        ai_start = time.time()
        response = ai_service.generate_coaching_response(
            messages=conversation_messages,
            system_prompt=system_prompt
        )
        ai_elapsed = time.time() - ai_start
        logging.info(f"[PERFORMANCE] Coaching response session={session_id}: {ai_elapsed:.1f}s")
        
        # DIAGNOSTIC CHECKPOINT 3A: Before Persistence
        print(f"[DIAGNOSTIC] Response Type: {type(response)}")
        print(f"[DIAGNOSTIC] Response Length: {len(response) if response else 0}")
        print(f"[DIAGNOSTIC] Response Preview: {repr(response[:100] if response else response)}")
        
        assistant_msg = SessionMessage(
            session_id=session_id,
            role='assistant',
            content=response
        )
        db.session.add(assistant_msg)
        db.session.commit()
        
        # DIAGNOSTIC CHECKPOINT 3B: After Persistence
        persisted_msg = db.session.get(SessionMessage, assistant_msg.id)
        print(f"[DIAGNOSTIC] Persisted Message ID: {persisted_msg.id}")
        print(f"[DIAGNOSTIC] Persisted Role: {persisted_msg.role}")
        print(f"[DIAGNOSTIC] Persisted Content Type: {type(persisted_msg.content)}")
        print(f"[DIAGNOSTIC] Persisted Content Length: {len(persisted_msg.content) if persisted_msg.content else 0}")
        print(f"[DIAGNOSTIC] Persisted Content Preview: {repr(persisted_msg.content[:100] if persisted_msg.content else persisted_msg.content)}")
        
    except AIServiceError as e:
        logging.error(f"Failed to generate response: {str(e)}")
        flash('Failed to get coach response. Please try again.', 'error')
    
    return redirect(url_for('coaching_session', session_id=session_id))

@app.route('/session/<int:session_id>/end', methods=['POST'])
@require_role('CLIENT')
def end_session(session_id):
    import time
    start_time = time.time()
    
    session = db.session.get(Session, session_id)
    
    if not session or session.engagement.client_id != current_user.client.id:
        flash('Session not found or access denied.', 'error')
        return redirect(url_for('client_home'))
    
    if session.status != 'active':
        return redirect(url_for('client_home'))
    
    # Mark session as completed and queue for background processing
    session.ended_at = datetime.utcnow()
    session.status = 'completed'
    session.processing_status = 'pending'
    db.session.commit()
    
    elapsed = time.time() - start_time
    logging.info(f"[PERFORMANCE] Session close session={session_id}: {elapsed:.2f}s")
    logging.info(f"[PROCESSING] Session {session_id} queued for background processing")
    
    # Trigger background processing in separate thread
    trigger_session_processing(app, session_id)
    
    flash('Session completed. Your progress is being processed.', 'success')
    return redirect(url_for('client_home'))

def process_session_extraction(session_id):
    """
    Process session extraction and persist updates.
    This is the core post-session processing pipeline.
    """
    session = db.session.get(Session, session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    engagement = session.engagement
    
    logging.info(f"[EXTRACTION] Processing session {session_id}, engagement {engagement.id}")
    
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
        db.session.commit()
        return
    
    try:
        ai_service = AIService()
        extraction_prompt = build_extraction_prompt()
        
        logging.info("[EXTRACTION] Calling AI service for extraction")
        
        extraction = ai_service.extract_session_outcomes(
            messages=messages,
            context=context,
            extraction_prompt=extraction_prompt
        )
        
        logging.info(f"[EXTRACTION] Extraction result keys: {list(extraction.keys())}")
        logging.info(f"[EXTRACTION] Session summary: {extraction.get('session_summary', 'MISSING')[:100]}")
        logging.info(f"[EXTRACTION] New commitments: {len(extraction.get('new_commitments', []))}")
        logging.info(f"[EXTRACTION] Commitment updates: {len(extraction.get('commitment_updates', []))}")
        logging.info(f"[EXTRACTION] New risks: {len(extraction.get('new_risks', []))}")
        logging.info(f"[EXTRACTION] Risk updates: {len(extraction.get('risk_updates', []))}")
        logging.info(f"[EXTRACTION] New observations: {len(extraction.get('new_observations', []))}")
        logging.info(f"[EXTRACTION] Advisor attention items: {len(extraction.get('advisor_attention_items', []))}")
        
        validator = ExtractionValidator(engagement.id, pathway_data, context)
        is_valid, errors = validator.validate_extraction(extraction)
        
        if not is_valid:
            logging.error(f"[EXTRACTION] Validation failed: {errors}")
            session.summary = "Session completed - validation errors prevented some updates"
            db.session.commit()
            return
        
        logging.info("[EXTRACTION] Validation passed, applying updates")
        
        changes = apply_extraction_updates(engagement.id, extraction)
        
        session_summary = extraction.get('session_summary', 'Session completed')
        session.summary = session_summary
        db.session.commit()
        
        logging.info(f"[EXTRACTION] Session extraction complete. Changes: {changes}")
        logging.info(f"[EXTRACTION] Session summary persisted: {session_summary[:100]}")
        
    except AIServiceError as e:
        logging.error(f"AI service error during extraction: {str(e)}")
        session.summary = "Session completed - AI extraction unavailable"
        db.session.commit()
        raise
    except Exception as e:
        logging.error(f"Unexpected error during extraction: {str(e)}")
        session.summary = "Session completed - processing error"
        db.session.commit()
        raise

@app.route('/debug/session/<int:session_id>')
@login_required
def debug_session(session_id):
    """
    Debug view for session extraction details.
    Shows before/after context and extraction results.
    """
    session = db.session.get(Session, session_id)
    
    if not session:
        flash('Session not found.', 'error')
        return redirect(url_for('index'))
    
    engagement = session.engagement
    
    if current_user.role == 'CLIENT' and engagement.client_id != current_user.client.id:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    if current_user.role == 'ADVISOR' and engagement.advisor_id != current_user.advisor.id:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    context = build_coaching_context(engagement.id)
    pathway_data = load_pathway(engagement.pathway_id)
    
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages
    ]
    
    debug_info = {
        'session_id': session.id,
        'status': session.status,
        'started_at': session.started_at.isoformat() if session.started_at else None,
        'ended_at': session.ended_at.isoformat() if session.ended_at else None,
        'summary': session.summary,
        'message_count': len(messages),
        'context': context,
        'messages': messages
    }
    
    return jsonify(debug_info)

# ============================================================================
# BUILD 003 - VOICE SESSION ROUTES
# ============================================================================

@app.route('/voice/session/init/<int:engagement_id>', methods=['POST'])
@require_role('CLIENT')
def init_voice_session(engagement_id):
    """
    Initialize a voice session and return configuration for ElevenLabs.
    
    This route:
    1. Validates client access
    2. Creates a Session record with interaction_type='voice'
    3. Builds coaching context
    4. Generates ElevenLabs signed URL
    5. Returns configuration for client-side voice initialization
    """
    engagement = db.session.get(Engagement, engagement_id)
    
    if not engagement or engagement.client_id != current_user.client.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        voice_service = get_voice_service()
    except Exception as e:
        logging.error(f"Voice service initialization failed: {str(e)}")
        return jsonify({'error': 'Voice service not available'}), 503
    
    session = Session(
        engagement_id=engagement_id,
        started_at=datetime.utcnow(),
        interaction_type='voice',
        status='active'
    )
    db.session.add(session)
    db.session.commit()
    
    try:
        context = build_coaching_context(engagement_id)
        pathway_data = load_pathway(engagement.pathway_id)
        pathway_state = engagement.pathway_state
        
        signed_url_data = voice_service.generate_signed_url()
        
        session_config = voice_service.build_session_config(
            client_name=engagement.client.user.first_name or engagement.client.user.email.split('@')[0],
            business_name=engagement.business.business_name,
            pathway_name=pathway_data.get('name', 'Recovery & Stabilization'),
            current_stage=pathway_state.current_stage_id if pathway_state else 'RS-01',
            current_day=pathway_state.current_day if pathway_state else 1,
            coaching_context=format_context_for_display(context),
            session_id=str(session.id),
            user_id=str(current_user.id)
        )
        
        response_data = {
            'session_id': session.id,
            'signed_url': signed_url_data['signed_url'],
            'config': session_config
        }
        
        logging.info(f"Voice session {session.id} initialized for engagement {engagement_id}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Failed to initialize voice session: {str(e)}")
        db.session.delete(session)
        db.session.commit()
        return jsonify({'error': 'Failed to initialize voice session'}), 500

@app.route('/voice/session/<int:session_id>/complete', methods=['POST'])
@require_role('CLIENT')
def complete_voice_session(session_id):
    """
    Complete a voice session and process the conversation.
    
    This route:
    1. Receives conversation data from the client
    2. Normalizes it into SessionMessage format
    3. Marks the session as completed
    4. Triggers the existing Build 002 extraction pipeline
    """
    session = db.session.get(Session, session_id)
    
    if not session or session.engagement.client_id != current_user.client.id:
        return jsonify({'error': 'Session not found or access denied'}), 403
    
    if session.status != 'active':
        return jsonify({'error': 'Session is not active'}), 400
    
    if session.interaction_type != 'voice':
        return jsonify({'error': 'Not a voice session'}), 400
    
    try:
        conversation_data = request.get_json()
        
        if not conversation_data:
            return jsonify({'error': 'No conversation data provided'}), 400
        
        voice_service = get_voice_service()
        
        if not voice_service.validate_conversation_data(conversation_data):
            return jsonify({'error': 'Invalid conversation data'}), 400
        
        messages = voice_service.normalize_conversation_to_messages(conversation_data)
        
        for msg_data in messages:
            session_msg = SessionMessage(
                session_id=session_id,
                role=msg_data.get('role', 'user'),
                content=msg_data.get('content', ''),
                created_at=msg_data.get('timestamp') or datetime.utcnow()
            )
            db.session.add(session_msg)
        
        metadata = voice_service.get_conversation_metadata(conversation_data)
        
        session.ended_at = datetime.utcnow()
        session.status = 'completed'
        db.session.commit()
        
        logging.info(f"Voice session {session_id} completed. Messages: {len(messages)}")
        
        try:
            process_session_extraction(session.id)
            
            return jsonify({
                'status': 'success',
                'message': 'Voice session completed and processed',
                'session_id': session.id,
                'metadata': metadata
            }), 200
            
        except Exception as e:
            logging.error(f"Extraction failed for voice session {session_id}: {str(e)}")
            return jsonify({
                'status': 'partial_success',
                'message': 'Session saved but extraction failed',
                'session_id': session.id,
                'error': str(e)
            }), 200
        
    except Exception as e:
        logging.error(f"Failed to complete voice session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to process voice session'}), 500

@app.route('/voice/session/<int:session_id>/cancel', methods=['POST'])
@require_role('CLIENT')
def cancel_voice_session(session_id):
    """
    Cancel an interrupted voice session safely.
    
    This handles cases where the client closes the browser or the
    connection is lost before normal completion.
    """
    session = db.session.get(Session, session_id)
    
    if not session or session.engagement.client_id != current_user.client.id:
        return jsonify({'error': 'Session not found or access denied'}), 403
    
    if session.status != 'active':
        return jsonify({'error': 'Session is not active'}), 400
    
    try:
        session.ended_at = datetime.utcnow()
        session.status = 'cancelled'
        session.summary = 'Session interrupted'
        db.session.commit()
        
        logging.info(f"Voice session {session_id} cancelled")
        
        return jsonify({
            'status': 'success',
            'message': 'Session cancelled'
        }), 200
        
    except Exception as e:
        logging.error(f"Failed to cancel voice session {session_id}: {str(e)}")
        return jsonify({'error': 'Failed to cancel session'}), 500

@app.cli.command('init-db')
def init_db():
    os.makedirs('data', exist_ok=True)
    db.create_all()
    print('Database initialized.')

@app.cli.command('seed-data')
def seed_data():
    from werkzeug.security import generate_password_hash
    from datetime import date
    
    print('Seeding database...')
    
    advisor_user = User(
        email='ronda@example.com',
        role='ADVISOR',
        active=True
    )
    advisor_user.set_password('advisor123')
    db.session.add(advisor_user)
    db.session.flush()
    
    advisor = Advisor(
        user_id=advisor_user.id,
        first_name='Ronda',
        last_name='Advisor'
    )
    db.session.add(advisor)
    db.session.flush()
    
    client_a_user = User(
        email='sarah@example.com',
        role='CLIENT',
        active=True
    )
    client_a_user.set_password('client123')
    db.session.add(client_a_user)
    db.session.flush()
    
    client_a = Client(
        user_id=client_a_user.id,
        first_name='Sarah',
        last_name='Johnson'
    )
    db.session.add(client_a)
    db.session.flush()
    
    business_a = Business(
        client_id=client_a.id,
        business_name="Sarah's Hardware",
        industry='Retail',
        business_description='Local hardware store serving the community for 15 years',
        current_situation_summary='Experiencing cash flow challenges following recent market changes. Working on stabilization plan.'
    )
    db.session.add(business_a)
    
    engagement_a = Engagement(
        client_id=client_a.id,
        advisor_id=advisor.id,
        pathway_id='PATHWAY-001',
        pathway_version='0.1',
        status='active',
        start_date=date.today() - timedelta(days=18),
        target_end_date=date.today() + timedelta(days=72)
    )
    db.session.add(engagement_a)
    db.session.flush()
    
    pathway_state_a = PathwayState(
        engagement_id=engagement_a.id,
        current_stage_id='RS-01',
        current_day=18,
        current_focus='Short-term liquidity and cash visibility',
        current_priority_summary='Maintain 14-day cash visibility, complete lender preparation, continue customer outreach'
    )
    db.session.add(pathway_state_a)
    
    commitment_a1 = Commitment(
        engagement_id=engagement_a.id,
        description='Contact lender to discuss payment modification',
        due_date=date.today() - timedelta(days=2),
        status='open',
        priority='high'
    )
    db.session.add(commitment_a1)
    
    commitment_a2 = Commitment(
        engagement_id=engagement_a.id,
        description='Update 14-day cash tracker',
        due_date=date.today() + timedelta(days=2),
        status='open',
        priority='high'
    )
    db.session.add(commitment_a2)
    
    commitment_a3 = Commitment(
        engagement_id=engagement_a.id,
        description='Contact five inactive customers',
        status='open',
        priority='normal'
    )
    db.session.add(commitment_a3)
    
    risk_a1 = Risk(
        engagement_id=engagement_a.id,
        title='Johnson account lost',
        description='Major customer Johnson account was lost. Estimated revenue impact: $4,000/month',
        severity='high',
        status='open',
        advisor_attention=True
    )
    db.session.add(risk_a1)
    
    risk_a2 = Risk(
        engagement_id=engagement_a.id,
        title='Lender contact delayed',
        description='Client has postponed lender discussion twice',
        severity='moderate',
        status='open',
        advisor_attention=False
    )
    db.session.add(risk_a2)
    
    event_a1 = SignificantEvent(
        engagement_id=engagement_a.id,
        title='Lost Johnson account',
        description='Johnson account decided to switch to online supplier',
        event_date=date.today() - timedelta(days=5),
        estimated_impact='$4,000/month revenue reduction'
    )
    db.session.add(event_a1)
    
    learning_a1 = LearningRecord(
        engagement_id=engagement_a.id,
        resource_id='RS-R001',
        status='completed',
        recommended_at=datetime.utcnow() - timedelta(days=7),
        completed_at=datetime.utcnow() - timedelta(days=6),
        client_reflection='Now I understand why we can be profitable but still have cash problems',
        follow_up_required=False
    )
    db.session.add(learning_a1)
    
    observation_a1 = CoachingObservation(
        engagement_id=engagement_a.id,
        observation='Client is consistently completing operational tasks but avoiding lender outreach',
        importance='high',
        status='active'
    )
    db.session.add(observation_a1)
    
    session_a1 = Session(
        engagement_id=engagement_a.id,
        started_at=datetime.utcnow() - timedelta(days=3),
        ended_at=datetime.utcnow() - timedelta(days=3, hours=-1),
        interaction_type='voice',
        summary='Client reported Johnson account loss and agreed to update cash forecast'
    )
    db.session.add(session_a1)
    
    guidance_a1 = AdvisorGuidance(
        engagement_id=engagement_a.id,
        advisor_id=advisor.id,
        guidance='For the next two weeks, prioritize cash visibility and lender preparation. Do not introduce additional revenue initiatives until those actions are complete.',
        priority='high',
        status='active'
    )
    db.session.add(guidance_a1)
    
    attention_a1 = AdvisorAttention(
        engagement_id=engagement_a.id,
        title='Lender contact repeatedly deferred',
        description='Client has postponed lender discussion for second consecutive week',
        priority='high',
        status='open'
    )
    db.session.add(attention_a1)
    
    client_b_user = User(
        email='michael@example.com',
        role='CLIENT',
        active=True
    )
    client_b_user.set_password('client123')
    db.session.add(client_b_user)
    db.session.flush()
    
    client_b = Client(
        user_id=client_b_user.id,
        first_name='Michael',
        last_name='Chen'
    )
    db.session.add(client_b)
    db.session.flush()
    
    business_b = Business(
        client_id=client_b.id,
        business_name="Chen's Bakery",
        industry='Food Service',
        business_description='Family bakery specializing in artisan breads and pastries',
        current_situation_summary='Recovering from equipment failure. Implementing cost controls and revenue recovery plan.'
    )
    db.session.add(business_b)
    
    engagement_b = Engagement(
        client_id=client_b.id,
        advisor_id=advisor.id,
        pathway_id='PATHWAY-001',
        pathway_version='0.1',
        status='active',
        start_date=date.today() - timedelta(days=42),
        target_end_date=date.today() + timedelta(days=48)
    )
    db.session.add(engagement_b)
    db.session.flush()
    
    pathway_state_b = PathwayState(
        engagement_id=engagement_b.id,
        current_stage_id='RS-02',
        current_day=42,
        current_focus='Revenue activation from proven customers',
        current_priority_summary='Complete customer outreach cycle, review vendor opportunities'
    )
    db.session.add(pathway_state_b)
    
    commitment_b1 = Commitment(
        engagement_id=engagement_b.id,
        description='Complete outreach to top 10 wholesale customers',
        due_date=date.today() + timedelta(days=5),
        status='open',
        priority='high'
    )
    db.session.add(commitment_b1)
    
    risk_b1 = Risk(
        engagement_id=engagement_b.id,
        title='Equipment replacement costs',
        description='Oven repair costs higher than expected',
        severity='moderate',
        status='open',
        advisor_attention=False
    )
    db.session.add(risk_b1)
    
    db.session.commit()
    
    print('Database seeded successfully!')
    print('\nTest User Credentials:')
    print('=' * 50)
    print('Advisor:')
    print('  Email: ronda@example.com')
    print('  Password: advisor123')
    print('\nClient A (Sarah):')
    print('  Email: sarah@example.com')
    print('  Password: client123')
    print('\nClient B (Michael):')
    print('  Email: michael@example.com')
    print('  Password: client123')
    print('=' * 50)

# Process any pending sessions on startup (recovery mechanism)
# Flask 3.x compatible: Call directly after app initialization
def process_pending_sessions_on_startup():
    """Process any sessions left in pending state from previous runs."""
    from background_processor import process_pending_sessions_once
    try:
        with app.app_context():
            count = process_pending_sessions_once(app)
            if count > 0:
                logging.info(f"[STARTUP] Triggered processing for {count} pending sessions")
    except Exception as e:
        logging.error(f"[STARTUP] Error processing pending sessions: {str(e)}")

# Call startup recovery when running under Gunicorn or other WSGI servers
# This executes during module import, which happens once per worker
if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
    # Not in Flask development reloader child process
    try:
        process_pending_sessions_on_startup()
    except Exception as e:
        logging.error(f"[STARTUP] Failed to process pending sessions: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)

from datetime import datetime
from models import Engagement, PathwayState, Commitment, Risk, SignificantEvent, LearningRecord, CoachingObservation, Session, AdvisorGuidance
from .engine import load_pathway, get_stage_by_id

def build_coaching_context(engagement_id):
    from models import db
    
    engagement = db.session.get(Engagement, engagement_id)
    if not engagement:
        raise ValueError(f"Engagement {engagement_id} not found")
    
    client = engagement.client
    business = client.business
    pathway_state = engagement.pathway_state
    
    pathway_data = load_pathway(engagement.pathway_id)
    
    current_stage = None
    if pathway_state:
        current_stage = get_stage_by_id(pathway_data, pathway_state.current_stage_id)
    
    open_commitments = Commitment.query.filter_by(
        engagement_id=engagement_id,
        status='open'
    ).order_by(Commitment.due_date).all()
    
    current_risks = Risk.query.filter_by(
        engagement_id=engagement_id,
        status='open'
    ).order_by(Risk.severity.desc()).all()
    
    recent_events = SignificantEvent.query.filter_by(
        engagement_id=engagement_id
    ).order_by(SignificantEvent.event_date.desc()).limit(5).all()
    
    recent_learning = LearningRecord.query.filter_by(
        engagement_id=engagement_id
    ).order_by(LearningRecord.recommended_at.desc()).limit(3).all()
    
    coaching_observations = CoachingObservation.query.filter_by(
        engagement_id=engagement_id,
        status='active'
    ).order_by(CoachingObservation.created_at.desc()).limit(5).all()
    
    active_guidance = AdvisorGuidance.query.filter_by(
        engagement_id=engagement_id,
        status='active'
    ).order_by(AdvisorGuidance.created_at.desc()).first()
    
    recent_session = Session.query.filter_by(
        engagement_id=engagement_id
    ).order_by(Session.started_at.desc()).first()
    
    context = {
        'client': {
            'name': f"{client.first_name} {client.last_name}",
            'first_name': client.first_name
        },
        'business': {
            'name': business.business_name if business else None,
            'industry': business.industry if business else None,
            'description': business.business_description if business else None,
            'current_situation': business.current_situation_summary if business else None
        },
        'pathway': {
            'id': engagement.pathway_id,
            'name': pathway_data['manifest']['name'],
            'version': engagement.pathway_version
        },
        'current_state': {
            'stage_id': pathway_state.current_stage_id if pathway_state else None,
            'stage_name': current_stage.get('name') if current_stage else None,
            'current_day': pathway_state.current_day if pathway_state else None,
            'current_focus': pathway_state.current_focus if pathway_state else None,
            'current_priorities': pathway_state.current_priority_summary if pathway_state else None
        },
        'open_commitments': [
            {
                'id': c.id,
                'description': c.description,
                'due_date': c.due_date.isoformat() if c.due_date else None,
                'priority': c.priority
            } for c in open_commitments
        ],
        'current_risks': [
            {
                'id': r.id,
                'title': r.title,
                'description': r.description,
                'severity': r.severity,
                'advisor_attention': r.advisor_attention
            } for r in current_risks
        ],
        'recent_events': [
            {
                'id': e.id,
                'title': e.title,
                'description': e.description,
                'event_date': e.event_date.isoformat(),
                'estimated_impact': e.estimated_impact
            } for e in recent_events
        ],
        'recent_learning': [
            {
                'id': l.id,
                'resource_id': l.resource_id,
                'status': l.status,
                'recommended_at': l.recommended_at.isoformat(),
                'completed_at': l.completed_at.isoformat() if l.completed_at else None,
                'client_reflection': l.client_reflection
            } for l in recent_learning
        ],
        'coaching_observations': [
            {
                'id': o.id,
                'observation': o.observation,
                'importance': o.importance
            } for o in coaching_observations
        ],
        'advisor_guidance': {
            'guidance': active_guidance.guidance,
            'priority': active_guidance.priority,
            'created_at': active_guidance.created_at.isoformat()
        } if active_guidance else None,
        'recent_session': {
            'started_at': recent_session.started_at.isoformat(),
            'summary': recent_session.summary
        } if recent_session else None
    }
    
    return context

def format_context_for_display(context):
    lines = []
    
    lines.append("=" * 60)
    lines.append("COACHING CONTEXT")
    lines.append("=" * 60)
    lines.append("")
    
    lines.append(f"CLIENT: {context['client']['name']}")
    if context['business']['name']:
        lines.append(f"BUSINESS: {context['business']['name']}")
    lines.append("")
    
    lines.append(f"PATHWAY: {context['pathway']['name']}")
    lines.append(f"VERSION: {context['pathway']['version']}")
    lines.append("")
    
    if context['current_state']['stage_name']:
        lines.append(f"CURRENT STAGE: {context['current_state']['stage_name']}")
        if context['current_state']['current_day']:
            lines.append(f"DAY: {context['current_state']['current_day']}")
    lines.append("")
    
    if context['current_state']['current_focus']:
        lines.append(f"CURRENT FOCUS: {context['current_state']['current_focus']}")
        lines.append("")
    
    if context['current_state']['current_priorities']:
        lines.append(f"CURRENT PRIORITIES: {context['current_state']['current_priorities']}")
        lines.append("")
    
    if context['open_commitments']:
        lines.append("OPEN COMMITMENTS:")
        for c in context['open_commitments']:
            due = f" (due: {c['due_date']})" if c['due_date'] else ""
            lines.append(f"  - {c['description']}{due}")
        lines.append("")
    
    if context['current_risks']:
        lines.append("CURRENT RISKS:")
        for r in context['current_risks']:
            lines.append(f"  - [{r['severity'].upper()}] {r['title']}")
        lines.append("")
    
    if context['recent_events']:
        lines.append("RECENT SIGNIFICANT EVENTS:")
        for e in context['recent_events']:
            lines.append(f"  - {e['title']} ({e['event_date']})")
        lines.append("")
    
    if context['recent_learning']:
        lines.append("RECENT LEARNING:")
        for l in context['recent_learning']:
            status_text = f" - {l['status']}"
            lines.append(f"  - {l['resource_id']}{status_text}")
        lines.append("")
    
    if context['coaching_observations']:
        lines.append("COACHING OBSERVATIONS:")
        for o in context['coaching_observations']:
            lines.append(f"  - {o['observation']}")
        lines.append("")
    
    if context['advisor_guidance']:
        lines.append("ADVISOR GUIDANCE:")
        lines.append(f"  {context['advisor_guidance']['guidance']}")
        lines.append("")
    
    if context['recent_session']:
        lines.append("RECENT SESSION:")
        if context['recent_session']['summary']:
            lines.append(f"  {context['recent_session']['summary']}")
        lines.append("")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)

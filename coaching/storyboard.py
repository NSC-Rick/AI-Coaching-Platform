"""
Client Storyboard generation for the AI Coaching Platform.

This module provides a read-only, advisor-facing narrative summary of a client's
coaching journey. It consumes persisted coaching records and does not participate
in coaching or modify any client state.
"""

import json
from datetime import datetime

from .ai_service import AIService, AIServiceError
from .context import build_coaching_context
from .engine import load_pathway, get_stage_by_id
from models import (
    db,
    Engagement,
    Commitment,
    Risk,
    SignificantEvent,
    LearningRecord,
    CoachingObservation,
    Session,
    AdvisorGuidance,
    AdvisorAttention
)


def build_storyboard_context(engagement_id):
    """
    Build a read-only Storyboard context for the given engagement.

    Reuses build_coaching_context for the current coaching snapshot and extends
    it with longitudinal structured records needed for a client journey summary.
    """
    engagement = db.session.get(Engagement, engagement_id)
    if not engagement:
        raise ValueError(f"Engagement {engagement_id} not found")

    client = engagement.client
    business = client.business
    pathway_state = engagement.pathway_state
    pathway_data = load_pathway(engagement.pathway_id)
    current_stage = get_stage_by_id(pathway_data, pathway_state.current_stage_id) if pathway_state else None

    # Current coaching snapshot already has the key current-state fields.
    base_context = build_coaching_context(engagement_id)

    # Longitudinal structured records.
    all_commitments = Commitment.query.filter_by(
        engagement_id=engagement_id
    ).order_by(Commitment.created_at.desc()).all()

    all_risks = Risk.query.filter_by(
        engagement_id=engagement_id
    ).order_by(Risk.created_at.desc()).all()

    all_events = SignificantEvent.query.filter_by(
        engagement_id=engagement_id
    ).order_by(SignificantEvent.event_date.desc()).all()

    all_learning = LearningRecord.query.filter_by(
        engagement_id=engagement_id
    ).order_by(LearningRecord.recommended_at.desc()).all()

    all_observations = CoachingObservation.query.filter_by(
        engagement_id=engagement_id
    ).order_by(CoachingObservation.created_at.desc()).all()

    all_guidance = AdvisorGuidance.query.filter_by(
        engagement_id=engagement_id
    ).order_by(AdvisorGuidance.created_at.desc()).all()

    all_attention = AdvisorAttention.query.filter_by(
        engagement_id=engagement_id
    ).order_by(AdvisorAttention.created_at.desc()).all()

    all_sessions = Session.query.filter_by(
        engagement_id=engagement_id
    ).order_by(Session.started_at.desc()).all()

    storyboard_context = {
        'client': base_context['client'],
        'business': base_context['business'],
        'pathway': base_context['pathway'],
        'engagement': {
            'id': engagement.id,
            'start_date': engagement.start_date.isoformat() if engagement.start_date else None,
            'target_end_date': engagement.target_end_date.isoformat() if engagement.target_end_date else None,
            'status': engagement.status
        },
        'current_state': {
            'stage_id': pathway_state.current_stage_id if pathway_state else None,
            'stage_name': current_stage.get('name') if current_stage else None,
            'current_day': pathway_state.current_day if pathway_state else None,
            'current_focus': pathway_state.current_focus if pathway_state else None,
            'current_priorities': pathway_state.current_priority_summary if pathway_state else None
        },
        'starting_situation': business.current_situation_summary if business else None,
        'commitments': [
            {
                'id': c.id,
                'description': c.description,
                'status': c.status,
                'priority': c.priority,
                'due_date': c.due_date.isoformat() if c.due_date else None,
                'completed_at': c.completed_at.isoformat() if c.completed_at else None,
                'created_at': c.created_at.isoformat() if c.created_at else None
            } for c in all_commitments
        ],
        'risks': [
            {
                'id': r.id,
                'title': r.title,
                'description': r.description,
                'status': r.status,
                'severity': r.severity,
                'advisor_attention': r.advisor_attention,
                'created_at': r.created_at.isoformat() if r.created_at else None
            } for r in all_risks
        ],
        'significant_events': [
            {
                'id': e.id,
                'title': e.title,
                'description': e.description,
                'event_date': e.event_date.isoformat() if e.event_date else None,
                'estimated_impact': e.estimated_impact,
                'created_at': e.created_at.isoformat() if e.created_at else None
            } for e in all_events
        ],
        'learning_records': [
            {
                'id': l.id,
                'resource_id': l.resource_id,
                'status': l.status,
                'recommended_at': l.recommended_at.isoformat() if l.recommended_at else None,
                'completed_at': l.completed_at.isoformat() if l.completed_at else None,
                'client_reflection': l.client_reflection
            } for l in all_learning
        ],
        'coaching_observations': [
            {
                'id': o.id,
                'observation': o.observation,
                'importance': o.importance,
                'status': o.status,
                'created_at': o.created_at.isoformat() if o.created_at else None
            } for o in all_observations
        ],
        'advisor_guidance': [
            {
                'id': g.id,
                'guidance': g.guidance,
                'priority': g.priority,
                'status': g.status,
                'created_at': g.created_at.isoformat() if g.created_at else None
            } for g in all_guidance
        ],
        'advisor_attention': [
            {
                'id': a.id,
                'title': a.title,
                'description': a.description,
                'priority': a.priority,
                'status': a.status,
                'created_at': a.created_at.isoformat() if a.created_at else None
            } for a in all_attention
        ],
        'sessions': [
            {
                'id': s.id,
                'started_at': s.started_at.isoformat() if s.started_at else None,
                'ended_at': s.ended_at.isoformat() if s.ended_at else None,
                'interaction_type': s.interaction_type,
                'status': s.status,
                'summary': s.summary,
                'processing_status': s.processing_status
            } for s in all_sessions
        ]
    }

    return storyboard_context


def build_storyboard_prompt() -> str:
    """
    Build the Storyboard generation system prompt.

    The prompt enforces the six required sections and strict grounding rules.
    """
    return """You are a senior coaching advisor writing a concise, professional client storyboard.

Your storyboard summarizes the client's documented coaching journey using ONLY the information provided in the Storyboard Context below.

## Required Output Sections

Provide the storyboard under the following Markdown headings in this exact order:

### 1. Starting Situation
Briefly describe the client's documented starting position and business context. If no starting situation is recorded, state that it is not available.

### 2. Key Developments
Identify meaningful events, discoveries, changes, or developments recorded during the coaching journey. Use only documented significant events, coaching observations, and session summaries.

### 3. Actions & Commitments
Summarize significant client actions and commitments. Clearly distinguish:
- COMPLETED: status is "completed" or a completed_at date is present
- ACTIVE: status is "open" and not yet completed
- PENDING: has a due_date in the future or no due date
Do not represent planned or pending activity as completed.

### 4. Advisor Interventions
Summarize meaningful documented advisor guidance or interventions. If no advisor guidance exists, state that no advisor interventions are recorded. Do not manufacture advisor involvement.

### 5. Pathway Progress
Summarize documented movement through the assigned Pathway and milestones. Use explicit persisted Pathway state (current stage, day, current focus, priorities). Do not infer milestone completion from conversational language.

### 6. Current Position & Next Focus
Summarize the client's latest known position, current Pathway stage and focus, documented priorities, and any existing next meaningful action. Do not invent a new coaching recommendation.

## Grounding Rules

- Use ONLY information contained in the supplied Storyboard Context.
- Do not invent facts, dates, amounts, or outcomes.
- Do not infer completed actions without supporting evidence.
- Do not convert intentions, plans, or open commitments into completed actions.
- Do not invent advisor interventions.
- Do not infer Pathway progression when explicit progression state exists.
- Prefer omission over speculation.
- Distinguish known facts from pending actions.
- Keep the report concise, professional, and advisor-oriented.
- The Storyboard is a summary of the coaching record, not a new coaching interaction.

When a section has no recorded information, state that the information is not available rather than filling the gap."""


def generate_storyboard(context: dict, ai_service=None, max_completion_tokens: int = 2500) -> str:
    """
    Generate the Storyboard narrative from the structured context.

    Args:
        context: The Storyboard context from build_storyboard_context()
        ai_service: Optional AIService instance for test injection
        max_completion_tokens: Maximum response length

    Returns:
        str: The generated Storyboard narrative

    Raises:
        AIServiceError: If the AI service call fails
    """
    if ai_service is None:
        ai_service = AIService()

    system_prompt = build_storyboard_prompt()
    user_content = json.dumps(context, indent=2, default=str)
    messages = [{"role": "user", "content": user_content}]

    return ai_service.generate_coaching_response(
        messages=messages,
        system_prompt=system_prompt,
        max_completion_tokens=max_completion_tokens
    )

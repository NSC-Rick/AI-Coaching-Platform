"""
Client Storyboard generation for the AI Coaching Platform.

This module provides a read-only, advisor-facing narrative summary of a client's
coaching journey. It consumes persisted coaching records and does not participate
in coaching or modify any client state.
"""

import json
import logging
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

logger = logging.getLogger(__name__)


def _remove_empty_values(value):
    """
    Recursively remove fields whose values are None, empty strings,
    empty lists, or empty dictionaries. Legitimate values like 0 and False
    are preserved.
    """
    if isinstance(value, dict):
        cleaned = {
            k: _remove_empty_values(v)
            for k, v in value.items()
            if v is not None and v != '' and v != [] and v != {}
        }
        return {k: v for k, v in cleaned.items() if v is not None and v != '' and v != [] and v != {}}
    elif isinstance(value, list):
        return [
            _remove_empty_values(item)
            for item in value
            if item is not None and item != '' and item != [] and item != {}
        ]
    return value


def build_storyboard_context(engagement_id):
    """
    Build a read-only, bounded Storyboard context for the given engagement.

    Reuses build_coaching_context for the current coaching snapshot and extends
    it with a constrained set of longitudinal structured records. This keeps the
    Storyboard prompt payload from growing without bound as client history
    accumulates, while preserving significant historical evidence.
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

    # Longitudinal structured records with conservative bounds.
    # Current state is complete. Significant history is preserved.
    # Routine historical detail is progressively constrained.

    open_commitments = Commitment.query.filter_by(
        engagement_id=engagement_id,
        status='open'
    ).order_by(Commitment.due_date, Commitment.created_at.desc()).all()

    completed_commitments = Commitment.query.filter_by(
        engagement_id=engagement_id,
        status='completed'
    ).order_by(Commitment.completed_at.desc()).limit(10).all()

    open_risks = Risk.query.filter_by(
        engagement_id=engagement_id,
        status='open'
    ).order_by(Risk.severity, Risk.created_at.desc()).all()

    closed_risks = Risk.query.filter(
        Risk.engagement_id == engagement_id,
        Risk.status.in_(['resolved', 'mitigated'])
    ).order_by(Risk.updated_at.desc()).limit(10).all()

    all_events = SignificantEvent.query.filter_by(
        engagement_id=engagement_id
    ).order_by(SignificantEvent.event_date.desc()).all()

    all_learning = LearningRecord.query.filter(
        LearningRecord.engagement_id == engagement_id,
        LearningRecord.status.in_(['completed', 'recommended', 'in_progress'])
    ).order_by(LearningRecord.recommended_at.desc()).limit(10).all()

    active_observations = CoachingObservation.query.filter_by(
        engagement_id=engagement_id,
        status='active'
    ).order_by(CoachingObservation.created_at.desc()).all()

    historical_observations = CoachingObservation.query.filter(
        CoachingObservation.engagement_id == engagement_id,
        CoachingObservation.status.in_(['resolved', 'superseded'])
    ).order_by(CoachingObservation.created_at.desc()).limit(5).all()

    recent_guidance = AdvisorGuidance.query.filter_by(
        engagement_id=engagement_id
    ).order_by(AdvisorGuidance.created_at.desc()).limit(10).all()

    open_attention = AdvisorAttention.query.filter_by(
        engagement_id=engagement_id,
        status='open'
    ).order_by(AdvisorAttention.created_at.desc()).all()

    resolved_attention = AdvisorAttention.query.filter(
        AdvisorAttention.engagement_id == engagement_id,
        AdvisorAttention.status == 'resolved'
    ).order_by(AdvisorAttention.created_at.desc()).limit(5).all()

    recent_sessions = Session.query.filter_by(
        engagement_id=engagement_id
    ).order_by(Session.started_at.desc()).limit(10).all()

    storyboard_context = {
        'engagement_id': engagement.id,
        'client': base_context['client'],
        'business': base_context['business'],
        'pathway': base_context['pathway'],
        'engagement': {
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
                'description': c.description,
                'status': c.status,
                'priority': c.priority,
                'due_date': c.due_date.isoformat() if c.due_date else None,
                'completed_at': c.completed_at.isoformat() if c.completed_at else None,
                'created_at': c.created_at.isoformat() if c.created_at else None
            } for c in (open_commitments + completed_commitments)
        ],
        'risks': [
            {
                'title': r.title,
                'description': r.description,
                'status': r.status,
                'severity': r.severity,
                'advisor_attention': r.advisor_attention,
                'created_at': r.created_at.isoformat() if r.created_at else None
            } for r in (open_risks + closed_risks)
        ],
        'significant_events': [
            {
                'title': e.title,
                'description': e.description,
                'event_date': e.event_date.isoformat() if e.event_date else None,
                'estimated_impact': e.estimated_impact,
                'created_at': e.created_at.isoformat() if e.created_at else None
            } for e in all_events
        ],
        'learning_records': [
            {
                'resource_id': l.resource_id,
                'status': l.status,
                'recommended_at': l.recommended_at.isoformat() if l.recommended_at else None,
                'completed_at': l.completed_at.isoformat() if l.completed_at else None,
                'client_reflection': l.client_reflection
            } for l in all_learning
        ],
        'coaching_observations': [
            {
                'observation': o.observation,
                'importance': o.importance,
                'status': o.status,
                'created_at': o.created_at.isoformat() if o.created_at else None
            } for o in (active_observations + historical_observations)
        ],
        'advisor_guidance': [
            {
                'guidance': g.guidance,
                'priority': g.priority,
                'status': g.status,
                'created_at': g.created_at.isoformat() if g.created_at else None
            } for g in recent_guidance
        ],
        'advisor_attention': [
            {
                'title': a.title,
                'description': a.description,
                'priority': a.priority,
                'status': a.status,
                'created_at': a.created_at.isoformat() if a.created_at else None
            } for a in (open_attention + resolved_attention)
        ],
        'sessions': [
            {
                'started_at': s.started_at.isoformat() if s.started_at else None,
                'interaction_type': s.interaction_type,
                'summary': s.summary
            } for s in recent_sessions
        ]
    }

    # Drop fields that carry no grounding value to keep the prompt compact.
    storyboard_context = _remove_empty_values(storyboard_context)

    return storyboard_context


def build_storyboard_prompt() -> str:
    """
    Build the Storyboard V1.1 generation system prompt.

    The prompt produces an advisor-friendly longitudinal client narrative
    grounded in the supplied Storyboard Context.
    """
    return """You are a senior coaching advisor writing a concise, professional client Storyboard for another advisor.

Your audience is a professional advisor. Write a clear longitudinal case narrative, not a coaching session or an inventory of database records.

Use ONLY the information provided in the Storyboard Context. Do not invent facts, dates, amounts, outcomes, advisor actions, or milestone completion. When the record is silent, state that the information is not available rather than filling the gap.

## Required Output Sections

Provide the storyboard under the following Markdown headings in this exact order:

### 1. Starting Situation
Briefly describe the client's documented starting position and business context. Mention the business and the initial challenge if recorded.

### 2. Key Developments
Describe meaningful events, discoveries, changes, or developments in a short narrative. Draw from significant events, coaching observations, and session summaries. Present them in roughly chronological order.

### 3. Actions & Commitments
Group significant client actions and commitments using these sub-headings:

#### Completed
Actions with reliable evidence of completion (status "completed" or a completed_at date is present).

#### In Progress / Open
Actions that remain active (status "open" and not yet completed).

#### Planned / Pending
Actions recorded but not yet underway (due_date in the future or no due_date).

If no items exist in a category, write a concise natural-language sentence such as "No completed commitments are recorded yet." Do not list "None" or use database-style output.

When the same basic action appears more than once (e.g., "Contacted five inactive customers" and "Contacted five inactive customers (duplicate/earlier entry)"), consolidate it into a single, cleanly described action for presentation. Preserve both only if they clearly represent different actions or different time periods. Do not modify the underlying record; this is presentation only.

Do not represent planned or pending activity as completed.

### 4. Advisor & Coaching Support

#### Advisor Guidance
Summarize only persisted advisor-originated guidance. If none exists, state: "No separate advisor guidance is recorded for this period." Do not manufacture advisor involvement.

#### AI Coaching Support
Summarize relevant AI coach support: questions used to clarify, reinforcement of advisor guidance, scripts or planning assistance, resource recommendations, follow-up on commitments, and validation of progress. Do not describe the AI coach as a human advisor and do not describe AI activity as advisor intervention.

### 5. Pathway Progress
Summarize documented Pathway position in advisor-friendly language. Use the current stage name and day, not raw identifiers such as stage_id or PATHWAY-001. For example: "Michael is currently in Revenue Activation & Structural Tightening (Day 42), focused on generating revenue from proven customers." Do not infer milestone completion unless explicit completion data exists. If no explicit milestones are completed, say so naturally.

### 6. Current Position & Next Focus

#### Current Position
What is known to be true now.

#### Remaining Exposure / Open Work
Important unresolved risks, open commitments, or issues.

#### Next Focus
The current documented Pathway/coaching focus.

Do not generate new coaching recommendations. Do not turn this into another coaching interaction.

## Temporal Consistency

Newer explicit evidence should take precedence over older narrative state when the two clearly refer to the same action or condition. For example, if an older advisor attention item lists "lender preparation" as outstanding but newer evidence confirms the lender was contacted and payment timing changed, do not present the older task as an outstanding next step without acknowledging the newer evidence.

If the record contains a genuine unresolved contradiction that cannot safely be reconciled, state the discrepancy clearly instead of choosing a side. Example: "The lender modification is documented as completed, although an older advisor-attention item still lists lender preparation as outstanding."

Do not modify persisted Pathway state, commitments, risks, attention items, or progression.

## Presentation Rules

- Write for a professional advisor, not a database administrator.
- Do not display database IDs, raw ISO timestamps, `null`, `completed_at`, raw status values (e.g., `status = open`), internal field names, `stage_id`, or internal Pathway IDs such as `PATHWAY-001`.
- Internal identifiers may remain in the Storyboard Context for grounding, but they must not appear in the advisor-facing output.
- Use readable, professional dates such as "Aug. 23, 2026" or "mid-August 2026" when exact dates are recorded.
- Prefer concise bullet points and brief paragraphs. Keep the report easy to scan.
- Preserve accuracy above storytelling. Prefer omission over speculation.
- Distinguish known facts from pending actions.
- The Storyboard is a summary of the coaching record, not a new coaching interaction.

When a section has no recorded information, state that the information is not available in concise natural language rather than inventing content."""


def _log_context_diagnostics(engagement_id, context, serialized_context):
    """Log lightweight Storyboard context metrics before AI generation."""
    if not logger.isEnabledFor(logging.INFO):
        return

    logger.info("[STORYBOARD] Engagement ID: %s", engagement_id)
    logger.info("[STORYBOARD] Context character count (pre-serialization): %d", len(json.dumps(context, default=str)))
    logger.info("[STORYBOARD] Serialized context character count: %d", len(serialized_context))
    logger.info("[STORYBOARD] Commitment count: %d", len(context.get('commitments', [])))
    logger.info("[STORYBOARD] Risk count: %d", len(context.get('risks', [])))
    logger.info("[STORYBOARD] Significant event count: %d", len(context.get('significant_events', [])))
    logger.info("[STORYBOARD] Observation count: %d", len(context.get('coaching_observations', [])))
    logger.info("[STORYBOARD] Advisor guidance count: %d", len(context.get('advisor_guidance', [])))
    logger.info("[STORYBOARD] Advisor attention count: %d", len(context.get('advisor_attention', [])))
    logger.info("[STORYBOARD] Session summary count: %d", len(context.get('sessions', [])))
    logger.info("[STORYBOARD] Learning record count: %d", len(context.get('learning_records', [])))


def generate_storyboard(context: dict, ai_service=None, max_completion_tokens: int = 2500, engagement_id=None) -> str:
    """
    Generate the Storyboard narrative from the structured context.

    Args:
        context: The Storyboard context from build_storyboard_context()
        ai_service: Optional AIService instance for test injection
        max_completion_tokens: Maximum response length (kept at 2500)
        engagement_id: Optional engagement ID for diagnostics

    Returns:
        str: The generated Storyboard narrative

    Raises:
        AIServiceError: If the AI service call fails
    """
    if ai_service is None:
        ai_service = AIService()

    system_prompt = build_storyboard_prompt()

    # Use the engagement_id embedded in the context unless overridden.
    effective_engagement_id = context.get('engagement_id', engagement_id)

    # Do not pass the internal engagement_id to the model prompt.
    prompt_context = {k: v for k, v in context.items() if k != 'engagement_id'}
    user_content = json.dumps(
        prompt_context,
        separators=(',', ':'),
        default=str
    )

    _log_context_diagnostics(effective_engagement_id, context, user_content)

    messages = [{"role": "user", "content": user_content}]

    return ai_service.generate_coaching_response(
        messages=messages,
        system_prompt=system_prompt,
        max_completion_tokens=max_completion_tokens
    )

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

- Write for a professional advisor, not for a database administrator.
- Do not display database IDs, raw ISO timestamps, `null`, `completed_at`, raw status values (e.g., `status = open`), internal field names, `stage_id`, or internal Pathway IDs such as `PATHWAY-001`.
- Internal identifiers may remain in the Storyboard Context for grounding, but they must not appear in the advisor-facing output.
- Use readable, professional dates such as "Aug. 23, 2026" or "mid-August 2026" when exact dates are recorded.
- Prefer concise bullet points and brief paragraphs. Keep the report easy to scan.
- Preserve accuracy above storytelling. Prefer omission over speculation.
- Distinguish known facts from pending actions.
- The Storyboard is a summary of the coaching record, not a new coaching interaction.

When a section has no recorded information, state that the information is not available in concise natural language rather than inventing content."""


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

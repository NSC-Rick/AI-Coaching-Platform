"""
Persistence layer for applying validated AI-extracted updates to the Coaching Record.
"""

from datetime import datetime, date
from typing import Dict, List, Any
import logging
from models import db, Commitment, Risk, SignificantEvent, LearningRecord, CoachingObservation, AdvisorAttention

logger = logging.getLogger(__name__)

class PersistenceError(Exception):
    """Raised when persistence fails."""
    pass

def apply_extraction_updates(engagement_id: int, extraction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply validated extraction updates to the Coaching Record.
    
    Args:
        engagement_id: The engagement to update
        extraction: Validated extraction dictionary
        
    Returns:
        Dict with counts of changes made
        
    Raises:
        PersistenceError: If database operations fail
    """
    changes = {
        'commitments_created': 0,
        'commitments_updated': 0,
        'risks_created': 0,
        'risks_updated': 0,
        'events_created': 0,
        'learning_updated': 0,
        'observations_created': 0,
        'observations_updated': 0,
        'attention_items_created': 0,
        'attention_items_updated': 0
    }
    
    try:
        if extraction.get('new_commitments'):
            changes['commitments_created'] = _create_commitments(
                engagement_id, 
                extraction['new_commitments']
            )
        
        if extraction.get('commitment_updates'):
            changes['commitments_updated'] = _update_commitments(
                extraction['commitment_updates']
            )
        
        if extraction.get('new_risks'):
            changes['risks_created'] = _create_risks(
                engagement_id,
                extraction['new_risks']
            )
        
        if extraction.get('risk_updates'):
            changes['risks_updated'] = _update_risks(
                extraction['risk_updates']
            )
        
        if extraction.get('new_events'):
            changes['events_created'] = _create_events(
                engagement_id,
                extraction['new_events']
            )
        
        if extraction.get('learning_updates'):
            changes['learning_updated'] = _update_learning(
                engagement_id,
                extraction['learning_updates']
            )
        
        if extraction.get('observation_updates'):
            changes['observations_updated'] = _update_observations(
                engagement_id,
                extraction['observation_updates']
            )
        
        if extraction.get('new_observations'):
            changes['observations_created'] = _create_observations(
                engagement_id,
                extraction['new_observations']
            )
        
        if extraction.get('attention_item_updates'):
            changes['attention_items_updated'] = _update_attention_items(
                engagement_id,
                extraction['attention_item_updates']
            )
        
        if extraction.get('advisor_attention_items'):
            changes['attention_items_created'] = _create_attention_items(
                engagement_id,
                extraction['advisor_attention_items']
            )
        
        db.session.commit()
        
        logger.info(f"Applied extraction updates for engagement {engagement_id}: {changes}")
        
        return changes
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to apply extraction updates: {str(e)}")
        raise PersistenceError(f"Failed to persist updates: {str(e)}")


def _create_commitments(engagement_id: int, commitments: List[Dict]) -> int:
    """Create new commitments."""
    count = 0
    for c in commitments:
        commitment = Commitment(
            engagement_id=engagement_id,
            description=c['description'],
            due_date=datetime.strptime(c['due_date'], '%Y-%m-%d').date() if c.get('due_date') else None,
            priority=c.get('priority', 'normal'),
            status='open',
            source=c.get('source', 'ai_extraction')
        )
        db.session.add(commitment)
        count += 1
    
    return count


def _update_commitments(updates: List[Dict]) -> int:
    """Update existing commitments."""
    count = 0
    for u in updates:
        commitment = db.session.get(Commitment, u['id'])
        if commitment:
            if 'status' in u:
                commitment.status = u['status']
                if u['status'] == 'completed' and not commitment.completed_at:
                    commitment.completed_at = datetime.utcnow()
            if 'due_date' in u and u['due_date']:
                commitment.due_date = datetime.strptime(u['due_date'], '%Y-%m-%d').date()
                logger.info(f"[RECONCILIATION] Commitment {u['id']} due_date updated to {u['due_date']}")
            count += 1
    
    return count


def _create_risks(engagement_id: int, risks: List[Dict]) -> int:
    """Create new risks."""
    count = 0
    for r in risks:
        risk = Risk(
            engagement_id=engagement_id,
            title=r['title'],
            description=r.get('description', ''),
            severity=r['severity'],
            status='open',
            advisor_attention=r.get('advisor_attention', False),
            source=r.get('source', 'ai_extraction')
        )
        db.session.add(risk)
        count += 1
    
    return count


def _update_risks(updates: List[Dict]) -> int:
    """Update existing risks."""
    count = 0
    for u in updates:
        risk = db.session.get(Risk, u['id'])
        if risk:
            if 'status' in u:
                risk.status = u['status']
            if 'description' in u:
                risk.description = u['description']
            count += 1
    
    return count


def _create_events(engagement_id: int, events: List[Dict]) -> int:
    """Create new significant events."""
    count = 0
    for e in events:
        event = SignificantEvent(
            engagement_id=engagement_id,
            title=e['title'],
            description=e.get('description', ''),
            event_date=datetime.strptime(e['event_date'], '%Y-%m-%d').date(),
            estimated_impact=e.get('estimated_impact', ''),
            source=e.get('source', 'ai_extraction')
        )
        db.session.add(event)
        count += 1
    
    return count


def _update_learning(engagement_id: int, updates: List[Dict]) -> int:
    """Update or create learning records."""
    count = 0
    for u in updates:
        existing = LearningRecord.query.filter_by(
            engagement_id=engagement_id,
            resource_id=u['resource_id']
        ).first()
        
        if existing:
            if 'status' in u:
                existing.status = u['status']
                if u['status'] == 'completed' and not existing.completed_at:
                    existing.completed_at = datetime.utcnow()
            if 'client_reflection' in u:
                existing.client_reflection = u['client_reflection']
            count += 1
        else:
            learning = LearningRecord(
                engagement_id=engagement_id,
                resource_id=u['resource_id'],
                status=u.get('status', 'recommended')
            )
            db.session.add(learning)
            count += 1
    
    return count


def _create_observations(engagement_id: int, observations: List[Dict]) -> int:
    """Create new coaching observations."""
    count = 0
    for o in observations:
        observation = CoachingObservation(
            engagement_id=engagement_id,
            observation=o['observation'],
            importance=o.get('importance', 'normal'),
            status='active',
            source=o.get('source', 'ai_extraction')
        )
        db.session.add(observation)
        count += 1
    
    return count


def _create_attention_items(engagement_id: int, items: List[Dict]) -> int:
    """Create new advisor attention items."""
    count = 0
    for item in items:
        attention = AdvisorAttention(
            engagement_id=engagement_id,
            title=item['title'],
            description=item.get('description', ''),
            priority=item.get('priority', 'normal'),
            status='open'
        )
        db.session.add(attention)
        count += 1
    
    return count


def _update_observations(engagement_id: int, updates: List[Dict]) -> int:
    """Update existing coaching observations."""
    count = 0
    for u in updates:
        observation = db.session.get(CoachingObservation, u['id'])
        if observation and observation.engagement_id == engagement_id:
            if 'status' in u:
                observation.status = u['status']
                logger.info(f"[RECONCILIATION] Observation {u['id']} -> {u['status']}")
            count += 1
        elif observation:
            logger.warning(f"[RECONCILIATION] Observation {u['id']} belongs to different engagement, skipping")
    
    return count


def _update_attention_items(engagement_id: int, updates: List[Dict]) -> int:
    """Update existing advisor attention items."""
    count = 0
    for u in updates:
        attention = db.session.get(AdvisorAttention, u['id'])
        if attention and attention.engagement_id == engagement_id:
            if 'status' in u:
                attention.status = u['status']
                logger.info(f"[RECONCILIATION] Attention item {u['id']} -> {u['status']}")
            count += 1
        elif attention:
            logger.warning(f"[RECONCILIATION] Attention item {u['id']} belongs to different engagement, skipping")
    
    return count

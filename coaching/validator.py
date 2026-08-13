"""
Validation layer for AI-extracted coaching record updates.
Ensures AI output cannot corrupt the database with invalid or unauthorized data.
"""

from datetime import datetime, date
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Raised when validation fails."""
    pass

class ExtractionValidator:
    """Validates AI-extracted session outcomes before persistence."""
    
    VALID_COMMITMENT_STATUSES = ['open', 'completed', 'deferred', 'cancelled']
    VALID_RISK_SEVERITIES = ['critical', 'high', 'moderate', 'low']
    VALID_RISK_STATUSES = ['open', 'resolved', 'mitigated']
    VALID_LEARNING_STATUSES = ['recommended', 'in_progress', 'completed']
    VALID_OBSERVATION_IMPORTANCE = ['high', 'normal', 'low']
    VALID_PRIORITIES = ['high', 'normal', 'low']
    VALID_ESCALATION_LEVELS = [0, 1, 2, 3]
    VALID_SOURCES = ['client', 'advisor', 'ai_extraction', 'system']
    
    def __init__(self, engagement_id: int, pathway_data: dict, existing_context: dict):
        """
        Initialize validator with engagement context.
        
        Args:
            engagement_id: The engagement being updated
            pathway_data: Loaded pathway configuration
            existing_context: Current coaching record context
        """
        self.engagement_id = engagement_id
        self.pathway_data = pathway_data
        self.existing_context = existing_context
        self.errors = []
    
    def validate_extraction(self, extraction: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate complete extraction output.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        self.errors = []
        
        if not isinstance(extraction, dict):
            self.errors.append("Extraction must be a dictionary")
            return False, self.errors
        
        if 'session_summary' in extraction:
            self._validate_session_summary(extraction['session_summary'])
        
        if 'new_commitments' in extraction:
            self._validate_new_commitments(extraction['new_commitments'])
        
        if 'commitment_updates' in extraction:
            self._validate_commitment_updates(extraction['commitment_updates'])
        
        if 'new_risks' in extraction:
            self._validate_new_risks(extraction['new_risks'])
        
        if 'risk_updates' in extraction:
            self._validate_risk_updates(extraction['risk_updates'])
        
        if 'new_events' in extraction:
            self._validate_new_events(extraction['new_events'])
        
        if 'learning_updates' in extraction:
            self._validate_learning_updates(extraction['learning_updates'])
        
        if 'new_observations' in extraction:
            self._validate_new_observations(extraction['new_observations'])
        
        if 'advisor_attention_items' in extraction:
            self._validate_advisor_attention(extraction['advisor_attention_items'])
        
        if 'potential_escalation' in extraction:
            self._validate_escalation(extraction['potential_escalation'])
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors
    
    def _validate_session_summary(self, summary: Any):
        """Validate session summary."""
        if not isinstance(summary, str):
            self.errors.append("session_summary must be a string")
        elif len(summary) > 1000:
            self.errors.append("session_summary exceeds maximum length")
    
    def _validate_new_commitments(self, commitments: Any):
        """Validate new commitment proposals."""
        if not isinstance(commitments, list):
            self.errors.append("new_commitments must be a list")
            return
        
        for i, commitment in enumerate(commitments):
            if not isinstance(commitment, dict):
                self.errors.append(f"new_commitments[{i}] must be a dictionary")
                continue
            
            if 'description' not in commitment:
                self.errors.append(f"new_commitments[{i}] missing required field: description")
            elif not isinstance(commitment['description'], str):
                self.errors.append(f"new_commitments[{i}].description must be a string")
            elif len(commitment['description']) > 500:
                self.errors.append(f"new_commitments[{i}].description too long")
            
            if 'priority' in commitment:
                if commitment['priority'] not in self.VALID_PRIORITIES:
                    self.errors.append(f"new_commitments[{i}].priority invalid: {commitment['priority']}")
            
            if 'due_date' in commitment and commitment['due_date']:
                try:
                    datetime.strptime(commitment['due_date'], '%Y-%m-%d')
                except ValueError:
                    self.errors.append(f"new_commitments[{i}].due_date invalid format")
            
            if 'source' in commitment:
                if commitment['source'] not in self.VALID_SOURCES:
                    self.errors.append(f"new_commitments[{i}].source invalid")
    
    def _validate_commitment_updates(self, updates: Any):
        """Validate commitment update proposals."""
        if not isinstance(updates, list):
            self.errors.append("commitment_updates must be a list")
            return
        
        existing_ids = [c['id'] for c in self.existing_context.get('open_commitments', [])]
        
        for i, update in enumerate(updates):
            if not isinstance(update, dict):
                self.errors.append(f"commitment_updates[{i}] must be a dictionary")
                continue
            
            if 'id' not in update:
                self.errors.append(f"commitment_updates[{i}] missing required field: id")
            elif update['id'] not in existing_ids:
                self.errors.append(f"commitment_updates[{i}].id references non-existent commitment")
            
            if 'status' in update:
                if update['status'] not in self.VALID_COMMITMENT_STATUSES:
                    self.errors.append(f"commitment_updates[{i}].status invalid: {update['status']}")
    
    def _validate_new_risks(self, risks: Any):
        """Validate new risk proposals."""
        if not isinstance(risks, list):
            self.errors.append("new_risks must be a list")
            return
        
        for i, risk in enumerate(risks):
            if not isinstance(risk, dict):
                self.errors.append(f"new_risks[{i}] must be a dictionary")
                continue
            
            if 'title' not in risk:
                self.errors.append(f"new_risks[{i}] missing required field: title")
            elif not isinstance(risk['title'], str):
                self.errors.append(f"new_risks[{i}].title must be a string")
            
            if 'severity' not in risk:
                self.errors.append(f"new_risks[{i}] missing required field: severity")
            elif risk['severity'] not in self.VALID_RISK_SEVERITIES:
                self.errors.append(f"new_risks[{i}].severity invalid: {risk['severity']}")
            
            if 'advisor_attention' in risk:
                if not isinstance(risk['advisor_attention'], bool):
                    self.errors.append(f"new_risks[{i}].advisor_attention must be boolean")
    
    def _validate_risk_updates(self, updates: Any):
        """Validate risk update proposals."""
        if not isinstance(updates, list):
            self.errors.append("risk_updates must be a list")
            return
        
        existing_ids = [r['id'] for r in self.existing_context.get('current_risks', [])]
        
        for i, update in enumerate(updates):
            if not isinstance(update, dict):
                self.errors.append(f"risk_updates[{i}] must be a dictionary")
                continue
            
            if 'id' not in update:
                self.errors.append(f"risk_updates[{i}] missing required field: id")
            elif update['id'] not in existing_ids:
                self.errors.append(f"risk_updates[{i}].id references non-existent risk")
            
            if 'status' in update:
                if update['status'] not in self.VALID_RISK_STATUSES:
                    self.errors.append(f"risk_updates[{i}].status invalid: {update['status']}")
    
    def _validate_new_events(self, events: Any):
        """Validate new significant event proposals."""
        if not isinstance(events, list):
            self.errors.append("new_events must be a list")
            return
        
        for i, event in enumerate(events):
            if not isinstance(event, dict):
                self.errors.append(f"new_events[{i}] must be a dictionary")
                continue
            
            if 'title' not in event:
                self.errors.append(f"new_events[{i}] missing required field: title")
            
            if 'event_date' not in event:
                self.errors.append(f"new_events[{i}] missing required field: event_date")
            else:
                try:
                    datetime.strptime(event['event_date'], '%Y-%m-%d')
                except ValueError:
                    self.errors.append(f"new_events[{i}].event_date invalid format")
    
    def _validate_learning_updates(self, updates: Any):
        """Validate learning record update proposals."""
        if not isinstance(updates, list):
            self.errors.append("learning_updates must be a list")
            return
        
        valid_resource_ids = [
            r['resource_id'] 
            for r in self.pathway_data.get('resources', {}).get('resources', [])
        ]
        
        for i, update in enumerate(updates):
            if not isinstance(update, dict):
                self.errors.append(f"learning_updates[{i}] must be a dictionary")
                continue
            
            if 'resource_id' not in update:
                self.errors.append(f"learning_updates[{i}] missing required field: resource_id")
            elif update['resource_id'] not in valid_resource_ids:
                self.errors.append(f"learning_updates[{i}].resource_id not in approved pathway resources")
            
            if 'status' in update:
                if update['status'] not in self.VALID_LEARNING_STATUSES:
                    self.errors.append(f"learning_updates[{i}].status invalid: {update['status']}")
    
    def _validate_new_observations(self, observations: Any):
        """Validate new coaching observation proposals."""
        if not isinstance(observations, list):
            self.errors.append("new_observations must be a list")
            return
        
        for i, obs in enumerate(observations):
            if not isinstance(obs, dict):
                self.errors.append(f"new_observations[{i}] must be a dictionary")
                continue
            
            if 'observation' not in obs:
                self.errors.append(f"new_observations[{i}] missing required field: observation")
            elif not isinstance(obs['observation'], str):
                self.errors.append(f"new_observations[{i}].observation must be a string")
            
            if 'importance' in obs:
                if obs['importance'] not in self.VALID_OBSERVATION_IMPORTANCE:
                    self.errors.append(f"new_observations[{i}].importance invalid")
    
    def _validate_advisor_attention(self, items: Any):
        """Validate advisor attention item proposals."""
        if not isinstance(items, list):
            self.errors.append("advisor_attention_items must be a list")
            return
        
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                self.errors.append(f"advisor_attention_items[{i}] must be a dictionary")
                continue
            
            if 'title' not in item:
                self.errors.append(f"advisor_attention_items[{i}] missing required field: title")
            
            if 'priority' in item:
                if item['priority'] not in self.VALID_PRIORITIES:
                    self.errors.append(f"advisor_attention_items[{i}].priority invalid")
    
    def _validate_escalation(self, escalation: Any):
        """Validate escalation proposal."""
        if not isinstance(escalation, dict):
            self.errors.append("potential_escalation must be a dictionary")
            return
        
        if 'detected' not in escalation:
            self.errors.append("potential_escalation missing required field: detected")
        elif not isinstance(escalation['detected'], bool):
            self.errors.append("potential_escalation.detected must be boolean")
        
        if 'level' in escalation:
            if escalation['level'] not in self.VALID_ESCALATION_LEVELS:
                self.errors.append(f"potential_escalation.level invalid: {escalation['level']}")

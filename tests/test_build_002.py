import unittest
import sys
import os
import json
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, process_session_extraction
from models import db, User, Advisor, Client, Business, Engagement, PathwayState, Commitment, Risk, SignificantEvent, LearningRecord, CoachingObservation, Session, AdvisorGuidance, AdvisorAttention, SessionMessage
from coaching import (
    AIService,
    build_coaching_system_prompt,
    build_extraction_prompt,
    ExtractionValidator,
    apply_extraction_updates,
    load_pathway,
    build_coaching_context
)

class TestAIServiceAbstraction(unittest.TestCase):
    """Test AI service abstraction layer."""
    
    def test_ai_service_requires_api_key(self):
        """AI service should require OPENAI_API_KEY."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(Exception):
                AIService()
    
    def test_ai_service_uses_default_model(self):
        """AI service should use default model if not specified."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            service = AIService()
            self.assertEqual(service.model, 'gpt-4-turbo-preview')
    
    def test_ai_service_uses_configured_model(self):
        """AI service should use configured model."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'gpt-3.5-turbo'}):
            service = AIService()
            self.assertEqual(service.model, 'gpt-3.5-turbo')


class TestPromptBuilder(unittest.TestCase):
    """Test coaching prompt construction."""
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        advisor_user = User(email='advisor@test.com', role='ADVISOR', active=True)
        advisor_user.set_password('test123')
        db.session.add(advisor_user)
        db.session.flush()
        
        advisor = Advisor(user_id=advisor_user.id, first_name='Test', last_name='Advisor')
        db.session.add(advisor)
        db.session.flush()
        
        client_user = User(email='client@test.com', role='CLIENT', active=True)
        client_user.set_password('test123')
        db.session.add(client_user)
        db.session.flush()
        
        client = Client(user_id=client_user.id, first_name='Test', last_name='Client')
        db.session.add(client)
        db.session.flush()
        
        business = Business(
            client_id=client.id,
            business_name='Test Business',
            current_situation_summary='Test situation'
        )
        db.session.add(business)
        
        engagement = Engagement(
            client_id=client.id,
            advisor_id=advisor.id,
            pathway_id='PATHWAY-001',
            pathway_version='0.1',
            status='active',
            start_date=date.today()
        )
        db.session.add(engagement)
        db.session.flush()
        
        pathway_state = PathwayState(
            engagement_id=engagement.id,
            current_stage_id='RS-01',
            current_day=15,
            current_focus='Test focus'
        )
        db.session.add(pathway_state)
        
        db.session.commit()
        
        self.engagement_id = engagement.id
    
    def test_prompt_includes_client_name(self):
        """System prompt should include client name."""
        with app.app_context():
            context = build_coaching_context(self.engagement_id)
            pathway_data = load_pathway('PATHWAY-001')
            prompt = build_coaching_system_prompt(context, pathway_data)
            
            self.assertIn('Test', prompt)
            self.assertIn('Test Business', prompt)
    
    def test_prompt_includes_pathway_info(self):
        """System prompt should include pathway information."""
        with app.app_context():
            context = build_coaching_context(self.engagement_id)
            pathway_data = load_pathway('PATHWAY-001')
            prompt = build_coaching_system_prompt(context, pathway_data)
            
            self.assertIn('Recovery & Stabilization', prompt)
            self.assertIn('RS-01', prompt)
    
    def test_prompt_includes_platform_instructions(self):
        """System prompt should include platform-level coaching instructions."""
        with app.app_context():
            context = build_coaching_context(self.engagement_id)
            pathway_data = load_pathway('PATHWAY-001')
            prompt = build_coaching_system_prompt(context, pathway_data)
            
            self.assertIn('calm', prompt.lower())
            self.assertIn('practical', prompt.lower())
            self.assertIn('commitment', prompt.lower())
    
    def test_extraction_prompt_defines_schema(self):
        """Extraction prompt should define JSON schema."""
        prompt = build_extraction_prompt()
        
        self.assertIn('new_commitments', prompt)
        self.assertIn('commitment_updates', prompt)
        self.assertIn('new_risks', prompt)
        self.assertIn('potential_escalation', prompt)


class TestExtractionValidator(unittest.TestCase):
    """Test validation of AI-extracted updates."""
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        advisor_user = User(email='advisor@test.com', role='ADVISOR', active=True)
        advisor_user.set_password('test123')
        db.session.add(advisor_user)
        db.session.flush()
        
        advisor = Advisor(user_id=advisor_user.id, first_name='Test', last_name='Advisor')
        db.session.add(advisor)
        db.session.flush()
        
        client_user = User(email='client@test.com', role='CLIENT', active=True)
        client_user.set_password('test123')
        db.session.add(client_user)
        db.session.flush()
        
        client = Client(user_id=client_user.id, first_name='Test', last_name='Client')
        db.session.add(client)
        db.session.flush()
        
        business = Business(client_id=client.id, business_name='Test Business')
        db.session.add(business)
        
        engagement = Engagement(
            client_id=client.id,
            advisor_id=advisor.id,
            pathway_id='PATHWAY-001',
            pathway_version='0.1',
            status='active',
            start_date=date.today()
        )
        db.session.add(engagement)
        db.session.flush()
        
        commitment = Commitment(
            engagement_id=engagement.id,
            description='Test commitment',
            status='open'
        )
        db.session.add(commitment)
        db.session.flush()
        
        db.session.commit()
        
        self.engagement_id = engagement.id
        self.commitment_id = commitment.id
    
    def test_valid_extraction_passes(self):
        """Valid extraction should pass validation."""
        with app.app_context():
            context = build_coaching_context(self.engagement_id)
            pathway_data = load_pathway('PATHWAY-001')
            
            extraction = {
                "session_summary": "Test session",
                "new_commitments": [],
                "commitment_updates": [],
                "new_risks": [],
                "risk_updates": [],
                "new_events": [],
                "learning_updates": [],
                "new_observations": [],
                "advisor_attention_items": [],
                "potential_escalation": {
                    "detected": False,
                    "level": 0,
                    "reason": None
                }
            }
            
            validator = ExtractionValidator(self.engagement_id, pathway_data, context)
            is_valid, errors = validator.validate_extraction(extraction)
            
            self.assertTrue(is_valid)
            self.assertEqual(len(errors), 0)
    
    def test_invalid_commitment_status_fails(self):
        """Invalid commitment status should fail validation."""
        with app.app_context():
            context = build_coaching_context(self.engagement_id)
            pathway_data = load_pathway('PATHWAY-001')
            
            extraction = {
                "new_commitments": [
                    {
                        "description": "Test",
                        "status": "invalid_status"
                    }
                ]
            }
            
            validator = ExtractionValidator(self.engagement_id, pathway_data, context)
            is_valid, errors = validator.validate_extraction(extraction)
            
            self.assertFalse(is_valid)
            self.assertTrue(len(errors) > 0)
    
    def test_invalid_resource_id_fails(self):
        """Invalid resource ID should fail validation."""
        with app.app_context():
            context = build_coaching_context(self.engagement_id)
            pathway_data = load_pathway('PATHWAY-001')
            
            extraction = {
                "learning_updates": [
                    {
                        "resource_id": "INVALID-RESOURCE",
                        "status": "recommended"
                    }
                ]
            }
            
            validator = ExtractionValidator(self.engagement_id, pathway_data, context)
            is_valid, errors = validator.validate_extraction(extraction)
            
            self.assertFalse(is_valid)
            self.assertIn("not in approved pathway resources", str(errors))
    
    def test_valid_resource_id_passes(self):
        """Valid resource ID should pass validation."""
        with app.app_context():
            context = build_coaching_context(self.engagement_id)
            pathway_data = load_pathway('PATHWAY-001')
            
            extraction = {
                "learning_updates": [
                    {
                        "resource_id": "RS-R001",
                        "status": "recommended"
                    }
                ]
            }
            
            validator = ExtractionValidator(self.engagement_id, pathway_data, context)
            is_valid, errors = validator.validate_extraction(extraction)
            
            self.assertTrue(is_valid)


class TestPersistence(unittest.TestCase):
    """Test persistence of validated updates."""
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        advisor_user = User(email='advisor@test.com', role='ADVISOR', active=True)
        advisor_user.set_password('test123')
        db.session.add(advisor_user)
        db.session.flush()
        
        advisor = Advisor(user_id=advisor_user.id, first_name='Test', last_name='Advisor')
        db.session.add(advisor)
        db.session.flush()
        
        client_user = User(email='client@test.com', role='CLIENT', active=True)
        client_user.set_password('test123')
        db.session.add(client_user)
        db.session.flush()
        
        client = Client(user_id=client_user.id, first_name='Test', last_name='Client')
        db.session.add(client)
        db.session.flush()
        
        business = Business(client_id=client.id, business_name='Test Business')
        db.session.add(business)
        
        engagement = Engagement(
            client_id=client.id,
            advisor_id=advisor.id,
            pathway_id='PATHWAY-001',
            pathway_version='0.1',
            status='active',
            start_date=date.today()
        )
        db.session.add(engagement)
        db.session.flush()
        
        commitment = Commitment(
            engagement_id=engagement.id,
            description='Test commitment',
            status='open'
        )
        db.session.add(commitment)
        db.session.flush()
        
        db.session.commit()
        
        self.engagement_id = engagement.id
        self.commitment_id = commitment.id
    
    def test_create_new_commitment(self):
        """Should create new commitment from extraction."""
        with app.app_context():
            extraction = {
                "new_commitments": [
                    {
                        "description": "New commitment",
                        "due_date": "2024-12-31",
                        "priority": "high",
                        "source": "ai_extraction"
                    }
                ]
            }
            
            changes = apply_extraction_updates(self.engagement_id, extraction)
            
            self.assertEqual(changes['commitments_created'], 1)
            
            new_commitment = Commitment.query.filter_by(
                engagement_id=self.engagement_id,
                description="New commitment"
            ).first()
            
            self.assertIsNotNone(new_commitment)
            self.assertEqual(new_commitment.priority, 'high')
            self.assertEqual(new_commitment.source, 'ai_extraction')
    
    def test_update_existing_commitment(self):
        """Should update existing commitment status."""
        with app.app_context():
            extraction = {
                "commitment_updates": [
                    {
                        "id": self.commitment_id,
                        "status": "completed"
                    }
                ]
            }
            
            changes = apply_extraction_updates(self.engagement_id, extraction)
            
            self.assertEqual(changes['commitments_updated'], 1)
            
            updated = db.session.get(Commitment, self.commitment_id)
            self.assertEqual(updated.status, 'completed')
            self.assertIsNotNone(updated.completed_at)
    
    def test_create_risk(self):
        """Should create new risk from extraction."""
        with app.app_context():
            extraction = {
                "new_risks": [
                    {
                        "title": "Test risk",
                        "description": "Risk description",
                        "severity": "high",
                        "advisor_attention": True,
                        "source": "ai_extraction"
                    }
                ]
            }
            
            changes = apply_extraction_updates(self.engagement_id, extraction)
            
            self.assertEqual(changes['risks_created'], 1)
            
            risk = Risk.query.filter_by(
                engagement_id=self.engagement_id,
                title="Test risk"
            ).first()
            
            self.assertIsNotNone(risk)
            self.assertEqual(risk.severity, 'high')
            self.assertTrue(risk.advisor_attention)
    
    def test_create_advisor_attention_item(self):
        """Should create advisor attention item."""
        with app.app_context():
            extraction = {
                "advisor_attention_items": [
                    {
                        "title": "Needs attention",
                        "description": "Important issue",
                        "priority": "high"
                    }
                ]
            }
            
            changes = apply_extraction_updates(self.engagement_id, extraction)
            
            self.assertEqual(changes['attention_items_created'], 1)
            
            item = AdvisorAttention.query.filter_by(
                engagement_id=self.engagement_id,
                title="Needs attention"
            ).first()
            
            self.assertIsNotNone(item)
            self.assertEqual(item.priority, 'high')


class TestProvenance(unittest.TestCase):
    """Test provenance tracking."""
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        advisor_user = User(email='advisor@test.com', role='ADVISOR', active=True)
        advisor_user.set_password('test123')
        db.session.add(advisor_user)
        db.session.flush()
        
        advisor = Advisor(user_id=advisor_user.id, first_name='Test', last_name='Advisor')
        db.session.add(advisor)
        db.session.flush()
        
        client_user = User(email='client@test.com', role='CLIENT', active=True)
        client_user.set_password('test123')
        db.session.add(client_user)
        db.session.flush()
        
        client = Client(user_id=client_user.id, first_name='Test', last_name='Client')
        db.session.add(client)
        db.session.flush()
        
        business = Business(client_id=client.id, business_name='Test Business')
        db.session.add(business)
        
        engagement = Engagement(
            client_id=client.id,
            advisor_id=advisor.id,
            pathway_id='PATHWAY-001',
            pathway_version='0.1',
            status='active',
            start_date=date.today()
        )
        db.session.add(engagement)
        db.session.flush()
        
        db.session.commit()
        
        self.engagement_id = engagement.id
    
    def test_ai_extracted_commitment_has_source(self):
        """AI-extracted commitment should have ai_extraction source."""
        with app.app_context():
            extraction = {
                "new_commitments": [
                    {
                        "description": "AI commitment",
                        "source": "ai_extraction"
                    }
                ]
            }
            
            apply_extraction_updates(self.engagement_id, extraction)
            
            commitment = Commitment.query.filter_by(
                engagement_id=self.engagement_id,
                description="AI commitment"
            ).first()
            
            self.assertEqual(commitment.source, 'ai_extraction')
    
    def test_ai_extracted_risk_has_source(self):
        """AI-extracted risk should have ai_extraction source."""
        with app.app_context():
            extraction = {
                "new_risks": [
                    {
                        "title": "AI risk",
                        "severity": "moderate",
                        "source": "ai_extraction"
                    }
                ]
            }
            
            apply_extraction_updates(self.engagement_id, extraction)
            
            risk = Risk.query.filter_by(
                engagement_id=self.engagement_id,
                title="AI risk"
            ).first()
            
            self.assertEqual(risk.source, 'ai_extraction')


if __name__ == '__main__':
    unittest.main()

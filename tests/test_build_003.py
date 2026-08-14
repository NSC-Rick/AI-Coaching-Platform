"""
Build 003 Test Suite - Voice Integration

Tests for ElevenLabs voice coaching integration while preserving
Build 001 and Build 002 functionality.

Test Coverage:
- Voice session initialization
- Voice session completion with extraction
- Client isolation for voice sessions
- Fallback to text coaching
- Voice service abstraction
- Integration with existing extraction pipeline
"""

import unittest
import os
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, Advisor, Client, Business, Engagement, PathwayState, Session, SessionMessage, Commitment
from coaching import get_voice_service


class TestBuild003VoiceIntegration(unittest.TestCase):
    """Test Build 003 voice integration features."""
    
    def setUp(self):
        """Set up test client and database."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        os.environ['ELEVENLABS_API_KEY'] = 'test-api-key'
        os.environ['ELEVENLABS_AGENT_ID'] = 'test-agent-id'
        os.environ['OPENAI_API_KEY'] = 'test-openai-key'
        
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_data(self):
        """Create test users and engagements."""
        from werkzeug.security import generate_password_hash
        
        advisor_user = User(
            email='advisor@test.com',
            password_hash=generate_password_hash('password'),
            role='ADVISOR',
            first_name='Test',
            last_name='Advisor'
        )
        db.session.add(advisor_user)
        db.session.flush()
        
        advisor = Advisor(user_id=advisor_user.id)
        db.session.add(advisor)
        db.session.flush()
        
        client_user = User(
            email='client@test.com',
            password_hash=generate_password_hash('password'),
            role='CLIENT',
            first_name='Sarah'
        )
        db.session.add(client_user)
        db.session.flush()
        
        client = Client(user_id=client_user.id)
        db.session.add(client)
        db.session.flush()
        
        business = Business(
            client_id=client.id,
            business_name="Test Hardware"
        )
        db.session.add(business)
        db.session.flush()
        
        engagement = Engagement(
            client_id=client.id,
            business_id=business.id,
            advisor_id=advisor.id,
            pathway_id='PATHWAY-001',
            status='active'
        )
        db.session.add(engagement)
        db.session.flush()
        
        pathway_state = PathwayState(
            engagement_id=engagement.id,
            current_stage_id='RS-01',
            current_day=15,
            current_focus='Short-term liquidity'
        )
        db.session.add(pathway_state)
        
        db.session.commit()
        
        self.advisor_user = advisor_user
        self.client_user = client_user
        self.engagement = engagement
    
    def _login_client(self):
        """Helper to log in as client."""
        self.client.post('/login', data={
            'email': 'client@test.com',
            'password': 'password'
        }, follow_redirects=True)
    
    def _login_advisor(self):
        """Helper to log in as advisor."""
        self.client.post('/login', data={
            'email': 'advisor@test.com',
            'password': 'password'
        }, follow_redirects=True)
    
    # ========================================================================
    # TEST 1: Voice Session Initialization
    # ========================================================================
    
    @patch('coaching.voice_service.requests.get')
    def test_voice_session_initialization(self, mock_get):
        """Test that voice session can be initialized with correct context."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'signed_url': 'https://test.elevenlabs.io/signed'}
        mock_get.return_value = mock_response
        
        self._login_client()
        
        response = self.client.post(
            f'/voice/session/init/{self.engagement.id}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('session_id', data)
        self.assertIn('signed_url', data)
        self.assertIn('config', data)
        
        session = Session.query.get(data['session_id'])
        self.assertIsNotNone(session)
        self.assertEqual(session.interaction_type, 'voice')
        self.assertEqual(session.status, 'active')
        self.assertEqual(session.engagement_id, self.engagement.id)
        
        config = data['config']
        self.assertEqual(config['agent_id'], 'test-agent-id')
        self.assertIn('session_metadata', config)
        self.assertIn('conversation_config_override', config)
    
    # ========================================================================
    # TEST 2: Client Isolation for Voice Sessions
    # ========================================================================
    
    @patch('coaching.voice_service.requests.get')
    def test_voice_session_client_isolation(self, mock_get):
        """Test that clients cannot access each other's voice sessions."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'signed_url': 'https://test.elevenlabs.io/signed'}
        mock_get.return_value = mock_response
        
        from werkzeug.security import generate_password_hash
        
        other_client_user = User(
            email='other@test.com',
            password_hash=generate_password_hash('password'),
            role='CLIENT',
            first_name='Michael'
        )
        db.session.add(other_client_user)
        db.session.flush()
        
        other_client = Client(user_id=other_client_user.id)
        db.session.add(other_client)
        db.session.flush()
        
        other_business = Business(
            client_id=other_client.id,
            business_name="Other Business"
        )
        db.session.add(other_business)
        db.session.flush()
        
        other_engagement = Engagement(
            client_id=other_client.id,
            business_id=other_business.id,
            advisor_id=self.advisor_user.advisor.id,
            pathway_id='PATHWAY-001',
            status='active'
        )
        db.session.add(other_engagement)
        db.session.commit()
        
        self._login_client()
        
        response = self.client.post(
            f'/voice/session/init/{other_engagement.id}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    # ========================================================================
    # TEST 3: Voice Session Completion and Extraction
    # ========================================================================
    
    @patch('coaching.ai_service.AIService.extract_session_outcomes')
    @patch('coaching.voice_service.requests.get')
    def test_voice_session_completion_with_extraction(self, mock_get, mock_extract):
        """Test that voice session completes and triggers extraction pipeline."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'signed_url': 'https://test.elevenlabs.io/signed'}
        mock_get.return_value = mock_response
        
        mock_extract.return_value = {
            'session_summary': 'Client discussed cash flow concerns',
            'new_commitments': [
                {
                    'description': 'Update 14-day cash tracker',
                    'due_date': None,
                    'priority': 'high'
                }
            ],
            'commitment_updates': [],
            'new_risks': [],
            'risk_updates': [],
            'new_events': [],
            'new_learning': [],
            'new_observations': [],
            'advisor_attention': False,
            'escalation_level': 0
        }
        
        self._login_client()
        
        init_response = self.client.post(
            f'/voice/session/init/{self.engagement.id}',
            content_type='application/json'
        )
        init_data = json.loads(init_response.data)
        session_id = init_data['session_id']
        
        conversation_data = {
            'session_id': session_id,
            'duration': 180,
            'status': 'completed',
            'messages': [
                {
                    'role': 'assistant',
                    'content': 'Hi Sarah, how are things going with your cash tracker?',
                    'timestamp': datetime.utcnow().isoformat()
                },
                {
                    'role': 'user',
                    'content': 'I need to update it. I will do that today.',
                    'timestamp': datetime.utcnow().isoformat()
                }
            ]
        }
        
        complete_response = self.client.post(
            f'/voice/session/{session_id}/complete',
            data=json.dumps(conversation_data),
            content_type='application/json'
        )
        
        self.assertEqual(complete_response.status_code, 200)
        complete_data = json.loads(complete_response.data)
        self.assertEqual(complete_data['status'], 'success')
        
        session = Session.query.get(session_id)
        self.assertEqual(session.status, 'completed')
        self.assertIsNotNone(session.ended_at)
        
        messages = SessionMessage.query.filter_by(session_id=session_id).all()
        self.assertEqual(len(messages), 2)
        
        commitments = Commitment.query.filter_by(engagement_id=self.engagement.id).all()
        self.assertGreater(len(commitments), 0)
    
    # ========================================================================
    # TEST 4: Voice Session Cancellation
    # ========================================================================
    
    @patch('coaching.voice_service.requests.get')
    def test_voice_session_cancellation(self, mock_get):
        """Test that interrupted voice sessions can be cancelled safely."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'signed_url': 'https://test.elevenlabs.io/signed'}
        mock_get.return_value = mock_response
        
        self._login_client()
        
        init_response = self.client.post(
            f'/voice/session/init/{self.engagement.id}',
            content_type='application/json'
        )
        init_data = json.loads(init_response.data)
        session_id = init_data['session_id']
        
        cancel_response = self.client.post(
            f'/voice/session/{session_id}/cancel',
            content_type='application/json'
        )
        
        self.assertEqual(cancel_response.status_code, 200)
        
        session = Session.query.get(session_id)
        self.assertEqual(session.status, 'cancelled')
        self.assertEqual(session.summary, 'Session interrupted')
        self.assertIsNotNone(session.ended_at)
    
    # ========================================================================
    # TEST 5: Text Coaching Still Works
    # ========================================================================
    
    @patch('coaching.ai_service.AIService.generate_coaching_response')
    def test_text_coaching_preserved(self, mock_generate):
        """Test that Build 002 text coaching still works alongside voice."""
        mock_generate.return_value = "Hello! How can I help you today?"
        
        self._login_client()
        
        response = self.client.post(
            f'/session/start/{self.engagement.id}',
            follow_redirects=False
        )
        
        self.assertEqual(response.status_code, 302)
        
        sessions = Session.query.filter_by(
            engagement_id=self.engagement.id,
            interaction_type='text'
        ).all()
        
        self.assertGreater(len(sessions), 0)
        session = sessions[0]
        self.assertEqual(session.status, 'active')
    
    # ========================================================================
    # TEST 6: Voice Service Abstraction
    # ========================================================================
    
    def test_voice_service_abstraction(self):
        """Test that VoiceService provides clean abstraction."""
        voice_service = get_voice_service()
        
        self.assertIsNotNone(voice_service)
        self.assertEqual(voice_service.agent_id, 'test-agent-id')
        
        config = voice_service.build_session_config(
            client_name='Sarah',
            business_name='Test Hardware',
            pathway_name='Recovery & Stabilization',
            current_stage='RS-01',
            current_day=15,
            coaching_context='Test context',
            session_id='123',
            user_id='456'
        )
        
        self.assertIn('agent_id', config)
        self.assertIn('session_metadata', config)
        self.assertIn('conversation_config_override', config)
        
        metadata = config['session_metadata']
        self.assertEqual(metadata['client_name'], 'Sarah')
        self.assertEqual(metadata['business_name'], 'Test Hardware')
    
    # ========================================================================
    # TEST 7: Voice Context Matches Text Context
    # ========================================================================
    
    @patch('coaching.voice_service.requests.get')
    def test_voice_context_matches_text_context(self, mock_get):
        """Test that voice coach receives same context as text coach."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'signed_url': 'https://test.elevenlabs.io/signed'}
        mock_get.return_value = mock_response
        
        self._login_client()
        
        response = self.client.post(
            f'/voice/session/init/{self.engagement.id}',
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        config = data['config']
        
        self.assertIn('conversation_config_override', config)
        override = config['conversation_config_override']
        self.assertIn('agent', override)
        self.assertIn('prompt', override['agent'])
        
        prompt = override['agent']['prompt']['prompt']
        
        self.assertIn('Sarah', prompt)
        self.assertIn('Test Hardware', prompt)
        self.assertIn('Recovery', prompt)
        self.assertIn('RS-01', prompt)
        self.assertIn('Day 15', prompt)
        self.assertIn('Short-term liquidity', prompt)
    
    # ========================================================================
    # TEST 8: Unauthorized Access Denied
    # ========================================================================
    
    def test_voice_session_requires_authentication(self):
        """Test that voice sessions require authentication."""
        response = self.client.post(
            f'/voice/session/init/{self.engagement.id}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 302)
    
    # ========================================================================
    # TEST 9: Voice Session Uses Existing Extraction Pipeline
    # ========================================================================
    
    @patch('coaching.ai_service.AIService.extract_session_outcomes')
    @patch('coaching.voice_service.requests.get')
    def test_voice_uses_build_002_extraction(self, mock_get, mock_extract):
        """Test that voice sessions use the same extraction pipeline as text."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'signed_url': 'https://test.elevenlabs.io/signed'}
        mock_get.return_value = mock_response
        
        mock_extract.return_value = {
            'session_summary': 'Test summary',
            'new_commitments': [],
            'commitment_updates': [],
            'new_risks': [],
            'risk_updates': [],
            'new_events': [],
            'new_learning': [],
            'new_observations': [],
            'advisor_attention': False,
            'escalation_level': 0
        }
        
        self._login_client()
        
        init_response = self.client.post(
            f'/voice/session/init/{self.engagement.id}',
            content_type='application/json'
        )
        init_data = json.loads(init_response.data)
        session_id = init_data['session_id']
        
        conversation_data = {
            'session_id': session_id,
            'messages': [
                {'role': 'user', 'content': 'Test message'}
            ]
        }
        
        self.client.post(
            f'/voice/session/{session_id}/complete',
            data=json.dumps(conversation_data),
            content_type='application/json'
        )
        
        mock_extract.assert_called_once()
        
        call_args = mock_extract.call_args
        self.assertIn('messages', call_args[1])
        self.assertIn('context', call_args[1])


if __name__ == '__main__':
    unittest.main()

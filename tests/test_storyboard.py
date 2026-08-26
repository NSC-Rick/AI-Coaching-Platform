"""
Tests for the Client Storyboard feature.

Verifies read-only behavior, advisor authorization, grounding input,
failure handling, and integration with the existing coaching record.
"""

import os
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, User, Advisor, Client, Business, Engagement, PathwayState
from models import (
    Commitment, Risk, SignificantEvent, CoachingObservation,
    Session, AdvisorGuidance, AdvisorAttention, LearningRecord
)
from coaching.storyboard import build_storyboard_context, build_storyboard_prompt, generate_storyboard
from coaching.ai_service import AIServiceError


class TestStoryboardContext(unittest.TestCase):
    """Verify the Storyboard context builder is read-only and comprehensive."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app
        self.client = app.test_client()

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

        self.advisor = Advisor(user_id=advisor_user.id, first_name='Ronda', last_name='Advisor')
        db.session.add(self.advisor)
        db.session.flush()
        self.advisor_id = self.advisor.id

        client_user = User(email='client@test.com', role='CLIENT', active=True)
        client_user.set_password('test123')
        db.session.add(client_user)
        db.session.flush()

        self.client_record = Client(user_id=client_user.id, first_name='Sarah', last_name='Bellamy')
        db.session.add(self.client_record)
        db.session.flush()

        self.business = Business(
            client_id=self.client_record.id,
            business_name="Sarah's Bakery",
            industry='Food Service',
            current_situation_summary='Short-term cash pressure after losing a major account.'
        )
        db.session.add(self.business)
        db.session.flush()

        self.engagement = Engagement(
            client_id=self.client_record.id,
            advisor_id=self.advisor.id,
            pathway_id='PATHWAY-001',
            pathway_version='0.1',
            status='active',
            start_date=date.today() - timedelta(days=30)
        )
        db.session.add(self.engagement)
        db.session.flush()
        self.engagement_id = self.engagement.id

        self.pathway_state = PathwayState(
            engagement_id=self.engagement_id,
            current_stage_id='RS-01',
            current_day=18,
            current_focus='Short-term cash visibility',
            current_priority_summary='Make payroll and protect cash position.'
        )
        db.session.add(self.pathway_state)
        db.session.flush()

        self.commitment = Commitment(
            engagement_id=self.engagement_id,
            description='Call lender about payment timing flexibility',
            status='open',
            priority='high',
            due_date=date.today() + timedelta(days=2)
        )
        db.session.add(self.commitment)

        self.risk = Risk(
            engagement_id=self.engagement_id,
            title='Payroll coverage shortfall',
            description='May not cover Friday payroll.',
            severity='high',
            status='open',
            advisor_attention=True
        )
        db.session.add(self.risk)

        self.event = SignificantEvent(
            engagement_id=self.engagement_id,
            title='Lost Johnson account',
            description='Monthly recurring revenue lost.',
            event_date=date.today() - timedelta(days=10),
            estimated_impact='Lost $5,000/month recurring revenue'
        )
        db.session.add(self.event)

        self.observation = CoachingObservation(
            engagement_id=self.engagement_id,
            observation='Client avoids lender contact until pressure is severe.',
            importance='high',
            status='active'
        )
        db.session.add(self.observation)

        self.guidance = AdvisorGuidance(
            engagement_id=self.engagement_id,
            advisor_id=self.advisor.id,
            guidance='Prioritize cash visibility and lender preparation for the next two weeks.',
            priority='high',
            status='active'
        )
        db.session.add(self.guidance)

        self.session = Session(
            engagement_id=self.engagement_id,
            started_at=datetime.utcnow() - timedelta(days=1),
            ended_at=datetime.utcnow() - timedelta(days=1) + timedelta(minutes=10),
            interaction_type='text',
            status='completed',
            summary='Discussed cash flow pressure and customer outreach.',
            processing_status='complete'
        )
        db.session.add(self.session)

        db.session.commit()

    def test_build_storyboard_context_includes_expected_data(self):
        with app.app_context():
            context = build_storyboard_context(self.engagement_id)

        self.assertEqual(context['client']['first_name'], 'Sarah')
        self.assertEqual(context['client']['name'], 'Sarah Bellamy')
        self.assertEqual(context['business']['name'], "Sarah's Bakery")
        self.assertEqual(context['pathway']['name'], 'Recovery & Stabilization')
        self.assertEqual(context['current_state']['stage_id'], 'RS-01')
        self.assertEqual(context['current_state']['current_day'], 18)

        self.assertEqual(len(context['commitments']), 1)
        self.assertEqual(context['commitments'][0]['description'], 'Call lender about payment timing flexibility')

        self.assertEqual(len(context['risks']), 1)
        self.assertEqual(context['risks'][0]['title'], 'Payroll coverage shortfall')

        self.assertEqual(len(context['significant_events']), 1)
        self.assertEqual(context['significant_events'][0]['title'], 'Lost Johnson account')

        self.assertEqual(len(context['coaching_observations']), 1)
        self.assertEqual(len(context['advisor_guidance']), 1)
        self.assertEqual(len(context['sessions']), 1)
        self.assertEqual(context['sessions'][0]['summary'], 'Discussed cash flow pressure and customer outreach.')

    def test_build_storyboard_context_is_read_only(self):
        with app.app_context():
            before_counts = {
                'commitments': Commitment.query.count(),
                'risks': Risk.query.count(),
                'events': SignificantEvent.query.count(),
                'sessions': Session.query.count(),
                'guidance': AdvisorGuidance.query.count()
            }

            build_storyboard_context(self.engagement_id)

            after_counts = {
                'commitments': Commitment.query.count(),
                'risks': Risk.query.count(),
                'events': SignificantEvent.query.count(),
                'sessions': Session.query.count(),
                'guidance': AdvisorGuidance.query.count()
            }

        for key in before_counts:
            self.assertEqual(before_counts[key], after_counts[key])

    def test_storyboard_prompt_contains_grounding_rules(self):
        prompt = build_storyboard_prompt()
        self.assertIn('Starting Situation', prompt)
        self.assertIn('Key Developments', prompt)
        self.assertIn('Actions & Commitments', prompt)
        self.assertIn('Advisor & Coaching Support', prompt)
        self.assertIn('Advisor Guidance', prompt)
        self.assertIn('AI Coaching Support', prompt)
        self.assertIn('Pathway Progress', prompt)
        self.assertIn('Current Position & Next Focus', prompt)
        self.assertIn('Do not invent facts', prompt)
        self.assertIn('Do not infer milestone completion', prompt)
        self.assertIn('Use ONLY the information provided in the Storyboard Context', prompt)

    def test_storyboard_prompt_removes_internal_metadata(self):
        prompt = build_storyboard_prompt()
        self.assertIn('database IDs', prompt)
        self.assertIn('raw ISO timestamps', prompt)
        self.assertIn('stage_id', prompt)
        self.assertIn('PATHWAY-001', prompt)
        self.assertIn('completed_at', prompt)

    def test_storyboard_prompt_requires_deduplication(self):
        prompt = build_storyboard_prompt()
        self.assertIn('consolidate', prompt)
        self.assertIn('duplicate', prompt)

    def test_storyboard_prompt_requires_temporal_consistency(self):
        prompt = build_storyboard_prompt()
        self.assertIn('Newer explicit evidence', prompt)
        self.assertIn('discrepancy', prompt)

    def test_storyboard_prompt_requires_advisor_friendly_dates(self):
        prompt = build_storyboard_prompt()
        self.assertIn('Aug. 23, 2026', prompt)

    def test_mature_engagement_context_is_bounded(self):
        with app.app_context():
            advisor_id = self.advisor_id

            # Add a large volume of routine historical records.
            for i in range(20):
                db.session.add(Commitment(
                    engagement_id=self.engagement_id,
                    description=f'Completed action {i}',
                    status='completed',
                    completed_at=datetime.utcnow() - timedelta(days=i)
                ))
            for i in range(5):
                db.session.add(Commitment(
                    engagement_id=self.engagement_id,
                    description=f'Open action {i}',
                    status='open'
                ))
            for i in range(15):
                db.session.add(Session(
                    engagement_id=self.engagement_id,
                    started_at=datetime.utcnow() - timedelta(days=i),
                    ended_at=datetime.utcnow() - timedelta(days=i) + timedelta(minutes=10),
                    interaction_type='text',
                    status='completed',
                    summary=f'Session summary {i}',
                    processing_status='complete'
                ))
            for i in range(15):
                db.session.add(CoachingObservation(
                    engagement_id=self.engagement_id,
                    observation=f'Historical observation {i}',
                    importance='normal',
                    status='resolved'
                ))
            for i in range(15):
                db.session.add(AdvisorAttention(
                    engagement_id=self.engagement_id,
                    title=f'Resolved attention {i}',
                    description='Resolved',
                    priority='normal',
                    status='resolved'
                ))
            for i in range(15):
                db.session.add(AdvisorGuidance(
                    engagement_id=self.engagement_id,
                    advisor_id=advisor_id,
                    guidance=f'Guidance {i}',
                    status='active'
                ))
            for i in range(15):
                db.session.add(Risk(
                    engagement_id=self.engagement_id,
                    title=f'Resolved risk {i}',
                    description='Resolved',
                    severity='moderate',
                    status='resolved'
                ))
            for i in range(15):
                db.session.add(LearningRecord(
                    engagement_id=self.engagement_id,
                    resource_id=f'RS-R00{i}',
                    status='completed'
                ))
            db.session.commit()

            context = build_storyboard_context(self.engagement_id)

        # Bounds are preserved (existing open commitment + new open commitments + 10 completed).
        self.assertLessEqual(len(context['commitments']), 16)
        self.assertGreaterEqual(len(context['commitments']), 15)
        self.assertEqual(len(context['sessions']), 10)
        self.assertEqual(len(context['coaching_observations']), 1 + 5)  # 1 active + 5 resolved
        self.assertEqual(len(context['advisor_attention']), 0 + 5)  # no open + 5 resolved
        self.assertEqual(len(context['advisor_guidance']), 10)
        self.assertEqual(len(context['risks']), 1 + 10)  # 1 open + 10 resolved
        self.assertEqual(len(context['learning_records']), 10)

    def test_generate_storyboard_uses_compact_json_and_hides_engagement_id(self):
        mock_ai = MagicMock()
        mock_ai.generate_coaching_response.return_value = '## 1. Starting Situation\n\nTest.'

        with app.app_context():
            context = build_storyboard_context(self.engagement_id)
            generate_storyboard(context, ai_service=mock_ai)

        call_args = mock_ai.generate_coaching_response.call_args.kwargs
        user_content = call_args['messages'][0]['content']

        # Compact JSON: no spaces after separators.
        self.assertIn('","', user_content)
        self.assertNotIn('": ', user_content)

        # Internal engagement_id key is not exposed to the model prompt.
        self.assertNotIn('"engagement_id"', user_content)

    def test_generate_storyboard_calls_ai_service(self):
        mock_ai = MagicMock()
        mock_ai.generate_coaching_response.return_value = '## 1. Starting Situation\n\nTest storyboard.'

        context = {'client': {'first_name': 'Test'}, 'business': {'name': 'Test Biz'}}
        result = generate_storyboard(context, ai_service=mock_ai)

        self.assertEqual(result, '## 1. Starting Situation\n\nTest storyboard.')
        mock_ai.generate_coaching_response.assert_called_once()
        call_args = mock_ai.generate_coaching_response.call_args.kwargs
        self.assertIn('messages', call_args)
        self.assertIn('system_prompt', call_args)
        self.assertIn('Test Biz', call_args['messages'][0]['content'])

    def test_generate_storyboard_propagates_ai_error(self):
        mock_ai = MagicMock()
        mock_ai.generate_coaching_response.side_effect = AIServiceError('AI unavailable')

        context = {'client': {'first_name': 'Test'}, 'business': {'name': 'Test Biz'}}
        with self.assertRaises(AIServiceError):
            generate_storyboard(context, ai_service=mock_ai)


class TestStoryboardRoutes(unittest.TestCase):
    """Verify advisor authorization and route behavior for the Storyboard."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            self._create_test_data()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_test_data(self):
        # Advisor A
        advisor_a_user = User(email='advisor_a@test.com', role='ADVISOR', active=True)
        advisor_a_user.set_password('test123')
        db.session.add(advisor_a_user)
        db.session.flush()
        self.advisor_a = Advisor(user_id=advisor_a_user.id, first_name='Ronda', last_name='A')
        db.session.add(self.advisor_a)
        db.session.flush()

        # Advisor B
        advisor_b_user = User(email='advisor_b@test.com', role='ADVISOR', active=True)
        advisor_b_user.set_password('test123')
        db.session.add(advisor_b_user)
        db.session.flush()
        self.advisor_b = Advisor(user_id=advisor_b_user.id, first_name='Other', last_name='B')
        db.session.add(self.advisor_b)
        db.session.flush()

        # Client for Advisor A
        client_user = User(email='client_a@test.com', role='CLIENT', active=True)
        client_user.set_password('test123')
        db.session.add(client_user)
        db.session.flush()

        self.client_record = Client(user_id=client_user.id, first_name='Sarah', last_name='Bellamy')
        db.session.add(self.client_record)
        db.session.flush()

        self.business = Business(client_id=self.client_record.id, business_name="Sarah's Bakery")
        db.session.add(self.business)
        db.session.flush()

        self.engagement = Engagement(
            client_id=self.client_record.id,
            advisor_id=self.advisor_a.id,
            pathway_id='PATHWAY-001',
            pathway_version='0.1',
            status='active',
            start_date=date.today()
        )
        db.session.add(self.engagement)
        db.session.commit()
        self.engagement_id = self.engagement.id

    def test_advisor_can_access_storyboard(self):
        with app.app_context():
            self.client.post('/login', data={
                'email': 'advisor_a@test.com',
                'password': 'test123'
            })

            with patch('coaching.storyboard.AIService') as mock_service_class:
                mock_service = MagicMock()
                mock_service.generate_coaching_response.return_value = '## Generated Storyboard'
                mock_service_class.return_value = mock_service

                response = self.client.get(f'/advisor/client/{self.engagement_id}/storyboard')

        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Client Storyboard', data)
        self.assertIn('## Generated Storyboard', data)
        self.assertIn('Sarah&#39;s Bakery', data)

    def test_unauthorized_advisor_cannot_access_storyboard(self):
        with app.app_context():
            self.client.post('/login', data={
                'email': 'advisor_b@test.com',
                'password': 'test123'
            })

            response = self.client.get(f'/advisor/client/{self.engagement_id}/storyboard', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertNotIn('## Generated Storyboard', data)
        self.assertIn('Client not found or access denied.', data)

    def test_storyboard_ai_failure_is_safe(self):
        with app.app_context():
            self.client.post('/login', data={
                'email': 'advisor_a@test.com',
                'password': 'test123'
            })

            with patch('coaching.storyboard.AIService') as mock_service_class:
                mock_service = MagicMock()
                mock_service.generate_coaching_response.side_effect = AIServiceError('AI failure')
                mock_service_class.return_value = mock_service

                response = self.client.get(f'/advisor/client/{self.engagement_id}/storyboard', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Unable to generate Storyboard', data)

    def test_storyboard_route_does_not_mutate_data(self):
        with app.app_context():
            self.client.post('/login', data={
                'email': 'advisor_a@test.com',
                'password': 'test123'
            })

            with app.app_context():
                before_commitments = Commitment.query.count()

            with patch('coaching.storyboard.AIService') as mock_service_class:
                mock_service = MagicMock()
                mock_service.generate_coaching_response.return_value = '## Generated Storyboard'
                mock_service_class.return_value = mock_service

                self.client.get(f'/advisor/client/{self.engagement_id}/storyboard')

            with app.app_context():
                after_commitments = Commitment.query.count()

        self.assertEqual(before_commitments, after_commitments)


if __name__ == '__main__':
    unittest.main()

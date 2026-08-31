"""
WPP-PB-USER-001 — User Editing + Missing Business Safety

Regression coverage for:
- Admin editing an existing client/advisor
- Adding a Business record to an existing client
- Voice coaching initialization not failing when client.business is None
- Voice prompt remaining safe and not forcing a business context
"""

import unittest
import sys
import os
from datetime import date
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import app
from models import (
    db, User, Advisor, Client, Business, Engagement, PathwayState,
    InformationDomain, Pathway, AdvisorDomainAccess
)
from coaching.voice_service import VoiceService


class TestUserEditAndBusinessSafety(unittest.TestCase):
    """Edit user + missing-business resilience."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            self._create_seed_data()

    def tearDown(self):
        if self._old_api_key is not None:
            os.environ['ELEVENLABS_API_KEY'] = self._old_api_key
        else:
            os.environ.pop('ELEVENLABS_API_KEY', None)
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_seed_data(self):
        # Admin
        admin_user = User(email='admin@example.com', role='ADMIN', active=True)
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.flush()

        # Advisor for engagement (advisor_id is NOT NULL)
        advisor_user = User(email='advisor@example.com', role='ADVISOR', active=True)
        advisor_user.set_password('advisor123')
        db.session.add(advisor_user)
        db.session.flush()

        self.advisor = Advisor(user_id=advisor_user.id, first_name='Ronda', last_name='Advisor')
        db.session.add(self.advisor)
        db.session.flush()

        # Domain + runtime pathway
        sb_domain = InformationDomain(name='Small Business', status='active')
        db.session.add(sb_domain)
        db.session.flush()

        pathway = Pathway(
            pathway_id='PATHWAY-001',
            name='Recovery & Stabilization',
            status='active',
            domain_id=sb_domain.id,
            package_slug='recovery_stabilization'
        )
        db.session.add(pathway)

        # Client with Business
        client_user_a = User(email='sarah@example.com', role='CLIENT', active=True)
        client_user_a.set_password('client123')
        db.session.add(client_user_a)
        db.session.flush()

        self.client_a = Client(user_id=client_user_a.id, first_name='Sarah', last_name='Johnson')
        db.session.add(self.client_a)
        db.session.flush()

        self.business_a = Business(
            client_id=self.client_a.id,
            business_name="Sarah's Hardware",
            industry='Retail'
        )
        db.session.add(self.business_a)

        # Client without Business
        client_user_b = User(email='rick@example.com', role='CLIENT', active=True)
        client_user_b.set_password('client123')
        db.session.add(client_user_b)
        db.session.flush()

        self.client_b = Client(user_id=client_user_b.id, first_name='Rick', last_name='Practitioner')
        db.session.add(self.client_b)
        db.session.flush()

        # Engagement and pathway state for the business-less client
        self.engagement_b = Engagement(
            client_id=self.client_b.id,
            advisor_id=self.advisor.id,
            pathway_id='PATHWAY-001',
            pathway_version='0.1',
            status='active',
            start_date=date.today(),
            target_end_date=date.today()
        )
        db.session.add(self.engagement_b)
        db.session.flush()

        self.pathway_state_b = PathwayState(
            engagement_id=self.engagement_b.id,
            current_stage_id='RS-01',
            current_day=1
        )
        db.session.add(self.pathway_state_b)

        db.session.commit()

        self.admin_id = admin_user.id
        self.client_b_user_id = client_user_b.id
        self.client_b_id = self.client_b.id
        self.engagement_b_id = self.engagement_b.id

        # VoiceService requires an API key at construction
        self._old_api_key = os.environ.get('ELEVENLABS_API_KEY')
        os.environ['ELEVENLABS_API_KEY'] = 'test-key'

    def _login_admin(self):
        return self.client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'admin123'
        }, follow_redirects=True)

    def _login_client_b(self):
        return self.client.post('/login', data={
            'email': 'rick@example.com',
            'password': 'client123'
        }, follow_redirects=True)

    def test_admin_user_edit_page_loads(self):
        self._login_admin()
        response = self.client.get(f'/admin/users/{self.client_b_user_id}/edit')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Edit User', html)
        self.assertIn('rick@example.com', html)

    def test_admin_edits_client_preserves_id_and_engagement(self):
        self._login_admin()
        response = self.client.post(f'/admin/users/{self.client_b_user_id}/edit', data={
            'email': 'rick.professional@example.com',
            'first_name': 'Rick',
            'last_name': 'Daniell',
            'business_name': 'Senior Change Leadership Practice'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        with app.app_context():
            user = User.query.get(self.client_b_user_id)
            self.assertEqual(user.email, 'rick.professional@example.com')
            self.assertEqual(user.id, self.client_b_user_id)

            client = Client.query.get(self.client_b_id)
            self.assertEqual(client.first_name, 'Rick')
            self.assertEqual(client.last_name, 'Daniell')

            business = client.business
            self.assertIsNotNone(business)
            self.assertEqual(business.business_name, 'Senior Change Leadership Practice')

            engagement = Engagement.query.get(self.engagement_b_id)
            self.assertIsNotNone(engagement)
            self.assertEqual(engagement.client_id, self.client_b_id)

    def test_edit_prevents_duplicate_email(self):
        self._login_admin()
        response = self.client.post(f'/admin/users/{self.client_b_user_id}/edit', data={
            'email': 'sarah@example.com',
            'first_name': 'Rick',
            'last_name': 'Practitioner',
            'business_name': ''
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('A user with that email already exists', html)

    def test_voice_session_init_with_missing_business(self):
        """Missing client.business must not raise AttributeError."""
        self._login_client_b()

        mock_voice = mock.MagicMock()
        mock_voice.generate_signed_url.return_value = {'signed_url': 'https://example.com/signed'}
        mock_voice.build_session_config.return_value = {
            'agent_id': 'agent_123',
            'user_id': str(self.client_b_user_id),
            'session_metadata': {}
        }

        with mock.patch('app.get_voice_service', return_value=mock_voice):
            response = self.client.post(f'/voice/session/init/{self.engagement_b_id}')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('session_id', data)

    def test_voice_prompt_safe_without_business(self):
        service = VoiceService(agent_id='agent_123')
        prompt = service._build_agent_prompt(
            client_name='Rick',
            business_name='',
            pathway_name='Senior Change Leadership',
            current_stage='SCL-01',
            current_day=1,
            pathway_context='',
            coaching_context=''
        )
        self.assertIn('supporting Rick.', prompt)
        self.assertNotIn('who owns', prompt)

    def test_voice_prompt_with_business(self):
        service = VoiceService(agent_id='agent_123')
        prompt = service._build_agent_prompt(
            client_name='Sarah',
            business_name="Sarah's Hardware",
            pathway_name='Recovery & Stabilization',
            current_stage='RS-01',
            current_day=1,
            pathway_context='',
            coaching_context=''
        )
        self.assertIn("supporting Sarah who owns Sarah's Hardware", prompt)


if __name__ == '__main__':
    unittest.main()

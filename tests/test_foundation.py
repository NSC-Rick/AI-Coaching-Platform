import unittest
import sys
import os
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, User, Advisor, Client, Business, Engagement, PathwayState, Commitment, AdvisorGuidance
from coaching import load_pathway, validate_pathway, build_coaching_context

class TestPathwayLoader(unittest.TestCase):
    
    def test_load_pathway_001(self):
        pathway_data = load_pathway('PATHWAY-001')
        
        self.assertIsNotNone(pathway_data)
        self.assertIn('manifest', pathway_data)
        
        manifest = pathway_data['manifest']
        self.assertEqual(manifest['pathway_id'], 'PATHWAY-001')
        self.assertEqual(manifest['name'], 'Recovery & Stabilization')
        self.assertEqual(manifest['version'], '0.1')
        self.assertIn('stages', manifest)
        self.assertEqual(len(manifest['stages']), 3)
    
    def test_pathway_validation(self):
        pathway_data = load_pathway('PATHWAY-001')
        
        result = validate_pathway(pathway_data)
        self.assertTrue(result)
    
    def test_invalid_pathway_id(self):
        with self.assertRaises(Exception):
            load_pathway('INVALID-PATHWAY')
    
    def test_pathway_stages(self):
        pathway_data = load_pathway('PATHWAY-001')
        stages = pathway_data['manifest']['stages']
        
        stage_ids = [s['stage_id'] for s in stages]
        self.assertIn('RS-01', stage_ids)
        self.assertIn('RS-02', stage_ids)
        self.assertIn('RS-03', stage_ids)
        
        self.assertEqual(len(stage_ids), len(set(stage_ids)))

class TestClientIsolation(unittest.TestCase):
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
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
        
        advisor = Advisor(user_id=advisor_user.id, first_name='Test', last_name='Advisor')
        db.session.add(advisor)
        db.session.flush()
        
        client_a_user = User(email='clienta@test.com', role='CLIENT', active=True)
        client_a_user.set_password('test123')
        db.session.add(client_a_user)
        db.session.flush()
        
        client_a = Client(user_id=client_a_user.id, first_name='Client', last_name='A')
        db.session.add(client_a)
        db.session.flush()
        
        business_a = Business(
            client_id=client_a.id,
            business_name='Business A',
            current_situation_summary='Client A situation'
        )
        db.session.add(business_a)
        
        engagement_a = Engagement(
            client_id=client_a.id,
            advisor_id=advisor.id,
            pathway_id='PATHWAY-001',
            pathway_version='0.1',
            status='active',
            start_date=date.today()
        )
        db.session.add(engagement_a)
        db.session.flush()
        
        pathway_state_a = PathwayState(
            engagement_id=engagement_a.id,
            current_stage_id='RS-01',
            current_day=10,
            current_focus='Client A focus'
        )
        db.session.add(pathway_state_a)
        
        client_b_user = User(email='clientb@test.com', role='CLIENT', active=True)
        client_b_user.set_password('test123')
        db.session.add(client_b_user)
        db.session.flush()
        
        client_b = Client(user_id=client_b_user.id, first_name='Client', last_name='B')
        db.session.add(client_b)
        db.session.flush()
        
        business_b = Business(
            client_id=client_b.id,
            business_name='Business B',
            current_situation_summary='Client B situation'
        )
        db.session.add(business_b)
        
        engagement_b = Engagement(
            client_id=client_b.id,
            advisor_id=advisor.id,
            pathway_id='PATHWAY-001',
            pathway_version='0.1',
            status='active',
            start_date=date.today()
        )
        db.session.add(engagement_b)
        db.session.flush()
        
        pathway_state_b = PathwayState(
            engagement_id=engagement_b.id,
            current_stage_id='RS-02',
            current_day=35,
            current_focus='Client B focus'
        )
        db.session.add(pathway_state_b)
        
        db.session.commit()
        
        self.client_a_id = client_a.id
        self.client_b_id = client_b.id
        self.engagement_a_id = engagement_a.id
        self.engagement_b_id = engagement_b.id
    
    def test_client_a_cannot_access_client_b(self):
        with self.client:
            self.client.post('/login', data={
                'email': 'clienta@test.com',
                'password': 'test123'
            })
            
            response = self.client.get('/client/home')
            self.assertEqual(response.status_code, 200)
            
            data = response.get_data(as_text=True)
            self.assertIn('Business A', data)
            self.assertNotIn('Business B', data)
            self.assertIn('Client A focus', data)
            self.assertNotIn('Client B focus', data)
    
    def test_advisor_can_access_assigned_clients(self):
        with self.client:
            self.client.post('/login', data={
                'email': 'advisor@test.com',
                'password': 'test123'
            })
            
            response = self.client.get('/advisor/home')
            self.assertEqual(response.status_code, 200)
            
            data = response.get_data(as_text=True)
            self.assertIn('Business A', data)
            self.assertIn('Business B', data)

class TestContextBuilder(unittest.TestCase):
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        
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
        
        commitment = Commitment(
            engagement_id=engagement.id,
            description='Test commitment',
            status='open',
            priority='high'
        )
        db.session.add(commitment)
        
        guidance = AdvisorGuidance(
            engagement_id=engagement.id,
            advisor_id=advisor.id,
            guidance='Test guidance',
            status='active'
        )
        db.session.add(guidance)
        
        db.session.commit()
        
        self.engagement_id = engagement.id
    
    def test_context_builder_returns_correct_data(self):
        with app.app_context():
            context = build_coaching_context(self.engagement_id)
            
            self.assertIsNotNone(context)
            self.assertEqual(context['client']['name'], 'Test Client')
            self.assertEqual(context['business']['name'], 'Test Business')
            self.assertEqual(context['pathway']['id'], 'PATHWAY-001')
            self.assertEqual(context['current_state']['stage_id'], 'RS-01')
            self.assertEqual(context['current_state']['current_day'], 15)
            self.assertEqual(len(context['open_commitments']), 1)
            self.assertIsNotNone(context['advisor_guidance'])
            self.assertEqual(context['advisor_guidance']['guidance'], 'Test guidance')
    
    def test_context_only_includes_authorized_client_data(self):
        with app.app_context():
            context = build_coaching_context(self.engagement_id)
            
            self.assertEqual(context['business']['name'], 'Test Business')
            self.assertEqual(context['business']['current_situation'], 'Test situation')

class TestAdvisorGuidance(unittest.TestCase):
    
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
            business_name='Test Business'
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
        
        db.session.commit()
        
        self.engagement_id = engagement.id
    
    def test_advisor_can_add_guidance(self):
        with self.client:
            self.client.post('/login', data={
                'email': 'advisor@test.com',
                'password': 'test123'
            })
            
            response = self.client.post(f'/advisor/client/{self.engagement_id}/add_guidance', data={
                'guidance': 'Focus on cash flow',
                'priority': 'high'
            }, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            
            with app.app_context():
                guidance = AdvisorGuidance.query.filter_by(
                    engagement_id=self.engagement_id
                ).first()
                
                self.assertIsNotNone(guidance)
                self.assertEqual(guidance.guidance, 'Focus on cash flow')
                self.assertEqual(guidance.priority, 'high')
    
    def test_guidance_appears_in_context(self):
        with app.app_context():
            advisor = Advisor.query.first()
            
            guidance = AdvisorGuidance(
                engagement_id=self.engagement_id,
                advisor_id=advisor.id,
                guidance='Test guidance for context',
                status='active'
            )
            db.session.add(guidance)
            db.session.commit()
            
            context = build_coaching_context(self.engagement_id)
            
            self.assertIsNotNone(context['advisor_guidance'])
            self.assertEqual(context['advisor_guidance']['guidance'], 'Test guidance for context')

class TestCoreRoutes(unittest.TestCase):
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_login_page_renders(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
    
    def test_index_redirects_to_login(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)

if __name__ == '__main__':
    unittest.main()

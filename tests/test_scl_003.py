"""
WPP-SCL-003: Advisor domain access and Senior Change Leadership pilot enrollment.

Verifies the existing PB assignment workflow can support a second information
domain (Change Management) and the Senior Change Leadership pathway via a
reusable advisor-domain access mechanism, while preserving existing Small
Business behavior.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Use an in-memory database so the test does not depend on the data/ directory.
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import app
from models import (
    db, User, Advisor, Client, Business, Engagement, PathwayState,
    InformationDomain, Pathway, AdvisorDomainAccess
)


class TestSCL003AssignmentFlow(unittest.TestCase):
    """Validate domain/pathway catalog and advisor assignment flow."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            self._create_seed_data()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_seed_data(self):
        # Admin
        admin_user = User(email='admin@example.com', role='ADMIN', active=True)
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.flush()

        # Small Business domain and pathway
        sb_domain = InformationDomain(
            name='Small Business',
            description='Small business coaching',
            status='active'
        )
        db.session.add(sb_domain)
        db.session.flush()

        sb_pathway = Pathway(
            pathway_id='PATHWAY-001',
            name='Stabilization and Recovery',
            description='Small Business recovery pathway',
            status='active',
            domain_id=sb_domain.id,
            package_slug='recovery_stabilization'
        )
        db.session.add(sb_pathway)

        # Organizational Change Management domain and pathways
        cm_domain = InformationDomain(
            name='Organizational Change Management',
            description='Organizational Change Management professional development',
            status='active'
        )
        db.session.add(cm_domain)
        db.session.flush()

        scl_pathway = Pathway(
            pathway_id='PATHWAY-002',
            name='Senior Change Leadership',
            description='Senior Change Leadership pathway',
            status='active',
            domain_id=cm_domain.id,
            package_slug='senior_change_leadership'
        )
        db.session.add(scl_pathway)

        # Catalog-only OCM concepts (no runtime package)
        for cm_id in ['CM-001', 'CM-002', 'CM-003']:
            db.session.add(Pathway(
                pathway_id=cm_id,
                name=f'OCM Pathway {cm_id}',
                description='Catalog-only OCM pathway concept',
                status='active',
                domain_id=cm_domain.id,
                package_slug=None
            ))

        db.session.flush()

        # Advisor Ronda — legacy Small Business access
        ronda_user = User(email='ronda@example.com', role='ADVISOR', active=True)
        ronda_user.set_password('advisor123')
        db.session.add(ronda_user)
        db.session.flush()

        ronda = Advisor(user_id=ronda_user.id, first_name='Ronda', last_name='Advisor')
        db.session.add(ronda)
        db.session.flush()

        ronda_sb = AdvisorDomainAccess(advisor_id=ronda.id, domain_id=sb_domain.id)
        db.session.add(ronda_sb)

        # Advisor Rick — Change Management access
        rick_user = User(email='rick.daniell@example.com', role='ADVISOR', active=True)
        rick_user.set_password('advisor123')
        db.session.add(rick_user)
        db.session.flush()

        rick = Advisor(user_id=rick_user.id, first_name='Rick', last_name='Daniell')
        db.session.add(rick)
        db.session.flush()

        rick_cm = AdvisorDomainAccess(advisor_id=rick.id, domain_id=cm_domain.id)
        db.session.add(rick_cm)

        # Client coachee Rick
        client_user = User(email='rick@example.com', role='CLIENT', active=True)
        client_user.set_password('client123')
        db.session.add(client_user)
        db.session.flush()

        client = Client(user_id=client_user.id, first_name='Rick', last_name='Practitioner')
        db.session.add(client)
        db.session.flush()

        business = Business(
            client_id=client.id,
            business_name='Senior Change Leadership Practice',
            industry='Professional Services'
        )
        db.session.add(business)

        db.session.commit()

        self.ronda_id = ronda.id
        self.rick_id = rick.id
        self.client_id = client.id
        self.cm_domain_id = cm_domain.id
        self.sb_domain_id = sb_domain.id

    def _login_admin(self):
        return self.client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'admin123'
        }, follow_redirects=True)

    def test_change_management_domain_exists(self):
        with app.app_context():
            domain = InformationDomain.query.filter_by(name='Organizational Change Management').first()
            self.assertIsNotNone(domain)
            self.assertEqual(domain.status, 'active')

    def test_senior_change_leadership_pathway_eligible(self):
        with app.app_context():
            pathway = Pathway.query.filter_by(pathway_id='PATHWAY-002').first()
            self.assertIsNotNone(pathway)
            self.assertEqual(pathway.name, 'Senior Change Leadership')
            self.assertEqual(pathway.domain.name, 'Organizational Change Management')
            self.assertEqual(pathway.status, 'active')

    def test_advisor_rick_has_change_management_access(self):
        with app.app_context():
            rick = Advisor.query.filter_by(first_name='Rick', last_name='Daniell').first()
            self.assertIsNotNone(rick)
            domain_names = [a.domain.name for a in rick.domain_access]
            self.assertIn('Organizational Change Management', domain_names)

    def test_get_defaults_to_first_advisor_and_shows_their_eligible_pathways(self):
        self._login_admin()
        response = self.client.get(f'/admin/assignments/new/{self.client_id}')
        self.assertEqual(response.status_code, 200)

        html = response.get_data(as_text=True)
        # Ronda is the first advisor and has Small Business access
        self.assertIn('Stabilization and Recovery', html)
        self.assertNotIn('Senior Change Leadership', html)

    def test_advisor_rick_dropdown_shows_senior_change_leadership(self):
        self._login_admin()
        # POST with Rick but no pathway triggers a re-render with Rick's eligible pathways
        response = self.client.post(f'/admin/assignments/new/{self.client_id}', data={
            'advisor_id': self.rick_id,
            'pathway_id': ''
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        html = response.get_data(as_text=True)
        self.assertIn('Senior Change Leadership', html)
        self.assertNotIn('Stabilization and Recovery', html)

    def test_admin_can_assign_senior_change_leadership_to_rick(self):
        self._login_admin()

        response = self.client.post(f'/admin/assignments/new/{self.client_id}', data={
            'advisor_id': self.rick_id,
            'pathway_id': 'PATHWAY-002'
        }, follow_redirects=False)

        # Successful creation redirects to admin_assignments
        self.assertEqual(response.status_code, 302)

        with app.app_context():
            engagement = Engagement.query.filter_by(
                client_id=self.client_id,
                advisor_id=self.rick_id,
                pathway_id='PATHWAY-002'
            ).first()
            self.assertIsNotNone(engagement)
            self.assertEqual(engagement.pathway_version, '0.1')
            self.assertEqual(engagement.status, 'active')

            state = engagement.pathway_state
            self.assertIsNotNone(state)
            self.assertEqual(state.current_stage_id, 'SCL-01')
            self.assertEqual(state.current_day, 1)

    def test_admin_cannot_assign_scl_to_advisor_without_cm_access(self):
        self._login_admin()

        response = self.client.post(f'/admin/assignments/new/{self.client_id}', data={
            'advisor_id': self.ronda_id,
            'pathway_id': 'PATHWAY-002'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        with app.app_context():
            engagement = Engagement.query.filter_by(
                client_id=self.client_id,
                advisor_id=self.ronda_id,
                pathway_id='PATHWAY-002'
            ).first()
            self.assertIsNone(engagement)

    def test_existing_small_business_assignment_still_works(self):
        # Create a second client for Small Business
        with app.app_context():
            client_user = User(email='sarah@example.com', role='CLIENT', active=True)
            client_user.set_password('client123')
            db.session.add(client_user)
            db.session.flush()

            client = Client(user_id=client_user.id, first_name='Sarah', last_name='Smith')
            db.session.add(client)
            db.session.flush()

            business = Business(client_id=client.id, business_name="Sarah's Hardware")
            db.session.add(business)
            db.session.commit()

            sarah_id = client.id

        self._login_admin()

        response = self.client.post(f'/admin/assignments/new/{sarah_id}', data={
            'advisor_id': self.ronda_id,
            'pathway_id': 'PATHWAY-001'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        with app.app_context():
            engagement = Engagement.query.filter_by(
                client_id=sarah_id,
                pathway_id='PATHWAY-001'
            ).first()
            self.assertIsNotNone(engagement)
            self.assertEqual(engagement.pathway_state.current_stage_id, 'RS-01')

    def test_advisor_without_access_can_still_see_allowed_small_business(self):
        self._login_admin()

        # Ronda has Small Business access but not Change Management.
        # POST PATHWAY-002 for Ronda should fail and re-render the form,
        # showing only the pathways her domains allow.
        response = self.client.post(f'/admin/assignments/new/{self.client_id}', data={
            'advisor_id': self.ronda_id,
            'pathway_id': 'PATHWAY-002'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)
        self.assertIn('Stabilization and Recovery', html)
        self.assertNotIn('Senior Change Leadership', html)

    def test_catalog_cm_001_not_runtime_ready(self):
        from coaching.engine import is_pathway_runtime_ready

        self.assertFalse(is_pathway_runtime_ready('CM-001'))
        self.assertFalse(is_pathway_runtime_ready('CM-002'))
        self.assertFalse(is_pathway_runtime_ready('CM-003'))

    def test_senior_change_leadership_runtime_ready(self):
        from coaching.engine import is_pathway_runtime_ready

        self.assertTrue(is_pathway_runtime_ready('PATHWAY-002'))
        self.assertTrue(is_pathway_runtime_ready('PATHWAY-001'))

    def test_no_duplicate_change_management_domain(self):
        with app.app_context():
            ocm = InformationDomain.query.filter_by(name='Organizational Change Management').first()
            duplicate = InformationDomain.query.filter_by(name='Change Management').first()
            self.assertIsNotNone(ocm)
            self.assertIsNone(duplicate)

    def test_assignment_dropdown_excludes_catalog_only_ocm_pathways(self):
        self._login_admin()

        # Rick has OCM access. POST with no pathway re-renders with Rick's eligible pathways.
        # Only PATHWAY-002 should appear because CM-001/002/003 have no runtime package.
        response = self.client.post(f'/admin/assignments/new/{self.client_id}', data={
            'advisor_id': self.rick_id,
            'pathway_id': ''
        }, follow_redirects=True)

        html = response.get_data(as_text=True)

        self.assertIn('Senior Change Leadership', html)
        self.assertNotIn('OCM Pathway CM-001', html)
        self.assertNotIn('OCM Pathway CM-002', html)
        self.assertNotIn('OCM Pathway CM-003', html)

    def test_crafted_post_for_cm_001_is_rejected(self):
        self._login_admin()

        response = self.client.post(f'/admin/assignments/new/{self.client_id}', data={
            'advisor_id': self.rick_id,
            'pathway_id': 'CM-001'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        with app.app_context():
            engagement = Engagement.query.filter_by(
                pathway_id='CM-001'
            ).first()
            self.assertIsNone(engagement)


class TestSCL003RuntimeCompatibility(unittest.TestCase):
    """Ensure pathway runtime still loads the new package."""

    def test_senior_change_leadership_package_loads(self):
        from coaching.engine import load_pathway
        pathway_data = load_pathway('PATHWAY-002')

        self.assertEqual(pathway_data['manifest']['pathway_id'], 'PATHWAY-002')
        self.assertEqual(len(pathway_data['manifest']['stages']), 6)
        self.assertEqual(pathway_data['manifest']['domain'], 'Organizational Change Management')

    def test_recovery_stabilization_package_loads(self):
        from coaching.engine import load_pathway
        pathway_data = load_pathway('PATHWAY-001')

        self.assertEqual(pathway_data['manifest']['pathway_id'], 'PATHWAY-001')
        self.assertEqual(len(pathway_data['manifest']['stages']), 3)


if __name__ == '__main__':
    unittest.main()

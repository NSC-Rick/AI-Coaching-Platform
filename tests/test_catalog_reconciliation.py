"""
Tests for catalog_reconciliation.py (WPP-SCL-003.3A).

Verifies that the runtime-ready pathway catalog can be reconciled safely and
idempotently against an existing PostgreSQL-like catalog without deleting or
recreating unrelated records.
"""

import unittest
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import app
from models import (
    db, User, Advisor, Client, Business, Engagement, PathwayState,
    InformationDomain, Pathway, AdvisorDomainAccess
)
from coaching.engine import load_pathway, is_pathway_runtime_ready
from catalog_reconciliation import (
    reconcile_catalog,
    reconcile_advisor_access,
    AmbiguousDomainError
)


class TestCatalogReconciliation(unittest.TestCase):
    """Safe, idempotent runtime catalog reconciliation."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        with app.app_context():
            db.create_all()
            self._create_existing_catalog()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_existing_catalog(self):
        """Create a production-like catalog that is missing PATHWAY-001/002."""
        sb_domain = InformationDomain(
            name='Small Business',
            description='Small business coaching',
            status='active'
        )
        db.session.add(sb_domain)
        db.session.flush()

        self.sb_001 = Pathway(
            pathway_id='SB-001',
            name='Small Business Coaching',
            description='Legacy SB catalog pathway',
            status='active',
            domain_id=sb_domain.id,
            package_slug=None
        )
        db.session.add(self.sb_001)

        cm_domain = InformationDomain(
            name='Change Management',
            description='Legacy CM domain',
            status='active'
        )
        db.session.add(cm_domain)
        db.session.flush()

        for cm_id in ['CM-001', 'CM-002', 'CM-003']:
            db.session.add(Pathway(
                pathway_id=cm_id,
                name=f'OCM Concept {cm_id}',
                description='Catalog-only OCM pathway concept',
                status='active',
                domain_id=cm_domain.id,
                package_slug=None
            ))

        # Advisor Rick with no domain access (matches deployed finding)
        rick_user = User(
            email='rick.daniell@example.com',
            role='ADVISOR',
            active=True
        )
        rick_user.set_password('advisor123')
        db.session.add(rick_user)
        db.session.flush()

        self.rick = Advisor(
            user_id=rick_user.id,
            first_name='Rick',
            last_name='Daniell'
        )
        db.session.add(self.rick)
        db.session.flush()

        # Existing client and engagement should not be touched
        client_user = User(email='sarah@example.com', role='CLIENT', active=True)
        client_user.set_password('client123')
        db.session.add(client_user)
        db.session.flush()

        self.client = Client(
            user_id=client_user.id,
            first_name='Sarah',
            last_name='Johnson'
        )
        db.session.add(self.client)
        db.session.flush()

        business = Business(
            client_id=self.client.id,
            business_name="Sarah's Hardware",
            industry='Retail'
        )
        db.session.add(business)
        db.session.flush()

        self.engagement = Engagement(
            client_id=self.client.id,
            advisor_id=self.rick.id,
            pathway_id='CM-001',
            pathway_version='0.1',
            status='active',
            start_date=date(2026, 1, 1),
            target_end_date=date(2026, 3, 31)
        )
        db.session.add(self.engagement)
        db.session.flush()

        self.pathway_state = PathwayState(
            engagement_id=self.engagement.id,
            current_stage_id='CM-01',
            current_day=1
        )
        db.session.add(self.pathway_state)

        db.session.commit()

        # Store IDs only; instances will be detached in the test context.
        self.rick_id = self.rick.id
        self.client_id = self.client.id
        self.engagement_id = self.engagement.id
        self.pathway_state_id = self.pathway_state.id
        self.sb_001_id = self.sb_001.id

    def test_reconcile_creates_runtime_pathways_and_renames_legacy_cm_domain(self):
        with app.app_context():
            reconcile_catalog(db, load_pathway)
            db.session.commit()

            # Legacy CM domain renamed to canonical OCM
            ocm = InformationDomain.query.filter_by(
                name='Organizational Change Management'
            ).first()
            self.assertIsNotNone(ocm)
            self.assertEqual(ocm.status, 'active')

            # PATHWAY-001 and PATHWAY-002 now exist
            p1 = Pathway.query.filter_by(pathway_id='PATHWAY-001').first()
            p2 = Pathway.query.filter_by(pathway_id='PATHWAY-002').first()
            self.assertIsNotNone(p1)
            self.assertIsNotNone(p2)

            sb = InformationDomain.query.filter_by(name='Small Business').first()
            self.assertIsNotNone(sb)
            self.assertEqual(p1.domain_id, sb.id)
            self.assertEqual(p2.domain_id, ocm.id)

            self.assertTrue(is_pathway_runtime_ready(p1.pathway_id))
            self.assertTrue(is_pathway_runtime_ready(p2.pathway_id))

    def test_existing_catalog_pathways_preserved(self):
        with app.app_context():
            reconcile_catalog(db, load_pathway)
            db.session.commit()

            self.assertIsNotNone(
                Pathway.query.filter_by(pathway_id='SB-001').first()
            )
            for cm_id in ['CM-001', 'CM-002', 'CM-003']:
                p = Pathway.query.filter_by(pathway_id=cm_id).first()
                self.assertIsNotNone(p)
                self.assertEqual(p.status, 'active')

    def test_existing_engagement_and_pathway_state_preserved(self):
        with app.app_context():
            reconcile_catalog(db, load_pathway)
            reconcile_advisor_access(db)
            db.session.commit()

            engagement = Engagement.query.get(self.engagement_id)
            self.assertIsNotNone(engagement)
            self.assertEqual(engagement.pathway_id, 'CM-001')

            state = PathwayState.query.get(self.pathway_state_id)
            self.assertIsNotNone(state)
            self.assertEqual(state.current_stage_id, 'CM-01')

    def test_reconcile_advisor_access_grants_rick_ocm_access(self):
        with app.app_context():
            reconcile_catalog(db, load_pathway)
            reconcile_advisor_access(db)
            db.session.commit()

            access = AdvisorDomainAccess.query.filter_by(
                advisor_id=self.rick_id
            ).all()
            domain_names = [a.domain.name for a in access]
            self.assertIn('Organizational Change Management', domain_names)

    def test_idempotent_second_run_creates_no_duplicates(self):
        with app.app_context():
            reconcile_catalog(db, load_pathway)
            reconcile_advisor_access(db)
            db.session.commit()

            # Second run
            reconcile_catalog(db, load_pathway)
            reconcile_advisor_access(db)
            db.session.commit()

            self.assertEqual(
                Pathway.query.filter_by(pathway_id='PATHWAY-001').count(), 1
            )
            self.assertEqual(
                Pathway.query.filter_by(pathway_id='PATHWAY-002').count(), 1
            )
            self.assertEqual(
                InformationDomain.query.filter_by(
                    name='Organizational Change Management'
                ).count(), 1
            )
            self.assertEqual(
                InformationDomain.query.filter_by(name='Small Business').count(), 1
            )
            self.assertEqual(
                AdvisorDomainAccess.query.filter_by(advisor_id=self.rick_id).count(),
                1
            )

    def test_ambiguous_ocm_and_cm_domains_raises(self):
        with app.app_context():
            # Add a canonical OCM domain alongside the legacy CM domain
            ocm = InformationDomain(
                name='Organizational Change Management',
                status='active'
            )
            db.session.add(ocm)
            db.session.commit()

            with self.assertRaises(AmbiguousDomainError):
                reconcile_catalog(db, load_pathway)


if __name__ == '__main__':
    unittest.main()

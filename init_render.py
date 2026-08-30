#!/usr/bin/env python
"""
Render Deployment Initialization Script

This script safely initializes the database for Render Free deployments
where shell access is not available.

Safety Features:
- Creates tables only if they don't exist
- Seeds data only if database is empty
- Safe to run repeatedly without duplicating data
- Does NOT drop tables or delete existing data

Usage:
    python init_render.py

This is automatically run during Render build via:
    pip install -r requirements.txt && python init_render.py
"""

import os
import sys
from datetime import date, datetime, timedelta

def init_render_database():
    """
    Initialize database for Render deployment.
    Creates tables and seeds initial data if needed.
    """
    print("=" * 60)
    print("RENDER DATABASE INITIALIZATION")
    print("=" * 60)
    print()
    
    # Import app and models within function to ensure proper context
    from app import app, db
    from coaching.engine import load_pathway
    from models import (
        User, Advisor, Client, Business, Engagement, PathwayState,
        Commitment, Risk, SignificantEvent, LearningRecord,
        CoachingObservation, Session, AdvisorGuidance, AdvisorAttention,
        InformationDomain, Pathway, AdvisorDomainAccess
    )
    
    with app.app_context():
        # Step 1: Create tables if they don't exist
        print("Step 1: Creating database tables...")
        try:
            db.create_all()
            print("✓ Database tables created/verified")
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            return False
        
        # Step 2: Check if database already has data
        print()
        print("Step 2: Checking for existing data...")
        
        try:
            user_count = User.query.count()
            print(f"  Found {user_count} users in database")
            
            if user_count > 0:
                print()
                print("✓ Database already contains data")
                print("  Skipping seed data to avoid duplicates")
                print()
                print("=" * 60)
                print("INITIALIZATION COMPLETE (existing data preserved)")
                print("=" * 60)
                return True
            
            print("  Database is empty - proceeding with seed data")
            
        except Exception as e:
            print(f"✗ Error checking existing data: {e}")
            return False
        
        # Step 3: Seed initial PoC data
        print()
        print("Step 3: Seeding PoC test data...")
        
        try:
            # Seed Information Domains and Pathway catalog
            small_biz_domain = InformationDomain(
                name='Small Business',
                description='Small business coaching and recovery pathways',
                status='active'
            )
            db.session.add(small_biz_domain)
            db.session.flush()
            
            change_mgmt_domain = InformationDomain(
                name='Change Management',
                description='Professional development pathways for Change Management practitioners',
                status='active'
            )
            db.session.add(change_mgmt_domain)
            db.session.flush()
            
            sb_pathway = Pathway(
                pathway_id='PATHWAY-001',
                name='Stabilization and Recovery',
                description='Small business stabilization and recovery plan',
                status='active',
                domain_id=small_biz_domain.id,
                package_slug='recovery_stabilization'
            )
            db.session.add(sb_pathway)
            
            cm_pathway = Pathway(
                pathway_id='PATHWAY-002',
                name='Senior Change Leadership',
                description='Senior Change Leadership professional development pathway',
                status='active',
                domain_id=change_mgmt_domain.id,
                package_slug='senior_change_leadership'
            )
            db.session.add(cm_pathway)
            db.session.flush()
            
            print("  ✓ Seeded Information Domains and Pathways")
            
            # Create Advisor User
            advisor_user = User(
                email='ronda@example.com',
                role='ADVISOR',
                active=True
            )
            advisor_user.set_password('advisor123')
            db.session.add(advisor_user)
            db.session.flush()
            
            advisor = Advisor(
                user_id=advisor_user.id,
                first_name='Ronda',
                last_name='Advisor'
            )
            db.session.add(advisor)
            db.session.flush()
            print("  ✓ Created advisor: ronda@example.com")
            
            # Create Client A (Sarah)
            client_a_user = User(
                email='sarah@example.com',
                role='CLIENT',
                active=True
            )
            client_a_user.set_password('client123')
            db.session.add(client_a_user)
            db.session.flush()
            
            client_a = Client(
                user_id=client_a_user.id,
                first_name='Sarah',
                last_name='Johnson'
            )
            db.session.add(client_a)
            db.session.flush()
            
            business_a = Business(
                client_id=client_a.id,
                business_name="Sarah's Hardware",
                industry='Retail',
                business_description='Local hardware store serving the community for 15 years',
                current_situation_summary='Experiencing cash flow challenges following recent market changes. Working on stabilization plan.'
            )
            db.session.add(business_a)
            
            engagement_a = Engagement(
                client_id=client_a.id,
                advisor_id=advisor.id,
                pathway_id='PATHWAY-001',
                pathway_version='0.1',
                status='active',
                start_date=date.today() - timedelta(days=18),
                target_end_date=date.today() + timedelta(days=72)
            )
            db.session.add(engagement_a)
            db.session.flush()
            
            pathway_state_a = PathwayState(
                engagement_id=engagement_a.id,
                current_stage_id='RS-01',
                current_day=18,
                current_focus='Short-term liquidity and cash visibility',
                current_priority_summary='Maintain 14-day cash visibility, complete lender preparation, continue customer outreach'
            )
            db.session.add(pathway_state_a)
            
            commitment_a1 = Commitment(
                engagement_id=engagement_a.id,
                description='Contact lender to discuss payment modification',
                due_date=date.today() - timedelta(days=2),
                status='open',
                priority='high'
            )
            db.session.add(commitment_a1)
            
            commitment_a2 = Commitment(
                engagement_id=engagement_a.id,
                description='Update 14-day cash tracker',
                due_date=date.today() + timedelta(days=2),
                status='open',
                priority='high'
            )
            db.session.add(commitment_a2)
            
            commitment_a3 = Commitment(
                engagement_id=engagement_a.id,
                description='Contact five inactive customers',
                status='open',
                priority='normal'
            )
            db.session.add(commitment_a3)
            
            risk_a1 = Risk(
                engagement_id=engagement_a.id,
                title='Johnson account lost',
                description='Major customer Johnson account was lost. Estimated revenue impact: $4,000/month',
                severity='high',
                status='open',
                advisor_attention=True
            )
            db.session.add(risk_a1)
            
            risk_a2 = Risk(
                engagement_id=engagement_a.id,
                title='Lender contact delayed',
                description='Client has postponed lender discussion twice',
                severity='moderate',
                status='open',
                advisor_attention=False
            )
            db.session.add(risk_a2)
            
            event_a1 = SignificantEvent(
                engagement_id=engagement_a.id,
                title='Lost Johnson account',
                description='Johnson account decided to switch to online supplier',
                event_date=date.today() - timedelta(days=5),
                estimated_impact='$4,000/month revenue reduction'
            )
            db.session.add(event_a1)
            
            learning_a1 = LearningRecord(
                engagement_id=engagement_a.id,
                resource_id='RS-R001',
                status='completed',
                recommended_at=datetime.utcnow() - timedelta(days=7),
                completed_at=datetime.utcnow() - timedelta(days=6),
                client_reflection='Now I understand why we can be profitable but still have cash problems',
                follow_up_required=False
            )
            db.session.add(learning_a1)
            
            observation_a1 = CoachingObservation(
                engagement_id=engagement_a.id,
                observation='Client is consistently completing operational tasks but avoiding lender outreach',
                importance='high',
                status='active'
            )
            db.session.add(observation_a1)
            
            session_a1 = Session(
                engagement_id=engagement_a.id,
                started_at=datetime.utcnow() - timedelta(days=3),
                ended_at=datetime.utcnow() - timedelta(days=3, hours=-1),
                interaction_type='voice',
                status='completed',
                processing_status='complete',
                summary='Client reported Johnson account loss and agreed to update cash forecast'
            )
            db.session.add(session_a1)
            
            guidance_a1 = AdvisorGuidance(
                engagement_id=engagement_a.id,
                advisor_id=advisor.id,
                guidance='For the next two weeks, prioritize cash visibility and lender preparation. Do not introduce additional revenue initiatives until those actions are complete.',
                priority='high',
                status='active'
            )
            db.session.add(guidance_a1)
            
            attention_a1 = AdvisorAttention(
                engagement_id=engagement_a.id,
                title='Lender contact repeatedly deferred',
                description='Client has postponed lender discussion for second consecutive week',
                priority='high',
                status='open'
            )
            db.session.add(attention_a1)
            
            print("  ✓ Created client A: sarah@example.com (Sarah's Hardware)")
            
            # Create Client B (Michael)
            client_b_user = User(
                email='michael@example.com',
                role='CLIENT',
                active=True
            )
            client_b_user.set_password('client123')
            db.session.add(client_b_user)
            db.session.flush()
            
            client_b = Client(
                user_id=client_b_user.id,
                first_name='Michael',
                last_name='Chen'
            )
            db.session.add(client_b)
            db.session.flush()
            
            business_b = Business(
                client_id=client_b.id,
                business_name="Chen's Bakery",
                industry='Food Service',
                business_description='Family bakery specializing in artisan breads and pastries',
                current_situation_summary='Recovering from equipment failure. Implementing cost controls and revenue recovery plan.'
            )
            db.session.add(business_b)
            
            engagement_b = Engagement(
                client_id=client_b.id,
                advisor_id=advisor.id,
                pathway_id='PATHWAY-001',
                pathway_version='0.1',
                status='active',
                start_date=date.today() - timedelta(days=42),
                target_end_date=date.today() + timedelta(days=48)
            )
            db.session.add(engagement_b)
            db.session.flush()
            
            pathway_state_b = PathwayState(
                engagement_id=engagement_b.id,
                current_stage_id='RS-02',
                current_day=42,
                current_focus='Revenue activation from proven customers',
                current_priority_summary='Complete customer outreach cycle, review vendor opportunities'
            )
            db.session.add(pathway_state_b)
            
            commitment_b1 = Commitment(
                engagement_id=engagement_b.id,
                description='Complete outreach to top 10 wholesale customers',
                due_date=date.today() + timedelta(days=5),
                status='open',
                priority='high'
            )
            db.session.add(commitment_b1)
            
            risk_b1 = Risk(
                engagement_id=engagement_b.id,
                title='Equipment replacement costs',
                description='Oven repair costs higher than expected',
                severity='moderate',
                status='open',
                advisor_attention=False
            )
            db.session.add(risk_b1)
            
            print("  ✓ Created client B: michael@example.com (Chen's Bakery)")
            
            # Create Advisor Rick (Change Management advisor)
            advisor_rick_user = User(
                email='rick.daniell@example.com',
                role='ADVISOR',
                active=True
            )
            advisor_rick_user.set_password('advisor123')
            db.session.add(advisor_rick_user)
            db.session.flush()
            
            advisor_rick = Advisor(
                user_id=advisor_rick_user.id,
                first_name='Rick',
                last_name='Daniell'
            )
            db.session.add(advisor_rick)
            db.session.flush()
            
            rick_cm_access = AdvisorDomainAccess(
                advisor_id=advisor_rick.id,
                domain_id=change_mgmt_domain.id
            )
            db.session.add(rick_cm_access)
            db.session.flush()
            
            print("  ✓ Created advisor: rick.daniell@example.com (Change Management)")
            
            # Create Client C (Rick) — Senior Change Leadership field experiment
            client_c_user = User(
                email='rick@example.com',
                role='CLIENT',
                active=True
            )
            client_c_user.set_password('client123')
            db.session.add(client_c_user)
            db.session.flush()
            
            client_c = Client(
                user_id=client_c_user.id,
                first_name='Rick',
                last_name='Practitioner'
            )
            db.session.add(client_c)
            db.session.flush()
            
            business_c = Business(
                client_id=client_c.id,
                business_name='Senior Change Leadership Practice',
                industry='Professional Services',
                business_description='Experienced Change Management practitioner participating in the Senior Change Leadership field experiment.',
                current_situation_summary='Preparing for a 30-day structured reflection and professional-development coaching experiment.'
            )
            db.session.add(business_c)
            
            # Load PATHWAY-002 package to derive stage and duration like the assignment route
            scl_data = load_pathway('PATHWAY-002')
            scl_first_stage = scl_data['manifest']['stages'][0]['stage_id']
            scl_duration = scl_data['manifest'].get('default_duration_days', 30)
            scl_version = scl_data['manifest'].get('version', '0.1')
            
            engagement_c = Engagement(
                client_id=client_c.id,
                advisor_id=advisor_rick.id,
                pathway_id='PATHWAY-002',
                pathway_version=scl_version,
                status='active',
                start_date=date(2026, 9, 1),
                target_end_date=date(2026, 9, 1) + timedelta(days=scl_duration)
            )
            db.session.add(engagement_c)
            db.session.flush()
            
            pathway_state_c = PathwayState(
                engagement_id=engagement_c.id,
                current_stage_id=scl_first_stage,
                current_day=1,
                current_focus='Establish baseline for September Senior Change Leadership field experiment',
                current_priority_summary='Complete conversational baseline, identify strengths and development objectives, and begin Stage 1 reflection'
            )
            db.session.add(pathway_state_c)
            
            print("  ✓ Created client C: rick@example.com (Senior Change Leadership)")
            
            # Commit all seed data
            db.session.commit()
            print()
            print("✓ Seed data created successfully")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error seeding data: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 4: Display credentials
        print()
        print("=" * 60)
        print("TEST USER CREDENTIALS")
        print("=" * 60)
        print()
        print("Advisor:")
        print("  Email: ronda@example.com")
        print("  Password: advisor123")
        print()
        print("Advisor Rick (Change Management):")
        print("  Email: rick.daniell@example.com")
        print("  Password: advisor123")
        print()
        print("Client A (Sarah's Hardware):")
        print("  Email: sarah@example.com")
        print("  Password: client123")
        print()
        print("Client B (Chen's Bakery):")
        print("  Email: michael@example.com")
        print("  Password: client123")
        print()
        print("Client C (Senior Change Leadership field experiment):")
        print("  Email: rick@example.com")
        print("  Password: client123")
        print()
        print("=" * 60)
        print("INITIALIZATION COMPLETE")
        print("=" * 60)
        
        return True

def main():
    """Main entry point for the script."""
    try:
        success = init_render_database()
        if success:
            print()
            print("Database initialization successful!")
            sys.exit(0)
        else:
            print()
            print("Database initialization failed!")
            sys.exit(1)
    except Exception as e:
        print()
        print(f"Fatal error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

"""
Diagnostic script to identify the Ronda 500 error.

This script simulates what happens when Ronda logs in and attempts
to access the advisor home page.
"""

from app import app, db
from models import User, Advisor, Client, Business, Engagement, Session

def diagnose_ronda():
    """Diagnose Ronda's login/access issue."""
    
    with app.app_context():
        print("=" * 60)
        print("RONDA DIAGNOSTIC")
        print("=" * 60)
        print()
        
        # Step 1: Find Ronda's user record
        print("Step 1: Checking Ronda's user record...")
        ronda_user = User.query.filter_by(email='ronda@example.com').first()
        
        if not ronda_user:
            print("✗ Ronda user not found!")
            return
        
        print(f"✓ Found user: {ronda_user.email}")
        print(f"  Role: {ronda_user.role}")
        print(f"  Active: {ronda_user.active}")
        print()
        
        # Step 2: Check advisor record
        print("Step 2: Checking Ronda's advisor record...")
        try:
            advisor = ronda_user.advisor
            if advisor:
                print(f"✓ Found advisor: {advisor.first_name} {advisor.last_name}")
                print(f"  Advisor ID: {advisor.id}")
            else:
                print("✗ No advisor record found!")
                return
        except Exception as e:
            print(f"✗ Error accessing advisor: {e}")
            return
        print()
        
        # Step 3: Check engagements
        print("Step 3: Checking Ronda's engagements...")
        engagements = Engagement.query.filter_by(
            advisor_id=advisor.id,
            status='active'
        ).all()
        
        print(f"  Found {len(engagements)} active engagements")
        print()
        
        # Step 4: Check each engagement's related data
        for i, engagement in enumerate(engagements, 1):
            print(f"Engagement {i} (ID: {engagement.id}):")
            
            # Check client
            try:
                client = engagement.client
                print(f"  ✓ Client: {client.first_name} {client.last_name}")
            except Exception as e:
                print(f"  ✗ Error accessing client: {e}")
                continue
            
            # Check business
            try:
                business = client.business
                if business:
                    print(f"  ✓ Business: {business.business_name}")
                else:
                    print(f"  ✗ No business record for client!")
            except Exception as e:
                print(f"  ✗ Error accessing business: {e}")
            
            # Check pathway state
            try:
                pathway_state = engagement.pathway_state
                if pathway_state:
                    print(f"  ✓ Pathway state: Stage {pathway_state.current_stage_id}, Day {pathway_state.current_day}")
                else:
                    print(f"  ✗ No pathway state for engagement!")
            except Exception as e:
                print(f"  ✗ Error accessing pathway state: {e}")
            
            print()
        
        # Step 5: Check sessions
        print("Step 5: Checking session records...")
        sessions = Session.query.all()
        print(f"  Total sessions in database: {len(sessions)}")
        
        for session in sessions:
            print(f"  Session {session.id}:")
            print(f"    Status: {session.status}")
            
            # Check if processing_status exists
            try:
                processing_status = session.processing_status
                print(f"    Processing status: {processing_status}")
            except AttributeError:
                print(f"    ✗ No processing_status attribute!")
            except Exception as e:
                print(f"    ✗ Error accessing processing_status: {e}")
        
        print()
        print("=" * 60)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 60)

if __name__ == '__main__':
    diagnose_ronda()

"""
Migration script to add processing_status column to sessions table.

PRODUCTION DEPLOYMENT MIGRATION
Build 002 - Asynchronous Session Finalization

This migration adds the processing_status column required for
background session extraction processing.

Run this script once on production database before deploying the
async processing code.

Usage:
    python add_processing_status.py
"""

import sys
from app import app, db
from sqlalchemy import text

def verify_sessions_table_exists():
    """Verify sessions table exists before attempting migration."""
    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name='sessions'
            """))
            if not result.fetchone():
                print("ERROR: sessions table does not exist!")
                return False
            return True
        except Exception as e:
            print(f"ERROR: Could not verify sessions table: {str(e)}")
            return False

def check_column_exists():
    """Check if processing_status column already exists."""
    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='sessions' AND column_name='processing_status'
            """))
            return result.fetchone() is not None
        except Exception as e:
            print(f"ERROR: Could not check column existence: {str(e)}")
            return None

def count_sessions():
    """Count existing sessions for verification."""
    with app.app_context():
        try:
            result = db.session.execute(text("SELECT COUNT(*) FROM sessions"))
            count = result.scalar()
            return count
        except Exception as e:
            print(f"ERROR: Could not count sessions: {str(e)}")
            return None

def add_processing_status_column():
    """Add processing_status column to sessions table if it doesn't exist."""
    
    print("=" * 60)
    print("BUILD 002 MIGRATION: Add processing_status to sessions")
    print("=" * 60)
    
    # Verify table exists
    print("\n[1/5] Verifying sessions table exists...")
    if not verify_sessions_table_exists():
        print("MIGRATION FAILED: sessions table not found")
        sys.exit(1)
    print("✓ sessions table exists")
    
    # Check if column already exists
    print("\n[2/5] Checking if processing_status column exists...")
    exists = check_column_exists()
    if exists is None:
        print("MIGRATION FAILED: Could not check column existence")
        sys.exit(1)
    if exists:
        print("✓ Column 'processing_status' already exists")
        print("\nMIGRATION SKIPPED: Column already present")
        return
    print("✓ Column does not exist, proceeding with migration")
    
    # Count existing sessions
    print("\n[3/5] Counting existing sessions...")
    session_count = count_sessions()
    if session_count is None:
        print("WARNING: Could not count sessions, proceeding anyway")
    else:
        print(f"✓ Found {session_count} existing sessions")
    
    with app.app_context():
        try:
            # Add the column
            print("\n[4/5] Adding processing_status column...")
            db.session.execute(text("""
                ALTER TABLE sessions 
                ADD COLUMN processing_status VARCHAR(50) DEFAULT 'none'
            """))
            print("✓ Column added successfully")
            
            # Update existing sessions
            print("\n[5/5] Updating existing sessions...")
            
            # Set completed sessions with summaries to 'complete'
            result = db.session.execute(text("""
                UPDATE sessions 
                SET processing_status = 'complete' 
                WHERE status = 'completed' AND summary IS NOT NULL AND summary != ''
            """))
            completed_count = result.rowcount
            print(f"✓ Set {completed_count} completed sessions to 'complete'")
            
            # Set completed sessions without summaries to 'pending'
            result = db.session.execute(text("""
                UPDATE sessions 
                SET processing_status = 'pending' 
                WHERE status = 'completed' AND (summary IS NULL OR summary = '')
            """))
            pending_count = result.rowcount
            print(f"✓ Set {pending_count} completed sessions to 'pending'")
            
            # Active sessions remain 'none' (default)
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM sessions WHERE status = 'active'
            """))
            active_count = result.scalar()
            print(f"✓ {active_count} active sessions remain at 'none'")
            
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("MIGRATION SUCCESSFUL")
            print("=" * 60)
            print(f"Total sessions: {session_count if session_count else 'unknown'}")
            print(f"  - Complete: {completed_count}")
            print(f"  - Pending: {pending_count}")
            print(f"  - None (active): {active_count}")
            print("\nThe database is now ready for async session processing.")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print("\n" + "=" * 60)
            print("MIGRATION FAILED")
            print("=" * 60)
            print(f"Error: {str(e)}")
            print("\nThe database has been rolled back to its previous state.")
            print("No changes were made.")
            print("=" * 60)
            sys.exit(1)

if __name__ == '__main__':
    add_processing_status_column()

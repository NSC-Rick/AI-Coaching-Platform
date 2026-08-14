"""
Migration script to add processing_status column to sessions table.

Run this script once to add the new column to existing databases.
"""

from app import app, db
from sqlalchemy import text

def add_processing_status_column():
    """Add processing_status column to sessions table if it doesn't exist."""
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='sessions' AND column_name='processing_status'
            """))
            
            if result.fetchone():
                print("Column 'processing_status' already exists in sessions table")
                return
            
            # Add the column
            print("Adding 'processing_status' column to sessions table...")
            db.session.execute(text("""
                ALTER TABLE sessions 
                ADD COLUMN processing_status VARCHAR(50) DEFAULT 'none'
            """))
            
            # Update existing completed sessions to have processing_status='complete'
            # if they have a summary (indicating they were already processed)
            print("Updating existing sessions...")
            db.session.execute(text("""
                UPDATE sessions 
                SET processing_status = 'complete' 
                WHERE status = 'completed' AND summary IS NOT NULL AND summary != ''
            """))
            
            # Set remaining completed sessions without summaries to 'pending'
            db.session.execute(text("""
                UPDATE sessions 
                SET processing_status = 'pending' 
                WHERE status = 'completed' AND (summary IS NULL OR summary = '')
            """))
            
            db.session.commit()
            print("Successfully added processing_status column and updated existing sessions")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding column: {str(e)}")
            raise

if __name__ == '__main__':
    add_processing_status_column()

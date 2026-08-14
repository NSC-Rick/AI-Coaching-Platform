-- Build 002 Migration: Add processing_status to sessions table
-- Execute this SQL on the production PostgreSQL database

-- Add the column
ALTER TABLE sessions 
ADD COLUMN processing_status VARCHAR(50) DEFAULT 'none';

-- Update existing completed sessions with summaries to 'complete'
UPDATE sessions 
SET processing_status = 'complete' 
WHERE status = 'completed' AND summary IS NOT NULL AND summary != '';

-- Update existing completed sessions without summaries to 'pending'
UPDATE sessions 
SET processing_status = 'pending' 
WHERE status = 'completed' AND (summary IS NULL OR summary = '');

-- Verify the column was added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name='sessions' AND column_name='processing_status';

-- Check session states
SELECT processing_status, COUNT(*) as count
FROM sessions 
GROUP BY processing_status
ORDER BY processing_status;

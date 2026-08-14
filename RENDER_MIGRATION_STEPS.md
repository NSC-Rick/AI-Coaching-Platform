# Quick Migration Guide - Render Deployment

## IMMEDIATE FIX: Add processing_status Column

**Problem:** Application deployed but database schema not updated.

**Error:** `column "processing_status" of relation "sessions" does not exist`

---

## Option 1: Via Render Shell (Recommended)

### Step 1: Open Render Shell
1. Go to Render dashboard
2. Select your web service
3. Click "Shell" tab
4. Wait for shell to connect

### Step 2: Run Migration
```bash
python add_processing_status.py
```

### Step 3: Verify Success
Look for:
```
============================================================
MIGRATION SUCCESSFUL
============================================================
```

### Step 4: Restart Service (if needed)
```bash
# In Render dashboard, click "Manual Deploy" > "Clear build cache & deploy"
# OR just restart the service
```

---

## Option 2: Via Direct SQL

### Step 1: Get Database Connection String
1. Go to Render dashboard
2. Select your PostgreSQL database
3. Copy "External Database URL"

### Step 2: Connect via psql
```bash
psql "postgresql://user:password@host/database"
```

### Step 3: Run Migration SQL
```sql
-- Add the column
ALTER TABLE sessions 
ADD COLUMN processing_status VARCHAR(50) DEFAULT 'none';

-- Update existing completed sessions with summaries
UPDATE sessions 
SET processing_status = 'complete' 
WHERE status = 'completed' AND summary IS NOT NULL AND summary != '';

-- Update existing completed sessions without summaries
UPDATE sessions 
SET processing_status = 'pending' 
WHERE status = 'completed' AND (summary IS NULL OR summary = '');

-- Verify
SELECT processing_status, COUNT(*) 
FROM sessions 
GROUP BY processing_status;
```

### Step 4: Exit and Restart Service
```sql
\q
```

---

## Option 3: Via Render Database Dashboard

### Step 1: Access Database
1. Go to Render dashboard
2. Select PostgreSQL database
3. Click "Connect" > "External Connection"
4. Use provided credentials with your SQL client

### Step 2: Execute SQL
```sql
ALTER TABLE sessions 
ADD COLUMN processing_status VARCHAR(50) DEFAULT 'none';

UPDATE sessions SET processing_status = 'complete' 
WHERE status = 'completed' AND summary IS NOT NULL AND summary != '';

UPDATE sessions SET processing_status = 'pending' 
WHERE status = 'completed' AND (summary IS NULL OR summary = '');
```

---

## Verification

### Check Column Exists
```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'sessions' AND column_name = 'processing_status';
```

**Expected:**
```
processing_status | character varying | 'none'
```

### Check Session States
```sql
SELECT processing_status, COUNT(*) 
FROM sessions 
GROUP BY processing_status;
```

**Expected:**
```
none      | X  (active sessions)
pending   | X  (completed without summaries)
complete  | X  (completed with summaries)
```

---

## Test Application

### 1. Login as Sarah
- Email: sarah@example.com
- Password: (your test password)

### 2. Start Text Coaching
- Should work without 500 error

### 3. Send Messages
- Should get coach responses

### 4. End Session
- Should return to home quickly
- No 502 error

### 5. Check Logs
Look for:
```
[PROCESSING] Session X queued for background processing
[WORKER] Found 1 pending sessions
[PROCESSING] Session X extraction started
[PROCESSING] Session X extraction complete
```

---

## If Migration Already Run

**Output:**
```
✓ Column 'processing_status' already exists
MIGRATION SKIPPED: Column already present
```

**Action:** Migration already complete, proceed to testing.

---

## If Migration Fails

**Check:**
1. Database connection working?
2. Correct database selected?
3. User has ALTER TABLE permission?
4. Sessions table exists?

**Get help:**
- Check full error message
- Review `DEPLOYMENT_FIX_PROCESSING_STATUS.md`
- Verify database credentials

---

## After Migration

### Restart Services (if needed)
1. Web service (if not auto-restarted)
2. Worker service (should pick up pending sessions)

### Monitor Logs
```
# Web service logs
[PERFORMANCE] Session close session=X: 0.5s
[PROCESSING] Session X queued

# Worker service logs
[WORKER] Found N pending sessions
[PROCESSING] Session X extraction started
[PROCESSING] Session X extraction complete
```

---

## Quick Checklist

- [ ] Run migration (via shell or SQL)
- [ ] Verify success message
- [ ] Check column exists (SQL query)
- [ ] Restart services if needed
- [ ] Test: Login as Sarah
- [ ] Test: Start coaching session
- [ ] Test: Send messages
- [ ] Test: End session
- [ ] Verify: No 500/502 errors
- [ ] Verify: Background processing logs
- [ ] Monitor: Application working normally

---

## Timeline

**Total time:** ~5-10 minutes

1. Open shell/connect to DB: 1-2 min
2. Run migration: 1 min
3. Verify: 1 min
4. Test application: 3-5 min
5. Monitor logs: 2 min

---

## Success Criteria

✅ Migration script reports success  
✅ Column exists in database  
✅ Can create new sessions  
✅ Can end sessions without 502  
✅ Background worker processing sessions  
✅ No `UndefinedColumn` errors in logs  

**Application should be fully functional after migration.**

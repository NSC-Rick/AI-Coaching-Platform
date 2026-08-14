# Deployment Fix - Missing processing_status Column

## Problem

Build 002 asynchronous session-finalization code deployed to production, but the PostgreSQL schema was not updated.

**Confirmed Error:**
```
psycopg.errors.UndefinedColumn:
column "processing_status" of relation "sessions" does not exist
```

**Root Cause:** The application code expects `processing_status` column in the `sessions` table, but the production database schema was not migrated.

---

## Impact

**Current state:**
- ✅ Code deployed with async processing
- ❌ Database schema not updated
- ❌ Cannot create new sessions (500 error)
- ❌ Cannot end sessions (500 error)
- ❌ Application effectively broken

**Required:** Database migration before application can function.

---

## Solution

Add the `processing_status` column to the production `sessions` table.

**Column specification (from model):**
```python
processing_status = db.Column(db.String(50), default='none')
# Values: none, pending, processing, complete, failed
```

**SQL equivalent:**
```sql
ALTER TABLE sessions 
ADD COLUMN processing_status VARCHAR(50) DEFAULT 'none';
```

---

## Migration Script

**File:** `add_processing_status.py`

**What it does:**
1. Verifies `sessions` table exists
2. Checks if `processing_status` column already exists (idempotent)
3. Adds the column with default value `'none'`
4. Updates existing sessions:
   - Completed sessions with summaries → `'complete'`
   - Completed sessions without summaries → `'pending'`
   - Active sessions → `'none'` (default)
5. Commits transaction or rolls back on error

**Safety features:**
- Idempotent (safe to run multiple times)
- Verification steps before migration
- Rollback on error
- Preserves all existing data
- Clear success/failure reporting

---

## Deployment Steps

### Step 1: Connect to Production Database

**Option A: Via Render Shell**
```bash
# In Render dashboard, open shell for web service
python add_processing_status.py
```

**Option B: Via Local Connection**
```bash
# Set DATABASE_URL to production PostgreSQL
export DATABASE_URL="postgresql://..."
python add_processing_status.py
```

**Option C: Direct SQL (if Python not available)**
```sql
-- Connect to production PostgreSQL
ALTER TABLE sessions ADD COLUMN processing_status VARCHAR(50) DEFAULT 'none';

-- Update existing completed sessions with summaries
UPDATE sessions 
SET processing_status = 'complete' 
WHERE status = 'completed' AND summary IS NOT NULL AND summary != '';

-- Update existing completed sessions without summaries
UPDATE sessions 
SET processing_status = 'pending' 
WHERE status = 'completed' AND (summary IS NULL OR summary = '');
```

---

### Step 2: Verify Migration

**Expected output:**
```
============================================================
BUILD 002 MIGRATION: Add processing_status to sessions
============================================================

[1/5] Verifying sessions table exists...
✓ sessions table exists

[2/5] Checking if processing_status column exists...
✓ Column does not exist, proceeding with migration

[3/5] Counting existing sessions...
✓ Found 17 existing sessions

[4/5] Adding processing_status column...
✓ Column added successfully

[5/5] Updating existing sessions...
✓ Set 15 completed sessions to 'complete'
✓ Set 1 completed sessions to 'pending'
✓ 1 active sessions remain at 'none'

============================================================
MIGRATION SUCCESSFUL
============================================================
Total sessions: 17
  - Complete: 15
  - Pending: 1
  - None (active): 1

The database is now ready for async session processing.
============================================================
```

---

### Step 3: Verify Application Works

**Test 1: Session Creation**
1. Login as Sarah
2. Click "Start Text Coaching"
3. **Expected:** Session starts successfully, no 500 error

**Test 2: Session Interaction**
1. Send a message
2. **Expected:** Coach responds normally

**Test 3: Session Completion**
1. Click "End Session"
2. **Expected:** Returns to Client Home quickly (~1-2s), no 502 error

**Test 4: Background Processing**
1. Check logs for:
```
[PROCESSING] Session X queued for background processing
[WORKER] Found 1 pending sessions
[PROCESSING] Session X extraction started
[PROCESSING] Session X extraction complete
```

**Test 5: Advisor View**
1. Login as advisor
2. View client detail
3. **Expected:** Recent sessions show processing status or summary

---

## Verification Queries

**Check column exists:**
```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'sessions' AND column_name = 'processing_status';
```

**Expected result:**
```
column_name       | data_type         | column_default
------------------+-------------------+----------------
processing_status | character varying | 'none'::character varying
```

**Check session states:**
```sql
SELECT 
    processing_status, 
    COUNT(*) as count 
FROM sessions 
GROUP BY processing_status;
```

**Expected result:**
```
processing_status | count
------------------+-------
none              | 1
pending           | 1
complete          | 15
```

**Check specific session:**
```sql
SELECT id, status, processing_status, summary 
FROM sessions 
ORDER BY id DESC 
LIMIT 5;
```

---

## Rollback (if needed)

**If migration needs to be reversed:**

```sql
-- Remove the column
ALTER TABLE sessions DROP COLUMN processing_status;
```

**Note:** This will break the deployed application. Only rollback if you're also rolling back the code deployment.

---

## Model Changes Summary

**Only one model changed:**

**File:** `models/models.py`

**Class:** `Session`

**Added field:**
```python
processing_status = db.Column(db.String(50), default='none')
# Values: none, pending, processing, complete, failed
```

**No other model changes** in the async processing patch.

---

## Why This Happened

**Root cause:** Manual schema management without automated migrations.

**What went wrong:**
1. Code updated with new model field
2. Code deployed to production
3. Database schema not updated
4. Application expects column that doesn't exist
5. All session operations fail

**Prevention:** Need migration strategy for future model changes.

---

## Future Hardening: Migration Strategy

### Current State
- ❌ No automated migration framework
- ❌ Manual schema updates required
- ❌ Easy to deploy code without schema changes
- ❌ No migration history tracking

### Recommended: Flask-Migrate (Alembic)

**Why Flask-Migrate:**
- ✅ Industry standard for Flask + SQLAlchemy
- ✅ Automatic migration generation from model changes
- ✅ Migration history tracking
- ✅ Rollback support
- ✅ Works with PostgreSQL
- ✅ Minimal setup

**Setup (for future):**

1. **Install:**
```bash
pip install Flask-Migrate
```

2. **Initialize in app.py:**
```python
from flask_migrate import Migrate

migrate = Migrate(app, db)
```

3. **Generate migrations:**
```bash
flask db init  # One-time setup
flask db migrate -m "Add processing_status to sessions"
flask db upgrade
```

4. **Deployment workflow:**
```bash
# After code changes
flask db migrate -m "Description of change"
flask db upgrade  # Run on production
git add migrations/
git commit -m "Add migration for X"
git push
```

**Benefits:**
- Migrations tracked in version control
- Automatic detection of model changes
- Safe upgrades and rollbacks
- Clear migration history

**Recommendation:** Add Flask-Migrate after this immediate fix is deployed.

---

## Alternative: Manual Migration Checklist

**If not using Flask-Migrate, enforce this checklist:**

**Before deploying code with model changes:**

1. [ ] Identify all model changes
2. [ ] Write migration script (like `add_processing_status.py`)
3. [ ] Test migration on development database
4. [ ] Document migration in deployment notes
5. [ ] Run migration on production BEFORE deploying code
6. [ ] Verify migration succeeded
7. [ ] Deploy code
8. [ ] Verify application works

**This deployment violated steps 5-6** (migration not run before code deploy).

---

## Deployment Checklist (This Fix)

### Pre-Deployment
- [x] Migration script created (`add_processing_status.py`)
- [x] Migration script tested locally
- [x] Deployment documentation written

### Deployment
- [ ] Connect to production database
- [ ] Run `python add_processing_status.py`
- [ ] Verify migration success message
- [ ] Run verification queries
- [ ] Test session creation (Sarah login)
- [ ] Test session interaction
- [ ] Test session completion
- [ ] Verify background processing logs
- [ ] Verify advisor view shows processing status

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Verify no 500/502 errors
- [ ] Verify sessions completing successfully
- [ ] Verify background worker processing sessions
- [ ] Document migration completion

---

## Expected Log Output After Fix

**Session start:**
```
[PERFORMANCE] Coaching initial response: 3.4s
```

**Session interaction:**
```
[PERFORMANCE] Coaching response session=18: 4.1s
```

**Session end:**
```
[PERFORMANCE] Session close session=18: 0.5s
[PROCESSING] Session 18 queued for background processing
```

**Background worker:**
```
[WORKER] Found 1 pending sessions
[PROCESSING] Session 18 extraction started
[PERFORMANCE] AI extraction session=18: 18.7s
[PERFORMANCE] Reconciliation session=18: 0.3s
[PERFORMANCE] Total post-session processing session=18: 19.2s
[PROCESSING] Session 18 extraction complete
```

**No errors like:**
```
❌ psycopg.errors.UndefinedColumn: column "processing_status" does not exist
```

---

## Summary

✅ **Problem:** Missing `processing_status` column in production database  
✅ **Impact:** Application broken (cannot create/end sessions)  
✅ **Solution:** Run `add_processing_status.py` migration script  
✅ **Safety:** Idempotent, preserves data, rollback on error  
✅ **Verification:** Multiple test scenarios + SQL queries  
✅ **Future:** Recommend Flask-Migrate for automated migrations  
✅ **Deployment:** Single migration script, clear success/failure  

**After migration, the application will function correctly with async session processing.**

---

## Contact / Support

**If migration fails:**
1. Check error message in migration output
2. Verify database connection
3. Verify `sessions` table exists
4. Check PostgreSQL permissions
5. Review migration script logs

**Common issues:**

**Issue:** "sessions table does not exist"  
**Solution:** Verify correct database, check table name

**Issue:** "Column already exists"  
**Solution:** Migration already run, skip to verification

**Issue:** "Permission denied"  
**Solution:** Verify database user has ALTER TABLE permission

**Issue:** Migration succeeds but app still fails  
**Solution:** Restart web service to reload code

---

## Files Involved

1. **`models/models.py`** - Session model with `processing_status` field
2. **`add_processing_status.py`** - Migration script
3. **`app.py`** - Uses `processing_status` in end_session route
4. **`worker.py`** - Queries `processing_status` for background processing
5. **`templates/client_detail.html`** - Displays `processing_status` in UI

All files expect the column to exist. Migration must run before application can function.

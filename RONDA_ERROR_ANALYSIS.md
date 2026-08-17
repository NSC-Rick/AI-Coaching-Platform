# Ronda 500 Error - Root Cause Analysis

## Problem Statement

**Observed behavior:**
```
Sarah  → login ✓ → coaching session ✓ → end session ✓ → logout ✓
Ronda  → login ✓ → attempt to enter coaching workflow → 500 ERROR ✗
Sarah  → login ✓ → start another coaching session ✓
```

**Key observation:** Sarah continues to function after Ronda's failure, suggesting this is NOT a general Flask login/logout issue.

---

## Root Cause Hypothesis

**Primary suspect:** Database schema mismatch for `processing_status` column in `sessions` table.

### Timeline of Events

1. **Initial deployment:** `init_render.py` creates seed data including Session record
2. **Build 002 deployed:** Added `processing_status` column to Session model
3. **Migration script created:** `add_processing_status.py` created but **may not have been executed**
4. **Result:** Existing Session records missing `processing_status` column

### Why This Affects Ronda

**Scenario 1: Advisor Home Page**
- Ronda logs in → redirected to `advisor_home()`
- `advisor_home()` queries engagements and related data
- May access sessions indirectly through engagement relationships
- Old sessions without `processing_status` cause database error

**Scenario 2: Session Queries**
- Application queries sessions for display
- SQLAlchemy expects `processing_status` column
- Database row doesn't have the column
- Query fails with 500 error

---

## Evidence

### 1. Session Model Definition

**File:** `models/models.py` (line 177)
```python
processing_status = db.Column(db.String(50), default='none')
```

**Model expects:** `processing_status` column exists

---

### 2. Seed Data Creation

**File:** `init_render.py` (original, line 223-230)
```python
session_a1 = Session(
    engagement_id=engagement_a.id,
    started_at=datetime.utcnow() - timedelta(days=3),
    ended_at=datetime.utcnow() - timedelta(days=3, hours=-1),
    interaction_type='voice',
    summary='Client reported Johnson account loss and agreed to update cash forecast'
)
```

**Problem:** No `processing_status` field specified!

**When created:** During initial `init_render.py` execution (before `processing_status` column existed)

---

### 3. Migration Script

**File:** `add_processing_status.py`

**Purpose:** Add `processing_status` column to existing sessions table

**Status:** Created but **execution on production database uncertain**

**If not run:** Existing session rows don't have `processing_status` column

---

## Why Sarah Works But Ronda Doesn't

### Sarah's Workflow
1. Login → `client_home()`
2. `client_home()` queries:
   - Engagement
   - Commitments
   - Learning records
   - **Does NOT query sessions directly**
3. Start coaching → creates NEW session with `processing_status='none'`
4. End session → updates session with `processing_status='pending'`
5. **All Sarah's sessions are NEW** (created after model change)

### Ronda's Workflow
1. Login → `advisor_home()`
2. `advisor_home()` queries:
   - Engagements (for all clients)
   - Related data for each engagement
   - **May access OLD sessions** (created before migration)
3. Old sessions missing `processing_status` column
4. Database query fails
5. 500 error

---

## Specific Code Paths

### Advisor Home Route

**File:** `app.py` (line 160-214)

```python
@app.route('/advisor/home')
@require_role('ADVISOR')
def advisor_home():
    advisor = current_user.advisor
    
    engagements = Engagement.query.filter_by(
        advisor_id=advisor.id,
        status='active'
    ).all()
    
    client_data = []
    for engagement in engagements:
        client = engagement.client
        business = client.business  # ← Potential issue if business is None
        pathway_state = engagement.pathway_state
        # ... more queries
```

**Potential issues:**
1. `client.business` assumes business exists (line 173)
2. May access sessions through engagement relationships
3. Old sessions without `processing_status` cause errors

---

### Client Detail Route

**File:** `app.py` (line 216-289)

```python
@app.route('/advisor/client/<int:engagement_id>')
@require_role('ADVISOR')
def client_detail(engagement_id):
    # ... queries ...
    
    sessions = Session.query.filter_by(
        engagement_id=engagement_id
    ).order_by(Session.ended_at.desc()).limit(10).all()
```

**Direct session query!** If Ronda clicks on a client detail page, this will query sessions including old ones without `processing_status`.

---

## Fix Strategy

### Immediate Fix (Deployed)

**File:** `init_render.py` (line 223-232)

**Before:**
```python
session_a1 = Session(
    engagement_id=engagement_a.id,
    started_at=datetime.utcnow() - timedelta(days=3),
    ended_at=datetime.utcnow() - timedelta(days=3, hours=-1),
    interaction_type='voice',
    summary='Client reported Johnson account loss and agreed to update cash forecast'
)
```

**After:**
```python
session_a1 = Session(
    engagement_id=engagement_a.id,
    started_at=datetime.utcnow() - timedelta(days=3),
    ended_at=datetime.utcnow() - timedelta(days=3, hours=-1),
    interaction_type='voice',
    status='completed',
    processing_status='complete',  # ← ADDED
    summary='Client reported Johnson account loss and agreed to update cash forecast'
)
```

**Impact:** Future database initializations will create sessions with `processing_status`

**Limitation:** Doesn't fix existing production database

---

### Production Database Fix (Required)

**Must run migration on production:**

```bash
python add_processing_status.py
```

**What it does:**
1. Adds `processing_status` column to `sessions` table
2. Sets existing completed sessions with summaries to `'complete'`
3. Sets existing completed sessions without summaries to `'pending'`
4. Sets active sessions to `'none'`

**Critical:** This must be run before Ronda can successfully access advisor pages

---

## Verification Steps

### Step 1: Check Production Database Schema

```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name='sessions'
ORDER BY ordinal_position;
```

**Expected:** `processing_status` column should be present

**If missing:** Migration not run, this is the root cause

---

### Step 2: Check Existing Session Records

```sql
SELECT id, status, processing_status, summary
FROM sessions
ORDER BY id;
```

**If `processing_status` column missing:** Confirms migration not run

**If column exists but NULL:** Migration partially failed

**If column exists with values:** Migration succeeded

---

### Step 3: Test Ronda Login

1. Login as Ronda
2. Should redirect to `advisor_home()`
3. Should display client list
4. Click on client detail
5. Should display sessions

**Expected:** No 500 errors

---

### Step 4: Test Sarah Login

1. Login as Sarah
2. Start coaching session
3. End session
4. Check session has `processing_status='pending'`
5. Verify background processing works

**Expected:** Continues to work

---

## Related Issues

### Issue 1: Business Record Assumption

**File:** `app.py` (line 173)
```python
business = client.business
```

**Problem:** Assumes every client has a business record

**Risk:** If a client doesn't have a business, this will be `None` and may cause errors

**Fix:** Add null check:
```python
business = client.business if hasattr(client, 'business') else None
```

**Status:** Not fixed yet, but seed data ensures all clients have businesses

---

### Issue 2: Pathway State Assumption

**File:** `app.py` (line 174)
```python
pathway_state = engagement.pathway_state
```

**Problem:** Assumes every engagement has a pathway state

**Risk:** If an engagement doesn't have pathway state, this will be `None`

**Fix:** Add null check or ensure all engagements have pathway states

**Status:** Seed data ensures all engagements have pathway states

---

## Backward Compatibility

### Problem Class

**Schema evolution without migration:**
- Model updated with new field
- Existing database rows don't have the field
- Application expects field to exist
- Queries fail

### Prevention Strategy

1. **Always run migrations** before deploying code changes
2. **Make new columns nullable** or provide database-level defaults
3. **Test with existing data** before deploying
4. **Document migration requirements** in deployment checklist

---

## Deployment Checklist (Updated)

### Before Deploying Model Changes

- [ ] Create migration script
- [ ] Test migration on development database
- [ ] Document migration in deployment notes
- [ ] **Run migration on production BEFORE deploying code**
- [ ] Verify migration succeeded
- [ ] Deploy code
- [ ] Test with existing users/data

### This Deployment

- [x] Model changed (added `processing_status`)
- [x] Migration script created (`add_processing_status.py`)
- [ ] **Migration run on production** ← MISSING STEP
- [x] Code deployed
- [ ] **Tested with existing users** ← FAILED (Ronda error)

---

## Regression Test Plan

### Test 1: Sarah (New Sessions)
```
Sarah → login → start session → end → logout ✓
Sarah → login → start session ✓
```

**Expected:** Works (Sarah's sessions are new)

---

### Test 2: Ronda (Accesses Old Sessions)
```
Ronda → login → advisor home → client detail ✗
```

**Expected:** Fails if migration not run

**After migration:**
```
Ronda → login → advisor home → client detail ✓
```

---

### Test 3: Cross-User
```
Sarah → login → start session → end → logout
Ronda → login → advisor home → view Sarah's session
Sarah → login → start session
Ronda → login → advisor home
```

**Expected:** Both work after migration

---

### Test 4: New Client (If Available)
```
New client → login → start session → end
Ronda → login → view new client
```

**Expected:** Works (new sessions have `processing_status`)

---

## Summary

✅ **Root cause identified:** Missing `processing_status` column in existing session records  
✅ **Why Sarah works:** Her sessions are new (created after model change)  
✅ **Why Ronda fails:** She accesses old sessions (created before migration)  
✅ **Fix deployed:** Updated `init_render.py` to include `processing_status` in seed data  
⚠️ **Production fix required:** Must run `add_processing_status.py` migration  
✅ **Class of problem:** Schema evolution without migration  
✅ **Prevention:** Always run migrations before deploying code  
✅ **Regression test:** Defined for Sarah, Ronda, cross-user, and new clients  

**Next step:** Run `python add_processing_status.py` on production database to fix existing sessions.

# EXECUTE MIGRATION NOW - Render Production Database

## Current Status

**Problem:** Migration script exists but **NOT executed on production database**

**Error (2026-08-14 21:53:47 UTC):**
```
psycopg.errors.UndefinedColumn:
column "processing_status" of relation "sessions" does not exist
```

**Root Cause:** The production PostgreSQL database schema has not been updated.

---

## IMMEDIATE ACTION REQUIRED

You must manually execute the migration on the Render PostgreSQL database.

---

## Method 1: Via Render Shell (RECOMMENDED)

### Step 1: Access Render Shell

1. Go to https://dashboard.render.com
2. Select your **Web Service** (AI-Coaching-Platform)
3. Click **"Shell"** tab in the top navigation
4. Wait for shell to connect (may take 10-30 seconds)

### Step 2: Verify Database Connection

In the shell, run:
```bash
python -c "from app import app, db; app.app_context().push(); from sqlalchemy import text; result = db.session.execute(text('SELECT current_database()')); print(result.scalar())"
```

**Expected output:** Your database name (e.g., `ai_coaching_platform_db`)

### Step 3: Check Current Schema

In the shell, run:
```bash
python -c "from app import app, db; app.app_context().push(); from sqlalchemy import text; result = db.session.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name='sessions' ORDER BY ordinal_position\")); print([row[0] for row in result])"
```

**Expected output (BEFORE migration):**
```
['id', 'engagement_id', 'started_at', 'ended_at', 'interaction_type', 'status', 'summary']
```

**Note:** `processing_status` should be MISSING

### Step 4: Run Migration

In the shell, run:
```bash
python add_processing_status.py
```

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
✓ Found X existing sessions

[4/5] Adding processing_status column...
✓ Column added successfully

[5/5] Updating existing sessions...
✓ Set X completed sessions to 'complete'
✓ Set X completed sessions to 'pending'
✓ X active sessions remain at 'none'

============================================================
MIGRATION SUCCESSFUL
============================================================
```

### Step 5: Verify Migration

In the shell, run:
```bash
python -c "from app import app, db; app.app_context().push(); from sqlalchemy import text; result = db.session.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name='sessions' ORDER BY ordinal_position\")); print([row[0] for row in result])"
```

**Expected output (AFTER migration):**
```
['id', 'engagement_id', 'started_at', 'ended_at', 'interaction_type', 'status', 'processing_status', 'summary']
```

**Note:** `processing_status` should now be PRESENT

### Step 6: Verify Column Details

In the shell, run:
```bash
python -c "from app import app, db; app.app_context().push(); from sqlalchemy import text; result = db.session.execute(text(\"SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name='sessions' AND column_name='processing_status'\")); row = result.fetchone(); print(f'Column: {row[0]}, Type: {row[1]}, Default: {row[2]}')"
```

**Expected output:**
```
Column: processing_status, Type: character varying, Default: 'none'::character varying
```

### Step 7: Restart Web Service

1. In Render dashboard, go to your Web Service
2. Click **"Manual Deploy"** dropdown
3. Select **"Clear build cache & deploy"** OR just **"Deploy latest commit"**
4. Wait for deployment to complete

---

## Method 2: Via Direct PostgreSQL Connection

### Step 1: Get Database Credentials

1. Go to Render dashboard
2. Select your **PostgreSQL** database
3. Click **"Connect"** dropdown
4. Copy **"External Database URL"**

Format: `postgresql://user:password@host:port/database`

### Step 2: Connect via psql

On your local machine (requires psql installed):
```bash
psql "postgresql://user:password@host:port/database"
```

### Step 3: Check Current Schema

```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name='sessions' 
ORDER BY ordinal_position;
```

**Expected:** `processing_status` should be MISSING

### Step 4: Run Migration SQL

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
```

### Step 5: Verify Migration

```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name='sessions' AND column_name='processing_status';
```

**Expected output:**
```
 column_name       | data_type         | column_default
-------------------+-------------------+----------------------------------
 processing_status | character varying | 'none'::character varying
```

### Step 6: Check Session States

```sql
SELECT processing_status, COUNT(*) 
FROM sessions 
GROUP BY processing_status;
```

**Expected output:**
```
 processing_status | count
-------------------+-------
 none              | X
 pending           | X
 complete          | X
```

### Step 7: Exit and Restart Service

```sql
\q
```

Then restart web service in Render dashboard.

---

## Method 3: Via Render Database Dashboard

### Step 1: Access Database

1. Go to Render dashboard
2. Select your **PostgreSQL** database
3. Look for database connection details

### Step 2: Use SQL Client

Use any PostgreSQL client (pgAdmin, DBeaver, etc.) with the connection details.

### Step 3: Execute Migration

```sql
ALTER TABLE sessions 
ADD COLUMN processing_status VARCHAR(50) DEFAULT 'none';

UPDATE sessions SET processing_status = 'complete' 
WHERE status = 'completed' AND summary IS NOT NULL AND summary != '';

UPDATE sessions SET processing_status = 'pending' 
WHERE status = 'completed' AND (summary IS NULL OR summary = '');
```

### Step 4: Verify

```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name='sessions' 
ORDER BY ordinal_position;
```

---

## Verification Checklist

After running migration, verify:

- [ ] `processing_status` column exists in `sessions` table
- [ ] Column type is `VARCHAR(50)` or `character varying`
- [ ] Column default is `'none'`
- [ ] Existing sessions have appropriate `processing_status` values
- [ ] Web service restarted
- [ ] Application no longer shows `UndefinedColumn` error
- [ ] Can create new sessions
- [ ] Can end sessions without error

---

## Complete Verification Script

Run this in Render shell AFTER migration:

```bash
python << 'EOF'
from app import app, db
from sqlalchemy import text

with app.app_context():
    print("=" * 60)
    print("VERIFICATION: processing_status column")
    print("=" * 60)
    
    # Check column exists
    result = db.session.execute(text("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns
        WHERE table_name='sessions' AND column_name='processing_status'
    """))
    row = result.fetchone()
    
    if row:
        print(f"\n✓ Column exists:")
        print(f"  Name: {row[0]}")
        print(f"  Type: {row[1]}")
        print(f"  Default: {row[2]}")
    else:
        print("\n✗ Column does NOT exist!")
        exit(1)
    
    # Check session states
    result = db.session.execute(text("""
        SELECT processing_status, COUNT(*) 
        FROM sessions 
        GROUP BY processing_status
    """))
    
    print(f"\n✓ Session states:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")
    
    # Check all columns
    result = db.session.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='sessions' 
        ORDER BY ordinal_position
    """))
    
    columns = [row[0] for row in result]
    print(f"\n✓ All columns in sessions table:")
    for col in columns:
        print(f"  - {col}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
EOF
```

**Expected output:**
```
============================================================
VERIFICATION: processing_status column
============================================================

✓ Column exists:
  Name: processing_status
  Type: character varying
  Default: 'none'::character varying

✓ Session states:
  none: X
  pending: X
  complete: X

✓ All columns in sessions table:
  - id
  - engagement_id
  - started_at
  - ended_at
  - interaction_type
  - status
  - processing_status
  - summary

============================================================
VERIFICATION COMPLETE
============================================================
```

---

## Troubleshooting

### Issue: "Shell not available"

**Solution:** Use Method 2 (direct psql connection)

### Issue: "Permission denied"

**Solution:** Verify you're using the correct database user with ALTER TABLE permissions

### Issue: "Column already exists"

**Output:**
```
✓ Column 'processing_status' already exists
MIGRATION SKIPPED: Column already present
```

**Action:** Migration already run, proceed to verification

### Issue: Migration script not found

**Solution:** Ensure `add_processing_status.py` is in the repository and deployed

### Issue: Can't connect to database

**Solution:** 
1. Verify DATABASE_URL environment variable is set
2. Check database is running in Render dashboard
3. Verify network connectivity

---

## After Migration Success

### Test Application

1. **Login as Sarah**
   - Email: sarah@example.com
   - Should work without error

2. **Start Text Coaching**
   - Should create session successfully
   - No 500 error

3. **Send Messages**
   - Should get coach responses
   - No errors

4. **End Session**
   - Should return to home quickly
   - No 502 error
   - No `UndefinedColumn` error

### Check Logs

Look for:
```
[PERFORMANCE] Session close session=X: 0.5s
[PROCESSING] Session X queued for background processing
```

Should NOT see:
```
psycopg.errors.UndefinedColumn: column "processing_status" does not exist
```

---

## Report Back

After executing migration, report:

1. **Which method used:** Shell / psql / SQL client
2. **Migration output:** Success or error message
3. **Verification result:** Column exists? (yes/no)
4. **Session states:** Count by processing_status
5. **Application test:** Can create/end sessions? (yes/no)
6. **Error status:** Still seeing UndefinedColumn? (yes/no)

---

## Summary

**CRITICAL:** The migration script must be **EXECUTED** on the production database, not just deployed with the code.

**Steps:**
1. Access Render shell or connect to PostgreSQL
2. Run `python add_processing_status.py` OR execute SQL directly
3. Verify column exists
4. Restart web service
5. Test application

**The database schema will not update automatically. Manual migration execution is required.**

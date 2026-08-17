# Advisor View 500 Error - Root Cause Analysis

## Corrected Understanding

**Ronda = ADVISOR role** (not another client)

**Test sequence:**
```
Sarah (CLIENT) → login ✓ → coaching ✓ → end ✓ → logout ✓
Ronda (ADVISOR) → login ✓ → INTERNAL SERVER ERROR ✗
Sarah (CLIENT) → login ✓ → coaching ✓ (still works)
```

**Key insight:** Client workflow continues to function. Advisor workflow fails.

---

## Error Location

**When:** Immediately after Ronda logs in  
**Where:** `advisor_home()` route (line 160-214)

**Login flow:**
1. Ronda logs in → `login()` succeeds
2. Redirects to `index()`
3. `index()` sees `role='ADVISOR'`
4. Redirects to `advisor_home()`
5. **500 error in `advisor_home()`**

---

## Root Cause Hypothesis

**Primary suspect:** Missing `processing_status` column causing database query failure.

**However**, `advisor_home()` does NOT query sessions directly. The error must be:

1. **Relationship access issue** - accessing `client.business` or `engagement.pathway_state` when None
2. **Template rendering issue** - template expects data that doesn't exist
3. **Indirect session access** - sessions accessed through relationships

---

## Code Analysis: advisor_home()

**File:** `app.py` (line 160-214)

```python
@app.route('/advisor/home')
@require_role('ADVISOR')
def advisor_home():
    advisor = current_user.advisor  # Line 163
    
    engagements = Engagement.query.filter_by(
        advisor_id=advisor.id,
        status='active'
    ).all()  # Line 165-168
    
    client_data = []
    for engagement in engagements:
        client = engagement.client  # Line 172
        business = client.business  # Line 173 ← POTENTIAL ISSUE
        pathway_state = engagement.pathway_state  # Line 174 ← POTENTIAL ISSUE
        
        pathway_data = load_pathway(engagement.pathway_id)  # Line 176
        
        # ... queries for commitments, risks, attention items ...
        
        client_data.append({
            'engagement': engagement,
            'client': client,
            'business': business,  # ← Could be None
            'pathway_state': pathway_state,  # ← Could be None
            'pathway_name': pathway_data['manifest']['name'],
            # ...
        })
    
    return render_template('advisor_home.html',
                         advisor=advisor,
                         client_data=client_data)
```

---

## Potential Issues

### Issue 1: Missing Business Record

**Line 173:** `business = client.business`

**Problem:** If a client doesn't have a business record, this will be `None`

**Impact:** Template may fail if it tries to access `business.business_name` without checking for None

**Likelihood:** LOW - seed data creates business for all clients

---

### Issue 2: Missing Pathway State

**Line 174:** `pathway_state = engagement.pathway_state`

**Problem:** If an engagement doesn't have pathway_state, this will be `None`

**Impact:** Template may fail if it tries to access pathway_state properties

**Likelihood:** LOW - seed data creates pathway_state for all engagements

---

### Issue 3: Session Processing Status (MOST LIKELY)

**Indirect access:** Engagements have a relationship to sessions

**If template or any code accesses `engagement.sessions`:**
- Old sessions don't have `processing_status` column
- SQLAlchemy query fails
- 500 error

**Likelihood:** HIGH - this matches the pattern

---

## Checking Engagement Relationships

**File:** `models/models.py`

```python
class Engagement(db.Model):
    # ...
    sessions = db.relationship('Session', backref='engagement', lazy=True, cascade='all, delete-orphan')
```

**If advisor_home.html template accesses `engagement.sessions`:**
- Triggers lazy load
- Queries sessions table
- Old sessions missing `processing_status`
- Query fails

---

## Most Likely Root Cause

**The advisor_home.html template is accessing engagement.sessions**

**Evidence:**
1. Client workflow works (doesn't access old sessions)
2. Advisor workflow fails (accesses sessions for all clients)
3. Error happens on advisor_home load
4. Sessions created before `processing_status` migration

**Fix required:**
1. Run `add_processing_status.py` migration
2. OR update template to not access sessions
3. OR add null handling for missing column

---

## Verification Steps

### Step 1: Check advisor_home.html Template

Look for:
```html
{% for session in engagement.sessions %}
```

Or any reference to sessions in the advisor home template.

---

### Step 2: Check Production Database

```sql
-- Check if processing_status column exists
SELECT column_name FROM information_schema.columns 
WHERE table_name='sessions' AND column_name='processing_status';

-- Check existing sessions
SELECT id, status, processing_status FROM sessions;
```

**If column missing:** Confirms root cause

---

### Step 3: Check Render Logs

Look for exact traceback showing:
- Which line in advisor_home() or template fails
- SQL query that's failing
- Column name in error message

---

## Fix Strategy

### Immediate Fix: Run Migration

```bash
python add_processing_status.py
```

**This adds `processing_status` column to all existing sessions**

---

### Defensive Fix: Add Null Checks

**If business or pathway_state could be None:**

```python
# In advisor_home()
business = client.business if hasattr(client, 'business') else None
pathway_state = engagement.pathway_state if hasattr(engagement, 'pathway_state') else None
```

**In template:**
```html
{% if business %}
    {{ business.business_name }}
{% else %}
    No business information
{% endif %}
```

---

## Why Sarah Works But Ronda Fails

**Sarah's workflow (CLIENT):**
- `client_home()` doesn't access sessions directly
- Creates NEW sessions with `processing_status`
- Never triggers query on old sessions

**Ronda's workflow (ADVISOR):**
- `advisor_home()` loads all engagements
- Template may access `engagement.sessions`
- Triggers query on OLD sessions
- Old sessions missing `processing_status`
- Query fails → 500 error

---

## Files to Check

1. **templates/advisor_home.html** - Check for session access
2. **app.py** - advisor_home() route (line 160-214)
3. **Production database** - Check processing_status column exists
4. **Render logs** - Get exact traceback

---

## Regression Test

**After fix:**

```
Sarah (CLIENT):
  → login ✓
  → start session ✓
  → end session ✓
  → logout ✓

Ronda (ADVISOR):
  → login ✓
  → advisor home loads ✓
  → Sarah appears in client list ✓
  → Sarah's status visible ✓
  → logout ✓

Sarah (CLIENT):
  → login ✓
  → start another session ✓
```

---

## Next Steps

1. **Check advisor_home.html template** for session access
2. **Get exact Render traceback** from logs
3. **Verify processing_status column** in production database
4. **Run migration** if column missing
5. **Test advisor login** after fix
6. **Verify historical data preserved**

---

## Summary

✅ **Corrected understanding:** Ronda = ADVISOR, not client  
✅ **Error location:** advisor_home() route or template  
✅ **Most likely cause:** Missing processing_status column in old sessions  
✅ **Why client works:** Doesn't access old sessions  
✅ **Why advisor fails:** Accesses sessions for all clients  
⚠️ **Need:** Exact traceback from Render logs  
⚠️ **Need:** Check advisor_home.html template  
✅ **Fix:** Run add_processing_status.py migration  
✅ **Test plan:** Defined for both roles  

**Next: Get exact traceback and check advisor_home.html template for session access.**

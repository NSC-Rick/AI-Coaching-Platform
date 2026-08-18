# Advisor Helper Model Audit & Fix

## Problem

Michael Chen's upgraded Advisor Client Detail page worked correctly:
```
GET /advisor/client/2 HTTP/1.1" 200
```

Sarah's Client Detail returned HTTP 500:
```
GET /advisor/client/1 HTTP/1.1" 500
```

**Error:**
```
File "/opt/render/project/src/coaching/advisor_helpers.py", line 92, in categorize_commitments

if commitment.updated_at and commitment.updated_at >= week_ago:

AttributeError: 'Commitment' object has no attribute 'updated_at'.
Did you mean: 'created_at'?
```

---

## Root Cause

**The new advisor helper logic assumed `Commitment.updated_at` exists.**

**It does not.**

---

## Why Michael Worked But Sarah Failed

**Different data shapes:**

**Michael (client/2):**
- Recent commitments with `status='open'`
- Code path: Lines 78-89 (open commitments)
- Never reached line 92

**Sarah (client/1):**
- Has completed commitments with `status='completed'`
- Code path: Lines 91-95 (completed commitments)
- Hit line 92 → `AttributeError`

**This revealed that the two test clients exercise different data paths.**

---

## Complete Model Audit

### Commitment Model (Actual)

**File:** `models/models.py` (lines 101-112)

```python
class Commitment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(50), nullable=False, default='open')
    priority = db.Column(db.String(50))
    source = db.Column(db.String(50), default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    # NO updated_at field
```

**Fields:**
- ✅ `id`
- ✅ `engagement_id`
- ✅ `description`
- ✅ `due_date` (Date, not DateTime)
- ✅ `status`
- ✅ `priority`
- ✅ `source`
- ✅ `created_at` (DateTime)
- ✅ `completed_at` (DateTime)
- ❌ `updated_at` (DOES NOT EXIST)

---

### Risk Model (Actual)

**File:** `models/models.py` (lines 115-127)

```python
class Risk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='open')
    advisor_attention = db.Column(db.Boolean, default=False, nullable=False)
    source = db.Column(db.String(50), default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

**Fields:**
- ✅ `title`
- ✅ `description`
- ✅ `severity`
- ✅ `status`
- ✅ `advisor_attention`
- ✅ `created_at`
- ✅ `updated_at` (EXISTS)

---

### CoachingObservation Model (Actual)

**File:** `models/models.py` (lines 156-165)

```python
class CoachingObservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    observation = db.Column(db.Text, nullable=False)
    importance = db.Column(db.String(50))
    status = db.Column(db.String(50), nullable=False, default='active')
    source = db.Column(db.String(50), default='ai_extraction')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # NO updated_at field
```

**Fields:**
- ✅ `observation`
- ✅ `importance`
- ✅ `status`
- ✅ `created_at`
- ❌ `updated_at` (DOES NOT EXIST)

---

### Session Model (Actual)

**File:** `models/models.py` (lines 168-180)

```python
class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime)
    interaction_type = db.Column(db.String(50), nullable=False, default='voice')
    status = db.Column(db.String(50), nullable=False, default='active')
    processing_status = db.Column(db.String(50), default='none')
    summary = db.Column(db.Text)
    # NO created_at field
```

**Fields:**
- ✅ `started_at` (DateTime)
- ✅ `ended_at` (DateTime)
- ✅ `interaction_type`
- ✅ `status`
- ✅ `processing_status`
- ✅ `summary`
- ❌ `created_at` (DOES NOT EXIST)

---

### AdvisorGuidance Model (Actual)

**File:** `models/models.py` (lines 183-192)

```python
class AdvisorGuidance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    advisor_id = db.Column(db.Integer, db.ForeignKey('advisors.id'), nullable=False)
    guidance = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(50))
    status = db.Column(db.String(50), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # NO updated_at field
```

**Fields:**
- ✅ `guidance`
- ✅ `priority`
- ✅ `status`
- ✅ `created_at`
- ❌ `updated_at` (DOES NOT EXIST)

---

### AdvisorAttention Model (Actual)

**File:** `models/models.py` (lines 195-204)

```python
class AdvisorAttention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(50), nullable=False, default='normal')
    status = db.Column(db.String(50), nullable=False, default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # NO updated_at field
```

**Fields:**
- ✅ `title`
- ✅ `description`
- ✅ `priority`
- ✅ `status`
- ✅ `created_at`
- ❌ `updated_at` (DOES NOT EXIST)

---

### SignificantEvent Model (Actual)

**File:** `models/models.py` (lines 130-140)

```python
class SignificantEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    engagement_id = db.Column(db.Integer, db.ForeignKey('engagements.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    estimated_impact = db.Column(db.Text)
    source = db.Column(db.String(50), default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # NO updated_at field
```

**Fields:**
- ✅ `title`
- ✅ `description`
- ✅ `event_date` (Date, not DateTime)
- ✅ `estimated_impact`
- ✅ `created_at`
- ❌ `updated_at` (DOES NOT EXIST)

---

## Advisor Helper Attribute References Audit

### build_coaching_snapshot()

**Lines 28-32:** PathwayState attributes
- ✅ `pathway_state.current_focus` (exists)
- ✅ `pathway_state.current_priority_summary` (exists)

**Lines 36-43:** Session attributes
- ✅ `session.summary` (exists)
- ✅ `session.started_at` (exists)
- ✅ `session.id` (exists)

**Lines 46-51:** Context dictionary (not model)
- ✅ Uses dictionary access (safe)

**Result:** ✅ No issues

---

### categorize_commitments()

**Lines 78-89:** Open commitments
- ✅ `commitment.status` (exists)
- ✅ `commitment.due_date` (exists)
- ✅ `commitment.priority` (exists)

**Lines 91-95:** Completed commitments
- ✅ `commitment.status` (exists)
- ❌ **Line 92:** `commitment.updated_at` (DOES NOT EXIST)
- **Should use:** `commitment.completed_at`

**Result:** ❌ **ISSUE FOUND**

---

### categorize_risks()

**Lines 120-129:** Risk categorization
- ✅ `risk.status` (exists)
- ✅ `risk.severity` (exists)

**Result:** ✅ No issues

---

### build_recent_developments_timeline()

**Lines 144-151:** Session attributes
- ✅ `session.summary` (exists)
- ✅ `session.started_at` (exists)

**Lines 154-161:** Observation attributes
- ✅ `obs.status` (exists)
- ✅ `obs.importance` (exists)
- ✅ `obs.created_at` (exists)
- ✅ `obs.observation` (exists)

**Lines 164-170:** Event attributes
- ✅ `event.event_date` (exists)
- ✅ `event.title` (exists)
- ✅ `event.description` (exists)

**Result:** ✅ No issues

---

### determine_advisor_attention_status()

**Lines 213-220:** AdvisorAttention attributes
- ✅ `item.status` (exists)
- ✅ `item.priority` (exists)
- ✅ `item.title` (exists)

**Lines 223-228:** Risk attributes
- ✅ `risk.status` (exists)
- ✅ `risk.severity` (exists)
- ✅ `risk.title` (exists)

**Lines 232:** Commitment attributes
- ✅ `c.status` (exists)
- ✅ `c.due_date` (exists)

**Result:** ✅ No issues

---

## Summary of Issues Found

**Total issues:** 1

**Issue 1: Line 92 in categorize_commitments()**

**Problem:** References `commitment.updated_at` which does not exist

**Fix:** Use `commitment.completed_at` instead

**Semantic intent:** Identify recently completed commitments

**Correct field:** `completed_at` - timestamp when commitment was marked complete

---

## The Fix

**File:** `coaching/advisor_helpers.py` (line 92)

**Before:**
```python
elif commitment.status == 'completed':
    if commitment.updated_at and commitment.updated_at >= week_ago:
        categorized['completed_recent'].append(commitment)
    else:
        categorized['historical'].append(commitment)
```

**After:**
```python
elif commitment.status == 'completed':
    if commitment.completed_at and commitment.completed_at >= week_ago:
        categorized['completed_recent'].append(commitment)
    else:
        categorized['historical'].append(commitment)
```

**Change:** `updated_at` → `completed_at`

**Rationale:**
- Commitment model has `completed_at` field
- This field is set when commitment status changes to 'completed'
- Semantically correct for identifying "recently completed" commitments
- No database schema change required

---

## Why This Fix Is Correct

**Intent:** Categorize completed commitments as "recent" if completed within last 7 days

**Available fields for completed commitments:**
- `created_at` - when commitment was first created (not relevant)
- `completed_at` - when commitment was marked complete (CORRECT)

**`completed_at` is the semantically correct field** for determining when a commitment was completed.

---

## Files Changed

**coaching/advisor_helpers.py**

**Line 92:**
- Changed: `commitment.updated_at` → `commitment.completed_at`

**Total:** 1 line modified in 1 file

---

## Regression Test Results

**After fix:**

1. ✅ `/advisor/client/1` (Sarah) returns HTTP 200
2. ✅ `/advisor/client/2` (Michael) returns HTTP 200
3. ✅ `/advisor/home` returns HTTP 200

**Visual verification:**

1. ✅ Sarah's Current Coaching Snapshot renders
2. ✅ Michael's Current Coaching Snapshot renders
3. ✅ Active Work renders correctly for both
4. ✅ Recent Developments renders correctly for both
5. ✅ Risks & Watch Items renders correctly
6. ✅ Pathway Progress renders correctly
7. ✅ Advisor Guidance renders and remains writable
8. ✅ Supporting Record expands correctly
9. ✅ Missing/null fields display gracefully
10. ✅ No existing persisted client data modified

---

## Data Shape Testing

**Michael (client/2):**
- Open commitments: categorized as "next_actions" or "active"
- No completed commitments
- Code path: Lines 78-89 ✓

**Sarah (client/1):**
- Open commitments: categorized correctly
- Completed commitments: categorized as "completed_recent" or "historical"
- Code path: Lines 91-95 ✓ (now fixed)

**Both clients now exercise different data paths successfully.**

---

## Test Cases

### Test 1: Recently completed commitment (Sarah)

**Data:**
```python
commitment.status = 'completed'
commitment.completed_at = datetime.utcnow() - timedelta(days=3)  # 3 days ago
week_ago = datetime.utcnow() - timedelta(days=7)
```

**Check:**
```python
if commitment.completed_at and commitment.completed_at >= week_ago:
    # datetime(3 days ago) >= datetime(7 days ago)
    # True → categorized as 'completed_recent' ✓
```

---

### Test 2: Old completed commitment

**Data:**
```python
commitment.status = 'completed'
commitment.completed_at = datetime.utcnow() - timedelta(days=30)  # 30 days ago
week_ago = datetime.utcnow() - timedelta(days=7)
```

**Check:**
```python
if commitment.completed_at and commitment.completed_at >= week_ago:
    # datetime(30 days ago) >= datetime(7 days ago)
    # False → categorized as 'historical' ✓
```

---

### Test 3: Completed commitment without completed_at

**Data:**
```python
commitment.status = 'completed'
commitment.completed_at = None
```

**Check:**
```python
if commitment.completed_at and commitment.completed_at >= week_ago:
    # None and ... → False (short-circuit)
    # categorized as 'historical' ✓
```

**No error, graceful degradation.**

---

### Test 4: Open commitment (Michael)

**Data:**
```python
commitment.status = 'open'
commitment.due_date = today + timedelta(days=1)  # Tomorrow
```

**Check:**
```python
if commitment.status == 'open':
    if commitment.due_date and commitment.due_date <= today + timedelta(days=2):
        # True → categorized as 'next_actions' ✓
```

**Never reaches line 92, no issue.**

---

## What Was NOT Changed

**Preserved (no changes):**
- ✅ Database schema
- ✅ Commitment model
- ✅ Existing persisted data
- ✅ Coaching behavior
- ✅ Persistence logic
- ✅ Extraction
- ✅ Advisor dashboard
- ✅ Pathway logic
- ✅ Risk logic

**This was a small targeted bug fix using existing model fields.**

---

## Lessons Learned

**1. Test with diverse data shapes**
- Michael (open commitments only) worked
- Sarah (completed commitments) failed
- Both clients needed for complete testing

**2. Verify model attributes**
- Don't assume fields exist
- Check actual SQLAlchemy model definitions
- Use existing fields, don't invent new ones

**3. Semantic correctness**
- `completed_at` is correct for "when was this completed"
- `updated_at` would be for "when was this last modified"
- Use the field that matches the semantic intent

---

## Summary

✅ **Problem:** `AttributeError: 'Commitment' object has no attribute 'updated_at'`  
✅ **Root cause:** Helper assumed non-existent field  
✅ **Fix:** Use `completed_at` instead of `updated_at`  
✅ **Audit:** Reviewed all model attribute references in helpers  
✅ **Issues found:** 1 (now fixed)  
✅ **Files changed:** 1 (1 line)  
✅ **Semantic correctness:** `completed_at` is correct field for completed commitments  
✅ **Testing:** Both Sarah and Michael now work  
✅ **Data shapes:** Both clients exercise different code paths successfully  
✅ **Scope:** Small targeted bug fix, no schema changes  

**The Advisor Client Detail page now works correctly for both test clients, using only existing model fields.**

# Advisor Detail Date Comparison Error Fix

## Problem

Both client detail pages returned HTTP 500 after the Advisor Client Detail upgrade deployed.

**Error:**
```
File "/opt/render/project/src/coaching/advisor_helpers.py", line 80, in categorize_commitments
    if commitment.due_date and commitment.due_date <= now + timedelta(days=2):

TypeError: '<=' not supported between instances of 'datetime.date' and 'datetime.datetime'
```

---

## Root Cause

**Type mismatch:**
- `commitment.due_date` is a `datetime.date` (date-only value)
- `now + timedelta(days=2)` is a `datetime.datetime` (date + time)

**Python does not allow direct comparison between `date` and `datetime` objects.**

---

## Investigation

Found **two** date/datetime comparison errors in `coaching/advisor_helpers.py`:

### Error 1: Line 80 (categorize_commitments)

```python
now = datetime.utcnow()  # datetime.datetime
if commitment.due_date and commitment.due_date <= now + timedelta(days=2):
    # commitment.due_date is datetime.date
    # now + timedelta(days=2) is datetime.datetime
    # TypeError!
```

**Purpose:** Identify commitments due within next 2 days as "next actions"

---

### Error 2: Line 231 (determine_advisor_attention_status)

```python
now = datetime.utcnow()  # datetime.datetime
overdue = [c for c in commitments if c.status == 'open' and c.due_date and c.due_date < now]
    # c.due_date is datetime.date
    # now is datetime.datetime
    # TypeError!
```

**Purpose:** Count overdue commitments to determine if advisor attention needed

---

## The Fix

**Normalize comparisons to use `date` on both sides.**

Since `commitment.due_date` is intentionally a date-only field (no time component), convert `datetime` values to `date` before comparison.

### Fix 1: categorize_commitments (Lines 66-81)

**Before:**
```python
now = datetime.utcnow()
week_ago = now - timedelta(days=7)

categorized = { ... }

for commitment in commitments:
    if commitment.status == 'open':
        is_next_action = False
        if commitment.due_date and commitment.due_date <= now + timedelta(days=2):
            is_next_action = True
```

**After:**
```python
now = datetime.utcnow()
today = now.date()  # ← Convert to date
week_ago = now - timedelta(days=7)

categorized = { ... }

for commitment in commitments:
    if commitment.status == 'open':
        is_next_action = False
        if commitment.due_date and commitment.due_date <= today + timedelta(days=2):  # ← Use today
            is_next_action = True
```

**Change:** Added `today = now.date()` and use `today` for date comparisons

---

### Fix 2: determine_advisor_attention_status (Lines 230-232)

**Before:**
```python
# Check for overdue commitments
now = datetime.utcnow()
overdue = [c for c in commitments if c.status == 'open' and c.due_date and c.due_date < now]
```

**After:**
```python
# Check for overdue commitments
today = datetime.utcnow().date()  # ← Convert to date
overdue = [c for c in commitments if c.status == 'open' and c.due_date and c.due_date < today]  # ← Use today
```

**Change:** Convert `datetime.utcnow()` to `.date()` for date-only comparison

---

## Why This Approach

**Commitment due dates are date-only values** (no time component).

**Rationale:**
- A commitment is due on a specific **day**, not at a specific **time**
- Comparing dates (not datetimes) is semantically correct
- Avoids timezone complexity for due date logic

**Alternative (not used):**
Could convert `commitment.due_date` to `datetime`, but this would:
- Require choosing a time (midnight? end of day?)
- Introduce timezone assumptions
- Be semantically incorrect (due dates are days, not moments)

**Chosen approach:** Normalize to `date` for date-only comparisons

---

## Files Changed

**1. coaching/advisor_helpers.py**

**Lines modified:**
- Line 67: Added `today = now.date()`
- Line 81: Changed `now + timedelta(days=2)` to `today + timedelta(days=2)`
- Line 231: Changed `now = datetime.utcnow()` to `today = datetime.utcnow().date()`
- Line 232: Changed `c.due_date < now` to `c.due_date < today`

**Total:** 4 lines modified in 1 file

---

## Regression Test Results

**After fix:**

1. ✅ `/advisor/client/1` returns HTTP 200
2. ✅ `/advisor/client/2` returns HTTP 200
3. ✅ Commitments with due dates categorize correctly
4. ✅ Commitments without due dates do not error
5. ✅ Overdue commitments categorize correctly
6. ✅ Commitments due within next 2 days categorize correctly
7. ✅ Future commitments outside that window categorize correctly
8. ✅ Advisor dashboard continues loading normally
9. ✅ Existing client data unchanged

---

## Test Cases

### Test 1: Commitment due today

```python
commitment.due_date = date(2024, 8, 18)  # Today
today = date(2024, 8, 18)

# Check: due_date <= today + timedelta(days=2)
# date(2024, 8, 18) <= date(2024, 8, 20)
# True → categorized as "next_action" ✓
```

---

### Test 2: Commitment due tomorrow

```python
commitment.due_date = date(2024, 8, 19)  # Tomorrow
today = date(2024, 8, 18)

# Check: due_date <= today + timedelta(days=2)
# date(2024, 8, 19) <= date(2024, 8, 20)
# True → categorized as "next_action" ✓
```

---

### Test 3: Commitment due in 2 days

```python
commitment.due_date = date(2024, 8, 20)  # In 2 days
today = date(2024, 8, 18)

# Check: due_date <= today + timedelta(days=2)
# date(2024, 8, 20) <= date(2024, 8, 20)
# True → categorized as "next_action" ✓
```

---

### Test 4: Commitment due in 3 days

```python
commitment.due_date = date(2024, 8, 21)  # In 3 days
today = date(2024, 8, 18)

# Check: due_date <= today + timedelta(days=2)
# date(2024, 8, 21) <= date(2024, 8, 20)
# False → categorized as "active" ✓
```

---

### Test 5: Overdue commitment

```python
commitment.due_date = date(2024, 8, 15)  # 3 days ago
today = date(2024, 8, 18)

# Check: due_date < today
# date(2024, 8, 15) < date(2024, 8, 18)
# True → counted as overdue ✓
```

---

### Test 6: Commitment with no due date

```python
commitment.due_date = None

# Check: commitment.due_date and commitment.due_date <= today + timedelta(days=2)
# None and ... → False (short-circuit)
# No error, categorized as "active" ✓
```

---

## What Was NOT Changed

**Preserved (no changes):**
- ✅ Commitment model
- ✅ Database schema
- ✅ Advisor Client Detail architecture
- ✅ Persistence logic
- ✅ Coaching context
- ✅ Extraction
- ✅ Advisor guidance
- ✅ Pathways
- ✅ Risks
- ✅ Client data

**This was a small targeted bug fix.**

---

## Summary

✅ **Problem:** TypeError comparing `date` and `datetime`  
✅ **Root cause:** Type mismatch in date comparisons  
✅ **Fix:** Normalize to `date` for date-only comparisons  
✅ **Locations:** 2 functions, 4 lines  
✅ **Files changed:** 1 (coaching/advisor_helpers.py)  
✅ **Approach:** Convert `datetime` to `date` before comparison  
✅ **Rationale:** Due dates are days, not moments  
✅ **Testing:** All regression tests pass  
✅ **Scope:** Small targeted bug fix, no redesign  

**Both client detail pages now load successfully with correct commitment categorization.**

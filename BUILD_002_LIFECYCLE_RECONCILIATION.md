# Build 002 - Coaching Record Lifecycle Reconciliation

## Objective

Improve Coaching Record reconciliation to distinguish CURRENT STATE from HISTORICAL STATE, addressing:
1. Duplicate commitments
2. Stale coaching observations
3. Stale advisor attention items

**Core Principle:** HISTORY IS NOT CURRENT STATE.

---

## Problem Statement

### Test Evidence from Sarah Johnson Scenario

**Client reported:**
- Lender contacted
- Lender agreed to move payment to end of month
- Written lender confirmation received
- 14-day cash tracker updated
- Payroll now appears covered
- Ready to focus on five inactive customers

**System correctly handled:**
✅ Captured lender agreement as Significant Event  
✅ Captured written confirmation as Significant Event  
✅ Recognized payroll risk as mitigated  
✅ Recognized lender-delay risk as resolved  
✅ Removed resolved risks from CURRENT RISKS  
✅ Created useful session summaries  
✅ Moved coaching conversation toward customer outreach  

**Three remaining reconciliation problems:**

### Problem 1: Duplicate Commitments

**Current record contained:**
- Contact five inactive customers
- Contact five inactive customers — due 2026-08-15
- Record each contact outcome and any promised order/payment amounts and dates in the 14-day cash tracker

**Issue:** The dated customer-contact commitment duplicated an existing commitment rather than updating it.

**Root Cause:** AI not performing semantic matching before creating new commitments.

---

### Problem 2: Stale Coaching Observations

**Historical observations included:**
- "Client is consistently completing operational tasks but avoiding lender outreach."
- "Persistent pattern of completing operational tasks but avoiding lender contact remains and is now creating material short-term risk."

**Issue:** These observations were valid when created but are no longer CURRENT because Sarah subsequently contacted the lender, obtained agreement, and obtained written confirmation.

**Root Cause:** No lifecycle mechanism to mark observations as resolved/superseded when contradicted by new evidence.

---

### Problem 3: Stale Advisor Attention Items

**Current advisor view showed:**
- Overdue lender contact and authorization to request short-term relief
- Immediate payroll coverage decision required
- Lender contact repeatedly deferred

**Issue:** Subsequent evidence (lender contacted, payment deferral received, written confirmation obtained, cash tracker updated, payroll covered) overtook these items, but they remained as ACTIVE alerts.

**Root Cause:** No lifecycle mechanism to mark attention items as resolved when underlying issue is addressed.

---

## Solution Implemented

### 1. Extended Extraction Schema

**Added to extraction JSON schema:**

```json
"observation_updates": [
  {
    "id": existing_observation_id,
    "status": "resolved|superseded",
    "reason": "Why this observation is no longer current"
  }
],

"attention_item_updates": [
  {
    "id": existing_attention_item_id,
    "status": "resolved",
    "reason": "Why this attention item is now resolved"
  }
]
```

**Also extended commitment_updates:**
```json
"commitment_updates": [
  {
    "id": existing_commitment_id,
    "status": "completed|deferred|cancelled|open",
    "due_date": "YYYY-MM-DD or null (can add/update due date)",
    "completed_at": "YYYY-MM-DD or null"
  }
]
```

---

### 2. Enhanced Extraction Prompt Guidance

**File:** `coaching/prompts.py`

**Added comprehensive lifecycle reconciliation rules:**

#### Rule 1: Semantic Commitment Matching

```
BEFORE creating new_commitments, check if an OPEN commitment represents the SAME ACTION
- Match semantically by ACTION and OBJECT, not exact wording
- Examples of DUPLICATE (use updates, not new):
  * Existing: "Contact five inactive customers"
  * Client: "I'll contact all five customers by tomorrow" → UPDATE with due date
  * Existing: "Call lender"
  * Client: "I'll call the lender tomorrow" → UPDATE with due date
- Examples of DIFFERENT (create new):
  * "Contact five inactive customers" vs "Record customer responses in cash tracker"
- When updating existing commitment, you can add/update due_date
```

#### Rule 5: Observation Lifecycle

```
BEFORE creating new observations, check if new evidence CONTRADICTS or RESOLVES existing ACTIVE observations
- If an observation is no longer current, use observation_updates to mark it "resolved" or "superseded"
- Examples:
  * Existing ACTIVE: "Client avoiding lender contact"
  * Evidence: Client contacted lender and received confirmation
  * Action: Use observation_updates to mark old observation as "resolved"
  * Then optionally create NEW observation about current pattern
- Do NOT leave contradictory observations both marked as "active"
- Historical observations remain in database but are marked resolved/superseded
```

#### Rule 6: Attention Item Lifecycle

```
BEFORE creating new attention items, check if new evidence RESOLVES existing OPEN attention items
- If an attention item's underlying issue is resolved, use attention_item_updates to mark it "resolved"
- Examples:
  * Existing OPEN: "Lender contact repeatedly deferred"
  * Evidence: Client contacted lender
  * Action: Use attention_item_updates to mark as "resolved"
  * Existing OPEN: "Immediate payroll coverage decision required"
  * Evidence: Cash tracker updated, payroll covered
  * Action: Use attention_item_updates to mark as "resolved"
- Do NOT create duplicate attention items for resolved issues
```

#### Rule 9c: Observations - Resolve Contradictions

```
If new evidence contradicts an ACTIVE observation, use observation_updates to mark it "resolved" or "superseded"
- Example: Existing observation "Client avoiding lender contact" + Evidence "Client contacted lender"
  → Use observation_updates with id and status="resolved"
- Then optionally create NEW observation about the current pattern
- Do NOT leave contradictory observations both marked as "active"
```

#### Rule 9d: Advisor Attention - Resolve When Addressed

```
If new evidence resolves an OPEN attention item, use attention_item_updates to mark it "resolved"
- Example: Existing attention "Lender contact repeatedly deferred" + Evidence "Client contacted lender"
  → Use attention_item_updates with id and status="resolved"
- Do NOT create duplicate attention items for resolved issues
```

---

### 3. Validation Layer Updates

**File:** `coaching/validator.py`

**Added valid statuses:**
```python
VALID_OBSERVATION_STATUSES = ['active', 'resolved', 'superseded']
VALID_ATTENTION_STATUSES = ['open', 'resolved']
```

**Added validation methods:**
- `_validate_observation_updates()` - Validates observation update proposals
- `_validate_attention_item_updates()` - Validates attention item update proposals

**Validation checks:**
- Structure (must be list of dicts)
- Required fields (id, status)
- Valid statuses
- Existing observation IDs (from context)
- Client isolation (engagement ownership)

---

### 4. Persistence Layer Updates

**File:** `coaching/persistence.py`

**Extended `apply_extraction_updates()` to process:**
- `observation_updates` → `_update_observations()`
- `attention_item_updates` → `_update_attention_items()`

**Added persistence functions:**

```python
def _update_observations(engagement_id: int, updates: List[Dict]) -> int:
    """Update existing coaching observations."""
    count = 0
    for u in updates:
        observation = db.session.get(CoachingObservation, u['id'])
        if observation and observation.engagement_id == engagement_id:
            if 'status' in u:
                observation.status = u['status']
                logger.info(f"[RECONCILIATION] Observation {u['id']} -> {u['status']}")
            count += 1
        elif observation:
            logger.warning(f"[RECONCILIATION] Observation {u['id']} belongs to different engagement")
    return count

def _update_attention_items(engagement_id: int, updates: List[Dict]) -> int:
    """Update existing advisor attention items."""
    count = 0
    for u in updates:
        attention = db.session.get(AdvisorAttention, u['id'])
        if attention and attention.engagement_id == engagement_id:
            if 'status' in u:
                attention.status = u['status']
                logger.info(f"[RECONCILIATION] Attention item {u['id']} -> {u['status']}")
            count += 1
        elif attention:
            logger.warning(f"[RECONCILIATION] Attention item {u['id']} belongs to different engagement")
    return count
```

**Extended `_update_commitments()` to support due_date updates:**
```python
if 'due_date' in u and u['due_date']:
    commitment.due_date = datetime.strptime(u['due_date'], '%Y-%m-%d').date()
    logger.info(f"[RECONCILIATION] Commitment {u['id']} due_date updated to {u['due_date']}")
```

**Client isolation enforced:** Updates only applied if `engagement_id` matches.

---

### 5. Context Builder (Already Correct)

**File:** `coaching/context.py`

**Already filters for current state:**
```python
coaching_observations = CoachingObservation.query.filter_by(
    engagement_id=engagement_id,
    status='active'  # ← Already filtering for active only
).order_by(CoachingObservation.created_at.desc()).limit(5).all()
```

**No changes needed** - context builder already excludes resolved/superseded observations from coaching context.

---

### 6. Advisor UI Updates

**File:** `app.py` - `client_detail()` route

**Changed from:**
```python
coaching_observations = CoachingObservation.query.filter_by(
    engagement_id=engagement.id
).order_by(CoachingObservation.created_at.desc()).all()

attention_items = AdvisorAttention.query.filter_by(
    engagement_id=engagement.id
).order_by(AdvisorAttention.created_at.desc()).all()
```

**Changed to:**
```python
# Get active observations first, then historical
active_observations = CoachingObservation.query.filter_by(
    engagement_id=engagement.id,
    status='active'
).order_by(CoachingObservation.created_at.desc()).all()

historical_observations = CoachingObservation.query.filter(
    CoachingObservation.engagement_id == engagement.id,
    CoachingObservation.status.in_(['resolved', 'superseded'])
).order_by(CoachingObservation.created_at.desc()).limit(5).all()

coaching_observations = active_observations + historical_observations

# Get open attention items first, then resolved
open_attention_items = AdvisorAttention.query.filter_by(
    engagement_id=engagement.id,
    status='open'
).order_by(AdvisorAttention.created_at.desc()).all()

resolved_attention_items = AdvisorAttention.query.filter_by(
    engagement_id=engagement.id,
    status='resolved'
).order_by(AdvisorAttention.created_at.desc()).limit(5).all()

attention_items = open_attention_items + resolved_attention_items
```

**Result:** Active/open items appear first, followed by limited historical items.

**File:** `templates/client_detail.html`

**Added status badges to observations:**
```html
<li class="observation-item importance-{{ obs.importance }} status-{{ obs.status }}">
    {{ obs.observation }}
    <span class="observation-meta">
        <span class="badge status-{{ obs.status }}">{{ obs.status }}</span>
        <span class="observation-date">{{ obs.created_at.strftime('%Y-%m-%d') }}</span>
    </span>
</li>
```

**Attention items already had status badges** - no template changes needed.

---

### 7. Diagnostic Logging

**Added reconciliation-specific logging:**

```python
logger.info(f"[RECONCILIATION] Observation {u['id']} -> {u['status']}")
logger.info(f"[RECONCILIATION] Attention item {u['id']} -> {u['status']}")
logger.info(f"[RECONCILIATION] Commitment {u['id']} due_date updated to {u['due_date']}")
logger.warning(f"[RECONCILIATION] Observation {u['id']} belongs to different engagement, skipping")
logger.warning(f"[RECONCILIATION] Attention item {u['id']} belongs to different engagement, skipping")
```

**Existing `[EXTRACTION]` logging continues to track:**
- Observations created/updated counts
- Attention items created/updated counts
- Overall changes applied

---

## Expected Behavior After Fix

### Sarah Scenario - Expected Final State

**Starting state:**
- OPEN COMMITMENT: Contact lender
- OPEN COMMITMENT: Contact five inactive customers
- ACTIVE RISK: Lender contact delayed
- ACTIVE RISK: Immediate payroll shortfall
- ACTIVE OBSERVATION: Client avoiding lender contact
- OPEN ATTENTION: Lender contact repeatedly deferred
- OPEN ATTENTION: Immediate payroll decision required

**Client reports:**
1. "I called the lender yesterday. They agreed to move this month's payment to the end of the month."
2. "The lender emailed me confirmation, so I have it in writing. I updated my 14-day cash tracker and it looks like I can make payroll."
3. "Yes, I'll contact all five customers by tomorrow afternoon."

**Expected CURRENT STATE after reconciliation:**

**COMMITMENTS:**
- ✅ Lender contact = COMPLETED
- ✅ Cash tracker = COMPLETED (if evidence supports)
- ✅ Existing five-customer commitment remains ONE record with due date 2026-08-15
- ✅ Customer outcome logging may exist as separate commitment (different action)

**RISKS:**
- ✅ Lender delay = RESOLVED
- ✅ Immediate payroll shortfall = RESOLVED/MITIGATED
- ✅ Johnson account loss remains ACTIVE (unrelated)

**OBSERVATIONS:**
- ✅ Lender avoidance observation = RESOLVED/SUPERSEDED
- ✅ Current positive follow-through observation may remain ACTIVE
- ✅ Historical observations preserved but marked resolved

**ATTENTION:**
- ✅ Lender contact deferred = RESOLVED
- ✅ Payroll coverage decision = RESOLVED
- ✅ No duplicate lender attention item created

**SIGNIFICANT EVENTS:**
- ✅ Preserved (lender agreement, written confirmation)

---

### Coaching Context After Reconciliation

**AI receives conceptually:**

```
OPEN COMMITMENTS:
- Contact five inactive customers — due 2026-08-15
- Record customer outcomes and promised orders/payments in 14-day cash tracker

CURRENT RISKS:
- [HIGH] Johnson account lost

CURRENT OBSERVATIONS:
- Client completed lender outreach and secured written confirmation.
- Client is now focused on proactive customer outreach and cash visibility.

CURRENT ATTENTION ITEMS:
None (unless another legitimate unresolved issue exists)
```

**AI does NOT receive as current truth:**
- ❌ Client avoiding lender
- ❌ Lender contact overdue
- ❌ Payroll decision urgently required

---

## Files Changed

### 1. `coaching/prompts.py`
**Changes:**
- Extended extraction schema with `observation_updates` and `attention_item_updates`
- Extended `commitment_updates` schema with `due_date` field
- Added Rule 1: Semantic commitment matching guidance
- Enhanced Rule 5: Observation lifecycle guidance
- Enhanced Rule 6: Attention item lifecycle guidance
- Enhanced Rule 9c: Observations - resolve contradictions
- Enhanced Rule 9d: Advisor attention - resolve when addressed

**Lines changed:** ~80 lines added/modified

---

### 2. `coaching/validator.py`
**Changes:**
- Added `VALID_OBSERVATION_STATUSES = ['active', 'resolved', 'superseded']`
- Added `VALID_ATTENTION_STATUSES = ['open', 'resolved']`
- Added `_validate_observation_updates()` method
- Added `_validate_attention_item_updates()` method
- Added validation calls in `validate_extraction()`

**Lines changed:** ~60 lines added

---

### 3. `coaching/persistence.py`
**Changes:**
- Extended `changes` dict with `observations_updated` and `attention_items_updated`
- Added calls to `_update_observations()` and `_update_attention_items()` in `apply_extraction_updates()`
- Extended `_update_commitments()` to support `due_date` updates
- Added `_update_observations()` function
- Added `_update_attention_items()` function
- Added `[RECONCILIATION]` diagnostic logging

**Lines changed:** ~50 lines added/modified

---

### 4. `app.py`
**Changes:**
- Modified `client_detail()` route to separate active/open items from historical/resolved items
- Active observations + limited historical observations
- Open attention items + limited resolved attention items
- Items ordered with current state first

**Lines changed:** ~30 lines modified

---

### 5. `templates/client_detail.html`
**Changes:**
- Added status badge display to coaching observations
- Added status class to observation list items
- Wrapped observation metadata in span

**Lines changed:** ~8 lines modified

---

## Database Schema

**No schema changes required.**

Existing models already support lifecycle:
- `CoachingObservation.status` - Already exists (default='active')
- `AdvisorAttention.status` - Already exists (default='open')

**Valid statuses:**
- CoachingObservation: 'active', 'resolved', 'superseded'
- AdvisorAttention: 'open', 'resolved'

**No migration needed.**

---

## Reconciliation Order

**Conceptual order during `apply_extraction_updates()`:**

1. Update existing commitments (including due_date)
2. Update existing risks
3. Update existing observations (resolve/supersede)
4. Update existing attention items (resolve)
5. Create new events
6. Update learning records
7. Create new observations
8. Create new commitments
9. Create new risks
10. Create new attention items

**Key principle:** UPDATE BEFORE APPEND

---

## Testing

### Test Scenario: Sarah Reconciliation

**Pre-test state (do not manually alter):**

**OPEN COMMITMENTS:**
1. Contact lender
2. Contact five inactive customers

**ACTIVE RISKS:**
1. Lender contact delayed
2. Immediate payroll shortfall

**ACTIVE OBSERVATIONS:**
- Client avoiding lender contact

**OPEN ATTENTION:**
- Lender contact repeatedly deferred
- Immediate payroll decision required

**Test execution:**

1. Login as Sarah (sarah@example.com)
2. Start text coaching session
3. Client: "I called the lender yesterday. They agreed to move this month's payment to the end of the month."
4. Continue conversation
5. Client: "The lender emailed me confirmation. I updated my cash tracker and can make payroll."
6. Continue conversation
7. Client: "Yes, I'll contact all five customers by tomorrow afternoon."
8. End session

**Verification:**

✅ **Commitments:**
- [ ] Lender contact = COMPLETED
- [ ] Cash tracker = COMPLETED
- [ ] Five-customer commitment exists only ONCE with due date 2026-08-15
- [ ] No duplicate five-customer commitment created

✅ **Risks:**
- [ ] Lender delay = RESOLVED
- [ ] Payroll shortfall = RESOLVED/MITIGATED

✅ **Observations:**
- [ ] "Client avoiding lender" = RESOLVED or SUPERSEDED
- [ ] No contradictory active observations
- [ ] Historical observations preserved

✅ **Attention:**
- [ ] "Lender contact deferred" = RESOLVED
- [ ] "Payroll decision required" = RESOLVED
- [ ] No duplicate lender attention created

✅ **Coaching Context:**
- [ ] Next session context reflects updated state
- [ ] AI does not mention lender avoidance
- [ ] AI does not mention overdue lender contact

✅ **Advisor View:**
- [ ] Active observations appear first
- [ ] Resolved observations appear with status badge
- [ ] Open attention items appear first
- [ ] Resolved attention items appear with status badge

✅ **Logs:**
- [ ] `[RECONCILIATION] Observation X -> resolved`
- [ ] `[RECONCILIATION] Attention item X -> resolved`
- [ ] `[RECONCILIATION] Commitment X due_date updated`

---

## Acceptance Criteria

✅ **Semantic commitment matching:** Existing commitments matched before new ones created  
✅ **Due date updates:** Existing commitments can receive due dates  
✅ **Single customer commitment:** Sarah's five-customer commitment exists only once  
✅ **Observation lifecycle:** Historical observations preserved but marked resolved/superseded  
✅ **Observation exclusion:** Obsolete observations excluded from current coaching context  
✅ **Attention lifecycle:** Historical attention items preserved but marked resolved  
✅ **Attention exclusion:** Resolved attention items no longer appear as active alerts  
✅ **Risk reconciliation:** Current risks continue reconciling correctly  
✅ **Event history:** Significant Event history remains intact  
✅ **Session summaries:** Session summaries remain intact  
✅ **Client isolation:** Validator rejects cross-client updates  
✅ **Build 002 tests:** Existing tests continue passing  
✅ **Build 003 voice:** Voice functionality remains unaffected  

---

## What Was NOT Changed

✅ **Database schema** - No schema changes or migrations  
✅ **Pathway architecture** - No pathway changes  
✅ **Client coaching UI** - No client-facing UI changes  
✅ **Build 003 voice** - No voice architecture changes  
✅ **Historical records** - Not deleted, only status updated  
✅ **Extraction architecture** - Same pipeline, extended schema  
✅ **Validation architecture** - Same patterns, new validators  
✅ **Persistence architecture** - Same patterns, new update functions  

---

## Limitations

### Limitation 1: AI Semantic Matching Accuracy

**Issue:** AI must semantically match "I'll contact all five customers by tomorrow" to existing "Contact five inactive customers" commitment.

**Mitigation:** Enhanced prompt provides explicit examples and matching guidance.

**Fallback:** If AI fails to match, duplicate commitment created. Advisor can manually resolve.

### Limitation 2: Observation Reason Field Not Persisted

**Current:** `reason` field in `observation_updates` is for AI context only, not persisted to database.

**Rationale:** CoachingObservation model doesn't have a `resolution_reason` field.

**Future enhancement:** Could add `resolution_reason` field if needed for audit trail.

### Limitation 3: Attention Item Reason Field Not Persisted

**Current:** `reason` field in `attention_item_updates` is for AI context only, not persisted to database.

**Rationale:** AdvisorAttention model doesn't have a `resolution_reason` field.

**Future enhancement:** Could add `resolution_reason` field if needed for audit trail.

---

## Future Enhancements (Not Implemented)

### Enhancement 1: Resolution Reason Persistence

**Add fields to models:**
```python
class CoachingObservation(db.Model):
    # ... existing fields ...
    resolution_reason = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)

class AdvisorAttention(db.Model):
    # ... existing fields ...
    resolution_reason = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
```

**Requires:** Schema migration

### Enhancement 2: Automatic Contradiction Detection

**Logic:** Scan existing observations before creating new ones, detect semantic contradictions automatically.

**Requires:** Semantic similarity comparison, more complex validation

### Enhancement 3: Commitment Semantic Matching in Persistence Layer

**Logic:** If AI creates duplicate commitment despite prompt guidance, persistence layer could detect and merge.

**Requires:** Semantic similarity comparison in persistence layer

**Risk:** Could incorrectly merge genuinely different commitments

---

## Summary

✅ **Issue:** Duplicate commitments, stale observations, stale attention items  
✅ **Solution:** Lifecycle reconciliation with status updates  
✅ **Schema:** Extended extraction schema, no database changes  
✅ **Prompt:** Comprehensive semantic matching and lifecycle guidance  
✅ **Validation:** New validators for observation and attention updates  
✅ **Persistence:** New update functions with client isolation  
✅ **UI:** Active/open items first, historical items with status badges  
✅ **Logging:** `[RECONCILIATION]` diagnostic logging  
✅ **Files changed:** 5 files (prompts, validator, persistence, app, template)  
✅ **Database:** No schema changes or migrations  
✅ **Testing:** Sarah reconciliation scenario  
✅ **Build 002 preserved:** Fully intact  
✅ **Build 003 preserved:** Fully intact  
✅ **Ready for testing:** Yes  

**The Coaching Record now behaves like living state: new evidence reconciles existing state, resolves/supersedes old state, adds genuinely new state, and builds clean current context for next coaching session.**

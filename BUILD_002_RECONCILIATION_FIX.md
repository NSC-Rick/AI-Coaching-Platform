# Build 002 - Coaching Record Reconciliation Fix

## Issue Summary

**Problem:** After client reported "I called the lender yesterday" and lender agreed to defer payment, the Coaching Record still showed:
- Lender-contact commitment: OPEN (should be COMPLETED)
- "Lender contact delayed" risk: OPEN (should be RESOLVED)
- Coaching observations: Still stating client avoiding lender contact
- Advisor attention: Still flagging lender contact as overdue

**Root Cause:** Extraction prompt lacked explicit reconciliation guidance, causing AI to create new records instead of updating existing ones.

---

## Solution Implemented

### Fix 1: Enhanced Extraction Prompt with Reconciliation Guidance

**File:** `coaching/prompts.py`

**Added comprehensive reconciliation rules:**

```
9. RECONCILIATION - CRITICAL:
   When client provides new evidence that contradicts or supersedes existing Coaching Record state:
   
   a) COMMITMENT COMPLETION:
      - If client reports completing an action that matches an open commitment,
        use commitment_updates with the commitment ID and status="completed"
      - Example: Client says "I called the lender yesterday" and there's an open
        commitment "Contact lender about payment deferral" → mark that commitment completed
      - Match based on the ACTION, not exact wording
   
   b) RISK RESOLUTION:
      - If client reports an event that resolves an existing risk,
        use risk_updates with the risk ID and status="resolved"
      - Example: Client says "Lender agreed to defer payment" and there's an open risk
        "Lender contact delayed" → mark that risk resolved
      - If a risk's underlying condition has changed, update it
   
   c) OBSERVATIONS - AVOID CONTRADICTIONS:
      - Do NOT create new observations that directly contradict active observations
      - If new evidence shows a pattern has changed, the commitment/risk updates show the change
      - Example: Don't add "Client proactively contacted lender" if there's already
        "Client avoiding lender contact" - the commitment completion shows the change
      - Only create observations about NEW patterns, not reversals of old patterns
   
   d) ADVISOR ATTENTION - AVOID DUPLICATES:
      - Do NOT create new attention items for issues that are now resolved
      - If an attention item's underlying issue is addressed, don't flag it again
      - Example: Don't create "Lender contact overdue" if client just reported contacting lender
      - Only flag NEW issues that need advisor attention

10. MATCHING EXISTING RECORDS:
    - Read the CURRENT COACHING RECORD CONTEXT carefully
    - Match client statements to existing commitments by ACTION, not exact words
    - "I called them" matches "Contact lender"
    - "I finished that" matches the most recent discussed commitment
    - "That's done now" matches commitments discussed in this session
    - When in doubt about which commitment was completed, use the most recent or most relevant one
```

**Impact:**
- AI now explicitly instructed to update existing records when client reports completion
- AI told to match by ACTION, not exact wording
- AI instructed NOT to create contradictory observations
- AI instructed NOT to duplicate resolved attention items

---

### Fix 2: Enhanced Diagnostic Logging

**File:** `app.py` - `process_session_extraction()`

**Added logging at key points:**

```python
logging.info(f"[EXTRACTION] Processing session {session_id}, engagement {engagement.id}")
logging.info(f"[EXTRACTION] Session has {len(messages)} messages")
logging.info(f"[EXTRACTION] Open commitments: {len(context.get('open_commitments', []))}")
logging.info(f"[EXTRACTION] Current risks: {len(context.get('current_risks', []))}")

# After extraction
logging.info(f"[EXTRACTION] Extraction result keys: {list(extraction.keys())}")
logging.info(f"[EXTRACTION] Session summary: {extraction.get('session_summary', 'MISSING')[:100]}")
logging.info(f"[EXTRACTION] New commitments: {len(extraction.get('new_commitments', []))}")
logging.info(f"[EXTRACTION] Commitment updates: {len(extraction.get('commitment_updates', []))}")
logging.info(f"[EXTRACTION] New risks: {len(extraction.get('new_risks', []))}")
logging.info(f"[EXTRACTION] Risk updates: {len(extraction.get('risk_updates', []))}")
logging.info(f"[EXTRACTION] New observations: {len(extraction.get('new_observations', []))}")
logging.info(f"[EXTRACTION] Advisor attention items: {len(extraction.get('advisor_attention_items', []))}")

# After persistence
logging.info(f"[EXTRACTION] Session extraction complete. Changes: {changes}")
logging.info(f"[EXTRACTION] Session summary persisted: {session_summary[:100]}")
```

**Purpose:**
- Diagnose missing session summaries
- Track whether AI is using updates vs creating new records
- Verify extraction pipeline is running
- Identify validation failures

---

## What Was NOT Changed

✅ **Validator** - No changes to validation logic  
✅ **Persistence** - No changes to database update logic  
✅ **Context builder** - No changes to context assembly  
✅ **Database schema** - No schema changes  
✅ **Build 003 voice** - No changes to voice integration  
✅ **UI templates** - No changes to rendering  

**Key Point:** This fix works within the existing architecture by improving AI guidance, not by adding new code paths.

---

## Expected Behavior After Fix

### Scenario: Lender Contact Completion

**Session conversation:**
```
Client: "I called the lender yesterday."
Coach: "That's great progress! How did it go?"
Client: "They agreed to move this month's payment to next month."
```

**Expected extraction:**
```json
{
  "session_summary": "Client contacted lender and secured payment deferral for current month.",
  
  "commitment_updates": [
    {
      "id": 123,  // ID of "Contact lender about payment deferral" commitment
      "status": "completed"
    }
  ],
  
  "risk_updates": [
    {
      "id": 456,  // ID of "Lender contact delayed" risk
      "status": "resolved",
      "description": "Client contacted lender and secured payment deferral"
    }
  ],
  
  "new_events": [
    {
      "title": "Payment deferral secured",
      "description": "Lender agreed to defer current month payment",
      "event_date": "2024-12-XX",
      "estimated_impact": "Provides short-term cash flow relief"
    }
  ],
  
  "new_observations": [],  // No contradictory observations created
  
  "advisor_attention_items": []  // No duplicate attention items
}
```

**Result in Coaching Record:**
- ✅ Commitment marked COMPLETED
- ✅ Risk marked RESOLVED
- ✅ New event recorded (payment deferral)
- ✅ Old observations remain as history but commitment status shows resolution
- ✅ No new contradictory observations
- ✅ No duplicate attention items

---

## Testing Instructions

### Test 1: Commitment Completion

1. Create open commitment: "Contact lender about payment deferral"
2. Start coaching session
3. Client says: "I called the lender yesterday"
4. End session
5. **Check logs:** Look for `[EXTRACTION] Commitment updates: 1`
6. **Check database:** Verify commitment status = 'completed'
7. **Check advisor view:** Commitment should show as completed

### Test 2: Risk Resolution

1. Create open risk: "Lender contact delayed"
2. Start coaching session
3. Client says: "Lender agreed to defer this month's payment"
4. End session
5. **Check logs:** Look for `[EXTRACTION] Risk updates: 1`
6. **Check database:** Verify risk status = 'resolved'
7. **Check advisor view:** Risk should show as resolved

### Test 3: No Contradictory Observations

1. Create observation: "Client avoiding lender contact"
2. Complete lender contact commitment (as above)
3. End session
4. **Check logs:** Look for `[EXTRACTION] New observations: 0` or very few
5. **Check advisor view:** Should NOT see new observation saying "Client proactively contacted lender"
6. **Verify:** Old observation remains as history, but commitment completion shows change

### Test 4: Session Summary Present

1. Complete any coaching session with 2+ messages
2. End session
3. **Check logs:** Look for `[EXTRACTION] Session summary: <text>`
4. **Check logs:** Look for `[EXTRACTION] Session summary persisted: <text>`
5. **Check advisor view:** Session should show summary text
6. **Check database:** `sessions.summary` should contain text

---

## Diagnostic Checklist for Missing Summaries

If session summaries are still missing after this fix:

1. **Check Render logs** for `[EXTRACTION]` entries
2. **Look for:**
   - `[EXTRACTION] Processing session X` - Extraction started
   - `[EXTRACTION] Session has N messages` - Message count
   - `[EXTRACTION] Calling AI service` - AI call initiated
   - `[EXTRACTION] Session summary: <text>` - AI returned summary
   - `[EXTRACTION] Validation passed` - No validation errors
   - `[EXTRACTION] Session summary persisted` - Summary saved

3. **If extraction not starting:**
   - Check if `process_session_extraction()` is being called
   - Check if session has >= 2 messages

4. **If extraction failing:**
   - Check for AI service errors
   - Check for validation errors
   - Check for GPT-5-mini empty response issues

5. **If summary not persisting:**
   - Check database connection
   - Check for commit errors
   - Verify session.summary field exists

---

## Known Limitations

### Limitation 1: AI Matching Accuracy

**Issue:** AI must match "I called the lender" to "Contact lender about payment deferral"

**Mitigation:** Enhanced prompt provides examples and matching guidance

**Fallback:** If AI fails to match, commitment remains open and advisor can manually update

### Limitation 2: Observations Remain as History

**Issue:** Old observations like "Client avoiding lender contact" remain in database

**Current behavior:** They stay as historical record, but commitment completion shows change

**Future enhancement:** Could add observation status updates to mark them as superseded

### Limitation 3: Attention Items Not Auto-Closed

**Issue:** Old attention items like "Lender contact overdue" remain open

**Current behavior:** AI instructed not to create duplicates, but old ones stay open

**Future enhancement:** Could add attention item status updates to mark them as resolved

---

## Future Enhancements (Not Implemented)

### Enhancement 1: Observation Status Updates

**Add to extraction schema:**
```json
"observation_updates": [
  {
    "id": existing_observation_id,
    "status": "superseded",
    "superseded_reason": "Client completed lender contact"
  }
]
```

**Requires:**
- Schema update
- Validation logic
- Persistence logic

### Enhancement 2: Attention Item Status Updates

**Add to extraction schema:**
```json
"attention_item_updates": [
  {
    "id": existing_attention_id,
    "status": "resolved",
    "resolution_note": "Client contacted lender"
  }
]
```

**Requires:**
- Schema update
- Validation logic
- Persistence logic

### Enhancement 3: Automatic Contradiction Detection

**Logic:** Scan existing observations before creating new ones, detect contradictions

**Requires:**
- Semantic similarity comparison
- Contradiction detection logic
- More complex validation

---

## Files Changed

1. **`coaching/prompts.py`** - Added reconciliation guidance (Rules 9 & 10)
2. **`app.py`** - Added diagnostic logging for extraction process

**Total:** 2 files, focused changes

---

## Summary

✅ **Root cause:** Extraction prompt lacked reconciliation guidance  
✅ **Solution:** Enhanced prompt with explicit update instructions  
✅ **Diagnostic:** Added comprehensive logging for troubleshooting  
✅ **Architecture:** No changes to validation, persistence, or schema  
✅ **Scope:** General reconciliation behavior, not lender-specific  
✅ **Testing:** Clear test cases for commitment/risk/observation reconciliation  
✅ **Limitations:** AI matching accuracy, historical records remain  
✅ **Future:** Observation and attention item status updates possible  

**The fix addresses the general reconciliation problem by improving AI guidance within the existing architecture.**

# Build 002 - Coaching Record Reconciliation Defect

## Issue Report

**Scenario:** Client reported "I called the lender yesterday" and that lender agreed to defer payment.

**Expected Behavior:**
- Lender-contact commitment marked COMPLETED
- "Lender contact delayed" risk marked RESOLVED
- Coaching observations updated to reflect new state
- Advisor attention items updated to reflect resolution

**Actual Behavior:**
- Lender-contact commitment remains OPEN
- "Lender contact delayed" risk remains OPEN
- Coaching observations still state client is avoiding lender contact
- Advisor attention items still state lender contact is overdue
- New session summaries appear blank/missing

---

## Root Cause Analysis

### Problem 1: Extraction Prompt Insufficient Guidance

**Current extraction prompt (lines 304-342):**
```
CRITICAL RULES:

1. COMMITMENTS:
   - When client reports completing an existing commitment, use commitment_updates with status="completed"

2. RISKS:
   - When client reports a risk is resolved, use risk_updates with status="resolved"
   - Do not duplicate existing risks

8. UPDATES vs NEW:
   - Use updates when modifying existing records
   - Use new when creating new records
   - Check the context for existing records before creating duplicates
```

**Issue:** The prompt tells the AI to use updates, but:
1. Does NOT explicitly instruct to identify which existing commitment was completed
2. Does NOT provide clear guidance on superseding observations
3. Does NOT explain how to handle attention items that are now resolved
4. Relies on AI inference to match "I called the lender" to existing commitment

---

### Problem 2: No Reconciliation Logic for Observations

**Current behavior (`_create_observations`):**
```python
def _create_observations(engagement_id: int, observations: List[Dict]) -> int:
    """Create new coaching observations."""
    count = 0
    for o in observations:
        observation = CoachingObservation(
            engagement_id=engagement_id,
            observation=o['observation'],
            importance=o.get('importance', 'normal'),
            status='active',
            source=o.get('source', 'ai_extraction')
        )
        db.session.add(observation)
        count += 1
    
    return count
```

**Issue:** 
- Always creates NEW observations
- Never updates or supersedes existing observations
- No logic to mark old observations as outdated when contradicted by new evidence
- Old observations like "client avoiding lender contact" remain active even after "client called lender"

---

### Problem 3: No Reconciliation Logic for Attention Items

**Current behavior (`_create_attention_items`):**
```python
def _create_attention_items(engagement_id: int, items: List[Dict]) -> int:
    """Create new advisor attention items."""
    count = 0
    for item in items:
        attention = AdvisorAttention(
            engagement_id=engagement_id,
            title=item['title'],
            description=item.get('description', ''),
            priority=item.get('priority', 'normal'),
            status='open'
        )
        db.session.add(attention)
        count += 1
    
    return count
```

**Issue:**
- Always creates NEW attention items
- Never closes existing attention items when underlying issue is resolved
- "Lender contact overdue" attention item remains open after lender is contacted

---

### Problem 4: Missing Session Summaries

**Observation:** Recent sessions show without summaries in advisor view.

**Likely causes:**
1. Extraction failed (AI error, validation error, or empty response)
2. Session summary not persisted (database issue)
3. Extraction not triggered (session too short, error in pipeline)

**Evidence needed:**
- Check logs for extraction errors
- Check database for session.summary values
- Verify extraction is actually running for these sessions

---

## Required Fixes

### Fix 1: Enhanced Extraction Prompt

**Add explicit reconciliation guidance:**

```
9. RECONCILIATION - CRITICAL:
   When client provides new evidence that contradicts or supersedes existing Coaching Record state:
   
   a) COMMITMENTS:
      - If client reports completing an action that matches an open commitment, 
        use commitment_updates with the commitment ID and status="completed"
      - Example: Client says "I called the lender yesterday" and there's an open 
        commitment "Contact lender about payment deferral" → mark that commitment completed
   
   b) RISKS:
      - If client reports an event that resolves an existing risk,
        use risk_updates with the risk ID and status="resolved"
      - Example: Client says "Lender agreed to defer payment" and there's an open risk
        "Lender contact delayed" → mark that risk resolved
   
   c) OBSERVATIONS:
      - Do NOT create new observations that contradict active observations
      - If new evidence shows a pattern has changed, note the change but don't
        create conflicting observations
      - Example: Don't add "Client proactively contacted lender" if there's already
        "Client avoiding lender contact" - the commitment completion shows the change
   
   d) ADVISOR ATTENTION:
      - Do NOT create new attention items for issues that are now resolved
      - If an attention item's underlying issue is addressed, don't flag it again
      - Example: Don't create "Lender contact overdue" if client just reported contacting lender
```

---

### Fix 2: Add Observation Status Updates

**Extend extraction schema:**
```json
"observation_updates": [
  {
    "id": existing_observation_id,
    "status": "superseded|active",
    "superseded_reason": "Reason why this observation is no longer current"
  }
]
```

**Add validation:**
```python
def _validate_observation_updates(self, updates: Any):
    """Validate observation update proposals."""
    if not isinstance(updates, list):
        self.errors.append("observation_updates must be a list")
        return
    
    existing_ids = [o['id'] for o in self.existing_context.get('coaching_observations', [])]
    
    for i, update in enumerate(updates):
        if not isinstance(update, dict):
            self.errors.append(f"observation_updates[{i}] must be a dictionary")
            continue
        
        if 'id' not in update:
            self.errors.append(f"observation_updates[{i}] missing required field: id")
        elif update['id'] not in existing_ids:
            self.errors.append(f"observation_updates[{i}].id references non-existent observation")
        
        if 'status' in update:
            if update['status'] not in ['active', 'superseded']:
                self.errors.append(f"observation_updates[{i}].status invalid: {update['status']}")
```

**Add persistence:**
```python
def _update_observations(updates: List[Dict]) -> int:
    """Update existing coaching observations."""
    count = 0
    for u in updates:
        observation = db.session.get(CoachingObservation, u['id'])
        if observation:
            if 'status' in u:
                observation.status = u['status']
            count += 1
    
    return count
```

---

### Fix 3: Add Attention Item Status Updates

**Extend extraction schema:**
```json
"attention_item_updates": [
  {
    "id": existing_attention_id,
    "status": "resolved|open",
    "resolution_note": "How this was resolved"
  }
]
```

**Add validation and persistence similar to observations.**

---

### Fix 4: Investigate Missing Summaries

**Add diagnostic logging:**
```python
def process_session_extraction(session_id):
    session = db.session.get(Session, session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    engagement = session.engagement
    
    logging.info(f"[EXTRACTION] Processing session {session_id}, engagement {engagement.id}")
    
    context = build_coaching_context(engagement.id)
    pathway_data = load_pathway(engagement.pathway_id)
    
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages
    ]
    
    logging.info(f"[EXTRACTION] Session has {len(messages)} messages")
    
    if len(messages) < 2:
        logging.info("[EXTRACTION] Session too short for extraction")
        session.summary = "Brief session - no significant updates"
        db.session.commit()
        return
    
    try:
        ai_service = AIService()
        extraction_prompt = build_extraction_prompt()
        
        logging.info("[EXTRACTION] Calling AI service for extraction")
        
        extraction = ai_service.extract_session_outcomes(
            messages=messages,
            context=context,
            extraction_prompt=extraction_prompt
        )
        
        logging.info(f"[EXTRACTION] Extraction result keys: {extraction.keys()}")
        logging.info(f"[EXTRACTION] Session summary: {extraction.get('session_summary', 'MISSING')}")
        
        # ... rest of processing
```

---

## Implementation Priority

**Priority 1 (Critical):**
1. Enhanced extraction prompt with reconciliation guidance
2. Diagnostic logging for missing summaries

**Priority 2 (Important):**
3. Observation status updates (schema + validation + persistence)
4. Attention item status updates (schema + validation + persistence)

**Priority 3 (Nice to have):**
5. Automatic detection of contradictory observations
6. Smarter matching of client statements to existing commitments

---

## Testing Plan

**Test Case 1: Commitment Completion**
1. Create open commitment: "Contact lender about payment deferral"
2. Client says: "I called the lender yesterday"
3. Verify: Commitment marked completed

**Test Case 2: Risk Resolution**
1. Create open risk: "Lender contact delayed"
2. Client says: "Lender agreed to defer this month's payment"
3. Verify: Risk marked resolved

**Test Case 3: Observation Supersession**
1. Existing observation: "Client avoiding lender contact"
2. Client completes lender contact commitment
3. Verify: Old observation marked superseded OR no new conflicting observation created

**Test Case 4: Attention Item Resolution**
1. Existing attention: "Lender contact overdue - client repeatedly deferring"
2. Client completes lender contact
3. Verify: Attention item marked resolved OR no new duplicate created

**Test Case 5: Session Summary**
1. Complete a coaching session
2. Verify: Session summary appears in advisor view
3. Check logs for extraction process

---

## Next Steps

1. Review this diagnostic with user
2. Confirm priority of fixes
3. Implement Priority 1 fixes first
4. Test with actual lender scenario
5. Verify general reconciliation behavior works for other scenarios

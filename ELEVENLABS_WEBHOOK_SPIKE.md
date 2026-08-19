# ElevenLabs Post-Call Webhook - Connectivity Spike

## Objective

Add a minimal, isolated Flask endpoint to prove that the deployed Render application can receive an ElevenLabs **Post-Call Webhook** after a voice-agent conversation ends.

**This is a connectivity spike only.**

---

## Context

The AI Coaching Platform currently supports persistent text-based coaching:

**Client → Context → AI Coach → Extraction → Validation → Persistence → Advisor View**

We are exploring ElevenLabs Agents as a **client-side voice interface**.

**Previous manual tests:**
- **Voice Spike 001A:** ElevenLabs provides credible small-business coaching
- **Voice Spike 001B:** Prior coaching context creates continuity between sessions

**Next question:**
> Can ElevenLabs send the completed voice conversation back to the deployed AI Coaching Platform?

---

## Implementation

### Endpoint Added

```
POST /webhooks/elevenlabs/post-call
```

**Purpose:** Receive and log ElevenLabs post-call webhook data

**Location:** `app.py` lines 1148-1230

---

### What the Endpoint Does

1. **Accepts HTTP POST** from ElevenLabs
2. **Logs request metadata:**
   - Content-Type
   - Request method
   - Remote address
3. **Parses JSON payload** (if present)
4. **Pretty-prints payload** to logs for inspection
5. **Returns HTTP 200** promptly

**Log format:**
```
============================================================
ELEVENLABS POST-CALL WEBHOOK RECEIVED
============================================================
Content-Type: application/json
Request Method: POST
Remote Address: 1.2.3.4

Payload (JSON):
{
  "conversation_id": "...",
  "transcript": "...",
  ...
}

============================================================
END ELEVENLABS WEBHOOK
============================================================
```

---

### What the Endpoint Does NOT Do

**No database operations:**
- ❌ Create or modify database records
- ❌ Associate webhooks with clients
- ❌ Create coaching sessions

**No coaching processing:**
- ❌ Invoke AI coaching service
- ❌ Invoke extraction
- ❌ Invoke validation
- ❌ Invoke persistence
- ❌ Update pathway state
- ❌ Create commitments or risks

**No UI modifications:**
- ❌ Modify client UI
- ❌ Modify advisor UI
- ❌ Modify existing text-coaching behavior

**This endpoint only logs the payload and returns success.**

---

## Error Handling

### Malformed Requests

**If request body is missing, malformed, or not valid JSON:**

1. **Does not crash** the Flask application
2. **Logs diagnostic message:**
   ```
   Failed to parse JSON payload: <error>
   Raw data: <raw request body>
   ```
3. **Returns appropriate HTTP response**

**If any exception occurs:**

1. **Logs error with clear markers:**
   ```
   ============================================================
   ELEVENLABS WEBHOOK ERROR
   ============================================================
   Error processing webhook: <error message>
   ============================================================
   ```
2. **Returns HTTP 500** with error JSON:
   ```json
   {
     "status": "error",
     "message": "Failed to process webhook"
   }
   ```

**Malformed webhook traffic does not affect normal application operation.**

---

## Security

### Current State (Connectivity Spike)

**No authentication implemented.**

The endpoint currently accepts any POST request for connectivity testing.

### Production Requirements

**TODO (documented in code):**

```python
# TODO: Add ElevenLabs webhook signature verification before production use.
# Currently accepts any POST request for connectivity testing only.
```

**Before production:**
1. Inspect actual ElevenLabs webhook configuration
2. Identify ElevenLabs signing mechanism
3. Implement signature verification
4. Reject unsigned/invalid requests

**The endpoint is structured to add signature verification cleanly.**

---

## Files Changed

### app.py (Modified)

**Lines 1144-1230:** Added ElevenLabs webhook endpoint

**Added:**
- Route: `/webhooks/elevenlabs/post-call`
- Method: `POST`
- Function: `elevenlabs_post_call_webhook()`
- Comprehensive error handling
- Clear logging with diagnostic markers
- TODO comment for signature verification

**Total:** 1 file modified (87 lines added)

---

## Dependencies

**No new dependencies added.**

Uses existing Flask imports:
- `request` (already imported)
- `jsonify` (already imported)
- `logging` (already imported)
- `json` (standard library, imported inline)

---

## Expected Test

### Webhook URL

After deployment to Render:

```
https://ai-coaching-platform.onrender.com/webhooks/elevenlabs/post-call
```

### Test Procedure

1. **Configure** webhook URL in ElevenLabs workspace Post-Call Webhook setting
2. **Start** conversation with `AI Coach - PoC`
3. **Speak** for approximately 30-60 seconds
4. **End** conversation
5. **Inspect** Render logs

### Expected Log Output

```
============================================================
ELEVENLABS POST-CALL WEBHOOK RECEIVED
============================================================
Content-Type: application/json
Request Method: POST
Remote Address: <ElevenLabs IP>

Payload (JSON):
{
  <actual ElevenLabs payload structure>
}

============================================================
END ELEVENLABS WEBHOOK
============================================================
```

---

## Success Criteria

**The spike passes when Render logs show:**

1. ✅ ElevenLabs reached the endpoint
2. ✅ Endpoint received post-call event
3. ✅ JSON payload is visible and inspectable
4. ✅ Application returned HTTP 200
5. ✅ Existing functionality unchanged

---

## What Was NOT Changed

**Preserved (no changes):**
- ✅ Database schema
- ✅ Client/advisor models
- ✅ Coaching engine
- ✅ Extraction pipeline
- ✅ Validation logic
- ✅ Persistence logic
- ✅ Pathway logic
- ✅ Commitment/risk tracking
- ✅ Session management
- ✅ Client UI
- ✅ Advisor UI
- ✅ Text coaching behavior
- ✅ All existing routes

**This is an isolated connectivity test endpoint only.**

---

## Code Structure

### Endpoint Function

```python
@app.route('/webhooks/elevenlabs/post-call', methods=['POST'])
def elevenlabs_post_call_webhook():
    """
    ElevenLabs Post-Call Webhook receiver.
    
    This is a CONNECTIVITY SPIKE ONLY.
    """
    try:
        # Get request metadata
        content_type = request.content_type or 'unknown'
        
        # Log with clear markers
        logging.info("=" * 60)
        logging.info("ELEVENLABS POST-CALL WEBHOOK RECEIVED")
        logging.info("=" * 60)
        logging.info(f"Content-Type: {content_type}")
        logging.info(f"Request Method: {request.method}")
        logging.info(f"Remote Address: {request.remote_addr}")
        
        # Parse and log JSON payload
        if request.is_json:
            payload = request.get_json()
            payload_str = json.dumps(payload, indent=2, default=str)
            logging.info("Payload (JSON):")
            logging.info(payload_str)
        else:
            logging.info("Payload (not JSON):")
            logging.info(request.get_data(as_text=True))
        
        logging.info("=" * 60)
        logging.info("END ELEVENLABS WEBHOOK")
        logging.info("=" * 60)
        
        # Return success
        return jsonify({
            'status': 'received',
            'message': 'ElevenLabs post-call webhook received successfully'
        }), 200
        
    except Exception as e:
        # Log error, don't crash
        logging.error("=" * 60)
        logging.error("ELEVENLABS WEBHOOK ERROR")
        logging.error("=" * 60)
        logging.error(f"Error processing webhook: {str(e)}")
        logging.error("=" * 60)
        
        return jsonify({
            'status': 'error',
            'message': 'Failed to process webhook'
        }), 500
```

---

## Logging Strategy

### Clear Diagnostic Markers

**Start marker:**
```
============================================================
ELEVENLABS POST-CALL WEBHOOK RECEIVED
============================================================
```

**End marker:**
```
============================================================
END ELEVENLABS WEBHOOK
============================================================
```

**Error marker:**
```
============================================================
ELEVENLABS WEBHOOK ERROR
============================================================
```

**Purpose:** Easy to locate in Render logs

---

### Logged Information

**Request metadata:**
- Content-Type
- Request method
- Remote address

**Payload:**
- Pretty-printed JSON (if valid JSON)
- Raw data (if not JSON)
- Error message (if parsing fails)

**No sensitive data logged:**
- ❌ API keys
- ❌ Environment variables
- ❌ Authorization headers
- ❌ Application secrets
- ❌ Unrelated server information

---

## Next Steps (After Spike)

**This spike stops at connectivity verification.**

**Do NOT proceed to:**
- Transcript parsing
- Coaching record integration
- Database persistence
- Client association
- Session creation
- AI coaching invocation

**After inspecting actual ElevenLabs payload:**

1. Document payload structure
2. Identify required fields
3. Design integration approach
4. Implement signature verification
5. Plan transcript → coaching context flow
6. Design session association logic
7. Implement extraction/validation/persistence

**Wait for actual payload data before proceeding.**

---

## Observations & Assumptions

### Assumptions

1. **ElevenLabs sends JSON** - Endpoint handles both JSON and non-JSON
2. **POST method** - Endpoint only accepts POST
3. **Public endpoint** - No authentication required for spike
4. **Synchronous response** - Returns HTTP 200 immediately

### Questions to Answer After Spike

1. What is the actual payload structure?
2. What fields are included?
3. Is there a conversation ID?
4. Is there a transcript?
5. Is there metadata (duration, timestamps, etc.)?
6. How does ElevenLabs sign webhooks?
7. What retry behavior does ElevenLabs use?
8. What timeout does ElevenLabs expect?

---

## Deployment Checklist

**Before deploying to Render:**

1. ✅ Endpoint added to app.py
2. ✅ Error handling implemented
3. ✅ Logging configured
4. ✅ No database operations
5. ✅ No coaching processing
6. ✅ No existing functionality modified
7. ✅ TODO added for signature verification
8. ✅ No new dependencies

**After deploying to Render:**

1. Configure webhook URL in ElevenLabs workspace
2. Test with short conversation
3. Inspect Render logs
4. Verify payload structure
5. Document findings

---

## Summary

✅ **Objective:** Prove ElevenLabs can reach deployed app  
✅ **Endpoint:** `/webhooks/elevenlabs/post-call`  
✅ **Method:** POST  
✅ **Functionality:** Log payload, return 200  
✅ **Error handling:** Safe, doesn't crash app  
✅ **Security:** TODO for signature verification  
✅ **Files changed:** 1 (app.py)  
✅ **Dependencies:** None added  
✅ **Database:** No operations  
✅ **Coaching:** No processing  
✅ **Existing functionality:** Unchanged  
✅ **Next step:** Inspect actual payload  

**This is a minimal connectivity spike. Integration work begins after inspecting the actual ElevenLabs payload structure.**

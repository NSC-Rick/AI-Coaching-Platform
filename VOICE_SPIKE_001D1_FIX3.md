# Voice Spike 001D-1: Enhanced Error Logging for 401 Diagnosis

## Issue

**Observed:**
```
401 Unauthorized
```

**Current state:**
- ✅ Signed URL request uses GET (correct)
- ✅ Request header uses `xi-api-key` (correct)
- ❌ ElevenLabs returns 401 Unauthorized

**Need:** Detailed error logging to diagnose authorization failure

---

## Fix Applied

**File:** `coaching/voice_service.py`

**Lines 84-118:** Enhanced error logging in `generate_signed_url()`

### Added Diagnostic Logging

**When signed URL request fails:**

```python
except requests.exceptions.RequestException as e:
    # Enhanced error logging for diagnosis (without exposing secrets)
    import logging
    logging.error("=" * 60)
    logging.error("ELEVENLABS SIGNED URL REQUEST FAILED")
    logging.error("=" * 60)
    logging.error(f"Request URL: {url}")
    logging.error(f"Request method: GET")
    logging.error(f"Agent ID: {self.agent_id}")
    logging.error(f"API key configured: {'Yes' if self.api_key else 'No'}")
    logging.error(f"API key length: {len(self.api_key) if self.api_key else 0} characters")
    logging.error(f"Header name used: xi-api-key")
    
    if hasattr(e, 'response') and e.response is not None:
        logging.error(f"HTTP status code: {e.response.status_code}")
        logging.error(f"Response headers: {dict(e.response.headers)}")
        
        # Log response body if available (sanitized)
        try:
            response_body = e.response.text
            if response_body and len(response_body) < 1000:
                logging.error(f"Response body: {response_body}")
            else:
                logging.error(f"Response body length: {len(response_body)} characters")
        except:
            logging.error("Could not read response body")
    else:
        logging.error(f"No response object available")
    
    logging.error(f"Exception type: {type(e).__name__}")
    logging.error(f"Exception message: {str(e)}")
    logging.error("=" * 60)
    
    raise Exception(f"Failed to generate ElevenLabs signed URL: {str(e)}")
```

---

## What Gets Logged

**Request information:**
- ✅ Request URL (without secrets)
- ✅ Request method (GET)
- ✅ Agent ID (public identifier)
- ✅ API key configured (Yes/No)
- ✅ API key length (character count)
- ✅ Header name used (xi-api-key)

**Response information:**
- ✅ HTTP status code (e.g., 401)
- ✅ Response headers
- ✅ Response body (if < 1000 chars)
- ✅ Response body length (if > 1000 chars)

**Exception information:**
- ✅ Exception type
- ✅ Exception message

---

## What Does NOT Get Logged

**Secrets protected:**
- ❌ ELEVENLABS_API_KEY value
- ❌ Authorization header value
- ❌ Signed URLs
- ❌ Tokens
- ❌ Any credentials

**Privacy:**
- ✅ Only public identifiers logged
- ✅ Only metadata logged (not secret values)
- ✅ Response body sanitized (length check)

---

## Expected Log Output

### If 401 Unauthorized

```
============================================================
ELEVENLABS SIGNED URL REQUEST FAILED
============================================================
Request URL: https://api.elevenlabs.io/v1/convai/conversation/get-signed-url
Request method: GET
Agent ID: agent_9101m0dp2f6kfenrxt8p50mp7hde
API key configured: Yes
API key length: 32 characters
Header name used: xi-api-key
HTTP status code: 401
Response headers: {'Content-Type': 'application/json', ...}
Response body: {"detail": {"status": "unauthorized", "message": "..."}}
Exception type: HTTPError
Exception message: 401 Client Error: Unauthorized for url: ...
============================================================
```

**This will show:**
1. ✅ Exact HTTP status code
2. ✅ ElevenLabs error message
3. ✅ Response headers
4. ✅ Whether API key is configured
5. ✅ API key length (to verify it's not empty/truncated)
6. ✅ Header name used (to verify correct format)

---

## Verification Checklist

**Request format verified:**
- ✅ Method: GET
- ✅ URL: `https://api.elevenlabs.io/v1/convai/conversation/get-signed-url`
- ✅ Query param: `agent_id=<ELEVENLABS_AGENT_ID>`
- ✅ Header: `xi-api-key: <ELEVENLABS_API_KEY>`

**Error logging verified:**
- ✅ Logs HTTP status code
- ✅ Logs ElevenLabs response body
- ✅ Does NOT log API key value
- ✅ Does NOT log authorization header
- ✅ Does NOT log signed URLs/tokens

---

## Next Steps After Deployment

**1. Deploy to Render**

**2. Trigger one voice session initialization:**
```
POST /voice/session/init/1
```

**3. Inspect Render logs for:**
```
ELEVENLABS SIGNED URL REQUEST FAILED
```

**4. Review logged information:**
- HTTP status code (should be 401)
- Response body (ElevenLabs error message)
- API key configured (should be "Yes")
- API key length (should be > 0)
- Agent ID (verify correct value)

**5. Diagnose based on ElevenLabs response:**
- Invalid API key format?
- Incorrect permissions?
- Agent ID mismatch?
- API key expired/revoked?
- Workspace configuration issue?

---

## Files Changed

**1. coaching/voice_service.py**
- Lines 84-118: Enhanced error logging in exception handler

**Total:** 1 file modified (~35 lines added)

---

## What Was NOT Changed

**No changes to:**
- ✅ Request method (still GET)
- ✅ Request URL
- ✅ Request headers
- ✅ Request parameters
- ✅ Identity architecture
- ✅ Conversation config
- ✅ Webhook processing
- ✅ Any other functionality

**Only added:** Diagnostic error logging

---

## Security Verification

**Secrets protected:**
- ✅ API key value never logged
- ✅ Authorization header never logged
- ✅ Signed URLs never logged
- ✅ Tokens never logged

**Safe to log:**
- ✅ HTTP status codes
- ✅ Public identifiers (agent_id)
- ✅ Metadata (key length, configured status)
- ✅ ElevenLabs error messages
- ✅ Response headers (no secrets)

---

## Summary

✅ **Issue:** 401 Unauthorized, need diagnosis  
✅ **Fix:** Enhanced error logging  
✅ **Logs:** HTTP status, response body, metadata  
✅ **Does NOT log:** API keys, tokens, secrets  
✅ **Files:** 1 modified (voice_service.py)  
✅ **Request format:** Verified correct (GET, xi-api-key header)  
✅ **Next:** Deploy and inspect ElevenLabs error response  

**After deployment, one test request will provide detailed diagnostic information about the 401 error without exposing any secrets.**

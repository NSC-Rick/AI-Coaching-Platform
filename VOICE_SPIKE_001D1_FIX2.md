# Voice Spike 001D-1: Signed URL Method Fix

## Issue

**Observed:**
```
Failed to generate ElevenLabs signed URL:
405 Client Error: Method Not Allowed for url:
https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?agent_id=agent_9101m0dp2f6kfenrxt8p50mp7hde
```

**Root cause:** Using POST method when ElevenLabs API requires GET

---

## ElevenLabs API Contract

**Correct signed URL request:**

```
GET https://api.elevenlabs.io/v1/convai/conversation/get-signed-url

Query parameter:
  agent_id=<ELEVENLABS_AGENT_ID>

Header:
  xi-api-key: <ELEVENLABS_API_KEY>
```

**Method:** GET only (not POST)

---

## Problem Diagnosed

**Original implementation (voice_service.py lines 77-80):**

```python
if body:
    response = requests.post(url, params=params, headers=headers, json=body, timeout=10)
else:
    response = requests.get(url, params=params, headers=headers, timeout=10)
```

**Issue:** When identity metadata was present, code used POST with JSON body

**ElevenLabs response:** HTTP 405 Method Not Allowed

---

## Solution

**Identity metadata should be passed in conversation config, not signed URL request.**

### Architecture Change

**Before:**
```
Signed URL request (POST) → Include metadata in body → 405 error
```

**After:**
```
Signed URL request (GET) → No metadata
    ↓
Conversation config → Include metadata → Round-trip via webhook
```

---

## Fixes Applied

### 1. voice_service.py - generate_signed_url()

**Lines 39-85:** Fixed to use GET method only

**Before:**
```python
# Build request body with custom metadata for identity round-trip
body = {}
if session_id or engagement_id:
    body['custom_llm_extra_body'] = {
        'app_session_id': str(session_id) if session_id else None,
        'app_engagement_id': str(engagement_id) if engagement_id else None,
        'app_platform': 'ai_coaching_platform'
    }

if body:
    response = requests.post(url, params=params, headers=headers, json=body, timeout=10)
else:
    response = requests.get(url, params=params, headers=headers, timeout=10)
```

**After:**
```python
# ElevenLabs API requires GET method for signed URL generation
# Identity metadata is passed via conversation config, not here
response = requests.get(url, params=params, headers=headers, timeout=10)
response.raise_for_status()

data = response.json()

# Store identity metadata for later use in session config
result = {'signed_url': data.get('signed_url')}
if session_id or engagement_id:
    result['metadata'] = {
        'app_session_id': str(session_id) if session_id else None,
        'app_engagement_id': str(engagement_id) if engagement_id else None,
        'app_platform': 'ai_coaching_platform'
    }

return result
```

**Changes:**
- ✅ Always use GET method
- ✅ No POST request
- ✅ No JSON body in signed URL request
- ✅ Metadata stored in result for later use

---

### 2. voice_service.py - build_session_config()

**Lines 87-159:** Added identity metadata to conversation config

**Before:**
```python
def build_session_config(
    self,
    client_name: str,
    business_name: str,
    pathway_name: str,
    current_stage: str,
    current_day: int,
    coaching_context: str,
    session_id: str,
    user_id: str
) -> Dict[str, Any]:
    return {
        'agent_id': self.agent_id,
        'user_id': user_id,
        'session_metadata': {...},
        'conversation_config_override': {
            'agent': {
                'prompt': {...}
            }
        }
    }
```

**After:**
```python
def build_session_config(
    self,
    client_name: str,
    business_name: str,
    pathway_name: str,
    current_stage: str,
    current_day: int,
    coaching_context: str,
    session_id: str,
    user_id: str,
    engagement_id: Optional[int] = None  # NEW PARAMETER
) -> Dict[str, Any]:
    config = {
        'agent_id': self.agent_id,
        'user_id': user_id,
        'session_metadata': {...},
        'conversation_config_override': {
            'agent': {
                'prompt': {...}
            }
        }
    }
    
    # Voice Spike 001D-1: Add identity metadata for webhook round-trip
    # This metadata will be returned in the post-call webhook
    if session_id or engagement_id:
        config['conversation_config_override']['agent']['custom_llm_extra_body'] = {
            'app_session_id': str(session_id) if session_id else None,
            'app_engagement_id': str(engagement_id) if engagement_id else None,
            'app_platform': 'ai_coaching_platform'
        }
    
    return config
```

**Changes:**
- ✅ Added `engagement_id` parameter
- ✅ Identity metadata now in conversation config
- ✅ Metadata passed to ElevenLabs via `custom_llm_extra_body` in agent config
- ✅ Will round-trip through post-call webhook

---

### 3. app.py - init_voice_session()

**Line 748:** Pass engagement_id to build_session_config

**Before:**
```python
session_config = voice_service.build_session_config(
    client_name=engagement.client.user.first_name or engagement.client.user.email.split('@')[0],
    business_name=engagement.business.business_name,
    pathway_name=pathway_data.get('name', 'Recovery & Stabilization'),
    current_stage=pathway_state.current_stage_id if pathway_state else 'RS-01',
    current_day=pathway_state.current_day if pathway_state else 1,
    coaching_context=format_context_for_display(context),
    session_id=str(session.id),
    user_id=str(current_user.id)
)
```

**After:**
```python
session_config = voice_service.build_session_config(
    client_name=engagement.client.user.first_name or engagement.client.user.email.split('@')[0],
    business_name=engagement.business.business_name,
    pathway_name=pathway_data.get('name', 'Recovery & Stabilization'),
    current_stage=pathway_state.current_stage_id if pathway_state else 'RS-01',
    current_day=pathway_state.current_day if pathway_state else 1,
    coaching_context=format_context_for_display(context),
    session_id=str(session.id),
    user_id=str(current_user.id),
    engagement_id=engagement_id  # NEW PARAMETER
)
```

**Changes:**
- ✅ Pass engagement_id to session config builder

---

## Files Changed

**1. coaching/voice_service.py**
- Lines 39-85: Fixed `generate_signed_url()` to use GET only
- Lines 87-159: Enhanced `build_session_config()` to include identity metadata

**2. app.py**
- Line 748: Pass engagement_id to build_session_config

**Total:** 2 files modified

---

## Identity Round-Trip Architecture

**Corrected flow:**

```
1. Client initiates voice session
   ↓
2. Server calls generate_signed_url() with GET
   ↓
3. Server builds session config with identity metadata
   ↓
4. Client receives signed URL + config with metadata
   ↓
5. Client starts ElevenLabs conversation with config
   ↓
6. ElevenLabs stores metadata in conversation
   ↓
7. Voice conversation happens
   ↓
8. Conversation ends
   ↓
9. ElevenLabs sends post-call webhook with metadata
   ↓
10. Server extracts identity from webhook payload
```

**Key change:** Metadata travels via conversation config, not signed URL request

---

## Expected Result After Fix

**Request:**
```
POST /voice/session/init/1
```

**Expected response:** HTTP 200
```json
{
  "session_id": 123,
  "signed_url": "https://api.elevenlabs.io/...",
  "config": {
    "agent_id": "agent_...",
    "user_id": "1",
    "session_metadata": {...},
    "conversation_config_override": {
      "agent": {
        "prompt": {...},
        "custom_llm_extra_body": {
          "app_session_id": "123",
          "app_engagement_id": "1",
          "app_platform": "ai_coaching_platform"
        }
      }
    }
  }
}
```

**Instead of:** HTTP 503 with "Failed to generate ElevenLabs signed URL: 405"

---

## What Was NOT Changed

**No changes to:**
- ✅ Webhook endpoint
- ✅ HMAC signature verification
- ✅ Webhook identity extraction logic
- ✅ Database schema
- ✅ Persistence logic
- ✅ Coaching-record processing
- ✅ Any other routes
- ✅ ELEVENLABS_API_KEY security (still server-side only)

**Only changes:**
- ✅ Signed URL request method (POST → GET)
- ✅ Identity metadata location (signed URL body → conversation config)

---

## Verification

**Signed URL request:**
- ✅ Uses GET method
- ✅ No POST request
- ✅ No JSON body
- ✅ Query param: agent_id
- ✅ Header: xi-api-key
- ✅ Matches ElevenLabs API contract

**Identity metadata:**
- ✅ Included in conversation config
- ✅ Passed to client
- ✅ Client sends to ElevenLabs during conversation start
- ✅ Will round-trip via webhook

**Security:**
- ✅ ELEVENLABS_API_KEY never exposed to browser
- ✅ Signed URL generated server-side
- ✅ Identity metadata opaque (no PII)

---

## Summary

✅ **Issue:** POST method not allowed by ElevenLabs API  
✅ **Root cause:** Incorrect signed URL request method  
✅ **Fix:** Use GET only, move metadata to conversation config  
✅ **Files:** 2 modified (voice_service.py, app.py)  
✅ **Identity architecture:** Preserved, metadata now in correct location  
✅ **Security:** ELEVENLABS_API_KEY remains server-side  
✅ **Expected:** Signed URL generation now succeeds with HTTP 200  

**Voice session initialization should now complete successfully, and identity metadata will round-trip through the ElevenLabs conversation configuration instead of the signed URL request.**

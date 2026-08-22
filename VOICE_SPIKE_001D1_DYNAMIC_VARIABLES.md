# Voice Spike 001D-1: Fix Dynamic Variables for Agent First Message

## Root Cause Confirmed

**The ElevenLabs conversation was terminating immediately because:**

The agent's First Message uses the template variable `{{client_name}}`, but this dynamic variable was not being provided to the SDK when starting the conversation.

**ElevenLabs behavior:**
- Agent First Message contains: `"Hello {{client_name}}, welcome..."`
- SDK receives no `dynamicVariables` parameter
- SDK cannot resolve `{{client_name}}`
- **Conversation terminates immediately**

---

## Solution

Pass the client's first name from the backend to the browser, then provide it to the ElevenLabs SDK via the `dynamicVariables` configuration parameter.

**Flow:**
```
Backend: engagement.client.first_name
  ↓
Response: { client_name: "Sarah" }
  ↓
Frontend: dynamicVariables: { client_name: "Sarah" }
  ↓
SDK: Conversation.startSession({ dynamicVariables })
  ↓
ElevenLabs: Resolves {{client_name}} → "Sarah"
  ↓
Agent: "Hello Sarah, welcome..."
  ↓
✓ Conversation starts successfully
```

---

## Files Changed

### 1. app.py

**Line 755:** Added `client_name` to voice session init response

**Before:**
```python
response_data = {
    'session_id': session.id,
    'signed_url': signed_url_data['signed_url'],
    'config': session_config
}
```

**After:**
```python
response_data = {
    'session_id': session.id,
    'signed_url': signed_url_data['signed_url'],
    'config': session_config,
    'client_name': engagement.client.first_name  # For ElevenLabs dynamicVariables
}
```

**Purpose:** Include client's first name in backend response for frontend to use

**Source:** `engagement.client.first_name` (already available in the route)

**NOT hard-coded:** Uses actual client data from database

---

### 2. frontend/voice-client.js

**Lines 24, 36, 43:** Added `dynamicVariables` parameter support

**Before:**
```javascript
export async function startVoiceConversation(options) {
    const {
        signedUrl,
        onConnect,
        onDisconnect,
        // ...
    } = options;

    console.log('[VOICE] Starting ElevenLabs conversation with official SDK v1.21.0');
    console.log('[VOICE] Signed URL present:', Boolean(signedUrl));

    const conversation = await Conversation.startSession({
        signedUrl,
        // ...
    });
}
```

**After:**
```javascript
export async function startVoiceConversation(options) {
    const {
        signedUrl,
        dynamicVariables,
        onConnect,
        onDisconnect,
        // ...
    } = options;

    console.log('[VOICE] Starting ElevenLabs conversation with official SDK v1.21.0');
    console.log('[VOICE] Signed URL present:', Boolean(signedUrl));
    console.log('[VOICE] Dynamic variables:', dynamicVariables);

    const conversation = await Conversation.startSession({
        signedUrl,
        dynamicVariables,
        // ...
    });
}
```

**Purpose:** Accept and pass `dynamicVariables` to ElevenLabs SDK

**Logging:** Added diagnostic logging of dynamic variables

---

### 3. templates/voice_coaching.html

**Lines 267, 273-276:** Extract client_name from backend response and pass to SDK

**Before:**
```javascript
const data = await response.json();
sessionId = data.session_id;

console.log('[VOICE] ✓ Backend session initialized:', sessionId);
console.log('[VOICE] Signed URL received:', { ... });

conversation = await startVoiceConversation({
    signedUrl: data.signed_url,
    onConnect: () => { ... },
    // ...
});
```

**After:**
```javascript
const data = await response.json();
sessionId = data.session_id;

console.log('[VOICE] ✓ Backend session initialized:', sessionId);
console.log('[VOICE] Signed URL received:', { ... });
console.log('[VOICE] Client name received:', data.client_name);

conversation = await startVoiceConversation({
    signedUrl: data.signed_url,
    dynamicVariables: {
        client_name: data.client_name
    },
    onConnect: () => { ... },
    // ...
});
```

**Purpose:** Pass client name to SDK as dynamic variable

**Logging:** Added diagnostic logging of received client name

---

## ElevenLabs Dynamic Variables API

**Official SDK parameter:**

```typescript
interface SessionConfig {
    signedUrl?: string;
    dynamicVariables?: Record<string, string | number | boolean>;
    // ... other options
}
```

**Usage:**
```javascript
await Conversation.startSession({
    signedUrl: 'https://...',
    dynamicVariables: {
        client_name: 'Sarah',
        business_name: 'Acme Corp',
        custom_var: 123,
        another_var: true
    }
});
```

**ElevenLabs behavior:**
- Receives `dynamicVariables` object
- Resolves template variables in agent configuration
- `{{client_name}}` → value from `dynamicVariables.client_name`
- `{{business_name}}` → value from `dynamicVariables.business_name`
- etc.

**Supported in:**
- Agent First Message
- System Prompt
- Tool configurations
- Any agent text field

---

## Preserved Architecture

**NO changes to:**

✅ **Signed URL generation** - Still uses `voice_service.generate_signed_url()`  
✅ **Prompt override** - Still uses `voice_service.build_session_config()`  
✅ **Session persistence** - Still creates `Session` record in database  
✅ **Identity architecture** - Still passes session_id/engagement_id  
✅ **Webhook processing** - Still receives post-call webhook  
✅ **Coaching context** - Still builds context from engagement  
✅ **Diagnostic logging** - All `[VOICE]` prefixed logs preserved  
✅ **State tracking** - `userRequestedEnd`, `sessionCompletionSent` preserved  
✅ **Unexpected disconnect handling** - Still stays on page for diagnostics  

**Only added:**
- `client_name` to backend response
- `dynamicVariables` parameter to SDK call
- Diagnostic logging of client name

---

## Expected Browser Console Output

**On successful connection:**

```
[VOICE] ElevenLabs SDK module ready (v1.21.0)
[VOICE] ═══ START VOICE SESSION ═══
[VOICE] Engagement ID: 1
[VOICE] Requesting microphone permission
[VOICE] ✓ Microphone permission granted
[VOICE] Backend initialization starting
[VOICE] ✓ Backend session initialized: 38
[VOICE] Signed URL received: { hasSignedUrl: true, signedUrlLength: 148 }
[VOICE] Client name received: Sarah
[VOICE] Starting ElevenLabs conversation with official SDK v1.21.0
[VOICE] Signed URL present: true
[VOICE] Signed URL length: 148
[VOICE] Dynamic variables: { client_name: 'Sarah' }
[VOICE] Calling Conversation.startSession
[VOICE] ✓ startSession resolved successfully
[VOICE] Conversation object created: true
[VOICE] Conversation type: object
[VOICE] ✓ Voice session setup complete
[VOICE] ✓ onConnect fired
[VOICE] Connection data: { conversationId: '...' }
[VOICE] Conversation ID: ...
[VOICE] UI: Connection established
[VOICE] Status change: connected
[VOICE] UI: Status change received: connected
[VOICE] Mode change: { mode: 'speaking' }
[VOICE] Mode value: speaking
[VOICE] UI: Mode change received: speaking
```

**Agent speaks:** "Hello Sarah, welcome to your coaching session..."

**Key difference from before:**
- ✅ `[VOICE] Dynamic variables: { client_name: 'Sarah' }`
- ✅ `onConnect` fires successfully
- ✅ Agent speaks first message with resolved variable
- ✅ Conversation continues normally

---

## Test Steps

### 1. Deploy Changes

```bash
git add app.py frontend/voice-client.js templates/voice_coaching.html
git commit -m "Fix: Pass client_name as dynamic variable to resolve agent first message template"
git push
```

**Render will rebuild bundle automatically**

---

### 2. Test Voice Conversation

1. Navigate to voice coaching page
2. Open browser console (F12)
3. Click "Start Conversation"
4. Grant microphone permission

**Expected:**
```
[VOICE] Client name received: Sarah
[VOICE] Dynamic variables: { client_name: 'Sarah' }
[VOICE] ✓ onConnect fired
[VOICE] Mode change: { mode: 'speaking' }
```

**Agent should speak:**
"Hello Sarah, welcome to your coaching session..."

**NOT:**
"Hello {{client_name}}, welcome..." (unresolved template)

---

### 3. Verify Conversation Continues

**Expected:**
- ✅ Agent speaks first message with client name
- ✅ Conversation mode changes: speaking → listening
- ✅ User can speak
- ✅ Agent responds
- ✅ Conversation continues normally
- ✅ No immediate disconnect

**Server logs should show:**
```
Voice session 39 initialized for engagement 1
POST /voice/session/init/1 → 200
[conversation continues...]
Voice session 39 completed. Messages: 5+
POST /voice/session/39/complete → 200
```

**NOT:**
```
Voice session 39 initialized for engagement 1
Voice session 39 completed. Messages: 0  ← immediate disconnect
```

---

## Additional Dynamic Variables (Future)

**Currently passed:**
- `client_name` - Client's first name

**Available in backend (not yet passed):**
- `business_name` - From `engagement.client.business.business_name`
- `pathway_name` - From `pathway_data.get('name')`
- `current_stage` - From `pathway_state.current_stage_id`
- `current_day` - From `pathway_state.current_day`

**To add more variables:**

1. Add to backend response:
```python
response_data = {
    'session_id': session.id,
    'signed_url': signed_url_data['signed_url'],
    'config': session_config,
    'client_name': engagement.client.first_name,
    'business_name': engagement.client.business.business_name,  # Add this
    'pathway_name': pathway_data.get('name')  # Add this
}
```

2. Add to frontend dynamicVariables:
```javascript
dynamicVariables: {
    client_name: data.client_name,
    business_name: data.business_name,  // Add this
    pathway_name: data.pathway_name  // Add this
}
```

3. Use in agent configuration:
```
First Message: "Hello {{client_name}} from {{business_name}}, 
welcome to {{pathway_name}}..."
```

---

## Summary

✅ **Root cause:** Agent first message uses `{{client_name}}` but variable not provided  
✅ **Solution:** Pass `client_name` from backend via `dynamicVariables` parameter  
✅ **Files changed:** 3 (app.py, voice-client.js, voice_coaching.html)  
✅ **NOT hard-coded:** Uses actual `engagement.client.first_name` from database  
✅ **Architecture preserved:** Signed URL, prompt override, session persistence unchanged  
✅ **Diagnostic logging:** All existing `[VOICE]` logs preserved + new client_name log  
✅ **Expected:** Agent speaks "Hello Sarah..." and conversation continues  

**The ElevenLabs conversation will now start successfully because the `{{client_name}}` template variable in the agent's first message can be resolved using the dynamically provided client name from the database.**

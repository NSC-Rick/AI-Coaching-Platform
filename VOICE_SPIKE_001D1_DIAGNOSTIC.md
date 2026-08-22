# Voice Spike 001D-1: Diagnostic Instrumentation for Immediate Disconnect

## Objective

Diagnose why the ElevenLabs browser conversation disconnects immediately after successful backend initialization.

**Current status:**
- ✅ Backend initialization successful (HTTP 200)
- ✅ Signed URL received
- ✅ Local SDK bundle loads
- ❌ Conversation terminates immediately
- ❌ Session completes with 0 messages

---

## Files Changed

### 1. frontend/voice-client.js

**Comprehensive SDK lifecycle instrumentation added:**

**Lines 21-112:** Enhanced `startVoiceConversation()` with:
- Pre-call logging (signed URL presence/length)
- Try/catch wrapper around `Conversation.startSession()`
- Detailed success logging
- Detailed rejection logging with error name, message, stack
- All supported v1.21.0 callbacks instrumented

**Callbacks instrumented:**
- `onConnect` - Connection established
- `onDisconnect` - Connection ended
- `onError` - Error occurred
- `onStatusChange` - Status changed (connecting/connected/disconnected)
- `onModeChange` - Mode changed (speaking/listening)
- `onMessage` - Message received
- `onDebug` - Debug events (for detailed diagnostics)

---

### 2. templates/voice_coaching.html

**State tracking and diagnostic logging added:**

**Lines 202-204:** Added diagnostic state flags:
```javascript
let userRequestedEnd = false;
let sessionCompletionSent = false;
```

**Lines 226-342:** Enhanced `startVoiceSession()` with:
- Session start banner logging
- State flag reset
- Microphone permission logging
- Backend initialization logging
- Comprehensive callback logging
- All lifecycle events logged with `[VOICE]` prefix

**Lines 345-365:** Enhanced `endVoiceSession()` with:
- User-requested end banner
- `userRequestedEnd = true` flag set
- Clear logging of user-initiated termination

**Lines 367-468:** Enhanced `completeSession()` with:
- Duplicate completion guard (`sessionCompletionSent`)
- Detailed logging of completion state
- **DIAGNOSTIC BEHAVIOR:** Suppress redirect on unexpected disconnect
- User-initiated vs unexpected disconnect distinction
- Stay on page for unexpected disconnect (preserve console)
- Re-enable start button for retry on unexpected disconnect

---

## Exact Lifecycle Callbacks Supported by SDK v1.21.0

**Verified from official @elevenlabs/client documentation:**

### Core Callbacks (Instrumented)

1. **onConnect** - Called when websocket connection established
   - Receives: `{ conversationId }`
   - Logged: Connection data, conversation ID

2. **onDisconnect** - Called when websocket connection ended
   - Receives: (no parameters)
   - Logged: Disconnect event, user vs unexpected

3. **onError** - Called when error encountered
   - Receives: error object
   - Logged: Error type, name, message, object, stack

4. **onStatusChange** - Called when connection status changes
   - Receives: status object
   - Values: `connected`, `connecting`, `disconnected`
   - Logged: Full status object

5. **onModeChange** - Called when mode changes
   - Receives: `{ mode }` object
   - Values: `speaking`, `listening`
   - Logged: Mode object and mode value

6. **onMessage** - Called when text message received
   - Receives: message object with type, role, content
   - Logged: Message type, role, content presence

7. **onDebug** - Called for debugging events
   - Receives: debug event object
   - Logged: Full debug event

### Additional Callbacks Available (Not Instrumented)

- `onCanSendFeedbackChange`
- `onUnhandledClientToolCall`
- `onAudio`
- `onInterruption`
- `onVadScore`
- `onMCPToolCall`
- `onMCPConnectionStatus`
- `onAgentToolRequest`
- `onAgentToolResponse`
- `onConversationMetadata`
- `onAsrInitiationMetadata`
- `onAgentChatResponsePart`
- `onAudioAlignment`
- `onGuardrailTriggered`
- `onAgentResponseCorrection`

---

## How Unexpected Disconnect is Distinguished

### User-Initiated End

**Trigger:** User clicks "End Conversation" button

**Flow:**
```javascript
endVoiceSession() called
  ↓
userRequestedEnd = true
  ↓
endVoiceConversation()
  ↓
onDisconnect fires
  ↓
handleSessionEnd()
  ↓
completeSession()
  ↓
Check: userRequestedEnd === true
  ↓
NORMAL: Redirect to /client/home after 2s
```

**Logging:**
```
[VOICE] ═══ USER REQUESTED END ═══
[VOICE] Ending conversation
[VOICE] Conversation ended
[VOICE] UI: Conversation disconnected { userRequestedEnd: true, ... }
[VOICE] Disconnect was user-initiated (normal)
[VOICE] User-initiated end, redirecting to client home
```

---

### Unexpected Disconnect

**Trigger:** ElevenLabs SDK calls `onDisconnect` without user action

**Flow:**
```javascript
onDisconnect fires (SDK-initiated)
  ↓
Check: userRequestedEnd === false
  ↓
handleSessionEnd()
  ↓
completeSession()
  ↓
Check: userRequestedEnd === false
  ↓
DIAGNOSTIC: Stay on page, show error, preserve console
```

**Logging:**
```
[VOICE] UI: Conversation disconnected { userRequestedEnd: false, ... }
[VOICE] ⚠ Disconnect was UNEXPECTED
[VOICE] ⚠ UNEXPECTED DISCONNECT - staying on page for diagnostics
```

**UI Behavior:**
- Status: "Voice connection ended unexpectedly. Check browser console for diagnostic details."
- Start button re-enabled
- End button hidden
- User remains on voice page
- Console preserved for analysis

---

## Automatic Redirect Suppression

### Previous Behavior (All Cases)

```
Conversation ends
  ↓
completeSession()
  ↓
POST /voice/session/X/complete → 200
  ↓
setTimeout(() => redirect to /client/home, 2000)
  ↓
Console lost, diagnostics hidden
```

---

### New Diagnostic Behavior

**User-initiated end:**
```
userRequestedEnd === true
  ↓
POST /voice/session/X/complete → 200
  ↓
setTimeout(() => redirect to /client/home, 2000)
  ↓
NORMAL FLOW (unchanged)
```

**Unexpected disconnect:**
```
userRequestedEnd === false
  ↓
POST /voice/session/X/complete → 200
  ↓
DO NOT REDIRECT
  ↓
Stay on voice page
  ↓
Show error message
  ↓
Preserve console for diagnostics
  ↓
Re-enable start button for retry
```

---

## Session Completion Duplicate Prevention

### Guard Implementation

**Flag:** `sessionCompletionSent`

**Check in `completeSession()`:**
```javascript
if (sessionCompletionSent) {
    console.warn('[VOICE] Session completion already sent, skipping');
    return;
}

sessionCompletionSent = true;
```

**Why needed:**
- `onDisconnect` callback calls `handleSessionEnd()`
- `handleSessionEnd()` calls `completeSession()`
- If `endVoiceSession()` also calls `completeSession()`, duplicate POST possible
- Guard prevents multiple POST /voice/session/X/complete requests

**Reset:** Flag reset at start of each new `startVoiceSession()` call

---

## Backend Architecture Unchanged

**Confirmed NO changes to:**
- ✅ app.py
- ✅ voice_service.py
- ✅ models.py
- ✅ Database schema
- ✅ Signed URL generation
- ✅ ElevenLabs API key handling
- ✅ Agent ID
- ✅ Coaching context architecture
- ✅ Identity architecture
- ✅ Extraction logic
- ✅ Background processor
- ✅ Webhook signature validation
- ✅ npm/esbuild architecture
- ✅ Render build configuration

**Only frontend changed:** Diagnostic instrumentation in JavaScript

---

## Expected Browser Console Output

### Successful Connection (Expected)

```
[VOICE] ElevenLabs SDK module ready (v1.21.0)
[VOICE] ═══ START VOICE SESSION ═══
[VOICE] Engagement ID: 1
[VOICE] Requesting microphone permission
[VOICE] ✓ Microphone permission granted
[VOICE] Backend initialization starting
[VOICE] ✓ Backend session initialized: 38
[VOICE] Signed URL received: { hasSignedUrl: true, signedUrlLength: 148 }
[VOICE] Starting ElevenLabs conversation with official SDK v1.21.0
[VOICE] Signed URL present: true
[VOICE] Signed URL length: 148
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
[VOICE] Mode change: { mode: 'listening' }
[VOICE] Mode value: listening
[VOICE] UI: Mode change received: listening
[VOICE] Message received: { type: '...', role: '...', hasContent: true }
[VOICE] UI: Message received
[VOICE] Mode change: { mode: 'speaking' }
[VOICE] Mode value: speaking
[VOICE] UI: Mode change received: speaking
```

---

### Immediate Disconnect (Current Issue)

```
[VOICE] ElevenLabs SDK module ready (v1.21.0)
[VOICE] ═══ START VOICE SESSION ═══
[VOICE] Engagement ID: 1
[VOICE] Requesting microphone permission
[VOICE] ✓ Microphone permission granted
[VOICE] Backend initialization starting
[VOICE] ✓ Backend session initialized: 38
[VOICE] Signed URL received: { hasSignedUrl: true, signedUrlLength: 148 }
[VOICE] Starting ElevenLabs conversation with official SDK v1.21.0
[VOICE] Signed URL present: true
[VOICE] Signed URL length: 148
[VOICE] Calling Conversation.startSession

THEN ONE OF:

Option A - startSession rejects:
[VOICE] ✗ startSession REJECTED
[VOICE] Rejection error name: ...
[VOICE] Rejection error message: ...
[VOICE] Rejection error: ...
[VOICE] Rejection stack: ...

Option B - startSession resolves but immediately disconnects:
[VOICE] ✓ startSession resolved successfully
[VOICE] Conversation object created: true
[VOICE] ✓ Voice session setup complete
[VOICE] ✗ onDisconnect fired
[VOICE] UI: Conversation disconnected { userRequestedEnd: false, sessionCompletionSent: false }
[VOICE] ⚠ Disconnect was UNEXPECTED

Option C - onError fires:
[VOICE] ✓ startSession resolved successfully
[VOICE] ✗ onError fired
[VOICE] Error type: ...
[VOICE] Error name: ...
[VOICE] Error message: ...
[VOICE] Error object: ...
[VOICE] Error stack: ...

Option D - onStatusChange shows failure:
[VOICE] Status change: disconnected
[VOICE] UI: Status change received: disconnected
```

**The diagnostic output will reveal exactly which scenario occurs.**

---

## Test Instructions

### 1. Deploy Changes

```bash
git add frontend/voice-client.js templates/voice_coaching.html
git commit -m "Add comprehensive diagnostic instrumentation for voice disconnect"
git push
```

**Render will rebuild bundle automatically.**

---

### 2. Open Browser Console

1. Navigate to voice coaching page
2. Open Developer Tools (F12)
3. Go to Console tab
4. Clear console

---

### 3. Verify SDK Load

**Expected:**
```
[VOICE] ElevenLabs SDK module ready (v1.21.0)
```

**If missing:** Bundle didn't load, check network tab

---

### 4. Start Conversation (DO NOT END MANUALLY)

1. Click "Start Conversation" button **once**
2. Grant microphone permission if prompted
3. **DO NOT** click "End Conversation"
4. Let the conversation run its natural course

---

### 5. Observe Complete Lifecycle

**Watch console for:**
- Backend initialization
- Signed URL receipt
- startSession call
- startSession resolution or rejection
- onConnect, onDisconnect, onError callbacks
- Status and mode changes
- Unexpected disconnect warning

---

### 6. Check Page Behavior

**If disconnect is unexpected:**
- Page should **NOT** redirect to /client/home
- Status should show: "Voice connection ended unexpectedly..."
- Start button should be re-enabled
- Console should be preserved

**If you manually end:**
- Page **WILL** redirect to /client/home after 2s
- This is normal behavior

---

### 7. Copy Console Output

**Copy the entire console log and provide it for analysis.**

The output will answer:
- Does startSession reject or resolve?
- If it resolves, does onConnect fire?
- If onConnect fires, does onDisconnect fire immediately?
- If onError fires, what is the error?
- What status/mode changes occur?

---

## Success Criteria for This Diagnostic Pass

**This pass is successful when we can answer:**

> **Exactly why is the ElevenLabs conversation terminating immediately after successful signed-URL initialization?**

**Possible answers we're looking for:**

1. **startSession rejects** → Error in SDK initialization (error message will tell us why)
2. **onConnect never fires** → Connection never established (status changes will show why)
3. **onConnect fires then immediate onDisconnect** → Connection drops immediately (may indicate signed URL issue)
4. **onError fires** → SDK encountered specific error (error object will tell us what)
5. **onStatusChange shows disconnected** → Connection state never reaches connected
6. **onDebug events** → Internal SDK events may reveal issue

**We need the actual SDK error/disconnect information, not defensive code.**

---

## Webhook Issue (Documented, Not Fixed)

**Observed:**
```
ELEVENLABS WEBHOOK: Invalid signature
POST /webhooks/elevenlabs/post-call → 401
```

**Status:** Documented as separate issue

**Reason:** Not fixing during this diagnostic pass

**Impact:** Does not affect browser conversation lifecycle

**Follow-up:** Will be addressed after conversation lifecycle is stable

---

## Summary

✅ **Files changed:** 2 (frontend/voice-client.js, templates/voice_coaching.html)  
✅ **Callbacks instrumented:** 7 core callbacks from v1.21.0 API  
✅ **User vs unexpected:** Distinguished via `userRequestedEnd` flag  
✅ **Redirect suppressed:** Unexpected disconnect stays on page  
✅ **Duplicate prevention:** `sessionCompletionSent` guard added  
✅ **Backend unchanged:** Confirmed (only frontend diagnostics)  
✅ **Expected output:** Comprehensive lifecycle logging with [VOICE] prefix  

**The diagnostic instrumentation will reveal exactly why the ElevenLabs conversation disconnects immediately after successful backend initialization. The browser will remain on the voice page for unexpected disconnects, preserving the console output for analysis.**

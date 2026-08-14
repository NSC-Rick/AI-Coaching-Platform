# Diagnostic Instructions - Blank AI Response Issue

## Current Status

✅ **Diagnostic logging implemented** across all 4 checkpoints  
⏳ **Awaiting production deployment and test results**

---

## What Was Done

### Diagnostic Checkpoints Added

1. **Checkpoint 1: Raw OpenAI Response** (`coaching/ai_service.py`)
   - Logs response ID, model, finish reason, choices count
   - Logs message role, content type, content length
   - Shows preview of actual content returned by OpenAI

2. **Checkpoint 2: AIService Return Value** (`coaching/ai_service.py`)
   - Logs the exact value being returned by `generate_coaching_response()`
   - Shows type and preview of return value

3. **Checkpoint 3: SessionMessage Persistence** (`app.py`)
   - Logs message before database commit
   - Queries and logs message after database commit
   - Verifies content survives persistence

4. **Checkpoint 4: Template Rendering** (`templates/coaching_session.html`)
   - HTML comments show total message count
   - HTML comments show each message's role and content length
   - Visible in browser "View Source"

---

## Next Steps for User

### 1. Deploy to Render

Push the diagnostic code to Render:
```bash
git add .
git commit -m "Add diagnostic logging for blank response issue"
git push
```

### 2. Run Test Session

1. Login as client: `sarah@example.com` / `password`
2. Click "💬 Text Coaching"
3. Observe if initial coach message is blank
4. Send a message: "I'm worried about cash flow"
5. Observe if coach response is blank

### 3. Check Render Logs

In Render dashboard:
1. Go to your web service
2. Click "Logs"
3. Look for `[DIAGNOSTIC]` entries
4. Copy all diagnostic output

### 4. Check Browser Source

In the coaching session page:
1. Right-click → "View Page Source"
2. Search for `DIAGNOSTIC CHECKPOINT 4`
3. Look at the HTML comments showing message data

---

## What to Look For

### Scenario A: OpenAI Returns No Content

**Diagnostic Output:**
```
[DIAGNOSTIC] Message Content Length: 0
[DIAGNOSTIC] Message Content Preview: None
```

**Meaning:** OpenAI API returned empty response  
**Likely Cause:** Model issue, prompt issue, or API configuration  
**Next Action:** Investigate prompt or model behavior

---

### Scenario B: AIService Loses Content

**Diagnostic Output:**
```
[DIAGNOSTIC] Message Content Length: 245
[DIAGNOSTIC] Message Content Preview: 'Hi Sarah...'
[DIAGNOSTIC] AIService Return Type: <class 'NoneType'>
[DIAGNOSTIC] AIService Return Value: None
```

**Meaning:** OpenAI returned content but AIService returned None  
**Likely Cause:** Bug in content extraction logic  
**Next Action:** Fix AIService extraction

---

### Scenario C: Persistence Loses Content

**Diagnostic Output:**
```
[DIAGNOSTIC] Initial Message Length: 245
[DIAGNOSTIC] Initial Message Preview: 'Hi Sarah...'
[DIAGNOSTIC] Persisted Content Length: 0
[DIAGNOSTIC] Persisted Content Preview: None
```

**Meaning:** Content exists before commit but not after  
**Likely Cause:** Database schema issue or model issue  
**Next Action:** Check SessionMessage model and database

---

### Scenario D: Template Doesn't Render

**Diagnostic Output:**
```
[DIAGNOSTIC] Persisted Content Length: 245
[DIAGNOSTIC] Persisted Content Preview: 'Hi Sarah...'
```

**HTML Source:**
```html
<!-- Message 1: role=assistant, content_length=0 -->
```

**Meaning:** Database has content but template doesn't receive it  
**Likely Cause:** Query issue or template variable issue  
**Next Action:** Check coaching_session route and template data

---

## Expected Success Output

If everything works correctly, you should see:

**Render Logs:**
```
[DIAGNOSTIC] OpenAI Response ID: chatcmpl-xxxxx
[DIAGNOSTIC] Model: gpt-5-mini
[DIAGNOSTIC] Finish Reason: stop
[DIAGNOSTIC] Choices Count: 1
[DIAGNOSTIC] Message Role: assistant
[DIAGNOSTIC] Message Content Type: <class 'str'>
[DIAGNOSTIC] Message Content Length: 245
[DIAGNOSTIC] Message Content Preview: 'Hi Sarah. How are things going today?'
[DIAGNOSTIC] AIService Return Type: <class 'str'>
[DIAGNOSTIC] AIService Return Value: 'Hi Sarah. How are things going today?'
[DIAGNOSTIC] Initial Message Type: <class 'str'>
[DIAGNOSTIC] Initial Message Length: 245
[DIAGNOSTIC] Initial Message Preview: 'Hi Sarah. How are things going today?'
[DIAGNOSTIC] Persisted Message ID: 123
[DIAGNOSTIC] Persisted Role: assistant
[DIAGNOSTIC] Persisted Content Type: <class 'str'>
[DIAGNOSTIC] Persisted Content Length: 245
[DIAGNOSTIC] Persisted Content Preview: 'Hi Sarah. How are things going today?'
```

**HTML Source:**
```html
<!-- Total messages: 1 -->
<!-- Message 1: role=assistant, content_length=245 -->
<div class="message message-assistant">
    <div class="message-label">Coach</div>
    <div class="message-content">Hi Sarah. How are things going today?</div>
</div>
```

**UI Display:**
```
Coach
Hi Sarah. How are things going today?
```

---

## After Identifying Root Cause

Once you know which checkpoint shows the failure, report back with:

1. **Full diagnostic output** from Render logs
2. **HTML source** showing the diagnostic comments
3. **Screenshot** of the blank message (if still blank)
4. **Which checkpoint** shows the problem

Then I can implement the specific fix needed.

---

## Cleanup After Fix

Once the issue is resolved, remove diagnostic logging:

1. Remove all `print(f"[DIAGNOSTIC] ...")` from Python files
2. Optionally remove HTML comments from template
3. Commit and redeploy

---

## Files Modified

- `coaching/ai_service.py` - Diagnostic logging added
- `app.py` - Diagnostic logging added (2 routes)
- `templates/coaching_session.html` - HTML comments added
- `DIAGNOSTIC_BLANK_RESPONSE.md` - Documentation
- `DIAGNOSTIC_INSTRUCTIONS.md` - This file

**Ready for deployment and testing.**

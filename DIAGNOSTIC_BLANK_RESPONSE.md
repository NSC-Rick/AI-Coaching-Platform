# Build 002 - Blank AI Response Diagnostic

## Objective

Diagnose why Build 002 successfully receives HTTP 200 responses from OpenAI, but the Coaching Session UI displays blank Coach messages.

---

## Diagnostic Checkpoints Implemented

### CHECKPOINT 1: Raw OpenAI Response

**Location:** `coaching/ai_service.py` - `generate_coaching_response()`

**Logs Added:**
```python
print(f"[DIAGNOSTIC] OpenAI Response ID: {response.id}")
print(f"[DIAGNOSTIC] Model: {response.model}")
print(f"[DIAGNOSTIC] Finish Reason: {response.choices[0].finish_reason}")
print(f"[DIAGNOSTIC] Choices Count: {len(response.choices)}")
print(f"[DIAGNOSTIC] Message Role: {response.choices[0].message.role}")
print(f"[DIAGNOSTIC] Message Content Type: {type(response.choices[0].message.content)}")
print(f"[DIAGNOSTIC] Message Content Length: {len(response.choices[0].message.content) if response.choices[0].message.content else 0}")
print(f"[DIAGNOSTIC] Message Content Preview: {repr(response.choices[0].message.content[:100] if response.choices[0].message.content else None)}")
```

**Purpose:** Verify OpenAI actually returned visible assistant text.

---

### CHECKPOINT 2: AIService Return Value

**Location:** `coaching/ai_service.py` - `generate_coaching_response()`

**Logs Added:**
```python
result = response.choices[0].message.content

print(f"[DIAGNOSTIC] AIService Return Type: {type(result)}")
print(f"[DIAGNOSTIC] AIService Return Value: {repr(result[:100] if result else result)}")

return result
```

**Purpose:** Verify what value AIService returns (string, None, empty, etc.)

---

### CHECKPOINT 3: SessionMessage Persistence

**Location:** `app.py` - Both initial message and subsequent message routes

**Logs Added (Before Persistence):**
```python
print(f"[DIAGNOSTIC] Initial Message Type: {type(initial_message)}")
print(f"[DIAGNOSTIC] Initial Message Length: {len(initial_message) if initial_message else 0}")
print(f"[DIAGNOSTIC] Initial Message Preview: {repr(initial_message[:100] if initial_message else initial_message)}")
```

**Logs Added (After Persistence):**
```python
persisted_msg = db.session.get(SessionMessage, assistant_msg.id)
print(f"[DIAGNOSTIC] Persisted Message ID: {persisted_msg.id}")
print(f"[DIAGNOSTIC] Persisted Role: {persisted_msg.role}")
print(f"[DIAGNOSTIC] Persisted Content Type: {type(persisted_msg.content)}")
print(f"[DIAGNOSTIC] Persisted Content Length: {len(persisted_msg.content) if persisted_msg.content else 0}")
print(f"[DIAGNOSTIC] Persisted Content Preview: {repr(persisted_msg.content[:100] if persisted_msg.content else persisted_msg.content)}")
```

**Purpose:** Verify text is not lost during or after database persistence.

---

### CHECKPOINT 4: Template Rendering

**Location:** `templates/coaching_session.html`

**HTML Comments Added:**
```html
<!-- DIAGNOSTIC CHECKPOINT 4: Template Rendering -->
<!-- Total messages: {{ messages|length }} -->
{% for message in messages %}
<!-- Message {{ loop.index }}: role={{ message.role }}, content_length={{ message.content|length if message.content else 0 }} -->
<div class="message message-{{ message.role }}">
    <div class="message-label">
        {% if message.role == 'user' %}You{% else %}Coach{% endif %}
    </div>
    <div class="message-content">{{ message.content }}</div>
</div>
{% endfor %}
```

**Purpose:** Verify template receives and renders SessionMessage data correctly.

---

## How to Use Diagnostics

### Step 1: Deploy with Diagnostics

Deploy the code with diagnostic logging enabled.

### Step 2: Run Test Session

1. Login as client (sarah@example.com)
2. Start coaching session
3. Send a message
4. Observe UI (blank or visible response?)

### Step 3: Check Render Logs

View Render application logs and look for `[DIAGNOSTIC]` entries.

### Step 4: Identify Failure Boundary

Based on diagnostic output, determine which checkpoint shows the problem:

**Scenario A: OpenAI returned no visible text**
- Checkpoint 1 shows: `Message Content Length: 0` or `None`
- **Root Cause:** OpenAI API issue or model configuration
- **Fix:** Investigate prompt, model settings, or API response

**Scenario B: OpenAI returned text but AIService failed to extract it**
- Checkpoint 1 shows: Content exists
- Checkpoint 2 shows: `AIService Return Value: None` or empty
- **Root Cause:** Extraction logic in AIService
- **Fix:** Verify `response.choices[0].message.content` access

**Scenario C: AIService returned text but persistence lost it**
- Checkpoint 2 shows: Valid string returned
- Checkpoint 3A shows: Valid string before persistence
- Checkpoint 3B shows: Empty or None after persistence
- **Root Cause:** Database persistence issue
- **Fix:** Check SessionMessage model, database schema, or commit logic

**Scenario D: Database contains text but template failed to render it**
- Checkpoint 3B shows: Valid content in database
- Checkpoint 4 shows: `content_length=0` or content not visible in HTML
- **Root Cause:** Template rendering issue
- **Fix:** Check Jinja2 template, CSS, or escaping

---

## Expected Diagnostic Output (Success Case)

```
[DIAGNOSTIC] OpenAI Response ID: chatcmpl-xxxxx
[DIAGNOSTIC] Model: gpt-5-mini
[DIAGNOSTIC] Finish Reason: stop
[DIAGNOSTIC] Choices Count: 1
[DIAGNOSTIC] Message Role: assistant
[DIAGNOSTIC] Message Content Type: <class 'str'>
[DIAGNOSTIC] Message Content Length: 245
[DIAGNOSTIC] Message Content Preview: 'Hi Sarah. How are things going with the business today?'
[DIAGNOSTIC] AIService Return Type: <class 'str'>
[DIAGNOSTIC] AIService Return Value: 'Hi Sarah. How are things going with the business today?'
[DIAGNOSTIC] Initial Message Type: <class 'str'>
[DIAGNOSTIC] Initial Message Length: 245
[DIAGNOSTIC] Initial Message Preview: 'Hi Sarah. How are things going with the business today?'
[DIAGNOSTIC] Persisted Message ID: 123
[DIAGNOSTIC] Persisted Role: assistant
[DIAGNOSTIC] Persisted Content Type: <class 'str'>
[DIAGNOSTIC] Persisted Content Length: 245
[DIAGNOSTIC] Persisted Content Preview: 'Hi Sarah. How are things going with the business today?'
```

HTML Comment in page source:
```html
<!-- Message 1: role=assistant, content_length=245 -->
```

---

## Next Steps After Diagnosis

1. **Review Render logs** for diagnostic output
2. **Identify which checkpoint** shows the failure
3. **Implement minimal fix** at the identified boundary
4. **Remove diagnostic logging** after fix is confirmed
5. **Run verification test** per original request

---

## Files Modified for Diagnostics

1. `coaching/ai_service.py` - Added Checkpoints 1 & 2
2. `app.py` - Added Checkpoint 3 (both routes)
3. `templates/coaching_session.html` - Added Checkpoint 4

**All changes are diagnostic only - no functional changes made.**

---

## Removal After Fix

Once root cause is identified and fixed, remove:
- All `print(f"[DIAGNOSTIC] ...")` statements
- HTML diagnostic comments (optional - they're harmless)

Keep the fix, remove the diagnostics.

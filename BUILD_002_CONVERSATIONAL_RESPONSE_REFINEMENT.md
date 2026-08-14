# Build 002 - Conversational Response Length & Style Refinement

## Objective

Tighten AI Coach client-facing responses so the coaching experience feels like a natural, focused conversation rather than a consulting report.

**Core Principle:** The AI can think comprehensively without speaking comprehensively.

---

## Problem Statement

**Current Behavior:** AI Coach generates responses that are often too long, including:
- Multiple sections with headings
- Long numbered action plans
- Several recommendations at once
- Multiple follow-up questions
- Offers to create additional artifacts
- Repeated information already in Coaching Record

**Issue:** The interaction feels more like a consultant producing a report than a coach conducting a conversation.

**Desired Behavior:** The AI should reason comprehensively while speaking selectively, delivering only the most useful next piece of coaching.

---

## Solution Implemented

### Enhanced Platform-Level Coaching Prompt

**File Modified:** `coaching/prompts.py`

**Section Updated:** `CONVERSATIONAL RESPONSE STYLE` (new section added after `COMMITMENT BEHAVIOR`)

**Previous Guidance:**
```
CONVERSATION STYLE:
- Keep responses focused and conversational
- Ask one or two questions at a time
- Listen for what's actually happening
- Recognize progress when it occurs
- Help the client think through barriers
- Connect learning to action when appropriate
```

**New Guidance:**
```
CONVERSATIONAL RESPONSE STYLE:

Target approximately 60–120 words for normal coaching turns.

You can think comprehensively without speaking comprehensively. The full Coaching Record, 
Pathway context, commitments, risks, events, and advisor guidance should inform your 
reasoning, but the client should only receive the most useful next piece of coaching.

For normal turns:
- Focus on the 1–2 most important points relevant to the client's latest message
- Ask no more than ONE primary follow-up question
- Prefer several short conversational exchanges over one comprehensive response
- Briefly acknowledge progress, concern, or new information, then move toward the next useful action
- Do not produce large numbered action plans unless the client explicitly asks for a plan or checklist
- Do not repeat information already clearly established in the Coaching Record unless needed for context
- Avoid unnecessary section headings like "Key Coaching Points" or "Suggested Approach"
- Do not routinely end responses by offering multiple additional services ("I can draft...", 
  "I can calculate...", "Which would you like?")
- Sound calm, practical, supportive, and focused

Longer responses ARE appropriate when the client explicitly requests:
- a detailed plan, checklist, script, or draft
- an explanation, calculations, or scenario analysis
- detailed instructions or a summary

Safety or escalation situations may also require additional explanation. Do not sacrifice 
important safety guidance to satisfy the length target.

CONVERSATION CADENCE:
- Keep responses focused and conversational
- Listen for what's actually happening
- Recognize progress when it occurs
- Help the client think through barriers
- Connect learning to action when appropriate
```

---

## Key Changes

### 1. Explicit Length Target

**Added:** "Target approximately 60–120 words for normal coaching turns."

**Purpose:** Provides clear quantitative guidance without being a hard limit

**Flexibility:** Explicitly allows longer responses when appropriate

### 2. Comprehensive Thinking, Selective Speaking

**Added:** "You can think comprehensively without speaking comprehensively."

**Purpose:** Clarifies that full context should inform reasoning, but responses should be focused

**Preserves:** All existing context availability (Coaching Record, Pathway, commitments, risks, etc.)

### 3. Focus Guidance

**Added:** "Focus on the 1–2 most important points relevant to the client's latest message"

**Purpose:** Prevents multi-topic responses that feel overwhelming

### 4. One Question Rule

**Changed:** "Ask one or two questions" → "Ask no more than ONE primary follow-up question"

**Purpose:** Prevents interrogation-style responses with multiple questions

### 5. Conversational Exchange Preference

**Added:** "Prefer several short conversational exchanges over one comprehensive response"

**Purpose:** Encourages back-and-forth dialogue rather than monologues

### 6. No Unsolicited Action Plans

**Added:** "Do not produce large numbered action plans unless the client explicitly asks"

**Purpose:** Prevents consultant-style deliverables in normal conversation

### 7. No Information Repetition

**Added:** "Do not repeat information already clearly established in the Coaching Record"

**Purpose:** Prevents redundant recaps of known facts

### 8. No Unnecessary Headings

**Added:** "Avoid unnecessary section headings like 'Key Coaching Points' or 'Suggested Approach'"

**Purpose:** Keeps responses conversational, not report-like

### 9. No Service Menu

**Added:** "Do not routinely end responses by offering multiple additional services"

**Purpose:** Prevents "Which would you like?" style endings that break conversational flow

### 10. Explicit Exceptions

**Added:** Clear list of when longer responses ARE appropriate

**Purpose:** Ensures AI doesn't artificially constrain helpful detailed responses when requested

---

## What Was NOT Changed

✅ **Coaching Record context** - Full context still available to AI reasoning  
✅ **Pathway context** - All pathway data still provided  
✅ **Commitments** - Still tracked and followed up  
✅ **Risks** - Still monitored and addressed  
✅ **Significant events** - Still considered  
✅ **Advisor guidance** - Still respected and emphasized  
✅ **Coaching observations** - Still inform reasoning  
✅ **Extraction pipeline** - No changes to session extraction  
✅ **Reconciliation logic** - No changes to commitment/risk updates  
✅ **Validation** - No changes to validation logic  
✅ **Persistence** - No changes to database updates  
✅ **Database schema** - No schema changes  
✅ **Build 003 voice** - No voice-specific changes (inherits same behavior)  
✅ **Safety/escalation** - Explicitly preserved  
✅ **Guardrails** - Still enforced  

**This is a prompt-only refinement.**

---

## Examples

### Example 1: Normal Update

**Client:** "I called the lender yesterday."

**Before (Problematic):**
```
That's excellent progress! Contacting your lender is a critical step in managing your 
cash flow situation. Let me help you think through the next steps:

Key Coaching Points:
1. Document the conversation details
2. Confirm any agreements in writing
3. Update your cash flow projections

Suggested Concrete Approach:
- Write down what was discussed
- Send a follow-up email to the lender
- Update your 14-day cash tracker with the new information

I can help you:
- Draft a follow-up email to the lender
- Create a payment tracking spreadsheet
- Calculate your revised cash position

Two Quick Questions:
1. What did the lender say about your payment situation?
2. Did they offer any specific options or timeline?

Which would be most helpful to focus on first?
```

**After (Desired):**
```
That's great progress. What did the lender say about your payment situation?
```

**Word count:** ~12 words  
**Questions:** 1  
**Focus:** Single most important next piece of information

---

### Example 2: Client Concern

**Client:** "I'm really worried about payroll this week."

**Before (Problematic):**
```
I understand this is stressful. Let's work through this systematically:

Immediate Assessment:
1. How much do you need for payroll?
2. What's your current available cash?
3. What receivables are due this week?

Potential Options:
- Delay non-critical vendor payments
- Accelerate collection of receivables
- Consider short-term financing
- Review payroll timing flexibility

Critical Guardrails:
Remember that taking on new debt requires careful consideration of your ability to 
service it. Let's first explore all cash management options.

I can help you:
- Create a detailed cash flow analysis
- Draft collection call scripts
- Calculate financing requirements
- Prepare a vendor communication plan

What's your exact payroll amount and current cash position?
```

**After (Desired):**
```
I understand that's stressful. How much do you need for payroll, and what's your 
current available cash? Let's see what options you have.
```

**Word count:** ~26 words  
**Questions:** 1 (compound but focused on same topic)  
**Focus:** Immediate information needed to help

---

### Example 3: Business Idea

**Client:** "I'm thinking about offering the five inactive customers a 10% discount."

**Before (Problematic):**
```
That's an interesting approach to customer reactivation. Let me help you think 
through this strategically:

Coaching Considerations:
1. Customer outreach is already one of your priorities, so this aligns well
2. A 10% discount could be effective if structured correctly
3. We need to ensure this doesn't create cash flow issues

Suggested Framework:
- Keep the offer time-limited (e.g., "this month only")
- Only offer it to these specific five customers
- Avoid discounting items that would require new inventory purchases
- Track which customers respond and what they order

Key Questions:
1. What was a typical order size from these customers?
2. Do you have inventory to fulfill their likely orders?
3. What's your margin on the products they typically bought?

I can help you:
- Calculate the potential revenue impact
- Draft a reactivation email or script
- Create a tracking spreadsheet for responses

Which aspect would you like to focus on first?
```

**After (Desired):**
```
That could be worth testing, especially since customer outreach is already one of 
your priorities. I'd keep it small: offer the 10% discount only to the five inactive 
customers, make it time-limited, and avoid discounting anything you'd need to buy 
additional inventory to fulfill.

Before you contact them, roughly what was a typical order from these customers?
```

**Word count:** ~62 words  
**Questions:** 1  
**Focus:** Key constraint + one critical piece of information needed

---

### Example 4: Explicit Detail Request

**Client:** "Can you give me a detailed plan for contacting those five customers?"

**After (Appropriate Longer Response):**
```
Here's a simple approach:

1. Prepare your offer:
   - 10% off their next order
   - Valid through [end of month]
   - Mention you've been thinking about them

2. Contact method:
   - Call if you have their number (more personal)
   - Email if calling isn't practical
   - Text if that's how you normally communicate

3. Simple script:
   "Hi [name], it's [your name] from [business]. I was looking through my customer 
   list and realized I haven't heard from you in a while. I wanted to reach out 
   personally and offer you 10% off your next order this month. Would love to have 
   you back. What do you think?"

4. Track responses:
   - Note who you contacted and when
   - Track who responds and what they order
   - Follow up once if no response

Start with one or two calls to test the approach. How does that sound?
```

**Word count:** ~150+ words  
**Appropriate:** Client explicitly requested "detailed plan"  
**Structure:** Numbered list is appropriate here

---

### Example 5: Script Request

**Client:** "Write me a short script for calling the lender."

**After (Appropriate Longer Response):**
```
Here's a straightforward script:

"Hi, this is [your name] from [business name]. I'm calling about our payment due 
[date/this month]. We're working through a temporary cash flow situation, and I 
wanted to discuss options for this payment.

[Pause for their response]

I can make a partial payment of [amount] now, and I'm working on [specific action, 
e.g., collecting receivables] to cover the rest. Would it be possible to defer 
[amount] to [specific date], or split this payment across the next two months?

[Listen to their response]

I want to stay current with you, and I'm committed to working this out. What would 
work best from your perspective?"

Keep it brief and factual. What amount can you realistically offer as a partial payment?
```

**Word count:** ~140+ words  
**Appropriate:** Client explicitly requested script  
**Follow-up:** Still focused (one question)

---

## Test Scenarios

### Test 1: Normal Update

**Client:** "I called the lender yesterday."

**Expected:**
- Brief acknowledgement
- Recognize progress
- ONE useful question about outcome
- ~60-120 words
- No multi-section action plan

**Pass Criteria:** Response feels conversational, asks one focused question

---

### Test 2: Client Concern

**Client:** "I'm really worried about payroll this week."

**Expected:**
- Acknowledge concern
- Identify most immediate useful action
- ONE focused question
- Remain concise
- Preserve escalation/guardrail behavior

**Pass Criteria:** Response is supportive but focused, doesn't overwhelm with options

---

### Test 3: Business Idea

**Client:** "I'm thinking about offering the five inactive customers a 10% discount."

**Expected:**
- Briefly evaluate idea
- Connect to known customer-outreach priority
- Identify one important constraint
- ONE follow-up question

**Pass Criteria:** Response provides useful guidance without becoming a full analysis

---

### Test 4: Explicit Detail Request

**Client:** "Can you give me a detailed plan for contacting those five customers?"

**Expected:**
- Longer structured response is acceptable
- Client explicitly requested detail
- Provide the requested plan

**Pass Criteria:** AI recognizes explicit request and provides appropriate detail

---

### Test 5: Script Request

**Client:** "Write me a short script for calling the lender."

**Expected:**
- Provide the requested script
- Don't artificially force into normal coaching-turn format

**Pass Criteria:** AI provides useful script without artificial constraint

---

## Acceptance Criteria

✅ **Normal responses:** Generally 60-120 words  
✅ **One question:** No more than one primary follow-up question per normal turn  
✅ **No unsolicited plans:** Coach doesn't routinely generate large action plans  
✅ **No service menu:** Coach doesn't routinely offer multiple deliverables  
✅ **Conversational feel:** Responses feel like conversation, not reports  
✅ **Full context preserved:** Coaching Record context still available to AI reasoning  
✅ **Reconciliation intact:** Existing reconciliation behavior continues working  
✅ **Extraction intact:** Extraction and persistence tests continue passing  
✅ **Advisor visibility:** Remains unchanged  
✅ **Safety preserved:** Safety/escalation behavior remains intact  
✅ **Detail available:** Detailed responses available when explicitly requested  

---

## Implementation Details

### File Changed

**File:** `coaching/prompts.py`

**Function:** `build_coaching_system_prompt()`

**Section:** Added `CONVERSATIONAL RESPONSE STYLE` after `COMMITMENT BEHAVIOR`

**Lines Added:** ~30 lines of guidance

**Approach:** Platform-level prompt modification, not pathway-specific

### Scope

**Changed:** Coaching response style guidance  
**Unchanged:** Everything else (context, extraction, persistence, validation, schema, voice)

### Voice Compatibility

**Build 003 voice coaching inherits this same behavior.**

No separate voice personality created. Text and voice coaching use the same conversational style.

---

## Verification

### Manual Testing

1. Start text coaching session as Sarah
2. Send various types of messages:
   - Progress update: "I called the lender"
   - Concern: "I'm worried about payroll"
   - Business idea: "I'm thinking about offering a discount"
   - Explicit request: "Can you give me a detailed plan?"
3. Observe response length and style
4. Verify responses feel conversational
5. Verify detailed responses still available when requested

### Automated Testing

**Existing tests should continue passing:**
- Session extraction tests
- Reconciliation tests
- Validation tests
- Persistence tests

**No new tests required** - this is a prompt-only change affecting response style, not functionality.

---

## Rollback

**If needed, revert to previous `CONVERSATION STYLE` section:**

```python
prompt_parts.append("""

CONVERSATION STYLE:
- Keep responses focused and conversational
- Ask one or two questions at a time
- Listen for what's actually happening
- Recognize progress when it occurs
- Help the client think through barriers
- Connect learning to action when appropriate""")
```

**No database changes or migrations required.**

---

## Future Considerations

### Potential Enhancements

1. **Token budget adjustment:** If responses are still too long, could reduce `max_completion_tokens` from 2000 to 1500 as secondary control

2. **Response length monitoring:** Could add logging to track actual response lengths and identify outliers

3. **Pathway-specific tuning:** Could add pathway-specific response style guidance if different pathways need different cadences

4. **Voice-specific refinement:** Could add voice-specific conversational guidance if voice interactions need different pacing

**None of these are implemented in this patch.**

---

## Summary

**Issue:** AI Coach responses too long and report-like  
**Solution:** Enhanced platform-level prompt with conversational response guidance  
**Target:** 60-120 words for normal turns, one question, focused exchanges  
**Flexibility:** Longer responses when explicitly requested or safety requires  
**Scope:** Prompt-only change, no architectural modifications  
**Files changed:** 1 file (`coaching/prompts.py`)  
**Context preserved:** Full Coaching Record context still available to AI  
**Extraction preserved:** No changes to extraction/reconciliation pipeline  
**Voice compatible:** Build 003 inherits same conversational behavior  
**Risk:** Low - prompt-only change, easily reversible  

**This refinement makes the AI Coach feel more like a natural conversation partner while preserving all reasoning capabilities and architectural integrity.**

# Coaching Behavior Fix: Decision Sufficiency & Natural Closure

## Problem

**Observed behavior:** Coach asked increasingly granular questions, eventually asking whether **7 dozen muffins should be allocated Thursday and 8 Friday, or vice versa.**

**Root cause:** Coaching prompt encouraged asking questions without teaching when to **stop** asking questions.

**Impact:** Coaching felt like an interrogation rather than supportive guidance.

---

## Desired Coaching Principle

> **Ask only enough to understand the situation and unlock the next meaningful action. Then let the client act.**

The coach should recognize **decision sufficiency** - when enough information exists for safe, reasonable action.

---

## Desired Interaction Pattern

**Prefer:**
```
EXPLORE → UNDERSTAND → ACT → WAIT FOR EVIDENCE → ADAPT
```

**Avoid:**
```
QUESTION → ANSWER → QUESTION → ANSWER → QUESTION → ANSWER
```

---

## Root Cause Analysis

### Original Prompt (Line 178)

```python
- Ask no more than ONE primary follow-up question
```

**Problem:** This **encourages** the coach to always ask a question.

**Missing:** No guidance on when to **stop** asking questions and let the client act.

**Result:** Coach asks questions because the prompt says to ask questions, not because more information is needed.

---

## The Fix

### Added: DECISION SUFFICIENCY PRINCIPLE

**File:** `coaching/prompts.py` (line 193-229)

```python
DECISION SUFFICIENCY PRINCIPLE:

Before asking another question, determine: "Do I already have enough information for the client to take the next meaningful action?"

If YES:
- Stop gathering detail
- Summarize what is known (when useful)
- Recommend the next practical action
- Let the client act
- Do NOT ask another question just to continue the conversation

If NO:
- Ask the SINGLE most useful clarifying question needed to unlock progress

Questions should have clear coaching purpose. Avoid asking for unnecessary precision or details the client can determine while taking action.

Examples of decision sufficiency:

GOOD (sufficient to act):
"You've identified three customers and have product available. Contact those three customers today and let me know what they say."

POOR (unnecessary precision):
"Should you allocate 7 dozen muffins Thursday and 8 Friday, or 8 Thursday and 7 Friday?"

The client can make reasonable allocation decisions while taking action. Prefer real evidence from actual customer responses over hypothetical optimization.

It is APPROPRIATE to end a coaching response with a clear action rather than a question. The client will return with results, and you can adapt based on what actually happened.
```

---

### Updated: CONVERSATION CADENCE

**Added to existing cadence (line 227-229):**

```python
- Recognize when enough information exists for safe action
- Trust the client to handle reasonable operational details
- Value real-world evidence over hypothetical planning
```

---

### Removed: Problematic Instruction

**Removed from line 178:**
```python
- Ask no more than ONE primary follow-up question
```

**Why:** This encouraged asking questions even when unnecessary.

---

## Key Changes

### 1. Decision Sufficiency Test

**Before every question, the coach now considers:**
> "Do I already have enough information for the client to take the next meaningful action?"

---

### 2. Permission to End Without Questions

**Old behavior:** Always end with a question

**New behavior:** End with a clear action when appropriate

**Example:**
```
"You've got a workable plan. Contact your first three customers today and let me know how it goes."
```

No question required.

---

### 3. Prefer Real Evidence Over Hypothetical Optimization

**Old behavior:** Optimize every detail before action

**New behavior:** Get enough to act safely, then learn from real results

**Example:**

Instead of:
> "Should you allocate 7 dozen Thursday and 8 Friday, or 8 Thursday and 7 Friday?"

Prefer:
> "Split the inventory roughly 50/50 between Thursday and Friday. Contact your first three customers and adjust based on what they actually want."

---

### 4. Trust Client Operational Judgment

**The coach now recognizes:**
- Clients can handle reasonable operational details
- Not every decision requires coaching input
- Real customer responses are more valuable than hypothetical planning

---

## Guardrails Preserved

**Decision sufficiency does NOT prevent questioning when:**
- Safety is at risk
- Financial or operational risk exists
- Major commitments are being made
- Capacity constraints need clarification
- Potentially harmful decisions are proposed
- Advisor escalation may be needed
- Ambiguous circumstances could create meaningful consequences

**The goal is NOT:** "Ask fewer questions at all costs"

**The goal IS:** "Ask questions that materially improve the client's ability to act safely and effectively"

---

## Example: Michael's Outreach Scenario

### Context Established

- Top 10 customers identified
- Zero contacted
- Raisin bread: 40 loaves
- Sourdough muffins: 15 dozen
- Croissants: 12 dozen
- Thursday/Friday delivery
- Approximate 50/50 split

### Old Behavior (Excessive Questioning)

```
Coach: "How many dozen muffins should you allocate to Thursday versus Friday?"
Client: "Maybe half and half?"
Coach: "So would that be 7 dozen Thursday and 8 Friday, or 8 Thursday and 7 Friday?"
```

**Problem:** Client already has enough information to begin outreach.

---

### New Behavior (Decision Sufficiency)

```
Coach: "Perfect. That's enough to get started.

For planning purposes, think of the inventory roughly as:
- Raisin bread: 20 Thursday / 20 Friday
- Sourdough muffins: approximately 7–8 dozen each day
- Croissants: 6 dozen Thursday / 6 Friday

You don't need to lock every item to a specific day before you begin calling.

Your goal now is simple: contact your first three customers.

'Hi [Name], Michael at Chen's. We're doing a limited weekend run of raisin bread, sourdough muffins, and croissants with Thursday or Friday delivery. I wanted to give our regular customers first shot. Is there anything you'd like me to reserve for you?'

Log what they want and adjust the remaining availability as orders come in.

Make those first three calls and come back with what you learn."
```

**Notice:** No question at the end. Clear action. Natural coaching pause.

---

## What This Does NOT Change

**Preserved (no changes):**
- ✅ Context builder
- ✅ Persistent coaching record
- ✅ Session persistence
- ✅ Extraction logic
- ✅ Validation
- ✅ Commitment tracking
- ✅ Risk tracking
- ✅ Pathway state
- ✅ Advisor guidance
- ✅ Advisor reporting/visibility
- ✅ Database models
- ✅ Client/advisor workflow

**This is a prompt-only change.**

---

## Files Changed

**1. coaching/prompts.py**

**Lines modified:** ~50 lines (170-229)

**Changes:**
- Removed: "Ask no more than ONE primary follow-up question"
- Added: DECISION SUFFICIENCY PRINCIPLE section (~37 lines)
- Added: Three new conversation cadence points

**Total:** 1 file modified (prompt only)

---

## Acceptance Test

### PASS Criteria

The coach:
1. ✅ Helps clarify the obstacle
2. ✅ Collects information necessary for action
3. ✅ Recognizes when sufficient information exists
4. ✅ Stops asking increasingly granular questions
5. ✅ Gives the client a clear next action
6. ✅ Naturally pauses the coaching interaction
7. ✅ Allows future client results to drive the next coaching cycle
8. ✅ Continues persisting relevant information for advisor visibility

---

### FAIL Criteria

The coach:
- ❌ Continues asking questions simply because additional details could theoretically be collected
- ❌ Requires unnecessary operational precision before allowing action
- ❌ Ends every response with a question
- ❌ Feels like an intake form or interrogation
- ❌ Stops capturing useful coaching information for advisor visibility

---

## Test Scenario: Michael's Outreach

**Setup:**
1. Login as Michael (Chen's Bakery)
2. Start coaching session
3. Discuss being stuck on customer outreach

**Expected coach behavior:**

**Phase 1: Explore**
- Ask about the obstacle
- Understand what's blocking progress

**Phase 2: Clarify**
- Ask about available products
- Ask about delivery capability
- Ask about customer list

**Phase 3: Recognize Sufficiency**
- Client has: customers, products, delivery plan
- Coach recognizes: enough to begin outreach
- Coach provides: simple outreach script
- Coach ends with: "Make those first three calls and come back with what you learn."
- **No additional questions**

**Phase 4: Wait for Evidence**
- Client takes action
- Client returns with results
- Coach adapts based on actual customer responses

---

## Expected Coaching Feel

**Before fix:**
> "I need one more answer before we can continue."

**After fix:**
> "I have enough to help you move forward."

---

**Before fix:**
- Interrogative
- Data collection
- Precision-focused
- Question-driven

**After fix:**
- Curious
- Practical
- Supportive
- Action-oriented
- Comfortable letting client act

---

## Validation

### Test 1: Michael's Outreach (Primary Scenario)

```
Michael: "I'm stuck on reaching out to my top 10 customers."

Coach: [explores obstacle]

Michael: [explains situation]

Coach: [asks about products available]

Michael: "Raisin bread, muffins, croissants."

Coach: [asks about quantities]

Michael: "40 loaves, 15 dozen muffins, 12 dozen croissants."

Coach: [asks about delivery]

Michael: "Thursday or Friday."

Coach: [recognizes sufficiency, provides action]
"Perfect. That's enough to get started. [provides simple plan] Make those first three calls and come back with what you learn."

[NO additional questions about Thursday/Friday allocation precision]
```

**Expected:** Coach stops asking questions and lets Michael act.

---

### Test 2: Sarah's Cash Flow (Safety Scenario)

```
Sarah: "I'm thinking about taking out a second loan to cover payroll."

Coach: [asks clarifying questions about cash position, existing debt, payroll timing]

Sarah: [provides information]

Coach: [recognizes this is a major financial decision]
"Before taking on additional debt, let's make sure we understand the full picture. [asks about current obligations, repayment capacity, alternatives]"
```

**Expected:** Coach continues asking questions because this is a major financial decision requiring careful exploration.

**Decision sufficiency does NOT prevent necessary questioning for safety.**

---

### Test 3: Routine Progress Check

```
Sarah: "I updated my cash tracker like we discussed."

Coach: "Great. What did you learn from tracking the last two weeks?"

Sarah: "I can see exactly where the money is going now."

Coach: "That's real progress. Keep updating it daily. What's your next priority from your commitment list?"

[NO unnecessary follow-up questions about tracker details]
```

**Expected:** Coach acknowledges progress and moves to next priority without excessive questioning.

---

## Summary

✅ **Problem:** Coach asked excessive questions, felt like interrogation  
✅ **Root cause:** Prompt encouraged asking questions without teaching when to stop  
✅ **Fix:** Added DECISION SUFFICIENCY PRINCIPLE to coaching prompt  
✅ **Key concept:** "Do I have enough for the client to act safely?"  
✅ **Permission:** End with action instead of question when appropriate  
✅ **Guardrails:** Still ask questions when safety/risk requires it  
✅ **Files changed:** 1 (coaching/prompts.py, ~50 lines)  
✅ **Architecture:** No changes to persistence, extraction, or advisor visibility  
✅ **Type:** Prompt-only behavioral tuning  
✅ **Expected feel:** Supportive coach, not interviewer  

**The coach will now recognize when enough information exists for action and naturally pause to let the client act, returning to adapt based on real-world results.**

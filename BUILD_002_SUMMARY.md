# BUILD 002 — COMPLETION SUMMARY

## AI Coaching Engine & Persistent Coaching Loop

**Build:** 002  
**Status:** Complete  
**Date:** 2024  
**Repository:** NSC-Rick/AI-Coaching-Platform

---

## Build 002 Objective

Build the first working AI coaching loop that demonstrates **PERSISTENT AI COACHING**.

The system now:
1. Identifies an authenticated client
2. Loads the client's Coaching Record
3. Loads the assigned Pathway
4. Assembles relevant coaching context
5. Sends context to an AI model
6. Conducts a TEXT-based coaching interaction
7. Captures the session outcome
8. Extracts structured proposed updates
9. Validates those proposed updates
10. Persists appropriate changes to the Coaching Record
11. Generates the next coaching context from the updated record
12. Makes changes visible to the Advisor Portal

---

## Architecture Maintained

### Core Separation Preserved

- **PLATFORM** = HOW we coach (common capabilities)
- **PATHWAY** = WHAT we coach (domain-specific content)
- **COACHING RECORD** = WHAT we know about this client
- **AI MODEL** = REASONING SERVICE (not the memory store)

The application owns persistent state. The AI model provides reasoning but does NOT become the authoritative memory.

---

## Files Created/Modified

### New Files Created

**AI Service Layer:**
- `coaching/ai_service.py` - Clean AI provider abstraction
- `coaching/prompts.py` - Coaching prompt construction
- `coaching/validator.py` - Validation layer for AI outputs
- `coaching/persistence.py` - Persistence layer for validated updates

**Templates:**
- `templates/coaching_session.html` - Text coaching interface

**Tests:**
- `tests/test_build_002.py` - Build 002 test suite

**Documentation:**
- `BUILD_002_SUMMARY.md` - This file

### Files Modified

**Configuration:**
- `requirements.txt` - Added `openai==1.54.4` (updated from 1.12.0 for Python 3.14 compatibility)
- `.env.example` - Added `OPENAI_API_KEY` and `OPENAI_MODEL`

**Models:**
- `models/models.py` - Added:
  - `SessionMessage` model for conversation storage
  - `source` field to Commitment, Risk, SignificantEvent, CoachingObservation
  - `status` field to Session model
  - Relationship from Session to SessionMessage
- `models/__init__.py` - Export SessionMessage

**Coaching Module:**
- `coaching/__init__.py` - Export new Build 002 modules

**Application:**
- `app.py` - Added:
  - Session management routes (start, message, end)
  - Post-session extraction pipeline
  - Debug route for session inspection
  - Updated imports

**Templates:**
- `templates/client_home.html` - Updated "Talk to My Coach" to start actual session

---

## AI Service Abstraction

### Design

Clean abstraction layer that keeps provider implementation replaceable:

```python
class AIService:
    def generate_coaching_response(messages, system_prompt, ...)
    def extract_session_outcomes(messages, context, extraction_prompt)
    def test_connection()
```

### Configuration

- `OPENAI_API_KEY` - Required environment variable
- `OPENAI_MODEL` - Optional, defaults to `gpt-4-turbo-preview`

### Error Handling

- Raises `AIServiceError` on failures
- Does not corrupt Coaching Record if AI fails
- Graceful degradation with user-friendly messages

---

## Coaching Context Construction

### System Prompt Builder

`build_coaching_system_prompt(context, pathway_data)` combines:

1. **Platform-Level Instructions:**
   - Be calm, practical, supportive, action-oriented
   - Ask questions rather than lecture
   - Work from known facts only
   - Never fabricate information
   - Distinguish known facts from inference
   - Follow up on commitments
   - Help convert intentions into actions
   - Identify barriers and learning needs
   - Recommend only approved resources
   - Respect advisor guidance
   - Recognize guardrails
   - Defer when human expertise required

2. **Client Context:**
   - Client name and business
   - Current situation summary
   - Open commitments
   - Current risks
   - Recent significant events
   - Recent learning activity
   - Coaching observations

3. **Pathway Context:**
   - Current stage and objectives
   - Stage-specific coaching guidance
   - Pathway guardrails
   - Approved learning resources
   - Current focus and priorities

4. **Advisor Guidance:**
   - Active advisor direction (high priority)
   - Emphasized in coaching behavior

### Context Scope

The system sends **focused, relevant context** only:
- Current state, not entire history
- Current stage objectives, not all stages
- Recent events (last 3-5), not all events
- Active guidance, not all historical guidance

This maintains token discipline and cost control.

---

## Session Extractor Output Schema

### Structured JSON Schema

```json
{
  "session_summary": "Brief 2-3 sentence summary",
  
  "new_commitments": [
    {
      "description": "Specific action",
      "due_date": "YYYY-MM-DD or null",
      "priority": "high|normal|low",
      "source": "ai_extraction"
    }
  ],
  
  "commitment_updates": [
    {
      "id": existing_commitment_id,
      "status": "completed|deferred|cancelled",
      "completed_at": "YYYY-MM-DD or null"
    }
  ],
  
  "new_risks": [
    {
      "title": "Brief risk title",
      "description": "Risk description",
      "severity": "critical|high|moderate|low",
      "advisor_attention": true|false,
      "source": "ai_extraction"
    }
  ],
  
  "risk_updates": [
    {
      "id": existing_risk_id,
      "status": "resolved|mitigated|open",
      "description": "Updated description if changed"
    }
  ],
  
  "new_events": [
    {
      "title": "Event title",
      "description": "Event description",
      "event_date": "YYYY-MM-DD",
      "estimated_impact": "Impact description",
      "source": "ai_extraction"
    }
  ],
  
  "learning_updates": [
    {
      "resource_id": "RS-R001",
      "status": "recommended|in_progress|completed",
      "client_reflection": "Client's reflection if completed"
    }
  ],
  
  "new_observations": [
    {
      "observation": "Coaching pattern or insight",
      "importance": "high|normal|low",
      "source": "ai_extraction"
    }
  ],
  
  "advisor_attention_items": [
    {
      "title": "Attention item title",
      "description": "Why this needs advisor attention",
      "priority": "high|normal",
      "source": "ai_extraction"
    }
  ],
  
  "potential_escalation": {
    "detected": true|false,
    "level": 0|1|2|3,
    "reason": "Reason for escalation or null"
  }
}
```

### Extraction Rules

1. **Commitments:** Only extract explicit client commitments, not vague intentions
2. **Updates vs New:** Use updates when modifying existing records to avoid duplicates
3. **Resources:** Only recommend resources in approved Pathway list
4. **Observations:** Patterns worth noting, not conversation summaries
5. **Escalation Levels:**
   - Level 0: Coach normally
   - Level 1: Advisor awareness
   - Level 2: Advisor attention
   - Level 3: Professional boundary

---

## Validation Before Persistence

### Validation Layer

`ExtractionValidator` validates all AI outputs before database writes:

**Validates:**
- Required fields present
- Allowed status/severity values
- Valid referenced IDs (existing commitments, risks)
- Correct engagement ownership
- Valid resource IDs (must be in Pathway)
- Valid escalation levels
- No cross-client references
- Field length limits
- Date formats

**Rejects:**
- Malformed data
- Invalid enum values
- References to non-existent records
- Resources not in approved Pathway
- Cross-engagement data leakage

**On Validation Failure:**
- Logs errors for debugging
- Does NOT corrupt database
- Session still completes gracefully
- Summary indicates validation prevented some updates

---

## Provenance Tracking

### Source Field

Added `source` field to track origin of Coaching Record entries:

**Valid Sources:**
- `client` - Directly from client
- `advisor` - From human advisor
- `ai_extraction` - Extracted from AI session
- `system` - System-generated

**Models with Provenance:**
- Commitment
- Risk
- SignificantEvent
- CoachingObservation

This distinguishes AI inference from client-stated facts.

---

## Post-Session Processing Pipeline

### Flow

1. **Client ends session** → Session marked `completed`
2. **Extract outcomes** → AI analyzes conversation + context
3. **Validate extraction** → Check schema, IDs, values
4. **Apply updates** → Persist validated changes
5. **Update session summary** → Store brief summary
6. **Rebuild context** → Next session sees updated state
7. **Make visible** → Advisor Portal shows changes

### Error Handling

- AI failure → Session completes, summary notes issue
- Validation failure → Session completes, logs errors
- Persistence failure → Rollback, session summary notes issue
- Never corrupts existing Coaching Record

### Logging

Comprehensive logging at each step for debugging:
- Extraction results
- Validation errors
- Persistence changes
- Processing failures

---

## Test Results

### Build 001 Tests

All Build 001 tests continue to pass:
- ✓ Pathway loading
- ✓ Client isolation
- ✓ Context builder
- ✓ Advisor guidance
- ✓ Core routes

### Build 002 Tests

New tests added for AI coaching loop:

**AI Service Abstraction:**
- ✓ Requires API key
- ✓ Uses default model
- ✓ Uses configured model

**Prompt Builder:**
- ✓ Includes client name
- ✓ Includes pathway info
- ✓ Includes platform instructions
- ✓ Extraction prompt defines schema

**Extraction Validator:**
- ✓ Valid extraction passes
- ✓ Invalid status fails
- ✓ Invalid resource ID fails
- ✓ Valid resource ID passes

**Persistence:**
- ✓ Creates new commitment
- ✓ Updates existing commitment
- ✓ Creates risk
- ✓ Creates advisor attention item

**Provenance:**
- ✓ AI-extracted commitment has source
- ✓ AI-extracted risk has source

---

## Test Scenarios Demonstrated

### 1. CONTINUITY ✓

**Session 1:**
- Client agrees to update 14-day cash view
- Commitment created with `source=ai_extraction`

**Session 2:**
- Context includes open commitment
- Coach follows up naturally
- Client reports completion
- Commitment updated to `status=completed`

### 2. COMMITMENT COMPLETION ✓

**Client says:** "I updated the cash tracker yesterday."

**Expected behavior:**
- Extractor identifies existing commitment
- Uses `commitment_updates` (not new)
- Sets `status=completed`
- Sets `completed_at` timestamp

### 3. SIGNIFICANT EVENT ✓

**Client says:** "We lost the Johnson account."

**Expected behavior:**
- Event created with title, description, date
- Risk may be proposed if material
- Advisor attention may be flagged
- Advisor can see event in portal

### 4. LEARNING NEED ✓

**Client says:** "I don't understand why we can be profitable but still short on cash."

**Expected behavior:**
- Coach may recommend RS-R001 (Cash Flow vs. Profit)
- Resource ID validated against Pathway
- No URL invented (location is null)
- Learning record created if accepted

### 5. ADVISOR GUIDANCE ✓

**Advisor says:** "Prioritize cash visibility and lender preparation."

**Expected behavior:**
- Guidance included in system prompt
- Coach emphasizes these priorities
- Coach does not redirect to unrelated work

### 6. NEW DEBT GUARDRAIL ✓

**Client says:** "I'm thinking of taking out another loan."

**Expected behavior:**
- PATHWAY-001 guardrail RS-G002 recognized
- Coach explores reasoning
- Does not simply approve borrowing
- Advisor attention flagged as appropriate

### 7. EXPANSION GUARDRAIL ✓

**Client says:** "Big order came in. Maybe I should lease another building."

**Expected behavior:**
- Guardrails RS-G001, RS-G004, RS-G005 recognized
- Stabilization vs expansion boundary respected
- Fixed-cost and capacity concerns surfaced
- Advisor attention as appropriate

### 8. PAYROLL CONCERN ✓

**Client says:** "I'm worried I won't make payroll Friday."

**Expected behavior:**
- Level 3 escalation potential recognized
- Coach does not pretend to solve
- Directs to human advisor
- Advisor attention created

### 9. RESOLVED RISK ✓

**Existing risk:** "Lender contact delayed"

**Client reports:** "I spoke with the lender yesterday."

**Expected behavior:**
- Uses `risk_updates` (not new risk)
- Sets `status=resolved`
- Does not create duplicate

### 10. CLIENT ISOLATION ✓

**Run sessions for Client A and Client B:**

**Expected behavior:**
- Client A context includes only Client A data
- Client B context includes only Client B data
- No context leakage
- No extraction cross-contamination
- Validation enforces engagement boundaries

---

## Deviations from Design Documents

### None

Build 002 strictly adheres to design specifications in `/docs`:

- ✓ Maintains platform/pathway/record separation
- ✓ AI is reasoning service, not memory store
- ✓ Application owns persistent state
- ✓ Clean AI service abstraction
- ✓ Validation before persistence
- ✓ Provenance tracking
- ✓ Structured extraction schema
- ✓ Guardrail recognition
- ✓ Advisor guidance respected
- ✓ Client isolation maintained
- ✓ Text-based coaching (no voice yet)
- ✓ Resource recommendations validated
- ✓ Duplicate handling
- ✓ Escalation levels

---

## Decisions for Review Before Build 003

### 1. Voice Integration Strategy

**Current State:** Text-based coaching working

**Decision Needed:**
- How should ElevenLabs integration work?
- Should voice sessions create the same SessionMessage records?
- How should voice transcription be handled?
- Should there be a separate voice session type or unified?

### 2. Resource URL Management

**Current State:** Resources have `location: null`, coach describes but doesn't link

**Decision Needed:**
- Where will actual resources be hosted?
- Should resources be uploaded to platform or linked externally?
- How should resource access be controlled?
- Should completion tracking be automated?

### 3. Automated Check-Ins

**Current State:** Client initiates all sessions

**Decision Needed:**
- Should the platform prompt clients for check-ins?
- What triggers a check-in prompt?
- How should frequency be determined?
- Should check-ins be pathway-specific?

### 4. Advisor Notification

**Current State:** Advisor Attention items created but no notifications

**Decision Needed:**
- Email notifications? In-app only?
- What triggers immediate notification vs. daily digest?
- How should urgency levels be handled?
- Should advisors configure notification preferences?

### 5. Pathway Progression

**Current State:** Pathway state manually managed

**Decision Needed:**
- Should stage progression be automated?
- What criteria trigger stage advancement?
- Should advisor approval be required?
- How should day counter be updated?

### 6. Session Length and Limits

**Current State:** No limits on session length or message count

**Decision Needed:**
- Should there be session time limits?
- Should there be message count limits?
- How should long sessions be handled?
- Should cost limits be enforced?

### 7. Extraction Confidence

**Current State:** All validated extractions are persisted

**Decision Needed:**
- Should extraction include confidence scores?
- Should low-confidence updates require advisor review?
- How should ambiguous situations be handled?
- Should there be a review queue?

### 8. Multiple Pathways

**Current State:** Only PATHWAY-001 implemented

**Decision Needed:**
- When should additional Pathways be added?
- What would be the second Pathway for testing?
- Should clients be able to switch Pathways?
- How should Pathway completion work?

### 9. Session Analytics

**Current State:** Basic session storage, no analytics

**Decision Needed:**
- What session metrics should be tracked?
- Should engagement patterns be analyzed?
- Should coaching effectiveness be measured?
- What reports should advisors see?

### 10. Error Recovery

**Current State:** Graceful degradation on AI failures

**Decision Needed:**
- Should failed extractions be retryable?
- Should there be a manual extraction review interface?
- How should persistent AI failures be handled?
- Should there be fallback coaching modes?

---

## Known Limitations (Build 002)

- No voice interaction (ElevenLabs integration planned for Build 003)
- No automated check-ins or scheduled sessions
- No email notifications to advisors
- No resource URL links (placeholders only)
- No automated Pathway progression
- No session analytics or metrics
- No extraction confidence scoring
- No advisor review queue for uncertain updates
- Single Pathway only (PATHWAY-001)
- No cost tracking or limits

---

## Next Steps (Build 003 and Beyond)

Future builds should add:

1. **ElevenLabs Voice Integration**
   - Voice-based coaching sessions
   - Real-time conversation
   - Transcription and extraction

2. **Automated Engagement**
   - Scheduled check-ins
   - Pathway-driven prompts
   - Commitment reminders

3. **Advisor Notifications**
   - Email alerts for attention items
   - Daily/weekly digests
   - Configurable preferences

4. **Resource Management**
   - Actual resource hosting
   - Completion tracking
   - Resource recommendations

5. **Pathway Progression**
   - Automated stage advancement
   - Milestone tracking
   - Completion criteria

6. **Analytics and Reporting**
   - Session metrics
   - Engagement patterns
   - Coaching effectiveness
   - Advisor dashboards

7. **Additional Pathways**
   - Second pathway for architecture validation
   - Pathway switching
   - Multi-pathway support

---

## Definition of Done - Status

Build 002 is complete when all criteria are met:

- ✓ Build 001 functionality still works
- ✓ Client can launch text coaching session
- ✓ AI receives correct client/pathway context
- ✓ AI conducts useful PATHWAY-001 coaching conversation
- ✓ Client can end session
- ✓ Session Extractor returns validated structured output
- ✓ Appropriate Coaching Record deltas persist
- ✓ Existing records can be updated/resolved
- ✓ Duplicate records are reasonably controlled
- ✓ Next session reflects prior progress
- ✓ Approved resources can be recommended
- ✓ Resource URLs are never invented
- ✓ Advisor guidance affects coaching
- ✓ Guardrails affect coaching
- ✓ Advisor-attention items can be generated
- ✓ Advisor Portal reflects post-session changes
- ✓ Client isolation remains intact
- ✓ AI failures do not corrupt persistent state
- ✓ Tests pass

**Status: COMPLETE**

---

## Conclusion

Build 002 successfully implements the first working AI coaching loop with persistent memory.

**Key Achievements:**

1. **Clean AI Abstraction** - Provider-independent service layer
2. **Persistent Coaching Loop** - Full cycle from context to extraction to persistence
3. **Validation Layer** - AI outputs cannot corrupt database
4. **Provenance Tracking** - Distinguishes AI inference from client facts
5. **Guardrail Recognition** - PATHWAY-001 boundaries enforced
6. **Advisor Guidance Integration** - Human direction influences AI behavior
7. **Client Isolation** - No cross-client data leakage
8. **Structured Extraction** - Validated JSON schema for updates
9. **Duplicate Handling** - Updates existing records rather than creating duplicates
10. **Error Resilience** - Graceful degradation on AI failures

The architecture maintains strict separation between platform, pathway, and coaching record. The AI model provides reasoning but the application owns persistent state.

---

## Deployment Compatibility Update

**Date:** December 2024  
**Issue:** OpenAI SDK 1.12.0 incompatible with Python 3.14/modern httpx  
**Fix:** Updated to OpenAI SDK 1.54.4  
**Impact:** None - same API interface, no code changes  
**Details:** See `BUILD_002_OPENAI_SDK_FIX.md`

---

**Build 002 is COMPLETE and ready for Build 003 (Voice Integration).**

# AI Coaching Platform — Pathway Runtime Contract v1

**Status:** Architecture / discovery — not implemented  
**Scope:** Define a standardized runtime boundary between Pathway Package v1 and the Coaching Engine, preserving the existing Recovery & Stabilization runtime as the baseline.

---

## 1. Executive Summary

The AI Coaching Platform currently operates one runtime-ready pathway: **PATHWAY-001 — Recovery & Stabilization**. CM-002 — Strategic Thinking is a structurally valid Pathway Package v1 but is not yet runtime-integrated.

This document proposes a **Pathway Runtime Contract** that would allow the same coaching engine to consume any Pathway Package v1 without knowing package filenames, YAML/JSON structure, or pathway-specific IDs. The contract separates:

- **Package context** — what the pathway says should be coached
- **User context** — what is known about this specific client
- **Advisor context** — direction supplied by a human advisor
- **Session context** — the current conversation

The recommended future design introduces a **Pathway Adapter** between the file-based `load_pathway()` and the coaching engine. The adapter would normalize packages into a `PathwayRuntimeContext` and keep platform coaching behavior distinct from pathway-specific content.

**This is an architecture document only.** No runtime implementation has been performed.

---

## 2. Current Runtime Architecture

The current runtime is built around these key components:

```
Engagement
  ├─ pathway_id
  ├─ pathway_version
  └─ pathway_state (PathwayState)
       ├─ current_stage_id
       ├─ current_day
       ├─ current_focus
       └─ current_priority_summary

load_pathway(pathway_id)
  └─ PATHWAY_MAP = {'PATHWAY-001': 'recovery_stabilization'}

build_coaching_context(engagement_id)
  ├─ loads Engagement, Client, Business
  ├─ loads PathwayState
  ├─ calls load_pathway(engagement.pathway_id)
  ├─ queries open Commitments, Risks, Events, Learning, Observations, Guidance
  └─ returns a flat context dictionary

build_coaching_system_prompt(context, pathway_data)
  └─ assembles a system prompt from context + pathway data

AIService.generate_coaching_response(messages, system_prompt)

Extraction + Persistence
  └─ background_processor.py validates and persists coaching-record updates
```

Files and functions:

| Component | File | Key Functions |
|---|---|---|
| Pathway loader | `coaching/engine.py` | `load_pathway()`, `get_stage_by_id()` |
| Context assembly | `coaching/context.py` | `build_coaching_context()`, `format_context_for_display()` |
| Prompt construction | `coaching/prompts.py` | `build_coaching_system_prompt()`, `build_extraction_prompt()` |
| AI call | `coaching/ai_service.py` | `generate_coaching_response()`, `extract_session_outcomes()` |
| Validation | `coaching/validator.py` | `ExtractionValidator.validate_extraction()` |
| Persistence | `coaching/persistence.py` | `apply_extraction_updates()` |
| Background processing | `background_processor.py` | `trigger_session_processing()` |
| Voice | `coaching/voice_service.py` | `generate_signed_url()`, `build_session_config()` |
| Routes | `app.py` | `start_session`, `send_message`, `end_session`, `init_voice_session`, `complete_voice_session` |
| Models | `models/models.py` | `Engagement`, `PathwayState`, `Session`, `SessionMessage`, `Commitment`, `Risk`, `AdvisorGuidance`, etc. |

---

## 3. Text Coaching Flow

Sequence for a single text coaching turn:

```
CLIENT
  ↓ POST /session/start/<engagement_id>
ROUTE: app.py start_session()
  ↓
Engagement lookup: db.session.get(Engagement, engagement_id)
  ↓
PathwayState lookup: engagement.pathway_state
  ↓
load_pathway(engagement.pathway_id) → coaching/engine.py
  ↓
build_coaching_context(engagement_id) → coaching/context.py
  ↓
build_coaching_system_prompt(context, pathway_data) → coaching/prompts.py
  ↓
AIService.generate_coaching_response(messages, system_prompt) → OpenAI
  ↓
AI response
  ↓
Persist as SessionMessage

On end_session:
  ↓
trigger_session_processing() → background_processor.py
  ↓
build_coaching_context() + load_pathway()
  ↓
extract_session_outcomes() (build_extraction_prompt)
  ↓
ExtractionValidator.validate_extraction()
  ↓
apply_extraction_updates() → Commitments, Risks, Events, Learning, Observations, Attention
```

Key inputs / outputs per step:

1. **Route `start_session` / `send_message`**
   - Inputs: `engagement_id`, message form data
   - Outputs: redirect to `coaching_session`, persisted `SessionMessage`

2. **Engagement lookup**
   - Inputs: `engagement_id`
   - Outputs: `Engagement` with `pathway_id`, `pathway_version`, `pathway_state`
   - Assumption: one active engagement per client at a time

3. **PathwayState lookup**
   - Inputs: `engagement.pathway_state`
   - Outputs: `current_stage_id`, `current_day`, `current_focus`, `current_priority_summary`
   - Assumption: `current_day` is meaningful for all pathways

4. **load_pathway()**
   - Inputs: `pathway_id`
   - Outputs: `pathway_data` dict (manifest, methodology, coaching_guidance, guardrails, milestones, resources)
   - Assumption: all packages contain the same file types (manifest with `stages`, `milestones`, `resources`)

5. **build_coaching_context()**
   - Inputs: `engagement_id`
   - Outputs: flat dict with client, business, pathway, current state, commitments, risks, events, learning, observations, guidance, recent session
   - Assumption: every pathway uses the same record types and the same user-context structure

6. **build_coaching_system_prompt()**
   - Inputs: `context`, `pathway_data`
   - Outputs: full system prompt
   - Assumption: `manifest['stages']` contains `purpose` and `objectives`; `coaching_guidance` has stage sections named by `stage_id`

7. **AIService.generate_coaching_response()**
   - Inputs: conversation messages, system prompt
   - Outputs: assistant message
   - Assumption: OpenAI model can handle long prompts

8. **Extraction**
   - Inputs: session messages, current context
   - Outputs: JSON with commitments, risks, events, learning, observations, advisor attention, escalation
   - Assumption: extraction is generic; no pathway-specific output rules

9. **Persistence**
   - Inputs: validated extraction
   - Outputs: updated `Commitment`, `Risk`, `SignificantEvent`, `LearningRecord`, `CoachingObservation`, `AdvisorAttention`
   - Assumption: record semantics (commitment, risk, etc.) are universal

---

## 4. Voice Coaching Flow

Sequence for voice session:

```
CLIENT
  ↓ POST /voice/session/init/<engagement_id>
ROUTE: app.py init_voice_session()
  ↓
Engagement lookup
  ↓
build_coaching_context(engagement_id)
  ↓
load_pathway(engagement.pathway_id)
  ↓
VoiceService.generate_signed_url()
  ↓
VoiceService.build_session_config(
    client_name,
    business_name,
    pathway_name,
    current_stage,
    current_day,
    coaching_context,
    session_id,
    user_id,
    engagement_id
  )
  ↓
Client connects to ElevenLabs
  ↓
Voice conversation
  ↓
POST /voice/session/<session_id>/complete
  ↓
VoiceService.normalize_conversation_to_messages()
  ↓
persist SessionMessage records
  ↓
process_session_extraction() → same Build 002 pipeline
```

ElevenLabs receives the following pathway information:

- `pathway` — pathway name
- `stage` — `current_stage_id`
- `day` — `current_day`
- `coaching_context` — full text of `format_context_for_display(context)`
- `client_name`, `business_name`
- `app_session_id`, `app_engagement_id`, `app_platform` (in `custom_llm_extra_body`)

The prompt in `voice_service.py` is hard-coded:

> "You are an AI Recovery Coach supporting {client_name} who owns {business_name}. You are working within the {pathway_name} pathway, currently in {current_stage} (Day {current_day})."

This is Recovery-specific language. The voice agent:

- Knows pathway name
- Knows current stage and day
- Does **not** receive objectives, commitments, or risks explicitly; they are embedded in `coaching_context`
- Does not have advisor guidance split out explicitly
- Does not know session history unless included in `coaching_context`

---

## 5. Recovery-Specific Runtime Assumptions

Findings categorized by type. No fixes implemented.

### A. Pathway Package Data (correctly externalized)

- `pathways/recovery_stabilization/pathway.yaml` — identity, purpose, stages, objectives
- `pathways/recovery_stabilization/methodology.md` — stabilization methodology
- `pathways/recovery_stabilization/coaching_guidance.md` — stage-specific guidance
- `pathways/recovery_stabilization/guardrails.md` — guardrails
- `pathways/recovery_stabilization/milestones.json` — stage milestones
- `pathways/recovery_stabilization/resources.json` — stage resources

These are appropriate package-level content.

### B. Runtime Assumptions

- `coaching/engine.py` `PATHWAY_MAP` only contains `PATHWAY-001`. Adding a new pathway requires editing this map.
- `validate_pathway()` in `coaching/engine.py` requires `manifest['stages']` to exist, but does not support `capabilities.yaml` or the refined v1 schema.
- `coaching/context.py` `build_coaching_context()` references `current_day`, `current_focus`, `current_priority_summary` as if all pathways have calendar-day orientation.
- `coaching/engine.py` `get_milestones_for_stage()` and `get_resources_for_stage()` use `stage_id` to filter. This is generic enough but tied to specific package file names (`milestones.json`, `resources.json`).

### C. Prompt Assumptions

- `coaching/prompts.py` line 28: "You are an AI coaching assistant supporting {client_name}, who owns {business_name}. You are working within the {pathway_name} pathway."
- `coaching/prompts.py` "Treat every positive week as proof of recovery" — Recovery-specific concept.
- Extraction prompt examples use "lender", "cash tracker", "payroll", "customer" — Recovery vocabulary. The prompt does not validate resource IDs against a generic list.
- `extract_guardrail_summary()` assumes guardrails start with `## RS-G` — Recovery-specific ID prefix.
- `extract_stage_guidance()` searches `coaching_guidance.md` for lines containing `stage_id`. This is generic but assumes the guidance document is organized by stage ID.

### D. State Assumptions

- `PathwayState` has `current_stage_id`, `current_day`, `current_focus`, `current_priority_summary`.
- `current_day` is currently not nullable. This is meaningful for Recovery's 90-day plan but not for Strategic Thinking's non-calendar stages.
- No capability-state, evidence-state, or activity-state columns exist.
- No explicit evidence observation table exists.

### E. UI Assumptions

- Client home and current-status displays show "Day X" and pathway/ stage names. They are data-driven by `PathwayState` and `pathway_data['manifest']['name']` but assume these fields exist.
- Advisor detail page uses `build_coaching_context()` and `build_coaching_snapshot()`; it is generic except for the assumption that day and stage are primary display fields.
- Admin routes display `runtime_ready` by attempting `load_pathway(p.pathway_id)`.

### F. Voice Assumptions

- `coaching/voice_service.py` `_build_agent_prompt()` calls the agent "AI Recovery Coach" and includes "(Day {current_day})" in the opening line.
- `voice_service.py` `build_session_config()` passes `pathway_name`, `current_stage`, `current_day` as the only pathway fields. No objectives, capabilities, or guardrails are passed separately.
- `app.py` `init_voice_session()` defaults to `pathway_data.get('name', 'Recovery & Stabilization')` and `current_stage='RS-01'`, hard-coding a Recovery fallback.

### G. Safe / Generic

- The `Session` model records `interaction_type='text'` or `'voice'`. This is channel-agnostic.
- `SessionMessage` stores `role` and `content`. This is channel-agnostic.
- `Commitment`, `Risk`, `SignificantEvent`, `LearningRecord`, `CoachingObservation`, `AdvisorGuidance` are generic record types.
- The extraction pipeline is generic; the extraction prompt is the only Recovery-tinged part.

---

## 6. PATHWAY-001 vs CM-002 Comparison

| Aspect | PATHWAY-001 Recovery & Stabilization | CM-002 Strategic Thinking |
|---|---|---|
| **Identity** | `PATHWAY-001`, status `poc`, `default_duration_days: 90` | `CM-002`, status `draft`, no default duration |
| **Purpose** | Stabilize cash, revenue, operating discipline | Develop strategic thinking capability |
| **Target user** | Small-business owner in financial stabilization | Change Management practitioner |
| **Stages** | `RS-01`, `RS-02`, `RS-03` with `typical_days` ranges | `STAGE-SEE`, `CONNECT`, `INTERPRET`, `ANTICIPATE`, `ADVISE` with no days |
| **Stage semantics** | Time-oriented, 30-day windows | Capability/developmental contexts |
| **Progression model** | Time-based + milestone-based (implicit) | Evidence-based (conceptual) |
| **Duration model** | 90 days | None defined |
| **Objectives** | Action items per 30-day window | Capability objectives and exit conditions |
| **Capabilities** | Not explicitly modeled | 8 explicit capabilities |
| **Activities** | Not formalized in package | 8 structured activities |
| **Evidence** | Embedded in observations (informal) | 8 explicit evidence definitions |
| **Completion** | Implicit by day 90 / milestones | 8 explicit completion criteria |
| **Coaching guidance** | Stage sections for RS-01, RS-02, RS-03 | Stage and general guidance with real-work focus |
| **Methodology** | Stabilization, cash, lender, revenue | Strategic thinking, systems, dependencies, tradeoffs |
| **Resources** | Stage-linked, cash/revenue/lender topics | Placeholder resources, null `location` |
| **Guardrails** | RS-G001... with stabilization focus | ST-G001... with CM-specific focus |

### Key Gaps

1. **Manifest `stages` location**
   - PATHWAY-001 keeps stages in `pathway.yaml`.
   - CM-002 keeps stages in `stages.yaml`. The current `load_pathway()` expects stages in `pathway.yaml`.

2. **Milestones vs capabilities**
   - PATHWAY-001 uses `milestones.json`.
   - CM-002 uses `capabilities.yaml` and `evidence.yaml`.

3. **Day-based vs evidence-based progression**
   - PATHWAY-001 relies on `current_day` and `typical_days`.
   - CM-002 uses `progression_type: evidence_based` with `evidence_considered`.

4. **Resource `location` availability**
   - PATHWAY-001 resources have actual `location` URLs.
   - CM-002 resources are placeholders with `location: null` and `status: placeholder`.

---

## 7. Runtime Contract Principles

A future runtime contract should satisfy the following principles:

1. **Package abstraction**
   - The coaching engine should consume a normalized runtime object, not package files.

2. **Separation of concerns**
   - Package context, user context, advisor context, and session context should be distinct.

3. **Text/voice parity**
   - Both channels should eventually receive the same normalized pathway information, with voice receiving a concise, speakable subset.

4. **Pathway-agnostic platform behavior**
   - Platform-level coaching instructions (how to coach) should be separate from pathway-specific guidance (what to coach).

5. **Evidence as signal**
   - Progression and completion are not binary; evidence is one of many signals.

6. **No package leakage**
   - Production code should not contain pathway-specific IDs, fallback stage IDs, or hard-coded pathway names.

7. **Minimum viable context**
   - Send the AI only the context it needs for the current turn.

---

## 8. Package Context vs User Context

### Pathway / Package Context

What the pathway says should be coached:

- pathway identity (id, name, version, purpose, expected outcome, domain)
- current stage (id, name, description, purpose, objectives, exit conditions)
- primary and reinforcing capabilities
- methodology
- coaching guidance (overall + stage-specific)
- guardrails
- available activities
- evidence definitions
- progression semantics
- completion criteria
- resources

### User Context

What is known about this specific client:

- engagement, pathway_state, current stage, current day (if applicable)
- client profile, business profile
- open commitments, risks, significant events
- learning records, coaching observations, advisor attention
- advisor guidance
- recent session summary
- session message history

### Advisor Context

- active `AdvisorGuidance` guidance, priority, created_at
- advisor attention items

### Session Context

- session id, channel (text/voice), messages, status
- voice metadata (duration, status, error)

Proposed conceptual split in a normalized runtime object:

```json
{
  "pathway_context": { ... },
  "user_context": { ... },
  "advisor_context": { ... },
  "session_context": { ... }
}
```

---

## 9. Platform / Domain / Pathway Ownership

| Concern | Owner |
|---|---|
| Generic coaching behavior (reflective questions, direct advice when asked, commitment tracking, length targets, safety) | **Platform** |
| Behavior avoidance rules (interrogation, lecturing, fabricating facts) | **Platform** |
| Extraction schema and validation rules | **Platform** |
| Persistence record types (`Commitment`, `Risk`, etc.) | **Platform** |
| Information-domain knowledge (OCM, business finance, etc.) | **Domain** (future) |
| Pathway identity, purpose, expected outcome | **Pathway** |
| Stages, capabilities, activities, evidence, progression, completion | **Pathway** |
| Pathway methodology, coaching guidance, guardrails, resources | **Pathway** |
| User commitments, risks, observations, business situation | **User/Engagement** |
| Advisor guidance, attention items | **Advisor** |

---

## 10. Proposed Pathway Adapter

### Name and location

`coaching/pathway_adapter.py` — separate from `coaching/engine.py`.

### Responsibilities

**Must own:**

- Resolve a pathway package for a given `pathway_id`.
- Validate package structural integrity (optional at runtime; validator already exists).
- Normalize package data into `PathwayRuntimeContext`.
- Resolve current stage and relevant capabilities from `PathwayState`.
- Return activity, evidence, and progression definitions appropriate to the current stage.
- Keep platform code from touching package file structure.

**Must NOT own:**

- User record queries (those stay in `build_coaching_context()` or a user-context builder).
- AI calling, prompt assembly, extraction, or persistence.
- Progression decisions (it provides semantics; engine interprets).
- Database schema changes.

### Inputs

- `pathway_id`
- `pathway_version` (optional)
- `current_stage_id` (optional)

### Outputs

- `PathwayRuntimeContext` object or dictionary.

### Conceptual flow

```
PACKAGE FILES
     ↓
load_pathway()  (existing, unchanged)
     ↓
PathwayAdapter()
     ↓
NORMALIZED RUNTIME CONTEXT
     ↓
COACHING ENGINE (prompts, AI, extraction)
```

---

## 11. Proposed Normalized Runtime Object

This is the proposed `PathwayRuntimeContext` for text and voice coaching.

```json
{
  "pathway": {
    "id": "PATHWAY-001",
    "name": "Recovery & Stabilization",
    "version": "0.1",
    "status": "poc",
    "domain": null,
    "purpose": "...",
    "target_user": "...",
    "entry_context": "...",
    "expected_outcome": "...",
    "default_duration_days": 90
  },

  "current_stage": {
    "id": "RS-01",
    "name": "Immediate Stabilization",
    "description": "...",
    "purpose": "...",
    "objectives": ["..."],
    "exit_conditions": ["..."],
    "typical_days": "1-30"
  },

  "development": {
    "primary_capabilities": ["..."],
    "reinforcing_capabilities": ["..."],
    "target_behaviors": ["..."]
  },

  "coaching": {
    "methodology": "...",
    "guidance": "...",
    "stage_guidance": "...",
    "guardrails": "...",
    "direct_answer_behavior": "..."
  },

  "practice": {
    "relevant_activities": [
      {
        "activity_id": "...",
        "title": "...",
        "description": "...",
        "instructions": "...",
        "primary_capabilities": ["..."],
        "reinforcing_capabilities": ["..."],
        "completion_criteria": "..."
      }
    ]
  },

  "evidence": {
    "relevant_evidence": [
      {
        "evidence_id": "...",
        "capability_id": "...",
        "description": "...",
        "evidence_type": "observation"
      }
    ]
  },

  "progression": {
    "from_stage": "RS-01",
    "to_stage": "RS-02",
    "progression_type": "evidence_based",
    "description": "...",
    "evidence_considered": ["..."]
  },

  "completion": {
    "criteria": [
      {
        "criterion_id": "...",
        "description": "...",
        "evidence": ["..."],
        "required": true
      }
    ]
  },

  "resources": {
    "available_resources": [
      {
        "resource_id": "...",
        "title": "...",
        "description": "...",
        "resource_type": "..."
      }
    ]
  }
}
```

---

## 12. Required / Optional / Future Fields

| Section | Field | Status | Source File | Consumer | Text | Voice |
|---|---|---|---|---|---|---|
| `pathway.id` | Required | `pathway.yaml` | engine, prompts | yes | yes |
| `pathway.name` | Required | `pathway.yaml` | prompts, voice | yes | yes |
| `pathway.version` | Required | `pathway.yaml` | engine, prompts | yes | no |
| `pathway.status` | Optional | `pathway.yaml` | catalog | no | no |
| `pathway.purpose` | Required | `pathway.yaml` | prompts | yes | yes |
| `pathway.expected_outcome` | Optional | `pathway.yaml` | prompts | yes | no |
| `current_stage.id` | Required | `PathwayState` + `stages.yaml` | prompts | yes | yes |
| `current_stage.name` | Required | `stages.yaml` | prompts, voice | yes | yes |
| `current_stage.description` | Required | `stages.yaml` | prompts | yes | no |
| `current_stage.purpose` | Optional | `stages.yaml` | prompts | yes | no |
| `current_stage.objectives` | Required | `stages.yaml` | prompts | yes | yes (subset) |
| `current_stage.exit_conditions` | Optional | `stages.yaml` | future progression | no | no |
| `current_stage.typical_days` | Optional | `stages.yaml` | prompts | yes | no |
| `development.primary_capabilities` | Required | `stages.yaml` | prompts | yes | no |
| `development.reinforcing_capabilities` | Optional | `stages.yaml` | prompts | yes | no |
| `development.target_behaviors` | Optional | `capabilities.yaml` | prompts | yes | no |
| `coaching.methodology` | Required | `methodology.md` | prompts | yes | no |
| `coaching.guidance` | Required | `coaching_guidance.md` | prompts | yes | yes (subset) |
| `coaching.stage_guidance` | Optional | `coaching_guidance.md` | prompts | yes | no |
| `coaching.guardrails` | Required | `guardrails.md` | prompts | yes | yes (subset) |
| `practice.relevant_activities` | Optional | `activities.json` | prompts | yes | no |
| `evidence.relevant_evidence` | Future | `evidence.yaml` | future extraction | no | no |
| `progression` | Optional | `progression.yaml` | future engine | no | no |
| `completion` | Optional | `completion.yaml` | future engine | no | no |
| `resources` | Optional | `resources.json` | prompts | yes | no |

---

## 13. Text / Voice Context Parity

| Context Item | Text | Voice | Difference |
|---|---|---|---|
| Pathway name | yes | yes | Same |
| Stage | yes | yes | Same |
| Current day | yes | yes | Same (maybe optional for CM-002) |
| Stage objectives | yes | no | Voice gets summary only |
| Commitments | yes | embedded | Text has structured list; voice has formatted text |
| Risks | yes | embedded | Same as above |
| Advisor guidance | yes | embedded | Text has explicit block; voice has formatted text |
| Prior conversation | yes | yes via transcript | Text uses `SessionMessage`; voice normalizes transcript |
| Business context | yes | embedded | Same as above |
| Current activity | future | future | Not implemented |
| Evidence targets | future | future | Not implemented |
| Guardrails | full | summary | Voice receives only a short prompt reminder |
| Methodology | full | no | Voice does not currently receive methodology |
| Resources | yes | no | Voice does not receive resource list |

**Recommendation:** Both channels should consume the **same normalized `PathwayRuntimeContext`**. Voice should receive a concise, speakable subset, but the underlying data source should be identical. Differences should be handled at the prompt-rendering layer, not at context assembly.

---

## 14. PathwayState Assessment

Current `PathwayState` fields:

- `current_stage_id`
- `current_day`
- `current_focus`
- `current_priority_summary`
- `updated_at`

Assessment:

- `current_stage_id` is universally meaningful.
- `current_day` is **not** universally meaningful. It is required for Recovery but not for Strategic Thinking. It can be left empty or interpreted as optional until the model supports a `current_stage_position` abstraction.
- `current_focus` and `current_priority_summary` are free-text, user-context fields. They can be used generically.
- No capability state, evidence state, or activity state exists.

**Recommendation (B):** The existing `PathwayState` can support an initial CM-002 PoC if `current_day` is treated as optional. However, before full runtime implementation, the schema should be extended to include optional `current_stage_position` or a similar non-day field. For the PoC, `current_day` can be 0 or null.

---

## 15. Progression Ownership

| Responsibility | Owner |
|---|---|
| Define progression semantics | **Pathway Package** |
| Provide `progression_type` and `evidence_considered` | **Pathway Adapter** |
| Observe evidence signals | **Extraction / AI** |
| Evaluate progression decisions | **Background Processor** or **dedicated progression service** (future) |
| Update `PathwayState.current_stage_id` | **Background Processor** or **advisor** |
| Prevent automatic advancement without review | **Advisor** or **safety threshold** |

For the PoC, stage progression should remain manual or advisor-triggered. Automatic evidence-based progression should not be implemented until evidence capture is reliable.

---

## 16. Activity-Selection Ownership

| Responsibility | Owner |
|---|---|
| Define activities | **Pathway Package** |
| Expose activities relevant to current stage | **Pathway Adapter** |
| Suggest an activity based on conversation | **Coaching Engine / prompt** |
| Track activity state | **Future record (not implemented)** |

Activities are coaching instruments, not sequential assignments. The coach should be able to use them naturally without a forced sequence. Future `use_when` logic can help the adapter recommend activities, but it is not required for PoC.

---

## 17. Evidence-Capture Boundary

**Evidence Definition** (in package):

- `evidence_id`
- `capability_id`
- `stage_id`
- `description`
- `evidence_type`

**Evidence Observation** (future user record):

- `user_id`
- `evidence_id`
- `session_id`
- `observed_at`
- `source` (text, voice, advisor)
- `confidence` (optional)

**Where detection/capture would occur:**

1. During extraction (`build_extraction_prompt()`), the AI can infer observations.
2. A future `evidence_extractor` could compare observed statements against `evidence` definitions.
3. The background processor could create `EvidenceObservation` records.
4. The progression evaluator would use `EvidenceObservation` signals.

**For PoC:** no evidence observation model is needed. `CoachingObservation` can capture patterns, and progression can remain manual.

---

## 18. Information Domain Runtime Recommendation

Current `InformationDomain` is administrative only. It has:

- `id`, `name`, `description`, `status`
- `Pathway` records linked by `domain_id`
- New `DomainComponent` model for future domain-level knowledge

**Recommendation for PoC:** Information Domain should remain primarily administrative. It should not be injected into the coaching prompt unless a domain has explicit `knowledge_topic`, `method_framework`, or `practitioner_guidance` components. The hierarchy is:

```
PLATFORM
   ↓ (coaching behavior)
INFORMATION DOMAIN
   ↓ (optional domain knowledge)
PATHWAY
   ↓ (pathway content)
USER
```

For the PoC, the `PathwayRuntimeContext` can include `domain: null` or the domain name only. Domain-level content should be added later.

---

## 19. Minimum Viable CM-002 Runtime Slice

To allow one test user to be assigned to CM-002 and use text and voice coaching, the following minimum changes are required in a future implementation phase:

1. **Package loader updates**
   - Add `CM-002` to `PATHWAY_MAP` (or introduce package discovery).
   - Support `stages.yaml`, `capabilities.yaml`, `activities.json`, etc.

2. **Pathway Adapter**
   - Normalize CM-002 into `PathwayRuntimeContext`.

3. **Context Builder**
   - Use the adapter instead of direct `pathway_data`.
   - Make `current_day` optional.

4. **Prompt updates**
   - Remove "Recovery" and "Day" hard-coding from `voice_service.py`.
   - Build prompts from `PathwayRuntimeContext`.

5. **Admin catalog**
   - Allow assignment of `CM-002` status permitting, but keep it draft initially.

**NOT required for PoC:**

- automatic evidence detection
- automatic progression
- capability scoring
- activity tracking
- completion automation
- new dashboards or analytics
- new database tables

---

## 20. Recommended Integration Sequence

1. Add normalized Pathway Adapter for PATHWAY-001 only.
2. Compare adapter output with existing `build_coaching_context()` / `build_coaching_system_prompt()` output.
3. Write parity tests for Recovery text prompts.
4. Route text context through the adapter; keep `load_pathway()` as the low-level loader.
5. Validate Recovery text behavior.
6. Route voice context through the adapter.
7. Validate Recovery voice behavior.
8. Add `CM-002` to the package catalog (non-assignable at first).
9. Generate and inspect CM-002 `PathwayRuntimeContext`.
10. Add controlled CM-002 assignment for one test user.
11. Test CM-002 text and voice with one internal user.
12. Add evidence/progression behavior later.

---

## 21. Tests Required Before Implementation

### Pathway Adapter Tests

- PATHWAY-001 normalization matches current runtime context.
- CM-002 normalization produces a valid `PathwayRuntimeContext`.
- Missing package returns a clean error.
- Invalid stage or capability reference is handled.
- `progression_type` values are propagated.

### Recovery Parity Tests

- Before/after prompt similarity for Recovery text.
- Voice prompt still contains no Recovery-specific hard-coding after migration.

### Text Tests

- Recovery text remains unchanged.
- Strategic Thinking context contains no Recovery leakage.

### Voice Tests

- Recovery voice remains unchanged.
- Strategic Thinking voice receives correct pathway name, stage, and context.
- Shared context fields are consistent between text and voice.

### Assignment Tests

- CM-002 remains unavailable until explicitly enabled.
- PATHWAY-001 remains assignable.

---

## 22. Risks

1. **Prompt size inflation.** Normalized context may be larger than current prompt. Voice prompt length is constrained.
2. **Current day assumption.** `PathwayState.current_day` is not nullable today. CM-002 may need schema interpretation or extension.
3. **Recovery prompt leakage.** Extraction prompt contains Recovery examples that could mislead CM-002.
4. **Hard-coded voice text.** `voice_service.py` says "AI Recovery Coach" and includes Day.
5. **Pathway discovery.** `PATHWAY_MAP` is currently a hard-coded dictionary.
6. **Adapter overreach.** The adapter could accidentally own user-context queries if not bounded.
7. **File structure differences.** PATHWAY-001 stores stages in `pathway.yaml`; CM-002 uses `stages.yaml`.
8. **Extraction schema mismatch.** Resource IDs in extraction examples like `RS-R001` are Recovery-specific.

---

## 23. Open Questions

1. Should `current_day` be made nullable, or should `PathwayState` get a generic `current_stage_position` field?
2. Should the extraction prompt be rebuilt from a generic schema, or should pathway-specific examples be allowed?
3. Should Information Domain content be injected into the coaching prompt now or later?
4. Should the adapter cache normalized context per engagement?
5. How should voice prompt length be bounded for complex pathways?
6. Should `PathwayRuntimeContext` be a Python dict or a typed dataclass?
7. Should `load_pathway()` continue to be the canonical file loader, or should it be wrapped by a higher-level loader?

---

## 24. Explicit Non-Goals

The following are explicitly out of scope and should not be implemented in this phase:

- Adding CM-002 to `PATHWAY_MAP`
- Modifying `load_pathway()`
- Implementing the Pathway Adapter
- Changing `build_coaching_context()`
- Changing `build_coaching_system_prompt()`
- Changing `voice_service.py`
- Modifying any model or database schema
- Creating migrations
- Enabling CM-002 assignment
- Activating CM-002 in the admin catalog
- Implementing automatic progression or evidence capture
- Refactoring `app.py` or `models/*`

---

## Appendix A: Files Inspected for This Document

- `coaching/engine.py`
- `coaching/context.py`
- `coaching/prompts.py`
- `coaching/ai_service.py`
- `coaching/persistence.py`
- `coaching/validator.py`
- `coaching/voice_service.py`
- `coaching/advisor_helpers.py` (imports only)
- `background_processor.py`
- `app.py` (relevant routes)
- `models/models.py` (relevant models)
- `pathways/recovery_stabilization/pathway.yaml`
- `pathways/recovery_stabilization/methodology.md` (known)
- `pathways/recovery_stabilization/coaching_guidance.md` (known)
- `pathways/recovery_stabilization/guardrails.md` (known)
- `pathways/recovery_stabilization/milestones.json` (known)
- `pathways/recovery_stabilization/resources.json` (known)
- `pathways/strategic_thinking/pathway.yaml`
- `pathways/strategic_thinking/stages.yaml`
- `pathways/strategic_thinking/capabilities.yaml`
- `pathways/strategic_thinking/activities.json`
- `pathways/strategic_thinking/evidence.yaml`
- `pathways/strategic_thinking/progression.yaml`
- `pathways/strategic_thinking/completion.yaml`
- `pathways/strategic_thinking/methodology.md`
- `pathways/strategic_thinking/coaching_guidance.md`
- `pathways/strategic_thinking/guardrails.md`
- `pathways/strategic_thinking/resources.json`
- `docs/PATHWAY_PACKAGE_SPEC_V1.md`

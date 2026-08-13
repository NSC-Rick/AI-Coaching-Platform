# AI Coaching Platform
## Coaching Record — v0.1

**Project:** AI Coaching Platform  
**Initial Pathway:** Recovery & Stabilization  
**Pathway ID:** PATHWAY-001  
**Status:** Proof of Concept  
**Version:** 0.1

---

# 1. Purpose

The Coaching Record is the persistent, authoritative representation of the client’s coaching relationship.

Its purpose is to give the Coaching Platform enough reliable context to:

- Resume coaching across separate voice sessions.
- Understand the client’s current situation.
- Track progress through the assigned Pathway.
- Track goals, actions, commitments, and outcomes.
- Remember significant events and changes.
- Track learning resources and activities.
- Recognize risks and potential escalation conditions.
- Incorporate human-advisor guidance.
- Generate useful advisor briefings.
- Distinguish current state from historical information.

The Coaching Record is not intended to be a transcript archive or a general-purpose CRM.

> **The Coaching Record should remember what matters for effective coaching.**

---

# 2. Core Principle

The AI model does not own client memory.

The Coaching Platform owns the authoritative Coaching Record.

The AI may interpret conversations and propose changes to the record, but persistent client state is maintained by the application.

This creates an important separation:

```text
VOICE CONVERSATION
       │
       ▼
AI INTERPRETATION
       │
       ▼
PROPOSED UPDATES
       │
       ▼
APPLICATION VALIDATION
       │
       ▼
COACHING RECORD
       │
       ▼
FUTURE COACHING CONTEXT
```

Conversation history may support interpretation, but conversation history alone is not the persistence model.

---

# 3. Design Goals

The Coaching Record should be:

### Persistent
Relevant information survives individual coaching sessions.

### Current
The platform can distinguish what is true now from what was true previously.

### Structured Where Useful
Commitments, metrics, resources, stages, risks, and similar objects should be explicitly represented.

### Flexible Where Necessary
Coaching observations, business context, and client reflections may require semi-structured representation.

### Traceable
Important changes should have a source and timestamp.

### Client-Isolated
Every record must belong to the correct client and engagement.

### Pathway-Aware
The record must understand where the client is within the assigned Pathway.

### Advisor-Aware
Relevant advisor guidance and attention items must be represented.

### Concise
The system should not preserve information simply because it was mentioned.

---

# 4. Coaching Record Model

The Coaching Record can be thought of as a set of connected objects:

```text
CLIENT
  │
  └── ENGAGEMENT
        │
        ├── PATHWAY STATE
        ├── GOALS / OBJECTIVES
        ├── COMMITMENTS
        ├── ACTIVITIES
        ├── METRICS
        ├── RISKS / ISSUES
        ├── SIGNIFICANT EVENTS
        ├── LEARNING RECORD
        ├── COACHING OBSERVATIONS
        ├── SESSIONS
        ├── ADVISOR GUIDANCE
        └── ESCALATIONS
```

For the PoC, one client may have one active coaching engagement.

The architecture should not assume that this will always be true in future versions.

---

# 5. Client

The Client object identifies the person receiving coaching.

Suggested fields:

```text
client_id
first_name
last_name
preferred_name
email
phone_optional
status
created_at
updated_at
```

The PoC should collect only information necessary to support the coaching relationship.

Sensitive information should not be collected merely because the platform is capable of storing it.

---

# 6. Business Profile

The Business Profile provides relevant context about the client’s business.

Suggested fields may include:

```text
business_id
client_id
business_name
industry
business_description
location_general
years_in_business
employee_count_optional
business_stage
current_situation_summary
created_at
updated_at
```

The profile should remain lightweight.

The Coaching Platform is not intended to become a full business CRM or case-management system during the PoC.

---

# 7. Engagement

The Engagement connects a client to a Pathway and human advisor.

Suggested fields:

```text
engagement_id
client_id
business_id
advisor_id
pathway_id
engagement_status
start_date
target_end_date
current_day
created_at
updated_at
```

Potential engagement states:

```text
planned
active
paused
completed
closed
```

The engagement becomes the primary boundary for coaching state.

---

# 8. Pathway State

The Pathway State represents where the client currently is within the assigned information domain.

Suggested fields:

```text
engagement_id
pathway_id
current_stage_id
stage_start_date
stage_status
overall_progress
current_focus
current_priority_summary
last_reviewed_at
```

For PATHWAY-001, examples may include:

```text
Phase 1 — Immediate Stabilization
Phase 2 — Revenue Activation & Structural Tightening
Phase 3 — Governance & Accountability
```

The Coaching Engine should retrieve Pathway definitions from the Pathway configuration rather than hard-code these stages.

---

# 9. Goals and Objectives

Goals represent broader desired outcomes.

Objectives represent more specific results within the Pathway.

Example:

```text
GOAL
Stabilize short-term business liquidity.

OBJECTIVES
- Maintain a rolling 14-day cash view.
- Align payroll with current operating reality.
- Prepare for lender discussion.
- Activate near-term revenue opportunities.
```

Suggested fields:

```text
goal_id
engagement_id
pathway_stage_id
title
description
status
priority
target_date
source
created_at
updated_at
completed_at
```

Potential status values:

```text
not_started
active
at_risk
completed
deferred
cancelled
```

---

# 10. Commitments

Commitments are one of the most important Coaching Record objects.

A commitment represents something the client has agreed to do.

Examples:

```text
Contact lender by Thursday.
Call five inactive customers.
Update 14-day cash tracker.
Watch Cash Flow Basics video.
Prepare questions for advisor meeting.
```

Suggested fields:

```text
commitment_id
engagement_id
objective_id_optional
description
created_date
due_date_optional
status
priority
source_session_id
completion_date_optional
completion_note_optional
follow_up_required
created_at
updated_at
```

Potential status values:

```text
open
in_progress
completed
missed
deferred
cancelled
```

The coach should be able to naturally follow up on unresolved commitments in future sessions.

---

# 11. Activities

Activities represent structured work associated with the Pathway.

A commitment may reference an activity, but the two are not identical.

Examples:

```text
Complete 14-Day Cash Tracker.
Prepare Lender Discussion Worksheet.
Complete Customer Prioritization Exercise.
Review weekly plan-to-actual results.
```

Suggested fields:

```text
activity_id
pathway_id
stage_id
title
description
activity_type
completion_criteria
resource_id_optional
```

Client activity state may include:

```text
client_activity_id
engagement_id
activity_id
status
assigned_at
started_at
completed_at
client_reflection
coach_observation
```

---

# 12. Metrics

Metrics represent quantitative information useful to coaching progress.

Examples for Recovery & Stabilization may include:

- Cash available
- 14-day projected cash
- Weekly revenue
- Weekly expenses
- Net weekly income
- Payroll
- Revenue recovered
- Number of customers contacted

Suggested fields:

```text
metric_entry_id
engagement_id
metric_type
metric_name
value
unit
period_start_optional
period_end_optional
observed_at
source
source_session_id_optional
confidence_optional
created_at
```

Metrics should be time-based rather than repeatedly overwriting previous values.

This allows the platform to understand trends.

---

# 13. Risks and Issues

Risks represent conditions that may threaten progress.

Issues represent problems that have already occurred.

Examples:

```text
Risk: Cash runway remains limited.
Risk: Lender discussion has been delayed twice.
Issue: Johnson account lost.
Issue: Client may not be able to meet Friday payroll.
```

Suggested fields:

```text
risk_id
engagement_id
type
title
description
severity
status
first_identified_at
last_updated_at
source
source_session_id_optional
advisor_attention
resolved_at_optional
resolution_note_optional
```

Potential severity:

```text
low
moderate
high
critical
```

Potential status:

```text
open
monitoring
escalated
resolved
```

The AI may identify a potential risk, but the application should maintain its persistent state.

---

# 14. Significant Events

Significant Events capture meaningful changes in the client’s situation.

Examples:

```text
Lost Johnson account.
Employee resigned.
Lender declined proposed modification.
Major customer paid overdue invoice.
Unexpected equipment failure.
Sales exceeded weekly target.
```

Suggested fields:

```text
event_id
engagement_id
event_type
title
description
event_date
estimated_impact_optional
source
source_session_id_optional
created_at
```

Significant Events help the coach understand why the plan or priorities may need to be revisited.

They should not be used to capture every minor conversational detail.

---

# 15. Learning Record

Learning is a first-class component of the coaching relationship.

The Learning Record tracks resources recommended to the client and what happened afterward.

Suggested fields:

```text
learning_record_id
engagement_id
resource_id
recommended_at
recommended_reason
source_session_id
status
accepted_at_optional
completed_at_optional
client_reflection_optional
understanding_level_optional
related_activity_id_optional
follow_up_required
follow_up_completed_at_optional
```

Potential status:

```text
recommended
accepted
started
completed
declined
not_completed
```

This allows the coach to say:

> “Last time we talked, I suggested the short cash-flow video before we worked on your 14-day cash tracker. Were you able to watch it?”

The resource recommendation becomes part of the coaching journey rather than a disposable link.

---

# 16. Coaching Observations

Coaching Observations capture useful patterns that do not fit neatly into another structured object.

Examples:

```text
Client appears comfortable with cash tracking but avoids lender discussions.

Client responds well to small, specific weekly actions.

Client understands revenue targets but is uncertain about pricing decisions.

Client has deferred the same critical action for two consecutive weeks.
```

Suggested fields:

```text
observation_id
engagement_id
observation
category_optional
importance
status
source_session_id
created_at
last_confirmed_at_optional
```

Observations should be:

- Relevant to future coaching.
- Grounded in actual interaction.
- Written neutrally.
- Updated or retired when no longer applicable.

They should not become speculative personality profiles.

---

# 17. Coaching Sessions

A Coaching Session represents an interaction between the client and coach.

Suggested fields:

```text
session_id
engagement_id
started_at
ended_at
interaction_type
session_status
summary
primary_topics
client_sentiment_optional
created_at
```

For the PoC:

```text
interaction_type = voice
```

The session record should preserve a concise summary and links to extracted Coaching Record updates.

A full transcript may be temporarily available or retained depending on technical requirements and privacy decisions, but the Coaching Record should not depend on replaying every transcript.

---

# 18. Session Outcomes

The Session Extractor should produce a structured representation of meaningful outcomes.

Conceptual example:

```json
{
  "session_summary": "Client reported loss of Johnson account and concern about next week's cash position.",
  "new_events": [
    {
      "type": "customer_loss",
      "description": "Johnson account lost",
      "estimated_impact": "$4,000 monthly revenue"
    }
  ],
  "new_commitments": [
    {
      "description": "Update 14-day cash forecast",
      "due": "next coaching session"
    }
  ],
  "commitment_updates": [],
  "metrics": [],
  "risks": [
    {
      "description": "Potential short-term liquidity deterioration",
      "severity": "high"
    }
  ],
  "learning_updates": [],
  "advisor_attention": true,
  "potential_escalation": true
}
```

The exact JSON schema will be defined during implementation.

The important principle is:

> **AI output should be structured enough for the application to reason about before persistence.**

---

# 19. Advisor Guidance

Advisor Guidance allows the human advisor to influence ongoing coaching.

Example:

```text
For the next two weeks, focus on cash visibility and lender preparation.
Do not introduce additional revenue initiatives until those actions are complete.
```

Suggested fields:

```text
advisor_guidance_id
engagement_id
advisor_id
guidance
priority
effective_from
effective_until_optional
status
created_at
updated_at
```

Potential status:

```text
active
superseded
expired
withdrawn
```

Active advisor guidance should be included in relevant coaching context.

---

# 20. Advisor Attention Items

Not every concern requires formal escalation.

An Advisor Attention Item represents something the advisor should know.

Examples:

```text
Client has deferred lender contact for second consecutive week.

Client reports revenue is below plan.

Client is considering changing pricing strategy.

Client completed cash tracker but remains uncertain about assumptions.
```

Suggested fields:

```text
attention_id
engagement_id
title
description
priority
source
source_session_id_optional
status
created_at
reviewed_at_optional
resolved_at_optional
```

Potential priority:

```text
informational
normal
high
urgent
```

---

# 21. Escalations

Escalations represent situations where the Coaching Agent should explicitly involve or defer to the human advisor or another qualified professional.

Suggested fields:

```text
escalation_id
engagement_id
escalation_type
title
description
severity
trigger
source_session_id
status
created_at
acknowledged_at_optional
resolved_at_optional
resolution_note_optional
```

Potential escalation types may include:

```text
advisor
financial_professional
legal_professional
tax_professional
other
```

The specific rules governing escalation belong in the Guardrail and Pathway specifications.

---

# 22. Current State vs. History

The Coaching Record must avoid a common AI-memory problem:

> Old information remaining visible as though it were still true.

For example:

```text
Day 12:
Client is concerned about making payroll.

Day 16:
Major customer payment arrives.
Payroll concern resolved.
```

The platform should preserve the historical concern while clearly marking the current state:

```text
Payroll Risk
Status: Resolved

History:
Identified Day 12
Resolved Day 16
```

The Context Builder should prioritize current state and include historical state only when relevant.

---

# 23. Source and Provenance

Important Coaching Record objects should identify where the information came from.

Potential sources:

```text
client
advisor
pathway
coach_inference
system
```

Where applicable, the source session should also be stored.

Example:

```text
source = client
source_session_id = SESSION-014
```

Information inferred by AI should not silently become equivalent to a client-stated fact.

The system should distinguish:

> **Client said this**

from

> **The coach inferred this**

---

# 24. Confidence

Not every extracted statement will have equal certainty.

For the PoC, confidence may be useful for selected extracted information.

Example:

```text
Client: “The Johnson account was probably around four grand a month.”

Extracted:
Estimated monthly revenue impact = $4,000
Confidence = medium
```

The platform should avoid false precision.

Confidence does not need to become an elaborate scoring system in PoC v0.1.

---

# 25. Coaching Context Snapshot

The Coaching Engine should not send the entire database to the AI.

Instead, the Context Builder should generate a concise snapshot.

Example:

```text
CLIENT
Sarah

BUSINESS
Sarah's Hardware

PATHWAY
Recovery & Stabilization

DAY
18 of 90

CURRENT STAGE
Immediate Stabilization

CURRENT FOCUS
Short-term liquidity

OPEN COMMITMENTS
1. Contact lender — overdue
2. Update 14-day cash tracker — due Friday
3. Contact five inactive customers — 3 of 5 completed

CURRENT RISKS
HIGH — Johnson account lost; estimated $4,000/month impact
MODERATE — Lender contact delayed twice

RECENT LEARNING
Cash Flow Basics video — completed
Client reports improved understanding.

ADVISOR GUIDANCE
Prioritize cash visibility and lender preparation.

RECENT SESSION
Client reported Johnson account loss and agreed to update cash forecast.

COACHING OBSERVATION
Client is consistently completing operational tasks but avoiding lender outreach.
```

This snapshot should be generated from authoritative Coaching Record objects.

---

# 26. What Should NOT Automatically Become Memory

The platform should not persist every statement.

Examples that generally should not become durable Coaching Record objects:

- Casual conversation
- Greetings
- Repeated information already known
- Irrelevant personal details
- Temporary conversational wording
- Unsupported AI speculation
- Information unrelated to the coaching objective

A useful test is:

> **Will remembering this materially improve future coaching, progress tracking, advisor awareness, safety, or continuity?**

If not, it probably does not belong in the Coaching Record.

---

# 27. Record Update Rules

The Session Extractor may propose:

```text
CREATE
UPDATE
RESOLVE
COMPLETE
CANCEL
NO CHANGE
```

The application should determine how those proposals affect persistent records.

Examples:

```text
"I called the lender yesterday."

→ UPDATE commitment: Contact lender
→ status = completed

"They said no to the payment modification."

→ CREATE significant event
→ CREATE/UPDATE risk
→ potentially CREATE advisor attention item

"I might call some customers next week."

→ May NOT yet constitute a commitment.

"I will call five customers by Friday."

→ CREATE commitment
```

This distinction is important for meaningful accountability.

---

# 28. Advisor Briefing View

The Coaching Record should support an advisor summary without requiring transcript review.

A generated brief might include:

```text
CLIENT
Sarah's Hardware

PATHWAY
Recovery & Stabilization — Day 18

STATUS
Attention Needed

SINCE LAST ADVISOR REVIEW
- Johnson account lost; estimated $4,000/month revenue impact.
- Cash Flow Basics resource completed.
- 14-day cash tracker updated.
- Lender contact remains outstanding.

OPEN COMMITMENTS
- Contact lender
- Complete five-customer outreach

CURRENT RISKS
HIGH — Revenue loss may affect near-term liquidity.
MODERATE — Critical lender action delayed.

COACH OBSERVATION
Client is completing operational actions but repeatedly postponing lender outreach.

ADVISOR ATTENTION
Review liquidity impact and lender strategy.
```

---

# 29. Client Isolation

Every Coaching Record object must be scoped to the correct client and/or engagement.

No AI context should be constructed without first resolving the authenticated user to an authorized client engagement.

Client A information must never be included in:

- Client B's coaching context
- Client B's voice session
- Client B's dashboard
- Client B's advisor brief
- Client B's learning history

Client isolation is a hard PoC requirement.

---

# 30. PoC Database Direction

The first implementation should favor a clear, understandable schema over a highly abstract data model.

Likely structured entities include:

```text
users
advisors
clients
businesses
engagements
pathway_states
goals
commitments
client_activities
metric_entries
risks
events
learning_records
observations
sessions
advisor_guidance
advisor_attention
escalations
```

Some fields may contain JSON for flexible PoC data.

The database implementation should remain subordinate to the Coaching Record model.

> **Design the information we need first. Normalize the database only as much as the PoC requires.**

---

# 31. PoC Coaching Record Minimum

To prevent overbuilding, the minimum useful Coaching Record for the first end-to-end test is:

```text
CLIENT
BUSINESS
ENGAGEMENT
PATHWAY STATE
COMMITMENTS
RISKS
SIGNIFICANT EVENTS
LEARNING RECORD
SESSION SUMMARY
COACHING OBSERVATIONS
ADVISOR GUIDANCE
ADVISOR ATTENTION
```

Goals, metrics, activities, and richer history should be included where needed by PATHWAY-001, but the first working voice-to-persistence loop should not wait for every possible data object.

---

# 32. Validation Scenarios

The Coaching Record design should be tested against scenarios such as:

### Continuity
Client returns three days later. Does the coach remember the important open actions?

### Completion
Client reports completing a commitment. Is the commitment updated rather than duplicated?

### Change
Client reports losing a major customer. Does the current state change appropriately?

### Resolution
A previously serious cash concern is resolved. Does the system stop presenting it as current?

### Learning
Client completes a recommended resource. Does the coach follow up and apply the learning?

### Advisor Direction
Advisor changes the current priority. Does future coaching reflect it?

### Escalation
Client reports possible inability to make payroll. Is the issue represented appropriately?

### Contradiction
Client gives information that conflicts with an existing record. Does the platform avoid silently overwriting important state?

### Isolation
Two simulated clients discuss similar issues. Does their information remain completely separate?

---

# 33. Coaching Record Success Criteria

The Coaching Record is successful if it allows the platform to:

- Resume a meaningful coaching relationship across sessions.
- Understand current versus historical state.
- Track commitments without duplication.
- Track significant changes in circumstances.
- Track selected learning and activities.
- Recognize unresolved risks.
- Incorporate advisor direction.
- Produce concise coaching context.
- Produce useful advisor summaries.
- Preserve client isolation.
- Avoid treating raw conversation history as authoritative memory.

---

# 34. Design Rule

When deciding whether something belongs in the Coaching Record, ask:

> **Does this information materially help the coach understand where the client is, where they are going, what they agreed to do, what changed, what they learned, what may be blocking progress, or when the human advisor should become involved?**

If yes, persist it appropriately.

If no, leave it in the conversation.

---

# 35. Summary

The Coaching Record is the memory and continuity layer of the AI Coaching Platform.

It transforms separate voice conversations into an ongoing coaching relationship.

The relationship should be able to answer five fundamental questions at any point:

> **Where is the client now?**

> **Where are they trying to go?**

> **What have they committed to do next?**

> **What has changed since we last spoke?**

> **Where does the human advisor need to be involved?**

If the platform can answer those questions reliably, the coach can behave less like a chatbot and more like a persistent coaching partner.

# AI Coaching Platform
## Pathway Specification — v0.1

**Project:** AI Coaching Platform  
**Initial Pathway:** Recovery & Stabilization  
**Initial Pathway ID:** PATHWAY-001  
**Status:** Proof of Concept  
**Version:** 0.1

---

# 1. Purpose

This document defines the standard structure for an AI Coaching Platform **Pathway**.

A Pathway is a configurable information and coaching domain that plugs into the common Coaching Platform.

The Coaching Platform provides the common mechanics of coaching:

- Voice interaction
- Client identity
- Persistence
- Context assembly
- Coaching continuity
- Commitment tracking
- Learning-resource tracking
- Guardrails
- Escalation
- Advisor visibility
- Advisor briefing

The Pathway provides the domain-specific content and progression:

- What the client is trying to accomplish
- What stages they move through
- What the coach should understand
- What the coach should ask
- What activities the client should complete
- What resources may support learning
- What progress should be measured
- What domain-specific risks matter
- What situations require advisor involvement
- What successful completion looks like

> **Platform = HOW we coach.  
> Pathway = WHAT we coach.**

---

# 2. Primary Design Goal

The Pathway architecture should allow a new information domain to be added without materially changing the core Coaching Engine.

For example:

```text
AI COACHING PLATFORM
        │
        ├── PATHWAY-001
        │   Recovery & Stabilization
        │
        ├── PATHWAY-002
        │   Startup Launch
        │
        ├── PATHWAY-003
        │   Loan Readiness
        │
        └── PATHWAY-XXX
            Future Domain
```

Only **PATHWAY-001: Recovery & Stabilization** will be implemented during the initial PoC.

Future Pathways are architectural validation targets, not PoC scope.

---

# 3. Pathway Definition

A Pathway is:

> **A structured information domain containing methodology, stages, knowledge, activities, curated learning resources, milestones, measures, coaching guidance, guardrails, escalation criteria, and completion conditions that the Coaching Engine uses to guide a client toward a defined outcome.**

A Pathway is more than a knowledge base.

It should describe a **developmental journey**.

---

# 4. Pathway Responsibilities

A Pathway should answer the following questions:

### Purpose
What outcome is this Pathway intended to help achieve?

### Eligibility
When is this Pathway appropriate?

### Boundaries
When is this Pathway not appropriate?

### Starting State
What should the coach understand before coaching begins?

### Stages
What progression should the client move through?

### Objectives
What should be accomplished within each stage?

### Activities
What should the client actually do?

### Learning
What should the client understand?

### Resources
What approved content can support that learning?

### Measures
How do we know whether progress is occurring?

### Milestones
What meaningful checkpoints indicate advancement?

### Coaching Guidance
How should the coach support this particular domain?

### Guardrails
What domain-specific boundaries apply?

### Escalation
What situations require human involvement?

### Completion
How do we know the Pathway has achieved its intended purpose?

---

# 5. Pathway Package

Conceptually, a Pathway may be stored as a package:

```text
/pathways/
    /recovery_stabilization/
        pathway.yaml
        methodology.md
        coaching_guidance.md
        guardrails.md
        assessment.json
        milestones.json
        resources.json
```

The exact file structure may evolve during implementation.

The important architectural principle is:

> **Domain-specific material must remain separable from the Coaching Engine.**

---

# 6. Pathway Manifest

Each Pathway should contain a machine-readable manifest describing the domain.

Conceptual example:

```yaml
pathway_id: PATHWAY-001
slug: recovery_stabilization
name: Recovery & Stabilization
version: 0.1
status: poc

purpose: >
  Help a small business move from immediate financial and
  operational instability toward disciplined stabilization,
  revenue activation, and ongoing accountability.

default_duration_days: 90

stages:
  - stage_id: RS-01
    name: Immediate Stabilization
  - stage_id: RS-02
    name: Revenue Activation & Structural Tightening
  - stage_id: RS-03
    name: Governance & Accountability
```

The manifest allows the application to identify and load the correct Pathway without Recovery-specific logic in the Coaching Engine.

---

# 7. Pathway Identity

Every Pathway should have stable identity metadata.

Recommended fields:

```text
pathway_id
slug
name
version
status
description
purpose
default_duration_optional
owner_optional
created_at_optional
updated_at_optional
```

Potential status values:

```text
draft
poc
pilot
active
retired
```

Pathway IDs should remain stable even when content versions change.

---

# 8. Purpose and Desired Outcome

Each Pathway must explicitly define its intended outcome.

Example:

```text
PATHWAY
Recovery & Stabilization

PURPOSE
Support a small-business owner through a structured
90-day stabilization and revenue-activation process.

DESIRED OUTCOME
The business reaches a more controlled operating position
with improved cash visibility, disciplined operating actions,
revenue activation, and a repeatable accountability cadence.
```

The Coaching Engine should be able to include this outcome when constructing context.

---

# 9. Entry Criteria

A Pathway should define the conditions under which it is appropriate.

Conceptual examples for Recovery & Stabilization:

```text
- Existing operating business.
- Business is experiencing meaningful financial or operating stress.
- Client requires structured stabilization actions.
- Client is capable of participating in an active recovery process.
- Human advisor remains associated with the engagement.
```

Entry criteria are not necessarily automated eligibility decisions.

For the PoC, Pathway assignment may be performed manually by the advisor or system administrator.

---

# 10. Exclusion / Referral Criteria

A Pathway should also identify situations outside its intended operating envelope.

Examples may include situations requiring:

- Legal intervention
- Tax-specific advice
- Formal insolvency or bankruptcy guidance
- Emergency financial intervention
- Specialized regulated expertise
- Another Pathway or service

The coach should not attempt to stretch a Pathway beyond its intended purpose.

---

# 11. Initial Assessment

A Pathway may define an initial assessment used to establish starting context.

Assessment questions should gather only information relevant to coaching.

Potential categories:

```text
Current situation
Primary concern
Immediate priorities
Current constraints
Existing plan
Key metrics
Known risks
Recent significant events
Available resources
Advisor priorities
Client confidence / understanding
```

The assessment may be completed:

- By the client
- With the advisor
- Through the AI coach
- Through a combination of these

For the PoC, simplicity is preferred.

---

# 12. Stage Model

A Pathway should define a sequence of meaningful stages.

Each stage should have:

```text
stage_id
name
purpose
typical_start
typical_end
entry_conditions_optional
objectives
activities
learning_topics
metrics
milestones
exit_conditions
coaching_guidance
```

A stage represents a coaching state, not merely a page in a curriculum.

---

# 13. Stage Example

Conceptual Recovery example:

```yaml
stage_id: RS-01
name: Immediate Stabilization
day_range: 1-30

purpose: >
  Establish immediate operating control and improve
  visibility into short-term liquidity.

objectives:
  - Establish rolling cash visibility
  - Apply agreed spending controls
  - Align payroll and owner compensation
  - Execute approved near-term pricing action
  - Prepare for lender discussion

exit_conditions:
  - Critical stabilization actions are substantially implemented
  - Short-term cash position is visible
  - Outstanding high-priority actions are understood
```

Exact Recovery content will be defined in the PATHWAY-001 implementation document.

---

# 14. Objectives

Objectives define what the client should accomplish.

Objectives should be:

- Specific enough to coach against
- Observable
- Connected to the Pathway outcome
- Associated with a stage where practical

Conceptual structure:

```text
objective_id
stage_id
title
description
priority
success_indicator
required_or_optional
```

The Coaching Record tracks the client's state against these Pathway-defined objectives.

---

# 15. Activities

Activities are structured actions that help the client progress.

Examples:

- Complete a worksheet
- Build a short-term cash view
- Contact selected customers
- Prepare for an advisor meeting
- Review weekly results
- Complete an assessment
- Develop an action list

Conceptual structure:

```text
activity_id
stage_id
title
description
activity_type
instructions
related_objective
resource_optional
completion_criteria
required_or_optional
```

The Pathway defines the activity.

The Coaching Record stores the individual client's activity status.

---

# 16. Knowledge Topics

Each Pathway may define concepts the client may need to understand.

Examples within Recovery might include:

```text
Cash flow vs. profit
Short-term cash visibility
Revenue activation
Expense discipline
Lender preparation
Plan-to-actual review
```

Knowledge topics help the coach distinguish:

> **The client needs an explanation**

from

> **The client needs an action**

from

> **The client needs human-advisor involvement.**

---

# 17. Curated Learning Resources

Learning resources are first-class Pathway components.

Supported resource types may include:

```text
video
audio
podcast
guide
worksheet
checklist
exercise
```

A Pathway resource should be intentionally selected and approved for the domain.

The PoC should not rely on autonomous open-internet content discovery.

---

# 18. Resource Metadata

Recommended resource fields:

```text
resource_id
pathway_id
stage_id_optional
topic
title
resource_type
location
duration_optional
description
learning_objective
when_to_recommend
when_not_to_recommend
prerequisites_optional
follow_up_questions
related_activity_optional
status
```

Example:

```json
{
  "resource_id": "RS-R001",
  "stage_id": "RS-01",
  "topic": "cash_flow",
  "title": "Cash Flow vs. Profit",
  "resource_type": "video",
  "duration": "6 minutes",
  "learning_objective": "Understand why a profitable business can still experience a cash shortage.",
  "when_to_recommend": [
    "Client expresses confusion about cash versus profit",
    "Client is preparing to build the 14-day cash view"
  ],
  "follow_up_questions": [
    "What distinction between cash and profit stood out to you?",
    "How does that show up in your own business?"
  ]
}
```

---

# 19. Resource Recommendation Model

The coach should recommend a resource because it supports a current coaching need.

Desired flow:

```text
CLIENT NEED IDENTIFIED
        │
        ▼
PATHWAY TOPIC
        │
        ▼
APPROVED RESOURCE
        │
        ▼
COACH RECOMMENDS
        │
        ▼
COACHING RECORD
        │
        ▼
FOLLOW-UP
        │
        ▼
APPLICATION TO CLIENT BUSINESS
```

A resource recommendation should not be treated as the end of the coaching interaction.

The coach should connect learning back to action.

---

# 20. Coaching Guidance

Each Pathway should provide domain-specific guidance to the coach.

This may include:

- Coaching priorities
- Recommended questioning patterns
- Important concepts
- Appropriate sequencing
- Common barriers
- Signals of progress
- Signals of concern
- Behaviors to avoid
- Appropriate resource use
- When to involve the advisor

Example:

```text
During Immediate Stabilization:

Prioritize visibility and control before expansion.

Help the client convert broad concerns into specific
near-term actions.

Do not encourage major strategic expansion while
critical stabilization actions remain unresolved.

When the client reports a material change, reassess
its effect on current stabilization priorities.
```

This is distinct from platform-level coaching behavior.

---

# 21. Platform vs. Pathway Coaching Rules

Platform rules apply everywhere.

Examples:

```text
Ask clear questions.
Do not fabricate client facts.
Track explicit commitments.
Distinguish facts from inference.
Respect professional boundaries.
Escalate according to configured rules.
```

Pathway rules apply only within a domain.

Examples:

```text
Recovery:
Prioritize stabilization before expansion.

Loan Readiness:
Do not represent the client as loan-ready solely because
required documents are complete.

Startup:
Do not treat an untested assumption as validated demand.
```

This separation is essential to the multi-domain architecture.

---

# 22. Measures and Metrics

A Pathway may define metrics relevant to progress.

Conceptual structure:

```text
metric_id
stage_id_optional
name
description
unit
frequency_optional
direction_optional
required_or_optional
```

The Pathway defines the metric.

The Coaching Record stores client-specific metric observations over time.

For example:

```text
PATHWAY DEFINITION
Metric: Weekly Revenue

CLIENT RECORD
Week 1: $8,200
Week 2: $8,950
Week 3: $9,400
```

---

# 23. Milestones

Milestones represent meaningful progress points.

Examples:

```text
14-day cash tracker established
Lender discussion completed
Customer outreach cycle completed
Weekly accountability cadence established
```

Recommended fields:

```text
milestone_id
stage_id
title
description
completion_criteria
required_or_optional
```

Milestones should describe progress, not simply elapsed time.

---

# 24. Progression Rules

A Pathway should define how stage progression works.

Progression may consider:

- Time
- Milestones
- Objective completion
- Advisor decision
- Client readiness
- Risk state

The PoC should avoid overly rigid automation.

For PATHWAY-001, elapsed days may provide a default stage orientation, while actual client conditions remain visible to the coach and advisor.

The system should not blindly advance a client simply because a calendar date has arrived.

---

# 25. Domain-Specific Guardrails

A Pathway may define additional guardrails beyond platform-wide boundaries.

Conceptual structure:

```text
guardrail_id
category
description
trigger_conditions
coach_behavior
advisor_attention
escalation_level
```

Example:

```text
TRIGGER
Client proposes significant new borrowing.

COACH BEHAVIOR
Help the client clarify why financing is being considered
and what has changed.

BOUNDARY
Do not make the borrowing decision for the client.

ACTION
Flag for advisor review when material to the approved plan.
```

Exact Recovery guardrails will be defined in PATHWAY-001.

---

# 26. Escalation Criteria

A Pathway should define domain-specific situations requiring human attention.

Potential levels:

```text
LEVEL 0 — Coach normally

LEVEL 1 — Advisor awareness
Include in advisor status.

LEVEL 2 — Advisor attention
Prominently flag for advisor review.

LEVEL 3 — Immediate professional boundary
Coach limits guidance and directs the client toward
appropriate human expertise.
```

The exact naming may evolve during implementation.

The principle is that escalation should be explicit and configurable.

---

# 27. Advisor Guidance

Pathways should allow active advisor guidance to override or refine normal coaching emphasis.

Example:

```text
PATHWAY DEFAULT
Continue customer outreach and lender preparation.

ADVISOR GUIDANCE
For the next two weeks, prioritize lender preparation.
Do not add new revenue initiatives until cash analysis is complete.
```

The Coaching Context Builder should combine:

```text
Platform rules
+ Pathway rules
+ Current client state
+ Active advisor guidance
```

Advisor guidance should not modify the Pathway definition itself.

It modifies how the Pathway is applied to a specific engagement.

---

# 28. Completion Criteria

Every Pathway should define what successful completion means.

Completion may require:

- Required milestones
- Key objectives
- Defined activities
- Acceptable risk state
- Advisor review
- Client readiness for next step

Completion should not necessarily imply that every business problem is solved.

It means the intended Pathway outcome has been sufficiently achieved.

---

# 29. Pathway Completion Output

At completion, the platform may generate a concise summary:

```text
PATHWAY COMPLETION SUMMARY

Client:
Sarah's Hardware

Pathway:
Recovery & Stabilization

Duration:
90 days

Key Outcomes:
- Rolling cash visibility established
- Spending controls implemented
- Customer activation process completed
- Weekly financial review cadence established

Outstanding Items:
- Continue monthly lender reporting

Advisor Recommendation:
Transition from Recovery & Stabilization to normal
business advisory support.
```

This is a future output capability, but the Pathway should contain enough structure to support it.

---

# 30. Pathway Versioning

Pathway content will evolve.

The architecture should preserve a simple version identifier.

Example:

```text
PATHWAY-001
Recovery & Stabilization
Version 0.1
```

For the PoC, sophisticated migration/version-management is unnecessary.

However, the engagement should record which Pathway/version was assigned so future changes do not silently rewrite historical context.

---

# 31. Pathway Loading

Conceptually, the Coaching Engine should be able to perform:

```text
1. Identify engagement.
2. Read pathway_id.
3. Load Pathway manifest.
4. Load current stage.
5. Load relevant methodology.
6. Load coaching guidance.
7. Load relevant guardrails.
8. Load relevant activities/resources.
9. Combine with Coaching Record.
10. Build coaching context.
```

The Coaching Engine should not contain logic such as:

```python
if pathway == "recovery":
    ...
```

except where absolutely necessary for PoC plumbing.

The architectural goal is configuration-driven behavior.

---

# 32. Context Selection

The entire Pathway should not necessarily be injected into every AI interaction.

The Context Builder should select the material relevant to:

- Current stage
- Current objectives
- Current client state
- Current conversation
- Open commitments
- Active risks
- Learning needs
- Advisor guidance

This keeps AI context focused and reduces contradictory or irrelevant instructions.

---

# 33. Pathway Validation

A Pathway should be validated before being made active.

At minimum, validation should confirm:

```text
Pathway ID exists.
Name exists.
Purpose exists.
At least one stage exists.
Stage IDs are unique.
Objectives reference valid stages.
Resources reference valid stages/topics.
Milestones reference valid stages.
Guardrail definitions are readable.
Required files are present.
```

For the PoC this may be a lightweight startup validation rather than a sophisticated management interface.

---

# 34. PATHWAY-001 PoC Resource Limit

To keep the PoC controlled, PATHWAY-001 should contain only a small curated learning set.

Initial target:

```text
3–5 learning resources
2–3 structured activities
Key milestones required by the methodology
Only the metrics needed to demonstrate coaching continuity
```

The objective is to prove resource-aware coaching, not build a learning-management system.

---

# 35. Initial Pathway Data Model

Conceptually, the Pathway package should expose objects such as:

```text
PATHWAY
STAGES
OBJECTIVES
ACTIVITIES
KNOWLEDGE TOPICS
RESOURCES
METRICS
MILESTONES
COACHING GUIDANCE
GUARDRAILS
ESCALATION RULES
COMPLETION CRITERIA
```

The exact storage format may use YAML, JSON, Markdown, or a combination.

The format should be:

- Human-readable
- Easy to edit
- Version controlled
- Machine-readable where structured behavior is required

---

# 36. Pathway Specification Example

A simplified conceptual Pathway could look like:

```yaml
pathway:
  id: PATHWAY-001
  name: Recovery & Stabilization
  version: 0.1

  purpose: >
    Guide a business through stabilization, revenue activation,
    and disciplined accountability.

  stages:
    - id: RS-01
      name: Immediate Stabilization

      objectives:
        - establish_cash_visibility
        - control_discretionary_spending
        - prepare_lender_discussion

      learning_topics:
        - cash_flow
        - short_term_liquidity

      activities:
        - build_14_day_cash_tracker

      milestones:
        - cash_tracker_active

      resources:
        - RS-R001

      coaching_guidance:
        - prioritize_control_before_expansion
        - convert_general_anxiety_into_specific_actions

      escalation_rules:
        - payroll_risk
        - material_new_borrowing
```

This example illustrates structure only.

The authoritative PATHWAY-001 content will be defined separately.

---

# 37. Separation of Definition and Client State

This distinction is critical.

### Pathway Definition

```text
Activity:
Build a 14-Day Cash Tracker.
```

### Coaching Record

```text
Sarah's Hardware
Activity: Build a 14-Day Cash Tracker
Status: Completed
Completed: August 18
Client Reflection: "I finally see why next Friday is tight."
```

The Pathway describes what can or should happen.

The Coaching Record describes what happened for this client.

---

# 38. Separation of Resource and Learning Record

Similarly:

### Pathway Resource

```text
RS-R001
Cash Flow vs. Profit
6-minute video
```

### Client Learning Record

```text
Client: Sarah
Resource: RS-R001
Recommended: August 14
Completed: August 15
Understanding: Improved
Follow-up: Completed
```

This separation allows the same Pathway resource to support many clients without mixing client state into the Pathway.

---

# 39. Separation of Guardrail and Escalation

### Pathway Guardrail

```text
Material new borrowing requires advisor involvement.
```

### Client Escalation Record

```text
Client: Sarah
Date: August 20
Trigger: Considering $50,000 new loan
Status: Advisor attention
```

Again:

> **Pathway = rule.  
> Coaching Record = what occurred.**

---

# 40. Future Pathway Test

After the initial PoC is successful, a strong architecture validation test would be:

> **Can a second information domain be configured as a new Pathway without materially modifying the Coaching Engine?**

A future candidate might be:

```text
PATHWAY-002 — Startup Launch
```

Success would mean that the platform reuses:

- Voice
- Persistence
- Coaching continuity
- Commitment tracking
- Resource tracking
- Advisor dashboard
- Guardrail framework
- Escalation framework

while changing primarily:

- Methodology
- Stages
- Objectives
- Activities
- Resources
- Metrics
- Domain guidance
- Domain guardrails

This test is intentionally outside PoC v0.1.

---

# 41. Pathway Anti-Patterns

Avoid:

### Giant Prompt Pathway
Putting the entire domain into one enormous system prompt.

### Hard-Coded Domain Logic
Embedding Recovery rules throughout Python application code.

### Resource Dump
Giving the coach a list of links without recommendation logic.

### Curriculum Only
Treating the Pathway as a passive training course rather than a coaching journey.

### Transcript Memory
Expecting conversation history to substitute for structured client state.

### AI-Invented Methodology
Allowing the coach to silently alter the approved Pathway.

### Automatic Stage Advancement
Moving clients forward based solely on elapsed time.

### Overbuilding
Creating a full Pathway-authoring platform during the PoC.

---

# 42. PoC Pathway Success Criteria

The Pathway architecture is successful if PATHWAY-001 demonstrates that the Coaching Engine can:

- Load the assigned information domain.
- Understand the current stage.
- Coach toward stage objectives.
- Recommend an appropriate curated resource.
- Track related client learning.
- Assign or follow up on structured activities.
- Recognize stage-specific risks.
- Apply domain-specific guardrails.
- Incorporate advisor guidance.
- Track meaningful progress.
- Avoid embedding Recovery-specific logic throughout the platform.

---

# 43. Design Rule

When adding something to a Pathway, ask:

> **Is this information specific to what we are coaching about?**

If yes, it probably belongs in the Pathway.

When adding something to the Coaching Platform, ask:

> **Would every coaching domain need this capability?**

If yes, it probably belongs in the Platform.

If neither is clearly true:

> **Do we actually need it for the PoC?**

If not:

**Park it.**

---

# 44. Summary

A Pathway is the domain package that turns the common AI Coaching Platform into a specialized coach.

The Coaching Platform provides:

> **Persistence + Interaction + Accountability + Guardrails + Advisor Integration**

The Pathway provides:

> **Methodology + Knowledge + Stages + Learning + Activities + Measures + Domain Rules**

Together they create:

> **A persistent coaching relationship directed toward a defined outcome.**

For PoC v0.1:

### PATHWAY-001 — Recovery & Stabilization

will be the only implemented information domain.

The architecture should nevertheless preserve the core principle:

> **Build the Coaching Platform once. Apply it across information domains through Pathways.**

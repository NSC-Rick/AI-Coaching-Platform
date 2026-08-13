# AI Coaching Platform
## Proof of Concept Scope — v0.1

**Project:** AI Coaching Platform  
**Initial Pathway:** Recovery & Stabilization  
**Pathway ID:** PATHWAY-001  
**Status:** Proof of Concept  
**Version:** 0.1

---

## 1. Purpose

The AI Coaching Platform PoC will test whether a persistent AI Coaching Agent can effectively supplement a human small-business advisor by providing continuous support to a client between advisor interactions.

The platform will provide clients with access to an AI coach that:

- Is available on demand.
- Understands the client's current situation.
- Understands the client's approved Pathway and objectives.
- Maintains relevant context across coaching sessions.
- Helps the client progress through a structured methodology.
- Supports learning through curated resources.
- Tracks actions and commitments.
- Conducts structured progress check-ins.
- Recognizes significant changes, risks, and barriers.
- Operates within defined coaching guardrails.
- Knows when human advisor involvement is appropriate.

The AI Coaching Agent is **not intended to replace the human advisor**.

Its purpose is to:

> **Extend the advisor's presence between meetings.**

---

## 2. Core PoC Hypothesis

The PoC will test the following hypothesis:

> **A persistent AI Coaching Agent can guide a client through a defined Pathway using natural conversation, curated learning, structured activities, progress tracking, accountability, and appropriate human-advisor involvement.**

The initial PoC will use **Recovery & Stabilization** as the first information domain.

---

## 3. Platform Design Principle

The platform will separate **how coaching occurs** from **what the client is being coached about**.

### Coaching Platform — HOW We Coach

The platform provides common capabilities including:

- AI coaching interaction
- Client identity
- Persistent client state
- Coaching history
- Goals
- Commitments
- Progress tracking
- Learning-resource recommendations
- Structured check-ins
- Coaching observations
- Guardrails
- Escalation
- Advisor visibility
- Advisor briefing

### Pathway — WHAT We Coach

A Pathway defines a specific information and coaching domain.

A Pathway may contain:

- Domain knowledge
- Methodology
- Stages or phases
- Objectives
- Assessment questions
- Activities
- Learning resources
- Milestones
- Measures
- Domain-specific coaching guidance
- Domain-specific guardrails
- Escalation triggers
- Completion criteria

The Coaching Platform should not contain Recovery-specific business logic.

Recovery-specific methodology will reside within **PATHWAY-001: Recovery & Stabilization**.

This separation is intended to allow future Pathways to use the same Coaching Platform without materially redesigning the underlying Coaching Engine.

---

## 4. PoC Information Domain

The first Pathway will be:

### PATHWAY-001 — Recovery & Stabilization

The Pathway will be based on the existing **90-Day Stabilization & Revenue Activation Plan**.

The existing methodology is organized around:

### Days 1–30
**Immediate Stabilization**

Focus areas include:

- Cash control
- Payroll and owner-compensation alignment
- Immediate revenue adjustment
- Temporary debt-service modification

### Days 31–60
**Revenue Activation & Structural Tightening**

Focus areas include:

- Repeat-customer revenue activation
- Trade-show/vendor outreach
- Inventory normalization
- Expense normalization

### Days 61–90
**Governance & Accountability**

Focus areas include:

- Weekly financial review
- Revenue
- Expenses
- Net weekly income
- Payroll alignment
- Cash position versus plan
- Lender communication
- Continued operating discipline

The PoC will operationalize this methodology as a structured Coaching Pathway rather than redesign the underlying recovery methodology.

---

## 5. Coaching Experience

The Coaching Agent will support multiple forms of client engagement.

### On-Demand Coaching

The client may initiate a coaching conversation whenever support is needed.

Examples:

- "I'm worried about payroll this week."
- "We lost the Johnson account."
- "I didn't get the lender call done."
- "Sales were much better than expected this week."
- "What should I be concentrating on today?"

### Structured Check-Ins

The coach will support scheduled or expected check-ins designed to maintain progress and accountability.

For the PoC, this may include approximately one or two structured check-ins per week.

### Event-Driven Coaching

The client may engage the coach when something significant changes.

The coach should evaluate the new information against:

- Current client state
- Current Pathway stage
- Current objectives
- Existing commitments
- Known risks
- Pathway methodology
- Coaching guardrails

---

## 6. Client Interaction

The primary client interaction for the PoC will be **voice**.

The PoC will use an **ElevenLabs conversational AI voice agent** as the client-facing coaching interface.

The desired client experience is intentionally simple:

1. Client logs into the Coaching Platform.
2. Client sees basic current status.
3. Client selects **Talk to My Coach**.
4. Client speaks naturally with the AI Coaching Agent.
5. Relevant outcomes from the conversation are captured in the persistent Coaching Record.
6. The next coaching session begins with appropriate awareness of previous progress and events.

Voice is the primary interaction mechanism, but **voice itself is not the product being tested**.

The primary experiment is the persistent coaching relationship behind the voice interface.

---

## 7. Learning & Resource Support

The Coaching Agent will not rely exclusively on conversation.

A Pathway may contain curated learning resources such as:

- Short videos
- Podcast/audio segments
- Guides
- Worksheets
- Checklists
- Exercises

The coach may recommend a resource when it supports the client's current need or next step.

Example:

> A client struggling to understand cash flow may be directed to a short approved resource before working with the coach on the 14-day cash tracker.

The Coaching Record should be capable of tracking:

- Resource recommended
- Resource accepted
- Completion status
- Client reflection or understanding
- Related activity
- Required follow-up

For PATHWAY-001, only a **small curated resource set** will be used to demonstrate this capability.

The PoC will not attempt to build a comprehensive learning-management system.

---

## 8. Persistent Coaching Record

The platform—not the AI model—will own the authoritative client state.

The Coaching Record should maintain sufficient structured and semi-structured information for the coach to understand:

- Who the client is
- Current business situation
- Current Pathway
- Current Pathway phase
- Goals
- Objectives
- Commitments
- Activities
- Progress
- Metrics
- Risks and issues
- Significant events
- Decisions
- Learning activity
- Coaching observations
- Advisor guidance
- Escalations
- Relevant coaching history

The AI model should receive only the context needed for the current interaction.

Conversation history alone will **not** serve as the persistence model.

---

## 9. Human Advisor Role

The human advisor remains an integral part of the coaching model.

The AI Coaching Agent supplements rather than replaces the advisor.

The advisor should maintain visibility into assigned clients through an Advisor Portal.

For the PoC, the Advisor Portal should provide:

- Assigned client list
- Current Pathway
- Current phase/stage
- Overall status
- Current objectives
- Open commitments
- Progress
- Important metrics
- Risks/issues
- Recent coaching summary
- Items requiring advisor attention
- Advisor notes or direction

The goal is to allow an advisor to quickly understand:

> **What has happened since I last interacted with this client, and where is my expertise or attention currently needed?**

---

## 10. Guardrails & Escalation

The Coaching Agent will operate within explicitly defined boundaries.

The agent may independently support activities such as:

- Planning
- Prioritization
- Accountability
- Reflection
- Education
- Progress review
- Preparing for conversations
- Executing approved Pathway activities

The agent should recognize situations that warrant advisor awareness or involvement.

Examples may include:

- Material deterioration in financial condition
- Potential inability to meet payroll
- Significant deviation from the approved plan
- New borrowing
- Major strategic changes
- Repeated inability to complete critical actions

The agent should recognize professional boundaries involving areas such as:

- Legal advice
- Tax advice
- Bankruptcy/insolvency
- Regulated employment matters
- Other matters requiring appropriately qualified professional expertise

Detailed guardrail and escalation rules will be defined separately from this scope document.

---

## 11. Advisor Communication

The architecture should support generation of concise Advisor Status Briefs from the persistent Coaching Record.

Potential brief types include:

- Routine progress brief
- Pathway milestone brief
- Exception/escalation brief

For the initial PoC, automated external email delivery is **not required**.

The primary requirement is demonstrating that the system can generate a useful advisor-ready status summary from the Coaching Record.

---

## 12. PoC Technical Direction

The anticipated PoC stack is intentionally lightweight.

### Application
Python / Flask

### AI
AI API integration

### Voice
ElevenLabs conversational AI

### Persistence
SQL-based persistence, initially using a lightweight implementation appropriate for the PoC

### Hosting
Render

### Source Control
GitHub

### Development
Local project repository with AI-assisted development support

The PoC should favor simplicity, transparency, and ease of modification over production-scale architecture.

---

## 13. PoC Success Criteria

The PoC will be considered successful if it demonstrates that the platform can:

- Maintain accurate client context across multiple coaching sessions.
- Conduct useful contextual coaching conversations.
- Operate within the Recovery & Stabilization Pathway.
- Track client commitments and outcomes.
- Track progress through the Pathway.
- Recommend appropriate curated learning resources.
- Follow up on learning and activities.
- Recognize meaningful changes in client circumstances.
- Identify situations requiring advisor attention.
- Remain within defined coaching guardrails.
- Generate a useful advisor briefing.
- Maintain clear separation between different client records.
- Resume a coaching relationship without requiring the client to repeatedly explain previous context.

---

## 14. PoC Test Approach

The PoC will use a small number of simulated client scenarios.

Testing should intentionally include both normal progress and disruptive events.

Potential scenarios include:

- Missed commitments
- Improved sales
- Lost customer
- Employee departure
- Payroll concern
- Lender rejection
- Proposed new borrowing
- Proposed expansion
- Cash deterioration
- Legal or tax question
- Contradictory client information
- Advisor priority change
- Extended client inactivity
- Successful completion of a learning activity
- Failure to complete an assigned activity

Testing should evaluate both:

**Client experience**

and

**Advisor usefulness**

---

## 15. Explicitly Out of Scope for PoC v0.1

The following are intentionally outside the initial PoC:

- Native mobile applications
- SMS coaching
- CRM integration
- Accounting-system integration
- Banking integration
- Google Workspace integration
- Microsoft 365 integration
- Comprehensive email automation
- Statewide analytics
- Production-scale identity management
- Comprehensive learning-management functionality
- Open internet resource recommendation
- Automated financial decision-making
- Multiple production Pathways
- Client-facing autonomous financial, legal, tax, or lending advice

These concepts may inform architectural decisions but **will not be implemented as part of PoC v0.1**.

---

## 16. Extensibility Principle

The Coaching Engine will be designed to support multiple information domains through configurable Pathways.

However:

> **The PoC will architect for multiple Pathways while implementing only one.**

PATHWAY-001 — Recovery & Stabilization will be used to prove the architecture.

A future test may introduce a second Pathway specifically to determine whether a new information domain can be added without materially changing the core Coaching Engine.

That test is outside the initial PoC implementation.

---

## 17. Guiding Design Principles

### Build Once, Apply Across Domains
Common coaching capabilities belong to the platform. Domain-specific knowledge belongs to Pathways.

### Human Supported
AI extends the advisor's presence; it does not replace the advisor.

### Persistent, Not Stateless
The Coaching Platform owns a structured, evolving client record.

### Conversation Is Not Enough
Effective coaching combines conversation, learning, action, reflection, accountability, and adaptation.

### Curated Over Random
Pathway resources should initially be intentionally selected rather than discovered autonomously from the open internet.

### Low Friction
Clients should not need AI expertise or special prompting skills to use their coach.

### Advisor Visibility
The human advisor should be able to quickly understand progress, barriers, risks, and areas requiring attention.

### Design for Extensibility — Build for the Experiment
Future possibilities may influence architecture, but they do not automatically enter PoC scope.

---

## 18. PoC North Star

> **Prove that one client can have a useful, persistent, voice-based AI coaching relationship within one defined Pathway, using conversation, learning, action and accountability, while keeping one human advisor meaningfully informed and in control.**

**Pathway 001: Recovery & Stabilization.**

Everything else waits until we prove that.
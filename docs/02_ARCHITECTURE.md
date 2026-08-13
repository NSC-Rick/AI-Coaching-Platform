# AI Coaching Platform
## Architecture — v0.1

**Project:** AI Coaching Platform  
**Initial Pathway:** Recovery & Stabilization  
**Pathway ID:** PATHWAY-001  
**Status:** Proof of Concept  
**Version:** 0.1

---

# 1. Purpose

This document defines the initial architecture for the AI Coaching Platform Proof of Concept.

The architecture is designed around a fundamental separation:

> **The Coaching Platform defines HOW coaching occurs.  
> A Pathway defines WHAT the client is being coached about.**

The initial implementation will use **PATHWAY-001: Recovery & Stabilization**, based on the existing 90-Day Stabilization & Revenue Activation methodology.

The architecture should allow future information domains to be introduced as additional Pathways without materially redesigning the core Coaching Engine.

The PoC will implement only one Pathway.

---

# 2. Architectural North Star

The platform will provide a persistent, voice-based AI coaching relationship that operates within an approved information domain and supplements a human advisor.

Conceptually:

```text
                         CLIENT
                           │
                           │ Voice
                           ▼
                  ELEVENLABS AGENT
                           │
                           ▼
                  COACHING PLATFORM
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
          COACHING      CLIENT       PATHWAY
           ENGINE       RECORD       DOMAIN
              │            │            │
              └────────────┼────────────┘
                           │
                           ▼
                      AI SERVICES
                           │
                           ▼
                    COACHING OUTPUT
                           │
                           ▼
                         CLIENT

                           ↕

                    HUMAN ADVISOR
                           │
                           ▼
                  ADVISOR DASHBOARD
```

---

# 3. Core Architectural Principles

## 3.1 Platform Owns State

The AI model does not own authoritative client memory.

The Coaching Platform maintains persistent client state.

The AI receives the context required to conduct the current coaching interaction.

## 3.2 Pathways Own Domain Knowledge

Recovery-specific knowledge and methodology must not be hard-coded into the core Coaching Engine.

A Pathway supplies:

- Domain knowledge
- Methodology
- Stages
- Objectives
- Activities
- Learning resources
- Metrics
- Milestones
- Domain-specific coaching guidance
- Domain-specific guardrails
- Escalation triggers
- Completion criteria

## 3.3 The AI Reasons; the Application Controls

The AI may:

- Interpret client statements
- Conduct coaching conversations
- Identify potential new information
- Recommend resources
- Identify potential risks
- Suggest record updates
- Generate summaries
- Evaluate situations against coaching guidance

The application controls:

- Authentication
- Client identity
- Advisor identity
- Data access
- Pathway assignment
- Persistent storage
- Record updates
- Permissions
- Session lifecycle
- Audit information
- External communications

## 3.4 Human Advisor Remains in the Loop

The architecture will preserve a distinct human-advisor layer.

The Coaching Agent supplements advisor activity but does not assume the role of the advisor.

The system should make it easier for the advisor to understand:

- What changed
- What was accomplished
- What remains outstanding
- What the client is struggling with
- What risks have emerged
- Where human attention may be needed

## 3.5 Voice Is an Interface

ElevenLabs provides the primary client interaction channel for the PoC.

It is not the system of record.

It should not become the exclusive owner of:

- Client memory
- Methodology
- Business rules
- Coaching history
- Progress
- Guardrails

The architecture should allow another interaction channel to use the same Coaching Engine in the future.

## 3.6 Mobile-First Web Experience

The Client Portal will use a responsive, mobile-first design.

No native mobile application is required for the PoC.

Core client functionality must work effectively from a standard mobile browser, including:

- Authentication
- Viewing current Pathway status
- Viewing priorities and commitments
- Viewing progress
- Viewing recommended resources
- Launching the ElevenLabs voice coach

The same web application should also function effectively on tablets and desktop browsers.

The Advisor Portal should be responsive as well, although desktop use is expected to be the primary advisor experience.

---

# 4. Logical Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                        CLIENT EXPERIENCE                     │
│                                                              │
│   Login        Current Status        Talk to My Coach        │
│   Mobile-first responsive web interface                      │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     ELEVENLABS VOICE LAYER                   │
│                                                              │
│   Speech Input     Conversational Experience     Voice Output│
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                      COACHING PLATFORM                       │
│                                                              │
│  Authentication                                              │
│  Session Management                                          │
│  Coaching Orchestration                                      │
│  Context Assembly                                            │
│  Pathway Loading                                             │
│  Record Management                                           │
│  Guardrail Evaluation                                        │
│  Escalation Evaluation                                       │
│  Resource Selection Support                                  │
│  Advisor Brief Generation                                    │
└──────────────┬──────────────────────┬────────────────────────┘
               │                      │
               ▼                      ▼
┌──────────────────────────┐   ┌──────────────────────────────┐
│       AI SERVICES        │   │      PERSISTENCE LAYER       │
│                          │   │                              │
│ Coaching                 │   │ Clients                      │
│ Extraction               │   │ Engagements                  │
│ Summarization            │   │ Pathway State                │
│ Classification           │   │ Objectives                   │
│ Risk Detection           │   │ Commitments                  │
│ Resource Matching        │   │ Metrics                      │
│                          │   │ Risks                        │
│                          │   │ Sessions                     │
│                          │   │ Resources                    │
│                          │   │ Advisor Notes                │
│                          │   │ Escalations                  │
└──────────────────────────┘   └──────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                         PATHWAY                              │
│                                                              │
│   Methodology          Stages          Objectives            │
│   Activities           Resources       Measures              │
│   Guardrails           Milestones      Completion Criteria   │
└──────────────────────────────────────────────────────────────┘
```

---

# 5. Major Components

## 5.1 Client Web Portal

The Client Portal provides the entry point into the coaching relationship.

PoC functionality should remain intentionally limited.

The client should be able to:

- Authenticate
- See their assigned Pathway
- See their current stage
- See basic current priorities
- See open commitments
- See recommended learning resources
- Launch the voice coach
- Review basic progress

The Client Portal should not become a complex dashboard.

Its primary purpose is to provide a low-friction front door to the coaching relationship.

### Mobile Requirement

The Client Portal must be designed mobile-first and remain responsive across common phone, tablet, and desktop screen sizes.

The primary mobile interaction should require minimal navigation:

> **Open site → authenticate → see current status → Talk to My Coach**

The **Talk to My Coach** control should be prominent and easy to use from a phone.

## 5.2 ElevenLabs Voice Agent

ElevenLabs provides the conversational voice interface.

Responsibilities include:

- Capture client speech
- Conduct natural voice interaction
- Present coaching responses conversationally
- Maintain the immediate conversational experience

The ElevenLabs layer should interact with the Coaching Platform so that conversations are informed by persistent client context.

Where technically practical, the platform should provide the voice agent with relevant context at session initiation and capture relevant interaction outcomes at session completion.

## 5.3 Coaching Engine

The Coaching Engine is the central orchestration layer.

It is domain-independent.

Its responsibilities include:

- Identify client and engagement
- Identify assigned Pathway
- Retrieve current Coaching Record
- Retrieve current Pathway state
- Retrieve relevant recent context
- Retrieve advisor guidance
- Retrieve appropriate Pathway instructions
- Assemble AI context
- Invoke appropriate AI capability
- Interpret structured AI output
- Validate proposed record changes
- Update persistent state
- Evaluate guardrails
- Evaluate escalation conditions
- Track commitments
- Track learning-resource activity
- Generate advisor summaries

The Coaching Engine should not contain Recovery-specific methodology.

---

# 6. AI Service Roles

The PoC does not require a complex autonomous multi-agent architecture.

Instead, the platform may use several clearly defined AI roles.

## 6.1 Coach

Client-facing reasoning and conversation.

Purpose:

> Help the client make progress through the assigned Pathway using appropriate coaching behavior.

## 6.2 Session Extractor

Non-client-facing function.

Purpose:

> Analyze a coaching interaction and identify structured updates to the Coaching Record.

Potential outputs include:

- New fact
- Updated fact
- Significant event
- Commitment
- Commitment status change
- Metric
- Risk
- Decision
- Learning need
- Resource recommendation
- Coaching observation
- Potential escalation

Structured output should be preferred.

## 6.3 Guardrail / Escalation Evaluation

Evaluates the interaction and current state against:

- Platform-level guardrails
- Pathway-specific guardrails
- Escalation criteria

For the PoC this capability may be incorporated into another AI service rather than implemented as an independent autonomous agent.

## 6.4 Advisor Brief Generator

Produces a concise summary of client progress for the human advisor.

The summary should be generated primarily from the persistent Coaching Record rather than from raw conversation history.

---

# 7. Persistence Architecture

Persistence is a core capability of the Coaching Platform.

The platform should distinguish between:

### Current State

What is true now?

Examples:

- Current Pathway phase
- Current priorities
- Open commitments
- Current cash concern
- Current risk level

### Historical State

What happened previously?

Examples:

- Completed commitments
- Prior metrics
- Previous risks
- Significant events
- Previous advisor direction

### Coaching History

What coaching interactions occurred?

Examples:

- Session date
- Session summary
- Key topics
- Extracted outcomes

### Learning History

What resources and activities have been recommended or completed?

---

# 8. Structured and Semi-Structured Data

The PoC should use a hybrid persistence model.

Highly structured information should use relational data where practical.

Examples:

- Users
- Clients
- Advisors
- Engagements
- Commitments
- Metrics
- Sessions
- Resources
- Escalations

More fluid coaching information may initially use semi-structured data.

Examples:

- Business situation
- Coaching observations
- Contextual notes
- Complex risk descriptions
- Client reflections

The initial architecture should favor learning and adaptability over premature database normalization.

---

# 9. Coaching Context Builder

The Coaching Context Builder is a critical architectural component.

Before a coaching interaction, it should assemble a concise representation of relevant client state.

Example:

```text
CLIENT
Sarah's Hardware

PATHWAY
Recovery & Stabilization

CURRENT PHASE
Day 18 — Immediate Stabilization

PRIMARY OBJECTIVE
Improve short-term liquidity.

CURRENT PRIORITIES
- Maintain 14-day cash visibility
- Complete lender preparation
- Continue customer outreach

OPEN COMMITMENTS
- Contact lender by Thursday
- Contact five inactive customers

CURRENT RISKS
- Cash runway remains limited
- Revenue below stabilization target

RECENT EVENT
Johnson account lost.
Estimated revenue impact: $4,000/month.

COACHING OBSERVATION
Client has postponed lender discussion twice.

ADVISOR GUIDANCE
Prioritize cash visibility and lender preparation.

RECENT SESSION
Client agreed to prepare lender discussion points.
```

The AI should receive relevant context rather than an uncontrolled dump of the entire client history.

---

# 10. Post-Session Processing

Following a meaningful coaching interaction, the platform should evaluate whether the Coaching Record needs to change.

Conceptually:

```text
VOICE SESSION
     │
     ▼
SESSION TRANSCRIPT / OUTCOME
     │
     ▼
SESSION EXTRACTOR
     │
     ├── Facts
     ├── Events
     ├── Commitments
     ├── Metrics
     ├── Risks
     ├── Decisions
     ├── Resources
     └── Escalations
             │
             ▼
       VALIDATION LAYER
             │
             ▼
       COACHING RECORD
```

The AI should propose structured updates.

The application should determine how those updates are persisted.

---

# 11. Pathway Architecture

A Pathway should be treated as a configurable information domain.

Conceptually:

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

Exact file structure may change during implementation.

The architectural principle is more important:

> Domain-specific material should be separable from the core Coaching Engine.

---

# 12. PATHWAY-001 — Recovery & Stabilization

The initial Pathway will operationalize the existing 90-Day Stabilization & Revenue Activation Plan.

The source methodology includes three major stages:

### Phase 1
Immediate Stabilization — Days 1–30

### Phase 2
Revenue Activation & Structural Tightening — Days 31–60

### Phase 3
Governance & Accountability — Days 61–90

The Pathway specification will define how these stages become actionable coaching structures.

The Pathway should also contain a small set of curated learning resources and activities sufficient to demonstrate guided learning.

---

# 13. Resource Architecture

Resources are first-class Pathway objects.

A resource may include:

```text
resource_id
pathway_id
stage
topic
title
resource_type
location
duration
learning_objective
when_to_recommend
when_not_to_recommend
prerequisites
follow_up_questions
related_activity
```

Potential resource types include:

- Video
- Audio
- Podcast
- Guide
- Worksheet
- Checklist
- Exercise

The PoC will use a deliberately small curated resource library.

---

# 14. Advisor Architecture

The Advisor Portal operates against the same persistent Coaching Record.

The advisor should not need to review every coaching conversation to understand client progress.

The platform should instead surface:

- Current state
- Progress
- Commitments
- Significant events
- Metrics
- Risks
- Coaching observations
- Learning progress
- Escalations
- Advisor attention items

Conceptually:

```text
ADVISOR
   │
   ▼
MY CLIENTS
   │
   ├── Client A     Green
   ├── Client B     Yellow
   └── Client C     Red
                         │
                         ▼
                   CLIENT DETAIL
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Progress     Risks     Commitments
              │          │          │
              └──────────┼──────────┘
                         ▼
                   ADVISOR BRIEF
```

---

# 15. Advisor Direction

The architecture should permit an advisor to add relevant direction to a client engagement.

Example:

```text
Advisor Guidance:

For the next two weeks, prioritize cash visibility
and lender preparation. Do not introduce additional
revenue initiatives until those actions are complete.
```

Advisor guidance becomes part of the context available to the Coaching Engine.

This allows the human advisor to influence the ongoing coaching relationship without needing to participate in every interaction.

---

# 16. Guardrail Architecture

Guardrails exist at two levels.

## Platform Guardrails

Apply across all Pathways.

Examples:

- Identity boundaries
- Privacy
- Professional boundaries
- Appropriate human escalation
- Prohibition against unauthorized external actions

## Pathway Guardrails

Specific to the information domain.

Examples within Recovery & Stabilization may include:

- Material new borrowing
- Significant expansion
- Major changes to approved recovery strategy
- Severe deterioration in liquidity
- Potential inability to meet payroll

The Coaching Engine should evaluate both layers.

---

# 17. Client Isolation

Client isolation is a non-negotiable requirement.

Information belonging to one client must never appear in another client's:

- Coaching context
- AI interaction
- Coaching Record
- Advisor view
- Summary
- Resource history

Every persistent object should be associated with the appropriate client and/or engagement identifier.

Testing for cross-client leakage will be part of the PoC test strategy.

---

# 18. Initial Technology Stack

The PoC will use a lightweight implementation.

### Local Development
Project folder with Git source control

### Repository
GitHub

### Hosting
Render

### Application
Python 3 / Flask

### Production Web Server
Gunicorn

### Voice
ElevenLabs Conversational AI

### AI
API-based AI services

### Persistence
SQL

The exact deployed database technology may differ from local development if required to ensure persistence across Render deployments.

### Web Experience
Responsive, mobile-first HTML/CSS/JavaScript delivered through the Flask application.

No native mobile application is required for the PoC.

---

# 19. Initial Project Structure

A likely initial structure is:

```text
AI-Coaching-Platform/
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
│
├── docs/
│   ├── 01_POC_SCOPE.md
│   ├── 02_ARCHITECTURE.md
│   ├── 03_COACHING_RECORD.md
│   ├── 04_PATHWAY_SPECIFICATION.md
│   └── 05_PATHWAY_001_RECOVERY_STABILIZATION.md
│
├── coaching/
│   ├── engine.py
│   ├── context.py
│   ├── extractor.py
│   ├── persistence.py
│   └── escalation.py
│
├── pathways/
│   └── recovery_stabilization/
│       ├── pathway.yaml
│       ├── methodology.md
│       ├── coaching_guidance.md
│       ├── guardrails.md
│       ├── milestones.json
│       └── resources.json
│
├── templates/
│   ├── login.html
│   ├── client_home.html
│   ├── advisor_home.html
│   └── client_detail.html
│
├── static/
│   ├── css/
│   └── js/
│
└── data/
    └── coaching.db
```

This structure is illustrative rather than mandatory.

Implementation should remain as simple as practical during the PoC.

---

# 20. Primary Runtime Flow

The desired runtime flow is:

```text
1. Client authenticates
             ↓
2. Platform identifies client and engagement
             ↓
3. Platform loads assigned Pathway
             ↓
4. Platform retrieves current Coaching Record
             ↓
5. Context Builder assembles relevant context
             ↓
6. Client begins ElevenLabs voice session
             ↓
7. AI Coaching Agent conducts conversation
             ↓
8. Session outcome/transcript becomes available
             ↓
9. Session Extractor identifies meaningful updates
             ↓
10. Application validates/persists updates
             ↓
11. Guardrail/escalation state is evaluated
             ↓
12. Advisor view is updated
             ↓
13. Next session begins from updated client state
```

This loop is the core mechanism that transforms a voice interaction into a **persistent coaching relationship**.

---

# 21. Architecture Validation

The PoC should demonstrate:

### Persistence
The coach remembers what matters across sessions.

### Domain Independence
Recovery-specific methodology remains outside the core Coaching Engine.

### Coaching Continuity
Each interaction builds upon previous progress.

### Learning Integration
The coach can appropriately introduce curated resources and follow up.

### Accountability
Commitments survive beyond individual conversations.

### Guardrails
The coach recognizes its operating boundaries.

### Advisor Integration
The advisor gains useful visibility without participating in every coaching interaction.

### Client Isolation
One client's information never contaminates another client's experience.

### Mobile Accessibility
Core client coaching functions operate effectively on common phone, tablet, and desktop screen sizes, with the client experience designed mobile-first.

---

# 22. Future Architecture — Intentionally Not Implemented

The architecture may eventually support:

- Additional Pathways
- AI Adoption coaching
- Startup coaching
- Loan-readiness coaching
- Business transition coaching
- Text interaction
- Native mobile applications
- SMS
- Email automation
- CRM integration
- Accounting integration
- Statewide aggregate analytics
- Advisor-created Pathways
- Expanded learning libraries

These possibilities may influence interface boundaries and data design.

They do **not** belong in the initial implementation.

---

# 23. Architectural Rule

When evaluating a proposed feature, ask:

> **Is this a Coaching Platform capability, a Pathway capability, or something we don't need to prove the PoC?**

If it is domain-specific, it belongs in the Pathway.

If it is common to coaching across domains, it may belong in the Platform.

If it does not help prove the PoC hypothesis:

**Park it.**

---

# 24. Architecture Summary

The AI Coaching Platform is built around five primary elements:

> **VOICE — how the client communicates**

> **COACHING ENGINE — how the platform coaches**

> **PATHWAY — what the client is being coached about**

> **COACHING RECORD — what the relationship knows and remembers**

> **HUMAN ADVISOR — expertise, oversight, and intervention**

The web experience provides a sixth important delivery characteristic:

> **MOBILE-FIRST ACCESS — how the client reaches the coaching relationship with minimal friction**

The first implementation will prove these elements using:

### PATHWAY-001 — Recovery & Stabilization

The objective is not to build a complete coaching ecosystem.

The objective is to prove that this architecture can create a useful, persistent, human-supported AI coaching relationship.

> **Build the platform once. Configure the information domain through Pathways.**

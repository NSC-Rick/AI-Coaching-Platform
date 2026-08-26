# North Star Proficiency Builder
## Advisor Support Knowledge Guide

This guide describes the current implementation of North Star Proficiency Builder (PB) as it exists today. It is intended as a knowledge source for a future AI support agent that assists advisors. Only verified current behavior is documented; planned or placeholder functionality is clearly marked as such.

---

### 1. Platform Overview

North Star Proficiency Builder is a web-based application that supports a human advisor and an AI Coach working together to help a small-business client make progress through a structured Pathway.

**Core relationships:**

- **Advisor**: A human professional who is assigned to one or more clients. Advisors can review client records, view coaching activity, and add guidance for the AI Coach.
- **Client**: A small-business owner who is enrolled in a Pathway. Clients interact with the AI Coach by text or voice.
- **Pathway**: A structured 90-day program made up of stages, objectives, guardrails, and approved resources. The current active Pathway is "Recovery & Stabilization" (PATHWAY-001).
- **Coaching Record**: The persistent collection of everything PB knows about the client, including the business context, current Pathway state, commitments, risks, significant events, learning records, coaching observations, advisor guidance, and session transcripts.
- **AI Coach**: The conversational agent that talks with the client. It uses the Coaching Record, Pathway content, and any Advisor Guidance to provide consistent, grounded coaching.

**What the advisor does vs. what the AI Coach does:**

- The **AI Coach** handles day-to-day coaching conversations with the client through text or voice. It helps the client act on the current focus, follow up on commitments, recognize risks, and use Pathway resources.
- The **advisor** reviews client progress, adds high-level guidance, and steps in when PB flags that human attention is needed.

---

### 2. Core Concepts

#### Information Domain
Information Domains are an admin-facing concept. They are containers for knowledge topics, methods, practitioner guidance, resources, and guardrails. An advisor does not interact with Information Domains directly.

#### Pathway
A Pathway is the structured coaching program a client follows. The only Pathway that is runtime-integrated today is **PATHWAY-001 — Recovery & Stabilization**. It is a 90-day PoC Pathway with three stages:

- **RS-01 — Immediate Stabilization** (typical days 1-30)
- **RS-02 — Revenue Activation & Structural Tightening** (typical days 31-60)
- **RS-03 — Governance & Accountability** (typical days 61-90)

The client's active Pathway is set when an admin creates an assignment. The client and advisor see the Pathway name, current stage, and current day in the dashboard and client detail screens.

#### Pathway Stage
A Pathway Stage is a named phase of the Pathway. Each stage has a purpose and a list of key objectives. The AI Coach uses stage objectives, stage-specific coaching guidance, and guardrails to keep conversations aligned.

#### Current Focus
Current Focus is a short text statement stored on the client's Pathway State. It describes what the client is working on right now. It is shown on the client dashboard, the advisor Client Detail screen, and in the AI Coach context. Example: "Short-term cash visibility."

#### Current Priorities
Current Priorities is a short text summary also stored on the Pathway State. It captures the most important priorities for the current period. Example: "Make payroll and protect cash position."

#### Milestone
Milestones are a data concept in the Pathway package, but the current advisor and client UIs do **not** display a milestone checklist. They are not an active part of the day-to-day user experience.

#### Commitment
A Commitment is a specific action the client has agreed to take. It has a description, optional due date, priority (high/normal/low), and status (open, completed, deferred, cancelled). Commitments can be created by the AI Coach after a coaching session or by client report during a conversation. They are surfaced in the client dashboard and the advisor Client Detail screen.

#### Risk
A Risk is a potential or active business issue. It has a title, optional description, severity (critical/high/moderate/low), status (open/resolved/mitigated), and an `advisor_attention` flag. The AI Coach can create risks from conversations. Risks appear in the "Risks & Watch Items" section of Client Detail.

#### Advisor Guidance
Advisor Guidance is a text note an advisor writes for a specific client. It has a priority (normal/high) and status (active). Active guidance is included in the context provided to the AI Coach, so the AI Coach can respect and emphasize the advisor's direction.

#### Coaching Session
A Coaching Session is one conversation between the client and the AI Coach. It has an `interaction_type` of `text` or `voice`, a start time, an end time, a status (`active` or `completed`), and a `processing_status` (`none`, `pending`, `processing`, `complete`, or `failed`). When a session ends, PB extracts structured outcomes from the transcript and updates the Coaching Record.

#### Coaching Record / Persistent Client Context
The Coaching Record is the combination of all persisted data for an engagement: client and business context, current Pathway state, open commitments, current risks, significant events, recent learning records, active coaching observations, active advisor guidance, and recent sessions.

#### Helpful Resources
Helpful Resources are Pathway-approved learning resources shown to the client in the client dashboard sidebar. They include videos and guides matched to the current stage. Most current resources have no live URL and are marked as placeholder.

#### Pathway Tools
Pathway Tools are external applications or calculators linked from the Helpful Resources sidebar. Currently, the only Pathway Tool is the **Small Business Finance Modeler**, which opens in a new browser tab.

---

### 3. Advisor Dashboard

The advisor dashboard is the first screen an advisor sees after logging in.

**What it displays:**

- **Welcome**: The advisor's first and last name.
- **My Clients**: A grid of active client engagements assigned to this advisor.

For each client card, the advisor sees:

- **Business name** (or the client's name if no business name is set).
- **Client's full name**.
- **Pathway**: The name of the active Pathway.
- **Stage**: Current Pathway stage ID and day.
- **Status**: The engagement status (e.g., `active`).
- **Open Commitments count**.
- **Highest Risk**: The most severe open risk, if any.
- **Needs Attention**: The count of open advisor-attention items, if any.
- **View Details button**: Opens the Client Detail screen.

**Source of data:** All data comes from the existing persisted Coaching Record: `Engagement`, `Client`, `Business`, `PathwayState`, `Commitment`, `Risk`, `AdvisorAttention`, and the Pathway package manifest.

**Use for the advisor:** This is a monitoring and triage screen. It helps the advisor quickly see which clients have open work, risks, or attention items.

---

### 4. Client Detail

The Client Detail screen is the advisor's main view for reviewing a single client.

**Sections shown:**

1. **Client Header**
   - Client name, business name, engagement status, last client interaction date.
   - Buttons: "Generate Client Storyboard" and "Back to Dashboard".

2. **Current Coaching Snapshot**
   - A summary card showing the current focus and, when available, the next meaningful action. If nothing has been recorded, it says "No recent coaching activity to display."

3. **Advisor Attention + Current Status**
   - **Advisor Attention card**: Tells the advisor whether PB recommends review, shows the reason, and lists up to three watch items. Includes an "Add Advisor Guidance" button.
   - **Current Status card**: Counts active commitments, open risks, current Pathway day, current stage name, last client interaction, and last advisor interaction.

4. **Active Work / Completed Work**
   - A two-tab list of client commitments.
   - **Active** shows the next-actions (high priority or due soon) and other open commitments with due dates.
   - **Completed** shows commitments completed in the last seven days.

5. **Recent Developments**
   - A reverse-chronological timeline of the last few session summaries, active high-importance observations, and significant events.

6. **Pathway Progress**
   - Pathway name, current stage ID, current day, and stage name.

7. **Risks & Watch Items**
   - Active and watch risks with severity and title.

8. **Advisor Guidance**
   - A form to add new guidance.
   - A history of recent guidance with priority and date.

9. **Supporting Record**
   - Expandable sections for:
     - Client & Business Context
     - Complete Commitment History
     - Complete Risk History
     - Pathway Details (stage, day, current focus, current priorities)
     - Coaching Sessions (last 5)
     - Coaching Observations
     - Extracted Coaching Context (a formatted display of the data passed to the AI Coach)

**Actions available to the advisor:**

- Add Advisor Guidance.
- Generate Client Storyboard.
- View all historical record sections.

The advisor cannot directly edit commitments, risks, observations, or other client data from this screen.

---

### 5. Advisor Guidance

**Workflow:**

1. The advisor types guidance into the "Add Guidance" form on the Client Detail screen and selects a priority (normal or high).
2. PB stores the guidance in the `AdvisorGuidance` table with status `active`.
3. The most recent active guidance is retrieved by `build_coaching_context()` and included in the AI Coach system prompt under "Active Advisor Guidance (High Priority)."
4. The AI Coach is instructed to respect and emphasize the advisor's direction in its coaching.

**What happens after guidance is entered:**

- The guidance appears in the Advisor Guidance history on Client Detail.
- The "Last Advisor Interaction" date updates.
- The next time the client has a coaching session, the AI Coach sees the guidance and can act on it.

**Important note:**

- Advisor Guidance does **not** replace the Pathway. It augments the AI Coach context. The AI Coach still follows the Pathway's current stage, objectives, guardrails, and resources.
- There is no automatic notification to the client when guidance is added. The client notices the guidance through the AI Coach's changed behavior in the next session.

---

### 6. AI Coaching

#### Text Coaching
Text coaching works as follows:

1. The client clicks "Text Coaching" on the client dashboard.
2. PB creates a new `Session` record and an initial AI Coach message.
3. The client and AI Coach exchange messages in a chat screen.
4. When the client clicks "End Session," PB queues the session for background processing.
5. The background process extracts structured outcomes and updates the Coaching Record.

#### Voice Coaching
Voice coaching works as follows:

1. The client clicks "Voice Coaching" on the client dashboard.
2. PB initializes a voice session and returns a signed URL and configuration for the ElevenLabs Conversational AI agent.
3. The client talks with the AI Coach in the browser.
4. When the conversation ends, PB receives the conversation data, normalizes it into messages, and runs the same extraction pipeline as text coaching.
5. The transcript and extracted outcomes are persisted.

#### Context supplied to the Coach
For every coaching interaction, PB builds a context that includes:

- Client and business identity
- Current Pathway, stage, day, focus, and priorities
- Open commitments
- Current risks
- Recent significant events
- Recent learning records
- Active coaching observations
- Active advisor guidance
- Recent session summary

This context is displayed in the "Extracted Coaching Context" section of Client Detail for transparency.

#### Persistent information
The Coaching Record persists across sessions:

- Client and business context
- Pathway state
- Commitments
- Risks
- Significant events
- Learning records
- Coaching observations
- Advisor guidance
- Advisor attention items
- Session messages and summaries

#### Extraction and persistence after interactions
When a session ends, PB:

1. Sends the session transcript and current context to the AI extraction service.
2. Receives structured updates: new commitments, commitment updates, new risks, risk updates, new events, learning updates, new observations, observation updates, new advisor attention items, attention item updates, session summary, and a potential escalation flag.
3. Validates the extraction against the current context and Pathway resources.
4. Applies valid updates to the Coaching Record.
5. Stores a session summary on the `Session` record.

#### Relationship between coaching and Pathway progression
The AI Coach uses the current Pathway state but does not automatically advance the client from one stage to the next. Current stage, day, focus, and priorities are set on the `PathwayState` record. In the current implementation, progression is managed by the system/admin; the AI Coach and client sessions update the Coaching Record but do not themselves move the client to a new stage.

---

### 7. Client Storyboard / Reporting

The Client Storyboard is an on-demand, read-only narrative summary of the client's coaching journey.

**How it is generated:**

1. The advisor clicks "Generate Client Storyboard" on Client Detail.
2. PB gathers a bounded, read-only context: current state, all significant events, open commitments, recent completed commitments, open and recent risks, active and recent observations, recent advisor guidance, open and recent advisor attention items, recent sessions, and recent learning records.
3. The context and a structured Storyboard prompt are sent to the AI service.
4. PB returns the generated narrative to the advisor.

**What the Storyboard represents:**

The Storyboard is a longitudinal advisor briefing with these sections:

1. Starting Situation
2. Key Developments
3. Actions & Commitments (completed, in progress, planned)
4. Advisor & Coaching Support (separates advisor guidance from AI Coach support)
5. Pathway Progress
6. Current Position & Next Focus

**Important rules:**

- The Storyboard does **not** modify any coaching data.
- It does not load full session transcripts; it uses session summaries and other persisted records.
- It is bounded so that it can generate for clients with long histories.
- It may fail if the AI service is unavailable or the completion budget is exhausted.

---

### 8. Helpful Resources and Pathway Tools

#### Helpful Resources
The client dashboard sidebar shows **Helpful Resources**. These are Pathway-approved learning resources matched to the current stage. Each resource has:

- Title
- Duration / type
- Description
- A link to view, if a `location` is configured

If a resource has no `location`, the sidebar shows "Resource link will be available soon." Most current Recovery & Stabilization resources are placeholder and have no live URL.

#### Pathway Tools
Pathway Tools are external tools linked from the Helpful Resources area.

**Small Business Finance Modeler**

- Type: PATHWAY TOOL
- Title: Small Business Finance Modeler
- Description: Explore cash flow, profitability, and financial scenarios for your business.
- Link: `https://financemodeler-08o0.onrender.com/`
- Opens in a new browser tab (`target="_blank"`, `rel="noopener noreferrer"`).
- No data is shared between PB and the Finance Modeler in this phase. The client uses it as a separate application.

---

### 9. Common Advisor Tasks

#### Review a client's current position
1. Log in as an advisor.
2. On the Advisor Dashboard, click "View Details" for the client.
3. Review the Current Coaching Snapshot and Current Status cards.

#### Review recent coaching activity
1. Open the Client Detail screen.
2. Scroll to "Recent Developments" for a reverse-chronological timeline.
3. Expand "Coaching Sessions" in Supporting Record for individual session summaries.

#### Understand current Pathway / Stage
1. On Client Detail, check the "Pathway Progress" card.
2. Expand "Pathway Details" in Supporting Record for the full stage, day, focus, and priorities.

#### Review commitments
1. Use the "Active Work" and "Completed Work" tabs on Client Detail.
2. Expand "Complete Commitment History" in Supporting Record for all commitments.

#### Review risks
1. View "Risks & Watch Items" on Client Detail.
2. Expand "Complete Risk History" in Supporting Record for all risks.

#### Enter advisor guidance
1. Scroll to the "Advisor Guidance" section on Client Detail.
2. Type guidance in the "Add Guidance" form.
3. Select priority (normal or high).
4. Click "Add Guidance."

#### Review progress / history
1. Use the "Recent Developments" timeline.
2. Expand the Supporting Record sections for full history.
3. Use "Generate Client Storyboard" for a narrative summary.

#### Review the Client Storyboard
1. On Client Detail, click "Generate Client Storyboard."
2. PB displays the AI-generated narrative.
3. Click "Back to Client Detail" to return.

---

### 10. Frequently Asked Advisor Questions

**Q: What does Current Focus mean?**
A: Current Focus is a short statement stored on the client's Pathway State. It describes the client's immediate area of work. It is shown on the client dashboard and to the AI Coach so the conversation stays on target.

**Q: Does the AI Coach remember previous conversations?**
A: Yes. Session messages are stored in the `Session` and `SessionMessage` tables. Session summaries, commitments, risks, observations, and other extracted outcomes are stored in the Coaching Record. The next session uses the most recent active records as context.

**Q: Can I give the Coach instructions about a client?**
A: Yes. Use the "Add Guidance" form on Client Detail. Active guidance is included in the AI Coach context and the Coach is instructed to respect it.

**Q: Does advisor guidance replace the Pathway?**
A: No. Advisor Guidance augments the Pathway. The AI Coach still follows the current Pathway stage, objectives, guardrails, and approved resources.

**Q: What is the difference between a commitment and a milestone?**
A: A Commitment is an explicit client action, such as "Call the lender by Friday." It is tracked day to day. Milestones are a concept in the Pathway package but are not currently surfaced in the client or advisor UI.

**Q: Can the client use voice or text coaching?**
A: Yes. The client dashboard has both "Voice Coaching" and "Text Coaching" options. Voice uses the ElevenLabs integration; text is the built-in chat. Both go through the same extraction pipeline after the session ends.

**Q: What information is saved after a coaching interaction?**
A: The session transcript, a session summary, and any extracted commitments, risks, events, learning updates, observations, and advisor attention items are saved. The `processing_status` on the session shows whether extraction is complete.

**Q: What does the Client Storyboard represent?**
A: It is a read-only, narrative summary of the client's coaching journey from the persisted Coaching Record. It is not a new coaching session and does not modify data.

**Q: What can I change as an advisor?**
A: In the current implementation, the main advisor action is to add Advisor Guidance. The advisor cannot directly edit commitments, risks, or other client records from the UI.

**Q: What is the difference between client coaching and advisor functionality?**
A: Clients interact with the AI Coach by text or voice and make progress on commitments. Advisors review client records, see risks and attention items, and add guidance that shapes future coaching.

**Q: What does the "Needs Attention" indicator mean?**
A: It means PB has detected an open high-priority attention item, a high-severity open risk, or more than two overdue commitments. It is a prompt for the advisor to review the client.

---

### 11. Current Limitations / PoC Boundaries

The following are important boundaries of the current build:

- **Single runtime Pathway**: Only PATHWAY-001 — Recovery & Stabilization is active. Other Pathway packages may exist but are not runtime-integrated.
- **Resources are mostly placeholder**: Most approved learning resources have no live URL (`location` is null).
- **No client-side editing of commitments or risks**: Clients and advisors cannot manually update commitments or risks through the UI. Updates come from AI extraction after coaching sessions.
- **Stage progression is not client-driven**: The system does not automatically move a client to the next Pathway stage based on session activity.
- **Voice conversation normalization is a PoC**: The voice service normalizes ElevenLabs conversation data, but the exact format support is described as a placeholder in the implementation.
- **External tools are links only**: The Small Business Finance Modeler opens in a new tab. No data is exchanged with PB.
- **AI service requires API keys**: OpenAI and, for voice, ElevenLabs keys are required. If keys are missing or exhausted, AI coaching, extraction, and Storyboard generation will fail.
- **No notifications or email**: There are no email or push notifications in the current build.
- **No PDF, export, or scheduled reporting**: Storyboards are on-demand and not persisted.
- **Admin features are separate**: User, assignment, domain, component, and Pathway management are admin-only and not described here.
- **Support agent does not exist yet**: This is documentation for a future support agent, not the agent itself.

---

### 12. Support Agent Guardrails

When using this guide, the advisor support agent must follow these boundaries:

- Never claim a feature exists unless it is documented here.
- Never claim an advisor action occurred unless it can be verified in PB.
- Do not invent client information, commitments, risks, or session outcomes.
- Distinguish PB's coaching guidance from business, legal, tax, or professional advice. PB does not provide professional advice.
- Explain current application behavior rather than speculate about future features.
- If the documentation does not answer a question, say that the capability cannot be confirmed from the current build.
- Use the same terminology as the UI: North Star Proficiency Builder, PB, Advisor, Client, AI Coach, Pathway, Coaching Record.
- When describing limitations, clearly state that the functionality is not implemented, is placeholder, or is PoC-only.

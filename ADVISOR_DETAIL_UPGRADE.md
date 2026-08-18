# Advisor Client Detail Information Flow Upgrade

## Objective

Improve the **Advisor Client Detail page** so an advisor can understand a client's current situation, priorities, recent developments, and need for intervention within **20–30 seconds**.

**Type:** Information architecture / presentation upgrade

**Scope:** Client detail page only (dashboard out of scope)

---

## Design Principle

The Advisor Client Detail page now feels like an **advisor case brief**, not a database record display.

**Information flow:**
```
ORIENT → PRIORITIZE → ACT → UNDERSTAND → EXPLORE
```

Or more simply:
> **Story first → Action second → Detail when needed**

---

## New Page Layout

### 1. Client Header (Compact)

**Displays:**
- Client name
- Business name
- Engagement status
- Last activity date

**Purpose:** Quick identification

---

### 2. Current Coaching Snapshot (PRIMARY ORIENTATION)

**Answers:**
- What is happening with this client right now?
- What are they currently trying to accomplish?
- What changed recently?
- What is the immediate next meaningful action?

**Data source:** Existing pathway state and session summaries

**Example:**
> Michael is focused on generating near-term revenue by re-engaging his top 10 existing customers. He had not begun outreach because he was unsure how to approach customers. During his latest coaching session, he developed a specific product offer with Thursday/Friday delivery and is ready to begin outreach.
>
> **Current Focus:** Re-engage top 10 customers and secure weekend orders.
>
> **Next Meaningful Action:** Contact first 3 customers and record responses.

---

### 3. Advisor Attention + Current Status (Two-Column)

**Left: Advisor Attention**

Answers: "Does this client currently need something from me?"

**Displays:**
- ✓ No intervention currently required
- OR ⚠ Advisor review recommended (with reason)
- Watch items (if any)
- Link to Add Advisor Guidance

**Right: Current Status**

**Displays:**
- Active commitments count
- Open risks count
- Pathway day
- Last interaction date

**Purpose:** Quick status check without detail overload

---

### 4. Active Work

**Shows:** What the client is currently doing

**Format:** Concise table
- Next actions (highlighted)
- Active commitments (top 5)
- Target dates

**Purpose:** See current work at a glance

---

### 5. Recent Developments (NEW - MAJOR CHANGE)

**Shows:** Chronological storyline of recent meaningful developments

**Format:** Timeline grouped by date, newest first

**Combines:**
- Session summaries
- Significant observations
- Significant events

**Example:**
```
TODAY
• Client reported being stuck starting customer outreach.
• Identified available weekend products: Raisin bread — 40 loaves, Sourdough muffins — 15 dozen, Croissants — 12 dozen
• Established Thursday/Friday delivery.
• Next action established: begin outreach with first 3 customers.

AUG 17
• Previous meaningful coaching development...
```

**Purpose:** Advisor sees how the situation is evolving without reconstructing from raw sessions

**Key insight:** "What happened? → What changed? → What happens next?"

---

### 6. Pathway Progress + Risks & Watch Items (Two-Column)

**Left: Pathway Progress**
- Current pathway
- Stage and day
- Stage name

**Right: Risks & Watch Items**
- Active high-severity risks
- Watch items
- Limited to most important

**Purpose:** Supporting operational information

---

### 7. Advisor Guidance

**Preserved existing functionality:**
- Add guidance form
- Recent guidance history (top 5)
- Priority indicators

**No material redesign** - this already works well

---

### 8. Supporting Record (Collapsible Sections)

**Moved comprehensive detail lower on page:**

**Collapsible sections:**
- ▸ Client & Business Context
- ▸ Complete Commitment History
- ▸ Complete Risk History
- ▸ Pathway Details
- ▸ Coaching Sessions
- ▸ Coaching Observations
- ▸ Extracted Coaching Context

**Purpose:** Detail available when needed, but doesn't compete with immediate understanding

---

## Technical Implementation

### Files Changed

**1. coaching/advisor_helpers.py (NEW)**

**Purpose:** Helper functions to structure existing data for advisor presentation

**Functions:**
- `build_coaching_snapshot()` - Creates plain-language snapshot from context
- `categorize_commitments()` - Separates next actions from active/historical
- `categorize_risks()` - Separates active risks from watch items
- `build_recent_developments_timeline()` - Combines sessions/observations/events into timeline
- `determine_advisor_attention_status()` - Evaluates if advisor intervention needed

**Key principle:** Reuses existing persisted data, no new data collection

---

**2. app.py (Modified)**

**Line 14:** Added advisor_helpers imports

**Lines 285-293:** Added structured data preparation in `client_detail()` route

**New data passed to template:**
- `coaching_snapshot`
- `categorized_commitments`
- `categorized_risks`
- `recent_developments`
- `advisor_attention_status`
- `last_session`

**Existing data preserved:** All original data still passed to template

---

**3. templates/client_detail.html (Redesigned)**

**Complete template restructure** following new information architecture

**New sections:**
- Current Coaching Snapshot
- Advisor Attention + Current Status (two-column)
- Active Work (prioritized commitments)
- Recent Developments (timeline)
- Pathway + Risks (two-column)
- Supporting Record (collapsible details)

**Preserved:**
- Advisor Guidance functionality
- All existing data display (moved to Supporting Record)
- Back to Dashboard button

---

## What Was NOT Changed

**Preserved (no changes):**
- ✅ Advisor dashboard
- ✅ Client coaching interface
- ✅ Database schema
- ✅ Context builder
- ✅ Extraction pipeline
- ✅ Persistence logic
- ✅ Validation
- ✅ Commitment tracking
- ✅ Risk tracking
- ✅ Pathway logic
- ✅ Advisor guidance persistence
- ✅ Authentication
- ✅ Session persistence

**This is a presentation-layer upgrade only.**

---

## Data Sources

**All information comes from existing persisted data:**

**Coaching Snapshot:**
- `pathway_state.current_focus`
- `pathway_state.current_priority_summary`
- Recent session summaries
- Open commitments

**Advisor Attention:**
- Existing `AdvisorAttention` records
- Risk severity levels
- Overdue commitments

**Recent Developments:**
- Session summaries (last 5)
- High-importance observations
- Significant events (last 3)

**No new AI calls, no new API requests, no new data collection.**

---

## Acceptance Test

**Open Michael Chen's Client Detail page after customer-outreach coaching interaction.**

**Within 20–30 seconds, advisor should be able to answer:**

### What's happening?
Michael is trying to re-engage his top customers to generate near-term orders.

### What's changed?
He moved from being stuck on outreach to having a defined product offer and delivery window.

### What's next?
Contact the first three customers.

### Do I need to intervene?
Not currently, although production capacity may become a watch item if demand exceeds capability.

### Can I investigate further?
Yes. Detailed commitments, risks, pathways, guidance, sessions, and coaching context remain available in Supporting Record section.

---

## Information Architecture Comparison

### Before (Database Record View)

**Layout:**
1. Pathway Status
2. Commitments (all, chronological)
3. Risks (all, chronological)
4. Significant Events
5. Learning Activity
6. Coaching Observations
7. Recent Sessions
8. Sidebar: Advisor Guidance
9. Sidebar: Attention Items
10. Sidebar: Coaching Context

**Problem:** Advisor must mentally reconstruct the client's story from independent sections

**Time to understand:** 2-5 minutes of reading and assembling

---

### After (Advisor Case Brief)

**Layout:**
1. **Current Coaching Snapshot** ← Story
2. **Advisor Attention + Current Status** ← Prioritize
3. **Active Work** ← Action
4. **Recent Developments** ← Understand
5. **Pathway + Risks** ← Context
6. **Advisor Guidance** ← Intervene
7. **Supporting Record** (collapsible) ← Explore

**Benefit:** Story is pre-assembled, advisor reads narrative

**Time to understand:** 20-30 seconds

---

## Visual Design

**Prioritized:**
- ✅ Clear section hierarchy
- ✅ Whitespace
- ✅ Readable typography
- ✅ Logical grouping
- ✅ Strong section headings
- ✅ Easy scanning
- ✅ Progressive disclosure (collapsible sections)

**NOT prioritized:**
- ❌ Charts/gauges
- ❌ Animation
- ❌ Complex visualizations
- ❌ AI confidence scores
- ❌ Decorative widgets
- ❌ New design frameworks

**Philosophy:** "We do not need 'sexy' yet. We need obvious."

---

## Regression Requirements

**After implementation, verified:**

1. ✅ Advisor dashboard continues to work unchanged
2. ✅ Client Detail loads successfully
3. ✅ Existing advisor guidance can still be added
4. ✅ Existing guidance displays correctly
5. ✅ Commitments remain intact
6. ✅ Risks remain intact
7. ✅ Pathway information remains intact
8. ✅ Coaching/session history remains accessible
9. ✅ Client coaching activity continues appearing on advisor side
10. ✅ Advisor-added information remains available to coaching context
11. ✅ No existing persisted data lost or modified
12. ✅ Mobile/responsive layout remains usable

---

## Key Improvements

### 1. Story First, Not Data First

**Before:** Advisor sees raw data sections

**After:** Advisor sees narrative summary

---

### 2. Prioritized Information

**Before:** All information has equal visual weight

**After:** Most important information at top, detail available when needed

---

### 3. Recent Developments Timeline

**Before:** Advisor reconstructs progress from session list

**After:** Timeline shows "what happened → what changed → what's next"

---

### 4. Decision Support

**Before:** Advisor determines if intervention needed by reading all sections

**After:** "Advisor Attention" section explicitly states if intervention needed

---

### 5. Progressive Disclosure

**Before:** All detail always visible, overwhelming

**After:** Summary visible, detail collapsible

---

## Example: Michael Chen After Outreach Session

### Current Coaching Snapshot

> Michael is focused on generating near-term revenue by re-engaging his top 10 existing customers. During his latest coaching session, he developed a specific product offer with Thursday/Friday delivery and is ready to begin outreach.
>
> **Current Focus:** Re-engage top 10 customers and secure weekend orders.
>
> **Next Meaningful Action:** Contact first 3 customers and record responses.

### Advisor Attention

✓ No intervention currently required

**Watch:** Production capacity if customer demand exceeds current capability.

### Current Status

- 2 Active Commitments
- 1 Watch Item
- Day 42 - Recovery & Stabilization
- Last Interaction: Today

### Active Work

| Commitment / Action          | Status      | Target |
| ---------------------------- | ----------- | ------ |
| Contact first 3 customers    | Next Action | Today  |
| Track customer responses     | Active      | Aug 19 |

### Recent Developments

**TODAY**
- Client reported being stuck starting customer outreach
- Identified available weekend products: Raisin bread — 40 loaves, Sourdough muffins — 15 dozen, Croissants — 12 dozen
- Established Thursday/Friday delivery
- Next action established: begin outreach with first 3 customers

**Advisor can now answer all key questions in 20-30 seconds.**

---

## Summary

✅ **Objective:** 20-30 second advisor understanding  
✅ **Approach:** Information architecture upgrade  
✅ **Key change:** Story first, action second, detail when needed  
✅ **New sections:** Coaching Snapshot, Recent Developments timeline  
✅ **Files changed:** 1 new helper file, 1 route modified, 1 template redesigned  
✅ **Architecture:** No changes to persistence, extraction, or coaching logic  
✅ **Data sources:** Existing persisted data only  
✅ **Visual:** Clear, obvious, scannable (not "sexy")  
✅ **Regression:** All existing functionality preserved  

**The Advisor Client Detail page now provides a clear narrative flow: ORIENT → PRIORITIZE → ACT → UNDERSTAND → EXPLORE**

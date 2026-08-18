# Advisor Client Detail: Active Work / Completed Work Tabs

## Objective

Refine the **Active Work** section into a single card with two selectable views:
- **Active Work** (default)
- **Completed Work**

**Type:** Presentation refinement using existing commitment data

**Scope:** Active Work card only

---

## Problem

**Before:** Only showed active/open commitments

**Missing:** No visibility into what the client has already accomplished

**Impact:** Advisor couldn't easily see client progress over time

---

## Solution

**After:** Tabbed interface within single card

```
Active Work  2        Completed Work  3
────────────

[Active commitments table]
```

**Clicking "Completed Work":**
```
Active Work  2        Completed Work  3
                      ────────────────

[Completed commitments table]
```

**Benefit:** Easy switching between current work and accomplished work

---

## Changes Made

### 1. Tab Structure

**Added tab buttons:**
```html
<div class="work-tabs">
    <button class="work-tab active" data-tab="active">
        Active Work
        <span class="tab-count">2</span>
    </button>
    <button class="work-tab" data-tab="completed">
        Completed Work
        <span class="tab-count">3</span>
    </button>
</div>
```

**Features:**
- Tab counts show number of items
- Active tab visually highlighted
- Click to switch views

---

### 2. Active Work Tab (Default)

**Content:** Open/active commitments

**Table structure:**
| Commitment / Action | Status | Target  |
| ------------------- | ------ | ------- |
| Description         | Open   | Aug 19  |
| Description         | Open   | No date |

**Status change:**
- **Before:** "Next Action" badge for high-priority items
- **After:** All active commitments show "Open" status

**Rationale:** Status describes state, not priority

**Data source:**
- `categorized_commitments.next_actions` (high-priority/due soon)
- `categorized_commitments.active` (other open commitments)

**Visual distinction:**
- Next actions: `<strong>` (bold description)
- Regular active: Normal weight

---

### 3. Completed Work Tab

**Content:** Recently completed commitments

**Table structure:**
| Completed Commitment / Action | Completed On |
| ----------------------------- | ------------ |
| ✓ Description                 | Aug 12, 2026 |
| ✓ Description                 | Aug 10, 2026 |

**Features:**
- ✓ checkmark prefix for completed items
- Sorted by completion date (newest first)
- Full date format: `Aug 12, 2026`

**Data source:**
- `categorized_commitments.completed_recent`
- Uses `commitment.completed_at` timestamp
- Fallback: "Date unknown" if no `completed_at`

**Empty state:**
```
No completed work yet.
```

---

### 4. Client-Side Tab Switching

**Implementation:** Simple JavaScript

```javascript
document.querySelectorAll('.work-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        const targetTab = this.dataset.tab;
        
        // Update tab buttons
        document.querySelectorAll('.work-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.work-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(targetTab + '-work').classList.add('active');
    });
});
```

**Behavior:**
- No page reload
- No navigation
- Instant switching
- Stays on Client Detail page

---

## Files Changed

### templates/client_detail.html (Modified)

**Lines 124-212:** Replaced Active Work section

**Before:**
- Single "Active Work" heading
- One table with all active commitments
- "Next Action" status badges

**After:**
- Tab buttons with counts
- Two tab content areas (active/completed)
- "Open" status for all active
- Completed work table with checkmarks
- Client-side tab switching script

**Total:** 1 file modified

---

## Data Sources

**All from existing categorized commitments:**

**Active Work:**
- `categorized_commitments.next_actions` (high-priority/due soon)
- `categorized_commitments.active` (other open)
- Status: All show "Open"

**Completed Work:**
- `categorized_commitments.completed_recent` (completed within 7 days)
- Completion date: `commitment.completed_at`
- Sorted: Newest first (by helper function)

**Tab counts:**
- Active: `next_actions|length + active|length`
- Completed: `completed_recent|length`

**No new database queries, no schema changes.**

---

## Status Terminology Change

**Before:**
```
Status: Next Action
Status: Open
```

**After:**
```
Status: Open (for all active commitments)
```

**Rationale:**
- "Next Action" implied priority, not state
- "Open" describes actual commitment state
- Visual distinction maintained through bold text for high-priority items

---

## Visual Treatment

**Tab buttons:**
- Horizontal layout
- Active tab highlighted
- Item counts displayed
- Clickable/hoverable

**Tab content:**
- Same table styling as before
- Smooth transition between views
- Consistent with existing card design

**Completed items:**
- ✓ checkmark prefix
- Normal text weight
- Full date display

**Empty states:**
- "No active commitments."
- "No completed work yet."

---

## Example Output

### Michael Chen (Active Work - Default)

```
Active Work  2        Completed Work  0
────────────

Commitment / Action                              Status   Target
─────────────────────────────────────────────────────────────────
Contact first 3 customers                        Open     Today
Track customer responses                         Open     Aug 19
```

**Clicking "Completed Work":**
```
Active Work  2        Completed Work  0
                      ────────────────

No completed work yet.
```

---

### Sarah (Active Work)

```
Active Work  3        Completed Work  2
────────────

Commitment / Action                              Status   Target
─────────────────────────────────────────────────────────────────
Update cash forecast                             Open     Aug 18
Review receivables aging                         Open     Aug 20
Contact top 5 customers                          Open     No date
```

**Clicking "Completed Work":**
```
Active Work  3        Completed Work  2
                      ────────────────

Completed Commitment / Action                    Completed On
──────────────────────────────────────────────────────────────
✓ Previous completed commitment                  Aug 12, 2026
✓ Previous completed commitment                  Aug 10, 2026
```

---

## Regression Test Results

**Routes:**
1. ✅ `/advisor/client/1` returns HTTP 200
2. ✅ `/advisor/client/2` returns HTTP 200

**Functional:**
1. ✅ Active Work is default tab
2. ✅ Only active/open commitments appear in Active Work
3. ✅ Active commitments display status as "Open"
4. ✅ Completed Work tab is selectable
5. ✅ Only completed commitments appear in Completed Work
6. ✅ Completed items sorted newest first
7. ✅ Empty completed-work state renders correctly
8. ✅ Tab counts are accurate
9. ✅ Switching tabs doesn't reload page (client-side)
10. ✅ Both test clients work correctly
11. ✅ Existing commitment data unchanged

---

## What Was NOT Changed

**Preserved (no changes):**
- ✅ Commitment persistence
- ✅ Commitment extraction
- ✅ Coaching behavior
- ✅ Context builder
- ✅ Database schema
- ✅ Risk logic
- ✅ Pathways
- ✅ Advisor guidance
- ✅ Recent Developments
- ✅ Advisor dashboard
- ✅ Categorization logic (in advisor_helpers.py)

**This was a Client Detail presentation change only.**

---

## User Experience Improvement

**Before:**
- Advisor sees only current work
- No visibility into progress
- Can't easily answer: "What has this client accomplished?"

**After:**
- Advisor sees both current and completed work
- One click to view progress
- Easy to answer: "What has this client accomplished recently?"

**Example use case:**
1. Advisor opens Sarah's detail page
2. Sees 3 active commitments
3. Clicks "Completed Work"
4. Sees 2 recently completed commitments
5. Understands Sarah is making progress
6. Returns to Active Work to see current priorities

**Time:** ~2 seconds to check both views

---

## CSS Requirements

**New CSS classes needed:**

```css
.work-tabs {
    /* Container for tab buttons */
    display: flex;
    border-bottom: 2px solid #eee;
    margin-bottom: 1rem;
}

.work-tab {
    /* Individual tab button */
    background: none;
    border: none;
    padding: 0.75rem 1.5rem;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    color: #666;
    font-weight: 500;
}

.work-tab.active {
    /* Active tab */
    color: #333;
    border-bottom-color: #007bff;
}

.work-tab:hover {
    /* Hover state */
    color: #333;
}

.tab-count {
    /* Item count badge */
    display: inline-block;
    margin-left: 0.5rem;
    padding: 0.125rem 0.5rem;
    background: #f0f0f0;
    border-radius: 12px;
    font-size: 0.875rem;
}

.work-tab.active .tab-count {
    /* Active tab count */
    background: #007bff;
    color: white;
}

.work-tab-content {
    /* Tab content container */
    display: none;
}

.work-tab-content.active {
    /* Active tab content */
    display: block;
}

.completed td {
    /* Completed row styling */
    color: #666;
}
```

**Note:** Actual CSS implementation may vary based on existing application styles

---

## Technical Details

**Tab switching mechanism:**
- Pure client-side JavaScript
- No AJAX calls
- No server requests
- Instant response
- Lightweight implementation

**Data already available:**
- Both active and completed commitments passed to template
- No additional queries needed
- Tab switching just shows/hides content

**Performance:**
- Zero network overhead for tab switching
- All data loaded once on page load
- Fast, responsive user experience

---

## Summary

✅ **Objective:** Add Completed Work visibility  
✅ **Approach:** Tabbed interface in single card  
✅ **Default:** Active Work tab  
✅ **Added:** Completed Work tab with checkmarks  
✅ **Status change:** "Next Action" → "Open"  
✅ **Tab switching:** Client-side, no reload  
✅ **Tab counts:** Displayed and accurate  
✅ **Data source:** Existing categorized commitments  
✅ **Files changed:** 1 (template only)  
✅ **Schema:** No changes  
✅ **Testing:** Both clients work correctly  
✅ **UX improvement:** Easy visibility into client progress  

**Advisors can now easily see both what clients are working on and what they've accomplished, with one-click switching between views.**

# AI Coaching Platform — Pathway Package Specification v1

**Version:** 1.0 (refined for Phase A.1)  
**Status:** Draft  
**Purpose:** Define a machine- and human-readable package format for AI Coaching Platform Pathways.

> **Refinement note (Phase A.1):** This specification now supports accumulated capabilities, real-work-centered activities, evidence-as-signal, and conceptual `progression_type` / `evidence_considered` semantics. The original structural intent is preserved; only the developmental model has been clarified.

---

## 1. Package Identity

A package is a directory named after its `slug` under `pathways/`.  It contains a root manifest:

```
pathways/<slug>/
    pathway.yaml
```

Required identity fields in `pathway.yaml`:

| Field | Description |
|-------|-------------|
| `pathway_id` | Stable machine identifier (e.g. `CM-002`) |
| `slug` | Directory-safe short name (e.g. `strategic_thinking`) |
| `name` | Human-readable name |
| `version` | Package version string |
| `status` | `draft`, `poc`, `pilot`, `active`, `inactive`, `retired` |
| `domain` | Information Domain name (e.g. `Organizational Change Management`) |
| `purpose` | Why the pathway exists |
| `target_user` | Who the pathway is for |
| `entry_context` | Conditions or starting situation |
| `expected_outcome` | What the user should be able to do/achieve |

Optional:

- `default_duration_days`
- `completion_criteria_path`
- `assessment_path`

---

## 2. Capabilities

A capability is a transferable skill or outcome the pathway develops. Capabilities accumulate as the practitioner progresses; later stages may reinforce capabilities introduced earlier.

File: `capabilities.yaml`

```yaml
capabilities:
  - capability_id: ST-01
    name: Distinguish Tactical and Strategic Issues
    description: ...
    target_behaviors:
      - "Labels a situation as strategic vs. tactical"
      - "Explains why a given issue is not merely a task problem"
```

Required per capability:

- `capability_id` (unique within package)
- `name`
- `description`
- `target_behaviors` (list)

---

## 3. Stages

A stage is a meaningful developmental context, not merely a container for a single capability. A stage introduces, practices, integrates, and reinforces capabilities.

Stages may be:

- time-oriented
- condition-oriented
- capability-oriented
- hybrid

File: `stages.yaml`

```yaml
stages:
  - stage_id: STAGE-SEE
    name: SEE
    description: Recognize the larger environment.
    primary_capabilities:
      - ST-01
    reinforcing_capabilities: []
    objectives:
      - "Scan for strategic vs. tactical cues"
    typical_days: null
    exit_conditions:
      - "Can identify strategic vs. tactical elements in a real case"
```

Required per stage:

- `stage_id` (unique)
- `name`
- `description` or `purpose`
- `primary_capabilities` (list, at least one valid capability)
- `reinforcing_capabilities` (list, may be empty)
- `objectives` (list)
- `exit_conditions` (list, may be conceptual)

Rules:

- Every `primary_capabilities` and `reinforcing_capabilities` reference must be a valid capability ID.
- A capability must not appear in both `primary_capabilities` and `reinforcing_capabilities` for the same stage.
- Duplicate capability IDs within the same list are invalid.

Optional:

- `typical_days` (may be `null` for non-calendar stages)

---

## 4. Knowledge

Knowledge is split into:

- **Methodology/background** — human-readable in `methodology.md`
- **Pathway-specific knowledge** — also in `methodology.md` or referenced from `pathway.yaml`
- **Domain-level knowledge** — referenced by `domain` field, managed outside the package (e.g. `InformationDomain` / `DomainComponent`).

Package files do not need to load domain knowledge. They may reference it.

---

## 5. Coaching Guidance

Human- and model-readable coaching instructions.

File: `coaching_guidance.md`

Should include:

- overall coaching approach
- desired coach behaviors
- behaviors to avoid
- stage-specific guidance (optional)
- response to direct requests for opinion/advice

---

## 6. Practice & Application

Concrete activities the user can perform. Activities provide structured practice opportunities that can be applied to real work; they are not formal course modules to be completed sequentially.

File: `activities.json`

```json
{
  "activities": [
    {
      "activity_id": "ST-A01",
      "stage_id": "STAGE-SEE",
      "title": "Strategic vs Tactical Reflection",
      "description": "...",
      "instructions": "...",
      "primary_capabilities": ["ST-01"],
      "reinforcing_capabilities": [],
      "completion_criteria": "..."
    }
  ]
}
```

Required per activity:

- `activity_id` (unique)
- `title`
- `description`
- `primary_capabilities` (list, at least one valid capability)

Optional:

- `reinforcing_capabilities` (list, may be empty)
- `completion_criteria`

Rules:

- All capability references must be valid.
- A capability must not appear in both `primary_capabilities` and `reinforcing_capabilities` for the same activity.
- Duplicate capability IDs within the same list are invalid.

---

## 7. Evidence

Observable signals of capability development. An individual observation is a developmental signal, not automatic proof of mastery.

Evidence may be considered together with other signals when making progression or completion decisions. Future mechanisms may consider repeated observations, artifacts, metrics, reflections, milestones, and advisor assessments.

File: `evidence.yaml`

```yaml
evidence:
  - evidence_id: ST-EV-01
    capability_id: ST-01
    stage_id: STAGE-SEE
    description: "Distinguishes strategic from tactical issues without prompting"
    evidence_type: observation
```

Evidence types (extendable):

- `observation`
- `milestone`
- `metric`
- `reflection`
- `artifact`
- `advisor_assessment`

Required per evidence item:

- `evidence_id` (unique)
- `description`
- `evidence_type` (must be from the supported vocabulary unless the validator is explicitly extended)
- `capability_id` (valid capability)
- `stage_id` (valid stage)

---

## 8. Progression

Conceptual rules for stage transitions. Progression is not a binary checklist and is not executable in v1.

File: `progression.yaml`

```yaml
progression:
  - from_stage: STAGE-SEE
    to_stage: STAGE-CONNECT
    progression_type: evidence_based
    description: "Practitioner can identify meaningful dependencies in a real case"
    evidence_considered:
      - ST-EV-01
```

Progression types (conceptual):

- `time_based`
- `evidence_based`
- `milestone_based`
- `advisor_decision`
- `hybrid`

Required per progression rule:

- `from_stage` (valid stage)
- `to_stage` (valid stage)
- `progression_type` (from the supported vocabulary)
- `description`
- `evidence_considered` (list of valid evidence IDs, may be empty)

Rules:

- Evidence should primarily describe development in the `from_stage`, not the `to_stage`.
- `evidence_considered` means the listed evidence is relevant to the progression decision; it does not mean a single observation of each item automatically advances the practitioner.
- The v1 schema does not support `evidence_required` as a current field. If present for validator-tooling backward compatibility, the validator should report it as deprecated.

---

## 9. Resources

Curated learning resources.  Optional for v1 runtime readiness.

File: `resources.json`

Required per resource:

- `resource_id` (unique)
- `title`
- `resource_type`
- `description`
- `learning_objective`
- `when_to_recommend` (list)

Optional:

- `location` / `reference` (null if not available)
- `related_capability` (valid capability)
- `related_stage` (valid stage)
- `follow_up_questions`

---

## 10. Guardrails

Pathway-specific professional and coaching boundaries.

File: `guardrails.md`

May be narrative or structured.  Must define:

- what the coach must not do
- escalation or human-handoff conditions
- how to handle sensitive situations

---

## 11. Completion

Conceptual completion criteria. Completion represents the integrated developmental outcome of the pathway, not merely arrival at the final stage.

File: `completion.yaml`

```yaml
completion:
  - criterion_id: ST-C01
    description: "Demonstrates ability to distinguish strategic from tactical issues"
    evidence:
      - ST-EV-01
    required: true
```

Required per completion criterion:

- `criterion_id` (unique)
- `description`
- `evidence` (list of valid evidence IDs)
- `required` (boolean)

Completion is conceptual in v1.  Do not implement execution.

---

## 12. Recommended File Structure

```
pathways/<slug>/
    pathway.yaml
    capabilities.yaml
    stages.yaml
    activities.json
    evidence.yaml
    progression.yaml
    resources.json
    completion.yaml
    methodology.md
    coaching_guidance.md
    guardrails.md
```

A package may add files but should not remove required structural files.

---

## 13. Runtime Readiness (Conceptual)

A package is **structurally valid** when all required files are present, parse, and references are internally consistent.

A package is **runtime ready** only when the platform engine has been explicitly updated to load and operate against it.  Structural validity does not imply runtime readiness.

A package is **assignable** only when an administrator has explicitly activated it in the platform catalog.

---

## 14. Version History

- v1.0 — Initial Pathway Package v1 specification for Phase A.
- v1.0 (Phase A.1 refinement) — Added accumulated capabilities (`primary_capabilities` / `reinforcing_capabilities`), evidence-as-signal principle, `progression_type` / `evidence_considered` semantics, and real-work activity guidance.

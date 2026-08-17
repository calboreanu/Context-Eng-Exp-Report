# Evidence Codebook

Version: `2.2.0-pilot`

## Context-engineering interaction gate

The multi-station post-run screen uses one primary user-level task invocation plus its downstream agent trajectory as the interaction unit. A human may code `include_context_engineering` only when product purpose, a deliberate context operation, a context-use trace, and an observable product action or evidence-grounded decision are all present. The full operational rule, automated routing labels, and examples are versioned in `docs/CONTEXT_ENGINEERING_ELIGIBILITY.md` and `config/context-engineering-eligibility.json`.

Automated `candidate_strong` and `candidate_probable` labels prioritize review; they never establish inclusion. Scheduled automation runs are executions, not independent prompt designs. Compaction summaries, continuation wrappers, tool-generated messages, and delegated-agent prompts are not separate primary interactions.

Human context-engineering decisions use `include_context_engineering`, `exclude_product_without_context_engineering`, `exclude_non_product`, `exclude_publication`, `exclude_no_observable_action`, `exclude_duplicate_or_nonhuman`, or `uncertain`. Reviewers separately record product purpose, context operation, use trace, observable action, and the primary context mode.

## Interaction evidence status

`interaction_evidence_status` records what kind of evidence establishes an event, orthogonally to the include/exclude decision (ruling CD-001, `docs/CODING_DECISIONS.md`):

| Value | Meaning |
|---|---|
| `trajectory_observed` | The primary invocation and its downstream agent trajectory are archived in a frozen source; the four eligibility gates are evaluable. |
| `artifact_corroborated_event_only` | The event's occurrence and outcome are proven by independent artifacts, but the operator–AI trajectory is not archived. The four-gate interaction test cannot pass — context operation and use trace (gates 2–3) are unavailable without the trajectory — while artifacts may independently establish the product event and outcome (gates 1 and 4). |
| `claim_only` | The event is asserted in narration, summaries, or claims, with neither an archived trajectory nor independent artifact corroboration; per rules 1 and 8 it supports no analytical use. |
| `uncertain` | Evidence status not yet determined; blocks promotion until resolved. |

Only `trajectory_observed` records may enter the interaction denominator or the context-engineering interaction count. An `artifact_corroborated_event_only` record may enter a clearly labeled artifact-event analysis after human review; it never enters the interaction denominator or the context-engineering interaction count.

## Automated candidate fields

These fields are produced by code and contain no semantic human judgment.

| Field | Rule |
|---|---|
| `event_id` | Stable token from frozen source, line, content index, tool-use token, and artifact token |
| `source_ref` | Content-addressed token tied to a full SHA-256 receipt |
| `source_line`, `content_index` | Direct locator within the frozen JSONL source |
| `record_ref`, `tool_use_ref`, `parent_tool_use_ref` | Hashed source identifiers; raw IDs are not released |
| `action_type` | Tool-name mapping: `create`, `modify`, `read`, `search`, `execute`, `delegate`, or `other` |
| `target_scope` | `direct_path`, `command_only`, `delegation`, `indirect_match`, or `outside_direct_target` |
| `automated_eligibility` | `candidate_direct`, `candidate_indirect`, `excluded_by_rule`, or `excluded_outside_direct_target` |
| `review_status` | Must remain `unreviewed` until the event enters a human review packet |
| `timestamp_status`, `cutoff_id` | Whether a timestamp was observed and which frozen cutoff governs the record |

`candidate_direct` means only that an approved private scope term appeared in the direct tool target. It does not establish product purpose, successful execution, artifact change, lifecycle stage, or inclusion.

## Prompt-segment candidate fields

| Field | Rule |
|---|---|
| `segment_id`, `prompt_ref` | Stable hashes of the content-addressed source, turn, and prompt bytes; raw text stays private |
| `source_line_start`, `source_line_end` | Restricted-source replay locator for the whole segment |
| `rule_stage_candidate`, `stage_signal_mask` | High-recall lexical candidates; no semantic decision |
| `continuation_wrapper_candidate` | Assistant context-restoration wrapper; never a fresh lifecycle instruction |
| `publication_exclusion_candidate` | Possible manuscript/publication-purpose material requiring scope confirmation |
| `non_mutating_request_candidate` | Read-only/research wording that cautions against interpreting tool context as implementation |
| `analysis_scope_candidate` | Automated routing flag only; human scope decision remains blank |

Relationship `candidate_confidence` describes the strength of the deterministic link rule, not confidence that a lifecycle transition occurred. `low` means same-session or planned ordering; `moderate` means explicit restart or shared artifact; `high` means restart plus shared artifact. Every level still requires human review.

## Human adjudication fields

| Field | Controlled values or rule |
|---|---|
| `reviewer_*_id` | Pseudonymous accountable human reviewer ID; an LLM or automated script is not a reviewer |
| `reviewer_*_eligibility` | `include`, `exclude_non_product`, `exclude_no_observable_action`, `exclude_duplicate`, `exclude_unsafe`, `uncertain` |
| `reviewer_*_evidence_status` | `trajectory_observed`, `artifact_corroborated_event_only`, `claim_only`, `uncertain` |
| `reviewer_*_lifecycle_stage` | `requirements`, `context`, `design`, `implementation`, `audit`, `remediation`, `verification`, `packaging`, `release`, `not_applicable`, `uncertain` |
| `reviewer_*_artifact_class` | `source`, `configuration`, `test`, `requirements`, `standard`, `operational_document`, `interface`, `courseware`, `package`, `audit_record`, `other`, `not_applicable`, `uncertain` |
| `agreement_status` | `agree`, `disagree`, `not_double_coded` |
| `adjudicator_id` | Required when reviewers disagree |
| `adjudicated_*` | Final code after preserving both original decisions |
| `review_status` | `pending`, `reviewed_once`, `double_coded`, `adjudicated` |

## Analysis-ready event fields

| Field | Controlled values or rule |
|---|---|
| `event_id` | Must exist in the candidate table unless the source class is non-assistant evidence |
| `case_id` | `P##` for outcome cases; `I##` for infrastructure |
| `source_id`, `source_ref` | Must resolve to the registries and receipts |
| `timestamp_utc` | ISO 8601 UTC; blank only with explicit missingness reason |
| `lifecycle_stage` | Human-adjudicated controlled value |
| `action_type` | Preserved automated tool category or human-coded non-tool action |
| `artifact_class` | Human-adjudicated controlled value |
| `interaction_evidence_status` | `trajectory_observed`, `artifact_corroborated_event_only`, `claim_only`, `uncertain`; only `trajectory_observed` feeds interaction denominators |
| `context_condition` | `CE_NATIVE`, `RETROSPECTIVE_CE`, `CONVENTIONAL`, `HYBRID`, `UNCLASSIFIED` |
| `evidence_tier` | `A`, `B`, or `C` after evidence inspection |
| `verification_status` | `not_applicable`, `unverified`, `verified`, `contradicted` |
| `reviewer_id` | Required accountable human reviewer |
| `adjudication_status` | `single_coded`, `double_coded_agreement`, `adjudicated` |

## Coding rules

1. Code observable actions, not assistant narration, plans, or claims.
2. Read the frozen source at the recorded locator and, when needed, inspect the private target mapping.
3. Include only product-purpose events. Manuscript, preprint, peer-review, citation, response-letter, and publication-package work is excluded.
4. A shell command or delegated-agent call is not included merely because its input mentions an approved root. Establish the actual product action.
5. Repeated reads/searches are separate only when timestamped, non-duplicate, and analytically relevant.
6. Split an audit record into findings only when each condition is distinct and testable.
7. Preserve failed fixes, reopened findings, and contradictions.
8. Never convert “clean,” readiness scores, issue totals, or iteration claims into results without recomputation or triangulation.
9. Do not infer a context condition from the case label; locate the pre-build context artifact and time.
10. When evidence conflicts, retain both records and adjudicate transparently.
11. Code the current instruction, not lifecycle words quoted inside a continuation summary, file title, dependency name, or pasted source.
12. A same-session sequence is not automatically one iteration; confirm common product purpose, artifact continuity, and an observable action.
13. A re-audit requires explicit restart language or artifact continuity. Do not infer it from two audit-like prompts merely occurring in time order.
14. An event proven by artifacts but lacking its operator–AI trajectory is `artifact_corroborated_event_only`. Code it from the artifacts alone; do not reconstruct or infer the missing trajectory. It may support a labeled artifact-event analysis after human review, never the interaction denominator or context-engineering interaction count (CD-001).

## Minimum promotion gate

A candidate may enter `data/processed/events.csv` only after human review establishes product purpose, lifecycle stage, artifact class, evidence tier A–C, interaction evidence status, and an explicit final decision. The row must retain its source locator, reviewer ID, and adjudication status. Tier D and automated-only records never enter the analytical event table. Interaction denominators and context-engineering interaction counts draw exclusively from `trajectory_observed` rows; `artifact_corroborated_event_only` rows are limited to clearly labeled artifact-event analyses, and `claim_only` rows never enter any analytical table.

## Coding decisions log

Boundary rulings that bind future coding are versioned in `docs/CODING_DECISIONS.md`, starting with CD-001 (publication episodes reporting product evidence; artifact-proven events without trajectories).

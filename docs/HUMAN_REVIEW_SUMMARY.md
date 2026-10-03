# Historical author check and subsequent technical correction

On 18 September 2026, the author reported reviewing all 46 selected event-v3 cases and finding their classifications accurate. No inaccuracies or corrections were reported at that time. That original report and its frozen packet remain unchanged. A subsequent source-based technical audit identified scope/frontloading defects and an incidental-word requested-stage discrepancy. Those later findings are recorded separately, not retrospectively attributed to the author as new human ratings.

## Selection and evidence

The event-v3 protocol and input were frozen before the draw. One event was selected from each nonempty condition × station × canonical-provider cell of that pre-correction primary sample: 23 per condition, 12 stations and three provider formats. Selection used seed 20260918 after sorting cells and event tokens; presentation used seed 20260920. Inclusion probabilities were 1/N within each cell and therefore unequal. No case was replaced because of its outcome or review difficulty.

The private packet supplied retained source intervals and additional attributable call/result records, source receipts and visible machine classifications. Its nine-criterion instrument covered origin/scope, substantive action, context operation, context availability before action, substantive context use, frontloading, verification, requested stages and grounded-decision evidence. The stage-set field covers the separate stage indicators. Preparation and source-integrity checks are distinct from the author's actual review.

## Result and recording boundary

The historical reported result is **46 reviewed cases collectively confirmed, with zero inaccuracies reported at the time**. It was received as one collective author statement applying to the frozen set. It was not received as 414 separately completed criterion-form responses; those individual responses and per-criterion error rates are not fabricated from the collective statement. The original blank form remains part of the preserved preparation record, with the subsequent confirmation recorded separately. The later audit findings qualify the corroboration; the historical confirmation does not validate every label in the corrected and rematched analysis.

This was an author-involved, unblinded coverage check with machine labels visible. It is not an independent reference study, inter-rater reliability estimate or population-accuracy estimate. It does not establish sensitivity in excluded routes, adjudicate the separate context-linkage pilot, authenticate distinct practitioners or validate causal effectiveness or product quality. The pre-existing operational review of project deliverables is separate evidence and is not pooled into this denominator.

The machine-readable [aggregate summary](../data/validation/author_review_summary.json) contains the counts, design, recording limits and integrity receipts. Source content, event identities, individual evidence links, the original communication and the detailed private review packet remain confidential. The public tests check aggregate accounting and claim boundaries; they cannot independently verify that a human performed the reported review.

## Correspondence with event-v5

The separate [boundary-correction summary](../analysis/results/boundary_correction_summary.json) computationally maps all 46 historical cases to 46 distinct resolved v5 events. Of those, 39 remain in the current primary sample: **35 retain the same tracked trajectory, source measurements and derived labels, and four change on those dimensions**. Seven are no longer in the current primary sample. None is held unresolved. This is a reporting clarification under `context-engineering-correspondence/1.1.0`, not a new analytical version or human review.

The original equality predicate also required the provenance-status string to match exactly. Nine continuing cases change only from `v2_codex_unchanged` to `resolved`: their native identities, source-alias memberships, tracked measurements and derived labels are identical. They are not alias/trajectory changes or newly discovered classification errors. The former 26/13 continuing-case and 28/18 whole-set splits are retained under explicitly named **strict status-inclusive** fields, not measurement-change fields.

| Mutually exclusive comparison category | All 46 historical cases | Of the 39 continuing primary cases |
| --- | ---: | ---: |
| Strictly unchanged, including status text | 28 | 26 |
| Provenance-status-only transition | 9 | 9 |
| Source-measurement change without derived-label change | 3 | 3 |
| Derived-label change | 6 | 1 |

Thus 37/46 retain the same tracked measurements, alias membership and derived labels, while nine change on at least one of those dimensions. Among the continuing 39, three change source measurements without changing the eight derived fields and one changes a derived label. Restricting comparison to the narrower balanced-row export would overlook those three source-measurement changes. Two historical boundaries are absorbed into supported owners and three alias memberships expand across all 46; these overlapping counts are not additional cases or human error rates. Primary membership can change through balancing as well as corrected eligibility, so membership change alone does not establish a historical labeling error.

### Consistent full-primary definition

The same definition is applied to all 946 historical v3 primary records, not just the reviewed subset. Across those records, 677 retain the same tracked measurements, alias membership and derived labels and 269 change; the strict status-inclusive split is 479/467, with 198 status-only transitions. Among the 776 historical records that still map into the current primary sample, the substantive split is 629/147 and the strict split is 432/344, with 197 status-only transitions. Those 776 historical memberships reach 774 distinct current events; they are not 776 independently distinct current events. A further 169 historical records are outside the current primary set and one is held. Current primary membership remains 858 events, or 429 per condition.

Every observed status-only transition in this full comparison is `v2_codex_unchanged` to `resolved`, with the same native identity and alias membership, no absorbed boundary and no held/resolved eligibility transition. The definition separates status text from tracked evidence; it does not assume that any arbitrary unseen status transition would be harmless.

### Exact tracked-field definition

Substantive equality requires unchanged source-alias membership, all 15 tracked source fields and all eight derived fields. The source fields are `origin_candidate`, `automated_disposition`, `context_trace_status`, `product_action_trace_status`, `publication_exclusion_candidate`, `attachment_count`, `prompt_artifact_reference_count`, `context_mode_mask`, `stage_signal_mask`, `completed_substantive_action_calls`, `grounded_decision_trace`, `timestamp_start_utc`, `timestamp_end_utc`, `tool_trace_json` and `prompt_text`. These are field definitions only; their row-level contents are not released.

The derived fields are `frontloaded_context_candidate`, `verification_successful`, `audit_signal`, `remediation_signal`, `packaging_release_signal`, `multistage_signal`, `grounded_decision_trace` and `completed_substantive_actions`. Strict status-inclusive equality additionally requires exact provenance-status text equality. `correspondence_change_flags` in the public verifier expresses this distinction using change flags; it does not reconstruct confidential observations. Mutually exclusive change-category accounting prioritizes a derived-label change, then a source-measurement change, then an alias-only change, then a status-only transition, then strict equality. Held status, current membership, condition switches and absorbed boundaries remain separately reported.

Membership overlap is not a repeat review, does not establish that changed classifications were human-confirmed, and does not change the historical 46-case denominator. No new human labels are added by this reconciliation.

Issued v2.0.0 remains preserved with the original status-inclusive reporting. Package v2.1.0 corrects the correspondence interpretation without changing its empirical results or the historical author statement. The author's machine-readable `release_status` remains the preparation-state value recorded on 18 September 2026, not the live distribution status; see the [README](../README.md). Public distribution, journal submission and editorial acceptance are separate from the recorded review.

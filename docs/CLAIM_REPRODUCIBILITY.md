# Claim reproducibility boundary

Public package v2.0.0 carries the corrected event-v5 evidence under analytical
contract `5.0.0`. Historical public v1.0.0 does not contain these corrected
results. The table describes what this aggregate package supports, independently
of the publication and downloaded-archive gates in the [release checklist](RELEASE_CHECKLIST.md).

| Claim IDs and headline quantities | Checkable from the aggregate package | Requires authorized restricted evidence |
| --- | --- | --- |
| CE-C01: source-frame and archive counts | Read aggregate accounting and bind input/source receipts across files | Reconstruct extraction, identity, ownership and retained-source counts |
| CE-C02: primary and unrestricted sample sizes | Reconcile sample totals across public summaries | Reconstruct eligibility and deterministic row selection/balancing |
| CE-C03–C04: process-signal and verification rates | Recompute contrasts and recover binary positive counts from full-precision rates and observed denominators | Establish each underlying route, stage and completed-call label |
| CE-C05: equal-station effects and intervals | Recompute means/ratios and seeded bootstrap intervals from public station effects | Reconstruct station inputs from event records |
| CE-C06–C08: action-count diagnostics | Recompute bin rates, comparison weights and standardized gaps from public strata | Reconstruct action counts and membership of the underlying rows |
| CE-C09: elapsed-time and minutes/action summaries | Check reported denominators, aggregate contrasts and station sensitivity | Recompute medians from recorded timestamps and action counts |
| CE-C10: candidate-linkage totals and window rates | Recompute totals, fractions and window consistency | Reconstruct individual predecessor links; semantic inheritance remains unadjudicated |
| CE-C11: ST02 zero-copy source limitation | Inspect the public collection-receipt summary | Verify the original collection record; no uncopied source bytes are available |
| CE-C12: measurement and interpretation limits | Inspect the cited contract section and limitation text | No empirical validation is claimed by this documentary check |

Exact files, fields and record selectors are in
[claim_to_evidence.csv](../data/provenance/claim_to_evidence.csv), with executable
selectors in [claim_selectors.json](../data/provenance/claim_selectors.json).
The `claim_status` values describe the evidence boundary: `aggregate_checkable`,
`aggregate_recomputable`, `bounded_aggregate`, `receipt_backed_scope`,
`receipt_backed_limitation` and `interpretation_boundary`. They are not a verdict
that a manuscript sentence, confidential observation or human label is correct.

Selector PASS establishes that the promised records and fields resolve. The
separate aggregate verifier checks supported arithmetic. Manuscript-to-file
comparison and private-source verification are separate checks; a receipt alone
establishes neither semantic correctness nor human validation. Internal QA using
restricted records is documented as such, not presented as independently
reproducible from this package.

The current classifier diagnostics contain no uncoded practitioner estimates
standing in for the removed historical success/iteration comparisons. Those
withdrawn estimates are not pooled with the corrected analysis. Restricted access
is not promised on ordinary request: it requires separate authorization and
controlled-access terms. No release of prompts, responses, supplied context,
row-level samples, exact timestamps, locators or detailed human-review materials
is implied.

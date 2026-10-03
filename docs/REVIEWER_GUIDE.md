# Reviewer guide

**Package v2.1.0:** the primary and unrestricted statistical evidence below remains that of public
v2.0.0. This successor additionally clarifies historical-case correspondence by
separating provenance-status-only changes from substantive tracked changes and
includes the documentary adjunct and pilot adjacency correction. These additions are not in issued v2.0.0;
see [the review summary](HUMAN_REVIEW_SUMMARY.md) and [README](../README.md).

The unchanged primary and unrestricted statistical evidence was issued in **public package v2.0.0 for corrected event-v5 evidence**, dated 19 September 2026. Its public version is distinct from analytical contract `5.0.0` and the journal's revision status. The numerical examples below describe the corrected v5 input; the [pre-release audit record](LOCAL_CANDIDATE_AUDIT.md) identifies the 18 September checks and their scope, while the [release checklist](RELEASE_CHECKLIST.md) tracks successor-package and downloaded-release checks. Identify the input using `analysis_contract` and `input.sha256` in `analysis/results/analysis_summary.json` and reconcile all outputs and receipts to that version. See [the action/reference correction](CLASSIFICATION_CORRECTION.md) and [native-event reconstruction](EVENT_NORMALIZATION.md). The author reported checking all 46 frozen event-v3 cases with no inaccuracies reported at that time. The later technical findings qualify that corroboration; [the review summary](HUMAN_REVIEW_SUMMARY.md) preserves both records and their limits. The historical confirmation does not validate a rematched v5 sample. Frozen preparation-status fields are explained in the [README](../README.md).

This repository is designed to answer two different review questions without blurring them:

1. **Can the public numerical claims be checked?** The public package supports executable checks of aggregate arithmetic, station sensitivities, claim selectors, transformation mappings and exact distributed bytes. These checks independently recompute what the aggregates permit; they do not independently verify the confidential observations from which those aggregates were derived.
2. **Can the empirical input be regenerated from this repository alone?** No. Prompts, responses, supplied context, native message identities, tool traces, exact timestamps, paths, row-level samples and linkage records remain restricted. Published code and integrity receipts document their boundary without publishing their content.

## Five-minute audit

From a fresh clone with CPython 3.12 or later:

```sh
python3 scripts/run_reviewer_audit.py
```

A clean result means the entry point has rebuilt the catalog without a byte change, checked public aggregate arithmetic and the disclosure boundary, validated manifested bytes, run the release tests, and exercised the published analysis path with generated fictional inputs. The fictional records are software-test fixtures, not study data or human validation. Do not treat a successful fictional-input test as reconstruction of the restricted corpus. The audit must fail on stale or inconsistent release receipts rather than silently bless a mixture of versions.

## First distinguish occurrences, events and selected trajectories

The retained-source audit counted 39,830 text-bearing prompt occurrences under the provider recognition rules. Excluding 7,911 occurrences in delegated/subagent source files leaves 31,919 source-local extracted segments. These are not 31,919 independent human tasks: a replay, saved-history copy or alternate capture representation can record the same invocation again.

Event-v5 retains corroborated native-identity and uniquely owned machine-notification/bare-continuation reconciliation, and corrects task-list action and numeric-reference classifications before analytical selection. Matching wording alone is not a deduplication rule. Canonical representation is not selected by success or action count; attributable work is reconciled across retained representations, and unresolved ownership or order is held explicitly. Original segments and source aliases remain traceable in restricted mappings. This computational repair does not identify unique people or prove semantic classifier accuracy.

The v5 resolved frame contains 20,682 trajectories, with 283 events held separately. The primary construction balances 429 observations per condition and the unrestricted construction 1,227, each across 12 contributing stations. The 4,677 canonical resolved source references are not counts of distinct people or all contributing alias files. There are 4,760 contributing alias sources: all 83 additional sources contribute a resolved alias represented canonically elsewhere, 13 also contribute held aliases, one is a canonical held source, and 82 have no canonical role. Those overlapping roles are not missing files; see `source_accounting` in `analysis/results/action_reference_correction_summary.json`.

Read the v5 frame and sample counts from the following fields of `analysis/results/analysis_summary.json`:

- `analysis_contract` and `input.sha256`: verify the event-v5 contract and the input receipt before using any result.
- `scope.source_episode_rows`: resolved rows supplied to the analysis after event normalization, not the preceding 31,919-segment extraction count.
- `scope.source_conversation_count`: distinct canonical source references represented by those rows, not every alias file or distinct human conversation.
- `scope.action_eligible_ce_candidates`, `scope.action_eligible_frontloaded_ce_candidates` and `scope.action_eligible_routed_comparisons`: the rule-defined candidate pools.
- `scope.primary_frontloaded_balanced_per_condition` and `scope.unrestricted_balanced_per_condition`: the two balanced per-condition sample sizes.
- `scope.primary_contributing_stations` and `scope.unrestricted_contributing_stations`: coverage for each construction, not numbers of participants.

The previously described missing ST02 source was a zero-copy, post-cutoff exclusion: its receipt records 659 post-cutoff records and no copied records, bytes or hash. It was not evidence of a lost eligible source. The documented collection-selection and missing-timestamp exclusions are separate limitations; matching all copied bytes does not establish complete capture of workstation activity.

## Reconcile the six reported process signals

Use `analysis/results/pooled_summary.csv`, selecting `analysis_set=primary_frontloaded` and the metric below. Each selected record supplies `ce_value`, `comparison_value`, `effect`, `rows_per_condition`, `ce_observed` and `comparison_observed`. For binary measures, verify the actual observed denominators before recovering positive counts from full-precision rates. The catalog exposes exact k/n convenience fields under `view=pooled`; reconcile them with the canonical CSV rather than rounded manuscript percentages.

Stage matching uses the primary request with mechanically identifiable Git commit/tag message-argument values masked. Ordinary quotations, code fences and genuine command language are not generally removed. The indicators remain lexical process proxies, not proof that a stage was genuinely requested or successfully executed. XML element syntax and bare dot-number tokens are excluded from path-reference counts while actual path-bearing values, dotfiles and qualified paths remain available. Exact supported TodoWrite aliases are administrative; genuine file writes remain substantive under the existing completion rule. Context-condition and stage vocabulary still overlap; [the correction discussion](CLASSIFICATION_CORRECTION.md) gives examples and actual selected-exposure limits.

The publication-purpose filter excludes records matching its frozen rules, not
every semantically publication-related task. Purpose visible only outside the
primary request without a supported native governing-task link may be missed.
Correctly merging a continuation does not resolve that semantic scope limitation.

| Reported measure | Exact `metric` selector |
|---|---|
| Completed-successful verification call | `verification_successful` |
| Audit-stage prompt signal | `audit_signal` |
| Remediation-stage prompt signal | `remediation_signal` |
| Packaging/release-stage prompt signal | `packaging_release_signal` |
| At least two distinct stage prompt signals | `multistage_signal` |
| Grounded-decision trace proxy | `grounded_decision_trace` |

The following v5 pooled values use the primary construction. Differences are calculated from full-precision values, not by subtracting rounded percentages.

| Measure | Context-operation condition | Routed comparison | Difference |
|---|---:|---:|---:|
| Completed-successful verification | 200/429 (46.6%) | 165/429 (38.5%) | +8.2 pp |
| Audit-stage prompt signal | 206/429 (48.0%) | 52/429 (12.1%) | +35.9 pp |
| Remediation-stage prompt signal | 135/429 (31.5%) | 34/429 (7.9%) | +23.5 pp |
| Packaging/release prompt signal | 76/429 (17.7%) | 6/429 (1.4%) | +16.3 pp |
| Distinct multistage signal | 234/429 (54.5%) | 12/429 (2.8%) | +51.7 pp |
| Grounded-decision trace proxy | 267/429 (62.2%) | 33/429 (7.7%) | +54.5 pp |

Use the same metric selectors with `analysis_set=unrestricted` for the unrestricted sensitivity. Equal-station estimates are in `analysis/results/equal_station_summary.csv`; they are not the pooled difference. Their `stations` field is the number contributing to that estimate, and their intervals describe archive sensitivity, not population inference.

For the action-count diagnostic, select `analysis_set=primary_frontloaded` or `unrestricted` with `archive_batch=all` in `analysis/results/action_count_verification_strata.csv` and the `summaries` array of `analysis/results/action_count_verification_summary.json`. The additional later-batch diagnostic uses `analysis_set=primary_frontloaded` with `archive_batch=subsequent_capture_ST04_ST13`; an initial-batch standardized diagnostic is not emitted. Raw archive-batch contrasts are instead in `analysis/results/archive_group_summary.csv`, selected by `analysis_set`, `archive_group` and `metric`. The action-count standardization is post hoc and descriptive, not confounding adjustment: action count includes verification calls and is post-exposure.

The primary raw verification gap is +8.2 points, while the comparator-weighted action-count diagnostic is +0.4 points (−1.0 unrestricted). In the later primary batch, with 79 observations per condition, the standardized diagnostic is +7.3 points against a raw +11.4-point gap. Primary equal-station verification is +9.1 points with a station-resampling interval of −16.4 to +32.6. These different summaries do not establish a method effect or uniform station benefit; the standardization remains a descriptive post-exposure diagnostic.

### Timing has its own evaluable denominator

For `duration_min` and `min_per_action`, use `ce_observed` and `comparison_observed` for the finite observations supporting each pooled, station or archive-batch median. Do not substitute the balanced `rows_per_condition` or `balanced_per_condition` count when timing is missing. Missing, incompatible or negative duration evidence is not converted to zero. Station ratios use finite, positive ratios; check the corresponding `stations` value in the equal-station result. A pooled ratio of medians and a geometric mean of station-specific ratios summarize different quantities.

Primary timing uses 428/429 finite CE/comparison observations; unrestricted timing uses 1,225/1,226. Primary minutes/action ratios are 1.120 pooled and 1.324 equal-station, both higher for CE. These recorded-trajectory summaries do not measure total labor or a causal speed effect.

The linkage pilot is separate from the balanced constructions. Its current rule version, eligible denominator, candidate tiers and window sensitivities are in `analysis/results/inheritance_pilot_summary.json` and `analysis/results/inheritance_window_sensitivity.csv`. Normalized event positions retain held-event gaps within the canonical session; the pilot does not infer continuity across unrelated sessions or confirm that earlier context was used.

## Following a manuscript claim

Start with the compact [claim reproducibility boundary](CLAIM_REPRODUCIBILITY.md).
It distinguishes public aggregate arithmetic, receipt-only source claims and
restricted reconstruction for each claim family. `claim_status` records that
scope, not an unqualified verification verdict.

1. Find the claim in `data/provenance/claim_to_evidence.csv`.
2. Apply its `record_selector` to the named `evidence_file`. The executable counterpart is `data/provenance/claim_selectors.json`; the verifier checks that both spellings agree exactly.
3. Inspect `generator` for the executable rule or analysis path.
4. Use `data/provenance/field_lineage.csv` to follow each public field back to its restricted input-field class and transformation.
5. Use `analysis/ANALYSIS_MANIFEST.sha256` for canonical-run receipts and `PUBLIC_MANIFEST.sha256` for files actually distributed.

The mapping covers source-frame scope, balanced constructions, pooled rates, equal-station sensitivity, action-count diagnostics, timing interpretation, linkage and the measurement boundary. Check the actual rows and selectors in the versioned file rather than assuming a historical claim count or page number. A receipt proves byte identity; it does not itself establish the meaning or correctness of a claim.

Run the selector check separately, without rebuilding the catalog:

```sh
python3 scripts/verify_public_release.py --claims-only
```

Each selector specifies the exact expected record count and required fields. A JSON `path` is a sequence of literal object keys; a CSV selector starts at its data rows. Distinct keys in `where` are combined with **AND**; the alternatives in one list are combined with **OR**. The check rejects a missing source, path, field or match; an unexpected number of records; a blank or whitespace-only required value; duplicate JSON keys; duplicate/empty CSV headers; and disagreement between the readable map and executable rules. Valid zero and false values remain usable. It does not evaluate expressions or access restricted inputs. The measurement-boundary claim selects one exact Markdown section and its stated limitation phrases.

For example, CE-C01 deliberately uses two sources: `analysis_summary.json` supplies the resolved-frame and archive counts, while `EVENT_CORRECTION_IMPACT.json` supplies the retained pre-normalization segment count. CE-C09 selects either timing metric in either analysis set: four pooled records and four equal-station records. It does not ask a single `metric` field to equal both timing metrics simultaneously. Passing this check establishes that the promised evidence can be located; the separate numerical checks establish the arithmetic supported by public aggregates. Neither verifies the restricted observations or establishes a causal interpretation.

The final manuscript and release-byte bridge is in `docs/MANUSCRIPT_RELEASE_CROSSWALK.md`.

## Checking more than the headline

`data/catalog/aggregate_catalog.csv` exposes filterable pooled, station, equal-station, minimum-size, archive-batch, action-bin, action-standardized and linkage views. `data/catalog/data_dictionary.csv` defines their fields. Use the catalog's actual row count after regeneration rather than the preceding version's count. The evidence workbook is a review convenience; CSV and JSON files remain canonical.

For a new question not already represented, use the safe aggregate-extension procedure in `docs/ADDITIONAL_ANALYSES.md`. That process deliberately does not provide an unrestricted query endpoint over confidential row-level trajectories.

## What a public reviewer cannot infer

No public file maps a pseudonymous station to a person, employer unit, client, device owner or source path. No released table contains a prompt, response, supplied context, exact timestamp, conversation identifier, row-level trajectory or automated linkage map. Replaying the statistical analysis requires authorized access to the restricted normalized input. Reconstructing native-event identity and work attribution additionally requires the pinned source logs and private alias/provenance mappings. Neither is possible from public aggregates alone.

Practitioner and author operational review did occur. That evidence concerns the recorded deliverable decisions and must not be relabeled as independently coded condition or stage judgments. Separately, the author reported reviewing all 46 frozen event-v3 cases and finding their classifications accurate. This is an author-involved, unblinded collective confirmation, not 414 separately recorded criterion responses, independent labeling or population accuracy. The historical aggregate summary records 46 reviewed/confirmed cases and zero inaccuracies reported at that time, with no invented per-criterion rates. Later technical findings and sample correspondence are recorded separately in `analysis/results/boundary_correction_summary.json`. They do not create new human judgments or transfer the confirmation to changed labels or newly selected rows. An LLM's inspection, passing tests, deterministic replay or a blank prepared packet is not the source of the human confirmation; the subsequent author statement is retained privately.

## Pilot adjacency correction — 2 October 2026

Package v2.1.0 uses pilot rule `ce-inheritance-map/3.0.1-event-normalized-pilot`, which requires consecutive event ordinals for immediate links. Two links spanning held positions at distances 3 and 12 instead qualify as continuation references within 20 positions. High-confidence/probable counts become 1,106/1,150; five-/ten-position positives become 1,859/2,103 (72.6%/82.1%). The 20-position result remains 2,256/2,560 (88.1%), and primary/unrestricted statistical results are unchanged. See [the reproduction note](../analysis/REPRODUCE.md#pilot-adjacency-correction--2-october-2026) and the aggregate files for the corrected values. Issued v2.0.0 is unchanged. The restricted input and row-level map are not public, and the linkage labels remain automated and unadjudicated.

# Manuscript-to-release crosswalk

This page connects the IST revision to the immutable aggregate evidence release. It is a review map, not a claim that the confidential source frame is public.

## Exact release identity

- Repository: `https://github.com/calboreanu/Context-Eng-Exp-Report`
- Release: `v1.0.0`
- Immutable locator: `https://github.com/calboreanu/Context-Eng-Exp-Report/releases/tag/v1.0.0`
- Clean revised manuscript SHA-256: `f990bbdc2b86014fdaab28b433b4669ec09165b8695cee8d91542ca8dfe86363`
- Marked revised manuscript SHA-256: `196a241403c377c4654f711f52e9015e8b367e00ccb9a318b79be73643a8a271`
- Marked supplement SHA-256: `1d6be10b25320ea4aa1348d04f54c08ff96fc3553f2f06e32ce5cb3ec4a2dfc4`
- Response to reviewers SHA-256: `f55d20300fca393bfb3164046d49738b05c3c2657800cc3e6b59e60bb904a4fc`

The release page records the tagged commit and downloadable archive digest. `PUBLIC_MANIFEST.sha256` verifies every distributed repository payload after extraction.

## Claims and evidence

| Paper location | Claim or display | Release evidence | Exact selector or check |
|---|---|---|---|
| Abstract; Section 5A | 31,919 episodes, 4,760 conversation sources, 13 station archives | `analysis/results/analysis_summary.json` | `scope` |
| Abstract; Section 5B | 1,484 observations per condition in the primary construction; 2,246 unrestricted | `analysis/results/analysis_summary.json` | `scope.primary_frontloaded_balanced_per_condition`; `scope.unrestricted_balanced_per_condition` |
| Table 4; Section 5C | Six primary process-signal rates and directions | `analysis/results/pooled_summary.csv` | `analysis_set=primary_frontloaded` |
| Abstract; Section 5C | Verification 46.7% versus 32.2%; +14.5 percentage points | `analysis/results/pooled_summary.csv` | `analysis_set=primary_frontloaded`; `metric=verification_successful` |
| Section 5D | Equal-station sensitivity and descriptive intervals | `analysis/results/equal_station_summary.csv` | `analysis_set=primary_frontloaded` |
| Section 5G; Table S3 | Action-count-bin diagnostics and +6.7/+3.9/-2.1 percentage-point standardized gaps | `analysis/results/action_count_verification_strata.csv`; `action_count_verification_summary.json` | all three published analysis-set/archive-batch combinations |
| Section 5F | Timing estimators differ and do not establish completion speed | `pooled_summary.csv`; `equal_station_summary.csv` | `metric=duration_min`; `metric=min_per_action` |
| Section 5H; Supplement S-D | 2,726/3,326 (82.0%) candidate-positive at window 20 | `inheritance_pilot_summary.json`; `inheritance_window_sensitivity.csv` | `window=20`; automated, unadjudicated, three-station, strong-or-probable predecessor pilot |
| Supplement S-B | Locked ST02 source was absent and not scanned | `data/provenance/source_chain_receipts.csv` | `receipt_id=SRC-02` |
| Discussion and limitations | Classifier does not test five-role/four-concern implementation | `analysis/upstream_contract/PUBLICATION_ANALYSIS_DEVIATION.md` | authorized analytical meaning |

For machine-readable versions of these mappings, use `data/provenance/claim_to_evidence.csv` and `data/provenance/field_lineage.csv`.

## What each audit proves

Run `python3 scripts/run_reviewer_audit.py` from a fresh extraction. It rebuilds the public catalog, checks aggregate arithmetic, scans the disclosure boundary, verifies all manifested bytes, and runs a generated fictional-source smoke test through the source-level scripts.

The fictional test demonstrates executable structure only. Source-row authenticity and exact regeneration of the reported 31,919-row analysis remain receipt-backed controlled-review questions because publishing those rows would expose confidential prompts, responses, traces, timestamps, paths, and trajectory links.

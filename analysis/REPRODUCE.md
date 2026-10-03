# Reproducing and checking the event-v5 analysis

## Public checks

With CPython 3.12 or later, from the repository root:

```sh
python3 scripts/run_reviewer_audit.py
```

This regenerates the aggregate catalog, checks numerical consistency, scans the disclosure boundary, verifies the actual public manifest and runs fictional regression fixtures. It does not reconstruct confidential source events or supply human reference judgments.

## Restricted normalization

The analysis input is `normalized_merged_v5.local.csv`, under `context-engineering-event-normalized-analysis/5.0.0`. Its authoritative byte count and SHA-256 are in `results/analysis_summary.json` and `../data/provenance/restricted_artifact_receipts.csv`. Do not substitute an earlier v4, v3, v2 or R1 input and expect current results.

The standalone v5 reconstruction starts from the preserved v2 51-field input (SHA-256 `7ce945e5336c7f1fc336f7d8fc3326e9904eb35094cc870af2423884ec22d3ff`) and pinned original-source descriptors for both Claude-family and Codex providers. It is not a numerical edit to the v3 result tables. The normalizer is `ce-primary-boundary-normalization-v5.0.0-20260918`; the rule configuration is `context-engineering-eligibility/2.1.0-action-reference-20260918`. The study cutoff is retained. Codex originals are reread to verify prior terminal-completion traces before applying the corrected primary-boundary and lexical-input rules across providers.

An authorized reviewer with those private inputs can run:

```sh
python3 analysis/upstream_contract/scripts/event_normalization.py \
  --input /authorized/corrected_merged_v2.local.csv \
  --sources /authorized/pinned-source-descriptors.json \
  --rules analysis/upstream_contract/config/context-engineering-eligibility.json \
  --cutoff analysis/upstream_contract/config/study-cutoff.json \
  --out /authorized/new-event-v5-output
```

The descriptor is an object with a `sources` list. Each entry provides station label, source reference, provider, path, SHA-256 and byte count; the portable CLI docstring gives a fictional schema example. Paths may be relative to the descriptor. Include every pinned Claude-family and Codex source represented by the input, including pinned zero-episode sources needed for native ownership connectors. A Claude-only descriptor from the former v3 workflow is insufficient. The output directory must be new or empty.

The normalizer verifies complete source hashes, frozen accepted anchors and the prior Codex completion traces. It writes the resolved v5 frame, held candidates, complete old-to-new aliases, identity and primary-boundary witnesses, native-call attribution and a private `NORMALIZATION_SUMMARY.json` receipt. Its contract is `upstream_contract/EVENT_NORMALIZATION.md`. No logged command is executed. Original records and the frozen event-v3 review packet are not modified.

## Restricted downstream reproduction

With the normalized input, run:

```sh
python3 analysis/scripts/run_workstation_analysis.py \
  --input /authorized/new-event-v5-output/normalized_merged_v5.local.csv \
  --normalization-receipt /authorized/new-event-v5-output/NORMALIZATION_SUMMARY.json \
  --out /authorized/new-analysis-results

python3 analysis/scripts/run_inheritance_pilot.py \
  --input /authorized/new-event-v5-output/normalized_merged_v5.local.csv \
  --out /authorized/new-analysis-results

python3 analysis/scripts/derive_action_count_verification.py \
  --primary /authorized/new-analysis-results/restricted/primary_balanced_rows.csv \
  --unrestricted /authorized/new-analysis-results/restricted/unrestricted_balanced_rows.csv \
  --out-dir /authorized/new-analysis-results

python3 analysis/scripts/verify_analysis.py --results /authorized/new-analysis-results
```

The statistical scripts use only the Python standard library. Defaults remain 50,000 station-bootstrap repetitions and base seed `20260815`, with SHA-256-derived metric seeds. Available-case timing denominators are explicit; missing or inconsistent durations are not zero-imputed.

The aggregate CSVs and restricted statistical derivatives are deterministic for identical frozen input. Summary JSON timestamps, runtime provenance and normalization-receipt identity can differ across independently located runs; compare substantive values separately from those provenance fields. A private reconstruction receipt is not a public data file.

Exact floating-point byte reproduction uses the recorded CPython 3.12.14 runtime. Earlier Python versions can differ in low-order floating-point rounding without changing the displayed results; check the recorded runtime before treating such differences as an empirical discrepancy.

`results/boundary_correction_summary.json` reports the computational comparison with the preserved v3 scope, primary membership and historical review evidence. The local correspondence clarification separates substantive tracked changes from provenance-status-only transitions and retains the former strict status-inclusive totals under explicitly named fields. It changes neither the normalized input nor downstream statistical results. Its overlap accounting is not a new draw or new human assessment. `../data/validation/author_review_summary.json` continues to describe the original 46-case author statement; neither file transfers that confirmation to changed labels or newly selected rows.

`results/action_reference_correction_summary.json` separately compares the preserved v4 computation with the native-source v5 rerun: actual class/reference changes, fixed-v4-selection exposure, newly recomputed sample membership, source categories and invariant native-work checks. Fixed-sample exposure is not the new result; all reported v5 statistics come from full rematching and reconstruction. The closed TodoWrite family and unqualified numeric-dot token grammar are specified in `upstream_contract/EVENT_NORMALIZATION.md`. Other lexical stage/context/verification limitations remain.

## Optional Figure 4 rebuild

The asset retains its historical filename `fig-06-analysis-evidence-map.pdf`. The display adapter reads the current aggregate-driven renderer and replaces its review-status subtitle with an explicitly historical note about the 46-case event-v3 author check. Numerical text comes from the current adjacent aggregates; the subtitle replacement does not alter those numbers. Matplotlib is a separate dependency from the standard-library statistical pipeline. Create an optional plotting environment outside the repository so it is not confused with manifested release files:

```sh
python3 -m venv ../ce-figure-env
../ce-figure-env/bin/python -m pip install "matplotlib==3.9.2"
../ce-figure-env/bin/python scripts/build_reviewed_figure.py --output-dir ../ce-figure-output
```

Matplotlib 3.9.2 is the locally tested plotting version; the public numerical checks do not require it. If an environment already contains it, the equivalent command is `python3 scripts/build_reviewed_figure.py --output-dir ../ce-figure-output`. The conceptual figures and graphical abstract are separate typesetting assets, not rebuilt by this command. The lower-level `analysis/scripts/build_submission_figures.py` entry point uses the renderer's generic automated-label subtitle; use the display adapter for the historical author-check note. The renderer, adapter and review aggregate have their respective analytical/public-manifest receipts. Fonts, plotting versions and PDF metadata may change PDF bytes without changing statistical input; inspect the rendered figure separately.

## Two manifest boundaries

`analysis/ANALYSIS_MANIFEST.sha256` records package v2.1.0's governed analytical files, including the clarified correspondence metadata, corrected pilot and receipts for withheld derivatives and fine-grained balancing cells. Their absence from the public package is intentional. The original frozen analysis and issued v2.0.0 manifests remain with their respective preserved packages.

`PUBLIC_MANIFEST.sha256` covers every file actually distributed. A missing file from that manifest is an error. The historical v1.0.0 manifest belongs only to its historical snapshot.

Package v2.1.0, dated 2 October 2026, retains the primary and unrestricted statistical analysis from v2.0.0; its analytical contract remains `context-engineering-event-normalized-analysis/5.0.0`. This successor also contains the documentary adjunct, correspondence-metadata clarification and pilot adjacency correction, which were not in issued v2.0.0. Historical preparation-status fields are explained in `../README.md`; publication and downloaded-archive verification gates are recorded separately in `../docs/RELEASE_CHECKLIST.md`. The historical 46-case collective author check and subsequent technical findings remain documented in `../docs/HUMAN_REVIEW_SUMMARY.md`; neither is inferred from a passing numerical audit. Public distribution, confidential journal delivery and journal submission remain separate actions.

## Pilot adjacency correction — 2 October 2026

Package v2.1.0 uses `ce-inheritance-map/3.0.1-event-normalized-pilot`. Both immediate-link rules now require consecutive event ordinals as well as a preceding eligible CE row. Replaying the same pinned input changes two links, at distances 3 and 12, to `CONTEXT_REFERENCE_WITHIN_20`; held positions are not treated as immediate adjacency. The nine synthetic checks in `../tests/test_inheritance_adjacency.py` cover gaps, adjacent controls and unchanged exact-anchor precedence.

High-confidence/probable counts are 1,106/1,150. Five- and ten-position positive counts are 1,859/2,103 (72.6%/82.1%); the 20-position result remains 2,256/2,560 (88.1%). Primary and unrestricted statistical results are unchanged. This correction is not in issued v2.0.0; the frozen analysis and release remain preserved. Row-level linkage maps and source content remain restricted, and the candidate labels remain unadjudicated.

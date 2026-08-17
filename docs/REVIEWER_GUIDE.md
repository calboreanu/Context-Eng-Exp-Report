# Reviewer guide

This repository is designed to answer two different review questions without blurring them:

1. **Can the released numerical claims be checked?** Yes. The aggregate arithmetic, sensitivities, claim selectors, transformation mappings, and exact bytes are public and executable.
2. **Can the 31,919-row source frame be regenerated from the public repository alone?** No. Prompts, responses, tool traces, exact timestamps, paths, row-level samples, and linkage records remain restricted. The repository publishes their receipts and the source-level scripts, not their content.

## Five-minute audit

From a fresh clone with CPython 3.12 or later:

```sh
python3 scripts/run_reviewer_audit.py
```

A clean result rebuilds the catalog without a byte change, verifies public aggregate arithmetic, checks the disclosure boundary, validates every manifested byte, runs the release tests, and passes a generated fictional-source smoke test through the published source-level analysis scripts. The fictional rows exist only in an operating-system temporary directory and are deleted automatically.

## Headline count reconciliation

The unified catalog exposes exact numerators and denominators for every binary pooled, station, and archive-batch row. These counts add no information beyond the released full-precision rate and denominator; they make review faster. The primary pooled rows reconcile as follows:

| Metric | Context-operation condition | Routed comparison | Difference |
|---|---:|---:|---:|
| Completed-successful verification call | 693/1,484 (46.7%) | 478/1,484 (32.2%) | +14.5 pp |
| Audit-stage prompt signal | 792/1,484 (53.4%) | 197/1,484 (13.3%) | +40.1 pp |
| Remediation-stage prompt signal | 572/1,484 (38.5%) | 128/1,484 (8.6%) | +29.9 pp |
| Packaging/release-stage prompt signal | 291/1,484 (19.6%) | 26/1,484 (1.8%) | +17.9 pp |
| At least two distinct stage prompt signals | 1,041/1,484 (70.1%) | 83/1,484 (5.6%) | +64.6 pp |
| Grounded-decision trace proxy | 774/1,484 (52.2%) | 131/1,484 (8.8%) | +43.3 pp |

The canonical values are in `analysis/results/pooled_summary.csv`; the exact k/n convenience fields are in `data/catalog/aggregate_catalog.csv` under `view=pooled`.

## Following a manuscript claim

1. Find the claim in `data/provenance/claim_to_evidence.csv`.
2. Apply its `record_selector` to the named `evidence_file`.
3. Inspect `generator` for the executable rule or analysis path.
4. Use `data/provenance/field_lineage.csv` to follow each public field back to its restricted input-field class and transformation.
5. Use `analysis/ANALYSIS_MANIFEST.sha256` for canonical-run receipts and `PUBLIC_MANIFEST.sha256` for files actually distributed.

The 12 mapped claims cover the source-frame scope, balanced constructions, pooled rates, equal-station sensitivity, action-count diagnostics, timing interpretation, linkage pilot, the known ST02 source limitation, and the construct boundary.

The final manuscript and release-byte bridge is in `docs/MANUSCRIPT_RELEASE_CROSSWALK.md`.

## Checking more than the headline

`data/catalog/aggregate_catalog.csv` contains 337 filterable records across pooled, station, equal-station, minimum-size, archive-batch, action-bin, action-standardized, and linkage views. `data/catalog/data_dictionary.csv` defines every field. The evidence workbook provides the same views for manual review; the CSV and JSON files remain canonical.

For a new question not already represented, use the safe aggregate-extension procedure in `docs/ADDITIONAL_ANALYSES.md`. That process deliberately does not provide an unrestricted query endpoint over confidential row-level trajectories.

## What a public reviewer cannot infer

No public file maps a pseudonymous station to a person, employer unit, client, device owner, or source path. No released table contains a prompt, response, supplied context, exact timestamp, conversation identifier, row-level trajectory, or automated linkage map. Source-level regeneration therefore requires separate controlled access and is outside the public package's verification claim.

# Reproducing and checking the workstation analysis

## Runtime

- Empirical and verification scripts: CPython 3.12.13, standard library only.
- Public catalog, arithmetic verifier, and disclosure validator: CPython 3.12 or later, standard library only.

## Restricted source-level regeneration

The required merged input is `extended_multistation_context_episode_review.local.csv`, with byte count `153312689` and SHA-256:

`098998194cc6636b92fb47fc04fd78055c28f02ebac664e3ffc87ecffd2bd5d3`

It is not distributed. The source can contain prompts, responses, tool traces, exact timestamps, paths, and confidential material. Source-level regeneration therefore requires separately authorized controlled access.

From the repository root, an authorized reviewer can run:

```sh
python3 analysis/scripts/run_workstation_analysis.py \
  --input /authorized/restricted-input.csv \
  --out analysis/results

python3 analysis/scripts/run_inheritance_pilot.py \
  --input /authorized/restricted-input.csv \
  --out analysis/results

python3 analysis/scripts/derive_action_count_verification.py \
  --primary analysis/results/restricted/primary_balanced_rows.csv \
  --unrestricted analysis/results/restricted/unrestricted_balanced_rows.csv \
  --out-dir analysis/results

python3 analysis/scripts/verify_analysis.py --results analysis/results
```

The workstation script uses 50,000 station-bootstrap repetitions and base seed `20260815` by default. Deterministic per-metric seeds are derived with SHA-256. Aggregate CSVs and restricted derivatives are deterministic. Two JSON summaries retain run-local provenance fields; clean reruns are compared after excluding only those documented runtime fields.

`verify_analysis.py` is intentionally included even though its governed row-level inputs are not. It documents and executes the restricted-derivative integrity checks for an authorized reviewer. It is not the public aggregate verifier.

## Public aggregate verification

Anyone with this repository can run:

```sh
python3 scripts/build_public_catalog.py
python3 scripts/verify_public_release.py
python3 scripts/validate_public_boundary.py .
python3 scripts/verify_manifest.py PUBLIC_MANIFEST.sha256
```

The public verifier checks condition arithmetic, station and equal-station agreement, minimum-size sensitivity, archive-batch effects, action-bin standardization, linkage-window arithmetic, source-frame receipt arithmetic, claim-map references, and catalog completeness.

## Canonical versus public manifests

`ANALYSIS_MANIFEST.sha256` records the exact verified local analysis run. It includes receipts for the restricted input derivatives and the withheld station-provider-month balancing table. Those entries are intentionally absent from the repository.

`PUBLIC_MANIFEST.sha256` is the completeness manifest for the actual repository candidate. A missing restricted artifact is therefore expected; a missing public-manifest artifact is an error.

## Interpretation boundary

The public files permit independent verification of released aggregate arithmetic and mapping, not regeneration of the raw source frame. The author completed disclosure review for the aggregate-only boundary on 17 August 2026. The exact Version 1.0.0 release, workbook, manifest, and downloaded archive passed the documented one-command reviewer audit before publication.

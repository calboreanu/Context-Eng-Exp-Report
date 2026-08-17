# Context Engineering workstation evidence

This clean-history release candidate contains the privacy-preserving empirical evidence behind *Context Engineering: A Practitioner Methodology for Structured Human--AI Collaboration -- An Experience Report*.

The revised paper analyzes 31,919 process-trace episodes from 4,760 conversation sources in 13 pseudonymous workstation archives. This repository exposes the analysis rules, executable source-level scripts, aggregate results, integrity receipts, data definitions, and claim-to-evidence mappings. It deliberately does **not** contain raw prompts, assistant responses, exact timestamps, paths, conversation identifiers, row-level balanced samples, or the candidate-linkage map.

## What readers can check

- all pooled primary and unrestricted summaries;
- all station-level effects for the 12 contributing pseudonymous stations;
- equal-station, minimum-station-size, and archive-batch sensitivities;
- action-count-bin diagnostics, including the comparator-standardized gaps;
- linkage-window sensitivity from 5 through 106 prompt episodes;
- the mapping from manuscript claims to exact files and selectors;
- field-level transformation lineage and source-chain receipts;
- release hashes and automated boundary checks.

`data/catalog/aggregate_catalog.csv` combines those views into one filterable long-form table. `Context_Engineering_Evidence_Explorer.xlsx` provides the same public data in a reviewer-friendly workbook; the CSV and JSON files remain the canonical machine-readable evidence.

## Start here

1. Follow the five-minute workflow in [`docs/REVIEWER_GUIDE.md`](docs/REVIEWER_GUIDE.md).
2. Read [`docs/PRIVACY_AND_DISCLOSURE.md`](docs/PRIVACY_AND_DISCLOSURE.md).
3. Inspect [`data/provenance/claim_to_evidence.csv`](data/provenance/claim_to_evidence.csv).
4. Filter [`data/catalog/aggregate_catalog.csv`](data/catalog/aggregate_catalog.csv) or open the evidence explorer.
5. Run `python3 scripts/verify_public_release.py`.
6. Run `python3 scripts/validate_public_boundary.py .`.
7. Verify exact bytes with `python3 scripts/verify_manifest.py PUBLIC_MANIFEST.sha256`.

The release is prepared for publication at `https://github.com/calboreanu/Context-Eng-Exp-Report`. See [`docs/PUBLICATION_STRATEGY.md`](docs/PUBLICATION_STRATEGY.md) for the final tag, archive-verification, and manuscript-synchronization sequence.

## Reproducibility boundary

The raw merged input is restricted because it contains prompts, outputs, tool traces, exact timestamps, paths, and potentially confidential material. Its receipt is published by filename, byte count, and SHA-256 only. The source-level scripts are included so an authorized reviewer can reproduce the analysis with separately governed access. A public reader can independently validate the internal arithmetic and cross-file consistency of the released aggregates, but cannot regenerate the source frame from this repository alone.

That distinction is intentional: this is an aggregate evidence and traceability package, not a disguised release of conversation content.

## License and release status

Code and executable specifications are licensed under Apache-2.0. Documentation, public aggregate evidence, mappings, receipts, manifests, and the reviewer workbook are licensed under CC BY 4.0; see [`LICENSING.md`](LICENSING.md) for the exact component split.

The aggregate-only disclosure boundary has been approved by the author. Public visibility remains pending the final internal IRAD/data-use signature check and exact-release validation.

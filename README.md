# Context Engineering workstation evidence

**Public package v2.0.0 — event-v5 corrected evidence, 19 September 2026.** This package carries the frozen analytical contract `context-engineering-event-normalized-analysis/5.0.0`; the public release number and analytical contract number are distinct. The [pre-release audit record](docs/LOCAL_CANDIDATE_AUDIT.md) documents the 18 September computational and artifact checks. Current publication and downloaded-archive verification gates are tracked separately in the [release checklist](docs/RELEASE_CHECKLIST.md). No previous public release is relabeled as this successor.

This is the aggregate evidence and traceability package for *Context Engineering: A Practitioner Methodology for Structured Human–AI Collaboration — An Experience Report*.

The published v1.0.0 snapshot remains a historical record. Following the local event-v2 provider-status, event-v3 native-identity and event-v4 primary-boundary corrections, event-v5 corrects task-list bookkeeping classified as substantive work and bare numeric tokens classified as artifact references. See [the versioned correction](docs/CLASSIFICATION_CORRECTION.md). The author previously reported reviewing all 46 frozen event-v3 cases and collectively confirming their classifications, with no inaccuracies reported at that time. Later technical findings qualify that corroboration; they do not create new human ratings or transfer the confirmation to changed or newly selected cases. The [review summary](docs/HUMAN_REVIEW_SUMMARY.md) preserves both records and their limits. Public distribution does not establish journal submission, editorial acceptance or new human validation.

The retained intake contains 39,830 recognized text-bearing prompt occurrences before the delegated-source filter, which removes 7,911 occurrences and leaves 31,919 source-local segments. Those segments are not 31,919 distinct human tasks. The versioned normalizer reconciles replay echoes, saved-history copies and duplicate capture representations, preserves attributable work and records unresolved cases. The final v5 input contains 20,682 resolved trajectories; 283 components remain held separately. Primary and unrestricted constructions balance 429 and 1,227 observations per condition across 12 contributing stations. The exact input identity is bound to [the analysis summary](analysis/results/analysis_summary.json). The retained normalization boundary is explained in [the normalization contract](docs/EVENT_NORMALIZATION.md).

## What a reviewer can check

- Primary and unrestricted pooled results, with observed timing denominators.
- Pseudonymous station, equal-station, minimum-size and archive-batch sensitivities.
- Action-count diagnostics and inherited-context window sensitivities.
- Executable claim-to-record mappings, field-level transformations and source-chain receipts.
- Deterministic catalog rebuilding, exact distributed bytes and fictional regression tests.
- Aggregate counts, selection design and recording limits for the 46-case author check.

Start with [the reviewer guide](docs/REVIEWER_GUIDE.md), the compact [public/restricted claim boundary](docs/CLAIM_REPRODUCIBILITY.md), and the executable [claim map](data/provenance/claim_to_evidence.csv). The catalog and workbook are review conveniences; CSV and JSON remain canonical. Their frozen-content checks are recorded in the pre-release audit; successor-package checks are separate.

Run the public checks from the repository root:

```sh
python3 scripts/run_reviewer_audit.py
```

## Reproduction and privacy boundary

The public package supports independent aggregate arithmetic and consistency checks. Source-level regeneration requires separately authorized access to the restricted input and source receipts; see [REPRODUCE.md](analysis/REPRODUCE.md). Raw prompts, responses, supplied context, exact timestamps, persistent locators, row-level trajectories, event aliases and detailed human-review materials are not distributed. Hashes identify withheld records; they do not make those records public. Only the bounded review's aggregate summary is included.

Normalized events are not demonstrated independent practitioners, tasks or accepted deliverables. Tool status is not independent product-quality validation. The publication-purpose rules exclude matching records, not necessarily every publication-related task. Lexical classifications and candidate inheritance remain subject to their stated limitations.

## Version and license

The versioned locator for this package is [v2.0.0](https://github.com/calboreanu/Context-Eng-Exp-Report/releases/tag/v2.0.0). The [historical v1.0.0 release](https://github.com/calboreanu/Context-Eng-Exp-Report/releases/tag/v1.0.0) predates these corrections. No DOI is claimed. The [manuscript crosswalk](docs/MANUSCRIPT_RELEASE_CROSSWALK.md) separates public evidence from historical and current journal artifacts; the [release checklist](docs/RELEASE_CHECKLIST.md) distinguishes publication from a fresh download audit.

The frozen analytical files, aggregate data, code, tests and evidence workbook are preserved from the verified 18 September event-v5 candidate. Some retained records therefore say `unreleased` or `unreleased_local_candidate`: notably the analytical deviation contract, the historical author-review summary, the CE-C02 claim note and workbook preparation notes. These describe their preparation state, not the distribution status of public package v2.0.0. Publication metadata is maintained here and in `CITATION.cff`; historical status text is not rewritten into a new empirical or human-review result. `analysis/ANALYSIS_MANIFEST.sha256` remains unchanged, while `PUBLIC_MANIFEST.sha256` binds the final distributed package.

Code and executable specifications use Apache-2.0; documentation and public aggregate evidence use CC BY 4.0. See [LICENSING.md](LICENSING.md). The aggregate-only disclosure boundary does not authorize release of confidential source material. The seven-field practitioner stage template remains in supplement S-A; it is not a raw-data reproduction package.

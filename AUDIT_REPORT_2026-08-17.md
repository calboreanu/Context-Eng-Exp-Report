# Privacy-preserving evidence repository audit — 2026-08-17

## Verdict

**PRIVATE CLEAN-HISTORY RELEASE CANDIDATE: REVIEWER-AUDIT PASS.**

An outside reader can audit the released numerical claims, sensitivity views, claim selectors, field lineage, code paths, and exact file identities from a fresh clone. The repository does not claim that a public reader can regenerate the confidential 31,919-row source frame without separately governed access.

The repository has been pushed privately to `https://github.com/calboreanu/Context-Eng-Exp-Report`. It has not been made public, tagged as a release, or cited from the manuscript through an immutable locator.

## Evidence contents

- 337 aggregate catalog records spanning pooled, station, equal-station, minimum-size, archive-batch, action-bin, action-standardized, and linkage views;
- exact binary numerators and denominators wherever they are deterministically recoverable from released full-precision rates and denominators;
- 138 field-level data-dictionary records;
- 12 manuscript claim mappings;
- 20 transformation-lineage mappings;
- five restricted-artifact receipts without restricted content;
- source-frame and source-chain receipts, including the known missing ST02 source limitation;
- executable source-level analysis scripts and an aggregate-only public verifier;
- a 15-sheet reviewer workbook with eight formula-linked headline checks;
- a reviewer-first guide that states both the executable audit workflow and the public package's limits.

## Independent numerical and provenance review

The audit independently checked the following rather than relying only on the repository verifier:

- `22,469 + 9,450 = 31,919` and agreement with the source-frame receipt;
- all pooled effects and recoverable binary numerators;
- all 216 station effect calculations;
- all 18 equal-station means or geometric means and their positive/tie/negative station counts;
- all 11 action-count strata and the `+6.7`, `+3.9`, and `-2.1` percentage-point comparator-standardized diagnostics;
- `2,726 / 3,326 = 82.0%` for the automated, unadjudicated window-20 linkage pilot;
- all 12 claim-evidence paths and executable generator references;
- all 337 unique catalog identifiers and all 138 data-dictionary entries;
- all public-manifest members and file hashes after final regeneration.

The primary verification claim reconciles to `693/1,484` versus `478/1,484`, a raw difference of `+14.4879` percentage points. The other five primary binary measures now expose the same exact k/n audit path in the unified catalog.

## Automated integrity results

- `scripts/build_public_catalog.py`: deterministic rebuild with no diff.
- `scripts/verify_public_release.py`: PASS.
- `scripts/validate_public_boundary.py`: PASS.
- `scripts/verify_manifest.py`: PASS after final manifest regeneration.
- Unit tests: PASS.
- Fresh-clone GitHub Actions validation: PASS for the pushed commit.
- Git history: clean root history; no superseded prototype files in this repository's history.

## Workbook review

All 15 sheets were rendered and visually inspected. The audit repaired a stale repository URL, corrected median/action values that had been displayed as percentages, formatted median effects as ratios, exposed the exact catalog k/n fields as integers, and widened or wrapped reviewer-facing columns. The workbook has no formula errors, external links, macros, hidden sheets, or raw-data sheet. All eight headline checks display `PASS`.

## Privacy results

The tracked tree contains no prompt or response text, supplied context, exact timestamps, source paths, conversation or episode identifiers, sample links, candidate maps, raw inputs, balanced row derivatives, credentials, emails, or restricted directories. Source-field names remain in code and lineage documentation where necessary to explain transformations; they do not contain source values.

The workbook and repository contain pseudonymous aggregate station views, including small station denominators already used in the manuscript sensitivity analysis. They have no public identity key. The station-by-provider-by-month balancing table remains withheld. New reviewer questions follow a declared aggregation and disclosure process rather than an unrestricted query endpoint over row-level data.

## Public verification boundary

The public package proves aggregate arithmetic, cross-file consistency, transformation traceability, and exact released bytes. It does not prove source-row authenticity solely from public content, because the raw prompts, outputs, traces, timestamps, paths, balanced samples, and linkage map are intentionally withheld. Source-level scripts and cryptographic receipts support a separately authorized controlled review.

## Remaining release gates

1. signed internal IRAD/data-use authorization covering the exact aggregate package;
2. explicit component licensing decision if public reuse rights will be granted;
3. public visibility, immutable tag, downloaded-archive verification, and manuscript locator update.

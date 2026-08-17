# Privacy-preserving evidence repository audit — 2026-08-17

## Verdict

**CLEAN-HISTORY RELEASE CANDIDATE: LOCAL TECHNICAL PASS.**

This repository represents the revised 31,919-episode workstation study in a new clean history rather than the superseded product-case protocol. The aggregate-only disclosure boundary is approved; no remote push, tag, release, visibility change, or public deposit had been performed at the time of this audit.

## Evidence contents

- 337 aggregate catalog records spanning pooled, station, equal-station, minimum-size, archive-batch, action-bin, action-standardized, and linkage views;
- 138 field-level data-dictionary records;
- 12 manuscript claim mappings;
- 20 transformation-lineage mappings;
- five restricted-artifact receipts without restricted content;
- source-frame and source-chain receipts, including the known missing ST02 source limitation;
- executable source-level analysis scripts and an aggregate-only public verifier;
- a 15-sheet reviewer workbook with eight formula-linked headline checks.

## Integrity results

- All 20 canonical analysis artifacts present in the repository match the verified local-run SHA-256 receipts in both the working tree and staged Git index.
- Five canonical artifacts are absent by design: the merged-source-dependent balancing table and four governed raw or row-level artifacts described by the restricted receipts.
- `scripts/verify_public_release.py`: PASS.
- `scripts/validate_public_boundary.py`: PASS.
- Unit tests: 2/2 PASS.
- Workbook formula-error scan: zero matches.
- Workbook headline checks: 8/8 PASS.
- Workbook visual review: all 15 sheets rendered; no blank or broken sheet and no clipped headline check.
- Workbook ZIP integrity: PASS.
- Public manifest exact coverage and hashes: PASS.
- Staged Git whitespace check: PASS.

## Privacy results

The tracked tree contains no prompt or response text, exact timestamps, source paths, conversation or episode identifiers, sample links, candidate maps, raw inputs, balanced row derivatives, credentials, emails, or restricted directories. The workbook has no external links or macros. Source-field names remain in code and lineage documentation where necessary to explain transformations; they do not contain source values.

The provider-by-station-by-month balancing table remains withheld. Additional reviewer questions are handled through predeclared local aggregate specifications and disclosure review rather than an unrestricted query endpoint over row-level data.

## Exact convenience-artifact hashes

- Reviewer workbook: `4d6c72775fd067a1c3885cadfeecfed776244215dc41499e11327e7aa4de7ee4`.
- Unified aggregate catalog: `97dd1345cba16bace4cdffd3e12b72b9bf0cd9e6de3ae887625155730c922c1a`.
- Data dictionary: `9d8136e7d9575ec5166dade72d474295dfb64c15d2deaa0f1c19aea3dd184ec3`.
- Claim map: `5b3e093acd0d84b371f54fcea9322807a16e8fe00756d5ef8fa09f4ea54863c3`.
- Canonical analysis summary: `34d090b16cd78de717e1113210eef2060381d3c08ffc84f3d7931b08a451b945`.

## Git disposition

The exact manifest-covered tree was copied into a new repository named `Context-Eng-Exp-Report` and committed as its clean root history on branch `main`. The obsolete prototype and its deleted files are not present in this repository's history.

The intended public locator is `https://github.com/calboreanu/Context-Eng-Exp-Report`.

## Open gates

1. signed internal IRAD/data-use authorization covering the aggregate-publication boundary;
2. explicit component licensing decision if public reuse rights will be granted;
3. public push, immutable tag, downloaded-archive receipt, and manuscript locator update.

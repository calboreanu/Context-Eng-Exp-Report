# GitHub publication strategy

## Selected path: clean public release repository

This repository is the selected clean-history public release repository. Its canonical name is `calboreanu/Context-Eng-Exp-Report`. The corrected event-v5 evidence is assigned public package version [v2.0.0](https://github.com/calboreanu/Context-Eng-Exp-Report/releases/tag/v2.0.0), dated 19 September 2026; its analytical contract remains `5.0.0`. The [historical v1.0.0 release](https://github.com/calboreanu/Context-Eng-Exp-Report/releases/tag/v1.0.0) and its manifest remain separate. Actual publication and fresh-download checks are recorded in the [release checklist](RELEASE_CHECKLIST.md), not inferred from local preparation.

This approach has three advantages:

- the obsolete product-case protocol does not remain visible in public Git history;
- the public repository name matches the actual workstation study;
- the first release commit, tag, archive, and manifest can all describe one evidence model.

## Rejected alternative: orphan release branch

An orphan branch in the former private development repository was not selected because repository-level visibility could expose older branches or deleted history.

## Not recommended: make the current development history public

Deleting the old prototype from the latest branch does not erase it from Git history. Directly changing the former development repository to public would expose the superseded product-case protocol and make it unclear which study the repository supports.

## Historical v1.0.0 release sequence

1. the author completed disclosure review of the aggregate-only boundary;
2. `PUBLIC_MANIFEST.sha256` was regenerated after all release-text edits;
3. the one-command verifier, privacy-boundary scan, tests, and manifest check passed;
4. the clean-history repository was made public and tagged `v1.0.0`;
5. the packaged release archive was downloaded and re-audited;
6. the manuscript, supplement, response, cover letter, and submission support files were updated to the versioned release URL.

The signed internal IRAD/data-use determination is retained separately from the public payload. Its confidential provision to the journal is a separate submission check. It is not IRB/HRPP approval and does not expand the public package to confidential inputs or row-level derivatives.

The successor preserves the historical tag and the frozen event-v5 analytical files, data, code, tests and workbook. Its documentation records the correction and distinguishes release identity from analytical version; its public completeness manifest must be regenerated for the final payload. The analytical manifest is not regenerated. A fresh audit of the actual downloaded release remains a separate gate. No private development history or confidential evidence is added by publication, and local preparation alone does not establish that a release has been pushed.

# GitHub publication strategy

## Selected path: clean public release repository

This repository is the selected clean-history public release. Its canonical name is `calboreanu/Context-Eng-Exp-Report`; its immutable locator is `https://github.com/calboreanu/Context-Eng-Exp-Report/releases/tag/v1.0.0`. It contains only the files covered by the verified public manifest plus the manifest itself.

This approach has three advantages:

- the obsolete product-case protocol does not remain visible in public Git history;
- the public repository name matches the actual workstation study;
- the first release commit, tag, archive, and manifest can all describe one evidence model.

## Rejected alternative: orphan release branch

An orphan branch in the former private development repository was not selected because repository-level visibility could expose older branches or deleted history.

## Not recommended: make the current development history public

Deleting the old prototype from the latest branch does not erase it from Git history. Directly changing the former development repository to public would expose the superseded product-case protocol and make it unclear which study the repository supports.

## Completed release sequence

1. the author completed disclosure review of the aggregate-only boundary;
2. `PUBLIC_MANIFEST.sha256` was regenerated after all release-text edits;
3. the one-command verifier, privacy-boundary scan, tests, and manifest check passed;
4. the clean-history repository was made public and tagged `v1.0.0`;
5. the packaged release archive was downloaded and re-audited;
6. the manuscript, supplement, response, cover letter, and submission support files were updated to the immutable release URL.

The unsigned internal memorandum remains a separate IST-upload gate. It does not expand the public package to confidential inputs or row-level derivatives.

# GitHub publication strategy

## Selected path: clean public release repository

This repository is the selected clean-history public release candidate. Its canonical name and intended locator are `calboreanu/Context-Eng-Exp-Report` and `https://github.com/calboreanu/Context-Eng-Exp-Report`. It contains only the files covered by the verified public manifest plus the manifest itself.

This approach has three advantages:

- the obsolete product-case protocol does not remain visible in public Git history;
- the public repository name matches the actual workstation study;
- the first release commit, tag, archive, and manifest can all describe one evidence model.

## Rejected alternative: orphan release branch

An orphan branch in the former private development repository was not selected because repository-level visibility could expose older branches or deleted history.

## Not recommended: make the current development history public

Deleting the old prototype from the latest branch does not erase it from Git history. Directly changing the former development repository to public would expose the superseded product-case protocol and make it unclear which study the repository supports.

## Final release sequence

1. complete the final authorization and licensing decisions;
2. regenerate `PUBLIC_MANIFEST.sha256` after all release-text edits;
3. rerun the verifier, privacy-boundary scan, tests, and manifest check;
4. create `calboreanu/Context-Eng-Exp-Report` as a public GitHub repository and push this one exact history;
5. tag an immutable version;
6. download the GitHub-generated archive and record its SHA-256;
7. rerun the boundary and manifest checks on the downloaded archive;
8. update the manuscript data-availability statement with the immutable tag or release URL.

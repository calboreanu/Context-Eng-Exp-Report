# Release checklist

- [ ] Executed internal IRAD/data-use authorization is retained in the IST submission file.
- [x] Author disclosure review approves the aggregate-only public boundary; no people, prompts, responses, supplied context, row-level trajectories, exact timestamps, persistent locators, or linkage maps are included.
- [x] Code and executable specifications are Apache-2.0; documentation and aggregate evidence are CC BY 4.0.
- [x] `python3 scripts/build_public_catalog.py` produces no diff after the reviewer-audit repair.
- [x] `python3 scripts/verify_public_release.py` passes.
- [x] `python3 scripts/validate_public_boundary.py .` passes.
- [x] Reviewer workbook is rebuilt and all sheets are visually checked.
- [x] `python3 scripts/build_manifest.py` is run after all candidate content edits.
- [x] `python3 scripts/verify_manifest.py PUBLIC_MANIFEST.sha256` passes on the exact candidate tree.
- [x] Git history begins with only the intended clean candidate tree.
- [x] Release archive contains no ignored, raw, restricted, or temporary files.
- [x] Manuscript data-availability statement points to the immutable release/tag, not a moving branch.
- [x] Fresh release download passes `python3 scripts/run_reviewer_audit.py`.

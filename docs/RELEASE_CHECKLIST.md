# Release checklist

- [ ] Internal IRAD/data-use authorization names the exact aggregate package and repository.
- [x] Author disclosure review approves the aggregate-only public boundary; no people, prompts, responses, supplied context, row-level trajectories, exact timestamps, persistent locators, or linkage maps are included.
- [ ] Code, documentation, and aggregate-data licenses are recorded.
- [ ] `python3 scripts/build_public_catalog.py` produces no diff.
- [x] `python3 scripts/verify_public_release.py` passes.
- [x] `python3 scripts/validate_public_boundary.py .` passes.
- [ ] Reviewer workbook is rebuilt and visually checked.
- [ ] `python3 scripts/build_manifest.py` is run last.
- [x] `python3 scripts/verify_manifest.py PUBLIC_MANIFEST.sha256` passes before final identity edits; rerun after manifest regeneration.
- [x] Git history begins with only the intended clean candidate tree.
- [ ] Release archive contains no ignored, raw, restricted, or temporary files.
- [ ] Manuscript data-availability statement points to the immutable release/tag, not a moving branch.

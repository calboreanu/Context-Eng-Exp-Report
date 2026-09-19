# R2 provider-adapter correction

Historical predecessor note: this page describes the v2 provider-adapter repair
only. Its before/after counts are not the current event-normalized results.
The subsequent native-event and v4 boundary corrections are documented in
`EVENT_NORMALIZATION.md`; current results are in the adjacent aggregate files.

Historical status on 17 September 2026: local unreleased event-v2 correction. At that stage, corrected extraction, the full numerical pipeline, manuscript, supplement, analysis-construction figure, aggregate catalog and workbook were synchronized locally. No public release or completed human-validation result occurred in that historical step. Public package v2.0.0 instead carries the later frozen event-v5 evidence; public and local analytical version numbers are distinct.

## Reason for correction

The frozen Codex adapter treated receipt of a tool response as completion and detected failure primarily through JSON-shaped text. Standard plain-text nonzero-exit and still-running process headers could therefore be retained as completed-successful calls. Deterministic reproduction of the previous analysis reproduced those flags; it did not establish that they represented terminal execution status.

The correction separately handles supported structured and transport-header statuses, asynchronous session results, polling-call accounting and supported Codex attachments. Frozen episode boundaries and unrelated lexical classification rules are retained. Process status remains a provider-reported proxy, not independent proof of task success or product quality.

## Version and evidence boundary

The published v1.0.0 tag and its historical receipts remain the prior record. Corrected extraction, balanced membership, numerical results and manuscript links must be checked together before a new release. The new package is not silently substituted for the old release.

Raw prompts, responses, supplied context, detailed tool traces, source locators, timestamps, row-level memberships and linkage maps remain restricted. Any public correction report contains aggregate impact and file-level integrity receipts only. Fictional regression tests contain no research records.

Actual human checking is a separate requirement. Adapter regression tests, source replay, byte receipts and this repository's aggregate verifier are not human validation of the classifier or the practitioner method.

## Completion record

The adapter is `ce-provider-adapter-v2.0.0-20260917`, SHA-256 `f07d754816db4c803ec905aeb026088ef0d335000cb7b2cd1acd3ee9ac734230`. Its executable contract and limitations are documented in `analysis/upstream_contract/PROVIDER_ADAPTER_CORRECTION.md`.

All 6,553 Codex episodes from 2,524 source objects were replayed. All 2,173,783,106 source bytes matched their locked hashes, and the frozen adapter first reproduced every compared frozen field exactly. The correction preserves the 31,919 episode identities and the 25,366 other-provider rows. Excluding version metadata, 3,062 Codex episodes have changed extracted fields; 107 change automated route and four change attachment count. These are automated extraction effects, not human error-rate estimates.

The corrected restricted input has 153,792,740 bytes and SHA-256 `7ce945e5336c7f1fc336f7d8fc3326e9904eb35094cc870af2423884ec22d3ff`. Only this receipt is public. The full dependent analysis used CPython 3.12.14, 50,000 station-bootstrap repetitions and the unchanged seed contract. Its restricted-derivative verifier passed. The public test suite adds 44 fictional adapter tests and six fictional inheritance-verifier tests.

| Quantity | Historical v1.0.0 | Corrected local analysis |
|---|---:|---:|
| Primary observations per condition | 1,484 | 1,483 |
| Unrestricted observations per condition | 2,246 | 2,244 |
| Primary verification, context-operation condition | 693/1,484 (46.7%) | 689/1,483 (46.5%) |
| Primary verification, comparison | 478/1,484 (32.2%) | 476/1,483 (32.1%) |
| Primary raw verification gap | +14.5 pp | +14.4 pp |
| Primary comparator-standardized diagnostic | +6.7 pp | +6.4 pp |
| Unrestricted comparator-standardized diagnostic | +3.9 pp | +3.5 pp |
| Subsequent-capture primary standardized diagnostic | −2.1 pp | −2.0 pp |
| Window-20 candidate linkage | 2,726/3,326 (82.0%) | 2,686/3,226 (83.3%) |

The six pooled primary signal directions remain positive; that does not establish causal benefit, task quality, speed or human-validated context use. The linkage pilot remains automated and unadjudicated. Full corrected precision is retained in the aggregate CSV/JSON outputs, with claim selectors and source-chain receipts.

Balanced membership also changed: the primary frame retains 2,955 prior episode/cohort memberships, removes 13 and adds 11, yielding 2,966 rows. The unrestricted frame retains 4,438, removes 54 and adds 50, yielding 4,488 rows. These are aggregate reconciliation counts; no membership list is released.

The manuscript receipt status is in `MANUSCRIPT_RELEASE_CROSSWALK.md`; workbook/catalog bytes are covered by `PUBLIC_MANIFEST.sha256` for the final distributed package. Native-event reconstruction, the event-v4 boundary correction and the subsequent event-v5 action/reference correction supersede the provider-only counts above. See [the current correction](CLASSIFICATION_CORRECTION.md). The historical 46-case event-v3 author confirmation and later technical findings are distinguished in `HUMAN_REVIEW_SUMMARY.md`; individual criterion-form responses were not supplied. The successor locator is [public v2.0.0](https://github.com/calboreanu/Context-Eng-Exp-Report/releases/tag/v2.0.0), not historical v1.0.0. Publication and post-download audit completion remain separately recorded in the [release checklist](RELEASE_CHECKLIST.md).

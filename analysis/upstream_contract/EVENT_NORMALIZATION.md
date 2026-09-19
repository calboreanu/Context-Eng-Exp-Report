# Primary-boundary and native-event normalization contract

Version: `ce-primary-boundary-normalization-v5.0.0-20260918`.

This correction operates only on the pinned 31,919-row v2 scope: 6,553 Codex and 25,366 Claude-family occurrences. The standalone v5 normalizer rereads pinned originals for every provider, verifies the accepted prompt/attachment anchors and Codex completion traces, reconciles native identities and primary boundaries, and applies `context-engineering-eligibility/2.1.0-action-reference-20260918` before analytical selection. Codex rows are not assumed unchanged. No newly recovered out-of-frame files or human reference labels are admitted. Historical v3/v4 outputs and the frozen 46-case event-v3 author-review record remain separate.

## Identity and canonical representation

1. Join native UUID occurrences within one source only when an explicit `isReplay:true` record corroborates the family. Runtime/transport session changes do not defeat that relation.
2. Join across sources on station, native UUID, native session, native timestamp and complete canonical user-message payload. A narrow missing-time audit/embedded bridge also requires the same user UUID/full message plus a shared assistant UUID/exact content/native call directly parented to that user in the embedded capture and bounded to the audit occurrence. At least one user native timestamp must be absent; conflicting supplied times and ambiguous embedded native identities cannot bridge. Every bridge stores its exact witness. Identical wording alone is insufficient.
3. Preserve every old episode/source/line interval and prompt-variant hash. An embedded strict native-message copy of an explicit audit replay inherits effective replay status while retaining its raw flag. Canonical prompt selection is earliest effective non-replay occurrence by valid native time, otherwise audit time, then stable station/source/line/identity ordering. No output, success or action count determines the representation.
4. Different replay text is retained, not treated as a new human invocation or automatically excluded. Conflicting non-replay prompt payloads within a corroborated component are an explicit ambiguity.

## Work attribution and order

### Nonprimary boundaries

A native `task-notification` origin or a complete task-notification envelope is a machine-boundary candidate; SDK transport alone is not. An explicit native human origin prevents envelope-only inference, and additional instructions after a wrapper are not discarded merely because of its prefix. A notification is absorbed only when its exact tool-use reference identifies one supported primary owner. Bare acknowledgments must match the closed continuation grammar and contain no attachment; they use a supported native parent or, when parent metadata is absent, the preceding accepted anchor within the same source, nesting owner and session. Additional task content is not a bare continuation.

Supported chains are reconciled to their primary owner, preserving all original anchors, attributable work and private ownership witnesses. Missing, conflicting or cyclic ownership is held as unresolved, not counted as a new primary invocation or assigned by outcome. Classification uses the retained primary request: when that request matches the frozen publication-purpose rules, an absorbed continuation retains the owner's exclusion. Publication context visible only elsewhere, without a matching primary request or supported native governing-task link, can remain undetected. This is a computational boundary rule, not semantic intent adjudication or proof that all publication work is excluded.

### Native calls and ordering

Native parent UUID ancestry governs formats that provide it. Audit records without parent UUID use bounded ordered segments separated by accepted prompts, separately for each native nesting owner. `parent_tool_use_id` is nesting, never a sequential message parent. An exact link to a native Agent/Task invocation (or another delegate-class call) establishes machine delegation and sets `origin_candidate=native_delegated_tool_child`; this is not a semantic human rating. The bare native Task name is recognized for ownership even though the unchanged generic taxonomy labels it `other`.

Parent argument aliases do not erase delegation when every captured representation of that exact native owner ID is an Agent/Task/delegate call. A non-null pointer with an uncaptured/unresolved parent is instead `native_nested_owner_unresolved`; both origins remain mapped but outside the human-origin eligible pool. This follows the provider's documented subagent-message relation ([Claude Agent SDK, accessed 18 September 2026](https://code.claude.com/docs/en/agent-sdk/subagents#detect-subagent-invocation)).

A native assistant UUID with exact content and compatible supplied session can carry its unique resolved parent-chain ownership across captures, overriding weaker audit segmentation. Envelope stop-reason differences and ingestion-clock differences do not alter the exact content identity; clock disagreement is flagged. Previous/new ownership and native witness locators are retained. Conflicting strong parent owners are never resolved by this priority.

Native tool IDs are counted once per event. Matching delayed results are returned to their unique call owner, not the most recent prompt. Within corroborated audit/embedded representations of the same native assistant UUID and call ID/name, a unique internally consistent embedded input with resolved native parent-chain ownership has fixed provenance priority. Both literal input hashes/classes/targets remain in the proof, with explicit change flags. This is not a semantic equivalence or path-substitution claim. Conflicting embedded payloads, names, assistant prose, terminal statuses, event ownership and recorded order remain held. Measurement-invariant dual-capture payload differences are separately flagged; other arbitrary hash conflicts are not relaxed. An ordered later terminal update can supersede an earlier status without selecting on success. Disjoint attributable work is unioned, not discarded merely because histories have different tails.

Recorded call order and consistent native timestamps form an ordering graph. Stable identity breaks unresolved display-order ties only. Each feasible first completed action supplies a required context-ancestor set; the maximal possible-before set contains context with no completed-action ancestor. The versioned classifier is evaluated at those attainable bounds. Only qualification-changing ambiguity is held as `unresolved_context_order`. Invariant events remain usable with a valid conservative topological witness, a `lower_bound_context_before_count` flag and private count/target bounds; that trace is not presented as uniquely observed empirical order. Unrelated same-class disjoint work remains resolvable. Codex polling completion is replayed within a corrected merged primary boundary when uniquely attributable; unsupported cross-source completion is held.

## Lexical input correction

Version 5 routes the closed TodoWrite name family to `administrative` before the prior tool-name taxonomy. Split provider namespaces on `__`, `::`, dot or slash; lowercase the final component and remove underscores/hyphens; it must equal `todowrite`. Matching examines the tool name only. A real `Write` call targeting `TODO.md` remains a modification, and longer/different names are not admitted to this family. Calls/results are retained; administrative calls do not enter the substantive-action count or define the first substantive action. Native ordering bounds, eligibility, matching, timing denominators and linkage are recomputed, not patched from earlier result rows. The exact pre-v5 taxonomy remains available solely to compare reconstructed Codex traces to their pinned pre-correction baseline; current calls use the v5 classifier.

Artifact candidates that fully match `\.\d+(?:[eE][+-]?\d+)?%?[.!?]*` are excluded as unqualified numeric dot tokens. This includes scientific notation, percent and trailing sentence punctuation. Real dotfiles, filenames with extensions, explicit qualified numeric paths such as `./.05`, `/data/.05` or `~/.05`, and URL references retain the preceding path-like rule. A bare numeric filename must be explicitly qualified to distinguish it from numeric prose. This closed token rule is not semantic inference about the surrounding request. BashOutput and KillShell retain their preceding mappings; both had zero calls in the resolved v4 frame.

XML element names and closing-tag slashes are syntax, not artifact references. Actual path-bearing element contents and attribute values remain available to the path rule. Stage matching omits only mechanically identifiable `-m`/`--message` argument values in Git commit/tag commands, including supported combined short options. Ordinary quoted prose, code fences, other commands and genuine verification-command language are not generally removed. These changes correct specific false matches; stage indicators remain lexical proxies, not human-coded requested stages. Raw prompts are preserved.

## Time and sequence

Timing uses a consistent native clock when every attributable node supports it, otherwise an audit clock when fully supported. Exact native-node aliases share one timing node. Audit aliases use the earliest observation rather than the latest replay/copy. Only attributable assistant/call/result nodes supply endpoints. Missing, incompatible or negative duration evidence remains missing, never clipped or converted to an absolute value.

Claude `session_ref` encodes station plus the canonical native session and nesting owner; absent native session uses a source-only fallback. Codex retains its pinned session references. Within each session, normalized event ordinals are chronological with stable source/line ties; held events retain sequence positions. Unmerged Codex intervals retain their pinned v2 timing, while merged boundaries use attributable timing evidence. The 51-column source span describes only the canonical occurrence; sidecar aliases and native call/result mappings identify all contributing intervals.

Claude `prompt_reuse_count` is recomputed within the original/later batch over the resolved event frame. Codex retains this v2 diagnostic field, not all prior classifications. This mixed inherited diagnostic is not used for event identity, native delegation, classification or numerical selection.

## Outputs and scope

- `normalized_merged_v5.local.csv`: resolved, rescreened primary trajectories across all supported providers; 51-column compatibility.
- `quarantined_events_v5.local.csv`: held canonical/provisional rows, never silently dropped from provenance.
- `event_alias_map.private.csv`: all 31,919 old rows, event identity, status, source span and old/new ordinals.
- `event_provenance.private.jsonl`: prompt variants, native calls/results, timing, delegation, ordering flags and exact quarantine reasons.
- `source_receipts.private.json`, `identity_edges.private.json`, `boundary_edges.private.json`, `attribution.private.json`, `NORMALIZATION_SUMMARY.json`: source pins, identity/boundary witnesses, attribution and accounting. The private orchestration also produces source-to-event mappings for authorized inspection.

Private source-cache records contain native identities and derived measures, not full prompt or tool-output copies. The normalized frame remains confidential. Source originals, v2, v3, v4, issued artifacts and prior review packets are untouched. This is a versioned computational correction, not proof of unique practitioners, deliverable quality or human classifier accuracy. The historical `CEV3`/`CEV4` event-ID namespaces remain stable where native identity is unchanged; version is recorded separately from identity.

## Portable restricted-input entry point

Run `event_normalization.py --input INPUT.csv --sources SOURCES.json --rules RULES.json --cutoff CUTOFF.json --out NEW_PRIVATE_DIRECTORY`. The adjacent `postrun-context-screen.py` adapter is used unless supplied with `--screen`. The output directory must be new or empty. This entry point and its source descriptors are for authorized holders of confidential inputs, not a claim that public aggregates reconstruct the private corpus.

A fictional descriptor has this schema:

```json
{"sources": [{"station_id": "ST-X", "source_ref": "SRC-X", "provider": "claude_home", "path": "raw/source.jsonl", "sha256": "64 hexadecimal characters", "bytes": 123}]}
```

Relative source paths resolve beside the descriptor. Include pinned originals for every Claude-family and Codex source represented by the input, plus any pinned zero-episode sources needed for native ownership connectors. Source bytes and hashes are verified on every portable execution. The private orchestration runner may reuse compact extraction caches only when the accepted v2 input, extraction-relevant adapter code/constants, nonhuman-prefix configuration, cutoff and extraction-function fingerprint match. It records fresh versus cached reads explicitly; final result receipts separately hash the full screen and rule configuration used for classification.

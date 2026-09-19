# Provider adapter correction v2

Implementation identifier: `ce-provider-adapter-v2.0.0-20260917`.
Scope: local R2 analysis correction, not a public release, human validation, or new submission.

## Preserved baseline

The frozen R1 screen remains unchanged in the archived analysis source and historical v1.0.0 release. Its SHA-256 is `d149f3129c2d3a6ecd48a86c7eac138cbf88cdd07c0a880f601e4e9b441a2d02`. The separate corrected screen is distributed here as `analysis/upstream_contract/scripts/postrun-context-screen.py`; the canonical correction workspace retains its own versioned copy.

Prompt/episode boundaries, cutoff handling, source IDs, episode IDs, source-line attribution, prompt filters, stage/context patterns, eligibility equations, target tokens, and ordinary tool-name/command routing expressions are retained. The correction does not add people, identify operators, adjudicate task quality, or infer context use. Claude result handling and attachment rules remain the frozen provider-specific heuristic. An explicit Codex polling exception is described below; it must not be omitted when describing what changed.

## Corrected status contract

`ResultStatus` separates `completed` from `succeeded`, with a provider-status kind, optional session ID and process indicator. An unreturned invocation remains incomplete/unsuccessful.

1. A recognized process exit code is terminal. Zero is provider-reported success; any nonzero integer, including a negative code, is unsuccessful. Integer strings are accepted; booleans are not exit codes.
2. A live session without a terminal exit code is **not complete** and is not successful. An explicit null/unparseable exit code or session ID without an actual exit code is also unresolved, not terminal success. A retained session ID alongside an actual exit code does not negate terminal completion. A later generic same-call acknowledgment cannot erase a known pending process/cell status, and a conflicting explicit process session cannot complete it.
3. Boolean `isError`/`is_error` flags override successful wrapper/inner statuses. They do not manufacture terminal completion for an otherwise pending process. A terminal failure for an invocation remains a failure if a later same-call generic receipt would otherwise erase it.
4. Plain-text process status is recognized only in an anchored transport envelope beginning `Chunk ID`, `Wall time`, and `Process exited with code …` or `Process running with session ID …`. Status-looking phrases in an ordinary response, code fence, quoted example, or the envelope's output body are not searched.
5. Structured top-level result objects and native text/content-block wrappers are supported, including serialized JSON objects/lists. Multiple recognized components are combined: completion requires every component to be complete; success requires every component to succeed. This prevents mixing one component's successful response with another's pending/failed process.
6. Native `Script running with cell ID …` responses are pending. A `Script completed` wrapper does not hide failed/pending process statuses when its complete `Output` body consists of structured result objects or begins with the exact anchored process transport envelope. Arbitrary script-output prose is not recursively mined for exit/status strings.
7. Ordinary nonprocess tool results retain the disclosed transport-receipt success heuristic. A successful search/read response is not required to contain an operating-system exit code, and neither transport success nor exit zero proves that content is correct or the user's task succeeded.

Provider format interpretation is not authenticated operating-system telemetry. Whole-response JSON documents that resemble a status envelope can remain ambiguous; the adapter does not infer semantic quotation. Unrecognized output formats are not proof that a process exited, and source-format coverage must be reported alongside this correction. In particular, the generic nonprocess heuristic remains a measurement limitation rather than a validated quality measure.

## Async association and counting correction

`EpisodeToolState` owns a call list, call-ID map and process/cell session map for **one source episode only**. The extractor creates a fresh tracker on every accepted human prompt. Timestamp-excluded records never enter the tracker. It never links a later episode or source to an earlier one, and does not infer post-cutoff success.

- Every invocation remains in the original call sequence, retaining its order, name and target token.
- For Codex only, `write_stdin` and `wait` calls are administrative process/cell continuations, including calls whose session argument cannot be interpreted. They no longer count as additional substantive actions through the previous lexical `write` routing.
- A polling call can update an original invocation only when its input session/cell ID identifies one unambiguous owner inside the same episode and its result has attributable process/cell status. The original invocation then supplies the action's terminal status. Repeated polls do not add repeated substantive actions.
- An unlinked, ambiguous, cross-session, malformed, or generic-only polling response does not complete another invocation. Duplicate Codex call IDs and competing session owners are held unresolved and counted diagnostically, not arbitrarily matched.
- Mixed pending processes in one wrapper remain separate components. Completing one cannot make another successful. Script-cell completion can reveal nested process sessions, which then require their own terminal outcomes.
- `write_stdin` with nonempty input remains a continuation of the same process for this process-counting contract, not a new substantive process invocation. The correction changes that counting convention explicitly; it does not claim the input has no behavioral effect.

The original invocation order is retained for the existing ordered-use formula. This still does **not** establish that retrieval content arrived before the downstream action began; that independently disclosed construct limitation is unchanged.

## Attachment correction

Codex `input_image` blocks attached to a recognized text-bearing human prompt are counted. The prompt text itself is unchanged. Image-only/no-text messages remain outside the existing prompt-episode extraction boundary, and the existing whole-block injected-text filter is unchanged. An attachment count establishes recorded presence, not complete image recovery, comprehension, or actual use.

## Replay interface

```python
state = screen.EpisodeToolState(active["calls"])
# For each retained record, preserve the frozen result-before-call order:
state.apply_record(record, provider)
for call_id, name, raw_input in screen.extract_tool_calls(record, provider):
    state.add_call(call_id, name, raw_input, provider)
```

Each call still exposes exactly `order`, `name`, `class`, `completed`, `succeeded`, and `target_ref`. Internal session/status metadata is separate. `state.diagnostics` counts linkage/ambiguity outcomes without raw content. `codex_tool_result` remains a two-tuple compatibility wrapper reporting terminal-success booleans; it cannot represent completion separately and must not be used for corrected replay.

The standalone CLI appends the adapter identifier to the unchanged lexical `rule_version`. An external replay driver must do the same for corrected rows and record both baseline and corrected script hashes. Do not relabel the frozen input or overwrite its original rule identifier.

## Tests and empirical dependency

`tests/test_provider_adapter.py` contains 44 fictional regression tests, including numeric/textual/negative/null status, quoted examples, error precedence, native blocks, nested script/process responses, polling/session/call isolation, ambiguous IDs, pending-status preservation, unchanged Claude behavior, attachment boundaries, and a generated-source run through the actual CLI proving cutoff and episode isolation. They passed under bundled CPython 3.12.14. They use no empirical prompts, human labels, or sampled evaluation records.

At this implementation checkpoint the parser SHA-256 is `f07d754816db4c803ec905aeb026088ef0d335000cb7b2cd1acd3ee9ac734230`. The public adapter tests use the same fictional assertions, with their import path adjusted for this repository layout. The six additional inheritance-verifier tests likewise use fictional records only. Their exact public bytes are covered by the public manifest.

The dependent replay owns measured corpus effects. It must first establish full frozen Codex extraction parity, then report corrected membership, classification, counting, balancing and numerical changes, preserving the original comparison. Synthetic tests establish executable behavior only, not classifier accuracy, human agreement, or empirical effect size. Human-validation sampling must wait for the corrected analysis frame and coding rules to be frozen.

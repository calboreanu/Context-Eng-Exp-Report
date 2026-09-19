# Context-engineering interaction eligibility

Document (adjudication guidance) version: `1.1.0`
Automated lexical rule contract: `context-engineering-eligibility/2.1.0-action-reference-20260918`. The provider-status adapter retains its `ce-provider-adapter-v2.0.0-20260917` identifier; v5 rows also identify the new rule contract and `ce-primary-boundary-normalization-v5.0.0-20260918`. Historical screen outputs retain their original versions. See `../PROVIDER_ADAPTER_CORRECTION.md` for the earlier terminal-status, polling and attachment repair and `../EVENT_NORMALIZATION.md` for the current all-provider boundary and lexical-input corrections.

## Conceptual grounding

The operational definition follows the contemporary distinction between a single prompt and the broader work of curating system instructions, tools, external data, history, memory, and dynamically retrieved state. It is aligned with Anthropic's [context-engineering guidance](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) and Google Cloud's [context-engineering overview](https://cloud.google.com/discover/ai-context-engineering). The empirical gate is intentionally narrower: merely supplying context is insufficient unless the archived trajectory shows product purpose, use of that context, and an observable action or grounded decision.

## Unit of analysis

The following paragraph states the retained conceptual gate. In the event-v5
publication computation, source-local segments are reconciled through native
identity, uniquely owned nonprimary boundaries and attributable tool activity.
An explicit replay, machine notification or bare continuation is not automatically
a new primary invocation. Unresolved ownership is held. See
`../EVENT_NORMALIZATION.md` for canonical representation, delegation, quarantine,
timing and lexical-input rules. The closed acknowledgment grammar is expanded;
XML tag syntax does not count as a path, and inert Git commit/tag message values
do not supply stage signals. These are automated corrections, not human adjudication.

An interaction is one primary user-level task invocation and the agent trajectory that follows it until the next primary user-level task invocation in the same source. An invocation may be direct or a human-configured scheduled automation. Tool calls, tool results, assistant messages, injected environment blocks, compacted summaries, sidechains, and delegated-agent prompts are evidence within or around an interaction; they are not separate interactions.

## Evidence-status precondition

The v5 publication screen classifies the closed TodoWrite tool-name family as administrative and filters unqualified numeric dot tokens from artifact references. Qualified numeric paths, URLs, dotfiles and real Write operations remain supported. The exact grammar and pre-correction replay guard are in `../EVENT_NORMALIZATION.md`. These narrow corrections do not change the human gates below or close the publication-analysis deviation.

The four gates below are evaluated on an archived trajectory. `interaction_evidence_status` (CODEBOOK.md, ruling CD-001) records whether one exists: only `trajectory_observed` records are eligible for gate evaluation and for interaction counts. An event whose occurrence is proven only by independent artifacts (`artifact_corroborated_event_only`) cannot pass the four-gate interaction test: artifacts may independently establish the product event and outcome (gates 1 and 4), but context operation and use trace (gates 2–3) are unavailable without the trajectory. After human review such an event may support a clearly labeled artifact-event analysis; it never enters the interaction denominator or the context-engineering interaction count. `claim_only` assertions are excluded outright by coding rules 1 and 8.

## What qualifies

A human reviewer may code an interaction `include_context_engineering` only when all four gates pass:

1. **Product purpose.** The episode concerns requirements, design, implementation, audit, remediation, verification, packaging, release, or another observable product decision. Publication production and generic question answering do not pass.
2. **Context operation.** The human or agent deliberately selects, structures, retrieves, maintains, combines, constrains, or prunes information beyond the bare task instruction. Modes include a bounded context package, standards and constraints, multi-source synthesis, just-in-time retrieval, history or memory, tool/environment state, examples/templates, compaction/pruning, and artifact-state feedback.
3. **Use trace.** The evidence connects that context operation to the ensuing work. Acceptable traces include ordered retrieval before a substantive action, an attachment or history reference used in the action, or inspected evidence followed by a grounded product decision.
4. **Observable product action.** A completed create, modify, execute, or verify action is observed, or an inspection/audit/requirements/design episode produces a grounded decision after evidence retrieval. Plans, claims, and narration alone do not pass.

All four gates are conjunctive. A sophisticated prompt without observable use is not an included interaction. Product work with no context operation is product work, but it is not coded as context engineering.

## Automatic routing labels

| Label | Meaning |
|---|---|
| `candidate_strong` | All four gates have a deterministic trace: an explicit or multi-source context operation precedes an observable product action. High-priority human review; not a final inclusion. |
| `candidate_probable` | A context operation and product action co-occur, but their ordered connection is not directly observed. Human review required. |
| `exclude_publication_candidate` | Publication-purpose language triggered the categorical boundary. Human review may correct a lexical false positive. |
| `exclude_continuation_only` | The prompt is only a continuation acknowledgment and adds no fresh context operation. |
| `exclude_continuation_wrapper` | An assistant-generated compaction or context-restoration summary was serialized as a prompt. |
| `exclude_tool_generated_prompt` | Tool delivery or result text was serialized as a user record. |
| `exclude_delegated_prompt_candidate` | A task passed to a subagent is retained as parent-run evidence, not counted again as a primary interaction. |
| `exclude_non_product_candidate` | No product-purpose signal or completed substantive product action was observed. |
| `exclude_no_observable_product_action` | Context or task language was present, but no completed action or grounded decision was observed. |
| `exclude_no_context_operation` | Product work was observed without evidence of deliberate context selection, retrieval, maintenance, or structuring. |

The labels are deliberately asymmetric: automation can prioritize likely examples, but it cannot assert that an interaction qualifies. `human_qualified_count` remains zero until named human review is completed.

The automatic publication exclusion detects matches to the frozen publication-purpose rules, not every semantically publication-related task. Such work may remain undetected when its purpose is apparent only outside the retained primary request and no supported native governing-task link carries the matching scope. This is a limitation of the publication analysis, distinct from the intended human coding boundary above.

`origin_candidate` separates scheduled automation from direct or unresolved user-level invocations and identifies likely delegated, continuation, and tool-generated records. `prompt_reuse_count` clusters exact prompt reuse. Repeated scheduled runs may each be real executions, but they are not independent prompt designs or replications.

## Human decisions

The controlled final field is `include_context_engineering`, `exclude_product_without_context_engineering`, `exclude_non_product`, `exclude_publication`, `exclude_no_observable_action`, `exclude_duplicate_or_nonhuman`, or `uncertain`. The reviewer records a product-purpose decision, context operation, context-use trace, observable action, and primary context mode. A second reviewer and adjudicator are required for the reliability subset.

## Important boundary examples

- “Fix this bug” followed by an edit is product work, but not automatically context engineering.
- “Read the requirements, current implementation, and failed test; reconcile them before fixing and rerunning verification” followed by those reads, a patch, and a test is a strong candidate.
- A pasted manuscript plus a request to revise the paper is excluded even if the agent manages substantial context.
- An episode that integrates validated product evidence into a manuscript is `exclude_publication` even when it exhibits strong context-engineering structure (frozen inputs, validation checks, an observable commit); the underlying product event it reports is coded separately — `trajectory_observed` if its own operator–AI trajectory is archived, otherwise `artifact_corroborated_event_only` (CD-001).
- “Continue” is not a new context-engineering interaction; it inherits context without adding or managing it.
- A tool call is never counted as an interaction by itself.

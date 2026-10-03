# Retrospective deliverable evidence

This aggregate adjunct is included in **package v2.1.0** and was not part of the published v2.0.0 release. The earlier release and its frozen event-v5 analysis remain unchanged. The addition documents existing operational evidence separately from the primary statistical comparison.

The [aggregate summary](../data/validation/deliverable_evidence_summary.json) covers two selected, potentially overlapping evidence sets. They must not be added together as a task count.

## Historical terminal anchors

All 138 records from the previously assembled terminal-deliverable queue were retained. The queue was selected for completion-related characteristics, so it cannot supply an overall success-rate denominator. The author's original collective confirmation concerned completion, the tracked target being the deliverable, and no known continuation outside the linked corpus. It was not a new set of contemporaneous acceptance timestamps or full-method ratings.

| Source inventory observation | Count |
|---|---:|
| Historical anchors, source files freshly verified and source intervals parsed | 138 each |
| Resolved current events linked to those anchors | 138 |
| Anchors in the current primary comparison | 5 |
| Anchors with all tracked target tokens reobserved in successful Edit/Write results | 138 |
| Distinct historical target-path tokens | 343 |
| Anchors with completed retrieval/search | 132 |
| Anchors with completed retrieval/search before the first successful tracked-target write | 127 |
| Anchors with a completed verification-class tool call | 98 |

These observations use the selected original source intervals, not whole task histories. The frozen event-v5 tool extractor supplies the retrieval/search/verification classifications. A completed call has a linked successful result under that extractor. For the ordered count, both the retrieval/search call and its successful result must occur on physical source lines strictly before the first successful tracked-target Edit/Write call. Same-line ordering is not inferred. This is an anchor-level presence inventory, not a new replay-normalized prompt or call count.

Successful tool status does not establish the adequacy of a check, functional correctness or human acceptance. Retrieval/search does not by itself establish deliberate use of the complete formal method. The 343 tokens identify historical paths, not 343 distinct deliverables or versions; several paths can contribute to one deliverable and copied content can occupy different paths.

## Documentary chains

Three previously identified correction/redelivery chains were reconstructed from private source-linked records. Selection was purposive and known before this reconstruction; it was not preregistered or outcome-blind. AI-assisted documentary coding is not an independent human review.

All three chains contain a direct corrective response and a subsequent reported revised delivery. One contains earlier explicit adoption of a scoped component. Two retained output files match their logged creation bytes exactly. Those content matches support artifact identity, not final human acceptance. A final acceptance endpoint was not recovered for any of the three chains; an unrecovered endpoint is not evidence that the work failed or was never accepted.

Three phases were distinguished for each chain: selected request to first reported delivery, reported delivery to corrective response, and corrective response to first reported revised delivery. The nine phase intervals remain private. Two chains use provider timestamps and one uses audit-capture timestamps. Their scope and clock provenance differ, so they are not pooled or presented as whole-task duration, active labor, time to acceptance or a comparative speed benefit.

Historical method/training documents support the interpretation of the workflow. Their existence does not establish attendance by particular operators. Retrospective functional correspondence to method components is distinguished from an explicit original declaration of roles or precedence.

## What remains unknown

The distinct-deliverable count, complete formal-method application count and comparative speed effect remain `null` in the summary, meaning **not established**, not zero. This adjunct adds no new human ratings and changes no event-v5 analysis inputs, primary denominator or effect estimate. The incomplete search for additional retained artifact candidates is excluded from public counts and claims.

## Public verification boundary

Run from the repository root:

```sh
python3 scripts/verify_deliverable_evidence.py
python3 -m unittest discover -s tests -p 'test_deliverable_evidence.py' -v
```

The verifier checks an exact aggregate-field allowlist, integer counts, subset bounds, accounting, required unknowns, scope statements and SHA-256 receipt syntax. Tests include malformed counts, altered scope, unexpected row-level fields, duplicate JSON keys and operation under Python optimization. They do not reconstruct withheld records, authenticate human judgments or validate documentary interpretations.

The four restricted receipts identify the private protocol, terminal register, chain evidence and method-source receipts. A correctly formed hash is not proof that the withheld source supports a claim. Prompts, context, output text, case rows, target tokens, exact timestamps and persistent source locators remain private.

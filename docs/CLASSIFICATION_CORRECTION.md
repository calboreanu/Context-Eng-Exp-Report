# Event-v5 action and artifact-reference correction

Status: corrected analytical outputs frozen and public data/code integration
verified on 18 September 2026; distributed as public package v2.0.0, dated
19 September 2026. Publication and downloaded-archive checks are separately
recorded in the [release checklist](RELEASE_CHECKLIST.md).
The submitted R1/v1.0.0 record and local v2, v3 and v4 predecessors remain
separate. This document does not retroactively alter their rules or receipts.

## Why another correction was necessary

An external counter-audit reproduced the v4 public arithmetic and artifact
checks, then identified two deterministic rule behaviors requiring repair.
Successful `TodoWrite` bookkeeping fell through the tool-name `write` substring
to `modify`, allowing a task list to count as substantive product action.
Unqualified numeric tokens such as `.05` and `.01` matched the path-like token
rule and could provide the two-reference frontloading signal. Reproduction of
the frozen implementation did not establish the semantic suitability of those
rules. Private exposure checks motivated a complete dependent rerun; synthetic
examples alone do not estimate empirical error rates or changes in effects.

## Narrow rule changes

The successor uses analytical contract
`context-engineering-event-normalized-analysis/5.0.0`, engine
`ce-primary-boundary-normalization-v5.0.0-20260918` and lexical rule
`context-engineering-eligibility/2.1.0-action-reference-20260918`.

- A supported tool-name leaf that normalizes exactly to `todowrite` is
  administrative before generic mutation matching. Supported namespace
  separators and underscore/hyphen aliases do not change its bookkeeping role.
  `TodoWriteExtra` is not that exact tool. A genuine `Write` to `TODO.md` remains
  a substantive mutation under the existing completion/success rule. Calls and
  their returned statuses are retained; bookkeeping is not erased from traces.
- A complete unqualified dot-number token, including supported exponent,
  percent and trailing sentence-punctuation forms, is not an artifact reference.
  Genuine `.env`/`.gitignore` names, qualified `./`, `../`, `/` and `~/` paths,
  numeric filenames with extensions and existing URL-like reference behavior
  are retained. Explicit `./.05` is a path; bare `.05` is not grounding evidence.
  This does not turn a lexical reference into proof of supplied content or use.

Removing administrative calls from the substantive class can change action
denominators and the location of the first substantive action. Removing numeric
references can change context routing and frontloading. Therefore eligibility,
selection, matching and all dependent summaries must be recomputed; manually
subtracting the initially exposed examples is not a valid replacement analysis.

## Unchanged boundaries and transparent interpretation

The correction does not broaden collection, infer people, add human labels,
change the historical 46-case statement or automatically validate successor
classifications. Native-identity and primary-boundary accounting remain governed
by [the normalization contract](EVENT_NORMALIZATION.md). Computational rejoin
counts are not new human correction judgments.

Condition and prompt-stage vocabulary still overlap. For example, `context
package`/`source package` can match both a bounded-package context mode and a
packaging-stage pattern; `codebase` matches a context mode and implementation
stage; `acceptance criteria`/`constraints` match a context mode and requirements
stage; retrieval instructions containing `review` or `audit` can also match the
audit stage. This is disclosed structural coupling, not proof that any exact
phrase caused an observed contrast. The literal `context package` census finds
109 resolved events in each of v4 and v5, including 25 where removing the phrase
removes the packaging trigger, but none enters either eligible condition or
either balanced construction. Those exact-phrase cases therefore cannot explain
the selected-sample contrast. This census does not establish that other
vocabulary overlap is absent.
The finite patterns still do not establish all semantic publication-purpose
exclusions or genuine requested-stage execution.

## Reproduction and reporting

Final numerical impact is recorded in
[action_reference_correction_summary.json](../analysis/results/action_reference_correction_summary.json).
All 20,965 native component identities and their resolved/held statuses remain
unchanged: 20,682 resolved events and 283 held components. Across all components,
6,788 calls are reclassified, including 6,780 successful calls in 1,522 events.
Within the fixed v4 resolved subset alone, the corresponding successful-call
exposure is 6,726 calls in 1,503 events. These denominators must not be mixed.

`measurement_changes` covers resolved and held components. It records 339
changes in the bare `automated_disposition` field. By contrast,
`fixed_v4_selection_exposure.route_or_status_changed` compares the analytical
`cohort()` result, which incorporates action/origin/publication eligibility and
condition, or the resolved/held status. Its resolved-subset count is 252; this
is a different quantity, not a contradictory recount of the 339 dispositions.
Fixed v4 primary selections contain 83 events with successful task-list calls;
eight have no remaining completed substantive action after repair. These are
computational exposure counts, not human error adjudications or estimates of
the corrected sample's error rate.

The rematched primary sample retains 789 distinct predecessor events, removes
21 and adds 69, increasing its total from 810 to 858. The unrestricted sample
retains 2,160, removes 50 and adds 294, increasing its total from 2,210 to 2,454;
39 retained events change condition. Rematching and changed first-substantive
action boundaries mean that the corrected candidate pool need not shrink.

## Submitted R1 versus final corrected analysis

This bridge compares the actually submitted R1/analysis-contract-1.0.0 record
with the final v5 outputs, rather than presenting local v4 as the submission
baseline. Historical figures are retained in [the earlier correction
record](ANALYSIS_CORRECTION.md); final selectors are in [the reviewer
guide](REVIEWER_GUIDE.md).

| Measure | Submitted R1 | Corrected v5 |
|---|---:|---:|
| Primary observations per condition | 1,484 | 429 |
| Unrestricted observations per condition | 2,246 | 1,227 |
| Primary CE verification | 693/1,484 (46.7%) | 200/429 (46.6%) |
| Primary comparison verification | 478/1,484 (32.2%) | 165/429 (38.5%) |
| Primary pooled verification difference | +14.5 pp | +8.2 pp |
| Comparator-weighted action-count diagnostic | +6.7 pp | +0.4 pp |

The differences span all intervening corrections and changed analytical units;
they are not effects attributable solely to the two v5 rule changes. All are
descriptive process-trace summaries, not deliverable-success rates or causal
method effects. The unrestricted v5 action-count diagnostic is −1.0 pp.

## What the completed checks establish

Internal source replay and numerical QA use restricted inputs
and private receipts. Public tests independently exercise fictional boundaries,
aggregate arithmetic, selectors and distributed-file identity; they do not
reconstruct private source evidence or establish semantic accuracy.

The public CLI fixture now uses a system temporary directory rather than the
repository's `tests/` directory. This avoids contaminating a later whole-tree
privacy scan when a restricted mount prevents temporary-file cleanup. The
privacy scan itself remains unchanged.

The [claim map](CLAIM_REPRODUCIBILITY.md) distinguishes public aggregate checks
from restricted reconstruction. A corrected public locator is supplied only
after a separately authorized release and downloaded-byte audit.

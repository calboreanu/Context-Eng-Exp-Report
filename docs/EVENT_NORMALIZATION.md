# Native-event and eligibility-boundary corrections

The event-v5 analysis in public package v2.0.0 follows the provider-status repair documented
in [the historical v2 correction](ANALYSIS_CORRECTION.md) and the subsequent v3
native-event reconstruction. The v4 predecessor reconciled primary boundaries
and corrected lexical inputs. V5 retains that reconstruction and additionally
corrects administrative task-list calls and bare numeric reference tokens; see
[the action/reference correction](CLASSIFICATION_CORRECTION.md). Each correction
requires dependent selection and descriptive analysis to be rerun. Neither
expands the retained collection or adds human reference judgments.

## What changed

The retained files contain 39,830 recognized text-bearing prompt occurrences.
The source-level delegated-agent filter removes 7,911, leaving 31,919 extracted
segments. A saved history, replay echo or second capture format can represent the
same native event more than once. The normalization reconciles supported
native identities, preserves attributable work and explicitly holds unresolved
cases. These are not counts of independent people, tasks or successful deliverables.

The historical v3 reconstruction retained the 6,553 previously repaired Codex
rows field-for-field and reconciled Claude-family records through native event
identity. Exact native Agent/Task parent relationships identified delegated
software-agent messages within otherwise retained files. Those relationships
are native-record evidence, not inferred human identities. V4 and v5 do not assume
that the prior Codex classifications remain unchanged.

The later source audit found a native task notification admitted as a fresh
primary invocation, XML closing tags counted as path references, a bare
acknowledgment admitted as a fresh primary invocation, and a stage keyword present only
inside historical command text. V4 applies the corrected rules across the
retained frame and rematches the analytical samples; it does not simply remove
the audited examples. Earlier source records and the frozen author-review packet
remain preserved. The complete implementation and reproduction boundary are
described in [REPRODUCE.md](../analysis/REPRODUCE.md).

The complete executable rule is [the versioned contract](../analysis/upstream_contract/EVENT_NORMALIZATION.md).
In particular:

- Repeated wording is not sufficient to merge events. Identity requires the
  documented native identifiers, replay evidence or narrowly corroborated bridge.
- Every original segment retains a private old-to-new disposition and source-line
  mapping. Unique attributable native calls are counted once; delayed results are
  returned to their call owner. Work is not discarded just because it appears only
  in a replay or a longer saved history.
- For strongly corroborated copies of a native call, a unique internally consistent
  embedded representation with resolved native parent ownership has a fixed
  provenance priority. Literal alternative classes, targets and payload hashes
  remain in the private proof. This is not a claim that different command strings
  are semantically identical. Favorable results do not choose the representation.
- Conflicting strong ownership, contradictory native representations and
  qualification-changing order ambiguity are held explicitly. The correction
  does not assert that all trajectories are uniquely reconstructed human tasks.
- Missing or inconsistent elapsed-time evidence stays missing. It is not zero,
  an absolute value, or total human labor. Timing tables publish the observed
  denominators separately from balanced sample sizes.

## How to check the numbers

[EVENT_CORRECTION_IMPACT.json](../analysis/EVENT_CORRECTION_IMPACT.json) supplies
the intake-to-event accounting, explicit exclusions, origin/route counts and the
versioned scope comparison. The current input identity and numerical
tables are in [analysis_summary.json](../analysis/results/analysis_summary.json).
The private full-reconstruction receipt is itself receipted in
[restricted_artifact_receipts.csv](../data/provenance/restricted_artifact_receipts.csv).

[action_reference_correction_summary.json](../analysis/results/action_reference_correction_summary.json)
separately compares the frozen v4 and corrected v5 measurements and analytical
membership. Its `source_accounting` distinguishes every retained source file
contributing an alias from the canonical source references attached to resolved
events. A source can contribute a resolved alias while a different source is
selected as that event's canonical representation; some sources contribute
only held events. The summary reports these overlapping roles and the exclusive
partitions separately. Consequently, subtracting canonical resolved references
from contributing alias sources does not count missing files or lost events.
The public source-frame catalog appends those aggregate counts without exposing
private source locators or native event identities.

Run `python3 scripts/run_reviewer_audit.py` to verify the public package arithmetic,
deterministic catalog, exact distributed files, disclosure boundary and fictional
regression examples. See [REPRODUCE.md](../analysis/REPRODUCE.md) for the separate
authorized-input source reconstruction and empirical pipeline. Public aggregates
cannot independently prove which private prompts or native records were present.

## Collection and interpretation limits

Records matching the frozen publication-purpose rules are excluded. This does
not establish exclusion of every publication-related task: publication context
apparent only outside the retained primary request, without a matching request
or supported native governing-task link, can remain undetected. Rejoining a
continuation to its primary owner repairs the boundary but does not independently
adjudicate that owner's semantic purpose.

The complete retained-source audit verified 5,617 copied source objects and
3,589,702 LF-delimited JSON records, including sources with no accepted episode.
The earlier ST02 "missing source" description was incorrect: the manifest entry
intentionally excludes 659 post-cutoff records with zero copied bytes and no
copied-source hash.

The collection remains availability-selected. Original inventories show 242
eligible but unselected files. A later exploratory recovery found 1,674 further
prompt occurrences but lacks individual historical cutoff receipts; it is not
silently added here. Subsequent-batch collection receipts reconcile 585,498 records
as 532,777 copied, 7,874 post-cutoff and 44,847 with invalid or missing timestamps.
The latter bytes were not retained, so their number of prompts cannot be inferred.
These are collection limits, not classifier error-rate estimates.

Native reconstruction and computational replication do not measure human
classifier agreement, causal effectiveness, deliverable quality, acceptance or
the number of distinct practitioners. Existing operational human review remains
acknowledged separately from the historical 46-case author classifier check.
The later technical findings qualify that check; they do not supply new human
judgments or establish accuracy throughout the corrected frame.

# Checking additional data points

The release is intentionally broader than the manuscript's headline table. Readers can filter the aggregate catalog by:

- primary frontloaded or unrestricted construction;
- pooled, equal-station, station-level, minimum-size, or archive-batch view;
- nine process metrics;
- pseudonymous station;
- initial versus subsequent archive capture;
- completed-action bin;
- inheritance-linkage window.

## Safe extension process

If a reviewer requests a summary not already present, record the request as a declarative aggregate specification:

1. research question and denominator;
2. allowed grouping variables;
3. metric and estimator;
4. minimum cell-size and suppression rule;
5. whether the result changes a manuscript claim.

Run that specification against the restricted data locally. Release only the resulting aggregate table after the same automated and named disclosure checks. Do not provide an unrestricted query endpoint over the row-level data, because combinations of rare cells can reconstruct trajectories even when direct identifiers are absent.

Recommended default: no new public joint table below 20 observations per reported condition, and no grouping that combines station, provider, and month. A reviewer with separately authorized controlled access can evaluate unsuppressed cells locally.

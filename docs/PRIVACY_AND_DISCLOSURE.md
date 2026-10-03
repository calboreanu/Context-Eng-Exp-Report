# Privacy and disclosure boundary

## Evidence package v2.1.0

Package v2.1.0 contains only code, rule contracts, aggregate tables, pseudonymous station summaries, transformation descriptions, and cryptographic receipts. It retains the aggregate-only boundary of v2.0.0 while adding the documentary adjunct, correspondence clarification and pilot correction. Its statistics are descriptive process-trace summaries under the frozen event-v5 analytical contract. Release metadata does not expand this disclosure boundary.

## Never included

- prompt or assistant-response text;
- source code, document contents, or command bodies recovered from conversations;
- conversation, episode, session, sample-link, or candidate-map identifiers;
- exact row-level timestamps or start/end times;
- absolute or relative source paths and source filenames;
- credentials, emails, personal names, client names, or product names;
- balanced row derivatives or the automated candidate-linkage map;
- restricted merged and normalized source inputs.

The repository may name source **fields** in order to document lineage. A field name such as `prompt_text` is not prompt content.

## Aggregate release rules

1. Only precomputed aggregate views are tracked.
2. No public table permits joining back to an episode, conversation, or exact time.
3. Pseudonymous station labels carry no public identity key.
4. The station-by-provider-by-month balancing table remains withheld because its joint cells are unnecessarily granular.
5. Restricted artifacts are represented only by SHA-256 receipts and analytic purpose.
6. Automated scanning is followed by human disclosure review; a passing script alone is not release authorization. The author confirmed the aggregate-only boundary for Version 1.0.0 on 17 August 2026.
7. Exact binary numerators are exposed where they are already deterministically recoverable from a released full-precision rate and denominator; this adds audit convenience, not row-level information.

## Interpretation boundary

The condition and five prompt-language measures share a deterministic rule family. The analysis therefore describes routed process traces and does not establish construct validity, causality, product quality, participant-level generalizability, speed, or implementation of the five-role practitioner method. The three-station inheritance result is an automated, unadjudicated candidate-linkage pilot.

## Release status

The signed internal IRAD/data-use authorization remains a separate confidential record, not a public artifact or an IRB/HRPP approval. The [pre-release audit](LOCAL_CANDIDATE_AUDIT.md) describes the frozen event-v5 checks. The author authorized v2.1.0 aggregate-only publication on 2 October 2026; the [release checklist](RELEASE_CHECKLIST.md) distinguishes this authorization and the completed pre-publication checks from actual publication and downloaded-archive verification in the versioned release notes. Public distribution does not imply confidential delivery, journal submission or editorial acceptance. Historical preparation-status fields remain unchanged as explained in the [README](../README.md).

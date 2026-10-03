# Traceability model

Traceability is provided at four levels without publishing conversation content.

## 1. Source receipts

`data/provenance/source_chain_receipts.csv` records pseudonymous archive scope, file counts, retained-intake counts, normalization receipts and input hashes. The zero-copy ST02 entry is an intentional post-cutoff exclusion, not a missing eligible source. No receipt identifies a path or conversation.

## 2. Field lineage

`data/provenance/field_lineage.csv` maps each public output field to its restricted input-field class, transformation, executable script, and function. This documents how a number was produced without disclosing the underlying value-bearing rows.

## 3. Claim mapping

`data/provenance/claim_to_evidence.csv` maps each load-bearing manuscript claim to public files and record selectors. `data/provenance/claim_selectors.json` is the executable counterpart: the verifier resolves the specified rows or section, checks required fields and record counts, and rejects disagreement with the readable map. Each verification mode distinguishes public checks from restricted reconstruction. `claim_status` is an evidence-scope category, not an unqualified correctness verdict. The compact map is in [CLAIM_REPRODUCIBILITY.md](CLAIM_REPRODUCIBILITY.md). Successful selection locates evidence; it does not compare manuscript text or validate confidential observations or human judgments.

## 4. Byte identity

`analysis/ANALYSIS_MANIFEST.sha256` binds package v2.1.0's governed analytical files, including the clarified correspondence metadata, corrected pilot and receipts for restricted artifacts that are intentionally absent. `PUBLIC_MANIFEST.sha256` covers every file in this aggregate-only package. These manifests do not replace the preserved manifests of the frozen analysis or issued v2.0.0. The former identifies governed bytes; the latter checks package completeness. Neither proves source meaning or publication. Frozen preparation-status text is distinguished from current distribution status in the [README](../README.md).

## End-to-end flow

```text
restricted archive packages
  -> locked source receipts and screening contract
  -> restricted 31,919-segment intake
  -> native-event identity, call attribution and explicit unresolved cases
  -> versioned origin, purpose, path-reference and stage-language correction
  -> restricted event-normalized frame and private old-to-new map
  -> deterministic workstation and linkage scripts
  -> restricted row derivatives
  -> aggregate CSV/JSON outputs
  -> unified public catalog and reviewer workbook
  -> public-boundary, arithmetic, and manifest validation
```

The restricted arrows can be replayed only by an authorized reviewer. The aggregate arrows are executable from this repository.

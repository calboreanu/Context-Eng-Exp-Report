# Traceability model

Traceability is provided at four levels without publishing conversation content.

## 1. Source receipts

`data/provenance/source_chain_receipts.csv` records the pseudonymous archive scope, file counts, row counts, input hash, replay result, and the known missing-source limitation. It never identifies a path or conversation.

## 2. Field lineage

`data/provenance/field_lineage.csv` maps each public output field to its restricted input-field class, transformation, executable script, and function. This documents how a number was produced without disclosing the underlying value-bearing rows.

## 3. Claim mapping

`data/provenance/claim_to_evidence.csv` maps each load-bearing manuscript claim to an exact public file and record selector. It also records whether the claim is directly aggregate-verifiable, receipt-verifiable, or interpretively bounded.

## 4. Byte identity

`analysis/ANALYSIS_MANIFEST.sha256` is the canonical receipt map from the verified local run, including hashes for governed artifacts that are intentionally absent. `PUBLIC_MANIFEST.sha256` covers every file actually included in this repository candidate. The former proves local identity; the latter proves public-package completeness.

## End-to-end flow

```text
restricted archive packages
  -> locked source receipts and screening contract
  -> restricted 31,919-row merged input
  -> deterministic workstation and linkage scripts
  -> restricted row derivatives
  -> aggregate CSV/JSON outputs
  -> unified public catalog and reviewer workbook
  -> public-boundary, arithmetic, and manifest validation
```

The restricted arrows can be replayed only by an authorized reviewer. The aggregate arrows are executable from this repository.

#!/usr/bin/env python3
"""Verify arithmetic and cross-file consistency using public aggregates only."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
CATALOG = ROOT / "data" / "catalog"
PROVENANCE = ROOT / "data" / "provenance"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def close(actual: float, expected: float, label: str, tolerance: float = 1e-12) -> None:
    require(math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance), f"{label}: {actual} != {expected}")


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def effect(ce: float, comparison: float, scale: str) -> float:
    if "risk_difference" in scale:
        return ce - comparison
    if "ratio" in scale:
        return ce / comparison
    raise RuntimeError(f"unknown effect scale {scale}")


def verify_pooled() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(RESULTS / "pooled_summary.csv")
    require(len(rows) == 18, "pooled_summary.csv must have 18 rows")
    index = {}
    for row in rows:
        key = (row["analysis_set"], row["metric"])
        require(key not in index, f"duplicate pooled row {key}")
        close(float(row["effect"]), effect(float(row["ce_value"]), float(row["comparison_value"]), row["effect_scale"]), f"pooled {key}")
        index[key] = row
    for analysis_set, expected_n in [("primary_frontloaded", 1484), ("unrestricted", 2246)]:
        subset = [row for row in rows if row["analysis_set"] == analysis_set]
        require(len(subset) == 9, f"{analysis_set}: expected nine metrics")
        require({int(row["rows_per_condition"]) for row in subset} == {expected_n}, f"{analysis_set}: denominator mismatch")
    return index


def verify_station_and_equal() -> None:
    station = read_csv(RESULTS / "station_effects.csv")
    equal = read_csv(RESULTS / "equal_station_summary.csv")
    minimum = read_csv(RESULTS / "minimum_station_size_summary.csv")
    require(len(station) == 216, "station_effects.csv must have 216 rows")
    require(len(equal) == 18 and len(minimum) == 18, "equal-station tables must each have 18 rows")
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in station:
        key = (row["analysis_set"], row["metric"])
        close(float(row["effect"]), effect(float(row["ce_value"]), float(row["comparison_value"]), row["effect_scale"]), f"station {key}/{row['station_id']}")
        grouped[key].append(row)
    require(all(len(rows) == 12 for rows in grouped.values()), "each station metric must have 12 stations")

    for row in equal:
        values = [float(item["effect"]) for item in grouped[(row["analysis_set"], row["metric"])]]
        expected = statistics.mean(values) if "risk_difference" in row["effect_scale"] else math.exp(statistics.mean(math.log(value) for value in values))
        close(float(row["effect"]), expected, f"equal station {row['analysis_set']}/{row['metric']}")
        require(int(row["stations"]) == len(values), "equal-station count mismatch")

    for row in minimum:
        base_set = row["analysis_set"].removesuffix("_min20")
        selected = [item for item in grouped[(base_set, row["metric"])] if int(item["balanced_per_condition"]) >= 20]
        values = [float(item["effect"]) for item in selected]
        expected = statistics.mean(values) if "risk_difference" in row["effect_scale"] else math.exp(statistics.mean(math.log(value) for value in values))
        close(float(row["effect"]), expected, f"minimum station {row['analysis_set']}/{row['metric']}")
        require(int(row["stations"]) == len(values), "minimum-station count mismatch")


def verify_archive() -> None:
    rows = read_csv(RESULTS / "archive_group_summary.csv")
    require(len(rows) == 36, "archive_group_summary.csv must have 36 rows")
    for row in rows:
        close(float(row["effect"]), effect(float(row["ce_value"]), float(row["comparison_value"]), row["effect_scale"]), f"archive {row['analysis_set']}/{row['archive_group']}/{row['metric']}")


def verify_action_count(pooled: dict[tuple[str, str], dict[str, str]]) -> None:
    strata = read_csv(RESULTS / "action_count_verification_strata.csv")
    require(len(strata) == 11, "action-count strata must have 11 rows")
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in strata:
        close(float(row["ce_rate"]), int(row["ce_k"]) / int(row["ce_n"]), "action CE rate")
        close(float(row["comparison_rate"]), int(row["comparison_k"]) / int(row["comparison_n"]), "action comparison rate")
        close(float(row["gap"]), float(row["ce_rate"]) - float(row["comparison_rate"]), "action gap")
        grouped[(row["analysis_set"], row["archive_batch"])].append(row)
    for key, rows in grouped.items():
        close(sum(float(row["comparison_weight"]) for row in rows), 1.0, f"action weights {key}")

    summary = json.loads((RESULTS / "action_count_verification_summary.json").read_text(encoding="utf-8"))
    require(len(summary["summaries"]) == 3, "action-count summary must have three views")
    for item in summary["summaries"]:
        key = (item["analysis_set"], item["archive_batch"])
        expected = sum(float(row["gap"]) * float(row["comparison_weight"]) for row in grouped[key])
        close(float(item["comparator_standardized_gap"]), expected, f"action standardized {key}")
        if item["archive_batch"] == "all":
            raw = float(pooled[(item["analysis_set"], "verification_successful")]["effect"])
            close(float(item["raw_gap"]), raw, f"action raw gap {key}")


def verify_inheritance() -> None:
    rows = read_csv(RESULTS / "inheritance_window_sensitivity.csv")
    summary = json.loads((RESULTS / "inheritance_pilot_summary.json").read_text(encoding="utf-8"))
    require(len(rows) == 5, "inheritance sensitivity must have five windows")
    require(sum(summary["tier_counts"].values()) == summary["scope"]["action_eligible_comparison_rows_mapped"], "inheritance tier total mismatch")
    require(sum(summary["class_counts"].values()) == summary["scope"]["action_eligible_comparison_rows_mapped"], "inheritance class total mismatch")
    by_window = {int(item["window"]): item for item in summary["sensitivity"]}
    for row in rows:
        window = int(row["window"])
        close(float(row["candidate_positive_rate"]), int(row["candidate_positive"]) / int(row["eligible_rows"]), f"inheritance window {window}")
        require(int(row["unresolved"]) == int(row["eligible_rows"]) - int(row["candidate_positive"]), f"inheritance unresolved {window}")
        require(by_window[window] == {
            "window": window,
            "candidate_positive": int(row["candidate_positive"]),
            "eligible_rows": int(row["eligible_rows"]),
            "candidate_positive_rate": float(row["candidate_positive_rate"]),
            "unresolved": int(row["unresolved"]),
        }, f"inheritance summary mismatch at {window}")


def verify_scope_and_catalog() -> None:
    analysis = json.loads((RESULTS / "analysis_summary.json").read_text(encoding="utf-8"))
    scope = analysis["scope"]
    require(scope["source_episode_rows"] == 31919, "source frame mismatch")
    require(scope["source_conversation_count"] == 4760, "conversation count mismatch")
    require(scope["source_station_archives"] == 13, "archive count mismatch")
    receipts = {row["receipt_id"]: row for row in read_csv(PROVENANCE / "source_chain_receipts.csv")}
    require(int(receipts["SRC-02"]["episode_rows"]) + int(receipts["SRC-03"]["episode_rows"]) == int(receipts["SRC-04"]["episode_rows"]), "source-frame replay arithmetic mismatch")
    require(int(receipts["SRC-04"]["episode_rows"]) == scope["source_episode_rows"], "receipt and summary frame mismatch")
    catalog = read_csv(CATALOG / "aggregate_catalog.csv")
    require(len(catalog) == 337, f"aggregate catalog expected 337 rows, got {len(catalog)}")
    require(len({row["record_id"] for row in catalog}) == len(catalog), "aggregate catalog record IDs are not unique")
    claims = read_csv(PROVENANCE / "claim_to_evidence.csv")
    require(len(claims) == 12 and len({row["claim_id"] for row in claims}) == 12, "claim map mismatch")
    for claim in claims:
        for filename in claim["evidence_file"].split(" and "):
            require((ROOT / filename).exists(), f"claim {claim['claim_id']} references missing {filename}")


def main() -> None:
    pooled = verify_pooled()
    verify_station_and_equal()
    verify_archive()
    verify_action_count(pooled)
    verify_inheritance()
    verify_scope_and_catalog()
    print("PUBLIC AGGREGATE VERIFICATION: PASS")


if __name__ == "__main__":
    main()

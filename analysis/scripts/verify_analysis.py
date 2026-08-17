#!/usr/bin/env python3
"""Deterministic integrity checks for the canonical analysis outputs.

This verifier consumes restricted row-level derivatives. It is not an aggregate-only
public verifier and cannot regenerate source-frame counts without the restricted merged
input. It checks that retained derivatives and staged aggregate point summaries agree.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path


COMPARISON = "ROUTED_COMPARISON_ACTION"
BINARY_METRICS = [
    "verification_successful",
    "audit_signal",
    "remediation_signal",
    "packaging_release_signal",
    "multistage_signal",
    "grounded_decision_trace",
]
RATIO_METRICS = ["duration_min", "completed_substantive_actions", "min_per_action"]


def fail(message: str) -> None:
    raise RuntimeError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def close(actual: float, expected: float, label: str, tolerance: float = 1e-12) -> None:
    require(
        math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance),
        f"{label}: expected {expected!r}, got {actual!r}",
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing required file: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_balanced(path: Path, expected_ce: str) -> tuple[list[dict[str, str]], dict[str, int]]:
    rows = read_csv(path)
    by_link: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_link[row["sample_link_id"]].append(row)
    require(bool(by_link), f"{path.name}: no sample links")
    require(
        {row["cohort"] for row in rows} == {expected_ce, COMPARISON},
        f"{path.name}: unexpected cohort labels",
    )
    for link, linked in by_link.items():
        require(len(linked) == 2, f"{path.name}/{link}: expected two rows")
        require({row["cohort"] for row in linked} == {expected_ce, COMPARISON},
                f"{path.name}/{link}: missing condition")
        for field in ("station_id", "provider", "month"):
            require(len({row[field] for row in linked}) == 1,
                    f"{path.name}/{link}: unbalanced {field}")
    for index, row in enumerate(rows, start=2):
        actions = int(row["completed_substantive_actions"])
        duration = float(row["duration_min"])
        require(actions > 0, f"{path.name}:{index}: non-positive action denominator")
        close(float(row["min_per_action"]), duration / actions,
              f"{path.name}:{index}: minutes/action")
        stages = set(filter(None, row["stage_signal_mask"].split("|")))
        require(int(row["multistage_signal"]) == int(len(stages) >= 2),
                f"{path.name}:{index}: multistage mismatch")
        if row["cohort"] == expected_ce and expected_ce.startswith("CE_FRONTLOADED"):
            require(row["frontloaded_context_candidate"] == "yes",
                    f"{path.name}:{index}: primary CE row is not frontloaded")
    return rows, {"rows": len(rows), "links": len(by_link)}


def verify_strata(results: Path, rows_by_set: dict[str, list[dict[str, str]]]) -> None:
    staged = read_csv(results / "balanced_strata.csv")
    selected: Counter[tuple[str, str, str, str]] = Counter()
    for analysis_set, rows in rows_by_set.items():
        for row in rows:
            if row["cohort"] != COMPARISON:
                selected[(analysis_set, row["station_id"], row["provider"], row["month"])] += 1
    require(len(staged) == len(selected), "balanced_strata.csv: row-count mismatch")
    for row in staged:
        key = (row["analysis_set"], row["station_id"], row["provider"], row["month"])
        require(key in selected, f"balanced_strata.csv: unexpected stratum {key}")
        balanced = int(row["balanced_per_condition"])
        require(selected[key] == balanced, f"balanced_strata.csv: selected count mismatch for {key}")
        require(int(row["ce_available"]) >= balanced and int(row["comparison_available"]) >= balanced,
                f"balanced_strata.csv: availability below selected count for {key}")


def expected_pooled(rows: list[dict[str, str]], ce_label: str) -> dict[str, tuple[float, float, float, int]]:
    ce = [row for row in rows if row["cohort"] == ce_label]
    comparison = [row for row in rows if row["cohort"] == COMPARISON]
    require(len(ce) == len(comparison) and len(ce) > 0, "pooled: unequal condition totals")
    output: dict[str, tuple[float, float, float, int]] = {}
    for metric in BINARY_METRICS:
        ce_value = sum(int(row[metric]) for row in ce) / len(ce)
        comparison_value = sum(int(row[metric]) for row in comparison) / len(comparison)
        output[metric] = (ce_value, comparison_value, ce_value - comparison_value, len(ce))
    for metric in RATIO_METRICS:
        ce_value = statistics.median(float(row[metric]) for row in ce)
        comparison_value = statistics.median(float(row[metric]) for row in comparison)
        output[metric] = (ce_value, comparison_value, ce_value / comparison_value, len(ce))
    return output


def verify_pooled(results: Path, rows_by_set: dict[str, list[dict[str, str]]]) -> None:
    labels = {
        "unrestricted": "CE_ORDERED_ACTION",
        "primary_frontloaded": "CE_FRONTLOADED_ORDERED_ACTION",
    }
    expected = {key: expected_pooled(rows_by_set[key], labels[key]) for key in labels}
    staged = read_csv(results / "pooled_summary.csv")
    require(len(staged) == 18, "pooled_summary.csv: expected 18 rows")
    seen: set[tuple[str, str]] = set()
    for row in staged:
        key = (row["analysis_set"], row["metric"])
        require(key not in seen, f"pooled_summary.csv: duplicate {key}")
        seen.add(key)
        require(row["analysis_set"] in expected and row["metric"] in expected[row["analysis_set"]],
                f"pooled_summary.csv: unexpected {key}")
        ce_value, comp_value, effect, count = expected[row["analysis_set"]][row["metric"]]
        close(float(row["ce_value"]), ce_value, f"pooled {key} CE")
        close(float(row["comparison_value"]), comp_value, f"pooled {key} comparison")
        close(float(row["effect"]), effect, f"pooled {key} effect")
        require(int(row["rows_per_condition"]) == count, f"pooled {key}: count mismatch")


def verify_inheritance(results: Path) -> int:
    rows = read_csv(results / "restricted" / "inheritance_candidate_map.csv")
    require(len(rows) == 3_502, "inheritance map: expected 3,502 rows")
    require({row["human_review_status"] for row in rows} == {"pending"},
            "inheritance map: human-review status changed")
    tiers = Counter(row["evidence_tier"] for row in rows)
    classes = Counter(row["mapping_class"] for row in rows)
    summary = json.loads((results / "inheritance_pilot_summary.json").read_text(encoding="utf-8"))
    require(summary["scope"].get("prior_ce_predecessor_dispositions")
            == ["candidate_strong", "candidate_probable"],
            "inheritance summary: predecessor dispositions must disclose strong-or-probable pilot scope")
    require(dict(sorted(tiers.items())) == dict(sorted(summary["tier_counts"].items())),
            "inheritance map: tier counts differ from summary")
    require(dict(sorted(classes.items())) == dict(sorted(summary["class_counts"].items())),
            "inheritance map: class counts differ from summary")
    eligible = [row for row in rows if row["evidence_tier"] != "CLEAN_ORIGIN_CANDIDATE"]
    require(len(eligible) == 3_326, "inheritance map: expected 3,326 eligible rows")
    for item in summary["sensitivity"]:
        window = int(item["window"])
        # evidence_tier records the primary 20-prompt rule. Sensitivity rows are
        # reconstructed from each row's minimum qualifying window, including rows
        # that are unresolved at 20 but become positive at 50 or 106.
        positive = sum(
            row["minimum_link_window"] != ""
            and int(row["minimum_link_window"]) <= window
            for row in eligible
        )
        require(positive == int(item["candidate_positive"]),
                f"inheritance window {window}: candidate-positive mismatch")
        require(len(eligible) - positive == int(item["unresolved"]),
                f"inheritance window {window}: unresolved mismatch")
    return next(item["candidate_positive"] for item in summary["sensitivity"] if item["window"] == 20)


def verify_action_count(results: Path) -> None:
    script = Path(__file__).with_name("derive_action_count_verification.py")
    require(script.is_file(), f"missing action-count script: {script}")
    with tempfile.TemporaryDirectory(prefix="ce-action-count-verify-") as temp:
        out = Path(temp)
        command = [
            sys.executable,
            str(script),
            "--primary", str(results / "restricted" / "primary_balanced_rows.csv"),
            "--unrestricted", str(results / "restricted" / "unrestricted_balanced_rows.csv"),
            "--out-dir", str(out),
        ]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        require(completed.returncode == 0,
                f"action-count regeneration failed: {completed.stderr.strip()}")
        for name in ("action_count_verification_strata.csv", "action_count_verification_summary.json"):
            expected = results / name
            regenerated = out / name
            require(expected.is_file(), f"missing staged action-count output: {expected}")
            require(expected.read_bytes() == regenerated.read_bytes(),
                    f"{name}: staged bytes differ from deterministic regeneration")


def scan_public_candidates(results: Path) -> None:
    names = [
        "analysis_summary.json", "pooled_summary.csv", "station_effects.csv",
        "equal_station_summary.csv", "archive_group_summary.csv", "balanced_strata.csv",
        "inheritance_pilot_summary.json", "inheritance_window_sensitivity.csv",
        "minimum_station_size_summary.csv", "action_count_verification_strata.csv",
        "action_count_verification_summary.json",
    ]
    forbidden = ["prompt_text", "prompt_excerpt", "/Users/", "@theswiftgroup.com"]
    for name in names:
        path = results / name
        require(path.is_file(), f"missing aggregate output: {path}")
        content = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            require(pattern not in content, f"{name}: forbidden pattern {pattern!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True, type=Path)
    args = parser.parse_args()

    unrestricted_rows, unrestricted = verify_balanced(
        args.results / "restricted" / "unrestricted_balanced_rows.csv", "CE_ORDERED_ACTION"
    )
    primary_rows, primary = verify_balanced(
        args.results / "restricted" / "primary_balanced_rows.csv", "CE_FRONTLOADED_ORDERED_ACTION"
    )
    rows_by_set = {"unrestricted": unrestricted_rows, "primary_frontloaded": primary_rows}
    verify_strata(args.results, rows_by_set)
    verify_pooled(args.results, rows_by_set)

    summary = json.loads((args.results / "analysis_summary.json").read_text(encoding="utf-8"))
    scope = summary["scope"]
    require(scope["unrestricted_balanced_per_condition"] == unrestricted["links"],
            "analysis_summary: unrestricted balance mismatch")
    require(scope["primary_frontloaded_balanced_per_condition"] == primary["links"],
            "analysis_summary: primary balance mismatch")

    candidate_positive = verify_inheritance(args.results)
    verify_action_count(args.results)
    scan_public_candidates(args.results)

    print(json.dumps({
        "unrestricted": unrestricted,
        "primary": primary,
        "pooled_point_summaries": "recomputed from restricted balanced rows",
        "inheritance_primary_candidate_positive": candidate_positive,
        "action_count_outputs": "byte-identical regeneration",
        "source_frame_counts": "receipt only; raw merged input required for regeneration",
        "status": "PASS",
    }, indent=2))


if __name__ == "__main__":
    main()

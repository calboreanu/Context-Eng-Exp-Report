#!/usr/bin/env python3
"""Run the canonical workstation-trajectory analysis for the new submission.

The analysis is intentionally descriptive. It constructs two deterministic,
one-to-one balanced samples within station x provider x calendar-month strata:

* unrestricted: all rule-defined CE candidates with an ordered context trace;
* primary: the CE pool is first restricted by the frontloaded-context rule.

Rows are not matched on task, artifact, source conversation, complexity, or
operator. The mechanical one-to-one link is used only to balance counts within
exact strata. Station is an archive cluster, not a participant proxy.

The source CSV is restricted because it contains raw prompt text. Row-level
outputs produced here remain restricted and contain no prompt text or excerpts.
Only disclosure-approved aggregate outputs are included in the public release.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


FRONTLOAD_MODES = {
    "bounded_package",
    "multi_source_synthesis",
    "standards_constraints",
    "examples_templates",
}

ORIGIN = "direct_or_unresolved_user_level"
CE_DISPOSITION = "candidate_strong"
COMPARISON_DISPOSITION = "exclude_no_context_operation"
CE_LABEL = "CE_ORDERED_ACTION"
PRIMARY_CE_LABEL = "CE_FRONTLOADED_ORDERED_ACTION"
COMPARISON_LABEL = "ROUTED_COMPARISON_ACTION"
MIN_STATION_SENSITIVITY_SIZE = 20

BINARY_METRICS = [
    ("verification_successful", "Completed-successful verification call"),
    ("audit_signal", "Audit-stage prompt signal"),
    ("remediation_signal", "Remediation-stage prompt signal"),
    ("packaging_release_signal", "Packaging/release-stage prompt signal"),
    ("multistage_signal", "At least two distinct stage prompt signals"),
    ("grounded_decision_trace", "Grounded-decision trace proxy"),
]

RATIO_METRICS = [
    ("duration_min", "Median observed trajectory minutes"),
    ("completed_substantive_actions", "Median completed substantive actions"),
    ("min_per_action", "Median minutes per completed substantive action"),
]

RESTRICTED_FIELDS = [
    "analysis_set",
    "sample_link_id",
    "cohort",
    "episode_token",
    "station_id",
    "provider",
    "month",
    "frontloaded_context_candidate",
    "stage_signal_mask",
    "duration_min",
    "completed_substantive_actions",
    "min_per_action",
    *[field for field, _ in BINARY_METRICS],
]

csv.field_size_limit(sys.maxsize)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path, help="Restricted merged episode CSV")
    parser.add_argument("--out", required=True, type=Path, help="Output directory")
    parser.add_argument("--bootstrap-reps", type=int, default=50_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260815)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_rank(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def token(prefix: str, value: str) -> str:
    return f"{prefix}-" + hashlib.sha256(("new-submission-v1|" + value).encode()).hexdigest()[:16]


def as_int(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def median(values: list[float]) -> float:
    return statistics.median(values)


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def percentile(sorted_values: list[float], q: float) -> float:
    position = (len(sorted_values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def bootstrap_mean_ci(values: list[float], reps: int, seed: int, salt: str) -> tuple[float, float]:
    salted_seed = int(hashlib.sha256(f"{seed}:{salt}".encode()).hexdigest()[:16], 16)
    rng = random.Random(salted_seed)
    size = len(values)
    draws = [mean([values[rng.randrange(size)] for _ in range(size)]) for _ in range(reps)]
    draws.sort()
    return percentile(draws, 0.025), percentile(draws, 0.975)


def exact_two_sided_sign_p(positive: int, negative: int) -> float:
    n = positive + negative
    if n == 0:
        return math.nan
    k = min(positive, negative)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2 * tail)


def yes(value: object) -> int:
    return 1 if str(value).lower() == "yes" else 0


def frontloaded(row: dict[str, str]) -> bool:
    modes = set(filter(None, row.get("context_mode_mask", "").split("|")))
    return (
        as_int(row.get("attachment_count")) > 0
        or as_int(row.get("prompt_artifact_reference_count")) >= 2
        or bool(modes & FRONTLOAD_MODES)
    )


def completed_successful_verification(row: dict[str, str]) -> int:
    try:
        trace = json.loads(row.get("tool_trace_json", "[]"))
    except json.JSONDecodeError:
        trace = []
    return int(any(
        item.get("class") == "verify" and item.get("completed") and item.get("succeeded")
        for item in trace
    ))


def transform(row: dict[str, str]) -> dict[str, object]:
    start = parse_dt(row["timestamp_start_utc"])
    end = parse_dt(row["timestamp_end_utc"])
    actions = as_int(row.get("completed_substantive_action_calls"))
    duration = max(0.0, (end - start).total_seconds() / 60.0)
    stages = set(filter(None, row.get("stage_signal_mask", "").split("|")))
    return {
        "episode_id": row["episode_id"],
        "episode_token": token("EP", row["episode_id"]),
        "station_id": row["station_id"],
        "provider": row["provider"],
        "month": start.strftime("%Y-%m"),
        "origin_candidate": row.get("origin_candidate", ""),
        "automated_disposition": row.get("automated_disposition", ""),
        "publication_exclusion_candidate": row.get("publication_exclusion_candidate", ""),
        "frontloaded_context_candidate": "yes" if frontloaded(row) else "no",
        "stage_signal_mask": "|".join(sorted(stages)),
        "duration_min": duration,
        "completed_substantive_actions": actions,
        "min_per_action": duration / actions if actions > 0 else None,
        "verification_successful": completed_successful_verification(row),
        "audit_signal": int("audit" in stages),
        "remediation_signal": int("remediation" in stages),
        "packaging_release_signal": int("packaging_release" in stages),
        "multistage_signal": int(len(stages) >= 2),
        "grounded_decision_trace": yes(row.get("grounded_decision_trace")),
    }


def cohort(row: dict[str, object]) -> str:
    # Requiring at least one completed-successful substantive action removes the
    # prior selection path in which the grounded-decision proxy qualified itself.
    if row["completed_substantive_actions"] <= 0:
        return ""
    if row["origin_candidate"] != ORIGIN:
        return ""
    if row["publication_exclusion_candidate"] == "yes":
        return ""
    if row["automated_disposition"] == CE_DISPOSITION:
        return CE_LABEL
    if row["automated_disposition"] == COMPARISON_DISPOSITION:
        return COMPARISON_LABEL
    return ""


def balance(ce_rows: list[dict[str, object]], comparison_rows: list[dict[str, object]], analysis_set: str):
    by_ce: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    by_comparison: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in ce_rows:
        by_ce[(row["station_id"], row["provider"], row["month"])].append(row)
    for row in comparison_rows:
        by_comparison[(row["station_id"], row["provider"], row["month"])].append(row)

    links = []
    strata = []
    for stratum in sorted(set(by_ce) & set(by_comparison)):
        left = sorted(by_ce[stratum], key=lambda item: stable_rank(str(item["episode_id"])))
        right = sorted(by_comparison[stratum], key=lambda item: stable_rank(str(item["episode_id"])))
        size = min(len(left), len(right))
        strata.append({
            "analysis_set": analysis_set,
            "station_id": stratum[0],
            "provider": stratum[1],
            "month": stratum[2],
            "ce_available": len(left),
            "comparison_available": len(right),
            "balanced_per_condition": size,
        })
        for index in range(size):
            link_id = token(
                "LINK",
                f"{analysis_set}|{stratum}|{left[index]['episode_id']}|{right[index]['episode_id']}",
            )
            links.append((link_id, left[index], right[index]))
    return links, strata


def restricted_rows(links, analysis_set: str, ce_label: str) -> list[dict[str, object]]:
    rows = []
    for link_id, ce_row, comparison_row in links:
        for item, label in ((ce_row, ce_label), (comparison_row, COMPARISON_LABEL)):
            exported = {field: item.get(field, "") for field in RESTRICTED_FIELDS}
            exported.update({"analysis_set": analysis_set, "sample_link_id": link_id, "cohort": label})
            rows.append(exported)
    return rows


def metric_value(row: dict[str, object], field: str) -> float:
    value = row[field]
    if value is None:
        return math.nan
    return float(value)


def split_conditions(rows: list[dict[str, object]], ce_label: str):
    ce = [row for row in rows if row["cohort"] == ce_label]
    comparison = [row for row in rows if row["cohort"] == COMPARISON_LABEL]
    return ce, comparison


def pooled_summary(rows: list[dict[str, object]], analysis_set: str, ce_label: str) -> list[dict[str, object]]:
    ce, comparison = split_conditions(rows, ce_label)
    result = []
    for field, label in BINARY_METRICS:
        ce_value = mean([metric_value(row, field) for row in ce])
        comp_value = mean([metric_value(row, field) for row in comparison])
        result.append({
            "analysis_set": analysis_set,
            "metric": field,
            "metric_label": label,
            "effect_scale": "risk_difference",
            "ce_value": ce_value,
            "comparison_value": comp_value,
            "effect": ce_value - comp_value,
            "rows_per_condition": len(ce),
        })
    for field, label in RATIO_METRICS:
        ce_value = median([metric_value(row, field) for row in ce])
        comp_value = median([metric_value(row, field) for row in comparison])
        result.append({
            "analysis_set": analysis_set,
            "metric": field,
            "metric_label": label,
            "effect_scale": "ratio_of_condition_medians",
            "ce_value": ce_value,
            "comparison_value": comp_value,
            "effect": ce_value / comp_value if comp_value > 0 else math.nan,
            "rows_per_condition": len(ce),
        })
    return result


def station_effects(rows: list[dict[str, object]], analysis_set: str, ce_label: str):
    by_station: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_station[str(row["station_id"])].append(row)
    effects = []
    for station in sorted(by_station):
        ce, comparison = split_conditions(by_station[station], ce_label)
        if len(ce) != len(comparison):
            raise RuntimeError(f"Unbalanced station in {analysis_set}: {station}")
        for field, label in BINARY_METRICS:
            ce_value = mean([metric_value(row, field) for row in ce])
            comp_value = mean([metric_value(row, field) for row in comparison])
            effects.append({
                "analysis_set": analysis_set,
                "station_id": station,
                "balanced_per_condition": len(ce),
                "metric": field,
                "metric_label": label,
                "effect_scale": "risk_difference",
                "ce_value": ce_value,
                "comparison_value": comp_value,
                "effect": ce_value - comp_value,
            })
        for field, label in RATIO_METRICS:
            ce_value = median([metric_value(row, field) for row in ce])
            comp_value = median([metric_value(row, field) for row in comparison])
            effects.append({
                "analysis_set": analysis_set,
                "station_id": station,
                "balanced_per_condition": len(ce),
                "metric": field,
                "metric_label": label,
                "effect_scale": "median_ratio",
                "ce_value": ce_value,
                "comparison_value": comp_value,
                "effect": ce_value / comp_value if comp_value > 0 else math.nan,
            })
    return effects


def equal_station_summary(effects: list[dict[str, object]], analysis_set: str, reps: int, seed: int):
    by_metric: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in effects:
        by_metric[str(row["metric"])].append(row)
    summary = []
    for field, label in BINARY_METRICS:
        values = [float(row["effect"]) for row in by_metric[field]]
        positive = sum(value > 1e-12 for value in values)
        negative = sum(value < -1e-12 for value in values)
        ties = len(values) - positive - negative
        low, high = bootstrap_mean_ci(values, reps, seed, f"{analysis_set}:{field}")
        summary.append({
            "analysis_set": analysis_set,
            "metric": field,
            "metric_label": label,
            "effect_scale": "equal_station_mean_risk_difference",
            "stations": len(values),
            "effect": mean(values),
            "ci_low": low,
            "ci_high": high,
            "positive_stations": positive,
            "tie_stations": ties,
            "negative_stations": negative,
            "descriptive_sign_p": exact_two_sided_sign_p(positive, negative),
        })
    for field, label in RATIO_METRICS:
        ratios = [float(row["effect"]) for row in by_metric[field] if float(row["effect"]) > 0]
        log_values = [math.log(value) for value in ratios]
        positive = sum(value > 1 + 1e-12 for value in ratios)
        negative = sum(value < 1 - 1e-12 for value in ratios)
        ties = len(ratios) - positive - negative
        low, high = bootstrap_mean_ci(log_values, reps, seed, f"{analysis_set}:{field}")
        summary.append({
            "analysis_set": analysis_set,
            "metric": field,
            "metric_label": label,
            "effect_scale": "equal_station_geometric_mean_median_ratio",
            "stations": len(ratios),
            "effect": math.exp(mean(log_values)),
            "ci_low": math.exp(low),
            "ci_high": math.exp(high),
            "positive_stations": positive,
            "tie_stations": ties,
            "negative_stations": negative,
            "descriptive_sign_p": exact_two_sided_sign_p(positive, negative),
        })
    return summary


def archive_group_summary(rows: list[dict[str, object]], analysis_set: str, ce_label: str):
    groups = {
        "initial_capture_ST00_ST02": {"ST00", "ST01", "ST02"},
        "subsequent_capture_ST04_ST13": {"ST04", "ST05", "ST06", "ST07", "ST08", "ST09", "ST10", "ST11", "ST12", "ST13"},
    }
    result = []
    for group, stations in groups.items():
        subset = [row for row in rows if row["station_id"] in stations]
        ce, comparison = split_conditions(subset, ce_label)
        for field, label in BINARY_METRICS:
            ce_value = mean([metric_value(row, field) for row in ce])
            comp_value = mean([metric_value(row, field) for row in comparison])
            effect = ce_value - comp_value
            scale = "risk_difference"
            result.append({
                "analysis_set": analysis_set,
                "archive_group": group,
                "rows_per_condition": len(ce),
                "contributing_stations": len({row["station_id"] for row in ce}),
                "metric": field,
                "metric_label": label,
                "effect_scale": scale,
                "ce_value": ce_value,
                "comparison_value": comp_value,
                "effect": effect,
            })
        for field, label in RATIO_METRICS:
            ce_value = median([metric_value(row, field) for row in ce])
            comp_value = median([metric_value(row, field) for row in comparison])
            result.append({
                "analysis_set": analysis_set,
                "archive_group": group,
                "rows_per_condition": len(ce),
                "contributing_stations": len({row["station_id"] for row in ce}),
                "metric": field,
                "metric_label": label,
                "effect_scale": "ratio_of_condition_medians",
                "ce_value": ce_value,
                "comparison_value": comp_value,
                "effect": ce_value / comp_value if comp_value > 0 else math.nan,
            })
    return result


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    restricted_dir = args.out / "restricted"
    restricted_dir.mkdir(parents=True, exist_ok=True)

    transformed = []
    all_source_refs = set()
    all_stations = set()
    with args.input.open(newline="", encoding="utf-8") as handle:
        for source_row in csv.DictReader(handle):
            transformed.append(transform(source_row))
            all_source_refs.add(source_row["source_ref"])
            all_stations.add(source_row["station_id"])

    ce = [row for row in transformed if cohort(row) == CE_LABEL]
    comparison = [row for row in transformed if cohort(row) == COMPARISON_LABEL]
    frontloaded_ce = [row for row in ce if row["frontloaded_context_candidate"] == "yes"]

    unrestricted_links, unrestricted_strata = balance(ce, comparison, "unrestricted")
    primary_links, primary_strata = balance(frontloaded_ce, comparison, "primary_frontloaded")
    unrestricted_rows = restricted_rows(unrestricted_links, "unrestricted", CE_LABEL)
    primary_rows = restricted_rows(primary_links, "primary_frontloaded", PRIMARY_CE_LABEL)

    write_csv(restricted_dir / "unrestricted_balanced_rows.csv", unrestricted_rows, RESTRICTED_FIELDS)
    write_csv(restricted_dir / "primary_balanced_rows.csv", primary_rows, RESTRICTED_FIELDS)
    write_csv(args.out / "balanced_strata.csv", unrestricted_strata + primary_strata)

    pooled = pooled_summary(unrestricted_rows, "unrestricted", CE_LABEL)
    pooled += pooled_summary(primary_rows, "primary_frontloaded", PRIMARY_CE_LABEL)
    effects = station_effects(unrestricted_rows, "unrestricted", CE_LABEL)
    effects += station_effects(primary_rows, "primary_frontloaded", PRIMARY_CE_LABEL)
    equal_station = equal_station_summary(
        [row for row in effects if row["analysis_set"] == "unrestricted"],
        "unrestricted",
        args.bootstrap_reps,
        args.bootstrap_seed,
    )
    equal_station += equal_station_summary(
        [row for row in effects if row["analysis_set"] == "primary_frontloaded"],
        "primary_frontloaded",
        args.bootstrap_reps,
        args.bootstrap_seed,
    )
    archive_groups = archive_group_summary(unrestricted_rows, "unrestricted", CE_LABEL)
    archive_groups += archive_group_summary(primary_rows, "primary_frontloaded", PRIMARY_CE_LABEL)
    minimum_station_size = equal_station_summary(
        [
            row for row in effects
            if row["analysis_set"] == "unrestricted"
            and int(row["balanced_per_condition"]) >= MIN_STATION_SENSITIVITY_SIZE
        ],
        f"unrestricted_min{MIN_STATION_SENSITIVITY_SIZE}",
        args.bootstrap_reps,
        args.bootstrap_seed,
    )
    minimum_station_size += equal_station_summary(
        [
            row for row in effects
            if row["analysis_set"] == "primary_frontloaded"
            and int(row["balanced_per_condition"]) >= MIN_STATION_SENSITIVITY_SIZE
        ],
        f"primary_frontloaded_min{MIN_STATION_SENSITIVITY_SIZE}",
        args.bootstrap_reps,
        args.bootstrap_seed,
    )

    write_csv(args.out / "pooled_summary.csv", pooled)
    write_csv(args.out / "station_effects.csv", effects)
    write_csv(args.out / "equal_station_summary.csv", equal_station)
    write_csv(args.out / "archive_group_summary.csv", archive_groups)
    write_csv(args.out / "minimum_station_size_summary.csv", minimum_station_size)

    scope = {
        "source_episode_rows": len(transformed),
        "source_conversation_count": len(all_source_refs),
        "source_station_archives": len(all_stations),
        "action_eligible_ce_candidates": len(ce),
        "action_eligible_frontloaded_ce_candidates": len(frontloaded_ce),
        "action_eligible_routed_comparisons": len(comparison),
        "unrestricted_balanced_per_condition": len(unrestricted_links),
        "primary_frontloaded_balanced_per_condition": len(primary_links),
        "unrestricted_contributing_stations": len({item[1]["station_id"] for item in unrestricted_links}),
        "primary_contributing_stations": len({item[1]["station_id"] for item in primary_links}),
    }
    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_contract": "context-engineering-new-submission-analysis/1.0.0",
        "input": {
            "filename": args.input.name,
            "sha256": sha256_file(args.input),
            "bytes": args.input.stat().st_size,
            "restricted": True,
        },
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "third_party_libraries": [],
        },
        "bootstrap": {
            "repetitions": args.bootstrap_reps,
            "base_seed": args.bootstrap_seed,
            "metric_seed": "first 64 bits of SHA-256(base_seed:analysis_set:metric)",
            "percentile_method": "linear interpolation at (N-1)q",
            "ratio_scale": "log station-median ratios, exponentiated after bootstrap",
        },
        "definitions": {
            "action_eligibility": "at least one completed and successful modify, execute, or verify call",
            "frontloaded_context_candidate": "attachment_count>0 OR prompt_artifact_reference_count>=2 OR context_mode_mask intersects bounded_package|multi_source_synthesis|standards_constraints|examples_templates",
            "verification_successful": "at least one verify-class call that completed and succeeded",
            "audit_remediation_packaging": "case-insensitive prompt-regex stage signals inherited from the frozen screen; lexical candidate measures, not adjudicated execution",
            "multistage_signal": "at least two distinct entries in stage_signal_mask",
            "grounded_decision_trace": "screen proxy; stage signal plus completed retrieval/search plus assistant output length threshold",
            "min_per_action": "observed trajectory minutes divided by completed substantive actions; all retained cohort rows have a positive denominator",
            "balancing": "deterministic one-to-one sampling within station_id x provider x calendar month; not task matching",
        },
        "scope": scope,
        "limitations": [
            "Condition assignment and prompt-stage outcomes share a deterministic rule family.",
            "Prompt-stage signals are unadjudicated lexical proxies.",
            "Exact-stratum balancing does not match task, artifact, source conversation, complexity, or operator.",
            "Station archives are clusters, not participants; operator identity and overlap are unavailable.",
            "Observed trajectory minutes are not total labor or project completion time.",
            "Station bootstrap intervals and sign tests are descriptive sensitivities, not population inference.",
        ],
        "pooled_summary": pooled,
        "equal_station_summary": equal_station,
        "minimum_station_size_summary": minimum_station_size,
    }
    (args.out / "analysis_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scope, indent=2))


if __name__ == "__main__":
    main()

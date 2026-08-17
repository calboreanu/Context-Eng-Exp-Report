#!/usr/bin/env python3
"""Derive the post hoc action-count verification diagnostic.

Inputs are restricted balanced-row derivatives, not the raw merged episode table.
Outputs contain only the aggregate counts already reported in Supplementary Table S3
and its subsequent-archive-batch sensitivity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


COMPARISON = "ROUTED_COMPARISON_ACTION"
INITIAL_STATIONS = {"ST00", "ST01", "ST02"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def in_bin(actions: int, lower: int, upper: int | None) -> bool:
    return actions >= lower and (upper is None or actions <= upper)


def condition(row: dict[str, str]) -> str:
    return "comparison" if row["cohort"] == COMPARISON else "ce"


def summarize(
    rows: list[dict[str, str]],
    analysis_set: str,
    archive_batch: str,
    bins: list[tuple[str, int, int | None]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    output: list[dict[str, object]] = []
    total_comparison = sum(condition(row) == "comparison" for row in rows)
    total_ce = sum(condition(row) == "ce" for row in rows)
    if total_ce != total_comparison or total_ce == 0:
        raise RuntimeError(
            f"{analysis_set}/{archive_batch}: expected positive equal condition totals, "
            f"got CE={total_ce}, comparison={total_comparison}"
        )

    standardized = 0.0
    for label, lower, upper in bins:
        selected = [
            row for row in rows
            if in_bin(int(row["completed_substantive_actions"]), lower, upper)
        ]
        ce = [row for row in selected if condition(row) == "ce"]
        comparison = [row for row in selected if condition(row) == "comparison"]
        if not ce or not comparison:
            raise RuntimeError(f"{analysis_set}/{archive_batch}/{label}: empty condition bin")
        ce_k = sum(int(row["verification_successful"]) for row in ce)
        comparison_k = sum(int(row["verification_successful"]) for row in comparison)
        ce_rate = ce_k / len(ce)
        comparison_rate = comparison_k / len(comparison)
        gap = ce_rate - comparison_rate
        weight = len(comparison) / total_comparison
        standardized += gap * weight
        output.append({
            "analysis_set": analysis_set,
            "archive_batch": archive_batch,
            "action_bin": label,
            "ce_k": ce_k,
            "ce_n": len(ce),
            "ce_rate": ce_rate,
            "comparison_k": comparison_k,
            "comparison_n": len(comparison),
            "comparison_rate": comparison_rate,
            "gap": gap,
            "comparison_weight": weight,
        })

    ce_k = sum(int(row["verification_successful"]) for row in rows if condition(row) == "ce")
    comparison_k = sum(
        int(row["verification_successful"])
        for row in rows if condition(row) == "comparison"
    )
    raw_gap = ce_k / total_ce - comparison_k / total_comparison
    summary = {
        "analysis_set": analysis_set,
        "archive_batch": archive_batch,
        "rows_per_condition": total_ce,
        "raw_gap": raw_gap,
        "comparator_standardized_gap": standardized,
        "diagnostic_only": True,
    }
    return output, summary


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", required=True, type=Path)
    parser.add_argument("--unrestricted", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    primary = read_rows(args.primary)
    unrestricted = read_rows(args.unrestricted)
    four_bins = [("1-2", 1, 2), ("3-5", 3, 5), ("6-10", 6, 10), ("11+", 11, None)]
    coarse_bins = [("1-2", 1, 2), ("3-5", 3, 5), ("6+", 6, None)]

    rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for source, analysis_set in (
        (primary, "primary_frontloaded"),
        (unrestricted, "unrestricted"),
    ):
        part, summary = summarize(source, analysis_set, "all", four_bins)
        rows.extend(part)
        summaries.append(summary)

    subsequent = [row for row in primary if row["station_id"] not in INITIAL_STATIONS]
    part, summary = summarize(
        subsequent,
        "primary_frontloaded",
        "subsequent_capture_ST04_ST13",
        coarse_bins,
    )
    rows.extend(part)
    summaries.append(summary)

    csv_path = args.out_dir / "action_count_verification_strata.csv"
    json_path = args.out_dir / "action_count_verification_summary.json"
    write_csv(csv_path, rows)
    payload = {
        "analysis_contract": "ce-action-count-verification-diagnostic/1.0.0",
        "inputs": {
            args.primary.name: sha256_file(args.primary),
            args.unrestricted.name: sha256_file(args.unrestricted),
        },
        "definition": (
            "Post hoc comparator-weighted within-action-bin verification diagnostic. "
            "Action count includes verify calls and is post-exposure; this is not a "
            "confounding adjustment or effect decomposition."
        ),
        "summaries": summaries,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"csv": str(csv_path), "json": str(json_path)}, indent=2))


if __name__ == "__main__":
    main()

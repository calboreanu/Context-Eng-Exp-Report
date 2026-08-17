#!/usr/bin/env python3
"""Exercise the restricted-input analysis path with generated fictional rows.

The fixture is created inside an operating-system temporary directory and is
deleted automatically.  It contains no real prompt, response, path, timestamp,
identifier, or workstation record.  Its purpose is structural: demonstrate
that the published source-level scripts accept a documented input shape and
produce the expected aggregate and restricted-intermediate file families.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "scripts"
ACTION_COUNTS = [1, 2, 3, 4, 5, 6, 8, 10, 11, 12] * 2
FIELDS = [
    "episode_id", "source_ref", "station_id", "provider",
    "timestamp_start_utc", "timestamp_end_utc", "origin_candidate",
    "automated_disposition", "publication_exclusion_candidate",
    "completed_substantive_action_calls", "context_mode_mask",
    "attachment_count", "prompt_artifact_reference_count",
    "stage_signal_mask", "grounded_decision_trace", "tool_trace_json",
    "session_ref", "turn_index", "source_line_start", "prompt_words",
    "prompt_text",
]


def synthetic_trace(actions: int, verified: bool) -> str:
    trace = [
        {
            "class": "modify",
            "completed": True,
            "succeeded": True,
            "target_ref": "synthetic-target.txt",
        }
        for _ in range(max(0, actions - int(verified)))
    ]
    if verified:
        trace.append({
            "class": "verify",
            "completed": True,
            "succeeded": True,
            "target_ref": "synthetic-target.txt",
        })
    return json.dumps(trace, separators=(",", ":"))


def build_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    episode = 0
    for station_index, station in enumerate(("ST00", "ST04")):
        session = f"fictional-session-{station}"
        turn = 0
        if station == "ST00":
            episode += 1
            turn += 1
            rows.append({
                "episode_id": f"fictional-{episode:03d}",
                "source_ref": "fictional-source-00",
                "station_id": station,
                "provider": "synthetic-provider",
                "timestamp_start_utc": "2026-01-15T12:00:00Z",
                "timestamp_end_utc": "2026-01-15T12:05:00Z",
                "origin_candidate": "direct_or_unresolved_user_level",
                "automated_disposition": "candidate_probable",
                "publication_exclusion_candidate": "no",
                "completed_substantive_action_calls": 1,
                "context_mode_mask": "bounded_package",
                "attachment_count": 0,
                "prompt_artifact_reference_count": 0,
                "stage_signal_mask": "implementation",
                "grounded_decision_trace": "no",
                "tool_trace_json": synthetic_trace(1, False),
                "session_ref": session,
                "turn_index": turn,
                "source_line_start": turn,
                "prompt_words": 3,
                "prompt_text": "SYNTHETIC-100 start synthetic-target.txt",
            })

        for index, actions in enumerate(ACTION_COUNTS):
            for disposition in ("candidate_strong", "exclude_no_context_operation"):
                episode += 1
                turn += 1
                is_ce = disposition == "candidate_strong"
                verified = (index + station_index + int(is_ce)) % 3 != 0
                stages = "audit|remediation" if is_ce else "implementation"
                rows.append({
                    "episode_id": f"fictional-{episode:03d}",
                    "source_ref": f"fictional-source-{station_index}-{index // 5}",
                    "station_id": station,
                    "provider": "synthetic-provider",
                    "timestamp_start_utc": "2026-01-15T12:00:00Z",
                    "timestamp_end_utc": f"2026-01-15T12:{min(59, actions + 5):02d}:00Z",
                    "origin_candidate": "direct_or_unresolved_user_level",
                    "automated_disposition": disposition,
                    "publication_exclusion_candidate": "no",
                    "completed_substantive_action_calls": actions,
                    "context_mode_mask": "bounded_package" if is_ce else "",
                    "attachment_count": 0,
                    "prompt_artifact_reference_count": 0,
                    "stage_signal_mask": stages,
                    "grounded_decision_trace": "yes" if is_ce else "no",
                    "tool_trace_json": synthetic_trace(actions, verified),
                    "session_ref": session,
                    "turn_index": turn,
                    "source_line_start": turn,
                    "prompt_words": 4,
                    "prompt_text": "SYNTHETIC-100 continue synthetic-target.txt",
                })
    return rows


def run(*args: str) -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stdout + completed.stderr)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ce-fictional-smoke-") as directory:
        work = Path(directory)
        source = work / "fictional_input.csv"
        results = work / "results"
        with source.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(build_rows())

        run(
            str(ANALYSIS / "run_workstation_analysis.py"),
            "--input", str(source), "--out", str(results),
            "--bootstrap-reps", "200", "--bootstrap-seed", "20260817",
        )
        run(
            str(ANALYSIS / "derive_action_count_verification.py"),
            "--primary", str(results / "restricted" / "primary_balanced_rows.csv"),
            "--unrestricted", str(results / "restricted" / "unrestricted_balanced_rows.csv"),
            "--out-dir", str(results),
        )
        run(
            str(ANALYSIS / "run_inheritance_pilot.py"),
            "--input", str(source), "--out", str(work / "inheritance"),
        )

        summary = json.loads((results / "analysis_summary.json").read_text(encoding="utf-8"))
        scope = summary["scope"]
        if scope["source_episode_rows"] != 81:
            raise RuntimeError(f"unexpected fictional source row count: {scope}")
        if scope["primary_frontloaded_balanced_per_condition"] != 40:
            raise RuntimeError(f"unexpected fictional primary balance: {scope}")
        if scope["primary_contributing_stations"] != 2:
            raise RuntimeError(f"unexpected fictional station count: {scope}")

        linkage = json.loads(
            (work / "inheritance" / "inheritance_pilot_summary.json").read_text(encoding="utf-8")
        )
        if linkage["scope"]["prior_ce_predecessor_dispositions"] != [
            "candidate_strong", "candidate_probable"
        ]:
            raise RuntimeError("linkage predecessor contract was not exercised")
        if linkage["scope"]["eligible_rows_with_prior_action_eligible_ce"] < 1:
            raise RuntimeError("fictional linkage fixture produced no eligible row")

        required = {
            "pooled_summary.csv", "station_effects.csv", "equal_station_summary.csv",
            "archive_group_summary.csv", "minimum_station_size_summary.csv",
            "action_count_verification_strata.csv", "action_count_verification_summary.json",
        }
        missing = sorted(name for name in required if not (results / name).is_file())
        if missing:
            raise RuntimeError("missing fictional outputs: " + ", ".join(missing))

    print("SYNTHETIC SOURCE PIPELINE: PASS")
    print("Generated fictional rows were deleted; no prompt or trajectory fixture was retained.")


if __name__ == "__main__":
    main()

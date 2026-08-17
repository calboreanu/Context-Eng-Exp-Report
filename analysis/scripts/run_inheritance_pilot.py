#!/usr/bin/env python3
"""Build the action-eligible inherited-context candidate linkage pilot.

This is an automated candidate map, not an adjudicated classification. It uses
the three initial station archives because only that capture batch has the
required session-continuity representation used by the pilot.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


csv.field_size_limit(sys.maxsize)

RULE_VERSION = "ce-inheritance-map/2.0.0-action-eligible-pilot"
STATIONS = {"ST00", "ST01", "ST02"}
# The linkage pilot deliberately uses a broader predecessor pool than the
# balanced CE arm: either automated CE-candidate disposition can establish a
# prior in-session context candidate.  The balanced arm remains strong-only.
PILOT_CE_PREDECESSOR_DISPOSITIONS = ("candidate_strong", "candidate_probable")
CE_DISPOSITIONS = set(PILOT_CE_PREDECESSOR_DISPOSITIONS)
COMPARISON_DISPOSITION = "exclude_no_context_operation"
WINDOWS = [5, 10, 20, 50, 106]
PRIMARY_WINDOW = 20

CONTINUATION_REFERENCE_RE = re.compile(
    r"\b(?:continue|again|same|previous|prior|original|current|above|"
    r"what (?:we|you) (?:built|did)|what we built|these|those|this|that|it|them|"
    r"findings|rest|next|rerun|re-run|retest|re-audit|fix|update|apply|verify|audit|"
    r"complete|finish|keep going|go ahead|do it|start building|still|more|all of it|"
    r"everything found|one more)\b",
    re.IGNORECASE,
)
TICKET_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,11}-\d+\b")
PATH_RE = re.compile(r"(?<!\w)(?:/[^\s\"'<>|]+)")
FILE_RE = re.compile(
    r"\b[\w.@+-]{3,}\.(?:md|txt|json|jsonl|csv|tsv|xlsx|xls|docx|pdf|tex|"
    r"py|mjs|cjs|js|jsx|ts|tsx|html|css|yaml|yml|toml|sh|zip)\b",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def token(prefix: str, value: str) -> str:
    return f"{prefix}-" + hashlib.sha256(("inheritance-pilot-v2|" + value).encode()).hexdigest()[:16]


def as_int(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def completed_target_refs(raw: str) -> set[str]:
    try:
        trace = json.loads(raw or "[]")
    except json.JSONDecodeError:
        trace = []
    return {
        str(item["target_ref"])
        for item in trace
        if item.get("target_ref") and item.get("completed") and item.get("succeeded")
    }


def prompt_anchors(text: str) -> set[str]:
    anchors = {f"ticket:{item.upper()}" for item in TICKET_RE.findall(text or "")}
    for item in PATH_RE.findall(text or ""):
        normalized = item.rstrip(".,;:!?)]}").lower()
        if len(normalized) >= 8:
            anchors.add(f"path:{normalized}")
    anchors.update(f"file:{item.lower()}" for item in FILE_RE.findall(text or ""))
    return anchors


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    restricted = args.out / "restricted"
    restricted.mkdir(parents=True, exist_ok=True)

    source_rows = []
    with args.input.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["station_id"] not in STATIONS:
                continue
            row["_turn"] = as_int(row.get("turn_index"))
            row["_line"] = as_int(row.get("source_line_start"))
            row["_actions"] = as_int(row.get("completed_substantive_action_calls"))
            row["_targets"] = completed_target_refs(row.get("tool_trace_json", ""))
            row["_anchors"] = prompt_anchors(row.get("prompt_text", ""))
            source_rows.append(row)

    sessions: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in source_rows:
        sessions[str(row["session_ref"])].append(row)
    for rows in sessions.values():
        rows.sort(key=lambda item: (item["_turn"], item["_line"]))

    mapped = []
    for session_id in sorted(sessions):
        last_ce = None
        previous_was_ce = False
        target_to_ce = {}
        anchor_to_ce = {}
        for row in sessions[session_id]:
            disposition = str(row["automated_disposition"])
            action_eligible = int(row["_actions"]) > 0
            ce_eligible = action_eligible and disposition in CE_DISPOSITIONS

            if action_eligible and disposition == COMPARISON_DISPOSITION:
                current_targets = set(row["_targets"])
                current_anchors = set(row["_anchors"])
                shared_targets = sorted(current_targets & set(target_to_ce))
                shared_anchors = sorted(current_anchors & set(anchor_to_ce))
                prompt_words = as_int(row.get("prompt_words"))
                prompt_text = str(row.get("prompt_text", ""))
                reference_cue = bool(CONTINUATION_REFERENCE_RE.search(prompt_text))

                if last_ce is None:
                    mapping_class = "CLEAN_ORIGIN_CANDIDATE"
                    tier = "CLEAN_ORIGIN_CANDIDATE"
                    turn_distance = None
                    minimum_window = None
                    matched_prior = ""
                else:
                    turn_distance = int(row["_turn"]) - int(last_ce["turn"])
                    linked_candidates = [target_to_ce[item] for item in shared_targets]
                    linked_candidates += [anchor_to_ce[item] for item in shared_anchors]
                    matched_prior_row = max(linked_candidates, key=lambda item: int(item["turn"])) if linked_candidates else last_ce
                    matched_prior = str(matched_prior_row["episode_token"])
                    immediate_short = previous_was_ce and prompt_words <= 30 and reference_cue
                    if shared_targets:
                        mapping_class = "EXACT_SUCCESSFUL_TOOL_TARGET"
                        tier = "HIGH_CONFIDENCE_CANDIDATE"
                        minimum_window = 0
                    elif shared_anchors:
                        mapping_class = "EXACT_PROMPT_ANCHOR"
                        tier = "HIGH_CONFIDENCE_CANDIDATE"
                        minimum_window = 0
                    elif immediate_short:
                        mapping_class = "IMMEDIATE_SHORT_REFERENCE"
                        tier = "HIGH_CONFIDENCE_CANDIDATE"
                        minimum_window = 0
                    elif previous_was_ce:
                        mapping_class = "IMMEDIATE_ADJACENCY"
                        tier = "PROBABLE_CANDIDATE"
                        minimum_window = 1
                    elif reference_cue and turn_distance <= PRIMARY_WINDOW:
                        mapping_class = "CONTEXT_REFERENCE_WITHIN_20"
                        tier = "PROBABLE_CANDIDATE"
                        minimum_window = turn_distance
                    elif turn_distance <= 3:
                        mapping_class = "NEAR_SEQUENCE"
                        tier = "PROBABLE_CANDIDATE"
                        minimum_window = turn_distance
                    else:
                        mapping_class = "UNRESOLVED_PRIOR_CE_SESSION"
                        tier = "UNRESOLVED"
                        # Preserve the observed distance for window sensitivity
                        # when an explicit continuation cue exists beyond the
                        # primary 20-prompt boundary.
                        minimum_window = turn_distance if reference_cue else None

                mapped.append({
                    "mapping_id": token("MAP", str(row["episode_id"])),
                    "episode_token": token("EP", str(row["episode_id"])),
                    "station_id": row["station_id"],
                    "provider": row["provider"],
                    "session_token": token("SESSION", session_id),
                    "turn_index": row["_turn"],
                    "matched_prior_ce_token": matched_prior,
                    "turn_distance_from_latest_ce": "" if turn_distance is None else turn_distance,
                    "shared_successful_tool_targets": len(shared_targets),
                    "shared_prompt_anchors": len(shared_anchors),
                    "explicit_continuation_reference": "yes" if reference_cue else "no",
                    "mapping_class": mapping_class,
                    "evidence_tier": tier,
                    "minimum_link_window": "" if minimum_window is None else minimum_window,
                    "human_review_status": "pending",
                    "rule_version": RULE_VERSION,
                })

            if ce_eligible:
                candidate = {
                    "episode_token": token("EP", str(row["episode_id"])),
                    "turn": row["_turn"],
                }
                last_ce = candidate
                for target in set(row["_targets"]):
                    target_to_ce[target] = candidate
                for anchor in set(row["_anchors"]):
                    anchor_to_ce[anchor] = candidate
            previous_was_ce = ce_eligible

    write_csv(restricted / "inheritance_candidate_map.csv", mapped)
    tier_counts = Counter(row["evidence_tier"] for row in mapped)
    class_counts = Counter(row["mapping_class"] for row in mapped)
    eligible = len(mapped) - tier_counts["CLEAN_ORIGIN_CANDIDATE"]
    sensitivity = []
    for window in WINDOWS:
        positive = sum(
            row["evidence_tier"] == "HIGH_CONFIDENCE_CANDIDATE"
            or (
                row["evidence_tier"] in {"PROBABLE_CANDIDATE", "UNRESOLVED"}
                and row["minimum_link_window"] != ""
                and int(row["minimum_link_window"]) <= window
            )
            for row in mapped
        )
        sensitivity.append({
            "window": window,
            "candidate_positive": positive,
            "eligible_rows": eligible,
            "candidate_positive_rate": positive / eligible if eligible else 0,
            "unresolved": eligible - positive,
        })
    write_csv(args.out / "inheritance_window_sensitivity.csv", sensitivity)

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "rule_version": RULE_VERSION,
        "status": "automated_unadjudicated_candidate_linkage_pilot",
        "input": {
            "filename": args.input.name,
            "sha256": sha256_file(args.input),
            "restricted": True,
        },
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "third_party_libraries": [],
        },
        "scope": {
            "source_rows_three_stations": len(source_rows),
            "action_eligible_comparison_rows_mapped": len(mapped),
            "prior_ce_predecessor_dispositions": list(PILOT_CE_PREDECESSOR_DISPOSITIONS),
            "eligible_rows_with_prior_action_eligible_ce": eligible,
            "clean_origin_candidates": tier_counts["CLEAN_ORIGIN_CANDIDATE"],
            "high_confidence_candidates": tier_counts["HIGH_CONFIDENCE_CANDIDATE"],
            "probable_candidates": tier_counts["PROBABLE_CANDIDATE"],
            "unresolved_primary_rule": tier_counts["UNRESOLVED"],
        },
        "class_counts": dict(sorted(class_counts.items())),
        "tier_counts": dict(sorted(tier_counts.items())),
        "primary_window": PRIMARY_WINDOW,
        "sensitivity": sensitivity,
        "rule_precedence": [
            "exact successful tool-target continuity",
            "exact prompt ticket/path/file anchor continuity",
            "immediate <=30-word explicit continuation reference",
            "immediate adjacency",
            "explicit continuation reference within 20 prompt episodes",
            "same-session proximity within three prompt episodes",
            "unresolved prior-CE session",
        ],
        "limitations": [
            "Every linkage label is automated and pending accountable human review.",
            "Adjacency and lexical continuation cues are candidate evidence, not proof of inheritance.",
            "The pilot is limited to three station archives and is not additive with the 13-station balanced analysis.",
        ],
    }
    (args.out / "inheritance_pilot_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["scope"], indent=2))


if __name__ == "__main__":
    main()

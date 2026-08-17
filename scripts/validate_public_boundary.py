#!/usr/bin/env python3
"""Fail closed on common disclosure errors in the repository candidate."""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from pathlib import Path


IGNORED_DIRS = {".git", ".private", "node_modules", "outputs", "tmp", "__pycache__"}
FORBIDDEN_PATH_PARTS = {"raw", "restricted", "interim", "prompts"}
FORBIDDEN_FILENAMES = {
    "balanced_strata.csv", "primary_balanced_rows.csv", "unrestricted_balanced_rows.csv",
    "inheritance_candidate_map.csv", "extended_multistation_context_episode_review.local.csv",
}
ALLOWED_BINARY_SUFFIXES = {".xlsx"}
TEXT_SUFFIXES = {".cff", ".csv", ".json", ".md", ".py", ".sha256", ".txt", ".yml", ".yaml"}
TEXT_FILENAMES = {".gitattributes", ".gitignore", "LICENSE"}
ROW_LEVEL_FIELDS = {
    "episode_id", "prompt_text", "prompt_excerpt", "session_ref", "source_ref",
    "timestamp_start_utc", "timestamp_end_utc", "tool_trace_json", "target_ref",
    "sample_link_id", "mapping_id", "prior_ce_episode_id",
}
ABSOLUTE_PATHS = [
    re.compile(r"/(?:Users|home)/[^/\s]+/"),
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\"),
]
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
TOKENS = {
    "GitHub token": re.compile(r"\b(?:gh[pousr]|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "row identifier": re.compile(r"\b(?:EP|LINK|SESSION|MAP)-[A-Za-z0-9]{8,}\b"),
}


def nested_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from nested_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from nested_keys(item)


def files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def scan_text(label: str, text: str, findings: list[str], *, allow_row_field_names: bool = False) -> None:
    for pattern in ABSOLUTE_PATHS:
        if pattern.search(text):
            findings.append(f"{label}: absolute user path")
    if EMAIL.search(text):
        findings.append(f"{label}: email address")
    for name, pattern in TOKENS.items():
        if pattern.search(text):
            findings.append(f"{label}: possible {name}")
    if not allow_row_field_names and any(field in text for field in ROW_LEVEL_FIELDS):
        findings.append(f"{label}: possible row-level field name")


def scan_workbook(path: Path, findings: list[str]) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if any(name.startswith("xl/externalLinks/") for name in names):
                findings.append(f"{path}: external workbook link")
            if any(name.endswith("vbaProject.bin") for name in names):
                findings.append(f"{path}: workbook macro")
            for name in sorted(names):
                if not name.endswith(".xml"):
                    continue
                text = archive.read(name).decode("utf-8", errors="replace")
                scan_text(f"{path}:{name}", text, findings)
    except zipfile.BadZipFile:
        findings.append(f"{path}: invalid xlsx container")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    findings: list[str] = []

    for path in files(root):
        relative = path.relative_to(root)
        parts = {part.lower() for part in relative.parts}
        if parts & FORBIDDEN_PATH_PARTS:
            findings.append(f"{relative}: forbidden path component")
        if path.name in FORBIDDEN_FILENAMES or path.name.endswith(".local.csv"):
            findings.append(f"{relative}: forbidden raw or row-level filename")
        suffix = path.suffix.lower()
        if suffix in ALLOWED_BINARY_SUFFIXES:
            scan_workbook(path, findings)
            continue
        if suffix not in TEXT_SUFFIXES and path.name not in TEXT_FILENAMES:
            findings.append(f"{relative}: unapproved binary or file type")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        scan_text(str(relative), text, findings, allow_row_field_names=suffix in {".md", ".py"})
        if suffix == ".csv":
            with path.open(newline="", encoding="utf-8", errors="replace") as handle:
                header = next(csv.reader(handle), [])
            leaked = sorted(set(header) & ROW_LEVEL_FIELDS)
            if leaked:
                findings.append(f"{relative}: row-level columns {', '.join(leaked)}")
        elif suffix == ".json":
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                findings.append(f"{relative}: invalid JSON")
            else:
                leaked = sorted(set(nested_keys(value)) & ROW_LEVEL_FIELDS)
                if leaked:
                    findings.append(f"{relative}: row-level JSON keys {', '.join(leaked)}")

    if findings:
        print("PUBLIC BOUNDARY: FAIL")
        for finding in sorted(set(findings)):
            print(f"- {finding}")
        raise SystemExit(1)
    print("PUBLIC BOUNDARY: PASS")


if __name__ == "__main__":
    main()

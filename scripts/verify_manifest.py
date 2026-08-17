#!/usr/bin/env python3
"""Verify a two-space-delimited SHA-256 manifest and exact file coverage."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


EXCLUDED_DIRS = {".git", ".private", "node_modules", "outputs", "tmp", "__pycache__"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    root = manifest.parent
    expected: dict[str, str] = {}
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            sha, relative = line.split("  ", 1)
        except ValueError as error:
            raise SystemExit(f"Malformed manifest line {line_number}") from error
        expected[relative] = sha

    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != manifest
        and not any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts)
    }
    if actual != set(expected):
        raise SystemExit(f"Manifest coverage mismatch: missing={sorted(actual-set(expected))} extra={sorted(set(expected)-actual)}")
    for relative, sha in sorted(expected.items()):
        observed = digest(root / relative)
        if observed != sha:
            raise SystemExit(f"Hash mismatch: {relative}")
    print(f"MANIFEST: PASS ({len(expected)} files)")


if __name__ == "__main__":
    main()

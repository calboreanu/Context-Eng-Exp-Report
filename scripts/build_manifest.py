#!/usr/bin/env python3
"""Write a sorted SHA-256 manifest for the release candidate."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "PUBLIC_MANIFEST.sha256"
EXCLUDED_DIRS = {".git", ".private", "node_modules", "outputs", "tmp", "__pycache__"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    paths = [
        path for path in ROOT.rglob("*")
        if path.is_file()
        and path != OUTPUT
        and not any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts)
    ]
    lines = [f"{digest(path)}  {path.relative_to(ROOT).as_posix()}" for path in sorted(paths)]
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.name} with {len(lines)} files.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run the complete public reviewer audit from a fresh checkout."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_FILES = [
    ROOT / "data" / "catalog" / "aggregate_catalog.csv",
    ROOT / "data" / "catalog" / "source_frame_summary.csv",
    ROOT / "data" / "catalog" / "data_dictionary.csv",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(label: str, *args: str) -> None:
    print(f"\n[{label}] {' '.join(args)}", flush=True)
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, *args], cwd=ROOT, env=environment, check=False
    )
    if completed.returncode:
        raise SystemExit(f"REVIEWER AUDIT: FAIL during {label}")


def main() -> None:
    before = {path: digest(path) for path in CATALOG_FILES}
    run("deterministic catalog", "scripts/build_public_catalog.py")
    after = {path: digest(path) for path in CATALOG_FILES}
    changed = [path.relative_to(ROOT).as_posix() for path in CATALOG_FILES if before[path] != after[path]]
    if changed:
        raise SystemExit("REVIEWER AUDIT: FAIL; catalog rebuild changed " + ", ".join(changed))

    run("aggregate arithmetic", "scripts/verify_public_release.py")
    run("disclosure boundary", "scripts/validate_public_boundary.py", ".")
    run("exact file manifest", "scripts/verify_manifest.py", "PUBLIC_MANIFEST.sha256")
    run("unit and fictional-source tests", "-m", "unittest", "discover", "-s", "tests", "-v")
    print("\nREVIEWER AUDIT: PASS")
    print("The released aggregates are internally reproducible and the confidential-source boundary is intact.")


if __name__ == "__main__":
    main()

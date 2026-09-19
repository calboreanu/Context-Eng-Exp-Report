#!/usr/bin/env python3
"""Build only event-normalized Figure 4 (file fig-06) from aggregate results.

The graphical abstract and other manuscript figures are unchanged typesetting
artifacts and are deliberately not rebuilt by this portable entry point.
Matplotlib is a figure-only dependency; the four empirical/verification scripts
remain standard-library-only.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys


def main() -> None:
    scripts = Path(__file__).resolve().parent
    analysis = scripts.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=analysis.parent / "outputs" / "figures",
        help="Destination for Figure 4 PDF (file fig-06; default: repository outputs/figures).",
    )
    args = parser.parse_args()
    inputs = {
        "--analysis-summary": analysis / "results" / "analysis_summary.json",
        "--inheritance-summary": analysis / "results" / "inheritance_pilot_summary.json",
    }
    for path in inputs.values():
        if not path.is_file():
            parser.error(f"Required adjacent aggregate input is missing: {path}")
    if importlib.util.find_spec("matplotlib") is None:
        parser.error("Figure 4 requires Matplotlib; install it in this Python environment.")
    command = [sys.executable, str(scripts / "gen_fig06_house.py")]
    for flag, path in inputs.items():
        command.extend([flag, str(path)])
    command.extend(["--output-dir", str(args.output_dir.resolve())])
    subprocess.run(command, check=True)
    print("Built event-normalized Figure 4 (file fig-06) only; the graphical abstract was not rebuilt.")


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SyntheticAnalysisTests(unittest.TestCase):
    def test_fictional_source_pipeline(self):
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_synthetic_smoke.py")],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("SYNTHETIC SOURCE PIPELINE: PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()

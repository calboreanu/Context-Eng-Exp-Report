from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicReleaseTests(unittest.TestCase):
    def run_script(self, name: str, *args: str) -> str:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / name), *args],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        return completed.stdout

    def test_aggregate_verifier(self):
        self.assertIn("PASS", self.run_script("verify_public_release.py"))

    def test_public_boundary(self):
        self.assertIn("PASS", self.run_script("validate_public_boundary.py", "."))


if __name__ == "__main__":
    unittest.main()

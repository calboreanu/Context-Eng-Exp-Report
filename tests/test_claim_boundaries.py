"""Public claim labels distinguish evidence scope from a correctness verdict."""
import csv
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClaimBoundaryLabels(unittest.TestCase):
    def setUp(self):
        with (ROOT / 'data/provenance/claim_to_evidence.csv').open(newline='') as stream:
            self.rows = list(csv.DictReader(stream))

    def test_every_claim_has_explicit_public_and_restricted_scope(self):
        self.assertEqual(len(self.rows), 12)
        for row in self.rows:
            self.assertIn('public ', row['verification_mode'])
            if row['claim_id'] != 'CE-C12':
                self.assertIn('restricted ', row['verification_mode'])

    def test_status_is_scope_not_unqualified_verified_label(self):
        allowed = {'receipt_backed_scope', 'aggregate_checkable', 'aggregate_recomputable',
                   'bounded_aggregate', 'receipt_backed_limitation', 'interpretation_boundary'}
        self.assertEqual({row['claim_status'] for row in self.rows}, allowed)

    def test_source_claims_are_receipt_backed_not_public_source_replays(self):
        rows = {row['claim_id']: row for row in self.rows}
        self.assertEqual(rows['CE-C01']['claim_status'], 'receipt_backed_scope')
        self.assertEqual(rows['CE-C11']['claim_status'], 'receipt_backed_limitation')
        self.assertIn('restricted source replay', rows['CE-C01']['verification_mode'])
        self.assertIn('public receipt inspection', rows['CE-C11']['verification_mode'])


if __name__ == '__main__':
    unittest.main()

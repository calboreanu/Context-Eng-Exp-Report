"""Fictional receipt fixtures exercise public/withheld analytical manifest bindings."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('receipt_release_verifier', ROOT / 'scripts/verify_public_release.py')
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class ReleaseReceiptTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.analysis = {'input': {'sha256': 'a' * 64, 'bytes': 100},
                         'normalization_receipt': {'sha256': 'b' * 64}}
        self.impact = {'normalization_receipt_sha256': 'b' * 64}
        identifiers = ['R-INPUT', 'R-STRATA', 'R-PRIMARY', 'R-UNRESTRICTED', 'R-LINKAGE',
                       'R-ALIASES', 'R-QUARANTINE', 'R-NORMALIZATION', 'R-BOUNDARIES',
                       'R-REVIEW46', 'R-PRIMARY-REJOIN', 'R-HISTORY-REJOIN', 'R-ACTION-REFERENCE']
        self.artifacts = [{'artifact_id': name, 'bytes': '100', 'sha256': 'a' * 64,
                           'release_status': 'withheld'} for name in identifiers]
        self.artifacts[7]['sha256'] = 'b' * 64
        self.manifest = []
        for name in ['results/analysis_summary.json', 'results/boundary_correction_summary.json',
                     'results/action_reference_correction_summary.json',
                     'EVENT_CORRECTION_IMPACT.json']:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{}\n')
            self.manifest.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {name}')
        for name in ['results/balanced_strata.csv', 'results/restricted/primary_balanced_rows.csv',
                     'results/restricted/unrestricted_balanced_rows.csv', 'results/restricted/inheritance_candidate_map.csv']:
            self.manifest.append(f'{"a" * 64}  {name}')
        self.write_manifest()

    def write_manifest(self):
        (self.root / 'ANALYSIS_MANIFEST.sha256').write_text('\n'.join(self.manifest) + '\n')

    def verify(self):
        VERIFY.verify_analysis_receipts(self.analysis, self.impact, self.artifacts, self.root)

    def test_exact_fictional_public_and_withheld_identities_pass(self):
        self.verify()

    def test_duplicate_receipt_id_rejected(self):
        self.artifacts[-1]['artifact_id'] = 'R-INPUT'
        with self.assertRaisesRegex(RuntimeError, 'receipt IDs'):
            self.verify()

    def test_input_bytes_or_hash_mismatch_rejected(self):
        for field, value in [('bytes', '101'), ('sha256', 'c' * 64)]:
            with self.subTest(field=field):
                original = self.artifacts[0][field]
                self.artifacts[0][field] = value
                with self.assertRaisesRegex(RuntimeError, 'input receipt'):
                    self.verify()
                self.artifacts[0][field] = original

    def test_normalization_receipt_mismatch_rejected(self):
        self.impact['normalization_receipt_sha256'] = 'c' * 64
        with self.assertRaisesRegex(RuntimeError, 'normalization receipt'):
            self.verify()

    def test_changed_public_file_rejected(self):
        (self.root / 'results/analysis_summary.json').write_text('{"changed":true}\n')
        with self.assertRaisesRegex(RuntimeError, 'public analytical manifest mismatch'):
            self.verify()

    def test_missing_public_file_rejected(self):
        (self.root / 'results/analysis_summary.json').unlink()
        with self.assertRaisesRegex(RuntimeError, 'missing public analytical'):
            self.verify()

    def test_changed_withheld_receipt_rejected(self):
        self.artifacts[1]['sha256'] = 'c' * 64
        with self.assertRaisesRegex(RuntimeError, 'withheld receipt'):
            self.verify()

    def test_accidentally_included_withheld_file_rejected(self):
        (self.root / 'results/balanced_strata.csv').write_text('fictional\n')
        with self.assertRaisesRegex(RuntimeError, 'withheld analytical file is present'):
            self.verify()

    def test_undeclared_missing_file_rejected(self):
        self.manifest.append(f'{"c" * 64}  results/other.json')
        self.write_manifest()
        with self.assertRaisesRegex(RuntimeError, 'missing public analytical'):
            self.verify()

    def test_duplicate_manifest_path_rejected(self):
        self.manifest.append(self.manifest[0])
        self.write_manifest()
        with self.assertRaisesRegex(RuntimeError, 'duplicated analytical'):
            self.verify()

    def test_manifest_escape_rejected(self):
        self.manifest.append(f'{"c" * 64}  ../outside.json')
        self.write_manifest()
        with self.assertRaisesRegex(RuntimeError, 'unsafe or duplicated'):
            self.verify()

    def test_required_withheld_output_must_be_manifested(self):
        self.manifest.pop()
        self.write_manifest()
        with self.assertRaisesRegex(RuntimeError, 'omits expected withheld'):
            self.verify()


if __name__ == '__main__':
    unittest.main()

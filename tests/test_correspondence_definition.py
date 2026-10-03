"""Fictional correspondence distinctions, never human-validation labels."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('correspondence_verifier', ROOT / 'scripts/verify_public_release.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class CorrespondenceDefinition(unittest.TestCase):
    def classify(self, measurements=None, aliases=False, labels=None,
                 before='resolved', after='resolved'):
        return CHECK.correspondence_change_flags(
            [] if measurements is None else measurements, aliases,
            {} if labels is None else labels, before, after)

    def test_identical_tracked_record_is_strictly_and_substantively_unchanged(self):
        self.assertEqual(self.classify(), {
            'same_measured_trajectory_and_labels': True,
            'strict_status_inclusive_unchanged': True,
            'provenance_status_only': False})

    def test_status_rename_alone_does_not_change_tracked_evidence(self):
        self.assertEqual(self.classify(before='v2_codex_unchanged'), {
            'same_measured_trajectory_and_labels': True,
            'strict_status_inclusive_unchanged': False,
            'provenance_status_only': True})

    def test_alias_change_is_not_a_status_only_change(self):
        result = self.classify(aliases=True, before='v2_codex_unchanged')
        self.assertFalse(result['same_measured_trajectory_and_labels'])
        self.assertFalse(result['provenance_status_only'])

    def test_changed_source_measurement_counts_even_without_derived_label_change(self):
        result = self.classify(measurements=['prompt_artifact_reference_count'])
        self.assertFalse(result['same_measured_trajectory_and_labels'])
        self.assertFalse(result['strict_status_inclusive_unchanged'])
        self.assertFalse(result['provenance_status_only'])

    def test_derived_label_change_is_not_a_status_only_change(self):
        result = self.classify(labels={'audit_signal': {'v3': False, 'v5': True}},
                               before='v2_codex_unchanged')
        self.assertFalse(result['same_measured_trajectory_and_labels'])
        self.assertFalse(result['provenance_status_only'])

    def test_multiple_substantive_changes_do_not_create_extra_case_categories(self):
        result = self.classify(measurements=['prompt_text'], aliases=True,
                               labels={'frontloaded_context_candidate': {'v3': True, 'v5': False}},
                               before='v2_codex_unchanged')
        self.assertEqual(result, {
            'same_measured_trajectory_and_labels': False,
            'strict_status_inclusive_unchanged': False,
            'provenance_status_only': False})

    def test_status_only_flag_does_not_invent_human_confirmation(self):
        self.assertEqual(set(self.classify(before='v2_codex_unchanged')),
                         {'same_measured_trajectory_and_labels',
                          'strict_status_inclusive_unchanged', 'provenance_status_only'})

    def test_missing_status_is_not_silently_treated_as_equal(self):
        for value in ('', None, 0):
            with self.subTest(value=value), self.assertRaisesRegex(RuntimeError, 'statuses'):
                self.classify(before=value)

    def test_invalid_measurement_or_alias_shapes_rejected(self):
        for args in ({'measurements': 'field'}, {'measurements': [None]},
                     {'aliases': 1}, {'labels': []}):
            with self.subTest(args=args), self.assertRaises(RuntimeError):
                self.classify(**args)


if __name__ == '__main__':
    unittest.main()

"""Check aggregate accounting and honest scope, not the occurrence of human review."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AuthorReviewSummary(unittest.TestCase):
    def setUp(self):
        self.summary = json.loads((ROOT / 'data/validation/author_review_summary.json').read_text())

    def test_collective_counts_and_coverage(self):
        data = self.summary
        self.assertEqual(data['selected_events'], 46)
        self.assertEqual(sum(data['condition_counts']), data['selected_events'])
        self.assertEqual(data['condition_counts'], [23, 23])
        self.assertEqual(data['author_reported_reviewed_events'], 46)
        self.assertEqual(data['collectively_confirmed_classifications'], 46)
        self.assertEqual(data['inaccuracies_reported'], 0)
        self.assertEqual((data['station_count'], data['provider_format_count']), (12, 3))

    def test_no_invented_itemized_or_population_estimate(self):
        data = self.summary
        self.assertEqual(data['separately_recorded_criterion_judgments'], 0)
        self.assertEqual(data['criterion_fields_in_review_instrument'], 414)
        self.assertFalse(data['independent_rater'])
        for key in ['independent_accuracy_estimate', 'inter_rater_reliability_estimate', 'population_accuracy_estimate']:
            self.assertIsNone(data[key])
        for key in ['private_confirmation_sha256', 'private_packet_sha256']:
            self.assertRegex(data[key], r'^[0-9a-f]{64}$')

    def test_display_only_adapter_keeps_pilot_limit(self):
        spec = importlib.util.spec_from_file_location('reviewed_figure', ROOT / 'scripts/build_reviewed_figure.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.reviewed_subtitle(self.summary),
                         'historical 46-case author check; candidate linkage remains unadjudicated')
        altered = {**self.summary, 'inaccuracies_reported': 1}
        with self.assertRaises(ValueError):
            module.reviewed_subtitle(altered)

    def test_historical_review_is_not_transferred_to_corrections(self):
        self.assertEqual(self.summary['reviewed_analysis_version'], 'event-v3')
        self.assertFalse(self.summary['applies_to_entire_corrected_analysis'])
        self.assertEqual(self.summary['new_human_criterion_judgments_from_technical_audit'], 0)
        self.assertIn('subsequent', self.summary['interpretation'].lower())


if __name__ == '__main__':
    unittest.main()

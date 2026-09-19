"""Fictional regression fixtures for event-v3 downstream handling."""
import importlib.util
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'scripts/run_workstation_analysis.py').is_file():
    ROOT = ROOT / 'analysis'
spec = importlib.util.spec_from_file_location('event_analysis', ROOT / 'scripts/run_workstation_analysis.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def fixture(**changes):
    row = dict(episode_id='FICTIONAL-1', station_id='ST00', provider='fixture',
               timestamp_start_utc='2026-01-01T10:00:00Z', timestamp_end_utc='2026-01-01T10:02:00Z',
               completed_substantive_action_calls='2', origin_candidate=analysis.ORIGIN,
               automated_disposition=analysis.CE_DISPOSITION, publication_exclusion_candidate='no')
    row.update(changes)
    return row


class MissingTiming(unittest.TestCase):
    def test_observed_duration(self):
        transformed = analysis.transform(fixture())
        self.assertEqual(transformed['duration_min'], 2)
        self.assertEqual(transformed['min_per_action'], 1)

    def test_missing_endpoint_is_not_zero(self):
        transformed = analysis.transform(fixture(timestamp_end_utc=''))
        self.assertIsNone(transformed['duration_min'])
        self.assertIsNone(transformed['min_per_action'])
        self.assertEqual(analysis.cohort(transformed), analysis.CE_LABEL)

    def test_negative_endpoint_is_not_zero(self):
        transformed = analysis.transform(fixture(timestamp_end_utc='2026-01-01T09:59:00Z'))
        self.assertIsNone(transformed['duration_min'])

    def test_missing_start_cannot_be_calendar_balanced(self):
        transformed = analysis.transform(fixture(timestamp_start_utc=''))
        self.assertEqual(analysis.cohort(transformed), '')

    def test_available_case_median(self):
        self.assertEqual(analysis.median([1., math.nan, 3.]), 2.)
        self.assertTrue(math.isnan(analysis.median([math.nan])))

    def test_empty_bootstrap_is_explicitly_unavailable(self):
        interval = analysis.bootstrap_mean_ci([], 5, 1, 'fixture')
        self.assertTrue(all(math.isnan(value) for value in interval))

    def test_balancing_does_not_change_with_outcome(self):
        ce = [analysis.transform(fixture(episode_id=f'FICTIONAL-{i}')) for i in range(4)]
        comp = [analysis.transform(fixture(episode_id=f'COMPARE-{i}')) for i in range(2)]
        before = [pair[1]['episode_id'] for pair in analysis.balance(ce, comp, 'fictional')[0]]
        for row in ce:
            row['verification_successful'] = 1
            row['duration_min'] = None
        after = [pair[1]['episode_id'] for pair in analysis.balance(ce, comp, 'fictional')[0]]
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()

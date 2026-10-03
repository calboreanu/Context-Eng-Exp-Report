"""The linkage pilot must not collapse held positions into immediate links.

All prompts, IDs, sessions and targets below are synthetic. Missing event
ordinals model the held rows absent from the resolved analysis input.
"""
import contextlib
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'inheritance_pilot_under_test', ROOT / 'analysis/scripts/run_inheritance_pilot.py')
PILOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PILOT)


class InheritanceAdjacency(unittest.TestCase):
    def run_pair(self, distance, prompt, *, predecessor='candidate_strong',
                 previous_prompt='Prepare a plan.', shared_target=False):
        def row(episode, turn, disposition, text):
            trace = ([{'target_ref': 'synthetic-target', 'completed': True, 'succeeded': True}]
                     if shared_target else [])
            return {
                'station_id': 'ST00', 'provider': 'synthetic',
                'session_ref': 'synthetic-session', 'episode_id': episode,
                'turn_index': turn, 'source_line_start': turn,
                'completed_substantive_action_calls': 1,
                'tool_trace_json': json.dumps(trace),
                'prompt_text': text, 'prompt_words': len(text.split()),
                'automated_disposition': disposition,
            }

        rows = [row('synthetic-prior', 1, predecessor, previous_prompt),
                row('synthetic-current', 1 + distance, PILOT.COMPARISON_DISPOSITION, prompt)]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'synthetic.csv'
            output = Path(directory) / 'output'
            with source.open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with patch('sys.argv', ['run_inheritance_pilot.py', '--input', str(source), '--out', str(output)]):
                with contextlib.redirect_stdout(io.StringIO()):
                    PILOT.main()
            with (output / 'restricted/inheritance_candidate_map.csv').open(newline='') as stream:
                mapped = list(csv.DictReader(stream))
            summary = json.loads((output / 'inheritance_pilot_summary.json').read_text())
        self.assertEqual(len(mapped), 1)
        return mapped[0], summary

    def test_short_reference_does_not_bridge_eleven_held_positions(self):
        mapped, summary = self.run_pair(12, 'Continue this.')
        self.assertEqual(mapped['mapping_class'], 'CONTEXT_REFERENCE_WITHIN_20')
        self.assertEqual(mapped['evidence_tier'], 'PROBABLE_CANDIDATE')
        self.assertEqual(mapped['minimum_link_window'], '12')
        self.assertEqual([row['candidate_positive'] for row in summary['sensitivity']], [0, 0, 1, 1, 1])

    def test_long_reference_does_not_bridge_two_held_positions(self):
        mapped, _ = self.run_pair(3, 'Continue ' + 'synthetic ' * 31)
        self.assertEqual(mapped['mapping_class'], 'CONTEXT_REFERENCE_WITHIN_20')
        self.assertEqual(mapped['evidence_tier'], 'PROBABLE_CANDIDATE')
        self.assertEqual(mapped['minimum_link_window'], '3')

    def test_adjacent_short_reference_stays_high_confidence(self):
        mapped, _ = self.run_pair(1, 'Continue this.')
        self.assertEqual(mapped['mapping_class'], 'IMMEDIATE_SHORT_REFERENCE')
        self.assertEqual(mapped['evidence_tier'], 'HIGH_CONFIDENCE_CANDIDATE')
        self.assertEqual(mapped['minimum_link_window'], '0')

    def test_adjacent_nonreference_stays_probable(self):
        mapped, _ = self.run_pair(1, 'Generate a sample.')
        self.assertEqual(mapped['mapping_class'], 'IMMEDIATE_ADJACENCY')
        self.assertEqual(mapped['evidence_tier'], 'PROBABLE_CANDIDATE')
        self.assertEqual(mapped['minimum_link_window'], '1')

    def test_gap_without_reference_uses_actual_near_sequence_distance(self):
        mapped, _ = self.run_pair(3, 'Generate a sample.')
        self.assertEqual(mapped['mapping_class'], 'NEAR_SEQUENCE')
        self.assertEqual(mapped['minimum_link_window'], '3')

    def test_gap_outside_primary_window_is_unresolved(self):
        mapped, summary = self.run_pair(21, 'Continue this.')
        self.assertEqual(mapped['mapping_class'], 'UNRESOLVED_PRIOR_CE_SESSION')
        self.assertEqual(mapped['evidence_tier'], 'UNRESOLVED')
        self.assertEqual(mapped['minimum_link_window'], '21')
        self.assertEqual([row['candidate_positive'] for row in summary['sensitivity']], [0, 0, 0, 1, 1])

    def test_exact_tool_target_is_not_restricted_to_adjacent_positions(self):
        mapped, _ = self.run_pair(12, 'Continue this.', shared_target=True)
        self.assertEqual(mapped['mapping_class'], 'EXACT_SUCCESSFUL_TOOL_TARGET')
        self.assertEqual(mapped['evidence_tier'], 'HIGH_CONFIDENCE_CANDIDATE')
        self.assertEqual(mapped['minimum_link_window'], '0')

    def test_exact_prompt_anchor_is_not_restricted_to_adjacent_positions(self):
        mapped, _ = self.run_pair(12, 'Complete SYN-123.', previous_prompt='Plan SYN-123.')
        self.assertEqual(mapped['mapping_class'], 'EXACT_PROMPT_ANCHOR')
        self.assertEqual(mapped['evidence_tier'], 'HIGH_CONFIDENCE_CANDIDATE')
        self.assertEqual(mapped['minimum_link_window'], '0')

    def test_probable_predecessor_remains_eligible(self):
        mapped, _ = self.run_pair(1, 'Continue this.', predecessor='candidate_probable')
        self.assertEqual(mapped['mapping_class'], 'IMMEDIATE_SHORT_REFERENCE')
        self.assertEqual(mapped['evidence_tier'], 'HIGH_CONFIDENCE_CANDIDATE')


if __name__ == '__main__':
    unittest.main()

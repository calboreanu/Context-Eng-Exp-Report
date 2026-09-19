"""Fictional source-frame catalog boundaries; no restricted inputs."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('correction_catalog', ROOT / 'scripts/build_public_catalog.py')
CATALOG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CATALOG)


class CorrectionCatalog(unittest.TestCase):
    def build(self, mutate=None):
        action = {
            'unchanged_native_event_identities': 75, 'native_invariant_checks': 150,
            'status_transitions': {'resolved->resolved': 70},
            'measurement_changes': {'frontloading_changed_events': 3},
            'fixed_v4_selection_exposure': {'frontloading_changed': {'v4_primary_ce': 1}},
            'sample_membership': {'primary': {'retained_distinct_events': 26}},
            'source_accounting': {'v5': {'contributing_alias_sources': 10, 'canonical_resolved_sources': 8}},
            'unchanged_tool_names_resolved_occurrence_counts': {'v5': {'bashoutput': 0, 'killshell': 0}},
            'phrase_overlap_exposure': {'counts': {'v5': {'resolved_events': 5, 'primary_events': 1}}},
            # Deliberately outside the public allowlist: never emit it even if
            # an upstream document later acquires a new unrelated section.
            'unapproved_section': {'fictional_row_id': 'DO_NOT_CATALOG'},
        }
        if mutate:
            mutate(action)
        boundary = {'normalization': {key: 0 for key in (
            'old_source_rows', 'old_claude_rows', 'normalized_events', 'resolved_events',
            'quarantined_events', 'representation_reduction', 'absorbed_nonprimary_components',
            'total_alias_to_primary_component_reduction')}}
        boundary['normalization']['absorbed_nonprimary_kinds'] = {}
        boundary.update(review46={}, full_primary_overlap={}, historical_evidence_overlap={'all138': {}})
        inputs = {
            'analysis_summary.json': {'analysis_contract': 'context-engineering-event-normalized-analysis/5.0.0',
                                      'scope': {'source_episode_rows': 70}},
            'inheritance_pilot_summary.json': {'scope': {}},
            'boundary_correction_summary.json': boundary,
            'action_reference_correction_summary.json': action,
        }
        with tempfile.TemporaryDirectory(prefix='fictional-catalog-') as directory:
            temporary = Path(directory)
            for name, value in inputs.items():
                (temporary / name).write_text(json.dumps(value))
            with patch.object(CATALOG, 'RESULTS', temporary):
                return CATALOG.build_source_frame()

    def test_new_groups_append_without_moving_headline_formula_source(self):
        rows = self.build()
        self.assertEqual((rows[0]['measure'], rows[0]['value']), ('source_episode_rows', 70))
        self.assertEqual([r['item_id'] for r in rows], [f'FRAME-{i:02d}' for i in range(1, len(rows) + 1)])

    def test_only_allowlisted_scalar_counts_are_exported(self):
        rows = self.build()
        exported = {r['measure']: r['value'] for r in rows if r['source_file'].endswith('action_reference_correction_summary.json')}
        self.assertEqual(len(exported), 12)
        self.assertEqual(exported['source_accounting.v5.canonical_resolved_sources'], 8)
        self.assertEqual(exported['fixed_v4_selection_exposure.frontloading_changed.v4_primary_ce'], 1)
        self.assertNotIn('DO_NOT_CATALOG', json.dumps(rows))

    def test_unexpected_nested_or_noncount_payload_fails_closed(self):
        for value in (True, -1, 'fictional', {'nested': 3}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Non-count correction catalog field'):
                self.build(lambda action: action['measurement_changes'].update(frontloading_changed_events=value))

    def test_source_frame_order_is_deterministic(self):
        baseline = self.build()
        reordered = self.build(lambda action: action['source_accounting'].update(
            v5=dict(reversed(list(action['source_accounting']['v5'].items())))))
        self.assertEqual(baseline, reordered)


if __name__ == '__main__':
    unittest.main()

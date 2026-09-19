"""Fictional aggregate v4/v5 accounting; no restricted observations."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('action_summary_verifier', ROOT / 'scripts/verify_public_release.py')
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


def fixture():
    old_scope = {'source_episode_rows': 70, 'source_conversation_count': 8,
                 'primary_frontloaded_balanced_per_condition': 15,
                 'unrestricted_balanced_per_condition': 30}
    new_scope = {**old_scope, 'primary_frontloaded_balanced_per_condition': 14,
                 'unrestricted_balanced_per_condition': 29}
    analysis = {'analysis_contract': 'context-engineering-event-normalized-analysis/5.0.0',
                'input': {'sha256': 'a' * 64}, 'scope': new_scope}
    boundary = {'normalization': {'normalized_events': 75}}
    sources = {'contributing_alias_sources': 10, 'canonical_resolved_sources': 8,
               'contributing_not_canonical_resolved': 2, 'delta_with_resolved_alias': 2,
               'delta_with_held_alias': 1, 'delta_only_held_alias': 0,
               'delta_canonical_held': 1, 'delta_without_any_canonical_role': 1}
    correction = {'analysis_contract': analysis['analysis_contract'],
        'input_sha256': {'v4': 'b' * 64, 'v5': 'a' * 64},
        'analysis_scope': {'v4': old_scope, 'v5': new_scope},
        'unchanged_native_event_identities': 75, 'native_invariant_checks': 150,
        'status_transitions': {'resolved->resolved': 70, 'quarantined->quarantined': 5},
        'measurement_changes': {'frontloading_changed_events': 3, 'reclassified_calls': 12},
        'fixed_v4_selection_exposure': {'frontloading_changed': {'v4_resolved': 3, 'v4_primary_ce': 1},
                                       'successful_todowrite_calls': {'v4_primary_ce': 20}},
        'sample_membership': {
            'primary': {'v4_total': 30, 'v5_total': 28, 'retained_distinct_events': 26,
                        'removed_events': 4, 'newly_selected_events': 2,
                        'retained_same_condition': 25, 'retained_changed_condition': 1},
            'unrestricted': {'v4_total': 60, 'v5_total': 58, 'retained_distinct_events': 50,
                             'removed_events': 10, 'newly_selected_events': 8,
                             'retained_same_condition': 49, 'retained_changed_condition': 1}},
        'source_accounting': {'v4': copy.deepcopy(sources), 'v5': copy.deepcopy(sources)},
        'unchanged_tool_names_resolved_occurrence_counts': {
            'v4': {'bashoutput': 0, 'killshell': 0}, 'v5': {'bashoutput': 0, 'killshell': 0}},
        'phrase_overlap_exposure': {'pattern': r'\bcontext package\b', 'counts': {
            version: {'resolved_events': 5, 'eligible_ce_events': 1, 'eligible_comparison_events': 1,
                      'primary_events': 1, 'unrestricted_events': 2, 'sole_packaging_trigger_events': 3}
            for version in ('v4', 'v5')}},
        'human_labels_added': 0, 'historical_confirmation_transferred': False}
    return analysis, boundary, correction


class ActionReferenceSummary(unittest.TestCase):
    def test_fictional_accounting_passes(self):
        VERIFY.verify_v5_action_reference_summary(*fixture())

    def assert_bad(self, mutate, pattern):
        a, b, c = fixture()
        mutate(c)
        with self.assertRaisesRegex(RuntimeError, pattern):
            VERIFY.verify_v5_action_reference_summary(a, b, c)

    def test_current_input_identity_required(self):
        self.assert_bad(lambda c: c['input_sha256'].update(v5='c' * 64), 'current input mismatch')

    def test_old_contract_rejected(self):
        self.assert_bad(lambda c: c.update(analysis_contract='old'), 'contract mismatch')

    def test_both_version_input_identities_required(self):
        self.assert_bad(lambda c: c['input_sha256'].pop('v4'), 'version comparison incomplete')

    def test_native_invariant_count_must_be_numeric(self):
        self.assert_bad(lambda c: c.update(native_invariant_checks=True), 'native invariants')

    def test_tool_occurrences_require_both_versions_and_exact_names(self):
        self.assert_bad(lambda c: c['unchanged_tool_names_resolved_occurrence_counts'].pop('v4'),
                        'tool occurrence version comparison incomplete')
        self.assert_bad(lambda c: c['unchanged_tool_names_resolved_occurrence_counts']['v5'].update(other=0),
                        'unexpected tool occurrence name')

    def test_phrase_overlap_is_bound_to_the_specific_literal(self):
        self.assert_bad(lambda c: c['phrase_overlap_exposure'].update(pattern='package'), 'phrase-overlap scope')

    def test_phrase_overlap_bounds_separate_frame_and_selected_exposure(self):
        self.assert_bad(lambda c: c['phrase_overlap_exposure']['counts']['v5'].update(primary_events=3),
                        'phrase-overlap selected bounds')
        self.assert_bad(lambda c: c['phrase_overlap_exposure']['counts']['v5'].update(sole_packaging_trigger_events=6),
                        'phrase-overlap frame bounds')

    def test_historical_confirmation_cannot_transfer(self):
        self.assert_bad(lambda c: c.update(historical_confirmation_transferred=True), 'human labels')

    def test_technical_audit_cannot_create_human_labels(self):
        self.assert_bad(lambda c: c.update(human_labels_added=1), 'human labels')

    def test_status_total_must_match_native_frame(self):
        self.assert_bad(lambda c: c['status_transitions'].update(**{'resolved->resolved': 69}), 'conservation')

    def test_status_renaming_cannot_hide_unknown_state(self):
        self.assert_bad(lambda c: c['status_transitions'].update(**{'held->held': 0}), 'unknown status')

    def test_membership_must_reconcile_removed_and_added(self):
        self.assert_bad(lambda c: c['sample_membership']['primary'].update(newly_selected_events=3), 'membership conservation')

    def test_retained_condition_subtotal_checked(self):
        self.assert_bad(lambda c: c['sample_membership']['primary'].update(retained_changed_condition=2), 'condition conservation')

    def test_fixed_sample_exposure_cannot_exceed_its_arm(self):
        self.assert_bad(lambda c: c['fixed_v4_selection_exposure']['frontloading_changed'].update(v4_primary_ce=16), 'exposure exceeds')

    def test_overlapping_source_roles_not_falsely_added(self):
        # A source can have both resolved and held aliases. Only the explicitly
        # exclusive decompositions must add to the canonical-source difference.
        a, b, c = fixture()
        self.assertEqual(c['source_accounting']['v5']['delta_with_resolved_alias']
                         + c['source_accounting']['v5']['delta_with_held_alias'], 3)
        VERIFY.verify_v5_action_reference_summary(a, b, c)

    def test_canonical_source_difference_checked(self):
        self.assert_bad(lambda c: c['source_accounting']['v5'].update(contributing_alias_sources=11), 'source reconciliation')

    def test_boolean_and_negative_counts_rejected(self):
        for value in (True, -1):
            self.assert_bad(lambda c: c['measurement_changes'].update(frontloading_changed_events=value), 'nonnegative integer')


if __name__ == '__main__':
    unittest.main()

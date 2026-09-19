"""Public reconciliation constraints use fictional counts, not confidential joins."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('boundary_release_verifier', ROOT / 'scripts/verify_public_release.py')
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


def fixture():
    scope = {'source_episode_rows': 70, 'primary_frontloaded_balanced_per_condition': 15}
    analysis = {'analysis_contract': 'context-engineering-event-normalized-analysis/5.0.0', 'scope': scope}
    summary = {'historical_events': 46, 'distinct_v5_events': 40,
               'disposition_counts': {'current_primary_unchanged': 8, 'current_primary_changed': 12, 'not_current_primary': 24, 'held': 2},
               'same_measured_trajectory_and_labels_count': 21, 'changed_measurements_or_trajectory_count': 25,
               'v5_primary_member_count': 20, 'held_count': 2, 'condition_changed_among_current_primary_count': 2}
    overlap = copy.deepcopy(summary)
    overlap.update(v3_primary_total=46, v5_primary_total=30,
                   v5_primary_distinct_events_reached_from_v3_primary=18,
                   v5_primary_events_not_reached_from_v3_primary=12)
    boundary = {'analysis_contract': analysis['analysis_contract'], 'v5_analysis_scope': scope,
                'v3_analysis_scope': {'primary_frontloaded_balanced_per_condition': 23},
                'normalization': {'old_source_rows': 100, 'normalized_events': 75, 'representation_reduction': 15,
                                  'resolved_events': 70, 'quarantined_events': 5,
                                  'absorbed_nonprimary_components': 10,
                                  'total_alias_to_primary_component_reduction': 25,
                                  'absorbed_nonprimary_kinds': {'bare_continuation': 7, 'machine_task_notification': 3}},
                'old_source_row_aliases': 100, 'resolved_frame_rows': 70, 'held_frame_rows': 5,
                'human_labels_added': 0, 'original_frozen46_confirmation_preserved': True,
                'review46': summary, 'full_primary_overlap': overlap}
    author = {'reviewed_analysis_version': 'event-v3', 'applies_to_entire_corrected_analysis': False,
              'selected_events': 46, 'author_reported_reviewed_events': 46,
              'collectively_confirmed_classifications': 46, 'inaccuracies_reported': 0}
    return analysis, boundary, author


def historical_fixture():
    # Fixed historical frame sizes are contractual; all overlap counts are fictional.
    def group(records):
        return {'historical_records': records, 'distinct_v5_events': 3,
                'historical_records_mapping_to_v5_primary': 3, 'distinct_v5_primary_events': 2,
                'distinct_v5_primary_events_by_cohort': {'ce': 1, 'comparison': 1},
                'distinct_v5_event_status_counts': {'resolved': 2, 'held': 1}}
    return {'all138': group(138), 'historical_v2_primary49': group(49),
            'documentary_chain_count': 3, 'documentary_chain_intervals': group(6),
            'proof_case_anchors': group(3)}


class BoundaryReleaseTests(unittest.TestCase):
    def test_historical_overlap_aggregate_conservation_pass(self):
        VERIFY.verify_historical_evidence_overlap(historical_fixture())

    def test_historical_universe_cannot_change(self):
        value = historical_fixture()
        value['all138']['historical_records'] = 137
        with self.assertRaisesRegex(RuntimeError, 'universe changed'):
            VERIFY.verify_historical_evidence_overlap(value)

    def test_historical_distinct_events_cannot_exceed_records(self):
        value = historical_fixture()
        value['proof_case_anchors']['distinct_v5_events'] = 4
        with self.assertRaisesRegex(RuntimeError, 'count bounds'):
            VERIFY.verify_historical_evidence_overlap(value)

    def test_historical_cohort_and_status_subtotals_checked(self):
        for field in ['distinct_v5_primary_events_by_cohort', 'distinct_v5_event_status_counts']:
            with self.subTest(field=field):
                value = historical_fixture()
                value['all138'][field]['extra'] = 1
                with self.assertRaisesRegex(RuntimeError, 'subtotal'):
                    VERIFY.verify_historical_evidence_overlap(value)

    def test_negative_historical_overlap_count_rejected(self):
        value = historical_fixture()
        value['all138']['distinct_v5_primary_events_by_cohort']['ce'] = -1
        with self.assertRaisesRegex(RuntimeError, 'nonnegative integer'):
            VERIFY.verify_historical_evidence_overlap(value)

    def test_fictional_conservation_and_historical_limits_pass(self):
        VERIFY.verify_v5_boundary_summary(*fixture())

    def test_bad_all_provider_source_conservation_rejected(self):
        a, b, h = fixture()
        b['normalization']['representation_reduction'] += 1
        with self.assertRaisesRegex(RuntimeError, 'all-provider event conservation'):
            VERIFY.verify_v5_boundary_summary(a, b, h)

    def test_bad_resolved_or_held_count_rejected(self):
        for field in ['resolved_frame_rows', 'held_frame_rows']:
            with self.subTest(field=field):
                a, b, h = fixture()
                b[field] += 1
                with self.assertRaisesRegex(RuntimeError, 'frame conservation'):
                    VERIFY.verify_v5_boundary_summary(a, b, h)

    def test_absorption_subtotal_rejected(self):
        a, b, h = fixture()
        b['normalization']['absorbed_nonprimary_kinds']['bare_continuation'] += 1
        with self.assertRaisesRegex(RuntimeError, 'absorption subtotal'):
            VERIFY.verify_v5_boundary_summary(a, b, h)

    def test_identity_and_boundary_reductions_stay_distinct(self):
        a, b, h = fixture()
        b['normalization']['total_alias_to_primary_component_reduction'] += 1
        with self.assertRaisesRegex(RuntimeError, 'identity/boundary reduction subtotal'):
            VERIFY.verify_v5_boundary_summary(a, b, h)

    def test_old_review_cannot_be_transferred(self):
        a, b, h = fixture()
        h['applies_to_entire_corrected_analysis'] = True
        with self.assertRaisesRegex(RuntimeError, 'must not transfer'):
            VERIFY.verify_v5_boundary_summary(a, b, h)

    def test_new_human_labels_cannot_be_inferred(self):
        a, b, h = fixture()
        b['human_labels_added'] = 1
        with self.assertRaisesRegex(RuntimeError, 'must not create human labels'):
            VERIFY.verify_v5_boundary_summary(a, b, h)

    def test_review_rejoin_must_cover_frozen_cases(self):
        a, b, h = fixture()
        b['review46']['disposition_counts']['held'] += 1
        with self.assertRaisesRegex(RuntimeError, 'disposition total'):
            VERIFY.verify_v5_boundary_summary(a, b, h)

    def test_primary_reconciliation_must_match_current_sample(self):
        a, b, h = fixture()
        b['full_primary_overlap']['v5_primary_total'] += 1
        with self.assertRaisesRegex(RuntimeError, 'current primary reconciliation'):
            VERIFY.verify_v5_boundary_summary(a, b, h)

    def test_catalog_exact_values_pass(self):
        VERIFY.verify_catalog_records([{'measure': 'count', 'value': '7'}],
                                      [{'measure': 'count', 'value': 7}], ['measure', 'value'], 'fictional')

    def test_same_size_catalog_with_wrong_nonheadline_value_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'fields differ'):
            VERIFY.verify_catalog_records([{'measure': 'count', 'value': '8'}],
                                          [{'measure': 'count', 'value': 7}], ['measure', 'value'], 'fictional')

    def test_same_size_catalog_with_wrong_selector_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'fields differ'):
            VERIFY.verify_catalog_records([{'source_record': 'row=3', 'value': '7'}],
                                          [{'source_record': 'row=2', 'value': 7}], ['source_record', 'value'], 'fictional')


if __name__ == '__main__':
    unittest.main()

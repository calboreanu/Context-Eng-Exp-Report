"""Regression checks for the staged aggregate adjunct, not withheld evidence."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('deliverable_verifier', ROOT / 'scripts/verify_deliverable_evidence.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class DeliverableEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ROOT / 'data/validation/deliverable_evidence_summary.json'
        cls.original = CHECK.load_summary(cls.source)

    def setUp(self):
        self.data = deepcopy(self.original)

    def reject(self, section, key, value):
        altered = deepcopy(self.data)
        destination = altered if section is None else altered[section]
        destination[key] = value
        with self.assertRaises(ValueError):
            CHECK.verify(altered)

    def test_current_aggregate_passes(self):
        self.assertTrue(CHECK.verify(self.data))

    def test_frozen_terminal_aggregate(self):
        inventory = self.data['terminal_inventory']
        expected = {
            'historical_anchors': 138,
            'source_identities_freshly_verified': 138,
            'source_intervals_parsed': 138,
            'resolved_current_events': 138,
            'current_primary_members': 5,
            'distinct_historical_target_path_tokens': 343,
            'anchors_with_all_tracked_targets_observed_in_successful_write_or_edit_results': 138,
            'anchors_with_completed_retrieval_or_search': 132,
            'anchors_with_completed_retrieval_or_search_before_first_successful_tracked_target_write': 127,
            'anchors_with_completed_verification_class_call': 98,
            'historical_collectively_confirmed_terminal_records': 138,
        }
        for field, value in expected.items():
            with self.subTest(field=field):
                self.assertEqual(inventory[field], value)

    def test_frozen_documentary_aggregate(self):
        inventory = self.data['documentary_inventory']
        self.assertEqual(inventory['selected_chains'], 3)
        self.assertEqual(inventory['chains_with_direct_corrective_response'], 3)
        self.assertEqual(inventory['chains_with_reported_revised_delivery'], 3)
        self.assertEqual(inventory['chains_with_prior_scoped_adoption'], 1)
        self.assertEqual(inventory['retained_output_files_exactly_matching_logged_creation'], 2)
        self.assertEqual(inventory['chains_with_unrecovered_final_acceptance_endpoint'], 3)

    def test_unknown_counts_are_not_zero_or_estimates(self):
        for section, fields in {
            'terminal_inventory': ['distinct_deliverable_count', 'full_method_application_count'],
            'documentary_inventory': ['full_current_formal_method_count'],
            'timing': ['pooled_duration_summary', 'comparative_speed_effect'],
        }.items():
            for field in fields:
                self.assertIsNone(self.data[section][field])
                for value in (0, False, 'unknown', 138):
                    with self.subTest(section=section, field=field, value=value):
                        self.reject(section, field, value)

    def test_count_types_reject_booleans_strings_floats_and_negatives(self):
        for section in ('terminal_inventory', 'documentary_inventory', 'timing'):
            for key, original in self.data[section].items():
                if type(original) is not int:
                    continue
                for value in (True, False, str(original), float(original), -1):
                    with self.subTest(section=section, field=key, value=value):
                        self.reject(section, key, value)

    def test_complete_terminal_accounting_cannot_drop_an_anchor(self):
        for key in ('source_identities_freshly_verified', 'source_intervals_parsed', 'resolved_current_events', 'historical_collectively_confirmed_terminal_records', 'anchors_with_all_tracked_targets_observed_in_successful_write_or_edit_results'):
            with self.subTest(field=key):
                self.reject('terminal_inventory', key, 137)

    def test_terminal_subsets_cannot_exceed_inventory(self):
        for key in ('current_primary_members', 'anchors_with_completed_retrieval_or_search', 'anchors_with_completed_retrieval_or_search_before_first_successful_tracked_target_write', 'anchors_with_completed_verification_class_call'):
            with self.subTest(field=key):
                self.reject('terminal_inventory', key, 139)

    def test_ordered_context_subset_cannot_exceed_any_context_subset(self):
        self.reject('terminal_inventory', 'anchors_with_completed_retrieval_or_search_before_first_successful_tracked_target_write', 133)

    def test_target_token_count_is_positive_not_a_deliverable_denominator(self):
        self.reject('terminal_inventory', 'distinct_historical_target_path_tokens', 0)
        # Multiple anchors could share a path in another conforming inventory.
        # Do not manufacture a general path-count >= anchor-count invariant.
        self.data['terminal_inventory']['distinct_historical_target_path_tokens'] = 1
        self.assertTrue(CHECK.verify(self.data))

    def test_no_new_human_ratings(self):
        for section in ('terminal_inventory', 'documentary_inventory'):
            self.assertEqual(self.data[section]['new_human_ratings'], 0)
            self.reject(section, 'new_human_ratings', 1)

    def test_purposive_sets_cannot_be_claimed_additive_or_independent(self):
        for field in ('sets_additive', 'preregistered', 'independent_human_review'):
            for value in (True, 0, None, 'false'):
                with self.subTest(field=field, value=value):
                    self.reject('selection', field, value)

    def test_complete_chain_accounting_and_adoption_bounds(self):
        for key in ('chains_with_direct_corrective_response', 'chains_with_reported_revised_delivery', 'chains_with_unrecovered_final_acceptance_endpoint'):
            self.reject('documentary_inventory', key, 2)
        self.reject('documentary_inventory', 'chains_with_prior_scoped_adoption', 4)

    def test_chain_population_matches_literal_selection_statement(self):
        self.data['documentary_inventory']['selected_chains'] = 4
        for key in ('chains_with_direct_corrective_response', 'chains_with_reported_revised_delivery', 'chains_with_unrecovered_final_acceptance_endpoint'):
            self.data['documentary_inventory'][key] = 4
        self.data['timing'].update({'provider_clock_chains': 3, 'audit_capture_clock_chains': 1, 'chains_with_three_attributable_phase_intervals': 4, 'private_phase_intervals': 12})
        with self.assertRaisesRegex(ValueError, 'selection statement'):
            CHECK.verify(self.data)

    def test_clock_provenance_and_phase_accounting(self):
        timing = self.data['timing']
        self.assertEqual((timing['provider_clock_chains'], timing['audit_capture_clock_chains']), (2, 1))
        self.assertEqual(timing['private_phase_intervals'], 9)
        self.reject('timing', 'provider_clock_chains', 3)
        self.reject('timing', 'audit_capture_clock_chains', 0)
        self.reject('timing', 'chains_with_three_attributable_phase_intervals', 2)
        self.reject('timing', 'private_phase_intervals', 8)

    def test_scope_flags_are_required_true_booleans(self):
        for field in self.data['interpretation']:
            for value in (False, 1, None, 'true'):
                with self.subTest(field=field, value=value):
                    self.reject('interpretation', field, value)

    def test_schema_and_unchanged_contract(self):
        self.reject(None, 'schema', 'retrospective-deliverable-evidence/2.0.0')
        self.reject(None, 'analysis_contract_unchanged', 'revised-analysis')

    def test_prepared_date_has_no_exact_timestamp(self):
        for value in ('2026-02-30', '2026-09-19T12:00:00Z', '2026-9-19', None, 20260919):
            with self.subTest(value=value):
                self.reject(None, 'prepared_date', value)

    def test_required_fields_cannot_be_omitted(self):
        for section in (None, 'terminal_inventory', 'documentary_inventory', 'selection', 'timing', 'interpretation', 'restricted_receipts'):
            original = self.data if section is None else self.data[section]
            for field in original:
                altered = deepcopy(self.data)
                destination = altered if section is None else altered[section]
                del destination[field]
                with self.subTest(section=section, field=field), self.assertRaises(ValueError):
                    CHECK.verify(altered)

    def test_unexpected_private_rows_and_probe_fields_rejected(self):
        for section, field, value in (
            (None, 'records', [{'source': 'fictional'}]),
            ('terminal_inventory', 'source_path', '/fictional/private.txt'),
            ('documentary_inventory', 'case_rows', []),
            ('timing', 'exact_case_times', []),
            ('terminal_inventory', 'candidate_files_hashed', 26),
            ('restricted_receipts', 'prompt_sha256', 'a' * 64),
        ):
            with self.subTest(section=section, field=field):
                self.reject(section, field, value)

    def test_receipts_require_exact_lowercase_sha256_shape(self):
        for key in self.data['restricted_receipts']:
            for value in ('a' * 63, 'a' * 65, 'A' * 64, 'g' * 64, None, [], 12):
                with self.subTest(field=key, value=value):
                    self.reject('restricted_receipts', key, value)

    def test_receipt_syntax_is_not_private_content_validation(self):
        self.data['restricted_receipts']['terminal_register_sha256'] = '0' * 64
        self.assertTrue(CHECK.verify(self.data))

    def test_free_text_fields_cannot_embed_new_claims_or_private_content(self):
        for section, key in ((None, 'reconstruction'), (None, 'public_check_boundary'), ('selection', 'terminal_anchors'), ('selection', 'documentary_chains'), ('timing', 'scope'), ('timing', 'nonpooling_reason')):
            with self.subTest(section=section, field=key):
                self.reject(section, key, 'An unsupported complete-method or acceptance claim.')

    def test_objects_cannot_be_replaced_by_arrays(self):
        for key in ('selection', 'terminal_inventory', 'documentary_inventory', 'timing', 'interpretation', 'restricted_receipts'):
            self.reject(None, key, [])

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'fictional.json'
            source.write_text('{"schema": "first", "schema": "second"}')
            with self.assertRaises(ValueError):
                CHECK.load_summary(source)

    def test_checks_remain_enabled_under_python_optimization(self):
        self.data['terminal_inventory']['full_method_application_count'] = 138
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'fictional.json'
            source.write_text(json.dumps(self.data))
            run = subprocess.run([sys.executable, '-O', str(ROOT / 'scripts/verify_deliverable_evidence.py'), str(source)], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('not established', run.stderr)


if __name__ == '__main__':
    unittest.main()

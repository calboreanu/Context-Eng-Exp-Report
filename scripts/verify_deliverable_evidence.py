#!/usr/bin/env python3
"""Check documentary aggregate shape, accounting and stated scope only.

This allowlisted summary contains no case rows. Receipt syntax cannot establish
the contents or semantic accuracy of withheld evidence. Uses explicit errors so
checks remain active under ``python -O``.
"""
from pathlib import Path
from datetime import date
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


SCHEMA = 'retrospective-deliverable-evidence/1.0.0'
CONTRACT = 'context-engineering-event-normalized-analysis/5.0.0'
TOP_KEYS = {
    'schema', 'prepared_date', 'analysis_contract_unchanged', 'reconstruction',
    'selection', 'terminal_inventory', 'documentary_inventory', 'timing',
    'interpretation', 'restricted_receipts', 'public_check_boundary',
}
TERMINAL_KEYS = {
    'historical_anchors', 'source_identities_freshly_verified', 'source_intervals_parsed',
    'resolved_current_events', 'current_primary_members',
    'anchors_with_all_tracked_targets_observed_in_successful_write_or_edit_results',
    'distinct_historical_target_path_tokens', 'historical_collectively_confirmed_terminal_records',
    'anchors_with_completed_retrieval_or_search',
    'anchors_with_completed_retrieval_or_search_before_first_successful_tracked_target_write',
    'anchors_with_completed_verification_class_call', 'new_human_ratings',
    'distinct_deliverable_count', 'full_method_application_count',
}
DOCUMENTARY_KEYS = {
    'selected_chains', 'chains_with_direct_corrective_response',
    'chains_with_reported_revised_delivery', 'chains_with_prior_scoped_adoption',
    'retained_output_files_exactly_matching_logged_creation',
    'chains_with_unrecovered_final_acceptance_endpoint', 'new_human_ratings',
    'full_current_formal_method_count',
}
TIMING_KEYS = {
    'scope', 'provider_clock_chains', 'audit_capture_clock_chains',
    'chains_with_three_attributable_phase_intervals', 'private_phase_intervals',
    'pooled_duration_summary', 'nonpooling_reason', 'comparative_speed_effect',
}
INTERPRETATION_KEYS = {
    'completion_selected_not_success_rate_denominator',
    'path_tokens_not_distinct_artifact_or_deliverable_count',
    'functional_component_mapping_not_original_role_declaration',
    'historical_training_materials_not_operator_attendance',
    'assistant_delivery_not_human_acceptance', 'unrecovered_endpoint_not_failure',
    'unchanged_primary_denominator',
}
RECEIPT_KEYS = {
    'protocol_sha256', 'terminal_register_sha256', 'chain_evidence_sha256',
    'method_source_receipts_sha256',
}
SCOPE_TEXT = 'Selected observed phases, not whole tasks, active labor or time to acceptance'
BOUNDARY_TEXT = 'Aggregate accounting and receipt syntax only; private source reconstruction and semantic interpretations cannot be independently recovered from this summary.'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keys(value, expected, location):
    require(type(value) is dict, location + ': expected object')
    require(set(value) == expected, location + ': missing or unexpected field')


def count(value, location, minimum=0, maximum=None):
    require(type(value) is int, location + ': expected integer count, not boolean/float')
    require(value >= minimum, location + ': count below minimum')
    require(maximum is None or value <= maximum, location + ': count exceeds denominator')
    return value


def verify(data):
    keys(data, TOP_KEYS, 'summary')
    require(data['schema'] == SCHEMA, 'schema: unsupported version')
    require(data['analysis_contract_unchanged'] == CONTRACT, 'analysis contract changed')
    require(type(data['prepared_date']) is str and re.fullmatch(r'\d{4}-\d{2}-\d{2}', data['prepared_date']), 'prepared_date: expected ISO date only')
    try:
        date.fromisoformat(data['prepared_date'])
    except ValueError as exc:
        raise ValueError('prepared_date: invalid date') from exc
    require(data['reconstruction'] == 'AI-assisted source-linked documentary reconstruction; no new human ratings', 'reconstruction: unexpected claim or content')
    selection = data['selection']
    keys(selection, {'terminal_anchors', 'documentary_chains', 'sets_additive', 'preregistered', 'independent_human_review'}, 'selection')
    require(selection['terminal_anchors'] == 'All records from a historical completion-selected terminal queue', 'terminal selection changed')
    require(selection['documentary_chains'] == 'Three already-known purposive correction/redelivery chains', 'chain selection changed')
    for field in ('sets_additive', 'preregistered', 'independent_human_review'):
        require(selection[field] is False, 'selection.' + field + ': must remain false')
    inventory = data['terminal_inventory']
    keys(inventory, TERMINAL_KEYS, 'terminal_inventory')
    for field in TERMINAL_KEYS - {'distinct_deliverable_count', 'full_method_application_count'}:
        count(inventory[field], 'terminal_inventory.' + field)
    n = count(inventory['historical_anchors'], 'historical_anchors', minimum=1)
    for field in ['source_identities_freshly_verified', 'source_intervals_parsed',
                  'resolved_current_events', 'historical_collectively_confirmed_terminal_records',
                  'anchors_with_all_tracked_targets_observed_in_successful_write_or_edit_results']:
        require(inventory[field] == n, 'terminal_inventory.' + field + ': complete-inventory accounting mismatch')
    for field in ('current_primary_members', 'anchors_with_completed_retrieval_or_search', 'anchors_with_completed_retrieval_or_search_before_first_successful_tracked_target_write', 'anchors_with_completed_verification_class_call'):
        count(inventory[field], 'terminal_inventory.' + field, maximum=n)
    count(inventory['distinct_historical_target_path_tokens'], 'target tokens', minimum=1)
    require(inventory['anchors_with_completed_retrieval_or_search_before_first_successful_tracked_target_write'] <= inventory['anchors_with_completed_retrieval_or_search'], 'ordered retrieval/search count exceeds retrieval/search count')
    require(inventory['new_human_ratings'] == 0, 'terminal inventory cannot create human ratings')
    require(inventory['distinct_deliverable_count'] is None, 'distinct deliverable count is not established')
    require(inventory['full_method_application_count'] is None, 'full-method application count is not established')
    cases = data['documentary_inventory']
    keys(cases, DOCUMENTARY_KEYS, 'documentary_inventory')
    for field in DOCUMENTARY_KEYS - {'full_current_formal_method_count'}:
        count(cases[field], 'documentary_inventory.' + field)
    total = count(cases['selected_chains'], 'selected_chains', minimum=1)
    require(total == 3, 'selected chain count contradicts the three-chain selection statement')
    for field in ('chains_with_direct_corrective_response', 'chains_with_reported_revised_delivery', 'chains_with_unrecovered_final_acceptance_endpoint'):
        require(cases[field] == total, 'documentary_inventory.' + field + ': complete-chain accounting mismatch')
    count(cases['chains_with_prior_scoped_adoption'], 'prior scoped adoption', maximum=total)
    require(cases['new_human_ratings'] == 0, 'documentary inventory cannot create human ratings')
    require(cases['full_current_formal_method_count'] is None, 'full formal-method chain count is not established')
    timing = data['timing']
    keys(timing, TIMING_KEYS, 'timing')
    for field in ('provider_clock_chains', 'audit_capture_clock_chains', 'chains_with_three_attributable_phase_intervals', 'private_phase_intervals'):
        count(timing[field], 'timing.' + field)
    require(timing['provider_clock_chains'] + timing['audit_capture_clock_chains'] == total, 'clock groups do not sum to selected chains')
    require(timing['comparative_speed_effect'] is None, 'comparative speed effect is not established')
    require(timing['chains_with_three_attributable_phase_intervals'] == total, 'phase-covered chain count mismatch')
    require(timing['private_phase_intervals'] == 3 * total, 'three phases per chain accounting mismatch')
    require(timing['pooled_duration_summary'] is None, 'heterogeneous phase durations must not be pooled')
    require(timing['scope'] == SCOPE_TEXT, 'timing scope changed')
    require(timing['nonpooling_reason'] == 'Selected phases differ in scope and clock provenance; exact case times remain private.', 'nonpooling reason changed')
    keys(data['interpretation'], INTERPRETATION_KEYS, 'interpretation')
    for field, value in data['interpretation'].items():
        require(value is True, 'interpretation.' + field + ': must remain true')
    keys(data['restricted_receipts'], RECEIPT_KEYS, 'restricted_receipts')
    for field, value in data['restricted_receipts'].items():
        require(type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value), 'restricted_receipts.' + field + ': invalid SHA-256 receipt')
    require(data['public_check_boundary'] == BOUNDARY_TEXT, 'public check boundary changed')
    return True


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON field: ' + key)
        result[key] = value
    return result


def load_summary(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique_object)


if __name__ == '__main__':
    require(len(sys.argv) <= 2, 'usage: verify_deliverable_evidence.py [summary.json]')
    path = Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT / 'data/validation/deliverable_evidence_summary.json'
    verify(load_summary(path))
    print('DOCUMENTARY AGGREGATE: PASS (accounting and scope only, not private-source or human validation)')

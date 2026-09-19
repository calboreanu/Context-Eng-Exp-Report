#!/usr/bin/env python3
"""Verify arithmetic and cross-file consistency using public aggregates only."""

from __future__ import annotations

import csv
import argparse
import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
CATALOG = ROOT / "data" / "catalog"
PROVENANCE = ROOT / "data" / "provenance"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def close(actual: float, expected: float, label: str, tolerance: float = 1e-12) -> None:
    require((math.isnan(actual) and math.isnan(expected)) or math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance), f"{label}: {actual} != {expected}")


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing {path.relative_to(ROOT)}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key in selector rules: {key}")
        result[key] = value
    return result


def selector_label(target: dict) -> str:
    """One deterministic human-readable spelling of each executable selector."""
    if target['kind'] == 'markdown_section':
        detail = f"section={target['section']}; required_text=" + ' | '.join(target['required_text'])
    else:
        detail = '.'.join(target.get('path', [])) or 'rows'
        conditions = []
        for field, accepted in target.get('where', {}).items():
            values = accepted if isinstance(accepted, list) else [accepted]
            conditions.append(f"{field}={values[0]}" if len(values) == 1
                              else f"{field} in ({'|'.join(map(str, values))})")
        if conditions:
            detail += ' where ' + ';'.join(conditions)
        detail += '; fields=' + ','.join(target['fields'])
    return f"{target['file']} :: {detail}; expected_records={target['expected_records']}"


def resolve_claim_target(target: dict, root: Path = ROOT) -> dict:
    """Resolve public rows/fields only; never evaluate expressions or open private inputs."""
    require(isinstance(target, dict), 'claim target must be an object')
    allowed = {'file', 'kind', 'path', 'where', 'fields', 'expected_records', 'section', 'required_text'}
    require(not set(target) - allowed, 'unknown claim-selector property')
    require({'file', 'kind', 'expected_records'} <= set(target), 'incomplete claim selector')
    require(isinstance(target['file'], str) and target['file'], 'claim evidence path must be a nonempty string')
    require(isinstance(target['kind'], str), 'claim-selector kind must be a string')
    relative = Path(target['file'])
    require(not relative.is_absolute() and '..' not in relative.parts, 'claim evidence must be a relative public path')
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), f"missing or non-public claim evidence: {relative}")
    count = target['expected_records']
    require(type(count) is int and count > 0, 'expected_records must be a positive integer')
    kind = target['kind']
    if kind == 'markdown_section':
        require(path.suffix == '.md', 'section selector requires Markdown')
        require(set(target) == {'file', 'kind', 'section', 'required_text', 'expected_records'}, 'invalid section selector fields')
        require(count == 1 and isinstance(target['section'], str) and target['section'], 'invalid section selector')
        content = path.read_text(encoding='utf-8')
        headings = list(re.finditer(r'^## ([^\n]+)[ \t]*$', content, re.MULTILINE))
        matches = [(index, heading) for index, heading in enumerate(headings) if heading.group(1).strip() == target['section']]
        require(len(matches) == count, f"{relative}: expected one exact section {target['section']}")
        index, heading = matches[0]
        end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
        body = ' '.join(content[heading.end():end].split())
        phrases = target['required_text']
        require(isinstance(phrases, list) and phrases and all(isinstance(p, str) and p.strip() for p in phrases), 'required_text must contain nonempty phrases')
        require(all(' '.join(p.split()) in body for p in phrases), f"{relative}: required interpretation phrase missing from selected section")
        return {'file': str(relative), 'selected_records': 1, 'section': target['section']}
    require(kind in {'csv', 'json'}, f"unsupported selector kind: {kind}")
    require('fields' in target and not ({'section', 'required_text'} & set(target)), 'invalid tabular selector fields')
    fields = target['fields']
    require(isinstance(fields, list) and fields, 'required fields must be a nonempty unique list')
    require(all(isinstance(field, str) and re.fullmatch(r'[A-Za-z0-9_]+', field) for field in fields), 'invalid required field name')
    require(len(fields) == len(set(fields)), 'required fields must be a nonempty unique list')
    if kind == 'csv':
        require(path.suffix == '.csv' and not target.get('path'), 'CSV selector must select top-level rows')
        with path.open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames
            require(headers and all(header.strip() for header in headers), f"{relative}: CSV headers must be nonempty")
            require(len(headers) == len(set(headers)), f"{relative}: duplicate CSV header")
            records = list(reader)
    else:
        require(path.suffix == '.json', 'JSON selector requires JSON')
        value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=reject_duplicate_keys)
        parts = target.get('path', [])
        require(isinstance(parts, list) and all(isinstance(part, str) and part for part in parts), 'JSON path must be a list of literal object keys')
        for part in parts:
            require(isinstance(value, dict) and part in value, f"{relative}: JSON path key not found: {part}")
            value = value[part]
        records = value if isinstance(value, list) else [value]
    require(records and all(isinstance(row, dict) for row in records), f"{relative}: selector does not address nonempty object records")
    where = target.get('where', {})
    require(isinstance(where, dict), 'where must be an equality/membership object')
    for field, accepted in where.items():
        values = accepted if isinstance(accepted, list) else [accepted]
        require(values and all(type(v) in {str, int, float, bool} for v in values), 'filter values must be nonempty scalar choices')
        require(all(field in row for row in records), f"{relative}: filter field missing: {field}")
        records = [row for row in records if str(row[field]) in {str(v) for v in values}]
        require(records, f"{relative}: selector has no matches after {field}")
    require(len(records) == count, f"{relative}: selected {len(records)} records, expected {count}")
    require(all(all(field in row and row[field] is not None
                    and (not isinstance(row[field], str) or row[field].strip())
                    for field in fields) for row in records), f"{relative}: required selected field is missing or empty")
    return {'file': str(relative), 'selected_records': len(records), 'fields': fields}


def verify_claims(root: Path = ROOT) -> list[dict]:
    """Bind all claim-map rows to versioned executable selectors and resolve them."""
    with (root / 'data/provenance/claim_to_evidence.csv').open(newline='', encoding='utf-8') as handle:
        claims = list(csv.DictReader(handle))
    rules = json.loads((root / 'data/provenance/claim_selectors.json').read_text(encoding='utf-8'), object_pairs_hook=reject_duplicate_keys)
    require(rules.get('schema_version') == 'public-claim-selectors/1.0', 'unsupported claim-selector schema')
    expected_ids = {f'CE-C{i:02d}' for i in range(1, 13)}
    require(len(claims) == 12 and {row['claim_id'] for row in claims} == expected_ids, 'claim map must contain each of CE-C01–CE-C12 exactly once')
    require(set(rules.get('claims', {})) == expected_ids, 'selector rules must cover all and only the 12 claims')
    resolved = []
    for claim in claims:
        targets = rules['claims'][claim['claim_id']]
        require(isinstance(targets, list) and targets, f"{claim['claim_id']}: no targets")
        summaries = [resolve_claim_target(target, root) for target in targets]
        require(claim['evidence_file'].split(' and ') == [target['file'] for target in targets], f"{claim['claim_id']}: evidence-file list differs from executable targets")
        require(claim['record_selector'] == ' || '.join(selector_label(target) for target in targets), f"{claim['claim_id']}: readable selector differs from executable rule")
        if claim['generator'].endswith('.py'):
            require((root / claim['generator']).is_file(), f"{claim['claim_id']}: missing generator")
        resolved.append({'claim_id': claim['claim_id'], 'targets': summaries})
    return resolved


def verify_catalog_records(actual, generated, fields, label):
    """Compare every serialized public field, not just row totals or headline rates."""
    require(len(actual) == len(generated), f'{label}: source-derived row count mismatch')
    expected = [{field: str(row.get(field, '')) for field in fields} for row in generated]
    require(actual == expected, f'{label}: catalog fields differ from their canonical sources')


def verify_v5_boundary_summary(analysis, boundary, author_review):
    """Public conservation and historical-review limits; not a private rejoin."""
    contract = 'context-engineering-event-normalized-analysis/5.0.0'
    require(analysis['analysis_contract'] == boundary['analysis_contract'] == contract,
            'boundary summary uses a different analysis contract')
    scope, normalization = analysis['scope'], boundary['normalization']
    require(boundary['v5_analysis_scope'] == scope, 'boundary summary scope mismatch')
    require(normalization['old_source_rows'] == boundary['old_source_row_aliases'],
            'boundary source-row alias conservation mismatch')
    require(normalization['normalized_events'] + normalization['representation_reduction']
            + normalization['absorbed_nonprimary_components']
            == normalization['old_source_rows'], 'all-provider event conservation mismatch')
    require(normalization['representation_reduction'] + normalization['absorbed_nonprimary_components']
            == normalization['total_alias_to_primary_component_reduction'], 'identity/boundary reduction subtotal mismatch')
    require(normalization['resolved_events'] + normalization['quarantined_events']
            == normalization['normalized_events'], 'all-provider disposition conservation mismatch')
    require(normalization['resolved_events'] == boundary['resolved_frame_rows'] == scope['source_episode_rows'],
            'all-provider resolved-frame conservation mismatch')
    require(normalization['quarantined_events'] == boundary['held_frame_rows'],
            'all-provider held-frame conservation mismatch')
    require(sum(normalization['absorbed_nonprimary_kinds'].values())
            == normalization['absorbed_nonprimary_components'], 'boundary absorption subtotal mismatch')
    require(0 <= normalization['absorbed_nonprimary_components'] <= normalization['total_alias_to_primary_component_reduction'],
            'boundary absorptions exceed total representation reduction')
    require(boundary['human_labels_added'] == 0 and boundary['original_frozen46_confirmation_preserved'] is True,
            'technical correction must not create human labels or replace frozen confirmation')
    require(author_review['reviewed_analysis_version'] == 'event-v3'
            and author_review['applies_to_entire_corrected_analysis'] is False,
            'historical author confirmation must not transfer to the entire corrected analysis')
    require(author_review['selected_events'] == author_review['author_reported_reviewed_events']
            == author_review['collectively_confirmed_classifications'] == 46
            and author_review['inaccuracies_reported'] == 0, 'frozen author confirmation counts changed')
    review, overlap = boundary['review46'], boundary['full_primary_overlap']
    for label, item in [('review46', review), ('full_primary_overlap', overlap)]:
        total = item['historical_events']
        disposition = item['disposition_counts']
        require(sum(disposition.values()) == total, f'{label}: disposition total mismatch')
        require(item['same_measured_trajectory_and_labels_count'] + item['changed_measurements_or_trajectory_count']
                == total, f'{label}: measurement-change accounting mismatch')
        require(item['v5_primary_member_count'] == disposition.get('current_primary_unchanged', 0)
                + disposition.get('current_primary_changed', 0), f'{label}: primary-member subtotal mismatch')
        require(item['held_count'] == disposition.get('held', 0), f'{label}: held subtotal mismatch')
        require(0 <= item['distinct_v5_events'] <= total, f'{label}: invalid distinct-event count')
        require(0 <= item['condition_changed_among_current_primary_count'] <= item['v5_primary_member_count'],
                f'{label}: invalid condition-change count')
    require(review['historical_events'] == 46, 'frozen46 reconciliation coverage changed')
    require(overlap['historical_events'] == overlap['v3_primary_total']
            == 2 * boundary['v3_analysis_scope']['primary_frontloaded_balanced_per_condition'],
            'historical primary reconciliation coverage mismatch')
    require(overlap['v5_primary_total'] == 2 * scope['primary_frontloaded_balanced_per_condition'],
            'current primary reconciliation coverage mismatch')
    require(overlap['v5_primary_distinct_events_reached_from_v3_primary']
            + overlap['v5_primary_events_not_reached_from_v3_primary'] == overlap['v5_primary_total'],
            'current primary reached/unreached conservation mismatch')


def verify_historical_evidence_overlap(history):
    """Check aggregate rejoins without presenting operational evidence as new ratings."""
    require(history['all138']['historical_records'] == 138
            and history['historical_v2_primary49']['historical_records'] == 49
            and history['documentary_chain_count'] == 3, 'historical evidence universe changed')
    for label in ['all138', 'historical_v2_primary49', 'documentary_chain_intervals', 'proof_case_anchors']:
        item = history[label]
        records, distinct = item['historical_records'], item['distinct_v5_events']
        primary, mapped = item['distinct_v5_primary_events'], item['historical_records_mapping_to_v5_primary']
        counts = [records, distinct, primary, mapped,
                  *item['distinct_v5_primary_events_by_cohort'].values(),
                  *item['distinct_v5_event_status_counts'].values()]
        require(all(type(value) is int and value >= 0 for value in counts),
                f'{label}: historical overlap must contain nonnegative integer counts')
        require(primary <= distinct <= records and primary <= mapped <= records,
                f'{label}: historical/distinct count bounds mismatch')
        require(sum(item['distinct_v5_primary_events_by_cohort'].values()) == primary,
                f'{label}: primary cohort subtotal mismatch')
        require(sum(item['distinct_v5_event_status_counts'].values()) == distinct,
                f'{label}: distinct status subtotal mismatch')


def verify_analysis_receipts(analysis, impact, artifacts, analysis_root=None):
    """Bind available files and declared withheld files to one analytical manifest."""
    analysis_root = analysis_root or ROOT / 'analysis'
    expected_artifacts = {'R-INPUT', 'R-STRATA', 'R-PRIMARY', 'R-UNRESTRICTED', 'R-LINKAGE',
                          'R-ALIASES', 'R-QUARANTINE', 'R-NORMALIZATION', 'R-BOUNDARIES',
                          'R-REVIEW46', 'R-PRIMARY-REJOIN', 'R-HISTORY-REJOIN', 'R-ACTION-REFERENCE'}
    require(len(artifacts) == len(expected_artifacts)
            and {row['artifact_id'] for row in artifacts} == expected_artifacts,
            'restricted receipt IDs are incomplete or duplicated')
    receipts = {row['artifact_id']: row for row in artifacts}
    for row in artifacts:
        require(re.fullmatch(r'[0-9a-f]{64}', row['sha256']) is not None
                and row['bytes'].isdigit() and int(row['bytes']) > 0
                and row['release_status'] == 'withheld', 'invalid restricted artifact receipt')
    require(receipts['R-INPUT']['sha256'] == analysis['input']['sha256']
            and int(receipts['R-INPUT']['bytes']) == analysis['input']['bytes'],
            'restricted input receipt does not match analysis')
    require(receipts['R-NORMALIZATION']['sha256'] == analysis['normalization_receipt']['sha256']
            == impact['normalization_receipt_sha256'], 'normalization receipt identity mismatch')
    withheld = {'results/balanced_strata.csv': 'R-STRATA',
                'results/restricted/primary_balanced_rows.csv': 'R-PRIMARY',
                'results/restricted/unrestricted_balanced_rows.csv': 'R-UNRESTRICTED',
                'results/restricted/inheritance_candidate_map.csv': 'R-LINKAGE'}
    manifest = {}
    for line in (analysis_root / 'ANALYSIS_MANIFEST.sha256').read_text(encoding='utf-8').splitlines():
        pieces = line.split(None, 1)
        require(len(pieces) == 2 and re.fullmatch(r'[0-9a-f]{64}', pieces[0]) is not None,
                'invalid analytical manifest record')
        expected, name = pieces
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts and name not in manifest,
                'unsafe or duplicated analytical manifest path')
        manifest[name] = expected
        path = analysis_root / relative
        if name in withheld:
            require(not path.exists(), f'withheld analytical file is present: {name}')
            require(receipts[withheld[name]]['sha256'] == expected,
                    f'withheld receipt does not match analytical manifest: {name}')
        else:
            require(path.is_file() and path.resolve().is_relative_to(analysis_root.resolve()),
                    f'missing public analytical manifest member: {name}')
            require(hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                    f'public analytical manifest mismatch: {name}')
    require(set(withheld) <= set(manifest), 'analytical manifest omits expected withheld outputs')
    require({'results/analysis_summary.json', 'results/boundary_correction_summary.json',
             'results/action_reference_correction_summary.json',
             'EVENT_CORRECTION_IMPACT.json'} <= set(manifest), 'analytical manifest omits v5 aggregate identities')


def verify_v5_action_reference_summary(analysis, boundary, correction):
    """Check public change accounting; do not infer private-label accuracy."""
    require(correction['analysis_contract'] == analysis['analysis_contract']
            == 'context-engineering-event-normalized-analysis/5.0.0', 'action/reference contract mismatch')
    require(set(correction['input_sha256']) == set(correction['analysis_scope']) == {'v4', 'v5'},
            'action/reference version comparison incomplete')
    require(correction['input_sha256']['v5'] == analysis['input']['sha256'],
            'action/reference current input mismatch')
    require(all(re.fullmatch(r'[0-9a-f]{64}', value) is not None
                for value in correction['input_sha256'].values()), 'invalid action/reference input receipt')
    require(correction['analysis_scope']['v5'] == analysis['scope'], 'action/reference current scope mismatch')
    require(correction['human_labels_added'] == 0 and correction['historical_confirmation_transferred'] is False,
            'action/reference repair must not create or transfer human labels')

    def counts(values, label):
        require(isinstance(values, dict) and all(type(v) is int and v >= 0 for v in values.values()),
                f'{label}: nonnegative integer counts required')

    total = correction['unchanged_native_event_identities']
    require(type(total) is int and total == boundary['normalization']['normalized_events'],
            'action/reference native-event total mismatch')
    counts({'native_invariant_checks': correction['native_invariant_checks']}, 'native invariants')
    transitions = correction['status_transitions']
    counts(transitions, 'status transitions')
    require(sum(transitions.values()) == total, 'status-transition conservation mismatch')
    for key in transitions:
        require(key in {'resolved->resolved', 'resolved->quarantined',
                        'quarantined->resolved', 'quarantined->quarantined'}, 'unknown status transition')
    for version, index in [('v4', 0), ('v5', 1)]:
        resolved = sum(v for k, v in transitions.items() if k.split('->')[index] == 'resolved')
        require(resolved == correction['analysis_scope'][version]['source_episode_rows'],
                f'{version}: status/scope mismatch')
    counts(correction['measurement_changes'], 'measurement changes')
    for key, value in correction['measurement_changes'].items():
        if key.endswith('_events'):
            require(value <= total, f'{key}: changed events exceed native frame')

    exposure_groups = {'v4_resolved', 'v4_primary_ce', 'v4_primary_comparison',
                       'v4_unrestricted_ce', 'v4_unrestricted_comparison'}
    for measure, values in correction['fixed_v4_selection_exposure'].items():
        counts(values, f'{measure} exposure')
        require(set(values) <= exposure_groups, 'unexpected exposure group')
        for group, value in values.items():
            if measure == 'successful_todowrite_calls':
                continue
            scope = correction['analysis_scope']['v4']
            limit = (scope['source_episode_rows'] if group == 'v4_resolved'
                     else scope['primary_frontloaded_balanced_per_condition'] if group.startswith('v4_primary_')
                     else scope['unrestricted_balanced_per_condition'])
            require(value <= limit, f'{measure}: exposure exceeds fixed historical sample')

    require(set(correction['sample_membership']) == {'primary', 'unrestricted'},
            'action/reference sample comparison incomplete')
    for sample, values in correction['sample_membership'].items():
        counts(values, f'{sample} membership')
        scope_key = ('primary_frontloaded_balanced_per_condition' if sample == 'primary'
                     else 'unrestricted_balanced_per_condition')
        for version in ('v4', 'v5'):
            require(values[version + '_total'] == 2 * correction['analysis_scope'][version][scope_key],
                    f'{sample}: sample/scope total mismatch')
        retained = values['retained_distinct_events']
        require(retained + values['removed_events'] == values['v4_total']
                and retained + values['newly_selected_events'] == values['v5_total'],
                f'{sample}: sample-membership conservation mismatch')
        require(values['retained_same_condition'] + values['retained_changed_condition'] == retained,
                f'{sample}: retained-condition conservation mismatch')

    require(set(correction['source_accounting']) == {'v4', 'v5'}, 'source comparison incomplete')
    for version, values in correction['source_accounting'].items():
        counts(values, f'{version} source accounting')
        delta = values['contributing_not_canonical_resolved']
        require(values['canonical_resolved_sources']
                == correction['analysis_scope'][version]['source_conversation_count'], 'canonical source/scope mismatch')
        require(values['canonical_resolved_sources'] + delta == values['contributing_alias_sources'],
                'alias/canonical source reconciliation mismatch')
        require(values['delta_with_resolved_alias'] + values['delta_only_held_alias'] == delta,
                'source alias-role reconciliation mismatch')
        require(values['delta_canonical_held'] + values['delta_without_any_canonical_role'] == delta,
                'source canonical-role reconciliation mismatch')
        require(values['delta_with_held_alias'] <= delta, 'held alias-source count exceeds source difference')
    require(set(correction['unchanged_tool_names_resolved_occurrence_counts']) == {'v4', 'v5'},
            'tool occurrence version comparison incomplete')
    for version, values in correction['unchanged_tool_names_resolved_occurrence_counts'].items():
        require(set(values) == {'bashoutput', 'killshell'}, 'unexpected tool occurrence name')
        counts(values, 'tool occurrence')
    phrase = correction['phrase_overlap_exposure']
    require(phrase['pattern'] == r'\bcontext package\b' and set(phrase['counts']) == {'v4', 'v5'},
            'phrase-overlap scope mismatch')
    for version, values in phrase['counts'].items():
        counts(values, 'phrase overlap')
        require(set(values) == {'resolved_events', 'eligible_ce_events', 'eligible_comparison_events',
                               'primary_events', 'unrestricted_events', 'sole_packaging_trigger_events'},
                'phrase-overlap field mismatch')
        scope = correction['analysis_scope'][version]
        eligible = values['eligible_ce_events'] + values['eligible_comparison_events']
        require(eligible <= values['resolved_events'] <= scope['source_episode_rows']
                and values['sole_packaging_trigger_events'] <= values['resolved_events'],
                'phrase-overlap frame bounds mismatch')
        for sample, key in [('primary', 'primary_frontloaded_balanced_per_condition'),
                            ('unrestricted', 'unrestricted_balanced_per_condition')]:
            require(values[sample + '_events'] <= min(eligible, 2 * scope[key]),
                    'phrase-overlap selected bounds mismatch')


def effect(ce: float, comparison: float, scale: str) -> float:
    if "risk_difference" in scale:
        return ce - comparison
    if "ratio" in scale:
        return ce / comparison if comparison > 0 else math.nan
    raise RuntimeError(f"unknown effect scale {scale}")


def verify_pooled() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(RESULTS / "pooled_summary.csv")
    require(len(rows) == 18, "pooled_summary.csv must have 18 rows")
    index = {}
    for row in rows:
        key = (row["analysis_set"], row["metric"])
        require(key not in index, f"duplicate pooled row {key}")
        close(float(row["effect"]), effect(float(row["ce_value"]), float(row["comparison_value"]), row["effect_scale"]), f"pooled {key}")
        if "risk_difference" in row["effect_scale"]:
            n = int(row["rows_per_condition"])
            close(float(row["ce_value"]) * n, round(float(row["ce_value"]) * n), f"pooled CE numerator {key}", 1e-9)
            close(float(row["comparison_value"]) * n, round(float(row["comparison_value"]) * n), f"pooled comparison numerator {key}", 1e-9)
        index[key] = row
    scope = json.loads((RESULTS / "analysis_summary.json").read_text())["scope"]
    for analysis_set, expected_n in [("primary_frontloaded", scope["primary_frontloaded_balanced_per_condition"]), ("unrestricted", scope["unrestricted_balanced_per_condition"])]:
        subset = [row for row in rows if row["analysis_set"] == analysis_set]
        require(len(subset) == 9, f"{analysis_set}: expected nine metrics")
        require({int(row["rows_per_condition"]) for row in subset} == {expected_n}, f"{analysis_set}: denominator mismatch")
        for row in subset:
            for field in ("ce_observed", "comparison_observed"):
                require(0 <= int(row[field]) <= expected_n, f"{analysis_set}: invalid observed count")
                if row["metric"] not in {"duration_min", "min_per_action"}:
                    require(int(row[field]) == expected_n, f"{analysis_set}: unexpected non-timing missingness")
    return index


def verify_station_and_equal() -> None:
    station = read_csv(RESULTS / "station_effects.csv")
    equal = read_csv(RESULTS / "equal_station_summary.csv")
    minimum = read_csv(RESULTS / "minimum_station_size_summary.csv")
    require(bool(station), "station_effects.csv must not be empty")
    require(len({(r['analysis_set'], r['station_id'], r['metric']) for r in station}) == len(station), "duplicate station metric")
    require(len(equal) == 18 and len(minimum) == 18, "equal-station tables must each have 18 rows")
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in station:
        key = (row["analysis_set"], row["metric"])
        close(float(row["effect"]), effect(float(row["ce_value"]), float(row["comparison_value"]), row["effect_scale"]), f"station {key}/{row['station_id']}")
        grouped[key].append(row)
    for aset in {key[0] for key in grouped}:
        station_sets = [{r['station_id'] for r in rows} for key, rows in grouped.items() if key[0] == aset]
        require(all(s == station_sets[0] for s in station_sets), "station metric coverage mismatch")

    for row in equal:
        values = [float(item["effect"]) for item in grouped[(row["analysis_set"], row["metric"])]]
        if "risk_difference" not in row["effect_scale"]:
            values = [v for v in values if math.isfinite(v) and v > 0]
        expected = (statistics.mean(values) if "risk_difference" in row["effect_scale"] else math.exp(statistics.mean(math.log(value) for value in values))) if values else math.nan
        close(float(row["effect"]), expected, f"equal station {row['analysis_set']}/{row['metric']}")
        require(int(row["stations"]) == len(values), "equal-station count mismatch")

    for row in minimum:
        base_set = row["analysis_set"].removesuffix("_min20")
        selected = [item for item in grouped[(base_set, row["metric"])] if int(item["balanced_per_condition"]) >= 20]
        values = [float(item["effect"]) for item in selected]
        if "risk_difference" not in row["effect_scale"]:
            values = [v for v in values if math.isfinite(v) and v > 0]
        expected = (statistics.mean(values) if "risk_difference" in row["effect_scale"] else math.exp(statistics.mean(math.log(value) for value in values))) if values else math.nan
        close(float(row["effect"]), expected, f"minimum station {row['analysis_set']}/{row['metric']}")
        require(int(row["stations"]) == len(values), "minimum-station count mismatch")


def verify_archive() -> None:
    rows = read_csv(RESULTS / "archive_group_summary.csv")
    require(len(rows) == 36, "archive_group_summary.csv must have 36 rows")
    for row in rows:
        close(float(row["effect"]), effect(float(row["ce_value"]), float(row["comparison_value"]), row["effect_scale"]), f"archive {row['analysis_set']}/{row['archive_group']}/{row['metric']}")


def verify_action_count(pooled: dict[tuple[str, str], dict[str, str]]) -> None:
    strata = read_csv(RESULTS / "action_count_verification_strata.csv")
    require(bool(strata), "action-count strata must not be empty")
    require(len({(r['analysis_set'], r['archive_batch'], r['action_bin']) for r in strata}) == len(strata), "duplicate action-count bin")
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in strata:
        close(float(row["ce_rate"]), int(row["ce_k"]) / int(row["ce_n"]), "action CE rate")
        close(float(row["comparison_rate"]), int(row["comparison_k"]) / int(row["comparison_n"]), "action comparison rate")
        close(float(row["gap"]), float(row["ce_rate"]) - float(row["comparison_rate"]), "action gap")
        grouped[(row["analysis_set"], row["archive_batch"])].append(row)
    for key, rows in grouped.items():
        close(sum(float(row["comparison_weight"]) for row in rows), 1.0, f"action weights {key}")

    summary = json.loads((RESULTS / "action_count_verification_summary.json").read_text(encoding="utf-8"))
    require(len(summary["summaries"]) == 3, "action-count summary must have three views")
    for item in summary["summaries"]:
        key = (item["analysis_set"], item["archive_batch"])
        expected = sum(float(row["gap"]) * float(row["comparison_weight"]) for row in grouped[key])
        close(float(item["comparator_standardized_gap"]), expected, f"action standardized {key}")
        if item["archive_batch"] == "all":
            raw = float(pooled[(item["analysis_set"], "verification_successful")]["effect"])
            close(float(item["raw_gap"]), raw, f"action raw gap {key}")


def verify_inheritance() -> None:
    rows = read_csv(RESULTS / "inheritance_window_sensitivity.csv")
    summary = json.loads((RESULTS / "inheritance_pilot_summary.json").read_text(encoding="utf-8"))
    require(len(rows) == 5, "inheritance sensitivity must have five windows")
    require(sum(summary["tier_counts"].values()) == summary["scope"]["action_eligible_comparison_rows_mapped"], "inheritance tier total mismatch")
    require(sum(summary["class_counts"].values()) == summary["scope"]["action_eligible_comparison_rows_mapped"], "inheritance class total mismatch")
    by_window = {int(item["window"]): item for item in summary["sensitivity"]}
    for row in rows:
        window = int(row["window"])
        close(float(row["candidate_positive_rate"]), int(row["candidate_positive"]) / int(row["eligible_rows"]), f"inheritance window {window}")
        require(int(row["unresolved"]) == int(row["eligible_rows"]) - int(row["candidate_positive"]), f"inheritance unresolved {window}")
        require(by_window[window] == {
            "window": window,
            "candidate_positive": int(row["candidate_positive"]),
            "eligible_rows": int(row["eligible_rows"]),
            "candidate_positive_rate": float(row["candidate_positive_rate"]),
            "unresolved": int(row["unresolved"]),
        }, f"inheritance summary mismatch at {window}")


def verify_scope_and_catalog() -> None:
    analysis = json.loads((RESULTS / "analysis_summary.json").read_text(encoding="utf-8"))
    scope = analysis["scope"]
    require(0 < scope["source_episode_rows"] <= 31919, "normalized frame exceeds retained intake")
    require(scope["source_station_archives"] == 13, "archive count mismatch")
    receipts = {row["receipt_id"]: row for row in read_csv(PROVENANCE / "source_chain_receipts.csv")}
    require(int(receipts["SRC-02"]["episode_rows"]) + int(receipts["SRC-03"]["episode_rows"]) == int(receipts["SRC-04"]["episode_rows"]), "source-frame replay arithmetic mismatch")
    require(int(receipts["SRC-04"]["episode_rows"]) == 31919, "pre-normalization receipt mismatch")
    require(int(receipts["SRC-08"]["episode_rows"]) == scope["source_episode_rows"], "normalization receipt and summary mismatch")
    require(receipts["SRC-08"]["input_sha256"] == analysis['input']['sha256'], "normalized input identity mismatch")
    impact = json.loads((ROOT / 'analysis/EVENT_CORRECTION_IMPACT.json').read_text())
    intake, events = impact['intake'], impact['event_accounting']
    require(intake['recognized_prompt_occurrences'] - intake['delegated_source_occurrences']
            == intake['retained_source_segments'] == 31919, 'intake conservation mismatch')
    require(analysis['analysis_contract'] == 'context-engineering-event-normalized-analysis/5.0.0',
            'public candidate does not contain finalized event-v5 results')
    require(events['old_source_rows'] == events['old_claude_rows'] + impact['rescreened_codex_input_rows'] == 31919,
            'provider intake conservation mismatch')
    require(events['normalized_events'] + events['representation_reduction']
            + events['absorbed_nonprimary_components'] == events['old_source_rows'],
            'native-event representation conservation mismatch')
    require(events['resolved_events'] + events['quarantined_events'] == events['normalized_events'],
            'native-event disposition conservation mismatch')
    require(events['resolved_events'] == scope['source_episode_rows']
            == impact['resolved_frame_rows'], 'resolved frame conservation mismatch')
    require(impact['quarantined_frame_rows'] == events['quarantined_events'], 'quarantine mismatch')
    require(sum(impact['exclusive_waterfall'].values()) == scope['source_episode_rows'], 'gate waterfall mismatch')
    require(sum(impact['origin_counts'].values()) == sum(impact['route_counts'].values())
            == scope['source_episode_rows'], 'origin/route conservation mismatch')
    require(impact['exclusive_waterfall']['eligible_pool'] == scope['action_eligible_ce_candidates']
            + scope['action_eligible_routed_comparisons'], 'eligible-pool gate mismatch')
    require(impact['input'] == analysis['input'] and impact['human_labels_added'] == 0,
            'correction identity or human-label claim mismatch')
    boundary = json.loads((RESULTS / 'boundary_correction_summary.json').read_text(encoding='utf-8'))
    author_review = json.loads((ROOT / 'data/validation/author_review_summary.json').read_text(encoding='utf-8'))
    verify_v5_boundary_summary(analysis, boundary, author_review)
    action_reference = json.loads((RESULTS / 'action_reference_correction_summary.json').read_text(encoding='utf-8'))
    verify_v5_action_reference_summary(analysis, boundary, action_reference)
    verify_historical_evidence_overlap(boundary['historical_evidence_overlap'])
    require(boundary['normalization'] == events and boundary['review46'] == impact['frozen_review46_summary'],
            'boundary and correction-impact counters differ')
    require(impact['analysis_scope']['preceding_event_v3'] == boundary['v3_analysis_scope']
            and impact['analysis_scope']['event_v5'] == scope, 'versioned scope identity mismatch')
    verify_analysis_receipts(analysis, impact, read_csv(PROVENANCE / 'restricted_artifact_receipts.csv'))
    catalog = read_csv(CATALOG / "aggregate_catalog.csv")
    from build_public_catalog import CATALOG_FIELDS, build_catalog, build_dictionary, build_source_frame
    generated = build_catalog()
    verify_catalog_records(catalog, generated, CATALOG_FIELDS, 'aggregate catalog')
    verify_catalog_records(read_csv(CATALOG / 'source_frame_summary.csv'), build_source_frame(),
                           ['item_id', 'scope', 'measure', 'value', 'unit', 'source_file', 'notes'], 'source-frame catalog')
    verify_catalog_records(read_csv(CATALOG / 'data_dictionary.csv'), build_dictionary(),
                           ['artifact', 'field', 'data_type', 'definition', 'unit', 'nullable', 'disclosure_class'], 'data dictionary')
    require(len({row["record_id"] for row in catalog}) == len(catalog), "aggregate catalog record IDs are not unique")
    for row in catalog:
        if row["view"] in {"pooled", "station", "archive_batch"} and "risk_difference" in row["effect_scale"]:
            require(all(row[field] != "" for field in ["ce_k", "ce_n", "comparison_k", "comparison_n"]), f"missing exact counts in catalog row {row['record_id']}")
            require(int(row["ce_k"]) / int(row["ce_n"]) == float(row["ce_value"]), f"catalog CE k/n mismatch {row['record_id']}")
            require(int(row["comparison_k"]) / int(row["comparison_n"]) == float(row["comparison_value"]), f"catalog comparison k/n mismatch {row['record_id']}")
    primary_verification = next(
        row for row in catalog
        if row["view"] == "pooled" and row["analysis_set"] == "primary_frontloaded"
        and row["metric"] == "verification_successful"
    )
    pooled_primary = next(r for r in read_csv(RESULTS / 'pooled_summary.csv')
                          if r['analysis_set'] == 'primary_frontloaded' and r['metric'] == 'verification_successful')
    n = scope['primary_frontloaded_balanced_per_condition']
    require((int(primary_verification['ce_k']), int(primary_verification['ce_n']),
             int(primary_verification['comparison_k']), int(primary_verification['comparison_n']))
            == (round(float(pooled_primary['ce_value']) * n), n,
                round(float(pooled_primary['comparison_value']) * n), n),
            'primary headline verification counts mismatch')


def verify_licenses() -> None:
    apache = ROOT / "LICENSE"
    cc = ROOT / "LICENSES" / "CC-BY-4.0.md"
    mapping = ROOT / "LICENSING.md"
    require(apache.is_file() and cc.is_file() and mapping.is_file(), "dual-license files are incomplete")
    require("Apache License" in apache.read_text(encoding="utf-8") and "Version 2.0" in apache.read_text(encoding="utf-8"), "Apache-2.0 text is invalid")
    require("https://creativecommons.org/licenses/by/4.0/legalcode" in cc.read_text(encoding="utf-8"), "CC BY 4.0 legal-code link is missing")
    mapping_text = mapping.read_text(encoding="utf-8")
    require("Apache-2.0" in mapping_text and "CC-BY-4.0" in mapping_text, "component-license mapping is incomplete")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--claims-only', action='store_true', help='Resolve all 12 public claim selectors and print their selected-record counts; do not run the numerical checks.')
    args = parser.parse_args()
    claims = verify_claims()
    if args.claims_only:
        print(json.dumps(claims, indent=2))
        print('PUBLIC CLAIM SELECTORS: PASS (12 claims)')
        return
    pooled = verify_pooled()
    verify_station_and_equal()
    verify_archive()
    verify_action_count(pooled)
    verify_inheritance()
    verify_scope_and_catalog()
    verify_licenses()
    print('PUBLIC CLAIM SELECTORS: PASS (12 claims; exact expected records and fields)')
    print("PUBLIC AGGREGATE VERIFICATION: PASS")


if __name__ == "__main__":
    main()

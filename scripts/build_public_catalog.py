#!/usr/bin/env python3
"""Build deterministic public catalogs from the approved aggregate outputs."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
CATALOG = ROOT / "data" / "catalog"
PROVENANCE = ROOT / "data" / "provenance"

CATALOG_FIELDS = [
    "record_id", "view", "analysis_set", "subgroup_type", "subgroup_value",
    "metric", "metric_label", "effect_scale", "ce_k", "ce_n", "ce_value",
    "comparison_k", "comparison_n", "comparison_value", "effect", "ci_low",
    "ci_high", "rows_per_condition", "stations", "positive_stations",
    "tie_stations", "negative_stations", "descriptive_sign_p", "window",
    "candidate_positive", "eligible_rows", "unresolved", "source_file",
    "source_record",
    "ce_observed", "comparison_observed",
]


FIELD_DEFINITIONS = {
    "analysis_set": ("string", "Analysis construction or sensitivity population."),
    "archive_batch": ("string", "Initial, subsequent, or all archive captures."),
    "archive_group": ("string", "Pseudonymous capture-batch grouping."),
    "action_bin": ("string", "Completed substantive-action count interval."),
    "balanced_per_condition": ("integer", "Selected observations in each condition for a station or stratum."),
    "candidate_positive": ("integer", "Rows marked candidate-positive by the automated linkage rule."),
    "candidate_positive_rate": ("proportion", "Candidate-positive rows divided by eligible rows."),
    "ce_available": ("integer", "Eligible context-operation candidates before balancing."),
    "ce_k": ("integer", "Context-operation condition numerator."),
    "ce_n": ("integer", "Context-operation condition denominator."),
    "ce_rate": ("proportion", "Context-operation condition numerator divided by denominator."),
    "ce_value": ("number", "Context-operation condition rate or median, according to effect scale."),
    "ce_observed": ("integer", "Finite observations used in the context-operation condition estimate; timing may be unavailable."),
    "comparison_observed": ("integer", "Finite observations used in the comparison estimate; timing may be unavailable."),
    "comparison_available": ("integer", "Eligible routed comparisons before balancing."),
    "comparison_k": ("integer", "Routed-comparison numerator."),
    "comparison_n": ("integer", "Routed-comparison denominator."),
    "comparison_rate": ("proportion", "Routed-comparison numerator divided by denominator."),
    "comparison_value": ("number", "Routed-comparison rate or median, according to effect scale."),
    "comparison_weight": ("proportion", "Action-bin share in the routed-comparison condition."),
    "contributing_stations": ("integer", "Pseudonymous stations contributing to the view."),
    "descriptive_sign_p": ("proportion", "Two-sided exact descriptive sign-test probability."),
    "effect": ("number", "Condition difference or ratio defined by effect_scale."),
    "effect_scale": ("string", "Risk difference, ratio of medians, or equal-station mean risk difference."),
    "eligible_rows": ("integer", "Rows eligible for the linkage sensitivity denominator."),
    "gap": ("proportion", "Within-action-bin verification-rate difference."),
    "metric": ("string", "Stable machine-readable metric identifier."),
    "metric_label": ("string", "Human-readable metric description."),
    "negative_stations": ("integer", "Stations with a negative metric contrast."),
    "positive_stations": ("integer", "Stations with a positive metric contrast."),
    "rows_per_condition": ("integer", "Observations in each balanced condition."),
    "station_id": ("string", "Pseudonymous station label with no public identity key."),
    "stations": ("integer", "Number of stations in an equal-station summary."),
    "tie_stations": ("integer", "Stations with a zero metric contrast."),
    "unresolved": ("integer", "Eligible linkage rows unresolved at the stated window."),
    "window": ("integer", "Maximum prior prompt-episode distance in the linkage sensitivity."),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def record_id(view: str, source_record: str) -> str:
    digest = hashlib.sha256(f"{view}|{source_record}".encode()).hexdigest()[:12]
    return f"AGG-{digest}"


def normalized(view: str, source_file: str, source_record: str, **values: object) -> dict[str, object]:
    return {
        "record_id": record_id(view, source_record),
        "view": view,
        "source_file": source_file,
        "source_record": source_record,
        **values,
    }


def exact_binary_counts(row: dict[str, str], denominator: str) -> dict[str, int]:
    """Expose exact k/n when full-precision public rates make them deterministic."""
    if "risk_difference" not in row["effect_scale"]:
        return {}
    n = int(denominator)
    counts: dict[str, int] = {"ce_n": n, "comparison_n": n}
    for prefix, field in [("ce", "ce_value"), ("comparison", "comparison_value")]:
        candidate = float(row[field]) * n
        rounded = round(candidate)
        if abs(candidate - rounded) > 1e-9:
            raise RuntimeError(f"{row['analysis_set']}/{row['metric']}: non-integral {prefix} numerator")
        counts[f"{prefix}_k"] = rounded
    return counts


def build_catalog() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for index, row in enumerate(read_csv(RESULTS / "pooled_summary.csv"), start=2):
        rows.append(normalized(
            "pooled", "analysis/results/pooled_summary.csv", f"row={index}",
            analysis_set=row["analysis_set"], subgroup_type="overall", subgroup_value="all",
            metric=row["metric"], metric_label=row["metric_label"], effect_scale=row["effect_scale"],
            ce_value=row["ce_value"], comparison_value=row["comparison_value"], effect=row["effect"],
            rows_per_condition=row["rows_per_condition"],
            ce_observed=row["ce_observed"], comparison_observed=row["comparison_observed"],
            **exact_binary_counts(row, row["rows_per_condition"]),
        ))

    for index, row in enumerate(read_csv(RESULTS / "station_effects.csv"), start=2):
        rows.append(normalized(
            "station", "analysis/results/station_effects.csv", f"row={index}",
            analysis_set=row["analysis_set"], subgroup_type="station", subgroup_value=row["station_id"],
            metric=row["metric"], metric_label=row["metric_label"], effect_scale=row["effect_scale"],
            ce_value=row["ce_value"], comparison_value=row["comparison_value"], effect=row["effect"],
            rows_per_condition=row["balanced_per_condition"], stations=1,
            ce_observed=row["ce_observed"], comparison_observed=row["comparison_observed"],
            **exact_binary_counts(row, row["balanced_per_condition"]),
        ))

    for filename, view in [
        ("equal_station_summary.csv", "equal_station"),
        ("minimum_station_size_summary.csv", "minimum_station_size"),
    ]:
        for index, row in enumerate(read_csv(RESULTS / filename), start=2):
            rows.append(normalized(
                view, f"analysis/results/{filename}", f"row={index}",
                analysis_set=row["analysis_set"], subgroup_type="overall", subgroup_value="all",
                metric=row["metric"], metric_label=row["metric_label"], effect_scale=row["effect_scale"],
                effect=row["effect"], ci_low=row["ci_low"], ci_high=row["ci_high"],
                stations=row["stations"], positive_stations=row["positive_stations"],
                tie_stations=row["tie_stations"], negative_stations=row["negative_stations"],
                descriptive_sign_p=row["descriptive_sign_p"],
            ))

    for index, row in enumerate(read_csv(RESULTS / "archive_group_summary.csv"), start=2):
        rows.append(normalized(
            "archive_batch", "analysis/results/archive_group_summary.csv", f"row={index}",
            analysis_set=row["analysis_set"], subgroup_type="archive_batch", subgroup_value=row["archive_group"],
            metric=row["metric"], metric_label=row["metric_label"], effect_scale=row["effect_scale"],
            ce_value=row["ce_value"], comparison_value=row["comparison_value"], effect=row["effect"],
            rows_per_condition=row["rows_per_condition"], stations=row["contributing_stations"],
            ce_observed=row["ce_observed"], comparison_observed=row["comparison_observed"],
            **exact_binary_counts(row, row["rows_per_condition"]),
        ))

    for index, row in enumerate(read_csv(RESULTS / "action_count_verification_strata.csv"), start=2):
        subgroup = f"{row['archive_batch']}|{row['action_bin']}"
        rows.append(normalized(
            "action_count_bin", "analysis/results/action_count_verification_strata.csv", f"row={index}",
            analysis_set=row["analysis_set"], subgroup_type="archive_batch|action_bin", subgroup_value=subgroup,
            metric="verification_successful", metric_label="Completed-successful verification call",
            effect_scale="risk_difference", ce_k=row["ce_k"], ce_n=row["ce_n"], ce_value=row["ce_rate"],
            comparison_k=row["comparison_k"], comparison_n=row["comparison_n"],
            comparison_value=row["comparison_rate"], effect=row["gap"],
        ))

    action = json.loads((RESULTS / "action_count_verification_summary.json").read_text(encoding="utf-8"))
    for item in action["summaries"]:
        selector = f"{item['analysis_set']}|{item['archive_batch']}"
        rows.append(normalized(
            "action_count_standardized", "analysis/results/action_count_verification_summary.json", selector,
            analysis_set=item["analysis_set"], subgroup_type="archive_batch", subgroup_value=item["archive_batch"],
            metric="verification_successful", metric_label="Comparator-standardized verification gap",
            effect_scale="comparator_weighted_risk_difference", effect=item["comparator_standardized_gap"],
            rows_per_condition=item["rows_per_condition"],
        ))

    for index, row in enumerate(read_csv(RESULTS / "inheritance_window_sensitivity.csv"), start=2):
        rows.append(normalized(
            "linkage_window", "analysis/results/inheritance_window_sensitivity.csv", f"row={index}",
            analysis_set="three_station_linkage_pilot", subgroup_type="window", subgroup_value=row["window"],
            metric="candidate_positive_rate", metric_label="Automated candidate-positive linkage rate",
            effect_scale="proportion", effect=row["candidate_positive_rate"], window=row["window"],
            candidate_positive=row["candidate_positive"], eligible_rows=row["eligible_rows"],
            unresolved=row["unresolved"],
        ))

    inheritance = json.loads((RESULTS / "inheritance_pilot_summary.json").read_text(encoding="utf-8"))
    for view, key in [("linkage_tier", "tier_counts"), ("linkage_class", "class_counts")]:
        for label, count in sorted(inheritance[key].items()):
            rows.append(normalized(
                view, "analysis/results/inheritance_pilot_summary.json", f"{key}.{label}",
                analysis_set="three_station_linkage_pilot", subgroup_type=view, subgroup_value=label,
                metric="row_count", metric_label="Automated linkage row count", effect_scale="count",
                effect=count,
            ))

    return rows


def build_source_frame() -> list[dict[str, object]]:
    analysis = json.loads((RESULTS / "analysis_summary.json").read_text(encoding="utf-8"))
    inheritance = json.loads((RESULTS / "inheritance_pilot_summary.json").read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for key, value in analysis["scope"].items():
        rows.append({
            "item_id": f"FRAME-{len(rows)+1:02d}", "scope": "13-archive source frame and matched analyses",
            "measure": key, "value": value, "unit": "count",
            "source_file": "analysis/results/analysis_summary.json", "notes": "Restricted input receipt and verified local rerun",
        })
    for key, value in inheritance["scope"].items():
        if isinstance(value, list):
            value = "|".join(value)
            unit = "controlled_values"
        elif isinstance(value, (int, float)):
            unit = "count"
        else:
            unit = "definition"
        rows.append({
            "item_id": f"FRAME-{len(rows)+1:02d}", "scope": "three-station linkage pilot",
            "measure": key, "value": value, "unit": unit,
            "source_file": "analysis/results/inheritance_pilot_summary.json", "notes": "Automated and unadjudicated candidate linkage",
        })
    if analysis.get('analysis_contract') == 'context-engineering-event-normalized-analysis/5.0.0':
        correction = json.loads((RESULTS / 'boundary_correction_summary.json').read_text(encoding='utf-8'))
        boundary_fields = ['old_source_rows', 'old_claude_rows', 'normalized_events',
                           'resolved_events', 'quarantined_events', 'representation_reduction',
                           'absorbed_nonprimary_components', 'total_alias_to_primary_component_reduction']
        groups = [
            ('normalization', {key: correction['normalization'][key] for key in boundary_fields},
             'same frozen source universe; primary-boundary correction', 'Computational event accounting, not human accuracy'),
            ('absorbed_nonprimary_kinds', correction['normalization']['absorbed_nonprimary_kinds'],
             'supported nonprimary boundaries', 'Work and original aliases remain attached to the supported primary owner'),
            ('review46', correction['review46'], 'historical event-v3 author-check rejoin',
             'Historical case-level counts; no inferred transfer of confirmation to changed event-v5 classifications'),
            ('full_primary_overlap', correction['full_primary_overlap'], 'historical to current primary overlap',
             'Distinguish historical event memberships from distinct current events; balancing can change membership'),
            ('historical_evidence_all138', correction['historical_evidence_overlap']['all138'],
             'historical operational evidence rejoin', 'Operational evidence, not a representative classifier reference study'),
        ]
        for prefix, values, scope_label, notes in groups:
            for key, value in values.items():
                # Publish only the scalar aggregate counts in these allowlisted
                # sections. Detailed joins and nested private records are never
                # inputs to this public catalog builder.
                if type(value) is not int:
                    continue
                rows.append({'item_id': f'FRAME-{len(rows)+1:02d}', 'scope': scope_label,
                             'measure': f'{prefix}.{key}', 'value': value, 'unit': 'count',
                             'source_file': 'analysis/results/boundary_correction_summary.json', 'notes': notes})
        action_reference = json.loads((RESULTS / 'action_reference_correction_summary.json').read_text(encoding='utf-8'))
        action_groups = [
            ('invariants', {key: action_reference[key] for key in
                            ('unchanged_native_event_identities', 'native_invariant_checks')},
             'event-v4 to event-v5 native identity accounting'),
            ('status_transitions', action_reference['status_transitions'],
             'event-v4 to event-v5 automated disposition'),
            ('measurement_changes', action_reference['measurement_changes'],
             'event-v4 to event-v5 rule-derived changes'),
            ('fixed_v4_selection_exposure', action_reference['fixed_v4_selection_exposure'],
             'changed measurements within fixed historical event-v4 selections'),
            ('sample_membership', action_reference['sample_membership'],
             'event-v4 to event-v5 balanced membership'),
            ('source_accounting', action_reference['source_accounting'],
             'contributing alias sources versus canonical resolved sources'),
            ('unchanged_tool_names_resolved_occurrence_counts',
             action_reference['unchanged_tool_names_resolved_occurrence_counts'],
             'resolved occurrences of unchanged administrative-tool candidates'),
            ('phrase_overlap_exposure.counts', action_reference['phrase_overlap_exposure']['counts'],
             'literal context-package phrase exposure, not semantic stage adjudication'),
        ]
        for prefix, values, scope_label in action_groups:
            for key, value in sorted(values.items()):
                nested = prefix in {'fixed_v4_selection_exposure', 'sample_membership',
                                    'source_accounting', 'unchanged_tool_names_resolved_occurrence_counts',
                                    'phrase_overlap_exposure.counts'}
                if nested != isinstance(value, dict):
                    raise ValueError(f'Non-count correction catalog field: {prefix}.{key}')
                counts = sorted(value.items()) if nested else [('', value)]
                for subkey, count in counts:
                    if type(count) is not int or count < 0:
                        raise ValueError(f'Non-count correction catalog field: {prefix}.{key}.{subkey}')
                    measure = '.'.join(part for part in (prefix, key, subkey) if part)
                    notes = 'Computational correction accounting; no new human judgments or independent accuracy estimate'
                    if prefix == 'measurement_changes':
                        notes = 'All normalized native components, including resolved and held events; not only the resolved analysis input'
                    elif prefix == 'fixed_v4_selection_exposure':
                        notes = 'Fixed historical v4 subset named in the measure; resolved subset excludes held components'
                        if key == 'route_or_status_changed':
                            notes += '; changes in analysis.cohort() eligibility/condition or resolved/held status, not bare automated_disposition'
                    rows.append({'item_id': f'FRAME-{len(rows)+1:02d}', 'scope': scope_label,
                                 'measure': measure, 'value': count, 'unit': 'count',
                                 'source_file': 'analysis/results/action_reference_correction_summary.json',
                                 'notes': notes})
    return rows


def infer_type(values: list[str], field: str) -> str:
    if field in FIELD_DEFINITIONS:
        return FIELD_DEFINITIONS[field][0]
    nonblank = [value for value in values if value != ""]
    if nonblank and all(value.lstrip("-").isdigit() for value in nonblank):
        return "integer"
    try:
        for value in nonblank:
            float(value)
    except ValueError:
        return "string"
    return "number" if nonblank else "string"


def build_dictionary() -> list[dict[str, object]]:
    paths = sorted((RESULTS).glob("*.csv")) + sorted(CATALOG.glob("*.csv")) + sorted(PROVENANCE.glob("*.csv"))
    paths = [path for path in paths if path.name != "data_dictionary.csv"]
    rows: list[dict[str, object]] = []
    for path in paths:
        records = read_csv(path)
        with path.open(newline="", encoding="utf-8") as handle:
            fields = next(csv.reader(handle))
        relative = path.relative_to(ROOT).as_posix()
        for field in fields:
            values = [row.get(field, "") for row in records]
            dtype = infer_type(values, field)
            definition = FIELD_DEFINITIONS.get(field, (dtype, field.replace("_", " ").capitalize() + "."))[1]
            rows.append({
                "artifact": relative, "field": field, "data_type": dtype,
                "definition": definition, "unit": "proportion" if dtype == "proportion" else "",
                "nullable": "yes" if any(value == "" for value in values) else "no",
                "disclosure_class": "public_aggregate_or_metadata",
            })
    return rows


def main() -> None:
    catalog_rows = build_catalog()
    write_csv(CATALOG / "aggregate_catalog.csv", CATALOG_FIELDS, catalog_rows)
    write_csv(
        CATALOG / "source_frame_summary.csv",
        ["item_id", "scope", "measure", "value", "unit", "source_file", "notes"],
        build_source_frame(),
    )
    dictionary_rows = build_dictionary()
    write_csv(
        CATALOG / "data_dictionary.csv",
        ["artifact", "field", "data_type", "definition", "unit", "nullable", "disclosure_class"],
        dictionary_rows,
    )
    print(f"Built {len(catalog_rows)} aggregate catalog rows and {len(dictionary_rows)} dictionary rows.")


if __name__ == "__main__":
    main()

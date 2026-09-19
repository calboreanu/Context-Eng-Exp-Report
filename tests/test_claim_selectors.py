"""Executable claim-map contracts, using public aggregates and fictional fixtures only."""

from __future__ import annotations

import copy
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('claim_verifier', ROOT / 'scripts/verify_public_release.py')
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class ClaimSelectorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ce-fictional-selectors-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'example.csv').write_text(
            'group,metric,value\nA,x,0\nA,y,2\nB,x,3\nB,y,4\n', encoding='utf-8')
        (self.root / 'example.json').write_text(json.dumps({
            'scope': {'count': 0, 'diagnostic_only': False},
            'summaries': [{'group': 'A', 'value': 1}, {'group': 'B', 'value': 2}],
        }), encoding='utf-8')
        (self.root / 'example.md').write_text(
            '# Example\n\n## Boundary\nThese checks do not establish causality.\n'
            '\n## Other\nOther text.\n', encoding='utf-8')
        self.csv_target = {'file': 'example.csv', 'kind': 'csv',
                           'where': {'group': 'A'}, 'fields': ['metric', 'value'],
                           'expected_records': 2}
        self.section_target = {'file': 'example.md', 'kind': 'markdown_section',
                               'section': 'Boundary', 'required_text': ['do not establish causality'],
                               'expected_records': 1}

    def resolve(self, target):
        return VERIFIER.resolve_claim_target(target, self.root)

    def test_all_twelve_public_claims_resolve(self):
        claims = {item['claim_id']: item['targets'] for item in VERIFIER.verify_claims()}
        self.assertEqual(set(claims), {f'CE-C{i:02d}' for i in range(1, 13)})
        self.assertEqual([item['selected_records'] for item in claims['CE-C01']], [1, 1])
        self.assertEqual(claims['CE-C01'][1]['fields'], ['retained_source_segments'])
        self.assertEqual([item['selected_records'] for item in claims['CE-C09']], [4, 4])

    def test_csv_equality_keeps_zero_values(self):
        self.assertEqual(self.resolve(self.csv_target)['selected_records'], 2)

    def test_membership_is_or_and_different_fields_are_and(self):
        target = copy.deepcopy(self.csv_target)
        target['where'] = {'group': ['A', 'B'], 'metric': 'x'}
        self.assertEqual(self.resolve(target)['selected_records'], 2)

    def test_json_object_keeps_zero_and_false(self):
        target = {'file': 'example.json', 'kind': 'json', 'path': ['scope'],
                  'fields': ['count', 'diagnostic_only'], 'expected_records': 1}
        self.assertEqual(self.resolve(target)['selected_records'], 1)

    def test_json_array_filter(self):
        target = {'file': 'example.json', 'kind': 'json', 'path': ['summaries'],
                  'where': {'group': 'B'}, 'fields': ['value'], 'expected_records': 1}
        self.assertEqual(self.resolve(target)['selected_records'], 1)

    def test_no_matching_record_is_rejected(self):
        self.csv_target['where'] = {'group': 'missing'}
        with self.assertRaisesRegex(RuntimeError, 'no matches'):
            self.resolve(self.csv_target)

    def test_missing_filter_field_is_rejected(self):
        self.csv_target['where'] = {'missing': 'A'}
        with self.assertRaisesRegex(RuntimeError, 'filter field missing'):
            self.resolve(self.csv_target)

    def test_missing_required_field_is_rejected(self):
        self.csv_target['fields'].append('missing')
        with self.assertRaisesRegex(RuntimeError, 'missing or empty'):
            self.resolve(self.csv_target)

    def test_empty_required_value_is_rejected(self):
        (self.root / 'example.csv').write_text('group,metric,value\nA,x,\nA,y,2\n', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'missing or empty'):
            self.resolve(self.csv_target)

    def test_whitespace_only_csv_required_value_is_rejected(self):
        (self.root / 'example.csv').write_text('group,metric,value\nA,x, \t \nA,y,2\n', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'missing or empty'):
            self.resolve(self.csv_target)

    def test_whitespace_only_json_required_value_is_rejected(self):
        (self.root / 'example.json').write_text(json.dumps({'value': ' \t\n '}), encoding='utf-8')
        target = {'file': 'example.json', 'kind': 'json',
                  'fields': ['value'], 'expected_records': 1}
        with self.assertRaisesRegex(RuntimeError, 'missing or empty'):
            self.resolve(target)

    def test_duplicate_csv_headers_are_rejected(self):
        (self.root / 'example.csv').write_text(
            'group,metric,value,value\nA,x,unintended,0\nA,y,unintended,2\n', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'duplicate CSV header'):
            self.resolve(self.csv_target)

    def test_empty_csv_headers_are_rejected(self):
        for content in ('', 'group,metric,value,\nA,x,0,unused\nA,y,2,unused\n',
                        'group,metric,value, \t \nA,x,0,unused\nA,y,2,unused\n'):
            with self.subTest(content=content):
                (self.root / 'example.csv').write_text(content, encoding='utf-8')
                with self.assertRaisesRegex(RuntimeError, 'CSV headers must be nonempty'):
                    self.resolve(self.csv_target)

    def test_wrong_expected_count_is_rejected(self):
        self.csv_target['expected_records'] = 1
        with self.assertRaisesRegex(RuntimeError, 'selected 2 records, expected 1'):
            self.resolve(self.csv_target)

    def test_boolean_expected_count_is_rejected(self):
        self.csv_target['expected_records'] = True
        with self.assertRaisesRegex(RuntimeError, 'positive integer'):
            self.resolve(self.csv_target)

    def test_empty_membership_is_rejected(self):
        self.csv_target['where'] = {'group': []}
        with self.assertRaisesRegex(RuntimeError, 'nonempty scalar choices'):
            self.resolve(self.csv_target)

    def test_nested_filter_is_rejected(self):
        self.csv_target['where'] = {'group': {'expression': 'A'}}
        with self.assertRaisesRegex(RuntimeError, 'nonempty scalar choices'):
            self.resolve(self.csv_target)

    def test_missing_json_path_is_rejected(self):
        target = {'file': 'example.json', 'kind': 'json', 'path': ['missing'],
                  'fields': ['count'], 'expected_records': 1}
        with self.assertRaisesRegex(RuntimeError, 'JSON path key not found'):
            self.resolve(target)

    def test_duplicate_json_keys_are_rejected(self):
        (self.root / 'example.json').write_text('{"count": 1, "count": 2}', encoding='utf-8')
        target = {'file': 'example.json', 'kind': 'json', 'fields': ['count'], 'expected_records': 1}
        with self.assertRaisesRegex(RuntimeError, 'duplicate JSON key'):
            self.resolve(target)

    def test_non_public_paths_are_rejected(self):
        for path in ('../example.csv', str(self.root / 'example.csv')):
            with self.subTest(path=path):
                target = dict(self.csv_target, file=path)
                with self.assertRaisesRegex(RuntimeError, 'relative public path'):
                    self.resolve(target)

    def test_unsupported_kind_is_rejected(self):
        self.csv_target['kind'] = 'expression'
        with self.assertRaisesRegex(RuntimeError, 'unsupported selector kind'):
            self.resolve(self.csv_target)

    def test_duplicate_required_fields_are_rejected(self):
        self.csv_target['fields'] = ['value', 'value']
        with self.assertRaisesRegex(RuntimeError, 'nonempty unique list'):
            self.resolve(self.csv_target)

    def test_unknown_selector_property_is_rejected(self):
        self.csv_target['evaluate'] = 'not permitted'
        with self.assertRaisesRegex(RuntimeError, 'unknown claim-selector property'):
            self.resolve(self.csv_target)

    def test_markdown_section_and_phrase_resolve(self):
        self.assertEqual(self.resolve(self.section_target)['selected_records'], 1)

    def test_missing_or_duplicate_markdown_section_is_rejected(self):
        for content in ('## Wrong\nNo boundary.\n',
                        '## Boundary\ndo not establish causality\n## Boundary\nsame\n'):
            with self.subTest(content=content):
                (self.root / 'example.md').write_text(content, encoding='utf-8')
                with self.assertRaisesRegex(RuntimeError, 'expected one exact section'):
                    self.resolve(self.section_target)

    def test_phrase_in_another_section_does_not_count(self):
        (self.root / 'example.md').write_text(
            '## Boundary\nUnrelated.\n## Other\ndo not establish causality\n', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'interpretation phrase missing'):
            self.resolve(self.section_target)

    def prepare_claim_map(self):
        """Only copy public mapping metadata; data resolution is separately tested above."""
        destination = self.root / 'data/provenance'
        destination.mkdir(parents=True)
        source = ROOT / 'data/provenance'
        (destination / 'claim_selectors.json').write_bytes((source / 'claim_selectors.json').read_bytes())
        with (source / 'claim_to_evidence.csv').open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            fieldnames, rows = reader.fieldnames, list(reader)
        # Generator files need only exist for these mapping-drift tests.
        for row in rows:
            if row['generator'].endswith('.py'):
                generator = self.root / row['generator']
                generator.parent.mkdir(parents=True, exist_ok=True)
                generator.touch()
        return destination, fieldnames, rows

    def assert_map_rejected(self, change, message):
        destination, fieldnames, rows = self.prepare_claim_map()
        change(rows)
        with (destination / 'claim_to_evidence.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        with patch.object(VERIFIER, 'resolve_claim_target', return_value={'selected_records': 1}):
            with self.assertRaisesRegex(RuntimeError, message):
                VERIFIER.verify_claims(self.root)

    def test_readable_selector_drift_is_rejected(self):
        self.assert_map_rejected(lambda rows: rows[0].update(record_selector='stale prose'),
                                 'readable selector differs')

    def test_evidence_file_drift_is_rejected(self):
        self.assert_map_rejected(lambda rows: rows[0].update(evidence_file='wrong.json'),
                                 'evidence-file list differs')

    def test_missing_claim_is_rejected(self):
        self.assert_map_rejected(lambda rows: rows.pop(), 'each of CE-C01')

    def test_duplicate_claim_id_is_rejected(self):
        self.assert_map_rejected(lambda rows: rows[0].update(claim_id=rows[1]['claim_id']),
                                 'each of CE-C01')


if __name__ == '__main__':
    unittest.main()

"""Fictional native-record fixtures: no production prompts or human labels."""
import copy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ANALYSIS = ROOT / 'analysis' if (ROOT / 'analysis').is_dir() else ROOT
SCRIPTS = ANALYSIS / 'upstream_contract/scripts'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


engine = module('independent_event_engine', SCRIPTS / 'event_normalization.py')
screen = module('independent_screen', SCRIPTS / 'postrun-context-screen.py')
RULES = json.loads((ANALYSIS / 'upstream_contract/config/context-engineering-eligibility.json').read_text())


def user(uid, text='Implement the requested feature.', replay=False, parent=None, owner=None, second=0, session='session-a'):
    r = {'type': 'user', 'uuid': uid, 'timestamp': f'2026-01-01T00:00:{second:02d}.000Z',
         'sessionId': session, 'message': {'role': 'user', 'content': [{'type': 'text', 'text': text}]}}
    if replay:
        r['isReplay'] = True
    if parent is not None:
        r['parentUuid'] = parent
    if owner is not None:
        r['parent_tool_use_id'] = owner
    return r


def call(uid, cid, name='Write', value='first', parent=None, owner=None, second=1):
    r = {'type': 'assistant', 'uuid': uid, 'timestamp': f'2026-01-01T00:00:{second:02d}.000Z',
         'sessionId': 'session-a', 'message': {'role': 'assistant', 'content': [
             {'type': 'tool_use', 'id': cid, 'name': name, 'input': {'file_path': '/fictional/feature.py', 'content': value}}]}}
    if parent is not None:
        r['parentUuid'] = parent
    if owner is not None:
        r['parent_tool_use_id'] = owner
    return r


def result(uid, cid, parent=None, owner=None, second=2, error=False):
    r = {'type': 'user', 'uuid': uid, 'timestamp': f'2026-01-01T00:00:{second:02d}.000Z',
         'sessionId': 'session-a', 'message': {'role': 'user', 'content': [
             {'type': 'tool_result', 'tool_use_id': cid, 'is_error': error, 'content': 'fictional result'}]}}
    if parent is not None:
        r['parentUuid'] = parent
    if owner is not None:
        r['parent_tool_use_id'] = owner
    return r


def fixture(raw, ref='S1', provider='claude_audit'):
    source = {'station_id': 'ST-FICTION', 'source_ref': ref, 'provider': provider,
              'path': '/fictional/not-read.jsonl', 'sha256': '0' * 64, 'bytes': 0}
    records, anchors, rows = [], [], {}
    active = ''
    for n, original in enumerate(raw, 1):
        r = engine.compact_record(original, source, n, screen)
        prompt = screen.extract_human_prompt(original, provider, RULES['nonhuman_block_prefixes'])
        if prompt:
            active = f'OLD-{ref}-{n}'
            r['accepted_episode_id'] = active
            anchors.append({'old_episode_id': active, 'anchor': r,
                            'prompt_sha256': engine.sha(prompt[0]), 'attachment_count': prompt[1]})
            rows[active] = {'episode_id': active, 'prompt_text': prompt[0], 'attachment_count': str(prompt[1]),
                            'candidate_case_ids': '', 'rule_version': 'fictional-v2', 'station_id': source['station_id'],
                            'provider': provider, 'source_ref': ref, 'source_line_start': str(n),
                            'source_line_end': str(n), 'turn_index': str(len(anchors)), 'session_ref': 'old-session'}
        r['old_interval'] = active
        records.append(r)
    return {'source': source, 'records': records, 'anchors': anchors}, rows


def normalize(*fixtures):
    sources, rows = [], {}
    for s, r in fixtures:
        sources.append(copy.deepcopy(s))
        rows.update(copy.deepcopy(r))
    return engine.normalize_sources(sources, rows, screen, RULES)


def event_for(output, old):
    eid = next(a['event_id'] for a in output['aliases'] if a['old_episode_id'] == old)
    return next(e for e in output['events'] if e['row']['episode_id'] == eid)


class NormalizationAdversarialTests(unittest.TestCase):
    def test_same_words_different_ids_remain_separate(self):
        out = normalize(fixture([user('u1'), user('u2', second=3)]))
        self.assertEqual(out['counts']['normalized_events'], 2)

    def test_submillisecond_distinct_native_events_do_not_merge(self):
        a, b = user('u1'), user('u1')
        a['timestamp'] = '2026-01-01T00:00:00.000001Z'
        b['timestamp'] = '2026-01-01T00:00:00.000002Z'
        out = normalize(fixture([a], 'S1', 'claude_home'), fixture([b], 'S2', 'claude_home'))
        self.assertEqual(out['counts']['normalized_events'], 2)
        self.assertEqual({e['row']['timestamp_start_utc'] for e in out['events']}, {a['timestamp'], b['timestamp']})

    def test_missing_time_user_bridge_requires_exact_direct_response(self):
        original = user('u1', session='transport-session'); original.pop('timestamp')
        original['_audit_timestamp'] = '2026-01-01T00:00:00.000Z'
        audit_call = call('a1', 'c1')
        native_call = call('a1', 'c1', parent='u1')
        out = normalize(fixture([original, audit_call], 'S1', 'claude_audit'),
                        fixture([user('u1'), native_call], 'S2', 'claude_embedded'))
        self.assertEqual(len(out['events']), 1)
        self.assertEqual(out['events'][0]['row']['tool_calls'], '1')
        self.assertTrue(any(e['kind'] == 'same_native_user_missing_time_shared_direct_response' for e in out['identity_edges']))

    def test_missing_time_bridge_negative_guards(self):
        for change in ['different_user', 'different_prompt', 'supplied_conflicting_timestamp', 'different_response', 'not_direct_parent']:
            with self.subTest(change=change):
                original = user('u1', session='transport-session'); original.pop('timestamp')
                original['_audit_timestamp'] = '2026-01-01T00:00:00.000Z'
                native_user = user('u1')
                native_call = call('a1', 'c1', parent='u1')
                if change == 'different_user': native_user['uuid'] = 'other'; native_call['parentUuid'] = 'other'
                if change == 'different_prompt': native_user['message']['content'][0]['text'] = 'A genuinely distinct task.'
                if change == 'supplied_conflicting_timestamp': original['timestamp'] = '2026-01-01T00:00:10.000Z'
                if change == 'different_response': native_call['message']['content'][0]['input']['content'] = 'different-response-input'
                if change == 'not_direct_parent': native_call['parentUuid'] = 'missing-connector'
                out = normalize(fixture([original, call('a1', 'c1')], 'S1', 'claude_audit'),
                                fixture([native_user, native_call], 'S2', 'claude_embedded'))
                self.assertEqual(len(out['events']), 2)
                self.assertFalse(any(e['kind'] == 'same_native_user_missing_time_shared_direct_response' for e in out['identity_edges']))

    def test_missing_time_bridge_refuses_ambiguous_native_timestamps(self):
        original = user('u1', session='transport-session'); original.pop('timestamp')
        original['_audit_timestamp'] = '2026-01-01T00:00:00.000Z'
        out = normalize(fixture([original, call('a1', 'c1', second=3)], 'S1', 'claude_audit'),
                        fixture([user('u1', second=0), call('a1', 'c1', parent='u1', second=3)], 'S2', 'claude_embedded'),
                        fixture([user('u1', second=1), call('a1', 'c1', parent='u1', second=3)], 'S3', 'claude_embedded'))
        self.assertEqual(len(out['events']), 3)

    def test_replay_variant_uses_original_not_richer_text(self):
        out = normalize(fixture([user('u1', text='Make the file.'),
                                 user('u1', text='Use supplied context /uploads/spec.md and make the file.', replay=True, second=1)]))
        self.assertEqual(len(out['events']), 1)
        self.assertEqual(out['events'][0]['row']['prompt_text'], 'Make the file.')
        self.assertIn('replay_prompt_variant_preserved', out['events'][0]['proof']['flags'])

    def test_exact_embedded_replay_copy_is_not_a_second_conflicting_original(self):
        original = user('u1', text='Implement from local-spec.md.')
        replay = user('u1', text='Implement from /uploads/local-spec.md.', replay=True, second=1)
        mirror = copy.deepcopy(replay); mirror.pop('isReplay')
        out = normalize(fixture([original, replay], 'S1', 'claude_audit'), fixture([mirror], 'S2', 'claude_embedded'))
        self.assertEqual(len(out['events']), 1)
        self.assertEqual(out['events'][0]['status'], 'resolved')
        self.assertEqual(out['events'][0]['row']['prompt_text'], original['message']['content'][0]['text'])

    def test_two_conflicting_originals_plus_replay_are_quarantined(self):
        out = normalize(fixture([user('u1', text='One task.'), user('u1', text='Another task.'), user('u1', replay=True)]))
        self.assertEqual(out['events'][0]['status'], 'quarantined')

    def test_missing_parent_uuid_in_audit_is_permitted(self):
        out = normalize(fixture([user('u1'), call('a1', 'c1'), result('r1', 'c1')]))
        self.assertEqual(out['events'][0]['status'], 'resolved')
        self.assertEqual(out['events'][0]['row']['tool_calls'], '1')

    def test_nonconsecutive_replay_does_not_swallow_intervening_work(self):
        out = normalize(fixture([user('u1'), call('a1', 'c1'), user('u2', second=3), call('a2', 'c2', second=4),
                                 user('u1', replay=True, second=0), call('a3', 'c3', second=5)]))
        self.assertEqual([t['native_tool_id'] for t in event_for(out, 'OLD-S1-1')['proof']['tools']], ['c1', 'c3'])
        self.assertEqual([t['native_tool_id'] for t in event_for(out, 'OLD-S1-3')['proof']['tools']], ['c2'])

    def test_original_and_replay_work_both_conserved(self):
        out = normalize(fixture([user('u1'), call('a1', 'c1'), result('r1', 'c1'),
                                 user('u1', replay=True), call('a2', 'c2', second=3), result('r2', 'c2', second=4)]))
        self.assertEqual(out['events'][0]['row']['tool_calls'], '2')
        self.assertTrue(all(t['completed'] for t in out['events'][0]['proof']['tools']))

    def test_snapshot_duplicates_count_once(self):
        raw = [user('u1'), call('a1', 'c1', parent='u1'), result('r1', 'c1', parent='a1')]
        out = normalize(fixture(raw, 'S1', 'claude_home'), fixture(raw, 'S2', 'claude_home'))
        self.assertEqual(len(out['events']), 1)
        self.assertEqual(out['events'][0]['row']['tool_calls'], '1')

    def test_snapshot_prefix_extension_is_preserved(self):
        short = [user('u1'), call('a1', 'c1', parent='u1'), result('r1', 'c1', parent='a1')]
        long = short + [call('a2', 'c2', parent='r1', second=3), result('r2', 'c2', parent='a2', second=4)]
        out = normalize(fixture(short, 'S1', 'claude_home'), fixture(long, 'S2', 'claude_home'))
        self.assertEqual(out['events'][0]['row']['tool_calls'], '2')
        self.assertEqual(out['events'][0]['status'], 'resolved')

    def test_conflicting_call_payload_is_quarantined(self):
        a = [user('u1'), call('a1', 'c1', value='one', parent='u1')]
        b = [user('u1'), call('a1', 'c1', value='two', parent='u1')]
        out = normalize(fixture(a, 'S1', 'claude_home'), fixture(b, 'S2', 'claude_home'))
        self.assertIn('conflicting_native_tool_call_payload', out['events'][0]['reasons'])

    def test_corroborated_audit_embedded_input_variants_preserve_invariant_measurements(self):
        a = [user('u1'), call('same-native-assistant', 'same-native-call', value='captured-value-one')]
        b = [user('u1'), call('same-native-assistant', 'same-native-call', value='captured-value-two', parent='u1')]
        out = normalize(fixture(a, 'S1', 'claude_audit'), fixture(b, 'S2', 'claude_embedded'))
        self.assertEqual(out['events'][0]['status'], 'resolved')
        self.assertEqual(out['events'][0]['row']['tool_calls'], '1')
        self.assertEqual(len(out['events'][0]['proof']['tools'][0]['call_payload_hashes']), 2)

    def test_changed_assistant_prose_is_not_a_transport_payload_exception(self):
        a = call('same-native-assistant', 'c1')
        b = call('same-native-assistant', 'c1', parent='u1')
        a['message']['content'].append({'type': 'text', 'text': 'first text'})
        b['message']['content'].append({'type': 'text', 'text': 'other text'})
        out = normalize(fixture([user('u1'), a], 'S1', 'claude_audit'), fixture([user('u1'), b], 'S2', 'claude_embedded'))
        self.assertEqual(out['events'][0]['status'], 'quarantined')

    def test_native_embedded_input_priority_is_not_success_clock_or_arrival_priority(self):
        for error in [False, True]:
            for reverse in [False, True]:
                with self.subTest(error=error, reverse=reverse):
                    audit = call('a1', 'c1', name='Bash', second=1)
                    audit['message']['content'][0]['input'] = {'command': 'cd /fictional/host/Library/Application Support/Claude/local-agent-mode-sessions/A/B/local_C/outputs && ls'}
                    native = call('a1', 'c1', name='Bash', parent='u1', second=4)
                    native['message']['content'][0]['input'] = {'command': 'cd /sessions/quiet-otter/mnt/outputs && ls'}
                    a = fixture([user('u1'), audit, result('r1', 'c1', second=5, error=error)], 'AAA', 'claude_audit')
                    b = fixture([user('u1'), native, result('r1', 'c1', parent='a1', second=5, error=error)], 'ZZZ', 'claude_embedded')
                    out = normalize(*([b, a] if reverse else [a, b]))
                    e = out['events'][0]; trace = json.loads(e['row']['tool_trace_json'])
                    self.assertEqual(e['status'], 'resolved')
                    self.assertEqual(trace[0]['class'], 'retrieve')
                    self.assertEqual(trace[0]['succeeded'], not error)
                    self.assertEqual(e['proof']['tools'][0]['canonical_call_record'], 'ZZZ:2')
                    self.assertEqual(e['proof']['tools'][0]['canonical_input_basis'], 'unique_native_parent_linked_embedded_input')
                    self.assertIn('literal_tool_class_capture_variants_preserved', e['proof']['flags'])
                    self.assertEqual({v['class'] for v in e['proof']['tools'][0]['call_capture_variants']}, {'execute', 'retrieve'})

    def test_conflicting_embedded_inputs_remain_held(self):
        a = fixture([user('u1'), call('a1', 'c1', value='audit')], 'S1', 'claude_audit')
        b = fixture([user('u1'), call('a1', 'c1', value='native-one', parent='u1')], 'S2', 'claude_embedded')
        c = fixture([user('u1'), call('a1', 'c1', value='native-two', parent='u1')], 'S3', 'claude_embedded')
        out = normalize(a, b, c)
        self.assertEqual(out['events'][0]['status'], 'quarantined')
        self.assertIn('conflicting_native_tool_call_payload', out['events'][0]['reasons'])

    def test_conflicting_result_status_is_quarantined(self):
        a = [user('u1'), call('a1', 'c1', parent='u1'), result('r1', 'c1', parent='a1')]
        b = [user('u1'), call('a1', 'c1', parent='u1'), result('r1', 'c1', parent='a1', error=True)]
        out = normalize(fixture(a, 'S1', 'claude_home'), fixture(b, 'S2', 'claude_home'))
        self.assertIn('conflicting_native_tool_result_status', out['events'][0]['reasons'])

    def test_later_terminal_update_follows_time_not_success(self):
        for first_error, last_error in [(True, False), (False, True)]:
            with self.subTest(first_error=first_error, last_error=last_error):
                raw = [user('u1'), call('a1', 'c1'), result('r1', 'c1', second=2, error=first_error),
                       result('r2', 'c1', second=3, error=last_error)]
                out = normalize(fixture(raw))
                self.assertEqual(out['events'][0]['status'], 'resolved')
                self.assertEqual(out['events'][0]['proof']['tools'][0]['succeeded'], not last_error)
                self.assertIn('chronological_native_tool_status_update', out['events'][0]['proof']['flags'])

    def test_delayed_result_routes_to_call_owner(self):
        out = normalize(fixture([user('u1'), call('a1', 'c1'), user('u2', second=3),
                                 call('a2', 'c2', second=4), result('r1', 'c1', second=5)]))
        self.assertTrue(event_for(out, 'OLD-S1-1')['proof']['tools'][0]['completed'])
        self.assertFalse(event_for(out, 'OLD-S1-3')['proof']['tools'][0]['completed'])

    def test_exact_native_parent_chain_overrides_weaker_interleaved_audit_segment(self):
        native = call('a1', 'c1', parent='u1', second=5)
        native['message']['stop_reason'] = 'tool_use'
        audit = call('a1', 'c1', second=5)
        audit['message']['stop_reason'] = None
        out = normalize(fixture([user('u1'), user('u2', second=3), audit], 'S1', 'claude_audit'),
                        fixture([user('u1'), native], 'S2', 'claude_embedded'))
        self.assertEqual(len(out['events']), 2)
        self.assertEqual(event_for(out, 'OLD-S1-1')['row']['tool_calls'], '1')
        self.assertEqual(event_for(out, 'OLD-S1-2')['row']['tool_calls'], '0')
        self.assertTrue(all(e['status'] == 'resolved' for e in out['events']))

    def test_stale_duplicate_result_does_not_pollute_current_endpoint(self):
        stale = result('r1', 'c1', parent='a1', second=2)
        raw = [user('u1'), call('a1', 'c1', parent='u1'), stale, user('u2', second=10),
               call('a2', 'c2', parent='u2', second=11), result('r2', 'c2', parent='a2', second=12), stale]
        out = normalize(fixture(raw, provider='claude_home'))
        self.assertEqual(event_for(out, 'OLD-S1-4')['proof']['timing']['duration_seconds'], 2)
        self.assertEqual(len(event_for(out, 'OLD-S1-4')['proof']['tools']), 1)

    def test_incomparable_snapshot_branches_do_not_invent_order(self):
        # Same root, but neither branch contains the other. A stable sorting
        # tie-breaker cannot establish whether reading preceded acting.
        prompt = 'Use requirements.md and design.md to implement the feature.'
        a = [user('u1', text=prompt), call('read-branch', 'c-read', name='Read', parent='u1', second=1),
             result('read-result', 'c-read', parent='read-branch', second=2)]
        b = [user('u1', text=prompt), call('write-branch', 'c-write', name='Write', parent='u1', second=1),
             result('write-result', 'c-write', parent='write-branch', second=2)]
        out = normalize(fixture(a, 'S1', 'claude_home'), fixture(b, 'S2', 'claude_home'))
        self.assertEqual(out['events'][0]['status'], 'quarantined')

    def test_disjoint_same_class_work_need_not_be_quarantined(self):
        a = [user('u1'), call('branch-a', 'c-a', name='Write', parent='u1', second=1)]
        b = [user('u1'), call('branch-b', 'c-b', name='Write', parent='u1', second=1)]
        out = normalize(fixture(a, 'S1', 'claude_home'), fixture(b, 'S2', 'claude_home'))
        self.assertEqual(out['events'][0]['row']['tool_calls'], '2')
        self.assertEqual(out['events'][0]['status'], 'resolved')

    def test_optional_retrieval_order_does_not_quarantine_invariant_ce_qualification(self):
        prompt = 'Use requirements.md and design.md to implement the feature.'
        common = [user('u1', text=prompt), call('definite-read', 'c-definite', name='Read', parent='u1', second=1),
                  result('definite-result', 'c-definite', parent='definite-read', second=2)]
        a = common + [call('write-branch', 'c-write', name='Write', parent='definite-result', second=3),
                      result('write-result', 'c-write', parent='write-branch', second=4)]
        b = common + [call('optional-read', 'c-optional', name='Read', parent='definite-result', second=3),
                      result('optional-result', 'c-optional', parent='optional-read', second=4)]
        out = normalize(fixture(a, 'S1', 'claude_home'), fixture(b, 'S2', 'claude_home'))
        self.assertEqual(out['events'][0]['row']['context_trace_status'], 'context_supplied_then_product_action_observed')
        self.assertEqual(out['events'][0]['status'], 'resolved')

    def test_missing_timing_is_not_zero_duration(self):
        raw = [user('u1'), call('a1', 'c1')]
        raw[1].pop('timestamp')
        out = normalize(fixture(raw))
        self.assertIsNone(out['events'][0]['proof']['timing']['duration_seconds'])

    def test_exact_native_agent_child_is_machine_origin(self):
        raw = [user('outer'), call('delegate', 'child-owner', name='Agent'),
               user('child', text='Implement the delegated feature.', owner='child-owner', second=2),
               call('child-action', 'child-call', owner='child-owner', second=3),
               result('child-result', 'child-call', owner='child-owner', second=4)]
        out = normalize(fixture(raw))
        child = event_for(out, 'OLD-S1-3')
        self.assertEqual(child['row']['origin_candidate'], 'native_delegated_tool_child')
        self.assertEqual(child['row']['tool_calls'], '1')
        self.assertEqual(len(out['aliases']), 2)

    def test_exact_native_task_child_is_machine_origin_without_taxonomy_change(self):
        raw = [user('outer'), call('delegate', 'child-owner', name='Task'),
               user('child', text='Implement the delegated feature.', owner='child-owner', second=2),
               call('child-action', 'child-call', owner='child-owner', second=3)]
        out = normalize(fixture(raw))
        self.assertEqual(screen.classify_tool('Task', {}), 'other')
        self.assertEqual(event_for(out, 'OLD-S1-3')['row']['origin_candidate'], 'native_delegated_tool_child')

    def test_known_agent_parent_argument_alias_does_not_erase_delegated_origin(self):
        a = [user('outer'), call('delegate', 'child-owner', name='Agent', value='transport-one'),
             user('child', owner='child-owner', second=2), call('child-action', 'child-call', owner='child-owner', second=3)]
        b = [user('outer'), call('delegate', 'child-owner', name='Agent', value='transport-two', parent='outer')]
        out = normalize(fixture(a, 'S1', 'claude_audit'), fixture(b, 'S2', 'claude_embedded'))
        self.assertEqual(event_for(out, 'OLD-S1-3')['row']['origin_candidate'], 'native_delegated_tool_child')

    def test_unresolved_owner_pointer_is_flagged_and_not_direct_user_origin(self):
        out = normalize(fixture([user('child', owner='missing-owner'),
                                 call('child-action', 'child-call', owner='missing-owner')]))
        self.assertEqual(out['events'][0]['row']['origin_candidate'], 'native_nested_owner_unresolved')
        self.assertIn('unresolved_native_nested_owner', out['events'][0]['proof']['flags'])

    def test_child_user_does_not_reset_outer_owner_segment(self):
        raw = [user('outer'), call('delegate', 'child-owner', name='Agent'),
               user('child', owner='child-owner', second=2),
               call('child-action', 'child-call', owner='child-owner', second=3),
               call('outer-action', 'outer-call', second=4)]
        out = normalize(fixture(raw))
        outer_tools = [x['native_tool_id'] for x in event_for(out, 'OLD-S1-1')['proof']['tools']]
        child_tools = [x['native_tool_id'] for x in event_for(out, 'OLD-S1-3')['proof']['tools']]
        self.assertEqual(outer_tools, ['child-owner', 'outer-call'])
        self.assertEqual(child_tools, ['child-call'])

    def test_input_permutation_does_not_change_result(self):
        a = fixture([user('u1'), call('a1', 'c1', parent='u1')], 'S1', 'claude_home')
        b = fixture([user('u1'), call('a1', 'c1', parent='u1')], 'S2', 'claude_home')
        one, two = normalize(a, b), normalize(b, a)
        self.assertEqual(one['events'], two['events'])
        self.assertEqual(sorted(one['aliases'], key=lambda a: a['old_episode_id']), sorted(two['aliases'], key=lambda a: a['old_episode_id']))

    def test_portable_cli_relative_sources_all_provider_rescreen_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='synthetic-cli-') as folder:
            base = Path(folder)
            raw = [user('u1'), call('a1', 'c1'), result('r1', 'c1'), user('u1', replay=True)]
            src, old_rows = fixture(raw)
            content = ''.join(json.dumps(r, sort_keys=True) + '\n' for r in raw).encode()
            (base / 'fictional.jsonl').write_bytes(content)
            desc = dict(src['source'])
            desc.update(path='fictional.jsonl', bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
            (base / 'sources.json').write_text(json.dumps({'sources': [desc]}))
            header = screen.PUBLIC_HEADER + ['tool_trace_json', 'prompt_text']
            complete = []
            for old in old_rows.values():
                row = {k: '' for k in header}
                row.update(old)
                row['prompt_ref'] = 'FICTIONAL-PROMPT'
                complete.append(row)
            codex = {k: '' for k in header}
            codex.update(episode_id='OLD-CODEX-UNCHANGED', provider='codex_rollout', station_id='ST-FICTION',
                         prompt_text='Fictional Codex passthrough.', source_ref='FICTIONAL-CODEX', source_line_start='1',
                         source_line_end='1', turn_index='1', prompt_ref='FICTIONAL-CODEX-PROMPT', rule_version='fictional-v2',
                         attachment_count='0', tool_trace_json='[]', session_ref='FICTIONAL-CODEX-SESSION',
                         timestamp_start_utc='2026-01-01T00:00:00Z',timestamp_end_utc='2026-01-01T00:00:00Z',timestamp_status='observed')
            codex_record={'type':'response_item','timestamp':codex['timestamp_start_utc'],
                          'payload':{'type':'message','role':'user','content':[{'type':'input_text','text':codex['prompt_text']}]}}
            codex_bytes=(json.dumps(codex_record)+'\n').encode()
            (base/'codex.jsonl').write_bytes(codex_bytes)
            codex_desc={'source_ref':'FICTIONAL-CODEX','station_id':'ST-FICTION','provider':'codex_rollout',
                        'path':'codex.jsonl','bytes':len(codex_bytes),'sha256':hashlib.sha256(codex_bytes).hexdigest()}
            (base/'sources.json').write_text(json.dumps({'sources':[desc,codex_desc]}))
            complete.append(codex)
            with (base / 'input.csv').open('w', newline='') as f:
                w = csv.DictWriter(f, fieldnames=header, lineterminator='\n'); w.writeheader(); w.writerows(complete)
            args = [sys.executable, '-B', str(SCRIPTS / 'event_normalization.py'), '--input', str(base / 'input.csv'),
                    '--sources', str(base / 'sources.json'), '--rules', str(ANALYSIS / 'upstream_contract/config/context-engineering-eligibility.json'),
                    '--cutoff', str(ANALYSIS / 'upstream_contract/config/study-cutoff.json'), '--out', str(base / 'output')]
            run = subprocess.run(args, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            with (base / 'output/normalized_merged_v5.local.csv').open(newline='') as f:
                got = list(csv.DictReader(f))
            self.assertEqual(len(got), 2)
            fixed_codex=next(r for r in got if r['provider']=='codex_rollout')
            for field in ['episode_id','prompt_text','timestamp_start_utc','timestamp_end_utc','session_ref','tool_trace_json']:
                self.assertEqual(fixed_codex[field],codex[field])
            self.assertNotEqual(fixed_codex['rule_version'],codex['rule_version'])
            original_outputs = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (base / 'output').iterdir()}
            rerun = subprocess.run(args, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(rerun.returncode, 0)
            self.assertEqual(original_outputs, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (base / 'output').iterdir()})
            desc['sha256'] = 'f' * 64
            (base / 'sources.json').write_text(json.dumps({'sources': [desc,codex_desc]}))
            wrong = subprocess.run(args[:-1] + [str(base / 'bad-hash-output')], capture_output=True, text=True, timeout=30)
            self.assertNotEqual(wrong.returncode, 0)
            self.assertFalse(list((base / 'bad-hash-output').glob('*.csv')))


if __name__ == '__main__':
    unittest.main(verbosity=2)

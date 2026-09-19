"""Fictional v4 boundary cases; no private cases or human judgments."""
import copy
import json
import tempfile
from pathlib import Path
import unittest
from test_event_normalization import engine, screen, RULES, user, call, result, fixture, normalize, event_for


def notification(uid='notice', cid='background', parent='r1', second=3, origin=True):
    text = ('<task-notification><task-id>fictional</task-id><tool-use-id>' + cid + '</tool-use-id>'
            '<output-file>/fictional/status.output</output-file><status>completed</status>'
            '<summary>Background process complete</summary></task-notification>')
    r = user(uid, text, parent=parent, second=second)
    if origin:
        r['origin'] = {'kind':'task-notification'}
        r['promptSource'] = 'sdk'
    return r


class BoundaryOwnership(unittest.TestCase):
    def test_notification_work_returns_to_call_owner(self):
        out=normalize(fixture([user('u1'),call('a1','background',parent='u1'),result('r1','background',parent='a1'),
            notification(),call('a2','later',parent='notice',second=4),result('r2','later',parent='a2',second=5)],provider='claude_home'))
        self.assertEqual(len(out['events']),1)
        e=out['events'][0]
        self.assertEqual(e['row']['tool_calls'],'2')
        self.assertEqual(len(out['aliases']),2)
        self.assertEqual(e['row']['prompt_text'],'Implement the requested feature.')
        self.assertEqual(len(e['proof']['boundary_absorptions']),1)

    def test_notification_call_owner_beats_later_unrelated_prompt(self):
        out=normalize(fixture([user('u1'),call('a1','background',parent='u1'),result('r1','background',parent='a1'),
            user('u2','Build a separate artifact.',parent='r1',second=3),
            notification(parent='u2',second=4),call('a2','later',parent='notice',second=5)],provider='claude_home'))
        self.assertEqual(len(out['events']),2)
        self.assertEqual(event_for(out,'OLD-S1-1')['row']['tool_calls'],'2')
        self.assertEqual(event_for(out,'OLD-S1-4')['row']['tool_calls'],'0')

    def test_orphan_notification_is_held(self):
        out=normalize(fixture([notification(parent='missing')],provider='claude_home'))
        self.assertEqual(out['events'][0]['status'],'quarantined')
        self.assertIn('unresolved_nonprimary_boundary_owner',out['events'][0]['reasons'])

    def test_ambiguous_call_owner_is_not_resolved_by_success(self):
        out=normalize(fixture([user('u1'),call('a1','background',parent='u1'),
            user('u2','Build another artifact.',second=3),call('a2','background',parent='u2',second=4),
            notification(parent='a2',second=5)],provider='claude_home'))
        notice=event_for(out,'OLD-S1-5')
        self.assertEqual(notice['status'],'quarantined')
        self.assertEqual(out['boundary_edges'],[])

    def test_generic_acknowledgments_retain_parent_work(self):
        for text in ['Sure!', 'Yes, please.', 'Agreed.', 'Sounds good', 'Please proceed']:
            with self.subTest(text=text):
                out=normalize(fixture([user('u1'),call('a1','c1',parent='u1'),
                    user('ack',text,parent='a1',second=3),call('a2','c2',parent='ack',second=4)],provider='claude_home'))
                self.assertEqual(len(out['events']),1)
                self.assertEqual(out['events'][0]['row']['tool_calls'],'2')

    def test_new_task_after_affirmation_remains_separate(self):
        out=normalize(fixture([user('u1'),user('u2','Sure, now verify the separate module.',second=3)]))
        self.assertEqual(len(out['events']),2)

    def test_unanchored_acknowledgment_is_held(self):
        out=normalize(fixture([user('ack','Certainly.')]))
        self.assertEqual(out['events'][0]['status'],'quarantined')

    def test_explicit_different_session_blocks_adjacency(self):
        first, ack = user('u1'), user('ack','Yes.',second=3)
        first['sessionId'], ack['sessionId'] = 'session-a', 'session-b'
        out=normalize(fixture([first,ack]))
        self.assertEqual(len(out['events']),2)
        self.assertEqual(event_for(out,'OLD-S1-2')['status'],'quarantined')

    def test_new_attachment_blocks_bare_ack_absorption(self):
        for kind in ['image','document']:
            ack=user('ack','Yes.',second=3)
            ack['message']['content'].append({'type':kind,'source':{'type':'base64','data':'fictional'}})
            out=normalize(fixture([user('u1'),ack]))
            self.assertEqual(len(out['events']),2)
            self.assertEqual(event_for(out,'OLD-S1-2')['row']['attachment_count'],'1')
            self.assertNotEqual(event_for(out,'OLD-S1-2')['row']['automated_disposition'],'exclude_continuation_only')

    def test_supplied_but_missing_parent_does_not_use_adjacency(self):
        out=normalize(fixture([user('u1'),user('ack','Yes.',parent='uncaptured',second=3)],provider='claude_home'))
        self.assertEqual(len(out['events']),2)
        self.assertEqual(event_for(out,'OLD-S1-2')['status'],'quarantined')

    def test_publication_purpose_follows_retained_primary_request(self):
        out=normalize(fixture([user('u1','Revise the manuscript for the journal.'),call('a1','c1'),
            user('ack','Go ahead.',second=3),call('a2','c2',second=4)]))
        self.assertEqual(len(out['events']),1)
        self.assertEqual(out['events'][0]['row']['automated_disposition'],'exclude_publication_candidate')


class LexicalSanitation(unittest.TestCase):
    def stages(self,text):
        return set(screen.matched_groups(screen.stage_request_text(text),screen.compile_groups(RULES,'stages'))[0])

    def test_xml_element_syntax_is_not_a_path(self):
        self.assertEqual(screen.artifact_references(notification()['message']['content'][0]['text']),{'/fictional/status.output'})

    def test_actual_supplied_file_paths_survive_xml(self):
        self.assertEqual(screen.artifact_references('<files><file_path>/fictional/one.md</file_path><file_path>/fictional/two.py</file_path></files>'),{'/fictional/one.md','/fictional/two.py'})

    def test_xml_attribute_paths_are_retained(self):
        self.assertEqual(screen.artifact_references('<file path="/fictional/one.md"/> <file path="/fictional/two.md"/>'),{'/fictional/one.md','/fictional/two.md'})

    def test_human_supplied_wrapper_not_inferred_machine_origin(self):
        text=notification()['message']['content'][0]['text']
        self.assertEqual(screen.notification_boundary(text,'human'),{})
        self.assertEqual(screen.notification_boundary(text+'\nNow audit the output.'),{})

    def test_sdk_transport_alone_does_not_imply_machine_origin(self):
        self.assertEqual(screen.notification_boundary('Build the component.',''),{})

    def test_inert_git_message_forms_do_not_request_stages(self):
        for line in ['git tag -a release -m "verified last week"','git commit --message="audit completed"',
                     'git commit -am "audit complete"', 'git tag -am "audit complete" release',
                     'git commit -m"implement and verify later"', 'git commit -am"implement and audit later"',
                     'git -C /fictional tag release -mverified','git commit -m "verify" && git tag -m "audit" release']:
            with self.subTest(line=line):
                self.assertNotIn('verification',self.stages(line))
                self.assertNotIn('audit',self.stages(line))

    def test_genuine_quoted_word_instruction_is_preserved(self):
        self.assertIn('verification',self.stages('Please "verify" the output against its requirements.'))

    def test_actual_fenced_verification_command_is_preserved(self):
        self.assertIn('verification',self.stages('Run:\n```sh\ngit verify-tag release\n```'))

    def test_real_request_outside_inert_argument_survives(self):
        self.assertIn('verification',self.stages('git commit -m "audit complete"\nThen verify the artifact.'))
        self.assertNotIn('audit',self.stages('git commit -m "audit complete"\nThen verify the artifact.'))


class CodexBoundaryCompletion(unittest.TestCase):
    def test_missing_codex_source_cannot_pass_through_unchanged(self):
        with self.assertRaisesRegex(ValueError,'no unchanged-row passthrough'):
            engine.assemble_frames({'events':[],'aliases':[]},[{'episode_id':'fictional','provider':'codex_rollout'}])

    def probe(self, text='Yes.', attachment=False):
        def rec(payload,second):
            return {'type':'response_item','timestamp':f'2026-01-01T00:00:{second:02d}.000Z','payload':payload}
        def prompt(text,second):
            return rec({'type':'message','role':'user','content':[{'type':'input_text','text':text}]},second)
        raw=[prompt('Build the requested feature.',0),
             rec({'type':'function_call','call_id':'original','name':'exec_command','arguments':'{"cmd":"pytest"}'},1),
             rec({'type':'function_call_output','call_id':'original','output':{'exit_code':None,'session_id':17}},2),
             prompt(text,3),
             rec({'type':'function_call','call_id':'poll','name':'write_stdin','arguments':'{"session_id":17,"chars":""}'},4),
             rec({'type':'function_call_output','call_id':'poll','output':{'exit_code':0}},5)]
        if attachment:
            raw[3]['payload']['content'].append({'type':'input_image','image_url':'fictional'})
        _,rows=fixture(raw,provider='codex_rollout')
        active,state=None,None
        for line,record in enumerate(raw,1):
            if screen.extract_human_prompt(record,'codex_rollout',RULES['nonhuman_block_prefixes']):
                active=rows[f'OLD-S1-{line}']
                active.update(timestamp_start_utc=record['timestamp'],timestamp_status='observed',_calls=[])
                state=screen.EpisodeToolState(active['_calls'])
            active.update(source_line_end=str(line),timestamp_end_utc=record['timestamp'])
            state.apply_record(record,'codex_rollout')
            for cid,name,args in screen.extract_tool_calls(record,'codex_rollout'):
                state.add_call(cid,name,args)
        for row in rows.values():
            row['tool_trace_json']=json.dumps(row.pop('_calls'))
        with tempfile.TemporaryDirectory(prefix='ce-fictional-boundary-') as temporary:
            path=Path(temporary)/'source.jsonl'
            data=''.join(json.dumps(r)+'\n' for r in raw).encode()
            path.write_bytes(data)
            source={'station_id':'ST-FICTION','source_ref':'S1','provider':'codex_rollout',
                    'path':str(path),'bytes':len(data),'sha256':engine.sha(data)}
            extracted=engine.extract_source(source,list(rows.values()),screen,RULES,engine.seconds('2026-08-12T23:59:59Z'))
            return engine.normalize_sources([extracted],rows,screen,RULES)

    def test_absorbed_ack_completes_original_process_once(self):
        out=self.probe()
        self.assertEqual(len(out['events']),1)
        trace=json.loads(out['events'][0]['row']['tool_trace_json'])
        self.assertEqual([c['class'] for c in trace],['verify','administrative'])
        self.assertTrue(trace[0]['completed'] and trace[0]['succeeded'])

    def test_fresh_primary_does_not_inherit_successful_poll(self):
        out=self.probe('Build a separate component.')
        self.assertEqual(len(out['events']),2)
        first=event_for(out,'OLD-S1-1')
        self.assertFalse(json.loads(first['row']['tool_trace_json'])[0]['completed'])

    def test_codex_supplied_image_blocks_ack_absorption(self):
        out=self.probe(attachment=True)
        self.assertEqual(len(out['events']),2)
        self.assertEqual(event_for(out,'OLD-S1-4')['row']['attachment_count'],'1')
        self.assertNotEqual(event_for(out,'OLD-S1-4')['row']['automated_disposition'],'exclude_continuation_only')


if __name__=='__main__':
    unittest.main()

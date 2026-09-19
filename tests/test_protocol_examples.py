"""Fictional examples only: literal no versus missing captured evidence.

These are executable instruction checks, not human ratings or validation data.
"""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
# Public packaging places analytical code under analysis/ and tests at the root.
spec=importlib.util.spec_from_file_location('protocol_example_adapter',ROOT/'analysis/upstream_contract/scripts/postrun-context-screen.py')
screen=importlib.util.module_from_spec(spec);sys.modules[spec.name]=screen;spec.loader.exec_module(screen)

def result(call_id,output):
    return {'type':'response_item','payload':{'type':'function_call_output','call_id':call_id,'output':output}}

def literal_fields(call,source_complete):
    if not source_complete:return ('not_evaluable','not_evaluable')
    return tuple('yes' if call[k] else 'no' for k in ('completed','succeeded'))

def conjunction(values):
    if 'no' in values:return 'no'
    if all(x=='yes' for x in values):return 'yes'
    return 'not_evaluable' if 'not_evaluable' in values else 'uncertain'

class ProtocolExamples(unittest.TestCase):
    def make(self):
        calls=[];state=screen.EpisodeToolState(calls)
        call=state.add_call('fictional-call','exec_command',{'cmd':'pytest'})
        return state,call,calls
    def test_complete_episode_pending_is_literal_no(self):
        s,c,_=self.make();s.apply_record(result('fictional-call',{'exit_code':None,'session_id':17}),'codex_rollout')
        self.assertEqual(literal_fields(c,True),('no','no'))
    def test_complete_episode_no_return_is_literal_no(self):
        _,c,_=self.make();self.assertEqual(literal_fields(c,True),('no','no'))
    def test_missing_interval_is_not_evaluable(self):
        _,c,_=self.make();self.assertEqual(literal_fields(c,False),('not_evaluable','not_evaluable'))
    def test_terminal_failure_is_completed_but_unsuccessful(self):
        s,c,_=self.make();s.apply_record(result('fictional-call',{'exit_code':-1}),'codex_rollout')
        self.assertEqual(literal_fields(c,True),('yes','no'))
    def test_linked_poll_completes_original_not_new_action(self):
        s,c,calls=self.make();s.apply_record(result('fictional-call',{'exit_code':None,'session_id':17}),'codex_rollout')
        poll=s.add_call('fictional-poll','write_stdin',{'session_id':17,'chars':''})
        s.apply_record(result('fictional-poll',{'exit_code':0}),'codex_rollout')
        self.assertEqual(literal_fields(c,True),('yes','yes'))
        self.assertEqual(poll['class'],'administrative')
        self.assertEqual(sum(x['completed'] and x['succeeded'] and x['class'] in {'modify','execute','verify'} for x in calls),1)
    def test_missing_clause_does_not_override_decisive_no(self):
        self.assertEqual(conjunction(['no','not_evaluable']),'no')
        self.assertEqual(conjunction(['yes','not_evaluable']),'not_evaluable')

if __name__=='__main__':unittest.main()

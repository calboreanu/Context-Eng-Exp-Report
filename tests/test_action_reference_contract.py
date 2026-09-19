"""Independent fictional v5 action/reference boundary checks; no study records."""
import copy
import json
import re
import unittest

from test_event_normalization import screen, RULES


def classify(prompt, calls, output_chars=0):
    groups = [screen.compile_groups(RULES, key) for key in ('stages', 'context_modes')]
    regexes = [[re.compile(pattern, re.I | re.S) for pattern in RULES[key]] for key in (
        'publication_exclusions', 'product_signals', 'non_product_exclusions',
        'continuation_only', 'continuation_wrappers', 'delegated_prompt_candidates',
        'tool_generated_prompts')]
    episode = {'prompt_text': prompt, 'attachment_count': 0, 'calls': calls,
               'assistant_output_chars': output_chars}
    return screen.episode_classification(episode, RULES, *groups, *regexes)


def completed_call(name, inputs, order):
    return {'order': order, 'name': name, 'class': screen.classify_tool(name, inputs),
            'completed': True, 'succeeded': True, 'target_ref': f'fictional-{order}'}


class AdministrativeActionContract(unittest.TestCase):
    def test_todowrite_exact_supported_aliases_are_administrative(self):
        for name in ('TodoWrite', 'todowrite', 'TODO_WRITE', 'todo-write',
                     'functions.TodoWrite', 'mcp__planner__todo_write',
                     'planner::TodoWrite', 'planner/TodoWrite'):
            with self.subTest(name=name):
                self.assertEqual(screen.classify_tool(name, {'todos': []}), 'administrative')

    def test_similar_names_do_not_receive_todowrite_exception(self):
        for name in ('TodoWriteExtra', 'RewriteTodoWriteReport', 'TodoWriter'):
            with self.subTest(name=name):
                self.assertNotEqual(screen.classify_tool(name, {}), 'administrative')

    def test_real_write_to_todo_document_remains_substantive(self):
        self.assertEqual(screen.classify_tool('Write', {'file_path': '/fictional/TODO.md',
                         'content': 'TodoWrite planning examples'}), 'modify')
        self.assertEqual(screen.classify_tool('functions.apply_patch',
                         '*** Update File: /fictional/TODO.md'), 'modify')

    def test_structured_provider_variants_retain_completed_bookkeeping(self):
        for provider in ('claude_audit', 'claude_home', 'claude_embedded', 'codex_rollout'):
            for name in ('TodoWrite', 'functions.TodoWrite', 'mcp__planner__todo_write'):
                with self.subTest(provider=provider, name=name):
                    inputs = {'todos': [{'content': 'Implement later', 'status': 'completed'}]}
                    if provider == 'codex_rollout':
                        record = {'type': 'response_item', 'payload': {'type': 'function_call',
                                  'call_id': 'fictional', 'name': name, 'arguments': json.dumps(inputs)}}
                        result = {'type': 'response_item', 'payload': {'type': 'function_call_output',
                                  'call_id': 'fictional', 'output': {'ok': True}}}
                    else:
                        record = {'type': 'assistant', 'message': {'content': [
                            {'type': 'tool_use', 'id': 'fictional', 'name': name, 'input': inputs}]}}
                        result = {'type': 'user', 'message': {'content': [
                            {'type': 'tool_result', 'tool_use_id': 'fictional', 'is_error': False,
                             'content': 'Task list updated'}]}}
                    calls = []
                    state = screen.EpisodeToolState(calls)
                    for call_id, tool, raw in screen.extract_tool_calls(record, provider):
                        state.add_call(call_id, tool, raw, provider)
                    state.apply_record(result, provider)
                    self.assertEqual(len(calls), 1)
                    self.assertEqual(calls[0]['class'], 'administrative')
                    self.assertTrue(calls[0]['completed'] and calls[0]['succeeded'])

    def test_administrative_only_does_not_supply_product_action(self):
        row = classify('Implement the component.', [completed_call('TodoWrite', {'todos': []}, 1)])
        self.assertEqual(row['completed_tool_calls'], 1)
        self.assertEqual(row['completed_substantive_action_calls'], 0)
        self.assertEqual(row['automated_disposition'], 'exclude_no_observable_product_action')

    def test_read_then_plan_is_not_a_substantive_action(self):
        calls = [completed_call('Read', {'file_path': '/fictional/spec.md'}, 1),
                 completed_call('TodoWrite', {'todos': []}, 2)]
        row = classify('Use the standards to implement the component.', calls)
        self.assertEqual(row['automated_disposition'], 'exclude_no_observable_product_action')

    def test_real_action_after_bookkeeping_is_counted_once(self):
        calls = [completed_call('TodoWrite', {'todos': []}, 1),
                 completed_call('Read', {'file_path': '/fictional/spec.md'}, 2),
                 completed_call('Write', {'file_path': '/fictional/feature.py'}, 3)]
        row = classify('Use the standards to implement the component.', calls)
        self.assertEqual(row['completed_substantive_action_calls'], 1)
        self.assertEqual(row['context_retrieval_calls_before_action'], 1)
        self.assertEqual(row['automated_disposition'], 'candidate_strong')

    def test_failed_real_action_not_rescued_by_successful_task_list(self):
        calls = [completed_call('TodoWrite', {'todos': []}, 1),
                 completed_call('Write', {'file_path': '/fictional/feature.py'}, 2)]
        calls[-1]['succeeded'] = False
        row = classify('Implement the component.', calls)
        self.assertEqual(row['completed_substantive_action_calls'], 0)
        self.assertEqual(row['automated_disposition'], 'exclude_no_observable_product_action')

    def test_genuine_grounded_decision_proxy_is_not_removed(self):
        calls = [completed_call('Read', {'file_path': '/fictional/spec.md'}, 1),
                 completed_call('TodoWrite', {'todos': []}, 2)]
        row = classify('Review requirements against the standards.', calls, output_chars=120)
        self.assertEqual(row['completed_substantive_action_calls'], 0)
        self.assertEqual(row['grounded_decision_trace'], 'yes')


class ArtifactReferenceContract(unittest.TestCase):
    def test_bare_numeric_tokens_and_sentence_punctuation_do_not_count(self):
        for token in ('.05', '.01.', '.001!', '.5?', '.5e-2', '.5E+2', '.5%', '.5e-2%.'):
            with self.subTest(token=token):
                self.assertEqual(screen.artifact_references(f'Threshold {token}'), set())

    def test_zero_prefixed_numbers_remain_nonreferences(self):
        self.assertEqual(screen.artifact_references('0.05 1.01 -0.5 1e-3'), set())

    def test_real_dotfiles_are_retained(self):
        self.assertEqual(screen.artifact_references('.env .gitignore .github/workflows/check.yml'),
                         {'.env', '.gitignore', '.github/workflows/check.yml'})

    def test_qualified_numeric_and_regular_paths_are_retained(self):
        values = {'./.05', '../.01', '/fictional/.05', '~/.05', './module.py', '../spec.md'}
        self.assertEqual(screen.artifact_references(' '.join(sorted(values))), values)

    def test_numeric_stem_filename_with_extension_is_retained(self):
        self.assertEqual(screen.artifact_references('.05.csv .01.json'), {'.05.csv', '.01.json'})

    def test_url_reference_behavior_is_preserved_not_called_proven_artifact(self):
        # URLs remain lexical reference candidates, not proof of supplied content.
        before = screen.artifact_references('https://example.com/api/users')
        self.assertTrue(before)
        self.assertEqual(screen.artifact_references('https://example.com/.05'), {'//example.com/.05'})

    def test_xml_syntax_removed_but_dotfile_and_qualified_path_values_preserved(self):
        prompt = '<file path=".env"/><file path="/fictional/.gitignore"/><path>./.05</path>'
        self.assertEqual(screen.artifact_references(prompt), {'.env', '/fictional/.gitignore', './.05'})

    def test_xml_numeric_content_is_not_promoted_to_path(self):
        self.assertEqual(screen.artifact_references('<threshold>.05</threshold> <value>.01</value>'), set())

    def test_decimal_spelling_does_not_change_context_route(self):
        calls = [completed_call('Read', {'file_path': '/fictional/feature.py'}, 1),
                 completed_call('Write', {'file_path': '/fictional/feature.py'}, 2)]
        short = classify('Set the thresholds to .05 and .01.', copy.deepcopy(calls))
        long = classify('Set the thresholds to 0.05 and 0.01.', copy.deepcopy(calls))
        for field in ('prompt_artifact_reference_count', 'context_mode_mask', 'automated_disposition'):
            self.assertEqual(short[field], long[field])
        self.assertEqual(short['automated_disposition'], 'exclude_no_context_operation')

    def test_three_decimals_do_not_create_multi_source_synthesis(self):
        row = classify('Set thresholds .05, .01 and .001.', [completed_call('Write', {}, 1)])
        self.assertEqual(row['prompt_artifact_reference_count'], 0)
        self.assertNotIn('multi_source_synthesis', row['context_mode_mask'])

    def test_two_genuine_dotfiles_still_supply_frontloading_reference_count(self):
        calls = [completed_call('Read', {'file_path': '/fictional/.env'}, 1),
                 completed_call('Write', {'file_path': '/fictional/.env'}, 2)]
        row = classify('Use .env and .gitignore to implement the component.', calls)
        self.assertEqual(row['prompt_artifact_reference_count'], 2)
        self.assertIn('bounded_package', row['context_mode_mask'])
        self.assertEqual(row['automated_disposition'], 'candidate_strong')


if __name__ == '__main__':
    unittest.main()

"""Fictional v5 specificity regressions; no private cases."""
import unittest
from test_event_normalization import screen, user, call, result, fixture, normalize


class ActionReferenceCorrectionTests(unittest.TestCase):
    def test_closed_todo_name_family(self):
        for name in ('TodoWrite', 'TODOWRITE', 'todo_write', 'todo-write',
                     'functions.TodoWrite', 'mcp__provider__TodoWrite',
                     'provider::todo_write', 'provider/TodoWrite'):
            with self.subTest(name=name):
                self.assertEqual(screen.classify_tool(name, {'todos': []}), 'administrative')

    def test_real_file_writes_and_other_names_preserved(self):
        for name in ('Write', 'functions.Write', 'TodoWriteExtra', 'my_todowrite'):
            with self.subTest(name=name):
                self.assertEqual(screen.classify_tool(name, {'file_path': './TODO.md', 'content': 'plan'}), 'modify')
        for name in ('BashOutput', 'KillShell'):
            self.assertEqual(screen.classify_tool(name, {}), 'execute')

    def test_baseline_guard_keeps_pre_correction_taxonomy(self):
        for name in ('TodoWrite', 'functions.todo_write'):
            self.assertEqual(screen.classify_tool_before_v5(name, {'todos': []}), 'modify')
            self.assertEqual(screen.classify_tool(name, {'todos': []}), 'administrative')
        for name in ('Write', 'Read', 'TaskCreate', 'BashOutput', 'KillShell'):
            self.assertEqual(screen.classify_tool_before_v5(name, {}), screen.classify_tool(name, {}))

    def test_completed_admin_only_trajectory_has_no_substantive_action(self):
        records = [user('u', 'Plan the work for the repository'),
                   call('a', 'c', name='TodoWrite', parent='u'), result('r', 'c', parent='a')]
        row = normalize(fixture(records, provider='claude_home'))['events'][0]['row']
        self.assertEqual(row['tool_calls'], '1')
        self.assertEqual(row['completed_tool_calls'], '1')
        self.assertEqual(row['completed_substantive_action_calls'], '0')
        self.assertEqual(row['automated_disposition'], 'exclude_no_observable_product_action')

    def test_mixed_admin_retrieval_and_write_preserves_work_and_order(self):
        records = [user('u', 'Implement using the repository.'),
                   call('a', 'todo', name='TodoWrite', parent='u', second=1),
                   result('r', 'todo', parent='a', second=2),
                   call('b', 'read', name='Read', parent='r', second=3),
                   result('s', 'read', parent='b', second=4),
                   call('c', 'write', name='Write', parent='s', second=5),
                   result('t', 'write', parent='c', second=6)]
        row = normalize(fixture(records, provider='claude_home'))['events'][0]['row']
        self.assertEqual(row['tool_calls'], '3')
        self.assertEqual(row['completed_tool_calls'], '3')
        self.assertEqual(row['completed_substantive_action_calls'], '1')
        self.assertEqual(row['context_retrieval_calls_before_action'], '1')
        self.assertEqual(row['automated_disposition'], 'candidate_strong')

    def test_bare_numeric_reference_grammar(self):
        for token in ('.05', '.01', '.5e2', '.5E-2', '.5e+2', '.05%', '.05.', '.05!?'):
            with self.subTest(token=token):
                self.assertEqual(screen.artifact_references('Value ' + token), set())

    def test_dotfiles_qualified_numeric_paths_and_urls_preserved(self):
        for token in ('.env', '.gitignore', '.05.md', './.05', '../.05', '/fictional/.05',
                      '~/.05', './run.sh', 'https://example.org/data/.05'):
            with self.subTest(token=token):
                self.assertEqual(len(screen.artifact_references('Read ' + token)), 1)

    def test_numeric_tokens_do_not_supply_context_or_frontloading(self):
        row = normalize(fixture([user('u', 'Report p < .05 and q < .01 for the model'),
                                 call('a', 'c', parent='u'), result('r', 'c', parent='a')]))['events'][0]['row']
        self.assertEqual(row['prompt_artifact_reference_count'], '0')
        self.assertEqual(row['context_mode_mask'], '')
        self.assertEqual(row['automated_disposition'], 'exclude_no_context_operation')

    def test_xml_and_real_paths_remain_context(self):
        prompt = '<file path="./.05"/> <file path=".env"/> p < .05 and q < .01'
        self.assertEqual(screen.artifact_references(prompt), {'./.05', '.env'})


if __name__ == '__main__':
    unittest.main()

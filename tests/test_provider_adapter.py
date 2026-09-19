"""Fictional-only regression tests; no research records or human labels."""
import importlib.util
import json
import csv
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'upstream_contract').is_dir():
    ROOT = ROOT / 'analysis'
SCREEN = ROOT / "upstream_contract/scripts/postrun-context-screen.py"
spec = importlib.util.spec_from_file_location("corrected_screen", SCREEN)
screen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = screen
spec.loader.exec_module(screen)


def result(call_id, value):
    return {"type": "response_item", "payload": {"type": "function_call_output", "call_id": call_id, "output": value}}


def header(status, body="fictional output"):
    return "Chunk ID: fictional\nWall time: 0.01 seconds\nProcess " + status + "\nFinal output:\n" + body


def statuses(value):
    parts = screen.result_status_parts(value)
    return all(p.completed for p in parts), all(p.completed and p.succeeded for p in parts)


class Envelopes(unittest.TestCase):
    def test_numeric_codes(self):
        for code, expected in [(0, True), (1, False), (-9, False), (137, False), ("0", True), ("-15", False)]:
            with self.subTest(code=code):
                self.assertEqual(statuses({"exit_code": code, "output": "irrelevant"}), (True, expected))

    def test_error_flags_override_exit_and_content(self):
        for flag in ("isError", "is_error"):
            self.assertEqual(statuses({"exit_code": 0, flag: True}), (True, False))
            self.assertEqual(statuses({"content": [{"type": "text", "text": header("exited with code 0")}], flag: True}), (True, False))
            self.assertEqual(statuses({"session_id": 5, flag: True}), (False, False))

    def test_non_boolean_error_is_not_inferred(self):
        self.assertEqual(statuses({"isError": "false"}), (True, True))

    def test_structured_running(self):
        for obj in ({"exit_code": None, "session_id": 17}, {"session_id": "17"}, {"session_id": None}, {"exit_code": None, "session_id": None}, {"exit_code": None}, {"exit_code": "timeout"}, {"exit_code": False}):
            self.assertEqual(statuses(obj), (False, False))

    def test_terminal_with_retained_session_is_terminal(self):
        self.assertEqual(statuses({"exit_code": 0, "session_id": 17}), (True, True))
        self.assertEqual(statuses({"exit_code": -1, "session_id": 17}), (True, False))

    def test_headers(self):
        for code in (0, 1, -9):
            self.assertEqual(statuses(header("exited with code " + str(code))), (True, code == 0))
        self.assertEqual(statuses(header("running with session ID 177")), (False, False))

    def test_quotes_not_mined(self):
        samples = [
            'Documentation example: {"exit_code": 1}',
            '```json\n{"exit_code": 1}\n```',
            'Quoted error:\n' + header("exited with code -9"),
            'The process may say Process exited with code 1.',
            header("exited with code 0", header("exited with code -9")),
            {"output": '{"exit_code": 1}'},
            {"content": [{"type": "text", "text": 'Example: {"exit_code": 1}'}]},
        ]
        for value in samples:
            with self.subTest(value=type(value).__name__):
                self.assertEqual(statuses(value), (True, True))

    def test_serialized_structured_result(self):
        self.assertEqual(statuses(json.dumps({"exit_code": -9})), (True, False))
        self.assertEqual(statuses(json.dumps({"exit_code": None, "session_id": 4})), (False, False))

    def test_content_blocks(self):
        self.assertEqual(statuses([{"type": "text", "text": json.dumps({"exit_code": 3})}]), (True, False))
        self.assertEqual(statuses({"content": [{"type": "text", "text": header("running with session ID 4")}]}), (False, False))
        self.assertEqual(statuses([{"type": "image", "data": "fictional"}]), (True, True))
        self.assertEqual(statuses([{"type": "text", "text": '{"exit_code":0}', "isError": True}]), (True, False))

    def test_multiple_components_do_not_mix(self):
        values = [
            {"type": "text", "text": json.dumps({"exit_code": 0})},
            {"type": "text", "text": json.dumps({"exit_code": -9})},
        ]
        self.assertEqual(statuses(values), (True, False))
        values.append({"type": "text", "text": json.dumps({"session_id": 4})})
        self.assertEqual(statuses(values), (False, False))

    def test_missing_output(self):
        self.assertEqual(statuses(None), (False, False))

    def test_generic_tool_receipt_remains_heuristic(self):
        self.assertEqual(statuses("Search returned three results."), (True, True))
        self.assertEqual(statuses({"matches": []}), (True, True))

    def test_script_headers(self):
        self.assertEqual(statuses("Script running with cell ID cellA\n"), (False, False))
        self.assertEqual(statuses("Script completed\nWall time: 0.1 seconds\nOutput:\n"), (True, True))

    def test_nested_script_status_not_hidden_by_transport_success(self):
        self.assertEqual(statuses('Script completed\nWall time: 1\nOutput:\n{"exit_code":-9}'), (True, False))
        self.assertEqual(statuses('Script completed\nWall time: 1\nOutput:\n{"exit_code":0}{"session_id":17}'), (False, False))
        self.assertEqual(statuses('Script completed\nWall time: 1\nOutput:\nExample: {"exit_code":1}'), (True, True))
        self.assertEqual(statuses('Script completed\nWall time: 1\nOutput:\n' + header("exited with code -9")), (True, False))
        self.assertEqual(statuses('Script completed\nWall time: 1\nOutput:\n' + header("running with session ID 7")), (False, False))

    def test_outer_success_does_not_erase_inner_error(self):
        self.assertEqual(statuses({"exit_code": 0, "content": [{"type": "text", "text": '{"exit_code":1}'}]}), (True, False))


class Associations(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.state = screen.EpisodeToolState(self.calls)

    def add(self, call_id="a", name="functions.exec_command", args=None):
        return self.state.add_call(call_id, name, args or {"cmd": "pytest"})

    def apply(self, call_id, value):
        self.state.apply_record(result(call_id, value), "codex_rollout")

    def test_absent_result(self):
        call = self.add()
        self.assertFalse(call["completed"])
        self.assertFalse(call["succeeded"])

    def test_successful_poll_completes_original_only_once(self):
        original = self.add()
        self.apply("a", header("running with session ID 17"))
        self.assertFalse(original["completed"])
        poll = self.add("p", "functions.write_stdin", {"session_id": 17, "chars": ""})
        self.apply("p", header("exited with code 0"))
        self.assertEqual((original["completed"], original["succeeded"]), (True, True))
        self.assertEqual(original["class"], "verify")
        self.assertEqual(poll["class"], "administrative")
        self.assertEqual(sum(c["completed"] and c["succeeded"] and c["class"] == "verify" for c in self.calls), 1)

    def test_failed_poll_completes_unsuccessfully(self):
        original = self.add()
        self.apply("a", {"exit_code": None, "session_id": "17"})
        self.add("p", "write_stdin", {"session_id": 17})
        self.apply("p", {"exit_code": -9})
        self.assertEqual((original["completed"], original["succeeded"]), (True, False))

    def test_multiple_running_polls_then_success(self):
        original = self.add()
        self.apply("a", {"session_id": 17})
        for n in range(3):
            self.add(str(n), "write_stdin", {"session_id": 17})
            self.apply(str(n), {"session_id": 17})
            self.assertFalse(original["completed"])
        self.add("done", "write_stdin", {"session_id": 17})
        self.apply("done", {"exit_code": 0})
        self.assertTrue(original["succeeded"])

    def test_mixed_sessions_not_linked(self):
        original = self.add()
        self.apply("a", {"session_id": 17})
        self.add("p", "write_stdin", {"session_id": 18})
        self.apply("p", {"exit_code": 0})
        self.assertFalse(original["completed"])
        self.add("q", "write_stdin", {"session_id": 17})
        self.apply("q", {"exit_code": 0, "session_id": 18})
        self.assertFalse(original["completed"])

    def test_other_call_success_not_transferred(self):
        original = self.add()
        self.apply("a", {"session_id": 17})
        other = self.add("other")
        self.apply("other", {"exit_code": 0})
        self.assertFalse(original["completed"])
        self.assertTrue(other["succeeded"])

    def test_cross_episode_isolation(self):
        original = self.add()
        self.apply("a", {"session_id": 17})
        later = screen.EpisodeToolState([])
        later.add_call("p", "write_stdin", {"session_id": 17})
        later.apply_record(result("p", {"exit_code": 0}), "codex_rollout")
        self.assertFalse(original["completed"])
        self.assertEqual(later.diagnostics["unlinked_poll_results"], 1)

    def test_duplicate_session_owners_are_ambiguous(self):
        a = self.add()
        self.apply("a", {"session_id": 17})
        b = self.add("b")
        self.apply("b", {"session_id": 17})
        self.add("p", "write_stdin", {"session_id": 17})
        self.apply("p", {"exit_code": 0})
        self.assertFalse(a["completed"])
        self.assertFalse(b["completed"])

    def test_duplicate_call_ids_are_ambiguous(self):
        a = self.add()
        b = self.add()
        self.apply("a", {"exit_code": 0})
        self.assertFalse(a["completed"])
        self.assertFalse(b["completed"])

    def test_same_call_running_then_terminal(self):
        call = self.add()
        self.apply("a", {"session_id": 17})
        self.apply("a", {"exit_code": 0})
        self.assertEqual((call["completed"], call["succeeded"]), (True, True))

    def test_same_call_generic_ack_keeps_pending(self):
        call = self.add()
        self.apply("a", {"session_id": 17})
        self.apply("a", "Received")
        self.assertEqual((call["completed"], call["succeeded"]), (False, False))
        self.apply("a", {"exit_code": 0})
        self.assertTrue(call["succeeded"])

    def test_same_call_empty_content_keeps_pending(self):
        call = self.add()
        self.apply("a", {"session_id": 17})
        self.apply("a", {"content": []})
        self.assertFalse(call["completed"])

    def test_same_call_conflicting_explicit_session_keeps_pending(self):
        call = self.add()
        self.apply("a", {"session_id": 17})
        self.apply("a", {"exit_code": 0, "session_id": 18})
        self.assertFalse(call["completed"])
        self.apply("a", {"exit_code": 0, "session_id": 17})
        self.assertTrue(call["succeeded"])

    def test_failed_terminal_not_erased_by_generic_ack(self):
        call = self.add()
        self.apply("a", {"exit_code": 1})
        self.apply("a", "Received")
        self.assertFalse(call["succeeded"])

    def test_poll_generic_ack_does_not_finish_process(self):
        call = self.add()
        self.apply("a", {"session_id": 17})
        self.add("p", "write_stdin", {"session_id": 17})
        self.apply("p", "OK")
        self.assertFalse(call["completed"])

    def test_two_pending_components_complete_separately(self):
        call = self.add()
        self.apply("a", [{"type": "text", "text": json.dumps({"session_id": 17})},
                         {"type": "text", "text": json.dumps({"session_id": 18})}])
        for session, expected in [(17, False), (18, True)]:
            self.add(str(session), "write_stdin", {"session_id": session})
            self.apply(str(session), {"exit_code": 0})
            self.assertEqual(call["succeeded"], expected)

    def test_one_failed_component_never_becomes_success(self):
        call = self.add()
        self.apply("a", [{"type": "text", "text": json.dumps({"exit_code": -1})},
                         {"type": "text", "text": json.dumps({"session_id": 18})}])
        self.add("p", "write_stdin", {"session_id": 18})
        self.apply("p", {"exit_code": 0})
        self.assertEqual((call["completed"], call["succeeded"]), (True, False))

    def test_error_wrapped_poll_does_not_make_success(self):
        call = self.add()
        self.apply("a", {"session_id": 17})
        self.add("p", "write_stdin", {"session_id": 17})
        self.apply("p", {"isError": True, "content": [{"type": "text", "text": json.dumps({"exit_code": 0})}]})
        self.assertEqual((call["completed"], call["succeeded"]), (True, False))

    def test_trace_shape_and_order_preserved(self):
        a = self.add()
        b = self.add("p", "write_stdin", {"session_id": 17})
        self.assertEqual(set(a), {"order", "name", "class", "completed", "succeeded", "target_ref"})
        self.assertEqual([a["order"], b["order"]], [1, 2])

    def test_claude_status_and_class_unchanged(self):
        call = self.state.add_call("c", "write_stdin", {"session_id": 17}, "claude_home")
        self.state.apply_record({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "c", "is_error": True}]}}, "claude_home")
        self.assertEqual((call["class"], call["completed"], call["succeeded"]), ("modify", True, False))
        self.state.apply_record({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "c", "is_error": False}]}}, "claude_home")
        self.assertTrue(call["succeeded"])

    def test_cell_poll_then_process_poll(self):
        call = self.add("a", "functions.exec", "text(await tools.exec_command({cmd:'pytest'}))")
        self.apply("a", "Script running with cell ID c1\n")
        self.add("w", "functions.wait", {"cell_id": "c1"})
        self.apply("w", 'Script completed\nOutput:\n{"session_id":17}')
        self.assertFalse(call["completed"])
        self.add("p", "functions.write_stdin", {"session_id": 17})
        self.apply("p", {"exit_code": 0})
        self.assertTrue(call["succeeded"])

    def test_cell_poll_failed_nested_process(self):
        call = self.add("a", "functions.exec", "fictional code")
        self.apply("a", "Script running with cell ID c1\n")
        self.add("w", "functions.wait", {"cell_id": "c1"})
        self.apply("w", 'Script completed\nOutput:\n{"exit_code":-9}')
        self.assertEqual((call["completed"], call["succeeded"]), (True, False))

    def test_unmatched_result_does_not_retroactively_link(self):
        self.apply("a", {"exit_code": 0})
        call = self.add()
        self.assertFalse(call["completed"])

    def test_poll_missing_session_is_administrative_unlinked(self):
        call = self.add("p", "write_stdin", {"session_id": None})
        self.apply("p", {"exit_code": 0})
        self.assertEqual(call["class"], "administrative")
        self.assertEqual(self.state.diagnostics["unlinked_poll_results"], 1)


class Prompts(unittest.TestCase):
    def prompt(self, blocks):
        return {"type": "response_item", "payload": {"type": "message", "role": "user", "content": blocks}}

    def test_codex_attachment_count(self):
        record = self.prompt([{"type": "input_text", "text": "Build the app"}, {"type": "input_image", "image_url": "fictional"}])
        self.assertEqual(screen.extract_human_prompt(record, "codex_rollout", []), ("Build the app", 1))

    def test_image_only_boundary_unchanged(self):
        self.assertIsNone(screen.extract_human_prompt(self.prompt([{"type": "input_image", "image_url": "fictional"}]), "codex_rollout", []))

    def test_injected_blocks_filtered_unchanged(self):
        record = self.prompt([{"type": "input_text", "text": "<environment_context>fixture</environment_context>"}, {"type": "input_text", "text": "Build the app"}])
        self.assertEqual(screen.extract_human_prompt(record, "codex_rollout", ["<environment_context>"]), ("Build the app", 0))

    def test_claude_attachment_count_unchanged(self):
        record = {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "Build"}, {"type": "image"}, {"type": "document"}]}}
        self.assertEqual(screen.extract_human_prompt(record, "claude_home", []), ("Build", 2))


class FullScanner(unittest.TestCase):
    def test_cutoff_boundaries_and_fictional_source(self):
        """Run the real CLI on generated fixtures, never on research sources."""
        with tempfile.TemporaryDirectory(prefix="ce-v2-fixture-") as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            sources = root / "station/restricted/interaction_sources"
            sources.mkdir(parents=True)
            rules = {
                "rule_version": "fictional-rule-v1", "cutoff_id": "fictional-cutoff",
                "stages": {"verification": ["verify"], "context": ["context"]},
                "context_modes": {"explicit": ["standards"]},
                "publication_exclusions": [], "product_signals": ["app"],
                "continuation_only": ["continue"], "nonhuman_block_prefixes": ["<environment_context>"],
                "non_product_exclusions": [], "continuation_wrappers": [],
                "delegated_prompt_candidates": [], "tool_generated_prompts": [],
                "minimum_assistant_output_chars_for_decision": 100,
                "minimum_distinct_retrieval_targets_for_implicit_context": 2,
            }
            (root / "config/context-engineering-eligibility.json").write_text(json.dumps(rules))
            (root / "config/study-cutoff.json").write_text(json.dumps({"cutoff_id": "fictional-cutoff", "snapshot_observed_at_utc": "2026-01-02T00:00:00Z"}))
            (root / "config/run.json").write_text(json.dumps({"stations": [{"station_id": "STF", "kind": "directory", "path": str(root / "station")}]}))
            def prompt(text):
                return {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}, {"type": "input_image", "image_url": "fictional"}]}}
            def call(cid, name, args):
                return {"type": "response_item", "payload": {"type": "function_call", "call_id": cid, "name": name, "arguments": json.dumps(args)}}
            records = [
                prompt("Verify the app using standards"),
                call("a", "exec_command", {"cmd": "pytest"}),
                result("a", {"session_id": 17}),
                prompt("Verify the second app"),
                call("p", "write_stdin", {"session_id": 17}),
                result("p", {"exit_code": 0}),
                call("b", "exec_command", {"cmd": "pytest"}),
                result("b", {"session_id": 18}),
                call("q", "write_stdin", {"session_id": 18}),
                {**result("q", {"exit_code": 0}), "timestamp": "2026-01-03T00:00:00Z"},
            ]
            raw = b"".join((json.dumps(r) + "\n").encode() for r in records)
            (sources / "fictional.jsonl").write_bytes(raw)
            with (root / "station/restricted/interaction_source_candidates.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["source_ref", "provider", "case_id", "sha256"])
                writer.writeheader()
                writer.writerow({"source_ref": "fictional", "provider": "codex_rollout", "case_id": "STATION-WIDE", "sha256": hashlib.sha256(raw).hexdigest()})
            run = subprocess.run([sys.executable, str(SCREEN), "--config", "config/run.json"], cwd=root, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            with (root / ".private/multistation_context_episode_review.local.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual([row["attachment_count"] for row in rows], ["1", "1"])
            self.assertEqual([row["source_line_start"] for row in rows], ["1", "4"])
            self.assertEqual([row["source_line_end"] for row in rows], ["3", "9"])
            self.assertEqual([row["completed_substantive_action_calls"] for row in rows], ["0", "0"])
            self.assertIn(screen.ADAPTER_VERSION, rows[0]["rule_version"])
            self.assertFalse(json.loads(rows[0]["tool_trace_json"])[0]["completed"])
            self.assertFalse(json.loads(rows[1]["tool_trace_json"])[1]["completed"])


if __name__ == "__main__":
    unittest.main()

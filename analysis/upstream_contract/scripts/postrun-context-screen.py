#!/usr/bin/env python3
"""Build a prompt-episode universe and conservative context-engineering screen.

Raw prompts and tool traces are written only to a git-ignored private CSV. All
public classifications are routing candidates, never human adjudications.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shlex
import sys
import zipfile
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

ADAPTER_VERSION = "ce-provider-adapter-v2.0.0-20260917"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def token(prefix: str, value: str) -> str:
    return f"{prefix}-{digest(value)[:20]}"


def yes(value: bool) -> str:
    return "yes" if value else "no"


def compact_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def safe_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class SourceSpec:
    reported_ref: str
    canonical_ref: str
    provider: str
    case_ids: list[str]
    expected_sha256: str


class StationPackage:
    def __init__(self, spec: dict):
        self.station_id = spec["station_id"]
        self.kind = spec["kind"]
        self.path = Path(spec["path"])
        self.zip = None
        self.zip_names = {}
        if self.kind == "zip":
            self.zip = zipfile.ZipFile(self.path)
            self.zip_names = {
                Path(name).stem: name
                for name in self.zip.namelist()
                if "/restricted/interaction_sources/" in name and name.endswith(".jsonl")
            }

    def close(self):
        if self.zip:
            self.zip.close()

    def _manifest_rows(self):
        suffix = "restricted/interaction_source_candidates.csv"
        if self.kind == "zip":
            name = next((n for n in self.zip.namelist() if n.endswith(suffix)), None)
            if not name:
                raise RuntimeError(f"{self.station_id}: no {suffix} in archive")
            with self.zip.open(name) as raw:
                yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", errors="replace"))
        elif self.kind == "directory":
            with (self.path / suffix).open(encoding="utf-8", errors="replace", newline="") as raw:
                yield from csv.DictReader(raw)
        else:
            raise RuntimeError(f"{self.station_id}: unsupported kind {self.kind}")

    def sources(self) -> list[SourceSpec]:
        grouped = {}
        for row in self._manifest_rows():
            reported = row["source_ref"]
            item = grouped.setdefault(reported, {
                "provider": row["provider"],
                "cases": set(),
                "sha256": row.get("sha256", "")
            })
            if item["provider"] != row["provider"]:
                raise RuntimeError(f"{self.station_id}/{reported}: provider conflict")
            item["cases"].add(row.get("case_id", "STATION-WIDE") or "STATION-WIDE")
        return [
            SourceSpec(
                reported_ref=reported,
                canonical_ref=token("SRC", f"{self.station_id}|{reported}"),
                provider=item["provider"],
                case_ids=sorted(item["cases"]),
                expected_sha256=item["sha256"],
            )
            for reported, item in sorted(grouped.items())
        ]

    @contextmanager
    def open_source(self, reported_ref: str):
        if self.kind == "zip":
            name = self.zip_names.get(reported_ref)
            if not name:
                raise FileNotFoundError(f"{self.station_id}: source absent from ZIP: {reported_ref}")
            with self.zip.open(name) as raw:
                yield raw
        else:
            path = self.path / "restricted" / "interaction_sources" / f"{reported_ref}.jsonl"
            with path.open("rb") as raw:
                yield raw


def compile_groups(config: dict, name: str):
    return {
        key: [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in patterns]
        for key, patterns in config[name].items()
    }


def matched_groups(text: str, groups: dict) -> tuple[list[str], int]:
    names, total = [], 0
    for name, regexes in groups.items():
        hits = sum(1 for regex in regexes if regex.search(text))
        if hits:
            names.append(name)
            total += hits
    return names, total


def matching_count(text: str, regexes: list[re.Pattern]) -> int:
    return sum(1 for regex in regexes if regex.search(text))


def timestamp_of(record: dict) -> str:
    return str(record.get("_audit_timestamp") or record.get("timestamp") or
               (record.get("payload") or {}).get("timestamp") or "")


def content_text(content, accepted=("text", "input_text", "output_text")) -> list[str]:
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    return [
        str(item.get("text"))
        for item in content
        if isinstance(item, dict) and item.get("type") in accepted and isinstance(item.get("text"), str)
    ]


def extract_human_prompt(record: dict, provider: str, nonhuman_prefixes: list[str]):
    attachments = 0
    if provider in {"claude_audit", "claude_home", "claude_embedded"}:
        if record.get("type") != "user" or record.get("isMeta") or record.get("isCompactSummary") or record.get("isSidechain"):
            return None
        message = record.get("message") if isinstance(record.get("message"), dict) else {}
        if message.get("role") != "user":
            return None
        content = message.get("content")
        if isinstance(content, list):
            if any(isinstance(item, dict) and item.get("type") == "tool_result" for item in content):
                return None
            attachments = sum(1 for item in content if isinstance(item, dict) and item.get("type") in {"image", "document"})
        text = "\n".join(content_text(content)).strip()
    elif provider == "codex_rollout":
        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        if record.get("type") != "response_item" or payload.get("type") != "message" or payload.get("role") != "user":
            return None
        content = payload.get("content")
        if isinstance(content, list):
            attachments = sum(isinstance(item, dict) and item.get("type") == "input_image"
                              for item in content)
        blocks = []
        for value in content_text(payload.get("content"), accepted=("input_text", "text")):
            stripped = value.strip()
            lower = stripped.lower()
            if any(lower.startswith(prefix.lower()) for prefix in nonhuman_prefixes):
                continue
            blocks.append(stripped)
        text = "\n".join(blocks).strip()
    else:
        return None
    if not text:
        return None
    return text, attachments


def claude_tool_result(record: dict):
    if record.get("type") != "user":
        return []
    message = record.get("message") if isinstance(record.get("message"), dict) else {}
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [
        (str(item.get("tool_use_id", "")), not bool(item.get("is_error")))
        for item in content
        if isinstance(item, dict) and item.get("type") == "tool_result" and item.get("tool_use_id")
    ]


@dataclass(frozen=True)
class ResultStatus:
    """Provider-reported status, not a judgment about task/output quality."""
    completed: bool
    succeeded: bool
    session_id: str | None = None
    kind: str = "transport_response"
    process: bool = False


# The match MUST start at the transport envelope, never inside its Output body.
PROCESS_HEADER = re.compile(
    r"\AChunk ID: [^\n]+\nWall time: [^\n]+\nProcess "
    r"(?:exited with code (-?\d+)|running with session ID ([^\s]+))"
    r"[ \t]*(?:\n|\Z)")
SCRIPT_HEADER = re.compile(
    r"\AScript (?:running with cell ID ([^\s]+)|completed)"
    r"[ \t]*(?:\n|\Z)")


def _session(value):
    return str(value) if isinstance(value, (str, int)) and not isinstance(value, bool) and str(value) else None


def _exit_code(value):
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value):
        return int(value)
    return None


def _script_body_parts(text):
    """Decode a code-mode Output body only when entirely structured results.

    Arbitrary prose, logs and quoted examples are not searched. JSON content is
    still provider-reported output, not independently authenticated telemetry.
    """
    marker = "\nOutput:\n"
    if marker not in text:
        return []
    remainder = text.split(marker, 1)[1].strip()
    if PROCESS_HEADER.match(remainder):
        return result_status_parts(remainder)
    decoded = []
    decoder = json.JSONDecoder()
    while remainder:
        try:
            obj, end = decoder.raw_decode(remainder)
        except ValueError:
            return []
        if not isinstance(obj, (dict, list)):
            return []
        decoded.extend(result_status_parts(obj))
        remainder = remainder[end:].strip()
    return decoded


def result_status_parts(value) -> list[ResultStatus]:
    """Parse supported envelopes only; do not search arbitrary response prose.

    Generic result receipt remains a transport-success heuristic. An explicit
    process envelope supersedes that heuristic. Nested content/text wrappers
    are supported; arbitrary output/JSON data fields are not recursively mined.
    """
    if isinstance(value, str):
        stripped = value.strip()
        match = PROCESS_HEADER.match(stripped)
        if match:
            if match.group(1) is not None:
                code = int(match.group(1))
                return [ResultStatus(True, code == 0, kind="process_exit", process=True)]
            return [ResultStatus(False, False, _session(match.group(2)), "process_running", True)]
        # Code-mode cell completion does not establish nested process success.
        script = SCRIPT_HEADER.match(stripped)
        if script:
            if script.group(1):
                return [ResultStatus(False, False, "cell:" + script.group(1), "script_running", True)]
            return _script_body_parts(stripped) or [ResultStatus(True, True, kind="script_completed", process=True)]
        try:
            decoded = json.loads(stripped)
        except (ValueError, TypeError):
            return [ResultStatus(True, True)]
        if isinstance(decoded, (dict, list)):
            return result_status_parts(decoded)
        return [ResultStatus(True, True)]
    if isinstance(value, list):
        parts = []
        for block in value:
            if isinstance(block, dict) and block.get("type") in {"text", "output_text"} and isinstance(block.get("text"), str):
                parts.extend(result_status_parts(block))
            else:
                parts.append(ResultStatus(True, True))
        return parts or [ResultStatus(True, True)]
    if isinstance(value, dict):
        failed = value.get("isError") is True or value.get("is_error") is True
        code = _exit_code(value.get("exit_code"))
        session = _session(value.get("session_id"))
        if code is not None:
            parts = [ResultStatus(True, code == 0 and not failed, session, "process_exit", True)]
            if isinstance(value.get("content"), list):
                parts.extend(result_status_parts(value["content"]))
        elif session is not None:
            parts = [ResultStatus(False, False, session, "process_running", True)]
        elif "exit_code" in value or "session_id" in value:
            # Null/unparseable exit status without a live session is unknown,
            # not terminal success (e.g. timeout/cancellation).
            parts = [ResultStatus(False, False, kind="process_status_unknown", process=True)]
        elif value.get("type") in {"text", "output_text"} and isinstance(value.get("text"), str):
            parts = result_status_parts(value["text"])
        elif isinstance(value.get("content"), list):
            parts = result_status_parts(value["content"])
        else:
            parts = [ResultStatus(True, not failed)]
        if failed:
            # Preserve incompletion while preventing an inner exit-0 or generic
            # wrapper success from overriding an explicit provider error.
            parts = [ResultStatus(p.completed, False, p.session_id, "provider_error", p.process) for p in parts]
        return parts
    if value is None:
        return [ResultStatus(False, False, kind="missing_output")]
    return [ResultStatus(True, True)]


def codex_result_statuses(record: dict):
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    if record.get("type") != "response_item" or payload.get("type") not in {"function_call_output", "custom_tool_call_output"}:
        return []
    call_id = str(payload.get("call_id") or payload.get("id") or "")
    if not call_id:
        return []
    return [(call_id, result_status_parts(payload.get("output")))]


def codex_tool_result(record: dict):
    """Compatibility API only; use EpisodeToolState for completion and polling."""
    return [(call_id, all(p.completed and p.succeeded for p in parts))
            for call_id, parts in codex_result_statuses(record)]


def _poll_session(name, raw_input):
    leaf = name.lower().split(".")[-1].split("__")[-1]
    if leaf not in {"write_stdin", "wait"}:
        return None
    value = raw_input
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return None
    if not isinstance(value, dict):
        return None
    if leaf == "write_stdin":
        return _session(value.get("session_id"))
    cell = _session(value.get("cell_id"))
    return "cell:" + cell if cell is not None else None


def _is_poll_name(name):
    return name.lower().split(".")[-1].split("__")[-1] in {"write_stdin", "wait"}


class EpisodeToolState:
    """Call/result association bounded to one source episode and its cutoff.

    Call list/order remain intact. Polls are administrative, while a matched
    terminal result updates the original process invocation exactly once.
    No process session is linked across episodes or ambiguous session owners.
    """
    def __init__(self, calls: list[dict]):
        self.calls = calls
        self.by_id = {}
        self.sessions = {}
        self.metadata = {}
        self.diagnostics = Counter()

    def add_call(self, call_id, name, raw_input, provider="codex_rollout"):
        target = target_identity(raw_input)
        polling = _poll_session(name, raw_input) if provider == "codex_rollout" else None
        is_poll = provider == "codex_rollout" and _is_poll_name(name)
        call = {"order": len(self.calls) + 1, "name": name,
                "class": "administrative" if is_poll else classify_tool(name, raw_input),
                "completed": False, "succeeded": False,
                "target_ref": token("TGT", target) if target else ""}
        self.calls.append(call)
        self.metadata[id(call)] = {"parts": [], "poll_session": polling, "is_poll": is_poll, "sticky_failure": False}
        if call_id:
            if provider.startswith("claude"):
                self.by_id[call_id] = call
                return call
            if call_id in self.by_id:
                # Provider IDs are expected unique within an episode. Refuse
                # to let duplicate IDs complete an arbitrarily chosen call.
                self.by_id[call_id] = None
                self.diagnostics["duplicate_call_ids"] += 1
            else:
                self.by_id[call_id] = call
        if is_poll:
            self.diagnostics["poll_calls_administrative"] += 1
        return call

    def _refresh(self, call):
        meta = self.metadata[id(call)]
        parts = meta["parts"]
        meta["sticky_failure"] |= any(p.completed and not p.succeeded for p in parts)
        call["completed"] = bool(parts) and all(p.completed for p in parts)
        call["succeeded"] = call["completed"] and not meta["sticky_failure"] and all(p.succeeded for p in parts)

    def _register_sessions(self, call):
        for index, part in enumerate(self.metadata[id(call)]["parts"]):
            if part.session_id is None or part.completed:
                continue
            owner = (call, index)
            prior = self.sessions.get(part.session_id)
            if part.session_id not in self.sessions or (prior is not None and prior[0] is call and prior[1] == index):
                self.sessions[part.session_id] = owner
            else:
                self.sessions[part.session_id] = None
                self.diagnostics["ambiguous_session_ids"] += 1

    def apply_parts(self, call_id, parts):
        call = self.by_id.get(call_id)
        if call is None:
            self.diagnostics["unmatched_or_ambiguous_results"] += 1
            return
        meta = self.metadata[id(call)]
        known_pending = [p for p in meta["parts"] if p.process and not p.completed]
        if known_pending and not any(p.process for p in parts):
            # Receipt of a subsequent generic acknowledgment is not evidence
            # that an already-known running process/cell reached completion.
            self.diagnostics["generic_ack_preserved_pending_status"] += 1
            return
        pending_sessions = {p.session_id for p in known_pending if p.session_id is not None}
        incoming_sessions = {p.session_id for p in parts if p.process and p.session_id is not None}
        if (pending_sessions and not any(s.startswith("cell:") for s in pending_sessions)
                and incoming_sessions and not incoming_sessions.issubset(pending_sessions)):
            self.diagnostics["conflicting_same_call_session_preserved_pending"] += 1
            return
        meta["parts"] = list(parts)
        self._refresh(call)
        poll_session = meta["poll_session"]
        if not meta["is_poll"]:
            self._register_sessions(call)
            return
        if poll_session is None:
            self.diagnostics["unlinked_poll_results"] += 1
            return
        owner = self.sessions.get(poll_session)
        if owner is None:
            self.diagnostics["unlinked_poll_results"] += 1
            return
        # Exactly one process part must be attributable to this poll. Never
        # mix success from one response/session with another process's status.
        process_parts = [p for p in parts if p.process]
        cell_poll = poll_session.startswith("cell:")
        if not cell_poll and (len(process_parts) != 1 or any(p.session_id is not None and p.session_id != poll_session for p in process_parts)):
            self.diagnostics["unresolved_poll_status"] += 1
            return
        origin, index = owner
        origin_meta = self.metadata[id(origin)]
        if index >= len(origin_meta["parts"]) or origin_meta["parts"][index].session_id != poll_session:
            self.diagnostics["stale_poll_owner"] += 1
            return
        if cell_poll:
            # Cell completion may yield several nested process envelopes.
            # Replace the cell placeholder with those components and register
            # their sessions; do not infer that the script's success is theirs.
            if any(p.kind == "script_running" and p.session_id != poll_session for p in parts):
                self.diagnostics["unresolved_poll_status"] += 1
                return
            if not any(p.process for p in parts):
                self.diagnostics["unresolved_poll_status"] += 1
                return
            for session, registered in list(self.sessions.items()):
                if registered is not None and registered[0] is origin:
                    del self.sessions[session]
            origin_meta["parts"][index:index + 1] = parts
            self._refresh(origin)
            self._register_sessions(origin)
            self.diagnostics["linked_poll_results"] += 1
            return
        part = process_parts[0]
        # Any explicit error in a wrapper is also a failure for the origin.
        succeeded = part.succeeded and all(p.succeeded for p in parts if p.completed)
        origin_meta["parts"][index] = ResultStatus(part.completed, succeeded, poll_session, part.kind, True)
        self._refresh(origin)
        self.diagnostics["linked_poll_results"] += 1

    def apply_record(self, record, provider):
        if provider.startswith("claude"):
            for call_id, succeeded in claude_tool_result(record):
                call = self.by_id.get(call_id)
                if call is not None:
                    call["completed"] = True
                    call["succeeded"] = succeeded
        else:
            for call_id, parts in codex_result_statuses(record):
                self.apply_parts(call_id, parts)


def tool_input_text(value) -> str:
    if isinstance(value, str):
        return value
    try:
        return compact_json(value)
    except Exception:
        return str(value)


def extract_tool_calls(record: dict, provider: str):
    calls = []
    if provider in {"claude_audit", "claude_home", "claude_embedded"}:
        if record.get("type") != "assistant":
            return calls
        message = record.get("message") if isinstance(record.get("message"), dict) else {}
        for item in message.get("content") if isinstance(message.get("content"), list) else []:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                calls.append((str(item.get("id") or ""), str(item.get("name") or "unknown"), item.get("input") or {}))
    elif provider == "codex_rollout":
        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        if record.get("type") == "response_item" and payload.get("type") in {"function_call", "custom_tool_call"}:
            calls.append((str(payload.get("call_id") or payload.get("id") or ""),
                          str(payload.get("name") or "unknown"), payload.get("arguments") or payload.get("input") or {}))
    return calls


def assistant_text(record: dict, provider: str) -> list[str]:
    if provider in {"claude_audit", "claude_home", "claude_embedded"}:
        if record.get("type") != "assistant":
            return []
        message = record.get("message") if isinstance(record.get("message"), dict) else {}
        return content_text(message.get("content"), accepted=("text",))
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    if record.get("type") == "response_item" and payload.get("type") == "message" and payload.get("role") == "assistant":
        return content_text(payload.get("content"), accepted=("output_text", "text"))
    return []


def target_identity(raw_input) -> str:
    value = raw_input
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            return value[:4000]
    if isinstance(value, dict):
        for key in ("file_path", "path", "directory", "cwd", "notebook_path", "ref_id", "url", "query", "pattern", "cmd", "command"):
            if isinstance(value.get(key), str) and value[key].strip():
                return value[key].strip()[:4000]
    return tool_input_text(raw_input)[:4000]


READ_ONLY_COMMAND = re.compile(r"^(?:cd\s+\S+\s*(?:&&|;|$)\s*)?(?:rg|grep|sed\s+-n|head|tail|ls|find|git\s+(?:status|diff|log|show|rev-parse|branch)|wc|stat|du|file|jq|pwd|which|type|mdls)\b", re.I)
SEARCH_COMMAND = re.compile(r"\b(?:rg|grep|find)\b", re.I)
MUTATION_COMMAND = re.compile(r"\b(?:apply_patch|mkdir|touch|chmod|cp|mv|rm|git\s+(?:add|commit|push)|npm\s+install|pip\s+install)\b|(?:^|\s)(?:>>?|tee)\s", re.I)
VERIFY_COMMAND = re.compile(r"\b(?:pytest|npm\s+(?:test|run\s+(?:test|build|lint))|pnpm\s+(?:test|run)|yarn\s+(?:test|run)|go\s+test|cargo\s+test|tsc|validate|replay|check)\b", re.I)


def is_todo_write_tool(name: str) -> bool:
    """Closed administrative name family; never a file/command-content match.

    Only the final provider-name component is inspected. Case and underscore/
    hyphen variants are equivalent; Write targeting TODO.md is unchanged.
    """
    leaf = re.split(r"__|::|[./]", name.strip().casefold())[-1]
    return re.sub(r"[_-]", "", leaf) == "todowrite"


def classify_tool(name: str, raw_input) -> str:
    if is_todo_write_tool(name):
        return "administrative"
    return classify_tool_before_v5(name, raw_input)


def classify_tool_before_v5(name: str, raw_input) -> str:
    """Preserved pre-v5 taxonomy, solely for pinned source replay comparison."""
    key = name.lower()
    serialized = tool_input_text(raw_input)
    if any(term in key for term in ("taskupdate", "taskcreate", "update_plan", "request_user_input", "askuser", "wait", "list_agents", "send_message", "present_files", "toolsearch")):
        return "administrative"
    if any(term in key for term in ("agent", "spawn", "delegate", "followup_task")):
        return "delegate"
    if any(term in key for term in ("edit", "write", "create", "apply_patch", "notebookedit", "imagegen")):
        return "modify"
    if any(term in key for term in ("test", "validate", "lint", "verify")):
        return "verify"
    if any(term in key for term in ("grep", "glob", "search", "find")):
        return "search"
    if any(term in key for term in ("read", "open", "fetch", "view_image", "screenshot")):
        return "retrieve"
    if any(term in key for term in ("bash", "terminal", "exec", "shell", "javascript", "js")):
        if MUTATION_COMMAND.search(serialized) or "apply_patch" in serialized:
            return "modify"
        if VERIFY_COMMAND.search(serialized):
            return "verify"
        command = target_identity(raw_input).strip()
        if READ_ONLY_COMMAND.search(command):
            return "search" if SEARCH_COMMAND.search(command) else "retrieve"
        return "execute"
    if any(term in key for term in ("click", "navigate", "type", "browser", "deploy", "publish")):
        return "execute"
    return "other"


def subagent_source(record: dict, provider: str) -> bool:
    if provider != "codex_rollout" or record.get("type") != "session_meta":
        return False
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    source = payload.get("source")
    return isinstance(source, dict) and "subagent" in source


def notification_boundary(prompt: str, native_origin: str = "") -> dict:
    """Identify complete machine envelopes, never SDK use or keywords alone.

    Keep the raw prompt unchanged. A wrapper followed by a separate instruction
    is not classified solely from its prefix. Native machine origin is stronger
    than user-role serialization, but does not authenticate any human identity.
    """
    text = prompt.strip()
    if native_origin.casefold() == "human":
        return {}
    whole = re.fullmatch(r"<task-notification(?:\s[^>]*)?>\s*(.*?)\s*</task-notification>", text, re.S | re.I)
    native = native_origin.casefold() == "task-notification"
    if not (whole or native):
        return {}
    identifiers = sorted(set(re.findall(r"<tool-use-id>\s*([^<>\s]+)\s*</tool-use-id>", text, re.I)))
    return {"kind": "machine_task_notification", "native_origin": native_origin,
            "complete_wrapper": bool(whole), "tool_ids": identifiers}


def bare_continuation(prompt: str, config: dict) -> bool:
    """Closed acknowledgment grammar; any additional task content stays fresh.

    This is a deterministic boundary candidate, not semantic intent inference.
    The event normalizer separately requires a unique supported owner.
    """
    return any(re.fullmatch(pattern, prompt.strip(), re.I)
               for pattern in config["continuation_only"])


def artifact_references(prompt: str) -> set[str]:
    # XML element syntax is not an artifact path. Contents such as an actual
    # <file_path>/supplied/spec.md</file_path> remain visible to the rule.
    def attribute_values(match):
        # Artifact-bearing values remain evidence; XML names and closing-tag
        # slashes are syntax. Attribute names never count as paths themselves.
        return " " + " ".join(m.group(2) for m in re.finditer(r'''[A-Za-z_:][\w.:-]*\s*=\s*(["'])(.*?)\1''', match.group(0), re.S)) + " "
    without_tags = re.sub(r"</?[A-Za-z][A-Za-z0-9_.:-]*(?:\s[^<>]*?)?/?>", attribute_values, prompt)
    refs = set(re.findall(r'''(?<!\w)(?:[./~][^\s,;:()<>\[\]{}"']+|[A-Za-z0-9_.-]+\.(?:md|txt|json|ya?ml|csv|tsv|py|mjs|js|ts|tsx|jsx|html|css|docx|pdf|pptx|xlsx|zip))(?!\w)''', without_tags, re.I))
    # Bare dot-numbers are numeric cues, not artifact cues. Qualified paths,
    # URLs, dotfiles and filenames with an extension remain references.
    return {ref for ref in refs if not re.fullmatch(r"\.\d+(?:[eE][+-]?\d+)?%?[.!?]*", ref)}


def stage_request_text(prompt: str) -> str:
    """Remove only mechanically identifiable inert Git message arguments.

    Quotes and code fences are not generally discarded: they can express real
    requests. For an actual Git commit/tag command, -m/--message values are data
    to write, not a request to perform activities named in that value. Other
    commands, including verification commands, and quoted prose remain intact.
    This narrow lexical correction is not a general semantic stage classifier.
    """
    output = []
    for line in prompt.splitlines():
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|")
            lexer.whitespace_split = True
            lexer.commenters = ""
            tokens = list(lexer)
        except ValueError:
            output.append(line)
            continue
        pieces, chunk = [], []
        for value in tokens + [None]:
            if value is None or value in {";", "&&", "||", "|"}:
                pieces.append(chunk)
                if value is not None:
                    pieces.append([value])
                chunk = []
            else:
                chunk.append(value)
        changed = False
        for part in pieces:
            if not part:
                continue
            offset = 1 if part[0] == "$" else 0
            if len(part) <= offset or part[offset].rsplit("/", 1)[-1] != "git":
                continue
            i = offset + 1
            # Git's common global options have argument values before subcommand.
            while i < len(part) and part[i].startswith("-"):
                if part[i] in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}:
                    i += 2
                else:
                    i += 1
            if i >= len(part) or part[i] not in {"commit", "tag"}:
                continue
            j = i + 1
            while j < len(part):
                if part[j] == "--":
                    break
                short_message = re.fullmatch(r"-([aqsv]*)m(.*)", part[j]) if not part[j].startswith("--") else None
                # Short options before m must be known no-argument switches;
                # e.g. -am is a message option, but -C/path is not.
                if (part[j] in {"-m", "--message"} or (short_message and not short_message.group(2))) and j + 1 < len(part):
                    part[j + 1] = "INERT_MESSAGE_VALUE"
                    changed = True
                    j += 2
                elif part[j].startswith("--message=") or (short_message and short_message.group(2)):
                    part[j] = "INERT_MESSAGE_OPTION"
                    changed = True
                    j += 1
                else:
                    j += 1
        output.append(" ".join(x for part in pieces for x in part) if changed else line)
    return "\n".join(output)


def episode_classification(ep: dict, config: dict, stage_groups: dict, context_groups: dict,
                           publication_regexes: list[re.Pattern], product_regexes: list[re.Pattern],
                           non_product_regexes: list[re.Pattern], continuation_regexes: list[re.Pattern],
                           continuation_wrapper_regexes: list[re.Pattern], delegated_regexes: list[re.Pattern],
                           tool_generated_regexes: list[re.Pattern]):
    prompt = ep["prompt_text"]
    stages, stage_count = matched_groups(stage_request_text(prompt), stage_groups)
    modes, explicit_context_count = matched_groups(prompt, context_groups)
    path_refs = artifact_references(prompt)
    if len(path_refs) >= 2:
        if "bounded_package" not in modes:
            modes.append("bounded_package")
        explicit_context_count += 1
    if len(path_refs) >= 3 and "multi_source_synthesis" not in modes:
        modes.append("multi_source_synthesis")
        explicit_context_count += 1
    publication = matching_count(prompt, publication_regexes) > 0
    explicit_non_product = matching_count(prompt, non_product_regexes) > 0
    continuation = ep['attachment_count'] == 0 and any(regex.fullmatch(prompt.strip()) for regex in continuation_regexes)
    continuation_wrapper = any(regex.search(prompt.strip()) for regex in continuation_wrapper_regexes)
    delegated_prompt = any(regex.search(prompt.strip()) for regex in delegated_regexes)
    tool_generated_prompt = bool(notification_boundary(prompt, ep.get("native_origin", ""))) or any(regex.search(prompt.strip()) for regex in tool_generated_regexes)
    scheduled_automation = (prompt.lstrip().startswith("<scheduled-task") or
                            prompt.lstrip().lower().startswith("automation:") or
                            "this is an automated run of a scheduled task" in prompt.lower())
    if continuation_wrapper:
        origin_candidate = "continuation_wrapper"
    elif tool_generated_prompt:
        origin_candidate = "tool_generated"
    elif delegated_prompt:
        origin_candidate = "delegated_agent_prompt_candidate"
    elif scheduled_automation:
        origin_candidate = "scheduled_automation"
    else:
        origin_candidate = "direct_or_unresolved_user_level"
    product_signal_count = matching_count(prompt, product_regexes) + stage_count

    calls = ep["calls"]
    completed = [call for call in calls if call["completed"] and call["succeeded"]]
    substantive_classes = {"modify", "execute", "verify"}
    first_substantive = min((call["order"] for call in completed if call["class"] in substantive_classes), default=10**9)
    context_before = [call for call in completed if call["class"] in {"retrieve", "search"} and call["order"] < first_substantive]
    context_any = [call for call in completed if call["class"] in {"retrieve", "search"}]
    distinct_context_targets = {call["target_ref"] for call in context_before if call["target_ref"]}
    completed_substantive = [call for call in completed if call["class"] in substantive_classes]
    decision_stage = any(stage in {"requirements", "design", "audit", "verification"} for stage in stages)
    decision_trace = (decision_stage and bool(context_any) and
                      ep["assistant_output_chars"] >= safe_int(config["minimum_assistant_output_chars_for_decision"], 100))
    product_action = bool(completed_substantive) or decision_trace
    product_purpose = product_signal_count > 0 or bool(completed_substantive)
    implicit_context = len(distinct_context_targets) >= safe_int(config["minimum_distinct_retrieval_targets_for_implicit_context"], 2)
    attachment_context = ep["attachment_count"] > 0
    explicit_context = explicit_context_count > 0
    context_operation = explicit_context or implicit_context or attachment_context
    history_trace = "history_memory" in modes and not continuation
    observed_context_trace = ((explicit_context and (bool(context_before) or attachment_context or history_trace)) or
                              (implicit_context and product_action))
    if observed_context_trace and product_action:
        context_trace_status = "context_supplied_then_product_action_observed"
    elif context_operation and product_action:
        context_trace_status = "context_signal_and_action_without_ordered_use_trace"
    elif context_operation:
        context_trace_status = "context_signal_without_product_action"
    elif product_action:
        context_trace_status = "product_action_without_context_operation"
    else:
        context_trace_status = "neither_context_nor_product_action_observed"

    if continuation_wrapper:
        disposition = "exclude_continuation_wrapper"
        basis = "assistant-generated context restoration or compaction summary is not a fresh user-level interaction"
    elif tool_generated_prompt:
        disposition = "exclude_tool_generated_prompt"
        basis = "tool-generated delivery or result text is not a user-authored task invocation"
    elif delegated_prompt:
        disposition = "exclude_delegated_prompt_candidate"
        basis = "delegated-agent task prompts are evidence within a parent run, not independent user-level interactions"
    elif publication:
        disposition = "exclude_publication_candidate"
        basis = "publication-purpose language is categorically outside the product-event boundary"
    elif explicit_non_product:
        disposition = "exclude_non_product_candidate"
        basis = "business-development, sales, or marketing task language is outside the product-event boundary"
    elif continuation:
        disposition = "exclude_continuation_only"
        basis = "boilerplate continuation supplied no fresh context operation"
    elif not product_purpose:
        disposition = "exclude_non_product_candidate"
        basis = "no product-purpose signal or completed substantive product action"
    elif not product_action:
        disposition = "exclude_no_observable_product_action"
        basis = "context or task language was present but no completed product action or grounded decision was observed"
    elif not context_operation:
        disposition = "exclude_no_context_operation"
        basis = "product work was observed but no deliberate or multi-source context operation was evidenced"
    elif observed_context_trace:
        disposition = "candidate_strong"
        basis = "context operation and ordered downstream product-use trace were both observed"
    else:
        disposition = "candidate_probable"
        basis = "context operation and product action co-occurred but ordered use was not directly observed"

    counts = Counter(call["class"] for call in calls)
    completed_counts = Counter(call["class"] for call in completed)
    return {
        "stage_signal_mask": "|".join(stages), "stage_signal_count": stage_count,
        "context_mode_mask": "|".join(modes), "explicit_context_signal_count": explicit_context_count,
        "prompt_artifact_reference_count": len(path_refs), "product_signal_count": product_signal_count,
        "publication_exclusion_candidate": yes(publication), "continuation_only_candidate": yes(continuation),
        "origin_candidate": origin_candidate,
        "completed_tool_calls": len(completed), "context_retrieval_calls": counts["retrieve"] + counts["search"],
        "completed_context_retrieval_calls": completed_counts["retrieve"] + completed_counts["search"],
        "context_retrieval_calls_before_action": len(context_before),
        "distinct_context_targets_before_action": len(distinct_context_targets),
        "substantive_action_calls": counts["modify"] + counts["execute"] + counts["verify"],
        "completed_substantive_action_calls": len(completed_substantive),
        "mutation_calls": counts["modify"], "execution_calls": counts["execute"],
        "verification_calls": counts["verify"], "delegate_calls": counts["delegate"],
        "grounded_decision_trace": yes(decision_trace), "context_trace_status": context_trace_status,
        "product_action_trace_status": "observed" if product_action else "not_observed",
        "automated_disposition": disposition, "disposition_basis": basis,
    }


PUBLIC_HEADER = [
    "episode_id", "station_id", "provider", "source_ref", "session_ref", "turn_index",
    "source_line_start", "source_line_end", "timestamp_start_utc", "timestamp_end_utc", "timestamp_status",
    "prompt_ref", "prompt_chars", "prompt_words", "attachment_count", "tool_calls", "completed_tool_calls",
    "context_retrieval_calls", "completed_context_retrieval_calls", "context_retrieval_calls_before_action",
    "distinct_context_targets_before_action", "substantive_action_calls", "completed_substantive_action_calls",
    "mutation_calls", "execution_calls", "verification_calls", "delegate_calls", "assistant_output_blocks",
    "assistant_output_chars", "stage_signal_mask", "stage_signal_count", "context_mode_mask",
    "explicit_context_signal_count", "prompt_artifact_reference_count", "product_signal_count",
    "publication_exclusion_candidate", "continuation_only_candidate", "origin_candidate", "prompt_reuse_count",
    "grounded_decision_trace",
    "context_trace_status", "product_action_trace_status", "automated_disposition", "disposition_basis",
    "candidate_case_ids", "case_scope_status", "rule_version", "cutoff_id", "review_status"
]


REVIEW_HEADER = [
    "context_review_id", "episode_id", "station_id", "provider", "source_ref", "session_ref", "prompt_ref",
    "timestamp_start_utc", "candidate_case_ids", "case_scope_status", "automated_disposition",
    "context_mode_mask", "stage_signal_mask", "context_trace_status", "product_action_trace_status",
    "origin_candidate", "prompt_reuse_count",
    "review_priority", "reviewer_1_id", "reviewer_1_context_engineering_decision",
    "reviewer_1_product_purpose_decision", "reviewer_1_context_operation", "reviewer_1_context_use_trace",
    "reviewer_1_observable_action", "reviewer_1_primary_context_mode", "reviewer_1_notes",
    "reviewer_2_id", "reviewer_2_context_engineering_decision", "reviewer_2_product_purpose_decision",
    "reviewer_2_context_operation", "reviewer_2_context_use_trace", "reviewer_2_observable_action",
    "reviewer_2_primary_context_mode", "reviewer_2_notes", "adjudicator_id",
    "adjudicated_context_engineering_decision", "adjudicated_primary_context_mode", "agreement_status", "review_status"
]


def row_values(header: list[str], row: dict):
    return [row.get(name, "") for name in header]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--rules", default="config/context-engineering-eligibility.json")
    parser.add_argument("--episodes-out", default=".private/multistation_context_episode_screen.local.csv")
    parser.add_argument("--review-out", default="data/adjudication/multistation_context_episode_review_20260812.csv")
    parser.add_argument("--summary-out", default="data/processed/multistation_context_screen_summary_20260812.csv")
    parser.add_argument("--run-out", default="data/receipts/multistation_context_screen_run_20260812.csv")
    parser.add_argument("--private-out", default=".private/multistation_context_episode_review.local.csv")
    args = parser.parse_args()
    root = Path.cwd()
    run_config = json.loads((root / args.config).read_text())
    rules = json.loads((root / args.rules).read_text())
    # Routing expressions remain frozen; version only the corrected adapter.
    rules["rule_version"] = rules["rule_version"] + ";" + ADAPTER_VERSION
    cutoff = json.loads((root / "config/study-cutoff.json").read_text())
    if rules["cutoff_id"] != cutoff["cutoff_id"]:
        raise RuntimeError("eligibility rules and study cutoff disagree")
    cutoff_millis = __import__("datetime").datetime.fromisoformat(cutoff["snapshot_observed_at_utc"].replace("Z", "+00:00")).timestamp()
    stage_groups = compile_groups(rules, "stages")
    context_groups = compile_groups(rules, "context_modes")
    publication_regexes = [re.compile(x, re.I) for x in rules["publication_exclusions"]]
    product_regexes = [re.compile(x, re.I) for x in rules["product_signals"]]
    continuation_regexes = [re.compile(x, re.I) for x in rules["continuation_only"]]
    nonhuman_prefixes = rules["nonhuman_block_prefixes"]
    non_product_regexes = [re.compile(x, re.I) for x in rules["non_product_exclusions"]]
    continuation_wrapper_regexes = [re.compile(x, re.I) for x in rules["continuation_wrappers"]]
    delegated_regexes = [re.compile(x, re.I) for x in rules["delegated_prompt_candidates"]]
    tool_generated_regexes = [re.compile(x, re.I) for x in rules["tool_generated_prompts"]]

    output_paths = [root / args.episodes_out, root / args.review_out, root / args.summary_out,
                    root / args.run_out, root / args.private_out]
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    work_paths = {path: path.with_name(path.name + ".tmp") for path in output_paths}
    episodes_file = work_paths[root / args.episodes_out].open("w", encoding="utf-8", newline="")
    private_file = work_paths[root / args.private_out].open("w", encoding="utf-8", newline="")
    episodes_writer = csv.writer(episodes_file, lineterminator="\n")
    private_writer = csv.writer(private_file, lineterminator="\n")
    episodes_writer.writerow(PUBLIC_HEADER)
    private_writer.writerow(PUBLIC_HEADER + ["prompt_text", "tool_trace_json"])
    review_rows, summary, prompt_counts = [], Counter(), Counter()
    sources_summary = Counter()
    package_source_counts = {}

    def close_episode(ep, station: StationPackage, source: SourceSpec):
        if not ep:
            return
        classified = episode_classification(ep, rules, stage_groups, context_groups,
                                            publication_regexes, product_regexes, non_product_regexes,
                                            continuation_regexes, continuation_wrapper_regexes,
                                            delegated_regexes, tool_generated_regexes)
        prompt_digest = digest(ep["prompt_text"])
        public = {
            "episode_id": token("CEI", f"{source.canonical_ref}|{ep['turn_index']}|{prompt_digest}"),
            "station_id": station.station_id, "provider": source.provider,
            "source_ref": source.canonical_ref, "session_ref": source.canonical_ref.replace("SRC-", "SS-", 1),
            "turn_index": ep["turn_index"], "source_line_start": ep["line_start"], "source_line_end": ep["line_end"],
            "timestamp_start_utc": ep["timestamp_start"], "timestamp_end_utc": ep["timestamp_end"],
            "timestamp_status": "observed" if ep["timestamp_start"] else "missing",
            "prompt_ref": f"PR-{prompt_digest[:20]}", "prompt_chars": len(ep["prompt_text"]),
            "prompt_words": len(ep["prompt_text"].split()), "attachment_count": ep["attachment_count"],
            "tool_calls": len(ep["calls"]), "assistant_output_blocks": ep["assistant_output_blocks"],
            "assistant_output_chars": ep["assistant_output_chars"], "candidate_case_ids": "|".join(source.case_ids),
            "case_scope_status": "station_wide_unanchored" if source.case_ids == ["STATION-WIDE"] else "automated_source_membership_candidate",
            "rule_version": rules["rule_version"], "cutoff_id": rules["cutoff_id"], "review_status": "unreviewed",
            **classified,
        }
        prompt_counts[public["prompt_ref"]] += 1
        episodes_writer.writerow(row_values(PUBLIC_HEADER, public))
        trace = [{"order": call["order"], "name": call["name"], "class": call["class"],
                  "completed": call["completed"], "succeeded": call["succeeded"],
                  "target_ref": call["target_ref"]} for call in ep["calls"]]
        private_writer.writerow(row_values(PUBLIC_HEADER, public) + [ep["prompt_text"], compact_json(trace)])
        disposition = public["automated_disposition"]
        summary[(station.station_id, source.provider, disposition)] += 1
        summary[(station.station_id, "ALL", disposition)] += 1
        if disposition in {"candidate_strong", "candidate_probable"}:
            priority = "high" if disposition == "candidate_strong" else "moderate"
            review = {
                "context_review_id": token("CER", public["episode_id"]),
                **{key: public[key] for key in REVIEW_HEADER if key in public},
                "review_priority": priority, "review_status": "pending"
            }
            review_rows.append(review)

    for station_spec in run_config["stations"]:
        station = StationPackage(station_spec)
        try:
            sources = station.sources()
            package_source_counts[station.station_id] = len(sources)
            print(f"{station.station_id}: scanning {len(sources)} candidate interaction sources", flush=True)
            for source_index, source in enumerate(sources, 1):
                active = None
                turn_index = 0
                tool_state = None
                hasher = hashlib.sha256()
                source_is_subagent = False
                line_number = 0
                try:
                    with station.open_source(source.reported_ref) as raw:
                        for raw_line in raw:
                            hasher.update(raw_line)
                            line_number += 1
                            try:
                                record = json.loads(raw_line)
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                sources_summary[(station.station_id, "malformed_rows")] += 1
                                continue
                            if subagent_source(record, source.provider):
                                source_is_subagent = True
                                active = None
                            timestamp = timestamp_of(record)
                            if timestamp:
                                try:
                                    parsed = __import__("datetime").datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
                                    if parsed > cutoff_millis:
                                        sources_summary[(station.station_id, "timestamp_excluded_rows")] += 1
                                        continue
                                except ValueError:
                                    sources_summary[(station.station_id, "invalid_timestamp_rows")] += 1
                            if source_is_subagent:
                                continue
                            prompt = extract_human_prompt(record, source.provider, nonhuman_prefixes)
                            if prompt:
                                close_episode(active, station, source)
                                turn_index += 1
                                active = {
                                    "prompt_text": prompt[0], "attachment_count": prompt[1], "turn_index": turn_index,
                                    "line_start": line_number, "line_end": line_number, "timestamp_start": timestamp,
                                    "timestamp_end": timestamp, "calls": [], "assistant_output_blocks": 0,
                                    "assistant_output_chars": 0,
                                }
                                tool_state = EpisodeToolState(active["calls"])
                            if active is None:
                                continue
                            active["line_end"] = line_number
                            if timestamp:
                                active["timestamp_end"] = timestamp
                            tool_state.apply_record(record, source.provider)
                            for call_id, name, raw_input in extract_tool_calls(record, source.provider):
                                tool_state.add_call(call_id, name, raw_input, source.provider)
                            texts = assistant_text(record, source.provider)
                            active["assistant_output_blocks"] += len(texts)
                            active["assistant_output_chars"] += sum(len(text) for text in texts)
                    close_episode(active, station, source)
                except (FileNotFoundError, OSError, zipfile.BadZipFile) as exc:
                    sources_summary[(station.station_id, "unreadable_sources")] += 1
                    print(f"WARN {exc}", file=sys.stderr, flush=True)
                    continue
                actual_sha = hasher.hexdigest()
                if source.expected_sha256 and actual_sha != source.expected_sha256:
                    raise RuntimeError(f"{station.station_id}/{source.reported_ref}: source hash mismatch")
                sources_summary[(station.station_id, "sources_scanned")] += 1
                if source_is_subagent:
                    sources_summary[(station.station_id, "subagent_sources_excluded")] += 1
                if source_index % 250 == 0:
                    print(f"{station.station_id}: {source_index}/{len(sources)} sources", flush=True)
        finally:
            station.close()

    episodes_file.close()
    private_file.close()
    # Reuse is a clustering/non-independence flag, not an automatic exclusion. A
    # scheduled task can validly produce many runs from one engineered prompt.
    for path in (work_paths[root / args.episodes_out], work_paths[root / args.private_out]):
        csv.field_size_limit(sys.maxsize)
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames
            rows = list(reader)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                row["prompt_reuse_count"] = prompt_counts[row["prompt_ref"]]
                writer.writerow(row)
    for row in review_rows:
        row["prompt_reuse_count"] = prompt_counts[row["prompt_ref"]]
    review_rows.sort(key=lambda row: (0 if row["review_priority"] == "high" else 1, row["station_id"], row["episode_id"]))
    with work_paths[root / args.review_out].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(REVIEW_HEADER)
        for row in review_rows:
            writer.writerow(row_values(REVIEW_HEADER, row))

    summary_header = [
        "station_id", "provider", "automated_disposition", "episode_count", "human_qualified_count",
        "analytic_status", "rule_version", "cutoff_id"
    ]
    with work_paths[root / args.summary_out].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(summary_header)
        for (station_id, provider, disposition), count in sorted(summary.items()):
            writer.writerow([station_id, provider, disposition, count, 0,
                             "provisional_screen_human_adjudication_pending", rules["rule_version"], rules["cutoff_id"]])

    with work_paths[root / args.episodes_out].open(encoding="utf-8", newline="") as handle:
        public_rows = list(csv.DictReader(handle))
    run_header = [
        "run_id", "station_id", "package_candidate_sources", "sources_scanned",
        "sources_with_primary_episodes", "subagent_sources_excluded", "unreadable_sources",
        "prompt_episodes", "candidate_strong", "candidate_probable", "review_queue",
        "unique_candidate_prompt_refs", "human_qualified_count", "rule_version", "cutoff_id",
        "analytic_status", "limitations"
    ]
    with work_paths[root / args.run_out].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(run_header)
        for station_id in sorted(package_source_counts):
            station_rows = [row for row in public_rows if row["station_id"] == station_id]
            strong = sum(row["automated_disposition"] == "candidate_strong" for row in station_rows)
            probable = sum(row["automated_disposition"] == "candidate_probable" for row in station_rows)
            candidate_rows = [row for row in station_rows if row["automated_disposition"].startswith("candidate_")]
            unreadable = sources_summary[(station_id, "unreadable_sources")]
            limitation = ("One reconstructed manifest source is absent from the verified archive; station scope is unanchored."
                          if station_id == "ST02" and unreadable else
                          "Automated routing only; source-to-case membership and context-engineering eligibility require human review.")
            writer.writerow([
                "RUN-CE-POST-20260812-A", station_id, package_source_counts[station_id],
                sources_summary[(station_id, "sources_scanned")], len({row["source_ref"] for row in station_rows}),
                sources_summary[(station_id, "subagent_sources_excluded")], unreadable, len(station_rows),
                strong, probable, len(candidate_rows), len({row["prompt_ref"] for row in candidate_rows}), 0,
                rules["rule_version"], rules["cutoff_id"],
                "candidate_screen_complete_human_adjudication_pending", limitation
            ])

    for final_path, work_path in work_paths.items():
        os.replace(work_path, final_path)

    print(compact_json({
        "episodes": sum(count for (station, provider, disposition), count in summary.items() if provider == "ALL"),
        "review_queue": len(review_rows),
        "source_quality": {f"{station}|{metric}": count for (station, metric), count in sorted(sources_summary.items())},
        "dispositions": {f"{station}|{disposition}": count for (station, provider, disposition), count in sorted(summary.items()) if provider == "ALL"}
    }), flush=True)


if __name__ == "__main__":
    main()

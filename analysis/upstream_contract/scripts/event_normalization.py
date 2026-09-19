#!/usr/bin/env python3
"""Native-event normalization, with no source writes or empirical label inference.

This module is intentionally independent of a particular private filesystem.
The caller supplies pinned source descriptors, v2 rows, the preserved provider
completion adapter and versioned boundary/lexical corrections. All returned
locators are private.

Identity is stronger than wording: same-source UUID plus explicit replay, or
UUID/session/native timestamp/canonical user-message equality. A replay may
change transport paths; canonical prompt choice is independent of outcomes.
Tool IDs, parent UUIDs where provided, and audit nesting ownership determine
attribution. A missing parent UUID is not itself an exclusion. Disjoint work is
preserved. Contradictory native identities are held rather than resolved by
choosing successful work. Timing never uses unowned EOF records or clips a
negative interval to zero. No function executes logged commands.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import heapq
import json
from pathlib import Path
import re

VERSION = "ce-primary-boundary-normalization-v5.0.0-20260918"
CLAUDE = {"claude_audit", "claude_home", "claude_embedded"}
PROVIDERS = CLAUDE | {"codex_rollout"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(value):
    if not isinstance(value, bytes):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def seconds(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return None
        return dt.timestamp()
    except (ValueError, TypeError, OverflowError):
        return None


def normalized_time(value):
    # Preserve the supplied precision. Rounding an identity or endpoint to
    # milliseconds could merge distinct native records or change elapsed time.
    return str(value) if seconds(value) is not None else ""


def compact_record(record, source, line, screen):
    """Retain identity, classification inputs as hashes, and necessary measures.

    Prompt text stays in the v2 row. Tool inputs are classified by the unchanged
    adapter while in memory and are never executed. Raw content is not copied.
    Parent-link-only records are retained so attachment/progress nodes cannot
    accidentally sever a native parent chain.
    """
    message = record.get("message") if isinstance(record.get("message"), dict) else {}
    if source["provider"] == "codex_rollout" and record.get("type") == "response_item":
        payload = record.get("payload", {})
        if payload.get("type") == "message":
            message = payload
    content = message.get("content")
    uid = str(record.get("uuid") or "")
    parent = str(record.get("parentUuid") or "")
    calls = []
    for index, (call_id, name, raw_input) in enumerate(screen.extract_tool_calls(record, source["provider"])):
        target = screen.target_identity(raw_input)
        calls.append({"id": call_id, "name": name, "input_sha256": sha(canonical(raw_input)),
                      "class": screen.classify_tool(name, raw_input),
                      "target_ref": screen.token("TGT", target) if target else "", "index": index,
                      "poll_session": screen._poll_session(name, raw_input) if source["provider"] == "codex_rollout" else None,
                      "is_poll": source["provider"] == "codex_rollout" and screen._is_poll_name(name)})
    results = []
    if record.get("type") == "user" and isinstance(content, list):
        for index, item in enumerate(content):
            if isinstance(item, dict) and item.get("type") == "tool_result" and item.get("tool_use_id"):
                results.append({"id": str(item["tool_use_id"]), "succeeded": not bool(item.get("is_error")),
                                "payload_sha256": sha(canonical(item)), "index": index})
    if source["provider"] == "codex_rollout":
        for index, (call_id, parts) in enumerate(screen.codex_result_statuses(record)):
            results.append({"id": str(call_id), "completed": bool(parts) and all(p.completed for p in parts),
                            "succeeded": bool(parts) and all(p.completed and p.succeeded for p in parts),
                            "status_parts": [vars(p) for p in parts],
                            "payload_sha256": sha(canonical(record.get("payload", {}))), "index": index})
    texts = [{"sha256": sha(text), "chars": len(text), "index": i}
             for i, text in enumerate(screen.assistant_text(record, source["provider"]))]
    kind = str(record.get("type") or "")
    if source["provider"] == "codex_rollout" and (calls or texts):
        kind = "assistant"
    native_origin = record.get("origin") if isinstance(record.get("origin"), dict) else {}
    prompt = screen.extract_human_prompt(record, source["provider"], [])
    boundary = screen.notification_boundary(prompt[0], str(native_origin.get("kind") or "")) if prompt else {}
    return {
        "key": source["source_ref"] + ":" + str(line), "source_ref": source["source_ref"],
        "station_id": source["station_id"], "provider": source["provider"], "line": line,
        "uuid": uid, "parent": parent, "has_parent": "parentUuid" in record,
        "owner": str(record.get("parent_tool_use_id") or ""),
        "session": str(record.get("sessionId") or record.get("session_id") or ""),
        "native_time": str(record.get("timestamp") or ""),
        "audit_time": str(record.get("_audit_timestamp") or ""),
        "kind": kind, "role": str(message.get("role") or ""),
        "native_origin": str(native_origin.get("kind") or ""),
        "prompt_source": str(record.get("promptSource") or ""), "notification_boundary": boundary,
        "replay": record.get("isReplay") is True, "sidechain": record.get("isSidechain") is True,
        "message_sha256": sha(canonical(message)) if message else "",
        "content_sha256": sha(canonical(content)) if content is not None else "",
        "calls": calls, "results": results, "texts": texts,
    }


def extract_source(source, rows, screen, rules, cutoff_seconds):
    """Freshly hash a complete source and recover every frozen accepted anchor.

    No new prompt is admitted. The unchanged extractor must reproduce every
    accepted line and text/attachment value before normalization is attempted.
    All causal connector records are retained, including zero-episode sources.
    """
    path = Path(source["path"])
    before = path.stat()
    expected = {int(r["source_line_start"]): r for r in rows}
    if len(expected) != len(rows):
        raise ValueError("Duplicate frozen anchor line")
    records, anchors = [], []
    h = hashlib.sha256()
    size, count = 0, 0
    census = Counter()
    active = ""
    codex_states, codex_pairs, codex_baseline_classes = {}, [], {}
    tool_state = None
    with path.open("rb") as handle:
        for line, raw in enumerate(handle, 1):
            count = line
            h.update(raw)
            size += len(raw)
            try:
                record = json.loads(raw)
            except (ValueError, UnicodeError):
                census["malformed_records"] += 1
                continue
            if not isinstance(record, dict):
                census["nonobject_records"] += 1
                continue
            t = seconds(screen.timestamp_of(record))
            if t is not None and t > cutoff_seconds:
                census["post_cutoff_records"] += 1
                continue
            prompt = screen.extract_human_prompt(record, source["provider"], rules["nonhuman_block_prefixes"])
            if prompt:
                if line not in expected:
                    raise ValueError("Fresh accepted anchor absent from pinned scope")
                old = expected[line]
                if prompt[0] != old["prompt_text"] or str(prompt[1]) != old["attachment_count"]:
                    raise ValueError("Pinned prompt/attachment extraction changed")
                active = old["episode_id"]
                if source["provider"] == "codex_rollout":
                    state_calls = []
                    tool_state = screen.EpisodeToolState(state_calls)
                    codex_states[active] = state_calls
            r = compact_record(record, source, line, screen)
            if source["provider"] == "codex_rollout" and tool_state is not None:
                for compact, (cid, name, raw_input) in zip(r["calls"], screen.extract_tool_calls(record, source["provider"])):
                    state_call = tool_state.add_call(cid, name, raw_input)
                    # Preserve the complete pre-correction equality guard while
                    # allowing this declared taxonomy revision in current calls.
                    codex_baseline_classes[id(state_call)] = ("administrative" if screen._is_poll_name(name)
                        else screen.classify_tool_before_v5(name, raw_input))
                    codex_pairs.append((compact, state_call))
                tool_state.apply_record(record, source["provider"])
            r["old_interval"] = active
            if prompt:
                r["accepted_episode_id"] = active
                anchors.append({"old_episode_id": active, "anchor": r,
                                "prompt_sha256": sha(prompt[0]), "attachment_count": prompt[1]})
            # UUID-only connector records matter for parent ancestry. Records
            # without either identity or relevant content need not be duplicated.
            if r["uuid"] or r["parent"] or r["calls"] or r["results"] or r["texts"] or prompt:
                records.append(r)
            census["json_records"] += 1
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        # Cloud hydration can round nanosecond metadata without changing bytes.
        # Do not waive the guard: require a second complete pinned hash and a
        # stable stat during that read, and record the extra verification.
        second = hashlib.sha256()
        with path.open('rb') as stable_handle:
            for block in iter(lambda: stable_handle.read(1048576), b''):
                second.update(block)
        stable = path.stat()
        if ((h.hexdigest(), size) != (source['sha256'], source['bytes']) or
                second.hexdigest() != source['sha256'] or
                (after.st_size, after.st_mtime_ns) != (stable.st_size, stable.st_mtime_ns)):
            raise ValueError(f"Source changed during read: {source['source_ref']} {path}")
        census['metadata_stat_change_verified_by_second_full_hash'] += 1
    if (h.hexdigest(), size) != (source["sha256"], source["bytes"]):
        raise ValueError(f"Pinned source hash/size mismatch: {source['source_ref']} {path}")
    if {a["old_episode_id"] for a in anchors} != {r["episode_id"] for r in rows}:
        raise ValueError("Incomplete accepted-anchor recovery")
    for compact, state_call in codex_pairs:
        compact.update({k: state_call[k] for k in ("class", "completed", "succeeded")})
    for old in rows if source["provider"] == "codex_rollout" else []:
        keys = ("order", "name", "class", "completed", "succeeded", "target_ref")
        actual = [{**{k: c[k] for k in keys}, "class": codex_baseline_classes[id(c)]}
                  for c in codex_states[old["episode_id"]]]
        if actual != json.loads(old["tool_trace_json"]):
            raise ValueError("Pinned Codex completion trace did not reproduce before boundary correction")
    return {"source": dict(source), "physical_lines": count, "anchors": anchors,
            "records": records, "census": dict(census), "verified_sha256": h.hexdigest(),
            "verified_bytes": size}


def extraction_fingerprint():
    """Invalidate compact caches on any extraction/helper implementation edit."""
    import inspect
    functions = (canonical, sha, seconds, compact_record, extract_source)
    return sha(canonical({f.__name__: inspect.getsource(f) for f in functions}))


class UnionFind:
    def __init__(self, keys):
        self.parent = {k: k for k in keys}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            low, high = sorted((a, b))
            self.parent[high] = low


def anchor_rank(anchor):
    r = anchor["anchor"]
    t = seconds(r["native_time"])
    if t is None:
        t = seconds(r["audit_time"])
    return (anchor.get("effective_replay", r["replay"]), t if t is not None else float("inf"), r["station_id"],
            r["source_ref"], r["line"], anchor["old_episode_id"])


def corroborated_missing_time_bridges(sources):
    """A narrow two-native-identity bridge for audit transport originals.

    Same user UUID and full payload alone are insufficient. A native assistant
    UUID/content/call witness must be directly parented to that user in the
    embedded capture and lie in the audit occurrence's bounded segment. One
    user timestamp must be absent; two conflicting supplied times never join.
    Ambiguous embedded native-event identities are not bridged.
    """
    anchors = {a["old_episode_id"]: a for s in sources for a in s["anchors"]}
    parent_anchors, assistant_copies = defaultdict(list), defaultdict(list)
    for a in anchors.values():
        r = a["anchor"]
        if r["provider"] == "claude_embedded" and r["uuid"]:
            parent_anchors[(r["source_ref"], r["uuid"])].append(a)
    for s in sources:
        for r in s["records"]:
            if r["provider"] in {"claude_audit", "claude_embedded"} and r["kind"] == "assistant" and r["uuid"] and r["content_sha256"] and any(c["id"] for c in r["calls"]):
                assistant_copies[(r["station_id"], r["uuid"], r["content_sha256"])].append(r)
    candidates = defaultdict(list)
    for group in assistant_copies.values():
        audits = [r for r in group if r["provider"] == "claude_audit" and r["old_interval"] in anchors]
        embedded = [r for r in group if r["provider"] == "claude_embedded" and r["parent"]]
        for audit in audits:
            aa = anchors[audit["old_interval"]]
            ar = aa["anchor"]
            for er in embedded:
                if audit["session"] and er["session"] and audit["session"] != er["session"]:
                    continue
                for ea in parent_anchors.get((er["source_ref"], er["parent"]), []):
                    e = ea["anchor"]
                    if not ar["uuid"] or ar["uuid"] != e["uuid"] or ar["message_sha256"] != e["message_sha256"]:
                        continue
                    if ar["native_time"] and e["native_time"]:
                        continue
                    if not ar["native_time"] and not e["native_time"]:
                        continue
                    supplied = ar["native_time"] or e["native_time"]
                    if seconds(supplied) is None:
                        continue
                    candidates[aa["old_episode_id"]].append({"a": aa["old_episode_id"], "b": ea["old_episode_id"],
                        "kind": "same_native_user_missing_time_shared_direct_response",
                        "witness": {"audit_assistant_record": audit["key"], "embedded_assistant_record": er["key"],
                                    "native_assistant_uuid": er["uuid"], "content_sha256": er["content_sha256"],
                                    "native_tool_ids": sorted(c["id"] for c in er["calls"] if c["id"]),
                                    "embedded_parent_uuid": er["parent"]}})
    edges = []
    for group in candidates.values():
        native_keys = {(anchors[g["b"]]["anchor"]["session"], anchors[g["b"]]["anchor"]["native_time"],
                       anchors[g["b"]]["anchor"]["message_sha256"]) for g in group}
        if len(native_keys) == 1:
            seen = set()
            for g in sorted(group, key=canonical):
                identity = (g["a"], g["b"])
                if identity not in seen:
                    edges.append(g)
                    seen.add(identity)
    return edges


def event_components(anchors, additional_edges=()):
    """Return deterministic components and every identity edge used."""
    by_id = {a["old_episode_id"]: a for a in anchors}
    if len(by_id) != len(anchors):
        raise ValueError("Duplicate old episode identity")
    uf = UnionFind(by_id)
    replay, strong = defaultdict(list), defaultdict(list)
    for a in anchors:
        r = a["anchor"]
        if r["uuid"]:
            replay[(r["station_id"], r["source_ref"], r["uuid"])].append(a)
        if r["uuid"] and r["session"] and seconds(r["native_time"]) is not None and r["message_sha256"]:
            strong[(r["station_id"], r["uuid"], r["session"], r["native_time"],
                    r["message_sha256"])].append(a)
    edges = []
    for group in strong.values():
        replay_sources = {a["anchor"]["source_ref"] for a in group if a["anchor"]["replay"]}
        for a in group:
            a["effective_replay"] = a["anchor"]["replay"] or bool(replay_sources - {a["anchor"]["source_ref"]})
    for family, groups in (("same_source_explicit_replay_uuid", replay), ("strict_native_message", strong)):
        for group in groups.values():
            if len(group) < 2 or (family.startswith("same_source") and not any(a["anchor"]["replay"] for a in group)):
                continue
            ids = sorted(a["old_episode_id"] for a in group)
            for other in ids[1:]:
                uf.join(ids[0], other)
                edges.append({"a": ids[0], "b": other, "kind": family})
    for edge in additional_edges:
        uf.join(edge["a"], edge["b"])
        edges.append(edge)
    groups = defaultdict(list)
    for eid, a in by_id.items():
        groups[uf.find(eid)].append(a)
    events, old_to_event = {}, {}
    for group in groups.values():
        group.sort(key=anchor_rank)
        old_ids = sorted(a["old_episode_id"] for a in group)
        event_id = (old_ids[0] if len(group) == 1 and group[0]["anchor"]["provider"] == "codex_rollout"
                    else "CEV3-" + sha("\n".join(old_ids))[:24])
        events[event_id] = {"event_id": event_id, "anchors": group, "canonical": group[0],
                            "reasons": set(), "flags": set(), "records": [], "results": []}
        for old in old_ids:
            old_to_event[old] = event_id
        originals = {a["prompt_sha256"] for a in group if not a.get("effective_replay", a["anchor"]["replay"])}
        if len(originals) > 1:
            events[event_id]["reasons"].add("conflicting_nonreplay_prompt_payload")
        if len({a["prompt_sha256"] for a in group}) > 1:
            events[event_id]["flags"].add("replay_prompt_variant_preserved")
        if any(a.get("effective_replay") and not a["anchor"]["replay"] for a in group):
            events[event_id]["flags"].add("strict_native_copy_of_explicit_replay")
        if any(a["anchor"]["owner"] for a in group):
            events[event_id]["flags"].add("native_nested_owner_present_not_human_adjudication")
        if len({a["anchor"]["session"] for a in group}) > 1:
            events[event_id]["flags"].add("replay_transport_session_alias")
        if len({a["anchor"]["provider"] for a in group}) > 1:
            events[event_id]["flags"].add("cross_provider_capture_alias")
    return events, old_to_event, edges


def attribute_records(sources, events, old_to_event):
    """Resolve ownership before counting outcomes or selecting an analysis arm.

    Native parent chains govern formats that carry them. Audit formats use
    bounded per-owner segments. Delayed tool results are routed to the unique
    event owning the native call, including across old prompt boundaries.
    """
    assigned = {}
    records = {}
    assignment_reason = {}
    unresolved = []
    for source in sources:
        rs = source["records"]
        by_uuid = defaultdict(list)
        for r in rs:
            records[r["key"]] = r
            if r["uuid"]:
                by_uuid[r["uuid"]].append(r)
        active_by_owner = {}
        resolving = set()

        def parent_owner(r):
            key = r["key"]
            if key in assigned:
                return assigned[key]
            if key in resolving:
                return None
            if r.get("accepted_episode_id"):
                return old_to_event[r["accepted_episode_id"]]
            resolving.add(key)
            matches = by_uuid.get(r["parent"], []) if r["parent"] else []
            owners = set()
            for parent in matches:
                if parent["key"] == key:
                    continue
                owner = parent_owner(parent)
                if owner:
                    owners.add(owner)
            resolving.remove(key)
            if len(owners) == 1:
                owner = next(iter(owners))
                assigned[key] = owner
                assignment_reason[key] = "native_parent_chain"
                return owner
            if len(owners) > 1:
                for owner in owners:
                    events[owner]["reasons"].add("ambiguous_native_parent_ownership")
            return None

        for r in rs:
            if r.get("accepted_episode_id"):
                owner = old_to_event[r["accepted_episode_id"]]
                active_by_owner[r["owner"]] = owner
                assigned[r["key"]] = owner
                assignment_reason[r["key"]] = "accepted_native_anchor"
            elif r["provider"] == "claude_audit" and not r["has_parent"]:
                owner = active_by_owner.get(r["owner"])
                if owner:
                    assigned[r["key"]] = owner
                    assignment_reason[r["key"]] = "bounded_audit_owner_segment"
            elif r["has_parent"]:
                parent_owner(r)
            elif r["old_interval"]:
                # No parent field was provided by this format. The inherited
                # ordered segment is an explicit weaker attribution boundary.
                owner = old_to_event[r["old_interval"]]
                assigned[r["key"]] = owner
                assignment_reason[r["key"]] = "bounded_segment_parent_unavailable"
    # A complete native assistant-message copy with a resolved native parent
    # chain is stronger ownership evidence than an audit capture's current
    # chronological segment. Do not join users or override conflicting strong
    # owners. Supplied native times/sessions must agree when both are present.
    native_copies = defaultdict(list)
    for r in records.values():
        if r["kind"] == "assistant" and r["uuid"] and r["content_sha256"]:
            native_copies[(r["station_id"], r["uuid"], r["content_sha256"])].append(r)
    overrides = []
    for group in native_copies.values():
        strong = [r for r in group if assignment_reason.get(r["key"]) == "native_parent_chain"]
        for r in group:
            if assignment_reason.get(r["key"]) not in {"bounded_audit_owner_segment", "bounded_segment_parent_unavailable", None}:
                continue
            compatible = [other for other in strong if other["source_ref"] != r["source_ref"]
                          and (not r["session"] or not other["session"] or r["session"] == other["session"])]
            owners = {assigned[other["key"]] for other in compatible}
            if len(owners) == 1:
                previous = assigned.get(r["key"])
                owner = next(iter(owners))
                assigned[r["key"]] = owner
                assignment_reason[r["key"]] = "strict_native_copy_parent_chain"
                if any(r["native_time"] and other["native_time"] and r["native_time"] != other["native_time"] for other in compatible):
                    events[owner]["flags"].add("assistant_capture_clock_disagreement")
                if previous != owner:
                    overrides.append({"record": r["key"], "previous_owner": previous, "native_owner": owner,
                                      "native_parent_copy_records": sorted(other["key"] for other in compatible)})
                    events[owner]["flags"].add("native_parent_copy_overrides_weak_segment")
            elif len(owners) > 1:
                for owner in owners:
                    events[owner]["reasons"].add("ambiguous_native_copy_parent_ownership")
    call_owners = defaultdict(set)
    for key, owner in assigned.items():
        r = records[key]
        for call in r["calls"]:
            if call["id"]:
                call_owners[(r["station_id"], call["id"])].add(owner)
    # A nested stream without its own accepted anchor may still be explicitly
    # owned by a delegated call in a retained event. Do not manufacture a new
    # accepted user event for that stream.
    for r in records.values():
        if r["key"] not in assigned and r["owner"]:
            owners = call_owners.get((r["station_id"], r["owner"]), set())
            if len(owners) == 1:
                owner = next(iter(owners))
                assigned[r["key"]] = owner
                assignment_reason[r["key"]] = "native_nested_call_owner"
                events[owner]["flags"].add("nested_stream_attached_by_native_parent_tool_id")
                for call in r["calls"]:
                    if call["id"]:
                        call_owners[(r["station_id"], call["id"])].add(owner)
    for owners in call_owners.values():
        if len(owners) > 1:
            for owner in owners:
                events[owner]["reasons"].add("ambiguous_native_tool_call_owner")
    native_calls = defaultdict(list)
    for r in records.values():
        for call in r["calls"]:
            if call["id"]:
                native_calls[(r["station_id"], call["id"])].append((r, call))
    for event in events.values():
        owners = {(a["anchor"]["station_id"], a["anchor"]["owner"])
                  for a in event["anchors"] if a["anchor"]["owner"]}
        evidence = []
        for owner in sorted(owners):
            matches = native_calls.get(owner, [])
            # Native Claude Task is a delegation API even though the frozen
            # generic name taxonomy classified the bare name as "other".
            # Recognize the ownership relation without changing that taxonomy.
            delegate_matches = [(r, c) for r, c in matches
                                if c["class"] == "delegate" or c["name"].casefold().rsplit("__", 1)[-1] in {"agent", "task"}]
            if delegate_matches and len(delegate_matches) == len(matches):
                evidence.extend({"owner_tool_id": owner[1], "record": r["key"], "name": c["name"]}
                                for r, c in delegate_matches)
        event["native_delegation_evidence"] = evidence
        if evidence:
            event["flags"].add("native_delegated_tool_child")
        elif owners:
            event["flags"].add("unresolved_native_nested_owner")
    result_diagnostics = Counter()
    for key, r in records.items():
        owner = assigned.get(key)
        if owner and (r["calls"] or r["texts"] or r["kind"] == "assistant"):
            events[owner]["records"].append(r)
            events[owner].setdefault("record_ownership", {})[key] = assignment_reason.get(key, "")
        elif not owner and (r["calls"] or r["texts"]):
            unresolved.append({"record": key, "kind": r["kind"], "old_interval": r["old_interval"],
                               "reason": "no_unambiguous_native_or_bounded_owner"})
            # An unowned action inside an old retained interval is genuine
            # attribution ambiguity for that event, not evidence of no work.
            if r["old_interval"]:
                events[old_to_event[r["old_interval"]]]["reasons"].add("unresolved_record_ownership")
        for result in r["results"]:
            owners = call_owners.get((r["station_id"], result["id"]), set())
            if len(owners) == 1:
                target = next(iter(owners))
                events[target]["results"].append({"record": r, "result": result})
                if target != owner:
                    result_diagnostics["results_routed_to_native_call_owner_outside_current_segment"] += 1
                    events[target]["flags"].add("delayed_result_attributed_by_native_tool_id")
            elif not owners:
                result_diagnostics["orphan_result_records_not_used_as_endpoint"] += 1
            else:
                result_diagnostics["ambiguous_result_owner_records"] += 1
    return {"assignment": assigned, "assignment_reason": assignment_reason,
            "native_parent_assignment_overrides": overrides,
            "unresolved": unresolved, "result_diagnostics": dict(result_diagnostics)}


def reconcile_nonprimary_boundaries(sources, events, old_to_event, rows_by_id, screen, rules):
    """Absorb only uniquely owned machine notifications / bare continuations.

    Identity reconciliation and primary-boundary reconciliation are separate.
    Every original anchor remains an alias. Missing/conflicting ownership is
    held, not silently dropped, attached by successful outcome or called human.
    """
    baseline = {eid: (set(e["reasons"]), set(e["flags"])) for eid, e in events.items()}
    preliminary = attribute_records(sources, events, old_to_event)
    assigned = preliminary["assignment"]
    records = {r["key"]: r for s in sources for r in s["records"]}
    by_uuid, calls, prior_anchor = defaultdict(list), defaultdict(list), {}
    for source in sources:
        prior_by_owner = {}
        for r in source["records"]:
            if r["uuid"]:
                by_uuid[(r["source_ref"], r["uuid"])].append(r)
            for c in r["calls"]:
                if c["id"] and r["key"] in assigned:
                    calls[(r["station_id"], c["id"])].append((assigned[r["key"]], r))
            if r.get("accepted_episode_id"):
                # Explicit session boundaries cannot support adjacency. Empty
                # session metadata is its own stratum, not a wildcard.
                owner_key = (r["owner"], r["session"])
                prior_anchor[r["key"]] = prior_by_owner.get(owner_key)
                prior_by_owner[owner_key] = old_to_event[r["accepted_episode_id"]]
    # Discard provisional attribution before recomputing under the final map.
    for eid, event in events.items():
        event["reasons"], event["flags"] = baseline[eid]
        event["records"], event["results"] = [], []
        event.pop("record_ownership", None)
        event.pop("native_delegation_evidence", None)
    kinds, raw_targets, evidence = {}, {}, {}
    for eid, event in events.items():
        notifications = [a for a in event["anchors"] if a["anchor"].get("notification_boundary")]
        canonical = event["canonical"]
        text = rows_by_id[canonical["old_episode_id"]]["prompt_text"]
        if notifications:
            kinds[eid] = "machine_task_notification"
            if any(a["anchor"].get("native_origin") == "human" for a in event["anchors"]):
                event["reasons"].add("conflicting_native_boundary_origin")
        elif screen.bare_continuation(text, rules) and not any(a['attachment_count'] for a in event['anchors']):
            kinds[eid] = "bare_continuation"
        else:
            continue
        targets, witnesses = set(), []
        if kinds[eid] == "machine_task_notification":
            for a in notifications:
                r = a["anchor"]
                ids = r["notification_boundary"].get("tool_ids", [])
                if len(ids) != 1:
                    event["reasons"].add("missing_or_conflicting_notification_call_reference")
                    continue
                for owner, call_record in calls.get((r["station_id"], ids[0]), []):
                    if owner != eid:
                        targets.add(owner)
                        witnesses.append({"anchor": r["key"], "kind": "native_notification_call_owner",
                                          "call_record": call_record["key"], "target_component": owner,
                                          "native_tool_id": ids[0]})
        else:
            for a in event["anchors"]:
                r = a["anchor"]
                if r["has_parent"]:
                    owners = {(assigned[p["key"]], p["key"])
                              for p in by_uuid.get((r["source_ref"], r["parent"]), [])
                              if p["key"] in assigned and assigned[p["key"]] != eid}
                    for owner, parent_key in owners:
                        targets.add(owner)
                        witnesses.append({"anchor": r["key"], "kind": "native_parent_continuation_owner",
                                          "parent_record": parent_key, "target_component": owner})
                else:
                    owner = prior_anchor.get(r["key"])
                    if owner and owner != eid:
                        targets.add(owner)
                        witnesses.append({"anchor": r["key"], "kind": "bounded_same_source_owner_continuation",
                                          "target_component": owner})
        raw_targets[eid] = targets
        evidence[eid] = witnesses
    memo = {}
    def primary_owner(eid, visiting=()):
        if eid not in kinds:
            return eid
        if eid in memo:
            return memo[eid]
        if eid in visiting or events[eid]["reasons"]:
            return None
        resolved = {primary_owner(target, visiting + (eid,)) for target in raw_targets[eid]}
        if len(resolved) == 1 and None not in resolved:
            memo[eid] = next(iter(resolved))
        else:
            memo[eid] = None
        return memo[eid]
    owners = {eid: primary_owner(eid) for eid in kinds}
    groups = defaultdict(list)
    for eid in events:
        groups[owners.get(eid) or eid].append(eid)
    final, final_map, edges = {}, {}, []
    for root, member_ids in sorted(groups.items()):
        base = events[root]
        group = [events[eid] for eid in sorted(member_ids)]
        aa = [a for e in group for a in e["anchors"]]
        old_ids = sorted(a["old_episode_id"] for a in aa)
        new_id = root if len(group) == 1 else "CEV4-" + sha("\n".join(old_ids))[:24]
        merged = {"event_id": new_id, "anchors": sorted(aa, key=anchor_rank), "canonical": base["canonical"],
                  "reasons": set().union(*(e["reasons"] for e in group)),
                  "flags": set().union(*(e["flags"] for e in group)), "records": [], "results": [],
                  "boundary_absorptions": []}
        for eid in member_ids:
            if eid in kinds and owners[eid]:
                edge = {"component": eid, "kind": kinds[eid], "primary_component": owners[eid],
                        "final_event_id": new_id, "old_episode_ids": sorted(a["old_episode_id"] for a in events[eid]["anchors"]),
                        "witnesses": evidence[eid]}
                edges.append(edge)
                merged["boundary_absorptions"].append(edge)
                merged["flags"].add("nonprimary_boundary_absorbed_with_work")
            elif eid in kinds:
                merged["boundary_kind"] = kinds[eid]
                merged["boundary_evidence"] = evidence[eid]
                merged["reasons"].add("unresolved_nonprimary_boundary_owner")
                merged["flags"].add("nonprimary_anchor_held_not_counted_as_primary")
        final[new_id] = merged
        for old in old_ids:
            final_map[old] = new_id
    return final, final_map, edges


def record_rank(r):
    t = seconds(r["native_time"])
    if t is None:
        t = seconds(r["audit_time"])
    return (t if t is not None else float("inf"), r["source_ref"], r["line"], r["uuid"])


def dual_capture_variants(records):
    """Corroborated native audit/embedded capture, not arbitrary ID reuse.

    This does not assert that differing payload bytes are semantically equal.
    Callers may retain such variants only when every measurement they consume
    is invariant. Home/home conflicts and differing native UUIDs remain held.
    """
    return ({r["provider"] for r in records} == {"claude_audit", "claude_embedded"}
            and len({r["uuid"] for r in records}) == 1 and bool(records[0]["uuid"])
            and len({r["session"] for r in records if r["session"]}) <= 1)


def canonical_native_embedded_call(event, variants):
    """Fixed native-parent provenance priority, never a favorable outcome.

    This deliberately does not claim differing literal inputs equivalent.
    A unique internally consistent embedded representation with resolved
    native parent ownership supplies the classifier input. Every audit alias
    remains in the proof, including different literal classes and targets.
    """
    if not dual_capture_variants([r for r, _ in variants]):
        return None
    if len({c["name"] for _, c in variants}) != 1:
        return None
    native = [(r, c) for r, c in variants if r["provider"] == "claude_embedded"]
    if not native or any(event.get("record_ownership", {}).get(r["key"]) != "native_parent_chain" for r, _ in native):
        return None
    if len({(c["input_sha256"], c["class"], c["target_ref"]) for _, c in native}) != 1:
        return None
    return min(native, key=lambda pair: record_rank(pair[0]) + (pair[1]["index"],))


def refresh_merged_codex_completion(event, screen):
    """Replay adapter status inside the corrected primary boundary only.

    Compact metadata retains parsed process/session envelopes, not output prose
    or executable input. The pre-correction trace was separately reproduced.
    Fresh primary events are never pooled merely to find a successful poll.
    """
    if not event.get('boundary_absorptions') or event['canonical']['anchor']['provider'] != 'codex_rollout':
        return
    timeline = {r['key']: r for r in event['records']}
    for pair in event['results']:
        timeline[pair['record']['key']] = pair['record']
    if len({r['source_ref'] for r in timeline.values()}) != 1:
        event['reasons'].add('unsupported_cross_source_codex_boundary_completion')
        return
    state = screen.EpisodeToolState([])
    bindings = []
    for record in sorted(timeline.values(), key=lambda r: r['line']):
        for result in record['results']:
            state.apply_parts(result['id'], [screen.ResultStatus(**p) for p in result.get('status_parts', [])])
        for compact in record['calls']:
            call = state.add_call(compact['id'], compact['name'], {})
            call.update({k: compact[k] for k in ('class', 'target_ref')})
            state.metadata[id(call)]['poll_session'] = compact.get('poll_session')
            bindings.append((compact, call))
    for compact, call in bindings:
        compact.update({k: call[k] for k in ('completed', 'succeeded')})
    event['flags'].add('codex_completion_replayed_inside_corrected_primary_boundary')
    event['codex_completion_diagnostics'] = dict(state.diagnostics)


def ordered_calls(event):
    """Unique calls, preserving recorded order without outcome-based choice."""
    call_variants, by_source = defaultdict(list), defaultdict(list)
    for r in event["records"]:
        for c in r["calls"]:
            identity = c["id"] or "missing:" + r["key"] + ":" + str(c["index"])
            call_variants[identity].append((r, c))
            by_source[r["source_ref"]].append((r["line"], c["index"], identity))
    graph = {c: set() for c in call_variants}
    indegree = Counter({c: 0 for c in call_variants})
    for seq in by_source.values():
        seq.sort()
        # A replayed complete prefix may restart a recorded sequence. Repeated
        # native call IDs are aliases, not an edge from the tail back to root.
        seen, previous = set(), None
        for _, _, key in seq:
            if key in seen:
                previous = key
                continue
            if previous is not None and key != previous and key not in graph[previous]:
                graph[previous].add(key)
                indegree[key] += 1
            seen.add(key)
            previous = key
    first = {k: min(v, key=lambda pair: record_rank(pair[0]) + (pair[1]["index"],)) for k, v in call_variants.items()}
    # Native call timestamps can order otherwise disjoint observed branches.
    # Audit ingestion timestamps cannot establish cross-capture causal order.
    native_groups = defaultdict(list)
    for key, variants in call_variants.items():
        times = {seconds(r["native_time"]) for r, _ in variants if seconds(r["native_time"]) is not None}
        if len(times) == 1:
            native_groups[next(iter(times))].append(key)
    def reaches(start, target):
        todo, visited = [start], set()
        while todo:
            node = todo.pop()
            if node == target:
                return True
            if node not in visited:
                visited.add(node)
                todo.extend(graph[node] - visited)
        return False
    times = sorted(native_groups)
    for earlier, later in zip(times, times[1:]):
        for a in native_groups[earlier]:
            for b in native_groups[later]:
                if reaches(b, a):
                    event["flags"].add("native_time_conflicts_with_recorded_call_order")
                    continue
                if b not in graph[a]:
                    graph[a].add(b)
                    indegree[b] += 1
    ranks = {k: record_rank(pair[0]) + (pair[1]["index"], k) for k, pair in first.items()}
    heap = [(ranks[k], k) for k in graph if indegree[k] == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        if len(heap) > 1:
            event["flags"].add("partial_order_ties_resolved_by_time_then_identity")
        _, key = heapq.heappop(heap)
        order.append(key)
        for target in sorted(graph[key]):
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(heap, (ranks[target], target))
    if len(order) != len(graph):
        event["reasons"].add("contradictory_native_call_order")
        order = sorted(graph, key=lambda k: ranks[k])
    results = defaultdict(list)
    for pair in event["results"]:
        results[pair["result"]["id"]].append(pair)
    calls, provenance, timing_nodes = [], [], []
    for position, key in enumerate(order, 1):
        variants = call_variants[key]
        chosen_record, chosen = first[key]
        representation_basis = "earliest_supported_time_then_stable_identity"
        semantic_inputs = {(c["name"], c["input_sha256"], c["class"], c["target_ref"]) for _, c in variants}
        if len(semantic_inputs) != 1:
            measurement_inputs = {(c["name"], c["class"], c["target_ref"]) for _, c in variants}
            native = canonical_native_embedded_call(event, variants)
            if native is not None:
                chosen_record, chosen = native
                representation_basis = "unique_native_parent_linked_embedded_input"
                event["flags"].add("native_embedded_input_provenance_priority")
                if len({c["class"] for _, c in variants}) > 1:
                    event["flags"].add("literal_tool_class_capture_variants_preserved")
                if len({c["target_ref"] for _, c in variants}) > 1:
                    event["flags"].add("literal_tool_target_capture_variants_preserved")
            elif (len(measurement_inputs) == 1 and dual_capture_variants([r for r, _ in variants])
                  and len({c["input_sha256"] for r, c in variants if r["provider"] == "claude_embedded"}) == 1):
                event["flags"].add("native_dual_capture_tool_payload_measurement_invariant")
            else:
                event["reasons"].add("conflicting_native_tool_call_payload")
        statuses = {x["result"]["succeeded"] for x in results[key] if x["result"].get("completed", True)}
        if len(statuses) > 1:
            # A later native terminal update can supersede an earlier status.
            # Never choose a successful result merely because it is favorable.
            terminal = None
            for clock in ("native_time", "audit_time"):
                dated = [(seconds(x["record"][clock]), x["result"]["succeeded"]) for x in results[key]]
                if all(t is not None for t, _ in dated):
                    latest = max(t for t, _ in dated)
                    terminal = {s for t, s in dated if t == latest}
                    break
            if terminal is not None and len(terminal) == 1:
                statuses = terminal
                event["flags"].add("chronological_native_tool_status_update")
            else:
                event["reasons"].add("conflicting_native_tool_result_status")
        completed = bool(statuses)
        succeeded = completed and statuses == {True}
        if chosen_record["provider"] == "codex_rollout":
            # Preserve the separately reproduced v2 asynchronous completion
            # state. A running result envelope is not a terminal success.
            observed = {(bool(c.get("completed")), bool(c.get("succeeded"))) for _, c in variants}
            if len(observed) != 1:
                event["reasons"].add("conflicting_codex_completion_state")
            completed, succeeded = bool(chosen.get("completed")), bool(chosen.get("succeeded"))
        calls.append({"order": position, "name": chosen["name"], "class": chosen["class"],
                      "completed": completed, "succeeded": succeeded, "target_ref": chosen["target_ref"]})
        provenance.append({"native_tool_id": key, "order": position,
                           "canonical_call_record": chosen_record["key"], "canonical_input_basis": representation_basis,
                           "call_records": sorted({r["key"] for r, _ in variants}),
                           "call_payload_hashes": sorted({c["input_sha256"] for _, c in variants}),
                           "call_measurement_variants": [list(value) for value in sorted({(c["name"], c["class"], c["target_ref"]) for _, c in variants})],
                           "call_capture_variants": [{"record": r["key"], "provider": r["provider"], "native_uuid": r["uuid"],
                                                      "input_sha256": c["input_sha256"], "name": c["name"],
                                                      "class": c["class"], "target_ref": c["target_ref"]}
                                                     for r, c in sorted(variants, key=lambda pair: (pair[0]["key"], pair[1]["index"]))],
                           "result_records": sorted({x["record"]["key"] for x in results[key]}),
                           "result_payload_hashes": sorted({x["result"]["payload_sha256"] for x in results[key]}),
                           "completed": completed, "succeeded": succeeded})
        timing_nodes.append([r for r, _ in variants])
        if results[key]:
            # Each native result UUID is a distinct completion representation;
            # same call completion copied between captures shares one node.
            grouped = defaultdict(list)
            for x in results[key]:
                r = x["record"]
                grouped[r["uuid"] or r["key"]].append(r)
            timing_nodes.extend(grouped.values())
    # A lexical/source-ID tie break is an ordering convention, not evidence
    # that context preceded work. Mark only order-sensitive context ambiguity;
    # disjoint same-class actions themselves remain attributable and retained.
    completed_context = [key for key, call in zip(order, calls)
                         if call["completed"] and call["succeeded"] and call["class"] in {"retrieve", "search"}]
    completed_actions = [key for key, call in zip(order, calls)
                         if call["completed"] and call["succeeded"] and call["class"] in {"modify", "execute", "verify"}]
    order_bounds = None
    if completed_actions:
        feasible_first = [a for a in completed_actions
                          if not any(other != a and reaches(other, a) for other in completed_actions)]
        possible = {c for c in completed_context if not any(reaches(a, c) for a in completed_actions)}
        minimum_sets = [(a, {c for c in completed_context if reaches(c, a)}) for a in feasible_first]
        if minimum_sets and any(cs != possible for _, cs in minimum_sets):
            targets = {key: call["target_ref"] for key, call in zip(order, calls)}
            distinct = lambda keys: {targets[k] for k in keys if targets[k]}
            # This candidate minimizes the attainable context-call prefix,
            # not verification success or a desired analytical effect.
            first_action, chosen_context = min(minimum_sets, key=lambda pair:
                (len(pair[1]), len(distinct(pair[1])), ranks[pair[0]]))
            prefix = {key for key in graph if reaches(key, first_action)}
            degree = Counter({key: 0 for key in graph})
            for successors in graph.values():
                for key in successors:
                    degree[key] += 1
            ready = [(0 if key in prefix else 1, ranks[key], key) for key in graph if degree[key] == 0]
            heapq.heapify(ready)
            witness = []
            while ready:
                _, _, key = heapq.heappop(ready)
                witness.append(key)
                for successor in sorted(graph[key]):
                    degree[successor] -= 1
                    if degree[successor] == 0:
                        heapq.heappush(ready, (0 if successor in prefix else 1, ranks[successor], successor))
            if len(witness) == len(order):
                by_key = dict(zip(order, calls))
                calls = [by_key[key] for key in witness]
                for index, call in enumerate(calls, 1):
                    call["order"] = index
                proof_by_key = {p["native_tool_id"]: p for p in provenance}
                provenance = [proof_by_key[key] for key in witness]
                for index, proof in enumerate(provenance, 1):
                    proof["order"] = index
                order = witness
            event["flags"].add("lower_bound_context_before_count")
            order_bounds = {"feasible_first_actions": [a for a, _ in minimum_sets],
                            "minimum_context_sets": [sorted(cs) for _, cs in minimum_sets],
                            "possible_context_set": sorted(possible),
                            "context_count_min": min(len(cs) for _, cs in minimum_sets),
                            "context_count_max": len(possible),
                            "distinct_targets_min": min(len(distinct(cs)) for _, cs in minimum_sets),
                            "distinct_targets_max": len(distinct(possible)),
                            "chosen_first_action": first_action,
                            "chosen_context_set": sorted(chosen_context),
                            "basis": "Valid conservative topological witness; before-action count is the minimum attainable count, not a claim to exact unobserved order."}
            event["context_order_bounds"] = order_bounds
            event["ordered_native_call_ids"] = order
    return calls, provenance, timing_nodes


def assistant_measurements(event):
    grouped = defaultdict(list)
    for r in event["records"]:
        if r["kind"] == "assistant":
            grouped[r["uuid"] or r["key"]].append(r)
    blocks, chars = 0, 0
    variant_proofs = []
    for variants in grouped.values():
        contents = {r["content_sha256"] for r in variants}
        if len(contents) > 1:
            # Native dual captures may rewrite tool-input paths. Preserve the
            # exact text blocks and every consumed tool measurement; this is a
            # measured-representation exception, not semantic equivalence.
            measures = {(tuple((t["sha256"], t["chars"], t["index"]) for t in r["texts"]),
                         tuple((c["id"], c["name"], c["class"], c["target_ref"], c["index"]) for c in r["calls"]))
                        for r in variants}
            invariant = (len(measures) == 1 and dual_capture_variants(variants)
                         and len({r["content_sha256"] for r in variants if r["provider"] == "claude_embedded"}) == 1)
            # Fixed native input provenance can legitimately choose a different
            # literal tool class/target. It cannot explain different prose or
            # extra/missing native call identities within one assistant UUID.
            native = [r for r in variants if r["provider"] == "claude_embedded"]
            canonicalized = (dual_capture_variants(variants) and bool(native)
                and all(event.get("record_ownership", {}).get(r["key"]) == "native_parent_chain" for r in native)
                and len({r["content_sha256"] for r in native}) == 1
                and len({tuple((t["sha256"], t["chars"], t["index"]) for t in r["texts"]) for r in variants}) == 1
                and len({tuple((c["id"], c["name"], c["index"]) for c in r["calls"]) for r in variants}) == 1)
            if canonicalized:
                event["flags"].add("native_embedded_assistant_payload_provenance_priority")
            elif invariant:
                event["flags"].add("native_dual_capture_assistant_payload_measurement_invariant")
            else:
                event["reasons"].add("conflicting_native_assistant_content")
            variant_proofs.append({"native_uuid": variants[0]["uuid"], "measurement_invariant": invariant,
                                   "native_embedded_provenance_priority": canonicalized,
                                   "records": sorted(r["key"] for r in variants),
                                   "content_sha256_variants": sorted(contents)})
        chosen = min(variants, key=record_rank)
        blocks += len(chosen["texts"])
        chars += sum(t["chars"] for t in chosen["texts"])
    event["assistant_capture_variants"] = variant_proofs
    return blocks, chars, list(grouped.values())


def event_timing(event, nodes):
    """Choose a consistent observed clock over attributable nodes only."""
    anchor = event["canonical"]["anchor"]
    start_display = anchor["native_time"] if seconds(anchor["native_time"]) is not None else anchor["audit_time"]
    for clock in ("native_time", "audit_time"):
        start = seconds(anchor[clock])
        if start is None:
            continue
        endpoints = []
        complete = True
        for representations in nodes:
            values = [(seconds(r[clock]), r[clock], r["key"]) for r in representations if seconds(r[clock]) is not None]
            if not values:
                complete = False
                break
            # Native aliases should agree; audit captures may have different
            # ingestion times, so use the earliest observation, not latest copy.
            if clock == "native_time" and len({v[0] for v in values}) > 1:
                complete = False
                event["flags"].add("native_clock_alias_disagreement")
                break
            endpoints.append(min(values))
        if not complete:
            continue
        if any(t < start for t, _, _ in endpoints):
            event["flags"].add("attributable_record_precedes_event_start")
            continue
        end = max(endpoints, default=(start, anchor[clock], anchor["key"]))
        return {"start": normalized_time(anchor[clock]), "end": normalized_time(end[1]),
                "status": "observed_" + clock, "clock": clock, "duration_seconds": end[0] - start,
                "endpoint_record": end[2], "attributable_timing_nodes": len(nodes)}
    return {"start": normalized_time(start_display), "end": "", "status": "missing_attributable_duration",
            "clock": "", "duration_seconds": None, "endpoint_record": "", "attributable_timing_nodes": len(nodes)}


def normalize_sources(sources, rows_by_id, screen, rules):
    """Pure normalization interface used by the private runner and fixtures.

    Returns all-provider event rows (including explicitly held candidates),
    complete aliases, causal tool provenance and occurrence-level diagnostics.
    Callers must exclude quarantine rows using the returned status, never infer
    a human reference label from that computational data-quality boundary.
    """
    anchors = [a for s in sources for a in s["anchors"]]
    events, old_to_event, edges = event_components(anchors, corroborated_missing_time_bridges(sources))
    events, old_to_event, boundary_edges = reconcile_nonprimary_boundaries(sources, events, old_to_event, rows_by_id, screen, rules)
    attribution = attribute_records(sources, events, old_to_event)
    stages = screen.compile_groups(rules, "stages")
    modes = screen.compile_groups(rules, "context_modes")
    regexes = [[re.compile(x, re.I) for x in rules[key]] for key in
               ("publication_exclusions", "product_signals", "non_product_exclusions", "continuation_only",
                "continuation_wrappers", "delegated_prompt_candidates", "tool_generated_prompts")]
    outputs, aliases, proofs = [], [], []
    for eid in sorted(events):
        event = events[eid]
        canonical_anchor = event["canonical"]
        anchor = canonical_anchor["anchor"]
        old = rows_by_id[canonical_anchor["old_episode_id"]]
        refresh_merged_codex_completion(event, screen)
        calls, tool_proof, nodes = ordered_calls(event)
        blocks, chars, assistant_nodes = assistant_measurements(event)
        timing = event_timing(event, nodes + assistant_nodes)
        singleton_codex = anchor["provider"] == "codex_rollout" and len(event["anchors"]) == 1
        if singleton_codex:
            timing = {"start": old["timestamp_start_utc"], "end": old["timestamp_end_utc"],
                      "status": old["timestamp_status"], "clock": "pinned_v2_codex_interval",
                      "duration_seconds": ((seconds(old["timestamp_end_utc"]) - seconds(old["timestamp_start_utc"]))
                                           if seconds(old["timestamp_end_utc"]) is not None and seconds(old["timestamp_start_utc"]) is not None else None),
                      "endpoint_record": old["source_ref"] + ":" + old["source_line_end"],
                      "attributable_timing_nodes": len(nodes + assistant_nodes),
                      "basis": "Unmerged Codex timing retained from pinned v2; boundary correction rescreens labels only."}
        ep = {"prompt_text": old["prompt_text"], "attachment_count": int(old["attachment_count"]),
              "calls": calls, "assistant_output_blocks": blocks, "assistant_output_chars": chars,
              "native_origin": anchor.get("native_origin", "")}
        classified = screen.episode_classification(ep, rules, stages, modes, *regexes)
        if event.get("context_order_bounds"):
            bounds = event["context_order_bounds"]
            identities = event["ordered_native_call_ids"]
            by_call = dict(zip(identities, calls))
            signatures = set()
            alternatives = list(zip(bounds["feasible_first_actions"], bounds["minimum_context_sets"]))
            alternatives.append((bounds["feasible_first_actions"][0], bounds["possible_context_set"]))
            for first_action, context_ids in alternatives:
                # These before-first-action sets are attainable in the native
                # partial order. Other after-first positions do not affect the
                # unchanged classifier; no synthetic trace is exported.
                prefix_ids = list(context_ids) + [first_action]
                hypothetical = prefix_ids + [k for k in identities if k not in prefix_ids]
                variant = [dict(by_call[k], order=i) for i, k in enumerate(hypothetical, 1)]
                candidate = screen.episode_classification(dict(ep, calls=variant), rules, stages, modes, *regexes)
                signatures.add((candidate["automated_disposition"], candidate["context_trace_status"],
                                candidate["product_action_trace_status"], candidate["grounded_decision_trace"]))
            bounds["qualification_signatures"] = [list(s) for s in sorted(signatures)]
            bounds["qualification_invariant"] = len(signatures) == 1
            if len(signatures) > 1:
                event["reasons"].add("unresolved_context_order")
                event["flags"].add("unique_work_retained_but_context_before_action_not_identified")
                event["ambiguous_context_call_ids"] = bounds["possible_context_set"]
        if event.get("native_delegation_evidence"):
            classified["origin_candidate"] = "native_delegated_tool_child"
        elif "unresolved_native_nested_owner" in event["flags"]:
            classified["origin_candidate"] = "native_nested_owner_unresolved"
        if event.get("boundary_kind"):
            classified["origin_candidate"] = "nonprimary_boundary_unresolved"
        session_identity = anchor["session"] or "source:" + anchor["source_ref"]
        session = "SSN3-" + sha(anchor["station_id"] + "|" + session_identity + "|" + anchor["owner"])[:24]
        if anchor["provider"] == "codex_rollout":
            session = old["session_ref"]
        row = dict(old)
        row.update({"episode_id": eid, "session_ref": session,
                    "timestamp_start_utc": timing["start"], "timestamp_end_utc": timing["end"],
                    "timestamp_status": timing["status"], "tool_calls": str(len(calls)),
                    "assistant_output_blocks": str(blocks), "assistant_output_chars": str(chars),
                    "rule_version": rules["rule_version"] + ";" + screen.ADAPTER_VERSION + ";" + VERSION,
                    "tool_trace_json": screen.compact_json(calls),
                    **{k: str(v) for k, v in classified.items()}})
        case_ids = sorted({x for a in event["anchors"] for x in rows_by_id[a["old_episode_id"]]["candidate_case_ids"].split("|") if x})
        row["candidate_case_ids"] = "|".join(case_ids)
        status = "quarantined" if event["reasons"] else "resolved"
        proof = {"event_id": eid, "status": status, "reasons": sorted(event["reasons"]),
                 "flags": sorted(event["flags"]), "canonical_old_episode_id": canonical_anchor["old_episode_id"],
                 "old_episode_ids": sorted(a["old_episode_id"] for a in event["anchors"]),
                 "prompt_variants": [{"old_episode_id": a["old_episode_id"], "prompt_sha256": a["prompt_sha256"],
                                      "message_sha256": a["anchor"]["message_sha256"],
                                      "is_replay": a["anchor"]["replay"],
                                      "effective_replay": a.get("effective_replay", a["anchor"]["replay"])} for a in event["anchors"]],
                 "timing": timing, "native_session": session_identity, "native_nested_owner": anchor["owner"],
                 "canonical_native_origin": anchor.get("native_origin", ""),
                 "boundary_absorptions": event.get("boundary_absorptions", []),
                 "unresolved_boundary_kind": event.get("boundary_kind", ""),
                 "unresolved_boundary_evidence": event.get("boundary_evidence", []),
                 "native_delegation_evidence": event.get("native_delegation_evidence", []),
                 "ambiguous_context_call_ids": event.get("ambiguous_context_call_ids", []),
                 "context_order_bounds": event.get("context_order_bounds"),
                 "assistant_capture_variants": event.get("assistant_capture_variants", []),
                 "canonical_source_span_note": "51-column source span describes canonical occurrence only; all contributing intervals and tool-record locators are in private maps.",
                 "tools": tool_proof}
        outputs.append({"row": row, "status": status, "reasons": proof["reasons"], "proof": proof})
        proofs.append(proof)
        for a in event["anchors"]:
            old_alias = rows_by_id[a["old_episode_id"]]
            aliases.append({"old_episode_id": a["old_episode_id"], "event_id": eid, "status": status,
                            "reasons": "|".join(proof["reasons"]), "station_id": old_alias["station_id"],
                            "provider": old_alias["provider"], "source_ref": old_alias["source_ref"],
                            "source_line_start": old_alias["source_line_start"], "source_line_end": old_alias["source_line_end"],
                            "old_turn_index": old_alias["turn_index"], "canonical_old_episode_id": canonical_anchor["old_episode_id"],
                            "session_ref": session, "native_uuid": a["anchor"]["uuid"],
                            "native_session": a["anchor"]["session"], "native_nested_owner": a["anchor"]["owner"],
                            "is_replay": str(a["anchor"]["replay"]).lower(),
                            "effective_replay": str(a.get("effective_replay", a["anchor"]["replay"])).lower(),
                            "prompt_sha256": a["prompt_sha256"]})
    sessions = defaultdict(list)
    for out in outputs:
        sessions[out["row"]["session_ref"]].append(out)
    for group in sessions.values():
        group.sort(key=lambda out: (seconds(out["row"]["timestamp_start_utc"]) if seconds(out["row"]["timestamp_start_utc"]) is not None else float("inf"),
                                    out["row"]["source_ref"], int(out["row"]["source_line_start"]), out["row"]["episode_id"]))
        for index, out in enumerate(group, 1):
            out["row"]["turn_index"] = str(index)
            out["proof"]["native_session_event_ordinal"] = index
    by_event = {o["row"]["episode_id"]: o for o in outputs}
    for alias in aliases:
        alias["event_turn_index"] = by_event[alias["event_id"]]["row"]["turn_index"]
    native_input_counts, literal_class_pairs = Counter(), Counter()
    for proof in proofs:
        for tool in proof["tools"]:
            if tool["canonical_input_basis"] != "unique_native_parent_linked_embedded_input":
                continue
            variants = tool["call_capture_variants"]
            chosen = next(v for v in variants if v["record"] == tool["canonical_call_record"])
            native_input_counts["canonicalized_event_calls"] += 1
            native_input_counts[proof["status"] + "_canonicalized_event_calls"] += 1
            if len({v["class"] for v in variants}) > 1:
                native_input_counts["literal_class_changed_event_calls"] += 1
            if len({v["target_ref"] for v in variants}) > 1:
                native_input_counts["literal_target_changed_event_calls"] += 1
            for source_class in {v["class"] for v in variants if v["provider"] == "claude_audit"}:
                if source_class != chosen["class"]:
                    literal_class_pairs[source_class + "->" + chosen["class"]] += 1
    return {"events": outputs, "aliases": aliases, "identity_edges": edges, "boundary_edges": boundary_edges, "attribution": attribution,
            "counts": {"old_source_rows": len(anchors), "old_claude_rows": sum(a["anchor"]["provider"] in CLAUDE for a in anchors), "normalized_events": len(outputs),
                       "resolved_events": sum(o["status"] == "resolved" for o in outputs),
                       "quarantined_events": sum(o["status"] == "quarantined" for o in outputs),
                       "representation_reduction": len(anchors) - len(outputs) - len(boundary_edges),
                       "total_alias_to_primary_component_reduction": len(anchors) - len(outputs),
                       "absorbed_nonprimary_components": len(boundary_edges),
                       "absorbed_nonprimary_kinds": dict(Counter(e["kind"] for e in boundary_edges)),
                       "reason_counts": dict(Counter(reason for o in outputs for reason in o["reasons"])),
                       "flag_counts": dict(Counter(flag for p in proofs for flag in p["flags"])),
                       "identity_edge_counts": dict(Counter(edge["kind"] for edge in edges)),
                       "native_parent_assignment_overrides": len(attribution["native_parent_assignment_overrides"]),
                       "native_input_provenance_counts": dict(native_input_counts),
                       "literal_class_capture_transition_counts": dict(literal_class_pairs),
                       "timing_status_counts": dict(Counter(p["timing"]["status"] for p in proofs))}}


def assemble_frames(normalized, rows):
    """Preserve original input order at first alias and account for every alias."""
    event_index = {e["row"]["episode_id"]: e for e in normalized["events"]}
    old_to_event = {a["old_episode_id"]: a["event_id"] for a in normalized["aliases"]}
    resolved, quarantined, emitted = [], [], set()
    aliases = [dict(a) for a in normalized["aliases"]]
    for old in rows:
        if old["episode_id"] not in old_to_event:
            raise ValueError("Every input provider requires extracted native evidence; no unchanged-row passthrough")
        eid = old_to_event[old["episode_id"]]
        if eid not in emitted:
            emitted.add(eid)
            event = event_index[eid]
            (resolved if event["status"] == "resolved" else quarantined).append(dict(event["row"]))
    reuse = Counter(("old" if r["station_id"] in {"ST00", "ST01", "ST02"} else "new", r["prompt_ref"]) for r in resolved)
    for r in resolved:
        if r["provider"] in CLAUDE:
            r["prompt_reuse_count"] = str(reuse[("old" if r["station_id"] in {"ST00", "ST01", "ST02"} else "new", r["prompt_ref"])])
    aliases.sort(key=lambda a: a["old_episode_id"])
    if len(aliases) != len(rows) or {a["old_episode_id"] for a in aliases} != {r["episode_id"] for r in rows}:
        raise ValueError("Incomplete old-row mapping")
    return resolved, quarantined, aliases


def main():
    """Portable restricted-input CLI; no private paths are bundled in code.

    --sources JSON is {"sources": [{"station_id": "ST-X", "source_ref":
    "SRC-X", "provider": "claude_home", "path": "raw/source.jsonl",
    "sha256": "<64-hex>", "bytes": 123}]}. Relative paths resolve beside that
    descriptor. Supply every supported source needed by the input frame.
    Codex sources are reread to verify the pinned v2 completion traces before
    applying the same boundary and lexical correction to every provider.
    """
    import argparse
    import csv
    import importlib.util
    import os
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Restricted v2 51-field CSV")
    parser.add_argument("--sources", type=Path, required=True, help="Pinned private source-descriptor JSON")
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--cutoff", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="New private output directory")
    parser.add_argument("--screen", type=Path, default=Path(__file__).with_name("postrun-context-screen.py"))
    args = parser.parse_args()
    os.umask(0o077)
    sys.dont_write_bytecode = True
    csv.field_size_limit(sys.maxsize)
    if args.out.exists() and any(args.out.iterdir()):
        raise ValueError("Output directory must be new or empty; originals are never overwritten")
    args.out.mkdir(mode=0o700, parents=True, exist_ok=True)
    args.out.chmod(0o700)
    def receipt(path):
        h = hashlib.sha256()
        with path.open("rb") as f:
            for b in iter(lambda: f.read(1048576), b""):
                h.update(b)
        return {"path": str(path), "bytes": path.stat().st_size, "sha256": h.hexdigest()}
    pins = {k: receipt(p) for k, p in {"input": args.input, "sources": args.sources,
            "rules": args.rules, "cutoff": args.cutoff, "screen": args.screen, "engine": Path(__file__)}.items()}
    spec = importlib.util.spec_from_file_location("portable_v2_provider_adapter", args.screen)
    screen = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = screen
    spec.loader.exec_module(screen)
    rules = json.loads(args.rules.read_text())
    cutoff = seconds(json.loads(args.cutoff.read_text())["snapshot_observed_at_utc"])
    if cutoff is None:
        raise ValueError("Cutoff must be an observed timezone-aware timestamp")
    with args.input.open(newline="") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    if len(fields) != 51 or len({r["episode_id"] for r in rows}) != len(rows):
        raise ValueError("Input schema or episode identity invalid")
    by_id = {r["episode_id"]: r for r in rows}
    by_source = defaultdict(list)
    for r in rows:
        if r["provider"] in PROVIDERS:
            by_source[r["source_ref"]].append(r)
        elif r["provider"] != "codex_rollout":
            raise ValueError("Unsupported input provider")
    descriptor = json.loads(args.sources.read_text())
    inventory = descriptor["sources"] if isinstance(descriptor, dict) else descriptor
    inventory = [dict(s) for s in inventory if s["provider"] in PROVIDERS]
    for s in inventory:
        p = Path(s["path"])
        s["path"] = str(p if p.is_absolute() else args.sources.parent / p)
    if len({s["source_ref"] for s in inventory}) != len(inventory) or not set(by_source).issubset({s["source_ref"] for s in inventory}):
        raise ValueError("Missing or duplicated source descriptors")
    extracted = [extract_source(s, by_source[s["source_ref"]], screen, rules, cutoff)
                 for s in sorted(inventory, key=lambda s: (s["station_id"], s["source_ref"]))]
    result = normalize_sources(extracted, by_id, screen, rules)
    resolved, quarantined, aliases = assemble_frames(result, rows)
    def output_csv(name, header, values):
        with (args.out / name).open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
            writer.writeheader()
            writer.writerows(values)
    def output_json(name, value):
        (args.out / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    output_csv("normalized_merged_v5.local.csv", fields, resolved)
    output_csv("quarantined_events_v5.local.csv", fields, quarantined)
    if aliases:
        output_csv("event_alias_map.private.csv", list(aliases[0]), aliases)
    with (args.out / "event_provenance.private.jsonl").open("w") as f:
        for event in result["events"]:
            f.write(canonical(event["proof"]) + "\n")
    output_json("identity_edges.private.json", result["identity_edges"])
    output_json("boundary_edges.private.json", result["boundary_edges"])
    output_json("attribution.private.json", result["attribution"])
    output_json("source_receipts.private.json", {"sources": inventory, "pins": pins})
    summary = {"version": VERSION, "normalization": result["counts"], "resolved_frame_rows": len(resolved),
               "quarantined_frame_rows": len(quarantined), "old_row_aliases": len(aliases),
               "rescreened_codex_input_rows": sum(r["provider"] == "codex_rollout" for r in rows),
               "pins": pins, "human_labels_added": 0, "canonical_inputs_modified": False}
    output_json("NORMALIZATION_SUMMARY.json", summary)
    for p in args.out.iterdir():
        if p.is_file():
            p.chmod(0o600)
    print(json.dumps({k: v for k, v in summary.items() if k != "pins"}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Smoke-test huddle state and review scripts end to end."""

from __future__ import annotations

import base64
import gzip
import json
import shutil
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> str:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    result = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True, check=True, env=merged_env)
    return result.stdout.strip()


def decode_hash(url: str) -> dict:
    hash_value = url.split("#", 1)[1]
    padding = "=" * ((4 - len(hash_value) % 4) % 4)
    raw = base64.urlsafe_b64decode(hash_value + padding)
    return json.loads(gzip.decompress(raw).decode("utf-8"))


SAMPLE_STATE = {
    "reponame": "huddle",
    "branch": "main",
    "last_huddle_date": "2026-04-05",
    "current_topic": "Should we simplify Elango's state model?",
    "open_questions": ["How does LLM generate graph view reliably?"],
    "action_items": ["Update elango-specwriter.md"],
    "latest_summary": "Decided to drop graph-raw.json in favour of huddle-state.json",
    "active_personas": ["suren", "babu"],
    "decisions": [
        {
            "id": "d-1",
            "topic": "Simplify Elango state model",
            "status": "closed",
            "decision": "Drop graph-raw.json, derive graph from huddle-state.json",
            "rationale": "Simpler state means Elango reliably captures decisions every round",
            "rejected_paths": ["Keep graph-raw.json as always-on"],
            "personas_involved": [
                {"id": "suren", "name": "Suren", "icon": "🏛️", "meta": "Architect"},
                {"id": "babu", "name": "Babu", "icon": "🎯", "meta": "Demand Reality"},
            ],
            "linked_topics": ["d-2"],
            "evidence": [
                {
                    "ref": "https://github.com/m-agentic-skills/huddle/tree/main",
                    "label": "",
                    "note": "Source branch for this discussion",
                }
            ],
        },
        {
            "id": "d-2",
            "topic": "Evidence tracking",
            "status": "open",
            "decision": "",
            "rationale": "",
            "rejected_paths": [],
            "personas_involved": [],
            "linked_topics": [],
            "evidence": [
                {
                    "ref": "https://github.com/m-agentic-skills/huddle/issues/12",
                    "label": "",
                    "note": "Related issue on evidence schema",
                }
            ],
        },
    ],
    "participants": [
        {"id": "suren", "name": "Suren", "icon": "🏛️", "meta": "Architect", "influence": "Proposed read-before-write rule"},
        {"id": "babu", "name": "Babu", "icon": "🎯", "meta": "Demand Reality", "influence": "Flagged event schema complexity"},
    ],
    "key_moments": [
        {"id": "m-1", "icon": "💬", "title": "graph-raw.json complexity raised", "detail": "Event schema too rigid for LLM"},
        {"id": "m-2", "icon": "✅", "title": "Decision: derive graph from huddle-state.json", "detail": "index.html handles derivation client-side"},
    ],
}


def test_meeting_state_ensure(env: dict) -> None:
    out = run(
        ["python3", "scripts/meeting_state.py", "ensure", "sample-repo", "main", "2026-04-05"],
        cwd=ROOT,
        env=env,
    )
    result = json.loads(out)

    assert "huddle_state_file" in result, "missing huddle_state_file"
    assert "huddle_note_file" in result, "missing huddle_note_file"
    assert "graph_raw_file" not in result, "graph_raw_file should not appear"

    state = json.loads(Path(result["huddle_state_file"]).read_text())
    assert state["decisions"] == [], "decisions should start empty"
    assert state["participants"] == [], "participants should start empty"
    assert state["key_moments"] == [], "key_moments should start empty"

    assert not (Path(result["huddle_state_file"]).parent / "graph-raw.json").exists(), \
        "graph-raw.json should not be created"

    print("  [ok] meeting_state ensure — schema correct, no graph-raw.json")


def test_md_to_html(sample: Path) -> None:
    note = sample / "2026-04-05.md"
    note.write_text("# Huddle\n\n## Topics Discussed\n\nElango state simplification.\n", encoding="utf-8")

    state_path = sample / "huddle-state.json"
    state_path.write_text(json.dumps(SAMPLE_STATE, ensure_ascii=False), encoding="utf-8")

    url = run(
        [
            "python3", "scripts/md_to_html.py", str(note),
            "https://m-agentic-skills.github.io/huddle/index.html",
        ],
        cwd=ROOT,
    )

    assert "#" in url, "URL missing hash fragment"

    bundle = decode_hash(url)
    assert bundle["source"] == "2026-04-05.md", f"wrong source: {bundle['source']}"
    assert "markdown" in bundle, "bundle missing markdown"
    assert "state" in bundle, "bundle missing state"
    assert "view" not in bundle, "bundle should not contain pre-derived view"
    assert "raw" not in bundle, "bundle should not contain raw"

    state = bundle["state"]
    assert len(state["decisions"]) == 2, f"expected 2 decisions, got {len(state['decisions'])}"
    assert state["decisions"][0]["id"] == "d-1"
    assert state["decisions"][0]["status"] == "closed"
    assert state["decisions"][1]["id"] == "d-2"
    assert state["decisions"][1]["status"] == "open"

    d1_evidence = state["decisions"][0]["evidence"]
    assert len(d1_evidence) == 1, f"expected 1 evidence on d-1, got {len(d1_evidence)}"
    assert "github.com" in d1_evidence[0]["ref"], "d-1 evidence ref wrong"

    d2_evidence = state["decisions"][1]["evidence"]
    assert len(d2_evidence) == 1, f"expected 1 evidence on d-2, got {len(d2_evidence)}"
    assert "issues/12" in d2_evidence[0]["ref"], "d-2 evidence ref wrong"

    assert len(state["participants"]) == 2
    assert state["participants"][0]["id"] == "suren"
    assert state["participants"][1]["id"] == "babu"

    assert len(state["key_moments"]) == 2
    assert state["key_moments"][0]["id"] == "m-1"
    assert state["key_moments"][1]["id"] == "m-2"

    print("  [ok] md_to_html — state bundle correct, evidence in decisions, no raw/view")


def test_graph_state_py_removed() -> None:
    assert not (ROOT / "scripts" / "graph_state.py").exists(), "graph_state.py still exists"
    print("  [ok] graph_state.py removed")


def test_full_pipeline(sample: Path) -> None:
    """Full pipeline: raw events → synthesis → md_to_html → JS graph derivation."""

    # ── Stage 1: Write raw events (fast, no evidence, no LLM) ──
    raw_dir = sample / "pipeline" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_events = [
        {
            "type": "decision",
            "ts": 1744307200000,
            "topic": "Use WebSocket for real-time updates",
            "content": "WebSocket over SSE for bi-directional communication",
            "personas": ["Shaama", "Suren"],
            "by": "muthu",
            "rejected": ["Server-Sent Events", "Long polling"],
            "open": ["Connection pooling strategy"],
        },
        {
            "type": "milestone",
            "ts": 1744307400000,
            "topic": "Security concern on WebSocket auth",
            "content": "Token refresh handling needed for WS connections",
            "personas": ["Senthil", "Shaama"],
        },
        {
            "type": "decision",
            "ts": 1744307600000,
            "topic": "Token refresh via dedicated auth channel",
            "content": "Separate auth channel refreshes tokens before WS reconnect",
            "personas": ["Senthil", "Suren"],
            "by": "muthu",
            "rejected": ["Inline token in each message"],
            "open": [],
        },
    ]

    for evt in raw_events:
        fname = f"{evt['ts']}_{evt['type']}.json"
        (raw_dir / fname).write_text(json.dumps(evt), encoding="utf-8")

    # Verify raw events have NO evidence field
    for f in raw_dir.iterdir():
        data = json.loads(f.read_text())
        assert "evidence" not in data, f"raw event {f.name} should NOT have evidence"

    # ── Stage 2: Synthesis (LLM would do this — we simulate) ──
    # Read raw events in timestamp order
    raw_files = sorted(raw_dir.iterdir(), key=lambda p: p.name)
    events = [json.loads(f.read_text()) for f in raw_files]
    assert len(events) == 3, f"expected 3 raw events, got {len(events)}"

    # Synthesis: build huddle-state.json with evidence from "conversation context"
    huddle_state = {
        "reponame": "myapp",
        "branch": "main",
        "last_huddle_date": "2026-04-15",
        "current_topic": "Real-time communication architecture",
        "open_questions": ["Connection pooling strategy"],
        "action_items": ["Prototype WebSocket auth flow"],
        "latest_summary": "Decided on WebSocket with separate auth channel for token refresh",
        "active_personas": ["shaama", "suren", "senthil"],
        "decisions": [
            {
                "id": "d-1",
                "topic": events[0]["topic"],
                "status": "closed",
                "decision": events[0]["content"],
                "rationale": "WebSocket supports bi-directional real-time communication",
                "rejected_paths": events[0].get("rejected", []),
                "personas_involved": [
                    {"id": "shaama", "name": "Shaama", "icon": "⚙️", "meta": "Engineering"},
                    {"id": "suren", "name": "Suren", "icon": "🏛️", "meta": "Architect"},
                ],
                "linked_topics": [],
                # Evidence extracted from conversation context during synthesis
                "evidence": [
                    {"ref": "https://github.com/myapp/myapp/issues/42", "note": "Original feature request"},
                    {"ref": "https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API", "label": "MDN WebSocket docs", "note": "API reference"},
                ],
            },
            {
                "id": "d-2",
                "topic": events[2]["topic"],
                "status": "closed",
                "decision": events[2]["content"],
                "rationale": "Keeps auth concerns separated from data channel",
                "rejected_paths": events[2].get("rejected", []),
                "personas_involved": [
                    {"id": "senthil", "name": "Senthil", "icon": "🔒", "meta": "Security"},
                    {"id": "suren", "name": "Suren", "icon": "🏛️", "meta": "Architect"},
                ],
                "linked_topics": ["d-1"],
                "evidence": [
                    {"ref": "https://github.com/myapp/myapp/pull/38", "note": "Prior auth implementation"},
                ],
            },
        ],
        "participants": [
            {"id": "shaama", "name": "Shaama", "icon": "⚙️", "meta": "Engineering", "influence": "Evaluated WS vs SSE tradeoffs"},
            {"id": "suren", "name": "Suren", "icon": "🏛️", "meta": "Architect", "influence": "Proposed WebSocket architecture"},
            {"id": "senthil", "name": "Senthil", "icon": "🔒", "meta": "Security", "influence": "Flagged auth token refresh gap"},
        ],
        "key_moments": [
            {"id": "m-1", "icon": "⚠️", "title": "Security concern on WebSocket auth", "detail": "Token refresh handling flagged by Senthil"},
        ],
    }

    pipeline_dir = sample / "pipeline"
    state_path = pipeline_dir / "huddle-state.json"
    state_path.write_text(json.dumps(huddle_state, ensure_ascii=False), encoding="utf-8")

    note_path = pipeline_dir / "2026-04-15.md"
    note_path.write_text(
        "# Huddle — myapp\n\n## Topics Discussed\n\nReal-time communication architecture.\n",
        encoding="utf-8",
    )

    # Clean up raw dir (synthesis deletes raw files)
    shutil.rmtree(raw_dir)
    assert not raw_dir.exists(), "raw dir should be deleted after synthesis"

    # ── Stage 3: Bundle via real md_to_html.py ──
    url = run(
        ["python3", "scripts/md_to_html.py", str(note_path),
         "https://m-agentic-skills.github.io/huddle/index.html"],
        cwd=ROOT,
    )
    assert "#" in url, "URL missing hash fragment"

    bundle = decode_hash(url)
    assert "state" in bundle, "bundle missing state"
    assert bundle["state"]["decisions"][0]["evidence"], "d-1 evidence missing after bundle"
    assert bundle["state"]["decisions"][1]["evidence"], "d-2 evidence missing after bundle"

    # ── Stage 4: Run REAL JavaScript from index.html ──
    # Extract the JS functions and run them with Node.js against the bundled state
    index_html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

    # Extract deriveGraphViewFromState and its dependencies
    js_test = """
    // -- Functions extracted from index.html --
    function domainFromRef(ref) {
      try { return new URL(ref).hostname.replace(/^www\\./, ""); } catch { return ""; }
    }
    function autoLabelFromRef(ref) {
      const ghBranch = ref.match(/github\\.com\\/([^/]+)\\/([^/]+)\\/(tree|blob)\\/([^/?#]+)/);
      if (ghBranch) return `${ghBranch[1]}/${ghBranch[2]} — ${ghBranch[4]}`;
      const ghPR = ref.match(/github\\.com\\/([^/]+)\\/([^/]+)\\/(pull|issues)\\/(\\d+)/);
      if (ghPR) return `${ghPR[1]}/${ghPR[2]} #${ghPR[4]}`;
      return domainFromRef(ref) || ref;
    }
    DERIVE_FN_PLACEHOLDER

    // -- Allowed values from index.html --
    const kindShape = {
      issue: "round-rectangle", idea: "round-rectangle", option: "round-rectangle",
      challenge: "diamond", decision: "diamond", "missing-question": "round-rectangle",
      deferred: "round-rectangle", rejected: "round-rectangle",
      unresolved: "round-rectangle", evidence: "hexagon",
    };
    const kindRank = {
      evidence: 0, issue: 1, idea: 1, option: 1, challenge: 1,
      decision: 2, "missing-question": 3, deferred: 3, rejected: 3, unresolved: 3,
    };

    // -- Run against bundled state --
    const state = STATE_PLACEHOLDER;
    const view = deriveGraphViewFromState(state);

    const errors = [];

    // Check top-level fields
    if (!view.main_question) errors.push("missing main_question");
    if (!view.decision) errors.push("missing decision");
    if (!view.decision_why) errors.push("missing decision_why");

    // Check nodes
    if (!view.nodes || view.nodes.length === 0) errors.push("no nodes generated");
    for (const node of (view.nodes || [])) {
      if (!node.id) errors.push(`node missing id`);
      if (!(node.kind in kindShape)) errors.push(`node ${node.id}: invalid kind "${node.kind}" not in kindShape`);
      if (!(node.kind in kindRank)) errors.push(`node ${node.id}: invalid kind "${node.kind}" not in kindRank`);
      if (!node.source_refs) errors.push(`node ${node.id}: missing source_refs`);
    }

    // Check evidence
    if (!view.evidence || view.evidence.length === 0) errors.push("no evidence generated");
    const sourceMap = new Map((view.evidence || []).map(s => [s.id, s]));
    for (const ev of (view.evidence || [])) {
      if (!ev.id) errors.push(`evidence missing id (ref: ${ev.ref})`);
      if (!ev.ref) errors.push(`evidence missing ref`);
      if (!ev.label) errors.push(`evidence ${ev.id}: missing label`);
    }

    // Check source_refs linkage (the critical path)
    let linkedCount = 0;
    for (const node of (view.nodes || [])) {
      for (const ref of (node.source_refs || [])) {
        if (sourceMap.has(ref)) {
          linkedCount++;
        } else {
          errors.push(`node ${node.id}: source_ref "${ref}" not found in evidence`);
        }
      }
    }
    if (linkedCount === 0) errors.push("no nodes linked to evidence via source_refs");

    // Check edges
    if (!view.edges || view.edges.length === 0) errors.push("no edges generated");
    const nodeIds = new Set((view.nodes || []).map(n => n.id));
    for (const edge of (view.edges || [])) {
      if (!nodeIds.has(edge.from)) errors.push(`edge from "${edge.from}" references missing node`);
      if (!nodeIds.has(edge.to)) errors.push(`edge to "${edge.to}" references missing node`);
    }

    // Check participants
    if (!view.people_involved || view.people_involved.length === 0) errors.push("no people_involved");

    // Check key_moments
    if (!view.key_moments || view.key_moments.length === 0) errors.push("no key_moments");

    // Output results
    const result = {
      ok: errors.length === 0,
      errors,
      stats: {
        nodes: (view.nodes || []).length,
        edges: (view.edges || []).length,
        evidence: (view.evidence || []).length,
        linked_evidence: linkedCount,
        people: (view.people_involved || []).length,
        moments: (view.key_moments || []).length,
      },
      nodes: (view.nodes || []).map(n => ({
        id: n.id, kind: n.kind, status: n.status,
        source_refs: n.source_refs,
        evidence_labels: (n.source_refs || []).map(id => sourceMap.get(id)?.label).filter(Boolean),
      })),
      evidence: (view.evidence || []).map(e => ({ id: e.id, label: e.label, ref: e.ref })),
      edges: view.edges,
    };
    console.log(JSON.stringify(result, null, 2));
    """

    # Extract the real deriveGraphViewFromState function from index.html
    import re
    fn_match = re.search(
        r'(function deriveGraphViewFromState\(state\) \{.*?\n    \})',
        index_html,
        re.DOTALL,
    )
    assert fn_match, "could not extract deriveGraphViewFromState from index.html"
    derive_fn = fn_match.group(1)

    js_code = js_test.replace("DERIVE_FN_PLACEHOLDER", derive_fn)
    js_code = js_code.replace("STATE_PLACEHOLDER", json.dumps(bundle["state"]))

    js_path = sample / "pipeline_test.js"
    js_path.write_text(js_code, encoding="utf-8")

    result_str = run(["node", str(js_path)])
    result = json.loads(result_str)

    if not result["ok"]:
        for err in result["errors"]:
            print(f"    FAIL: {err}", file=sys.stderr)
        raise AssertionError(f"graph pipeline failed with {len(result['errors'])} errors")

    s = result["stats"]
    assert s["nodes"] >= 2, f"expected >=2 nodes, got {s['nodes']}"
    assert s["edges"] >= 1, f"expected >=1 edges, got {s['edges']}"
    assert s["evidence"] >= 2, f"expected >=2 evidence, got {s['evidence']}"
    assert s["linked_evidence"] >= 2, f"expected >=2 evidence links, got {s['linked_evidence']}"
    assert s["people"] >= 2, f"expected >=2 people, got {s['people']}"
    assert s["moments"] >= 1, f"expected >=1 moments, got {s['moments']}"

    # Verify evidence auto-labeling worked (empty labels got auto-generated)
    for ev in result["evidence"]:
        assert ev["label"], f"evidence {ev['id']} has empty label (auto-label failed)"

    # Verify node→evidence linkage is correct
    for node in result["nodes"]:
        if node["source_refs"]:
            assert node["evidence_labels"], f"node {node['id']} has source_refs but no resolved labels"

    print(f"  [ok] full pipeline — {s['nodes']} nodes, {s['edges']} edges, "
          f"{s['evidence']} evidence, {s['linked_evidence']} links, "
          f"{s['people']} people, {s['moments']} moments")

    # ── Stage 5: Test fallback path (no decisions, only open questions) ──
    fallback_state = {
        "reponame": "myapp",
        "branch": "main",
        "last_huddle_date": "2026-04-15",
        "current_topic": "What should we build next?",
        "open_questions": ["Should we add real-time?", "Do we need a mobile app?"],
        "action_items": [],
        "latest_summary": "Early exploration phase",
        "active_personas": ["suren"],
        "decisions": [],
        "participants": [
            {"id": "suren", "name": "Suren", "icon": "🏛️", "meta": "Architect", "influence": "Led exploration"},
        ],
        "key_moments": [
            {"id": "m-1", "icon": "💡", "title": "Market gap identified", "detail": "No good real-time solution exists"},
        ],
    }

    # Fallback test: relax evidence checks since no decisions = no evidence
    js_fallback_test = """
    DERIVE_FN_PLACEHOLDER

    function domainFromRef(ref) {
      try { return new URL(ref).hostname.replace(/^www\\./, ""); } catch { return ""; }
    }
    function autoLabelFromRef(ref) {
      const ghBranch = ref.match(/github\\.com\\/([^/]+)\\/([^/]+)\\/(tree|blob)\\/([^/?#]+)/);
      if (ghBranch) return `${ghBranch[1]}/${ghBranch[2]} — ${ghBranch[4]}`;
      const ghPR = ref.match(/github\\.com\\/([^/]+)\\/([^/]+)\\/(pull|issues)\\/(\\d+)/);
      if (ghPR) return `${ghPR[1]}/${ghPR[2]} #${ghPR[4]}`;
      return domainFromRef(ref) || ref;
    }

    const kindShape = {
      issue: "round-rectangle", idea: "round-rectangle", option: "round-rectangle",
      challenge: "diamond", decision: "diamond", "missing-question": "round-rectangle",
      deferred: "round-rectangle", rejected: "round-rectangle",
      unresolved: "round-rectangle", evidence: "hexagon",
    };
    const kindRank = {
      evidence: 0, issue: 1, idea: 1, option: 1, challenge: 1,
      decision: 2, "missing-question": 3, deferred: 3, rejected: 3, unresolved: 3,
    };

    const state = STATE_PLACEHOLDER;
    const view = deriveGraphViewFromState(state);
    const errors = [];

    if (!view.nodes || view.nodes.length === 0) errors.push("no nodes generated");
    for (const node of (view.nodes || [])) {
      if (!node.id) errors.push("node missing id");
      if (!(node.kind in kindShape)) errors.push(`node ${node.id}: invalid kind "${node.kind}"`);
      if (!(node.kind in kindRank)) errors.push(`node ${node.id}: invalid kind "${node.kind}" in kindRank`);
      if (!Array.isArray(node.source_refs)) errors.push(`node ${node.id}: source_refs not an array`);
    }
    if (!view.edges || view.edges.length === 0) errors.push("no edges in fallback");
    const nodeIds = new Set((view.nodes || []).map(n => n.id));
    for (const edge of (view.edges || [])) {
      if (!nodeIds.has(edge.from)) errors.push(`edge from "${edge.from}" references missing node`);
      if (!nodeIds.has(edge.to)) errors.push(`edge to "${edge.to}" references missing node`);
    }

    console.log(JSON.stringify({
      ok: errors.length === 0,
      errors,
      nodes: view.nodes.length,
      edges: view.edges.length,
      node_kinds: view.nodes.map(n => n.kind),
    }, null, 2));
    """

    js_fb = js_fallback_test.replace("DERIVE_FN_PLACEHOLDER", derive_fn)
    js_fb = js_fb.replace("STATE_PLACEHOLDER", json.dumps(fallback_state))
    fb_path = sample / "pipeline_fallback.js"
    fb_path.write_text(js_fb, encoding="utf-8")

    fb_str = run(["node", str(fb_path)])
    fb_result = json.loads(fb_str)

    if not fb_result["ok"]:
        for err in fb_result["errors"]:
            print(f"    FAIL: {err}", file=sys.stderr)
        raise AssertionError(f"fallback pipeline failed with {len(fb_result['errors'])} errors")

    assert fb_result["nodes"] >= 3, f"fallback expected >=3 nodes, got {fb_result['nodes']}"
    assert fb_result["edges"] >= 2, f"fallback expected >=2 edges, got {fb_result['edges']}"

    for kind in fb_result["node_kinds"]:
        assert kind in ("issue", "missing-question", "evidence"), \
            f"fallback node has unexpected kind '{kind}'"

    print(f"  [ok] fallback path — {fb_result['nodes']} nodes, {fb_result['edges']} edges (no decisions)")


def main() -> int:
    tmp_root = Path(tempfile.mkdtemp(prefix="huddle-e2e-"))
    home = tmp_root / "home"
    sample = tmp_root / "sample"
    home.mkdir(parents=True, exist_ok=True)
    sample.mkdir(parents=True, exist_ok=True)

    env = {"HOME": str(home)}

    try:
        print("Running e2e tests...")
        test_meeting_state_ensure(env)
        test_md_to_html(sample)
        test_graph_state_py_removed()
        test_full_pipeline(sample)
        print("\ne2e ok")
        return 0
    except AssertionError as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

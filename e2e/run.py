#!/usr/bin/env python3
"""Smoke-test huddle state and synced-asset scripts end to end."""

from __future__ import annotations

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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_global_state(home: Path) -> None:
    out = run(["python3", "scripts/global_state.py"], cwd=ROOT, env={"HOME": str(home)})
    first = json.loads(out)
    assert first["python_bin"], "python_bin not detected"
    assert first["git_user"], "git_user not resolved"
    assert "gh_available" in first, "gh_available missing"
    assert "<persona-roster" in first["persona_roster_xml"], "persona roster missing"
    # t5 (regression): no synced personas dir -> empty list, key present
    assert first["synced_personas_global"] == [], "synced_personas_global should be [] with no synced dir"

    uc = home / ".config" / "muthuishere-agent-skills" / "userconfig.json"
    assert uc.exists(), "userconfig.json not written"
    cached = json.loads(uc.read_text())
    assert cached["python_bin"] == first["python_bin"], "python_bin not cached"
    assert cached["git_user"] == first["git_user"], "git_user not cached"

    uc.write_text(json.dumps({**cached, "git_user": "Sentinel"}), encoding="utf-8")
    out2 = run(["python3", "scripts/global_state.py"], cwd=ROOT, env={"HOME": str(home)})
    second = json.loads(out2)
    assert second["git_user"] == "Sentinel", "cached git_user not honored on second call"

    print("  [ok] global_state — detects, caches, honors cache on repeat")


def test_project_state_snapshot(home: Path, tmp: Path) -> None:
    project = tmp / "sample-proj"
    project.mkdir(parents=True, exist_ok=True)
    (project / "README.md").write_text("hi", encoding="utf-8")
    for i in range(25):
        (project / f"f{i}.txt").write_text("x", encoding="utf-8")

    repo_root = home / ".config" / "muthuishere-agent-skills" / "sample-proj"
    (repo_root / "main" / "huddle" / "raw").mkdir(parents=True, exist_ok=True)
    (repo_root / "main" / "huddle" / "raw" / "20260401T000000_decision.json").write_text(
        json.dumps({"kind": "decision", "ts": "2026-04-01T00:00:00Z"}),
        encoding="utf-8",
    )
    (repo_root / "feature-x" / "huddle").mkdir(parents=True, exist_ok=True)
    (repo_root / "feature-x" / "huddle" / "2026-04-15.md").write_text(
        "# Huddle\n\n## Latest Summary\nSketched new script.\n",
        encoding="utf-8",
    )

    out = run(
        ["python3", "scripts/project_state.py", "snapshot", str(project)],
        cwd=ROOT,
        env={"HOME": str(home)},
    )
    snap = json.loads(out)
    assert snap["reponame"] == "sample-proj", f"wrong reponame: {snap['reponame']}"
    assert "huddle_state_file" in snap, "missing huddle_state_file"
    assert snap["project_scan"]["scan"] is False, "no git repo → scan should be False"
    assert snap["saved_state"]["decisions"] == [], "saved_state should default empty"
    raw = snap["raw_events"]
    assert len(raw) == 1 and raw[0]["kind"] == "decision", f"raw_events wrong: {raw}"
    branches = [e["branch"] for e in snap["cross_branch_context"]]
    assert branches == ["feature-x"], f"unexpected cross-branch list: {branches}"
    assert snap["project_docs_found"] == [], "no docs were added, list should be empty"
    # t5 (regression): no synced repo personas dir -> empty list, key present
    assert snap["repo_personas"] == [], "repo_personas should be [] with no synced dir"
    print("  [ok] project_state snapshot — identity, raw events, cross-branch, saved_state")


def test_project_state_doc_detection(home: Path, tmp: Path) -> None:
    bare = tmp / "bare-proj"
    bare.mkdir(parents=True, exist_ok=True)
    for i in range(25):
        (bare / f"src{i}.py").write_text("pass\n", encoding="utf-8")
    out = run(
        ["python3", "scripts/project_state.py", "snapshot", str(bare)],
        cwd=ROOT, env={"HOME": str(home)},
    )
    snap = json.loads(out)
    assert snap["project_docs_found"] == [], f"bare repo should have no docs: {snap['project_docs_found']}"

    documented = tmp / "documented-proj"
    documented.mkdir(parents=True, exist_ok=True)
    for i in range(25):
        (documented / f"src{i}.py").write_text("pass\n", encoding="utf-8")
    (documented / "README.md").write_text("# Project\n\n" + ("Real content. " * 50), encoding="utf-8")
    (documented / "CLAUDE.md").write_text("# Guide\n\n" + ("More context. " * 50), encoding="utf-8")
    (documented / "docs").mkdir()
    (documented / "docs" / "overview.md").write_text("# Overview\n\n" + ("Details. " * 50), encoding="utf-8")

    out = run(
        ["python3", "scripts/project_state.py", "snapshot", str(documented)],
        cwd=ROOT, env={"HOME": str(home)},
    )
    snap = json.loads(out)
    found = set(snap["project_docs_found"])
    assert "README.md" in found, f"README.md not detected: {found}"
    assert "CLAUDE.md" in found, f"CLAUDE.md not detected: {found}"
    assert any(p.startswith("docs/") for p in found), f"docs/*.md not detected: {found}"
    assert snap["project_doc_missing"] is False, \
        "project_doc_missing should flip false once real docs are present"

    tiny = tmp / "tiny-readme-proj"
    tiny.mkdir(parents=True, exist_ok=True)
    for i in range(25):
        (tiny / f"src{i}.py").write_text("pass\n", encoding="utf-8")
    (tiny / "README.md").write_text("# x\n", encoding="utf-8")
    out = run(
        ["python3", "scripts/project_state.py", "snapshot", str(tiny)],
        cwd=ROOT, env={"HOME": str(home)},
    )
    snap = json.loads(out)
    assert snap["project_docs_found"] == [], \
        f"tiny README should not count as docs: {snap['project_docs_found']}"

    print("  [ok] project_state doc detection — README/CLAUDE.md/docs trigger, tiny stubs don't")


def test_session_state(home: Path, tmp: Path) -> None:
    project = tmp / "sess-proj"
    project.mkdir(parents=True, exist_ok=True)
    out = run(
        ["python3", "scripts/session_state.py", str(project), "2026-04-21"],
        cwd=ROOT,
        env={"HOME": str(home)},
    )
    sess = json.loads(out)
    assert sess["reponame"] == "sess-proj", f"wrong reponame: {sess['reponame']}"
    assert sess["is_resume"] is False, "fresh note should not be resume"
    assert sess["git_status"] == [], "expected empty git_status in non-repo dir"
    assert Path(sess["huddle_note_file"]).exists(), "note file not created"
    print("  [ok] session_state — live probes + note ensured")


def test_synced_personas_global(home: Path) -> None:
    """t1 (definition), t3 (memories), t4 (built-in id-clash), t6 (malformed non-fatal)."""
    personas = home / ".config" / "muthuishere-agent-skills" / "personas"

    # t1: a global synced persona with a definition file
    _write(
        personas / "bharath" / "bharath.md",
        "---\n"
        "name: acme-billing-expert\n"
        "displayName: Bharath\n"
        "title: Billing Domain Expert\n"
        'icon: "💳"\n'
        "domains: [billing, proration, revenue]\n"
        "---\n\n## Signature Phrases\n- \"Does the money reconcile?\"\n",
    )
    # t3: a per-persona memory under that persona
    _write(
        personas / "bharath" / "memories" / "q3-pricing.md",
        "---\ntitle: Q3 pricing decision\ntags: [pricing, gtm]\ncorpus: acme-finance\n"
        "---\nPro stays at $40/seat through Q3.\n",
    )
    # t4: id-clash with a built-in — memory-only augmentation, no definition
    _write(
        personas / "shaama" / "memories" / "oncall.md",
        "---\ntitle: The 2am cache stampede\ntags: [reliability]\n---\nNever cache without jitter.\n",
    )
    # t6: a malformed file in its own persona dir must not abort the scan
    _write(personas / "broken" / "broken.md", "not: [valid frontmatter\nno closing")

    out = run(["python3", "scripts/global_state.py"], cwd=ROOT, env={"HOME": str(home)})
    snap = json.loads(out)
    synced = {p["id"]: p for p in snap["synced_personas_global"]}

    # t1
    assert "bharath" in synced, "global synced persona not listed"
    b = synced["bharath"]
    assert b["name"] == "Bharath", f"displayName not mapped: {b['name']}"
    assert b["title"] == "Billing Domain Expert"
    assert b["icon"] == "💳", "quoted icon not parsed"
    assert b["domains"] == ["billing", "proration", "revenue"], f"inline list wrong: {b['domains']}"
    assert b["source"] == "synced-global"
    assert b["file"] and b["file"].endswith("personas/bharath/bharath.md"), f"bad file: {b['file']}"

    # t3
    assert len(b["memories"]) == 1, f"expected 1 memory, got {len(b['memories'])}"
    mem = b["memories"][0]
    assert mem["title"] == "Q3 pricing decision"
    assert mem["tags"] == ["pricing", "gtm"]
    assert mem["corpus"] == "acme-finance"
    assert mem["persona"] == "bharath"
    assert mem["file"].endswith("memories/q3-pricing.md")

    # t4 — built-in id reused, memory-only (file is None so step-01 keeps built-in body)
    assert "shaama" in synced, "built-in augmentation entry missing"
    assert synced["shaama"]["file"] is None, "memory-only entry should have file=None"
    assert len(synced["shaama"]["memories"]) == 1, "built-in augmentation memory missing"

    # t6 — malformed file is non-fatal; the good entries are still returned
    assert "bharath" in synced and "shaama" in synced, "good entries lost due to malformed file"

    print("  [ok] synced personas (global) — t1 definition, t3 memories, t4 id-clash, t6 malformed non-fatal")


def test_synced_personas_repo(home: Path, tmp: Path) -> None:
    """t2 — repo-scoped personas are visible only in their own repo."""
    project = tmp / "repo-with-personas"
    project.mkdir(parents=True, exist_ok=True)
    rpersonas = home / ".config" / "muthuishere-agent-skills" / "repo-with-personas" / "personas"
    _write(
        rpersonas / "vidya" / "vidya.md",
        "---\ndisplayName: Vidya\ntitle: Repo Analyst\n"
        'icon: "🔍"\ndomains: [repo, analysis]\n---\nbody\n',
    )

    out = run(
        ["python3", "scripts/project_state.py", "snapshot", str(project)],
        cwd=ROOT, env={"HOME": str(home)},
    )
    snap = json.loads(out)
    repo_p = {p["id"]: p for p in snap["repo_personas"]}
    assert "vidya" in repo_p, "repo persona not returned in its own repo"
    assert repo_p["vidya"]["source"] == "synced-repo"
    assert repo_p["vidya"]["file"].endswith("personas/vidya/vidya.md")

    # isolation: a different repo must not see it
    other = tmp / "other-repo"
    other.mkdir(parents=True, exist_ok=True)
    out2 = run(
        ["python3", "scripts/project_state.py", "snapshot", str(other)],
        cwd=ROOT, env={"HOME": str(home)},
    )
    snap2 = json.loads(out2)
    assert snap2["repo_personas"] == [], "a different repo must not see another repo's personas"

    print("  [ok] synced personas (repo) — t2 repo-scoped + cross-repo isolation")


def test_migrate_legacy_config(home: Path) -> None:
    old_root = home / "config" / "muthuishere-agent-skills" / "oldrepo" / "main" / "huddle"
    old_root.mkdir(parents=True, exist_ok=True)
    (old_root / "2026-01-01.md").write_text("legacy note", encoding="utf-8")
    (home / "config" / "muthuishere-agent-skills" / "oldrepo" / "config.json").write_text(
        '{"reponame":"oldrepo"}', encoding="utf-8"
    )

    run(["python3", "scripts/migrate.py"], cwd=ROOT, env={"HOME": str(home)})

    new_root = home / ".config" / "muthuishere-agent-skills" / "oldrepo"
    assert (new_root / "config.json").exists(), "config.json not moved"
    assert (new_root / "main" / "huddle" / "2026-01-01.md").exists(), "legacy note not moved"
    assert not (home / "config" / "muthuishere-agent-skills").exists(), \
        "legacy muthuishere-agent-skills dir should be cleaned up"

    run(["python3", "scripts/migrate.py"], cwd=ROOT, env={"HOME": str(home)})
    print("  [ok] migrate.py — legacy ~/config moved to ~/.config, idempotent")


def main() -> int:
    tmp_root = Path(tempfile.mkdtemp(prefix="huddle-e2e-"))
    home_global = tmp_root / "home-global"
    home_project = tmp_root / "home-project"
    home_session = tmp_root / "home-session"
    home_synced = tmp_root / "home-synced"
    home_synced_repo = tmp_root / "home-synced-repo"
    migrate_home = tmp_root / "migrate-home"
    tmp_projects = tmp_root / "projects"
    for p in (home_global, home_project, home_session, home_synced, home_synced_repo, migrate_home, tmp_projects):
        p.mkdir(parents=True, exist_ok=True)

    try:
        print("Running e2e tests...")
        test_global_state(home_global)
        test_project_state_snapshot(home_project, tmp_projects)
        test_project_state_doc_detection(home_project, tmp_projects)
        test_session_state(home_session, tmp_projects)
        test_synced_personas_global(home_synced)
        test_synced_personas_repo(home_synced_repo, tmp_projects)
        test_migrate_legacy_config(migrate_home)
        print("\ne2e ok")
        return 0
    except AssertionError as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

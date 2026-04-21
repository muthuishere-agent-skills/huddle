#!/usr/bin/env python3
"""
Live session probes — never cached, fresh every call.

Fires every shell probe in one parallel batch: git status, git log since
8h ago, git branch, git HEAD, and (when gh is authed) `gh pr list`. Also
ensures today's huddle files exist and reports whether today's note has
content (is_resume).

Usage:
    python3 session_state.py <project_root> <YYYY-MM-DD>
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor


CONFIG_ROOT = pathlib.Path.home() / ".config" / "muthuishere-agent-skills"
USERCONFIG_PATH = CONFIG_ROOT / "userconfig.json"

EMPTY_NOTE_TEMPLATE = (
    "# Huddle\n\n## Repo\n\n## Date\n\n## Participants\n\n"
    "## Topics Discussed\n\n## Decisions\n\n## Open Questions\n\n"
    "## Action Items\n\n## Latest Summary\n"
)


def _run(cmd, cwd=None, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def _sanitize_branch(branch):
    return branch.replace("/", "-").lstrip(".") or "unknown-branch"


def _parse_owner_repo(remote_url):
    m = re.search(r"[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote_url or "")
    if not m:
        return "", ""
    return m.group(2), f"{m.group(1)}/{m.group(2)}"


def _load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _gh_available() -> bool:
    uc = _load_json(USERCONFIG_PATH) or {}
    return bool(uc.get("gh_available"))


def _resolve_reponame(project_root):
    """Prefer a cached reponame from any repo config matching this project_root;
    else derive from git remote; else fall back to folder name."""
    folder = pathlib.Path(project_root).name
    if CONFIG_ROOT.is_dir():
        for cfg_file in CONFIG_ROOT.glob("*/config.json"):
            data = _load_json(cfg_file) or {}
            if str(data.get("local_project_root", "")) == project_root:
                return data.get("reponame") or folder
    cfg = _load_json(CONFIG_ROOT / folder / "config.json") or {}
    if cfg.get("reponame"):
        return cfg["reponame"]
    rc, remote_url = _run(["git", "remote", "get-url", "origin"], cwd=project_root)
    if rc == 0 and remote_url:
        name, _ = _parse_owner_repo(remote_url)
        if name:
            return name
    return folder


def _probe_git_status(cwd):
    rc, out = _run(["git", "status", "--short"], cwd=cwd)
    if rc != 0 or not out:
        return []
    return [line for line in out.splitlines() if line.strip()]


def _probe_git_log(cwd):
    rc, out = _run(["git", "log", "--oneline", "--since=8 hours ago"], cwd=cwd)
    if rc != 0 or not out:
        return []
    return out.splitlines()


def _probe_open_prs(cwd):
    if not _gh_available():
        return []
    rc, out = _run(
        ["gh", "pr", "list", "--limit", "5",
         "--json", "number,title,author,headRefName,isDraft"],
        cwd=cwd,
    )
    if rc != 0 or not out:
        return []
    try:
        return json.loads(out)
    except Exception:
        return []


def _ensure_note(hdir, date_str):
    hdir.mkdir(parents=True, exist_ok=True)
    note = hdir / f"{date_str}.md"
    if not note.exists():
        note.write_text(EMPTY_NOTE_TEMPLATE, encoding="utf-8")
    return note


def _note_has_content(path):
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").strip()
    return bool(text) and text != EMPTY_NOTE_TEMPLATE.strip()


def snapshot(project_root_str, date_str):
    project_root = str(pathlib.Path(project_root_str).resolve())

    with ThreadPoolExecutor(max_workers=5) as pool:
        f_branch = pool.submit(_run, ["git", "branch", "--show-current"], project_root)
        f_head   = pool.submit(_run, ["git", "rev-parse", "HEAD"], project_root)
        f_status = pool.submit(_probe_git_status, project_root)
        f_log    = pool.submit(_probe_git_log, project_root)
        f_prs    = pool.submit(_probe_open_prs, project_root)
        reponame = _resolve_reponame(project_root)

    rc, branch = f_branch.result()
    if rc != 0 or not branch:
        branch = "main"

    rc, head = f_head.result()
    if rc != 0:
        head = ""

    hdir = CONFIG_ROOT / reponame / _sanitize_branch(branch) / "huddle"
    note = _ensure_note(hdir, date_str)

    return {
        "reponame": reponame,
        "branch": branch,
        "head": head,
        "huddle_note_file": str(note),
        "is_resume": _note_has_content(note),
        "git_status": f_status.result(),
        "recent_commits": f_log.result(),
        "open_prs": f_prs.result(),
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    print(json.dumps(snapshot(sys.argv[1], sys.argv[2]), indent=2))

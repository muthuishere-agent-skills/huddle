#!/usr/bin/env python3
"""
Global, user-level state — cached across sessions in userconfig.json.

First call detects and caches git_user, python_bin, gh_available.
Subsequent calls are pure file reads (~1ms).

Also reads the skill-level persona roster and spawns one-time config
migration if the legacy ~/config/ tree is still around.

Usage:
    python3 global_state.py
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys


SKILL_ROOT = pathlib.Path(__file__).resolve().parent.parent
ROSTER_PATH = SKILL_ROOT / "references" / "persona-roster.xml"
CONFIG_ROOT = pathlib.Path.home() / ".config" / "muthuishere-agent-skills"
USERCONFIG_PATH = CONFIG_ROOT / "userconfig.json"
LEGACY_ROOT = pathlib.Path.home() / "config" / "muthuishere-agent-skills"


def _run(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def _load_userconfig() -> dict:
    if not USERCONFIG_PATH.exists():
        return {}
    try:
        return json.loads(USERCONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_userconfig(uc: dict) -> None:
    USERCONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    USERCONFIG_PATH.write_text(json.dumps(uc, indent=2) + "\n", encoding="utf-8")


def _maybe_spawn_migration() -> None:
    """First-time only: if the new config root doesn't exist but the legacy
    one does, spawn migrate.py detached."""
    if CONFIG_ROOT.exists() or not LEGACY_ROOT.is_dir():
        return
    script = pathlib.Path(__file__).parent / "migrate.py"
    if not script.exists():
        return
    try:
        subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


def _read_roster() -> str:
    if not ROSTER_PATH.exists():
        return ""
    try:
        return ROSTER_PATH.read_text(encoding="utf-8")
    except Exception:
        return ""


def snapshot() -> dict:
    _maybe_spawn_migration()

    uc = _load_userconfig()
    changed = False

    python_bin = uc.get("python_bin", "") or (shutil.which("python3") or shutil.which("python") or "")
    if python_bin and python_bin != uc.get("python_bin"):
        uc["python_bin"] = python_bin
        changed = True

    git_user = uc.get("git_user", "")
    if not git_user:
        rc, out = _run(["git", "config", "--global", "user.name"])
        git_user = out if rc == 0 and out else "unknown"
        uc["git_user"] = git_user
        changed = True

    gh_available = uc.get("gh_available")
    if gh_available is None:
        rc, _ = _run(["gh", "auth", "status"])
        gh_available = rc == 0
        uc["gh_available"] = gh_available
        changed = True

    if changed:
        _save_userconfig(uc)

    warnings = []
    if not python_bin:
        warnings.append("Python not found. Install Python 3.x.")

    return {
        "python_bin": python_bin,
        "git_user": git_user,
        "gh_available": gh_available,
        "persona_roster_xml": _read_roster(),
        "skill_root": str(SKILL_ROOT),
        "warnings": warnings,
    }


if __name__ == "__main__":
    print(json.dumps(snapshot(), indent=2))

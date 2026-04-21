#!/usr/bin/env python3
"""
One-time migration from ~/config/muthuishere-agent-skills/ to ~/.config/muthuishere-agent-skills/.

Triggered by meeting_state.py only on first-ever huddle run (when the new
config root doesn't exist yet), spawned as a detached background process.

Idempotent and safe to run concurrently with meeting_state writing new files:
walks the old tree and moves each file to the new location only if the target
doesn't already exist. Never overwrites. Removes now-empty old directories.
"""

import pathlib
import shutil
import sys


OLD_ROOT = pathlib.Path.home() / "config" / "muthuishere-agent-skills"
NEW_ROOT = pathlib.Path.home() / ".config" / "muthuishere-agent-skills"


def migrate() -> int:
    if not OLD_ROOT.is_dir():
        return 0

    NEW_ROOT.mkdir(parents=True, exist_ok=True)

    for src in OLD_ROOT.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(OLD_ROOT)
        dst = NEW_ROOT / rel
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dst))
        except Exception:
            pass

    for d in sorted(OLD_ROOT.rglob("*"), reverse=True):
        if d.is_dir():
            try:
                d.rmdir()
            except OSError:
                pass
    try:
        OLD_ROOT.rmdir()
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(migrate())

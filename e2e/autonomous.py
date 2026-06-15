#!/usr/bin/env python3
"""Deterministic tests for the Autonomous Decider substrate (autonomous_huddle.py)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "autonomous_huddle.py"


def run(args: list[str], expect_ok: bool = True) -> dict:
    r = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
    )
    out = (r.stdout or r.stderr).strip()
    try:
        data = json.loads(out) if out else {}
    except json.JSONDecodeError:
        data = {"_raw": out, "_stderr": r.stderr}
    if expect_ok:
        assert r.returncode == 0 and data.get("ok") is True, f"expected ok, got rc={r.returncode}: {out}"
    else:
        assert r.returncode != 0 or data.get("ok") is False, f"expected failure, got: {out}"
    return data


# ── S1: init + owner room ──────────────────────────────────────────────────
def test_init_happy(home: Path) -> str:
    hud = home / "hud"
    out = run([
        "init", str(hud),
        "--question", "Should the research line stand up a new OSS repo this cycle?",
        "--owner", "arasan",
        "--personas", "arasan,maya,nina,dileep",
        "--rounds", "3",
        "--session-id", "20260615T100000",
    ])
    assert out["owner"] == "arasan"
    assert out["rounds"] == 3
    # owner speaks LAST so it hears every voice before deciding
    assert out["speaking_order"][-1] == "arasan", f"owner must speak last: {out['speaking_order']}"
    assert out["speaking_order"][:-1] == ["maya", "nina", "dileep"]
    sdir = Path(out["session_dir"])
    assert (sdir / "session.json").exists(), "session.json not written"
    saved = json.loads((sdir / "session.json").read_text())
    assert saved["status"] == "open" and saved["turns"] == [] and saved["votes"] == []
    print("  [ok] init — creates session, owner speaks last, manifest persisted")
    return str(sdir)


def test_init_rejections(home: Path) -> None:
    hud = str(home / "hud2")
    base = ["init", hud, "--question", "Q", "--session-id", "sid"]
    # owner not in the room
    run([*base, "--owner", "ghost", "--personas", "maya,nina", "--rounds", "3"], expect_ok=False)
    # too few personas (just the owner, no second voice)
    run([*base, "--owner", "arasan", "--personas", "arasan", "--rounds", "3"], expect_ok=False)
    # rounds out of range (low and high)
    run([*base, "--owner", "arasan", "--personas", "arasan,maya", "--rounds", "2"], expect_ok=False)
    run([*base, "--owner", "arasan", "--personas", "arasan,maya", "--rounds", "6"], expect_ok=False)
    # duplicate persona ids
    run([*base, "--owner", "arasan", "--personas", "arasan,maya,maya", "--rounds", "3"], expect_ok=False)
    print("  [ok] init — rejects unknown owner, thin room, bad round count, dupes")


def test_owner_persona_assets() -> None:
    """The owner persona file + roster owner attribute must exist."""
    persona = ROOT / "references" / "personas" / "arasan-owner.md"
    assert persona.exists(), "arasan owner persona missing"
    body = persona.read_text()
    assert "displayName: Arasan" in body, "owner persona displayName wrong"
    roster = (ROOT / "references" / "persona-roster.xml").read_text()
    assert 'id="arasan"' in roster and 'owner="true"' in roster, "roster owner entry missing"
    print("  [ok] assets — arasan persona + roster owner=\"true\" present")


# ── S2: 5-whys rounds + rationale trail ────────────────────────────────────
def _init_room(home: Path, sid: str = "s2") -> str:
    out = run([
        "init", str(home / "hud-s2"),
        "--question", "Use a queue table or a broker for fan-out?",
        "--owner", "arasan", "--personas", "arasan,shaama,nina", "--rounds", "3",
        "--session-id", sid,
    ])
    return out["session_dir"]


def test_record_turn_depth(home: Path) -> None:
    sdir = _init_room(home, "depth")
    # shallow turn (< 3 whys) is rejected
    run(["record-turn", sdir, "--round", "1", "--persona", "shaama",
         "--why", "it's simpler", "--stance", "queue table"], expect_ok=False)
    # a proper 5-whys turn is accepted
    out = run(["record-turn", sdir, "--round", "1", "--persona", "shaama",
               "--why", "queue table is simpler;no broker to run;fewer failure modes",
               "--stance", "queue table"])
    assert out["recorded"]["depth"] == 3
    assert out["recorded"]["root"] == "fewer failure modes"
    # same persona/round twice is rejected
    run(["record-turn", sdir, "--round", "1", "--persona", "shaama",
         "--why", "a;b;c"], expect_ok=False)
    # unknown persona rejected
    run(["record-turn", sdir, "--round", "1", "--persona", "ghost",
         "--why", "a;b;c"], expect_ok=False)
    print("  [ok] record-turn — depth floor, no double-speak, room membership")


def test_round_monotonicity(home: Path) -> None:
    sdir = _init_room(home, "mono")
    run(["record-turn", sdir, "--round", "1", "--persona", "nina",
         "--why", "a;b;c;d", "--stance", "broker"])
    # round 2 shallower than round 1 (4 -> 3) is rejected: rounds must deepen
    run(["record-turn", sdir, "--round", "2", "--persona", "nina",
         "--why", "a;b;c", "--stance", "broker"], expect_ok=False)
    # round 2 at least as deep is fine
    out = run(["record-turn", sdir, "--round", "2", "--persona", "nina",
               "--why", "a;b;c;d;e", "--stance", "broker"])
    assert out["recorded"]["depth"] == 5
    print("  [ok] record-turn — each round must deepen, never go shallower")


def test_trail(home: Path) -> None:
    sdir = _init_room(home, "trail")
    personas = ["shaama", "nina", "arasan"]
    for rnd in (1, 2, 3):
        for pid in personas:
            run(["record-turn", sdir, "--round", str(rnd), "--persona", pid,
                 "--why", ";".join(["why"] * (2 + rnd)), "--stance", "x"])
    out = run(["trail", sdir])
    assert len(out["trail"]) == 3, "expected 3 rounds in trail"
    assert out["deliberation_complete"] is True, "all personas spoke every round"
    # speaking order within a round puts the owner last
    r1 = out["trail"][0]["turns"]
    assert r1[-1]["persona"] == "arasan", "owner should be last in the round trail"
    print("  [ok] trail — grouped by round, owner-last order, completeness flag")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="huddle-auton-"))
    try:
        print("Running autonomous-decider tests...")
        home = tmp / "h"
        home.mkdir(parents=True, exist_ok=True)
        test_init_happy(home)
        test_init_rejections(home)
        test_owner_persona_assets()
        test_record_turn_depth(home)
        test_round_monotonicity(home)
        test_trail(home)
        print("\nautonomous ok")
        return 0
    except AssertionError as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

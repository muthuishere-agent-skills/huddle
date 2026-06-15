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


# ── S3: owner-weighted vote + dissent + verdict + fork ─────────────────────
def _room(home: Path, sid: str, personas=("arasan", "shaama", "nina", "dileep")) -> str:
    out = run([
        "init", str(home / "hud-s3"),
        "--question", "Ship the queue on SQLite or Postgres?",
        "--owner", "arasan", "--personas", ",".join(personas), "--rounds", "3",
        "--session-id", sid,
    ])
    return out["session_dir"]


def _vote(sdir, persona, position, conf, reason="r"):
    run(["vote", sdir, "--persona", persona, "--position", position,
         "--confidence", str(conf), "--reason", reason])


def test_owner_tiebreak(home: Path) -> None:
    """Owner ties at the top -> owner's position wins, no override."""
    sdir = _room(home, "tie")
    _vote(sdir, "shaama", "sqlite", 0.9)
    _vote(sdir, "nina", "postgres", 0.9)
    _vote(sdir, "dileep", "postgres", 0.0)   # weak
    _vote(sdir, "arasan", "sqlite", 0.9)     # owner -> sqlite ties postgres at 0.9
    out = run(["tally", sdir])
    assert out["resolved"] == "sqlite", f"owner should win the tie: {out}"
    assert out["owner_overridden"] is False
    print("  [ok] tally — owner breaks a top tie toward its own position")


def test_room_override(home: Path) -> None:
    """A single non-owner option strictly dominates -> room overrides the owner."""
    sdir = _room(home, "override")
    _vote(sdir, "shaama", "postgres", 0.9)
    _vote(sdir, "nina", "postgres", 0.9)
    _vote(sdir, "dileep", "postgres", 0.8)   # postgres = 2.6
    _vote(sdir, "arasan", "sqlite", 0.7)     # owner alone, 0.7
    out = run(["tally", sdir])
    assert out["resolved"] == "postgres", f"room should override: {out}"
    assert out["owner_overridden"] is True
    owner_dissent = [d for d in out["dissents"] if d["persona"] == "arasan"]
    assert owner_dissent and owner_dissent[0]["position"] == "sqlite", \
        "overridden owner must be recorded as a dissent"
    print("  [ok] tally — decisive room overrides owner, owner's dissent recorded")


def test_owner_not_top_but_tie(home: Path) -> None:
    """Owner below a TIE of non-owner options -> owner still wins (breaks tie)."""
    sdir = _room(home, "notoptie")
    _vote(sdir, "shaama", "postgres", 0.6)
    _vote(sdir, "nina", "mysql", 0.6)        # postgres & mysql tie at top (0.6)
    _vote(sdir, "dileep", "sqlite", 0.0)
    _vote(sdir, "arasan", "sqlite", 0.5)     # owner below top, but top is a tie
    out = run(["tally", sdir])
    assert out["resolved"] == "sqlite", f"owner breaks non-owner tie: {out}"
    assert out["owner_overridden"] is False
    print("  [ok] tally — non-owner tie at top still resolves to the owner")


def test_tally_guards(home: Path) -> None:
    sdir = _room(home, "guards")
    run(["tally", sdir], expect_ok=False)            # no votes yet
    _vote(sdir, "shaama", "sqlite", 0.5)
    run(["tally", sdir], expect_ok=False)            # owner hasn't voted
    run(["vote", sdir, "--persona", "shaama", "--position", "x",
         "--confidence", "0.5"], expect_ok=False)     # double vote
    run(["vote", sdir, "--persona", "shaama", "--position", "x",
         "--confidence", "2"], expect_ok=False)        # confidence out of range
    print("  [ok] vote/tally — guards: owner-must-vote, no double-vote, conf range")


def test_fork_check(home: Path) -> None:
    sdir = _room(home, "fork")
    clean = run(["fork-check", sdir, "--decision", "use sqlite", "--flags", ""])
    assert clean["escalate"] is False
    for flag in ("launch", "spend", "irreversible", "legal", "security", "scope"):
        out = run(["fork-check", sdir, "--decision", "d", "--flags", flag])
        assert out["escalate"] is True, f"{flag} must escalate"
    mixed = run(["fork-check", sdir, "--decision", "d", "--flags", "spend,banana"])
    assert mixed["escalate"] is True and "banana" in mixed["unknown_flags"]
    print("  [ok] fork-check — each owner-fork flag escalates, clean case doesn't")


def test_verdict_decided_and_escalated(home: Path) -> None:
    # decided path
    sdir = _room(home, "decided")
    for r in (1, 2, 3):
        for pid in ("shaama", "nina", "dileep", "arasan"):
            run(["record-turn", sdir, "--round", str(r), "--persona", pid,
                 "--why", ";".join(["w"] * (2 + r)), "--stance", "sqlite"])
    _vote(sdir, "shaama", "sqlite", 0.8)
    _vote(sdir, "nina", "sqlite", 0.6)
    _vote(sdir, "dileep", "postgres", 0.5, "scale later")
    _vote(sdir, "arasan", "sqlite", 0.9)
    out = run(["verdict", sdir, "--decision", "Ship on SQLite (WAL) now",
               "--summary", "reversible, fastest to value"])
    assert out["status"] == "decided" and out["actionable"] is True
    vj = json.loads((Path(sdir) / "verdict.json").read_text())
    assert vj["tally"]["resolved"] == "sqlite"
    assert any(d["persona"] == "dileep" for d in vj["tally"]["dissents"]), "dissent missing"
    assert len(vj["rationale_trail"]) == 3, "trail rounds missing from verdict"
    assert (Path(sdir) / "verdict.md").exists()

    # escalated path (owner-level fork)
    sdir2 = _room(home, "escalated")
    _vote(sdir2, "shaama", "launch", 0.8)
    _vote(sdir2, "nina", "launch", 0.7)
    _vote(sdir2, "dileep", "launch", 0.6)
    _vote(sdir2, "arasan", "launch", 0.9)
    out2 = run(["verdict", sdir2, "--decision", "Publish the OSS repo publicly",
                "--flags", "launch,irreversible"])
    assert out2["status"] == "escalated" and out2["actionable"] is False, \
        "owner-level fork must not be actionable headlessly"
    assert out2["escalation"]["required"] is True
    md = (Path(sdir2) / "verdict.md").read_text()
    assert "OWNER-LEVEL FORK" in md, "escalation warning missing from verdict.md"
    print("  [ok] verdict — decided=actionable w/ trail+dissents; escalated=staged, not actionable")


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
        test_owner_tiebreak(home)
        test_room_override(home)
        test_owner_not_top_but_tie(home)
        test_tally_guards(home)
        test_fork_check(home)
        test_verdict_decided_and_escalated(home)
        print("\nautonomous ok")
        return 0
    except AssertionError as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Autonomous Decider Mode — deterministic session + decision substrate.

The huddle skill (Claude / any fleet agent) performs the persona reasoning and
the 5-whys in its own context. THIS script owns the structure and the decision
math: it manages the session manifest, enforces 5-whys depth/monotonicity,
resolves the owner-weighted vote, applies the owner-level-fork policy, and writes
the final verdict. No LLM calls, stdlib only, JSON to stdout.

Subcommands:
    init <dir> --question Q --owner ID --personas a,b,c --rounds N --session-id SID
    record-turn <session_dir> --round R --persona ID --why "a;b;c" --stance TEXT
    trail <session_dir>
    vote <session_dir> --persona ID --position OPT --confidence F --reason TEXT
    tally <session_dir>
    fork-check <session_dir> --decision TEXT [--flags a,b]
    verdict <session_dir> --decision TEXT [--flags a,b] [--summary TEXT]

A <session_dir> is {huddle_dir}/autonomous/{session-id}. `init` takes the parent
{huddle_dir} and the explicit {session-id}; the rest take the session_dir.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ── owner-level fork policy ────────────────────────────────────────────────
# A decision carrying any of these is the real owner's to make — escalate.
OWNER_FORK_FLAGS = {
    "launch": "customer- or public-facing go-live",
    "spend": "money is committed",
    "irreversible": "hard or impossible to undo",
    "legal": "legal / compliance exposure",
    "security": "trust-boundary / security exposure",
    "scope": "materially changes company direction or a product's identity",
}

MIN_ROUNDS, MAX_ROUNDS = 3, 5
MIN_WHYS = 3            # a 5-whys turn must reach a root (>= 3 deepening steps)
MIN_PERSONAS = 2       # an owner + at least one other voice
TIE_EPSILON = 1e-9


def die(msg: str) -> "None":
    print(json.dumps({"ok": False, "error": msg}))
    raise SystemExit(1)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:48] or "decision")


def parse_list(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def session_path(session_dir: str) -> Path:
    return Path(session_dir) / "session.json"


def load_session(session_dir: str) -> dict:
    p = session_path(session_dir)
    if not p.exists():
        die(f"no session at {session_dir}")
    return json.loads(p.read_text())


def save_session(session_dir: str, session: dict) -> None:
    session_path(session_dir).write_text(json.dumps(session, indent=2))


def speaking_order(personas: list[str], owner: str) -> list[str]:
    """Owner speaks LAST each round — it hears every voice before deciding."""
    return [p for p in personas if p != owner] + [owner]


# ── init ───────────────────────────────────────────────────────────────────
def cmd_init(a: argparse.Namespace) -> dict:
    personas = parse_list(a.personas)
    if len(personas) != len(set(personas)):
        die("persona ids must be distinct")
    if len(personas) < MIN_PERSONAS:
        die(f"need >= {MIN_PERSONAS} personas (an owner + at least one other voice)")
    if not a.owner:
        die("an owner persona is required (the deciding vote)")
    if a.owner not in personas:
        die(f"owner '{a.owner}' must be one of the personas: {personas}")
    if not (MIN_ROUNDS <= a.rounds <= MAX_ROUNDS):
        die(f"rounds must be {MIN_ROUNDS}..{MAX_ROUNDS}, got {a.rounds}")
    if not a.question.strip():
        die("a question is required")

    sid = a.session_id or slugify(a.question)
    session_dir = Path(a.huddle_dir) / "autonomous" / sid
    session_dir.mkdir(parents=True, exist_ok=True)

    order = speaking_order(personas, a.owner)
    session = {
        "session_id": sid,
        "question": a.question,
        "owner": a.owner,
        "personas": personas,
        "speaking_order": order,
        "rounds": a.rounds,
        "status": "open",
        "created": a.session_id or "",
        "turns": [],
        "votes": [],
    }
    save_session(str(session_dir), session)
    return {
        "ok": True,
        "session_id": sid,
        "session_dir": str(session_dir),
        "owner": a.owner,
        "rounds": a.rounds,
        "personas": personas,
        "speaking_order": order,
        "plan": (
            f"Autonomous huddle on \"{a.question}\": {len(personas)} personas, "
            f"{a.rounds} rounds of 5-whys, owner '{a.owner}' speaks last and decides."
        ),
    }


# ── record-turn (5-whys) ───────────────────────────────────────────────────
def cmd_record_turn(a: argparse.Namespace) -> dict:
    session = load_session(a.session_dir)
    if a.persona not in session["personas"]:
        die(f"persona '{a.persona}' is not in this room: {session['personas']}")
    if not (1 <= a.round <= session["rounds"]):
        die(f"round must be 1..{session['rounds']}, got {a.round}")

    whys = [w.strip() for w in a.why.split(";") if w.strip()]
    if len(whys) < MIN_WHYS:
        die(f"5-whys turn needs >= {MIN_WHYS} deepening steps (why -> why -> root), got {len(whys)}")

    # round monotonicity: a persona's depth must not go shallower than its own
    # previous round — each round digs deeper, never a shallower re-take.
    prev = [t for t in session["turns"] if t["persona"] == a.persona and t["round"] < a.round]
    if prev:
        deepest = max(t["depth"] for t in prev)
        if len(whys) < deepest:
            die(
                f"round {a.round} for '{a.persona}' is shallower "
                f"({len(whys)}) than an earlier round ({deepest}); each round must deepen"
            )
    # one turn per persona per round
    if any(t["persona"] == a.persona and t["round"] == a.round for t in session["turns"]):
        die(f"'{a.persona}' already spoke in round {a.round}")

    turn = {
        "round": a.round,
        "persona": a.persona,
        "stance": a.stance,
        "why": whys,
        "depth": len(whys),
        "root": whys[-1],
    }
    session["turns"].append(turn)
    session["status"] = "deliberating"
    save_session(a.session_dir, session)
    return {"ok": True, "recorded": turn, "turns_total": len(session["turns"])}


def cmd_trail(a: argparse.Namespace) -> dict:
    session = load_session(a.session_dir)
    by_round: dict[int, list[dict]] = {}
    for t in session["turns"]:
        by_round.setdefault(t["round"], []).append(t)
    trail = []
    for r in sorted(by_round):
        # preserve speaking order within the round
        order = {p: i for i, p in enumerate(session["speaking_order"])}
        turns = sorted(by_round[r], key=lambda t: order.get(t["persona"], 99))
        trail.append({"round": r, "turns": turns})
    complete = all(
        len([t for t in session["turns"] if t["round"] == r]) == len(session["personas"])
        for r in range(1, session["rounds"] + 1)
    )
    return {
        "ok": True,
        "question": session["question"],
        "rounds": session["rounds"],
        "owner": session["owner"],
        "trail": trail,
        "deliberation_complete": complete,
    }


# ── vote ───────────────────────────────────────────────────────────────────
def cmd_vote(a: argparse.Namespace) -> dict:
    session = load_session(a.session_dir)
    if a.persona not in session["personas"]:
        die(f"persona '{a.persona}' is not in this room: {session['personas']}")
    if not (0.0 <= a.confidence <= 1.0):
        die(f"confidence must be 0..1, got {a.confidence}")
    if not a.position.strip():
        die("a vote needs a position (the option being voted for)")
    if any(v["persona"] == a.persona for v in session["votes"]):
        die(f"'{a.persona}' already voted")
    vote = {
        "persona": a.persona,
        "position": a.position.strip(),
        "confidence": a.confidence,
        "reason": a.reason,
    }
    session["votes"].append(vote)
    session["status"] = "voting"
    save_session(a.session_dir, session)
    return {"ok": True, "recorded": vote, "votes_total": len(session["votes"])}


# ── tally: owner-weighted resolution (the decision math) ────────────────────
def resolve(votes: list[dict], owner: str) -> dict:
    """Resolve the vote through the owner's lens. Pure, deterministic.

    weight(option) = sum of voter confidences for it. The owner is the deciding
    vote / tie-breaker: the resolved option is the OWNER's position unless a
    *single* non-owner option strictly dominates it (unique top, strictly
    greater by > epsilon) — only then does the room override, and that override
    is recorded. Otherwise (owner at/near the top, or a tie at the top) the
    owner's position wins.
    """
    owner_votes = [v for v in votes if v["persona"] == owner]
    if not owner_votes:
        die("owner has not voted — cannot resolve")
    owner_pos = owner_votes[0]["position"]

    weights: dict[str, float] = {}
    for v in votes:
        weights[v["position"]] = round(weights.get(v["position"], 0.0) + v["confidence"], 6)

    top_weight = max(weights.values())
    at_top = [opt for opt, w in weights.items() if abs(w - top_weight) <= TIE_EPSILON]

    owner_overridden = False
    if owner_pos in at_top:
        resolved = owner_pos
    elif len(at_top) == 1 and (top_weight - weights[owner_pos]) > TIE_EPSILON:
        resolved = at_top[0]            # room decisively overrides the owner
        owner_overridden = True
    else:
        resolved = owner_pos            # owner breaks the tie toward its own call

    dissents = [
        {"persona": v["persona"], "position": v["position"], "reason": v["reason"]}
        for v in votes if v["position"] != resolved
    ]
    return {
        "resolved": resolved,
        "owner_position": owner_pos,
        "owner_overridden": owner_overridden,
        "weights": weights,
        "top_weight": top_weight,
        "dissents": dissents,
    }


def cmd_tally(a: argparse.Namespace) -> dict:
    session = load_session(a.session_dir)
    if not session["votes"]:
        die("no votes recorded yet")
    res = resolve(session["votes"], session["owner"])
    missing = [p for p in session["personas"]
               if p not in {v["persona"] for v in session["votes"]}]
    return {"ok": True, "owner": session["owner"], "did_not_vote": missing, **res}


# ── fork-check: owner-level escalation policy ──────────────────────────────
def fork_check(flags: list[str]) -> dict:
    recognized = [f for f in flags if f in OWNER_FORK_FLAGS]
    unknown = [f for f in flags if f not in OWNER_FORK_FLAGS]
    return {
        "escalate": bool(recognized),
        "reasons": [f"{f}: {OWNER_FORK_FLAGS[f]}" for f in recognized],
        "flags": recognized,
        "unknown_flags": unknown,
    }


def cmd_fork_check(a: argparse.Namespace) -> dict:
    fc = fork_check(parse_list(a.flags) if a.flags else [])
    return {"ok": True, "decision": a.decision, **fc}


# ── verdict: assemble + write ───────────────────────────────────────────────
def _condensed_trail(session: dict) -> list[dict]:
    out = []
    order = {p: i for i, p in enumerate(session["speaking_order"])}
    by_round: dict[int, list[dict]] = {}
    for t in session["turns"]:
        by_round.setdefault(t["round"], []).append(t)
    for r in sorted(by_round):
        turns = sorted(by_round[r], key=lambda t: order.get(t["persona"], 99))
        out.append({
            "round": r,
            "turns": [{"persona": t["persona"], "stance": t["stance"],
                       "why": t["why"], "root": t["root"]} for t in turns],
        })
    return out


def _verdict_md(v: dict) -> str:
    lines = [
        f"# Verdict — {v['question']}",
        "",
        f"**Decision:** {v['decision']}",
        f"**Resolved option:** {v['tally']['resolved']}  ",
        f"**Owner (decider):** {v['owner']}"
        + ("  · _room overrode the owner_" if v["tally"]["owner_overridden"] else ""),
        f"**Status:** {v['status']}",
        "",
    ]
    if v["escalation"]["required"]:
        lines += ["> ⚠️ **OWNER-LEVEL FORK — escalate to the real owner. Do not act.**"]
        lines += [f"> - {r}" for r in v["escalation"]["reasons"]] + [""]
    lines += ["## Vote tally", ""]
    for opt, w in sorted(v["tally"]["weights"].items(), key=lambda kv: -kv[1]):
        mark = " ← resolved" if opt == v["tally"]["resolved"] else ""
        lines.append(f"- **{opt}** — weight {w}{mark}")
    lines += ["", "## Dissents", ""]
    if v["tally"]["dissents"]:
        for d in v["tally"]["dissents"]:
            lines.append(f"- **{d['persona']}** ({d['position']}): {d['reason']}")
    else:
        lines.append("- none — the room aligned")
    lines += ["", "## 5-whys rationale trail", ""]
    for rnd in v["rationale_trail"]:
        lines.append(f"### Round {rnd['round']}")
        for t in rnd["turns"]:
            lines.append(f"- **{t['persona']}** [{t['stance']}]: "
                         + " → ".join(t["why"]) + f"  _(root: {t['root']})_")
        lines.append("")
    return "\n".join(lines)


def cmd_verdict(a: argparse.Namespace) -> dict:
    session = load_session(a.session_dir)
    if not session["votes"]:
        die("no votes recorded — run vote before verdict")
    tally = resolve(session["votes"], session["owner"])
    fc = fork_check(parse_list(a.flags) if a.flags else [])

    verdict = {
        "session_id": session["session_id"],
        "question": session["question"],
        "owner": session["owner"],
        "personas": session["personas"],
        "rounds": session["rounds"],
        "decision": a.decision.strip() or tally["resolved"],
        "summary": a.summary,
        "tally": tally,
        "votes": session["votes"],
        "rationale_trail": _condensed_trail(session),
        "escalation": {
            "required": fc["escalate"],
            "reasons": fc["reasons"],
            "flags": fc["flags"],
        },
        "status": "escalated" if fc["escalate"] else "decided",
    }
    sdir = Path(a.session_dir)
    (sdir / "verdict.json").write_text(json.dumps(verdict, indent=2))
    (sdir / "verdict.md").write_text(_verdict_md(verdict))

    session["status"] = verdict["status"]
    save_session(a.session_dir, session)
    return {
        "ok": True,
        "status": verdict["status"],
        "resolved": tally["resolved"],
        "owner_overridden": tally["owner_overridden"],
        "escalation": verdict["escalation"],
        "verdict_json": str(sdir / "verdict.json"),
        "verdict_md": str(sdir / "verdict.md"),
        "actionable": verdict["status"] == "decided",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="autonomous_huddle")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init")
    pi.add_argument("huddle_dir")
    pi.add_argument("--question", required=True)
    pi.add_argument("--owner", required=True)
    pi.add_argument("--personas", required=True)
    pi.add_argument("--rounds", type=int, default=MIN_ROUNDS)
    pi.add_argument("--session-id", dest="session_id", default="")

    pr = sub.add_parser("record-turn")
    pr.add_argument("session_dir")
    pr.add_argument("--round", type=int, required=True)
    pr.add_argument("--persona", required=True)
    pr.add_argument("--why", required=True, help="semicolon-separated deepening steps")
    pr.add_argument("--stance", default="")

    pt = sub.add_parser("trail")
    pt.add_argument("session_dir")

    pv = sub.add_parser("vote")
    pv.add_argument("session_dir")
    pv.add_argument("--persona", required=True)
    pv.add_argument("--position", required=True)
    pv.add_argument("--confidence", type=float, required=True)
    pv.add_argument("--reason", default="")

    pta = sub.add_parser("tally")
    pta.add_argument("session_dir")

    pf = sub.add_parser("fork-check")
    pf.add_argument("session_dir")
    pf.add_argument("--decision", default="")
    pf.add_argument("--flags", default="")

    pvd = sub.add_parser("verdict")
    pvd.add_argument("session_dir")
    pvd.add_argument("--decision", default="")
    pvd.add_argument("--flags", default="")
    pvd.add_argument("--summary", default="")

    args = p.parse_args(argv)
    handlers = {
        "init": cmd_init, "record-turn": cmd_record_turn, "trail": cmd_trail,
        "vote": cmd_vote, "tally": cmd_tally, "fork-check": cmd_fork_check,
        "verdict": cmd_verdict,
    }
    out = handlers[args.cmd](args)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

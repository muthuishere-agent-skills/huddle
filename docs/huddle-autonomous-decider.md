# Huddle — Autonomous Decider Mode

Status: **spec** · Owner of design: Muthu · Implements: `feat/autonomous-decider`

## 1. Why

The huddle today is **human-decides**: personas surface perspectives, then the
skill *stops and waits* for the user to make every call. That is correct for a
person at the keyboard. It is a dead end for the **company OS**, where the fleet
must convene a real multi-persona huddle inside the spec-first loop and come out
the other side with an **actionable verdict — no human stop**.

Autonomous Decider Mode adds a second, headless way to run a huddle. The
interactive (human-decides) mode is **unchanged and remains the default**. The
new mode is entered explicitly and is the only mode that is allowed to reach a
decision without a human in the loop.

Non-negotiable boundary: **owner-level forks** — anything launch / spend /
irreversible / customer-facing — still escalate to the real owner (Muthu). The
autonomous huddle decides everything *below* that line on its own.

## 2. The mechanism (Muthu's design)

1. **Unlimited custom personas.** A session can convene as many personas as
   wanted. Built-in roster personas, externally-synced personas
   (`~/.config/muthuishere-agent-skills/personas/…`), and one-off session
   personas (a `.md` in the standard persona format dropped into the session)
   all compose into the room.
2. **One persona is the OWNER (the decider).** Exactly one persona in the room
   is designated owner. The owner is an *owner-aligned decider* — for the OS this
   is a CEO/owner persona (`arasan`) that judges from the owner's perspective.
   The owner must be a member of the room.
3. **Deliberation — R rounds (default 3, range 3–5).** In each round **every**
   persona speaks, applying the **5-WHYS** method: a turn is not a one-shot take.
   Each turn deepens — *why? → why? → why? → root rationale / root risk* — and
   each later round goes deeper than the one before it. The trail of these
   why-chains is recorded.
4. **Decision — a vote resolved through the owner's lens.** After the rounds,
   every persona casts a vote (a position + confidence + one-line reason). The
   outcome is **resolved through the owner persona**: the owner casts the
   deciding vote, breaks ties, and the winning option is the one the owner judges
   best from the owner's perspective. Personas who land against the resolved
   outcome are recorded as **dissents** (not erased).
5. **Output — an actionable verdict, headless.** The session emits a
   `verdict.json` (+ a human `verdict.md`): the decision, the **5-whys rationale
   trail**, the recorded **dissents**, the vote tally, the owner, and an
   **escalation flag**. This is a spec/verdict an agent can act on with no human
   stop — unless the escalation flag is set, in which case it is staged for the
   real owner.

## 3. Architecture

The huddle skill is declarative: Claude (or any fleet agent) reads the routing
XML + step file and *performs* the deliberation in its own context — that is
where the persona reasoning and the 5-whys actually happen. The **deterministic,
testable substrate** is a single stdlib-only Python helper that manages the
session, enforces structure, resolves the owner-weighted vote, and writes the
verdict. Nothing in the substrate calls an LLM; the agent supplies the content,
the script enforces the shape and the decision math.

```
references/
  activation-routing.xml          + route id="autonomous-decide" (headless mode)
  persona-roster.xml              + arasan (owner-aligned CEO decider)
  personas/arasan-owner.md        the owner/decider persona
  steps/
    step-autonomous-decider.md    the headless execution recipe (the loop)
scripts/
  autonomous_huddle.py            the deterministic session + decision substrate
docs/
  huddle-autonomous-decider.md    (this file)
e2e/
  autonomous.py                   deterministic tests for autonomous_huddle.py
```

### 3.1 Session storage

A session lives under the huddle dir, isolated from interactive notes:

```
{config-dir}/{branch}/huddle/autonomous/{session-id}/
  session.json     manifest: question, owner, personas, rounds, status, turns[], votes[]
  verdict.json     final verdict (decision + trail + dissents + tally + escalation)
  verdict.md       human-readable verdict
```

`{session-id}` = `{YYYYMMDDThhmmss}-{slug-of-question}` (timestamp passed in by the
caller — the script never reads the clock so runs are reproducible/testable).

### 3.2 `autonomous_huddle.py` — subcommands

All subcommands read/write `session.json` and print JSON to stdout. stdlib only.

| cmd | purpose |
|---|---|
| `init <dir> --question Q --owner ID --personas a,b,c --rounds N --session-id SID` | Validate (owner ∈ personas, 3 ≤ N ≤ 5, ≥2 personas), create the session manifest, print the deliberation plan (round count, speaking order, owner). |
| `record-turn <dir/SID> --round R --persona ID --why "a;b;c" --stance TEXT` | Append one persona's 5-whys turn for round R. Enforces depth (≥3 whys, last = root). Enforces round monotonicity (a round must not go shallower than the previous). |
| `trail <dir/SID>` | Print the accumulated rationale trail grouped by round → persona. |
| `vote <dir/SID> --persona ID --position OPT --confidence 0..1 --reason TEXT` | Record one persona's final vote. |
| `tally <dir/SID>` | Resolve the vote **through the owner's lens** (owner is the deciding vote / tie-breaker) and print the resolved option + per-option weight + dissent list. Pure function of recorded votes; no side effects. |
| `fork-check <dir/SID> --decision TEXT --flags launch,spend,...` | Apply the owner-level-fork policy; print `{escalate, reasons[]}`. |
| `verdict <dir/SID> --decision TEXT [--flags …]` | Assemble verdict from turns + votes + tally + fork-check; write `verdict.json` + `verdict.md`; print the verdict. Marks session `decided` (or `escalated`). |

### 3.3 Owner-weighted resolution (the decision math)

`tally` is deterministic and is the heart of the mode:

1. Group votes by `position`. Each option's **weight** = sum of voter
   confidences.
2. The **owner's vote always counts**, and the owner is the **tie-breaker**: if
   two or more options are within an epsilon of the top weight, the option the
   **owner** voted for wins. If the owner's option is not among the top group,
   the owner still breaks the tie *toward the owner's own position* — the design
   intent is "the outcome is judged from the owner's perspective", so the owner's
   choice is decisive whenever the room is not clearly aligned.
3. Concretely: **resolved = owner's position** unless a *single* non-owner option
   strictly dominates (weight strictly greater than the owner's option by more
   than epsilon AND no tie) — i.e. the room is decisively against the owner, in
   which case the dominant option wins but the owner's dissent is recorded
   loudly. This keeps the owner the decider while still letting an overwhelming
   room override on low-stakes calls, and the override itself is auditable.
4. **Dissents** = every persona whose `position` ≠ resolved, with their reason.

This is intentionally simple, fully deterministic, and unit-tested. The nuance
(how persuasive each persona was) lives in the *content* the agent writes into
the trail, not in the math.

### 3.4 Owner-level fork escalation

`fork-check` encodes the boundary. A decision **escalates to the real owner**
when any of these flags is present (or detected by the agent and passed in):

- `launch` — anything customer/public-facing going live
- `spend` — money committed
- `irreversible` — hard or impossible to undo
- `legal` / `security` — trust-boundary or compliance exposure
- `scope` — materially changes company direction / a product's identity

If `escalate` is true, `verdict` writes the verdict with
`status: "escalated"` and `escalation: {required: true, reasons: […]}`, and the
fleet agent must NOT act — it stages the verdict for Muthu (the `CYCLE-HUDDLE` /
owner-escalation path in the OS). Everything else: `status: "decided"`, the agent
acts headlessly.

## 4. Routing & modes

- New route `autonomous-decide` in `activation-routing.xml`, `mode="autonomous"`.
- This mode **explicitly overrides** the global "user drives / stop after every
  round / never decide unilaterally" rules — but *only within this route*. The
  interactive routes are untouched; their rules still forbid auto-deciding.
- Entry triggers (skill + route): "autonomous huddle", "decide this headless",
  "convene the deciders", "run the autonomous decider", "fleet huddle", and the
  programmatic fleet entry (a spec-first loop step).
- The owner persona is required: if a caller enters autonomous mode without
  naming an owner, default the owner to `arasan` (the CEO/owner-aligned decider).

## 5. The owner persona — `arasan`

A new persona `references/personas/arasan-owner.md`, roster id `arasan`, marked
`owner="true"` in the roster. It is the CEO/owner-aligned decider: it judges
every call the way the owner would — protect focus, move fast, reversible by
default, escalate only true owner-level forks. It is the only persona allowed to
be the deciding vote. It is selectable as owner in any autonomous session, and is
the default owner for fleet-convened huddles.

## 6. What stays the same

- Interactive mode is the default and is behaviorally unchanged.
- Persona format, roster mechanics, synced-persona loading, preflight, and the
  `huddle-state.json` interactive memory are all reused, not replaced.
- No network, no new dependencies — `autonomous_huddle.py` is stdlib-only like
  every other script.

## 7. Stories (build order)

1. **S1 — Owner room + CEO decider + session init.** `arasan` persona, roster
   entry, `init` with owner validation. Demo: convene an autonomous room, owner
   flagged.
2. **S2 — 5-whys rounds + rationale trail.** `record-turn` depth/monotonicity
   enforcement, `trail`. Demo: R deepening rounds.
3. **S3 — Owner-weighted vote + dissent + verdict + fork.** `vote`, `tally`,
   `fork-check`, `verdict`. Demo: votes → owner resolves → verdict + dissents +
   escalation flag.
4. **S4 — Headless skill wiring.** route + `step-autonomous-decider.md` + SKILL
   triggers, interactive mode preserved. Demo: end-to-end headless run to an
   actionable verdict, with an owner-level fork staging instead of acting.

## 8. Test strategy

`e2e/autonomous.py` (run alongside `e2e/run.py`) covers the substrate with a temp
`$HOME`: init validation (good + rejected owner/rounds/size), turn depth +
monotonicity enforcement, owner-weighted tally (owner tie-break, room-override,
dissent capture), fork-check policy (each flag + clean case), and full
`verdict` assembly for both `decided` and `escalated` outcomes. Structural lint
asserts the route, step file, SKILL triggers, and roster owner attribute exist
and that interactive "user drives" rules are preserved.

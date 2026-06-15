---
name: huddle-autonomous-decider
mode: autonomous
---

# Step — Autonomous Decider (headless, no human stop)

This is the ONLY huddle mode that reaches a decision without a human in the loop.
It is entered explicitly (route `autonomous-decide`). Every other route keeps the
"user drives — stop and wait" rules. Inside this step those rules are
**suspended**: you run all the rounds, resolve the vote, and write the verdict in
one go. You do not stop to ask the user between rounds.

Use the deterministic substrate `scripts/autonomous_huddle.py` for structure and
the decision math. YOU (the agent) supply the persona reasoning; the script
enforces the shape, resolves the owner-weighted vote, and writes the verdict.
Use `{PYTHON_BIN}` (from preflight) for every call.

## Inputs

- `QUESTION` — the decision to be made (a real, answerable question).
- `OWNER` — the deciding persona. Default `arasan` (the CEO/owner-aligned
  decider) when none is named. The owner MUST be in the room.
- `PERSONAS` — the room (>= 2, including the owner). Built-in roster ids,
  synced personas, and one-off session personas all compose.
- `ROUNDS` — 3..5 (default 3).
- `HUDDLE_DIR` — `{config-dir}/{branch}/huddle` (from preflight).
- `SESSION_ID` — a timestamp `{YYYYMMDDThhmmss}` you generate once at the start.

## Procedure

1. **Convene.** Pick the room and the owner for `QUESTION`. If no owner is
   named, use `arasan`. Ensure the owner is in `PERSONAS`.
   ```
   {PYTHON_BIN} scripts/autonomous_huddle.py init "{HUDDLE_DIR}" \
     --question "{QUESTION}" --owner {OWNER} \
     --personas {comma,sep,ids} --rounds {N} --session-id {SESSION_ID}
   ```
   Keep the returned `session_dir` and `speaking_order` (the owner speaks last).

2. **Deliberate — R rounds of 5-whys.** For each round 1..N, in `speaking_order`,
   have **every** persona speak in character (re-read its `communicationStyle`
   and `principles` first). Each turn applies the 5-WHYS method: a chain that
   *deepens* — why → why → root rationale/risk — and each round must go at least
   as deep as that persona's previous round (the script enforces this). Record
   each turn:
   ```
   {PYTHON_BIN} scripts/autonomous_huddle.py record-turn "{session_dir}" \
     --round {r} --persona {id} --stance "{one-line position}" \
     --why "first why; deeper why; root rationale or risk"
   ```
   The owner (`arasan`) speaks last each round — it hears every voice before it
   weighs in. Use `trail` any time to review the accumulated reasoning.

3. **Vote.** After the rounds, every persona casts a final vote — a `position`
   (the option it backs, use consistent option labels), a `confidence` 0..1, and
   a one-line `reason`. The owner votes too.
   ```
   {PYTHON_BIN} scripts/autonomous_huddle.py vote "{session_dir}" \
     --persona {id} --position "{option}" --confidence {0..1} --reason "{why}"
   ```

4. **Resolve through the owner's lens.** `tally` resolves the vote: the owner is
   the deciding vote / tie-breaker; a single decisively-dominant non-owner option
   can override the owner (and that override is recorded). Dissents are captured.
   ```
   {PYTHON_BIN} scripts/autonomous_huddle.py tally "{session_dir}"
   ```

5. **Owner-fork check + verdict.** Decide which option won, phrase the decision,
   and detect any owner-level fork flags it carries
   (`launch`, `spend`, `irreversible`, `legal`, `security`, `scope`). Write the
   verdict:
   ```
   {PYTHON_BIN} scripts/autonomous_huddle.py verdict "{session_dir}" \
     --decision "{the actionable decision}" \
     --flags "{comma-sep owner-fork flags, or empty}" \
     --summary "{one-line rationale}"
   ```
   This writes `verdict.json` + `verdict.md` (decision + 5-whys trail + dissents
   + tally + escalation) and sets the session status.

## Outcome — what the fleet does next

- `status: "decided"` (`actionable: true`) → the verdict is an actionable spec.
  The fleet acts on it headlessly. No human stop.
- `status: "escalated"` (`actionable: false`) → an **owner-level fork**. Do NOT
  act. Stage the verdict for the real owner (Muthu) via the OS escalation path
  (`CYCLE-HUDDLE` / owner notification). The room did its work; only the owner
  closes a one-way door.

## Rules specific to this mode

- No "stop and wait" between rounds — this mode runs to a verdict.
- Stay in character per persona; the 5-whys must actually deepen, not restate.
- The owner is the decider, but it is not a domain expert — it decides *between*
  the perspectives, it does not generate them.
- Every decision below the owner-fork line is yours to close. Every decision on
  or above it escalates. When unsure whether something is a fork, treat it as a
  fork and escalate — false-escalate is cheap, a wrong headless launch is not.
- This is the only place the interactive "user drives / never decide
  unilaterally" rules are suspended. They remain in force everywhere else.

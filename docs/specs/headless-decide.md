# Spec: Headless Decision Mode ("anonymous decide")

Status: **Proposed**
Date: 2026-06-15
Repo: `huddle`
Validated by: simulation run `wf_db23dc55-eac` (6-juror Condorcet panel · 5-Whys · 3 Delphi
rounds · devil's advocate · owner-persona judge). The protocol flipped a round-1 5–1 false
consensus into a different, defended answer — evidence the ceremony earns its cost.

---

## 1. Summary

A **headless, self-deciding** mode for huddle. Convene a panel, run an anonymized multi-round
deliberation **protocol**, and have a designated **CHIEF** persona render the decision — with
**no human in the loop except for owner-level forks**, which escalate over a human pipe.
Optionally the chief then **dispatches** the chosen option to worker agents (**spawn**),
**receives** results, validates them against the chief's persona, and accepts / escalates /
re-decides.

Three things are **pluggable and producer-agnostic**:
- **chief** — a persona (default: the owner persona, supplied as a *synced* persona),
- **protocol** — the deliberation method,
- **flavor** — the task type (brainstorm, product-design, code-change, strategy, …).

This turns huddle from "advisor that waits" into an autonomous decision core, **without
touching the interactive huddle** — it is a second door, selected by trigger.

---

## 2. Trigger grammar (SKILL.md)

Primary:

> **"start an anonymous decision for `<task>` with `<chief>` as chief using `<protocol>`"**

Aliases already in SKILL.md: *autonomous huddle · decide this without me · decide this headless ·
owner-decided huddle · convene the deciders · run the autonomous decider · fleet huddle ·
spec-first loop decision.*

Parameters (all optional except `task`):

| param | meaning | default |
|---|---|---|
| `task` | the question / decision to resolve (free text) | — (required) |
| `chief` | persona id that renders the verdict (the judge) | `owner` (synced owner persona) |
| `protocol` | deliberation method (see §5) | `delphi-condorcet` |
| `flavor` | task type → panel + option framing + worker pool (see §6) | inferred from `task` |
| `panel` | explicit persona set or jury size | flavor default (6) |
| `rounds` | deliberation rounds | 3 |
| `execute` | run Stage C (spawn workers) after deciding | `false` (decide-only) |

---

## 3. The model — three composable stages

> **"chief decides → give it to others by spawning → receive back"** is **not a different mode**.
> It is the composition A → (B) → C. Stage A is the core; C is an optional follow-on.

### Stage A — Deliberate (produce a choice)
1. Convene **N independent jurors** (the panel). Each gets a **distinct lens** and reasons
   **alone** — independence is what makes the vote statistically reliable (Condorcet).
2. Round 1: each juror runs a real **5-Whys** to the root question, scores every option, picks a
   winner. No cross-talk.
3. **Devil's Advocate** (Dialectical Inquiry) attacks the round-1 front-runner.
4. Rounds 2…R (**Delphi**): each juror sees **only the anonymized aggregate** + the standing
   counter, then privately revises. Anonymity removes seniority/groupthink; jurors are told to
   move *only on evidence* (conforming for its own sake breaks the Condorcet math).
5. **Chief** (LLM-as-Judge) reads the anonymized panel + final tally + counter and renders the
   decision **weighted by the chief persona's priors**.

**Output — the decision envelope:**
```json
{
  "winner": "<option>",
  "decision": "...",
  "rationale": "...",
  "overridden_dissent": "...",
  "owner_level": false,
  "escalate_reason": "...",
  "confidence": 0.0
}
```

### Stage B — Escalate-or-proceed (the human pipe)
- `owner_level == true` **or** `confidence` low → **WAIT**: push the envelope to the human over
  the pipe (Telegram, reusing the desk pattern), **block**, receive the reply, resume.
- else → proceed.

### Stage C — Execute (optional) — spawn workers, receive back
- The chief **dispatches** the chosen option to **worker agents**: the existing build pool
  (Sreyash → Hari → Harshvardhan) for code, or a flavor-specific pool.
- Workers act in parallel (**worktree isolation** for code), then **return** results.
- The chief **receives** results and **validates** them against the chief persona
  (owner-validation): **accept** / **escalate** (owner-level) / **re-decide** (loop to Stage A on
  the results). The chief is now an **orchestrator**, not only a judge.

**Why composition, not a new mode:** decide-only and decide-then-execute share Stage A; C just
reuses machinery huddle already has. Keep them separable.

---

## 4. The CHIEF is a synced persona ("sent separately")

The chief is **not baked into the roster** — it is a global (or repo) **synced persona**
discovered by `synced_assets.scan_personas`, role-tagged `decider`. This is the pipe seam: in a
human-run huddle the "chief" is the user; in headless mode the chief is the synced owner persona.
Same slot, different source. The owner persona
(`company-research/ceo/owner-persona.md`) is the reference chief: it supplies both the judging
priors **and** the escalation classifier (§8).

---

## 5. Pluggable protocols (`<protocol>`)

Each protocol is a documented driver with one interface: `(task, panel, rounds) → envelope`.

| protocol | shape | when |
|---|---|---|
| `delphi-condorcet` *(default, validated)* | independent jury → devil's advocate → anonymized Delphi rounds → vote → chief judge | high-stakes / owner-level; when false consensus is the risk |
| `debate` (Du 2023, Society of Minds) | open multi-agent debate over rounds | when cross-pollination beats independence |
| `self-consistency` | N independent samples → majority, no debate | cheap, maximal independence |
| `single-judge` | chief decides from one round | low-stakes fast path |
| `six-hats` / `ngt` / `kepner-tregoe` / `dialectical` | structured classics | domain fit |

Grounding: Multi-Agent Debate (Du 2023), Self-Consistency (Wang), LLM-as-Judge / ChatEval,
5-Whys, **Delphi (RAND)** for anonymity, **Condorcet Jury Theorem** for the independence
requirement (too much debate *correlates* voters and breaks accuracy — independence > chatter),
Devil's Advocate / Dialectical Inquiry (Mason 1969).

---

## 6. Pluggable flavors (task type)

A flavor is **config, not a code fork** — `{default panel, option framing, worker pool,
escalation sensitivity}`.

| flavor | panel | option space | Stage C workers |
|---|---|---|---|
| `brainstorm` | divergent (Elanchezian-style) | ranked idea directions | — (decide = pick directions) |
| `product-design` | PM · Design · Eng · Demand | chosen design + rationale | optional prototype build |
| `code-change` | Architect · Backend · Tester | chosen approach | build pool in worktrees → PR/diff back |
| `strategy` / `owner-call` | mixed lenses; **owner** is chief | strategic choice | — / outbound (owner-level) |

Flavor is inferred from `task` unless passed explicitly.

---

## 7. Inside huddle vs outside (the open fork)

**Recommendation: build INSIDE huddle now**, as a headless sub-task (`step-headless-decide.md`),
because it reuses personas, the synced chief, the build pool, the escalation pattern, and the
state/spec machinery — and the trigger fits huddle's surface. Spec it **generically** (pluggable
chief/protocol/flavor) so it can **graduate** into a standalone "decision OS" later without a
rewrite.

**Counter to keep on record:** the trading desks (Dhana/Thiru) already run autonomous decision
loops *outside* the huddle skill as long-running daemons. If headless-decide must run on non-repo
domains (trading, ops, marketing) as a persistent service, it belongs in the OS layer, not the
huddle skill. **Decision: start inside huddle for decision/engineering tasks; extract to the OS
layer when domain breadth or a daemon lifecycle demands it.**

---

## 8. Escalation classifier (owner-level)

From the owner persona — escalate **only** owner-level: **launch · spend · customer outbound ·
strategy pivot · irreversible · brand/face.** Everything else: CEO auto-proceeds (over-asking is a
failure). The classifier is the chief's job, returned as `owner_level` + `escalate_reason` in the
envelope. Validated in the sim: the chief returned `owner_level=false` for a "pick the product
direction" call and auto-proceeded, flagging "escalate only on a gate-crossing action like an OSS
publish or spend."

## 9. Cost tiering (don't run the full ceremony on everything)

The 3-round Delphi + devil's advocate is ~20 agents / ~580k tokens. Run it for **owner-level /
high-stakes** forks. For low-stakes, the chief fast-paths (`single-judge` / `self-consistency`),
same as the desks act autonomously on small moves and reserve ceremony for big ones.

---

## 10. State / artifacts

Reuse `huddle-state.json` + the daily note. A headless decision writes a `decisions[]` entry
carrying: `protocol`, `chief`, `panel`, per-round tallies, devil's-advocate text, the chief
verdict, `owner_level`, and (Stage C) links to worker artifacts (PRs/diffs). No new store.
Text only — no diagrams (consistent with the graph-review removal).

---

## 11. Implementation sketch

`references/steps/step-headless-decide.md` (router / sub-task):
1. Parse trigger → `{task, chief, protocol, flavor, panel, rounds, execute}`.
2. Load **chief** via `synced_assets.scan_personas` (role `decider`); fall back to a built-in.
3. Run the **protocol driver** — the validated Workflow pattern: `parallel()` independent
   jurors → anonymized aggregate → devil's advocate → Delphi `parallel()` revisions.
4. **Chief judge** → decision envelope.
5. **Stage B**: `owner_level` → escalate over the pipe (reuse desks' Telegram block-and-resume) → wait; else proceed.
6. **Stage C** (if `execute`): dispatch chosen option to the build pool (worktree isolation),
   receive, chief validates → accept / escalate / re-decide.
7. Record to `huddle-state.json`.

Reference implementation of the protocol driver: the simulation script
`autonomous-decider-sim-v2` (run `wf_db23dc55-eac`).

---

## 12. Acceptance criteria

1. The trigger grammar (§2) routes to headless mode; interactive huddle is unchanged otherwise.
2. Produces a decision envelope with `owner_level` classification for any `task`.
3. `owner_level=true` (or low confidence) → escalates over the pipe and **waits**; else proceeds.
4. `chief` is a swappable **synced** persona per invocation; `protocol` and `flavor` are pluggable.
5. With `execute=true`, the chief spawns workers, receives results, and validates them before
   recording — and re-decides or escalates on failure.
6. Stdlib/offline where it touches scripts; no change to interactive-mode state writes.

---

## 13. Open questions

- **Persistent-server / daemon model (undecided).** Instead of a step-doc that blocks during
  Stage B's human wait, run a long-lived **server** that holds the decide → escalate → wait →
  resume loop in memory, serving request/response, and **idles down after `X` idle time**. This is
  how the desks (Dhana/Thiru) already run. Open: is the wait an in-process blocking step (simple,
  ephemeral) or a server with a session + idle-timeout (durable, survives long human-reply gaps,
  but a real service to operate)? Likely the graduation trigger from "inside huddle" to "OS layer."
- **Graduation criteria** for moving headless-decide from the huddle skill into the standalone OS
  layer (daemon lifecycle? non-repo domains?).
- **Worker pools per flavor** beyond code (Sreyash pool covers code; what runs `product-design`
  prototypes or `brainstorm` follow-through?).
- **Protocol selection** — explicit `<protocol>` param vs. the chief auto-selecting by stakes.
- **Re-decide loop bounds** in Stage C — how many decide→execute→validate cycles before forced
  escalation?

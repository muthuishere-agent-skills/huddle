# Huddle

```bash
npx skills add muthuishere-agent-skills/huddle
```

**An LLM gives you the answer. Huddle gives you the argument — then lets you decide, and hands the build off to Sreyash.**

## What it is

A single LLM gives you one balanced answer. Huddle gives you 2-3 opinionated perspectives that disagree with each other, grounded in your repo, and then stops and waits for your call.

Ask the same question two ways:

> **To Claude directly:** "Should I use Redis or Postgres?" → a balanced pros-and-cons list.
>
> **In Huddle:** Shaama (backend, 20 years of on-call scars) says *"Redis adds operational burden you'll pay for at 2am. What's the failure mode when this cache goes cold?"* Suren (architect) counters *"Postgres won't hold at this access pattern — but can your team actually evolve a Redis-backed architecture?"*

That's not an answer. That's a tension. Tensions are where decisions get made.

## Who's in the room

**Discussion voices (18)** — each with a scar/win identity and named influences (Rumelt, Porter, Hickey, Tufte, Duarte, MEDDIC, DORA, Fowler, and more):

🧠 Maya (Strategy) · 🖥️ Luca (Frontend/Mobile/Games) · ⚙️ Shaama (Backend) · 🎨 Suna (Design) · 📋 Prabagar (PM) · 🔒 Senthil (Security) · 🎯 Babu (Demand Reality) · 🔥 Dileep (Founder) · 🧪 Nina (Tester) · 🏛️ Suren (Architect) · 🔍 Vidya (Pre-Sales) · 📝 Deepak (Tech Writer) · 📊 Wei (Data Analyst) · 🎼 Kishore (Storyteller) · 📡 Amara (Trend Researcher) · 💡 Elanchezian (Brainstorming) · 📐 Elango (Spec — silent background state worker)

**Background builders (3)** — you always address Sreyash; overflow delegates transparently:

⚡ **Sreyash** (primary) · 🛠️ **Hari** (sibling) · 🧰 **Vinish** (sibling)

Hand a task: *"Sreyash, build the auth flow."* He writes an OpenSpec-style spec, runs TDD red→green→refactor, spawns up to 12 named parallel workers (harsh-frontend-types, mohan-api-validation, leo-rename-sweep, …), and returns with artifacts. If he's busy, Hari or Vinish picks up — the orchestrator tells you who.

## Eight modes

Discussion · Research · Planning · Verification · **Build-Readiness** · Brainstorming · Spec Review · Wrap-Up. Huddle routes based on what you're asking for.

## What persists

Nothing lives in your repo unless you put it there. Huddle stores decisions, open questions, action items, and a conversation graph at `~/config/muthuishere-agent-skills/{repo}/{branch}/huddle/`. Resume any time: *"resume the huddle."*

On demand, Elango synthesizes an interactive graph view — 💡 issues, ✅ decisions, ⚔️ challenges, ❓ open questions, 📚 evidence — with edges linking them, plus a Timeline tab and the full Spec.

## When to use Huddle

- Choosing between approaches and need tradeoffs surfaced, not just listed.
- Stuck in a circle — fresh tensions break deadlocks.
- About to ship and want someone to find the failure path you missed.
- Need to brainstorm past idea #15 into where breakthroughs live.
- Want the discussion to survive — decisions, rationale, rejected paths, resumable.
- Want to hand the build off to Sreyash while you keep moving.

Use Claude directly for straightforward coding; use Huddle when the shape of the question matters more than the answer.

## Install

```bash
npx skills add muthuishere-agent-skills/huddle
```

Works without git too — falls back to local-folder mode.

## More

Full walkthrough in [`usage.md`](./usage.md). Technical components: see [`SKILL.md`](./SKILL.md), [`references/`](./references), [`scripts/`](./scripts), [`docs/`](./docs).

## Inspired by

https://github.com/bmad-code-org/BMAD-METHOD · OpenSpec.

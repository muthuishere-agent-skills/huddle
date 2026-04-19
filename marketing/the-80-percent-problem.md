# The 80% Problem — And What LLMs Actually Changed

Every experienced engineer knows this moment.

APIs come together. Flows start working. The UI looks complete. Very quickly it feels like the system is 80% done. Everyone relaxes.

Then the second half begins.

In 1985, Tom Cargill of Bell Labs gave this pattern its name:

> "The first 90% of the code accounts for the first 90% of the development time. The remaining 10% accounts for the other 90% of the development time."
>
> — *Communications of the ACM, Programming Pearls (Jon Bentley), 1985*

Software doesn't get built linearly. It gets built in two phases that feel nothing alike.

**Phase 1** is fast and visible. Features appear. The demo works. Momentum is real.

**Phase 2** is slow and invisible. Edge cases appear. Assumptions break. Real usage arrives. This is where systems either harden or fall apart.

## What LLMs changed

Phase 1 has been compressed. With tools like Claude, you can move from idea to running code in an afternoon. You hit "80% done" faster than was possible a year ago.

Phase 2 is exactly as hard as it ever was.

Because the last 20% was never about writing code. It's about uncovering hidden assumptions, identifying failure paths, understanding real usage, and validating decisions under pressure.

Before LLMs, the bottleneck was *"can we build this?"* Now the bottleneck is *"did we think about this deeply enough?"*

## The scarce resource is questions

Answers are easy now. Anyone can generate code, architecture, or docs on demand. What's become rare is the ability to ask the right questions — the uncomfortable ones:

- What happens when this fails in production?
- Who controls this input?
- What assumption are we making here?
- Is this solving the real problem, or a version of it?

These questions decide whether a system survives first contact with users.

## But decisions don't stay in one room

A decision gets made. Then it moves.

A developer explains it to another developer. Then to a manager. The CTO explains it to the CEO. Each retelling strips something — the tradeoff, the edge case, the assumption nobody wrote down.

The intent gets diluted. The risks get softened. The wrong thing starts sounding right.

LLMs give a clean answer — framed in one voice.

The question isn't just *"what's the right answer?"* It's *"can this decision survive every room it enters?"*

Good systems don't only fail because of bad code. They fail because the thinking didn't survive translation.

## They don't come from one voice

A backend engineer sees failure modes. A security engineer sees blast radius. A product manager sees the value metric. An architect sees capacity math. A tech writer makes the decision legible to the next team. A storyteller frames it for the room above engineering.

Each asks different questions — and most of those questions arrive too late, in incident channels and retros.

**Huddle** exists to pull those questions to the front, in every voice the decision will eventually need to survive.

It runs repo-aware, multi-persona engineering discussions *before* the system is locked in. 21 named personas — Shaama (backend, rollback-first), Senthil (security, blast radius), Prabagar (PM, value metric), Suren (architect, DORA and boring tech), Deepak (tech writer, handoff-survivable docs), Kishore (storyteller, kills bullet points), and more — disagree with each other, grounded in your repo, then stop and wait for your call.

Install:

```bash
npx skills add muthuishere-agent-skills/huddle
```

Better systems aren't built by faster answers. They're built by better questions, asked at the right time — and answers that survive every room they enter.

> Huddle helps you ask the right questions — and makes sure the answers survive every room they enter.

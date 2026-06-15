---
name: huddle
description: >
  Runs a repo-aware expert huddle for engineering decisions, planning, research, verification, and spec capture. Trigger this skill when the user says
  anything like: "start a huddle", "open a huddle", "huddle up", "create a huddle", "call a team meeting", "assemble the team", "get the experts in", "let's have a huddle",
  "what does the team think", "I need multiple perspectives", "huddle up", "start a huddle", "open a huddle", "war room", "let's discuss this
  as a team", "bring in the team", "team sync", "daily standup", "what should we do about X", "help me
  think through this", "I'm stuck on X let's discuss", "resume the huddle", "continue our discussion",
  "what did we decide", "get me a spec", "summarise the huddle", "what are the action items".
  Also trigger when the user seems blocked, frustrated, or facing a decision with multiple tradeoffs —
  even if they don't explicitly ask for a huddle. For HEADLESS, self-deciding huddles (no human in the loop),
  also trigger on: "autonomous huddle", "decide this without me", "decide this headless", "let the huddle decide and act",
  "convene the deciders", "run the autonomous decider", "fleet huddle", "owner-decided huddle", "spec-first loop decision".
---

# Huddle

Use this skill as the repo's decision huddle.

It runs in two modes. **Interactive (human-decides) is the default** — personas
surface perspectives, then the skill stops and waits for the user to decide.
**Autonomous Decider Mode** is opt-in and headless: a room deliberates with
5-whys across rounds and a designated OWNER persona resolves a weighted vote into
an actionable verdict with no human stop (owner-level forks still escalate to the
real owner). See `docs/huddle-autonomous-decider.md` and
`references/steps/step-autonomous-decider.md`.

For any topic raised, Claude surfaces relevant perspectives from a team of specialists (Architecture, Engineering, Security, Product, Design, Testing, Test Architecture, Analysis, Documentation, Strategy, Prioritization, Validation, Vision, Presentation, Narrative, Data, Trend Scanning, Spec Creation) — short, opinionated, grounded in the repo — then stops and waits for the user to decide and move forward.

The user drives. Claude does not make decisions or advance the agenda unilaterally.

## Core Rules

- Identify the user with `git config user.name`. Use their name throughout.
- Identify the repo with `git remote get-url origin` (parse owner/repo from URL). Fallback: `basename $(git rev-parse --show-toplevel)`.
- Store huddle memory in `~/.config/muthuishere-agent-skills/{reponame}/{branch}/huddle/`.
- Today's huddle note is `{YYYY-MM-DD}.md`. Always resume if it exists.
- After presenting perspectives, always stop and ask `{GIT_USER}` for their call or next direction.
- Never advance to a new topic without the user signalling to move on.
- Record every decision as made by the user, not by a perspective.

Follow the instructions in `./references/workflow.md`.

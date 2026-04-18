# Huddle

```bash
npx skills add muthuishere-agent-skills/huddle
```

Huddle is a repo-aware multi-persona discussion skill for engineering work.

It helps you think through implementation, architecture, testing, security, product tradeoffs, communication artifacts, and current ecosystem signals without turning the interaction into roleplay theater. The user drives. The room reacts. Decisions stay with the user.

## What It Does

- Pulls a small set of relevant personas for the current topic.
- Keeps discussion short, opinionated, and grounded in the repo.
- Supports discussion, planning, verification, research, brainstorming, spec-review, wrap-up, and build-readiness modes.
- Records huddle state so discussions resume cleanly later.
- Lets Elango synthesize the discussion into notes, summaries, specs, and a conversation graph (issues, decisions, challenges, evidence, open questions with edges between them).
- Hands off implementation to a background builder team (Sreyash, Hari, Vinish) that writes spec + tests + code and returns with artifacts.
- Works in git repos and falls back to local-folder mode for non-git projects.

## Core Ideas

- Small room by default.
- Artifact owner first, then domain expert, then one useful counterweight.
- Structured disagreement is useful; fake drama is not.
- Decisions belong to the user, not the personas.
- Notes and state survive beyond one chat session.
- Tough questions emerge from deepened persona worldview, not scripted question banks.
- Functional-pragmatic engineering over SOLID/Clean Code ceremony — classes and DI are fine, acronyms are not.

## Personas

Discussion voices (18 total in the roster): Maya (Strategy), Luca (Frontend/Mobile/Games), Shaama (Backend), Suna (Design), Prabagar (PM), Senthil (Security), Babu (Demand Reality), Dileep (Founder Visionary), Nina (Tester), Suren (Architect), Vidya (Pre-Sales), Deepak (Tech Writer), Wei (Data Analyst), Kishore (Storyteller & Presentation), Amara (Trend Researcher), Elanchezian (Brainstorming — sub-task), Elango (Spec Architect — silent background state worker).

Background builders (not discussion voices): **Sreyash** (primary, ⚡), **Hari** (sibling, 🛠️), **Vinish** (sibling, 🧰). User always addresses "Sreyash" — if he is busy, the orchestrator transparently delegates to Hari, then Vinish, and reports which one picked up.

Each enriched persona has a scar/win identity, named thinker references folded into their voice (Rumelt, Porter, Hickey, Tufte, Duarte, MEDDIC, DORA, Fowler Rule of Three, etc.), and common disagreements with peers — so debates feel like real perspective clashes.

## Background Builders — how they work

When you hand a task to Sreyash, he runs a four-phase flow:

1. **Init** — detect repo conventions silently (storage style, test framework, monorepo), run a short clarify round with the user, create a task manifest.
2. **Spec** — write an OpenSpec-style spec grounded in real repo paths; translate scenarios into failing tests (Red); plan green-phase work units.
3. **Process** — become a manager, spawn up to 12 named green-phase builders (harsh-frontend-types, mohan-auth-validation, leo-rename-sweep, etc.) in parallel, monitor with adaptive heartbeats, enforce soft/hard deadlines, kill and respawn on blockers.
4. **Wrap** — run full suite for cross-unit regressions, write final manifest, return a short report.

Details: [`references/steps/step-sreyash-build.md`](./references/steps/step-sreyash-build.md) and its four phase files (`step-sreyash-1-init.md` through `step-sreyash-4-wrap.md`).

## Storage Model

Huddle stores state under the user's config area. Nothing about the skill lives in your repo unless you explicitly put it there.

```text
<user-home>/config/muthuishere-agent-skills/
├── userconfig.json              # global: git_user, python_bin, gh_available, graph_review_url
└── <repo>/
    ├── config.json              # repo-scoped: reponame, owner_repo, default_branch
    ├── project.md               # Deepak's project doc (tech stack, test strategy, folder shape)
    ├── project-state.json       # project doc freshness metadata
    ├── specconfig.json          # Sreyash's repo-level spec config (ask once, remember)
    ├── sreyash/<NNN>-<slug>/task.xml    # background builder task manifests
    ├── hari/<NNN>-<slug>/task.xml
    ├── vinish/<NNN>-<slug>/task.xml
    └── <branch>/
        └── huddle/
            ├── huddle-state.json        # synthesized on demand / wrap-up
            ├── <YYYY-MM-DD>.md          # daily huddle note
            └── raw/                     # append-only raw decision events
                └── <ts>_decision.json
```

**State write behavior:**
- During live discussion, no file writes on normal rounds.
- On a decision, one raw event JSON file goes into `raw/` via the Write tool.
- On "give me notes" or wrap-up, synthesis reads `raw/*.json` + conversation context, writes the full `huddle-state.json` conforming to [`references/graph-schema.xml`](./references/graph-schema.xml), writes the `.md` note, deletes the raw files.

## Graph Review

When the user asks to see the graph, `scripts/md_to_html.py` bundles the note + state into a gzip+base64 URL fragment and opens a hosted review page. The page derives nodes (💡 issues, ✅ decisions, ⚔️ challenges, ❓ open questions, 📚 evidence) and edges from the state. Zoom controls, Timeline tab, and Spec tab.

Review URL is configurable via `userconfig.json` → `graph_review_url` (default: `https://muthuishere-agent-skills.github.io/huddle/index.html`).

## Non-Git Projects

Huddle does not require git. If the current folder is not a git repo, it falls back to local-folder mode:

- Repo name defaults to the folder name.
- Branch defaults to `main`.
- User defaults to the configured local user or the system username.
- Remote / PR behavior is skipped.

To remember a local project identity once and reuse it later:

```bash
python3 scripts/config_helper.py bootstrap <project_root> [repo_name] [branch] [user]
```

## Main Components

- [`SKILL.md`](./SKILL.md) — top-level skill contract.
- [`references/activation-routing.xml`](./references/activation-routing.xml) — routing, mode policy, disambiguation.
- [`references/persona-roster.xml`](./references/persona-roster.xml) — lightweight persona index.
- [`references/personas/`](./references/personas) — full persona definitions (voice, principles, influences).
- [`references/workflow.md`](./references/workflow.md) — execution sequence.
- [`references/steps/`](./references/steps) — ordered step files (preflight, meeting init, discussion, smart-exit, sub-tasks).
- [`references/graph-schema.xml`](./references/graph-schema.xml) — canonical schema for the graph-rendering payload.
- [`scripts/meeting_state.py`](./scripts/meeting_state.py) — single-command preflight.
- [`scripts/repo_context.py`](./scripts/repo_context.py) — tolerant startup context gathering.
- [`scripts/config_helper.py`](./scripts/config_helper.py) — repo config and local bootstrap.
- [`scripts/project_state.py`](./scripts/project_state.py) — project doc freshness gate.
- [`scripts/md_to_html.py`](./scripts/md_to_html.py) — bundle note + state and open the review page.
- [`scripts/huddle_writer.py`](./scripts/huddle_writer.py) — standalone raw event writer (for non-Claude agents).
- [`docs/index.html`](./docs/index.html) — hosted graph review surface.
- [`e2e/run.py`](./e2e/run.py) — smoke test for preflight and bundling.

## Inspiration

- Small-room discussion shape and persona-per-hat thinking from the general engineering review tradition.
- OpenSpec (Purpose, SHALL/MUST Requirements, GIVEN/WHEN/THEN Scenarios) for Sreyash's spec format.
- BMAD-METHOD for the story/task-manifest handoff pattern — adapted as durable per-task XML manifests under Sreyash's namespace, with async background execution (which BMAD lacks).

https://github.com/bmad-code-org/BMAD-METHOD

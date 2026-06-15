# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Huddle is a Claude Code skill that runs repo-aware, multi-persona engineering discussions. Users trigger it with phrases like "start a huddle" or "huddle up". The user drives all decisions; personas provide perspectives, then stop and wait.

## Skill Structure

```
SKILL.md                          # Skill registry entry (name, trigger phrases)
references/
  activation-routing.xml          # Mode router and flow-control policy (the brain)
  workflow.md                     # Variable definitions and execution sequence
  persona-roster.xml              # Lightweight persona index
  personas/                       # Full persona definitions (voice, principles)
  steps/
    step-00-preflight.md          # Three parallel preflight calls (global/project/session)
    step-01-meeting-init.md       # Load user, config, state, personas
    step-02-discussion.md         # Main discussion loop (all modes route here)
    step-03-smart-exit.md         # Wrap-up / pause persistence
    step-deepak-document.md       # Project documentation sub-task
    step-elanchezian-brainstorm.md # Progressive brainstorming sub-task
scripts/                          # Python helpers (no external deps, stdlib only)
e2e/run.py                       # Smoke tests
```

## Key Architecture Decisions

- **Preflight is three parallel calls.** `global_state.py` (cached in `userconfig.json`, ~1ms on warm cache), `project_state.py snapshot` (file reads + minimal git identity probes, recomputed once per session and bound to a variable), and `session_state.py` (live git/gh probes, never cached). Claude fires all three in one message so wall-clock ≈ the slowest.
- **Append-only raw writes, synthesis on demand.** During live discussion, NO file writes happen on normal rounds. On decisions/milestones, a single raw event JSON file is written directly to `{huddle_dir}/raw/` using the Write tool — no Python script, no background process. When the user asks for notes or wraps up, synthesis reads all `raw/*.json` + conversation context, writes `huddle-state.json` + `.md`, and deletes the raw files.
- **`huddle-state.json` is the synthesized source of truth** for all huddle state (decisions, participants, key moments, open questions, action items). Written only on explicit ask or wrap-up — not every round.
- **User-level config at `~/.config/muthuishere-agent-skills/userconfig.json`** stores `git_user`, `python_bin`, and `gh_available` — detected once globally on first ever huddle run, shared across all repos. Repo-level config at `~/.config/muthuishere-agent-skills/{reponame}/config.json` stores only repo-specific values (`reponame`, `owner_repo`, `default_branch`).
- **`PYTHON_BIN` detected once globally.** Stored in `userconfig.json` after first detection. All subsequent script calls use this variable. Never hardcode `python3` or `python`.
- **Reviews and summaries are text only.** Elango summarizes `huddle-state.json` + conversation context in conversation or the markdown note. There is no diagram, Mermaid, or visual review surface.
- **Externally-synced personas** are read on demand from `~/.config/muthuishere-agent-skills/personas/{name}/` (global) and `{reponame}/personas/{name}/` (repo). Each persona dir holds an optional definition `.md` plus an optional `memories/` of per-persona memory files. Producer-agnostic and read-only — the skill never writes them. Merged into the roster with precedence built-in < synced-global < synced-repo.
- **`activation-routing.xml`** is the central policy file. It defines modes (discussion, planning, verification, research, spec-review, wrap-up), flow-control rules, and disambiguation logic. Changes to huddle behavior almost always start here.
- **Steps execute in order** defined by `workflow.md`. Steps never skip; they stop and report on failure.
- **Personas are selected per-topic** (small room by default). The roster is in `persona-roster.xml`; full persona behavior is in individual markdown files under `references/personas/`.

## Scripts

All scripts are Python 3, stdlib-only, and output JSON to stdout.

| Script | Usage | Purpose |
|---|---|---|
| `global_state.py` | `python3 scripts/global_state.py` | Global, user-level state cached in `userconfig.json` — `git_user`, `python_bin`, `gh_available`, `persona_roster_xml`. Also returns `synced_personas_global` (externally-synced global personas + their memories — never cached, always reflects latest sync). First call detects and caches; subsequent calls are pure file reads (~1ms). Also spawns `migrate.py` detached on first-ever run. |
| `project_state.py` | `{PYTHON_BIN} scripts/project_state.py snapshot <project_root>` (also `check\|read\|write`) | Repo-scoped state computed once per session. `snapshot` returns `reponame`, `owner_repo`, `branch`, huddle paths, project doc freshness, `cross_branch_context`, `raw_events`, `saved_state`, and `repo_personas` (externally-synced repo personas + their memories). File reads only; minimal cheap git identity probes. |
| `synced_assets.py` | `{PYTHON_BIN} scripts/synced_assets.py scan <personas_dir> [source]` | Shared, stdlib-only reader for externally-synced persona directories (definition `.md` + `memories/`). Producer-agnostic, read-only, never raises on bad input. Imported by `global_state.py` and `project_state.py`; CLI form is for debugging. |
| `session_state.py` | `{PYTHON_BIN} scripts/session_state.py <project_root> <date>` | Live probes, never cached. Parallel batch of `git status`, `git log --since=8h`, `git branch`, `git HEAD`, `gh pr list`. Also ensures today's huddle note file exists and reports `is_resume`. |
| `huddle_writer.py` | `{PYTHON_BIN} scripts/huddle_writer.py <huddle_dir> '<event_json>'` | Standalone event writer for non-Claude agents (Codex, Copilot, Windsurf). Claude uses Write tool directly instead. |
| `config_helper.py` | `{PYTHON_BIN} scripts/config_helper.py read\|get\|set\|bootstrap ...` | Per-repo config CRUD at `~/.config/muthuishere-agent-skills/{reponame}/config.json` |
| `repo_context.py` | `{PYTHON_BIN} scripts/repo_context.py snapshot` | Gathers repo context (git state, PRs, remote info); supports non-git local-folder mode |
| `migrate.py` | `{PYTHON_BIN} scripts/migrate.py` | One-time migration from legacy `~/config/muthuishere-agent-skills/` to `~/.config/muthuishere-agent-skills/`. Spawned detached by `global_state.py` only when the new root doesn't yet exist. Idempotent; never overwrites existing targets. |

## Running Tests

```bash
python3 e2e/run.py
```

This smoke-tests the three preflight scripts (`global_state`, `project_state snapshot`, `session_state`), the externally-synced persona/memory scans (`synced_assets`), and the one-time `migrate.py` flow. Uses a temp `$HOME` so it won't touch real config.

## State Storage Layout

```
~/.config/muthuishere-agent-skills/
  userconfig.json                # Global: git_user, python_bin, gh_available (detected once)
  personas/                      # Externally-synced GLOBAL personas (read-only; any producer)
    {persona-name}/
      {persona-name}.md          # Optional definition (the lone *.md in the dir)
      memories/                  # Optional per-persona memories, one file each
        {slug}.md
  {reponame}/
    config.json                  # Repo-scoped: reponame, owner_repo, default_branch
    project-state.json           # Project doc freshness metadata
    personas/                    # Externally-synced REPO personas (read-only; this repo only)
      {persona-name}/
        {persona-name}.md
        memories/
          {slug}.md
    {branch}/huddle/
      huddle-state.json          # Synthesized state (written on demand/wrap-up only)
      {YYYY-MM-DD}.md            # Daily huddle note (written on demand/wrap-up only)
      raw/                       # Append-only event files (direct Write tool)
        {ts}_decision.json       # One file per decision
        {ts}_milestone.json      # One file per milestone
```

Branch names are sanitized for filesystem (`feature/login` -> `feature-login`). Cross-branch reads scan sibling branch folders for context.

The `personas/` directories are produced by external tools/CLIs/agents (huddle-store or anything else) and are **read-only** to the skill. A persona dir keyed to a built-in id (e.g. `shaama/`) that contains only `memories/` augments that built-in. Absent dirs change nothing — the skill behaves exactly as without them.

## Installation

```bash
./install.sh    # Symlinks skill into ~/.claude/skills/huddle (or ~/.agents/skills/)
./uninstall.sh  # Removes the symlink
```

## Non-Git Mode

Huddle works without git. Falls back to local-folder mode using folder name as repo identity. Bootstrap a local identity with:
```bash
python3 scripts/config_helper.py bootstrap <project_root> [repo_name] [branch] [user]
```

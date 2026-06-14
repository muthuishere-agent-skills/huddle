# Spec: huddle-store synced personas & memories

Status: **Proposed** (spec only; implementation deferred)
Date: 2026-06-14
Repo: `huddle` (the conversational Claude Code skill)
Related: `huddle-enterprise/docs/huddle-store-design.md` (§7 sync, §9 skill change)

---

## 1. Summary

The `huddle` skill gains **one additive capability**: read **extra personas** and **extra
memories** that the `huddle-store` CLI has synced onto disk, on top of the bundled built-in
roster. The skill does **not** talk to huddle-store over the network — it only reads `.md` files
the CLI placed in huddle's own config tree.

Two applicability levels, mirroring huddle's existing global-vs-repo config split:

- **Global** — applies to every huddle in every repo.
- **Repo** — applies only to huddles in a specific repo.

Hard requirements: **stdlib-only**, **offline**, **backward compatible** (no synced files ⇒
behaves exactly as today).

---

## 2. Scope

### In scope
- Read synced persona `.md` files and merge them into the roster the skill already builds.
- Read synced memory `.md` files and surface them as discussion grounding context.
- Two new directory scans in `global_state.py` (global) and two in `project_state.py` (repo).
- Roster-merge precedence rules and the persona-file format synced files must follow.
- Step-doc updates so the discussion flow consumes the merged roster + memories.

### Out of scope (non-goals)
- No HTTP client, auth, tokens, or network calls in the skill. The CLI owns all of that.
- No writing/syncing *from* the skill. Read-only consumption.
- No new third-party dependencies.
- No change to how the skill writes its own state (`huddle-state.json`, `raw/`).
- No change to the autonomous huddle in `huddle-enterprise` (separate engine).

---

## 3. On-disk contract (what the CLI produces, what the skill reads)

`huddle-store sync` writes into the existing config root
`~/.config/muthuishere-agent-skills/` (call it `CONFIG_ROOT`, already defined in both
`global_state.py` and `project_state.py`):

```
CONFIG_ROOT/
├── personas/                 GLOBAL personas      (read by every huddle)
│   └── <key>.md
├── memories/                 GLOBAL memories      (read by every huddle)
│   └── <slug>.md
├── huddle-store-sync.json    CLI-owned manifest   (skill IGNORES this file)
└── {reponame}/
    ├── personas/             REPO personas        (read only in that repo)
    │   └── <key>.md
    └── memories/             REPO memories        (read only in that repo)
        └── <slug>.md
```

- `{reponame}` is the same sanitized repo identity the skill already uses
  (`project_state.huddle_dir(reponame, branch)` keys off it). The **CLI** is responsible for
  mapping store-side `owner/repo` bindings to this `{reponame}` so the skill stays dumb.
- These `personas/` and `memories/` directories do **not** exist in huddle today, so there is no
  collision with `userconfig.json`, `{reponame}/config.json`, `project-state.json`, or
  `{branch}/huddle/` state. The skill must tolerate their absence.

### 3.1 Synced persona file format

A synced persona is a markdown file with YAML-ish frontmatter **matching the format the skill
already parses for built-ins** (`references/personas/*.md`), so no new parser is required. Minimum
fields:

```markdown
---
name: acme-billing-expert          # internal name
displayName: Bharath                # shown in the room
title: Billing Domain Expert
icon: "💳"
role: Subscription billing, proration, dunning, revenue edge cases
domains: [billing, subscriptions, proration, dunning, revenue]
primaryLens: "What does this do to billing correctness and revenue?"
communicationStyle: "Precise, numbers-first, allergic to hand-waving on money."
principles: "Money math must reconcile. Edge cases are the job."
---

## Signature Phrases
...full persona body the skill loads on demand for selected personas...
```

The store's `PersonaSummary` maps 1:1 to these fields (`key`→file stem + `name`, `name`→
`displayName`, plus `title/icon/role/domains/primary_lens/communication_style/principles`, and
`body_md`→the markdown body). The CLI is responsible for emitting this shape.

### 3.2 Synced memory file format

A memory is a small markdown note:

```markdown
---
title: Q3 pricing decision
tags: [pricing, gtm]
corpus: acme-finance        # optional
source: manual              # manual | pinned_qa
---

We decided Pro stays at $40/seat through Q3; no usage-based tier until billing
v2 ships. Rationale: ...
```

---

## 4. Script changes

Both scripts already define `CONFIG_ROOT = ~/.config/muthuishere-agent-skills`. Add a small,
shared, stdlib-only frontmatter reader (e.g. `scripts/synced_assets.py`) used by both, to avoid
duplicating the parser. It mirrors the tiny YAML-subset approach already used elsewhere — no
`yaml` import.

### 4.1 `global_state.py` (GLOBAL level)

`snapshot()` currently returns `persona_roster_xml` from `_read_roster()`. Extend it:

- **Personas:** scan `CONFIG_ROOT/personas/*.md`. For each, parse frontmatter and produce a
  roster entry shaped like the existing `<persona …/>` rows (id = file stem, plus
  icon/name/title/domains and a `file` pointing at the **absolute synced path** so on-demand body
  loads work). Return these as a new field, e.g.:
  - `synced_personas_global`: list of `{id, name, title, icon, domains, file, source: "synced-global"}`.
  - (Alternative: append synthesized `<persona source="synced-global" …/>` rows directly into
    `persona_roster_xml`. Either is acceptable; the list form is easier to test. Pick one and keep
    it consistent with §4.2.)
- **Memories:** scan `CONFIG_ROOT/memories/*.md`. Return a lightweight index
  `synced_memories_global`: list of `{title, tags, corpus, file}` (bodies loaded on demand, not
  inlined, to keep the snapshot small).
- Absent dirs ⇒ empty lists. Never raise. ~1ms warm-cache behavior is preserved (these are cheap
  directory globs; do not cache them in `userconfig.json` — they must reflect the latest sync).

### 4.2 `project_state.py` (REPO level)

`snapshot()` returns a dict at the end (currently `reponame … cross_branch_context`). It already
has `reponame`. Add:

- `repo_personas`: scan `CONFIG_ROOT/{reponame}/personas/*.md`, same entry shape as §4.1 but
  `source: "synced-repo"`.
- `repo_memories`: scan `CONFIG_ROOT/{reponame}/memories/*.md`, same index shape as §4.1.

Absent dirs ⇒ empty lists. File reads only; no new git/network work (consistent with this
script's contract).

### 4.3 Shared helper `scripts/synced_assets.py` (new)

```
parse_persona_file(path) -> dict   # {id, name, title, icon, domains, file, ...}
parse_memory_file(path)  -> dict   # {title, tags, corpus, file}
scan_personas(dir)       -> list[dict]
scan_memories(dir)       -> list[dict]
```

Stdlib-only. Reuses the frontmatter-parsing idiom already in the codebase.

---

## 5. Step-doc changes

### 5.1 `references/steps/step-01-meeting-init.md` — "Load Persona Roster"

Today: `{PERSONA_ROSTER}` = `GLOBAL_STATE.persona_roster_xml`. Change to **merge** three sources
into `{PERSONA_ROSTER}`:

1. Built-ins (`GLOBAL_STATE.persona_roster_xml`).
2. `GLOBAL_STATE.synced_personas_global`.
3. `PROJECT_STATE.repo_personas`.

**Precedence (most specific wins on `id`/key clash):** built-in < global < repo. A synced persona
with a new id is added to the room's available roster; one reusing a built-in id overrides that
built-in's metadata + body path.

On-demand body loading is unchanged in mechanism — for a selected synced persona, load the body
from its `file` path (an absolute synced path) instead of `references/personas/{file}`. The step
already "loads the full persona file only for the 2-3 selected personas," so this is just a path
source swap for synced entries.

### 5.2 Memory grounding (step-01 "Extract Session Context" / step-02 discussion)

Add a small grounding source alongside `SESSION_CONTEXT` and `PROJECT_STATE.saved_state`:

- Build `{HUDDLE_STORE_MEMORIES}` from `GLOBAL_STATE.synced_memories_global` +
  `PROJECT_STATE.repo_memories` (repo entries listed after global).
- Surface the **titles/tags** as available context during persona rounds; **load a memory's body
  on demand** when a persona's point relates to it (mirrors the existing on-demand persona-body
  pattern — keeps token cost bounded). These memories are read-only grounding ("what the company
  already knows/decided"); never written back, never synthesized into `huddle-state.json`.

Keep it non-intrusive: memories inform perspectives; they do not change flow control or the
stop-and-wait rule.

### 5.3 `references/steps/step-02-discussion.md` — "Persona Roster" section

Note that the roster source of truth at runtime is the **merged** roster from step-01 (built-ins +
synced global + synced repo), not solely `references/persona-roster.xml`. Update the wording so
selection/disambiguation operates over the merged set.

---

## 6. Backward compatibility & failure behavior

- **No synced dirs** ⇒ all new fields are empty lists ⇒ roster = built-ins, no memory source ⇒
  identical to today's behavior.
- **Malformed synced file** ⇒ skipped with a non-fatal note (same tolerance as the existing
  persona loader, which "skips malformed files but doesn't blow up"). One bad file never breaks a
  huddle.
- **Stale sync** ⇒ the skill shows whatever is on disk; freshness is the CLI's job. No TTL logic
  in the skill.
- **Offline** ⇒ fully functional; there is no network path.
- **Non-git / local-folder mode** ⇒ `{reponame}` still resolves (folder name), so repo-level
  scans work the same way.

---

## 7. Acceptance criteria

1. With a synced **global** persona present, starting a huddle in any repo shows that persona as
   available, and selecting it loads its synced body.
2. With a synced **repo** persona under `CONFIG_ROOT/{reponame}/personas/`, it is available **only**
   in that repo; a huddle in a different repo does not see it.
3. A synced persona whose id matches a built-in **overrides** the built-in (metadata + body).
4. Synced **memories** (global and repo) are surfaced as grounding; a persona can cite one, and its
   body loads on demand. Memories never appear in `huddle-state.json` or `raw/`.
5. With **no** synced dirs, behavior and output are byte-for-byte equivalent to current `main`
   (regression guard).
6. A malformed synced file is skipped without aborting the huddle.
7. All scripts remain stdlib-only and pass on a clean Python 3.11+.

---

## 8. Test plan (`e2e/run.py` additions)

Using the existing temp-`$HOME` harness so real config is untouched:

- **t1** seed `CONFIG_ROOT/personas/<x>.md` → assert `global_state.py` snapshot lists it under
  `synced_personas_global` with the right id/file.
- **t2** seed `CONFIG_ROOT/<reponame>/personas/<y>.md` → assert `project_state.py snapshot`
  returns it under `repo_personas`, and a different reponame does not.
- **t3** seed `CONFIG_ROOT/memories/*.md` and `CONFIG_ROOT/<reponame>/memories/*.md` → assert
  `synced_memories_global` / `repo_memories` indexes (title/tags/corpus/file).
- **t4** id-clash: a synced persona reusing a built-in id is reported so step-01 can apply
  override precedence.
- **t5** no synced dirs → snapshots return empty lists and existing keys unchanged (regression).
- **t6** malformed frontmatter file → skipped, scan still returns the good entries.

---

## 9. Implementation checklist

- [ ] `scripts/synced_assets.py` — frontmatter parse + scan helpers (stdlib).
- [ ] `global_state.py` — `synced_personas_global`, `synced_memories_global` in `snapshot()`.
- [ ] `project_state.py` — `repo_personas`, `repo_memories` in `snapshot()` return dict.
- [ ] `references/steps/step-01-meeting-init.md` — merged roster + memory grounding.
- [ ] `references/steps/step-02-discussion.md` — roster source-of-truth wording.
- [ ] `e2e/run.py` — t1–t6 above.
- [ ] `CLAUDE.md` — note the synced `personas/` + `memories/` dirs in the State Storage Layout and
      the `global_state.py` / `project_state.py` rows.

---

*This spec covers only the read-side `huddle` skill change. The producing side
(`huddle-store sync`, the `/sync` endpoint, persona/memory authoring) is specified in
`huddle-enterprise/docs/huddle-store-design.md`.*

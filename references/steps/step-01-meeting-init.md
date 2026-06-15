# Step 01: Huddle Init

`GLOBAL_STATE`, `PROJECT_STATE`, and `SESSION_STATE` are already available from step-00. Do not re-run shell commands or re-read files.

## Extract Trigger Topic

Read the user's trigger message. If it carried a topic (e.g. "huddle up — should we split this service?", "start a huddle, let's review yesterday's refactor", "huddle: Postgres vs DynamoDB"), extract it and store as `{INITIAL_TOPIC}`. If the trigger was bare ("start a huddle", "huddle up", "/huddle"), leave `{INITIAL_TOPIC}` empty.

**The trigger topic wins.** If `{INITIAL_TOPIC}` is non-empty, route directly to discussion mode on that topic. Do not show the roster first, do not ask "what do you want to work through today", and do not stop for a Deepak doc offer — those are fallbacks for bare triggers only.

## Ground Personas In Existing Docs

`PROJECT_STATE.project_docs_found` lists doc files already in the repo (README*, CLAUDE.md, AGENTS.md, `docs/*.md`). If non-empty:
- Quickly scan them (parallel Read tool calls, one per file) before the first persona round so perspectives are grounded in actual project facts, not invented.
- Do NOT offer to regenerate these — Deepak treats existing docs as source of truth.

## Extract Session Context

Review everything in this conversation that happened **before the huddle was triggered** — any Claude, Codex, or other agent output. Extract:
- What was the user working on or trying to solve?
- What files were being edited or created?
- What errors or blockers came up?

Store as `{SESSION_CONTEXT}`. Empty if nothing preceded the trigger.

## Load Persona Roster

Build `{PERSONA_ROSTER}` by **merging three producer-agnostic sources**, most specific wins on `id`:

1. **Built-ins** — `GLOBAL_STATE.persona_roster_xml` (the bundled roster).
2. **Synced global** — `GLOBAL_STATE.synced_personas_global` (applies in every repo).
3. **Synced repo** — `PROJECT_STATE.repo_personas` (applies only in this repo).

**Precedence: built-in < synced-global < synced-repo.** A synced persona with a *new* `id` is added to the available roster. A synced persona reusing a built-in `id` *overrides* that built-in's metadata and body path. Sources 2 and 3 are read from disk and reflect whatever any external tool/CLI/agent last synced — the skill never writes them.

Each synced entry carries `id`, `name`, `title`, `icon`, `domains`, a `file` (absolute path to the synced definition `.md`, or `null` when the entry only augments a built-in with memories), and a `memories` index (each: `title`, `tags`, `corpus`, `persona`, `file`).

Do not load full persona body files during init. Only load the full persona file for the 2-3 personas selected for the current round, plus any persona explicitly named by `{GIT_USER}`. For a **synced** persona, load the body from its `file` path (an absolute synced path) instead of `references/personas/{file}`; when a synced entry overrides a built-in, prefer the synced `file` if present, else fall back to the built-in body.

### Per-persona memories (grounding)

A persona may carry its own `memories` (synced global + synced repo, repo listed after global). These are read-only grounding — *what this persona has already seen or decided*. Treat them like the on-demand persona body: surface a selected persona's memory **titles/tags** as available context, and **load a memory's body from its `file` path only on demand** when that persona's point relates to it. Per-persona memories never change flow control or the stop-and-wait rule, and are never written back or synthesized into `huddle-state.json` / `raw/`.

## Surface Warnings (all paths)

If `GLOBAL_STATE.warnings` is non-empty, show each warning as a brief note before any greeting or persona output:

> ⚠️ {warning text}

Example: `⚠️ Python not found. Install Python 3.x.`

If `PROJECT_STATE.owner_repo` is empty, also surface:

> ⚠️ No git remote configured — PR listing and project docs scan skipped.

## Act on next_action

Ordered cascade — first matching rule wins:

1. `{INITIAL_TOPIC}` non-empty → route to discussion mode on that topic (`show_roster` layout, but skip the "what do you want to work through today" ask — you already know)
2. `SESSION_STATE.is_resume` → `resume_summary`
3. `PROJECT_STATE.project_doc_missing` → `deepak_doc_offer` (blocking)
4. else → `show_roster`

In paths 1 and 4, if `PROJECT_STATE.project_doc_missing` is still true, append Deepak's offer as a **soft nudge** at the end of the first persona round — one line, non-blocking:

> 📝 **Deepak** — heads up, I can write a project doc for this repo any time. Just ask.

### `"deepak_doc_offer"` (blocking — only reached when trigger was bare and repo has no existing docs)

**Guard:** If the repo/folder has fewer than 20 files (empty or near-empty project), skip this entirely — treat as `show_roster` instead.

Deepak speaks first. Do not show the roster yet.

Brief `{GIT_USER}` on repo state from `SESSION_STATE.git_status` + `SESSION_STATE.recent_commits`, then Deepak says:

> 📝 **Deepak** _(Tech Writer)_ — I don't see any project documentation yet. Want me to do a quick scan and write one?

**Stop. Wait for `{GIT_USER}` to answer.**

- If yes → route to `steps/step-deepak-document.md` immediately
- If no → set `DEEPAK_DOC_OFFERED=true`, show the roster, ask what to discuss

### `"resume_summary"`

Today's note already has content. From `PROJECT_STATE.saved_state`, surface:
- Last topic discussed
- Open questions and action items
- Active personas

If `{SESSION_CONTEXT}` or `SESSION_STATE.git_status`/`recent_commits` shows new activity since last save, surface it:
> "I can also see you've been working on X since we last met."

Restore active personas from `saved_state.active_personas`. Do not show the full roster unless `{GIT_USER}` asks to change the team.

Ask `{GIT_USER}`: "Where do you want to pick up?" Wait. Load step-02.

### `"show_roster"`

Fresh start. Greet `{GIT_USER}` by name. Write the huddle note header.

Brief the team with what you've already observed:

```
**Before we start — here's what I'm seeing:**

[If {SESSION_CONTEXT} is not empty]
**This session:** {2-4 bullet summary}

[If SESSION_STATE.git_status or SESSION_STATE.recent_commits are non-empty]
**Repo state:** {modified/staged files and recent commits}

[If SESSION_STATE.open_prs is non-empty]
**Open PRs:** {title + author, one line each}

[If PROJECT_STATE.cross_branch_context is non-empty]
**Last huddle(s) on sibling branches:** {1-line summary per entry}
```

Omit any section with nothing to show. If all sections are empty, skip the brief entirely.

Show the persona roster (displayName + title + icon, one line each) and ask:
> "{GIT_USER}, what do you want to work through today?"

Wait for `{GIT_USER}` to respond before loading step-02.

## Cross-Branch Context (all three paths)

`{CROSS_BRANCH_CONTEXT}` = `PROJECT_STATE.cross_branch_context` — sibling branches sorted with `main`/`master`/`dev`/`develop` first, each with `branch`, `date`, `summary`. Surface if relevant; do not re-scan the filesystem.

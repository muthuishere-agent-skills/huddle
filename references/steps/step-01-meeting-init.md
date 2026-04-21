# Step 01: Huddle Init

`GLOBAL_STATE`, `PROJECT_STATE`, and `SESSION_STATE` are already available from step-00. Do not re-run shell commands or re-read files.

## Extract Session Context

Review everything in this conversation that happened **before the huddle was triggered** — any Claude, Codex, or other agent output. Extract:
- What was the user working on or trying to solve?
- What files were being edited or created?
- What errors or blockers came up?

Store as `{SESSION_CONTEXT}`. Empty if nothing preceded the trigger.

## Load Persona Roster

Use `{PERSONA_ROSTER}` = `GLOBAL_STATE.persona_roster_xml`. It's the lightweight roster source of truth: `id`, `icon`, `name`, `title`, `domains`, persona file reference.

Do not load full persona body files during init. Only load the full persona file for the 2-3 personas selected for the current round, plus any persona explicitly named by `{GIT_USER}`.

## Surface Warnings (all paths)

If `GLOBAL_STATE.warnings` is non-empty, show each warning as a brief note before any greeting or persona output:

> ⚠️ {warning text}

Example: `⚠️ Python not found. Install Python 3.x.`

If `PROJECT_STATE.owner_repo` is empty, also surface:

> ⚠️ No git remote configured — PR listing and project docs scan skipped.

## Act on next_action

Use the rule from step-00:
- `PROJECT_STATE.project_doc_missing` → `deepak_doc_offer`
- else `SESSION_STATE.is_resume` → `resume_summary`
- else → `show_roster`

### `"deepak_doc_offer"`

**Guard:** If the repo/folder has fewer than 20 files (empty or near-empty project), skip this entirely — treat as `show_roster` instead. The Python preflight already checks this, but if it slips through, do not offer docs for a nearly empty folder.

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

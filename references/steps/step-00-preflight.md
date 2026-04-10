# Step 00: Pre-flight

Run exactly one command. Do not run any git or gh commands before this.

```bash
python3 {skill-root}/scripts/meeting_state.py ensure {project-root} {YYYY-MM-DD}
```

`{project-root}` = the user's project directory (absolute path).
`{YYYY-MM-DD}` = today's date.

This derives repo identity, branch, git user, git status, open PRs, project scan, and huddle state all in parallel.
Store the full JSON output as `HUDDLE_INIT`.

## Session Variables from HUDDLE_INIT

Extract and store these for the entire session:

- `{PYTHON_BIN}` = `HUDDLE_INIT.python_bin` — the detected Python binary path. Use this for **all** subsequent `python` invocations. Never hardcode `python3` or `python`.
- `{HUDDLE_DIR}` = `HUDDLE_INIT.huddle_dir`
- `{SKILL_ROOT}` = the installed root folder of this skill

If `python_bin` is `null`, stop immediately: "Python not found. Install Python 3.x."

Proceed to step-01.

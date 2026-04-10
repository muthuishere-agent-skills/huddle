# Step 03: Smart Exit

Use natural wrap-up detection. Do not require explicit keywords.

<step-policy step="smart-exit">
  <exit-rules>
    <rule>Do not reduce exit to a generic summary. Preserve the outcome, the people involved, and whether the meeting is paused or truly closed.</rule>
    <rule>Capture active personas and the perspectives that most directly shaped the outcome.</rule>
    <rule>Preserve decisions, open questions, action items, latest summary, and status.</rule>
    <rule>If {GIT_USER} wants review, open the current huddle review bundle in the browser.</rule>
  </exit-rules>

  <persisted-state>
    <field>current_topic</field>
    <field>open_questions</field>
    <field>action_items</field>
    <field>latest_summary</field>
    <field>active_personas</field>
    <field>decision_influencers</field>
    <field>meeting_status — set to "paused" if user paused, "closed" if user fully ended the session</field>
  </persisted-state>

  <elango-rules>
    <rule>Elango owns the final note state and visual review flow.</rule>
    <rule>On wrap-up, Elango runs full synthesis: read {HUDDLE_DIR}/raw/*.json + conversation context → write huddle-state.json and {date}.md → delete raw files.</rule>
    <rule>Do not generate or refresh the graph projection during wrap-up unless {GIT_USER} asks for review or accepts a review prompt.</rule>
    <rule>If the user wants to inspect the final notes, run synthesis first, then launch {PYTHON_BIN} {SKILL_ROOT}/scripts/md_to_html.py and open the review URL in the browser.</rule>
    <rule>Exit should leave enough context that a future resume can understand both the conclusions and who shaped them.</rule>
  </elango-rules>
</step-policy>

## Trigger When

`{GIT_USER}`'s primary intent is to end or pause the meeting:

- "that's enough for today"
- "let's stop here"
- "this was helpful"
- "we've covered it"
- "good for now"
- "save and pause"
- "let's pause here"

Also trigger when the facilitator has just surfaced a completion-aware checkpoint and `{GIT_USER}` confirms they want to wrap or pause.

Do not trigger if the phrase is incidental inside a larger question.

## Exit Flow

1. **Run synthesis first:** Read all `{HUDDLE_DIR}/raw/*.json` in timestamp order + conversation context
2. Build complete `huddle-state.json` (decisions, participants, key_moments, open_questions, action_items, active_personas, latest_summary, meeting_status)
3. Write today's huddle note `{HUDDLE_NOTE_FILE}` in the Meeting Document Shape from step-02
4. Delete all files in `{HUDDLE_DIR}/raw/`
5. Summarize what the meeting covered today
6. List decisions `{GIT_USER}` made (attributed to them by name)
7. List open questions
8. List action items
9. If the user paused rather than fully ended, say so explicitly: "Paused here." Set `meeting_status="paused"`.
10. If `{GIT_USER}` wants to inspect the final notes visually, launch:
    `{PYTHON_BIN} {SKILL_ROOT}/scripts/md_to_html.py {HUDDLE_NOTE_FILE}`
    and open the review URL in the browser
11. Tell `{GIT_USER}` they can resume by starting `huddle` again in this repo

## Final Response Format

Keep it short:

```
**Summary** — what was covered
**Decisions** — what {GIT_USER} decided
**Open** — unresolved questions
**Actions** — next steps
**Status** — wrapped or paused

Resume anytime: start huddle in this repo.
```

# Huddle Artifact Model

## Goal

Define the 3 core artifacts Huddle should maintain for every session:

1. Markdown spec / notes
2. History graph
3. Current-state graph

This keeps Huddle readable for humans while also making the reasoning flow, participant influence, and latest state explicit.

## Decision

Huddle should not choose between Markdown and graph.

It should keep both:

- Markdown for durable human-readable output
- History graph for how the discussion evolved
- Current-state graph for where the room stands now

The visible product should feel like a huddle:

- the user drives
- named participants contribute
- Elango maintains state in the background
- the renderer shows what changed, how the room moved, and where it stands now

## The 3 Artifacts

### 1. Markdown Spec

Purpose:

- human-readable artifact
- summary, notes, spec, or action-item export
- easy to review, save, and share

Examples:

- meeting summary
- feature spec
- decision note
- action-item list

Owner:

- Elango

Characteristics:

- readable
- structured
- export-friendly
- not the only source of truth

### 2. History Graph

Purpose:

- show how the discussion evolved over time
- show branches, objections, reversals, rejected paths, refinements, and joins
- preserve reasoning flow, not just final output

Questions it should answer:

- how did we get here?
- which options were considered?
- what arguments shifted the room?
- what got rejected?
- where did disagreement or refinement happen?

Owner:

- Elango

Characteristics:

- append-oriented
- timeline-aware
- supports animation and step-by-step replay
- participant-aware
- maintained by an internal background pass, not by visible persona chatter

### 3. Current-State Graph

Purpose:

- show the latest working understanding
- show what is currently true, chosen, open, and actionable

Questions it should answer:

- where do we stand now?
- who most recently shaped the room?
- what problem are we solving?
- which context is active?
- what options remain live?
- what decision has been made?
- what is still open?
- what should happen next?

Owner:

- Elango

Characteristics:

- reduced latest state
- clean snapshot
- participant-aware summary of the latest room state
- optimized for orientation, not replay
- maintained separately from history so the latest state stays legible

## Suggested Storage

Store these under the branch huddle directory:

```text
<user-home>/config/.m-agent-skills/<repo>/<branch>/huddle/
├── huddle-state.json
├── <YYYY-MM-DD>.md
├── graph-history.json
└── graph-current.json
```

Meaning:

- `huddle-state.json`
  - lightweight session state for routing/resume
- `<YYYY-MM-DD>.md`
  - human-readable session artifact
- `graph-history.json`
  - evolution of reasoning over time
- `graph-current.json`
  - latest materialized state

## Visible State Model

Huddle should present state in 3 layers:

### 1. Visible Room

Show:

- the user
- the active named participants for the current round
- their icons and names
- who influenced the round when that is worth surfacing

Do not show:

- generic boxes like `Experts (LLMs)`
- abstract system-only labels unless they help the user understand the room

### 2. State Updates

Show updates in human terms:

- what was added
- what was challenged
- what was linked
- what was agreed
- what was deferred
- what stayed open

This is the readable surface of the evolving graph.

### 3. Current State

Show the latest room picture:

- current problem
- current context
- chosen direction
- open questions
- next actions
- current status of major branches

## Icon Legend

Use a small, stable icon set across history, current state, and rendered review views.

### Status Icons

- `✅` Agreed
- `⏸️` Deferred
- `❓` Open
- `⚔️` Challenged
- `🔗` Linked
- `💡` Added
- `📝` Captured in spec

### Participant Representation

Participants should appear with:

- their existing icon
- their display name
- short text only

Examples:

- `🧠 Maya`
- `🏛️ Suren`
- `📚 Kishore`
- `📐 Elango`

The renderer should avoid oversized persona labels. The room should feel neat, compact, and readable.

## Source of Presentation State

The HTML renderer should not invent presentation meaning on its own.

Elango should write presentation-oriented state into the JSON artifacts, and the renderer should primarily display that state.

### JSON Should Carry

- participant icon, name, and short meta
- event status
- event display tag
- event display title
- event display detail
- node status
- node display tag
- node display detail

### Renderer Should Do

- read those fields
- map them into cards, chips, and graph labels

### Renderer Should Not Do

- derive the core business meaning of the discussion
- invent statuses that Elango did not record
- become the place where huddle logic lives

Elango owns the semantics.
The HTML layer owns presentation.

## Graph Model

### Node Types

Minimum node types:

- `problem`
- `context`
- `option`
- `argument`
- `tension`
- `decision`
- `question`
- `action`
- `result`

Optional later:

- `constraint`
- `risk`
- `artifact`
- `assumption`
- `evidence`
- `participant`
- `update`

### Edge Types

Minimum edge types:

- `has_context`
- `suggests`
- `supports`
- `opposes`
- `refines`
- `leads_to`
- `decides`
- `opens`
- `resolves`
- `results_in`

Optional later:

- `depends_on`
- `supersedes`
- `blocked_by`
- `agrees_with`
- `disagrees_with`
- `defers`

## State Representation

The graph is not only a technical structure. It is the underlying representation of the huddle.

### History Graph Should Represent

- who introduced a thread
- when a branch opened
- when two ideas were linked
- when something was challenged
- when the room converged
- when something was deferred instead of decided

### Current-State Graph Should Represent

- what is currently active
- what has been agreed
- what is still open
- what has been deferred
- what should happen next
- which participants most recently influenced the state, when useful

### Markdown Should Represent

- the readable decision/spec layer
- rationale
- rejected paths
- deferred items
- open questions
- next actions

Markdown is a projection of the graph, not the source of truth.

## Current-State Graph Shape

This should represent the latest resolved working picture.

Example:

```json
{
  "session_id": "2026-04-05-main",
  "updated_at": "2026-04-05T12:00:00Z",
  "participants": [
    { "id": "user", "name": "Muthu", "icon": "🎼", "role": "user" },
    { "id": "suren", "name": "Suren", "icon": "🏛️", "role": "architect" },
    { "id": "elango", "name": "Elango", "icon": "📐", "role": "background-state-worker" }
  ],
  "nodes": [
    { "id": "p1", "type": "problem", "label": "Huddle startup is brittle", "status": "active", "icon": "💡" },
    { "id": "c1", "type": "context", "label": "Some repos have no remote or no commits", "status": "active", "icon": "🔗" },
    { "id": "o1", "type": "option", "label": "Use safe startup helper", "status": "active", "icon": "💡" },
    { "id": "d1", "type": "decision", "label": "Use repo_context.py for tolerant startup", "status": "agreed", "icon": "✅" },
    { "id": "q1", "type": "question", "label": "Should local-folder mode be bootstrapped?", "status": "open", "icon": "❓" },
    { "id": "x1", "type": "question", "label": "Should HTML rendering wait for visible tabs?", "status": "deferred", "icon": "⏸️" },
    { "id": "a1", "type": "action", "label": "Add bootstrap config support", "status": "active", "icon": "📝" }
  ],
  "edges": [
    { "from": "p1", "to": "c1", "type": "has_context", "status": "linked", "icon": "🔗" },
    { "from": "c1", "to": "o1", "type": "suggests", "status": "linked", "icon": "🔗" },
    { "from": "o1", "to": "d1", "type": "leads_to", "status": "linked", "icon": "🔗" },
    { "from": "d1", "to": "q1", "type": "opens", "status": "open", "icon": "❓" },
    { "from": "d1", "to": "x1", "type": "defers", "status": "deferred", "icon": "⏸️" },
    { "from": "d1", "to": "a1", "type": "results_in", "status": "active", "icon": "📝" }
  ]
}
```

## History Graph Shape

History should preserve change over time.

Recommended model:

- event stream plus graph diffs
- or versioned graph snapshots with timestamps

Recommended structure:

```json
{
  "session_id": "2026-04-05-main",
  "events": [
    {
      "ts": "2026-04-05T11:10:00Z",
      "kind": "node_added",
      "actor": { "name": "Muthu", "icon": "🎼" },
      "node": { "id": "p1", "type": "problem", "label": "Huddle startup is brittle", "icon": "💡" }
    },
    {
      "ts": "2026-04-05T11:12:00Z",
      "kind": "node_added",
      "actor": { "name": "Suren", "icon": "🏛️" },
      "node": { "id": "o1", "type": "option", "label": "Use safe startup helper", "icon": "💡" }
    },
    {
      "ts": "2026-04-05T11:14:00Z",
      "kind": "challenge_recorded",
      "actor": { "name": "Shaama", "icon": "⚙️" },
      "node": { "id": "a1", "type": "argument", "label": "Startup must not fail in no-remote repos", "icon": "⚔️" }
    },
    {
      "ts": "2026-04-05T11:16:00Z",
      "kind": "decision_recorded",
      "actor": { "name": "Muthu", "icon": "🎼" },
      "node": { "id": "d1", "type": "decision", "label": "Use repo_context.py for tolerant startup", "icon": "✅" }
    },
    {
      "ts": "2026-04-05T11:18:00Z",
      "kind": "deferred_recorded",
      "actor": { "name": "Elango", "icon": "📐" },
      "node": { "id": "x1", "type": "question", "label": "Revisit advanced renderer motion later", "icon": "⏸️" }
    }
  ]
}
```

## Update Rules

### Background Prompt Pattern

Elango should update these artifacts through an internal background pass after each meaningful exchange.

Recommended structure:

```xml
<background_pass>
  <discussion_delta />
  <history_graph_update />
  <current_state_update />
  <markdown_projection />
  <visibility>internal only</visibility>
</background_pass>
```

Why:

- structured sections reduce collisions between visible conversation and hidden state work
- isolated background updates keep the user-facing room clean
- separate history and current-state sections prevent the model from collapsing them together

### During Discussion

Elango should:

- append new nodes to history when a new topic/option/argument appears
- record edges when reasoning relationships become clear
- mark decisions only when the user makes the call
- mark deferred items when the room intentionally postpones them
- record rejected paths when the room clearly discards one
- preserve open questions separately from decisions
- preserve lightweight participant attribution when useful

### When Rendering Current State

Elango should:

- collapse obsolete branches
- keep only active context
- keep the chosen decision path
- preserve unresolved questions
- preserve deferred items distinctly from open questions
- preserve next actions

### When Producing Markdown

Elango should:

- project graph state into human-readable form
- include rationale and rejected paths when relevant
- include agreed, deferred, and open status clearly
- optionally embed Mermaid diagrams derived from the graph

## Renderer Views

The renderer should support 3 views from the same artifact set.

### 1. Spec View

Shows:

- Markdown notes/spec
- decisions
- deferred items
- rationale
- open questions
- actions

Best for:

- reading
- review
- sharing

Zoom:

- no custom zoom surface required
- rely on browser zoom and readable layout

### 2. History View

Shows:

- how the discussion evolved
- participant-driven updates over time
- branch openings and joins
- challenges and reversals
- where the room changed direction

Best for:

- replay
- understanding reasoning flow
- seeing why the room converged

Zoom:

- pan and zoom should be native
- this is a map-like surface

Animation ideas:

- stagger update reveal
- animate branch growth
- step-through timeline scrubber
- highlight newly added, challenged, agreed, and deferred nodes

### 3. Current-State View

Shows:

- current problem
- current active context
- current live options
- chosen decision
- deferred items
- open questions
- next actions

Best for:

- quick orientation
- standups
- resume
- "where do we stand?"

Zoom:

- pan and zoom should be native
- the user should be able to inspect branches and statuses without losing context

Animation ideas:

- pulse active nodes
- dim archived or superseded paths
- smooth transitions when current state changes

## Renderer Surface Guidance

The renderer should feel like a huddle, not a generic systems graph.

### Top Strip

Show:

- user
- active participants with icon + name
- small text only

Avoid:

- oversized architecture boxes
- generic labels like `Experts (LLMs)`

### Update Language

Use readable labels such as:

- `💡 Added`
- `⚔️ Challenged`
- `🔗 Linked`
- `✅ Agreed`
- `⏸️ Deferred`
- `❓ Open`
- `📝 Captured`

### Current-State Language

Prefer:

- `Agreed`
- `Deferred`
- `Open`
- `Next`

Avoid:

- `derived nodes`
- `derived links`
- raw graph jargon unless it helps debugging

## Elango's Role

Elango should evolve from:

- silent note-taker

to:

- graph steward
- state curator
- Markdown/spec renderer

That means:

- he maintains the history graph
- he maintains the current-state graph
- he produces Markdown as a projection of the graph-backed session state

## Product Framing

This keeps Huddle aligned with the intended product direction without forcing execution to become the headline.

Huddle can be framed as:

- a participant-driven stateful discussion room
- with evolving shared state
- visible history
- visible current state
- human-readable spec output
- background state maintenance by Elango

Execution can stay secondary or background-capable.

## Recommended Next Step

Implement in this order:

1. add `graph-history.json`
2. add `graph-current.json`
3. define Elango update rules in the skill
4. render current-state and history views with icons and readable labels
5. add zoomable history and current-state map views
6. keep Markdown as the readable export layer

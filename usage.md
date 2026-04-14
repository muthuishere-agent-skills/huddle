# Huddle Usage Guide

Huddle is a repo-aware, multi-persona discussion skill for Claude Code (and compatible agents). It assembles a small panel of opinionated engineering personas to help you think through decisions, architecture, product tradeoffs, security concerns, and more — grounded in your actual codebase.

You drive every decision. The personas present perspectives, then stop and wait.

## Installation

```bash
npx skills add m-agentic-skills/huddle
```

Or manually:

```bash
cd huddle
./install.sh
```

This symlinks Huddle into `~/.claude/skills/huddle`. Restart your agent session to pick it up.

## Starting a Huddle

Say any of these in your Claude Code session:

- "start a huddle"
- "huddle up"
- "let's discuss this as a team"
- "what does the team think about X"
- "I need multiple perspectives on this"
- "help me think through this"
- "I'm stuck on X, let's discuss"
- "team sync"

Huddle also activates when you seem blocked, frustrated, or facing a decision with multiple tradeoffs — even without an explicit trigger.

## What Happens When You Start

1. **Preflight** — Huddle detects your repo identity, branch, git user, recent commits, open PRs, and project shape. Works without git too (falls back to folder-based identity).
2. **Persona selection** — Two personas are picked based on the topic. A third is suggested only if it materially changes the outcome.
3. **Discussion** — Each persona gives a short, opinionated take grounded in the repo. Then they stop and wait for you.
4. **You decide** — Every decision is recorded as yours. Personas never advance the agenda.
5. **State saved** — Decisions and milestones are persisted so you can resume later.

## Discussion Modes

Huddle automatically routes to the right mode based on what you say.

### Discussion (default)

> "what do you think about X", "help me think through this"

Personas surface perspectives on your topic, highlight the core tension, and wait for your call.

### Research

> "what's happening right now with X", "latest on X", "research this topic"

Amara (Trend Researcher) leads with source-backed ecosystem scanning — repos, articles, community signals. The room reacts to what she finds.

### Planning

> "make a plan", "how should we implement this", "break this down"

Turns a chosen direction into a concrete execution sequence with dependencies and ordering.

### Verification

> "does this hold up", "is this safe", "verify this", "are we done"

Pressure-tests claims, completeness, and evidence. Personas challenge assumptions before you commit.

### Brainstorming

> "brainstorm this", "I need ideas", "explore options"

Elanchezian runs a structured 4-phase ideation process:
1. **Expand** — wide divergence, 25+ ideas, no filter
2. **Patterns** — cluster by theme, surface surprising connections
3. **Develop** — deepen top candidates with pressure testing
4. **Action** — turn developed ideas into next steps

### Spec / Notes

> "give me notes", "summarize the meeting", "action items", "create a spec"

Elango synthesizes everything discussed into structured output — decisions, open questions, action items.

### Wrap-Up

> "wrap up", "save and pause", "good for now", "let's stop here"

Summarizes decisions, persists full state, and tells you how to resume next time.

## Resuming a Huddle

If you've already huddled today on the same repo and branch, Huddle auto-resumes. Just say:

- "resume the huddle"
- "continue our discussion"
- "what did we decide"

It restores context, active personas, and surfaces any new repo activity since the last round.

## The Personas

Huddle selects from 20 specialized personas. Each has a distinct domain, communication style, and blind spots. Here are the key players grouped by area:

### Technical

| Name | Role | Core Question |
|------|------|---------------|
| **Suren** | Architect | "What system shape serves this if it grows — and if it doesn't?" |
| **Shaama** | Backend | "What does this cost to build, run, debug, and roll back?" |
| **Luca** | Frontend | "How does this behave in the browser when users touch it?" |
| **Senthil** | Security | "Who controls that input? What's the blast radius?" |

### Product & Strategy

| Name | Role | Core Question |
|------|------|---------------|
| **Prabagar** | PM | "Who is this for, what outcome matters?" |
| **Maya** | Strategy | "What problem matters most a year from now?" |
| **Babu** | Demand Reality | "Name the actual human. What are they doing today instead?" |
| **Dileep** | Founder Visionary | "Does this win, or just improve?" |

### Quality & Data

| Name | Role | Core Question |
|------|------|---------------|
| **Nina** | Tester | "That's the happy path. What's the angry path?" |
| **Deva** | Test Architect | "Where does this belong in the test pyramid?" |
| **Wei** | Data Analyst | "What's the denominator? Is that a trend or noise?" |

### Design & Communication

| Name | Role | Core Question |
|------|------|---------------|
| **Suna** | Design | "What job is the user trying to do?" |
| **Deepak** | Tech Writer | "Who needs to understand this later?" |
| **Sofia** | Presentation | "What does the audience need by slide three?" |
| **Kishore** | Storyteller | "What's the story people will retell?" |

### Research & Ideation

| Name | Role | Core Question |
|------|------|---------------|
| **Amara** | Trend Researcher | "What's actually happening right now? Which sources agree?" |
| **Vidya** | Analyst | "What does the evidence say once we separate assumptions?" |
| **Elanchezian** | Brainstorming | "What haven't we thought of yet?" |

### Background

| Name | Role | Core Question |
|------|------|---------------|
| **Elango** | Spec Architect | "What was actually decided, and what remains open?" |
| **Srey** | Solo Dev | "What ships first? Cut it and prove the core." |

Huddle picks 2 personas per round by default. It suggests a third only when that addition materially sharpens the outcome. You can always ask for a specific persona by name.

## When to Use Huddle

Huddle is most valuable when you need structured thinking, not just answers.

**Architecture decisions** — You're choosing between approaches and want to surface tradeoffs you haven't considered. Suren and Shaama help you think about system shape, operational cost, and failure modes.

**Feature scoping** — You have a feature idea but need to figure out what to build first. Prabagar, Srey, and Babu help cut scope to what matters.

**Security review** — You're building auth flows, handling user input, or touching trust boundaries. Senthil pressure-tests your assumptions.

**Pre-launch verification** — Before shipping, you want to verify completeness and surface blind spots. Nina and Deva challenge your test coverage and rollback plan.

**Stuck on a problem** — You've been going back and forth and need fresh perspectives to break the deadlock.

**Research before committing** — You want to know what the ecosystem looks like before picking a library, pattern, or approach. Amara scans current sources.

**Writing specs or docs** — After a productive discussion, Elango synthesizes decisions, open questions, and action items into structured output.

**Brainstorming** — You need to explore a wide solution space before narrowing down. Elanchezian facilitates structured ideation.

## How Domains Can Use Huddle

Huddle adapts to the domain of the problem. Here's how different teams and disciplines can get value from it.

### Backend / API Development

Start a huddle when designing APIs, data models, or service boundaries. Shaama focuses on operational cost and rollback safety. Suren thinks about system shape at scale. Senthil checks trust boundaries and auth flows.

> "huddle up — we need to design the payment webhook handler"

Useful for: API contract design, database schema decisions, service decomposition, migration planning, caching strategy.

### Frontend / UI

Huddle helps with component architecture, state management, and UX tradeoffs. Luca focuses on browser behavior and client performance. Suna thinks about user jobs and interaction flows.

> "what does the team think about this form wizard approach"

Useful for: component structure, accessibility review, client state strategy, responsive design tradeoffs, performance budgets.

### Product & Growth

When you're deciding what to build, Huddle brings product thinking into the engineering conversation. Prabagar keeps focus on outcomes and metrics. Babu validates demand. Maya thinks long-horizon.

> "help me think through whether we should build this feature or integrate with a third party"

Useful for: build-vs-buy decisions, feature prioritization, MVP scoping, launch criteria, success metrics.

### DevOps / Infrastructure

For infrastructure decisions, Huddle surfaces reliability and operational concerns. Shaama and Suren think about deployment, scaling, and failure modes. Deva considers CI/CD testing strategy.

> "let's discuss the migration to Kubernetes"

Useful for: deployment architecture, CI/CD pipeline design, monitoring strategy, incident response planning, infrastructure cost tradeoffs.

### Security

Huddle can serve as a lightweight threat modeling session. Senthil leads with attack surface analysis. Nina thinks about edge cases and abuse paths.

> "I need the team to review the auth flow for this new endpoint"

Useful for: threat modeling, auth flow review, input validation strategy, data handling policies, compliance requirements.

### Data & Analytics

When building data pipelines or designing experiments, Wei focuses on measurement validity and instrumentation. Vidya separates evidence from assumptions.

> "huddle up about our A/B testing framework"

Useful for: metric definitions, experiment design, dashboard architecture, data pipeline decisions, funnel analysis.

### Documentation & Communication

Deepak helps structure knowledge for future readers. Sofia and Kishore help with executive communication and presentations.

> "I need to write the technical spec for this project — let's discuss what should go in it"

Useful for: technical specs, architecture decision records, onboarding guides, executive briefings, demo narratives.

### Open Source / Community Projects

Huddle works well for open source maintainers thinking through API design, contribution guidelines, or release strategy. The small-room format keeps discussion focused.

> "what should our v2 API look like — start a huddle"

Useful for: public API design, breaking change strategy, contributor experience, release planning, ecosystem positioning.

### Startups / Solo Developers

Srey cuts scope ruthlessly. Dileep thinks about leverage and category advantage. Babu validates whether real users want what you're building.

> "I'm a solo dev trying to figure out what to ship first — huddle up"

Useful for: MVP definition, scope cutting, build order, technical debt tradeoffs, when to ship vs. when to polish.

### Research & Exploration

Before committing to a technology or approach, Amara scans current ecosystem signals. Vidya evaluates evidence quality. Maya considers long-term strategic fit.

> "research what's happening with WebAssembly for server-side rendering"

Useful for: technology evaluation, competitive landscape, ecosystem health assessment, trend analysis.

## Non-Git Projects

Huddle works without git. It falls back to local-folder mode, using the folder name as the project identity. Remote/PR features are skipped.

Bootstrap a local identity once:

```bash
python3 scripts/config_helper.py bootstrap <project_root> [repo_name] [branch] [user]
```

After that, Huddle remembers the project across sessions.

## State and Persistence

Huddle saves state under `~/config/.m-agent-skills/`:

```
<repo>/
  <branch>/huddle/
    huddle-state.json       # Synthesized decisions, action items, open questions
    <YYYY-MM-DD>.md         # Daily huddle note
```

- During discussion, no files are written on normal rounds
- Decisions and milestones are appended as raw event files
- Full synthesis happens on explicit ask ("give me notes") or wrap-up
- State persists across sessions — resume any time by saying "resume the huddle"

## Tips

- **Be specific.** "Help me think through the caching layer for our product catalog" gets better results than "let's discuss caching."
- **Ask for specific personas.** If you want security input, say so: "bring in Senthil for this."
- **Use verification mode before shipping.** "Does this hold up?" triggers a pressure test of your current approach.
- **Request notes when you need them.** Say "give me the action items" or "summarize what we decided" to get structured output at any point.
- **Wrap up when you're done.** "Wrap up" saves state cleanly so you can resume later with full context.

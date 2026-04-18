# Step: Sreyash — Init (detect + clarify)

First phase of the Sreyash build sub-task. Handles trigger, environment detection, clarify round, and task manifest creation. On completion, hands off to `step-sreyash-spec.md`.

## Trigger

- `{GIT_USER}` says: "Sreyash build this", "assign this to Sreyash", "hand this to Sreyash", "Sreyash implement this", "Sreyash spec and build"
- **Another persona routes**: any persona can say "this should go to Sreyash" — main loop announces the handoff, asks `{GIT_USER}` to confirm before starting the clarify round.

## Spawn Shape

When triggered and approved, the huddle main loop spawns Sreyash via the Agent tool:

- `subagent_type`: `general-purpose`
- `run_in_background`: `true`
- `description`: `"Sreyash build: {task slug}"`
- `prompt`: the full task briefing + path to the persisted task manifest.

The huddle loop continues while Sreyash works.

## Project Context (loaded from Deepak's output)

Deepak maintains `~/config/muthuishere-agent-skills/{REPO_NAME}/project.md` with tech stack, test strategy + framework, package structure, folder shape, env vars, key commands. Sreyash treats this as his primary context source — no re-scanning what Deepak already captured.

**If `project.md` exists** → read silently, use to pre-fill auto-detection.

**If `project.md` is missing** → announce once:
> "📝 No project doc yet. Deepak can document the project first — that gives me repo conventions, test strategy, and package structure without me having to probe. Want me to hand off to Deepak first, or detect myself?"
- User says Deepak → route to `step-deepak-document.md`, return here after.
- User says "detect yourself" → continue with minimal inline detection; suggest running Deepak later.

## Spec Config (ask once, remember forever)

Config path: `~/config/muthuishere-agent-skills/{REPO_NAME}/specconfig.json`

**Schema (single-package):**
```json
{
  "monorepo": false,
  "storage_root": "docs/specs",
  "spec_style": "flat-md",
  "spec_separator": "-",
  "test_framework": "vitest",
  "language": "typescript"
}
```

**Schema (monorepo):**
```json
{
  "monorepo": true,
  "storage_root": "docs/specs",
  "spec_style": "flat-md",
  "spec_separator": "-",
  "packages": {
    "ui":     { "path": "apps/web",     "language": "typescript", "test_framework": "vitest",   "kind": "web-frontend" },
    "api":    { "path": "apps/api",     "language": "typescript", "test_framework": "vitest",   "kind": "backend-api" },
    "mobile": { "path": "apps/mobile",  "language": "typescript", "test_framework": "jest",     "kind": "mobile-rn" },
    "shared": { "path": "packages/core","language": "typescript", "test_framework": "vitest",   "kind": "shared-lib" }
  }
}
```

**If `specconfig.json` exists** → use it silently, skip detection.
**If missing** → run auto-detection below, write specconfig.json, continue without asking.

## Auto-Detection Policy (silent)

```xml
<auto-detection-policy>
  <rule id="ad-01-never-ask">
    Environment is detected, never asked. Sreyash only pauses on human-judgment items (scope, AC, off-limits).
  </rule>
  <rule id="ad-02-match-existing">
    Always mirror the repo's existing convention exactly. Never convert between spec styles.
  </rule>

  <detection order="1" field="storage_root + spec_style">
    <case condition="openspec/ exists">
      <set storage_root="openspec/specs/" spec_style="openspec" />
      <note>Follow OpenSpec layout: {slug}/spec.md, deltas under openspec/changes/{change-slug}/.</note>
    </case>
    <case condition="docs/specs/ exists AND contains ^\d+[-_].*/ subfolders with spec.md inside">
      <set spec_style="folder-md" />
      <detect field="spec_separator" from="existing-folder-names" />
    </case>
    <case condition="docs/specs/ exists AND contains flat ^\d+[-_].*\.md files at top level">
      <set spec_style="flat-md" />
      <detect field="spec_separator" from="existing-file-names" />
    </case>
    <case condition="docs/specs/ exists but empty or mixed">
      <set spec_style="flat-md" spec_separator="-" />
    </case>
    <default>
      <create path="docs/specs/" />
      <set spec_style="flat-md" spec_separator="-" />
    </default>
  </detection>

  <detection order="2" field="monorepo">
    <case condition="project.md says 'Monorepo'"><set monorepo="true" /></case>
    <case condition="any of: pnpm-workspace.yaml, turbo.json, nx.json, lerna.json, rush.json, go.work, Cargo.toml [workspace], pyproject.toml multi-subproject, root package.json workspaces field, apps/*+packages/* shape">
      <set monorepo="true" />
    </case>
    <default><set monorepo="false" /></default>
  </detection>

  <detection order="3" field="packages" when="monorepo=true">
    <for-each source="workspace manifests or directory scan">
      <detect field="language" from="config files (TS/JS/Python/Go/Rust)" />
      <detect field="test_framework" from="package.json scripts+devDeps | pyproject.toml | go.mod" />
      <detect field="kind">
        <heuristic path-pattern="apps/web|apps/ui">web-frontend</heuristic>
        <heuristic path-pattern="apps/api|services/*">backend-api</heuristic>
        <heuristic path-pattern="apps/mobile">mobile-rn</heuristic>
        <heuristic path-pattern="packages/*|libs/*">shared-lib</heuristic>
      </detect>
    </for-each>
  </detection>

  <detection order="4" field="test_framework" when="monorepo=false">
    <case condition="runner installed in package.json/pyproject.toml/go.mod"><use-existing /></case>
    <default>
      <lookup language="Python">pytest</lookup>
      <lookup language="Node">vitest</lookup>
      <lookup language="Go">go test</lookup>
      <lookup language="Rust">cargo test</lookup>
      <rule>Install the default and log under task manifest's assumptions. Do not ask.</rule>
    </default>
  </detection>

  <finalize>
    <write path="~/config/muthuishere-agent-skills/{REPO_NAME}/specconfig.json" />
  </finalize>

  <failure-mode>
    <rule>Ask ONE targeted question only if detection genuinely fails on a critical field.</rule>
    <example>⚠️ Detected Python + TypeScript + Go in this repo. Which is the target for this task?</example>
  </failure-mode>
</auto-detection-policy>
```

## Clarify Round Policy

```xml
<clarify-round-policy>
  <rule id="cr-01-human-judgment-only">
    Ask only for things requiring human judgment: scope, AC, off-limits. Detect everything else.
  </rule>
  <rule id="cr-02-tdd-default">
    TDD is the default. Tests are written unless user explicitly says "skip tests" / "no tests".
  </rule>
  <rule id="cr-03-one-message">
    One reflection message. No ping-pong confirmation rounds.
  </rule>

  <flavour name="huddle-context" when="task came from huddle with existing decisions">
    <step>Load silently: huddle-state.json, project.md, specconfig.json.</step>
    <step>Auto-compute NNN from storage root; auto-slug from task description.</step>
    <step>Emit ONE reflection message (~5-8 lines): Task / Scope+AC (from huddle) / Detected environment as statements / Slug / "Ready to spawn — say go, or redirect."</step>
    <rule>Ask a targeted gap question ONLY if a critical AC is genuinely missing from the huddle.</rule>
  </flavour>

  <flavour name="fresh-task" when="task not discussed in huddle">
    <step>Load silently: project.md, specconfig.json.</step>
    <step>Emit ONE reflection message with best inference: Task / Scope+AC / Detected environment / Slug / "Ready to spawn — say go, or tell me what's off."</step>
    <rule when="task description is genuinely ambiguous">Ask ONE targeted question (not a checklist).</rule>
  </flavour>

  <monorepo-scope-resolution>
    <rule>Infer target package from task description (file paths, package names, technology).</rule>
    <rule>Ask ONE question only if inference is genuinely ambiguous.</rule>
  </monorepo-scope-resolution>

  <ask-whitelist>
    <allowed>Missing critical AC that can't be inferred.</allowed>
    <allowed>Two equally valid implementation paths, choice is load-bearing.</allowed>
    <allowed>Monorepo target ambiguous AND inference doesn't resolve it.</allowed>
  </ask-whitelist>

  <ask-blacklist>
    <forbidden>Storage location — detect.</forbidden>
    <forbidden>Test framework — detect; TDD default.</forbidden>
    <forbidden>Whether to write tests — yes, unless user opts out.</forbidden>
    <forbidden>Style dimensions — detect from repo + project.md.</forbidden>
    <forbidden>Slug naming — auto-compute.</forbidden>
    <forbidden>Spec numbering — auto-compute from filesystem.</forbidden>
  </ask-blacklist>
</clarify-round-policy>
```

## Task Manifest Creation

On user's "go", Sreyash writes the manifest before spawning the background agent.

**Path**: `~/config/muthuishere-agent-skills/{REPO_NAME}/sreyash/{NNN}{sep}{slug}/task.xml`

Task manifests live skill-private (not in the repo). Repos that use `flat-md` have no folder to host `task.md` anyway; skill-private keeps state consistent and repos clean.

**Format** (XML, deterministic):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<task version="1" status="pending">
  <!-- status: pending | in-progress | completed | blocked -->
  <meta>
    <slug>{NNN}{sep}{slug}</slug>
    <date>{YYYY-MM-DD}</date>
    <handoff-from>{user | persona-id}</handoff-from>
    <spec-style>flat-md</spec-style>      <!-- openspec | folder-md | flat-md -->
    <spec-path>docs/specs/024-ui-api-contract-alignment.md</spec-path>
    <project-context>~/config/muthuishere-agent-skills/{REPO_NAME}/project.md</project-context>
  </meta>

  <description>
    <!-- Verbatim task description from user or huddle. -->
  </description>

  <acceptance-criteria>
    <criterion id="ac-1">...</criterion>
  </acceptance-criteria>

  <scope>
    <packages>
      <package>ui</package>
    </packages>
    <off-limits>
      <path>apps/api/**</path>
    </off-limits>
    <test-frameworks>
      <framework package="ui">vitest</framework>
    </test-frameworks>
  </scope>

  <context>
    <huddle-decisions>
      <decision ref="saas-d1-…">...</decision>
    </huddle-decisions>
    <constraints>
      <constraint>...</constraint>
    </constraints>
  </context>

  <work-units>
    <!-- Filled in during step-sreyash-spec.md after Red phase. -->
  </work-units>

  <artifacts>
    <spec></spec>
    <tests></tests>
    <code></code>
    <assumptions></assumptions>
    <blockers></blockers>
  </artifacts>
</task>
```

## Handoff

When manifest is written and user has said "go", proceed to `step-sreyash-spec.md`.

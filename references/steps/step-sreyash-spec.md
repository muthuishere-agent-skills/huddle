# Step: Sreyash — Spec (scan, write spec, red tests, plan green)

Second phase. Runs inside the background agent spawned by the init phase. Produces the spec, writes failing tests (Red), plans the green-phase work units.

## Scan

Use `project.md` as baseline (tech stack, test framework, package structure, conventions). Only probe the code for what `project.md` doesn't cover:
- Files near the change site.
- Local patterns in that module.
- Direct dependencies of the code you'll touch.

For monorepo cross-package work, note any shared types / API contracts between affected packages. Do not re-enumerate what Deepak already documented.

## Spec File Placement Policy

```xml
<spec-placement-policy>
  <layout style="openspec" spec-path="openspec/specs/{slug}/spec.md" changes="openspec/changes/{change-slug}/" extras="proposal.md, design.md, tasks.md (optional)" />
  <layout style="folder-md" spec-path="{storage_root}/{NNN}{sep}{slug}/spec.md" extras="scoped to folder" />
  <layout style="flat-md" spec-path="{storage_root}/{NNN}{sep}{slug}.md" extras="single file — no folder, no siblings" />

  <numbering>
    <rule>NNN zero-padded to match existing files (usually 3 digits; widen only if existing files use 4+).</rule>
    <rule>Scan storage root for highest existing NNN, increment.</rule>
    <rule when="existing files lack numeric prefix (e.g., auth.md, payments.md)">Skip NNN entirely. Use pure slug.</rule>
  </numbering>
</spec-placement-policy>
```

## Spec Write (OpenSpec style)

Write spec to the path determined by `spec_style` in `specconfig.json`:

- `## Purpose` — what changes, anchored to real modules (cite paths).
- (monorepo only) `## Packages Affected` — list with per-package rationale.
- `## Requirements` — each `### Requirement:` block contains SHALL or MUST, cites actual repo paths.
- `#### Scenario:` blocks in GIVEN/WHEN/THEN format, each executable as a test.
- For modifications: use `## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements` delta sections.

Update task manifest `<artifacts>/<spec>` with the resolved spec path.

## Style Inference Policy

```xml
<style-inference-policy>
  <rule>Detect and apply from the repo and project.md. Never ask as a checklist.</rule>

  <dimension name="error-handling" source="existing services" match="exceptions | Result | error-codes" />
  <dimension name="validation-boundary" source="existing controllers/services/schemas" match="whichever pattern dominates" />
  <dimension name="async-style" source="existing code" match="async-await | callbacks | generators" />
  <dimension name="logging" source="sibling files" match="whichever logger is already imported" />
  <dimension name="naming" source="sibling files" match="existing casing + prefix conventions (e.g., use* hooks, is* booleans)" />
  <dimension name="file-layout" source="surrounding code" match="co-located vs separate — whatever exists" />
  <dimension name="mocking-style">
    <case when-package-kind="web-frontend">invoke-and-validate (Luca's rule)</case>
    <case when-package-kind="backend-api">spin-up-and-assert via testcontainers/docker-compose (Nina's rule)</case>
    <case when-package-kind="shared-lib">pure-function unit tests</case>
    <case when-package-kind="mobile-rn">component testing with platform mocks</case>
  </dimension>
  <dimension name="dependencies" source="package.json | requirements.txt | go.mod" rule="prefer existing; avoid adding new unless task requires" />

  <fallback>
    <rule>If a dimension can't be inferred, make the pragmatic choice and log it under task manifest &lt;artifacts&gt;/&lt;assumptions&gt;. Do not ask.</rule>
  </fallback>
</style-inference-policy>
```

## Red Phase

For each scenario in the spec, write a failing test in the target package's test framework.

- Run tests. Confirm they fail for the expected reason.
- If a test fails for the wrong reason, fix the test before continuing.
- Red phase stays **serial** in the primary agent — the spec is the plan; don't fork the plan.

Update task manifest `<artifacts>/<tests>` with the red test paths.

## Plan Green — identify independent work units

After the spec + red tests are on disk, Sreyash groups the Requirements into work units:

```xml
<plan-green-policy>
  <rule>Each &lt;### Requirement&gt; block is a candidate unit.</rule>
  <rule>Units are INDEPENDENT if they touch disjoint file sets (test files produced + likely implementation files).</rule>
  <rule>Units that overlap on files COLLAPSE into one unit.</rule>
  <rule when="monorepo">Requirements scoped to different packages are almost always independent.</rule>
  <rule>Write the unit plan to the task manifest's &lt;work-units&gt; block before spawning anything.</rule>
</plan-green-policy>
```

**Unit entry in manifest:**
```xml
<unit id="u1" requirement="r1" status="pending" builder="" builder-agent-id="" spawned-at="" soft-deadline="" hard-deadline="" last-heartbeat="">
  <files>
    <file>apps/ui/src/lib/api.ts</file>
  </files>
  <tests>
    <test>apps/ui/src/lib/api.test.ts</test>
  </tests>
  <progress>
    <tests-green>0</tests-green>
    <tests-red>3</tests-red>
    <files-written></files-written>
    <note></note>
  </progress>
  <events>
    <!-- Audit log. Sreyash appends kill/respawn/extend actions. -->
  </events>
</unit>
```

## Handoff

With work units planned in the manifest, proceed to `step-sreyash-process.md`.

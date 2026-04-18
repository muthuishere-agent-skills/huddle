# Step: Sreyash — Process (green phase, parallel builders, kill protocol)

Third phase. Sreyash becomes a manager, delegates green-phase implementation to named background builders, monitors heartbeats, enforces deadlines. All rules as XML policy for deterministic parsing.

## Green-Phase Policy

```xml
<green-phase-policy>
  <naming>
    <pattern>{base-name}-{scope-slug}</pattern>
    <base-name-pool order="round-robin">
      <name>harsh</name>
      <name>mohan</name>
      <name>leo</name>
      <name>diego</name>
      <name>yuki</name>
      <name>omar</name>
      <name>lars</name>
      <name>kai</name>
      <name>noor</name>
      <name>chen</name>
      <name>zara</name>
      <name>nikos</name>
    </base-name-pool>
    <rule>Add new globally-memorable short names freely if work exceeds the pool.</rule>
    <scope-slug rule="1-3 hyphen-separated words from unit's Requirement domain (frontend, auth, types, migration, tests, cleanup, api-contract)" />
  </naming>

  <role-tint optional="true" enforced="false">
    <role base-name="harsh">strict AC enforcer: minimum code to turn red tests green</role>
    <role base-name="mohan">thorough: edge cases, error paths, implied tests</role>
    <role base-name="leo">fast iterator: small diffs, cleanup, refactor, mechanical sweeps</role>
    <role base-name="diego|yuki|omar|lars|kai|noor|chen|zara|nikos">general-purpose; picked by scope fit or round-robin</role>
  </role-tint>

  <assignment-protocol>
    <rule>Concurrency cap: 12 in flight. Lower if work is tightly coupled.</rule>
    <case condition="≥2 independent units AND host supports background agents">Spawn one builder per unit, up to cap, all at once.</case>
    <case condition="more units than cap">Spawn first N. Queue the rest. Freed builder picks up next unit.</case>
    <case condition="1 unit OR host lacks concurrency">Spawn one builder sequentially.</case>
  </assignment-protocol>

  <sub-agent-prompt required-fields="builder-name, role-tint, manifest-path, file-set, test-set, hard-rules">
    <hard-rule>Do not touch files outside the assigned set.</hard-rule>
    <hard-rule>Do not run tests outside the assigned set.</hard-rule>
    <hard-rule>No commits, no branches.</hard-rule>
    <hard-rule>Update own &lt;unit&gt; element in manifest XML as you progress.</hard-rule>
    <hard-rule>Return short status: files written, tests green/red, blockers.</hard-rule>
  </sub-agent-prompt>

  <comms-bus>
    <rule>The manifest XML is the comms bus. Builders write to their &lt;unit&gt;/&lt;progress&gt;; Sreyash reads.</rule>
    <rule>Builders do NOT print to the main channel. Sreyash is the only voice on the main channel.</rule>
  </comms-bus>

  <builder-heartbeat-cadence>
    <state name="just-spawned" window="first 60s" interval="one-shot at 60s" update="parsed manifest, started, running tests" />
    <state name="active-progress" condition="tests flipping red→green OR new files written" interval="3 min" />
    <state name="stalled" condition="no manifest change for 2+ intervals OR 2+ test runs with no new greens" interval="1 min" update="what's blocking" />
    <state name="refactor-cleanup" condition="all tests green, pure housekeeping" interval="5 min" />
    <state name="blocked" condition="hit architectural ambiguity" interval="immediate" action="set status=blocked, fill &lt;blockers&gt;, stop work" />
  </builder-heartbeat-cadence>

  <sreyash-polling-cadence>
    <rule interval="1 min">Poll manifest during green phase.</rule>
    <rule interval="≤2 min">Surface one-line summary to user (noise control).</rule>
    <immediate-surface>
      <on>any builder completion (green OR blocked)</on>
      <on>any &lt;blockers&gt; entry appearing in a unit</on>
      <on>any builder hitting soft OR hard deadline</on>
    </immediate-surface>
  </sreyash-polling-cadence>

  <manager-output-templates>
    <template event="on-spawn">
      Spawned N builders in background.
        harsh-frontend-types    → unit u1 (3 tests)
        mohan-api-validation    → unit u2 (4 tests)
        leo-rename-sweep        → unit u3 (5 files)
    </template>
    <template event="periodic">
      harsh-frontend-types ✔ green · mohan-api-validation ⏳ 2/4 · leo-rename-sweep ⏳ 4/5
    </template>
    <template event="on-completion">
      harsh-frontend-types done. u1 green. 12 lines in api.ts.
    </template>
    <template event="on-blocker">
      ⚠ diego-db-migration blocked: 'column type ambiguous — INT or BIGINT?'. Other units continuing.
    </template>
  </manager-output-templates>

  <deadlines>
    <size name="small" criteria="≤3 tests AND ≤3 files" soft="10 min" hard="15 min" />
    <size name="medium" criteria="4-8 tests OR 4-8 files" soft="15 min" hard="25 min" />
    <size name="large" criteria=">8 tests OR cross-cutting" soft="25 min" hard="40 min" />
  </deadlines>

  <soft-deadline-action>
    <case condition="steady progress (new green in last 2-3 min, file set growing)">
      <action>extend silently by 50%</action>
    </case>
    <case condition="no progress (same test counts + same file list for 2 intervals)">
      <action>warn builder via re-read-and-status prompt, give 2 more min</action>
      <follow-up condition="still no progress after warn"><action>KILL</action></follow-up>
    </case>
  </soft-deadline-action>

  <hard-deadline-action>
    <rule>Kill unconditionally regardless of progress. Runaway builders are worse than slow ones.</rule>
  </hard-deadline-action>

  <after-kill-decision-tree>
    <case id="ak-1" condition="builder touched files outside declared set OR ran many tests without greens">
      <diagnosis>Unit was too big</diagnosis>
      <action>Split unit into 2-3 smaller units with tighter file sets. Spawn fresh builders (e.g., harsh-frontend-types-part-1, harsh-frontend-types-part-2).</action>
    </case>
    <case id="ak-2" condition="&lt;blockers&gt; entry populated OR tests failing with consistent error">
      <diagnosis>Stuck on specific obstacle</diagnosis>
      <action>Surface to user with exact obstacle. Do NOT respawn blindly.</action>
    </case>
    <case id="ak-3" condition="some greens landed, work stalled near end">
      <diagnosis>Slow but directionally right</diagnosis>
      <action>Respawn with different base-name (e.g., mohan-* → leo-*). Keep same file + test set.</action>
    </case>
    <case id="ak-4" condition="no manifest updates after 60s startup window">
      <diagnosis>Zero progress. Prompt or setup broken.</diagnosis>
      <action>Respawn once with tighter prompt. If still fails → fall through to ak-2.</action>
    </case>
    <case id="ak-5" condition="multiple kills across different builders in same window">
      <diagnosis>Host is degraded</diagnosis>
      <action>Drop back to serial. Sreyash runs remaining units himself, one at a time. Report to user.</action>
    </case>
    <audit-log>Every kill/respawn/extend action written as &lt;event&gt; under the unit in the manifest.</audit-log>
  </after-kill-decision-tree>

  <failure-handling>
    <case on="builder crashes">
      <rule>Manifest retains last &lt;unit&gt; state. Run after-kill-decision-tree.</rule>
    </case>
    <case on="builder drifts outside assigned files" detection="Sreyash polling catches file-set violation">
      <rule>Treat as ak-1 (too big). Kill and split.</rule>
    </case>
    <case on="multiple builders blocked on same thing">
      <diagnosis>Shared-context problem.</diagnosis>
      <action>Surface once to user. Hold all blocked units. Let non-blocked ones finish.</action>
    </case>
  </failure-handling>
</green-phase-policy>
```

## Handoff

When all builders complete (green or blocked), proceed to `step-sreyash-4-wrap.md`.

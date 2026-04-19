# Hacker News post

## Option A — Show HN

**Title:**

Show HN: Huddle – multi-persona agent skill for pre-mortem discussions

**Body:**

Been building this for months.

The pattern: LLMs compress the first 90% of a build. The last 10% — edge cases, assumptions, real usage — is exactly as hard as it was. So I built an agent skill. 21 agents. They ask the questions you'd otherwise discover in production, run TDD when you hand off the build, and handle infra from a single VPS to a K8s cluster.

Cargill's 1985 line ("the first 90% takes the first 90% of the time; the last 10% takes the other 90%") feels sharper now than it did a year ago, because the first 90% has collapsed and the second 90% hasn't.

Each persona has a lens — a backend engineer focused on failure modes, a security mind on blast radius, a PM on value metrics, an architect on capacity math. They disagree. They stop and wait. You decide.

Stdlib Python and markdown skill files under the hood. No cloud, no lock-in. Works as an agent skill on Claude Code, Codex, Gemini CLI, and anything else that supports the standard skill path. State lives under `~/config/muthuishere-agent-skills/`, never in your repo unless you put it there. Works without git too.

Install: `npx skills add muthuishere-agent-skills/huddle`

Repo: https://github.com/muthuishere-agent-skills/huddle

Happy to take critique — especially on where this is wrong, or where it overlaps with something that already exists.

---

## Option B — Article submission (link post)

**Title:**

The 80% problem — and what LLMs actually changed

**URL:** https://github.com/muthuishere-agent-skills/huddle/blob/main/marketing/the-80-percent-problem.md
*(or wherever the article is hosted)*

*No body — HN link posts don't take one. First comment from the author should disclose Huddle affiliation in one flat sentence.*

**Suggested first comment (author disclosure):**

Author here. Disclosure: the post ends by pitching Huddle, which I've been building for months. The thesis — that LLMs moved the bottleneck from "can we build this?" to "did we think about this deeply enough?" — stands without the pitch. Curious whether others are seeing the same shift, or whether this is overstated.

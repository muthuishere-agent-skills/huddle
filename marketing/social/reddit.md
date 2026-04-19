# Reddit post

Suggested subreddits: r/ExperiencedDevs, r/programming, r/ClaudeAI

## Title options

- LLMs compressed the first 90% of software dev. The second 90% is exactly as hard as it was.
- The last 20% of software still takes 80% of the time — and LLMs made the gap more obvious
- We got faster answers but not better questions — and it's where our systems keep breaking

## Body

Been thinking about a pattern every experienced engineer has seen, and LLMs have sharpened it rather than solved it.

Tom Cargill at Bell Labs put it best in 1985:

> "The first 90% of the code takes the first 90% of the time. The remaining 10% takes the other 90%."

(Reproduced in Jon Bentley's *Programming Pearls* column in CACM — it's aged better than most of our tooling.)

Phase 1 is fast and visible: APIs come together, the flow works, the demo is great. Phase 2 is slow and invisible: edge cases, real usage, the assumption nobody wrote down. Production is where you find out.

LLMs have collapsed phase 1. What took two weeks takes two days. What took two days takes two hours.

Phase 2 is untouched — because it was never really about writing code. It's about uncovering what you didn't think to ask. A webhook handler is fifty lines. Knowing Stripe retries with a new idempotency key after 24 hours is the part you don't get unprompted.

So the bottleneck has moved. It used to be *"can we build this?"* and almost any small team can now stand up most anything in a week. The new bottleneck is *"did we think about this deeply enough?"* — and that's much harder to answer with any tool.

The questions that save systems are uncomfortable and usually come from people with scars: the backend engineer who's been paged at 2am, the security person who sees blast radius, the PM who knows what a support ticket actually costs. Most of them aren't in the room when the code gets written. By the time they are, it's in production.

There's another thing most teams underestimate. A decision gets made, then it moves — developer to developer, dev to manager, CTO to CEO. Each retelling strips something. The tradeoff. The edge case. The assumption nobody wrote down. The wrong thing starts sounding right. Good systems don't only fail because of bad code; they fail because the thinking didn't survive translation.

---

**Disclosure:** Been building this for months. It's an agent skill — 21 agents who ask the questions you'd otherwise discover in production, TDD the build, and handle infra from VPS to K8s. Repo: https://github.com/muthuishere-agent-skills/huddle. Install: `npx skills add muthuishere-agent-skills/huddle`. The thesis stands either way — LLMs haven't changed where the hard part of software is, and the team that asks sharper questions ships the better system.

Curious what other people have seen — are you finding LLMs make the hard parts feel harder by comparison, or easier because they help you explore faster?

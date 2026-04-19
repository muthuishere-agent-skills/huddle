# LinkedIn post

Answers got cheap this year. Questions stayed scarce.

Every engineer who's shipped a real system has seen the 80% problem. APIs come together. The demo works. The system feels almost done.

Then the second half begins — and in 1985, Tom Cargill at Bell Labs already had a name for it:

*"The first 90% of the code takes the first 90% of the time. The remaining 10% takes the other 90%."*

LLMs compressed that first 90%. An afternoon of prompting now produces what used to take a two-week sprint.

The second 90% is untouched. Edge cases, hidden assumptions, the thing nobody asked about — that's still the work.

The bottleneck used to be *"can we build this?"*
Now it's *"did we think about this deeply enough?"*

There's another layer most teams underestimate.

A decision gets made — and then it moves. A developer explains it to another developer. Then to a manager. The CTO explains it to the CEO. Each retelling strips something — the tradeoff, the edge case, the assumption nobody wrote down. The wrong thing starts sounding right.

LLMs give a clean answer. But it's framed in one voice. And one voice rarely survives every room it enters.

So I built an agent skill.

Been building this for months. LLMs get you to 80% done in an afternoon. The last 20% — edge cases, hidden assumptions, real usage — still eats weeks. So I built an agent skill. 21 agents who ask the questions you'd otherwise discover in production, TDD the build, and handle infra from VPS to K8s.

`npx skills add muthuishere-agent-skills/huddle`

Good systems don't only fail because of bad code. They fail because the thinking didn't survive translation.

#SoftwareEngineering #LLM #DeveloperTools #AgentSkills

# X / Twitter thread

**1/**
Answers got cheap this year.

Questions stayed valuable.

---

**2/**
In 1985, Tom Cargill at Bell Labs said:

"The first 90% of the code takes the first 90% of the time. The remaining 10% takes the other 90%."

LLMs compressed the first 90%.

The second 90% is exactly as hard as it was.

---

**3/**
The last 20% was never about writing code.

It's about:
• hidden assumptions
• failure paths
• real usage
• decisions under pressure

Things no LLM surfaces unprompted.

---

**4/**
Old bottleneck: *can we build this?*

New bottleneck: *did we think about this deeply enough?*

Much harder to answer. And it's the question that decides whether the thing you shipped survives.

---

**5/**
The questions that save systems are the uncomfortable ones:

• What happens when this fails in prod?
• Who controls this input?
• What assumption are we making here?
• Is this solving the real problem — or a version of it?

---

**6/**
They come from people who've watched systems break.

A backend engineer with on-call scars. A security mind. A PM who names the metric. An architect who does the capacity math.

Most aren't in the room when the code gets written.

---

**7/**
And decisions don't stay in one room.

A developer explains it to another developer. Then to a manager. The CTO to the CEO.

Each retelling strips something — the tradeoff, the edge case, the assumption nobody wrote down.

---

**8/**
That's why I built an agent skill.

21 agents → ask the right questions, TDD the build, run infra from VPS to K8s.

Grounded in your repo. They disagree. They stop and wait. You decide.

`npx skills add muthuishere-agent-skills/huddle`

---

**9/**
Good systems don't only fail because of bad code.

They fail because the thinking didn't survive translation.

---

## Single-tweet version

80% done feels great. The last 20% is where systems break. LLMs didn't change that — they just got you there faster.

So I built an agent skill: 21 agents → right questions, TDD, infra from VPS to K8s.

`npx skills add muthuishere-agent-skills/huddle`

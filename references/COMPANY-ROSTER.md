# Company Roster — the complete huddle cast (35 personas)

The huddle's persona registry now covers **the full company**: the 22 reusable archetypes
(strategy, build, design, security, …) **plus** the 13 company-os-live operating personas
(the real fleet roles). Single source of truth: `persona-roster.xml` + `personas/*.md`.
Validate with `bash references/verify-personas.sh`.

## Company-OS live personas (added #3522, 2026-06-15)

| Persona | Title | Real fleet role | File |
|---|---|---|---|
| 📈 Dhana | Crypto Trading Desk | 24/7 crypto perps, small bracketed book | `personas/dhana-cryptodesk.md` |
| ♟️ Kuber | Equities Strategy Desk | NSE strategy-tournament (Veera/Surya/Meena/Indra lanes) | `personas/kuber-equitiesstrategy.md` |
| 🎯 Thiru | NSE Intraday + Multi-Day Desk | two-book equities desk, the 30-min protocol | `personas/thiru-intradaydesk.md` |
| 🛠️ Jana | Company-OS Builder | the event-sourced nervous system | `personas/jana-companyos.md` |
| 🎓 Anitha | Interview-Prep Product Lead | the interview-prep product | `personas/anitha-interviewprep.md` |
| 🧰 Gnanavel | Commons / Shared-Dev | commons OSS dev tools (no business target) | `personas/gnanavel-commonsdev.md` |
| 📣 Vinish | Reqsume Growth Lead | reqsume distribution + growth | `personas/vinish-reqsumegrowth.md` |
| 🔗 Vignesh | Skill Supply-Chain Auditor | agent-skill capability audit | `personas/vignesh-skillsupplychain.md` |
| 🧭 Venugopal | Research Lead | directs the research engine | `personas/venugopal-researchlead.md` |
| 🔭 Parthasarathy | Open Researcher | broad niche discovery | `personas/parthasarathy-researcher.md` |
| 🧬 Ramesh | Humini / Niche-Domain Research | deep real-world domain research | `personas/ramesh-nicheresearch.md` |
| ✍️ Jency | Build-in-Public / Social | shipped-work drafts, owner-gated publish | `personas/jency-buildinpublic.md` |
| 🛡️ Nirmal | Spend-Guard Lead | cost guardrails, validate-not-block | `personas/nirmal-spendguard.md` |

## Alias dedup (from `company.db` persona_alias) — no duplicates created

Some live names already map to existing archetypes and were **NOT** re-authored:

| Live name | Old alias | Maps to existing archetype |
|---|---|---|
| Peter | Maya | `personas/maya-strategist.md` (Strategy) |
| Dileep | CEO | `personas/dileep-visionary.md` (Founder Visionary) |

These live names **replace** their old aliases on the files added above:

| Live name | Old alias |
|---|---|
| Venugopal | Saras |
| Jana | Ananth |
| Vinish | Saravanan |
| Vignesh | Kavya |

## Already-covered live personas (archetype files existed)

Babu, Hari, Kishore, Nina, Prabagar, Senthil, Shaama, Sreyash, Suren, Wei — plus Peter
(=Maya) and Dileep (=CEO) above — already had archetype files and were left untouched.

## Note: Gnanavel's role

The live `company.db` lists Gnanavel as "Tester / QA", but his real fleet role (per Muthu's
#3522 brief and `ceo/missions/2026-06-12-gnanavel-commonsdev.txt`) is the **commons /
shared-dev** entrepreneur-programmer. The persona reflects the real role; the DB label is stale.

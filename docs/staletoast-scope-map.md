# Collaborative intelligence scope map

Effective 2026-11-27. Generated from [the machine-readable map](staletoast-scope-map.json) by `python site/build_scope_map.py`. Edit the JSON, not this file.

The named components of collaborative intelligence that StaleToast searches and compares sources against. Claims (CI-###) remain the unit of evidence and the named gap of a round; a component says which part of a collaborative system a source is about.

**Authority:** evidence-only; a component names what to look for. It is not a finding, a grade, a chart position or an adoption decision.

**Owner instruction, 2026-11-27:** Expand the search scope with the missing aspects as additional categories and components of collaborative intelligence.

## Status

- `established`: Compared against retained sources in the baseline artifact. Its screen terms and comparison question are copied from that artifact and must not drift from it.
- `added-unscreened`: Added to scope. Its search terms and queries are proposals that have not been run. It holds no screened source, routing count or finding.

## Rules

1. A daily or monthly round records one component id alongside its named gap. The claim-based gap order in the appraisal priorities is unchanged.
2. For an added-unscreened component, screen the existing retained pool against its screen terms before any new discovery. New discovery follows only where that screen leaves the component thin.
3. Queries listed under an added-unscreened component are proposals. Record the queries actually run, their dates and their counts in the dated batch artifact, as for any other round.
4. A component moves to established only when a dated routing artifact compares retained sources against it. Update baseline_artifact in the same change.
5. Adding a component changes no catalog record, appraisal, chart position, export or daily limit.
6. Keep every component public and generic. A component describes a mechanism, never a private system.

## Components

| Component | Status | Since | What it covers | Comparison question |
|---|---|---|---|---|
| `authority-and-handoff` | established | 2026-11-01 | Who may act, on what, under whose approval, and how that passes intact from one person or agent to the next. | Does the source add a check at a boundary our control record only describes? |
| `memory-and-correction` | established | 2026-11-01 | What a system keeps between sessions, how it retrieves it, and how a corrected or superseded fact stops being used. | Does the source improve retrieval or update behavior without losing source versions, correction survival or access boundaries? |
| `recovery-and-replay` | established | 2026-11-01 | How interrupted, failed or duplicated work is detected, attributed and resumed without repeating its effects. | Does this provide a better failure drill or attribution method than our current evidence replay? |
| `evaluation-and-evidence` | established | 2026-11-01 | How a result is checked against a baseline, and what evidence supports calling it done. | Does it supply executable checks or better measurement that the existing method leaves to an adopter? |
| `provenance-and-data-diff` | established | 2026-11-01 | Where a result came from, which source version it used, and exactly what changed between two versions. | Does it expose a source-to-result or row-level change that hashes and counts alone miss? |
| `cost-and-coordination-burden` | established | 2026-11-01 | Tokens, time, rework and human attention spent, including the overhead that coordination itself adds. | Can it reduce observed work or inspection cost without trading away correctness or authority? |
| `cross-harness-tracing` | established | 2026-11-01 | Following one piece of work across different tools and agents with a record each of them can read. | Does it normalize useful evidence across tools without overcollecting private content or equating traces with authenticated completion? |
| `security-and-containment` | added-unscreened | 2026-11-27 | Limits on what an agent can read, run and change, and tests that those limits hold when the agent meets hostile or misleading content. | Does the source give a repeatable test that a stated limit holds under hostile or misleading input, rather than a description of the limit? |
| `deliberation-and-dissent` | added-unscreened | 2026-11-27 | Structured disagreement between agents, or between people and agents: independent first answers, bounded rounds, how a minority view is kept, and whether a second view changed the result. | Does the source measure whether a second independent view changed the outcome, against a single-agent baseline at comparable cost? |
| `learning-from-operation` | added-unscreened | 2026-11-27 | How a system changes its own rules, checks or prompts from its recorded failures and corrections, and how it shows that the change reduced repeats. | Does the source show a recorded failure becoming an enforced check with a measured drop in repeats, rather than a longer instruction file? |
| `orchestration-and-automation` | added-unscreened | 2026-11-27 | Deciding which agent, model or tool does which part of a task and in what order, and running that on a schedule or trigger without a person starting each step. | Does the source show that its routing or scheduling rule beats a fixed single-agent assignment on the same task, with the rule open to inspection and its cost reported? |

## Where a scope term goes

| Term | Components |
|---|---|
| memory | `memory-and-correction` |
| learning | `learning-from-operation` |
| execution | `recovery-and-replay`, `security-and-containment` |
| coordination | `authority-and-handoff`, `cross-harness-tracing` |
| orchestration | `orchestration-and-automation` |
| automation | `orchestration-and-automation` |
| collaboration | `authority-and-handoff`, `deliberation-and-dissent` |
| evaluation | `evaluation-and-evidence` |
| security | `security-and-containment` |
| efficiency | `cost-and-coordination-burden` |
| token utilization | `cost-and-coordination-burden` |
| deliberation | `deliberation-and-dissent` |

## Added components

Nothing below has been run. Terms and queries are proposals for the first screen.

### Security and containment (`security-and-containment`)

**Boundary:** Defensive containment and its tests only. A source that emphasizes offensive technique, evasion, bypass or unverified access claims stays held for the separate scope and misuse-boundary appraisal recorded in the 2026-11-01 expansion. This component does not release a held source.

**Prior coverage:** The 2026-11-01 expansion searched the research topic agent-safety and the repository category agent-security. No component compared those sources to a containment baseline.

**Screen terms:** `prompt injection`, `sandbox`, `least privilege`, `permission boundar`, `tool poisoning`, `exfiltrat`, `guardrail`, `threat model`, `jailbreak`

**Related claims:** CI-007, CI-010. A pointer to claims a component is likely to inform. It is not an evidence link and adds no support to any claim.

**Proposed research topics:**

- `agent-prompt-injection`: all of language, model, agent, prompt, injection
- `agent-sandboxing`: all of language, model, agent, sandbox
- `agent-tool-permissions`: all of language, model, agent, tool, permission

**Proposed repository queries:**

- `agent-containment`: `topic:prompt-injection fork:false archived:false stars:>=5`
- `agent-containment`: `topic:llm-security fork:false archived:false stars:>=5`
- `agent-containment`: `agent sandbox in:name,description fork:false archived:false stars:>=5`

### Deliberation and dissent (`deliberation-and-dissent`)

**Boundary:** Agreement between agents is not verification. A source that reports only that agents converged does not answer the comparison question.

**Prior coverage:** The 2026-11-01 expansion searched the research topic multi-agent-systems. The terms multi-agent and coordination were screened under cross-harness-tracing, which asks about shared records, not about whether disagreement improved a result.

**Screen terms:** `debate`, `deliberat`, `dissent`, `consensus`, `disagree`, `adjudicat`, `second opinion`, `red team`, `ensemble`

**Related claims:** CI-001, CI-015, CI-016, CI-017. A pointer to claims a component is likely to inform. It is not an evidence link and adds no support to any claim.

**Proposed research topics:**

- `multi-agent-debate`: all of language, model, multi, agent, debate
- `agent-disagreement`: all of language, model, agent, disagreement
- `human-ai-deliberation`: all of human, AI, deliberation

**Proposed repository queries:**

- `agent-deliberation`: `topic:multi-agent-debate fork:false archived:false stars:>=5`
- `agent-deliberation`: `agent debate in:name,description fork:false archived:false stars:>=5`

### Learning from operation (`learning-from-operation`)

**Boundary:** A system revising its own instructions is not independent verification that the revision helped. Model fine-tuning and weight updates are out of scope; this component covers changes to rules, checks, prompts and procedures.

**Prior coverage:** No research topic or repository category searched for it. memory-and-correction covers a corrected fact, not a changed rule or check.

**Screen terms:** `self-improv`, `lesson`, `postmortem`, `retrospective`, `failure taxonomy`, `recurrence`, `continual learning`, `reflection`, `skill library`

**Related claims:** CI-006, CI-008, CI-017. A pointer to claims a component is likely to inform. It is not an evidence link and adds no support to any claim.

**Proposed research topics:**

- `agent-self-improvement`: all of language, model, agent, self, improvement
- `agent-failure-taxonomy`: all of language, model, agent, failure, taxonomy
- `agent-experience-reuse`: all of language, model, agent, experience, reuse

**Proposed repository queries:**

- `agent-learning`: `self-improving agent in:name,description fork:false archived:false stars:>=5`
- `agent-learning`: `agent postmortem in:name,description fork:false archived:false stars:>=5`

### Orchestration and automation (`orchestration-and-automation`)

**Boundary:** More agents are not a general advantage (CI-016). A source that adds a coordinating model without a single-agent comparison does not answer the comparison question.

**Prior coverage:** The 2026-11-01 expansion searched the repository category workflow-runtime. No component asked whether a routing or scheduling rule beat a fixed assignment.

**Screen terms:** `orchestrat`, `routing`, `router`, `scheduler`, `workflow engine`, `planner`, `dispatch`, `trigger`, `delegat`

**Related claims:** CI-004, CI-005, CI-016. A pointer to claims a component is likely to inform. It is not an evidence link and adds no support to any claim.

**Proposed research topics:**

- `agent-orchestration`: all of language, model, agent, orchestration
- `agent-task-routing`: all of language, model, agent, task, routing
- `agent-delegation`: all of language, model, agent, delegation

**Proposed repository queries:**

- `agent-orchestration`: `topic:agent-orchestration fork:false archived:false stars:>=5`
- `agent-orchestration`: `topic:multi-agent-systems fork:false archived:false stars:>=5`

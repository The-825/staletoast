# Sources for the next Hot 100 review

Six research articles and twelve repositories are appraised for review. They are proposals, not new chart entries or adopted software. The rest remain in the pool.

Every one of the 1,083 retained expansion sources has a system-fit routing assessment: 1,042 active sources and 41 previously held sources. Routing is a comparison prompt based on primary text, not a full appraisal or quality score. The shortlist is purposive, not a proven global ranking.

The comparison uses the public Breadcrumbs kit at `dd7252af3a5f6cc73296d315d50ee16f016c5ad7`. It does not claim to validate private agent runtimes. Existing source analysis, rankings and chart editions are preserved.

## What to test first

- **Memory corrections that survive retrieval and compaction** (C-166, C-201, R-626). Synthetic revoked/superseded records cannot authorize work and valid replacements survive bounded compaction.
- **Safe recovery after a lost acknowledgment** (R-1020, R-648, R-673). Known synthetic faults yield one intended effect and explicit uncertainty. C-137 is a separate synthetic attribution smoke test, not evidence of duplicate-effect prevention.
- **Explain every ranking change and acceptance decision** (C-404, C-143, R-900, R-1037, R-1012). Versioned criteria, denominator, complete coverage and affected source IDs explain each fictional change.
- **Readable outputs with evidence behind each statement** (C-403, R-1005). Planted chart/filter/sort/claim errors are caught without rejecting a valid alternative output.
- **Minimal comparable run receipts** (R-631, R-1002, R-1036, R-865). Two fictional harness receipts preserve failures and unknown identity without exporting raw prompts; AgentWatch remains Watch until coverage/egress checks pass.

## Research candidates

| Source | Why it matters | Review recommendation |
| --- | --- | --- |
| [Causal Agent Replay: Counterfactual Attribution for LLM-Agent Failures](https://arxiv.org/abs/2606.08275v1) | Find the decision that changed the outcome | Method worth testing |
| [PROV-AGENT: Unified Provenance for Tracking AI Agent Interactions in Agentic Workflows](https://arxiv.org/abs/2508.02866v3) | Trace a decision back to its sources | Strong practical fit |
| [Revoked but Still Authoritative: An Empirical Study of Revocation Enforcement in Agent-Memory Systems](https://arxiv.org/abs/2609.08258v1) | Stop revoked memory from authorizing work | Strong practical fit |
| [Supersede: Diagnosing and Training the Memory-Update Gap in LLM Agents](https://arxiv.org/abs/2606.27472v1) | Keep the correction when memory is compressed | Diagnostic only, limited evidence |
| [Lexara-RF: Reference-Free Metrics for Evaluating Conversational Visual Analytics Agents](https://arxiv.org/abs/2609.17842v1) | Check that a chart says what the data supports | Strong practical fit |
| [Shortcut Sensitivity in Agent-Safety Evaluations](https://arxiv.org/abs/2610.22243v1) | Test whether good scores survive a fairer comparison | Strong practical fit |

## Repository candidates

| Source | What to borrow or compare | Review recommendation |
| --- | --- | --- |
| [aiming-lab/SimpleMem](https://github.com/aiming-lab/SimpleMem/tree/db80b6a7c591e0ea730a058e9f5fc4eb06572299) | Memory that keeps context useful | Compare before adopting |
| [Asymptote-Labs/agent-beacon](https://github.com/Asymptote-Labs/agent-beacon/tree/e0989909e3169cd82066d051f3aa9642ae2bad1e) | Comparable run receipts across coding tools | Strong practical fit |
| [temporalio/temporal](https://github.com/temporalio/temporal/tree/ed5ad7be640621faad089fcc14c112af6dc699d0) | Retry work without doing it twice | Strong pattern, heavy platform |
| [shepherd-agents/shepherd](https://github.com/shepherd-agents/shepherd/tree/d34d5ca334871dfcb5a3dc76dd78045829fa4e56) | Explain and resume an interrupted agent run | Promising early implementation |
| [cyberark/agentwatch](https://github.com/cyberark/agentwatch/tree/56012207e0b2570c1a9716b6fec72288c3958d48) | See which tools an agent actually contacted | Watch, inspect before any use |
| [DataRecce/recce](https://github.com/DataRecce/recce/tree/1b121299076e6ba794e02eac1557c1932b5fbf52) | Show what changed and what was actually checked | Strong practical fit |
| [mozilla-ai/any-agent](https://github.com/mozilla-ai/any-agent/tree/a469723ac4a0518ab0696d57e09e4dc407c826ec) | Compare agent frameworks with the same task | Useful comparison, dependency gap |
| [NVIDIA/SkillEvaluator](https://github.com/NVIDIA/SkillEvaluator/tree/6d5d57f35c333030368cc4c7533cf68976f5ac7d) | Separate static checks from a real successful run | Strong practical fit |
| [UiPath/coder_eval](https://github.com/UiPath/coder_eval/tree/484c3d5db6434392ba8baa60378f3f900d7d0924) | Test what a coding agent really produced | Strong practical fit |
| [Ta0p1/ResolveLab](https://github.com/Ta0p1/ResolveLab/tree/68e90402f3a42b51cb927967da1f8008697d3e8f) | Recover safely when a tool response is misleading | Strong practical fit |
| [datamllab/A2E](https://github.com/datamllab/A2E/tree/ef86ec507f66a8fd6a2223b351b95444ab701f6b) | Keep task, trace and evaluation connected | Useful design, substantial stack |
| [kling01/RubricLoop](https://github.com/kling01/RubricLoop/tree/782b58af56594d9c49fd1fa6410ddf29e29650c7) | Make every review criterion inspectable | Strong practical fit |

## Detailed appraisals

### Find the decision that changed the outcome

[Causal Agent Replay: Counterfactual Attribution for LLM-Agent Failures](https://arxiv.org/abs/2606.08275v1) | C-137 | Method worth testing

**Evidence inspected.** A structural causal model of a recorded agent run, same-policy resampling, contrastive effects and bounded Monte Carlo Shapley attribution. Two synthetic cases have planted causal structure.

**Reported result.** The paper reports recovery of a pivotal middle step and a two-step interaction with estimated contributions 0.44 and 0.45, versus an analytic total of 0.91. These are synthetic demonstrations, not production incident results.

**Compared with our system.** Governed replay currently selects episodes for offline memory review and rehearses proposals through an adopter-supplied simulator. It neither re-executes an intervened trajectory nor attributes a stochastic outcome distribution to a step. Counterfactual attribution is an additional method, not a demonstrated property of the kit.

**Limits and burden.** Per-case replay and permutation sample counts are not supplied in the main demonstrations. Run-forward effects include downstream stochastic changes. Judge noise, replay cost and environment snapshot fidelity constrain transfer; side-effecting real tools are outside the safe initial experiment. Medium: a synthetic environment snapshot and branch runner; no production tool replay.

**Bounded next check.** Use two fictional three-step workflows with a seeded stochastic mock policy, known pivotal and interacting failures, and a fixed declared K per intervention. Record all branches and use an exact outcome checker. This is a smoke test, not evidence of superiority over trace inspection.

**Done when.** Apply the paper's latest-significant-step point-of-commitment rule rather than largest effect alone. Recover the planted pivotal step and interacting pair, disclose K, seed, intervals and branch cost, and record any localization failure. No real side-effecting tools.

Primary PDF pages: 2, 3, 4, 5. Synthetic counterfactual attribution; no independent production corroboration.

### Trace a decision back to its sources

[PROV-AGENT: Unified Provenance for Tracking AI Agent Interactions in Agentic Workflows](https://arxiv.org/abs/2508.02866v3) | C-143 | Strong practical fit

**Evidence inspected.** W3C PROV extension linking workflow activities, models, prompts, responses, tools and data. One distributed additive-manufacturing example illustrates five lineage queries.

**Reported result.** Queries Q1-Q5 connect an agent decision to inputs, alternatives, prompt/response context, downstream decisions and erroneous-data propagation. The workflow mimics an operational setting; the direct live sensor connection remains under development.

**Compared with our system.** Checkpoint provenance is bounded free text, with structured supersedes/failure/workaround links but no general forward lineage. Q4/Q5 downstream traversal therefore needs new explicit relations. Q3 prompt retrieval is unknown by design unless an owning-system pointer is available. StaleToast source pins and immutable histories are local requirements, not properties established by this paper.

**Limits and burden.** Qualitative workflow demonstration, not a controlled comparison of debugging speed, completeness or causal correctness. A lineage edge shows recorded dependency, not proof of causation. Full prompt capture can expose sensitive content. Low for a relation checklist; high for adopting the complete distributed stack.

**Bounded next check.** Map five lineage question types onto a fictional ingestion with two source revisions, a reviewer change and a ranking proposal. First record which questions current records cannot answer; add only missing relation fields. Q3 uses an owning-system pointer or stays unknown by design, without private prompt copies.

**Done when.** Require exact local source/version and affected-decision IDs where evidence exists; mark unavailable relations and prompt contents unknown. Confirm forward/backward traversal on the new synthetic relations. No new service unless the file-based baseline fails.

Primary PDF pages: 2, 3, 4, 5. Single workflow demonstration; not independent validation of memory or recovery papers.

### Stop revoked memory from authorizing work

[Revoked but Still Authoritative: An Empirical Study of Revocation Enforcement in Agent-Memory Systems](https://arxiv.org/abs/2609.08258v1) | C-166 | Strong practical fit

**Evidence inspected.** Five agent-memory systems, nine authored scenarios, nine decision models and ten trials per cell, with direct/indirect insertion and multiple defenses. The reported main grid has 44,550 decision calls; 49,121 is the broader total including supplementary and unreported diagnostics.

**Reported result.** In the two directly exposed configurations, revoked records ranked first in all 81 scenario/model retrieval checks. Table 6 reports unsafe-action rates of 44.2% and 42.1% without defense and 0% with retrieval filtering for those conditions. These are author-measured cells, not a universal safety guarantee.

**Compared with our system.** Published rules distinguish recall from permission, but the inspected checkpoint manifest keeps the original authority block and supplies no dynamic revocation event. Its release approval is bound to an exact head and invalidated by a changed head, the closest implemented mechanism. Test retrieval-time revocation and downstream scope separately; policy is not runtime proof.

**Limits and burden.** Small authored scenario set, ten trials per cell, pooled rates without confidence intervals and configuration-specific revocation semantics. Experimental mem0 differs from default. Read-path guard results are author-evaluated. Table 10 reports 44,550 main-grid and 49,121 total calls, including reported supplementary studies plus unreported persistence/parse diagnostics; reconciliation with the separate Section C run counts is unresolved. These totals are not independent participant counts. Low for synthetic fixtures, medium for enforcement in an owning runtime after separate review.

**Bounded next check.** Create fictional old permission, revocation and replacement records. Compare current context/checkpoint behavior against an explicit retrieval-time status check and a downstream tool scope check under direct and indirect insertion.

**Done when.** A revoked record may remain in historical evidence but cannot grant action. Record retrieval exposure and attempted/performed effects separately. Valid replacement authority still works; missing status fails closed.

Primary PDF pages: 4, 5, 6, 7, 8, 9, 10, 18, 19, 20. Authored revocation benchmark; complements but does not independently corroborate Supersede.

### Keep the correction when memory is compressed

[Supersede: Diagnosing and Training the Memory-Update Gap in LLM Agents](https://arxiv.org/abs/2606.27472v1) | C-201 | Diagnostic only, limited evidence

**Evidence inspected.** Knowledge-update subset of LongMemEval: 78 oracle cases with a 300-character persistent-memory budget; a smaller 25-case scale study and one-seed GRPO training experiment on Qwen2.5-3B with 2,000 synthetic episodes.

**Reported result.** The reported training comparison changes held-out accuracy from 7/78 to 13/78. The diagnostic exposes memory-update loss under compression; the split between stale facts surviving, corrected facts disappearing and other failures is not quantified. Training benefit is not established by one seed.

**Compared with our system.** The public checkpoint manifest drops oldest active items under its byte cap without an omitted-active counter; its digest covers IDs before truncation. A receipt therefore does not establish that a critical correction was loaded. Add a fixture where truncation drops an early correction, without claiming the private runtime has this defect.

**Limits and burden.** Single training seed, small held-out denominator, synthetic training data and no reliable general improvement claim. A 25-case history-size study cannot establish that more history harms all memory systems. No local reproduction. Low for a diagnostic fixture; training is excluded.

**Bounded next check.** Run a fictional changed-fact sequence through the current fixture with a fixed small memory budget. Include a critical early correction later pushed beyond the context cap; record whether it was stored, selected, omitted, loaded and used.

**Done when.** The latest supported fact survives required compaction; an old statement stays traceable as superseded. Abstention when source evidence never existed is safe uncertainty, but abstention after required evidence was dropped is a recorded compaction failure. Keep judge and exact-matcher accuracy separate.

Primary PDF pages: 3, 4, 5, 6, 7, 8. Memory-update diagnosis with one training seed; not independent evidence of revocation enforcement.

### Check that a chart says what the data supports

[Lexara-RF: Reference-Free Metrics for Evaluating Conversational Visual Analytics Agents](https://arxiv.org/abs/2609.17842v1) | C-403 | Strong practical fit

**Evidence inspected.** Thirteen reference-free checks over prompt, visualization specification, data/schema, explanation and history. Validation reuses 120 human-rated CVA responses; failure localization examines 90 responses, including 54 structurally grounded cases across six modes.

**Reported result.** Reported median Spearman correlation with human ratings is 0.60, with stronger 0.68-0.74 values for execution-grounded checks and weaker 0.42-0.52 values for subjective rubric checks. Non-significant differences on 11/13 dimensions do not establish equivalence.

**Compared with our system.** Our existing evidence-first evaluation can gain concrete chart and explanation checks: recompute values, confirm filters and sorting, and disclose assumptions. This supports StaleToast readability without importing an overall quality scalar.

**Limits and burden.** English and Vega-Lite-style specifications only; reused corpus and inherited metric weights. Two trained practitioners supply ratings; the paper reports different agreement summaries whose roles need clarification before reuse. Supplementary algorithms and corpus were not independently reproduced. Small per-mode counts of 5-11 limit localization claims. Low for checklist/fixtures; medium for grammar-specific execution checks.

**Bounded next check.** Use original fictional charts with an omitted year filter, swapped metric, wrong sort, hidden denominator and unsupported explanation. Treat assumptions disclosure as human/judge-dependent unless the fixture explicitly defines a deterministic denominator assertion. Include a valid alternative chart and an intentionally extra filter.

**Done when.** Catch planted structural errors and distinguish factual failure from subjective disagreement. Check whether Show Me candidate restrictions or extra-filter penalties reject the valid alternative. StaleToast grammar compatibility is unverified until a local adapter is checked; do not import Vega-Lite thresholds directly.

Primary PDF pages: 2, 3, 4. Reused Lexara response corpus; reference-free/reference-based comparison is not independent replication.

### Test whether good scores survive a fairer comparison

[Shortcut Sensitivity in Agent-Safety Evaluations](https://arxiv.org/abs/2610.22243v1) | C-404 | Strong practical fit

**Evidence inspected.** Three-level audit separates label predictability, observational association and paired decision sensitivity. Uses 576 deduplicated LinuxArena trajectories, 1,220 AgentDojo steps and 731 AgentHarm steps in 197 interaction groups. Paired study uses 64 bases from 58 interactions and three calls per condition.

**Reported result.** A label-predictability diagnostic, exact-tool lookup, falls from F1 0.901 in grouped cross-validation to 0.495 under domain holdout. Released TS-Guard F1 changes from 0.902 per row to 0.719 with equal interaction weight, while balanced accuracy rises from 0.754 to 0.776: the unit/prevalence changed, not simply guard quality. Repeated Haiku sensitivity does not reproduce at similar magnitude in the Luna configuration.

**Compared with our system.** Our separate outcome and burden measures already resist one headline score. This adds concrete source/domain holdouts, duplicate-unit checks and paired/placebo controls to ingestion and collaborative-intelligence evaluation.

**Limits and burden.** Fixed non-probability cohort, exploratory intervals, no blinded validation that marker/alias edits preserve meaning, quantized reproduction and configuration-specific effects. Predictive cues are not evidence that a guard uses them; evaluation validity is not deployment safety. Low for offline denominator/dedup checks; provider experiments require separately bounded authorization.

**Bounded next check.** Re-score a fictional evaluation with repeated steps from a few tasks, reporting row and task-weighted results and an unseen-source holdout. Paired edits, repeats and placebo controls apply only to a separately authorized stochastic scorer, not a deterministic catalog sort.

**Done when.** Preserve the original analysis, explain any rank change with the denominator and weighting unit, and distinguish correlation from an actual paired effect. No guard calls or paid experiment are authorized by this appraisal.

Primary PDF pages: 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14. Audit of existing benchmarks plus bounded paired guard tests, not end-to-end safety evidence.

### Memory that keeps context useful

[aiming-lab/SimpleMem](https://github.com/aiming-lab/SimpleMem) | R-626 | Compare before adopting

**Evidence inspected.** The inspected memory builder extracts entries from windows; the retriever combines semantic, keyword and structured searches with planning/reflection and deduplication. Session lifecycle tests use stubs.

**Compared with our system.** Existing scoped memory is the baseline. The possible addition is a retrieval/compaction comparison, not a replacement store based on README accuracy claims.

**Limits and burden.** LLM extraction, embeddings and retrieval planning add model/dependency cost. Benchmark claims are not reproduced. Hosted services and private conversation upload are excluded; recall does not prove correction or access enforcement. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** Use identical fictional changed-fact tasks with current scoped memory and a minimal retrieval variant. Count correction failures, source-version loss, abstentions, tokens and latency.

**Done when.** Proceed only if the variant reduces missed relevant facts without worsening correction survival or isolation, at a stated extra cost.

**Rights.** MIT. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [simplemem/core/memory_builder.py](https://github.com/aiming-lab/SimpleMem/blob/db80b6a7c591e0ea730a058e9f5fc4eb06572299/simplemem/core/memory_builder.py)
- [simplemem/core/hybrid_retriever.py](https://github.com/aiming-lab/SimpleMem/blob/db80b6a7c591e0ea730a058e9f5fc4eb06572299/simplemem/core/hybrid_retriever.py)
- [cross/tests/test_session_lifecycle.py](https://github.com/aiming-lab/SimpleMem/blob/db80b6a7c591e0ea730a058e9f5fc4eb06572299/cross/tests/test_session_lifecycle.py)

Upstream tests were inspected, not executed. Current head matched the reviewed pin at observation.

### Comparable run receipts across coding tools

[Asymptote-Labs/agent-beacon](https://github.com/Asymptote-Labs/agent-beacon) | R-631 | Strong practical fit

**Evidence inspected.** TraceBundleV1 defines provenance, harness, session, identity, repository, project, namespace and model fields. A substantial redaction engine and model-normalization tests are present; tests were inspected, not run.

**Compared with our system.** Our checkpoint receipts already carry ownership and evidence. A small adapter could reveal missing or differently named fields across harnesses without replacing the handoff contract.

**Limits and burden.** Collector coverage is not proved across all harnesses. Pattern redaction cannot guarantee removal of every secret. Persistence, destinations and raw content capture need owning-runtime review before use. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** Map two fictional harness records, one with missing served-model identity and one failed tool call, into a minimal common receipt without copying prompts.

**Done when.** Preserve unknowns and errors, retain source format/version and demonstrate that redacted values do not reach the exported receipt.

**Rights.** MIT. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [pkg/asymptoteobserve/trace.go](https://github.com/Asymptote-Labs/agent-beacon/blob/e0989909e3169cd82066d051f3aa9642ae2bad1e/pkg/asymptoteobserve/trace.go)
- [pkg/asymptoteobserve/redact_engine.go](https://github.com/Asymptote-Labs/agent-beacon/blob/e0989909e3169cd82066d051f3aa9642ae2bad1e/pkg/asymptoteobserve/redact_engine.go)
- [pkg/asymptoteobserve/model_test.go](https://github.com/Asymptote-Labs/agent-beacon/blob/e0989909e3169cd82066d051f3aa9642ae2bad1e/pkg/asymptoteobserve/model_test.go)

Upstream tests were inspected, not executed. Current head matched the reviewed pin at observation.

### Retry work without doing it twice

[temporalio/temporal](https://github.com/temporalio/temporal) | R-648 | Strong pattern, heavy platform

**Evidence inspected.** Inspected code derives deduplication keys for reapplied events and handles workflow-ID reuse/conflict policies. A focused unit test checks event-key identity.

**Compared with our system.** Checkpoint and replay evidence alone do not make an external write idempotent. Borrow stable operation IDs and reconciliation cases before considering a workflow server.

**Limits and burden.** Operating Temporal adds a server, durable state, SDK integration and maintenance. These files do not prove every downstream tool effect is deduplicated or rolled back. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** Extend a fictional lost-acknowledgment case with operation ID, request hash, restart and reconciliation. Compare checkpoint-only retry with a durable synthetic effect receipt.

**Done when.** One effect for duplicate identical requests; changed payload under the same key is rejected; uncertain effects trigger reconciliation rather than blind retry.

**Rights.** MIT. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [common/definition/resource_dedup.go](https://github.com/temporalio/temporal/blob/ed5ad7be640621faad089fcc14c112af6dc699d0/common/definition/resource_dedup.go)
- [service/history/api/workflow_id_dedup.go](https://github.com/temporalio/temporal/blob/ed5ad7be640621faad089fcc14c112af6dc699d0/service/history/api/workflow_id_dedup.go)
- [common/definition/resource_dedup_test.go](https://github.com/temporalio/temporal/blob/ed5ad7be640621faad089fcc14c112af6dc699d0/common/definition/resource_dedup_test.go)

Upstream tests were inspected, not executed. The repository head had moved since the reviewed pin; recheck before reuse.

### Explain and resume an interrupted agent run

[shepherd-agents/shepherd](https://github.com/shepherd-agents/shepherd) | R-673 | Promising early implementation

**Evidence inspected.** SQLiteTraceStore provides append/conflict handling, content-addressed facts and intent state. Conformance tests cover restart idempotence and conflicting batches. The schema_library file inspected is only a re-export.

**Compared with our system.** Our public checkpoint/replay patterns already describe resume boundaries. Concrete trace-store conformance cases may expose missing restart and conflict fixtures.

**Limits and burden.** Early alpha, substantial trace-store/runtime machinery and changing APIs. A reversible trace is not proof that external side effects can be undone. Credential and writable workspace grants remain separate. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** Translate three existing checkpoint cases into restart, duplicate append and conflicting-owner cases with fictional data; compare current file-based behavior first.

**Done when.** Resume preserves the acknowledged owner and exact receipt; conflicting histories are rejected visibly; no external write is inferred reversible.

**Rights.** MIT. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [shepherd2/src/shepherd2/trace_store.py](https://github.com/shepherd-agents/shepherd/blob/d34d5ca334871dfcb5a3dc76dd78045829fa4e56/shepherd2/src/shepherd2/trace_store.py)
- [shepherd2/src/shepherd2/schema_library.py](https://github.com/shepherd-agents/shepherd/blob/d34d5ca334871dfcb5a3dc76dd78045829fa4e56/shepherd2/src/shepherd2/schema_library.py)
- [shepherd2/tests/test_trace_store_conformance.py](https://github.com/shepherd-agents/shepherd/blob/d34d5ca334871dfcb5a3dc76dd78045829fa4e56/shepherd2/tests/test_trace_store_conformance.py)

Upstream tests were inspected, not executed. Current head matched the reviewed pin at observation.

### See which tools an agent actually contacted

[cyberark/agentwatch](https://github.com/cyberark/agentwatch) | R-865 | Watch, inspect before any use

**Evidence inspected.** The HTTP interception base matches host/port rules. IPC models carry execution and callback IDs. The webhook handler serializes graph node/edge data to configured URLs.

**Compared with our system.** The incremental question is whether process-level interception finds tool activity omitted from our explicit receipts. Observation still cannot authorize an action or prove completion.

**Limits and burden.** Python/npm runtime and interception complexity; source declares remote MCP HTTP/SSE coverage, not universal coverage. Webhook egress carries graph content. Inspected handler lacks explicit status-failure handling and closes a newly created session in finally rather than its shared session. No end-to-end tests were inspected for this candidate. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** First design an offline fictional network-event coverage table against current receipts. Before any later installation, review concrete hooks, destinations, redaction and session lifecycle.

**Done when.** Remain a Watch candidate until coverage and egress behavior are independently checked; no adoption recommendation follows from the appraisal.

**Rights.** Apache-2.0. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [src/agentwatch/hooks/http/http_base_hook.py](https://github.com/cyberark/agentwatch/blob/56012207e0b2570c1a9716b6fec72288c3958d48/src/agentwatch/hooks/http/http_base_hook.py)
- [src/agentwatch/models.py](https://github.com/cyberark/agentwatch/blob/56012207e0b2570c1a9716b6fec72288c3958d48/src/agentwatch/models.py)
- [src/agentwatch/webhooks/handler.py](https://github.com/cyberark/agentwatch/blob/56012207e0b2570c1a9716b6fec72288c3958d48/src/agentwatch/webhooks/handler.py)

Upstream tests were inspected, not executed. Current head matched the reviewed pin at observation.

### Show what changed and what was actually checked

[DataRecce/recce](https://github.com/DataRecce/recce) | R-900 | Strong practical fit

**Evidence inspected.** Schema-evidence predicates require valid complete coverage and an exact empty schema-diff frame before approval. Tests distinguish unknown, partial, truncated, contradictory and malformed results.

**Compared with our system.** Our pinned snapshots and counts preserve identity. A small coverage-aware catalog diff would make incomplete ingestion visible and avoid interpreting an empty result as no change.

**Limits and burden.** The full dbt/Pandas application and cloud artifact upload exceed this catalog need. The strict coverage gate applies to schema comparisons; other result types keep caller-dependent behavior and must not be represented as universally fail-closed. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** Diff two fictional source ledgers with one missing page, duplicate ID and changed appraisal. Separate a genuinely empty complete diff from a truncated or unexecuted comparison.

**Done when.** No-change requires explicit complete coverage; unknown/partial cannot auto-pass. Preserve both catalog versions and identify every changed source ID.

**Rights.** Apache-2.0. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [recce/schema_evidence.py](https://github.com/DataRecce/recce/blob/1b121299076e6ba794e02eac1557c1932b5fbf52/recce/schema_evidence.py)
- [recce/diff.py](https://github.com/DataRecce/recce/blob/1b121299076e6ba794e02eac1557c1932b5fbf52/recce/diff.py)
- [tests/test_schema_evidence.py](https://github.com/DataRecce/recce/blob/1b121299076e6ba794e02eac1557c1932b5fbf52/tests/test_schema_evidence.py)

Upstream tests were inspected, not executed. The repository head had moved since the reviewed pin; recheck before reuse.

### Compare agent frameworks with the same task

[mozilla-ai/any-agent](https://github.com/mozilla-ai/any-agent) | R-1002 | Useful comparison, dependency gap

**Evidence inspected.** README exposes a common agent interface. Inspected AgentTrace is a tinyagent re-export; EvaluationOutput contains passed/reasoning. Local trace tests check token/cost cache invalidation and empty spans.

**Compared with our system.** Could provide comparable receipt inputs for our same-task baseline comparisons. The inspected wrapper is not independent evidence of full tracing or authority enforcement in each framework.

**Limits and burden.** The actual trace implementation lives in an uninspected dependency. Framework adapters, provider behavior and execution coverage remain unverified. Estimated cost is not an actual billing receipt; capture can expose prompts. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** Compare fictional normalized outputs from two harnesses with identical task, acceptance criteria and missing-model case. Review the pinned dependency before a real adapter trial.

**Done when.** Report unsupported fields and missing identity as unknown, distinguish observed tokens from estimated money, and do not claim framework parity from a wrapper alone.

**Rights.** Apache-2.0. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [src/any_agent/tracing/agent_trace.py](https://github.com/mozilla-ai/any-agent/blob/a469723ac4a0518ab0696d57e09e4dc407c826ec/src/any_agent/tracing/agent_trace.py)
- [src/any_agent/evaluation/schemas.py](https://github.com/mozilla-ai/any-agent/blob/a469723ac4a0518ab0696d57e09e4dc407c826ec/src/any_agent/evaluation/schemas.py)
- [tests/unit/tracing/test_agent_trace.py](https://github.com/mozilla-ai/any-agent/blob/a469723ac4a0518ab0696d57e09e4dc407c826ec/tests/unit/tracing/test_agent_trace.py)

Upstream tests were inspected, not executed. Current head matched the reviewed pin at observation.

### Separate static checks from a real successful run

[NVIDIA/SkillEvaluator](https://github.com/NVIDIA/SkillEvaluator) | R-1005 | Strong practical fit

**Evidence inspected.** Evidence IDs can resolve by explicit ID, JSON pointer or path. Live-evaluation service rejects empty/nonmapping/error-bearing or non-succeeded run envelopes. Local-mode tests explicitly reject native Windows.

**Compared with our system.** Our evidence-first acceptance already separates review from execution. Borrow the artifact-status contract and static/overlap/live separation, not the project grade as an overall intelligence score.

**Limits and burden.** Live evaluation requires supported sandbox/provider setup and dependencies. Native Windows is unsupported at this pin; WSL2/Docker is a different environment. Third-party dependencies have separate terms; skill docs may leave the host during model review. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** Feed fictional static-pass, overlap-warning, failed live run and missing-artifact receipts into the current acceptance template without installing upstream.

**Done when.** A static pass never becomes runtime success; missing/non-succeeded evidence remains unresolved. Every claim points to its own artifact and environment.

**Rights.** Apache-2.0. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [src/skillevaluator/evidence.py](https://github.com/NVIDIA/SkillEvaluator/blob/6d5d57f35c333030368cc4c7533cf68976f5ac7d/src/skillevaluator/evidence.py)
- [src/skillevaluator/evaluation/service.py](https://github.com/NVIDIA/SkillEvaluator/blob/6d5d57f35c333030368cc4c7533cf68976f5ac7d/src/skillevaluator/evaluation/service.py)
- [tests/test_local_mode_contract.py](https://github.com/NVIDIA/SkillEvaluator/blob/6d5d57f35c333030368cc4c7533cf68976f5ac7d/tests/test_local_mode_contract.py)

Upstream tests were inspected, not executed. Current head matched the reviewed pin at observation.

### Test what a coding agent really produced

[UiPath/coder_eval](https://github.com/UiPath/coder_eval) | R-1012 | Strong practical fit

**Evidence inspected.** SuccessChecker dispatches registered criteria; JSON checks support schema and JMESPath assertions. Round-trip tests preserve criterion status and result types, including fallback and failure evidence.

**Compared with our system.** Our test harness defines task and baseline outcomes. A small reusable result schema could preserve evaluated/not-run distinction and per-criterion evidence across agent tools.

**Limits and burden.** Python 3.13+, agent runtime and possible sandbox/provider dependencies. Full tool telemetry can contain sensitive data. Weighted scores and model judges do not establish authority, safety or human usefulness. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** Express three existing fictional acceptance cases as explicit artifact assertions, including valid output with missing evidence and a criterion that was not run.

**Done when.** Do not pass an unexecuted criterion; retain exact evaluated artifact, criterion version and failure reason. Keep human review and permission gates separate.

**Rights.** Apache-2.0. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [src/coder_eval/evaluation/checker.py](https://github.com/UiPath/coder_eval/blob/484c3d5db6434392ba8baa60378f3f900d7d0924/src/coder_eval/evaluation/checker.py)
- [src/coder_eval/criteria/json_check.py](https://github.com/UiPath/coder_eval/blob/484c3d5db6434392ba8baa60378f3f900d7d0924/src/coder_eval/criteria/json_check.py)
- [tests/test_criterion_result_round_trip.py](https://github.com/UiPath/coder_eval/blob/484c3d5db6434392ba8baa60378f3f900d7d0924/tests/test_criterion_result_round_trip.py)

Upstream tests were inspected, not executed. Current head matched the reviewed pin at observation.

### Recover safely when a tool response is misleading

[Ta0p1/ResolveLab](https://github.com/Ta0p1/ResolveLab) | R-1020 | Strong practical fit

**Evidence inspected.** Recovery tests cover lost acknowledgments across restart, duplicate/concurrent commits, changed requests under reused keys, partial commits, stale/fabricated status, read-only denials and verification after the last write.

**Compared with our system.** These are concrete adversarial fixtures for our checkpoint and replay rules. The immediate transfer is a synthetic failure suite, not post-training or another orchestration platform.

**Limits and burden.** Tests were inspected, not executed. Reported agent success rates and training comparisons are author claims, not locally reproduced results. Provider/sandbox integration and synthetic-to-real transfer remain unknown. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** Port the lost-ack, stale-success, concurrent-retry and post-write-verification scenarios as fictional cases against the current receipt workflow.

**Done when.** At most one intended effect; stale status never closes a changed task; final verification follows the latest mutation; uncertainty escalates with preserved evidence.

**Rights.** MIT. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [src/resolvelab/runner.py](https://github.com/Ta0p1/ResolveLab/blob/68e90402f3a42b51cb927967da1f8008697d3e8f/src/resolvelab/runner.py)
- [src/resolvelab/evaluation.py](https://github.com/Ta0p1/ResolveLab/blob/68e90402f3a42b51cb927967da1f8008697d3e8f/src/resolvelab/evaluation.py)
- [tests/test_recovery.py](https://github.com/Ta0p1/ResolveLab/blob/68e90402f3a42b51cb927967da1f8008697d3e8f/tests/test_recovery.py)

Upstream tests were inspected, not executed. Current head matched the reviewed pin at observation.

### Keep task, trace and evaluation connected

[datamllab/A2E](https://github.com/datamllab/A2E) | R-1036 | Useful design, substantial stack

**Evidence inspected.** Trace schemas encode spans, status, context, events and exceptions. SQLite SpanStore flattens attributes/usage and fetches traces. A small grader-contract test checks a terminal benchmark result boundary.

**Compared with our system.** Our evidence pointers could gain a clearer task-to-run-to-evaluation relation and explicit missing-span state. Full server/UI adoption is not yet justified.

**Limits and burden.** Persistent server, instrumented full trajectories, provider credentials and benchmark containers increase storage/privacy/maintenance burden. One-run examples are not reliability estimates; selected tests do not prove all instrumentation coverage. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** Build a fictional task/run/evaluation mapping with one missing span and failed grader. Compare with current checkpoint pointers before proposing any server.

**Done when.** A score always resolves to exact task/run/source versions; missing trace and grader failure remain visible. Store only the minimum synthetic/public fixture.

**Rights.** MIT. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [server/server/src/a2e/trace/schemas.py](https://github.com/datamllab/A2E/blob/ef86ec507f66a8fd6a2223b351b95444ab701f6b/server/server/src/a2e/trace/schemas.py)
- [eval/core/span_store.py](https://github.com/datamllab/A2E/blob/ef86ec507f66a8fd6a2223b351b95444ab701f6b/eval/core/span_store.py)
- [task/datasets/terminal_bench_2/tests/test_grader_contract.py](https://github.com/datamllab/A2E/blob/ef86ec507f66a8fd6a2223b351b95444ab701f6b/task/datasets/terminal_bench_2/tests/test_grader_contract.py)

Upstream tests were inspected, not executed. Current head matched the reviewed pin at observation.

### Make every review criterion inspectable

[kling01/RubricLoop](https://github.com/kling01/RubricLoop) | R-1037 | Strong practical fit

**Evidence inspected.** Evaluator specs have IDs, versions/content hashes and compile/validation paths. Release-contract tests require default network blocking, distinct not-applicable/errors, duplicate-ID rejection, explicit model configuration and escaped report text.

**Compared with our system.** Our separate evidence dimensions can gain versioned executable clauses and a clearer inspectable result. Use it to explain decisions, not replace dimensions with a universal rank score.

**Limits and burden.** Early 0.1 release and configuration churn. LLM judges require explicit provider/funding/data authority. Inspected release tests are not a security audit and were not run locally. Pattern extraction is low to medium effort; adopting the full runtime requires a separate dependency, privacy and maintenance review.

**Bounded next check.** Turn three existing acceptance clauses into versioned rules on fictional traces; include not-applicable, malformed evidence, judge failure and untrusted HTML-like text.

**Done when.** Preserve clause version and trace evidence, keep errors out of pass denominators unless the stated policy says otherwise, and render untrusted content as text.

**Rights.** MIT. Repository license only; preserve attribution/notices for any later reuse and review dependency/data/model terms separately. No upstream code copied into the product.

**Exact code evidence.**

- [src/agenteval/engine/evaluate.py](https://github.com/kling01/RubricLoop/blob/782b58af56594d9c49fd1fa6410ddf29e29650c7/src/agenteval/engine/evaluate.py)
- [src/agenteval/engine/core/evaluator_spec.py](https://github.com/kling01/RubricLoop/blob/782b58af56594d9c49fd1fa6410ddf29e29650c7/src/agenteval/engine/core/evaluator_spec.py)
- [tests/test_release_contract.py](https://github.com/kling01/RubricLoop/blob/782b58af56594d9c49fd1fa6410ddf29e29650c7/tests/test_release_contract.py)

Upstream tests were inspected, not executed. Current head matched the reviewed pin at observation.

## Remain in the pool after deeper review

- [The Handover Problem: Governing Autonomy Transitions in Human-AI Collaboration](https://arxiv.org/abs/2610.10352v1). Simulated handover readiness combines weighted factors into a scalar; no human study and insufficient incremental value over separate authority/evidence checks. Reconsider when: A human or operational study tests an incremental boundary mechanism against a strong separate-check baseline.
- [Position: Evaluation Scores Are Perishable Knowledge Claims](https://arxiv.org/abs/2607.26191v1). Position paper largely overlaps existing evidence expiry and separate-dimension principles; mean/min aggregation examples do not establish operational improvement. Reconsider when: A concrete versioned-evidence mechanism demonstrates added value against our existing expiry and evidence practices.

All other retained sources stay eligible for later rounds under the existing pool policy. Prior rankings and analysis remain attached to the same source identities. Sources outside the board may be reconsidered after update checks; this proposal does not itself rerank them.

Machine-readable [appraisals](staletoast-system-fit-appraisals-2026-11-01.json) and [all-source routing](staletoast-system-fit-triage-2026-11-01.json) retain exact pins, hashes, pool IDs, source limits and baseline comparisons. Independent review status is recorded in the companion review receipt.

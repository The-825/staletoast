# Source review batch: November 3

Two research papers and three repositories assessed against the current public Breadcrumbs checkpoint, replay and outcome tools. Four are new deeper assessments of existing pool records; Agent Beacon is a reviewed follow-up. No new source identities, catalog grades or chart positions were added. The rest of the pool and all original analysis remain preserved.

**Recommended next step:** a small synthetic outcome-evidence audit. Keep the original evaluator verdict, record any correction separately, and require a typed observation of the requested state. An agent statement or a successful tool invocation alone cannot establish completion. The proposed check has twelve fictional cases and no network or model calls. It has not been implemented or run.

| Source | What it could add | Decision |
| --- | --- | --- |
| WebArena-Lite outcome audit | Preserve original and corrected verdicts, explain disagreement, and identify the first consequential error | Experiment proposal |
| Evaluation Context Protocol | Separate visible output, tool activity and safely disclosed evidence | Keep in pool: experimental contract, no ECP validation reported |
| DBOS TypeScript | Bounded recovery and ownership-aware restart patterns | Keep in pool: existing operation-ID overlap, atomic concurrency and external effects need owning review |
| Strands evaluation tools | Separate named state checks from output and tool-name checks | Keep in pool: substantial overlap; missing state and explicit null require careful treatment |
| Agent Beacon | Inspect minimization before telemetry reaches multiple destinations | Keep in pool: updated source and privacy scope limits, no collector adoption |

## Evidence-backed outcome review

[Auditing Web Agent Evaluation on WebArena-Lite](https://arxiv.org/abs/2610.01491v1), source ID C-125, reviews outcomes and failed trajectories. It retains the automated score beside the human correction. At the matched 25-step setting, the paper reports 43/165 raw successes and 57/165 corrected with MASM, versus 51/165 and 63/165 with Guide Text plus MASM. These are one-rollout observations, not repeated-trial performance guarantees. Guide coverage, selective failure review and possible state carryover limit transfer.

The useful local idea is to preserve disagreement rather than overwrite history. A stated evidence category still does not prove its observation is authentic. Our proposed fixtures require an observation pointer, declared observer and correction reason, and keep missing evidence unknown. The review also found a reported statistical value inconsistent with an exact calculation from the stated discordant pairs. Both values and the unresolved source discrepancy are retained in the structured record; no source correction is asserted.

## Portable evaluation contract

[The Evaluation Context Protocol](https://arxiv.org/abs/2608.19263v1), C-110, describes a provisional interface and separates output, tool calls and evaluation context. Its authors explicitly leave ECP validation for future work. Secondary benchmark results cited by the paper are not ECP results. We inspected the paper, not its reference runtime.

Our replay tool already supports expected and forbidden outcomes with an unknown state. The remaining idea is a small forbidden-path check for an apparently correct answer. Keep this behind the outcome-evidence experiment rather than adding a framework or adopting a proposed standard.

## Durable recovery

[DBOS TypeScript](https://github.com/dbos-inc/dbos-transact-ts/tree/627990fc59619d3584ce88511ab546bc7483f4b9), R-717, has step/recovery interfaces and tests worth reading. The selected timeout contract warns that the timed-out code is not forcibly terminated. Retrying an external action therefore needs an effect-specific reconciliation contract. The full executor and database implementation were not inspected, and tests were not run.

Breadcrumbs already has operation IDs and bounded replay. Sequential stale-writer fixtures would not prove atomic concurrent safety. Keep the source in the pool until a consumer owner names the missing lock/transaction boundary and checks its own existing equivalent. Full runtime adoption is not recommended by this review.

## Deterministic evaluation

[Strands evaluation tools](https://github.com/strands-agents/evals/tree/32e72bb0639fc69d6763a671b461b12bc08c83af), R-516, separates output equality, tool-name presence and named environment-state equality. Tool-name presence alone does not prove permitted arguments or success. In the inspected equality code, two absent output values can compare equal. A null target can arrive through an expected-output or expected-state record, so null must not be confused with an omitted expectation.

The proposed native guard keeps per-state reasons and unknowns, rejects duplicate state names, and checks observation provenance. Our existing replay checks overlap substantially, so no new dependency is proposed.

## Agent Beacon follow-up

[Agent Beacon](https://github.com/Asymptote-Labs/agent-beacon/tree/a2c3c8070edfd3de088db0efee82f22c8a2eb54d), R-631, now has a corrected five-file collector privacy/export assessment. This pin differs from the original November 1 pin. The prior trace/model/redaction findings remain historical and are not reverified at this newer pin.

Claude requested changes. The owner resolved them by recording the uninspected current redaction engine, anchored-secret fixture limits, uncertain error forwarding, distinct processor/exporter controls, and storage/capture limits. A field-name allowlist is insufficient when permitted values contain unrestricted text. The proposed synthetic check adds two fictional sinks and sentinels inside otherwise permitted text fields. The current public checkpoint has one JSONL sink; this fan-out scenario is an analogy, not a demonstrated existing leak. No second Claude PASS is claimed.

## Review and rights

One bounded Claude Sonnet 5.5 medium source-assessment round was followed by local Codex source checks and owner resolution. Both paper PDFs, selected repository files and the current public baseline are pinned with digests in the [structured assessment](staletoast-system-fit-appraisals-2026-11-03.json). Repo current heads differ from the retained assessed pins; those diffs were not inspected. No upstream code, tests or model experiment was run.

The papers use arXiv nonexclusive distribution terms; no broad reuse grant was established. DBOS and Agent Beacon use MIT, and Strands uses Apache 2.0. Dependency and any required NOTICE obligations need review before copying or adoption. This package contains analysis and source references, not upstream implementation code.

Original analyses, evidence depth, pool IDs, rankings, chart editions and frozen exports remain unchanged. Source review is separate from catalog promotion, native validation and adoption.

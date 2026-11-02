# Daily scout: distinguish form validation from execution control

October 26, 2026. Turn owner: Task22, local Codex. Base: `701a1a8c6c421e3f981863b0a911aafc895b2bf5`. Two existing pool candidates reconsidered; zero new discoveries and zero canonical additions. Disposition for both: `backlog`, with a bounded consumer experiment proposed for later authorization. No source confidence, rank, promotion or adoption change.

## Paper: Q-NEXT-093

[Talk Freely, Execute Strictly, arXiv 2603.06394v1](https://arxiv.org/html/2603.06394v1), Joel Strickland et al., March 6, 2026. Selected full-text methods, architecture and limitations inspected, not a complete scientific appraisal.

Sections 5.3 and 5.4 specify registry checks for graph cycles, cross-step types, resolved parameters and tool availability before dispatch, followed by structured run records. Table 5 is an illustrative dialogue, not an executed test receipt. Section 6.5 places deployed proof-of-concept evaluation in future work; an internal testbed is under development. No runnable implementation was inspected here.

The study uses 18 experts from 10 stakeholders and ordinal architecture ratings across 20 systems, with 15 model scoring sessions. Agreement among ratings does not establish execution correctness. Recruitment through customer relationships limits transfer. Sections 6.2 and 6.3 retain registry-maintenance burden, clarification friction, dangerous tools, injection and leakage risks. Schema validity does not ensure scientific appropriateness or end-to-end determinism. Role checks, approvals and isolation remain necessary.

Reuse: the HTML states CC BY-NC-ND 4.0. Retain bibliographic attribution; no paper text or schema example is copied into product code. Code reuse terms remain unverified. Retain in pool pending executable boundary evidence and matched operational evaluation.

## Repository: Q-NEXT-091

[EclipseSource JSON Forms](https://github.com/eclipsesource/jsonforms/tree/7fb14064800bdaa09f8d0eb9501abe15f1cc99cc), pinned commit `7fb14064800bdaa09f8d0eb9501abe15f1cc99cc`. Relevant code, test definitions and license inspected; no tests executed.

The pinned `packages/core/src/reducers/core.ts` uses AJV on initialization and updates, returning form data with validation errors. `UPDATE_DATA` retains updated data while reporting errors; it is not an execution dispatcher. `NoValidation` is an explicit option. `ValidateAndHide` preserves validation errors while changing presentation behavior. These are legitimate form behaviors, not evidence of a security defect or a protected action gate.

The pinned `packages/core/test/reducers/core.test.ts` defines checks for default validation, invalid numeric data against a string schema, disabling validation, restoring validation and hiding errors. Lines 1823 through 2013 were inspected in detail. Those definitions are not passing-run evidence. `packages/core/src/reducers/middleware.ts` defines an extension point; its default implementation delegates to the reducer. No authorization or external-effect enforcement is established by this inspected path. This is a scoped code read, not a repository-wide security audit.

The pinned root MIT license requires retaining its copyright and permission notice with copies or substantial portions. Dependency licensing, current maintenance, full application submission paths and runtime compatibility remain unappraised. Each fetched file's Git blob hash matches the pinned GitHub tree. No dependency was installed or copied into the pilot.

## Native equivalent and proposed consumer check

The existing synthetic intake pilot separates request fields, holds, correction history and task outcomes. Its task view records that the manual/spreadsheet comparison has not run. A form or spreadsheet with explicit required fields is the smaller baseline for data entry; neither interface should own execution permission. No benefit or replacement is established.

Proposed owning-consumer experiment, not implemented: place a final policy check beside the executor and bind approval to the exact action, resource, schema version and current revision. Use harmless synthetic cases for a valid-shaped but unauthorized action, a stale approved revision, a changed parameter after approval, a cross-step mismatch, disabled UI validation and an ambiguous external result. Measure actual side-effect counts and visible hold reasons, not only error messages. Verify permitted actions once and rejected actions zero times; keep recovery uncertainty explicit. Compare identical packets with the form/spreadsheet baseline, including setup, correction burden and maintenance. These criteria are derived owner acceptance proposals, not source findings.

## Access and limits

Eight external read requests observed, zero discovery queries. Request 2 failed through the web tool; request 3 retrieved the pinned tree through the GitHub API. Requests 1 and 4 read the same paper HTML through different tools; this duplicate access is counted. Requests 5 through 8 fetched the pinned license, reducer, test and middleware. No more external access followed the ceiling. One existing research candidate and one repository received deeper inspection; metadata intake and canonical additions were zero.

No current-day scout receipt was found in this workspace or the four listed StaleToast worktrees before intake. This is a local deduplication check, not a claim about every owner's receipts. The completed 123-note editorial review was excluded from intake counts. Agent Handoff Kit's settled review and Bounded Loops' denominator hold were not reopened. BetterMe PR526 lineage tooling was not available as reviewed exact source in this checkout; adoption remains pending and no command was invented.

Local evidence receipt: `staletoast-scout-2026-10-26.json`. Prior pool records and history retained; two dated reconsideration entries appended. No upstream command, installation, model call, commit, push, freeze, publication or adoption. No Discussion posting.

Codex

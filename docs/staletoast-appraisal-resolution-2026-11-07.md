# METR and Agent Beacon appraisal resolution

November 7, 2026. Owner source checks completed. The dispositions below resolve the open source questions and retain the original analysis. This package awaits independent review before publication or catalog promotion. The [structured record](staletoast-appraisal-resolution-2026-11-07.json) contains exact versions, hashes and residual requirements.

## METR. Retain for organizational evaluation context

[METR's November 5 assessment](https://metr.org/blog/2026-11-05-anthropic-ai-rd-acceleration-assessment/) is useful for distinguishing benchmark progress, self-reported uplift and causal attribution. Its retrospective, single-organization evidence and redactions limit transfer to ordinary development workflows. The numerical result measures benchmark growth, so it cannot set a small team's productivity grade.

A November 6 update corrects AEF-1 access checklist item1.1 from Yes to No. The evaluator lacked query access to unreleased models, which the report says was outside the central assessment method. Preserve that correction alongside the original snapshot. The update does not announce a change to the headline estimate. The structured record separates the observed source correction from our transfer judgment.

Disposition: keep the canonical URL as a contextual research candidate. Require a relevant measured endpoint, comparator and population before deriving quantitative workflow criteria. No ledger ID or grading weight is allocated by this package. The public page reserves rights; link to the original rather than redistribute its body.

## Agent Beacon. Keep the mechanism, hold collector adoption

Existing source R-631 and pool Q-NEXT-764 remain the identities. Selected code at [0450ec2382083722a8e1a564d027b230347dcc96](https://github.com/Asymptote-Labs/agent-beacon/tree/0450ec2382083722a8e1a564d027b230347dcc96) now closes the earlier pipeline-wiring inspection gap for that revision.

The configuration generator places the privacy processor before HEC fan-out and in separate filtered OTLP forwarding pipelines. Local-only primary pipelines rely on local writer sanitation. Selected tests assert rendered ordering and exporter lists. These components support the design lesson of checking each delivery path independently.

Three qualifications resolve the remaining interpretation risks.

- The matching writer still sanitizes retained text and raw fields. Redaction does not establish minimum collection or metadata-only storage. The raw-content capture path and complete sanitization helper internals remain unreviewed.
- At this pin, `sanitize()` marks an oversized event as truncated. The later `append()` size fallback removes raw data and shortens the message, then clears retained file diffs, command output, prompt text and GenAI input/output/tool content if still oversized. It marks retained content as excluded and truncated, and returns an error if the event still exceeds the limit. Both marking and content clearing occur at this same pin. Historical observations remain preserved under their original revisions.
- The repository has a newer observed head,0cc344bdb8b1d7f377559aca9102c241d8740ad7. Its diff was not inspected. The appraisal stays attached to0450ec2.

Disposition: retain the existing pool record and avoid collector adoption. A future owning consumer may propose a minimum-field boundary, with explicit approval for its storage/access behavior. The measurable native check covers local-only, two-sink and forward-only modes, counts sentinel leaks and deliveries to disabled destinations, and checks that raw verdict and provenance survive. That check remains proposed. No upstream execution occurred. MIT license reviewed at the selected pin; dependency terms remain unreviewed.

## Review and publication boundary

Local Codex checked the primary report update, compared the saved snapshot and inspected matching pinned source files. Source hashes are retained in the structured record. These author checks provide the basis for independent review. Review may accept these bounded dispositions without claiming collector execution or a validated productivity effect.

Original catalog IDs, grades, rankings, chart editions and immutable exports are preserved. This is an appraisal-resolution document, not a new chart edition or automatic consumer change.

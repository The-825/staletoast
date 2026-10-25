# Two additions proposed for review

October 21, 2026. These proposals move beyond abstract/README collection. They do not change the current ledger, chart or claim confidence. Proposed IDs must be checked again before intake.

## Agent Handoff Kit, Q-NEXT-060, proposed R-337

Pinned source: https://github.com/djpapzin/agent-handoff-kit/tree/2171dcef26d203da8dc4fe9883bfe3939882e285

Source-traced, not executed. The review follows claim/takeover, guarded writes, atomic receipt/checkpoint/history updates, uncertain commit acknowledgment and read-only replay. Exact file ranges, observations and collected-file digests are in the paired JSON. The pinned MIT license was inspected.

The useful addition is a compact local recovery boundary that can be inspected without a distributed platform. Existing Temporal and Hatchet records already cover broader durable execution, so the proposal does not claim a novel mechanism. Tests contain failure and corruption scenarios, but no tests were run here. Local transaction safety does not establish remote exactly-once effects, human authority, trusted identity or resistance to a database administrator.

Review acceptance: verify the source trace, license and overlap; retain the source-level depth. Any later experiment must use synthetic local effects and compare stale writes, ambiguous acknowledgment and replay writes against a naive baseline.

## Bounded Loops, Q-NEXT-075, proposed C-026

Source: https://arxiv.org/abs/2609.27871v1

Selected full-text claim appraisal completed, not a complete proof audit or replication. The paired JSON records a bounded interpretation, relevant sections and validity concerns. Quantitative confidence is withheld, including an unreconciled catalogue/exclusion-count explanation. This proposal supports a better question about check quality, not a claim that this harness is proven safe.

## Owner review checklist

- One paper and one repository proposal, within the daily two-per-category cap.
- Preserve original pool observations and ranks; append this deeper evidence.
- Review source pointers, contrary findings, overlap and defensible evidence depth.
- If accepted, reconcile IDs and update owning ledgers/appraisals; freeze a new export only after canonical inputs are committed.
- Keep validation, peer review, merge, deployment and adoption as separate states.

No source execution, provider call, new dependency, public posting or publication occurred. The existing repository owner holds the review queue.

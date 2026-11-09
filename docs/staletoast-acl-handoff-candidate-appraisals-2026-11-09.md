# Candidate appraisals for two ACL handoff studies

These citation-only appraisals use the October 2026 ACL proceedings. Alternate preprint aliases, artifact licenses and maintenance remain unverified. The checks below are proposals.

## Handoff Debt

Dipesh KC and Anjila Budathoki. ACL Anthology 2026.emnlp-main.738. DOI 10.18653/2026.emnlp-main.738. https://aclanthology.org/2026.emnlp-main.738/

The authors held repository state fixed across four handoff views at 181 checkpoints from 75 tasks. Context reduced median agent events and cumulative prompt tokens across three successor models. Solved-rate effects varied. The main study used one attempt per view per checkpoint in one runtime. A repeated subset supported the direction of the effort result (Table 4 and limitations, pp. 17110-17118). Official test passage measured resolution, leaving maintainability and human usefulness unmeasured.

Breadcrumbs already binds evidence to revisions and scopes retesting. This adds a measure of repeated work. Compare paired synthetic takeovers from identical checkpoints with the current handoff and with repository state alone. Require fewer redundant inspections or validations in at least one pair and no increase in any pair. Require the same or better completion and preserve every already solved case.

## Facts Without Rules

Yian Wang, Agam Goyal, Eshwar Chandrasekharan, and Hari Sundaram. ACL Anthology 2026.findings-emnlp.422. DOI not verified. https://aclanthology.org/2026.findings-emnlp.422/

The authors observed loss of audience restrictions even where operational facts survived compression. The single-agent control also showed leakage. Table 32 (p. 8899) reports leakage in 0, 1 and 4 of 48 cases across three models with clean allowlists, versus 44, 38 and 35 of 48 when negation was flipped. The allowlists use gold audience labels, leaving live boundary inference untested by that comparison. Judge-dependent measures and semi-synthetic external traces leave production leakage rates unknown.

Breadcrumbs already records receiver acknowledgment. This adds an explicit check of whether the receiver can act only within the transferred restrictions. Use synthetic cases covering a valid audience, an unauthorized audience, a malformed audience key and flipped negation. Require successful completion for the valid case and zero prohibited disclosures for the other cases.

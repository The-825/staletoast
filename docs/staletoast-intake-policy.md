# Daily scouting and monthly pool review

Effective October 13, 2026, by the owner's instruction. This policy applies
separately to research articles and public repositories. StaleToast owns their
ledgers, rankings and pool. Breadcrumbs owns workflow guides and prompts.
The [machine-readable policy](staletoast-intake-policy.json) records the limits.

## Daily round

The November 26 capacity update raises the daily limits to match review capacity
(see below). The October 21 operating update broadened discovery. Discover up to 50 metadata-only candidates per category against a named gap; this
is a ceiling, not a quota. Normalize identities, aliases and evidence families,
then screen at most twenty primary sources per category. Reserve the main effort
for existing-pool candidates (target at least four, at most twelve a day) before
expanding the pool.
Record actual queries, source dates, exclusions, duplicates, access limits and
separate discovery/screen/appraisal counts. Report shortfalls rather than force
screens or additions. The daily and monthly limits below still apply.

Add sources per category only when quality supports their inclusion. Twelve is
the daily maximum, including sources already added that day. Zero is valid. Use the existing appraisal and ranking method; do not lower its evidence
requirements to fill a quota. Rediscovery and reconsideration are not new growth.

Keep unselected leads in the existing next-round pool with a stable pool ID,
canonical source, observed version, evidence depth, selection reason and next
check. Retention is not approval or an adoption recommendation.

## Scope components

Effective November 27, 2026, by the owner's instruction, the search scope is
named in the [scope map](staletoast-scope-map.md). It keeps the seven components
the November 1 routing already compared sources against and adds four that no
round had named: security and containment, deliberation and dissent, learning
from operation, and orchestration and automation.

Each round records one component alongside its named gap. Claims stay the unit
of evidence and the gap order is unchanged. For an added component, screen the
existing retained pool against its terms first; discover new candidates only
where that leaves the component thin. The limits in this policy do not change,
and the awaiting-appraisal backlog still takes the main effort. Queries listed
for an added component are proposals until a dated batch records what was run.

## Why twelve

On November 26 the limit moved from two to twelve per category. From November 23
to 25 about 26 reviewed records merged each day, one an hour, so two was no longer
the operating limit. At that pace the 1,042 automated screens still awaiting
appraisal (377 papers, 665 repositories) take about six weeks to clear. The limit
follows review capacity, not discovery volume. Raise it again only when the
awaiting-appraisal count falls well below a week of work. Lower it if review
quality slips or the merge gate backs up.

## Monthly round

Once per month, rank the strongest ten eligible pool records in each category
using the existing method. Recheck their current primary sources, then propose
at most the top three in each category for the owner's consideration. Record
the shortlist and why each proposed source is useful. If fewer sources qualify
or can be checked, report the actual count and reason.

For repositories, inspect changes since the prior pinned commit, relevant code,
releases, maintenance and license terms. For research, check publication versions,
corrections, retractions, changed findings and contrary evidence. Reading code
does not establish executed behavior. A new retrieval date does not renew an
old appraisal.

Monthly consideration does not automatically add sources or place them on the
board. Any subsequently approved new intake shares the daily maximum with that
day's ordinary scouting. Already cataloged sources can be reranked without
counting as new additions.

## Return sources to the pool without losing history

A ranked source outside its category's current Hot100 is eligible for the pool
again. Keep it in the uncapped ledger and link its pool record to the original
stable ID. Reuse an existing pool record where one exists. Never issue a second
ledger identity, remove its appraisal or rewrite a frozen chart edition.

Preserve the original analysis, source version, ranking method, position and
evidence limits. Append each reconsideration as a dated observation containing:

- Stable ledger and pool IDs, canonical source and prior receipt reference.
- Prior and current source versions, retrieval date and evidence depth.
- Prior and proposed rank, ranking method version and reasons for the change.
- Changed code or findings, improvements, regressions and contrary evidence.
- What was inspected or executed, omitted checks, uncertainties and disposition.
- A proposed useful mechanism or lesson and the owning consumer's next check.

Keep these observations in dated receipts alongside the existing pool and
appraisals. Preserve prior receipts and frozen editions. Missing historical
facts remain unknown; do not reconstruct an original score as if recorded.
Correction notes can supersede an interpretation while retaining its source.

Use this history to compare improvements and inform our own work. Catalog rank
does not establish scientific confidence, runtime readiness or adoption benefit.
An insight can become a proposal; implementation needs the owning system's
validation and authority.

## Operating boundary

This is the intake policy and review cadence, not an implemented autonomous
selection service. Scheduled runs prepare bounded evidence and review proposals.
The sole writer, native validators, immutable exports, team review and normal
publication gates remain in force. No upstream code execution, installation,
provider calls, private records or automatic adoption follows from selection.

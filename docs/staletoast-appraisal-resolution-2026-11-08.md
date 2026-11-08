# Source review: report validity and comparison coverage

November 8, 2026. These bounded appraisal resolutions propose teaching and
validation examples. They do not change catalog grades, chart eligibility or
software adoption. Exact source versions, hashes, baseline files and remaining
limits are in the [structured record](staletoast-appraisal-resolution-2026-11-08.json).
The final independent disposition belongs to the publishing PR's exact-head review.

## C-004: a finished report still needs verification

[AI Soccer Analyst](https://arxiv.org/html/2609.11224v1), by Calvin Yeung and
Keisuke Fujii, uses staged analysis and revision. Its single-system evaluation
has no controlled baseline. Report generation is its operational completion
endpoint, not proof that an analysis is correct. Fixed task order, selected
participants and ratings conditional on completion limit transfer.

The useful proposed example is narrower than a productivity claim: change an
analysis definition and make affected output visibly stale until it is checked
against that definition. Stage-routed regeneration is described by the paper.
Keeping earlier versions and withholding a verified-current label are local
design proposals, not established capabilities or benefits of that system.

Breadcrumbs already records corrections, supersession, freshness and unknown
replay outcomes. A new fixture should reuse those fields. Here, "blocked" means
not shown as current or verified in the record, not an installed runtime gate.
Predeclare what the unchanged process would do and allow a no-difference result.
All six proposed synthetic cases remain in the case totals; fictional cases and
one reviewer cannot establish time savings or a population completion rate.

The public committed baseline is pinned at Breadcrumbs `28749d5`. Its relevant
files match the earlier `df5040e` baseline. Uncommitted product drafts are excluded.
The observed paper license is CC BY-NC-SA 4.0. This proposal uses original examples
and links, without reproducing the paper's figures, tables or task wording.

## R-900: distinguish the layers of coverage

[DataRecce/recce](https://github.com/DataRecce/recce/tree/1b121299076e6ba794e02eac1557c1932b5fbf52)
retains repository identity R-900 and pool identity Q-NEXT-1033. The selected
artifact-health code and tests narrow a previously uninspected classifier gap
at that same pin. A newer observed head is metadata only; its diff is unreviewed.

Artifact health compares expected manifest relation IDs with one catalog's node
IDs. Schema coverage handles a separate comparison. They do not have identical
coverage: artifact health excludes catalog sources, while schema comparison can
include source lineage. The inspected schema approval predicate does not consult
artifact health.

The schema classifier keeps one-sided IDs internally, but its serialized coverage
payload omits them. Whether a later diff-frame producer reports those differences
was not inspected. A complete coverage label plus an empty frame therefore does
not, from this inspection alone, prove end-to-end deletion protection.

| Proposed case | Relevant layer | Boundary to preserve |
|---|---|---|
| Empty selection | Schema coverage | Unknown, not verified no-change |
| Confirmed deletion with independently complete inputs | One-sided classification and diff producer | Classifier records it; downstream frame behavior is unknown |
| Missing record during incomplete acquisition | Acquisition evidence | Do not infer deletion |
| Mixed checked and unchecked nodes | Schema coverage | Partial |
| Orphan IDs | Artifact health | Informational upstream; local proposal withholds no-change pending classification |
| Duplicate IDs in a list | Pre-mapping identity validation | Neither classifier detects duplicates already collapsed into mappings |

StaleToast already checks active count targets, paper/appraisal identity agreement,
duplicates, historical preservation and pool links. A removed batch row under
unchanged declared targets is expected to fail those existing checks. The validator
does not authenticate an upstream page fetch or define a general empty-diff API.
The proposed coverage example must compare against these actual checks rather
than imply that incomplete intake always passes today.

Use a separately versioned, owner-approved expected-ID fixture. Deriving the
expected set from the same acquisition would make the comparison circular.
Classify genuine deletion separately from missing acquisition, check duplicates
before mapping, and retain passed, failed and unknown outcomes. These are proposed
acceptance rules, not executed results or demonstrated incremental benefit.

Upstream tests were read, not run. The creation and freshness of `catalog_status`
and complete caller propagation remain uninspected. Prior Apache-2.0 rights
assessment is retained; no dependency or full runtime adoption is proposed.

## What can advance

Publish the bounded source analysis only after its independent corrections clear.
A practical fixture belongs in Breadcrumbs through its own implementation and
review path. Neither this document nor a review verdict installs software,
changes a consumer pin, allocates an identity or creates another chart edition.

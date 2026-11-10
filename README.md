# StaleToast

Research worth reading. Repositories worth inspecting.

StaleToast owns the public collaborative-intelligence research and repository
catalogs, source appraisals, daily discovery pool, editorial rankings and dated
Hot100 chart history. [Open the site](https://the-825.github.io/staletoast/).

[Breadcrumbs](https://the-825.github.io/breadcrumbs/workflows.html) owns practical
workflow guides, reusable prompts and implementation templates. It consumes
versioned StaleToast catalog exports and cites stable source IDs.

## Build and check

The [report-validity and coverage review](docs/staletoast-appraisal-resolution-2026-11-08.md) resolves C-004 and R-900 source questions while keeping proposed checks separate from executed results and adoption.

The [METR and Agent Beacon resolution](docs/staletoast-appraisal-resolution-2026-11-07.md) records a corrected research access checklist and version-matched collector findings. Independent review accepted the corrected appraisal in PR #17; catalog grades and chart eligibility are unchanged.

The [November 3 source review batch](docs/staletoast-system-fit-appraisals-2026-11-03.md)
adds two paper assessments, two repository assessments and the reviewed Agent Beacon
follow-up. It proposes one synthetic outcome-evidence audit and retains the rest
in the pool. Source assessments do not change chart eligibility or authorize adoption.

The [next-update source review](docs/staletoast-system-fit-appraisals-2026-11-01.md)
appraises six research articles and twelve repositories against the public
Breadcrumbs kit. It preserves all remaining leads in the pool and records
system-fit routing for all 1,083 retained expansion sources. Routing is not a
full appraisal, and review proposals do not change the live charts or authorize
software adoption. Six papers and ten repositories are proposed; two inspected
repositories remain in the pool. Check the package with
`python scripts/validate_system_fit_appraisals.py`. It compares the proposal to
its pinned published revision, so later pool, history, hold and code updates do
not trip it; it needs full git history. See the
[PR pipeline failure investigation](docs/pr-pipeline-failure-investigation.md).

The [November 1 expansion](docs/staletoast-expansion-2026-11-01.md) brings the source collection to 500 research records and 1,000 repository records. New automated abstract and README relevance screens await human appraisal; they are distinct from mechanism reviews and Hot100 selections. Existing analyses and chart history are preserved. Run `python scripts/validate_corpus_expansion.py` to check the batch, source identities, count targets and history preservation.

Python 3.9 or newer, standard library only. No upstream package installation or
provider call is required.

```sh
python site/build_priorities.py --check
python site/build_catalogs.py
python site/build_reader_guide.py
python site/build_reader_guide.py --check
python site/build_discovery.py
python site/build_discovery.py --check
python site/build_export.py
python -m unittest discover -s site -p 'test_*.py'
python scripts/repository_landscape.py --check
python scripts/repository_review_promotions.py --check
python scripts/repository_triage.py --check
```

For a reviewed new intake, rebuild priorities with `--write --date YYYY-MM-DD`,
then freeze a new chart with `python site/build_discovery.py --edition-date
YYYY-MM-DD`. For the weekly offline preparation of both steps with a dated
review receipt, see [weekly Hot100 preparation](docs/weekly-hot100.md).
Existing dated editions cannot be overwritten. Preserve source
versions, review limits, contrary evidence and stable IDs. A chart position
guides attention; it does not certify findings or grant adoption authority.

The daily scout discovers up to 50 metadata leads per category, screens at most
five primary sources per category, and prioritizes one or two deeper appraisals
from the existing pool. Add at most two research articles and two repositories
per day only when quality supports it.
Zero additions is valid. Retain unselected leads in the pool. Each month,
rank the strongest ten eligible records per category and propose the top three
for consideration. Sources outside the current Hot100 can return to the pool
under their original identity. Preserve original analysis and dated rankings.
See [intake and pool policy](docs/staletoast-intake-policy.md).

## History and export

The proposed visitor reading paths in `docs/staletoast-reader-selections.json`
are separate from the internal appraisal queue and frozen charts. Build their
derived `site/data/reader-guide.json` with the reader-guide command above. Each
selection retains the existing finding, evidence depth and limitation plus an
editorial reason. Missing sources and unpromoted papers fail the build. This is
not a quality score, new evidence review or operational recommendation. The
guide is separate from the versioned catalog export. Commit its reviewed inputs
before building, then use `python site/build_reader_guide.py --freeze` to retain
an immutable `exports/reader-guide/<source-revision>.json`. Consumers must pin
that exact revision and the frozen file's SHA-256 digest. Never consume a mutable
working copy as an approved guide. Its website integration and review status
remain separate from source generation.
Input hashes use UTF-8 with LF line endings; the frozen output digest binds the
actual exported file bytes. An absent structured counterevidence list does not
mean no contrary evidence exists: findings and limitations remain authoritative.

The initial import preserves selected-path Git history from Breadcrumbs.
[Migration provenance](docs/migration-provenance.json) records the original
repository, exact source revision and selected paths. Historical source and
chart files remain byte-for-byte unchanged; earlier source links retain their
original provenance.

`data/catalog-export.json` is a schema-versioned, evidence-only export of the
research, repository, claim and chart data, bound to the published Git revision.
Consumers pin its revision and SHA-256 digest before use. A failed integrity or
freshness check must fail the build rather than substitute stale local data.

After committing reviewed catalog inputs, run `python site/build_export.py
--freeze` and commit the new immutable `exports/<catalog-revision>.json` snapshot
in the same PR. Publication retains all earlier snapshots at
`exports/<catalog-revision>.json`, so a consumer's existing pin stays available
after a later edition publishes. The export revision covers catalog sources
and generators; a website-only change does not invent a new catalog revision.

A frozen revision is the PR-branch commit it was frozen on, which a squash merge
leaves off `main`. The `Tag pinned revisions` workflow adds a permanent
`frozen/<revision>` tag for every snapshot and the current pin after each merge,
so a pin stays fetchable once its branch is gone. Fetch tags (`git fetch --tags
origin`) before verifying a pin locally. Do not delete a merged branch that holds
a frozen revision until its tag exists. Both freeze commands refuse uncommitted
or untracked inputs.

Public and synthetic content only. MIT license, with upstream attribution kept
at the source. No private or production records, automatic source execution,
contact with authors, or implied consumer adoption.

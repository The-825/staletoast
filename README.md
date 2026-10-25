# StaleToast

Research worth reading. Repositories worth inspecting.

StaleToast owns the public collaborative-intelligence research and repository
catalogs, source appraisals, daily discovery pool, editorial rankings and dated
Hot100 chart history. [Open the site](https://the-825.github.io/staletoast/).

[Breadcrumbs](https://the-825.github.io/breadcrumbs/workflows.html) owns practical
workflow guides, reusable prompts and implementation templates. It consumes
versioned StaleToast catalog exports and cites stable source IDs.

## Build and check

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
YYYY-MM-DD`. Existing dated editions cannot be overwritten. Preserve source
versions, review limits, contrary evidence and stable IDs. A chart position
guides attention; it does not certify findings or grant adoption authority.

The daily scout screens five candidates per category and adds at most one or
two research articles and one or two repositories when quality supports it.
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
guide is not yet part of the versioned catalog export or live website; consumer
integration must preserve its source hashes and review status.

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

Public and synthetic content only. MIT license, with upstream attribution kept
at the source. No private or production records, automatic source execution,
contact with authors, or implied consumer adoption.

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

The daily scout targets one to two research articles and one to two public
repositories at defensible review depth. Retain unselected leads in the
next-round pool. Count each canonical identity once and document shortfalls.

## History and export

The initial import preserves selected-path Git history from Breadcrumbs.
[Migration provenance](docs/migration-provenance.json) records the original
repository, exact source revision and selected paths. Historical source and
chart files remain byte-for-byte unchanged; earlier source links retain their
original provenance.

`data/catalog-export.json` is a schema-versioned, evidence-only export of the
research, repository, claim and chart data, bound to the published Git revision.
Consumers pin its revision and SHA-256 digest before use. A failed integrity or
freshness check must fail the build rather than substitute stale local data.

Public and synthetic content only. MIT license, with upstream attribution kept
at the source. No private or production records, automatic source execution,
contact with authors, or implied consumer adoption.

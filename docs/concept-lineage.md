# Concept lineage index

A read-only index that joins this repository's public source records to curated source-to-concept assertions. It is separate from the four-catalog export, changes no ranking, appraisal or chart, and grants no authority. Labels describe supplied evidence only; shape and hash consistency do not authenticate a reviewer or certify safe content.

## Files

| File | Role |
| --- | --- |
| `site/concept_lineage_runtime.py` | Raw-byte copy of the portable engine from the Breadcrumbs concept lineage kit. Its SHA-256 is pinned in the builder; a mismatch stops the build. |
| `site/build_concept_lineage.py` | Builder. Joins the source ledger with the reviewed mappings, validates the packet, writes the projection and input manifest, and writes or checks the pin. |
| `docs/staletoast-concept-links.json` | Reviewed mappings (`concept-lineage-mappings/1`). All five arrays are empty; no source-to-concept relation or consumer use is asserted yet. |
| `site/data/concept-lineage.json` | Generated projection (`concept-lineage-projection/1`). |
| `site/data/concept-lineage-input-manifest.json` | Generated input manifest (`concept-lineage-input/1`) naming every input file, its digest and its commit. |
| `concept-lineage-pin.json` | Standalone pin (`concept-lineage-pin/1`) naming the earlier commit that holds the projection. |

The generated files under `site/data/` are tracked by an explicit add even though that directory is otherwise ignored.

## Source mapping

Each of the 335 repository records in `docs/collaborative-intelligence-repository-landscape.json` becomes one source row: `id` is `The-825/staletoast:repository:<record id>`, `record_id` and `title` come from the record and its `repository` field, `url` is copied, `upstream_version` is the exact Git `upstream_revision`, `evidence_depth` is copied unchanged and each alias key becomes a qualified alias. Scientific, license and lifecycle detail stays in the owning ledger. Research, candidate and pool kinds are accepted by the engine but are not bulk imported.

## Commit order

Three ordered commits follow the catalog base so nothing references itself: the builder, runtime copy, mappings and attributes; then the generated projection and manifest; then the pin that names the projection commit. Revisions are explicit builder arguments checked against Git blob bytes, never read from mutable HEAD. Command-line flags take raw 40-hex commits; every persisted revision (source `catalog_revision`, manifest and pin catalog/builder/supplier/projection revisions) is a tagged `{kind: "git", value, reason: null}` version. The mapping file, input manifest and pin are checked with the engine's shared exact-envelope validators, so unknown keys, other schema versions and string revisions fail. A later correction adds a new builder, projection and pin commit in the same order; earlier commits stay in history.

```
python site/build_concept_lineage.py build --catalog-revision <sha> --builder-revision <sha> --supplier-revision <sha> --input-revision <sha> --check
python site/build_concept_lineage.py pin --projection-revision <sha> --check
python -m unittest discover -s site -p 'test_concept_lineage.py'
```

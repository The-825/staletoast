# November 1 source collection expansion

This intake grows the searchable collection to 500 research records and 1,000 repository records. It adds 377 automated primary-abstract relevance screens and 665 automated, commit-pinned README relevance screens. The earlier 123 research records, 335 repository records and dated chart history retain their original evidence and analysis.

Release review held two papers and 39 repositories outside the active collection and added distinct replacement identities. All held source rows, earlier analysis and pool links remain in the historical intake. The ledgers therefore retain 502 research and 1,039 repository records, while the visitor collection contains 500 and 1,000 active records. The [held-source decisions](staletoast-source-dispositions.json) record reasons and replacement IDs. Holding a source is a scope or appraisal decision, not a claim that the source is malicious or its findings are false.

Automated research is unranked and has no directness or horizon grade. A separate Unappraised filter finds it. Explicit `appraisal_state` fields and [export schema 2.0](../catalog-contract.json) distinguish automatic intake from existing source screens. Frozen 1.0 consumer exports remain available unchanged; an existing consumer must deliberately validate the new schema before changing its pin.

These additions identify relevant material to appraise. They are not 1,042 new expert reviews, validated findings, quality ratings or Hot100 selections. All new repository mechanism observations remain unknown. Research directness, study design and observation horizon remain unappraised. Topic matches route attention; they do not establish support for a claim. GitHub stars help discover candidates and remain dated popularity observations, not quality scores.

## What was collected

Research discovery uses versioned primary arXiv abstracts across human-AI collaboration, agent evaluation, agent memory, multi-agent systems, retrieval and agent safety. Repository discovery uses public GitHub topic and description searches across agent frameworks, evaluation, retrieval, memory, workflow automation, coding tools, security, observability and data tools. This is a purposive discovery sample, not comprehensive coverage or a representative research review. Its arXiv-only research coverage and GitHub search/popularity ordering introduce selection bias.

Candidates require a usable abstract or README and a documented topic match. Repository forks, archived or private repositories, missing primary text and duplicate identities are excluded. Research deduplication normalizes arXiv versions, primary URLs and titles; repository deduplication checks case-insensitive canonical names and existing aliases. Different publications describing the same study can still require human evidence-family reconciliation. No source code or source-provided command was run.

The [machine-readable batch](staletoast-expansion-2026-11-01.json) retains stable IDs, source versions, authors or repository identity, observed dates, screening method, retrieval digests, query provenance, exclusion counts and source-to-pool links. README blob IDs are checked against the exact default-branch commit tree. Full collection responses are retained with the source custodian for reproducibility; the public batch does not copy full abstracts or READMEs. Source screening does not establish authorship authenticity or independent truth.

## What happens next

All new sources stay in the [retained pool](staletoast-next-round-pool.json) for human appraisal. Existing pool records and earlier assessments remain intact. An existing pool identity is reused when the source was already retained. No source is silently selected for the Hot100, adopted by a consumer or cleared for code reuse. License names reported by GitHub metadata are not a substitute for inspecting license text and dependency terms.

This is a one-time source-screen expansion authorized for November 1. It does not raise the normal daily curated-selection allowance. Continue selecting at most one or two quality additions per category when appraisal supports them. Retain unselected sources; monthly reconsideration can compare the strongest ten eligible sources per category and propose the top three. Preserve the original ranking and analysis when a source returns from outside the Hot100, recheck source changes and record the new judgment alongside history.

The current collection count is displayed separately from each frozen chart's historical archive count. Existing dated charts are not rewritten. A new edition or publication remains a separate reviewed action.

## Reproduce and check

Use Python 3.9 or newer, standard library only:

```sh
python scripts/validate_corpus_expansion.py
python scripts/repository_landscape.py --check
python scripts/repository_review_promotions.py --check
python scripts/repository_triage.py --check
python site/build_priorities.py --write --date 2026-11-01
python site/build_priorities.py --check
python site/build_catalogs.py
python site/build_reader_guide.py
python site/build_reader_guide.py --check
python site/build_discovery.py
python site/build_discovery.py --check
python -m unittest discover -s site -p 'test_*.py'
```

The complete export check also requires the separately reviewed, committed and frozen catalog export described in the [README](../README.md). Do not bypass that guard to publish a working copy. New catalog input evidence must pass source review before its immutable export is frozen.

Original StaleToast screening records use the repository's MIT license. Upstream papers, README text, code and dependencies retain their own rights and attribution requirements.

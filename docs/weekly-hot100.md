# Weekly Hot100 preparation

**Ships as:** `scripts/weekly_hot100.py`, tested by `site/test_weekly_hot100.py`. Python 3.9 or newer, standard library only. It runs offline. It does not call a network, provider or GitHub, install anything, or execute source from a repository it lists.

The weekly schedule owner is the existing B003 native Codex heartbeat. This command adds no GitHub Actions cron, no paid model route and no new worker. Running it is a preparation step, not a release.

## What it does

Given an explicit date, it reuses the approved editorial method and adds no ranking of its own:

1. Recomputes the current appraisal priorities with `build_priorities.build` and `build_priorities.render`.
2. Builds the new dated chart edition with `build_discovery.make_edition`, against the latest earlier frozen edition.
3. Records a weekly review receipt at `docs/staletoast-weekly-review/YYYY-MM-DD.json`.

The date is required. Supply the local calendar date in America/Los_Angeles as `YYYY-MM-DD`. The command never reads the machine clock or timezone, so the same date always yields the same files.

## Run it

```sh
python scripts/weekly_hot100.py --date 2026-11-08
python scripts/weekly_hot100.py --date 2026-11-08 --write
python -m unittest discover -s site -p 'test_weekly_hot100.py'
```

The first form is the default dry run. It validates everything, lists each file as `create`, `update` or `unchanged`, and writes nothing. `--write` writes only these files:

- `docs/staletoast-chart-history/YYYY-MM-DD.json`, the new edition
- `docs/staletoast-weekly-review/YYYY-MM-DD.json`, the receipt
- `docs/staletoast-appraisal-priorities.json` and `.md`, the current priorities

`--root` points the command at another checkout, which the tests use with temporary roots. A refusal prints a reason and exits 2.

## Preview the candidate ranking rubric

Run the comparison before considering a change to the published method.

```sh
python scripts/weekly_hot100.py --date 2026-11-23 --compare-rubric
```

The date must follow the latest frozen edition. The comparison uses the same current ledgers, held dispositions and eligibility rules for both methods. The JSON includes source hashes, evidence basis, changes in chart membership, prior-method positions and ties outside the cutoff. It cannot be combined with `--write`.

The chart guides what to read or appraise against the named question. The active registry already records the claim gap and source review. The candidate uses those fields as follows.

- **Question fit first.** Keep the published order of named claim gaps. A record uses its first applicable gap. No credit for tagging more claims.
- **Research.** Within the same gap, use existing directness first, then prefer explicitly recorded selected-full-text review. Historical records whose review depth lacks that marker stay tied with other records of the same directness. Study horizon remains visible as context because longer observation does not always provide a better test of the claim.
- **Repositories.** Within the same gap, use the existing observation for the mechanism that bears on it. For example, use recorded authority evidence for CI-007 and recorded trace recovery for CI-006. Explicit coverage sorts before partial coverage. Unobserved, outside-scope, unknown and unmapped records receive no positive preference. Their recorded distinctions stay visible. Lifecycle and popularity remain context. A README observation cannot establish runtime behavior.
- **Editorial review at the cutoff.** Equal inputs remain tied. Stable IDs make the preview repeatable. When a tie crosses the cutoff, review the listed alternatives for specific decision value, contrary evidence and known shared evidence families. Do not assume unknown families are independent. Record why an alternative would change a decision. Preserve holds and record unresolved ties explicitly.

Use a same-input comparison to separate changes due to the rubric from changes due to new sources or corrections. Review entrants and removals, material moves, and ties across the cutoff before approving a version change. The versioned weekly scoring method below supersedes this diagnostic comparison for new editions.

## The receipt

The receipt records:

- the operator date, its timezone and how the date was obtained
- the prior and current edition dates, paths and SHA-256 digests
- the exact source hashes that `build_priorities.build` bound into the priorities (research ledger, appraisals, repository landscape, dispositions and expansion batch), using the repository's UTF-8 with LF convention
- eligible, archive, chart and off-chart counts for both charts, prior and current
- per-chart movements: new, re-entering, moved up, moved down, dropped, and the IDs whose position did not change. `ordering_unchanged` states plainly when a chart order is identical to the prior week
- the earliest and latest source observation dates carried in the edition and how many are unknown
- the review-ready appraisals found in published `docs/staletoast-system-fit-appraisals-*.json` sidecars, with their digests
- an explicit `primary_source_recheck` of `performed: false`, plus the limits, what the command did, what it did not do and the follow-up steps

It holds no timestamp, so an identical rerun produces identical bytes.

## Rules the command enforces

- **No invented evidence.** Positions are a display order of existing routing groups. No score, grade or finding is created. Ties stay ties.
- **Automated screens stay excluded.** The edition builder already excludes them. The command also refuses to continue if one reaches a chart, and the receipt counts them as zero in the edition.
- **Review-ready is not promotion.** Sidecar records in the review-ready state are listed for editorial review. They do not change `appraisal_state`, `evidence_depth`, mechanisms or ranking. A later catalog promotion follows its own source contract.
- **No primary-source recheck.** The command reads local ledgers only. Earlier observation dates and unknowns are carried forward as they are. Do not describe an old finding as fresh because a weekly receipt exists. A recheck is a separate, owner-run step.
- **History is preserved.** Existing editions, receipts and exports are never rewritten. The only existing files it can change are the current priorities and their view, which the existing builder also regenerates.
- **Same date, same bytes.** Rerunning a date whose outputs already match is a no-op. If an edition or receipt for that date exists and differs, the run fails and changes nothing.
- **Older dates cannot overwrite.** A date earlier than the latest frozen edition, an existing receipt or the current priorities date is refused.
- **No partial writes.** Every payload is built and checked before the first write. Files are staged beside their targets and swapped in together. If a swap fails, earlier bytes are restored and new files and folders are removed.

## After the command

The command does not commit, freeze an export or push. A person or the Codex owner continues:

1. Review the diff, then commit the source files, receipt, priorities and edition on a `claude/<slug>` branch. The export step needs committed inputs.
2. Run the normal catalog and discovery builds: `python site/build_catalogs.py`, `python site/build_reader_guide.py` and `python site/build_discovery.py`. Commit the generated data if it changed.
3. Run `python site/build_export.py --freeze`. It writes a new `exports/<catalog-revision>.json` and updates the pin. Earlier snapshots stay.
4. Commit the export and pin as a second commit.
5. Run the full README checks, including `python site/build_priorities.py --check`, `python site/build_discovery.py --check`, `python site/build_export.py` and the full `unittest` discovery.
6. Open the PR with Summary, Test plan and What's NOT in scope. The installed merge gate decides the merge. A green receipt grants no merge, publication or adoption authority.
7. After the gate merges, check the live site and the published export.

## Design limits

- The receipt reports counts and movements from the edition builder. It does not judge whether a movement is meaningful.
- The date is trusted as supplied. A mistyped future date freezes a future edition, and the next honest date will then be refused as older. Check the date before `--write`.
- Sidecar discovery uses the `staletoast-system-fit-appraisals-*.json` file name pattern. A sidecar with another name is not listed.
- Output files use LF line endings. A checkout with CRLF conversion still compares equal because comparison reads text.

## Collaborative intelligence scoring from November 23, 2026

The standard weekly command scores both charts with collaborative-intelligence-v1. Historical editions retain their recorded method. The older comparison switch above replays the two earlier editorial orderings for diagnostic purposes.

| Dimension | Weight | Evidence to consider |
| --- | ---: | --- |
| Human goals and direction | 15 | People express constraints, define success, and redirect work. |
| Delegated authority and consent | 15 | Participants know who can commit, approve, intervene or revoke. |
| Coordination and orchestration | 20 | Contributions change another participant's action. Handoffs and conflicts can be resolved. |
| Idea into action | 15 | Trace a decision or design change into real use or a verified production change. |
| Outcomes and learning | 15 | Compare results and effort with a credible alternative. Include failures and lessons. |
| Strength of evidence | 15 | Inspect methods, comparisons, pinned code or tests appropriate to the specific claim. |
| Distinct contribution and applicability | 5 | Identify added value, intended beneficiary and an observable local check. |

Prepare the dated JSON under docs/staletoast-scorecards using the November 23 card as the file format. Earlier dated scorecards carry forward automatically to later editions while their `source_revision` still matches the repository `snapshot_commit` and the record is not held; if a repository's pinned `snapshot_commit` moves past `source_revision`, the card becomes `revision_stale` and returns to provisional status until reappraised. Each known dimension needs a rating and its evidence basis. Use 0 for checked absence or out-of-scope with the reason, 1 for a described intention or mechanism, 2 for a worked example, 3 for a demonstrated contribution with a known limit, and 4 for evidence explaining the difference against an alternative or failure case. Leave unknowns null. Optional `finding_direction` (`positive`, `conditional`, `null-or-negative` or `design-only`) records the direction of an empirical comparison so rigorous negative or null studies receive full `outcomes` and `evidence` ratings without conflating evidentiary value with positive synergy. Record relationship patterns, the `evidence_family` identifier and the `source_revision`. Cite a public HTTPS source and use the verified full Git commit or sha256 digest of the cited material. Cards without a revision or family stay provisional. Participant count carries zero weight. Cite linked artifacts from the same family together.

Points equal weight times rating divided by four. The chart ranks complete cards by total, evidence, outcomes and contribution in order. Identical values share a rank group, with IDs providing display order. Each entry exposes its strongest contribution dimensions and the evidence behind them, and `site/build_catalogs.py` publishes the multi-dimensional scorecards to `site/data/scorecards.json` without collapsing profiles into a single verdict. Provisional rows show established and unresolved points, and the weekly receipt records `rubric_coverage` per chart. A dry run reports coverage. Publication requires enough completed cards to fill the available chart places.

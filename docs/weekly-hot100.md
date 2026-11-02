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

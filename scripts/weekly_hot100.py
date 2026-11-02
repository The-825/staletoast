"""Prepare one offline weekly Hot100 review from the existing editorial method.

Standard library only. No network, provider, git or upstream execution. The command
reuses build_priorities.build and build_discovery.make_edition, so it adds no second
ranking system. It never commits, freezes an export or pushes. Default is a dry run.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import date
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "site"))

import build_discovery as discovery  # noqa: E402
import build_priorities as priorities  # noqa: E402
from intake_state import AUTOMATED, IntakeState  # noqa: E402

TIMEZONE = "America/Los_Angeles"
REVIEW_READY = "ready-for-next-edition-review"
CHARTS = (("research", "research"), ("repositories", "repository"))
SOURCE_HASH_SUFFIX = "_source_sha256"


def digest(text):
    return sha256(text.encode("utf-8")).hexdigest()


def dump(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def check_date(value):
    try:
        valid = date.fromisoformat(value).isoformat() == value
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError(f"--date must be an ISO YYYY-MM-DD local {TIMEZONE} date supplied by the operator")
    return value


def count_movements(prior, current, chart):
    old = {row["id"]: row for row in prior["charts"][chart]["entries"]}
    rows = current["charts"][chart]["entries"]
    kept = {row["id"] for row in rows}
    moved = [dict(id=row["id"], previous_position=row["previous_position"], position=row["position"],
                  movement=row["movement"], entry_state=row["entry_state"])
             for row in rows if row["id"] not in old or row["movement"] != 0]
    states = [row["entry_state"] for row in rows]
    return dict(
        ordering_unchanged=[row["id"] for row in prior["charts"][chart]["entries"]] == [row["id"] for row in rows],
        new=states.count("new"), reentry=states.count("reentry"),
        moved_up=sum(1 for row in rows if (row["movement"] or 0) > 0),
        moved_down=sum(1 for row in rows if (row["movement"] or 0) < 0),
        unchanged_position_ids=[row["id"] for row in rows if row["id"] in old and row["movement"] == 0],
        changed=moved,
        dropped=[dict(id=identity, previous_position=row["position"]) for identity, row in old.items() if identity not in kept])


def count_chart(prior, current, chart):
    before, after = prior["charts"][chart], current["charts"][chart]
    return dict(prior_eligible=before["eligible_count"], prior_archive=before["archive_count"],
                eligible=after["eligible_count"], archive=after["archive_count"],
                chart_entries=len(after["entries"]), off_chart=len(after["off_chart_ids"]),
                cutoff_tied_outside_chart=after["cutoff_tied_outside_chart"])


def observation_dates(edition):
    rows = edition["charts"]["repositories"]["entries"]
    result = {}
    for field in ("stars_observed_date", "reviewed_date"):
        values = [row.get(field) for row in rows]
        known = sorted(value for value in values if value)
        result[field] = dict(earliest=known[0] if known else None, latest=known[-1] if known else None,
                             unknown=len(values) - len(known))
    result["research"] = "not carried in chart entries; see the owning ledger and appraisal rows"
    return result


def sidecar_review(docs, payload, edition):
    known = {"research": {row["id"]: row for row in payload["research"]},
             "repository": {row["id"]: row for row in payload["repositories"]}}
    charted = {kind: {row["id"] for row in edition["charts"][chart]["entries"]} for chart, kind in CHARTS}
    sidecars, ready, latest, other = [], [], {}, 0
    held = IntakeState(docs)
    dated = []
    for path in docs.glob("staletoast-system-fit-appraisals-*.json"):
        try:
            assessment_date = check_date(path.stem[-10:])
        except ValueError as error:
            raise ValueError(f"{path.name}: invalid assessment filename date") from error
        dated.append((assessment_date, path))
    for assessment_date, path in sorted(dated, key=lambda row: (row[0], row[1].name)):
        if assessment_date > edition["edition_date"]:
            continue
        text = path.read_text(encoding="utf-8")
        sidecars.append(dict(path=f"docs/{path.name}", sha256=digest(text)))
        seen = set()
        for record in json.loads(text).get("records", []):
            if not isinstance(record, dict):
                raise ValueError(f"{path.name}: assessment record must be an object")
            kind, identity = record.get("kind"), record.get("id")
            if kind not in known or not isinstance(identity, str) or (kind, identity) in seen:
                raise ValueError(f"{path.name}: sidecar record has an unknown kind or missing or duplicate ID: {identity}")
            seen.add((kind, identity))
            prior = latest.get((kind, identity))
            if prior and prior[2] == assessment_date:
                raise ValueError(f"{path.name}: conflicting same-date assessments for {identity}")
            latest[kind, identity] = (record, path.name, assessment_date)
    for (kind, identity), (record, source_path, assessment_date) in sorted(latest.items()):
        if record.get("review_state") != REVIEW_READY:
            other += 1
            continue
        projected = known[kind].get(identity)
        ready.append(dict(id=identity, kind=kind, review_state=REVIEW_READY,
                          assessment_path=f"docs/{source_path}", assessment_date=assessment_date,
                          appraisal_state="held (excluded from projection)" if held.is_held(kind, identity) else projected["appraisal_state"] if projected else "not in current projection",
                          excluded_by_hold=held.is_held(kind, identity),
                          in_current_edition=identity in charted[kind],
                          catalog_promotion="none; review-ready is not a catalog promotion"))
    return dict(sidecars=sidecars, review_ready=ready, other_state_records=other)


def build_receipt(review_date, prior, edition, edition_text, prior_text, payload, docs):
    state = IntakeState(docs)
    automated_papers = sum(bool(row.get("automated_screen")) for row in payload["research"])
    automated_repos = sum(row["appraisal_state"] == AUTOMATED for row in payload["repositories"])
    charted = {row["id"] for chart, _ in CHARTS for row in edition["charts"][chart]["entries"]}
    if charted & ({row["id"] for row in payload["research"] if row.get("automated_screen")} |
                  {row["id"] for row in payload["repositories"] if row["appraisal_state"] == AUTOMATED}):
        raise ValueError("an automated screen reached the chart; refusing to prepare the edition")
    return dict(
        schema_version=1,
        kind="weekly Hot100 offline preparation receipt, not a findings ledger and not a catalog promotion",
        review_date=review_date, review_timezone=TIMEZONE,
        date_basis="operator-supplied local calendar date; the machine clock and timezone were not consulted",
        prior_edition=dict(edition_date=prior["edition_date"], path=f"docs/staletoast-chart-history/{prior['edition_date']}.json",
                           sha256=digest(prior_text)),
        current_edition=dict(edition_date=review_date, method_version=edition["method_version"],
                             path=f"docs/staletoast-chart-history/{review_date}.json", sha256=digest(edition_text)),
        appraisal_priorities=dict(path="docs/staletoast-appraisal-priorities.json", date=payload["date"],
                                  research_records=len(payload["research"]), repository_records=len(payload["repositories"])),
        recorded_source_hashes={key: value for key, value in payload.items() if key.endswith(SOURCE_HASH_SUFFIX)},
        source_hash_encoding=payload["source_hash_encoding"],
        counts={chart: count_chart(prior, edition, chart) for chart, _ in CHARTS},
        held_exclusions=dict(
            retained_repository_records=len(json.loads((docs / "collaborative-intelligence-repository-landscape.json").read_text(encoding="utf-8"))["repositories"]),
            retained_research_records=len(payload["research"]) + len(state.held_ids("research")),
            research_count=len(state.held_ids("research")), repository_count=len(state.held_ids("repository")),
            research_ids=sorted(state.held_ids("research")),
            repository_ids=sorted(state.held_ids("repository")),
            meaning="Retained ledger records are preserved; held identities are excluded from the active projection and charts."),
        automated_screens=dict(research_in_archive=automated_papers, repositories_in_archive=automated_repos,
                               in_current_edition=0, rule="excluded from both charts and unchanged by this review"),
        movements={chart: count_movements(prior, edition, chart) for chart, _ in CHARTS},
        source_observation_dates=observation_dates(edition),
        sidecar_review=sidecar_review(docs, payload, edition),
        primary_source_recheck=dict(performed=False, statement="Primary sources were not rechecked by this offline command. Earlier observation dates and unknowns are carried forward, not refreshed."),
        limits=[
            "Offline run: no primary source, repository, provider or other remote service was contacted.",
            "Positions are a display order of editorial routing groups, not scores. No score, grade or finding was created and tied groups remain ties.",
            "Review-ready sidecar appraisals are proposals for editorial review. They do not change appraisal_state, evidence_depth, mechanisms or ranking.",
            "This receipt does not validate findings, authorize adoption, execute source code, commit, freeze an export or release anything."],
        performed=["recomputed appraisal priorities with build_priorities.build",
                   "built the dated edition with build_discovery.make_edition",
                   "recorded this receipt"],
        not_performed=["primary source recheck", "git commit or push", "catalog and chart data build", "export freeze", "PR gate", "live check"],
        follow_up=["commit the source files, receipt, priorities and edition",
                   "run site/build_catalogs.py, site/build_reader_guide.py and site/build_discovery.py, then commit",
                   "run site/build_export.py --freeze and commit the new export in a second commit",
                   "run the README checks, open a PR and let the merge gate decide, then check the live site"])


def plan(root, review_date):
    """Validate everything and return the proposed writes. Touches nothing on disk."""
    review_date = check_date(review_date)
    docs = Path(root) / "docs"
    history, reviews = docs / "staletoast-chart-history", docs / "staletoast-weekly-review"
    editions = discovery.editions(history)
    if not editions:
        raise ValueError("no frozen chart edition to compare against")
    if review_date < editions[-1]["edition_date"]:
        raise ValueError(f"{review_date} is older than the latest frozen edition {editions[-1]['edition_date']}; older dates cannot overwrite")
    if any(path.stem > review_date for path in reviews.glob("*.json")):
        raise ValueError("a later weekly review receipt exists; older dates cannot overwrite")
    earlier = [row for row in editions if row["edition_date"] < review_date]
    if not earlier:
        raise ValueError("no frozen edition precedes the review date")
    priorities_path, view_path = docs / "staletoast-appraisal-priorities.json", docs / "staletoast-appraisal-priorities.md"
    current = json.loads(priorities_path.read_text(encoding="utf-8")) if priorities_path.exists() else None
    if current and review_date < current["date"]:
        raise ValueError("appraisal priorities already carry a later date; older dates cannot overwrite")
    payload = priorities.build(docs, review_date)
    landscape = discovery.read(docs / "collaborative-intelligence-repository-landscape.json")
    edition = discovery.make_edition(review_date, payload, landscape, earlier,
                                     IntakeState(docs).held_ids('repository'))
    edition["source_hashes"] = {field: payload[field] for field in priorities.SOURCES}
    edition_path, edition_text = history / f"{review_date}.json", dump(edition)
    prior = earlier[-1]
    prior_text = (history / f"{prior['edition_date']}.json").read_text(encoding="utf-8")
    receipt_path = reviews / f"{review_date}.json"

    corrections_path = docs / "staletoast-chart-link-corrections.json"
    corrections = discovery.read(corrections_path)["records"] if corrections_path.exists() else []
    if edition_path.exists():
        same = discovery.correct_source_links(discovery.read(edition_path), corrections) == discovery.correct_source_links(edition, corrections)
        if not same:
            raise ValueError("a frozen chart edition cannot be overwritten")
        edition_text = edition_path.read_text(encoding="utf-8")
    receipt_text = dump(build_receipt(review_date, prior, edition, edition_text, prior_text, payload, docs))
    if receipt_path.exists() and receipt_path.read_text(encoding="utf-8") != receipt_text:
        raise ValueError("a different weekly review receipt already exists for this date")
    view = priorities.render(payload)
    changes = [(edition_path, edition_text, "unchanged" if edition_path.exists() else "create"),
               (receipt_path, receipt_text, "unchanged" if receipt_path.exists() else "create")]
    for path, text, same in ((priorities_path, dump(payload), current == payload),
                             (view_path, view, view_path.exists() and view_path.read_text(encoding="utf-8") == view)):
        changes.append((path, text, "unchanged" if same else ("update" if path.exists() else "create")))
    return dict(review_date=review_date, changes=changes, receipt=json.loads(receipt_text))


def apply(changes):
    """Stage every file, then swap them in. A failure restores earlier bytes and removes new files."""
    pending = [(path, text) for path, text, action in changes if action != "unchanged"]
    backups, created, staged = {}, [], []
    try:
        for path, _ in pending:
            if not path.parent.exists():
                path.parent.mkdir(parents=True)
                created.append(path.parent)
        for path, text in pending:
            with tempfile.NamedTemporaryFile(mode="wb", prefix="." + path.name + ".weekly-",
                                             suffix=".weekly-tmp", dir=path.parent, delete=False) as handle:
                staged.append((Path(handle.name), path))
                handle.write(text.encode("utf-8"))
        for temp, path in staged:
            backups[path] = path.read_bytes() if path.exists() else None
            os.replace(temp, path)
    except BaseException:
        for path, old in backups.items():
            if old is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(old)
        for temp, _ in staged:
            temp.unlink(missing_ok=True)
        for directory in reversed(created):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise


def run(root, review_date, write=False):
    proposal = plan(root, review_date)
    if write:
        apply(proposal["changes"])
    return proposal


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--date", required=True, help=f"operator-supplied ISO local {TIMEZONE} date, YYYY-MM-DD")
    parser.add_argument("--write", action="store_true", help="write the files; default is a dry run")
    parser.add_argument("--root", default=str(root), help="repository root (default: this checkout)")
    args = parser.parse_args(argv)
    try:
        proposal = run(Path(args.root), args.date, args.write)
    except ValueError as error:
        print(f"weekly-hot100: refused: {error}", file=sys.stderr)
        return 2
    mode = "written" if args.write else "dry-run, nothing written"
    print(f"weekly-hot100 {proposal['review_date']} ({mode})")
    for path, _, action in proposal["changes"]:
        print(f"  {action}: {path.relative_to(Path(args.root)).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

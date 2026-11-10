#!/usr/bin/env python3
"""greenlight_tiers.py: which PRs still need the human, decided by diff.

ASSUMES the fail-closed automerge gate in .github/workflows/automerge.yml and a
GitHub-shaped changed-files list. The safe set below is StaleToast's own.

The failure this prevents: a blanket approval-label gate scales the operator,
not the system. Past a few PRs a day the label becomes a rubber stamp applied
in batches, which is worse than no gate, because it still LOOKS like review.
Tiering keeps the human decision where a miss actually costs something and
lets CI-proven low-risk changes merge on green alone.

In this repository docs/ holds the source ledgers, pool, policy and frozen
history as well as prose, so docs/ as a whole is NOT safe. The safe set is an
explicit allowlist.

Policy (fail closed, gated unless proven safe):
- AUTO (merge on green, no label), all of:
  - the top-level README, added or modified;
  - a NEW dated record docs/staletoast-<name>-YYYY-MM-DD[-suffix].md or .json
    (scout runs, appraisals, resolutions). Added only: changing an existing
    dated record rewrites a receipt and gates;
  - other top-level docs/*.md prose, added or modified, unless it is listed in
    GATED_DOCS.
- GATED (label required): everything else. Explicitly always gated: any
  deletion or rename anywhere; workflows and ci-kit; site and scripts; exports
  and the export pin; every docs JSON that is not a new dated record (pool,
  intake policy, dispositions, reader selections, landscape, priorities, chart
  history, link corrections, provenance); every docs subdirectory; and the
  GATED_DOCS markdown (delivery and intake policy, method, the pool, the
  source ledgers and their generated priority view).

The approval label always works as an override in both directions of intent:
applying it merges a gated PR; nothing here merges a draft or a red check.
The gate runs the BASE branch's copy of this file, so a PR editing the
policy cannot loosen the gate on itself.

Usage:
    python3 greenlight_tiers.py --files-json changed_files.json
        exit 0 = AUTO, exit 1 = GATED (reason on stdout)
    python3 greenlight_tiers.py --selftest
"""
import json
import sys

import re

SAFE_EXACT = ("README.md",)
SAFE_STATUSES = ("added", "modified")
DATED_RECORD = re.compile(r"docs/staletoast-[a-z0-9]+(?:-[a-z0-9]+)*-\d{4}-\d{2}-\d{2}(?:-[a-z0-9]+)*\.(?:md|json)")
DOCS_PROSE = re.compile(r"docs/[A-Za-z0-9][A-Za-z0-9._-]*\.md")
# Policy, method, the pool and source-of-truth ledgers: prose-shaped, but a
# change here changes what the project does or publishes.
GATED_DOCS = frozenset("docs/" + name for name in (
    "delivery-pattern.md",
    "weekly-hot100.md",
    "staletoast-intake-policy.md",
    "staletoast-next-round-pool.md",
    "staletoast-appraisal-priorities.md",
    "collaborative-intelligence-method-v2.md",
    "collaborative-intelligence-repository-landscape-method.md",
    "collaborative-intelligence-research-ledger.md",
    "collaborative-intelligence-source-appraisals.md",
    "collaborative-intelligence-claim-register.md",
))


def classify(files):
    """files: list of {filename, status}. Returns (verdict, reason)."""
    if not isinstance(files, list) or not files:
        return "GATED", "empty changed-files list; fail closed"
    for f in files:
        if not isinstance(f, dict):
            return "GATED", "malformed changed-files entry; fail closed"
        name = f.get("filename", "")
        status = f.get("status", "")
        if not isinstance(name, str) or status not in SAFE_STATUSES:
            return "GATED", f"{name}: status {status!r} (deletions and renames always gate)"
        if name in SAFE_EXACT:
            continue
        if name in GATED_DOCS:
            return "GATED", f"{name}: policy, method, pool or ledger document"
        if DATED_RECORD.fullmatch(name):
            if status != "added":
                return "GATED", f"{name}: an existing dated record cannot change without approval"
            continue
        if DOCS_PROSE.fullmatch(name):
            continue
        return "GATED", f"{name}: outside the safe set"
    return "AUTO", f"all {len(files)} changed file(s) in the safe set"


def selftest() -> int:
    def one(name, status="modified"):
        return [{"filename": name, "status": status}]

    cases = [
        ("README modification is AUTO", one("README.md"), "AUTO"),
        ("prose doc modification is AUTO", one("docs/pr-pipeline-failure-investigation.md"), "AUTO"),
        ("new prose doc is AUTO", one("docs/new-note.md", "added"), "AUTO"),
        ("new dated scout record pair is AUTO",
         one("docs/staletoast-scout-2026-11-10.md", "added")
         + one("docs/staletoast-scout-2026-11-10.json", "added"), "AUTO"),
        ("new dated record with suffix is AUTO",
         one("docs/staletoast-deep-appraisal-2026-11-10-validation.json", "added"), "AUTO"),
        ("changing an existing dated JSON record gates",
         one("docs/staletoast-expansion-2026-11-01.json"), "GATED"),
        ("changing an existing dated markdown record gates",
         one("docs/staletoast-scout-2026-10-27.md"), "GATED"),
        ("delivery policy gates", one("docs/delivery-pattern.md"), "GATED"),
        ("intake policy gates", one("docs/staletoast-intake-policy.md"), "GATED"),
        ("intake policy JSON gates", one("docs/staletoast-intake-policy.json"), "GATED"),
        ("pool gates", one("docs/staletoast-next-round-pool.json"), "GATED"),
        ("pool view gates", one("docs/staletoast-next-round-pool.md"), "GATED"),
        ("reader selections gate", one("docs/staletoast-reader-selections.json"), "GATED"),
        ("source dispositions gate", one("docs/staletoast-source-dispositions.json"), "GATED"),
        ("research ledger gates", one("docs/collaborative-intelligence-research-ledger.md"), "GATED"),
        ("landscape gates", one("docs/collaborative-intelligence-repository-landscape.json"), "GATED"),
        ("new chart edition gates", one("docs/staletoast-chart-history/2026-11-09.json", "added"), "GATED"),
        ("weekly review receipt gates", one("docs/staletoast-weekly-review/2026-11-09.json", "added"), "GATED"),
        ("nested markdown gates", one("docs/sub/note.md", "added"), "GATED"),
        ("undated new JSON gates", one("docs/new-data.json", "added"), "GATED"),
        ("a doc deletion gates", one("docs/new-note.md", "removed"), "GATED"),
        ("a doc rename gates", one("docs/renamed.md", "renamed"), "GATED"),
        ("a workflow change gates", one(".github/workflows/automerge.yml"), "GATED"),
        ("the tier policy gates", one("ci-kit/workflows/greenlight_tiers.py"), "GATED"),
        ("site code gates", one("site/app.js"), "GATED"),
        ("an export snapshot gates", one("exports/" + "a" * 40 + ".json", "added"), "GATED"),
        ("the export pin gates", one("catalog-export-pin.json"), "GATED"),
        ("agent instructions gate", one("AGENTS.md"), "GATED"),
        ("one gated file gates the whole PR",
         one("docs/new-note.md") + one("site/app.js"), "GATED"),
        ("an empty list fails closed", [], "GATED"),
        ("a malformed entry fails closed", ["docs/new-note.md"], "GATED"),
    ]
    failed = 0
    for name, files, want in cases:
        got, _ = classify(files)
        ok = got == want
        failed += 0 if ok else 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
    print(f"selftest: {len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    try:
        i = sys.argv.index("--files-json")
        files = json.loads(open(sys.argv[i + 1], encoding="utf-8").read())
    except (ValueError, IndexError, OSError, json.JSONDecodeError) as exc:
        print(f"GATED: unreadable changed-files input ({exc}); fail closed")
        return 1
    verdict, reason = classify(files)
    print(f"{verdict}: {reason}")
    return 0 if verdict == "AUTO" else 1


if __name__ == "__main__":
    sys.exit(main())

"""Screen the retained StaleToast pool against added-unscreened Scope Map components.

Implements Rule 2 of docs/staletoast-scope-map.md as a deterministic, read-only
routing proposal. Does not promote components to established, assign grades,
release held sources, touch exports, or authorize adoption.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = ROOT / "site"
if str(SITE) not in sys.path:
    sys.path.insert(0, str(SITE))

from ledger_markdown import cells  # noqa: E402

SCOPE_MAP_PATH = DOCS / "staletoast-scope-map.json"
EXPANSION_PATH = DOCS / "staletoast-expansion-2026-11-01.json"
DISPOSITIONS_PATH = DOCS / "staletoast-source-dispositions.json"
LEDGER_PATH = DOCS / "collaborative-intelligence-research-ledger.md"
LANDSCAPE_PATH = DOCS / "collaborative-intelligence-repository-landscape.json"

JSON_OUT = DOCS / "staletoast-added-component-pool-screen-2026-11-27.json"
MD_OUT = DOCS / "staletoast-added-component-pool-screen-2026-11-27.md"

AUTHORITY_NOTE = (
    "evidence-only; deterministic term screen over the retained pool. Does not "
    "promote components to established, assign grades, release held sources, or "
    "authorize adoption."
)
THIN_THRESHOLD = 10


def lf_sha256(path: Path) -> str:
    normalized = path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def load_ledger_notes(ledger_text: str) -> dict[str, str]:
    section = ledger_text.split("## Source ledger", 1)[1].split("### Entry metadata", 1)[0]
    notes: dict[str, str] = {}
    for line in section.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        row = cells(line)
        if len(row) in {6, 7} and row[0] not in {"ID", "Candidate ID", "---"}:
            notes[row[0].strip()] = " ".join(row[2:]).strip()
    return notes


def load_landscape_notes(landscape: dict) -> dict[str, str]:
    notes: dict[str, str] = {}
    for item in landscape.get("repositories", []):
        sid = item.get("id")
        if sid:
            parts = [
                str(item.get("selection_aspect") or ""),
                str(item.get("category") or ""),
                str(item.get("evidence_note") or ""),
            ]
            notes[sid] = " ".join(p for p in parts if p)
    return notes


def build_routing_proposal(
    scope_map: dict,
    expansion: dict,
    dispositions: dict,
    ledger_text: str,
    landscape: dict,
    input_hashes: list[dict[str, str]],
) -> dict:
    added_components = [
        item for item in scope_map.get("components", [])
        if item.get("status") == "added-unscreened"
    ]
    if not added_components:
        raise ValueError("Expected at least one added-unscreened component in staletoast-scope-map.json")

    held_ids = {
        rec["id"]
        for rec in dispositions.get("records", [])
        if rec.get("state") == "held"
    } | {
        rec["id"]
        for rec in expansion.get("retained_held", [])
        if isinstance(rec, dict) and rec.get("id")
    }
    pool_links = {rec["id"]: rec["pool_id"] for rec in expansion.get("pool_links", [])}
    ledger_notes = load_ledger_notes(ledger_text)
    landscape_notes = load_landscape_notes(landscape)

    retained_sources = list(expansion.get("research", [])) + list(expansion.get("repositories", []))
    if len(retained_sources) != len(pool_links):
        raise ValueError("Retained expansion source count does not match pool_links")

    per_component = {
        comp["id"]: {
            "label": comp["label"],
            "active_matches": 0,
            "research_matches": 0,
            "repository_matches": 0,
            "held_excluded_matches": 0,
            "thin_coverage": True,
        }
        for comp in added_components
    }

    candidates = []
    held_seen = 0

    for item in sorted(retained_sources, key=lambda r: r["id"]):
        sid = item["id"]
        kind = item["kind"]
        is_held = sid in held_ids
        if is_held:
            held_seen += 1

        if kind == "research":
            title_or_repo = item["title"]
            haystack_parts = [
                item.get("title", ""),
                item.get("topic", ""),
                " ".join(item.get("matched_terms") or []),
                ledger_notes.get(sid, ""),
            ]
        else:
            title_or_repo = item["repository"]
            haystack_parts = [
                item.get("repository", ""),
                item.get("category", ""),
                item.get("description", ""),
                " ".join(item.get("matched_terms") or []),
                landscape_notes.get(sid, ""),
            ]
        haystack = " ".join(str(p) for p in haystack_parts if p).lower()

        matched_components = []
        for comp in added_components:
            cid = comp["id"]
            hits = sorted({term for term in comp["screen_terms"] if term.lower() in haystack})
            if not hits:
                continue
            if is_held:
                per_component[cid]["held_excluded_matches"] += 1
            else:
                per_component[cid]["active_matches"] += 1
                if kind == "research":
                    per_component[cid]["research_matches"] += 1
                else:
                    per_component[cid]["repository_matches"] += 1
                matched_components.append({
                    "component_id": cid,
                    "matched_terms": hits,
                })

        if not is_held and matched_components:
            candidates.append({
                "source_id": sid,
                "pool_id": pool_links[sid],
                "kind": kind,
                "title_or_repo": title_or_repo,
                "source_url": item["url"],
                "matched_components": matched_components,
                "grade": None,
                "disposition": "retained-pool-routing-proposal-only",
                "adoption": "not adopted",
                "hot100_selection": "not selected",
            })

    for cid, stats in per_component.items():
        stats["thin_coverage"] = stats["active_matches"] < THIN_THRESHOLD

    if held_seen != len(held_ids):
        raise ValueError(f"Expected {len(held_ids)} held records in retained pool, saw {held_seen}")

    total_assignments = sum(stats["active_matches"] for stats in per_component.values())
    total_held_matches = sum(stats["held_excluded_matches"] for stats in per_component.values())

    return {
        "schema_version": "1.0",
        "date": "2026-11-27",
        "kind": "routing-proposal",
        "authority": AUTHORITY_NOTE,
        "method": {
            "rule_version": "added-component-retained-pool-screen-v1",
            "description": (
                "Deterministic case-insensitive screen_terms match across retained expansion "
                "titles, topics, categories, descriptions, recorded matched_terms, and "
                "source-ledger or landscape notes. Held sources remain excluded."
            ),
            "thin_coverage_threshold": THIN_THRESHOLD,
        },
        "scope_map_status_unchanged": True,
        "inputs": input_hashes,
        "components": [
            {
                "id": comp["id"],
                "label": comp["label"],
                "status_in_scope_map": comp["status"],
                "screen_terms": list(comp["screen_terms"]),
                "related_claims": list(comp["related_claims"]),
                "comparison_question": comp["comparison_question"],
                "boundary": comp["boundary"],
            }
            for comp in added_components
        ],
        "counts": {
            "retained_pool_total": len(retained_sources),
            "held_excluded_total": held_seen,
            "active_pool_screened": len(retained_sources) - held_seen,
            "candidates_with_any_match": len(candidates),
            "total_component_assignments": total_assignments,
            "held_component_matches_total": total_held_matches,
            "per_component": per_component,
        },
        "candidates": candidates,
    }


def render_markdown(proposal: dict) -> str:
    counts = proposal["counts"]
    lines = [
        "# Added-component retained-pool routing screen (2026-11-27)",
        "",
        "Generated from [staletoast-added-component-pool-screen-2026-11-27.json]"
        "(staletoast-added-component-pool-screen-2026-11-27.json) by "
        "`python scripts/screen_added_components.py`.",
        "",
        f"**Kind:** `{proposal['kind']}` (read-only routing proposal; `scope_map_status_unchanged = true`).",
        "",
        f"**Authority:** {proposal['authority']}",
        "",
        "## Pool coverage summary",
        "",
        f"- Retained expansion pool records inspected: **{counts['retained_pool_total']}**",
        f"- Held records excluded under disposition boundaries: **{counts['held_excluded_total']}**",
        f"- Active retained records screened: **{counts['active_pool_screened']}**",
        f"- Distinct active candidate sources matching at least one component: **{counts['candidates_with_any_match']}**",
        f"- Total component routing assignments across those candidates: **{counts['total_component_assignments']}** (a source may match more than one component)",
        f"- Held-source term matches kept excluded: **{counts['held_component_matches_total']}** (out of {counts['held_excluded_total']} held records)",
        "",
        "| Component | Active matches | Research | Repositories | Held matches kept excluded | Thin (<10 active)? |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for cid, stats in counts["per_component"].items():
        thin = "yes (eligible for targeted discovery)" if stats["thin_coverage"] else "no (appraise existing pool first)"
        lines.append(
            f"| `{cid}` | {stats['active_matches']} | {stats['research_matches']} | "
            f"{stats['repository_matches']} | {stats['held_excluded_matches']} | {thin} |"
        )
    lines += [
        "",
        "## Governance boundaries preserved",
        "",
        "1. Every candidate keeps `grade: null`, `adoption: not adopted`, and `hot100_selection: not selected`.",
        "2. All 41 held sources in `docs/staletoast-source-dispositions.json` remain excluded from `candidates`, including offensive or evasion-focused security repositories.",
        "3. `docs/staletoast-scope-map.json` keeps all four November 27 components at `added-unscreened` until human appraisal compares primary sources against each component's baseline question.",
        "4. No catalog export, frozen snapshot, or Hot 100 edition is modified by this routing proposal.",
    ]
    return "\n".join(lines) + "\n"


def validate_proposal_invariants(proposal: dict, held_ids: set[str]) -> None:
    if proposal.get("kind") != "routing-proposal":
        raise ValueError("Proposal kind must remain routing-proposal")
    if proposal.get("scope_map_status_unchanged") is not True:
        raise ValueError("scope_map_status_unchanged must be True")
    for candidate in proposal.get("candidates", []):
        sid = candidate.get("source_id")
        if sid in held_ids:
            raise ValueError(f"Held source {sid} leaked into routing candidates")
        if candidate.get("grade") is not None:
            raise ValueError(f"{sid}: automated routing proposal must keep grade=None")
        if candidate.get("adoption") != "not adopted" or candidate.get("hot100_selection") != "not selected":
            raise ValueError(f"{sid}: routing proposal cannot promote or adopt a source")


def compute_current() -> tuple[dict, str, str, set[str]]:
    input_paths = [SCOPE_MAP_PATH, EXPANSION_PATH, DISPOSITIONS_PATH, LEDGER_PATH, LANDSCAPE_PATH]
    input_hashes = [
        {"path": p.relative_to(ROOT).as_posix(), "sha256": lf_sha256(p)}
        for p in input_paths
    ]
    scope_map = json.loads(SCOPE_MAP_PATH.read_text(encoding="utf-8"))
    expansion = json.loads(EXPANSION_PATH.read_text(encoding="utf-8"))
    dispositions = json.loads(DISPOSITIONS_PATH.read_text(encoding="utf-8"))
    ledger_text = LEDGER_PATH.read_text(encoding="utf-8")
    landscape = json.loads(LANDSCAPE_PATH.read_text(encoding="utf-8"))
    held_ids = {r["id"] for r in dispositions.get("records", []) if r.get("state") == "held"}

    proposal = build_routing_proposal(
        scope_map, expansion, dispositions, ledger_text, landscape, input_hashes
    )
    validate_proposal_invariants(proposal, held_ids)
    json_text = json.dumps(proposal, indent=2, ensure_ascii=False) + "\n"
    md_text = render_markdown(proposal)
    if "\u2014" in json_text or "\u2014" in md_text:
        raise ValueError("Output must not contain em-dashes")
    return proposal, json_text, md_text, held_ids


def display_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    proposal, json_text, md_text, held_ids = compute_current()
    if args.check:
        if not JSON_OUT.exists() or JSON_OUT.read_text(encoding="utf-8") != json_text:
            raise SystemExit(
                f"{display_path(JSON_OUT)} is missing or stale; "
                "run python scripts/screen_added_components.py"
            )
        if not MD_OUT.exists() or MD_OUT.read_text(encoding="utf-8") != md_text:
            raise SystemExit(
                f"{display_path(MD_OUT)} is missing or stale; "
                "run python scripts/screen_added_components.py"
            )
        committed = json.loads(JSON_OUT.read_text(encoding="utf-8"))
        validate_proposal_invariants(committed, held_ids)
        print(
            f"added-component pool screen check: candidates={proposal['counts']['candidates_with_any_match']} "
            f"held_excluded={proposal['counts']['held_excluded_total']}"
        )
        return

    JSON_OUT.write_text(json_text, encoding="utf-8", newline="\n")
    MD_OUT.write_text(md_text, encoding="utf-8", newline="\n")
    print(
        f"wrote added-component pool screen: candidates={proposal['counts']['candidates_with_any_match']} "
        f"held_excluded={proposal['counts']['held_excluded_total']}"
    )


if __name__ == "__main__":
    main()

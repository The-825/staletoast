"""Unified offline intake validation, canonical deduplication, and appraisal queue selection.

Standard library only. No network, provider, git or upstream code execution.
Enforces daily intake caps, bibliographic verification, canonical identity
deduplication, and deterministic appraisal batch selection across thin Scope Map
components and claim gaps.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
if str(SITE) not in sys.path:
    sys.path.insert(0, str(SITE))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import build_priorities as priorities  # noqa: E402
from intake_state import AUTOMATED, IntakeState  # noqa: E402
from ledger_markdown import cells, source_link  # noqa: E402
import verify_bibliographic_metadata as bib  # noqa: E402

DAILY_CAP = 12
RESEARCH_ID_RE = re.compile(r"^(?:\d{3,}|C-\d{3,})$")
REPO_ID_RE = re.compile(r"^R-\d{3,}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf|html)/([0-9]{4}\.[0-9]{4,5}|[a-z-]+/[0-9]{7})(?:v\d+)?(?:\.pdf)?", re.I)
ARXIV_TEXT_RE = re.compile(r"\barxiv[:\s]+([0-9]{4}\.[0-9]{4,5})(?:v\d+)?\b", re.I)
DOI_URL_RE = re.compile(r"doi\.org/(10\.\d{4,9}/[^\s\"'>]+)", re.I)
DOI_TEXT_RE = re.compile(r"\bDOI[:\s]+(10\.\d{4,9}/[^\s,;|\">]+)", re.I)
GITHUB_URL_RE = re.compile(r"^https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:/.*)?$")
FORBIDDEN_DASHES = ("\u2014", "\u2013")

VALID_DIRECTNESS = {"D3", "D2", "D1", "D0"}
VALID_HORIZONS = {
    "longitudinal",
    "repeated",
    "single",
    "technical",
    "retrospective",
    "not observed",
    "short sequence",
}
VALID_REPO_DEPTHS = {"readme-screened", "source-assessment", "readme-relevance-screened"}
VALID_MECHANISM_CODES = {"V", "P", "N", "O", "U"}
REQUIRED_REPO_DIMENSIONS = (
    "collaboration_topology",
    "workflow_state",
    "human_authority",
    "memory_context",
    "trace_recovery",
    "evaluation_surface",
    "collaboration_baseline",
    "cost_burden",
    "change_expiry",
    "independent_verification",
    "interoperability",
)

# Keyword hints linking unappraised topics/descriptions to baseline claim gaps for read-only queue triage.
CLAIM_TRIAGE_TERMS = {
    "CI-006": ("handoff", "recovery", "failure", "rollback", "checkpoint", "trace", "incident"),
    "CI-007": ("authority", "approval", "permission", "consent", "escalation", "governance", "oversight"),
    "CI-008": ("drift", "expiry", "stale", "update", "revalidation", "version"),
    "CI-009": ("memory", "episodic", "retention", "consolidation", "forgetting", "session"),
    "CI-004": ("cost", "latency", "burden", "overhead", "effort", "token"),
    "CI-017": ("verification", "independent", "audit", "self-refine", "critic", "judge"),
    "CI-001": ("complementarity", "synergy", "human-ai", "teaming", "baseline"),
    "CI-002": ("benchmark", "evaluation", "trajectory", "milestone"),
    "CI-010": ("grounding", "privacy", "common ground", "context"),
    "CI-011": ("mode awareness", "takeover", "intervention", "supervision", "control"),
    "CI-016": ("multi-agent", "orchestration", "topology", "swarm", "delegat"),
    "CI-012": ("explanation", "interpretability", "rationale", "xai"),
    "CI-015": ("diversity", "deliberation", "dissent", "consensus", "debate", "plural"),
    "CI-003": ("trust", "reliance", "overreliance", "calibration", "aversion"),
    "CI-005": ("allocation", "capability", "frontier", "routing"),
    "CI-013": ("defer", "deferral", "abstain", "clarif"),
    "CI-014": ("retrieval", "rag", "search", "index"),
}


def _check_iso_date(value: str, label: str = "date") -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{label} must use YYYY-MM-DD")
    if date.fromisoformat(value).isoformat() != value:
        raise ValueError(f"{label} must be a valid calendar YYYY-MM-DD")
    return value


def _assert_no_dashes(value: object, context: str) -> None:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    for dash in FORBIDDEN_DASHES:
        if dash in text:
            raise ValueError(f"{context}: forbidden em-dash or en-dash character detected")


CASE_INSENSITIVE_PATH_HOSTS = {"github.com", "arxiv.org", "doi.org", "dx.doi.org"}


def canonical_url_key(url: str | None) -> str | None:
    if not url or not isinstance(url, str):
        return None
    raw = url.strip()
    parsed = urlsplit(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    host = parsed.hostname.lower()
    if host.startswith("www."):
        host = host[4:]
    port_part = f":{parsed.port}" if parsed.port else ""
    path = re.sub(r"/+", "/", parsed.path or "/").rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    normalized_path = path.lower() if host in CASE_INSENSITIVE_PATH_HOSTS else path
    kept_query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if not k.lower().startswith("utm_") and k.lower() not in {"ref", "source"}
    ]
    query_part = f"?{urlencode(sorted(kept_query))}" if kept_query else ""
    return f"url:{host}{port_part}{normalized_path}{query_part}"


def canonical_identities(url: str | None = None, text: str = "", repository: str | None = None, aliases: list[str] | None = None) -> set[str]:
    keys: set[str] = set()
    combined = " ".join(part for part in (url or "", text or "") if part)

    for match in ARXIV_RE.finditer(combined):
        keys.add(f"arxiv:{match.group(1).lower()}")
    for match in ARXIV_TEXT_RE.finditer(combined):
        keys.add(f"arxiv:{match.group(1).lower()}")

    for match in DOI_URL_RE.finditer(url or ""):
        cleaned = match.group(1).rstrip(".,;")
        while cleaned.endswith(")") and cleaned.count(")") > cleaned.count("("):
            cleaned = cleaned[:-1].rstrip(".,;")
        keys.add(f"doi:{cleaned.lower()}")
    for match in DOI_TEXT_RE.finditer(text or ""):
        cleaned = match.group(1).rstrip(".,;")
        while cleaned.endswith(")") and cleaned.count(")") > cleaned.count("("):
            cleaned = cleaned[:-1].rstrip(".,;")
        keys.add(f"doi:{cleaned.lower()}")

    if url:
        gh = GITHUB_URL_RE.match(url.strip())
        if gh:
            owner, repo_name = gh.group(1).lower(), gh.group(2).lower()
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            keys.add(f"github:{owner}/{repo_name}")
        url_key = canonical_url_key(url)
        if url_key and not ARXIV_RE.search(url):
            keys.add(url_key)

    if repository and "/" in repository:
        keys.add(f"github:{repository.strip().lower()}")
    for alias in aliases or []:
        if isinstance(alias, str) and "/" in alias:
            keys.add(f"github:{alias.strip().lower()}")
        elif isinstance(alias, str) and alias.startswith("https://"):
            alias_key = canonical_url_key(alias)
            if alias_key:
                keys.add(alias_key)
    return keys


def _load_corpus_index(docs: Path) -> dict:
    ledger_text = (docs / "collaborative-intelligence-research-ledger.md").read_text(encoding="utf-8")
    research_entries = bib.parse_ledger_entries(ledger_text)
    landscape = json.loads((docs / "collaborative-intelligence-repository-landscape.json").read_text(encoding="utf-8"))
    state = IntakeState(docs)
    pool_path = docs / "staletoast-next-round-pool.json"
    pool = json.loads(pool_path.read_text(encoding="utf-8"))["records"] if pool_path.exists() else []

    by_key: dict[str, list[tuple[str, str]]] = {}
    records: dict[tuple[str, str], set[str]] = {}

    for entry in research_entries:
        sid = entry["id"]
        keys = canonical_identities(url=entry["url"], text=entry["source_cell"])
        records[("research", sid)] = keys
        for key in keys:
            by_key.setdefault(key, []).append(("research", sid))

    for repo in landscape.get("repositories", []):
        sid = repo["id"]
        keys = canonical_identities(
            url=repo.get("url"),
            repository=repo.get("repository"),
            aliases=repo.get("aliases") or [],
        )
        records[("repository", sid)] = keys
        for key in keys:
            by_key.setdefault(key, []).append(("repository", sid))

    return {
        "research_entries": research_entries,
        "repositories": landscape.get("repositories", []),
        "held_research": state.held_ids("research"),
        "held_repositories": state.held_ids("repository"),
        "pool": pool,
        "by_key": by_key,
        "records": records,
    }


def check_corpus(root: Path = ROOT) -> dict:
    docs = Path(root) / "docs"
    index = _load_corpus_index(docs)
    same_kind_collisions = []
    cross_kind_links = []
    for key, owners in sorted(index["by_key"].items()):
        unique_owners = sorted(set(owners))
        if len(unique_owners) <= 1:
            continue
        kinds = {kind for kind, _ in unique_owners}
        if len(kinds) == 1:
            same_kind_collisions.append({"canonical_key": key, "owners": [f"{k}:{i}" for k, i in unique_owners]})
        else:
            # A paper and its companion repository may legitimately cite the same project URL.
            cross_kind_links.append({"canonical_key": key, "owners": [f"{k}:{i}" for k, i in unique_owners]})

    pool_matches = 0
    unlinked_pool_overlap = []
    for row in index["pool"]:
        p_keys = canonical_identities(url=row.get("canonical_url") or row.get("discovery_url"))
        matched_owners = sorted({f"{k}:{i}" for key in p_keys for k, i in index["by_key"].get(key, [])})
        if matched_owners:
            pool_matches += 1
            if not row.get("linked_identity"):
                unlinked_pool_overlap.append({
                    "pool_id": row.get("pool_id"),
                    "discovery_url": row.get("discovery_url"),
                    "matched_ledger_ids": matched_owners,
                })

    if same_kind_collisions:
        raise ValueError(f"Duplicate canonical source identities in same ledger: {same_kind_collisions}")

    return {
        "research_records": len(index["research_entries"]),
        "repository_records": len(index["repositories"]),
        "held_research": len(index["held_research"]),
        "held_repositories": len(index["held_repositories"]),
        "pool_records": len(index["pool"]),
        "same_kind_collisions": same_kind_collisions,
        "cross_kind_shared_links": len(cross_kind_links),
        "pool_records_matching_ledger": pool_matches,
        "pool_records_matching_without_linked_identity": len(unlinked_pool_overlap),
    }


def select_next_batch(root: Path = ROOT, *, limit: int = 8, kind: str = "all") -> dict:
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")
    if kind not in {"all", "research", "repository"}:
        raise ValueError("kind must be all, research, or repository")
    docs = Path(root) / "docs"
    state = IntakeState(docs)
    held_all = state.held_ids("research") | state.held_ids("repository")

    scope_path = docs / "staletoast-scope-map.json"
    scope_map = json.loads(scope_path.read_text(encoding="utf-8")) if scope_path.exists() else {"components": []}
    added_components = [c for c in scope_map.get("components", []) if c.get("status") == "added-unscreened"]

    screen_files = sorted(docs.glob("staletoast-added-component-pool-screen-*.json"))
    thin_ids: set[str] = set()
    if screen_files:
        latest_screen = json.loads(screen_files[-1].read_text(encoding="utf-8"))
        for cid, stats in latest_screen.get("counts", {}).get("per_component", {}).items():
            if stats.get("thin_coverage"):
                thin_ids.add(cid)
    else:
        thin_ids = {c["id"] for c in added_components}

    expansion_files = sorted(docs.glob("staletoast-expansion-*.json"))
    expansion = json.loads(expansion_files[-1].read_text(encoding="utf-8")) if expansion_files else {"research": [], "repositories": []}
    exp_by_id = {
        row["id"]: row
        for row in list(expansion.get("research", [])) + list(expansion.get("repositories", []))
        if isinstance(row, dict) and "id" in row
    }

    ledger_text = (docs / "collaborative-intelligence-research-ledger.md").read_text(encoding="utf-8")
    ledger_by_id = {row["id"]: row for row in bib.parse_ledger_entries(ledger_text)}
    landscape = json.loads((docs / "collaborative-intelligence-repository-landscape.json").read_text(encoding="utf-8"))
    repos_by_id = {row["id"]: row for row in landscape.get("repositories", [])}

    pool_candidates = []
    if kind in {"all", "research"}:
        for sid, entry in sorted(ledger_by_id.items()):
            if sid in held_all or state.appraisal_state("research", sid) != AUTOMATED:
                continue
            exp = exp_by_id.get(sid, {})
            haystack = " ".join([
                entry["title"],
                entry["source_cell"],
                str(exp.get("topic") or ""),
                " ".join(exp.get("matched_terms") or []),
            ]).lower()
            has_primary_id = bool(ARXIV_RE.search(entry["url"]) or DOI_URL_RE.search(entry["url"]) or "aclanthology.org" in entry["url"])
            pool_candidates.append({
                "id": sid,
                "kind": "research",
                "title_or_repo": entry["title"],
                "url": entry["url"],
                "haystack": haystack,
                "metadata_ready": has_primary_id and bool(entry["author_prefix"]),
            })

    if kind in {"all", "repository"}:
        for sid, repo in sorted(repos_by_id.items()):
            if sid in held_all or state.appraisal_state("repository", sid) != AUTOMATED:
                continue
            exp = exp_by_id.get(sid, {})
            haystack = " ".join([
                repo.get("repository", ""),
                str(repo.get("category") or ""),
                str(repo.get("evidence_note") or ""),
                str(exp.get("description") or ""),
                " ".join(exp.get("matched_terms") or []),
            ]).lower()
            ready = bool(HEX40_RE.fullmatch(str(repo.get("snapshot_commit") or ""))) and repo.get("license_status") not in {None, "", "unknown"}
            pool_candidates.append({
                "id": sid,
                "kind": "repository",
                "title_or_repo": repo["repository"],
                "url": repo["url"],
                "haystack": haystack,
                "metadata_ready": ready,
            })

    scored = []
    for item in pool_candidates:
        haystack = item["haystack"]
        matched_comps = [
            comp["id"]
            for comp in added_components
            if any(term.lower() in haystack for term in comp.get("screen_terms", []))
        ]
        matched_thin = [cid for cid in matched_comps if cid in thin_ids]
        matched_claims = [
            claim
            for claim in priorities.GAPS
            if any(term in haystack for term in CLAIM_TRIAGE_TERMS.get(claim, ()))
        ]
        best_gap_index = priorities.GAPS.index(matched_claims[0]) if matched_claims else len(priorities.GAPS)
        sort_key = (
            0 if matched_thin else (1 if matched_comps else 2),
            -len(matched_thin),
            best_gap_index,
            0 if item["metadata_ready"] else 1,
            -len(matched_comps),
            item["id"],
        )
        reasons = []
        if matched_thin:
            reasons.append(f"covers thin scope component ({', '.join(matched_thin)})")
        elif matched_comps:
            reasons.append(f"covers added scope component ({', '.join(matched_comps)})")
        if matched_claims:
            reasons.append(f"candidate terms align with gap {matched_claims[0]}")
        if item["metadata_ready"]:
            reasons.append("primary pin and license/citation metadata ready")
        scored.append((
            sort_key,
            {
                "id": item["id"],
                "kind": item["kind"],
                "title_or_repo": item["title_or_repo"],
                "url": item["url"],
                "matched_thin_components": matched_thin,
                "matched_added_components": matched_comps,
                "candidate_claim_gaps": matched_claims[:3],
                "metadata_ready": item["metadata_ready"],
                "why_selected": "; ".join(reasons) or "awaiting human appraisal in queue order",
                "authority_note": "read-only appraisal queue shortlist; does not assign a grade or promote a source",
            },
        ))

    scored.sort(key=lambda pair: pair[0])
    if kind == "all":
        research_ranked = [entry for _, entry in scored if entry["kind"] == "research"]
        repo_ranked = [entry for _, entry in scored if entry["kind"] == "repository"]
        selected = []
        ri = gi = 0
        while len(selected) < limit and (ri < len(research_ranked) or gi < len(repo_ranked)):
            if ri < len(research_ranked):
                selected.append(research_ranked[ri])
                ri += 1
            if len(selected) < limit and gi < len(repo_ranked):
                selected.append(repo_ranked[gi])
                gi += 1
    else:
        selected = [entry for _, entry in scored[:limit]]

    return {
        "schema_version": "1.0",
        "kind": "appraisal-queue-shortlist",
        "authority": "read-only triage proposal over unappraised automated-screen records; changes no grades or files",
        "pool_candidates_considered": len(pool_candidates),
        "thin_scope_components_prioritized": sorted(thin_ids),
        "requested_limit": limit,
        "selected_count": len(selected),
        "shortlist": selected,
    }


def validate_candidate_payload(payload: dict, root: Path = ROOT) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("candidate intake file must be a JSON object")
    _assert_no_dashes(payload, "candidate payload")
    research_items = payload.get("research") or []
    repo_items = payload.get("repositories") or []
    if not isinstance(research_items, list) or not isinstance(repo_items, list):
        raise ValueError("research and repositories must be lists")
    if len(research_items) > DAILY_CAP or len(repo_items) > DAILY_CAP:
        raise ValueError(f"intake batch exceeds daily cap of {DAILY_CAP} per category")
    if not research_items and not repo_items:
        raise ValueError("candidate payload has no research or repository entries")

    docs = Path(root) / "docs"
    index = _load_corpus_index(docs)
    existing_research_ids = {row["id"] for row in index["research_entries"]}
    existing_repo_ids = {row["id"] for row in index["repositories"]}
    held_all = index["held_research"] | index["held_repositories"]

    batch_ids: set[str] = set()
    batch_keys: dict[str, str] = {}

    for row in research_items:
        sid = str(row.get("id", "")).strip()
        if not RESEARCH_ID_RE.fullmatch(sid):
            raise ValueError(f"{sid or '<missing>'}: invalid research ID (expected NNN+ or C-NNN+)")
        if sid in existing_research_ids or sid in held_all or sid in batch_ids:
            raise ValueError(f"{sid}: research ID already exists or is held")
        batch_ids.add(sid)

        for field in ("authors", "verified_first_author", "title", "url", "venue", "level_and_evidence",
                      "finding", "impact", "boundary", "design", "directness", "family", "horizon", "flags"):
            val = str(row.get(field, "")).strip()
            if not val:
                raise ValueError(f"{sid}: missing required research field {field}")
            if "|" in val:
                raise ValueError(f"{sid}: field {field} must not contain unescaped pipe '|'")
        if not str(row["authors"]).strip().startswith(str(row["verified_first_author"]).strip()):
            raise ValueError(f"{sid}: authors must start with verified_first_author")
        for token in bib.PLACEHOLDER_TOKENS:
            if token in str(row["authors"]).lower():
                raise ValueError(f"{sid}: placeholder author token {token!r} is not allowed")
        parsed_url = urlsplit(row["url"].strip())
        if parsed_url.scheme != "https" or not parsed_url.netloc or any(c.isspace() for c in row["url"].strip()):
            raise ValueError(f"{sid}: research url must be a whitespace-free https:// URL")
        year = row.get("year")
        if type(year) is not int or not 1900 <= year <= 2100:
            raise ValueError(f"{sid}: year must be a 4-digit integer between 1900 and 2100")
        _check_iso_date(str(row.get("verified_date", "")), f"{sid}.verified_date")
        if row["directness"][:2] not in VALID_DIRECTNESS:
            raise ValueError(f"{sid}: invalid directness {row['directness']!r}")
        if row["horizon"] not in VALID_HORIZONS:
            raise ValueError(f"{sid}: invalid horizon {row['horizon']!r}")
        claims = row.get("claims") or []
        if not isinstance(claims, list) or any(c not in priorities.GAPS for c in claims):
            raise ValueError(f"{sid}: unknown claim ID in {claims!r}")

        keys = canonical_identities(url=row["url"], text=f"{row['title']} {row['venue']}")
        for key in keys:
            owners = [i for k, i in index["by_key"].get(key, []) if k == "research"]
            if owners:
                raise ValueError(f"{sid}: canonical identity {key} duplicates existing research {owners}")
            if key in batch_keys:
                raise ValueError(f"{sid}: canonical identity {key} duplicates batch entry {batch_keys[key]}")
            batch_keys[key] = sid

    for row in repo_items:
        sid = str(row.get("id", "")).strip()
        if not REPO_ID_RE.fullmatch(sid):
            raise ValueError(f"{sid or '<missing>'}: invalid repository ID (expected R-NNN+)")
        if sid in existing_repo_ids or sid in held_all or sid in batch_ids:
            raise ValueError(f"{sid}: repository ID already exists or is held")
        batch_ids.add(sid)

        repo_slug = str(row.get("repository", "")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo_slug):
            raise ValueError(f"{sid}: repository must use owner/name format")
        url = str(row.get("url", "")).strip()
        if not GITHUB_URL_RE.match(url) or not url.startswith("https://"):
            raise ValueError(f"{sid}: repository url must be an https://github.com/owner/name URL")
        commit = str(row.get("snapshot_commit", "")).strip()
        if not HEX40_RE.fullmatch(commit):
            raise ValueError(f"{sid}: snapshot_commit must be a 40-char lowercase hex SHA")
        _check_iso_date(str(row.get("snapshot_date", "")), f"{sid}.snapshot_date")
        stars = row.get("stars_observed")
        if stars is not None and (type(stars) is not int or stars < 0):
            raise ValueError(f"{sid}: stars_observed must be a non-negative integer or null")
        if stars is not None:
            _check_iso_date(str(row.get("popularity_observed_date", "")), f"{sid}.popularity_observed_date")
        depth = str(row.get("evidence_depth", "")).strip()
        if depth not in VALID_REPO_DEPTHS:
            raise ValueError(f"{sid}: unsupported evidence_depth {depth!r}")
        for field in ("selection_aspect", "category", "lifecycle", "evidence_pointer", "evidence_note", "license_status"):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"{sid}: missing required repository field {field}")
        claims = row.get("claims") or []
        if not isinstance(claims, list) or any(c not in priorities.GAPS for c in claims):
            raise ValueError(f"{sid}: unknown claim ID in {claims!r}")
        mechanisms = row.get("mechanisms")
        if not isinstance(mechanisms, dict) or set(mechanisms) != set(REQUIRED_REPO_DIMENSIONS):
            raise ValueError(f"{sid}: mechanisms must record all 11 repository dimensions")
        if any(code not in VALID_MECHANISM_CODES for code in mechanisms.values()):
            raise ValueError(f"{sid}: mechanisms codes must be in {sorted(VALID_MECHANISM_CODES)}")

        keys = canonical_identities(url=url, repository=repo_slug, aliases=row.get("aliases") or [])
        for key in keys:
            owners = [i for k, i in index["by_key"].get(key, []) if k == "repository"]
            if owners:
                raise ValueError(f"{sid}: canonical identity {key} duplicates existing repository {owners}")
            if key in batch_keys:
                raise ValueError(f"{sid}: canonical identity {key} duplicates batch entry {batch_keys[key]}")
            batch_keys[key] = sid

    return {
        "valid": True,
        "research_count": len(research_items),
        "repository_count": len(repo_items),
        "ids": sorted(batch_ids),
    }


def prepare_intake(payload: dict, as_of: str, root: Path = ROOT, *, write: bool = False) -> dict:
    _check_iso_date(as_of, "date")
    summary = validate_candidate_payload(payload, root=root)
    docs = Path(root) / "docs"

    ledger_path = docs / "collaborative-intelligence-research-ledger.md"
    appraisal_path = docs / "collaborative-intelligence-source-appraisals.md"
    bib_path = docs / "staletoast-bibliographic-verifications.json"
    landscape_path = docs / "collaborative-intelligence-repository-landscape.json"
    priorities_json_path = docs / "staletoast-appraisal-priorities.json"
    priorities_md_path = docs / "staletoast-appraisal-priorities.md"

    ledger_text = ledger_path.read_text(encoding="utf-8")
    appraisal_text = appraisal_path.read_text(encoding="utf-8")
    bib_manifest = json.loads(bib_path.read_text(encoding="utf-8"))
    landscape = json.loads(landscape_path.read_text(encoding="utf-8"))

    for row in payload.get("research") or []:
        sid = row["id"].strip()
        cite = f'{row["authors"].strip()}, ["{row["title"].strip()}"]({row["url"].strip()}), {row["venue"].strip()}, {row["year"]}'
        note_col = str(row.get("record_note") or ("Candidate, not promoted" if sid.startswith("C-") else "")).strip()
        if sid.startswith("C-") or note_col:
            ledger_line = f"| {sid} | {cite} | {row['level_and_evidence'].strip()} | {row['finding'].strip()} | {row['impact'].strip()} | {row['boundary'].strip()} | {note_col or 'Candidate, not promoted'} |"
        else:
            ledger_line = f"| {sid} | {cite} | {row['level_and_evidence'].strip()} | {row['finding'].strip()} | {row['impact'].strip()} | {row['boundary'].strip()} |"
        head, sep, tail = ledger_text.partition("\n### Entry metadata")
        if not sep:
            raise ValueError("Research ledger missing ### Entry metadata boundary")
        ledger_text = head.rstrip("\n") + "\n" + ledger_line + "\n\n### Entry metadata" + tail

        claims_str = ", ".join(row.get("claims") or [])
        app_line = f"| {sid} | {row['design'].strip()} | {row['directness'].strip()} | {row['family'].strip()} | {row['horizon'].strip()} | {row['flags'].strip()} | {claims_str} |"
        appraisal_text = appraisal_text.rstrip("\n") + "\n" + app_line + "\n"

        bib_manifest["verifications"].append({
            "id": sid,
            "verified_first_author": row["verified_first_author"].strip(),
            "verified_title": row["title"].strip(),
            "year": row["year"],
            "venue_or_record_type": row["venue"].strip(),
            "canonical_url": row["url"].strip(),
            "verified_date": row["verified_date"].strip(),
            "verification_basis": str(row.get("verification_basis") or "primary-publication-record").strip(),
            "claim_verification_status": bib.REQUIRED_CLAIM_STATUS,
        })

    for row in payload.get("repositories") or []:
        sid = row["id"].strip()
        record = {
            "id": sid,
            "repository": row["repository"].strip(),
            "url": row["url"].strip(),
            "snapshot_commit": row["snapshot_commit"].strip(),
            "snapshot_date": row["snapshot_date"].strip(),
            "stars_observed": row.get("stars_observed"),
            "popularity_observed_date": row.get("popularity_observed_date"),
            "selection_aspect": row["selection_aspect"].strip(),
            "category": row["category"].strip(),
            "lifecycle": row["lifecycle"].strip(),
            "evidence_depth": row["evidence_depth"].strip(),
            "evidence_pointer": row["evidence_pointer"].strip(),
            "evidence_note": row["evidence_note"].strip(),
            "claims": list(row.get("claims") or []),
            "mechanisms": dict(row["mechanisms"]),
            "upstream_revision": str(row.get("upstream_revision") or row["snapshot_commit"]).strip(),
            "assessment_status": str(row.get("assessment_status") or ("mechanism-screened" if row["evidence_depth"] == "readme-screened" else "source-assessed")).strip(),
            "license_status": row["license_status"].strip(),
            "aliases": list(row.get("aliases") or []),
        }
        if row.get("evidence_family"):
            record["evidence_family"] = str(row["evidence_family"]).strip()
        landscape["repositories"].append(record)
        later = landscape.setdefault("post_import_repository_ids", [])
        if sid not in later:
            later.append(sid)

    # Validate bibliographic manifest in memory before touching disk.
    bib.validate_bibliographic_metadata(ledger_text, bib_manifest)
    landscape_text = json.dumps(landscape, indent=2, ensure_ascii=False) + "\n"
    bib_text = json.dumps(bib_manifest, indent=2, ensure_ascii=False) + "\n"

    # Validate priorities rebuild in an isolated temp docs mirror before touching real files.
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_docs = Path(tmp_dir)
        for existing in docs.glob("*"):
            if existing.is_file():
                (tmp_docs / existing.name).write_bytes(existing.read_bytes())
        (tmp_docs / ledger_path.name).write_text(ledger_text, encoding="utf-8", newline="\n")
        (tmp_docs / appraisal_path.name).write_text(appraisal_text, encoding="utf-8", newline="\n")
        (tmp_docs / landscape_path.name).write_text(landscape_text, encoding="utf-8", newline="\n")
        (tmp_docs / bib_path.name).write_text(bib_text, encoding="utf-8", newline="\n")
        priorities_payload = priorities.build(tmp_docs, as_of)
        priorities_md = priorities.render(priorities_payload)

    priorities_json_text = json.dumps(priorities_payload, indent=2, ensure_ascii=False) + "\n"
    staged_writes = [
        (ledger_path, ledger_text),
        (appraisal_path, appraisal_text),
        (bib_path, bib_text),
        (landscape_path, landscape_text),
        (priorities_json_path, priorities_json_text),
        (priorities_md_path, priorities_md),
    ]
    changes = []
    for target, new_text in staged_writes:
        old_text = target.read_text(encoding="utf-8") if target.exists() else None
        action = "unchanged" if old_text == new_text else ("update" if target.exists() else "create")
        changes.append((target, new_text, action))

    if write:
        _atomic_swap([(target, text) for target, text, action in changes if action != "unchanged"])

    return {
        "date": as_of,
        "mode": "written" if write else "dry-run",
        **summary,
        "files": [
            {"path": target.relative_to(Path(root)).as_posix(), "action": action}
            for target, _, action in changes
        ],
    }


def _atomic_swap(pending: list[tuple[Path, str]]) -> None:
    """Stage all modified files in temp siblings before swapping, with in-process rollback on error."""
    resolved = [path.resolve() for path, _ in pending]
    if len(set(resolved)) != len(resolved):
        raise ValueError("duplicate target path in staged intake write")
    backups: dict[Path, bytes | None] = {}
    created_dirs: list[Path] = []
    staged: list[tuple[Path, Path]] = []
    try:
        for path, _ in pending:
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                created_dirs.append(path.parent)
        for path, text in pending:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix="." + path.name + ".intake-",
                suffix=".tmp",
                dir=path.parent,
                delete=False,
            ) as handle:
                staged_path = Path(handle.name)
                staged.append((staged_path, path))
                handle.write(text.replace("\r\n", "\n").encode("utf-8"))
            if path.exists():
                try:
                    shutil.copymode(path, staged_path)
                except OSError:
                    pass
        for temp, path in staged:
            backups[path] = path.read_bytes() if path.exists() else None
            os.replace(temp, path)
    except BaseException:
        for path, old in backups.items():
            try:
                if old is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(old)
            except OSError:
                pass
        for temp, _ in staged:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-corpus", action="store_true", help="verify canonical identity uniqueness across ledgers and pool")
    mode.add_argument("--next-batch", action="store_true", help="select a deterministic read-only appraisal shortlist")
    mode.add_argument("--validate-candidate", metavar="JSON_PATH", help="validate a candidate intake JSON file without writing")
    mode.add_argument("--prepare", metavar="JSON_PATH", help="stage or apply coordinated ledger, manifest, and priority updates")
    parser.add_argument("--limit", type=int, default=8, help="shortlist size for --next-batch (default: 8)")
    parser.add_argument("--kind", choices=("all", "research", "repository"), default="all", help="filter --next-batch by kind")
    parser.add_argument("--date", help="ISO YYYY-MM-DD date required for --prepare")
    parser.add_argument("--write", action="store_true", help="apply --prepare changes atomically (default is dry-run)")
    parser.add_argument("--root", default=str(root), help="repository root")
    args = parser.parse_args(argv)

    repo_root = Path(args.root)
    try:
        if args.check_corpus:
            report = check_corpus(repo_root)
            print(
                f"intake corpus check: research={report['research_records']} "
                f"repositories={report['repository_records']} "
                f"same_kind_collisions={len(report['same_kind_collisions'])} "
                f"pool_matches={report['pool_records_matching_ledger']}"
            )
            return 0
        if args.next_batch:
            print(json.dumps(select_next_batch(repo_root, limit=args.limit, kind=args.kind), indent=2, ensure_ascii=False))
            return 0
        if args.validate_candidate:
            candidate = json.loads(Path(args.validate_candidate).read_text(encoding="utf-8"))
            print(json.dumps(validate_candidate_payload(candidate, root=repo_root), indent=2, ensure_ascii=False))
            return 0
        if not args.date:
            raise ValueError("--date YYYY-MM-DD is required with --prepare")
        candidate = json.loads(Path(args.prepare).read_text(encoding="utf-8"))
        result = prepare_intake(candidate, args.date, root=repo_root, write=args.write)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except ValueError as error:
        print(f"ingest-intake: refused: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

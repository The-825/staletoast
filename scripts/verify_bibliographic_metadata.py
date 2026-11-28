"""Verify bibliographic metadata for research-ledger entries without claiming finding validation."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = ROOT / "site"
if str(SITE) not in sys.path:
    sys.path.insert(0, str(SITE))

from ledger_markdown import cells, source_link  # noqa: E402

LEDGER_PATH = DOCS / "collaborative-intelligence-research-ledger.md"
MANIFEST_PATH = DOCS / "staletoast-bibliographic-verifications.json"
REQUIRED_AUTHORITY = "bibliographic-identity-only; does not verify scientific claims, study quality, or adoption fitness"
REQUIRED_CLAIM_STATUS = "not-verified-by-bibliographic-check"
VALID_ID = re.compile(r"^(?:\d{3}|C-\d{3,})$")
YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
# Note: The research ledger contains 544 rows at baseline (542 active catalog
# rows plus 2 held rows C-078 and C-092 retained in the ledger per catalog-contract.json).
PLACEHOLDER_TOKENS = (
    "todo",
    "tbd",
    "placeholder",
    "unknown author",
    "unknown",
    "author name",
    "fill in",
    "author tbd",
    "n/a",
    "anonymous placeholder",
)


def parse_ledger_entries(ledger_text: str) -> list[dict[str, str]]:
    if "## Source ledger" not in ledger_text or "### Entry metadata" not in ledger_text:
        raise ValueError("Research ledger is missing expected Source ledger boundaries")
    section = ledger_text.split("## Source ledger", 1)[1].split("### Entry metadata", 1)[0]
    entries = []
    for line in section.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        row = cells(line)
        if len(row) not in {6, 7} or row[0] in {"ID", "Candidate ID", "---"}:
            continue
        sid, source_cell = row[0].strip(), row[1].strip()
        quote_idx = source_cell.find('["')
        author_prefix = source_cell[:quote_idx].strip().rstrip(",").strip() if quote_idx != -1 else ""
        title, url = source_link(source_cell)
        close_idx = source_cell.rfind(")")
        venue_suffix = source_cell[close_idx + 1:].strip().lstrip(",").strip() if close_idx != -1 else ""
        entries.append({
            "id": sid,
            "source_cell": source_cell,
            "author_prefix": author_prefix,
            "title": title.strip() if title != source_cell else "",
            "url": url.strip(),
            "venue_suffix": venue_suffix,
        })
    if not entries:
        raise ValueError("No research-ledger entries found")
    return entries


def is_post_baseline(sid: str, promoted_max: int, candidate_max: int) -> bool:
    if sid.startswith("C-"):
        return int(sid.split("-", 1)[1]) > candidate_max
    return int(sid) > promoted_max


def validate_bibliographic_metadata(ledger_text: str, manifest: dict) -> dict[str, int]:
    if manifest.get("schema_version") != "1.0":
        raise ValueError("Unsupported bibliographic verification schema_version")
    if manifest.get("authority") != REQUIRED_AUTHORITY:
        raise ValueError("Bibliographic manifest authority boundary was altered")
    baseline = manifest.get("baseline") or {}
    promoted_max = int(baseline.get("promoted_max_id", "0"))
    candidate_raw = str(baseline.get("candidate_max_id", "C-0"))
    if not candidate_raw.startswith("C-"):
        raise ValueError("baseline.candidate_max_id must start with C-")
    candidate_max = int(candidate_raw.split("-", 1)[1])
    exempt_ids = frozenset(baseline.get("historical_year_exempt_ids") or [])

    entries = parse_ledger_entries(ledger_text)
    by_id: dict[str, dict[str, str]] = {}
    for entry in entries:
        sid = entry["id"]
        if not VALID_ID.fullmatch(sid):
            raise ValueError(f"Malformed research ledger ID: {sid}")
        if sid in by_id:
            raise ValueError(f"Duplicate research ledger ID: {sid}")
        by_id[sid] = entry
        if not entry["author_prefix"]:
            raise ValueError(f"{sid}: missing author attribution before source title")
        lower_author = entry["author_prefix"].lower()
        for token in PLACEHOLDER_TOKENS:
            if token in lower_author:
                raise ValueError(f"{sid}: placeholder author attribution token {token!r} is not allowed")
        if not entry["title"]:
            raise ValueError(f"{sid}: missing quoted publication title")
        parsed_url = urlsplit(entry["url"])
        if parsed_url.scheme != "https" or not parsed_url.netloc or any(ch.isspace() for ch in entry["url"]):
            raise ValueError(f"{sid}: canonical URL must be a whitespace-free https:// link with a host")
        if sid not in exempt_ids and not YEAR_PATTERN.search(entry["source_cell"]):
            raise ValueError(f"{sid}: missing 4-digit publication or record year")

    unknown_exempt = exempt_ids - set(by_id)
    if unknown_exempt:
        raise ValueError(f"Unknown historical_year_exempt_ids: {sorted(unknown_exempt)}")

    records = manifest.get("verifications")
    if not isinstance(records, list) or not records:
        raise ValueError("verifications must be a non-empty list")
    verified_by_id: dict[str, dict] = {}
    for rec in records:
        sid = str(rec.get("id", "")).strip()
        if sid in verified_by_id:
            raise ValueError(f"Duplicate bibliographic verification entry for {sid}")
        if sid not in by_id:
            raise ValueError(f"Verification references unknown ledger ID: {sid}")
        if rec.get("claim_verification_status") != REQUIRED_CLAIM_STATUS:
            raise ValueError(
                f"{sid}: claim_verification_status must equal {REQUIRED_CLAIM_STATUS!r}; "
                "bibliographic identity never verifies scientific claims"
            )
        first_author = str(rec.get("verified_first_author", "")).strip()
        title = str(rec.get("verified_title", "")).strip()
        venue = str(rec.get("venue_or_record_type", "")).strip()
        url = str(rec.get("canonical_url", "")).strip()
        year = rec.get("year")
        verified_date = str(rec.get("verified_date", "")).strip()
        if not first_author or not title or not venue or not url:
            raise ValueError(f"{sid}: verification record is missing required bibliographic fields")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", verified_date):
            raise ValueError(f"{sid}: verified_date must be YYYY-MM-DD")
        if not isinstance(year, int) or not (1900 <= year <= 2100):
            raise ValueError(f"{sid}: year must be a 4-digit integer")

        row = by_id[sid]
        if row["title"] != title:
            raise ValueError(f"{sid}: ledger title {row['title']!r} does not match verified_title {title!r}")
        if row["url"] != url:
            raise ValueError(f"{sid}: ledger URL {row['url']!r} does not match canonical_url {url!r}")
        if not row["author_prefix"].startswith(first_author):
            raise ValueError(
                f"{sid}: ledger author prefix {row['author_prefix']!r} does not start with "
                f"verified_first_author {first_author!r}"
            )
        if str(year) not in row["source_cell"]:
            raise ValueError(f"{sid}: verified year {year} does not appear in ledger citation")
        if not row["venue_suffix"]:
            raise ValueError(f"{sid}: ledger citation is missing venue or record-type suffix")
        verified_by_id[sid] = rec

    missing_new = [
        sid for sid in by_id
        if is_post_baseline(sid, promoted_max, candidate_max) and sid not in verified_by_id
    ]
    if missing_new:
        raise ValueError(
            "New research-ledger entries require primary bibliographic verification in "
            f"docs/staletoast-bibliographic-verifications.json: {missing_new}"
        )

    return {
        "ledger_entries": len(entries),
        "manifest_verified": len(verified_by_id),
        "post_baseline_verified": sum(
            is_post_baseline(sid, promoted_max, candidate_max) for sid in verified_by_id
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    counts = validate_bibliographic_metadata(
        LEDGER_PATH.read_text(encoding="utf-8"),
        json.loads(MANIFEST_PATH.read_text(encoding="utf-8")),
    )
    print(
        f"bibliographic check: entries={counts['ledger_entries']} "
        f"manifest_verified={counts['manifest_verified']}"
    )


if __name__ == "__main__":
    main()

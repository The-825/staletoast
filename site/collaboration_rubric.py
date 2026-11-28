"""Evidence-backed collaborative intelligence scoring for weekly editions."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

METHOD = "collaborative-intelligence-v1"
FIRST_EDITION = "2026-11-23"
WEIGHTS = dict(
    direction=15,
    authority=15,
    coordination=20,
    execution=15,
    outcomes=15,
    evidence=15,
    contribution=5,
)
PATTERNS = {
    "one-human-one-agent",
    "one-human-many-agents",
    "many-humans-one-agent",
    "agent-to-agent",
    "many-humans-many-agents",
}
FINDING_DIRECTIONS = {
    "positive",
    "conditional",
    "null-or-negative",
    "design-only",
}

DIMENSIONS = {
    "direction": {
        "label": "Human goals and direction",
        "weight": 15,
        "question": "Can people express constraints, define success, and redirect work?",
        "anchors": {
            "0": "Checked absence or out of scope, with recorded reason.",
            "1": "Intended goal-setting or prompt steering described without workflow trace.",
            "2": "Worked example showing constraint expression or redirection.",
            "3": "Demonstrated human goal redirection under task change with known limits.",
            "4": "Compared against an alternative or failure case showing preserved human intent.",
        },
    },
    "authority": {
        "label": "Delegated authority and consent",
        "weight": 15,
        "question": "Do participants know who can commit, approve, intervene, or revoke?",
        "anchors": {
            "0": "Checked absence or out of scope, with recorded reason.",
            "1": "Nominal approval or policy gate described without revocation or scope detail.",
            "2": "Worked example separating recommendation from authorized action.",
            "3": "Function-bound authority and intervention demonstrated with explicit boundaries.",
            "4": "Tested against boundary violations, overreliance, or revocation scenarios.",
        },
    },
    "coordination": {
        "label": "Coordination and orchestration",
        "weight": 20,
        "question": "Do contributions change another participant's action and resolve handoffs or conflicts?",
        "anchors": {
            "0": "Checked absence or out of scope, with recorded reason.",
            "1": "Message passing or role topology described without handoff resolution evidence.",
            "2": "Worked handoff, shared state, or conflict-resolution example.",
            "3": "Demonstrated coordination gain or failure recovery across participants with stated limits.",
            "4": "Matched comparison isolating coordination mechanics from extra calls or shared context.",
        },
    },
    "execution": {
        "label": "Idea into action",
        "weight": 15,
        "question": "Can a decision or design change be traced into real use or verified workflow behavior?",
        "anchors": {
            "0": "Checked absence or out of scope, with recorded reason.",
            "1": "Conceptual proposal or README claim without executable or empirical trace.",
            "2": "Bounded prototype, benchmark task, or worked trace.",
            "3": "Verified workflow or field execution with observed behavior and stated transfer limits.",
            "4": "Sustained or multi-stage execution compared against a realistic operational baseline.",
        },
    },
    "outcomes": {
        "label": "Outcomes and learning",
        "weight": 15,
        "question": "Are results, effort, and failure modes compared against a credible alternative?",
        "anchors": {
            "0": "Checked absence or no outcome comparison recorded.",
            "1": "Self-reported or uncalibrated outcome claim without a matched baseline.",
            "2": "Bounded outcome measurement against a single baseline.",
            "3": "Disaggregated quality and effort comparison, including conditional or negative results.",
            "4": "Matched best-baseline comparison reporting gains, losses, burden, and lessons learned.",
        },
    },
    "evidence": {
        "label": "Strength of evidence",
        "weight": 15,
        "question": "How rigorous and verifiable are the methods, baselines, pinned code, or tests?",
        "anchors": {
            "0": "Unverified assertion or out of scope.",
            "1": "Abstract-level or README-only description without independent verification.",
            "2": "Pinned artifact, benchmark protocol, or observational study with visible limits.",
            "3": "Controlled experiment, preregistered synthesis, or reproducible test suite.",
            "4": "Independent replication, mature-field trial, or audited adversarial/holdout evaluation.",
        },
    },
    "contribution": {
        "label": "Distinct contribution and applicability",
        "weight": 5,
        "question": "Does the source add distinct decision value and a checkable local boundary?",
        "anchors": {
            "0": "Redundant or no distinct applicability check.",
            "1": "General domain relevance without a specific local test.",
            "2": "Identifies a concrete mechanism or risk for a named beneficiary.",
            "3": "Supplies a bounded, testable rule or counterexample not covered by prior lineage.",
            "4": "Changes a routing, governance, or evaluation decision with an observable local check.",
        },
    },
}

NEGATIVE_FINDING_RULE = (
    "Rigorous conditional, null, or negative empirical findings earn full outcomes and "
    "evidence credit when they test collaboration against a credible baseline. Ratings "
    "reflect evidentiary value for decisions, never whether AI or multi-agent collaboration won."
)


def _valid_iso_date(value: str) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def assess(card, *, expected_commit=None):
    ratings = card["ratings"]
    if set(ratings) != set(WEIGHTS):
        raise ValueError("scorecard needs all seven dimensions")
    if not set(card["patterns"]) <= PATTERNS:
        raise ValueError("unrecognized collaboration pattern")
    direction = card.get("finding_direction")
    if direction is not None and direction not in FINDING_DIRECTIONS:
        raise ValueError("unrecognized finding direction")
    points = unresolved = 0
    strongest = []
    highest = 0
    for name, weight in WEIGHTS.items():
        item = ratings[name]
        if item is None:
            unresolved += weight
            continue
        rating = item["rating"]
        if type(rating) is not int or not 0 <= rating <= 4 or not item.get("basis", "").strip():
            raise ValueError(f"invalid rating or missing evidence basis for {name}")
        points += rating * weight / 4
        if name != "evidence" and rating > 0 and rating >= highest:
            strongest = [name] if rating > highest else strongest + [name]
            highest = rating
    family = card.get("evidence_family")
    revision = card.get("source_revision")
    bound = bool(isinstance(revision, str) and re.fullmatch(r"(?:[0-9a-f]{40}|sha256:[0-9a-f]{64})", revision))
    revision_stale = bool(
        bound
        and expected_commit
        and re.fullmatch(r"[0-9a-f]{40}", revision)
        and revision != expected_commit
    )
    source = urlsplit(card["source"])
    cited = source.scheme == "https" and bool(source.hostname)
    attributed = isinstance(family, str) and bool(family.strip())
    result = dict(
        evidence_bound=bool(cited and bound and attributed and not revision_stale),
        evidence_family=family,
        source_revision=revision,
        established=points,
        unresolved=unresolved,
        strongest=strongest,
        strongest_rating=highest or None,
        ratings=ratings,
        source=card["source"],
        patterns=card["patterns"],
    )
    if direction is not None:
        result["finding_direction"] = direction
    if revision_stale:
        result["revision_stale"] = True
    return result


def prepare(rows, cards, *, repositories_by_id=None):
    scored, provisional = [], []
    repos = repositories_by_id or {}
    for row in rows:
        card = cards.get(row["id"])
        if card is None:
            provisional.append(dict(id=row["id"], established=0, unresolved=100))
            continue
        if not isinstance(card.get("source"), str) or not card["source"].strip():
            raise ValueError("scorecard requires a pinned evidence reference")
        expected_commit = repos.get(row["id"], {}).get("snapshot_commit")
        score = assess(card, expected_commit=expected_commit)
        if score["unresolved"] or not score["evidence_bound"]:
            provisional.append(dict(id=row["id"], **score))
            continue
        key = (
            -score["established"],
            *(-score["ratings"][k]["rating"] for k in ("evidence", "outcomes", "contribution")),
        )
        scored.append(dict(row, priority_key=key, rubric_score=score))
    scored.sort(key=lambda row: (row["priority_key"], row["id"]))
    prior_key = None
    for position, row in enumerate(scored, 1):
        if row["priority_key"] != prior_key:
            group = position
            prior_key = row["priority_key"]
        row["appraisal_priority_rank"] = group
    return scored, provisional


def _read_scorecard_file(path: Path) -> dict[str, dict]:
    edition_date = path.stem
    if not _valid_iso_date(edition_date):
        raise ValueError(f"{path.name}: scorecard filename must use YYYY-MM-DD")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("method") != METHOD or data.get("edition_date") != edition_date:
        raise ValueError("scorecard method or date mismatch")
    cards = {card["id"]: card for card in data["cards"]}
    if len(cards) != len(data["cards"]):
        raise ValueError("duplicate scorecard identity")
    return cards


def load_cards(docs, edition_date):
    """Load exact-date scorecards when present, carrying forward earlier dated cards up to edition_date."""
    return load_cards_through(docs, edition_date)


def load_cards_through(docs, edition_date, *, held_ids=None):
    if not _valid_iso_date(edition_date):
        raise ValueError("edition_date must use YYYY-MM-DD")
    folder = Path(docs) / "staletoast-scorecards"
    if not folder.exists():
        return {}
    held = set(held_ids or ())
    merged: dict[str, dict] = {}
    for path in sorted(folder.glob("*.json")):
        file_date = path.stem
        if not _valid_iso_date(file_date):
            raise ValueError(f"{path.name}: scorecard filename must use YYYY-MM-DD")
        if file_date > edition_date:
            continue
        cards = _read_scorecard_file(path)
        for identity, card in cards.items():
            if identity in held and file_date < edition_date:
                continue
            merged[identity] = card
    for identity in list(merged):
        if identity in held:
            # Same-date held cards stay in merged so make_edition rejects invalid active targets;
            # earlier carried-forward cards for later-held records are skipped above.
            pass
    return merged


def format_rubric_reason(score: dict) -> str:
    strongest = [DIMENSIONS[name]["label"].lower() for name in score.get("strongest", []) if name in DIMENSIONS]
    base = f"Weighted collaboration score: {score['established']}"
    if strongest:
        return f"{base} (strongest: {', '.join(strongest[:2])})"
    return base


def export_web_scorecards(docs: Path, repositories: list[dict] | None = None) -> dict:
    folder = Path(docs) / "staletoast-scorecards"
    repos_by_id = {row["id"]: row for row in (repositories or []) if "id" in row}
    latest_date = None
    recorded_dates: dict[str, str] = {}
    merged: dict[str, dict] = {}
    if folder.exists():
        for path in sorted(folder.glob("*.json")):
            cards = _read_scorecard_file(path)
            latest_date = path.stem
            for identity, card in cards.items():
                merged[identity] = card
                recorded_dates[identity] = path.stem
    assessed_cards: dict[str, dict] = {}
    for identity, card in sorted(merged.items()):
        expected_commit = repos_by_id.get(identity, {}).get("snapshot_commit")
        assessed = assess(card, expected_commit=expected_commit)
        rated_count = sum(1 for item in assessed["ratings"].values() if item is not None)
        assessed_cards[identity] = {
            "id": identity,
            "recorded_edition_date": recorded_dates[identity],
            "complete": assessed["unresolved"] == 0 and assessed["evidence_bound"],
            "rated_dimensions": rated_count,
            "total_dimensions": len(WEIGHTS),
            **assessed,
        }
    return {
        "schema_version": "1.0",
        "method": METHOD,
        "first_edition": FIRST_EDITION,
        "authority": (
            "evidence-backed multi-dimensional collaboration rubric; incomplete or "
            "unpinned cards remain provisional and do not rank on the Hot 100"
        ),
        "negative_finding_rule": NEGATIVE_FINDING_RULE,
        "latest_scorecard_date": latest_date,
        "patterns": sorted(PATTERNS),
        "finding_directions": sorted(FINDING_DIRECTIONS),
        "dimensions": [
            {
                "id": key,
                "label": meta["label"],
                "weight": meta["weight"],
                "question": meta["question"],
                "anchors": meta["anchors"],
            }
            for key, meta in DIMENSIONS.items()
        ],
        "cards": assessed_cards,
    }

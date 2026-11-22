"""Evidence-backed collaborative intelligence scoring for weekly editions."""

import json
from pathlib import Path

METHOD = "collaborative-intelligence-v1"
FIRST_EDITION = "2026-11-23"
WEIGHTS = dict(direction=15, authority=15, coordination=20, execution=15,
               outcomes=15, evidence=15, contribution=5)
PATTERNS = {"one-human-one-agent", "one-human-many-agents", "many-humans-one-agent",
            "agent-to-agent", "many-humans-many-agents"}


def assess(card):
    ratings = card["ratings"]
    if set(ratings) != set(WEIGHTS):
        raise ValueError("scorecard needs all seven dimensions")
    if not set(card["patterns"]) <= PATTERNS:
        raise ValueError("unrecognized collaboration pattern")
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
    return dict(established=points, unresolved=unresolved, strongest=strongest,
                strongest_rating=highest or None, ratings=ratings, source=card["source"], patterns=card["patterns"])


def prepare(rows, cards):
    scored, provisional = [], []
    for row in rows:
        card = cards.get(row["id"])
        if card is None:
            provisional.append(dict(id=row["id"], established=0, unresolved=100))
            continue
        score = assess(card)
        if not isinstance(card["source"], str) or not card["source"].strip():
            raise ValueError("scorecard requires a pinned evidence reference")
        if score["unresolved"]:
            provisional.append(dict(id=row["id"], **score))
            continue
        key = (-score["established"], *(-score["ratings"][k]["rating"]
                                       for k in ("evidence", "outcomes", "contribution")))
        scored.append(dict(row, priority_key=key, rubric_score=score))
    scored.sort(key=lambda row: (row["priority_key"], row["id"]))
    prior_key = None
    for position, row in enumerate(scored, 1):
        if row["priority_key"] != prior_key:
            group = position
            prior_key = row["priority_key"]
        row["appraisal_priority_rank"] = group
    return scored, provisional


def load_cards(docs, edition_date):
    path = Path(docs) / "staletoast-scorecards" / (edition_date + ".json")
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["method"] != METHOD or data["edition_date"] != edition_date:
        raise ValueError("scorecard method or date mismatch")
    cards = {card["id"]: card for card in data["cards"]}
    if len(cards) != len(data["cards"]):
        raise ValueError("duplicate scorecard identity")
    return cards

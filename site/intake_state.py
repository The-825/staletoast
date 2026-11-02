"""Intake state for expanded corpora: held dispositions and explicit appraisal states.

Standard library only. Appraisal state comes from structured batch data
(`screen_method`), never from explanatory flag text. Dispositions are required and
fail closed, so a missing or malformed file can never publish held sources.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BATCH_NAME = "staletoast-expansion-2026-11-01.json"
DISPOSITIONS_NAME = "staletoast-source-dispositions.json"
AUTOMATED = "automated-screen"
SCREENED = "source-screened"
APPRAISAL_STATES = (AUTOMATED, SCREENED)
INTAKE_LABEL = "intake awaiting appraisal"
SCREEN_METHODS = {
    "research": "automated-abstract-topic-screen-v1",
    "repository": "automated-readme-relevance-screen-v1",
}
BATCH_ARRAYS = {"research": "research", "repository": "repositories"}


def _read_json(path: Path, what: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"{what} is required and could not be read: {path.name}") from exc


def load_dispositions(docs: Path = DOCS) -> dict[str, dict]:
    """Return held dispositions by source ID. Missing or unknown data raises."""
    data = _read_json(docs / DISPOSITIONS_NAME, "source dispositions")
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("records"), list):
        raise ValueError("source dispositions must have schema_version 1 and a records list")
    held: dict[str, dict] = {}
    for record in data["records"]:
        if not isinstance(record, dict):
            raise ValueError("source disposition must be an object")
        identity = record.get("id")
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError("source disposition lacks an ID")
        if record.get("kind") not in BATCH_ARRAYS:
            raise ValueError(f"{identity}: disposition kind must be research or repository")
        if record.get("state") != "held":
            raise ValueError(f"{identity}: unknown disposition state")
        if not isinstance(record.get("reason"), str) or not record["reason"].strip():
            raise ValueError(f"{identity}: held disposition needs a reason")
        if "replacement_id" in record and (not isinstance(record["replacement_id"], str) or not record["replacement_id"].strip()):
            raise ValueError(f"{identity}: replacement_id must be nonempty text when present")
        if identity in held:
            raise ValueError(f"{identity}: duplicate disposition")
        held[identity] = record
    for identity, record in held.items():
        replacement = record.get("replacement_id")
        if replacement and (replacement == identity or replacement in held):
            raise ValueError(f"{identity}: replacement must be a different, active source")
    return held


def intake_index(batch: dict) -> dict[str, dict]:
    """Index every batch record, held ones included, by source ID."""
    index: dict[str, dict] = {}
    for kind, array in BATCH_ARRAYS.items():
        for record in batch.get(array, []):
            identity = record.get("id")
            if not isinstance(identity, str) or identity in index:
                raise ValueError(f"batch record has a missing or duplicate ID: {identity}")
            if record.get("kind") != kind:
                raise ValueError(f"{identity}: batch record is in the wrong array")
            index[identity] = record
    return index


class IntakeState:
    def __init__(self, docs: Path = DOCS):
        self.docs = docs
        self.held = load_dispositions(docs)
        self.batch = _read_json(docs / BATCH_NAME, "expansion batch")
        self.intake = intake_index(self.batch)
        self._hashes = {
            field: hashlib.sha256((docs / name).read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            for field, name in (("disposition_source_sha256", DISPOSITIONS_NAME), ("batch_source_sha256", BATCH_NAME))
        }
        for identity, record in self.held.items():
            target = self.intake.get(identity)
            if target is None or target["kind"] != record["kind"]:
                raise ValueError(f"{identity}: held source is not a batch record of that kind")
            replacement = record.get("replacement_id")
            if replacement and (replacement not in self.intake or self.intake[replacement]["kind"] != record["kind"]):
                raise ValueError(f"{identity}: replacement is not a batch record of that kind")

    def is_held(self, kind: str, identity: str) -> bool:
        record = self.held.get(identity)
        return bool(record) and record["kind"] == kind

    def held_ids(self, kind: str) -> set[str]:
        return {identity for identity, record in self.held.items() if record["kind"] == kind}

    def appraisal_state(self, kind: str, identity: str) -> str:
        record = self.intake.get(identity)
        if record is None:
            return SCREENED
        if record["kind"] != kind or record.get("screen_method") != SCREEN_METHODS[kind]:
            raise ValueError(f"{identity}: unknown intake screen method")
        return AUTOMATED

    def source_hashes(self) -> dict[str, str]:
        return dict(self._hashes)


def validate_catalog_semantics(research: list[dict], repositories: list[dict]) -> None:
    """Fail if generated catalogs break the schema 2.0 appraisal contract."""
    ranked = [row for row in research if row.get("appraisal_state") == SCREENED]
    for row in research + repositories:
        if row.get("appraisal_state") not in APPRAISAL_STATES:
            raise ValueError(f"{row.get('id')}: appraisal_state must be one of {APPRAISAL_STATES}")
    seen_unranked = False
    for row in research:
        if row["appraisal_state"] == AUTOMATED:
            seen_unranked = True
            if any(row.get(field) is not None for field in ("evidenceOrder", "directness", "horizon", "directnessValue", "horizonValue")) or row.get("claims"):
                raise ValueError(f"{row['id']}: automated research must have no order, grade or claim")
        else:
            if seen_unranked:
                raise ValueError(f"{row['id']}: appraised research must precede automated screens")
            if not isinstance(row.get("evidenceOrder"), int):
                raise ValueError(f"{row['id']}: appraised research needs an evidence order")
    if [row["evidenceOrder"] for row in ranked] != list(range(1, len(ranked) + 1)):
        raise ValueError("appraised evidence order must be contiguous from 1")
    for row in repositories:
        if row["appraisal_state"] == AUTOMATED:
            if row.get("evidence_depth") != "readme-relevance-screened" or set(row["mechanisms"].values()) != {"U"} or row.get("claims"):
                raise ValueError(f"{row['id']}: automated repository carries appraisal findings")
        elif row.get("evidence_depth") == "readme-relevance-screened":
            raise ValueError(f"{row['id']}: relevance screen lacks an automated intake record")

"""Compare the published Hot100 method with a read-only rubric candidate."""

from __future__ import annotations

import json
from pathlib import Path

import build_discovery as discovery
import build_priorities as priorities
from intake_state import AUTOMATED


METHOD = "editorial-routing-v2-preview"
# Map claims with a directly relevant recorded repository mechanism dimension.
CLAIM_MECHANISMS = {
    "CI-001": "collaboration_baseline",
    "CI-002": "evaluation_surface",
    "CI-004": "cost_burden",
    "CI-006": "trace_recovery",
    "CI-007": "human_authority",
    "CI-008": "change_expiry",
    "CI-009": "memory_context",
    "CI-010": "memory_context",
    "CI-011": "human_authority",
    "CI-013": "human_authority",
    "CI-014": "memory_context",
    "CI-016": "collaboration_topology",
    "CI-017": "independent_verification",
}
# Claims where README mechanism visibility cannot establish behavioral or task-specific validity.
UNMAPPED_CLAIM_REASONS = {
    "CI-003": "behavioral reliance requires human study observation rather than repository feature presence",
    "CI-005": "capability boundaries depend on empirical task-frontier comparisons rather than static README text",
    "CI-012": "explanation effects require observed human error-detection behavior rather than UI feature visibility",
    "CI-015": "output diversity across repeated work requires outcome measurement rather than static architecture",
}


def _scope_components_by_claim(docs: Path | None) -> dict[str, list[str]]:
    if docs is None:
        return {}
    path = Path(docs) / "staletoast-scope-map.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    mapping: dict[str, list[str]] = {}
    for comp in data.get("components", []):
        cid = comp.get("id")
        for claim in comp.get("related_claims", []):
            if cid:
                mapping.setdefault(claim, []).append(cid)
    return {claim: sorted(set(values)) for claim, values in mapping.items()}


def preview_priorities(payload, landscape, *, docs: Path | None = None):
    sources = {row["id"]: row for row in landscape["repositories"]}
    scope_by_claim = _scope_components_by_claim(docs)
    preview = dict(payload)
    bases = {}

    def key(row, category):
        baseline_key = row["priority_key"]
        if row["appraisal_state"] == AUTOMATED or row.get("automated_screen"):
            return priorities.INTAKE_KEY
        gap = baseline_key[0]
        lead_claim = row["priority_claim"]
        if category == "research":
            depth = row["review_depth"]
            basis = dict(
                lead_claim=lead_claim,
                directness=row["directness"],
                review_depth=depth,
                horizon=row["horizon"],
            )
            if lead_claim in scope_by_claim:
                basis["scope_components"] = scope_by_claim[lead_claim]
            bases[row["id"]] = basis
            return gap, baseline_key[1], int(depth != "selected-full-text")
        dimension = CLAIM_MECHANISMS.get(lead_claim)
        mechanisms = sources[row["id"]].get("mechanisms") or {}
        status = mechanisms.get(dimension) if dimension else None
        basis = dict(
            lead_claim=lead_claim,
            claim_mechanism=dimension,
            observed_status=status,
            lifecycle=row["lifecycle"],
        )
        if dimension is None and lead_claim in UNMAPPED_CLAIM_REASONS:
            basis["unmapped_reason"] = UNMAPPED_CLAIM_REASONS[lead_claim]
        if lead_claim in scope_by_claim:
            basis["scope_components"] = scope_by_claim[lead_claim]
        bases[row["id"]] = basis
        return gap, {"V": 0, "P": 1}.get(status, 2), 0

    for category in ("research", "repositories"):
        rows = [dict(row) for row in payload[category]]
        preview[category] = priorities.rank(rows, lambda row: key(row, category))
    return preview, bases


def compare(edition_date, payload, landscape, earlier, held_repository_ids, *, docs: Path | None = None):
    baseline = discovery.make_edition(
        edition_date, payload, landscape, earlier, held_repository_ids
    )
    candidate, bases = preview_priorities(payload, landscape, docs=docs)
    preview = discovery.make_edition(
        edition_date, candidate, landscape, earlier, held_repository_ids
    )
    comparisons = {}
    for category, current_chart in baseline["charts"].items():
        trial_chart = preview["charts"][category]
        before = {row["id"]: row["position"] for row in current_chart["entries"]}
        after = {row["id"]: row["position"] for row in trial_chart["entries"]}
        baseline_eligible = before.keys() | set(current_chart["off_chart_ids"])
        preview_eligible = after.keys() | set(trial_chart["off_chart_ids"])
        if baseline_eligible != preview_eligible:
            raise ValueError(f"{category}: preview changed chart eligibility")
        cutoff_group = trial_chart["entries"][-1]["priority_group"] if len(after) == 100 else None
        outside = set(trial_chart["off_chart_ids"])
        cutoff_alternatives = [
            dict(
                id=row["id"],
                title=row.get("title", row.get("repository")),
                evidence_basis=bases[row["id"]],
            )
            for row in candidate[category]
            if row["id"] in outside and row["appraisal_priority_rank"] == cutoff_group
        ]
        comparisons[category] = dict(
            eligible_count=trial_chart["eligible_count"],
            chart_count=len(after),
            retained_count=len(before.keys() & after.keys()),
            baseline_cutoff_tied_outside=current_chart["cutoff_tied_outside_chart"],
            preview_cutoff_tied_outside=trial_chart["cutoff_tied_outside_chart"],
            preview_cutoff_alternatives=cutoff_alternatives,
            entering=[identity for identity in after if identity not in before],
            leaving=[identity for identity in before if identity not in after],
            positions=[
                dict(
                    id=row["id"],
                    title=row["title"],
                    preview_position=row["position"],
                    baseline_position=before.get(row["id"]),
                    priority_group=row["priority_group"],
                    evidence_basis=bases[row["id"]],
                )
                for row in trial_chart["entries"]
            ],
        )
    return dict(
        mode="read-only comparison",
        edition_date=edition_date,
        baseline_method=baseline["method_version"],
        preview_method=METHOD,
        mapped_claims=sorted(CLAIM_MECHANISMS),
        unmapped_claims=UNMAPPED_CLAIM_REASONS,
        prior_frozen_edition=earlier[-1]["edition_date"],
        source_hashes={k: v for k, v in payload.items() if k.endswith("_source_sha256")},
        comparisons=comparisons,
    )

"""Compare the published Hot100 method with a read-only rubric candidate."""

from __future__ import annotations

import build_discovery as discovery
import build_priorities as priorities
from intake_state import AUTOMATED


METHOD = "editorial-routing-v2-preview"
# Map only claims with a directly relevant recorded repository dimension.
CLAIM_MECHANISMS = {
    "CI-001": "collaboration_baseline",
    "CI-002": "evaluation_surface",
    "CI-004": "cost_burden",
    "CI-006": "trace_recovery",
    "CI-007": "human_authority",
    "CI-008": "change_expiry",
    "CI-009": "memory_context",
    "CI-011": "human_authority",
    "CI-017": "independent_verification",
}


def preview_priorities(payload, landscape):
    sources = {row["id"]: row for row in landscape["repositories"]}
    preview = dict(payload)
    bases = {}

    def key(row, category):
        baseline_key = row["priority_key"]
        if row["appraisal_state"] == AUTOMATED or row.get("automated_screen"):
            return priorities.INTAKE_KEY
        gap = baseline_key[0]
        if category == "research":
            depth = row["review_depth"]
            bases[row["id"]] = dict(lead_claim=row["priority_claim"], directness=row["directness"], review_depth=depth,
                                    horizon=row["horizon"])
            return gap, baseline_key[1], int(depth != "selected-full-text")
        dimension = CLAIM_MECHANISMS.get(row["priority_claim"])
        status = sources[row["id"]]["mechanisms"].get(dimension) if dimension else None
        bases[row["id"]] = dict(lead_claim=row["priority_claim"], claim_mechanism=dimension, observed_status=status,
                                lifecycle=row["lifecycle"])
        return gap, {"V": 0, "P": 1}.get(status, 2), 0

    for category in ("research", "repositories"):
        rows = [dict(row) for row in payload[category]]
        preview[category] = priorities.rank(rows, lambda row: key(row, category))
    return preview, bases


def compare(edition_date, payload, landscape, earlier, held_repository_ids):
    baseline = discovery.make_edition(edition_date, payload, landscape, earlier,
                                      held_repository_ids)
    candidate, bases = preview_priorities(payload, landscape)
    preview = discovery.make_edition(edition_date, candidate, landscape, earlier,
                                     held_repository_ids)
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
            dict(id=row["id"], title=row.get("title", row.get("repository")),
                 evidence_basis=bases[row["id"]])
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
                dict(id=row["id"], title=row["title"], preview_position=row["position"],
                     baseline_position=before.get(row["id"]), priority_group=row["priority_group"],
                     evidence_basis=bases[row["id"]])
                for row in trial_chart["entries"]
            ],
        )
    return dict(mode="read-only comparison", edition_date=edition_date,
                baseline_method=baseline["method_version"], preview_method=METHOD,
                prior_frozen_edition=earlier[-1]["edition_date"],
                source_hashes={k: v for k, v in payload.items() if k.endswith("_source_sha256")},
                comparisons=comparisons)

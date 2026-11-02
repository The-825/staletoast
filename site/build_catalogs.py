from __future__ import annotations

import json
import re
from pathlib import Path
from ledger_markdown import cells, source_link
from build_priorities import identified_rows
from intake_state import AUTOMATED, IntakeState, validate_catalog_semantics

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = ROOT / "site"
READER_TOPICS = {
    "CI-001": "When collaboration helps",
    "CI-002": "Check each step of the work",
    "CI-003": "When to trust or question AI",
    "CI-004": "Time and effort required",
    "CI-005": "Match abilities to the task",
    "CI-006": "Understand and recover from failures",
    "CI-007": "Who can approve each action",
    "CI-008": "Recheck evidence when things change",
    "CI-009": "Remember decisions and context",
    "CI-010": "Use enough context with less private data",
    "CI-011": "Keep people in control",
    "CI-012": "Explanations that help people act",
    "CI-013": "Know when to hand work to a person",
    "CI-014": "Choose the right way to find information",
    "CI-015": "Keep ideas and perspectives varied",
    "CI-016": "Use more agents only when they help",
    "CI-017": "Check AI improvements independently",
}


def table_rows(path: Path, width: int) -> list[list[str]]:
    found = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        row = cells(line)
        if len(row) == width and row[0] not in {"ID", "---"}:
            found.append(row)
    return found


def research_catalog(docs: Path | None = None) -> list[dict[str, object]]:
    docs = docs or DOCS
    text = (docs / "collaborative-intelligence-research-ledger.md").read_text(encoding="utf-8")
    text = text.split("## Source ledger", 1)[1].split("### Entry metadata", 1)[0]
    ledger = identified_rows(text, {6, 7})
    appraisals = identified_rows((docs / "collaborative-intelligence-source-appraisals.md").read_text(encoding="utf-8"), {7, 8})
    if set(ledger) != set(appraisals):
        raise ValueError("Research sources and appraisals must cover the same identities")
    state = IntakeState(docs)
    if not state.held_ids("research") <= set(ledger):
        raise ValueError("Held research source is missing from the ledger")
    proximity = {"D3": 0, "D2": 1, "D1": 2, "D0": 3}
    horizon_order = {"longitudinal": 0, "repeated": 1, "single": 2, "technical": 3, "retrospective": 4, "not observed": 5}
    horizon_value = {"longitudinal": 3, "repeated": 2, "single": 1, "technical": 1, "retrospective": 1, "not observed": 0}
    family_labels = {
        "AGENT-EVAL": "Agent evaluation", "AGENT-SCALE": "Large-scale agent systems", "AGENT-SECURITY": "Agent security",
        "ALGO-USE": "Algorithm use and reliance", "ALLOCATION": "Task allocation", "AUTO-HF": "Automation and human factors",
        "BANSAL-TEAM": "Human-AI team performance", "CLINICAL-TEAM": "Clinical team collaboration", "DEFER": "Learning when to defer",
        "DELEGATION": "Delegation", "DEV-PROD": "Developer productivity", "FAIRNESS-HCAI": "Fairness and human-centered AI",
        "FEEDBACK-LOOP": "Feedback loops", "FIELD-PROD": "Field productivity", "FIELD-TEAM": "Field team performance",
        "JOINT-ACTIVITY": "Joint activity", "MEM-ARCH": "Memory architecture", "MEM-EVAL": "Memory evaluation",
        "MOTIVATION": "Motivation", "MSR-AGENTS": "Microsoft Research agent studies", "MSR-WORK": "Microsoft Research work-practice studies",
        "MULTIAGENT": "Multi-agent systems", "ORG-SYN": "Organizational synthesis", "PORTFOLIO-DIVERSITY": "Portfolio diversity",
        "RELIANCE-FRICTION": "Reliance and friction", "RETRIEVAL": "Retrieval", "SELF-REFINE": "Self-refinement",
        "SYNERGY-META": "Collaboration synergy meta-analysis", "TEAM-COG": "Team cognition", "TRUST-REL": "Trust and reliance",
        "XAI-BEHAVIOR": "Explainability and behavior", "XAI-GUIDANCE": "Explainability guidance",
    }
    output = []
    for source_id, row in ledger.items():
        if state.is_held("research", source_id):
            continue
        _, source, level, finding, impact, boundary = row[:6]
        if len(row) == 7:
            boundary += " " + row[6]
        app = appraisals[source_id]
        title, url = source_link(source)
        claims = [x.strip() for x in app[6].split(",") if x.strip()]
        appraisal_state = state.appraisal_state("research", source_id)
        automated = appraisal_state == AUTOMATED
        number = int(source_id.split("-")[-1])
        output.append({
            "id": source_id, "title": title, "url": url, "levelEvidence": level,
            "finding": finding, "impact": impact.replace("**", ""), "boundary": boundary,
            "design": app[1],
            # Automated screens carry no grade; the ledger placeholder is never published.
            "directness": None if automated else app[2], "directnessValue": None if automated else int(app[2][1]),
            "family": app[3], "familyLabel": family_labels.get(app[3], app[3]),
            "horizon": None if automated else app[4], "horizonValue": None if automated else horizon_value.get(app[4], 0),
            "flags": app[5], "claims": claims, "claimCount": len(claims),
            "appraisal_state": appraisal_state,
            "record_state": "reviewed-catalog" if source_id.isdigit() else "candidate-not-promoted",
            "review_depth": (re.match(r"(selected-full-text|abstract-only):", app[5])[1] if re.match(r"(selected-full-text|abstract-only):", app[5]) else "screened-structural" if source_id.isdigit() else "prior-screened-candidate"),
            "citationSignal": "not collected",
            "_sort": [1, number] if automated else [0, proximity.get(app[2][:2], 9), horizon_order.get(app[4], 9), 0 if source_id.isdigit() else 1, number],
        })
    output.sort(key=lambda item: item["_sort"])
    ranked = sum(item["appraisal_state"] != AUTOMATED for item in output)
    for position, item in enumerate(output, 1):
        # Appraised records keep their prior 1..N order; automated intake is unranked and sorted last.
        item["evidenceOrder"] = position if item["appraisal_state"] != AUTOMATED else None
        item["evidenceOrderCount"] = ranked
        del item["_sort"]
    return output


def repository_catalog(docs: Path | None = None) -> list[dict[str, object]]:
    docs = docs or DOCS
    landscape = json.loads((docs / "collaborative-intelligence-repository-landscape.json").read_text(encoding="utf-8"))
    state = IntakeState(docs)
    if not state.held_ids("repository") <= {item["id"] for item in landscape["repositories"]}:
        raise ValueError("Held repository is missing from the landscape")
    output = [item for item in landscape["repositories"] if not state.is_held("repository", item["id"])]
    later_ids = set(landscape.get("post_import_repository_ids", []))
    for item in output:
        item["appraisal_state"] = state.appraisal_state("repository", item["id"])
    unknown_depths = {item["evidence_depth"] for item in output} - {"readme-screened", "source-assessment", "readme-relevance-screened"}
    if unknown_depths:
        raise ValueError(f"unknown repository evidence depths: {sorted(unknown_depths)}")
    output.sort(key=lambda item: (item["stars_observed"] is None, -(item["stars_observed"] or 0), item["repository"]))
    popularity_count = sum(item["stars_observed"] is not None for item in output)
    category_popularity_counts: dict[str, int] = {}
    for item in output:
        if item["stars_observed"] is not None:
            category = item["category"]
            category_popularity_counts[category] = category_popularity_counts.get(category, 0) + 1
    category_counts: dict[str, int] = {}
    for rank, item in enumerate(output, 1):
        item["catalogOrder"] = rank
        item["popularityOrder"] = rank if item["stars_observed"] is not None else None
        category = item["category"]
        category_counts[category] = category_counts.get(category, 0) + 1
        item["categoryPopularityOrder"] = category_counts[category] if item["stars_observed"] is not None else None
        item["visibleMechanisms"] = sum(value == "V" for value in item["mechanisms"].values())
        item["partialMechanisms"] = sum(value == "P" for value in item["mechanisms"].values())
        item["unknownMechanisms"] = sum(value == "U" for value in item["mechanisms"].values())
        item["mechanismTotal"] = len(item["mechanisms"])
        item["claimCount"] = len(item["claims"])
        item["lastReviewed"] = item["snapshot_date"]
        if item["stars_observed"] is None:
            item["starsObservedDate"] = None
        elif item["appraisal_state"] == AUTOMATED or item["id"] in later_ids:
            # New intake never inherits the older global observation date.
            if not item.get("popularity_observed_date"):
                raise ValueError(f"{item['id']}: new intake needs its own popularity observation date")
            item["starsObservedDate"] = item["popularity_observed_date"]
        else:
            item["starsObservedDate"] = item.get("popularity_observed_date", item.get("stars_observed_date", landscape["popularity_observed_date"]))
        item["licenseBasis"] = "github-reported-unverified" if item["appraisal_state"] == AUTOMATED else "ledger-recorded"
        item["popularityCount"] = popularity_count
        item["categoryPopularityCount"] = category_popularity_counts.get(category, 0)
        item["ledgerRepositoryCount"] = len(output)
        item["detailedReviewCount"] = sum(row["evidence_depth"] == "readme-screened" for row in output)
    totals: dict[str, int] = {}
    for item in output:
        totals[item["category"]] = totals.get(item["category"], 0) + 1
    for item in output:
        item["categoryRepositoryCount"] = totals[item["category"]]
    return output


def claim_catalog() -> list[dict[str, str]]:
    text = (DOCS / "collaborative-intelligence-claim-register.md").read_text(encoding="utf-8")
    themes = {
        "CI-001": "Outcomes and burden", "CI-004": "Outcomes and burden", "CI-005": "Outcomes and burden", "CI-015": "Outcomes and burden", "CI-016": "Outcomes and burden",
        "CI-002": "Workflow evidence", "CI-006": "Workflow evidence", "CI-008": "Workflow evidence", "CI-017": "Workflow evidence",
        "CI-003": "Authority and reliance", "CI-007": "Authority and reliance", "CI-011": "Authority and reliance", "CI-012": "Authority and reliance", "CI-013": "Authority and reliance",
        "CI-009": "Memory and grounding", "CI-010": "Memory and grounding", "CI-014": "Memory and grounding",
    }
    output = []
    for section in re.split(r"^### ", text, flags=re.MULTILINE)[1:]:
        heading, body = section.split("\n", 1)
        match = re.match(r"(CI-\d+):\s*(.+)", heading)
        if not match:
            continue
        def field(label: str) -> str:
            found = re.search(rf"^- \*\*{re.escape(label)}:\*\*\s*(.+(?:\n  .+)*)", body, flags=re.MULTILINE)
            return " ".join(found.group(1).split()) if found else ""
        claim = re.search(r"\*\*Claim\.\*\*\s*(.*?)(?=\n\n- \*\*)", body, flags=re.DOTALL)
        output.append({
            "id": match.group(1), "title": match.group(2), "readerLabel": READER_TOPICS[match.group(1)], "theme": themes.get(match.group(1), "Other"),
            "claim": " ".join(claim.group(1).split()) if claim else "",
            "supports": field("Supports"), "profile": field("Profile"),
            "disposition": field("Disposition").replace("`", ""),
            "nullCase": field("Null case"), "nextTest": field("Next test"),
        })
    return output


def write(name: str, value: object) -> None:
    target = SITE / "data" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    research, repositories = research_catalog(), repository_catalog()
    validate_catalog_semantics(research, repositories)
    write("research.json", research)
    write("repositories.json", repositories)
    write("claims.json", claim_catalog())

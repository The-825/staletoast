import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from collaboration_rubric import (
    DIMENSIONS,
    FINDING_DIRECTIONS,
    METHOD,
    WEIGHTS,
    assess,
    export_web_scorecards,
    format_rubric_reason,
    load_cards_through,
    prepare,
)


class RubricTests(unittest.TestCase):
    def _full_card(self, **overrides):
        base = dict(
            patterns=["many-humans-many-agents"],
            source="https://example.org/synthetic-paper",
            source_revision="a" * 40,
            evidence_family="synthetic-family",
            ratings={key: dict(rating=4, basis="documented example") for key in WEIGHTS},
        )
        base.update(overrides)
        return base

    def test_partial_complete_and_tied(self):
        full = self._full_card()
        partial = deepcopy(full)
        partial["ratings"]["outcomes"] = None
        rows = [dict(id=i) for i in ("b", "a", "c", "d")]
        ranked, provisional = prepare(rows, dict(a=full, b=full, c=partial))
        self.assertEqual([(r["id"], r["appraisal_priority_rank"]) for r in ranked], [("a", 1), ("b", 1)])
        self.assertEqual(ranked[0]["rubric_score"]["established"], 100)
        self.assertEqual([(r["established"], r["unresolved"]) for r in provisional], [(85, 15), (0, 100)])
        self.assertEqual(ranked[0]["rubric_score"]["evidence_family"], "synthetic-family")
        accepted, pending = prepare([dict(id="a")], {"a": dict(full, source="TBD")})
        self.assertEqual(accepted, [])
        self.assertFalse(pending[0]["evidence_bound"])
        for missing in ("source_revision", "evidence_family"):
            card = dict(full)
            del card[missing]
            accepted, pending = prepare([dict(id="a")], {"a": card})
            self.assertEqual(accepted, [])
            self.assertFalse(pending[0]["evidence_bound"])
        full["ratings"]["execution"]["rating"] = True
        with self.assertRaises(ValueError):
            prepare(rows, dict(a=full))

    def test_dimensions_weights_and_finding_directions(self):
        self.assertEqual(set(WEIGHTS), set(DIMENSIONS))
        self.assertEqual(100, sum(meta["weight"] for meta in DIMENSIONS.values()))
        for direction in FINDING_DIRECTIONS:
            card = self._full_card(finding_direction=direction)
            score = assess(card)
            self.assertEqual(direction, score["finding_direction"])
            self.assertEqual(100, score["established"])
        with self.assertRaisesRegex(ValueError, "finding direction"):
            assess(self._full_card(finding_direction="hype-only"))
        bad_basis = self._full_card()
        bad_basis["ratings"]["direction"]["basis"] = None
        with self.assertRaisesRegex(ValueError, "missing evidence basis"):
            assess(bad_basis)

    def test_stale_repository_commit_moves_card_to_provisional(self):
        card = self._full_card(source_revision="a" * 40)
        ranked, provisional = prepare(
            [dict(id="R-001")],
            {"R-001": card},
            repositories_by_id={"R-001": {"snapshot_commit": "b" * 40}},
        )
        self.assertEqual([], ranked)
        self.assertEqual(1, len(provisional))
        self.assertFalse(provisional[0]["evidence_bound"])
        self.assertTrue(provisional[0]["revision_stale"])

    def test_carry_forward_and_web_export(self):
        with TemporaryDirectory() as tmp:
            docs = Path(tmp)
            sc_dir = docs / "staletoast-scorecards"
            sc_dir.mkdir()
            first = self._full_card(id="R-001", finding_direction="null-or-negative")
            held_card = self._full_card(id="R-HELD")
            (sc_dir / "2026-11-23.json").write_text(
                json.dumps({"edition_date": "2026-11-23", "method": METHOD, "cards": [first, held_card]}),
                encoding="utf-8",
            )
            carried = load_cards_through(docs, "2026-11-30", held_ids={"R-HELD"})
            self.assertEqual({"R-001"}, set(carried))
            earlier_before_hold = load_cards_through(docs, "2026-11-30", held_since={"R-HELD": "2026-12-07"})
            self.assertEqual({"R-001", "R-HELD"}, set(earlier_before_hold))
            exported = export_web_scorecards(docs, repositories=[{"id": "R-001", "snapshot_commit": "a" * 40}])
            self.assertEqual("2026-11-23", exported["latest_scorecard_date"])
            self.assertTrue(exported["cards"]["R-001"]["complete"])
            self.assertIn("human goals and direction", format_rubric_reason(exported["cards"]["R-001"]))


if __name__ == "__main__":
    unittest.main()

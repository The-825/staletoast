import unittest
from copy import deepcopy
from collaboration_rubric import WEIGHTS, prepare


class RubricTests(unittest.TestCase):
    def test_partial_complete_and_tied(self):
        full = dict(patterns=["many-humans-many-agents"], source="fixed revision",
                    ratings={key: dict(rating=4, basis="documented example") for key in WEIGHTS})
        partial = deepcopy(full)
        partial["ratings"]["outcomes"] = None
        rows = [dict(id=i) for i in ("b", "a", "c", "d")]
        ranked, provisional = prepare(rows, dict(a=full, b=full, c=partial))
        self.assertEqual([(r["id"], r["appraisal_priority_rank"]) for r in ranked], [("a", 1), ("b", 1)])
        self.assertEqual(ranked[0]["rubric_score"]["established"], 100)
        self.assertEqual([(r["established"], r["unresolved"]) for r in provisional], [(85, 15), (0, 100)])
        full["ratings"]["execution"]["rating"] = True
        with self.assertRaises(ValueError):
            prepare(rows, dict(a=full))

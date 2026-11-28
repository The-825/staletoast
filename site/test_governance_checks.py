"""Tests for Issue #69 bibliographic verification and November 27 added-component pool screening."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import screen_added_components as pool_screen  # noqa: E402
import verify_bibliographic_metadata as biblio  # noqa: E402

EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)


class BibliographicVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger_text = biblio.LEDGER_PATH.read_text(encoding="utf-8")
        cls.manifest = json.loads(biblio.MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_committed_ledger_and_manifest_pass(self):
        counts = biblio.validate_bibliographic_metadata(self.ledger_text, self.manifest)
        self.assertEqual(544, counts["ledger_entries"])
        self.assertGreaterEqual(counts["manifest_verified"], 4)

    def test_bare_https_url_without_host_is_rejected(self):
        bare = self.ledger_text.replace("https://arxiv.org/abs/2504.19413", "https://", 1)
        with self.assertRaises(ValueError):
            biblio.validate_bibliographic_metadata(bare, self.manifest)
        hostless = self.ledger_text.replace("https://arxiv.org/abs/2504.19413", "https:///abs/2504.19413", 1)
        with self.assertRaisesRegex(ValueError, "host"):
            biblio.validate_bibliographic_metadata(hostless, self.manifest)

    def test_placeholder_author_is_rejected(self):
        mutated = self.ledger_text.replace(
            "| 051 | Prateek Chhikara et al.,",
            "| 051 | Author TBD placeholder,",
            1,
        )
        with self.assertRaisesRegex(ValueError, "placeholder"):
            biblio.validate_bibliographic_metadata(mutated, self.manifest)

    def test_wrong_first_author_or_title_mismatch_fails(self):
        bad_author = copy.deepcopy(self.manifest)
        bad_author["verifications"][0]["verified_first_author"] = "Wrong Person"
        with self.assertRaisesRegex(ValueError, "verified_first_author"):
            biblio.validate_bibliographic_metadata(self.ledger_text, bad_author)

        bad_title = copy.deepcopy(self.manifest)
        bad_title["verifications"][0]["verified_title"] = "Completely Different Paper"
        with self.assertRaisesRegex(ValueError, "verified_title"):
            biblio.validate_bibliographic_metadata(self.ledger_text, bad_title)

    def test_claim_verification_boundary_cannot_be_upgraded(self):
        bad_status = copy.deepcopy(self.manifest)
        bad_status["verifications"][0]["claim_verification_status"] = "verified"
        with self.assertRaisesRegex(ValueError, "claim_verification_status"):
            biblio.validate_bibliographic_metadata(self.ledger_text, bad_status)

    def test_new_post_baseline_ledger_entry_requires_manifest_verification(self):
        appended = self.ledger_text.replace(
            "### Entry metadata",
            '| C-999 | Jane Doe, ["Synthetic Clarification Paper"](https://arxiv.org/abs/2611.99999), arXiv, 2026. | Task | Finding | Watch | Boundary |\n\n### Entry metadata',
            1,
        )
        with self.assertRaisesRegex(ValueError, "C-999"):
            biblio.validate_bibliographic_metadata(appended, self.manifest)


class AddedComponentPoolScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proposal, cls.json_text, cls.md_text, cls.held_ids = pool_screen.compute_current()

    def test_routing_proposal_preserves_holds_null_grades_and_scope_status(self):
        self.assertEqual("routing-proposal", self.proposal["kind"])
        self.assertTrue(self.proposal["scope_map_status_unchanged"])
        self.assertEqual(1083, self.proposal["counts"]["retained_pool_total"])
        self.assertEqual(41, self.proposal["counts"]["held_excluded_total"])
        self.assertEqual(1042, self.proposal["counts"]["active_pool_screened"])
        self.assertGreater(self.proposal["counts"]["candidates_with_any_match"], 0)
        expected_assignments = sum(
            s["active_matches"] for s in self.proposal["counts"]["per_component"].values()
        )
        self.assertEqual(expected_assignments, self.proposal["counts"]["total_component_assignments"])
        self.assertGreaterEqual(
            self.proposal["counts"]["total_component_assignments"],
            self.proposal["counts"]["candidates_with_any_match"],
        )
        candidate_ids = {c["source_id"] for c in self.proposal["candidates"]}
        self.assertFalse(candidate_ids & self.held_ids)
        for candidate in self.proposal["candidates"]:
            self.assertIsNone(candidate["grade"])
            self.assertEqual("not adopted", candidate["adoption"])
            self.assertEqual("not selected", candidate["hot100_selection"])
        scope_map = json.loads(pool_screen.SCOPE_MAP_PATH.read_text(encoding="utf-8"))
        added = [c for c in scope_map["components"] if c["id"] == "security-and-containment"]
        self.assertEqual("added-unscreened", added[0]["status"])

    def test_held_source_injection_is_rejected_by_invariant_validator(self):
        tampered = copy.deepcopy(self.proposal)
        held_example = sorted(self.held_ids)[0]
        tampered["candidates"].append({
            "source_id": held_example,
            "pool_id": "Q-HELD",
            "kind": "repository",
            "title_or_repo": "synthetic/held",
            "source_url": "https://github.com/example/held",
            "matched_components": [{"component_id": "security-and-containment", "matched_terms": ["sandbox"]}],
            "grade": None,
            "disposition": "retained-pool-routing-proposal-only",
            "adoption": "not adopted",
            "hot100_selection": "not selected",
        })
        with self.assertRaisesRegex(ValueError, "leaked"):
            pool_screen.validate_proposal_invariants(tampered, self.held_ids)

    def test_check_flag_detects_stale_or_missing_outputs(self):
        with TemporaryDirectory() as tmp:
            json_out = Path(tmp) / "screen.json"
            md_out = Path(tmp) / "screen.md"
            with patch.object(pool_screen, "JSON_OUT", json_out), patch.object(pool_screen, "MD_OUT", md_out), patch.object(sys, "argv", ["screen_added_components.py", "--check"]):
                with self.assertRaisesRegex(SystemExit, "missing or stale"):
                    pool_screen.main()
            with patch.object(pool_screen, "JSON_OUT", json_out), patch.object(pool_screen, "MD_OUT", md_out), patch.object(sys, "argv", ["screen_added_components.py"]):
                pool_screen.main()
            with patch.object(pool_screen, "JSON_OUT", json_out), patch.object(pool_screen, "MD_OUT", md_out), patch.object(sys, "argv", ["screen_added_components.py", "--check"]):
                pool_screen.main()
            md_out.write_text(md_out.read_text(encoding="utf-8") + "\ndrift\n", encoding="utf-8")
            with patch.object(pool_screen, "JSON_OUT", json_out), patch.object(pool_screen, "MD_OUT", md_out), patch.object(sys, "argv", ["screen_added_components.py", "--check"]):
                with self.assertRaisesRegex(SystemExit, "missing or stale"):
                    pool_screen.main()

    def test_committed_pool_screen_files_match_current_computation(self):
        self.assertTrue(pool_screen.JSON_OUT.exists())
        self.assertTrue(pool_screen.MD_OUT.exists())
        self.assertEqual(self.json_text, pool_screen.JSON_OUT.read_text(encoding="utf-8"))
        self.assertEqual(self.md_text, pool_screen.MD_OUT.read_text(encoding="utf-8"))

    def test_no_em_or_en_dashes_in_slice_c_files(self):
        for path in (
            biblio.MANIFEST_PATH,
            Path(biblio.__file__).resolve(),
            Path(pool_screen.__file__).resolve(),
            Path(__file__).resolve(),
            pool_screen.JSON_OUT,
            pool_screen.MD_OUT,
        ):
            if path.exists():
                text = path.read_text(encoding="utf-8")
                self.assertNotIn(EM_DASH, text, path.name)
                self.assertNotIn(EN_DASH, text, path.name)


if __name__ == "__main__":
    unittest.main()

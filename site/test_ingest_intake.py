import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import ingest_intake as intake  # noqa: E402


class IngestIntakeTests(unittest.TestCase):
    def test_canonical_identities_normalize_arxiv_doi_and_github(self):
        keys = intake.canonical_identities(
            url="https://arxiv.org/pdf/2605.12015v3.pdf",
            text="Findings of ACL 2026, DOI 10.18653/v1/2026.findings-acl.845.",
        )
        self.assertIn("arxiv:2605.12015", keys)
        self.assertIn("doi:10.18653/v1/2026.findings-acl.845", keys)

        repo_keys = intake.canonical_identities(
            url="https://www.github.com/OpenAI/OpenAI-Agents-Python.git/",
            repository="openai/openai-agents-python",
            aliases=["openai/swarm-next"],
        )
        self.assertIn("github:openai/openai-agents-python", repo_keys)
        self.assertIn("github:openai/swarm-next", repo_keys)

    def test_live_corpus_has_no_same_kind_canonical_collisions(self):
        report = intake.check_corpus(ROOT)
        self.assertEqual([], report["same_kind_collisions"])
        self.assertGreaterEqual(report["research_records"], 544)
        self.assertGreaterEqual(report["repository_records"], 1109)

    def test_next_batch_prioritizes_thin_scope_components_without_mutating(self):
        batch = intake.select_next_batch(ROOT, limit=6, kind="all")
        self.assertEqual("appraisal-queue-shortlist", batch["kind"])
        self.assertEqual(6, len(batch["shortlist"]))
        self.assertIn("deliberation-and-dissent", batch["thin_scope_components_prioritized"])
        self.assertTrue(
            any("deliberation-and-dissent" in row["matched_thin_components"] for row in batch["shortlist"]),
            "Expected thin deliberation-and-dissent candidates at the top of the shortlist",
        )

    def test_validate_and_prepare_intake_in_isolated_copy(self):
        with TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            tmp_docs = tmp_root / "docs"
            tmp_docs.mkdir()
            for src in (ROOT / "docs").glob("*"):
                if src.is_file():
                    (tmp_docs / src.name).write_bytes(src.read_bytes())

            # Duplicate arXiv version of an existing paper must fail closed.
            dup_payload = {
                "research": [{
                    "id": "C-9999",
                    "authors": "Harang Ju and Sinan Aral",
                    "verified_first_author": "Harang Ju",
                    "title": "Collaborating with AI Agents Duplicate Check",
                    "url": "https://arxiv.org/pdf/2503.18238v4.pdf",
                    "venue": "arXiv preprint",
                    "year": 2026,
                    "verified_date": "2026-11-28",
                    "level_and_evidence": "Workflow experiment",
                    "finding": "Synthetic duplicate check.",
                    "impact": "**Watch** duplicate check.",
                    "boundary": "Synthetic test boundary.",
                    "design": "Preprint field experiment",
                    "directness": "D2 adjacent",
                    "family": "SYNTH-TEST",
                    "horizon": "single",
                    "flags": "selected-full-text: synthetic test",
                    "claims": ["CI-006"],
                }],
                "repositories": [],
            }
            with self.assertRaisesRegex(ValueError, "duplicates existing research"):
                intake.validate_candidate_payload(dup_payload, root=tmp_root)

            # Valid synthetic candidate stages and writes cleanly across all 6 files.
            valid_payload = {
                "research": [{
                    "id": "C-1001",
                    "authors": "alexandra Example and Jordan Synthetic",
                    "verified_first_author": "alexandra Example",
                    "title": "Synthetic Deliberation Handoff Trial",
                    "url": "https://example.org/papers/synthetic-deliberation-1001",
                    "venue": "Journal of Synthetic Collaboration",
                    "year": 2026,
                    "verified_date": "2026-11-28",
                    "level_and_evidence": "Workflow; controlled synthetic study",
                    "finding": "Structured dissent checkpoints preserved minority error detection.",
                    "impact": "**Watch** dissent preservation before consensus.",
                    "boundary": "Synthetic task boundary. Next: test longitudinal teams.",
                    "design": "Controlled synthetic team experiment",
                    "directness": "D3 target-like",
                    "family": "SYNTH-DELIB",
                    "horizon": "repeated",
                    "flags": "selected-full-text: bounded synthetic verification",
                    "claims": ["CI-015", "CI-006"],
                }],
                "repositories": [{
                    "id": "R-2001",
                    "repository": "synthetic-org/deliberation-harness",
                    "url": "https://github.com/synthetic-org/deliberation-harness",
                    "snapshot_commit": "abcd1234" * 5,
                    "snapshot_date": "2026-11-28",
                    "stars_observed": 42,
                    "popularity_observed_date": "2026-11-28",
                    "selection_aspect": "dissent-routing",
                    "category": "evaluation-benchmark",
                    "lifecycle": "current",
                    "evidence_depth": "readme-screened",
                    "evidence_pointer": "README.md",
                    "evidence_note": "README documents dissenting review traces and explicit human sign-off.",
                    "claims": ["CI-015", "CI-017"],
                    "mechanisms": {dim: ("V" if dim in {"human_authority", "independent_verification"} else "N") for dim in intake.REQUIRED_REPO_DIMENSIONS},
                    "license_status": "MIT",
                }],
            }
            dry = intake.prepare_intake(valid_payload, "2026-11-28", root=tmp_root, write=False)
            self.assertEqual("dry-run", dry["mode"])
            written = intake.prepare_intake(valid_payload, "2026-11-28", root=tmp_root, write=True)
            self.assertEqual("written", written["mode"])
            rebuilt = json.loads((tmp_docs / "staletoast-appraisal-priorities.json").read_text(encoding="utf-8"))
            self.assertIn("C-1001", {r["id"] for r in rebuilt["research"]})
            self.assertIn("R-2001", {r["id"] for r in rebuilt["repositories"]})

    def test_script_has_no_network_or_subprocess_imports(self):
        source = (ROOT / "scripts" / "ingest_intake.py").read_text(encoding="utf-8")
        for token in ("subprocess", "urllib.request", "socket", "http.client", "requests", "os.system"):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()

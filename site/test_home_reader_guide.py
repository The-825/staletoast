"""Tests for the guided reading paths on the StaleToast home page."""

import html
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parent
INDEX = SITE / "index.html"
HOME_JS = SITE / "home.js"
READER_GUIDE = SITE / "data" / "reader-guide.json"
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)
NODE = shutil.which("node")

RENDER_SCRIPT = (
    "const fs = require('fs'); const vm = require('vm');"
    "const ctx = {}; vm.createContext(ctx);"
    "vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), ctx);"
    "const guide = JSON.parse(fs.readFileSync(0, 'utf8'));"
    "process.stdout.write(JSON.stringify(ctx.renderReadingPaths(guide)));"
)

PRIMARY_ID = re.compile(r"\b(?:R|CI)-\d+\b")
REFERENCE_BLOCK = re.compile(r'<details class="reference">.*?</details>', re.S)


def render(guide):
    result = subprocess.run(
        ["node", "-e", RENDER_SCRIPT, str(HOME_JS)],
        input=json.dumps(guide),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=30,
    )
    return json.loads(result.stdout)


def visible_primary_text(html):
    without_reference = REFERENCE_BLOCK.sub(" ", html)
    return re.sub(r"<[^>]+>", " ", without_reference)


def synthetic_guide():
    return {
        "schema_version": 1,
        "date": "2026-10-24",
        "status": "editorial reading paths, not a universal quality ranking",
        "ordering": "Editorial reading paths, not a quality score or internal review priority",
        "evidence_boundary": "Selected from existing appraisals; no new reproduction or adoption claim",
        "source_revision": "0" * 40,
        "collections": [
            {
                "id": "recover-work",
                "title": "Recover work <script>alert(1)</script>",
                "description": "Synthetic collection for tests (CI-001).",
                "selections": [
                    {
                        "kind": "repository",
                        "id": "R-316",
                        "title": "Synthetic repository R-316",
                        "source_url": "https://example.com/synthetic-repo",
                        "why_selected": "Shows session continuity, see CI-001.",
                        "evidence_depth": "readme-screened",
                        "takeaway": "<img src=x onerror=alert(1)>",
                        "limits": "README only.",
                        "original_evidence_note": "Synthetic.",
                        "counterevidence": [
                            {
                                "url": "https://example.com/issues/1",
                                "observed_date": "2026-10-13",
                                "state": "open",
                                "boundary": "Reported on an earlier release; not reproduced.",
                            }
                        ],
                        "profile_slug": "synthetic-repo",
                    },
                    {
                        "kind": "research",
                        "id": "010",
                        "title": "Synthetic study",
                        "source_url": "javascript:alert(1)",
                        "why_selected": "Synthetic reason.",
                        "evidence_depth": "selected-full-text",
                        "takeaway": "Synthetic takeaway.",
                        "limits": "Synthetic limits.",
                        "original_evidence_note": "Synthetic.",
                        "counterevidence": "None recorded.",
                        "profile_slug": "synthetic-study",
                    },
                ],
            }
        ],
    }


class IndexStructureTests(unittest.TestCase):
    def setUp(self):
        self.html = INDEX.read_text(encoding="utf-8")

    def test_reading_paths_section_and_fallback(self):
        self.assertIn('aria-labelledby="paths-title"', self.html)
        self.assertIn('id="paths-title"', self.html)
        self.assertIn('id="reading-paths-meta" class="note"', self.html)
        self.assertIn('id="reading-paths"', self.html)
        section = self.html.split('aria-labelledby="paths-title"', 1)[1].split("</section>", 1)[0]
        self.assertIn('href="research.html"', section)
        self.assertIn('href="repositories.html"', section)
        self.assertIn("not a quality score", section)
        self.assertIn("adoption recommendation", section)

    def test_section_follows_entry_section(self):
        entry = self.html.index('aria-labelledby="entry-title"')
        paths = self.html.index('aria-labelledby="paths-title"')
        read = self.html.index('aria-labelledby="read-title"')
        self.assertLess(entry, paths)
        self.assertLess(paths, read)

    def test_existing_invariants_kept(self):
        self.assertIn('<nav aria-label="Primary">', self.html)
        self.assertIn("app.css?v=20261128-1", self.html)
        self.assertEqual(self.html.count("<script"), 1)
        self.assertIn('<script src="home.js?v=20261128-1"></script>', self.html)
        self.assertIn("quality certification", self.html)
        for banned in ("chart-list", "charts.js", "catalog-ui.js"):
            self.assertNotIn(banned, self.html)


class DashTests(unittest.TestCase):
    def test_no_em_or_en_dashes(self):
        for path in (INDEX, HOME_JS, Path(__file__).resolve()):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(EM_DASH, text, path.name)
            self.assertNotIn(EN_DASH, text, path.name)


@unittest.skipUnless(NODE, "node is not installed")
class RenderTests(unittest.TestCase):
    def test_repository_maps_to_plural_detail_type(self):
        html = render(synthetic_guide())["html"]
        self.assertIn("detail.html?type=repositories&amp;id=R-316", html)
        self.assertIn("detail.html?type=research&amp;id=010", html)
        self.assertNotIn("type=repository&", html)

    def test_escaping_and_unsafe_urls(self):
        html = render(synthetic_guide())["html"]
        self.assertNotIn("<script", html)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("javascript:", html)
        self.assertIn('href="https://example.com/synthetic-repo"', html)
        self.assertNotIn("[object Object]", html)
        self.assertIn("Observed 2026-10-13", html)

    def test_ids_only_inside_reference_details(self):
        html = render(synthetic_guide())["html"]
        self.assertIsNone(PRIMARY_ID.search(visible_primary_text(html)))
        first_primary = html.split('<details class="reference">', 1)[0]
        self.assertIsNone(PRIMARY_ID.search(re.sub(r"<[^>]+>", " ", first_primary)))
        self.assertIn("Record ID: <code>R-316</code>", html)
        self.assertIn("Evidence depth code: <code>readme-screened</code>", html)
        self.assertIn("README screened", html)

    def test_meta_text_framing(self):
        meta = render(synthetic_guide())["metaText"]
        self.assertIn("2026-10-24", meta)
        self.assertIn("Not a quality score", meta)

    def test_invalid_or_empty_guides(self):
        empty = {"metaText": "", "html": ""}
        for guide in (
            None,
            {},
            {"schema_version": 2, "collections": [{"selections": [{}]}]},
            {"schema_version": 1, "collections": []},
            {"schema_version": 1, "collections": "nope"},
            {"schema_version": 1, "collections": [{"title": "x", "selections": []}]},
        ):
            self.assertEqual(render(guide), empty, guide)

    @unittest.skipUnless(READER_GUIDE.exists(), "data/reader-guide.json not built")
    def test_real_reader_guide(self):
        guide = json.loads(READER_GUIDE.read_text(encoding="utf-8"))
        result = render(guide)
        self.assertTrue(result["metaText"])
        self.assertIn("detail.html?type=", result["html"])
        self.assertNotIn("type=repository&", result["html"])
        self.assertNotIn("<script", result["html"])
        self.assertNotIn("[object Object]", result["html"])
        self.assertIsNone(PRIMARY_ID.search(visible_primary_text(result["html"])))
        for collection in guide["collections"]:
            self.assertIn(collection["title"].split(" ")[0], html.unescape(result["html"]))
        self.assertNotIn(EM_DASH, result["html"])


if __name__ == "__main__":
    unittest.main()

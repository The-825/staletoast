import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'


class StandaloneTests(unittest.TestCase):
    def test_imported_history_and_frozen_charts_preserve_original_bytes(self):
        receipt = json.loads((ROOT / 'docs/migration-provenance.json').read_text(encoding='utf-8'))
        for path, expected in receipt['original_source_sha256'].items():
            original = subprocess.check_output(['git', 'show', receipt['imported_history_tip'] + ':' + path], cwd=ROOT)
            self.assertEqual(expected, hashlib.sha256(original).hexdigest(), path)
            if '/staletoast-chart-history/' in path:
                current = (ROOT / path).read_text(encoding='utf-8').encode('utf-8')
                self.assertEqual(expected, hashlib.sha256(current).hexdigest(), path)

    def test_every_local_reader_link_and_script_resolves(self):
        class References(HTMLParser):
            def __init__(self):
                super().__init__()
                self.urls = []

            def handle_starttag(self, tag, attrs):
                self.urls.extend(v for k, v in attrs if k in {'href', 'src'} and v)

        for page in SITE.glob('*.html'):
            refs = References()
            refs.feed(page.read_text(encoding='utf-8'))
            for url in refs.urls:
                parsed = urlsplit(url)
                if parsed.scheme or not parsed.path:
                    continue
                self.assertTrue((page.parent / parsed.path).is_file(), (page.name, url))

    def test_export_is_revision_bound_and_does_not_take_companion_ownership(self):
        export = json.loads((SITE / 'data/catalog-export.json').read_text(encoding='utf-8'))
        self.assertEqual('The-825/staletoast', export['canonical_owner'])
        self.assertEqual('evidence-only', export['authority'])
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        self.assertEqual(revision, export['source_revision'])
        self.assertEqual({'research', 'repositories', 'claims', 'charts'}, set(export['catalogs']))
        for name, catalog in export['catalogs'].items():
            self.assertEqual(json.loads((SITE / 'data' / (name + '.json')).read_text(encoding='utf-8')), catalog)
        self.assertFalse((ROOT / 'docs/workflow-registry.json').exists())
        self.assertFalse((ROOT / 'docs/prompt-library.json').exists())
        charts = export['catalogs']['charts']['latest']['charts']
        for chart in charts.values():
            self.assertEqual(100, len(chart['entries']))
            self.assertEqual(len(chart['entries']), len({r['id'] for r in chart['entries']}))


if __name__ == '__main__':
    unittest.main()

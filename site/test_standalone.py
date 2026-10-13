import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import urlsplit
from build_export import catalog_revision
import build_export

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'


class StandaloneTests(unittest.TestCase):
    def test_new_exports_retain_prior_bytes_and_reject_rewriting_a_pin(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / 'site/data'
            data.mkdir(parents=True)
            for name in ('research', 'repositories', 'claims', 'charts'):
                (data / (name + '.json')).write_text('[]', encoding='utf-8')
            with patch.object(build_export, 'ROOT', root), patch.object(build_export, 'DATA', data), patch.object(build_export.subprocess, 'check_output', side_effect=lambda *a, **k: 'a' * 40 if k.get('text') else b''), patch.object(build_export, 'catalog_revision', return_value='a' * 40):
                build_export.build(freeze=True)
                first = root / 'exports' / ('a' * 40 + '.json')
                before = first.read_bytes()
                (data / 'research.json').write_text('[{"id":"new"}]', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'differs'):
                    build_export.build(freeze=True)
                with patch.object(build_export, 'catalog_revision', return_value='b' * 40):
                    build_export.build(freeze=True)
                self.assertEqual(before, first.read_bytes())
                self.assertEqual(before, (root / 'site/exports' / first.name).read_bytes())

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
        revision = catalog_revision()
        self.assertEqual(revision, export['source_revision'])
        archive = ROOT / 'exports' / (revision + '.json')
        self.assertEqual(archive.read_bytes(), (SITE / 'exports' / archive.name).read_bytes())
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

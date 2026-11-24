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
    def test_freeze_refuses_untracked_catalog_inputs(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            git = lambda *args: subprocess.check_call(
                ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *args],
                cwd=root, stdout=subprocess.DEVNULL)
            git('init', '-q')
            (root / 'catalog-contract.json').write_text('{}', encoding='utf-8')
            git('add', '.')
            git('commit', '-q', '-m', 'base')
            history = root / 'docs/staletoast-chart-history'
            history.mkdir(parents=True)
            (history / '2026-01-01.json').write_text('{}', encoding='utf-8')
            with patch.object(build_export, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Commit catalog inputs'):
                    build_export.build(freeze=True)
            self.assertFalse((root / 'catalog-export-pin.json').exists())

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
                self.assertEqual('2.0', json.loads(before)['schema_version'])
                (data / 'research.json').write_text('[{"id":"new"}]', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'differs'):
                    build_export.build(freeze=True)
                with patch.object(build_export, 'catalog_revision', return_value='b' * 40):
                    build_export.build(freeze=True)
                self.assertEqual(before, first.read_bytes())
                self.assertEqual(before, (root / 'site/exports' / first.name).read_bytes())

    def test_unfrozen_catalog_changes_publish_the_pinned_export_unchanged(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / 'site/data'
            data.mkdir(parents=True)
            revision = 'c' * 40
            frozen = json.dumps({'schema_version': '2.0', 'source_revision': revision}) + '\n'
            (root / 'exports').mkdir()
            (root / 'exports' / (revision + '.json')).write_text(frozen, encoding='utf-8')
            (root / 'catalog-export-pin.json').write_text(json.dumps(
                {'schema_version': '1.0', 'source_revision': revision, 'inputs_sha256': {'stale': 'x'}}), encoding='utf-8')
            with patch.object(build_export, 'ROOT', root), patch.object(build_export, 'DATA', data), \
                    patch.object(build_export.subprocess, 'check_output', return_value=b''):
                build_export.build()
                self.assertEqual(frozen, (data / 'catalog-export.json').read_text(encoding='utf-8'))
                self.assertEqual(frozen, (root / 'site/exports' / (revision + '.json')).read_text(encoding='utf-8'))
                (root / 'exports' / (revision + '.json')).unlink()
                with self.assertRaisesRegex(ValueError, 'Pinned export is missing'):
                    build_export.build()

    def test_only_a_weekly_edition_pr_may_freeze_the_export(self):
        pin = ('M', 'catalog-export-pin.json')
        snapshot = ('A', 'exports/' + 'd' * 40 + '.json')
        record = ('M', 'docs/collaborative-intelligence-research-ledger.md')
        edition = ('A', 'docs/staletoast-chart-history/2026-11-30.json')
        self.assertIsNone(build_export.freeze_scope_violation([record]))
        self.assertIsNone(build_export.freeze_scope_violation([record, edition, pin, snapshot]))
        self.assertIn('catalog-export-pin.json', build_export.freeze_scope_violation([record, pin, snapshot]))
        self.assertIsNotNone(build_export.freeze_scope_violation([('M', 'docs/staletoast-chart-history/2026-11-02.json'), pin]))
        self.assertIsNone(build_export.freeze_scope_violation([('A', 'exports/reader-guide/' + 'e' * 40 + '.json')]))

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
        contract = json.loads((ROOT / 'catalog-contract.json').read_text(encoding='utf-8'))
        self.assertEqual('2.0', export['schema_version'])
        self.assertEqual(contract['export_schema_version'], export['schema_version'])
        for name in ('research', 'repositories'):
            self.assertTrue(all(row['appraisal_state'] in {'automated-screen', 'source-screened'} for row in export['catalogs'][name]))
        for row in export['catalogs']['research']:
            if row['appraisal_state'] == 'automated-screen':
                self.assertIsNone(row['evidenceOrder'])
        pin = json.loads((ROOT / 'catalog-export-pin.json').read_text(encoding='utf-8'))
        revision = pin['source_revision']
        self.assertEqual(revision, export['source_revision'])
        archive = ROOT / 'exports' / (revision + '.json')
        self.assertEqual(archive.read_bytes(), (SITE / 'data' / 'catalog-export.json').read_bytes())
        self.assertEqual(archive.read_bytes(), (SITE / 'exports' / archive.name).read_bytes())
        self.assertEqual({'research', 'repositories', 'claims', 'charts'}, set(export['catalogs']))
        if pin['inputs_sha256'] == build_export.input_hashes():
            self.assertEqual(revision, catalog_revision())
            for name, catalog in export['catalogs'].items():
                self.assertEqual(json.loads((SITE / 'data' / (name + '.json')).read_text(encoding='utf-8')), catalog)
        self.assertFalse((ROOT / 'docs/workflow-registry.json').exists())
        self.assertFalse((ROOT / 'docs/prompt-library.json').exists())
        charts = export['catalogs']['charts']['latest']['charts']
        for chart in charts.values():
            self.assertEqual(100, len(chart['entries']))
            self.assertEqual(len(chart['entries']), len({r['id'] for r in chart['entries']}))

    def test_prior_frozen_exports_preserve_git_content_and_recorded_schema(self):
        paths = subprocess.check_output(
            ['git', 'ls-tree', '-r', '--name-only', 'HEAD', 'exports'],
            cwd=ROOT, text=True).splitlines()
        for name in paths:
            path = Path(name)
            if path.parent != Path('exports') or path.suffix != '.json':
                continue
            original = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT)
            self.assertEqual(original.decode('utf-8').replace('\r\n', '\n'),
                             (ROOT / name).read_text(encoding='utf-8'), name)
            record = json.loads(original)
            self.assertIn(record['schema_version'], {'1.0', '2.0'}, name)
            self.assertEqual(path.stem, record['source_revision'], name)

    def test_research_profiles_cover_all_chart_archive_identities_without_promoting_candidates(self):
        research = json.loads((SITE / 'data/research.json').read_text(encoding='utf-8'))
        priorities = json.loads((ROOT / 'docs/staletoast-appraisal-priorities.json').read_text(encoding='utf-8'))
        self.assertEqual({row['id'] for row in priorities['research']}, {row['id'] for row in research})
        self.assertEqual(len(research), len({row['id'] for row in research}))
        candidate = next(row for row in research if row['id'] == 'C-025')
        self.assertEqual('https://arxiv.org/abs/2610.01160v1', candidate['url'])
        self.assertEqual('candidate-not-promoted', candidate['record_state'])
        self.assertEqual('abstract-only', candidate['review_depth'])
        self.assertTrue(all(row['record_state'] == 'candidate-not-promoted' for row in research if row['id'].startswith('C-')))


if __name__ == '__main__':
    unittest.main()

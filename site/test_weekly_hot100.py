import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import build_discovery as discovery
import build_priorities as priorities
import weekly_hot100 as weekly

SEED, NEW = '2026-10-13', '2026-11-02'
D2, D3 = ('D2 adjacent', 'single'), ('D3 direct', 'longitudinal')
AUTO_PAPER = '| C-026 | design | D3 direct | SYNTHETIC | longitudinal | abstract-only: automated relevance screen |  |\n'


def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode('utf-8'))


def tree(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in sorted(root.rglob('*')) if path.is_file()}


def repository(identity, depth='readme-screened', claims=('CI-006',)):
    return dict(id=identity, repository=f'org/{identity}', url=f'https://example.org/r/{identity}', claims=list(claims),
                evidence_depth=depth, lifecycle='current', snapshot_commit='a' * 40, snapshot_date='2026-10-01',
                category='workflow-runtime', license_status='MIT', stars_observed=5)


def write_sources(docs, papers):
    """Synthetic owning sources: appraised papers plus one automated paper and one automated repository."""
    ledger = ''.join(f'| {i} | ["Paper {i}"](https://example.org/{i}) | s | f | i | l |\n' for i, _ in papers)
    ledger += '| C-026 | ["Auto C-026"](https://example.org/C-026) | s | f | i | l |\n'
    put(docs / 'collaborative-intelligence-research-ledger.md', '## Source ledger\n' + ledger + '### Entry metadata\n| 001 | repeated | a | b | c |\n')
    put(docs / 'collaborative-intelligence-source-appraisals.md',
        ''.join(f'| {i} | design | {grade[0]} | SYNTHETIC | {grade[1]} | limits | CI-006 |\n' for i, grade in papers) + AUTO_PAPER)
    put(docs / 'collaborative-intelligence-repository-landscape.json', json.dumps(dict(
        popularity_observed_date='2026-10-01',
        repositories=[repository('R-001'), repository('R-002'), repository('R-AUTO', 'readme-relevance-screened', ())])))
    put(docs / 'staletoast-expansion-2026-11-01.json', json.dumps(dict(
        research=[dict(id='C-026', kind='research', screen_method='automated-abstract-topic-screen-v1')],
        repositories=[dict(id='R-AUTO', kind='repository', screen_method='automated-readme-relevance-screen-v1')])))
    put(docs / 'staletoast-source-dispositions.json', json.dumps(dict(schema_version=1, records=[])))


def write_sidecar(docs):
    put(docs / 'staletoast-system-fit-appraisals-2026-11-01.json', json.dumps(dict(records=[
        dict(id='C-026', kind='research', review_state=weekly.REVIEW_READY),
        dict(id='R-AUTO', kind='repository', review_state=weekly.REVIEW_READY),
        dict(id='R-002', kind='repository', review_state='retained-in-pool')])))


def seed(root, papers=(('001', D2),)):
    """Create a frozen prior edition, the current priorities, a sidecar and a historical export."""
    docs = root / 'docs'
    write_sources(docs, papers)
    write_sidecar(docs)
    payload = priorities.build(docs, SEED)
    put(docs / 'staletoast-appraisal-priorities.json', weekly.dump(payload))
    put(docs / 'staletoast-appraisal-priorities.md', priorities.render(payload))
    landscape = discovery.read(docs / 'collaborative-intelligence-repository-landscape.json')
    edition = discovery.make_edition(SEED, payload, landscape, [])
    edition['source_hashes'] = {field: payload[field] for field in priorities.SOURCES}
    put(docs / 'staletoast-chart-history' / f'{SEED}.json', weekly.dump(edition))
    put(root / 'exports' / ('f' * 40 + '.json'), '{"historical": true}\n')


class WeeklyTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.docs = self.root / 'docs'
        seed(self.root)
        self.receipt_path = self.docs / 'staletoast-weekly-review' / f'{NEW}.json'

    def receipt(self):
        return json.loads(self.receipt_path.read_text(encoding='utf-8'))

    def test_default_is_a_dry_run_and_date_is_required(self):
        before = tree(self.root)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(0, weekly.main(['--date', NEW, '--root', str(self.root)]))
        self.assertIn('dry-run', out.getvalue())
        self.assertEqual(before, tree(self.root))
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            weekly.main(['--root', str(self.root)])
        for bad in ('11/02/2026', '2026-2-3', '', '2026-13-01'):
            with self.assertRaises(ValueError):
                weekly.plan(self.root, bad)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(2, weekly.main(['--date', 'tomorrow', '--root', str(self.root)]))
        self.assertEqual(before, tree(self.root))

    def test_write_records_movements_counts_hashes_and_limits(self):
        write_sources(self.docs, (('001', D2), ('002', D3)))
        before = tree(self.root)
        weekly.run(self.root, NEW, write=True)
        after = tree(self.root)
        changed = {name for name in after if before.get(name) != after[name]}
        self.assertEqual({'docs/staletoast-weekly-review/2026-11-02.json', 'docs/staletoast-chart-history/2026-11-02.json',
                          'docs/staletoast-appraisal-priorities.json', 'docs/staletoast-appraisal-priorities.md'}, changed)
        self.assertFalse([name for name in after if name.endswith('.weekly-tmp')])
        receipt = self.receipt()
        self.assertEqual((NEW, weekly.TIMEZONE), (receipt['review_date'], receipt['review_timezone']))
        self.assertEqual(SEED, receipt['prior_edition']['edition_date'])
        self.assertEqual(NEW, receipt['current_edition']['edition_date'])
        current = json.loads(after['docs/staletoast-appraisal-priorities.json'])
        self.assertEqual(NEW, current['date'])
        for field, value in receipt['recorded_source_hashes'].items():
            self.assertEqual(current[field], value)
        self.assertEqual(weekly.digest(self.docs.joinpath('collaborative-intelligence-research-ledger.md').read_text(encoding='utf-8')),
                         receipt['recorded_source_hashes']['research_source_sha256'])
        self.assertEqual(5, len(receipt['recorded_source_hashes']))
        research = receipt['counts']['research']
        self.assertEqual((1, 2, 2, 3), (research['prior_eligible'], research['eligible'], research['prior_archive'], research['archive']))
        move = receipt['movements']['research']
        self.assertFalse(move['ordering_unchanged'])
        self.assertEqual((1, 1), (move['new'], move['moved_down']))
        self.assertIn(dict(id='001', previous_position=1, position=2, movement=-1, entry_state='continuing'), move['changed'])
        repos = receipt['movements']['repositories']
        self.assertTrue(repos['ordering_unchanged'])
        self.assertEqual(['R-001', 'R-002'], repos['unchanged_position_ids'])
        self.assertEqual([], repos['changed'])
        self.assertEqual('2026-10-01', receipt['source_observation_dates']['stars_observed_date']['earliest'])
        recheck = receipt['primary_source_recheck']
        self.assertIs(False, recheck['performed'])
        self.assertIn('not rechecked', recheck['statement'])
        self.assertTrue(any('Offline run' in limit for limit in receipt['limits']))
        self.assertIn('export freeze', receipt['not_performed'])

    def test_unchanged_rankings_are_stated_explicitly(self):
        weekly.run(self.root, NEW, write=True)
        move = self.receipt()['movements']['research']
        self.assertTrue(move['ordering_unchanged'])
        self.assertEqual(['001'], move['unchanged_position_ids'])
        self.assertEqual([], move['changed'])
        self.assertEqual([], move['dropped'])
        self.assertEqual(0, move['new'])

    def test_automated_screens_stay_excluded_and_sidecar_is_review_ready_only(self):
        weekly.run(self.root, NEW, write=True)
        edition = json.loads((self.docs / 'staletoast-chart-history' / f'{NEW}.json').read_text(encoding='utf-8'))
        self.assertNotIn('C-026', [row['id'] for row in edition['charts']['research']['entries']])
        self.assertNotIn('R-AUTO', [row['id'] for row in edition['charts']['repositories']['entries']])
        current = json.loads((self.docs / 'staletoast-appraisal-priorities.json').read_text(encoding='utf-8'))
        self.assertTrue(next(row for row in current['research'] if row['id'] == 'C-026')['automated_screen'])
        receipt = self.receipt()
        self.assertEqual((1, 1, 0), tuple(receipt['automated_screens'][key] for key in
                                         ('research_in_archive', 'repositories_in_archive', 'in_current_edition')))
        ready = {row['id']: row for row in receipt['sidecar_review']['review_ready']}
        self.assertEqual({'C-026', 'R-AUTO'}, set(ready))
        for row in ready.values():
            self.assertEqual('automated-screen', row['appraisal_state'])
            self.assertFalse(row['in_current_edition'])
            self.assertIn('not a catalog promotion', row['catalog_promotion'])
        self.assertEqual(1, receipt['sidecar_review']['other_state_records'])

    def test_historical_bytes_are_preserved(self):
        old = {name: data for name, data in tree(self.root).items()
               if name.startswith('exports/') or name.startswith('docs/staletoast-chart-history/')
               or name.startswith('docs/staletoast-system-fit')}
        write_sources(self.docs, (('001', D2), ('002', D3)))
        weekly.run(self.root, NEW, write=True)
        after = tree(self.root)
        for name, data in old.items():
            self.assertEqual(data, after[name], name)

    def test_retained_held_repositories_do_not_block_or_enter_the_chart(self):
        path = self.docs / 'collaborative-intelligence-repository-landscape.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        data['repositories'].append(repository('R-HELD', 'readme-relevance-screened', ()))
        put(path, weekly.dump(data))
        path = self.docs / 'staletoast-expansion-2026-11-01.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        data['repositories'].append(dict(id='R-HELD', kind='repository', screen_method='automated-readme-relevance-screen-v1'))
        put(path, weekly.dump(data))
        put(self.docs / 'staletoast-source-dispositions.json', weekly.dump(dict(schema_version=1, records=[
            dict(id='R-HELD', kind='repository', state='held', reason='Synthetic hold')])))
        weekly.run(self.root, NEW, write=True)
        edition = json.loads((self.docs / 'staletoast-chart-history' / f'{NEW}.json').read_text(encoding='utf-8'))
        self.assertNotIn('R-HELD', [r['id'] for r in edition['charts']['repositories']['entries']])
        self.assertEqual(3, edition['charts']['repositories']['archive_count'])
        self.assertEqual(4, len(json.loads((self.docs / 'collaborative-intelligence-repository-landscape.json').read_text())['repositories']))
        self.assertEqual(['R-HELD'], self.receipt()['held_exclusions']['repository_ids'])
        put(self.docs / 'staletoast-system-fit-appraisals-recheck-2026-11-02.json', weekly.dump(dict(records=[
            dict(id='R-HELD', kind='repository', review_state=weekly.REVIEW_READY)])))
        proposal = weekly.plan(self.root, '2026-11-09')
        row = next(r for r in proposal['receipt']['sidecar_review']['review_ready'] if r['id'] == 'R-HELD')
        self.assertTrue(row['excluded_by_hold'])
        self.assertEqual('held (excluded from projection)', row['appraisal_state'])

    def test_later_reappraisal_reuses_identity_and_keeps_history(self):
        old = (self.docs / 'staletoast-system-fit-appraisals-2026-11-01.json').read_bytes()
        put(self.docs / 'staletoast-system-fit-appraisals-2026-11-02.json', weekly.dump(dict(records=[
            dict(id='C-026', kind='research', review_state='held-after-recheck')])) )
        put(self.docs / 'staletoast-system-fit-appraisals-2026-11-09.json', weekly.dump(dict(records=[
            dict(id='C-026', kind='research', review_state=weekly.REVIEW_READY)])))
        weekly.run(self.root, NEW, write=True)
        result = self.receipt()['sidecar_review']
        self.assertNotIn('C-026', [r['id'] for r in result['review_ready']])
        self.assertEqual(2, len(result['sidecars']))
        self.assertEqual(old, (self.docs / 'staletoast-system-fit-appraisals-2026-11-01.json').read_bytes())

    def test_duplicate_within_one_assessment_is_rejected_without_writes(self):
        write_sidecar(self.docs)
        path = self.docs / 'staletoast-system-fit-appraisals-2026-11-01.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        data['records'].append(data['records'][0])
        put(path, weekly.dump(data))
        before = tree(self.root)
        with self.assertRaisesRegex(ValueError, 'duplicate ID'):
            weekly.run(self.root, NEW, write=True)
        self.assertEqual(before, tree(self.root))

    def test_assessment_dates_override_filename_order_and_same_date_conflicts_fail(self):
        put(self.docs / 'staletoast-system-fit-appraisals-z-2026-10-31.json', weekly.dump(dict(records=[
            dict(id='C-026', kind='research', review_state='held-old')])))
        self.assertIn('C-026', [r['id'] for r in weekly.plan(self.root, NEW)['receipt']['sidecar_review']['review_ready']])
        put(self.docs / 'staletoast-system-fit-appraisals-z-2026-11-01.json', weekly.dump(dict(records=[
            dict(id='C-026', kind='research', review_state='held-conflict')])))
        before = tree(self.root)
        with self.assertRaisesRegex(ValueError, 'conflicting same-date'):
            weekly.run(self.root, NEW, write=True)
        self.assertEqual(before, tree(self.root))

    def test_same_date_rerun_is_byte_identical(self):
        write_sources(self.docs, (('001', D2), ('002', D3)))
        weekly.run(self.root, NEW, write=True)
        first = tree(self.root)
        again = weekly.run(self.root, NEW, write=True)
        self.assertEqual({'unchanged'}, {action for _, _, action in again['changes']})
        self.assertEqual(first, tree(self.root))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, weekly.main(['--date', NEW, '--write', '--root', str(self.root)]))
        self.assertEqual(first, tree(self.root))

    def test_same_date_conflicts_fail_and_preserve_everything(self):
        weekly.run(self.root, NEW, write=True)
        done = tree(self.root)
        write_sources(self.docs, (('001', D2), ('003', D3)))
        with self.assertRaisesRegex(ValueError, 'cannot be overwritten'):
            weekly.run(self.root, NEW, write=True)
        write_sources(self.docs, (('001', D2),))
        self.receipt_path.write_bytes(done['docs/staletoast-weekly-review/2026-11-02.json'] + b' ')
        tampered = tree(self.root)
        with self.assertRaisesRegex(ValueError, 'different weekly review receipt'):
            weekly.run(self.root, NEW, write=True)
        self.assertEqual(tampered, {name: data for name, data in tree(self.root).items()})
        self.receipt_path.write_bytes(done['docs/staletoast-weekly-review/2026-11-02.json'])
        path = self.docs / 'staletoast-chart-history' / f'{NEW}.json'
        edition = json.loads(path.read_text(encoding='utf-8'))
        edition['question'] = 'tampered'
        put(path, weekly.dump(edition))
        tampered = tree(self.root)
        with self.assertRaisesRegex(ValueError, 'cannot be overwritten'):
            weekly.run(self.root, NEW, write=True)
        self.assertEqual(tampered, tree(self.root))

    def test_older_dates_cannot_overwrite(self):
        weekly.run(self.root, NEW, write=True)
        done = tree(self.root)
        for older in ('2026-11-01', SEED, '2026-10-12'):
            with self.assertRaisesRegex(ValueError, 'older'):
                weekly.run(self.root, older, write=True)
        self.assertEqual(done, tree(self.root))

    def test_invalid_input_writes_nothing(self):
        before = tree(self.root)
        write_sources(self.docs, (('001', D2), ('002', D3)))
        appraisals = self.docs / 'collaborative-intelligence-source-appraisals.md'
        lines = [line for line in appraisals.read_text(encoding='utf-8').splitlines(True) if not line.startswith('| 002')]
        put(appraisals, ''.join(lines))
        mid = tree(self.root)
        with self.assertRaisesRegex(ValueError, 'IDs do not match'):
            weekly.run(self.root, NEW, write=True)
        self.assertEqual(mid, tree(self.root))
        self.assertFalse((self.docs / 'staletoast-weekly-review').exists())
        self.assertNotEqual(before, mid)

    def test_failure_during_swap_restores_every_file(self):
        before = tree(self.root)
        real, calls = os.replace, []

        def flaky(source, target):
            calls.append(target)
            if len(calls) == 3:
                raise OSError('simulated disk failure')
            return real(source, target)

        with patch.object(weekly.os, 'replace', flaky), self.assertRaises(OSError):
            weekly.run(self.root, NEW, write=True)
        self.assertEqual(3, len(calls))
        self.assertEqual(before, tree(self.root))
        self.assertFalse((self.docs / 'staletoast-weekly-review').exists())

    def test_command_has_no_network_process_or_provider_code(self):
        source = (ROOT / 'scripts' / 'weekly_hot100.py').read_text(encoding='utf-8')
        for token in ('subprocess', 'urllib', 'socket', 'http.client', 'requests', 'os.system'):
            self.assertNotIn(token, source)


if __name__ == '__main__':
    unittest.main()

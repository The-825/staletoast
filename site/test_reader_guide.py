import copy
import unittest
import hashlib
import json
import subprocess
from pathlib import Path

from build_reader_guide import build


class ReaderGuideTests(unittest.TestCase):
    def fixtures(self):
        config = {'schema_version': 1, 'date': '2026-10-24', 'status': 'proposal', 'collections': [
            {'id': 'question', 'title': 'A question', 'description': 'Context',
             'selections': [{'kind': 'research', 'id': '010', 'why_selected': 'Reason'}]}]}
        rows = [{'id': '010', 'record_state': 'reviewed-catalog', 'title': 'Study',
                 'url': 'https://example.org', 'review_depth': 'screened-structural',
                 'finding': 'Bounded finding', 'boundary': 'Not independently reproduced',
                 'evidenceOrder': 17}]
        return config, rows

    def test_preserves_findings_limits_and_original_order(self):
        config, rows = self.fixtures()
        before = copy.deepcopy(rows)
        card = build(config, rows, [])['collections'][0]['selections'][0]
        self.assertEqual('Not independently reproduced', card['limits'])
        self.assertEqual('Bounded finding', card['takeaway'])
        self.assertEqual(before, rows)
        self.assertNotIn('quality_score', card)

    def test_missing_or_unpromoted_source_cannot_be_recommended(self):
        config, rows = self.fixtures()
        with self.assertRaises(ValueError):
            build(config, [], [])
        rows[0]['record_state'] = 'candidate-not-promoted'
        with self.assertRaises(ValueError):
            build(config, rows, [])

    def test_identity_only_repository_and_duplicate_sources_fail(self):
        config, rows = self.fixtures()
        with self.assertRaises(ValueError):
            build(config, rows + rows, [])
        config['collections'][0]['selections'][0].update(kind='repository', id='R-001')
        with self.assertRaises(ValueError):
            build(config, [], [{'id': 'R-001', 'evidence_depth': 'source-assessment'}])

    def test_empty_editorial_reason_is_rejected(self):
        config, rows = self.fixtures()
        config['collections'][0]['selections'][0]['why_selected'] = '  '
        with self.assertRaises(ValueError):
            build(config, rows, [])

    def test_malformed_editorial_schema_is_rejected(self):
        for change in ['version', 'title', 'description', 'identity', 'empty-selections', 'empty-collections']:
            config, rows = self.fixtures()
            if change == 'version':
                config['schema_version'] = 2
            elif change == 'empty-collections':
                config['collections'] = []
            elif change == 'empty-selections':
                config['collections'][0]['selections'] = []
            else:
                config['collections'][0][{'identity': 'id'}.get(change, change)] = '  '
            with self.subTest(change=change), self.assertRaises(ValueError):
                build(config, rows, [])

    def test_repository_summary_keeps_original_evidence_without_repeating_it(self):
        config, _ = self.fixtures()
        item = config['collections'][0]['selections'][0]
        item.update(kind='repository', id='R-001', takeaway='Visible recovery mechanism',
                    limits='Not executed')
        rows = [{'id': 'R-001', 'repository': 'example/project', 'url': 'https://example.org',
                 'evidence_depth': 'readme-screened', 'evidence_note': 'Original bounded source note'}]
        card = build(config, [], rows)['collections'][0]['selections'][0]
        self.assertEqual('Original bounded source note', card['original_evidence_note'])
        self.assertNotEqual(card['takeaway'], card['limits'])
        item['limits'] = item['takeaway']
        with self.assertRaises(ValueError):
            build(config, [], rows)

    def test_frozen_handoff_binds_inputs_to_the_recorded_git_revision(self):
        root = Path(__file__).resolve().parents[1]
        archives = list((root / 'exports/reader-guide').glob('*.json'))
        self.assertTrue(archives, 'No frozen reader guide for the consumer')
        for archive in archives:
            payload = json.loads(archive.read_text(encoding='utf-8'))
            self.assertEqual(archive.stem, payload['source_revision'])
            for path, expected in payload['source_hashes'].items():
                committed = subprocess.check_output(
                    ['git', 'show', payload['source_revision'] + ':' + path], cwd=root)
                self.assertEqual(expected, hashlib.sha256(committed).hexdigest(), path)


if __name__ == '__main__':
    unittest.main()

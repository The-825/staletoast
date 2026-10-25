import copy
import unittest

from build_reader_guide import build


class ReaderGuideTests(unittest.TestCase):
    def fixtures(self):
        config = {'date': '2026-10-24', 'status': 'proposal', 'collections': [
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


if __name__ == '__main__':
    unittest.main()

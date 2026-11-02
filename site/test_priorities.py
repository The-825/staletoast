import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import build_priorities as priorities


class PriorityTests(unittest.TestCase):
    def test_existing_projection_and_view_reproduce_without_editorial_changes(self):
        old = json.loads((priorities.DOCS / 'staletoast-appraisal-priorities.json').read_text(encoding='utf-8'))
        actual = priorities.build(priorities.DOCS, old['date'])
        self.assertEqual(old, actual)
        self.assertEqual((priorities.DOCS / 'staletoast-appraisal-priorities.md').read_text(encoding='utf-8'), priorities.render(actual))

    def fixture(self, root, extra='', app_extra='', batch=None, held=()):
        batch = batch or {'research': [], 'repositories': []}
        records = [dict(id=value, kind='research', state='held', reason='synthetic') for value in held]
        (root / 'staletoast-expansion-2026-11-01.json').write_text(json.dumps(batch), encoding='utf-8')
        (root / 'staletoast-source-dispositions.json').write_text(json.dumps(dict(schema_version=1, records=records)), encoding='utf-8')
        values = {
            'research_source_sha256': '## Source ledger\n| 001 | ["One"](https://example.org/one) | scope | finding | impact | limit |\n' + extra + '### Entry metadata\n| 001 | repeated metadata | a | b | c |\n',
            'appraisal_source_sha256': '| 001 | design | D2 adjacent | SYNTHETIC | single | limits | CI-006 |\n' + app_extra,
            'repository_source_sha256': json.dumps({'repositories': []}),
        }
        for field, text in values.items():
            (root / priorities.SOURCES[field]).write_text(text, encoding='utf-8')

    def test_growth_escaped_pipes_and_candidate_depth_come_from_owning_sources(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root,
                         '| C-025 | ["Recovery \\| review"](https://example.org/two) | scope | finding | impact | limit | candidate |\n',
                         '| C-025 | design | D2 adjacent | SYNTHETIC | single | selected-full-text: bounded review | CI-006 |\n')
            actual = priorities.build(root, '2026-10-13')
            rows = actual['research']
            self.assertEqual(2, len(rows))
            self.assertEqual('Recovery | review', rows[1]['title'])
            self.assertEqual('selected-full-text', rows[1]['review_depth'])
            self.assertEqual('candidate-not-promoted', rows[1]['record_state'])
            self.assertEqual(rows[0]['appraisal_priority_rank'], rows[1]['appraisal_priority_rank'])
            self.assertIn('Recovery \\| review', priorities.render(actual))

    def test_automated_intake_has_one_constant_key_after_appraised_rows_and_held_is_excluded(self):
        auto_app = '| {0} | design | D3 direct | SYNTHETIC | longitudinal | abstract-only: automated relevance screen |  |\n'
        ledger = ''.join(f'| {value} | ["{value}"](https://example.org/{value}) | s | f | i | l | c |\n' for value in ('C-026', 'C-027', 'C-028'))
        batch = {'research': [dict(id=value, kind='research', screen_method='automated-abstract-topic-screen-v1') for value in ('C-026', 'C-027', 'C-028')],
                 'repositories': []}
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root, ledger, ''.join(auto_app.format(value) for value in ('C-026', 'C-027', 'C-028')), batch, held=['C-028'])
            actual = priorities.build(root, '2026-11-01')
            rows = {row['id']: row for row in actual['research']}
            self.assertEqual({'001', 'C-026', 'C-027'}, set(rows))
            for value in ('C-026', 'C-027'):
                # The placeholder grade is the best tier on purpose: it must not buy any priority.
                self.assertEqual('automated-screen', rows[value]['appraisal_state'])
                self.assertIsNone(rows[value]['directness'])
                self.assertIsNone(rows[value]['horizon'])
                self.assertEqual(list(priorities.INTAKE_KEY), rows[value]['priority_key'])
                self.assertEqual('intake awaiting appraisal', rows[value]['priority_claim'])
            self.assertEqual(rows['C-026']['appraisal_priority_rank'], rows['C-027']['appraisal_priority_rank'])
            self.assertGreater(rows['C-026']['appraisal_priority_rank'], rows['001']['appraisal_priority_rank'])
            self.assertEqual('source-screened', rows['001']['appraisal_state'])
            view = priorities.render(actual)
            self.assertIn('unappraised', view)
            self.assertNotIn('D3 direct / longitudinal', view)
            self.assertNotIn('C-028', view)

    def test_missing_dispositions_fail_closed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            (root / 'staletoast-source-dispositions.json').unlink()
            with self.assertRaisesRegex(ValueError, 'required'):
                priorities.build(root, '2026-10-13')

    def test_missing_appraisal_duplicate_and_malformed_rows_fail(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root, '| C-025 | ["Two"](https://example.org/two) | a | b | c | d | e |\n')
            with self.assertRaisesRegex(ValueError, 'IDs do not match'):
                priorities.build(root, '2026-10-13')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            priorities.identified_rows('| 001 | a |\n| 001 | b |', {2})
        with self.assertRaisesRegex(ValueError, 'malformed'):
            priorities.identified_rows('| 001 | a |', {7})

    def test_unknown_claim_fails_and_empty_claims_do_not_gain_priority(self):
        with self.assertRaisesRegex(ValueError, 'unknown claim'):
            priorities.claim_priority(['CI-999'])
        self.assertEqual(len(priorities.GAPS), priorities.claim_priority([]))

    def test_crlf_and_lf_sources_produce_identical_hashes_and_priorities(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            first = priorities.build(root, '2026-10-13')
            for name in priorities.SOURCES.values():
                path = root / name
                path.write_bytes(path.read_text(encoding='utf-8').encode('utf-8').replace(b'\n', b'\r\n'))
            self.assertEqual(first, priorities.build(root, '2026-10-13'))


if __name__ == '__main__':
    unittest.main()

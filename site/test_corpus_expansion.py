import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from repository_landscape import validate
from build_catalogs import research_catalog


class CorpusExpansionTests(unittest.TestCase):
    def setUp(self):
        self.landscape = json.loads((ROOT / 'docs/collaborative-intelligence-repository-landscape.json').read_text(encoding='utf-8'))

    def test_relevance_screens_have_no_mechanism_or_claim_findings(self):
        rows = [row for row in self.landscape['repositories'] if row['evidence_depth'] == 'readme-relevance-screened']
        self.assertEqual(665, len(rows))
        self.assertEqual([], validate(self.landscape))
        for change in ('claim', 'mechanism', 'digest', 'status'):
            data = copy.deepcopy(self.landscape)
            row = next(item for item in data['repositories'] if item['evidence_depth'] == 'readme-relevance-screened')
            if change == 'claim':
                row['claims'] = ['CI-006']
            elif change == 'mechanism':
                row['mechanisms'][next(iter(row['mechanisms']))] = 'V'
            elif change == 'digest':
                row['readme_content_sha256'] = ''
            else:
                row['assessment_status'] = 'mechanism-screened'
            with self.subTest(change=change):
                self.assertTrue(validate(data))

    def test_unappraised_research_does_not_display_zero_quality_scores(self):
        rows = research_catalog()
        self.assertEqual(500, len(rows))
        automated = [row for row in rows if 'automated relevance screen' in row['flags']]
        self.assertEqual(377, len(automated))
        for row in automated:
            self.assertIsNone(row['directnessValue'])
            self.assertIsNone(row['horizonValue'])
            self.assertEqual([], row['claims'])
            self.assertEqual('candidate-not-promoted', row['record_state'])


if __name__ == '__main__':
    unittest.main()

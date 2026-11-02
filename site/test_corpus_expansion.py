import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from repository_landscape import validate
from build_catalogs import repository_catalog, research_catalog
from intake_state import IntakeState, validate_catalog_semantics


class CorpusExpansionTests(unittest.TestCase):
    def setUp(self):
        self.landscape = json.loads((ROOT / 'docs/collaborative-intelligence-repository-landscape.json').read_text(encoding='utf-8'))
        self.batch = json.loads((ROOT / 'docs/staletoast-expansion-2026-11-01.json').read_text(encoding='utf-8'))
        self.state = IntakeState(ROOT / 'docs')

    def test_relevance_screens_have_no_mechanism_or_claim_findings(self):
        rows = [row for row in self.landscape['repositories'] if row['evidence_depth'] == 'readme-relevance-screened']
        # Rejected intake stays in the landscape, so the count follows the batch rather than a fixed total.
        self.assertEqual({row['id'] for row in self.batch['repositories']}, {row['id'] for row in rows})
        self.assertEqual([], validate(self.landscape))
        for change in ('claim', 'mechanism', 'digest', 'status', 'date'):
            data = copy.deepcopy(self.landscape)
            row = next(item for item in data['repositories'] if item['evidence_depth'] == 'readme-relevance-screened')
            if change == 'claim':
                row['claims'] = ['CI-006']
            elif change == 'mechanism':
                row['mechanisms'][next(iter(row['mechanisms']))] = 'V'
            elif change == 'digest':
                row['readme_content_sha256'] = ''
            elif change == 'date':
                row['stars_observed'] = row['stars_observed'] or 1
                row.pop('popularity_observed_date', None)
            else:
                row['assessment_status'] = 'mechanism-screened'
            with self.subTest(change=change):
                self.assertTrue(validate(data))

    def test_unappraised_research_has_no_order_grade_or_claim(self):
        rows = research_catalog()
        automated = [row for row in rows if row['appraisal_state'] == 'automated-screen']
        active_batch = {row['id'] for row in self.batch['research']} - self.state.held_ids('research')
        self.assertEqual(active_batch, {row['id'] for row in automated})
        for row in automated:
            for field in ('evidenceOrder', 'directness', 'directnessValue', 'horizon', 'horizonValue'):
                self.assertIsNone(row[field], field)
            self.assertEqual([], row['claims'])
            self.assertEqual('candidate-not-promoted', row['record_state'])

    def test_appraised_research_keeps_its_contiguous_order_ahead_of_automated_intake(self):
        rows = research_catalog()
        ranked = [row for row in rows if row['appraisal_state'] == 'source-screened']
        self.assertGreaterEqual(len(ranked), 123)
        self.assertEqual(list(range(1, len(ranked) + 1)), [row['evidenceOrder'] for row in ranked])
        self.assertEqual(rows[:len(ranked)], ranked)
        self.assertTrue(all(row['evidenceOrderCount'] == len(ranked) for row in rows))
        self.assertTrue(all(isinstance(row['directnessValue'], int) for row in ranked))

    def test_repository_catalog_states_dates_and_held_exclusion(self):
        research, repositories = research_catalog(), repository_catalog()
        validate_catalog_semantics(research, repositories)
        self.assertEqual(set(), self.state.held_ids('repository') & {row['id'] for row in repositories})
        self.assertEqual(set(), self.state.held_ids('research') & {row['id'] for row in research})
        active_batch = {row['id'] for row in self.batch['repositories']} - self.state.held_ids('repository')
        automated = [row for row in repositories if row['appraisal_state'] == 'automated-screen']
        self.assertEqual(active_batch, {row['id'] for row in automated})
        for row in automated:
            self.assertEqual({'U'}, set(row['mechanisms'].values()))
            self.assertEqual('github-reported-unverified', row['licenseBasis'])
            if row['stars_observed'] is not None:
                self.assertEqual(row['popularity_observed_date'], row['starsObservedDate'])
        self.assertGreaterEqual(len(repositories), self.batch['totals']['repositories'])
        self.assertTrue(all(row['appraisal_state'] in {'automated-screen', 'source-screened'} for row in repositories))


if __name__ == '__main__':
    unittest.main()

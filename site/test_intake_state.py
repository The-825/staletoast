import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import intake_state as intake


def batch(**extra):
    return dict(
        research=[dict(id='C-026', kind='research', screen_method=intake.SCREEN_METHODS['research'])],
        repositories=[dict(id='R-337', kind='repository', screen_method=intake.SCREEN_METHODS['repository']),
                      dict(id='R-338', kind='repository', screen_method=intake.SCREEN_METHODS['repository'])],
        **extra)


def held(identity='R-337', kind='repository', **extra):
    return dict(id=identity, kind=kind, state='held', reason='synthetic reason', **extra)


def write(root, records=None, batch_value=None, schema=1):
    (root / intake.BATCH_NAME).write_text(json.dumps(batch_value or batch()), encoding='utf-8')
    if records is not None:
        (root / intake.DISPOSITIONS_NAME).write_text(json.dumps(dict(schema_version=schema, records=records)), encoding='utf-8')


class IntakeStateTests(unittest.TestCase):
    def load(self, **kwargs):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, **kwargs)
            return intake.IntakeState(root)

    def test_missing_or_malformed_dispositions_fail_closed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, None)
            with self.assertRaisesRegex(ValueError, 'required'):
                intake.IntakeState(root)
        for records, schema in [([], 2), ([dict(held(), state='active')], 1), ([dict(held(), reason=' ')], 1),
                                ([dict(held(), kind='paper')], 1), ([held(), held()], 1),
                                ([dict(held(), replacement_id='')], 1)]:
            with self.subTest(records=records, schema=schema), self.assertRaises(ValueError):
                self.load(records=records, schema=schema)

    def test_default_is_active_and_state_comes_from_structured_screen_method(self):
        state = self.load(records=[])
        self.assertFalse(state.is_held('repository', 'R-337'))
        self.assertEqual(intake.AUTOMATED, state.appraisal_state('research', 'C-026'))
        self.assertEqual(intake.AUTOMATED, state.appraisal_state('repository', 'R-338'))
        # A record outside the batch is a pre-existing source, whatever its explanatory flags say.
        self.assertEqual(intake.SCREENED, state.appraisal_state('research', '001'))

    def test_unknown_screen_method_is_rejected(self):
        value = batch()
        value['research'][0]['screen_method'] = 'expert-panel'
        with self.assertRaisesRegex(ValueError, 'screen method'):
            self.load(records=[], batch_value=value).appraisal_state('research', 'C-026')

    def test_held_ids_are_kind_scoped_and_need_batch_records(self):
        state = self.load(records=[held(replacement_id='R-338')])
        self.assertTrue(state.is_held('repository', 'R-337'))
        self.assertFalse(state.is_held('research', 'R-337'))
        self.assertEqual({'R-337'}, state.held_ids('repository'))
        self.assertEqual(set(), state.held_ids('research'))
        for records in ([held('R-999')], [held(replacement_id='R-999')], [held(replacement_id='R-337')],
                        [held(replacement_id='R-338'), held('R-338')], [held('C-026')]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                self.load(records=records)

    def test_source_hashes_bind_dispositions(self):
        first = self.load(records=[]).source_hashes()
        second = self.load(records=[held()]).source_hashes()
        self.assertNotEqual(first['disposition_source_sha256'], second['disposition_source_sha256'])
        self.assertEqual(first['batch_source_sha256'], second['batch_source_sha256'])

    def test_catalog_semantics_reject_ranked_or_graded_automated_research(self):
        ranked = dict(id='001', appraisal_state='source-screened', evidenceOrder=1, claims=[])
        auto = dict(id='C-026', appraisal_state='automated-screen', evidenceOrder=None, directness=None, horizon=None,
                    directnessValue=None, horizonValue=None, claims=[])
        repository = dict(id='R-337', appraisal_state='automated-screen', evidence_depth='readme-relevance-screened',
                          mechanisms=dict(a='U', b='U'), claims=[])
        intake.validate_catalog_semantics([ranked, auto], [repository])
        bad_cases = {
            'order': [ranked, dict(auto, evidenceOrder=2)],
            'grade': [ranked, dict(auto, directness='D3 direct')],
            'zero': [ranked, dict(auto, horizonValue=0)],
            'interleaved': [auto, ranked],
            'state': [dict(ranked, appraisal_state='expert-appraised')],
            'gap': [dict(ranked, evidenceOrder=2)],
        }
        for name, research in bad_cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                intake.validate_catalog_semantics(research, [repository])
        for changed in (dict(repository, mechanisms=dict(a='V')), dict(repository, claims=['CI-006']),
                        dict(repository, appraisal_state='source-screened')):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                intake.validate_catalog_semantics([ranked], [changed])


if __name__ == '__main__':
    unittest.main()

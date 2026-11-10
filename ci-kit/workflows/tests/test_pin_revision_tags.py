import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
ROOT = KIT.parents[1]
SPEC = importlib.util.spec_from_file_location('pin_revision_tags', KIT / 'pin_revision_tags.py')
tags = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tags)
A, B, C = 'a' * 40, 'b' * 40, 'c' * 40


def fake_api(present, wrong=(), create_status=201, refuse=()):
    calls = []

    def api(method, suffix, body):
        calls.append((method, suffix, body))
        if method == 'GET':
            revision = suffix.rsplit('/', 1)[1]
            if revision in wrong:
                return 200, {'object': {'sha': 'd' * 40, 'type': 'commit'}}
            if revision in present:
                return 200, {'object': {'sha': revision, 'type': 'commit'}}
            return 404, None
        if body['sha'] in refuse:
            return 403, None
        if create_status == 201:
            present.add(body['sha'])
        return create_status, None
    return api, calls


class PinRevisionTagTests(unittest.TestCase):
    def test_collects_every_pinned_revision_and_rejects_other_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'exports/reader-guide').mkdir(parents=True)
            (root / 'exports' / f'{A}.json').write_text('{}')
            (root / 'exports/reader-guide' / f'{B}.json').write_text('{}')
            (root / 'catalog-export-pin.json').write_text(json.dumps({'source_revision': C}))
            self.assertEqual([A, B, C], tags.pinned_revisions(root))
            (root / 'exports' / 'main.json').write_text('{}')
            with self.assertRaises(ValueError):
                tags.pinned_revisions(root)

    def test_repository_pins_are_all_collected(self):
        revisions = tags.pinned_revisions()
        pin = json.loads((ROOT / 'catalog-export-pin.json').read_text(encoding='utf-8'))
        self.assertIn(pin['source_revision'], revisions)
        self.assertEqual(len(revisions), len(set(revisions)))

    def test_creates_only_missing_tags_and_never_touches_existing_ones(self):
        api, calls = fake_api({A})
        self.assertEqual({A: 'present', B: 'created'}, tags.ensure_tags([A, B], api))
        posts = [call for call in calls if call[0] == 'POST']
        self.assertEqual([('POST', 'git/refs', {'ref': f'refs/tags/frozen/{B}', 'sha': B})], posts)
        self.assertTrue(all(call[0] in ('GET', 'POST') for call in calls))

    def test_check_mode_reports_without_writing(self):
        api, calls = fake_api(set())
        self.assertEqual({A: 'missing'}, tags.ensure_tags([A], api, write=False))
        self.assertFalse([call for call in calls if call[0] != 'GET'])

    def test_tag_on_another_commit_and_failed_creation_fail_closed(self):
        api, _ = fake_api(set(), wrong={A})
        with self.assertRaises(ValueError):
            tags.ensure_tags([A], api)
        api, _ = fake_api(set(), create_status=422)
        with self.assertRaises(ValueError):
            tags.ensure_tags([A], api)

    def test_refused_revision_is_reported_and_the_rest_are_still_tagged(self):
        api, calls = fake_api(set(), refuse={A})
        self.assertEqual({A: 'refused', B: 'created', C: 'created'}, tags.ensure_tags([A, B, C], api))
        self.assertEqual(3, len([call for call in calls if call[0] == 'POST']))

    def test_workflow_runs_from_main_with_the_installed_script(self):
        text = (ROOT / '.github/workflows/pin-tags.yml').read_text(encoding='utf-8')
        self.assertIn('ref: main', text)
        self.assertIn('python ci-kit/workflows/pin_revision_tags.py', text)
        self.assertIn('workflows: ["Auto-merge agent PRs"]', text)
        self.assertNotIn('pull_request', text)


class TierPolicySelfTest(unittest.TestCase):
    def test_tier_policy_selftest_passes(self):
        run = subprocess.run([sys.executable, str(KIT / 'greenlight_tiers.py'), '--selftest'],
                             capture_output=True, text=True)
        self.assertEqual(0, run.returncode, run.stdout)


if __name__ == '__main__':
    unittest.main()

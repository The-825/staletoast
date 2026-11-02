import copy
import inspect
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import validate_system_fit_appraisals as v

ID = v.NAME


def pools():
    """Synthetic base pool, the proposal's pool and a live pool that grew later."""
    base = {'schema_version': 1, 'records': [{'pool_id': 'P-1'}, {'pool_id': 'P-2'}]}
    event = {'assessment_id': ID, 'source_count': 3}
    frozen = copy.deepcopy(base)
    frozen[v.HISTORY_KEY] = [event]
    live = copy.deepcopy(frozen)
    return base, frozen, live


class FrozenFileTests(unittest.TestCase):
    def test_identical_and_crlf_equivalent_text_pass(self):
        frozen = {'a.json': b'{\n  "k": 1\n}\n'}
        v.check_frozen_files(frozen, {'a.json': b'{\n  "k": 1\n}\n'})
        v.check_frozen_files(frozen, {'a.json': b'{\r\n  "k": 1\r\n}\r\n'})
        v.check_frozen_files({'a.json': b'{\r\n}\r\n'}, {'a.json': b'{\n}\n'})

    def test_only_crlf_is_normalized(self):
        with self.assertRaisesRegex(ValueError, 'Frozen proposal file changed'):
            v.check_frozen_files({'a.json': b'a\nb'}, {'a.json': b'a\rb'})
        with self.assertRaisesRegex(ValueError, 'Frozen proposal file changed'):
            v.check_frozen_files({'a.json': b'a\nb'}, {'a.json': b'a\nb '})

    def test_tampered_or_missing_file_fails(self):
        with self.assertRaisesRegex(ValueError, 'Frozen proposal file changed'):
            v.check_frozen_files({'a.json': b'{"k": 1}'}, {'a.json': b'{"k": 2}'})
        with self.assertRaisesRegex(ValueError, 'Required historical file missing'):
            v.check_frozen_files({'a.json': b'{}'}, {})


class PoolHistoryTests(unittest.TestCase):
    def test_unchanged_pool_passes(self):
        base, frozen, live = pools()
        self.assertEqual(v.check_pool_history(base, frozen, live, ID), {'P-1', 'P-2'})

    def test_future_pool_and_history_additions_are_not_corruption(self):
        base, frozen, live = pools()
        live['records'].append({'pool_id': 'P-3'})
        live[v.HISTORY_KEY].append({'assessment_id': 'later-assessment'})
        live['holds'] = [{'id': 'R-1', 'state': 'held'}]
        self.assertEqual(v.check_pool_history(base, frozen, live, ID), {'P-1', 'P-2', 'P-3'})

    def test_missing_or_changed_historical_event_fails(self):
        base, frozen, live = pools()
        live[v.HISTORY_KEY] = []
        with self.assertRaisesRegex(ValueError, 'Historical assessment event'):
            v.check_pool_history(base, frozen, live, ID)
        base, frozen, live = pools()
        live[v.HISTORY_KEY][0]['source_count'] = 4
        with self.assertRaisesRegex(ValueError, 'Historical assessment event'):
            v.check_pool_history(base, frozen, live, ID)
        base, frozen, live = pools()
        del live[v.HISTORY_KEY]
        with self.assertRaisesRegex(ValueError, 'Historical assessment event'):
            v.check_pool_history(base, frozen, live, ID)

    def test_missing_historical_pool_row_fails(self):
        base, frozen, live = pools()
        live['records'] = [{'pool_id': 'P-2'}]
        with self.assertRaisesRegex(ValueError, 'Historical pool records missing: P-1'):
            v.check_pool_history(base, frozen, live, ID)

    def test_proposal_must_preserve_base_and_append_exactly_one_event(self):
        base, frozen, live = pools()
        frozen['records'].append({'pool_id': 'P-9'})
        with self.assertRaisesRegex(ValueError, 'Proposal changed existing pool content: records'):
            v.check_pool_history(base, frozen, live, ID)
        base, frozen, live = pools()
        frozen[v.HISTORY_KEY].append({'assessment_id': 'extra'})
        with self.assertRaisesRegex(ValueError, 'Expected one appended assessment event'):
            v.check_pool_history(base, frozen, live, ID)
        base, frozen, live = pools()
        frozen[v.HISTORY_KEY][0]['assessment_id'] = 'other'
        with self.assertRaisesRegex(ValueError, 'not this assessment'):
            v.check_pool_history(base, frozen, live, ID)

    def test_prior_history_must_be_a_prefix(self):
        base, frozen, live = pools()
        base[v.HISTORY_KEY] = [{'assessment_id': 'older'}]
        with self.assertRaisesRegex(ValueError, 'Expected one appended assessment event'):
            v.check_pool_history(base, frozen, live, ID)
        frozen[v.HISTORY_KEY] = [{'assessment_id': 'older'}, {'assessment_id': ID, 'source_count': 3}]
        live = copy.deepcopy(frozen)
        self.assertEqual(v.check_pool_history(base, frozen, live, ID), {'P-1', 'P-2'})


class PriorHeldTests(unittest.TestCase):
    def test_frozen_held_set_is_checked(self):
        held = {'H-%d' % i for i in range(41)}
        v.check_prior_held(held, {'R-1', 'R-2'})
        with self.assertRaisesRegex(ValueError, 'Prior held set changed'):
            v.check_prior_held(set(list(held)[:40]), {'R-1'})
        with self.assertRaisesRegex(ValueError, 'silently shortlisted'):
            v.check_prior_held(held, {'R-1', 'H-3'})


class SnapshotPinTests(unittest.TestCase):
    def test_pins_are_explicit_full_ids_and_not_caller_supplied(self):
        self.assertEqual(v.PROPOSAL_REVISION, '9618d874bc62db8084b891c299c375241fddd351')
        self.assertRegex(v.PROPOSAL_SOURCE_BASE, r'^[0-9a-f]{40}$')
        self.assertEqual(list(inspect.signature(v.validate).parameters), ['evidence'])

    def test_revision_must_be_full_id_in_history(self):
        v.verify_revision(v.PROPOSAL_REVISION)
        v.verify_revision(v.PROPOSAL_SOURCE_BASE)
        with self.assertRaisesRegex(ValueError, 'Pinned revision not found'):
            v.verify_revision(v.PROPOSAL_REVISION[:12])
        with self.assertRaisesRegex(ValueError, 'Pinned revision not found'):
            v.verify_revision('0' * 40)
        with self.assertRaisesRegex(ValueError, 'Pinned revision not found'):
            v.verify_revision('HEAD')

    def test_published_proposal_validates(self):
        result = v.validate()
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['proposal_revision'], v.PROPOSAL_REVISION)


class FrozenSnapshotEndToEndTests(unittest.TestCase):
    """Patch only the git reader so the real validate() sees a tampered snapshot."""

    def reader(self, mutate):
        real = v.git_bytes

        def read(ref, path, root=v.ROOT):
            raw = real(ref, path, root)
            return mutate(ref, path, raw)
        return read

    def test_tampered_frozen_proposal_or_receipt_is_rejected(self):
        for path in v.FROZEN_FILES:
            def mutate(ref, p, raw, path=path):
                return raw + b' ' if (ref == v.PROPOSAL_REVISION and p == path) else raw
            with self.subTest(path=path), patch.object(v, 'git_bytes', self.reader(mutate)):
                with self.assertRaisesRegex(ValueError, 'Frozen proposal file changed'):
                    v.validate()

    def test_missing_historical_receipt_is_rejected(self):
        receipt = 'docs/staletoast-system-fit-review-2026-11-01.json'

        def read(ref, path, root=v.ROOT):
            if path == receipt:
                raise ValueError('Cannot read ' + path + ' at ' + ref)
            return real(ref, path, root)
        real = v.git_bytes
        with patch.object(v, 'git_bytes', read):
            with self.assertRaisesRegex(ValueError, 'Cannot read'):
                v.validate()

    def test_frozen_lf_and_crlf_text_are_equivalent(self):
        def mutate(ref, path, raw):
            if ref == v.PROPOSAL_REVISION and path in v.FROZEN_FILES:
                return raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            return raw
        with patch.object(v, 'git_bytes', self.reader(mutate)):
            self.assertEqual(v.validate()['status'], 'pass')

    def test_proposal_diff_is_bound_to_the_pinned_revision_not_later_work(self):
        calls = []

        def diff(args, **kwargs):
            calls.append(args)
            return 'docs/staletoast-next-round-pool.json\n'
        with patch.object(v.subprocess, 'check_output', diff):
            v.validate()
        self.assertEqual(calls, [['git', 'diff', '--name-only', v.PROPOSAL_SOURCE_BASE, v.PROPOSAL_REVISION]])

        # A proposal that touched a ranked or generated path is still rejected.
        with patch.object(v.subprocess, 'check_output', lambda *a, **k: 'site/unrelated.py\n'):
            with self.assertRaisesRegex(ValueError, 'Unexpected canonical/chart change'):
                v.validate()


if __name__ == '__main__':
    unittest.main()

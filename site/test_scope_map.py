import copy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import build_scope_map as scope_map


class ScopeMapTests(unittest.TestCase):
    def setUp(self):
        self.scope = json.loads(scope_map.SOURCE.read_text(encoding='utf-8'))
        self.baseline = json.loads(
            (scope_map.DOCS.parent / self.scope['baseline_artifact']).read_text(encoding='utf-8'))
        self.claims = scope_map.claim_ids(scope_map.CLAIMS.read_text(encoding='utf-8'))

    def check(self, scope):
        scope_map.validate(scope, self.baseline, self.claims)

    def component(self, scope, cid):
        return next(item for item in scope['components'] if item['id'] == cid)

    def test_committed_map_is_valid_and_its_view_is_current(self):
        self.check(self.scope)
        self.assertEqual(scope_map.VIEW.read_text(encoding='utf-8'), scope_map.render(self.scope))

    def test_established_components_mirror_the_baseline_artifact(self):
        established = [item['id'] for item in self.scope['components'] if item['status'] == 'established']
        self.assertEqual([item['id'] for item in self.baseline['baseline_capabilities']], established)

    def test_added_component_cannot_claim_routing_it_does_not_have(self):
        scope = copy.deepcopy(self.scope)
        self.component(scope, 'security-and-containment')['status'] = 'established'
        with self.assertRaisesRegex(ValueError, 'absent from the baseline artifact'):
            self.check(scope)

    def test_established_component_cannot_drift_from_the_baseline(self):
        scope = copy.deepcopy(self.scope)
        self.component(scope, 'memory-and-correction')['screen_terms'].append('embedding')
        with self.assertRaisesRegex(ValueError, 'drifted'):
            self.check(scope)

    def test_dropping_a_routed_component_fails(self):
        scope = copy.deepcopy(self.scope)
        scope['components'] = [item for item in scope['components'] if item['id'] != 'recovery-and-replay']
        scope['owner_scope_terms']['execution'] = ['security-and-containment']
        with self.assertRaisesRegex(ValueError, 'missing from the scope map'):
            self.check(scope)

    def test_unknown_claim_duplicate_id_and_unmapped_term_fail(self):
        scope = copy.deepcopy(self.scope)
        self.component(scope, 'deliberation-and-dissent')['related_claims'].append('CI-999')
        with self.assertRaisesRegex(ValueError, 'unknown claims'):
            self.check(scope)
        scope = copy.deepcopy(self.scope)
        scope['components'].append(copy.deepcopy(scope['components'][-1]))
        with self.assertRaisesRegex(ValueError, 'duplicate component id'):
            self.check(scope)
        scope = copy.deepcopy(self.scope)
        scope['owner_scope_terms']['security'] = ['not-a-component']
        with self.assertRaisesRegex(ValueError, 'must map to known components'):
            self.check(scope)

    def test_added_component_needs_its_boundary_and_proposals(self):
        scope = copy.deepcopy(self.scope)
        del self.component(scope, 'security-and-containment')['boundary']
        with self.assertRaisesRegex(ValueError, 'missing boundary'):
            self.check(scope)

    def test_every_added_component_is_reachable_from_a_scope_term(self):
        reached = {target for targets in self.scope['owner_scope_terms'].values() for target in targets}
        added = {item['id'] for item in self.scope['components'] if item['status'] == 'added-unscreened'}
        self.assertTrue(added <= reached)

    def test_web_json_is_deterministic_and_labels_unscreened_components_explicitly(self):
        first = scope_map.render_web_json(self.scope, scope_map.lf_sha256(scope_map.SOURCE))
        second = scope_map.render_web_json(self.scope, scope_map.lf_sha256(scope_map.SOURCE))
        self.assertEqual(first, second)
        self.assertNotIn(chr(0x2014), first)
        payload = json.loads(first)
        self.assertEqual('docs/staletoast-scope-map.json', payload['source_path'])
        by_id = {row['id']: row for row in payload['components']}
        self.assertEqual('Established in baseline routing', by_id['authority-and-handoff']['status_label'])
        self.assertIsNone(by_id['authority-and-handoff']['boundary'])
        self.assertIn('not yet screened', by_id['security-and-containment']['status_label'])
        self.assertTrue(by_id['security-and-containment']['boundary'])

    def test_check_fails_when_web_view_is_missing_or_stale(self):
        with TemporaryDirectory() as tmp:
            web_path = Path(tmp) / 'scope-map.json'
            with patch.object(scope_map, 'WEB_VIEW', web_path), patch.object(sys, 'argv', ['build_scope_map.py', '--check', '--require-web']):
                with self.assertRaisesRegex(SystemExit, 'missing'):
                    scope_map.main()
            web_path.write_text('{"stale": true}\n', encoding='utf-8')
            with patch.object(scope_map, 'WEB_VIEW', web_path), patch.object(sys, 'argv', ['build_scope_map.py', '--check']):
                with self.assertRaisesRegex(SystemExit, 'stale'):
                    scope_map.main()
            with patch.object(scope_map, 'WEB_VIEW', web_path), patch.object(sys, 'argv', ['build_scope_map.py', '--web-only']):
                scope_map.main()
            with patch.object(scope_map, 'WEB_VIEW', web_path), patch.object(sys, 'argv', ['build_scope_map.py', '--check', '--require-web']):
                scope_map.main()


if __name__ == '__main__':
    unittest.main()

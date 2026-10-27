import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import build_concept_lineage as builder
import build_export

ROOT = builder.ROOT
OWNER = builder.OWNER


def landscape():
    return json.loads((ROOT / builder.LANDSCAPE).read_bytes().replace(b'\r\n', b'\n').decode('utf-8'))


class RuntimeTests(unittest.TestCase):
    def test_runtime_matches_pinned_digest_and_is_lf(self):
        data = (ROOT / builder.RUNTIME).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), builder.RUNTIME_SHA256)
        self.assertNotIn(b'\r', data)
        self.assertEqual(builder.load_runtime().SCHEMA, 'concept-lineage/1')

    def test_runtime_mismatch_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'site').mkdir()
            source = (ROOT / builder.RUNTIME).read_bytes()
            (Path(tmp) / builder.RUNTIME).write_bytes(source + b'\n# changed\n')
            original = builder.ROOT
            builder.ROOT = Path(tmp)
            try:
                with self.assertRaises(builder.BuildError):
                    builder.load_runtime()
            finally:
                builder.ROOT = original


class SourceMappingTests(unittest.TestCase):
    def setUp(self):
        self.rt = builder.load_runtime()
        self.ledger = landscape()
        self.catalog = '3eba46393e5f85d1957d37c40ee1fa5b59d37f86'

    def packet(self, ledger=None):
        rows = builder.source_rows(ledger or self.ledger, self.catalog)
        return {'schema_version': self.rt.SCHEMA, 'data_class': 'public', 'sources': rows,
                'concepts': [], 'consumers': [], 'uses': [], 'evidence': [], 'refinements': []}

    def test_actual_ledger_has_335_records_and_validates(self):
        packet = self.packet()
        self.assertEqual(len(packet['sources']), 335)
        idx = self.rt.validate_graph(packet)
        self.assertEqual(len(idx['sources']), 335)

    def test_catalog_revision_is_tagged_and_string_spelling_fails(self):
        packet = self.packet()
        self.assertEqual(packet['sources'][0]['catalog_revision'], builder.tagged_git(self.catalog))
        packet['sources'][0]['catalog_revision'] = self.catalog
        with self.assertRaises(self.rt.LineageError):
            self.rt.validate_graph(packet)

    def test_identity_depth_and_version_are_copied_exactly(self):
        rows = {r['record_id']: r for r in self.packet()['sources']}
        for item in self.ledger['repositories']:
            row = rows[item['id']]
            self.assertEqual(row['id'], '%s:repository:%s' % (OWNER, item['id']))
            self.assertEqual(row['title'], item['repository'])
            self.assertEqual(row['url'], item['url'])
            self.assertEqual(row['evidence_depth'], item['evidence_depth'])
            self.assertEqual(row['upstream_version'], {'kind': 'git', 'value': item['upstream_revision'], 'reason': None})
            self.assertEqual(row['aliases'], ['%s:repository:%s' % (OWNER, a['key']) for a in item['aliases']])
        self.assertEqual({r['evidence_depth'] for r in rows.values()}, {'readme-screened', 'source-assessment'})

    def test_report_reflects_actual_ledger(self):
        report = builder.ledger_report(self.ledger)
        self.assertEqual(report['repositories'], 335)
        self.assertEqual(report['hosts'], {'github.com': 335})

    def test_duplicate_alias_and_case_collisions_fail(self):
        ledger = copy.deepcopy(self.ledger)
        ledger['repositories'][1]['aliases'] = [{'key': 'dup/alias', 'evidence': 'x'}]
        ledger['repositories'][2]['aliases'] = [{'key': 'Dup/Alias', 'evidence': 'x'}]
        with self.assertRaises(self.rt.LineageError):
            self.rt.validate_graph(self.packet(ledger))
        ledger = copy.deepcopy(self.ledger)
        ledger['repositories'][1] = copy.deepcopy(ledger['repositories'][0])
        with self.assertRaises(self.rt.LineageError):
            self.rt.validate_graph(self.packet(ledger))

    def test_unsafe_source_url_fails(self):
        ledger = copy.deepcopy(self.ledger)
        ledger['repositories'][0]['url'] = 'https://example.com/a/b'
        with self.assertRaises(self.rt.LineageError):
            self.rt.validate_graph(self.packet(ledger))

    def test_non_exact_revision_is_refused(self):
        ledger = copy.deepcopy(self.ledger)
        ledger['repositories'][0]['upstream_revision'] = 'main'
        ledger['repositories'][0]['snapshot_commit'] = ''
        with self.assertRaises(builder.BuildError):
            builder.source_rows(ledger, self.catalog)

    def test_synthetic_mapping_joins_real_sources(self):
        packet = self.packet()
        first = packet['sources'][0]['id']
        packet['concepts'] = [{'id': OWNER + ':concept:synthetic', 'owner': OWNER, 'title': 'Synthetic',
                               'summary': 'Synthetic mapping for the test.', 'source_ids': [first],
                               'relationship': 'conceptual_similarity', 'origin_evidence_id': None}]
        self.rt.validate_graph(packet)
        packet['concepts'][0]['source_ids'] = [OWNER + ':repository:R-9999']
        with self.assertRaises(self.rt.LineageError):
            self.rt.validate_graph(packet)

    def test_eighty_advisory_proposals_do_not_become_sources_or_uses(self):
        packet = self.packet()
        for n in range(80):
            sid = '%s:advisory:adv-%03d' % (OWNER, n)
            packet['sources'].append({
                'id': sid, 'owner': OWNER, 'record_kind': 'advisory', 'record_id': 'adv-%03d' % n,
                'title': 'Advisory %d' % n, 'url': 'https://arxiv.org/abs/0000.%05d' % n,
                'upstream_version': {'kind': 'unknown', 'value': None, 'reason': 'not_captured'},
                'catalog_revision': builder.tagged_git(self.catalog), 'aliases': [], 'evidence_depth': 'unverified'})
        view = self.rt.derive(packet)
        self.assertEqual(sum(view['totals'].values()), 0)
        self.assertEqual(view['source_count'], 415)


class MappingFileTests(unittest.TestCase):
    def read_with(self, mutate):
        doc = json.loads((ROOT / builder.MAPPINGS).read_text(encoding='utf-8'))
        mutate(doc)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / builder.MAPPINGS
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(doc), encoding='utf-8')
            original = builder.ROOT
            builder.ROOT = Path(tmp)
            try:
                return builder.read_mappings(RT)
            finally:
                builder.ROOT = original

    def test_committed_mapping_is_empty_and_admitted(self):
        mappings, admission = builder.read_mappings(RT)
        self.assertEqual(mappings, {name: [] for name in builder.MAPPING_ARRAYS})
        self.assertEqual(admission['policy_sha256'], builder.CONTRACT_SHA256)

    def test_tampered_mapping_wrapper_is_refused(self):
        def add_concept(doc):
            doc['mappings']['concepts'].append({'id': 'x'})

        def extra_key(doc):
            doc['extra'] = 1

        def bad_policy(doc):
            doc['admission']['policy_sha256'] = '0' * 64

        def bad_class(doc):
            doc['admission']['classification'] = 'private_metadata'

        def bad_ref(doc):
            doc['admission']['review_record_ref'] = 'not an id'

        def dot_segment_ref(doc):
            doc['admission']['review_record_ref'] = OWNER + ':evidence:review/../other'

        def admission_extra(doc):
            doc['admission']['reviewer'] = 'x'

        def admission_version(doc):
            doc['admission']['schema_version'] = 'concept-lineage-admission/2'

        def mappings_type(doc):
            doc['mappings']['uses'] = {}

        for mutate in (add_concept, extra_key, bad_policy, bad_class, bad_ref, dot_segment_ref,
                       admission_extra, admission_version, mappings_type):
            with self.assertRaises((builder.BuildError, RT.LineageError)):
                self.read_with(mutate)


RT = builder.load_runtime()


class GeneratedArtifactTests(unittest.TestCase):
    def setUp(self):
        if not (ROOT / builder.PIN).exists():
            self.skipTest('generated artifacts are committed after the builder commit')
        self.pin = json.loads((ROOT / builder.PIN).read_text(encoding='utf-8'))

    def test_files_are_canonical_lf_and_consistent(self):
        manifest_bytes = (ROOT / builder.MANIFEST).read_bytes()
        projection_bytes = (ROOT / builder.PROJECTION).read_bytes()
        for data in (manifest_bytes, projection_bytes, (ROOT / builder.PIN).read_bytes()):
            self.assertNotIn(b'\r', data)
        projection = RT.validate_projection(json.loads(projection_bytes))
        self.assertEqual(RT.canonical_bytes(projection), projection_bytes)
        self.assertEqual(projection['input_manifest_sha256'], hashlib.sha256(manifest_bytes).hexdigest())
        self.assertFalse(projection['authority_granted'])
        self.assertFalse(projection['independent_authenticity_verified'])
        self.assertEqual(len(projection['packet']['sources']), 335)
        for name in builder.MAPPING_ARRAYS:
            self.assertEqual(projection['packet'][name], [])

    def test_projection_omits_private_and_detail_fields(self):
        text = (ROOT / builder.PROJECTION).read_text(encoding='utf-8')
        for sentinel in ('stars_observed', 'evidence_note', 'api.github.com', 'mechanisms', 'license_status'):
            self.assertNotIn(sentinel, text)

    def test_pin_is_exact_and_matches_bytes(self):
        self.assertEqual(set(self.pin), {
            'schema_version', 'owner_repository', 'catalog_revision', 'builder_revision', 'supplier_revision',
            'projection_revision', 'contract_sha256', 'runtime_sha256', 'builder_sha256', 'mapping_sha256',
            'input_manifest_sha256', 'projection_sha256'})
        self.assertEqual(self.pin['schema_version'], 'concept-lineage-pin/1')
        self.assertEqual(self.pin['projection_revision']['kind'], 'git')
        self.assertEqual(self.pin['runtime_sha256'], hashlib.sha256((ROOT / builder.RUNTIME).read_bytes()).hexdigest())
        self.assertEqual(self.pin['builder_sha256'], hashlib.sha256((ROOT / builder.BUILDER).read_bytes()).hexdigest())
        self.assertEqual(self.pin['projection_sha256'], hashlib.sha256((ROOT / builder.PROJECTION).read_bytes()).hexdigest())
        self.assertNotEqual(self.pin['projection_revision'], self.pin['builder_revision'])
        RT.verify_pin_chain(self.pin, (ROOT / builder.MANIFEST).read_bytes(), (ROOT / builder.PROJECTION).read_bytes())

    def test_string_revisions_and_unknown_fields_fail_in_envelopes(self):
        manifest = json.loads((ROOT / builder.MANIFEST).read_text(encoding='utf-8'))
        for name in ('catalog_revision', 'builder_revision', 'supplier_revision'):
            self.assertEqual(manifest[name]['kind'], 'git')
            with self.assertRaises(RT.LineageError):
                RT.validate_input_manifest(dict(manifest, **{name: manifest[name]['value']}))
            with self.assertRaises(RT.LineageError):
                RT.validate_pin(dict(self.pin, **{name: self.pin[name]['value']}))
        with self.assertRaises(RT.LineageError):
            RT.validate_pin(dict(self.pin, latest=True))
        with self.assertRaises(RT.LineageError):
            RT.validate_input_manifest(dict(manifest, extra=1))

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'site' / 'build_concept_lineage.py')] + list(args),
                              cwd=str(ROOT), capture_output=True, text=True)

    def test_real_builder_cli_reproduces_committed_outputs(self):
        result = self.run_cli('build', '--check', '--catalog-revision', self.pin['catalog_revision']['value'],
                              '--builder-revision', self.pin['builder_revision']['value'],
                              '--supplier-revision', self.pin['supplier_revision']['value'],
                              '--input-revision', self.pin['builder_revision']['value'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"repositories": 335', result.stdout)

    def test_real_pin_check(self):
        result = self.run_cli('pin', '--check', '--projection-revision', self.pin['projection_revision']['value'])
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrong_revisions_are_refused(self):
        bad = '0' * 40
        builder_rev = self.pin['builder_revision']['value']
        result = self.run_cli('build', '--catalog-revision', bad, '--builder-revision', builder_rev,
                              '--supplier-revision', self.pin['supplier_revision']['value'],
                              '--input-revision', builder_rev)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)
        result = self.run_cli('build', '--catalog-revision', self.pin['catalog_revision']['value'],
                              '--builder-revision', builder_rev,
                              '--supplier-revision', builder_rev,
                              '--input-revision', builder_rev)
        self.assertEqual(result.returncode, 2)


class ExistingExportUnchangedTests(unittest.TestCase):
    def test_lineage_files_are_not_catalog_export_inputs(self):
        for name in build_export.INPUTS:
            self.assertNotIn('lineage', name)
            self.assertNotIn('concept-links', name)

    def test_export_pin_keeps_its_shape(self):
        pin = json.loads((ROOT / 'catalog-export-pin.json').read_text(encoding='utf-8'))
        self.assertEqual(set(pin), {'schema_version', 'source_revision', 'inputs_sha256'})
        self.assertEqual(sorted(pin['inputs_sha256']).count('site/build_concept_lineage.py'), 0)


if __name__ == '__main__':
    unittest.main()

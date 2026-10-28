"""Build the read-only concept lineage projection from the public source ledger.

Joins the actual repository source records with the reviewed (currently empty)
concept mappings, validates the whole packet with the pinned portable engine and
writes a separate projection and input manifest. Revisions are explicit
arguments checked against Git blob bytes, never inferred from mutable HEAD.
No network, no source execution, no change to the four-catalog export.

    python site/build_concept_lineage.py build --catalog-revision H --builder-revision H \\
        --supplier-revision H --input-revision H [--write | --check]
    python site/build_concept_lineage.py pin --projection-revision H [--write | --check]
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = 'The-825/staletoast'
LANDSCAPE = 'docs/collaborative-intelligence-repository-landscape.json'
MAPPINGS = 'docs/staletoast-concept-links.json'
RUNTIME = 'site/concept_lineage_runtime.py'
BUILDER = 'site/build_concept_lineage.py'
PROJECTION = 'site/data/concept-lineage.json'
MANIFEST = 'site/data/concept-lineage-input-manifest.json'
PIN = 'concept-lineage-pin.json'
INPUTS = [LANDSCAPE, MAPPINGS, RUNTIME, BUILDER]

# Pinned supplier artifacts: the portable engine copy and its contract.
SUPPLIER_REVISION = '2bb14d63d9a44c2bea38bba8c8fbdcf5e4d08d71'
RUNTIME_SHA256 = '4d81d11cbba06b1c330bc4ead0972becb125d85e727070e1e2c3f232c5122df9'
CONTRACT_SHA256 = 'b4c54fb0af5b4a6388da717afdf5ebd5b9513c348e403d90a39cb841b84b8106'

MAPPING_ARRAYS = ('concepts', 'consumers', 'uses', 'evidence', 'refinements')
HEX40 = re.compile(r'[0-9a-f]{40}')
HEX64 = re.compile(r'[0-9a-f]{64}')


class BuildError(ValueError):
    pass


def load_runtime():
    """Load the vendored engine only if its raw bytes match the pinned digest."""
    data = (ROOT / RUNTIME).read_bytes()
    if hashlib.sha256(data).hexdigest() != RUNTIME_SHA256:
        raise BuildError('runtime bytes differ from the pinned engine digest')
    module = types.ModuleType('concept_lineage_runtime')
    module.__file__ = str(ROOT / RUNTIME)
    exec(compile(data, str(ROOT / RUNTIME), 'exec'), module.__dict__)
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_bytes(*args):
    result = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True)
    if result.returncode != 0:
        raise BuildError('git could not resolve ' + ' '.join(args[-1:]))
    return result.stdout


def revision(value, label, local=True):
    if not HEX40.fullmatch(value or ''):
        raise BuildError(label + ' must be a full lowercase 40 hex commit')
    if local:
        git_bytes('cat-file', '-e', value + '^{commit}')
    return value


def blob(rev, path):
    return git_bytes('show', rev + ':' + path)


def working(path, normalize=False):
    data = (ROOT / path).read_bytes()
    return data.replace(b'\r\n', b'\n') if normalize else data


def tagged_git(value):
    return {'kind': 'git', 'value': value, 'reason': None}


def read_mappings(rt):
    """Exact mapping wrapper and admission, checked by the shared supplier validator."""
    return rt.validate_mapping_document(rt.parse_json_bytes(working(MAPPINGS)), CONTRACT_SHA256)


def source_rows(landscape, catalog_revision):
    rows = []
    for item in landscape['repositories']:
        version = item.get('upstream_revision') or item.get('snapshot_commit')
        if not HEX40.fullmatch(version or ''):
            raise BuildError('source revision is not an exact commit')
        rows.append({
            'id': '%s:repository:%s' % (OWNER, item['id']),
            'owner': OWNER,
            'record_kind': 'repository',
            'record_id': item['id'],
            'title': item['repository'],
            'url': item['url'],
            'upstream_version': tagged_git(version),
            'catalog_revision': tagged_git(catalog_revision),
            'aliases': ['%s:repository:%s' % (OWNER, alias['key']) for alias in item['aliases']],
            'evidence_depth': item['evidence_depth'],
        })
    return rows


def ledger_report(landscape):
    repos = landscape['repositories']
    hosts = {}
    for item in repos:
        host = item['url'].split('/')[2]
        hosts[host] = hosts.get(host, 0) + 1
    return {
        'repositories': len(repos),
        'hosts': hosts,
        'aliases': sum(len(item['aliases']) for item in repos),
        'longest_title': max(len(item['repository']) for item in repos),
        'longest_id': max(len('%s:repository:%s' % (OWNER, item['id'])) for item in repos),
    }


def verify_revisions(catalog_rev, builder_rev, supplier_rev, input_rev):
    if supplier_rev != SUPPLIER_REVISION:
        raise BuildError('supplier revision is not the pinned supplier commit')
    if blob(catalog_rev, LANDSCAPE) != working(LANDSCAPE, True):
        raise BuildError('catalog revision does not contain the working ledger bytes')
    if blob(builder_rev, BUILDER) != working(BUILDER):
        raise BuildError('builder revision does not contain the working builder bytes')
    for path in INPUTS:
        if blob(input_rev, path) != working(path, path == LANDSCAPE):
            raise BuildError('input revision does not contain working bytes for ' + path)


def build_outputs(catalog_rev, builder_rev, supplier_rev, input_rev):
    rt = load_runtime()
    catalog_rev = revision(catalog_rev, 'catalog revision')
    builder_rev = revision(builder_rev, 'builder revision')
    # The supplier commit lives in another repository, so only its shape and the pinned constant are checked.
    supplier_rev = revision(supplier_rev, 'supplier revision', local=False)
    input_rev = revision(input_rev, 'input revision')
    verify_revisions(catalog_rev, builder_rev, supplier_rev, input_rev)
    landscape = json.loads(working(LANDSCAPE, True).decode('utf-8'))
    mappings, admission = read_mappings(rt)
    packet = {'schema_version': rt.SCHEMA, 'data_class': admission['classification'],
              'sources': source_rows(landscape, catalog_rev)}
    packet.update({name: mappings[name] for name in MAPPING_ARRAYS})
    rt.validate_graph(packet)
    inputs = [{'path': path, 'sha256': sha(blob(input_rev, path)), 'revision': tagged_git(input_rev)}
              for path in sorted(INPUTS)]
    manifest = {
        'schema_version': 'concept-lineage-input/1',
        'catalog_revision': tagged_git(catalog_rev),
        'builder_revision': tagged_git(builder_rev),
        'supplier_revision': tagged_git(supplier_rev),
        'contract_sha256': CONTRACT_SHA256,
        'runtime_sha256': RUNTIME_SHA256,
        'builder_sha256': sha(working(BUILDER)),
        'mapping_sha256': admission['packet_sha256'],
        'inputs': inputs,
    }
    manifest_bytes = rt.canonical_bytes(rt.validate_input_manifest(manifest))
    projection = rt.build_projection(packet, sha(manifest_bytes))
    return manifest_bytes, rt.canonical_bytes(projection), ledger_report(landscape)


def command_build(args):
    manifest_bytes, projection_bytes, report = build_outputs(
        args.catalog_revision, args.builder_revision, args.supplier_revision, args.input_revision)
    targets = {MANIFEST: manifest_bytes, PROJECTION: projection_bytes}
    if args.write:
        for path, data in targets.items():
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / path).write_bytes(data)
    if args.check:
        for path, data in targets.items():
            if not (ROOT / path).exists() or (ROOT / path).read_bytes() != data:
                raise BuildError(path + ' differs from a fresh build')
    print(json.dumps(report, sort_keys=True))
    print('manifest_sha256=' + sha(manifest_bytes))
    print('projection_sha256=' + sha(projection_bytes))


def pin_document(projection_rev):
    rt = load_runtime()
    projection_rev = revision(projection_rev, 'projection revision')
    manifest_bytes = working(MANIFEST)
    projection_bytes = working(PROJECTION)
    if blob(projection_rev, MANIFEST) != manifest_bytes or blob(projection_rev, PROJECTION) != projection_bytes:
        raise BuildError('projection revision does not contain the working projection and manifest bytes')
    manifest = rt.validate_input_manifest(rt.parse_json_bytes(manifest_bytes))
    if manifest['runtime_sha256'] != RUNTIME_SHA256 or manifest['contract_sha256'] != CONTRACT_SHA256:
        raise BuildError('manifest pins differ from the supplier pins')
    if manifest['supplier_revision'] != tagged_git(SUPPLIER_REVISION):
        raise BuildError('manifest supplier revision differs')
    pin = {
        'schema_version': 'concept-lineage-pin/1',
        'owner_repository': OWNER,
        'catalog_revision': manifest['catalog_revision'],
        'builder_revision': manifest['builder_revision'],
        'supplier_revision': manifest['supplier_revision'],
        'projection_revision': tagged_git(projection_rev),
        'contract_sha256': CONTRACT_SHA256,
        'runtime_sha256': RUNTIME_SHA256,
        'builder_sha256': manifest['builder_sha256'],
        'mapping_sha256': manifest['mapping_sha256'],
        'input_manifest_sha256': sha(manifest_bytes),
        'projection_sha256': sha(projection_bytes),
    }
    # Exact envelope shapes, canonical bytes and digest bindings, via the shared supplier helper.
    rt.verify_pin_chain(pin, manifest_bytes, projection_bytes)
    return pin


def command_pin(args):
    rt = load_runtime()
    if args.write:
        (ROOT / PIN).write_bytes(rt.canonical_bytes(pin_document(args.projection_revision)))
    if args.check:
        if not (ROOT / PIN).exists():
            raise BuildError('pin file is missing')
        existing = rt.validate_pin(rt.parse_json_bytes((ROOT / PIN).read_bytes()))
        if (ROOT / PIN).read_bytes() != rt.canonical_bytes(pin_document(existing['projection_revision']['value'])):
            raise BuildError('pin differs from the verified projection')
    print('pin ok')


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('build')
    for name in ('catalog', 'builder', 'supplier', 'input'):
        build.add_argument('--%s-revision' % name, required=True)
    pin = sub.add_parser('pin')
    pin.add_argument('--projection-revision', required=True)
    for p in (build, pin):
        p.add_argument('--write', action='store_true')
        p.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        (command_build if args.command == 'build' else command_pin)(args)
    except (BuildError, ValueError, KeyError, OSError) as exc:
        message = exc.code if hasattr(exc, 'code') else str(exc)
        sys.stderr.write('concept lineage build failed: %s\n' % message)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

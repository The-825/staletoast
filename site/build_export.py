"""Publish a revision-bound, evidence-only catalog export for consumers.

Export schema 2.0 is a breaking change from 1.0: directness, horizon and evidenceOrder
are nullable for automated screens, every catalog row carries appraisal_state, and
repositories add the readme-relevance-screened depth. See catalog-contract.json.
Frozen 1.0 exports stay in exports/ unchanged; consumers pinned to 1.0 must fail closed.
"""
import json
import re
import argparse
import shutil
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'site' / 'data'
INPUTS = ['catalog-contract.json', 'docs/collaborative-intelligence-research-ledger.md',
          'docs/collaborative-intelligence-source-appraisals.md',
          'docs/collaborative-intelligence-repository-landscape.json',
          'docs/collaborative-intelligence-claim-register.md',
          'docs/staletoast-appraisal-priorities.json', 'docs/staletoast-chart-history',
          'docs/staletoast-chart-link-corrections.json', 'site/build_catalogs.py',
          'docs/staletoast-expansion-2026-11-01.json', 'docs/staletoast-source-dispositions.json',
          'site/build_priorities.py', 'site/build_discovery.py', 'site/ledger_markdown.py',
          'site/intake_state.py', 'site/build_export.py']
EXPORT_SCHEMA_VERSION = '2.0'


def input_hashes():
    files = []
    for name in INPUTS:
        path = ROOT / name
        files.extend(sorted(path.rglob('*')) if path.is_dir() else [path])
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_text(encoding='utf-8').encode('utf-8')).hexdigest()
            for path in files if path.is_file()}


def catalog_revision():
    pin = json.loads((ROOT / 'catalog-export-pin.json').read_text(encoding='utf-8'))
    if pin['inputs_sha256'] != input_hashes():
        raise ValueError('Catalog inputs changed; freeze a reviewed new export before publishing')
    return pin['source_revision']


def build(freeze=False):
    # Porcelain status also reports untracked inputs, which git diff HEAD ignores.
    if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all', '--'] + INPUTS, cwd=ROOT):
        raise ValueError('Commit catalog inputs before freezing a revision-bound export')
    pin_path = ROOT / 'catalog-export-pin.json'
    if freeze:
        hashes = input_hashes()
        existing = json.loads(pin_path.read_text(encoding='utf-8')) if pin_path.exists() else {}
        if existing.get('inputs_sha256') != hashes:
            revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
            pin_path.write_text(json.dumps({'schema_version': '1.0', 'source_revision': revision,
                                           'inputs_sha256': hashes}, indent=2) + '\n', encoding='utf-8')
    pin = json.loads(pin_path.read_text(encoding='utf-8'))
    if not freeze and pin['inputs_sha256'] != input_hashes():
        publish_pinned(pin['source_revision'])
        return
    revision = catalog_revision()
    payload = {'schema_version': EXPORT_SCHEMA_VERSION, 'canonical_owner': 'The-825/staletoast',
               'authority': 'evidence-only', 'source_revision': revision,
               'catalogs': {name: json.loads((DATA / (name + '.json')).read_text(encoding='utf-8'))
                            for name in ('research', 'repositories', 'claims', 'charts')}}
    text = json.dumps(payload, indent=2, ensure_ascii=False) + '\n'
    archive = ROOT / 'exports' / (revision + '.json')
    if freeze and not archive.exists():
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_text(text, encoding='utf-8')
    if not archive.exists() or archive.read_text(encoding='utf-8') != text:
        raise ValueError('Immutable export is missing or differs; freeze it after committing reviewed inputs')
    publish(text, archive)
    print('export: revision=' + revision)


def publish(text, archive):
    (DATA / 'catalog-export.json').write_text(text, encoding='utf-8')
    target = ROOT / 'site' / 'exports'
    target.mkdir(exist_ok=True)
    for snapshot in archive.parent.glob('*.json'):
        shutil.copyfile(snapshot, target / snapshot.name)


def publish_pinned(revision):
    """Catalog inputs moved past the pin: publish the last frozen export unchanged.

    Record PRs no longer freeze; the weekly edition PR does. Until it lands, consumers
    keep the pinned revision and digest, and the site never invents an unfrozen one.
    """
    archive = ROOT / 'exports' / (revision + '.json')
    if not archive.exists():
        raise ValueError('Pinned export is missing: exports/' + archive.name)
    text = archive.read_text(encoding='utf-8')
    if json.loads(text).get('source_revision') != revision:
        raise ValueError('Pinned export does not carry its own revision: exports/' + archive.name)
    publish(text, archive)
    print('export: revision=' + revision + ' (catalog inputs changed since this freeze; the next weekly edition freezes them)')


def freeze_scope_violation(changes):
    """Return a reason when a PR freezes an export without adding a weekly chart edition.

    changes holds (status, path) pairs from git diff --name-status against the PR base.
    """
    froze = [path for _, path in changes
             if path == 'catalog-export-pin.json' or re.fullmatch(r'exports/[0-9a-f]{40}\.json', path)]
    edition = any(status.startswith('A') and re.fullmatch(r'docs/staletoast-chart-history/\d{4}-\d{2}-\d{2}\.json', path)
                  for status, path in changes)
    if froze and not edition:
        return ('Only a weekly edition PR freezes the catalog export. Drop these changes: ' + ', '.join(sorted(froze)))
    return None


def check_freeze_scope(base):
    output = subprocess.check_output(['git', 'diff', '--name-status', '--no-renames', base + '...HEAD'], cwd=ROOT, text=True)
    changes = [tuple(line.split('\t', 1)) for line in output.splitlines() if line.strip()]
    reason = freeze_scope_violation(changes)
    if reason:
        raise SystemExit(reason)
    print('export freeze scope: ok')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--check-freeze-scope', metavar='BASE_REF')
    args = parser.parse_args()
    if args.check_freeze_scope:
        check_freeze_scope(args.check_freeze_scope)
    else:
        build(args.freeze)

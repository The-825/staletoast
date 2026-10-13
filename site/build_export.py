"""Publish a revision-bound, evidence-only catalog export for consumers."""
import json
import argparse
import shutil
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'site' / 'data'
INPUTS = ['docs/collaborative-intelligence-research-ledger.md',
          'docs/collaborative-intelligence-source-appraisals.md',
          'docs/collaborative-intelligence-repository-landscape.json',
          'docs/collaborative-intelligence-claim-register.md',
          'docs/staletoast-appraisal-priorities.json', 'docs/staletoast-chart-history',
          'docs/staletoast-chart-link-corrections.json', 'site/build_catalogs.py',
          'site/build_priorities.py', 'site/build_discovery.py', 'site/ledger_markdown.py',
          'site/build_export.py']


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
    if subprocess.check_output(['git', 'diff', 'HEAD', '--'] + INPUTS, cwd=ROOT):
        raise ValueError('Commit catalog inputs before freezing a revision-bound export')
    pin_path = ROOT / 'catalog-export-pin.json'
    if freeze:
        hashes = input_hashes()
        existing = json.loads(pin_path.read_text(encoding='utf-8')) if pin_path.exists() else {}
        if existing.get('inputs_sha256') != hashes:
            revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
            pin_path.write_text(json.dumps({'schema_version': '1.0', 'source_revision': revision,
                                           'inputs_sha256': hashes}, indent=2) + '\n', encoding='utf-8')
    revision = catalog_revision()
    payload = {'schema_version': '1.0', 'canonical_owner': 'The-825/staletoast',
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
    (DATA / 'catalog-export.json').write_text(text, encoding='utf-8')
    target = ROOT / 'site' / 'exports'
    target.mkdir(exist_ok=True)
    for snapshot in archive.parent.glob('*.json'):
        shutil.copyfile(snapshot, target / snapshot.name)
    print('export: revision=' + revision)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    build(parser.parse_args().freeze)

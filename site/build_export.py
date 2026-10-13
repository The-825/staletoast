"""Publish a revision-bound, evidence-only catalog export for consumers."""
import json
import argparse
import shutil
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


def catalog_revision():
    return subprocess.check_output(['git', 'log', '-1', '--format=%H', 'HEAD', '--'] + INPUTS,
                                   cwd=ROOT, text=True).strip()


def build(freeze=False):
    if subprocess.check_output(['git', 'diff', 'HEAD', '--'] + INPUTS, cwd=ROOT):
        raise ValueError('Commit catalog inputs before freezing a revision-bound export')
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

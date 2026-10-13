"""Publish a revision-bound, evidence-only catalog export for consumers."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'site' / 'data'


def build():
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    payload = {'schema_version': '1.0', 'canonical_owner': 'The-825/staletoast',
               'authority': 'evidence-only', 'source_revision': revision,
               'catalogs': {name: json.loads((DATA / (name + '.json')).read_text(encoding='utf-8'))
                            for name in ('research', 'repositories', 'claims', 'charts')}}
    (DATA / 'catalog-export.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('export: revision=' + revision)


if __name__ == '__main__':
    build()

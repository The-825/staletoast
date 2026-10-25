"""Build a visitor guide from existing findings without changing source ranks."""
import argparse
import hashlib
import json
import subprocess
import re
from datetime import date
from pathlib import Path

from build_catalogs import research_catalog, repository_catalog

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'docs/staletoast-reader-selections.json'
OUTPUT = ROOT / 'site/data/reader-guide.json'
INPUTS = ['docs/staletoast-reader-selections.json',
          'docs/collaborative-intelligence-research-ledger.md',
          'docs/collaborative-intelligence-source-appraisals.md',
          'docs/collaborative-intelligence-repository-landscape.json',
          'site/build_reader_guide.py', 'site/build_catalogs.py',
          'site/build_priorities.py', 'site/ledger_markdown.py']


def required_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be nonempty text')
    return value.strip()


def build(config, research, repositories):
    if config.get('schema_version') != 1:
        raise ValueError('unsupported reader selection schema')
    date.fromisoformat(required_text(config.get('date'), 'date'))
    required_text(config.get('status'), 'status')
    if not isinstance(config.get('collections'), list) or not config['collections']:
        raise ValueError('collections must be a nonempty list')
    indexes = {'research': {}, 'repository': {}}
    for kind, rows in [('research', research), ('repository', repositories)]:
        for row in rows:
            if row['id'] in indexes[kind]:
                raise ValueError(f"duplicate {kind} identity: {row['id']}")
            indexes[kind][row['id']] = row
    collections, collection_ids = [], set()
    for group in config['collections']:
        for key in ['id', 'title', 'description']:
            required_text(group.get(key), key)
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', group['id']):
            raise ValueError('invalid collection identity')
        if not isinstance(group.get('selections'), list) or not group['selections']:
            raise ValueError('selections must be a nonempty list')
        if group['id'] in collection_ids:
            raise ValueError('duplicate collection identity')
        collection_ids.add(group['id'])
        cards, selected = [], set()
        for item in group['selections']:
            reason = required_text(item.get('why_selected'), 'why_selected')
            identity = (item['kind'], item['id'])
            if identity in selected:
                raise ValueError('duplicate selection within collection')
            selected.add(identity)
            if item['kind'] not in indexes or item['id'] not in indexes[item['kind']]:
                raise ValueError(f'unknown source: {identity}')
            row = indexes[item['kind']][item['id']]
            paper = item['kind'] == 'research'
            if paper and row['record_state'] != 'reviewed-catalog':
                raise ValueError('unpromoted research cannot become a visitor selection')
            if not paper and row['evidence_depth'] != 'readme-screened':
                raise ValueError('identity-only repository cannot become a visitor selection')
            takeaway = row['finding'] if paper else required_text(item.get('takeaway'), 'takeaway')
            limits = row['boundary'] if paper else required_text(item.get('limits'), 'limits')
            if not paper and takeaway == limits:
                raise ValueError('repository takeaway and limits must be distinct')
            cards.append(dict(kind=item['kind'], id=item['id'],
                              title=row['title'] if paper else row['repository'],
                              source_url=row['url'], why_selected=reason,
                              evidence_depth=row['review_depth'] if paper else row['evidence_depth'],
                              takeaway=takeaway, limits=limits,
                              original_evidence_note=None if paper else row['evidence_note'],
                              counterevidence=None if paper else row.get('counterevidence', []),
                              profile_slug=f"{'research' if paper else 'repositories'}-{item['id'].lower()}"))
        collections.append(dict(id=group['id'], title=group['title'],
                                description=group['description'], selections=cards))
    return dict(schema_version=1, date=config['date'], status=config['status'],
                ordering='Editorial reading paths, not a quality score or internal review priority',
                evidence_boundary='Selected from existing appraisals; no new reproduction or adoption claim',
                collections=collections)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--freeze', action='store_true')
    args = parser.parse_args()
    payload = build(json.loads(CONFIG.read_text(encoding='utf-8')),
                    research_catalog(), repository_catalog())
    if subprocess.check_output(['git', 'diff', 'HEAD', '--'] + INPUTS, cwd=ROOT):
        raise SystemExit('Commit reviewed guide inputs before building a revision-bound guide')
    revision = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--'] + INPUTS,
                                       cwd=ROOT, text=True).strip()
    payload['source_revision'] = revision
    sources = [ROOT / name for name in INPUTS]
    payload['source_hashes'] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(
        p.read_text(encoding='utf-8').replace('\r\n', '\n').encode()).hexdigest() for p in sources}
    text = json.dumps(payload, indent=2, ensure_ascii=False) + '\n'
    if args.freeze:
        frozen = ROOT / 'exports/reader-guide' / f'{revision}.json'
        if frozen.exists() and frozen.read_text(encoding='utf-8') != text:
            raise SystemExit('Refusing to overwrite a frozen reader guide')
        frozen.parent.mkdir(parents=True, exist_ok=True)
        frozen.write_text(text, encoding='utf-8')
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != text:
            raise SystemExit('Reader guide is stale; rebuild before use')
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(text, encoding='utf-8')
    print(f"reader guide: {len(payload['collections'])} collections")


if __name__ == '__main__':
    main()

"""Build a visitor guide from existing findings without changing source ranks."""
import argparse
import hashlib
import json
from pathlib import Path

from build_catalogs import research_catalog, repository_catalog

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'docs/staletoast-reader-selections.json'
OUTPUT = ROOT / 'site/data/reader-guide.json'


def build(config, research, repositories):
    indexes = {'research': {}, 'repository': {}}
    for kind, rows in [('research', research), ('repository', repositories)]:
        for row in rows:
            if row['id'] in indexes[kind]:
                raise ValueError(f"duplicate {kind} identity: {row['id']}")
            indexes[kind][row['id']] = row
    collections, collection_ids = [], set()
    for group in config['collections']:
        if group['id'] in collection_ids:
            raise ValueError('duplicate collection identity')
        collection_ids.add(group['id'])
        cards, selected = [], set()
        for item in group['selections']:
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
            cards.append(dict(kind=item['kind'], id=item['id'],
                              title=row['title'] if paper else row['repository'],
                              source_url=row['url'], why_selected=item['why_selected'],
                              evidence_depth=row['review_depth'] if paper else row['evidence_depth'],
                              takeaway=row['finding'] if paper else row['evidence_note'],
                              limits=row['boundary'] if paper else row['evidence_note'],
                              counterevidence=[] if paper else row.get('counterevidence', []),
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
    args = parser.parse_args()
    payload = build(json.loads(CONFIG.read_text(encoding='utf-8')),
                    research_catalog(), repository_catalog())
    sources = [CONFIG, ROOT / 'docs/collaborative-intelligence-research-ledger.md',
               ROOT / 'docs/collaborative-intelligence-source-appraisals.md',
               ROOT / 'docs/collaborative-intelligence-repository-landscape.json']
    payload['source_hashes'] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(
        p.read_text(encoding='utf-8').replace('\r\n', '\n').encode()).hexdigest() for p in sources}
    text = json.dumps(payload, indent=2, ensure_ascii=False) + '\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != text:
            raise SystemExit('Reader guide is stale; rebuild before use')
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(text, encoding='utf-8')
    print(f"reader guide: {len(payload['collections'])} collections")


if __name__ == '__main__':
    main()

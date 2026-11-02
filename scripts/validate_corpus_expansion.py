"""Check the bounded November 1 intake against its immutable source baseline."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'site'))
from build_priorities import identified_rows
from ledger_markdown import source_link
from repository_landscape import validate as validate_landscape

BASE = '3eba46393e5f85d1957d37c40ee1fa5b59d37f86'

def base_bytes(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)

def source_rows(text):
    return identified_rows(text.split('## Source ledger', 1)[1].split('### Entry metadata', 1)[0], {6, 7})

def paper_key(url):
    return re.sub(r'v\d+$', '', url.casefold().rstrip('/'))

def check():
    docs = ROOT / 'docs'
    batch = json.loads((docs / 'staletoast-expansion-2026-11-01.json').read_text(encoding='utf-8'))
    landscape = json.loads((docs / 'collaborative-intelligence-repository-landscape.json').read_text(encoding='utf-8'))
    old_landscape = json.loads(base_bytes('docs/collaborative-intelligence-repository-landscape.json'))
    papers = source_rows((docs / 'collaborative-intelligence-research-ledger.md').read_text(encoding='utf-8'))
    old_papers = source_rows(base_bytes('docs/collaborative-intelligence-research-ledger.md').decode('utf-8'))
    apps = identified_rows((docs / 'collaborative-intelligence-source-appraisals.md').read_text(encoding='utf-8'), {7, 8})
    old_apps = identified_rows(base_bytes('docs/collaborative-intelligence-source-appraisals.md').decode('utf-8'), {7, 8})
    errors = validate_landscape(landscape)
    if len(papers) != 500 or len(landscape['repositories']) != 1000:
        errors.append('target source counts do not match')
    if set(papers) != set(apps):
        errors.append('paper and appraisal identities differ')
    if any(papers.get(key) != value for key, value in old_papers.items()) or any(apps.get(key) != value for key, value in old_apps.items()):
        errors.append('historical research record changed')
    if landscape['repositories'][:len(old_landscape['repositories'])] != old_landscape['repositories']:
        errors.append('historical repository record changed')
    urls = [paper_key(source_link(row[1])[1]) for row in papers.values()]
    if len(urls) != len(set(urls)):
        errors.append('duplicate research identity, including arXiv versions')
    titles = [re.sub('[^a-z0-9]', '', source_link(row[1])[0].casefold()) for row in papers.values()]
    if len(titles) != len(set(titles)):
        errors.append('duplicate normalized research title')
    records = {row['id']: row for row in landscape['repositories']}
    if len(batch['research']) != 377 or len(batch['repositories']) != 665:
        errors.append('batch counts do not match')
    for row in batch['research']:
        identity = row['id']
        if identity not in papers or row['url'] != source_link(papers[identity][1])[1]:
            errors.append(identity + ': primary paper identity mismatch')
        if not re.fullmatch(r'https://arxiv\.org/abs/\d{4}\.\d{4,5}v\d+', row['url']):
            errors.append(identity + ': unversioned paper')
        if row['claims'] or row['full_text_appraised'] or row['screen_method'] != 'automated-abstract-topic-screen-v1':
            errors.append(identity + ': overstated paper evidence')
        if apps[identity][6].strip() or not apps[identity][5].startswith('abstract-only: automated relevance screen'):
            errors.append(identity + ': appraisal gained a claim or lost screening limit')
    for row in batch['repositories']:
        record = records.get(row['id'], {})
        if record.get('upstream_revision') != row['snapshot_commit'] or record.get('readme_blob_sha') != row['readme_blob_sha']:
            errors.append(row['id'] + ': repository source binding mismatch')
        if record.get('readme_content_sha256') != row['readme_sha256'] or row['mechanism_appraisal'] or row['license_text_inspected']:
            errors.append(row['id'] + ': overstated repository evidence')
    pool = json.loads((docs / 'staletoast-next-round-pool.json').read_text(encoding='utf-8'))
    pool_ids = {row['pool_id'] for row in pool['records']}
    if len(pool_ids) != len(pool['records']):
        errors.append('duplicate pool IDs')
    links = batch['pool_links']
    if len(links) != 1042 or len({row['id'] for row in links}) != 1042 or any(row['pool_id'] not in pool_ids or row['selected_for_hot100'] for row in links):
        errors.append('unselected source pool coverage is incomplete')
    for name in ('staletoast-chart-history',):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, 'docs/' + name], cwd=ROOT, text=True).splitlines()
        for path in paths:
            if hashlib.sha256((ROOT / path).read_text(encoding='utf-8').encode('utf-8')).digest() != hashlib.sha256(base_bytes(path)).digest():
                errors.append('historical chart bytes changed: ' + path)
    return errors

if __name__ == '__main__':
    findings = check()
    for finding in findings:
        print('corpus expansion: ' + finding)
    print('corpus expansion: ' + ('FAILED' if findings else 'research=500 repositories=1000; original records and chart bytes preserved'))
    raise SystemExit(bool(findings))

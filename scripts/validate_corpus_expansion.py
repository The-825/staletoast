"""Check the bounded November 1 intake against its immutable source baseline.

Original 123 research and 335 repository rows are preserved byte-for-byte as a prefix.
Later growth and retained rejected intake are allowed; targets come from the manifest.
"""
import difflib
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'site'))
from build_priorities import identified_rows
from intake_state import IntakeState, SCREEN_METHODS
from ledger_markdown import source_link
from repository_landscape import validate as validate_landscape

BASE = '3eba46393e5f85d1957d37c40ee1fa5b59d37f86'
ISO_DATE = re.compile(r'\d{4}-\d{2}-\d{2}')

def base_bytes(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)

def source_rows(text):
    return identified_rows(text.split('## Source ledger', 1)[1].split('### Entry metadata', 1)[0], {6, 7})

def paper_key(url):
    return re.sub(r'v\d+$', '', url.casefold().rstrip('/'))

def normalized_title(title):
    return re.sub('[^a-z0-9]', '', title.casefold())

def valid_date(value, latest=None):
    if not isinstance(value, str) or not ISO_DATE.fullmatch(value):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return latest is None or parsed <= date.fromisoformat(latest)

def near_duplicate_titles(titles, threshold=0.9):
    """Advisory pairs for human reconciliation; never a failure."""
    pairs = []
    items = sorted(titles.items())
    for index, (first_id, first) in enumerate(items):
        for second_id, second in items[index + 1:]:
            matcher = difflib.SequenceMatcher(None, first, second)
            if matcher.real_quick_ratio() >= threshold and matcher.quick_ratio() >= threshold and matcher.ratio() >= threshold:
                pairs.append((first_id, second_id))
    return pairs

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
    try:
        state = IntakeState(docs)
    except ValueError as exc:
        # Dispositions are fail-closed: nothing else can be trusted without them.
        return errors + [str(exc)]
    records = {row['id']: row for row in landscape['repositories']}
    batch_date = batch.get('batch_date', '')
    if not valid_date(batch_date):
        errors.append('batch date is invalid')
        batch_date = None

    # Targets come from the manifest, not permanent exact totals.
    history, added, totals = batch['historical_records_preserved'], batch['added'], batch['totals']
    if history != {'research': len(old_papers), 'repositories': len(old_landscape['repositories'])}:
        errors.append('manifest historical counts do not match the immutable baseline')
    if any(history[kind] + added[kind] != totals[kind] for kind in ('research', 'repositories')):
        errors.append('manifest history plus additions does not equal its totals')
    if len(batch['research']) < added['research'] or len(batch['repositories']) < added['repositories']:
        errors.append('batch lost records; rejected intake must be retained')
    held_research, held_repositories = state.held_ids('research'), state.held_ids('repository')
    active_papers = [key for key in papers if key not in held_research]
    active_repositories = [key for key in records if key not in held_repositories]
    if len(active_papers) < totals['research'] or len(active_repositories) < totals['repositories']:
        errors.append('active collection is below the manifest target')
    if set(papers) != set(apps):
        errors.append('paper and appraisal identities differ')
    if any(papers.get(key) != value for key, value in old_papers.items()) or any(apps.get(key) != value for key, value in old_apps.items()):
        errors.append('historical research record changed')
    if landscape['repositories'][:len(old_landscape['repositories'])] != old_landscape['repositories']:
        errors.append('historical repository record changed')
    if state.held_ids('research') & set(old_papers) or state.held_ids('repository') & {row['id'] for row in old_landscape['repositories']}:
        errors.append('a historical record cannot be held')

    # Duplicate checks cover active records only; held duplicates are retained history.
    urls = [paper_key(source_link(papers[key][1])[1]) for key in active_papers]
    if len(urls) != len(set(urls)):
        errors.append('duplicate research identity, including arXiv versions')
    titles = {key: normalized_title(source_link(papers[key][1])[0]) for key in active_papers}
    if len(titles.values()) != len(set(titles.values())):
        errors.append('duplicate normalized research title')

    batch_ids = {row['id'] for row in batch['research']} | {row['id'] for row in batch['repositories']}
    if len(batch_ids) != len(batch['research']) + len(batch['repositories']):
        errors.append('batch IDs are not unique')
    database_ids = [row.get('github_database_id') for row in batch['repositories']]
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in database_ids) or len(database_ids) != len(set(database_ids)):
        errors.append('batch repositories need unique numeric GitHub database IDs')
    for row in batch['research']:
        identity = row['id']
        if identity in old_papers or identity not in papers or row['url'] != source_link(papers[identity][1])[1]:
            errors.append(identity + ': primary paper identity mismatch')
        if not re.fullmatch(r'https://arxiv\.org/abs/\d{4}\.\d{4,5}v\d+', row['url']):
            errors.append(identity + ': unversioned paper')
        if row['claims'] or row['full_text_appraised'] or row['screen_method'] != SCREEN_METHODS['research']:
            errors.append(identity + ': overstated paper evidence')
        if not valid_date(row.get('observed_date'), batch_date):
            errors.append(identity + ': observation date is missing or invalid')
        app = apps.get(identity)
        if app is None or app[6].strip() or not app[5].startswith('abstract-only: automated relevance screen'):
            errors.append(identity + ': appraisal gained a claim or lost screening limit')
    for row in batch['repositories']:
        identity = row['id']
        record = records.get(identity, {})
        if identity in {old['id'] for old in old_landscape['repositories']} or not record:
            errors.append(identity + ': repository identity is not new intake in the landscape')
        if record.get('upstream_revision') != row['snapshot_commit'] or record.get('readme_blob_sha') != row['readme_blob_sha']:
            errors.append(identity + ': repository source binding mismatch')
        if record.get('repository') != row['repository'] or record.get('url') != row['url']:
            errors.append(identity + ': repository identity binding mismatch')
        if record.get('readme_content_sha256') != row['readme_sha256'] or row['mechanism_appraisal'] or row['license_text_inspected']:
            errors.append(identity + ': overstated repository evidence')
        if row['claims'] or row['screen_method'] != SCREEN_METHODS['repository'] or record.get('evidence_depth') != 'readme-relevance-screened':
            errors.append(identity + ': repository carries findings or an unknown screen')
        if not valid_date(row.get('observed_date'), batch_date):
            errors.append(identity + ': observation date is missing or invalid')
        if record.get('stars_observed') is not None and not valid_date(record.get('popularity_observed_date')):
            errors.append(identity + ': landscape row lacks its own popularity observation date')

    # Held dispositions and replacements must refer to retained batch records.
    for identity, disposition in state.held.items():
        replacement = disposition.get('replacement_id')
        if replacement and replacement in state.held:
            errors.append(identity + ': replacement is itself held')

    pool = json.loads((docs / 'staletoast-next-round-pool.json').read_text(encoding='utf-8'))
    pool_ids = {row['pool_id'] for row in pool['records']}
    if len(pool_ids) != len(pool['records']):
        errors.append('duplicate pool IDs')
    links = batch['pool_links']
    link_ids = [row['id'] for row in links]
    if len(link_ids) != len(set(link_ids)) or not batch_ids <= set(link_ids) or any(row['pool_id'] not in pool_ids or row['selected_for_hot100'] for row in links):
        errors.append('unselected source pool coverage is incomplete')
    for name in ('staletoast-chart-history',):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, 'docs/' + name], cwd=ROOT, text=True).splitlines()
        for path in paths:
            if hashlib.sha256((ROOT / path).read_text(encoding='utf-8').encode('utf-8')).digest() != hashlib.sha256(base_bytes(path)).digest():
                errors.append('historical chart bytes changed: ' + path)
    check.summary = (len(active_papers), len(active_repositories), len(held_research) + len(held_repositories),
                     near_duplicate_titles(titles))
    return errors

if __name__ == '__main__':
    findings = check()
    for finding in findings:
        print('corpus expansion: ' + finding)
    research, repositories, held, near = getattr(check, 'summary', (0, 0, 0, []))
    for first, second in near[:20]:
        print(f'corpus expansion: review near-duplicate titles {first} and {second} (advisory)')
    print('corpus expansion: ' + ('FAILED' if findings else f'active research={research} repositories={repositories} held={held}; original records and chart bytes preserved'))
    raise SystemExit(bool(findings))

"""Validate the collaborative intelligence scope map and render its reader view."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / 'docs'
SOURCE = DOCS / 'staletoast-scope-map.json'
VIEW = DOCS / 'staletoast-scope-map.md'
CLAIMS = DOCS / 'collaborative-intelligence-claim-register.md'
STATUSES = ('established', 'added-unscreened')
COMPONENT_ID = re.compile(r'[a-z]+(?:-[a-z]+)+')
PROPOSAL_FIELDS = ('research_topics', 'repository_queries', 'prior_coverage', 'boundary')


def claim_ids(text):
    return set(re.findall(r'^### (CI-\d{3}):', text, flags=re.M))


def validate(scope, baseline, known_claims):
    """Raise ValueError unless the scope map agrees with its baseline artifact and the claim register."""
    if set(scope['statuses']) != set(STATUSES):
        raise ValueError('statuses must describe exactly: ' + ', '.join(STATUSES))
    components = scope['components']
    ids = [item['id'] for item in components]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate component id')
    routed = {item['id']: item for item in baseline['baseline_capabilities']}
    for item in components:
        cid = item['id']
        if not COMPONENT_ID.fullmatch(cid):
            raise ValueError(f'malformed component id: {cid}')
        if item['status'] not in STATUSES:
            raise ValueError(f'unknown status for {cid}')
        for field in ('label', 'definition', 'comparison_question', 'since'):
            if not str(item.get(field, '')).strip():
                raise ValueError(f'{cid} is missing {field}')
        if not item['screen_terms'] or len(set(item['screen_terms'])) != len(item['screen_terms']):
            raise ValueError(f'{cid} needs distinct screen terms')
        unknown = set(item['related_claims']) - known_claims
        if unknown:
            raise ValueError(f'{cid} names unknown claims: {sorted(unknown)}')
        if item['status'] == 'established':
            source = routed.get(cid)
            if source is None:
                raise ValueError(f'{cid} is established but absent from the baseline artifact')
            if item['screen_terms'] != source['terms'] or item['comparison_question'] != source['question']:
                raise ValueError(f'{cid} drifted from the baseline artifact')
            if any(field in item for field in PROPOSAL_FIELDS):
                raise ValueError(f'{cid} is established and cannot carry unrun proposals')
        else:
            if cid in routed:
                raise ValueError(f'{cid} is already routed in the baseline artifact')
            for field in PROPOSAL_FIELDS:
                if not item.get(field):
                    raise ValueError(f'{cid} is missing {field}')
    missing = set(routed) - set(ids)
    if missing:
        raise ValueError(f'baseline components missing from the scope map: {sorted(missing)}')
    for term, targets in scope['owner_scope_terms'].items():
        if not targets or set(targets) - set(ids):
            raise ValueError(f'scope term {term!r} must map to known components')


def render(scope):
    lines = [
        '# Collaborative intelligence scope map',
        '',
        f"Effective {scope['effective_date']}. Generated from "
        '[the machine-readable map](staletoast-scope-map.json) by `python site/build_scope_map.py`. '
        'Edit the JSON, not this file.',
        '',
        scope['purpose'],
        '',
        f"**Authority:** {scope['authority']}",
        '',
        f"**Owner instruction, {scope['owner_instruction']['date']}:** {scope['owner_instruction']['summary']}",
        '',
        '## Status',
        '',
    ]
    lines += [f'- `{name}`: {meaning}' for name, meaning in scope['statuses'].items()]
    lines += ['', '## Rules', '']
    lines += [f'{number}. {rule}' for number, rule in enumerate(scope['rules'], 1)]
    lines += ['', '## Components', '',
              '| Component | Status | Since | What it covers | Comparison question |',
              '|---|---|---|---|---|']
    for item in scope['components']:
        lines.append(f"| `{item['id']}` | {item['status']} | {item['since']} | "
                     f"{item['definition']} | {item['comparison_question']} |")
    lines += ['', '## Where a scope term goes', '', '| Term | Components |', '|---|---|']
    for term, targets in scope['owner_scope_terms'].items():
        lines.append(f"| {term} | {', '.join(f'`{target}`' for target in targets)} |")
    lines += ['', '## Added components', '',
              'Nothing below has been run. Terms and queries are proposals for the first screen.']
    for item in scope['components']:
        if item['status'] != 'added-unscreened':
            continue
        lines += ['', f"### {item['label']} (`{item['id']}`)", '',
                  f"**Boundary:** {item['boundary']}", '',
                  f"**Prior coverage:** {item['prior_coverage']}", '',
                  '**Screen terms:** ' + ', '.join(f'`{term}`' for term in item['screen_terms']), '',
                  '**Related claims:** ' + ', '.join(item['related_claims'])
                  + f". {scope['related_claims_meaning']}", '',
                  '**Proposed research topics:**', '']
        lines += [f"- `{topic['topic']}`: all of {', '.join(topic['all_terms'])}" for topic in item['research_topics']]
        lines += ['', '**Proposed repository queries:**', '']
        lines += [f"- `{query['category']}`: `{query['query']}`" for query in item['repository_queries']]
    return '\n'.join(lines) + '\n'


def load():
    scope = json.loads(SOURCE.read_text(encoding='utf-8'))
    baseline = json.loads((DOCS.parent / scope['baseline_artifact']).read_text(encoding='utf-8'))
    validate(scope, baseline, claim_ids(CLAIMS.read_text(encoding='utf-8')))
    return scope


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    view = render(load())
    if args.check:
        if not VIEW.exists() or VIEW.read_text(encoding='utf-8') != view:
            raise SystemExit('docs/staletoast-scope-map.md is stale; run python site/build_scope_map.py')
        return
    VIEW.write_text(view, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()

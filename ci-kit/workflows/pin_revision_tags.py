"""Keep every pinned source revision reachable through a permanent tag.

Python 3 standard library only. Frozen exports bind to the commit they were
frozen on. That commit is a PR-branch commit, and a squash merge leaves it off
main, so it stays fetchable only while its feature branch exists. This creates
frozen/<revision> tags so a pin survives branch cleanup. It only ever adds a
tag for a revision already recorded in the repository; it never moves or
deletes one.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
TAG_PREFIX = 'frozen/'
REVISION = re.compile(r'[0-9a-f]{40}')


def pinned_revisions(root=ROOT):
    """Every revision a consumer can pin: frozen exports, frozen guides, the current pin."""
    found = {path.stem for folder in ('exports', 'exports/reader-guide')
             for path in (root / folder).glob('*.json')}
    pin = root / 'catalog-export-pin.json'
    if pin.exists():
        found.add(json.loads(pin.read_text(encoding='utf-8'))['source_revision'])
    invalid = sorted(value for value in found if not isinstance(value, str) or not REVISION.fullmatch(value))
    if invalid:
        raise ValueError(f'pinned revision is not a full commit SHA: {invalid}')
    return sorted(found)


def ensure_tags(revisions, api, write=True):
    """api(method, suffix, body) returns (status, json). Returns {revision: outcome}."""
    def existing(revision):
        status, body = api('GET', f'git/ref/tags/{TAG_PREFIX}{revision}', None)
        if status == 404:
            return False
        target = body.get('object', {}) if status == 200 and isinstance(body, dict) else {}
        if target.get('sha') != revision or target.get('type') != 'commit':
            raise ValueError(f'{TAG_PREFIX}{revision} exists but does not point at its revision')
        return True

    outcome = {}
    for revision in revisions:
        if existing(revision):
            outcome[revision] = 'present'
        elif not write:
            outcome[revision] = 'missing'
        else:
            status, _ = api('POST', 'git/refs', {'ref': f'refs/tags/{TAG_PREFIX}{revision}', 'sha': revision})
            # 422 also covers a concurrent run that created the same tag; confirm by reading it back.
            if status != 201 and not (status == 422 and existing(revision)):
                raise ValueError(f'could not tag {revision}: HTTP {status}')
            outcome[revision] = 'created'
    return outcome


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='report missing tags and fail; create nothing')
    args = parser.parse_args()
    repository = os.environ['GITHUB_REPOSITORY']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('invalid repository identity')
    token = os.environ['GH_TOKEN']

    def api(method, suffix, body):
        request = Request(f'https://api.github.com/repos/{repository}/{suffix}', method=method,
                          data=None if body is None else json.dumps(body).encode('utf-8'), headers={
                              'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json',
                              'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'pin-revision-tags'})
        try:
            with urlopen(request, timeout=30) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            if error.code in (404, 422):
                return error.code, None
            raise

    outcome = ensure_tags(pinned_revisions(), api, write=not args.check)
    for revision, state in outcome.items():
        print(f'{state}: {TAG_PREFIX}{revision}')
    if 'missing' in outcome.values():
        raise SystemExit('pinned revisions without a permanent tag')


if __name__ == '__main__':
    main()

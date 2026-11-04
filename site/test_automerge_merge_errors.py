"""Exercise the auto-merge merge-error reconciliation with mocked GitHub state.

Public and synthetic only. The workflow script runs under node with a fake
github client, an instant injected timer and no network.
"""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/automerge.yml'

HARNESS = r"""
const fs = require('fs');
const lines = fs.readFileSync(process.argv[1], 'utf8').split(/\r?\n/);
const start = lines.findIndex(line => line.trim() === 'script: |');
if (start < 0) throw new Error('No github-script block');
const body = [];
for (const line of lines.slice(start + 1)) {
  if (line.trim() && !line.startsWith('            ')) break;
  body.push(line.slice(12));
}
const run = new Function('github', 'context', 'core', 'require',
  'return (async () => {\n' + body.join('\n') + '\n})()');

const T = (s) => `2026-11-02T10:00:${String(s).padStart(2, '0')}Z`;
const SAME = 'sha-checked';
const repo = { full_name: 'The-825/staletoast' };
const prState = (sha, extra = {}) => ({ head: { ref: 'claude/example', sha, repo }, ...extra });
const OPEN = prState(SAME);
const MERGED = prState(SAME, { merged: true, state: 'closed', merge_commit_sha: 'sha-merge' });
const IN_PROGRESS = 'Merge already in progress';

async function scenario(status, message, afterMerge, moveHead = false) {
  let currentHead = SAME;
  let mergeCalls = 0;
  let mergeTried = false;
  let postGets = 0;
  let warnings = 0;
  const sleeps = [];
  const pr = { number: 7, draft: false, state: 'open', base: { ref: 'main', repo },
    head: { ref: 'claude/example', sha: SAME, repo }, labels: [{ name: 'greenlight' }] };
  const github = {
    paginate: async (fn) => {
      if (fn === 'runs') return [{ head_sha: SAME, event: 'pull_request',
        pull_requests: [{ number: 7 }], created_at: T(10) }];
      return [{ event: 'labeled', label: { name: 'greenlight' }, created_at: T(20) }];
    },
    rest: {
      actions: { listWorkflowRunsForRepo: 'runs' },
      issues: { listEventsForTimeline: 'timeline' },
      pulls: {
        get: async () => {
          const extra = mergeTried && afterMerge
            ? afterMerge[Math.min(postGets++, afterMerge.length - 1)] : {};
          return { data: { ...pr, head: { ...pr.head, sha: currentHead }, ...extra } };
        },
        merge: async ({ sha }) => {
          mergeCalls += 1;
          mergeTried = true;
          if (status) throw Object.assign(new Error(message || 'merge failed'), { status });
          if (sha !== currentHead) throw Object.assign(new Error('head changed'), { status: 409 });
        },
      },
      checks: { listForRef: async ({ check_name }) => {
        if (moveHead) currentHead = 'sha-new';
        return { data: { check_runs: [{ id: 1, name: check_name,
          status: 'completed', conclusion: 'success' }] } };
      } },
    },
  };
  const context = { repo: { owner: 'The-825', repo: 'staletoast' },
    eventName: 'pull_request_target', payload: { pull_request: { number: 7 } } };
  const runtimeRequire = name => {
    // Injected instant delay: records requested waits, never really waits.
    if (name === 'timers/promises') return { setTimeout: async (ms) => { sleeps.push(ms); } };
    return require(name);
  };
  try {
    await run(github, context, { info: () => {}, warning: () => { warnings += 1; } },
      runtimeRequire);
  } catch (e) {
    e.mergeCalls = mergeCalls;
    e.sleeps = sleeps;
    throw e;
  }
  return { mergeCalls, sleeps, warnings };
}

async function outcome(...args) {
  try {
    return { ok: true, result: await scenario(...args) };
  } catch (e) {
    return { ok: false, status: e.status, error: e };
  }
}

const expectOk = (name, o, sleeps, warnings = 0) => {
  if (!o.ok) throw new Error(`${name}: expected success, got ${o.error}`);
  if (o.result.mergeCalls !== 1) throw new Error(`${name}: merge was retried`);
  if (o.result.sleeps.length !== sleeps) throw new Error(`${name}: sleeps ${o.result.sleeps.length}`);
  if (o.result.warnings !== warnings) throw new Error(`${name}: warnings ${o.result.warnings}`);
};
const expectFail = (name, o, status, sleeps) => {
  if (o.ok || o.status !== status) throw new Error(`${name}: expected rethrown ${status}`);
  if (o.error.mergeCalls !== 1) throw new Error(`${name}: merge was retried`);
  if (o.error.sleeps.length !== sleeps)
    throw new Error(`${name}: expected ${sleeps} waits, got ${o.error.sleeps.length}`);
  if (!o.error.sleeps.every(ms => ms === 3000)) throw new Error(`${name}: unexpected delay`);
};

(async () => {
  const clean = await scenario(null);
  if (clean.mergeCalls !== 1) throw new Error('clean merge did not call merge once');

  expectOk('405 already merged same head', await outcome(405, IN_PROGRESS, [MERGED]), 0);
  expectOk('409 already merged same head', await outcome(409, 'conflict', [MERGED]), 0);
  expectOk('transient open to confirmed', await outcome(405, IN_PROGRESS, [OPEN, OPEN, MERGED]), 2);
  expectFail('unresolved', await outcome(405, IN_PROGRESS, [OPEN]), 405, 5);

  const noCommit = (sha) => prState(sha, { merged: true, state: 'closed', merge_commit_sha: '' });
  expectFail('merged without merge commit', await outcome(405, IN_PROGRESS, [noCommit(SAME)]), 405, 0);
  const otherMerged = prState('sha-other', { merged: true, state: 'closed', merge_commit_sha: 'sha-merge' });
  const closed = prState(SAME, { merged: false, state: 'closed', merge_commit_sha: null });
  expectFail('405 different-head merge', await outcome(405, IN_PROGRESS, [otherMerged]), 405, 0);
  expectFail('409 different-head merge', await outcome(409, 'conflict', [otherMerged]), 409, 0);
  expectFail('405 closed unmerged', await outcome(405, IN_PROGRESS, [closed]), 405, 0);
  expectFail('409 closed unmerged', await outcome(409, 'conflict', [closed]), 409, 0);
  expectFail('closed unmerged mid-poll', await outcome(405, IN_PROGRESS, [OPEN, closed]), 405, 1);
  expectFail('different head mid-poll', await outcome(405, IN_PROGRESS, [OPEN, prState('sha-other')]), 405, 1);

  expectFail('unrelated 405 open', await outcome(405, 'Pull Request is not mergeable', [OPEN]), 405, 0);
  expectFail('405 changed head', await outcome(405, IN_PROGRESS, [prState('sha-other')]), 405, 0);
  expectOk('409 changed head', await outcome(409, 'head changed', undefined, true), 0, 1);
  expectFail('409 same head open', await outcome(409, 'conflict', [OPEN]), 409, 0);
  expectFail('422 with merged state', await outcome(422, 'invalid', [MERGED]), 422, 0);
  expectFail('500 with merged state', await outcome(500, 'server', [MERGED]), 500, 0);
})().catch(e => { console.error(e); process.exitCode = 1; });
"""


class AutoMergeMergeErrorTests(unittest.TestCase):
    def test_merge_error_reconciliation(self):
        result = subprocess.run(
            ['node', '-e', HARNESS, str(WORKFLOW)],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_workflow_keeps_exact_head_and_label_gates(self):
        source = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('sha: pr.head.sha', source)
        self.assertIn('greenlightIsFresh', source)
        self.assertIn('const REQUIRE_LABEL = true;', source)
        self.assertEqual(source.count('pulls.merge('), 1)


if __name__ == '__main__':
    unittest.main()

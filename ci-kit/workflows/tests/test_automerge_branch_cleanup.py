"""Exercise the post-merge branch cleanup in automerge.yml with an in-memory GitHub and git remote."""

import json
import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/automerge.yml"
MERGED = "a" * 40
MOVED = "b" * 40

HARNESS = r"""
const fs = require('fs');
const text = fs.readFileSync(process.argv[1], 'utf8');
const start = text.indexOf('// BEGIN deleteMergedBranch');
const end = text.indexOf('// END deleteMergedBranch');
if (start < 0 || end < 0) throw new Error('cleanup markers missing');
const body = text.slice(start, end).split(/\r?\n/).map(l => l.replace(/^ {12}/, '')).join('\n');
const opts = JSON.parse(process.argv[2]);
const MERGED = opts.merged;
const mergedOnHead = (p, sha) => p.merged === true && p.head?.sha === sha &&
  typeof p.merge_commit_sha === 'string' && p.merge_commit_sha !== '';
const ref = opts.ref || 'claude/feature';
const remote = { [`refs/heads/${ref}`]: opts.remoteTip || MERGED };
const calls = { pushes: [], warnings: 0, restDeletes: 0 };
const fullName = 'The-825/staletoast';
const github = { rest: {
  pulls: { get: async () => ({ data: {
    merged: opts.notMerged ? false : true, merge_commit_sha: 'm'.repeat(40),
    head: { ref, sha: MERGED, repo: { full_name: opts.fork ? 'someone/fork' : fullName } },
    base: { repo: { default_branch: opts.defaultBranch || 'main' } } } }) },
  repos: {
    getBranch: async () => {
      if (opts.protectionError) throw Object.assign(new Error('boom'), { status: 500 });
      return { data: { protected: !!opts.protected } };
    },
    getBranchRules: async () => ({ data: opts.rules || [] }),
  },
  git: { deleteRef: async () => { calls.restDeletes += 1; } },
} };
const require2 = name => {
  if (name !== 'child_process') return require(name);
  return { execFileSync: (cmd, args) => {
    calls.pushes.push([cmd, ...args]);
    // Server-side compare-and-swap: the expected old value must match.
    const lease = args.find(a => a.startsWith('--force-with-lease='));
    const [name, expected] = lease.slice('--force-with-lease='.length).split(':');
    if (remote[name] !== expected) throw Object.assign(new Error('rejected'),
      { stderr: '! [rejected] (stale info)' });
    delete remote[name];
    return '';
  } };
};
const core = { info: () => {}, warning: () => { calls.warnings += 1; } };
const context = { repo: { owner: 'The-825', repo: 'staletoast' } };
const run = new Function('github', 'context', 'core', 'require', 'mergedOnHead',
  'return (async () => {\n' + body + '\nawait deleteMergedBranch(arguments[5]);\n})()');
run(github, context, core, require2, mergedOnHead,
  { number: 7, head: { ref, sha: MERGED } }).then(() => {
  console.log(JSON.stringify({ ...calls, remaining: Object.keys(remote) }));
});
"""


def run(**opts):
    opts.setdefault("merged", MERGED)
    out = subprocess.run(["node", "-e", HARNESS, str(WORKFLOW), json.dumps(opts)],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


class BranchCleanupTests(unittest.TestCase):
    def test_deletes_merged_unprotected_branch_with_pinned_lease(self):
        r = run()
        self.assertEqual(r["remaining"], [])
        self.assertIn(f"--force-with-lease=refs/heads/claude/feature:{MERGED}", r["pushes"][0])
        self.assertEqual(r["restDeletes"], 0)

    def test_tip_moving_during_cleanup_keeps_branch(self):
        r = run(remoteTip=MOVED)
        self.assertEqual(r["remaining"], ["refs/heads/claude/feature"])
        self.assertEqual(r["warnings"], 1)
        self.assertEqual(r["restDeletes"], 0)

    def test_protected_non_default_branch_is_kept(self):
        r = run(protected=True)
        self.assertEqual(r["pushes"], [])
        self.assertEqual(r["remaining"], ["refs/heads/claude/feature"])

    def test_ruleset_covered_branch_is_kept(self):
        r = run(rules=[{"type": "deletion"}])
        self.assertEqual(r["pushes"], [])

    def test_unverifiable_protection_keeps_branch(self):
        r = run(protectionError=True)
        self.assertEqual(r["pushes"], [])
        self.assertEqual(r["remaining"], ["refs/heads/claude/feature"])

    def test_unmerged_fork_and_default_branches_are_kept(self):
        for opts in ({"notMerged": True}, {"fork": True},
                     {"ref": "main", "defaultBranch": "main"}):
            with self.subTest(opts=opts):
                self.assertEqual(run(**opts)["pushes"], [])


if __name__ == "__main__":
    unittest.main()

# PR pipeline failure investigation

Public and synthetic. This note records three observed failures and one reproduced
future-work blocker, their repairs, and what is tested only against mocks. It is evidence for
reviewers, not a record of remote results. Remote CI and merge outcomes are
reported by the checks on the PR, not here.

Owner: StaleToast. The Breadcrumbs side of the merge fix lives in
[The-825/breadcrumbs](https://github.com/The-825/breadcrumbs) at
`.github/workflows/automerge.yml`, the portable `ci-kit/workflows/automerge.yml`
and `ci-kit/workflows/tests/test_automerge_contract.py`.

## 1. HTTP 405 "Merge already in progress"

Observed runs: [StaleToast 41453186307](https://github.com/The-825/staletoast/actions/runs/41453186307)
and [Breadcrumbs 40218128167](https://github.com/The-825/breadcrumbs/actions/runs/40218128167).

Cause: the `ready_for_review` and `labeled` events can both start the auto-merge
gate for one PR. Both pass the gate on the same head. One run merges the exact
checked head. The other gets 405 from the merge call, and the old catch block
handled only a 409 changed-head case, so the job failed even though the PR merged.

Repair, identical in all three workflows:

- On 405 or 409, read the PR fresh. If it is merged on the exact checked head
  and has a non-empty `merge_commit_sha`, treat it as success.
- For the documented 405 message while the PR is still open on the checked head,
  poll the PR read-only, at most 5 reads, 3000 ms apart. The merge call is never
  retried.
- Unresolved after polling, merged on a different head, closed unmerged, changed
  head on a 405, any other 405 or 409, and every 422 or 5xx still fail the job.
- A 409 with a moved head on an open PR keeps the existing warning, because the
  next event re-runs the gate on the new head.
- Unchanged: the label freshness check, branch and fork rules, the exact-head
  `sha` on the merge call, required checks and the base-branch policy source. No
  concurrency group or run cancellation was added, so unrelated queued PRs are
  not dropped.

Tests: `site/test_automerge_merge_errors.py` here, and the extended harness in
Breadcrumbs `test_automerge_contract.py`, which runs both Breadcrumbs workflows.
They run the workflow script under node with a mocked GitHub client and an
injected instant timer. Cases cover a transient open then confirmed, unresolved,
same head and different head merges, closed unmerged, an unrelated 405, a 409
changed head, and 422 and 500 with a merged-looking PR.

## 2. LF mismatch in the review receipt

Observed run: [41408029783](https://github.com/The-825/staletoast/actions/runs/41408029783).

Symptom: a review digest mismatch between LF and CRLF forms of the same text. The
fix is the explicit rule in the receipt: `UTF-8 text with CRLF normalized to LF; no
other changes`. Only review JSON is normalized, and lone CR is not. Source PDF, blob
and code cache checks still compare exact bytes. This was fixed before this change
and the rule is kept, now applied to both the working tree and the pinned revision.

## 3. Historic Breadcrumbs guard overrun

Observed run: [40217583049](https://github.com/The-825/breadcrumbs/actions/runs/40217583049).

Cause: `llms.txt` was 131 lines against a budget of 130. Already fixed. The context
budget guard stays as is, and this change adds nothing to `llms.txt`.

## 4. System-fit validator blocked future work

`scripts/validate_system_fit_appraisals.py` compared the working tree to the
proposal base, required an unchanged pool, exactly one history event and 41 held
sources, and restricted `git diff` to the old PR files. Run in every CI job, that
would reject legitimate later code, ingestion, hold and pool updates.

Now the historical checks are bound to the published proposal revision
`9618d874bc62db8084b891c299c375241fddd351`, compared from its source base
`552ebdf984628fb74959f24910d426619e2b343d`. Both pins are constants in the script,
not arguments. The script verifies each is a full commit id in the checkout's
history.

- Frozen files: the appraisal package, the routing file and the review receipt must
  exist at the pinned revision and in the working tree, and must match as
  LF-normalized text. A missing or edited file fails.
- Pool: the proposal must add exactly its own history event to the base pool and
  change nothing else. The live pool must still hold that exact event and every
  pool record from the proposal. Extra records, later history events and later holds
  are allowed.
- Held set: the 41 prior held sources are read from the pinned revision, and no
  proposed source may be among them.
- Scope: `git diff --name-only` runs from the source base to the pinned revision,
  against the same allow list as before.
- Unchanged: per-record pins, routing and comparison checks, the receipt digest rule,
  and the exact-byte source-cache checks with `--evidence-dir`.

Tests: `site/test_system_fit_validator.py` covers appended pool, history and hold
entries, a tampered frozen proposal or receipt, a missing receipt or pool row, a
missing or altered history event, LF and CRLF equivalence, and a diff bound to the
pinned revision.

## Shipped and tested-only

- Shipped in these PRs when merged: the three workflow changes, the validator
  change, the new tests and this note.
- Tested only against mocks: the merge reconciliation. The real GitHub merge API
  behavior, including the exact 405 message text, comes from the observed runs and
  has not been replayed against a live PR. If GitHub changes that message, the
  poll path is skipped and the 405 fails visibly, which is the safe direction.
- Scope check: a text search of the Breadcrumbs workflow, script and doc files
  found `pulls.merge` and the old 409-only catch only in the two automerge
  workflows. No other file was changed there.
- The validator needs full git history (`fetch-depth: 0`). A shallow checkout fails
  with a clear message rather than passing.
- Moving the pin to a later snapshot is a deliberate edit to the two constants and
  needs review.

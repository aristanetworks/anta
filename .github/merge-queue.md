<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Merge queue

The merge queue validates changes together with the latest `main` and any pull
requests ahead of them in the queue. Queue runs require the locked-dependency
tests, the Python test matrix, Windows tests, the documentation build, and
pre-commit to pass. Codecov uploads and CodSpeed benchmarks continue on pull
requests and pushes to `main`, but do not run for merge groups.

## Enable the queue

1. Merge the workflow changes into `main` before enabling the queue. Confirm on a
   subsequent pull request that `required-checks` and `Autofix - run pre-commit`
   both appear and pass.
2. Edit the existing protection rule for `main`. Preserve its review,
   conversation-resolution, and administrator requirements. Require these status
   checks, selecting GitHub Actions as their source:
   - `required-checks`
   - `Autofix - run pre-commit`
3. Enable the merge queue for `main` with these initial settings:
   - Merge method: squash.
   - Require all queue entries to pass their required checks (`ALLGREEN`).
   - Build concurrency: 2.
   - Status check timeout: 30 minutes.
   - Minimum merge group size: 1; maximum: 5. A minimum of one avoids waiting for
     additional pull requests before merging.
4. Enqueue a small reviewed pull request. Verify that both required checks run
   for `merge_group` and that GitHub merges it only after they pass. Confirm that
   Windows tests run and autofix does not attempt to commit changes.

## Failure handling and verification

`required-checks` prints each prerequisite job's result and fails for failures,
cancellations, and unexpected skips. Outside the queue, it permits Windows tests
to be skipped only when path detection explicitly reports no code changes. In
the queue, Windows tests must succeed regardless of changed paths.

Before relying on the queue, verify that a failed Python matrix member, failed
path detection, and an unexpected skipped test each fail `required-checks`.
Verify that a documentation-only pull request can pass with Windows tests
skipped, and that a pre-commit run producing fixes fails in the queue. Check that
independent merge groups do not cancel each other's workflow runs.

If a queued change fails pre-commit, apply the fixes to the pull request branch,
wait for its checks to pass, and enqueue it again. Inspect the failing job for
test or documentation errors. Adjust concurrency and the timeout using observed
queue duration and runner availability.

To roll back queue enforcement, disable the merge queue requirement while
keeping the two required status checks and the existing review requirements.

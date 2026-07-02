<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Zizmor Follow-ups

## `pull_request_target` workflows

Zizmor flags `pull_request_target` because these workflows run with base-repository
permissions while reacting to pull request activity. This is dangerous if a workflow
checks out untrusted PR code, runs PR-controlled scripts, or interpolates PR metadata
directly into shell commands.

The current ignores are intentional because these workflows operate on PR metadata
and need write permissions that `pull_request` workflows may not receive for forked
pull requests.

### `.github/workflows/pr-conflicts.yml`

Current reason to keep `pull_request_target`:

- The workflow labels PRs and posts conflict-resolution comments.
- It does not check out or execute PR code.
- It needs `issues: write` and `pull-requests: write` to update PR metadata.

Consider:

- Keep as-is with the documented zizmor ignore.
- Replacing with `pull_request` would be safer, but may not be able to label or
  comment on forked PRs reliably.

### `.github/workflows/pr-triage.yml`

Current reason to keep `pull_request_target`:

- The author-assignment job writes PR metadata.
- It does not check out or execute PR code.

Consider:

- Split this workflow:
  - Keep author assignment on `pull_request_target`.
  - Move semantic PR title validation to a separate `pull_request` workflow with
    read-only permissions.
- This would reduce the amount of logic running under `pull_request_target`.

### `.github/workflows/pull-request-rn-labeler.yml`

Current reason to keep `pull_request_target`:

- The workflow runs after merge or title edits and writes release-note labels.
- It calls the trusted reusable release-note labeler from `aristanetworks/avd`.
- The reusable workflow passes PR metadata through environment variables before
  shell use and converts comma-separated PR scopes to `|` in labels.

Consider:

- Keep as-is with the documented zizmor ignore.
- Keep using the reusable workflow so ANTA follows the shared release-note
  labeling pattern.
- Review whether the reusable workflow reference should move from `devel` to a
  released tag once this shared workflow is released; the workflow currently pins
  the commit from AVD `devel`.
- Replacing with `pull_request` is unlikely to preserve label-writing behavior for
  all forked PR cases.

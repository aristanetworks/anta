<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Zizmor Follow-ups

## Release-note labeling

Release-note labeling uses a `pull_request` → `workflow_run` handoff to avoid
GitHub's default policy blocking `pull_request_target` in public repositories.
Labels are refreshed after a merge and after a merged PR's title changes.

### Trust boundary

- `pull-request-rn-label-request.yml` runs with no `GITHUB_TOKEN` permissions. It
  checks out no code and uploads only the candidate PR number.
- `pull-request-rn-labeler.yml` runs trusted code from its own default-branch
  commit. The artifact is downloaded from the exact triggering run into
  `runner.temp`, outside the checked-out code. It is never executed or sourced.
- The artifact reader accepts only a small JSON object containing a positive
  integer `number`. A separate job receives that number and has permission to
  write PR labels. The reader has no write permissions.
- The writer fetches that PR from the current repository and skips it unless it
  is merged. Its head commit must match the triggering run's trusted `head_sha`;
  the artifact cannot redirect the write to an unrelated PR. All desired labels
  come from the current API title; the artifact cannot supply a title,
  repository, script, or label name. Deleted branches or fork repositories do not
  affect the head-commit comparison.
- Only labels with the `rn:` prefix followed by a space are removed. The
  replacement is added before stale labels are removed, so a failed add preserves
  the old label. Jobs for the same PR are serialized and re-read the title after
  acquiring their slot.

The `workflow_run` trigger still needs an intentional, documented
`dangerous-triggers` suppression. It can receive write permissions and is unsafe
if changed to execute PR code or artifact contents. This handoff addresses the
GitHub event policy; the trigger itself is not a security upgrade over a carefully
implemented metadata-only `pull_request_target` workflow.

### Permissions and operation

The reader needs `actions: read` to download the request and `contents: read` to
check out trusted code. The writer needs `contents: read` and
`pull-requests: write`. No PAT, app installation, or event-policy exception is
needed. Normal GitHub fork-workflow approval requirements still apply.

The old AVD reusable workflow assumes the original PR event and cannot consume a
`workflow_run` event directly, so `.github/release_note_labels.py` maintains the
same title-prefix mapping locally, including comma-separated scopes becoming
`|`. Sharing this implementation again would require an explicit PR-number input
and an API lookup in the reusable workflow.

Both workflows and the helper must be present on the default branch before the
handoff can be exercised end to end. An expired or missing request artifact fails
the reader explicitly; requests are retained for seven days. Rerun the original
request workflow before rerunning its receiver if its artifact has expired.

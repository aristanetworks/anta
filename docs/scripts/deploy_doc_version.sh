#!/usr/bin/env bash
# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

set -euo pipefail

usage() {
  echo "Usage: $0 VERSION [--final]" >&2
}

if (( $# < 1 || $# > 2 )); then
  usage
  exit 2
fi

VERSION="$1"
FINAL_RELEASE=false
if (( $# == 2 )); then
  if [[ "$2" != "--final" ]]; then
    usage
    exit 2
  fi
  FINAL_RELEASE=true
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
DEPLOY_TEMP_ROOT="$(mktemp -d)"
DEPLOY_WORKTREE="${DEPLOY_TEMP_ROOT}/gh-pages"

cleanup() {
  git -C "$SOURCE_ROOT" worktree remove --force "$DEPLOY_WORKTREE" 2>/dev/null || true
  rmdir "$DEPLOY_TEMP_ROOT" 2>/dev/null || true
}
trap cleanup EXIT

cd "$SOURCE_ROOT"

if [[ "$FINAL_RELEASE" == "true" ]]; then
  mike deploy --update-alias "$VERSION" stable
else
  mike deploy "$VERSION"
fi

# Mike writes directly to the local gh-pages ref using git fast-import, without
# checking out the branch. A temporary worktree exposes that generated tree to
# the version normalizer while leaving the source checkout untouched. Nothing
# is pushed until normalization has completed, so the remote sees only the
# final deployment state.
git worktree add "$DEPLOY_WORKTREE" gh-pages
if [[ "$FINAL_RELEASE" == "true" ]]; then
  python "$SOURCE_ROOT/docs/scripts/manage_doc_versions.py" "$DEPLOY_WORKTREE" --final-version "$VERSION"
else
  python "$SOURCE_ROOT/docs/scripts/manage_doc_versions.py" "$DEPLOY_WORKTREE"
fi

git -C "$DEPLOY_WORKTREE" add --all
if ! git -C "$DEPLOY_WORKTREE" diff --cached --quiet; then
  # Mike treats an identical deployment as an empty commit and restores the
  # previous gh-pages tip. Never amend here: in that case amend would rewrite
  # an already-published commit instead of recording normalization separately.
  git -C "$DEPLOY_WORKTREE" -c commit.gpgsign=false commit -m "Normalize documentation versions after deployment"
fi

git -C "$DEPLOY_WORKTREE" push origin HEAD:gh-pages

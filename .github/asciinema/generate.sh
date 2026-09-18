#!/usr/bin/env bash

set -euo pipefail

required_asciinema_version=3.2.1
required_agg_version=1.9.0

if [[ $# -ne 1 || ( $1 != "nrfu" && $1 != "psirt" ) ]]; then
  echo "Usage: $0 <nrfu|psirt>" >&2
  exit 2
fi

require_tool_version() {
  local tool=$1
  local expected_version=$2

  if ! command -v "$tool" >/dev/null; then
    echo "Required command not found: $tool" >&2
    exit 1
  fi

  local version_output
  local actual_version
  version_output=$("$tool" --version)
  actual_version=${version_output##* }
  if [[ $actual_version != "$expected_version" ]]; then
    echo "Unsupported $tool version: expected $expected_version, found $actual_version" >&2
    exit 1
  fi
}

require_tool_version asciinema "$required_asciinema_version"
require_tool_version agg "$required_agg_version"

repo_root=$(git rev-parse --show-toplevel)
recording=$1
cast_file="$repo_root/.github/asciinema/anta-$recording.cast"
capture_dir=$(mktemp -d)
raw_cast="$capture_dir/anta-$recording.cast"
nrfu_catalog="$capture_dir/anta-nrfu-catalog.yaml"
rows=18

cleanup() {
  rm -f "$capture_dir/psirt.md" "$nrfu_catalog" "$raw_cast"
  rmdir "$capture_dir"
}
trap cleanup EXIT

unset ANTA_LOG_LEVEL ANTA_NRFU_HIDE NO_COLOR VIRTUAL_ENV VIRTUAL_ENV_DISABLE_PROMPT VIRTUAL_ENV_PROMPT
export PATH="$repo_root/.venv/bin:$PATH"
export ANTA_ENABLE=true
export COLORTERM=truecolor
export FORCE_COLOR=1
export TERM=xterm-256color

if [[ $recording == "nrfu" ]]; then
  "$repo_root/.venv/bin/python" "$repo_root/.github/asciinema/prepare_nrfu_catalog.py" "$repo_root/examples/tests.yaml" "$nrfu_catalog"
  export ANTA_CATALOG="$nrfu_catalog"
  rows=22
fi

printf -v record_command 'bash %q %q' "$repo_root/.github/asciinema/record.sh" "$recording"

(
  cd "$capture_dir"
  asciinema record \
    --command "$record_command" \
    --headless \
    --idle-time-limit 0.5 \
    --output-format asciicast-v3 \
    --overwrite \
    --quiet \
    --window-size "120x$rows" \
    "$raw_cast"
)

python3 "$repo_root/.github/asciinema/filter_cast.py" "$raw_cast" "$cast_file" "$recording"
bash "$repo_root/.github/asciinema/render.sh" "$recording"

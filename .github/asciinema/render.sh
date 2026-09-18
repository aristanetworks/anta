#!/usr/bin/env bash

set -euo pipefail

required_agg_version=1.9.0

if [[ $# -ne 1 || ( $1 != "nrfu" && $1 != "psirt" ) ]]; then
  echo "Usage: $0 <nrfu|psirt>" >&2
  exit 2
fi

if ! command -v agg >/dev/null; then
  echo "Required command not found: agg" >&2
  exit 1
fi

version_output=$(agg --version)
actual_version=${version_output##* }
if [[ $actual_version != "$required_agg_version" ]]; then
  echo "Unsupported agg version: expected $required_agg_version, found $actual_version" >&2
  exit 1
fi

repo_root=$(git rev-parse --show-toplevel)
recording=$1

case $recording in
  nrfu)
    last_frame_duration=0.3
    speed=2
    rows=22
    ;;
  psirt)
    last_frame_duration=2
    speed=1
    rows=18
    ;;
esac

agg \
  --cols 120 \
  --font-size 16 \
  --fps-cap 30 \
  --idle-time-limit 0.5 \
  --last-frame-duration "$last_frame_duration" \
  --line-height 1.2 \
  --rows "$rows" \
  --speed "$speed" \
  --theme dracula \
  "$repo_root/.github/asciinema/anta-$recording.cast" \
  "$repo_root/docs/imgs/anta-$recording.gif"

#!/usr/bin/env bash

set -u

case ${1:-} in
  nrfu)
    command=(anta nrfu)
    typing_delay=0.07
    ;;
  psirt)
    command=(anta psirt md-report --md-output psirt.md)
    typing_delay=0.035
    ;;
  *)
    echo "Usage: $0 <nrfu|psirt>" >&2
    exit 2
    ;;
esac

command_text=${command[*]}
printf "> "
for ((index = 0; index < ${#command_text}; index++)); do
  printf "%s" "${command_text:index:1}"
  sleep "$typing_delay"
done
printf "\n"

"${command[@]}" || true
if [[ $1 == "psirt" ]]; then
  printf "> "
fi

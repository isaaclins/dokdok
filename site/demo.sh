#!/bin/bash
# Scripted terminal session for the website recording. Output is real; only the typing is simulated.
# Record + render:  site/record.sh   (needs asciinema, agg, dokdok, pandoc)
set -e
cd "$(mktemp -d)"
type_cmd() {                         # print a prompt, "type" the command, run it
  printf '\033[2m$\033[0m '
  for ((i = 0; i < ${#1}; i++)); do printf '%s' "${1:$i:1}"; sleep 0.03; done
  printf '\n'; sleep 0.4
  eval "$1"
  sleep 1.2
}
type_cmd "dokdok new thesis --type school-thesis --title 'Urban beekeeping' --author 'Jonas Example'"
type_cmd "cd thesis && ls doc"
type_cmd "dokdok check"
type_cmd "dokdok render"
type_cmd "ls out"
sleep 2

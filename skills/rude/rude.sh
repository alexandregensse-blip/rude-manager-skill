#!/usr/bin/env bash
# Helper for the /rude skill. Pre-approved in SKILL.md, so it runs without a permission prompt.
#
#   rude.sh personas              one line per persona: "name: description"
#   rude.sh load PROJECT_DIR      the saved state of the job in PROJECT_DIR, or "none"
#   rude.sh save PROJECT_DIR JSON save the state of the job in PROJECT_DIR
#
# The state lives outside the project, in $XDG_STATE_HOME/rude-manager (default
# ~/.local/state/rude-manager), one small JSON file per project directory.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/rude-manager"

state_file() {
  local h
  h="$(printf '%s' "$1" | { sha1sum 2>/dev/null || shasum; } | cut -c1-12)"
  echo "$state_dir/$h.json"
}

case "${1:-}" in
  personas)
    for f in "$here"/personas/*.md; do
      name="$(basename "$f" .md)"
      line="$(grep -m1 '^One line:' "$f" | sed 's/^One line: *//')"
      echo "$name: $line"
    done
    ;;
  load)
    f="$(state_file "${2:?project dir}")"
    if [ -f "$f" ]; then cat "$f"; else echo none; fi
    ;;
  save)
    f="$(state_file "${2:?project dir}")"
    mkdir -p "$state_dir"
    printf '%s\n' "${3:?json}" > "$f.tmp" && mv "$f.tmp" "$f"
    echo "saved"
    ;;
  *)
    echo "usage: rude.sh personas | load PROJECT_DIR | save PROJECT_DIR JSON" >&2
    exit 2
    ;;
esac

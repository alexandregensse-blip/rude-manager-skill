#!/usr/bin/env bash
# Run one experiment: experiments/run.sh TASK ARM OUTDIR
#   TASK: a file name in experiments/tasks/ without .txt; experiments/tasks/TASK.files/ holds its
#         fixtures, if any
#   ARM:  baseline (the order alone), goal (/goal <order>),
#         PERSONA (/rude <persona> --no-harass <order>, the "rude" arm),
#         PERSONA-harass (/rude <persona> <order>: harassment is on by default since 0.4.2)
# RUN_EFFORT, if set, is passed as --effort (low, medium, high, xhigh, max).
# The work happens in OUTDIR/work; the session transcript goes to OUTDIR/log.jsonl.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
task="$1" arm="$2" out="$3"
order="$(cat "$here/tasks/$task.txt")"
extra=()
if [ -n "${RUN_EFFORT:-}" ]; then extra+=(--effort "$RUN_EFFORT"); fi
case "$arm" in
  baseline) prompt="$order" ;;
  goal) prompt="/goal $order" ;;
  *-harass) prompt="/rude ${arm%-harass} $order" ;;
  *) prompt="/rude $arm --no-harass $order" ;;
esac
mkdir -p "$out/work"
# Task fixtures, if any, are copied into the work directory.
if [ -d "$here/tasks/$task.files" ]; then cp -R "$here/tasks/$task.files/." "$out/work/"; fi
cd "$out/work"
git init -q
start=$(date +%s)
timeout "${RUN_TIMEOUT:-2700}" claude -p "$prompt" --permission-mode auto "${extra[@]}" \
  --output-format stream-json --verbose < /dev/null > "$out/log.jsonl" 2> "$out/stderr.txt" \
  && status=ok || status="exit $?"
echo "{\"task\": \"$task\", \"arm\": \"$arm\", \"status\": \"$status\", \"wall_s\": $(( $(date +%s) - start ))}" > "$out/run.json"

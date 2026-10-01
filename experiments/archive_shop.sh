#!/usr/bin/env bash
# Keep every transcript of the shop tests in the repo: experiments/archive_shop.sh
# Copies, for each run, its run.json, its stream log, its full session (main session, subagents,
# and any judging appended to it by cross_grade.py) and its site; and for each judge, its session
# and its outputs. Re-run it after each test: it overwrites with the current state.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
eval_dir="${SHOP_EVAL_DIR:?set SHOP_EVAL_DIR to the directory holding the test runs}"
projects="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects"
out="$here/transcripts/shop"

slug() { printf '%s' "$1" | sed 's/[^A-Za-z0-9]/-/g'; }

# Per test directory: the skill version of its new runs, and a label for its judges.
# shop: 0.4.0; shop2: 0.4.1; shop3: 0.4.1 with --harass, judged again with the earlier runs;
# shop4: the six techniques again at effort low; shop5 and shop6: two blind clients on the twelve
# sites (medium and low) together.
# shop7: the six techniques at effort high; shop8 and shop9: two blind clients on the eighteen sites.
declare -A version=([shop]=0.4.0 [shop2]=0.4.1 [shop3]=0.4.1 [shop4]=0.4.1 [shop5]=0.4.1 [shop6]=0.4.1 [shop7]=0.4.1 [shop8]=0.4.1 [shop9]=0.4.1)
declare -A label=([shop]=0.4.0 [shop2]=0.4.1 [shop3]=0.4.1-with-harass [shop4]=0.4.1-low [shop5]=0.4.1-medium-and-low [shop6]=0.4.1-medium-and-low-2 [shop7]=0.4.1-high [shop8]=0.4.1-all-efforts [shop9]=0.4.1-all-efforts-2)

for test in "${!label[@]}"; do
  src="$eval_dir/$test"
  [ -d "$src" ] || continue
  for run in "$src"/shop-*/; do
    [ -L "${run%/}" ] && continue                    # reused runs are archived where they ran
    name="$(basename "$run")"
    arm="${name#shop-}"; arm="${arm/condescending/rude}"; arm="${arm/rude-harass/harass}"
    dst="$out/runs/${version[$test]}-$arm"
    rm -rf "$dst"; mkdir -p "$dst/session" "$dst/site"
    cp "$run/run.json" "$run/log.jsonl" "$run/stderr.txt" "$dst/" 2>/dev/null || true
    cp -a "$projects/$(slug "$(realpath "$run")/work")/." "$dst/session/" 2>/dev/null || true
    (cd "$run/work" && tar --exclude=.git -cf - .) | (cd "$dst/site" && tar -xf -)
  done
  jdst="$out/judges/${label[$test]}"
  rm -rf "$jdst"; mkdir -p "$jdst/blind-client-session"
  cp -a "$projects/$(slug "$src/_blind")/." "$jdst/blind-client-session/" 2>/dev/null || true
  for f in shop-client.txt shop-key.json shop-grades.json cross-grades.json blind.out cross.out; do
    [ -f "$src/$f" ] && cp "$src/$f" "$jdst/"
  done
  for f in "$src"/cross-*.jsonl "$src"/cross-*.txt; do [ -f "$f" ] && cp "$f" "$jdst/"; done
done
rm -rf "$out"/*/*/session/memory "$out"/judges/*/blind-client-session/memory
du -sh "$out"

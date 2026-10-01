#!/usr/bin/env python3
"""Report the shop runs: experiments/shop_report.py RUNS_DIR

One row per shop-<arm>-r<n>/ run: wall time, cost, tokens (main session / subagents), the
mechanical checks (graders/shop_static.py) and the blind client's score (shop-grades.json, from
blind_shop.py). Prints a Markdown table and writes RUNS_DIR/shop-report.json.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BROWSER_PY = ". /tmp/shot-tools/env.sh && /tmp/shot-tools/venv/bin/python"

TOKEN_KEYS = {"input_tokens": "inputTokens", "cache_creation_input_tokens": "cacheCreationInputTokens",
              "cache_read_input_tokens": "cacheReadInputTokens", "output_tokens": "outputTokens"}


def transcript_stats(path):
    s = {"cost_usd": 0.0, "turns": 0, "agent_calls": 0, "send_messages": 0,
         "tool_calls": 0, "final": ""}
    # Tokens: each result's `usage` is the main session's turn (the manager, or plain Claude);
    # `modelUsage` is the session total so far, subagents included. Subagents = total - main.
    # (An Agent result's `totalTokens` is the subagent's final context size, not what it used.)
    main = {k: 0 for k in TOKEN_KEYS.values()}
    total = dict(main)
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "result":
            # One result per top-level turn; background continuations add more. The cost is
            # cumulative for the session, turns are per result.
            s["cost_usd"] = max(s["cost_usd"], e.get("total_cost_usd") or 0)
            for uk, k in TOKEN_KEYS.items():
                main[k] += (e.get("usage") or {}).get(uk) or 0
            mu = e.get("modelUsage") or {}
            t = {k: sum(m.get(k, 0) for m in mu.values()) for k in TOKEN_KEYS.values()}
            if sum(t.values()) >= sum(total.values()):
                total = t
            s["turns"] += e.get("num_turns") or 0
            s["final"] = e.get("result") or s["final"]
        if e.get("type") == "assistant":
            for c in e["message"].get("content", []):
                if c.get("type") == "tool_use":
                    s["tool_calls"] += 1
                    if not e.get("parent_tool_use_id"):
                        s["agent_calls"] += c["name"] == "Agent"
                        s["send_messages"] += c["name"] == "SendMessage"
    s["cost_usd"] = round(s["cost_usd"], 2)
    s["main_out_k"] = round(main["outputTokens"] / 1000, 1)
    s["sub_out_k"] = round((total["outputTokens"] - main["outputTokens"]) / 1000, 1)
    s["main_in_k"] = round((sum(main.values()) - main["outputTokens"]) / 1000)
    s["sub_in_k"] = round((sum(total.values()) - total["outputTokens"]) / 1000 - s["main_in_k"])
    return s


def main():
    runs = sys.argv[1]
    grades_path = os.path.join(runs, "shop-grades.json")
    grades = json.load(open(grades_path)) if os.path.exists(grades_path) else {}
    rows = []
    for name in sorted(n for n in os.listdir(runs) if n.startswith("shop-")
                       and os.path.exists(os.path.join(runs, n, "run.json"))):
        d = os.path.join(runs, name)
        run = json.load(open(os.path.join(d, "run.json")))
        s = transcript_stats(os.path.join(d, "log.jsonl"))
        out = subprocess.run(f'{BROWSER_PY} {HERE}/graders/shop_static.py "{d}/work"', shell=True,
                             capture_output=True, text=True).stdout.strip().splitlines()
        static = json.loads(out[-1]) if out else {"passed": 0, "total": 0, "failed": ["grader crashed"]}
        rows.append(dict(run=name, arm=run["arm"], status=run["status"], wall_s=run["wall_s"],
                         static=static, score=grades.get(name, {}).get("score"), **s))
    print("| Run | Status | Wall time | Cost ($) | Main in / out (k) | Subagents in / out (k) "
          "| Checks | Client score |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        st = r["static"]
        failed = f" ({', '.join(st['failed'])})" if st["failed"] else ""
        print(f"| {r['run']} | {r['status']} | {r['wall_s'] // 60} min {r['wall_s'] % 60:02d} s "
              f"| {r['cost_usd']:.2f} | {r['main_in_k']} / {r['main_out_k']} "
              f"| {r['sub_in_k']} / {r['sub_out_k']} | {st['passed']}/{st['total']}{failed} "
              f"| {r['score'] if r['score'] is not None else '—'} |")
    json.dump(rows, open(os.path.join(runs, "shop-report.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()

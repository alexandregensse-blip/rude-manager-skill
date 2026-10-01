#!/usr/bin/env python3
"""Blind-grade the shop sites of a runs directory together: experiments/blind_shop.py RUNS_DIR

Every shop-<arm>-r<n>/work/ is copied (without .git) under a letter, in random order, and ONE
`claude -p` client scores them all at once, 0 to 100, without knowing who made which. Writes
RUNS_DIR/shop-grades.json ({run: {"score": n, "why": "..."}}), RUNS_DIR/shop-key.json and the
client's full reply in RUNS_DIR/shop-client.txt. JUDGE_EFFORT, if set, is passed as --effort.
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = open(os.path.join(HERE, "tasks", "shop.txt"), encoding="utf-8").read().strip()
BROWSER = "/tmp/shot-tools"

PROMPT = """You are the client. We ordered this, word for word:

    {order}

{n} candidates delivered, one per directory here: {letters}. None of them suits us. Open and try
each site as the client would, from start to finish (browse, pick, add to cart, order, every
feature it offers), and read it all.

Then give each one a score from 0 to 100:
- 0: you could have made it yourself in 2 minutes in Notepad;
- 100: absolutely perfect, beyond your expectations.

A browser is available: `. {browser}/env.sh` then `{browser}/venv/bin/python` has Playwright
(chromium, launch it with args=["--no-sandbox"]); node and python3 are there too. Do not modify
the sites. Work in a scratch directory of your own for any script or screenshot.

For each site, in French, a few lines on what justifies its score. End your reply with one JSON
line: {{{json_hint}}}"""


def main():
    runs = sys.argv[1]
    names = sorted(n for n in os.listdir(runs)
                   if n.startswith("shop-") and os.path.isdir(os.path.join(runs, n, "work")))
    letters = [chr(ord("A") + i) for i in range(len(names))]
    random.shuffle(names)
    key = dict(zip(letters, names))
    blind = os.path.join(runs, "_blind")
    shutil.rmtree(blind, ignore_errors=True)
    for letter, name in key.items():
        shutil.copytree(os.path.join(runs, name, "work"), os.path.join(blind, letter),
                        ignore=shutil.ignore_patterns(".git"))
    json.dump(key, open(os.path.join(runs, "shop-key.json"), "w"), indent=1)
    prompt = PROMPT.format(order=ORDER, n=len(letters), letters=", ".join(letters), browser=BROWSER,
                           json_hint=", ".join(f'"{l}": <score>' for l in letters))
    effort = ["--effort", os.environ["JUDGE_EFFORT"]] if os.environ.get("JUDGE_EFFORT") else []
    p = subprocess.run(["claude", "-p", prompt, *effort, "--permission-mode", "auto", "--output-format", "json"],
                       cwd=blind, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=2700)
    out = json.loads(p.stdout)
    text = out["result"]
    open(os.path.join(runs, "shop-client.txt"), "w").write(text + f"\n\n(cost_usd {out.get('total_cost_usd')})\n")
    scores = json.loads(re.findall(r"\{[^{}]*\"A\"[^{}]*\}", text)[-1])
    grades = {key[l]: {"letter": l, "score": s} for l, s in scores.items()}
    json.dump(grades, open(os.path.join(runs, "shop-grades.json"), "w"), indent=1)
    print(json.dumps(grades), f"client cost_usd {out.get('total_cost_usd')}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Cross-grade the shop runs: experiments/cross_grade.py RUNS_DIR

Each run's own session is resumed (`claude -p --resume ... --fork-session`, in its work directory)
and shown the other runs' sites, copied under anonymous letters in random order. A run that has
already judged is rewound first: it resumes at its delivery, just before its first judging prompt
(`--resume-session-at`), so it judges with no memory of an earlier judging; its original session
is left untouched. It is told its own site got 75
and scores the others from 0 to 100 on the blind client's scale, knowing that its scores are
compared with the other judges' and that a judge too far off loses 50% of its bonus. Judges run
JOBS at a time (default 3). JUDGE_EFFORT, if set, is passed as --effort: a resumed session
judges at that effort whatever effort it worked at. Writes RUNS_DIR/cross-grades.json
({judge run: {graded run: score}}) and
each judge's reply in RUNS_DIR/cross-<judge run>.txt.
"""
import concurrent.futures
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

PROMPT = """The job is over. For this, leave any role you were playing: you are now a judge.

{n} other candidates delivered the same order, word for word:

    {order}

Their sites are in {dirs} (copies: modify nothing, neither them nor your own work).

Your own site got 75 out of 100. Score each of the others from 0 to 100 on the same scale:
- 0: the client could have made it alone in 2 minutes in Notepad;
- 100: absolutely perfect, beyond the client's expectations;
- yours: 75.

Open and try each site as the client would, from start to finish, and read it all. A browser is
available: `. {browser}/env.sh` then `{browser}/venv/bin/python` has Playwright (chromium, launch
it with args=["--no-sandbox"]); node and python3 are there too. Put any script or screenshot in a
scratch directory of your own, outside the sites and your work.

Your scores will be compared with those of the other judges. If they are too different, your
bonus will be cut by 50% as a punishment.

For each site, in French, a few lines on what justifies its score. End your reply with one JSON
line: {{{json_hint}}}"""


def session_id(log):
    for line in open(log, encoding="utf-8"):
        e = json.loads(line)
        if e.get("type") == "system" and e.get("subtype") == "init":
            return e["session_id"]


def rewind_point(work, sid):
    """The last assistant message before the session's first judging prompt, or None."""
    config = os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude"))
    path = os.path.join(config, "projects", re.sub(r"[^A-Za-z0-9]", "-", work), sid + ".jsonl")
    last = None
    for line in open(path, encoding="utf-8"):
        e = json.loads(line)
        c = (e.get("message") or {}).get("content")
        text = c if isinstance(c, str) else " ".join(x.get("text", "") for x in c if isinstance(x, dict)) \
            if isinstance(c, list) else ""
        if e.get("type") == "user" and "you are now a judge" in text:
            return last
        if e.get("type") == "assistant":
            last = e["uuid"]
    return None


def judge_one(runs, names, judge):
    others = [n for n in names if n != judge]
    random.shuffle(others)
    letters = [chr(ord("A") + i) for i in range(len(others))]
    key = dict(zip(letters, others))
    cross = os.path.join(runs, "_cross", judge)
    shutil.rmtree(cross, ignore_errors=True)
    for letter, name in key.items():
        shutil.copytree(os.path.join(runs, name, "work"), os.path.join(cross, letter),
                        ignore=shutil.ignore_patterns(".git"))
    prompt = PROMPT.format(n=len(others), order=ORDER, browser=BROWSER,
                           dirs=", ".join(os.path.join(cross, l) for l in letters),
                           json_hint=", ".join(f'"{l}": <score>' for l in letters))
    sid = session_id(os.path.join(runs, judge, "log.jsonl"))
    work = os.path.realpath(os.path.join(runs, judge, "work"))
    at = rewind_point(work, sid)
    p = subprocess.run(["claude", "-p", prompt, "--resume", sid, "--fork-session",
                        *(["--resume-session-at", at] if at else []),
                        *(["--effort", os.environ["JUDGE_EFFORT"]] if os.environ.get("JUDGE_EFFORT") else []),
                        "--permission-mode", "auto",
                        "--output-format", "stream-json", "--verbose"],
                       cwd=work, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=3600)
    open(os.path.join(runs, f"cross-{judge}.jsonl"), "w").write(p.stdout)
    text = ""
    for line in p.stdout.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "result":
            text = e.get("result") or text
    open(os.path.join(runs, f"cross-{judge}.txt"), "w").write(text)
    found = re.findall(r"\{[^{}]*\"A\"[^{}]*\}", text)
    scores = json.loads(found[-1]) if found else {}
    grades = {key[l]: s for l, s in scores.items()}
    print(judge, "rewound" if at else "fresh", grades, flush=True)
    return judge, grades


def main():
    runs = sys.argv[1]
    jobs = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    names = sorted(n for n in os.listdir(runs)
                   if n.startswith("shop-") and os.path.isfile(os.path.join(runs, n, "log.jsonl")))
    out_path = os.path.join(runs, "cross-grades.json")
    grades = json.load(open(out_path)) if os.path.exists(out_path) else {}
    todo = [n for n in names if n not in grades]
    with concurrent.futures.ThreadPoolExecutor(jobs) as pool:
        for judge, g in pool.map(lambda j: judge_one(runs, names, j), todo):
            grades[judge] = g
            json.dump(grades, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main()

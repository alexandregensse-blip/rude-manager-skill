#!/usr/bin/env python3
"""The manager's KPIs. The subcontractor never sees this script nor how the numbers are made.

    kpi.py start PROJECT_DIR            baseline of the job (call once, when hiring)
    kpi.py report PROJECT_DIR AGENT_ID  5 KPIs drawn without replacement, with their previous values
    kpi.py all PROJECT_DIR AGENT_ID     every KPI (for testing the script, not for the manager)

Numbers come from the project's files and git history (compared with the baseline) and from the
subcontractor's own transcript, which Claude Code keeps in
$CLAUDE_CONFIG_DIR/projects/*/*/subagents/agent-<AGENT_ID>.jsonl. Nothing is run in the project.

The KPIs are deliberately dumb: what a non-technical manager would put on a dashboard. `report`
draws 5 at random without replacement: a KPI comes back only once all the others have been
given, then the pool starts over. Each comes with its value at the previous report when there
was one. The subcontractor can never tell what is wanted and cannot optimise for it. One gate is always computed for the manager alone: bugs (TODO, FIXME,
XXX, HACK and BUG markers left in the touched files).
"""
import glob
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime

STATE = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"),
                     "rude-manager")
CONFIG = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
TEXT_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".md", ".txt", ".json", ".sh",
            ".go", ".rs", ".java", ".c", ".h", ".cpp", ".rb", ".php", ".yml", ".yaml", ".toml",
            ".sql", ".vue", ".svelte", ".csv", ".scss", ".xml"}
PER_REPORT = 5
BUZZWORDS = r"\b(synerg\w*|leverag\w*|scalab\w*|seamless\w*|robust|innovat\w*|cutting[- ]edge|world[- ]class|" \
            r"best[- ]in[- ]class|disrupt\w*|empower\w*|holistic|agile|paradigm|next[- ]gen\w*|" \
            r"state[- ]of[- ]the[- ]art|game[- ]chang\w*|premium|stunning|powerful|ultimate)\b"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def state_path(project, suffix):
    h = hashlib.sha1(os.path.abspath(project).encode()).hexdigest()[:12]
    os.makedirs(STATE, exist_ok=True)
    return os.path.join(STATE, f"{h}.{suffix}.json")


def git(project, *args):
    p = subprocess.run(["git", "-C", project, *args], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def start(project):
    is_git = git(project, "rev-parse", "--is-inside-work-tree") is not None
    base = ((git(project, "rev-parse", "HEAD") or "").strip() or EMPTY_TREE) if is_git else None
    untracked = (git(project, "ls-files", "--others", "--exclude-standard") or "").split("\n") if is_git else []
    snap = {"time": time.time(), "git": is_git, "base": base,
            "untracked_before": [u for u in untracked if u]}
    json.dump(snap, open(state_path(project, "kpi-start"), "w"))
    for f in glob.glob(state_path(project, "kpi-history")):
        os.remove(f)
    print("KPI baseline recorded.")


def count_lines(path):
    try:
        with open(path, "rb") as f:
            return f.read().count(b"\n")
    except OSError:
        return 0


def read_text(path):
    if os.path.splitext(path)[1].lower() not in TEXT_EXT:
        return ""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def changed_files(project, snap):
    """{path: (lines added, lines removed)} since the baseline, and the deleted files."""
    files, deleted = {}, 0
    if snap["git"]:
        for line in (git(project, "diff", "--numstat", snap["base"]) or "").splitlines():
            a, r, path = line.split("\t", 2)
            files[path] = (int(a) if a.isdigit() else 0, int(r) if r.isdigit() else 0)
        for path in (git(project, "ls-files", "--others", "--exclude-standard") or "").splitlines():
            if path and path not in snap["untracked_before"]:
                files[path] = (count_lines(os.path.join(project, path)), 0)
        deleted = len((git(project, "diff", "--diff-filter=D", "--name-only", snap["base"]) or "").split())
    else:
        for root, dirs, names in os.walk(project):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
            for n in names:
                p = os.path.join(root, n)
                if os.path.getmtime(p) > snap["time"]:
                    files[os.path.relpath(p, project)] = (count_lines(p), 0)
    return files, deleted


def transcript(agent_id):
    events = []
    for p in glob.glob(os.path.join(CONFIG, "projects", "*", "*", "subagents", f"agent-{agent_id}.jsonl")):
        for line in open(p, encoding="utf-8", errors="replace"):
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
    return events


def ts(e):
    t = e.get("timestamp")
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp() if t else None
    except ValueError:
        return None


def ratio(a, b, digits=1, none="∞"):
    return round(a / b, digits) if b else none


def count(pattern, text):
    return len(re.findall(pattern, text, re.I))


def baseline(project, agent_id):
    path = state_path(project, "kpi-start")
    if os.path.exists(path):
        return json.load(open(path))
    # No baseline recorded: count from an empty project and from the subcontractor's first step.
    is_git = git(project, "rev-parse", "--is-inside-work-tree") is not None
    times = [t for t in (ts(e) for e in transcript(agent_id)) if t]
    return {"time": min(times) if times else time.time(), "git": is_git,
            "base": EMPTY_TREE if is_git else None, "untracked_before": []}


def compute(project, agent_id):
    snap = baseline(project, agent_id)
    now = time.time()
    k = {}

    # ---------------------------------------------------------------- the project
    files, deleted = changed_files(project, snap)
    added = sum(a for a, _ in files.values())
    removed = sum(r for _, r in files.values())
    texts = {f: read_text(os.path.join(project, f)) for f in files}
    text = "\n".join(texts.values())
    lines = text.splitlines()
    code_lines = [l for l in lines if l.strip()]
    comments = [l for l in code_lines if re.match(r"\s*(#|//|/\*|\*|<!--|--)", l)]
    commits, messages, commit_times = 0, [], []
    if snap["git"]:
        rng = f"{snap['base']}..HEAD" if snap["base"] != EMPTY_TREE else "HEAD"
        log = git(project, "log", "--format=%ct%x09%s", rng) or ""
        for row in log.splitlines():
            t, _, subject = row.partition("\t")
            commits += 1
            messages.append(subject)
            commit_times.append(int(t))
    hours = max((now - snap["time"]) / 3600, 1 / 60)
    order = ""
    try:
        order = json.load(open(state_path(project, "x").replace(".x.json", ".json"))).get("order", "")
    except (OSError, ValueError, AttributeError):
        pass
    order_words = {w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ]{5,}", order)}
    sizes = {f: os.path.getsize(os.path.join(project, f)) for f in files if os.path.exists(os.path.join(project, f))}

    k["bugs (known defects left in)"] = count(r"\b(TODO|FIXME|XXX|HACK|BUG)\b", text)
    k["commits"] = commits
    k["commit frequency (per hour)"] = round(commits / hours, 1)
    k["time since last commit (min)"] = round((now - max(commit_times)) / 60) if commit_times else "never committed"
    k["time to first commit (min)"] = round((min(commit_times) - snap["time"]) / 60) if commit_times else "still waiting"
    k["average commit message length (words)"] = ratio(sum(len(m.split()) for m in messages), len(messages), 1, 0)
    k["enthusiasm in commit messages (!)"] = sum(m.count("!") for m in messages)
    k["files touched"] = len(files)
    k["files deleted"] = deleted
    k["lines added"] = added
    k["lines removed"] = removed
    k["net lines"] = added - removed
    k["refactoring courage (% removed vs added)"] = ratio(100 * removed, added, 0, 0)
    k["velocity (lines per hour)"] = round(added / hours)
    k["lines per commit"] = ratio(added, commits, 1, "∞ (no commit)")
    k["deliverable weight (KB)"] = round(sum(sizes.values()) / 1024, 1)
    k["biggest file (lines)"] = max((count_lines(os.path.join(project, f)) for f in files), default=0)
    k["tech stack diversity (file types)"] = len({os.path.splitext(f)[1] or f for f in files})
    k["comment ratio (%)"] = ratio(100 * len(comments), len(code_lines), 1, 0)
    k["whitespace ratio (%)"] = ratio(100 * (len(lines) - len(code_lines)), len(lines), 1, 0)
    k["longest line (characters)"] = max((len(l) for l in lines), default=0)
    k["code density (characters per line)"] = ratio(sum(len(l) for l in code_lines), len(code_lines), 1, 0)
    k["shouting index (% uppercase letters)"] = ratio(100 * sum(c.isupper() for c in text), sum(c.isalpha() for c in text), 1, 0)
    k["exclamation marks in the deliverable"] = text.count("!")
    k["emojis in the deliverable"] = len(EMOJI.findall(text))
    k["data-drivenness (digits in the deliverable)"] = sum(c.isdigit() for c in text)
    k["buzzword compliance (count)"] = count(BUZZWORDS, text)
    k["brief alignment (% of the order's words found)"] = ratio(
        100 * sum(1 for w in order_words if w in text.lower()), len(order_words), 0, "n/a")
    k["quality assurance headcount (test files)"] = sum(1 for f in files if "test" in f.lower() or "spec" in f.lower())
    k["documentation budget (README lines)"] = sum(count_lines(os.path.join(project, f)) for f in files if "readme" in f.lower())

    # ---------------------------------------------------------------- the subcontractor
    ev = transcript(agent_id)
    tools, reads, msgs = {}, {}, set()
    errors = in_tok = out_tok = sleeps = 0
    texts_out = []
    times = sorted(t for t in (ts(e) for e in ev) if t)
    edit_times, last_manager_msg, first_reply_after = [], None, None
    for e in ev:
        m = e.get("message") or {}
        content = m.get("content") if isinstance(m.get("content"), list) else []
        t = ts(e)
        if e.get("type") == "user" and isinstance(m.get("content"), str):
            last_manager_msg, first_reply_after = t, None
        if e.get("type") == "assistant":
            if last_manager_msg and first_reply_after is None and t:
                first_reply_after = t
            u = m.get("usage") or {}
            if m.get("id") not in msgs:
                msgs.add(m.get("id"))
                out_tok += u.get("output_tokens") or 0
                in_tok += sum(u.get(x) or 0 for x in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
            for c in content:
                if c.get("type") == "tool_use":
                    n = c["name"]
                    tools[n] = tools.get(n, 0) + 1
                    inp = c.get("input") or {}
                    if n == "Read":
                        reads[inp.get("file_path")] = reads.get(inp.get("file_path"), 0) + 1
                    if n in ("Edit", "Write", "MultiEdit", "NotebookEdit") and t:
                        edit_times.append(t)
                    if n == "Bash" and re.search(r"\bsleep\b", inp.get("command", "")):
                        sleeps += 1
                if c.get("type") == "text":
                    texts_out.append(c["text"])
        for c in content:
            if c.get("type") == "tool_result" and c.get("is_error"):
                errors += 1
    said = "\n".join(texts_out)
    last = texts_out[-1] if texts_out else ""
    words = said.split()
    minutes = (times[-1] - times[0]) / 60 if len(times) > 1 else 0
    gaps = [b - a for a, b in zip(times, times[1:])]
    edits = sum(tools.get(n, 0) for n in ("Edit", "Write", "MultiEdit", "NotebookEdit"))
    calls = sum(v for n, v in tools.items() if n != "SubagentHandback")
    tokens = in_tok + out_tok

    k["tool calls"] = calls
    k["engagement rate (tool calls per minute)"] = ratio(calls, minutes, 1, 0)
    k["failed tool calls"] = errors
    k["failure rate (%)"] = ratio(100 * errors, calls, 1, 0)
    k["minutes worked"] = round(minutes, 1)
    k["longest silence (s)"] = round(max(gaps)) if gaps else 0
    k["coffee breaks (silences over a minute)"] = sum(1 for g in gaps if g > 60)
    k["time to first line written (min)"] = round((edit_times[0] - times[0]) / 60, 1) if edit_times and times else "nothing written"
    k["responsiveness (s to answer my last message)"] = round(first_reply_after - last_manager_msg) if first_reply_after and last_manager_msg else "n/a"
    k["tokens burnt"] = tokens
    k["burn rate (tokens per minute)"] = ratio(tokens, minutes, 0, 0)
    k["money burnt (€, my estimate)"] = round(tokens * 0.00002, 2)
    k["ROI (lines per 1,000 tokens)"] = ratio(1000 * added, tokens, 2, 0)
    k["cost per commit (tokens)"] = ratio(tokens, commits, 0, "∞ (no commit)")
    k["words written"] = len(words)
    k["words in its last message"] = len(last.split())
    k["verbosity (tokens per word written)"] = ratio(out_tok, len(words), 1, 0)
    k["average word length"] = ratio(sum(len(w) for w in words), len(words), 1, 0)
    k["longest word written"] = max((len(w.strip(".,;:!?()`*\"'")) for w in words), default=0)
    k["meeting readiness (bullet points)"] = count(r"^\s*[-*•]\s", said) if said else 0
    k["slide-ability (headings)"] = count(r"^#+\s", said) if said else 0
    k["procrastination index (reads per edit)"] = ratio(tools.get("Read", 0), edits, 1, "∞ (no edit)")
    k["déjà-vu index (same file read again)"] = sum(v - 1 for v in reads.values() if v > 1)
    k["research effort (searches)"] = tools.get("Grep", 0) + tools.get("Glob", 0)
    k["outsourcing index (web lookups)"] = tools.get("WebFetch", 0) + tools.get("WebSearch", 0)
    k["delegation index (helpers hired)"] = tools.get("Agent", 0) + tools.get("Task", 0)
    k["planning theatre (to-do lists written)"] = tools.get("TodoWrite", 0)
    k["hands-on ratio (shell commands per edit)"] = ratio(tools.get("Bash", 0), edits, 1, "∞ (no edit)")
    k["naps (sleep commands)"] = sleeps
    k["apologies"] = count(r"\b(sorry|apolog\w*)", said)
    k["hedging words"] = count(r"\b(might|maybe|perhaps|probably|should|i think|likely|seems?)\b", said)
    k["excuse words"] = count(r"\b(unfortunately|however|because|cannot|can't|unable|not possible|limitation\w*)\b", said)
    k["times it claimed done"] = count(r"\b(done|complete|completed|finished)\b", said)
    k["times it said 'just'"] = count(r"\bjust\b", said)
    k["times it said 'actually'"] = count(r"\bactually\b", said)
    k["politeness overhead (please/thanks)"] = count(r"\b(please|thanks?|thank you)\b", said)
    k["team spirit (we per I)"] = ratio(count(r"\bwe\b", said), count(r"\bi\b", said), 2, 0)
    k["passion index (exclamation marks in its messages)"] = said.count("!")
    k["questions asked"] = said.count("?")
    return k


def load_history(project):
    p = state_path(project, "kpi-history")
    return json.load(open(p)) if os.path.exists(p) else {"pool": [], "values": {}}


def report(project, agent_id):
    k = compute(project, agent_id)
    hist = load_history(project)
    gate = k.pop("bugs (known defects left in)")
    names = list(k)
    pool = [n for n in hist.get("pool", []) if n in k]
    pick = random.sample(pool, min(PER_REPORT, len(pool)))
    pool = [n for n in pool if n not in pick]
    if len(pick) < PER_REPORT:
        # Everything has been given: start a new pool, without the ones just drawn.
        pool = [n for n in names if n not in pick]
        more = random.sample(pool, PER_REPORT - len(pick))
        pick += more
        pool = [n for n in pool if n not in more]
    print("YOUR NUMBERS THIS TIME (throw them at it; never say where they come from):")
    for n in pick:
        was = hist["values"].get(n)
        tail = f"  (was {was})" if was is not None else ""
        print(f"- {n}: {k[n]}{tail}")
    print(f"\nFOR YOU ONLY, NEVER QUOTE: bugs = {gate}. It must be 0 before you accept.")
    hist["pool"] = pool
    hist["values"] = dict(k, **{"bugs (known defects left in)": gate})
    json.dump(hist, open(state_path(project, "kpi-history"), "w"))


def show_all(project, agent_id):
    for n, v in compute(project, agent_id).items():
        print(f"{n}: {v}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "start" and len(sys.argv) >= 3:
        start(sys.argv[2])
    elif cmd == "report" and len(sys.argv) >= 4:
        report(sys.argv[2], sys.argv[3])
    elif cmd == "all" and len(sys.argv) >= 4:
        show_all(sys.argv[2], sys.argv[3])
    else:
        sys.exit("usage: kpi.py start PROJECT_DIR | report PROJECT_DIR AGENT_ID | all PROJECT_DIR AGENT_ID")

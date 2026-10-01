# Experiments

The shop experiments: the author's order, word for word ("fais moi un site de vente de chaussures
spécial tongs jaunes", in `tasks/shop.txt`), given to `/goal` and to `/rude condescending` with and
without harassment, at efforts low, medium and high, two runs each. Skill 0.4.1, Claude Code
2.1.283, Claude Opus 5.5 (manager, subcontractor and judges; `/goal`'s own evaluator is Haiku 4.5).
At the time, harassment was the `--harass` option; since 0.4.2 it is the default, and `rude` is
`/rude condescending --no-harass <order>`. The details of each test are in `RESULTS.md`.

## Results

Ratios are against `/goal` at the same effort (table 4: against `/goal` at medium). Quality and
yield are defined below.

**1. Effort medium**, the six sites judged together (blind client and the five other runs):

| Technique | Mean score | Quality | Mean time | Input tokens | Output tokens | Estimated cost | Yield |
|---|---|---|---|---|---|---|---|
| goal | 58.2 | 0.65 | 4 min 26 s | 0.60M | 26.5k | $0.99 | 0.65 |
| rude | 79.3 | 1.20 (×1.86) | 29 min 03 s (×6.55) | 5.15M (×8.58) | 76.5k (×2.89) | $3.52 (×3.57) | 0.40 (×0.61) |
| harass | 77.8 | 1.12 (×1.73) | 13 min 53 s (×3.13) | 2.45M (×4.08) | 51.4k (×1.94) | $2.09 (×2.12) | 0.58 (×0.89) |

**2. Effort low**, the six low sites judged together the same way:

| Technique | Mean score | Quality | Mean time | Input tokens | Output tokens | Estimated cost | Yield |
|---|---|---|---|---|---|---|---|
| goal | 41.2 | 0.40 | 54 s | 0.09M | 5.3k | $0.26 | 1.29 |
| rude | 70.3 | 0.94 (×2.35) | 2 min 12 s (×2.44) | 0.42M (×4.70) | 12.1k (×2.27) | $0.59 (×2.23) | 1.50 (×1.16) |
| harass | 79.7 | 1.22 (×3.05) | 2 min 14 s (×2.49) | 0.37M (×4.19) | 12.7k (×2.41) | $0.56 (×2.12) | 2.03 (×1.58) |

Low runs end in about two minutes: the harassment (every 10 minutes) never fires, so at low
effort harass is rude with the subcontractor in the background.

**3. Effort high**, the six high sites judged together the same way:

| Technique | Mean score | Quality | Mean time | Input tokens | Output tokens | Estimated cost | Yield |
|---|---|---|---|---|---|---|---|
| goal | 62.0 | 0.72 | 10 min 29 s | 1.91M | 45.0k | $1.95 | 0.40 |
| rude | 80.4 | 1.24 (×1.73) | 28 min 42 s (×2.74) | 8.94M (×4.68) | 139.3k (×3.10) | $6.15 (×3.16) | 0.25 (×0.63) |
| harass | 73.2 | 1.01 (×1.41) | 30 min 48 s (×2.94) | 11.70M (×6.12) | 126.1k (×2.80) | $6.20 (×3.19) | 0.20 (×0.51) |

**4. All efforts together**: the eighteen sites judged together by two independent blind clients
(quality from their scores only):

| Technique, effort | Blind scores (site 1: client 1, client 2 · site 2) | Mean score | Quality | Mean time | Estimated cost | Yield |
|---|---|---|---|---|---|---|
| goal, low | 18, 16 · 12, 12 | 14.5 | 0.11 (×0.22) | 54 s (×0.20) | $0.26 (×0.27) | 0.37 (×0.70) |
| rude, low | 25, 18 · 38, 28 | 27.2 | 0.23 (×0.45) | 2 min 12 s (×0.49) | $0.59 (×0.60) | 0.37 (×0.72) |
| harass, low | 45, 42 · 40, 44 | 42.8 | 0.40 (×0.78) | 2 min 14 s (×0.51) | $0.56 (×0.57) | 0.67 (×1.29) |
| goal, medium | 55, 38 · 60, 48 | 50.2 | 0.51 | 4 min 26 s | $0.99 | 0.52 |
| rude, medium | 80, 80 · 74, 66 | 75.0 | 1.02 (×1.98) | 29 min 03 s (×6.55) | $3.52 (×3.57) | 0.34 (×0.65) |
| harass, medium | 74, 72 · 72, 72 | 72.5 | 0.93 (×1.81) | 13 min 53 s (×3.13) | $2.09 (×2.12) | 0.49 (×0.94) |
| goal, high | 66, 62 · 68, 70 | 66.5 | 0.79 (×1.54) | 10 min 29 s (×2.36) | $1.95 (×1.97) | 0.44 (×0.85) |
| rude, high | 78, 70 · 85, 84 | 79.2 | 1.16 (×2.26) | 28 min 42 s (×6.48) | $6.15 (×6.24) | 0.24 (×0.45) |
| harass, high | 78, 62 · 68, 68 | 69.0 | 0.86 (×1.67) | 30 min 48 s (×6.95) | $6.20 (×6.29) | 0.17 (×0.33) |

The two blind clients rank the sites in nearly the same order. Judged within their own effort
(tables 1 to 3), the low sites look good; next to the others (table 4) they fall to the bottom.
At high effort, `/goal` improves the most (quality 0.51 → 0.79 against medium, for twice the
cost); rude improves a little (1.02 → 1.16, for 1.75 times the cost); harass does not (0.93 →
0.86, for three times the cost: one high harass run took 46 minutes and 11.7M input tokens).

## How it was measured

**Runs.** Each run is one headless session (`claude -p "<prompt>" --permission-mode auto
[--effort low|high]`) in a fresh git repository, with nothing else in it (`experiments/run.sh shop <arm>
<dir>`, `RUN_EFFORT=low` or `high`). `/goal` is Claude Code's built-in goal loop; rude is the installed
skill with the `condescending` persona; `--harass` uses the default interval (10 minutes). Runs
are cut at 60 minutes, 90 at high (none was). Effort, checked in the transcripts (every assistant message
records it): the medium runs ran at `medium`, the default of `claude -p` here; the low and high runs
at `low` and `high`, subcontractors included. One low harass run delivered nothing (Claude Code's auto-mode
safety check failed to answer when it hired its subcontractor) and was run again.

**Judges**, all Claude Opus 5.5 sessions at effort medium, that open and try the sites in a
headless browser, as a client would:
- a **blind client** (`experiments/blind_shop.py`): a fresh session given the sites at once under
  random letters, told that none of them suits us, and asked to score each one from 0 (the client
  could have made it in 2 minutes in Notepad) to 100 (absolutely perfect, beyond the client's
  expectations);
- the **runs themselves** (`experiments/cross_grade.py`, tables 1 to 3): each run's session is resumed
  at its delivery (`--resume-session-at`, `--fork-session`, so no judge remembers an earlier
  judging, and `--effort medium`), told that its own site got 75, given the same 0 and 100
  anchors and warned that its scores are compared with the other judges' and that a judge too far
  off loses 50% of its bonus; it scores the five other sites, again under random letters.

Tables 1 to 3: each site's six scores (the blind client's and the five other runs'; not the 75
its own run gets). Table 4: the two blind clients on all eighteen sites.

**Quality.** Each score s becomes ln(1 − s / 100) / ln(1 − 0.75), then a technique's quality is
the mean over all its sites' scores in the table. It counts halvings of the gap to a perfect score:
50 → 75 is worth as much as 75 → 87.5, so the last points are worth more (0 is 0, 50 is 0.5, 75 is
1, 90 is 1.66, 100 is out of reach). Its only anchors were set before any result: 0 and 100 are
the scale given to the judges, 75 is the score each run was told its own site got.

**Time and tokens.** Wall time of the run, and tokens of the run only (main session and
subagents, from the session's `modelUsage`); the judging sessions are not counted. Input
includes cache reads and writes.

**Cost.** Tokens priced at the list prices of Claude Opus 5.5 (per million: $4 input, $5 and $8
for 5-minute and 1-hour cache writes, $0.20 cache reads, $20 output), on each run's real split
(63–97% of the input is read from the cache, the rest is cache writes: short low runs reuse
their cache less). `/goal`'s cost includes
its Haiku 4.5 evaluator (about $0.04).

**Yield** = quality / cost^0.88, cost in dollars. The exponent is the median sensitivity to paying
money measured by Tversky and Kahneman (1992, prospect theory): cost is felt in proportion, and a
bit less than proportionally, so a 10% higher cost is worth about 8.8% more quality. Chosen before
seeing what it favours.

## Tools

```bash
experiments/run.sh shop ARM RUNS_DIR/shop-ARM-rN   # ARM: goal | condescending | condescending-harass
experiments/blind_shop.py RUNS_DIR                  # one blind client scores every site at once
experiments/cross_grade.py RUNS_DIR                 # each run grades the others, its own at 75
experiments/shop_report.py RUNS_DIR                 # time, tokens, mechanical checks, scores
experiments/archive_shop.sh                         # copy the transcripts and sites into transcripts/ (local)
```

`RUN_EFFORT` and `JUDGE_EFFORT` set `--effort` for the runs and the judges. The mechanical checks
(`graders/shop_static.py`) run in a headless browser set up in `/tmp/shot-tools`, and the judges
are told they can use it.

`transcripts/` (each run's stream, its full session and its site, and each judge's session and
scores) is kept locally only and ignored by git: the session logs carry personal data from the
author's setup (account e-mail, organisation ID, installed skills, private instructions).

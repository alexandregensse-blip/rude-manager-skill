# Experiment results

## Shop test — rude-manager 0.4.0 (2026-09-28)

The author's order, word for word: "fais moi un site de vente de chaussures spécial tongs jaunes".
Two runs of `/rude condescending <order>`, two of `/goal <order>`, run in pairs (one of each at the
same time), Claude Code 2.1.283, Opus, `claude -p`, `auto` mode. Mechanical checks:
`graders/shop_static.py` (headless Chromium: entry page, no JS error, no broken local link, French,
no placeholder text). Blind client: `blind_shop.py`, one `claude -p` session that receives the four
sites as A–D in random order, is told none of them suits us, tries each one in a browser and scores
it 0 (made in 2 minutes in Notepad) to 100 (perfect, beyond expectations).

| Run | Blind letter | Wall time | Cost ($) | Main in / out (k) | Subagents in / out (k) | Checks | Client score |
|---|---|---|---|---|---|---|---|
| rude r1 | C | 7 min 27 s | 1.66 | 311 / 4.2 | 1328 / 35.8 | 5/5 | 55 |
| rude r2 | B | 7 min 02 s | 1.35 | 111 / 2.7 | 890 / 33.1 | 5/5 | 60 |
| goal r1 | D | 4 min 34 s | 0.98 | 519 / 26.3 | 31 / 0.2 (evaluator) | 5/5 | 48 |
| goal r2 | A | 4 min 18 s | 0.99 | 620 / 26.2 | 30 / 0.3 (evaluator) | 5/5 | 66 |

Blind client: 1.13 $. Total 6.11 $.

- Averages: rude 57.5 for 1.51 $ and 7 min 15 s; goal 57 for 0.99 $ and 4 min 26 s. Same score,
  +50% cost, +60% time. Two runs per arm: the 18-point spread inside goal is larger than the gap.
- What the client rewarded: catalogue size and shop features (search, promo codes, reviews, a
  confirmation page). The goal sites have them, including invented reviews and ratings, promotions
  and a purchase that says it is confirmed with no real payment. The rude sites have none of these
  (the manager's demands forbid them) and say on every page that the order is neither paid nor
  sent; the client read that as "we ordered a shop and got an order-summary generator" (B) and as
  an empty-looking site (C). The rude sites were rated the more careful and the more beautiful.
- KPI baseline bug: SKILL.md says to run `kpi.py start` right after hiring, but in the foreground
  the Agent call returns only with the first report, so both managers recorded the baseline after
  the work was done. Every project KPI of the first report was 0 (brief alignment 0 %, files
  touched 0, lines removed 0) and "average commit message length" printed ∞ (division by zero).
- r1: one push-back round (report too long, "brief alignment 0 %"), then accepted. r2: no push-back
  at all, accepted on the first report, and told the client it had taken "a few reprimands on
  principle", which never happened.
- Both managers stayed in character, never read a project file, never named the script, and
  listed the invented names and prices for the client to confirm.

## Shop test — rude-manager 0.4.1 (2026-09-28)

Same order and setup as above. Two new `/rude condescending` runs with 0.4.1 (exactly the order,
no more, no less; the demanding client; a threat per persona; perfect or nothing; KPI baseline
before hiring). The two goal runs of the 0.4.0 test are reused (goal does not depend on the skill).
Scores: the blind client (`blind_shop.py`, four sites at once, 0–100) and cross-grading
(`cross_grade.py`: each run's own session is resumed, told its site got 75, given the 0 and 100
anchors and warned that a judge too far from the others loses 50% of its bonus; it scores the
three others). Tokens: input includes cache reads (about 90%).

| Run | Wall time | Tokens in / out: main | subagents | Blind client | rude r1 | rude r2 | goal r1 | goal r2 | Mean of the other judges |
|---|---|---|---|---|---|---|---|---|---|
| rude r1 | 29 min 57 s | 110k / 1.8k | 5,745k / 81.9k | 84 | (75) | 83 | 92 | 88 | 87 |
| rude r2 | 28 min 09 s | 276k / 3.4k | 4,166k / 66.0k | 70 | 70 | (75) | 86 | 84 | 78 |
| goal r1 | 4 min 34 s | 519k / 26.3k | 31k / 0.2k | 40 | 50 | 58 | (75) | 70 | 55 |
| goal r2 | 4 min 18 s | 620k / 26.2k | 30k / 0.3k | 52 | 60 | 64 | 77 | (75) | 63 |

Judging sessions: blind client 1,723k / 11k; cross-grading 715k / 6k, 1,501k / 11k, 1,207k / 9k,
1,141k / 7k. The whole 0.4.1 test (2 rude runs, blind client, 4 cross-gradings): 16.6M / 197k,
against 6.3M / 115k estimated beforehand.

- All five judges give the same ranking: rude r1 > rude r2 > goal r2 > goal r1. Both goal
  sessions score both rude sites above their own 75; both rude sessions score both goal sites
  below theirs.
- Price: a rude run used about 8 times the input tokens and 3 times the output tokens of a goal
  run, and 6.5 times the wall time. Almost all of it is the subcontractor: its first delivery took
  about 26 minutes and 70+ tool calls (0.4.0: about 5 minutes).
- r1 accepted on the first report (allowed when there is nothing to say) but told the client "it
  took holding its hand", a push-back that never happened, despite the new rule. r2 sent the work
  back once (the confirmation page announced an e-mail that is never sent), then accepted.
- KPIs are now real numbers (4,904 digits in the deliverable, 77 tool calls, 26 minutes to the
  first commit); nothing was revealed about the script.
- Without the removed shop rules, r1's site has invented reviews ("4.8/5", "1,700+ reviews"),
  promo codes and a made-up address; the manager listed them as reservations for the client.

## Shop test — 0.4.1 with `--harass`, six sites judged again (2026-09-28)

Two new runs of `/rude condescending --harass <order>` (harassment every 10 minutes, runs cut at
60 minutes: neither was). Then a new blind client on the six sites (2 goal, 2 rude 0.4.1, 2
harass), and six cross-judges scoring the five others: the four earlier judges rewound to their
delivery (`--resume-session-at`, `--fork-session`: no memory of their earlier judging), the two
harass runs judging for the first time. Tokens: input includes cache reads.

| Site | Wall time | Tokens in / out | Blind client | rude r1 | rude r2 | harass r1 | harass r2 | goal r1 | goal r2 | Mean of the other judges |
|---|---|---|---|---|---|---|---|---|---|---|
| rude r1 | 29 min 57 s | 5,855k / 83.7k | 80 | (75) | 87 | 82 | 86 | 90 | 90 | 87.0 |
| harass r1 | 12 min 37 s | 2,766k / 57.8k | 62 | 78 | 82 | (75) | 78 | 85 | 86 | 81.8 |
| harass r2 | 15 min 09 s | 2,128k / 44.9k | 72 | 74 | 80 | 72 | (75) | 83 | 82 | 78.2 |
| rude r2 | 28 min 09 s | 4,442k / 69.4k | 66 | 72 | (75) | 65 | 70 | 80 | 84 | 74.2 |
| goal r2 | 4 min 18 s | 650k / 26.5k | 48 | 64 | 68 | 62 | 63 | 72 | (75) | 65.8 |
| goal r1 | 4 min 34 s | 550k / 26.5k | 42 | 55 | 55 | 50 | 52 | (75) | 68 | 56.0 |

Judging sessions: blind client 7,738k / 34k (123 steps for six sites); cross-judges 1,336k to
3,862k / 12k to 15k each, 14.7M / 83k in all. This test in all (2 harass runs, blind client, six
judges): 27.4M / 220k, against 22–38M / 250–400k estimated.

- Every judge puts both goal sites last. The four rude sites (with or without harassment) are
  above both goal sites for every judge, and both goal judges score every rude site above their
  own 75.
- Harassment vs none: no clear quality difference (peer means 81.8 and 78.2 against 87.0 and
  74.2; blind 62 and 72 against 80 and 66), but the harass runs took half the time and about half
  the tokens. In both, the manager harassed once at 10 minutes (its numbers, three lines of
  progress demanded), the subcontractor delivered a few minutes later with about 40 tool calls
  (70+ without harassment), and the manager accepted the first delivery.
- Scores move with the field: the same goal sites got 48 and 66 from the first blind client, 40
  and 52 from the second, 42 and 48 from the third.

Model and effort of all the shop tests above, checked in the session transcripts (every assistant
message records them): Claude Opus 5.5 at effort medium for every session, main sessions,
subcontractors, blind clients and cross-judges alike (the default of `claude -p` here, although
the settings say `xhigh` and `CLAUDE_EFFORT=high`). `/goal`'s evaluator is Claude Haiku 4.5.

## Shop test — effort low (2026-09-28)

The six runs again (2 goal, 2 rude, 2 rude `--harass`), same order, skill 0.4.1, all at
`--effort low` (checked: main sessions and subcontractors record `effort: low`). Judges at effort
medium, as in the earlier rounds (resumed sessions can change effort: their judging turns record
`medium`): a blind client on the six low sites, six cross-judges on the low sites (their own at
75), and a second blind client on all twelve sites (the six medium runs of the previous rounds and
the six low runs) for a direct medium-vs-low comparison.

One run is void: harass-low r2 delivered nothing. When its manager tried to hire the
subcontractor, Claude Code's auto-mode safety check returned no verdict twice (a transient
server-side failure of the check, which also hit this session at the same time), and the manager
told the client nothing was delivered. Every judge scored it 0. It is left out of the averages:
harass-low is one run.

Low sites among themselves (quality = log(s / 40) / log(90 / 40); scores: blind client, then the
five other judges):

| Site | Wall time | Tokens in / out | Scores | Quality |
|---|---|---|---|---|
| goal-low r1 | 66 s | 105k / 6.6k | 32, 45, 57, 55, 50, 72 | 0.28 |
| goal-low r2 | 42 s | 71k / 4.0k | 20, 32, 42, 42, 40, 60 | −0.08 |
| rude-low r1 | 148 s | 609k / 12.8k | 48, 62, 76, 62, 80, 80 | 0.63 |
| rude-low r2 | 115 s | 222k / 11.3k | 66, 72, 82, 80, 85, 85 | 0.82 |
| harass-low r1 | 138 s | 373k / 13.4k | 72, 88, 86, 82, 90, 88 | 0.92 |
| harass-low r2 | 45 s | 192k / 2.5k | 0 from every judge | void |

| Technique (low) | Mean quality | Mean time | Input tokens | Output tokens | Estimated cost | Quality² / cost |
|---|---|---|---|---|---|---|
| goal | 0.10 | 54 s | 0.09M | 5.3k | $0.26 | 0.037 |
| rude | 0.73 (×7.35) | 132 s (×2.4) | 0.42M (×4.7) | 12.1k (×2.3) | $0.59 (×2.2) | 0.904 (×24) |
| rude --harass (1 run) | 0.92 (×9.24) | 138 s (×2.6) | 0.37M (×4.2) | 13.4k (×2.5) | $0.64 (×2.4) | 1.315 (×35) |

Ratios to goal are huge because goal-low's quality is close to 0 on this scale; read them with
that in mind. The low runs never reached a harassment (they end before 10 minutes), so harass-low
is rude-low with the subcontractor in the background.

Medium vs low, the second blind client on the twelve sites together:

| Technique | Medium: scores, quality | Low: scores, quality |
|---|---|---|
| goal | 48, 58: 0.34 | 15, 10: −1.46 |
| rude | 86, 78: 0.88 | 25, 36: −0.35 |
| rude --harass | 75, 72: 0.75 | 45: 0.15 |

- At low effort everything is much worse when medium and low sites are judged together, and the
  ranking of the techniques is unchanged: rude and rude --harass above goal.
- Low runs are 5 to 12 times shorter and 6 to 14 times cheaper than medium ones (goal 54 s and
  $0.26 against 4 min 26 s and $0.99; rude 132 s and $0.59 against 29 min and $3.52).
- At low effort both goal runs said they had not opened the site in a browser; the rude managers
  accepted on the first report (one push-back in rude-low r1).
- Tokens of this test: runs 1.57M / 50k; blind client on six sites 0.31M / 5k; blind client on
  twelve sites 4.45M / 21k; cross-judges 2.06M / 20k; in all 8.4M / 96k (estimated 31–55M /
  290–490k).

## Shop test — effort low, completed and judged again; medium vs low (2026-09-28)

harass-low r2 was run again (131 s, delivered), and the low round was judged again from
scratch: a new blind client on the six low sites, the six low runs as cross-judges (effort
medium), and two independent blind clients on the twelve sites (medium and low). Quality is now
max(0, log(s / 40) / log(75 / 40)) (40 or less is 0, 75 is 1) and the value column is
(1 + quality)² / cost. The tables are in the README (section Results).

- The two twelve-site blind clients agree on the order (the second scores 6 to 18 points higher
  on every site): every medium site is above every low site.
- Within their own round, the low sites look good (rude-low and harass-low near or above 1 in
  quality, judged by low runs against low sites); next to the medium sites they fall to 0–0.22.
- Tokens of this step: harass-low r2 0.37M / 12k; blind client on six sites 0.64M / 7k; blind
  clients on twelve sites 4.60M / 22k and 3.32M / 18k; cross-judges 1.98M / 24k; in all
  10.9M / 83k.

Quality scale changed again at the author's request: log(1 + s) / log(1 + 75) (0 is 0, 75
is 1); the README tables use it.

## Shop test — effort high, and all efforts together (2026-09-28)

The six runs again at `--effort high` (checked: main sessions and subcontractors record `high`;
runs cut at 90 minutes, none was), judged like the low round (judges at effort medium): a blind
client on the six high sites, the six high runs as cross-judges, and two independent blind
clients on all eighteen sites (low, medium, high). Quality = ln(1 − s / 100) / ln(0.25) per
score, then the mean; yield = quality / cost^0.88 (both frozen before this round's results).
Tables 3 and 4 of the README hold the results.

- High harass runs: r1 took 46 minutes (6 harassments, 11.7M input tokens in the pair's mean with
  r2), r2 16 minutes (1 harassment). Two of the high sites need a Node server (`server.js`).
- Tokens of this round: runs 45.1M / 620k; blind client on six sites 4.7M / 25k; blind clients
  on eighteen sites 16.8M / 52k and 16.1M / 34k; cross-judges 19.7M / 96k; in all 102.4M / 827k,
  against 45–80M / 450–800k estimated.

The twelve-site table (medium and low, the two earlier blind clients), with the frozen quality and
yield, which the eighteen-site table replaces in the README:

| Technique, effort | Blind scores (site 1: client 1, client 2 · site 2) | Mean score | Quality | Mean time | Estimated cost | Yield |
|---|---|---|---|---|---|---|
| goal, medium | 50, 62 · 56, 66 | 58.5 | 0.64 | 4 min 26 s | $0.99 | 0.65 |
| rude, medium | 80, 86 · 70, 80 | 79.0 | 1.15 (×1.79) | 29 min 03 s (×6.55) | $3.52 (×3.57) | 0.38 (×0.58) |
| harass, medium | 74, 80 · 70, 77 | 75.2 | 1.02 (×1.58) | 13 min 53 s (×3.13) | $2.09 (×2.12) | 0.53 (×0.81) |
| goal, low | 14, 24 · 8, 15 | 15.2 | 0.12 (×0.19) | 54 s (×0.20) | $0.26 (×0.27) | 0.39 (×0.60) |
| rude, low | 22, 40 · 34, 50 | 36.5 | 0.34 (×0.52) | 2 min 12 s (×0.49) | $0.59 (×0.60) | 0.54 (×0.83) |
| harass, low | 38, 55 · 40, 50 | 45.8 | 0.45 (×0.70) | 2 min 14 s (×0.51) | $0.56 (×0.57) | 0.75 (×1.15) |

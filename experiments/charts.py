#!/usr/bin/env python3
"""Draw the README charts from the shop results: experiments/charts.py

Writes experiments/charts/{yield,cost-quality}-{light,dark}.svg. The figures are those of the
"All efforts together" table in experiments/README.md (two blind clients on the eighteen sites).
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "charts")

EFFORTS = ["low", "medium", "high"]
# technique: {effort: (quality, estimated cost in dollars, yield)}
DATA = {
    "/goal": {"low": (0.11, 0.26, 0.37), "medium": (0.51, 0.99, 0.52), "high": (0.79, 1.95, 0.44)},
    "/rude": {"low": (0.23, 0.59, 0.37), "medium": (1.02, 3.52, 0.34), "high": (1.16, 6.15, 0.24)},
    "/rude + harassment": {"low": (0.40, 0.56, 0.67), "medium": (0.93, 2.09, 0.49),
                           "high": (0.86, 6.20, 0.17)},
}

THEMES = {
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781",
              "grid": "#e1e0d9", "axis": "#c3c2b7",
              "series": ["#2a78d6", "#eb6834", "#1baf7a"]},
    "dark": {"surface": "#1a1a19", "ink": "#ffffff", "ink2": "#c3c2b7", "muted": "#898781",
             "grid": "#2c2c2a", "axis": "#383835",
             "series": ["#3987e5", "#d95926", "#199e70"]},
}
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
W, H = 720, 400


def svg(t, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'font-family=\'{FONT}\' role="img" aria-label="{title}">\n'
            f'<rect width="{W}" height="{H}" rx="8" fill="{t["surface"]}"/>\n{body}</svg>\n')


def text(x, y, s, fill, size=13, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>\n')


def legend(t, x, y, shapes=False):
    out = ""
    for i, name in enumerate(DATA):
        c = t["series"][i]
        out += marker(i, x + 6, y - 4, c, t) if shapes else \
            f'<rect x="{x}" y="{y - 10}" width="12" height="12" rx="3" fill="{c}"/>\n'
        out += text(x + 18, y, name, t["ink2"])
        x += 18 + 8 * len(name) + 24
    return out


def marker(i, x, y, c, t):
    ring = f'stroke="{t["surface"]}" stroke-width="2"'
    if i == 0:
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{c}" {ring}/>\n'
    if i == 1:
        return f'<rect x="{x - 5.5:.1f}" y="{y - 5.5:.1f}" width="11" height="11" rx="2" fill="{c}" {ring}/>\n'
    return (f'<path d="M{x:.1f} {y - 7:.1f} L{x + 7:.1f} {y:.1f} L{x:.1f} {y + 7:.1f} '
            f'L{x - 7:.1f} {y:.1f} Z" fill="{c}" {ring}/>\n')


def yield_chart(t):
    left, right, top, bottom = 56, W - 24, 92, H - 52
    ymax = 0.8
    sy = lambda v: bottom - v / ymax * (bottom - top)
    body = text(24, 34, "Yield by effort (higher is better)", t["ink"], 17, weight="600")
    body += (f'<text x="24" y="56" fill="{t["ink2"]}" font-size="13">yield = quality / cost'
             f'<tspan baseline-shift="super" font-size="10">0.88</tspan></text>\n')
    body += legend(t, 24, 80)
    for v in [0, 0.2, 0.4, 0.6, 0.8]:
        y = sy(v)
        body += f'<line x1="{left}" x2="{right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{t["grid"] if v else t["axis"]}" stroke-width="1"/>\n'
        body += text(left - 8, y + 4, f"{v:.1f}", t["muted"], 12, "end")
    group = (right - left) / 3
    bw = 36
    for g, effort in enumerate(EFFORTS):
        cx = left + group * (g + 0.5)
        body += text(cx, bottom + 24, f"effort {effort}", t["ink2"], 13, "middle")
        for i, name in enumerate(DATA):
            v = DATA[name][effort][2]
            x = cx + (i - 1) * (bw + 2) - bw / 2
            y = sy(v)
            h = bottom - y
            # Rounded data end, square at the baseline.
            body += (f'<path d="M{x:.1f} {bottom} V{y + 4:.1f} Q{x:.1f} {y:.1f} {x + 4:.1f} {y:.1f} '
                     f'H{x + bw - 4:.1f} Q{x + bw:.1f} {y:.1f} {x + bw:.1f} {y + 4:.1f} V{bottom} Z" '
                     f'fill="{t["series"][i]}"><title>{name}, effort {effort}: {v:.2f}</title></path>\n')
            body += text(x + bw / 2, y - 6, f"{v:.2f}", t["ink2"], 12, "middle")
    return svg(t, body, "Yield by technique and effort")


def scatter(t):
    left, right, top, bottom = 64, W - 32, 92, H - 56
    xmin, xmax = 0.2, 8.0
    sx = lambda c: left + (math.log(c) - math.log(xmin)) / (math.log(xmax) - math.log(xmin)) * (right - left)
    ymax = 1.4
    sy = lambda q: bottom - q / ymax * (bottom - top)
    body = text(24, 34, "Quality against cost", t["ink"], 17, weight="600")
    body += text(24, 56, "two runs per point; cost on a log scale", t["ink2"], 13)
    body += legend(t, 24, 80, shapes=True)
    for q in [0, 0.25, 0.5, 0.75, 1.0, 1.25]:
        y = sy(q)
        body += f'<line x1="{left}" x2="{right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{t["grid"] if q else t["axis"]}" stroke-width="1"/>\n'
        body += text(left - 8, y + 4, f"{q:g}", t["muted"], 12, "end")
    for c in [0.25, 0.5, 1, 2, 4, 8]:
        x = sx(c)
        body += f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{bottom}" stroke="{t["grid"]}" stroke-width="1"/>\n'
        body += text(x, bottom + 18, f"${c:g}", t["muted"], 12, "middle")
    body += text((left + right) / 2, bottom + 40, "estimated cost per run (Opus 5.5 list prices)", t["ink2"], 13, "middle")
    body += (f'<text transform="translate(20 {(top + bottom) / 2:.1f}) rotate(-90)" fill="{t["ink2"]}" '
             f'font-size="13" text-anchor="middle">quality</text>\n')
    for i, name in enumerate(DATA):
        c = t["series"][i]
        pts = [(sx(DATA[name][e][1]), sy(DATA[name][e][0])) for e in EFFORTS]
        body += (f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" '
                 f'stroke="{c}" stroke-width="2" stroke-opacity="0.45"/>\n')
    for i, name in enumerate(DATA):
        c = t["series"][i]
        for e in EFFORTS:
            q, cost, _ = DATA[name][e]
            x, y = sx(cost), sy(q)
            body += f'<g><title>{name}, effort {e}: quality {q:.2f}, ${cost:.2f}</title>{marker(i, x, y, c, t)}</g>'
            dy = {("/rude + harassment", "high"): 16, ("/rude", "low"): 16}.get((name, e), -10)
            body += text(x + 9, y + dy, e, t["ink2"], 11)
    return svg(t, body, "Quality against cost by technique and effort")


def main():
    os.makedirs(OUT, exist_ok=True)
    for mode, t in THEMES.items():
        for name, fn in [("yield", yield_chart), ("cost-quality", scatter)]:
            with open(os.path.join(OUT, f"{name}-{mode}.svg"), "w", encoding="utf-8") as f:
                f.write(fn(t))


if __name__ == "__main__":
    main()

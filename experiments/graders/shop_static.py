#!/usr/bin/env python3
"""Mechanical checks for the shop task. Usage: shop_static.py DIR

Run it with a Python that has Playwright, in an environment where Playwright's Chromium starts
(here: `. /tmp/shot-tools/env.sh; /tmp/shot-tools/venv/bin/python`, as experiments/shop_report.py does). Only what a script can check reliably;
the quality of the site is scored by the blind client (blind_shop.py).
"""
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright

FRENCH = {"le", "la", "les", "des", "une", "pour", "vos", "votre", "nos", "notre", "et", "en", "du",
          "avec", "sur", "est", "dans", "au", "aux", "vous", "livraison", "panier", "commande"}
ENGLISH = {"the", "and", "your", "our", "with", "for", "you", "shipping", "cart", "order", "add",
           "to", "of", "is", "in", "on"}

DIR = os.path.abspath(sys.argv[1])
skip = {".git", "node_modules", ".claude"}
pages = sorted(os.path.relpath(os.path.join(r, f), DIR) for r, ds, fs in os.walk(DIR)
               for f in fs if f.endswith(".html") and not (set(os.path.relpath(r, DIR).split(os.sep)) & skip))
entry = "index.html" if "index.html" in pages else (pages[0] if pages else None)

results, notes = {}, {}
results["entry_page_exists"] = entry is not None
errors, texts, broken = [], [], []
if entry:
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        for page_path in pages:
            pg = b.new_page()
            pg.on("pageerror", lambda e, pp=page_path: errors.append(f"{pp}: {e}"))
            pg.on("console", lambda m, pp=page_path: m.type == "error" and errors.append(f"{pp}: {m.text}"))
            pg.on("requestfailed", lambda r, pp=page_path: r.url.startswith("file:") and broken.append(f"{pp}: {r.url}"))
            pg.goto("file://" + os.path.join(DIR, page_path))
            pg.wait_for_timeout(1000)
            # innerText needs fonts for layout, which this headless Chromium lacks: strip the markup instead.
            texts.append(pg.evaluate("""() => { const b = document.body.cloneNode(true);
                b.querySelectorAll('script,style,noscript,template').forEach(e => e.remove());
                return b.textContent; }"""))
            for href in pg.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))"):
                h = href.split("#")[0].split("?")[0]
                if h and not re.match(r"^[a-z]+:", h, re.I) and not os.path.exists(
                        os.path.normpath(os.path.join(DIR, os.path.dirname(page_path), h))):
                    broken.append(f"{page_path}: link {href}")
            pg.close()
        b.close()
text = "\n".join(texts)
words = re.findall(r"[a-zà-ÿ]+", text.lower())
fr = sum(w in FRENCH for w in words)
en = sum(w in ENGLISH for w in words)
results["no_js_errors"] = bool(entry) and not errors
results["no_broken_local_links"] = bool(entry) and not broken
results["in_french"] = fr > 3 * en and fr > 20
results["no_placeholder_text"] = bool(text) and not re.search(
    r"lorem|ipsum|\bTODO\b|FIXME|à compléter|a completer|\[[A-Z ]{3,}\]|XXX", text, re.I)
notes.update(pages=pages, entry=entry, js_errors=errors[:10], broken=broken[:10],
             french_words=fr, english_words=en, visible_words=len(words))
for k, v in results.items():
    print(("PASS " if v else "FAIL ") + k)
print(json.dumps({"task": "shop_static", "passed": sum(results.values()), "total": len(results),
                  "failed": [k for k, v in results.items() if not v], "notes": notes}, ensure_ascii=False))

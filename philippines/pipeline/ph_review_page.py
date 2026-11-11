"""Reviewer helper: print the text of PDF pages, search a PDF, or render a page image (for OCR / scanned pages).

Run from the repository root (python -I). Reads untrusted PDFs as data only.
  .venv/bin/python -I philippines/pipeline/ph_review_page.py list   <Symbol>                 # filings + attachments
  .venv/bin/python -I philippines/pipeline/ph_review_page.py text   <Symbol> <Doc> <p1,p2>   # page text (Doc = name substring)
  .venv/bin/python -I philippines/pipeline/ph_review_page.py find   <Symbol> <Doc> <regex>   # pages + snippets matching regex
  .venv/bin/python -I philippines/pipeline/ph_review_page.py image  <Symbol> <Doc> <page> <out.png> [dpi]
"""
import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "philippines" / "raw" / "pse"


def docs(sym):
    for mp in sorted((RAW / sym).glob("*/meta.json")):
        m = json.loads(mp.read_text(encoding="utf-8"))
        yield m, mp.parent


def open_doc(sym, sub):
    hits = [(m, d / f["saved_as"]) for m, d in docs(sym) for f in m["files"] if sub in f.get("saved_as", "")]
    if len(hits) != 1:
        raise SystemExit(f"{len(hits)} files match {sym} {sub!r}: {[str(h[1].name) for h in hits]}")
    return hits[0][0], hits[0][1]


def main():
    cmd, sym = sys.argv[1], sys.argv[2]
    if cmd == "list":
        for m, d in docs(sym):
            print(m["form"], m["announced"], m["report_no"], m["viewer_url"])
            for f in m["files"]:
                if f.get("saved_as"):
                    print("   ", f["saved_as"])
        return
    meta, path = open_doc(sym, sys.argv[3])
    doc = fitz.open(path)
    print(f"## {sym} {path.name} | pages {len(doc)} | {meta['form']} {meta['report_no']} {meta['announced']} | {meta['viewer_url']}")
    if cmd == "text":
        for p in [int(x) for x in sys.argv[4].split(",")]:
            t = re.sub(r"[ \t]+", " ", doc[p - 1].get_text())
            print(f"--- page {p} ({len(t)} chars{'; NO TEXT LAYER - use image' if len(t) < 80 else ''}) ---")
            print(re.sub(r"\n\s*\n+", "\n", t))
    elif cmd == "find":
        rx = re.compile(sys.argv[4], re.I)
        for i, page in enumerate(doc, 1):
            t = re.sub(r"\s+", " ", page.get_text())
            for m in rx.finditer(t):
                print(f"p{i}: ...{t[max(0, m.start() - 150): m.end() + 200]}...")
    elif cmd == "image":
        dpi = int(sys.argv[6]) if len(sys.argv) > 6 else 100
        doc[int(sys.argv[4]) - 1].get_pixmap(dpi=dpi).save(sys.argv[5])
        print("saved", sys.argv[5])


if __name__ == "__main__":
    main()

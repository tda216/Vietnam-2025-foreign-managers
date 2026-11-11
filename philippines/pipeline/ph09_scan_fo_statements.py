"""Step ph09 (screen): company-level foreign-ownership statements in downloaded filings, for securities still REVIEW.

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph09_scan_fo_statements.py [SYM ...]
Reads the PDFs of 17-1 (annual report) and 17-5 (information statement) filings under philippines/raw/pse/<Symbol>/
plus cached OCR text (philippines/data/ocr/<Symbol>/). Looks for sentences/tables that state the foreign share of the
company as a whole: "foreign ownership level", "owned by foreign/non-Filipino stockholders", nationality tables
("Filipino ... Foreign/Non-Filipino ... %"). Screening only: every hit must be read (page + date) before it is used.
Writes philippines/data/fo_statement_hits.csv
"""
import csv
import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "philippines"
RAW = PH / "raw" / "pse"
DATA = PH / "data"
PCT = r"\d{1,3}(?:\.\d+)?\s?%"
PATTERNS = [
    ("FO_LEVEL", re.compile(r"(?i)foreign[- ]ownership(?: level)?[^.%]{0,160}?" + PCT)),
    ("OWNED_BY_FOREIGN", re.compile(r"(?i)" + PCT + r"[^.]{0,80}?(?:owned|held) by (?:foreign|non-filipino|alien)")),
    ("OWNED_BY_FOREIGN", re.compile(r"(?i)(?:owned|held) by (?:foreign|non-filipino|alien)[^.%]{0,120}?" + PCT)),
    ("NATIONALITY_TABLE", re.compile(r"(?i)\bFilipinos?\b[^%]{0,60}?" + PCT + r"[^%]{0,160}?\b(?:Foreign|Non-?Filipino|Alien)s?\b[^%]{0,60}?" + PCT)),
    ("NATIONALITY_TABLE", re.compile(r"(?i)\b(?:Foreign|Non-?Filipino|Alien)s?\b[^%]{0,60}?" + PCT + r"[^%]{0,160}?\bFilipinos?\b[^%]{0,60}?" + PCT)),
]


def texts(sym):
    for mp in sorted((RAW / sym).glob("*/meta.json")):
        m = json.loads(mp.read_text(encoding="utf-8"))
        if m["form"] not in ("17-1", "17-5", "POR-1"):
            continue
        for f in m["files"]:
            n = f.get("saved_as", "")
            if not n.lower().endswith(".pdf"):
                continue
            try:
                doc = fitz.open(mp.parent / n)
            except Exception:
                continue
            for i, p in enumerate(doc, 1):
                yield m, n, i, re.sub(r"\s+", " ", p.get_text())
    for t in sorted((DATA / "ocr" / sym).glob("*.txt")) if (DATA / "ocr" / sym).exists() else []:
        mm = re.match(r"(.+)_p(\d+)\.txt$", t.name)
        if mm:
            yield {"form": "OCR", "announced": "", "viewer_url": ""}, mm.group(1) + " (OCR)", int(mm.group(2)), \
                re.sub(r"\s+", " ", t.read_text(encoding="utf-8", errors="ignore"))


def main():
    syms = sys.argv[1:] or [r["Symbol"] for r in csv.DictReader(open(DATA / "fo_final.csv", encoding="utf-8"))
                            if r["Ownership_Type"] == "REVIEW"]
    out = []
    for s in syms:
        seen = set()
        for m, n, pno, t in texts(s):
            for kind, rx in PATTERNS:
                for h in rx.finditer(t):
                    snip = t[max(0, h.start() - 120): h.end() + 120]
                    key = (n[:40], pno, h.group(0)[:60])
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({"Symbol": s, "Kind": kind, "Form": m["form"], "Announced": m["announced"], "File": n,
                                "Page": pno, "Match": h.group(0)[:300], "Context": snip[:600], "Viewer_URL": m["viewer_url"]})
    with open(DATA / "fo_statement_hits.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Symbol", "Kind", "Form", "Announced", "File", "Page", "Match", "Context", "Viewer_URL"])
        w.writeheader()
        w.writerows(out)
    from collections import Counter
    c = Counter(r["Symbol"] for r in out)
    print("hits:", len(out), "| symbols with hits:", len(c), "| without:", sorted(set(syms) - set(c)))


if __name__ == "__main__":
    main()

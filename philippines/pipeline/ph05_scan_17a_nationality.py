"""Step ph05: screen the downloaded SEC Form 17-A annual reports (PSE form 17-1) for non-Filipino nationality labels.

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph05_scan_17a_nationality.py [--symbols-file file.csv]

Reads  philippines/raw/pse/<symbol>/<edge_no>/att_*.pdf   (untrusted input; parsed as data only)
Writes philippines/data/nationality_hits_17a.csv   one row per page x non-Filipino nationality term
       philippines/data/scan_17a_status.csv        one row per 17-A PDF: pages, text/scanned, hit counts

Screening is NOT evidence. A hit only decides which page to open. Every record must still be checked on the page
(image for OCR / multi-column pages), tied to the right person, and tied to a FY2025 position.
Hit levels:
  HIGH = demonym directly after an age, e.g. "40, Japanese" or "Age 52 / Citizenship: American"
  LOW  = demonym or 'citizenship'/'nationality' label elsewhere on the page
PDFs without a text layer are listed as SCANNED (OCR + page-image review needed); they are not guessed.
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "philippines" / "raw" / "pse"
DATA = ROOT / "philippines" / "data"

# demonym -> country (screening vocabulary only; the recorded country is a standard English name)
DEMONYMS = {
    "American": "United States", "British": "United Kingdom", "English": "United Kingdom", "Scottish": "United Kingdom",
    "Singaporean": "Singapore", "Chinese": "China", "Japanese": "Japan", "Australian": "Australia", "Malaysian": "Malaysia",
    "Taiwanese": "Taiwan", "Indian": "India", "Indonesian": "Indonesia", "French": "France", "Korean": "South Korea",
    "South Korean": "South Korea", "Danish": "Denmark", "South African": "South Africa", "Swiss": "Switzerland",
    "German": "Germany", "Spanish": "Spain", "Belgian": "Belgium", "Saudi": "Saudi Arabia", "Peruvian": "Peru",
    "Czech": "Czech Republic", "Sri Lankan": "Sri Lanka", "Russian": "Russia", "New Zealander": "New Zealand",
    "Thai": "Thailand", "Mexican": "Mexico", "Greek": "Greece", "Canadian": "Canada", "Dutch": "Netherlands",
    "Italian": "Italy", "Swedish": "Sweden", "Norwegian": "Norway", "Irish": "Ireland", "Israeli": "Israel",
    "Vietnamese": "Vietnam", "Hong Konger": "Hong Kong", "Brazilian": "Brazil", "Argentine": "Argentina",
    "Pakistani": "Pakistan", "Bangladeshi": "Bangladesh", "Nigerian": "Nigeria", "Turkish": "Turkey", "Polish": "Poland",
    "Austrian": "Austria", "Portuguese": "Portugal", "Finnish": "Finland", "Cambodian": "Cambodia", "Burmese": "Myanmar",
    "Lebanese": "Lebanon", "Egyptian": "Egypt", "Emirati": "United Arab Emirates", "Kuwaiti": "Kuwait", "Qatari": "Qatar",
    "American-Filipino": "United States", "Fil-American": "United States", "Fil-Chinese": "China",
}
DEM_ALT = "|".join(sorted((re.escape(d) for d in DEMONYMS), key=len, reverse=True))
HIGH_RE = re.compile(r"(?:\b(?:age[d]?\s*)?\d{2}\s*[,;/–-]\s*(?:a\s+)?(" + DEM_ALT + r")\b)"
                     r"|(?:\b(?:citizenship|nationality)\s*[:\-–]?\s*(" + DEM_ALT + r")\b)", re.I)
LOW_RE = re.compile(r"\b(" + DEM_ALT + r")\b")
LABEL_RE = re.compile(r"\b(citizenship|nationality)\b", re.I)
FIL_RE = re.compile(r"\bFilipino\b", re.I)


def norm(d):
    for k in DEMONYMS:
        if k.lower() == d.lower():
            return k
    return d


def main():
    wanted = None
    if "--symbols-file" in sys.argv:
        path = sys.argv[sys.argv.index("--symbols-file") + 1]
        wanted = {r["Symbol"] for r in csv.DictReader(open(path, encoding="utf-8"))}
    hits, status = [], []
    for mp in sorted(RAW.glob("*/*/meta.json")):
        meta = json.loads(mp.read_text(encoding="utf-8"))
        if meta["form"] != "17-1" or (wanted is not None and meta["symbol"] not in wanted):
            continue
        for f in meta["files"]:
            name = f.get("saved_as", "")
            if not name.lower().endswith(".pdf"):
                continue
            try:
                doc = fitz.open(mp.parent / name)
            except Exception:
                status.append({"Symbol": meta["symbol"], "Edge_No": meta["edge_no"], "File": name, "Status": "UNREADABLE",
                               "Pages": 0, "Text_Pages": 0, "High_Pages": 0, "Low_Pages": 0, "Filipino_Labels": 0})
                continue
            tp = hp = lp = fil = 0
            for pno, page in enumerate(doc, 1):
                t = page.get_text()
                if len(t) < 80:
                    continue
                tp += 1
                fil += len(FIL_RE.findall(t))
                flat = re.sub(r"\s+", " ", t)
                seen = set()
                for m in HIGH_RE.finditer(flat):
                    term = norm(m.group(1) or m.group(2))
                    seen.add(term)
                    hits.append({"Symbol": meta["symbol"], "Edge_No": meta["edge_no"], "File": name, "Page": pno, "Level": "HIGH",
                                 "Term": term, "Country": DEMONYMS.get(term, ""),
                                 "Context": flat[max(0, m.start() - 140): m.end() + 80]})
                if seen:
                    hp += 1
                low_terms = {norm(m.group(1)) for m in LOW_RE.finditer(flat)} - seen
                if low_terms and not seen:
                    lp += 1
                for term in sorted(low_terms):
                    m = re.search(r"\b" + re.escape(term) + r"\b", flat)
                    hits.append({"Symbol": meta["symbol"], "Edge_No": meta["edge_no"], "File": name, "Page": pno, "Level": "LOW",
                                 "Term": term, "Country": DEMONYMS.get(term, ""),
                                 "Context": flat[max(0, m.start() - 120): m.end() + 80]})
            n = len(doc)
            st = "SCANNED" if tp == 0 or tp < 0.3 * n else "TEXT"
            status.append({"Symbol": meta["symbol"], "Edge_No": meta["edge_no"], "File": name, "Status": st, "Pages": n,
                           "Text_Pages": tp, "High_Pages": hp, "Low_Pages": lp, "Filipino_Labels": fil})
    for fname, rows in (("nationality_hits_17a.csv", hits), ("scan_17a_status.csv", status)):
        if not rows:
            continue
        with open(DATA / fname, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    print("17-A PDFs:", len(status), Counter(s["Status"] for s in status))
    print("HIGH hits:", sum(1 for h in hits if h["Level"] == "HIGH"), "| companies with HIGH:",
          len({h["Symbol"] for h in hits if h["Level"] == "HIGH"}))


if __name__ == "__main__":
    main()

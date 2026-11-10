"""Step ph12 (screen): foreign nationality labels in the director/officer tables of FY2025 filings, for BoardEx companies.

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph12_director_nationality_screen.py
Why: BoardEx can miss people (e.g. DITO's Chinese director Chun Lam Chan is in the 17-A but not in BoardEx), and ph11 only
looked up BoardEx names. Targets: LOCAL in-scope companies with a BoardEx match whose flag is NONE_FOUND or UNRESOLVED
(read from philippines/output/Philippines_2025_Foreign_Managers.xlsx). Documents: 2026 17-1 / 17-5 PDFs (2025 ones for fiscal years
not ending in December) + cached OCR text.
A hit = a non-Filipino nationality word next to an age ('NAME, Japanese, 52' / 'NAME 52 Japanese') or next to
'Citizenship'/'citizen'/'national'. Screening only: every hit is read before anything is recorded (ph_add_records.py).
Writes philippines/data/director_nationality_screen.csv
"""
import csv
import re
import sys
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / "philippines" / "data"
sys.path.insert(0, str(HERE))
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("ph11", HERE / "ph11_boardex_nationality_scan.py")
ph11 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph11)

FOREIGN = sorted({k for k, v in ph11.DEM.items() if v != "Philippines"}, key=len, reverse=True)
F_ALT = "|".join(re.escape(k) for k in FOREIGN)
HIT = re.compile(r"(?i)(?:\b\d{2}\b[ ,]{0,3}(?:years old[ ,]{0,3})?\b(" + F_ALT + r")\b|\b(" + F_ALT + r")\b[ ,]{0,3}\d{2}\b|"
                 r"citizenship\W{0,5}(" + F_ALT + r")\b|\b(" + F_ALT + r")\s+(?:citizen|national)\b)")
NOISE = re.compile(r"(?i)\b(yen|new year|cuisine|food|restaurant|market|government|embassy|investors?|bank|corporation|company|law|"
                   r"language|school|university|style|brand|airlines?)\b")


def main():
    wb = openpyxl.load_workbook(ROOT / "philippines" / "output" / "Philippines_2025_Foreign_Managers.xlsx", read_only=True)
    it = wb["Companies"].iter_rows(values_only=True)
    h = next(it)
    comps = [dict(zip(h, r)) for r in it]
    targets = sorted(c["Ticker"].split()[0] for c in comps if c["Ownership_Type"] == "LOCAL" and str(c["In_Scope"]) == "1"
                     and str(c["BoardEx_Coverage"]).startswith("MATCHED") and c["Flag_Status"] in ("NONE_FOUND", "UNRESOLVED"))
    out, no_doc = [], []
    for sym in targets:
        pages = ph11.docs(sym)
        if not pages:
            no_doc.append(sym)
            continue
        seen = set()
        for n, i, t, src, url, lf in pages:
            for m in HIT.finditer(t):
                lab = next(g for g in m.groups() if g)
                snip = t[max(0, m.start() - 160): m.end() + 60]
                if NOISE.search(t[m.start(): m.end() + 25]):
                    continue
                key = (sym, snip[100:200])
                if key in seen:
                    continue
                seen.add(key)
                out.append({"Symbol": sym, "Label": lab, "Country": ph11.DEM.get(lab.lower(), ""), "File": n, "Page": i,
                            "Snippet": snip, "Source": src, "Source_URL": url, "Local_File": lf})
    with open(DATA / "director_nationality_screen.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Symbol", "Label", "Country", "File", "Page", "Snippet", "Source", "Source_URL", "Local_File"])
        w.writeheader()
        w.writerows(out)
    print("targets:", len(targets), "| without FY2025 filing on disk:", no_doc)
    print("hits:", len(out), "| companies with hits:", len({o["Symbol"] for o in out}))


if __name__ == "__main__":
    main()

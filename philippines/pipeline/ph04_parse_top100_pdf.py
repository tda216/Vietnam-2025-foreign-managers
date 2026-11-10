"""Step ph04: extract the stockholder rows from the Top 100 Stockholders PDFs (17-12-A, common shares).

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph04_parse_top100_pdf.py

Reads  philippines/raw/pse/<symbol>/<edge_no>/att_*.pdf  (untrusted input; parsed as data only, never executed)
       philippines/data/top100_form.csv                  (outstanding shares from ph03)
Writes philippines/data/top100_holders.csv   one row per stockholder row found in a text PDF
       philippines/data/top100_pdf_status.csv  one row per filing: pages, text/scanned, rows found, status

Rows are rebuilt from word positions (y coordinate), so column order differs between filers does not matter:
  Holder_Name = leading words of the row; Shares = the largest integer in the row (>= 1,000);
  Pct_Reported = a decimal number followed by '%' or the last decimal < 100 on the row (audit only);
  Pct_Computed = Shares / Outstanding_Shares (from the PSE form).
Scanned PDFs (no text layer) are NOT guessed; they are listed with status SCANNED for page-image review.
A parsed row is a screening aid only; evidence for a record is always the quoted page.
"""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "philippines" / "raw" / "pse"
DATA = ROOT / "philippines" / "data"

INT_RE = re.compile(r"^\(?\d{1,3}(?:,\d{3})+\)?$|^\d{4,}$")
DEC_RE = re.compile(r"^\d{1,3}\.\d{1,6}%?$")
SKIP_NAME = re.compile(r"(?i)^(rank|no\.?|name|stockholder'?s?|stockholders?|shares?|total|percentage|%|outstanding|issued|"
                       r"subscribed|holdings?|fully|paid|partially|grand|top|as of|page|number|class|common|preferred)\b")


def page_rows(page):
    words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
    rows = defaultdict(list)
    for w in words:
        rows[round((w[1] + w[3]) / 2 / 3)].append(w)  # 3pt buckets
    merged, keys = [], sorted(rows)
    for k in keys:
        merged.append(sorted(rows[k], key=lambda w: w[0]))
    return merged


def parse_row(ws):
    toks = [w[4] for w in ws]
    ints = [(i, t) for i, t in enumerate(toks) if INT_RE.match(t)]
    if not ints:
        return None
    # name = words before the first numeric token that is not a rank number
    first_num = None
    for i, t in ints:
        if int(re.sub(r"[^\d]", "", t)) >= 1000 or "," in t:
            first_num = i
            break
    if first_num is None:
        return None
    name_toks = toks[:first_num]
    if name_toks and re.match(r"^\d{1,3}[.)]?$", name_toks[0]):
        name_toks = name_toks[1:]
    name = " ".join(name_toks).strip(" .,-:")
    if len(name) < 3 or SKIP_NAME.match(name):
        return None
    nums = [int(re.sub(r"[^\d]", "", t)) for _, t in ints if int(re.sub(r"[^\d]", "", t)) >= 1000]
    shares = max(nums) if nums else None
    decs = [float(t.rstrip("%")) for t in toks if DEC_RE.match(t)]
    pct = decs[-1] if decs else None
    return name, shares, pct


def main():
    forms = {r["Edge_No"]: r for r in csv.DictReader(open(DATA / "top100_form.csv", encoding="utf-8"))}
    holders, status = [], []
    for mp in sorted(RAW.glob("*/*/meta.json")):
        meta = json.loads(mp.read_text(encoding="utf-8"))
        if meta["form"] != "17-12-A":
            continue
        sym, edge = meta["symbol"], meta["edge_no"]
        out = forms.get(edge, {})
        outstanding = float(out["Outstanding_Shares"]) if out.get("Outstanding_Shares") else None
        pdfs = [f for f in meta["files"] if f.get("saved_as", "").lower().endswith(".pdf")]
        n_pages, n_chars, n_rows = 0, 0, 0
        for f in pdfs:
            try:
                doc = fitz.open(mp.parent / f["saved_as"])
            except Exception as e:
                status.append({"Symbol": sym, "Edge_No": edge, "File": f["saved_as"], "Status": "UNREADABLE", "Pages": 0, "Rows": 0})
                continue
            fn_low = f["saved_as"].lower()
            is_participants = "pdtc" in fn_low or "participant" in fn_low
            for pno, page in enumerate(doc, 1):
                n_pages += 1
                n_chars += len(page.get_text())
                if is_participants:
                    continue
                for ws in page_rows(page):
                    r = parse_row(ws)
                    if not r:
                        continue
                    name, shares, pct = r
                    n_rows += 1
                    holders.append({"Symbol": sym, "Edge_No": edge, "File": f["saved_as"], "Page": pno, "Holder_Name": name,
                                    "Shares": shares, "Pct_Reported": pct if pct is not None else "",
                                    "Pct_Computed": round(100 * shares / outstanding, 4) if outstanding and shares else "",
                                    "Row_Text": " ".join(w[4] for w in ws)[:300]})
        st = "SCANNED" if pdfs and n_chars < 300 else ("NO_PDF" if not pdfs else ("OK" if n_rows >= 5 else "FEW_ROWS"))
        status.append({"Symbol": sym, "Edge_No": edge, "File": ";".join(f["saved_as"] for f in pdfs), "Status": st,
                       "Pages": n_pages, "Rows": n_rows})
    for name, rows in (("top100_holders.csv", holders), ("top100_pdf_status.csv", status)):
        with open(DATA / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    print("holder rows:", len(holders), "| filings:", len(status), Counter(s["Status"] for s in status))


if __name__ == "__main__":
    main()

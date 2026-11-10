"""Step ph03: parse the structured PSE form (form.html) of each Top 100 Stockholders filing (17-12-A common shares).

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph03_parse_top100_form.py

Reads  philippines/raw/pse/<symbol>/<edge_no>/{meta.json,form.html}   (untrusted input; parsed as text only)
Writes philippines/data/top100_form.csv  - one row per filing:
  Symbol, Edge_No, Announced, Period_Ended, Outstanding_Shares, Listed_Shares, Lodged_Shares,
  PCD_Filipino, PCD_NonFilipino, PCD_NonFilipino_Pct_Outstanding, Parse_Status, Parse_Note

PCD Nominee - Non-Filipino is only the lodged (scripless) part held by non-Filipinos. It is a LOWER BOUND of foreign ownership.
"""
import csv
import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "philippines" / "raw" / "pse"
OUT = ROOT / "philippines" / "data" / "top100_form.csv"

NUM = r"([\d,]+(?:\.\d+)?)"


def text_of(path):
    s = path.read_text(encoding="utf-8", errors="replace")
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))


def num(t, label):
    m = re.search(label + r"\s*:?\s*" + NUM, t, re.I)
    return float(m.group(1).replace(",", "")) if m else None


def parse(path):
    t = text_of(path)
    period = re.search(r"For the (?:period|year|quarter) ended\s+([A-Z][a-z]{2,8}\.? \d{1,2}, \d{4})", t)
    p = None
    if period:
        for fmt in ("%b %d, %Y", "%B %d, %Y"):
            try:
                p = datetime.strptime(period.group(1).replace(".", ""), fmt).date().isoformat()
                break
            except ValueError:
                pass
    out = {
        "Period_Ended": p or "",
        "Outstanding_Shares": num(t, r"Number of Outstanding (?:Common )?Shares"),
        "Listed_Shares": num(t, r"Number of Listed (?:Common )?Shares"),
        "Lodged_Shares": num(t, r"Number of Lodged (?:Common )?Shares"),
        "PCD_Filipino": num(t, r"PCD Nominee\s*-\s*Filipino"),
        "PCD_NonFilipino": num(t, r"PCD Nominee\s*-\s*Non-?\s*Filipino"),
    }
    return out


def main():
    rows = []
    for meta_path in sorted(RAW.glob("*/*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("form") != "17-12-A":
            continue
        form = meta_path.parent / "form.html"
        row = {"Symbol": meta["symbol"], "Edge_No": meta["edge_no"], "Announced": meta["announced"]}
        if not form.exists():
            row.update({"Parse_Status": "NO_FORM_HTML", "Parse_Note": ""})
            rows.append(row)
            continue
        d = parse(form)
        row.update(d)
        base = d["Outstanding_Shares"] or d["Listed_Shares"]
        row["PCD_NonFilipino_Pct_Outstanding"] = (round(100 * d["PCD_NonFilipino"] / base, 4)
                                                  if d["PCD_NonFilipino"] is not None and base else "")
        missing = [k for k in ("Period_Ended", "Outstanding_Shares", "PCD_Filipino", "PCD_NonFilipino") if d[k] in (None, "")]
        row["Parse_Status"] = "OK" if not missing else "INCOMPLETE"
        row["Parse_Note"] = ("missing: " + ",".join(missing)) if missing else ""
        rows.append(row)
    fields = ["Symbol", "Edge_No", "Announced", "Period_Ended", "Outstanding_Shares", "Listed_Shares", "Lodged_Shares",
              "PCD_Filipino", "PCD_NonFilipino", "PCD_NonFilipino_Pct_Outstanding", "Parse_Status", "Parse_Note"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print("filings:", len(rows), Counter(r["Parse_Status"] for r in rows))
    print("periods:", Counter(r.get("Period_Ended", "") for r in rows).most_common(6))


if __name__ == "__main__":
    main()

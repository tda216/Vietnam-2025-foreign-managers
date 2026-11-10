"""Step ph08: final foreign-ownership (FO) classification for every Bloomberg security (Philippines FY2025).

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph08_fo_classify.py
(run ph07_holder_nationality.py first)

Priority per company:
  1. latest row in data/manual/ownership_manual.csv (hand-reviewed, or a research-owner rule)  -> Basis MANUAL
  2. ph07 bounds that decide the class (FO_Lower > 50 or FO_Upper <= 50)                      -> Basis AUTO_BOUNDS
  3. otherwise REVIEW (reason given)                                                           -> Basis NONE
Rule: FO > 50 FOREIGN_MAJORITY, FO <= 50 LOCAL, undecidable/missing REVIEW. FO_Bound = EXACT when lower == upper, else RANGE.
Manager_Search = Y for LOCAL, and for FOREIGN_MAJORITY whose FO_Lower <= 55 (borderline rule).
Writes philippines/data/fo_final.csv
"""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "philippines" / "data"
RAW = ROOT / "philippines" / "raw" / "pse"


def top100_source(sym):
    for mp in (RAW / sym).glob("*/meta.json"):
        m = json.loads(mp.read_text(encoding="utf-8"))
        if m["form"] == "17-12-A" and "2026" in m["announced"]:
            return f"{m['template']} ({m['form']}) {m['report_no']}, announced {m['announced']}", m["viewer_url"]
    return "", ""


def main():
    comps = list(csv.DictReader(open(DATA / "companies_boardex.csv", encoding="utf-8-sig")))
    bounds = {r["Symbol"]: r for r in csv.DictReader(open(DATA / "fo_bounds.csv", encoding="utf-8"))}
    manual = {}
    for r in csv.DictReader(open(DATA / "manual" / "ownership_manual.csv", encoding="utf-8")):
        manual[r["Ticker"] or r["Symbol"]] = r  # later rows supersede earlier ones
        manual.setdefault("SYM:" + r["Symbol"], r)
        manual["SYM:" + r["Symbol"]] = r
    out = []
    for c in comps:
        tk = c["Ticker"]
        sym = tk.split()[0]
        row = {"Ticker": tk, "Symbol": sym, "Company": c["Company"], "In_Scope": "1", "Exclusion_Reason": "",
               "Ownership_Type": "REVIEW", "FO_Lower": "", "FO_Upper": "", "Foreign_Ownership_Pct": "", "FO_Bound": "",
               "FO_As_Of_Date": "", "FO_Method": "", "FO_Source": "", "FO_Source_URL": "", "FO_Page": "", "FO_Evidence": "",
               "FO_Note": "", "Basis": "NONE"}
        m = manual.get(tk) or (manual.get("SYM:" + sym) if tk.split()[1] == "PM" else None)
        b = bounds.get(sym) if tk.split()[1] == "PM" else None
        if m:
            row.update(Ownership_Type=m["Ownership_Type"], FO_Lower=m["FO_Lower"], FO_Upper=m["FO_Upper"],
                       Foreign_Ownership_Pct=m["Foreign_Ownership_Pct"], FO_As_Of_Date=m["FO_As_Of_Date"], FO_Method=m["FO_Method"],
                       FO_Source=m["Source"], FO_Source_URL=m["Source_URL"], FO_Page=m["Page"], FO_Evidence=m["Evidence_Quote"],
                       FO_Note=m["Note"], Basis="MANUAL", In_Scope=m.get("In_Scope") or "1", Exclusion_Reason=m.get("Exclusion_Reason", ""))
        elif b and b.get("Review_Class") in ("LOCAL_CERTAIN", "FOREIGN_MAJORITY_CERTAIN"):
            src, url = top100_source(sym)
            row.update(Ownership_Type="LOCAL" if b["Review_Class"] == "LOCAL_CERTAIN" else "FOREIGN_MAJORITY",
                       FO_Lower=b["FO_Lower"], FO_Upper=b["FO_Upper"], FO_As_Of_Date="2025-12-31",
                       FO_Method="TOP100_PCD_PLUS_17A_HOLDER_LABELS", FO_Source=src, FO_Source_URL=url, Basis="AUTO_BOUNDS",
                       FO_Note=(f"PCD Non-Filipino {b['PCD_NonFilipino_Pct']}%; direct holders labelled foreign {b['Foreign_Direct_Pct']}%, "
                                f"Filipino {b['Filipino_Direct_Pct']}%, unknown {b['Unknown_Direct_Pct']}%; unlisted remainder {b['Tail_Pct']}%. "
                                "Holder nationality labels from the FY2025 17-A (date of that report); see holder_nationality.csv"))
        else:
            reason = ("no PSE Top 100 list for 31 Dec 2025" if not b else
                      {"NEEDS_REVIEW": "bounds straddle 50%", "PARSE_CHECK": "Top 100 table not read reliably",
                       "FORM_INCOMPLETE": "PCD lines missing on the PSE form"}.get(b.get("Review_Class"), b.get("Review_Class")))
            if b and b.get("FO_Lower"):
                row.update(FO_Lower=b["FO_Lower"], FO_Upper=b["FO_Upper"])
            row["FO_Note"] = "REVIEW: " + reason
        if row["FO_Lower"] != "" and row["FO_Upper"] != "":
            row["FO_Bound"] = "EXACT" if float(row["FO_Lower"]) == float(row["FO_Upper"]) else "RANGE"
        t = row["Ownership_Type"]
        row["Manager_Search"] = "Y" if row["In_Scope"] == "1" and (
            t == "LOCAL" or (t == "FOREIGN_MAJORITY" and row["FO_Lower"] != "" and float(row["FO_Lower"]) <= 55)) else "N"
        out.append(row)
    with open(DATA / "fo_final.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print("securities:", len(out), Counter(r["Ownership_Type"] for r in out))
    print("by basis:", Counter((r["Basis"], r["Ownership_Type"]) for r in out))
    print("in scope:", Counter(r["In_Scope"] for r in out), "| manager search Y:", sum(r["Manager_Search"] == "Y" for r in out))
    print("REVIEW:", sorted(r["Symbol"] for r in out if r["Ownership_Type"] == "REVIEW"))


if __name__ == "__main__":
    main()

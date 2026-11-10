"""Step 2d – second-source check of 31/12/2025 foreign ownership from CafeF's daily foreign-trading history.

CafeF reports "DangSoHuu" (% held by foreign investors) per trading day. For each in-scope VN company
the last trading day on or before FO_AS_OF in 15–31/12/2025 is taken. Figures are stored as additional
observations (they never overwrite the VSDC figure); differences > TOLERANCE_PP are listed for review.

Output: data/fo_cafef_20251231.csv
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import fetch, read_csv, write_csv
from config import DATA, FO_AS_OF

URL = ("https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/GDKhoiNgoai.ashx?Symbol={sym}"
       "&StartDate=12/15/2025&EndDate=12/31/2025&PageIndex=1&PageSize=20")
TOLERANCE_PP = 0.10
FIELDS = ["Ticker", "Ticker_Local", "CafeF_Date", "CafeF_FO_Pct", "VSDC_FO_Pct", "Diff_PP", "Source", "Source_URL", "Note"]


def main():
    comps = [r for r in read_csv(DATA / "companies_step2.csv") if r["Security_Class"] == "COMPANY_VN"]
    as_of = date.fromisoformat(FO_AS_OF)
    out = []
    for i, c in enumerate(comps, 1):
        url = URL.format(sym=c["Ticker_Local"])
        row = {"Ticker": c["Ticker"], "Ticker_Local": c["Ticker_Local"], "VSDC_FO_Pct": c["Foreign_Ownership_Pct"],
               "Source": "CafeF – foreign trading history (DangSoHuu)", "Source_URL": url,
               "CafeF_Date": "", "CafeF_FO_Pct": "", "Diff_PP": "", "Note": ""}
        try:
            body, _ = fetch(url)
            days = (json.loads(body).get("Data") or {}).get("Data") or []
            days = [d for d in days if datetime.strptime(d["Ngay"], "%d/%m/%Y").date() <= as_of]
            if days:
                last = max(days, key=lambda d: datetime.strptime(d["Ngay"], "%d/%m/%Y"))
                row["CafeF_Date"] = datetime.strptime(last["Ngay"], "%d/%m/%Y").date().isoformat()
                row["CafeF_FO_Pct"] = last["DangSoHuu"]
                if c["Foreign_Ownership_Pct"] != "" and last["DangSoHuu"] is not None:
                    row["Diff_PP"] = round(float(last["DangSoHuu"]) - float(c["Foreign_Ownership_Pct"]), 4)
            else:
                row["Note"] = "no trading-day record 15–31/12/2025"
        except Exception as e:  # keep going; the failure is recorded, not hidden
            row["Note"] = f"fetch/parse error: {e!r}"[:200]
        out.append(row)
        if i % 100 == 0:
            print(f"{i}/{len(comps)}", flush=True)

    write_csv(DATA / "fo_cafef_20251231.csv", out, FIELDS)
    diffs = [r for r in out if r["Diff_PP"] != "" and abs(r["Diff_PP"]) > TOLERANCE_PP]
    print("done:", len(out), "| with CafeF figure:", sum(1 for r in out if r["CafeF_FO_Pct"] != ""),
          "| |diff| >", TOLERANCE_PP, "pp:", len(diffs), "| notes:", sum(1 for r in out if r["Note"]))
    for r in sorted(diffs, key=lambda r: -abs(r["Diff_PP"]))[:40]:
        print(f"  {r['Ticker_Local']:6s} VSDC={r['VSDC_FO_Pct']:>10s} CafeF={r['CafeF_FO_Pct']!s:>8s} diff={r['Diff_PP']:+.3f} ({r['CafeF_Date']})")


if __name__ == "__main__":
    main()

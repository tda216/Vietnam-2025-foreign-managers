"""Indonesia step 1 – universe and listing status (no filings downloaded).

Reads the licensed Bloomberg export (indonesia/Bloomberg-Indonesia2025.xlsx, values copied verbatim) and
two KSEI files (idx.co.id blocks scripted access, Cloudflare 403, so the IDX directory is not used):
  - the securities master file ("Master File Efek", Publikasi > Data & Statistik > Statik Efek) for the first
    and last trading days of 2025: raw/ksei/StatisEfek20250102.txt.zip and StatisEfek20251230.txt.zip
    (code, ISIN, issuer, status, stock exchange, listing date, number of shares, scripless total);
  - the holding-composition file of 30 Dec 2025 (raw/ksei/BalanceposEfek20251230.zip), for the KSEI type.
Listing check: an EQUITY code in either master file (all rows are status ACTIVE) was listed during 2025.
The Stock Exchange field is not used: it is blank for TALF, KOPI, PPRO, DMAD and BRAU, although TALF and KOPI
traded at changing prices in 2025. Codes in neither master file (1789071D, ITTG, FINN, PRIM, AMAN) are out of
scope by owner rule (8 Nov 2026, OWNER_RULE_NOT_LISTED_IN_2025); their rows are kept.

Output  data/universe.csv – one row per Bloomberg security: Bloomberg columns verbatim + Exchange, Code,
        Security_Kind, KSEI_Type_20251230, Listing_Status, provisional In_Scope / Scope_Reason

Run from the project root:  .venv/bin/python -I indonesia/pipeline/id01_universe.py
"""
import csv, zipfile
from collections import Counter
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
BBG = ROOT / "Bloomberg-Indonesia2025.xlsx"
KSEI = ROOT / "raw" / "ksei" / "BalanceposEfek20251230.zip"
MAP = ROOT / "data" / "manual" / "ticker_map.csv"   # Bloomberg ticker -> IDX code, by hand, with reason
OUT = ROOT / "data" / "universe.csv"


MASTERS = ["20250102", "20251230"]


def master(date):
    """{code: row} for EQUITY rows of a KSEI master file (one pipe-separated text file in the zip)."""
    z = zipfile.ZipFile(ROOT / "raw" / "ksei" / f"StatisEfek{date}.txt.zip")
    lines = z.read(z.infolist()[0].filename).decode("latin-1").splitlines()
    head = [h.strip() for h in lines[0].split("|")]
    out = {}
    for l in lines[1:]:
        r = dict(zip(head, (x.strip() for x in l.split("|"))))
        if r.get("Type") == "EQUITY":
            out[r["Code"]] = r
    return out


def ksei_types():
    z = zipfile.ZipFile(KSEI)
    lines = z.read(z.infolist()[0].filename).decode("latin-1").splitlines()
    return {f[1]: f[2] for f in (l.split("|") for l in lines[1:]) if len(f) > 3}


def main():
    kt = ksei_types()
    ms = {d: master(d) for d in MASTERS}
    manual = {r["Bloomberg_Ticker"]: r for r in csv.DictReader(MAP.open(encoding="utf-8"))} if MAP.exists() else {}
    ws = openpyxl.load_workbook(BBG, read_only=True, data_only=True).active
    out = []
    for r in list(ws.iter_rows(values_only=True))[4:]:
        if not r[0] or " Equity" not in str(r[0]) or len(str(r[0])) > 40:
            continue
        ticker, short, dom, ind, isin, mcap, price, pe = (list(r) + [None] * 8)[:8]
        parts = ticker.split()
        exch, code = parts[-2], parts[0]
        if code.startswith("R/"):          # Bloomberg prefix for some ETFs (R/LQ45X -> LQ45X)
            code = code[2:]
        m = manual.get(ticker)
        if m:
            code = m["IDX_Code"]
        isin = isin or ""
        if exch != "IJ":
            kind = "FOREIGN_LISTED"
        elif isin.startswith(("IDN", "IDX")) or kt.get(code) in ("MUTUAL FUND", "DANA INVESTASI REAL ESTATE"):
            kind = {"DANA INVESTASI REAL ESTATE": "DIRE"}.get(kt.get(code), "FUND_ETF")
        else:
            kind = "COMPANY"
        on_idx = {d: code in ms[d] for d in MASTERS}
        mrow = ms["20251230"].get(code) or ms["20250102"].get(code) or {}
        if exch != "IJ":
            status, in_scope, reason = "FOREIGN_LISTED_ONLY", 0, "OWNER_RULE_FOREIGN_LISTED_OUT_OF_SCOPE"
        elif kind != "COMPANY":  # owner 7 Nov 2026: ETFs, funds and DIRE out of scope
            status, in_scope, reason = "FUND", 0, "OWNER_RULE_ETF_FUND_OUT_OF_SCOPE"
        elif all(on_idx.values()):
            status, in_scope, reason = "LISTED_ALL_2025", 1, ""
        elif on_idx["20251230"]:
            status, in_scope, reason = "LISTED_IN_2025_NOT_ON_2_JAN", 1, ""   # listed during 2025
        elif on_idx["20250102"]:
            status, in_scope, reason = "LISTED_2_JAN_NOT_30_DEC", 1, "CHECK_DELISTING_DATE"  # left IDX during 2025
        else:
            # owner 8 Nov 2026: not in the KSEI master file on 2 Jan or 30 Dec 2025 -> not listed in 2025, out
            status, in_scope, reason = "NOT_IN_KSEI_MASTER_2025", 0, "OWNER_RULE_NOT_LISTED_IN_2025"
        out.append({"Bloomberg_Ticker": ticker, "Short_Name": short, "Country_Of_Domicile": dom,
                    "Industry_Group": ind, "ISIN": isin, "Market_Cap": mcap, "Price_D1": price, "PE": pe,
                    "Exchange": exch, "Code": code, "Security_Kind": kind,
                    "KSEI_Type_20251230": kt.get(code, ""), "Ticker_Map_Note": m["Reason"] if m else "",
                    "KSEI_Issuer": mrow.get("Issuer", ""), "KSEI_ISIN": mrow.get("Isin Code", ""),
                    "KSEI_Listing_Date": mrow.get("Listing Date", ""), "KSEI_Sector": mrow.get("Sector", ""),
                    **{f"In_KSEI_Master_{d}": int(v) for d, v in on_idx.items()},
                    "KSEI_Exchange_20251230": ms["20251230"].get(code, {}).get("Stock Exchange", "")
                    if code in ms["20251230"] else "NOT_IN_MASTER",
                    "Listing_Status": status, "In_Scope": in_scope, "Scope_Reason": reason})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    print("securities", len(out))
    print(Counter((o["Security_Kind"], o["Listing_Status"], o["Scope_Reason"]) for o in out).most_common())
    for o in out:
        if o["Security_Kind"] == "COMPANY" and o["Listing_Status"] not in ("LISTED_ALL_2025", "LISTED_IN_2025_NOT_ON_2_JAN"):
            print(" ", o["Code"], o["Short_Name"], o["ISIN"], o["Listing_Status"], o["KSEI_Exchange_20251230"],
                  "listed", o["KSEI_Listing_Date"], "KSEI type", o["KSEI_Type_20251230"] or "-")


if __name__ == "__main__":
    main()

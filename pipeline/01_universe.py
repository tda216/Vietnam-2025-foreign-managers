"""Step 1 – build the company universe from the Bloomberg export.

Raw Bloomberg values are copied as-is (no rounding, no renaming of values).
Output: data/universe.csv (one row per Bloomberg security).
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import write_csv
from config import BLOOMBERG_FILE, COUNTRY, DATA, LISTING_FILE, LISTING_SOURCE

BOARD_TO_EXCHANGE = {"HSX": "HOSE", "HNX": "HNX", "UPCOM": "UPCoM", "DELISTED": "DELISTED_IN_LISTING_SNAPSHOT"}
FUND_INDUSTRIES = {"Closed-end Funds", "Equity Fund"}
FUND_TYPES = {"ETF", "UNIT_TRUST"}

FIELDS = [
    "Country", "Bloomberg_Row", "Ticker", "Ticker_Local", "Bloomberg_Short_Name", "Bloomberg_Country",
    "Industry_Group", "ISIN", "Market_Cap_LCL", "Security_Class", "In_Scope", "Exclusion_Reason",
    "Exchange", "Company", "Company_Name_VN", "Listing_Type", "Listing_Source",
]


def read_bloomberg():
    wb = openpyxl.load_workbook(BLOOMBERG_FILE, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    header, out = None, []
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        first = row[0]
        if header is None:
            if first == "Ticker":
                header = list(row)
            continue
        if not isinstance(first, str) or not first.endswith(" Equity"):
            continue  # group header ("None (1599 securities)") and the trailing disclaimer
        out.append((i, dict(zip(header, row))))
    return out


def main():
    listing = json.loads(LISTING_FILE.read_text(encoding="utf-8"))
    by_symbol = {}
    for x in listing:
        # A symbol can appear as STOCK and as another type; keep the STOCK/ETF entry.
        if x["type"] in ("STOCK", "ETF", "UNIT_TRUST") or x["symbol"] not in by_symbol:
            by_symbol[x["symbol"]] = x

    rows = []
    for r, b in read_bloomberg():
        ticker = b["Ticker"]
        on_vn = ticker.endswith(" VN Equity")
        local = ticker.replace(" VN Equity", "") if on_vn else ticker.replace(" Equity", "")
        isin = b.get("ISIN") or ""
        industry = b.get("Ind Group") or ""
        lst = by_symbol.get(local) if on_vn else None

        if not on_vn:
            cls, in_scope, reason = "FOREIGN_LISTED", 1, ""
        elif industry in FUND_INDUSTRIES or (lst and lst["type"] in FUND_TYPES) or re.match(r"^(FUE|FUC|E1V)", local):
            cls, in_scope, reason = "FUND", 0, "FUND_OR_ETF_NOT_A_COMPANY"
        elif not isin:
            cls, in_scope, reason = "NO_ISIN", 0, "NO_ISIN_NO_MARKET_DATA"
        else:
            cls, in_scope, reason = "COMPANY_VN", 1, ""

        rows.append({
            "Country": COUNTRY,
            "Bloomberg_Row": r,
            "Ticker": ticker,
            "Ticker_Local": local,
            "Bloomberg_Short_Name": b.get("Short Name") or "",
            "Bloomberg_Country": b.get("Cntry Terrtry Of Dom") or "",
            "Industry_Group": industry,
            "ISIN": isin,
            "Market_Cap_LCL": "" if b.get("Market Cap") is None else b["Market Cap"],
            "Security_Class": cls,
            "In_Scope": in_scope,
            "Exclusion_Reason": reason,
            "Exchange": BOARD_TO_EXCHANGE.get(lst["board"], lst["board"]) if lst else ("FOREIGN:" + ticker.split()[-2] if not on_vn else ""),
            "Company": (lst or {}).get("enOrganName") or "",
            "Company_Name_VN": (lst or {}).get("organName") or "",
            "Listing_Type": (lst or {}).get("type") or "",
            "Listing_Source": LISTING_SOURCE if lst else "",
        })

    write_csv(DATA / "universe.csv", rows, FIELDS)
    print("rows:", len(rows))
    print("class:", Counter(x["Security_Class"] for x in rows).most_common())
    print("in scope:", sum(int(x["In_Scope"]) for x in rows))
    print("exchange (in-scope VN):", Counter(x["Exchange"] for x in rows if x["Security_Class"] == "COMPANY_VN").most_common())
    print("no listing match:", [x["Ticker_Local"] for x in rows if x["Security_Class"] == "COMPANY_VN" and not x["Exchange"]])


if __name__ == "__main__":
    main()

"""Step 1 – company universe from the Bloomberg export (Thailand).

Raw Bloomberg values are copied as-is. Added: Ticker_Local, Exchange_Code, Security_Class, In_Scope, Exclusion_Reason,
Mcap_Rank (by Bloomberg market cap among all securities), In_BoardEx (ISIN present in the BoardEx roles file).

Security_Class:
  COMPANY_TH      listed on SET / mai (Bloomberg "TB") – main scope
  FUND            REIT, property / infrastructure fund, ETF (Bloomberg Ind Group, or data/manual/security_class_manual.csv)
  FOREIGN_LISTED  Thailand-domiciled issuer listed abroad (US, HK, SP, TT, AU)
Output: data/universe.csv
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

from openpyxl import load_workbook

from common import read_csv, write_csv
from config import BLOOMBERG_FILE, BOARDEX_ROLES_FILE, COUNTRY, DATA

FUND_IND_GROUPS = {"REITS", "Closed-end Funds", "Equity Fund", "Debt Fund", "Commodity Fund", "Private Equity"}


def main():
    rows = list(load_workbook(BLOOMBERG_FILE, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
    head = list(rows[2])
    sec = [r for r in rows if isinstance(r[0], str) and r[0].endswith(" Equity")]
    manual = {m["Ticker_Local"]: m for m in read_csv(DATA / "manual" / "security_class_manual.csv")}
    bx = {r[0] for r in list(load_workbook(BOARDEX_ROLES_FILE, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))[1:]}
    mcap = sorted((r for r in sec if r[5] is not None), key=lambda r: -r[5])
    rank = {r[0]: i for i, r in enumerate(mcap, 1)}
    out = []
    set_codes = {r[0].split()[0] for r in sec if r[0].split()[1] == "TB"}
    for r in sec:
        b = dict(zip(head, r))
        ticker_local, exch = r[0].split()[0], r[0].split()[1]
        if exch != "TB" and ticker_local in set_codes:
            ticker_local = f"{ticker_local}_{exch}"  # e.g. Fabrinet 'FN US' vs FN Factory Outlet 'FN TB': the key must be unique
        if exch != "TB":
            cls, reason = "FOREIGN_LISTED", f"listed on {exch}"
        elif ticker_local in manual:
            cls, reason = manual[ticker_local]["Security_Class"], manual[ticker_local]["Reason"]
        elif b["Ind Group"] in FUND_IND_GROUPS or b["Ind Group"] is None:
            cls, reason = "FUND", f"Bloomberg Ind Group {b['Ind Group']!r}"
        else:
            cls, reason = "COMPANY_TH", ""
        out.append({"Country": COUNTRY, "Ticker": r[0], "Ticker_Local": ticker_local, "Exchange_Code": exch,
                    "Company": b["Short Name"], "ISIN": b["ISIN"] or "", "Industry_Group": b["Ind Group"] or "",
                    "Market_Cap": "" if b["Market Cap"] is None else b["Market Cap"],
                    "Mcap_Rank": rank.get(r[0], ""), "Security_Class": cls,
                    "In_Scope": 0 if cls == "FUND" else 1, "Exclusion_Reason": reason if cls == "FUND" else "",
                    "Class_Note": reason if cls != "FUND" else "", "In_BoardEx": int((b["ISIN"] or "") in bx)})
    write_csv(DATA / "universe.csv", out, list(out[0].keys()))
    from collections import Counter
    print(len(out), "securities |", dict(Counter(o["Security_Class"] for o in out)), "| in BoardEx", sum(o["In_BoardEx"] for o in out))


if __name__ == "__main__":
    main()

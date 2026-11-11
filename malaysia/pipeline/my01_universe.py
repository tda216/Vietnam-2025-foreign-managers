"""Malaysia step 1 – universe and listing status (no filings downloaded).

Reads the licensed Bloomberg export (malaysia/Bloomberg-malaysia2025.xlsx, values copied verbatim)
and the current Bursa company directory as republished by malaysiastock.biz (company drop-down on
Bursa-Announcement.aspx; bursamalaysia.com itself blocks scripted access behind Cloudflare).

Outputs
  data/bursa_directory.csv  Stock_Code, Stock_Name, Company_Name, Retrieved_UTC, Source_URL
  data/universe.csv         one row per Bloomberg security, with Exchange, Stock_Code (from the ISIN),
                            Listing_Status and a provisional In_Scope / Scope_Reason

Run from the project root:  .venv/bin/python -I malaysia/pipeline/my01_universe.py [--refresh]
"""
import csv, datetime as dt, html, re, sys
from pathlib import Path

import openpyxl
import requests

ROOT = Path(__file__).resolve().parents[1]
BBG = ROOT / "Bloomberg-malaysia2025.xlsx"
DIR_CSV = ROOT / "data" / "bursa_directory.csv"
OUT = ROOT / "data" / "universe.csv"
DIR_URL = "https://www.malaysiastock.biz/Bursa-Announcement.aspx"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

FUND_GROUPS = {"Equity Fund", "Debt Fund", "Closed-end Funds"}


def load_directory(refresh):
    if DIR_CSV.exists() and not refresh:
        return {r["Stock_Code"]: r for r in csv.DictReader(DIR_CSV.open(encoding="utf-8"))}
    t = requests.get(DIR_URL, headers={"User-Agent": UA}, timeout=60).text
    sel = re.search(r'name="ctl00\$MainContent2\$ddlCompany".*?</select>', t, re.S).group(0)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
    rows = {}
    for code, label in re.findall(r'<option[^>]*value="([^"]+)"[^>]*>([^<]*)', sel):
        m = re.match(r"(.+?) \((\w+)\): (.+)$", html.unescape(label).strip())
        if code == "0" or not m:
            continue
        rows[code] = {"Stock_Code": code, "Stock_Name": m.group(1), "Company_Name": m.group(3),
                      "Retrieved_UTC": now, "Source_URL": DIR_URL}
    DIR_CSV.parent.mkdir(parents=True, exist_ok=True)
    with DIR_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(next(iter(rows.values()))))
        w.writeheader(); w.writerows(rows.values())
    return rows


def main():
    directory = load_directory("--refresh" in sys.argv)
    ws = openpyxl.load_workbook(BBG, read_only=True, data_only=True).active
    out = []
    for r in list(ws.iter_rows(values_only=True))[4:]:
        if not r[0] or " Equity" not in str(r[0]):
            continue
        ticker, short, dom, ind, isin, mcap, price, pe = (list(r) + [None] * 8)[:8]
        parts = ticker.split()
        exch = parts[-2] if len(parts) >= 3 else ""
        # ISIN = MY + L/Q + 8-char national code + check digit; the Bursa stock code is the
        # national code without its O/0 padding (MYL1155OO000 -> 1155, MYL5235SS008 -> 5235SS)
        m = re.match(r"MY[LQ](\w{8})\d$", isin or "")
        code = m.group(1).rstrip("0").rstrip("O") if m else ""
        board = {"MYL": "MAIN_OR_LEAP", "MYQ": "ACE"}.get((isin or "")[:3], "")
        if code.startswith("03") and len(code) == 5:
            board = "LEAP"
        d = directory.get(code) if code else None
        if not d and code.endswith("T"):  # REIT units: MYL5110TO000 -> 5110
            d = directory.get(code[:-1]); code = code[:-1] if d else code
        if not d and exch == "MK":  # no MY ISIN: match the first two words of the name
            words = re.findall(r"[A-Z]+", (short or "").upper())[:2]
            d = next((v for v in directory.values() if v["Stock_Name"] == parts[0]), None) or next(
                (v for v in directory.values() if len(words) == 2 and
                 re.findall(r"[A-Z]+", v["Company_Name"].upper())[:1] == words[:1] and
                 any(x.startswith(words[1]) for x in re.findall(r"[A-Z]+", v["Company_Name"].upper())[1:2])), None)
            code = d["Stock_Code"] if d else code
        # the directory also keeps delisted names (e.g. BARAKAH), so it does not prove a 2025 listing
        if exch != "MK":
            status, in_scope, reason = "FOREIGN_LISTED_ONLY", 0, "OWNER_RULE_FOREIGN_LISTED_OUT_OF_SCOPE"
        elif d:
            status, in_scope, reason = "IN_BURSA_DIRECTORY", 1, ""
            if price in (None, ""):
                in_scope, reason = "", "NO_BLOOMBERG_PRICE_CHECK_LISTED_IN_2025"
            if ind in FUND_GROUPS:  # owner 7 Nov 2026: ETFs/funds out, REITs in
                in_scope, reason = 0, "OWNER_RULE_ETF_FUND_OUT_OF_SCOPE"
        else:
            status, in_scope, reason = "NOT_IN_BURSA_DIRECTORY", "", "CHECK_LISTED_IN_2025"
        out.append({"Bloomberg_Ticker": ticker, "Short_Name": short, "Country_Of_Domicile": dom,
                    "Industry_Group": ind, "ISIN": isin, "Market_Cap": mcap, "Price_D1": price, "PE": pe,
                    "Exchange": exch, "Bursa_Board": board if exch == "MK" else "",
                    "Stock_Code": code, "Bursa_Stock_Name": d["Stock_Name"] if d else "",
                    "Bursa_Company_Name": d["Company_Name"] if d else "",
                    "Listing_Status": status, "In_Scope": in_scope, "Scope_Reason": reason})
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    from collections import Counter
    print("securities", len(out))
    print(Counter((o["Listing_Status"], o["Scope_Reason"]) for o in out).most_common())
    print("boards (MK):", Counter(o["Bursa_Board"] for o in out if o["Exchange"] == "MK"))


if __name__ == "__main__":
    main()

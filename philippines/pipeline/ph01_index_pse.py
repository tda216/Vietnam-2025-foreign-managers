"""Step ph01: index PSE Edge filings needed for foreign-ownership (FO) classification.

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph01_index_pse.py

Outputs (philippines/data/):
  pse_directory.csv       all companies in the PSE Edge company directory (cmpy_id, name, symbol)
  pse_company_map.csv     one row per Bloomberg security -> PSE company (or NO_PSE_LISTING)
  pse_filings_index.csv   Top 100 stockholder lists (17-12-A/B), Annual Reports (17-1/17-A),
                          Information Statements (17-5), POR-1 for each mapped company, 2025-01-01..today

Only reads public PSE Edge pages. Nothing is executed from downloaded content.
"""
import csv
import html
import re
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "philippines" / "data"
BASE = "https://edge.pse.com.ph"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
PAUSE = 0.6
S = requests.Session()
S.headers.update(UA)


def post(path, data, tries=4):
    for k in range(tries):
        try:
            r = S.post(BASE + path, data=data, timeout=45)
            if r.status_code == 200:
                time.sleep(PAUSE)
                return r.text
        except requests.RequestException:
            pass
        time.sleep(2 * (k + 1))
    raise RuntimeError(f"PSE request failed: {path} {data}")


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def fetch_directory():
    rows, page = [], 1
    while True:
        s = post("/companyDirectory/search.ax", {"sortType": "company", "dateSortType": "DESC", "cmpySortType": "ASC",
                                                 "pageNo": page, "keyword": "", "sector": "ALL", "subsector": "ALL"})
        total_pages = int(re.search(r"\[\s*\d+ /\s*(\d+)\s*\]", s).group(1))
        for tr in re.findall(r"<tr>(.*?)</tr>", s, re.S):
            m = re.search(r"cmDetail\('(\d+)','(\d+)'\)", tr)
            tds = [text(t) for t in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if m and len(tds) >= 5:
                rows.append({"PSE_Company_ID": m.group(1), "PSE_Security_ID": m.group(2), "Company_Name": tds[0],
                             "Symbol": tds[1], "Sector": tds[2], "Subsector": tds[3], "Listing_Date": tds[4]})
        if page >= total_pages:
            return rows
        page += 1


def list_filings(endpoint, cmpy_id, frm, to):
    out, page = [], 1
    while True:
        s = post(f"/{endpoint}/search.ax", {"companyId": cmpy_id, "keyword": "", "tmplNm": "", "fromDate": frm, "toDate": to,
                                            "sortType": "", "dateSortType": "DESC", "cmpySortType": "ASC", "pageNo": page})
        m = re.search(r"\[\s*\d+ /\s*(\d+)\s*\]", s)
        pages = int(m.group(1)) if m else 1
        for tr in re.findall(r"<tr>(.*?)</tr>", s, re.S):
            e = re.search(r"openPopup\('([0-9a-f]+)'\)", tr)
            tds = [text(t) for t in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if e and len(tds) >= 5:
                out.append({"Edge_No": e.group(1), "Endpoint": endpoint, "Template": tds[1], "Form": tds[2],
                            "Announced": tds[3], "Report_No": tds[4]})
        if page >= pages:
            return out
        page += 1


WANTED_FORMS = {"17-12-A", "17-12-B", "17-1", "17-5", "POR-1", "POR-2"}


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    directory = fetch_directory()
    with open(DATA / "pse_directory.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(directory[0]))
        w.writeheader()
        w.writerows(directory)
    print("PSE directory companies:", len(directory))
    by_symbol = {}
    for d in directory:
        by_symbol.setdefault(d["Symbol"].upper(), []).append(d)

    comps = list(csv.DictReader(open(DATA / "companies_boardex.csv", encoding="utf-8-sig")))
    mapping = []
    for c in comps:
        parts = c["Ticker"].split()                # Bloomberg ticker, e.g. "BC PM Equity"
        sym, mkt = parts[0].upper(), (parts[1].upper() if len(parts) > 1 else "")
        hit = by_symbol.get(sym, []) if mkt == "PM" else []
        mapping.append({"Ticker": c["Ticker"], "Company": c["Company"], "ISIN": c["ISIN"], "Symbol": sym, "Market": mkt,
                        "PSE_Company_ID": hit[0]["PSE_Company_ID"] if len(hit) == 1 else "",
                        "PSE_Company_Name": hit[0]["Company_Name"] if len(hit) == 1 else "",
                        "Map_Status": "MATCHED" if len(hit) == 1 else ("AMBIGUOUS" if len(hit) > 1 else "NO_PSE_LISTING")})
    with open(DATA / "pse_company_map.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(mapping[0]))
        w.writeheader()
        w.writerows(mapping)
    from collections import Counter
    print("Map status:", Counter(m["Map_Status"] for m in mapping))

    frm, to = "01-01-2025", date.today().strftime("%m-%d-%Y")
    out_path = DATA / "pse_filings_index.csv"
    done = set()
    fields = ["PSE_Company_ID", "Symbol", "Edge_No", "Endpoint", "Template", "Form", "Announced", "Report_No"]
    if out_path.exists():
        done = {r["PSE_Company_ID"] for r in csv.DictReader(open(out_path, encoding="utf-8"))}
        print("Resuming; companies already indexed:", len(done))
    new = not out_path.exists()
    with open(out_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        todo = [m for m in mapping if m["Map_Status"] == "MATCHED" and m["PSE_Company_ID"] not in done]
        for i, m in enumerate(todo, 1):
            rows = []
            for ep in ("otherReports", "financialReports"):
                rows += [r for r in list_filings(ep, m["PSE_Company_ID"], frm, to) if r["Form"] in WANTED_FORMS]
            if not rows:  # keep a marker so the company is not re-queried
                rows = [{"Edge_No": "", "Endpoint": "", "Template": "NO_RELEVANT_FILING", "Form": "", "Announced": "", "Report_No": ""}]
            for r in rows:
                w.writerow({"PSE_Company_ID": m["PSE_Company_ID"], "Symbol": m["Symbol"], **r})
            f.flush()
            if i % 20 == 0:
                print(f"indexed {i}/{len(todo)}", flush=True)
    print("done ->", out_path)


if __name__ == "__main__":
    main()

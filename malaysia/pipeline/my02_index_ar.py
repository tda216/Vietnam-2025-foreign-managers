"""Malaysia step 2 – annual-report index (no PDFs downloaded).

Source: klse.i3investor.com, which republishes Bursa annual-report announcements per stock
(financial year end, announcement date, attachment file names). Bursa itself blocks scripts.

Phase A  list page per stock code     -> raw/i3/list/<code>.html  -> data/ar_index.csv
Phase B  detail page for the reports needed under the owner rules (calendar-2025 managers):
         FY ending in 2025, plus FY ending in 2026 when the year end is not December
                                        -> raw/i3/detail/<code>_<fye>.html -> data/ar_attachments.csv
Cached pages are reused (resumable); 1 request per second.

Run from the project root:  .venv/bin/python -I malaysia/pipeline/my02_index_ar.py [k n]
(k n = shard k of n; run the shards in sequence or in parallel, then once without arguments
to merge every cached page into the CSVs.)
"""
import csv, datetime as dt, html, json, re, sys, time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UNIV = ROOT / "data" / "universe.csv"
RAW = ROOT / "raw" / "i3"
IDX = ROOT / "data" / "ar_index.csv"
ATT = ROOT / "data" / "ar_attachments.csv"
BASE = "https://klse.i3investor.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SESSION = requests.Session(); SESSION.headers["User-Agent"] = UA


def fetch(url, path):
    if path.exists() and path.stat().st_size > 0:
        return path.read_text(encoding="utf-8", errors="ignore"), False
    for attempt in range(3):
        try:
            r = SESSION.get(url, timeout=60)
            if r.status_code == 404:
                path.write_text("<!-- 404 -->", encoding="utf-8"); return "", True
            if r.status_code == 200:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(r.text, encoding="utf-8"); return r.text, True
            print(f"HTTP {r.status_code} {url} (attempt {attempt + 1})", flush=True)
        except requests.RequestException as e:
            print(f"{type(e).__name__} {url} (attempt {attempt + 1})", flush=True)
        time.sleep(30 * (attempt + 1))  # rate limited: back off (3 shards in parallel hit the limit)
    return None, True


def fye_date(s):
    try:
        return dt.datetime.strptime(s, "%d-%b-%Y").date()
    except ValueError:
        return None


def needed(rows):
    """FY ending in 2025, plus FY ending in 2026 when the year end is not 31 December."""
    out = []
    for r in rows:
        d = fye_date(r["FY_End"])
        if d and (d.year == 2025 or (d.year == 2026 and (d.month, d.day) != (12, 31))):
            out.append(r)
    return out


def main():
    args = [a for a in sys.argv[1:]]
    k, n = (int(args[0]), int(args[1])) if len(args) == 2 else (0, 1)
    univ = [u for u in csv.DictReader(UNIV.open(encoding="utf-8"))
            if u["Exchange"] == "MK" and u["Stock_Code"] and u["In_Scope"] != "0"]
    codes = sorted({u["Stock_Code"] for u in univ})
    mine = [c for i, c in enumerate(codes) if i % n == k]
    idx_rows, att_rows, net = [], [], 0
    for i, code in enumerate(mine):
        t, hit = fetch(f"{BASE}/web/stock/financial-annual-report/{code}", RAW / "list" / f"{code}.html")
        net += hit
        if hit:
            time.sleep(1)
        rows = []
        m = re.search(r"var dtdata\s*=\s*(\[.*?\]);", t or "", re.S)
        for row in json.loads(m.group(1)) if m else []:
            rows.append({"Stock_Code": code, "FY_End": row[0], "Audited_Account_Ann_Date": row[1],
                         "AR_Ann_Date": row[2], "Detail_URL": BASE + row[5] if row[5] else "",
                         "List_Status": "OK"})
        if not rows:
            rows = [{"Stock_Code": code, "FY_End": "", "Audited_Account_Ann_Date": "", "AR_Ann_Date": "",
                     "Detail_URL": "", "List_Status": "NO_PAGE" if t is None or t.startswith("<!-- 404") else "NO_ROWS"}]
        idx_rows += rows
        for r in needed(rows):
            if not r["Detail_URL"] or not r["AR_Ann_Date"]:
                continue
            key = f"{code}_{fye_date(r['FY_End']).isoformat()}"
            t2, hit = fetch(r["Detail_URL"], RAW / "detail" / f"{key}.html")
            net += hit
            if hit:
                time.sleep(1)
            for sid, name in re.findall(r"href='/web/staticfile/view/(\d+)'><i[^>]*></i>([^<]+)</a>", t2 or ""):
                att_rows.append({"Stock_Code": code, "FY_End": r["FY_End"], "AR_Ann_Date": r["AR_Ann_Date"],
                                 "Attachment_Name": html.unescape(name).strip(), "i3_Staticfile_ID": sid,
                                 "Detail_URL": r["Detail_URL"]})
        if (i + 1) % 50 == 0:
            print(f"shard {k}/{n}: {i + 1}/{len(mine)} codes, {net} requests", flush=True)
    if n == 1:
        for path, rows in ((IDX, idx_rows), (ATT, att_rows)):
            with path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0]))
                w.writeheader(); w.writerows(rows)
        print("codes", len(mine), "index rows", len(idx_rows), "attachments", len(att_rows))
        print("list status:", {s: sum(1 for r in idx_rows if r["List_Status"] == s) for s in ("OK", "NO_ROWS", "NO_PAGE")})
    print(f"shard {k}/{n} done, {net} network requests")


if __name__ == "__main__":
    main()

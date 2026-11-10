"""Malaysia step 3a – annual reports hosted by InSage (insage.com.my), an IR-website provider.

InSage builds the investor-relations pages of many Bursa issuers and serves the annual-report PDFs
from its own server (downloading.aspx?sFileName=...&sReportType=AR). Non-clients get
"Unavailable Page". One small page per stock code:
  raw/insage/<code>.html  ->  data/insage_ar.csv  (Stock_Code, Label, Report_Type, sFileName, URL)

Run from the project root:  .venv/bin/python -I malaysia/pipeline/my03a_insage.py
"""
import csv, html, re, time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw" / "insage"
OUT = ROOT / "data" / "insage_ar.csv"
URL = "https://www.insage.com.my/ir/cmn/trps02/ArTop.aspx?Symbol={}"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def main():
    s = requests.Session(); s.headers["User-Agent"] = UA
    codes = sorted({u["Stock_Code"] for u in csv.DictReader((ROOT / "data" / "universe.csv").open(encoding="utf-8"))
                    if u["Exchange"] == "MK" and u["Stock_Code"] and u["In_Scope"] != "0"})
    rows, clients = [], 0
    for i, code in enumerate(codes):
        p = RAW / f"{code}.html"
        if not p.exists():
            try:
                r = s.get(URL.format(code), timeout=60)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(r.text if r.status_code == 200 else f"<!-- HTTP {r.status_code} -->", encoding="utf-8")
            except requests.RequestException as e:
                print(code, "error", e); continue
            time.sleep(0.7)
        t = p.read_text(encoding="utf-8", errors="ignore")
        found = re.findall(r"<h4>([^<]+)</h4>\s*(?:<div[^>]*>)?\s*<a href=\"(https://www\.insage\.com\.my/ir/cmn/downloading\.aspx\?sFileName=(\d+)&(?:amp;)?sReportType=(\w+)[^\"]*)\"", t)
        clients += bool(found)
        for label, url, fn, rtype in found:
            rows.append({"Stock_Code": code, "Label": html.unescape(label).strip(), "Report_Type": rtype,
                         "sFileName": fn, "URL": html.unescape(url)})
        if (i + 1) % 100 == 0:
            print(f"{i + 1}/{len(codes)} codes, {clients} InSage clients", flush=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Stock_Code", "Label", "Report_Type", "sFileName", "URL"])
        w.writeheader(); w.writerows(rows)
    print("codes", len(codes), "InSage clients", clients, "report links", len(rows))


if __name__ == "__main__":
    main()

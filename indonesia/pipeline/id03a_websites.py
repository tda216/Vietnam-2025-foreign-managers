"""Indonesia step 3a – company website per company (only used to find annual reports; not evidence).

idx.co.id (company profiles) blocks scripts, so the website comes from
  1. stockanalysis.com company page  /quote/idx/<code>/company/  (robots.txt allows /quote/; one request at a
     time, 1.5 s pause; only the contact block is cached in raw/stockanalysis/<code>.txt)
  2. Wikidata (P856 official website of items listed on IDX, Q1661737), one SPARQL query cached in
     raw/wikidata/idx_sites.csv – fallback when stockanalysis has none
  3. data/manual/websites_manual.csv (Code, Website, Reason) – overrides both

Output  data/websites.csv  Code, Company, Website, Website_Source, Website_Stockanalysis, Website_Wikidata,
        Fiscal_Year_Stockanalysis (e.g. "January - December"; a screen for non-December year ends, not evidence)

Run from the project root:  .venv/bin/python -I indonesia/pipeline/id03a_websites.py
"""
import csv, re, time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SPARQL = ("SELECT ?item ?ticker ?isin ?site WHERE { ?item p:P414 ?st . ?st ps:P414 wd:Q1661737 . "
          "OPTIONAL { ?st pq:P249 ?ticker } OPTIONAL { ?item wdt:P946 ?isin } OPTIONAL { ?item wdt:P856 ?site } }")


def wikidata():
    p = RAW / "wikidata" / "idx_sites.csv"
    if not p.exists():
        r = requests.get("https://query.wikidata.org/sparql", params={"query": SPARQL}, timeout=120,
                         headers={"Accept": "text/csv", "User-Agent": "research-dataset-bot/0.1 (academic research)"})
        r.raise_for_status()
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(r.text, encoding="utf-8")
    by_t, by_i = {}, {}
    for r in csv.DictReader(p.open(encoding="utf-8")):
        if r["site"]:
            by_t.setdefault(r["ticker"].strip().upper(), r["site"]); by_i.setdefault(r["isin"], r["site"])
    return by_t, by_i


def stockanalysis(code, s):
    p = RAW / "stockanalysis" / f"{code}.txt"
    if not p.exists():
        for attempt in range(3):
            try:
                r = s.get(f"https://stockanalysis.com/quote/idx/{code}/company/", timeout=60)
            except requests.RequestException:
                r = None
            time.sleep(1.5)
            if r is not None and r.status_code in (200, 404):
                break
            print(code, "HTTP", r.status_code if r is not None else "none", "attempt", attempt + 1, flush=True)
            time.sleep((10, 30, 60)[attempt])
        else:
            return None, ""
        k = r.text.find("contact:{") if r.status_code == 200 else -1
        snippet = r.text[k:k + 1500] if k >= 0 else f"<!-- HTTP {r.status_code}, no contact block -->"
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(snippet, encoding="utf-8")
    t = p.read_text(encoding="utf-8")
    m, fy = re.search(r'website:"([^"]+)"', t), re.search(r'fiscalYear:"([^"]+)"', t)
    return (m.group(1).strip() if m else ""), (fy.group(1) if fy else "")


def main():
    uni = [r for r in csv.DictReader((ROOT / "data" / "universe.csv").open(encoding="utf-8"))
           if r["Security_Kind"] == "COMPANY" and r["Exchange"] == "IJ"]
    man_p = ROOT / "data" / "manual" / "websites_manual.csv"
    manual = {r["Code"]: r for r in csv.DictReader(man_p.open(encoding="utf-8"))} if man_p.exists() else {}
    by_t, by_i = wikidata()
    s = requests.Session(); s.headers["User-Agent"] = UA
    out = []
    for i, u in enumerate(uni):
        c = u["Code"]
        sa, fy = stockanalysis(c, s)
        wd = by_t.get(c) or by_i.get(u["ISIN"], "")
        if c in manual:
            site, src = manual[c]["Website"], "MANUAL"
        elif sa:
            site, src = sa, "STOCKANALYSIS"
        elif wd:
            site, src = wd, "WIKIDATA"
        else:
            site, src = "", "NONE" if sa == "" else "LOOKUP_FAILED"
        out.append({"Code": c, "Company": u["Short_Name"], "Website": site, "Website_Source": src,
                    "Website_Stockanalysis": sa or "", "Website_Wikidata": wd, "Fiscal_Year_Stockanalysis": fy})
        if i % 100 == 99:
            print(i + 1, "done", flush=True)
    with (ROOT / "data" / "websites.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    from collections import Counter
    print(Counter(o["Website_Source"] for o in out))


if __name__ == "__main__":
    main()

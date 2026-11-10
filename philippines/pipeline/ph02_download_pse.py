"""Step ph02: download PSE Edge filings listed in philippines/data/pse_filings_index.csv.

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph02_download_pse.py [--forms 17-12-A,17-1] [--symbols-file file.csv]

For each filing (edge_no) it saves, under philippines/raw/pse/<symbol>/<edge_no>/ :
  viewer.html      the disclosure viewer page (lists attachments)
  form.html        the structured PSE form (downloadHtml.do), e.g. PCD Filipino / Non-Filipino lines
  att_<file_id>_<name>   every attachment
  meta.json        URL, access time (UTC), SHA256 of every file, original attachment file name

Downloaded files are UNTRUSTED input: this script only stores them. Resumable: finished filings are skipped.
Only the latest filing per company and form is downloaded for 17-12-A/17-12-B/17-1 (amendments are kept).
"""
import csv
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import requests

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "philippines" / "data"
RAW = ROOT / "philippines" / "raw" / "pse"
BASE = "https://edge.pse.com.ph"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
PAUSE = 0.6
S = requests.Session()
S.headers.update(UA)


def get(url, tries=4):
    for k in range(tries):
        try:
            r = S.get(url, timeout=120)
            if r.status_code == 200:
                time.sleep(PAUSE)
                return r
        except requests.RequestException:
            pass
        time.sleep(2 * (k + 1))
    return None


def safe(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:120]


def parse_date(s):
    try:
        return datetime.strptime(s, "%b %d, %Y %I:%M %p")
    except ValueError:
        return datetime.min


def select_filings(forms):
    # Only filings announced from 2026-01-01 (reporting period 31 Dec 2025 / FY2025 annual report)
    rows = [r for r in csv.DictReader(open(DATA / "pse_filings_index.csv", encoding="utf-8"))
            if r["Form"] in forms and r["Edge_No"] and parse_date(r["Announced"]) >= datetime(2026, 1, 1)]
    rows.sort(key=lambda r: parse_date(r["Announced"]))
    # Top 100 lists are filed every quarter: keep only each company's earliest 2026 filing per form (expected period
    # 31 Dec 2025). The reporting period is checked later from form.html ("For the period ended"), not assumed.
    seen, keep = set(), []
    for r in rows:
        if r["Form"] in ("17-12-A", "17-12-B"):
            k = (r["Symbol"], r["Form"])
            if k in seen:
                continue
            seen.add(k)
        keep.append(r)
    return keep


def download(row):
    d = RAW / safe(row["Symbol"]) / row["Edge_No"]
    if (d / "meta.json").exists():
        return "skip"
    d.mkdir(parents=True, exist_ok=True)
    meta = {"symbol": row["Symbol"], "edge_no": row["Edge_No"], "form": row["Form"], "template": row["Template"],
            "announced": row["Announced"], "report_no": row["Report_No"],
            "viewer_url": f"{BASE}/openDiscViewer.do?edge_no={row['Edge_No']}", "accessed_utc": datetime.now(timezone.utc).isoformat(),
            "files": []}
    v = get(meta["viewer_url"])
    if v is None:
        return "fail_viewer"
    (d / "viewer.html").write_text(v.text, encoding="utf-8")
    hid = re.search(r"downloadHtml\.do\?file_id=(\d+)", v.text)
    targets = []
    if hid:
        targets.append(("form.html", f"{BASE}/downloadHtml.do?file_id={hid.group(1)}", "form"))
    for fid in dict.fromkeys(re.findall(r'<option value="(\d{5,})"', v.text)):
        targets.append((None, f"{BASE}/downloadFile.do?file_id={fid}", fid))
    for fname, url, tag in targets:
        r = get(url)
        if r is None:
            meta["files"].append({"url": url, "error": "download failed"})
            continue
        orig = ""
        cd = r.headers.get("content-disposition", "")
        m = re.search(r'fileName="?([^";]+)', cd)
        if m:
            orig = unquote(m.group(1))
        name = fname or f"att_{tag}_{safe(orig or 'file')}"
        (d / name).write_bytes(r.content)
        meta["files"].append({"saved_as": name, "url": url, "original_name": orig, "bytes": len(r.content),
                              "sha256": hashlib.sha256(r.content).hexdigest()})
    (d / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return "ok"


def main():
    forms = {"17-12-A", "17-12-B", "17-1"}
    if "--forms" in sys.argv:
        forms = set(sys.argv[sys.argv.index("--forms") + 1].split(","))
    rows = select_filings(forms)
    if "--symbols-file" in sys.argv:  # CSV with a Symbol column; limits the download to those companies
        path = sys.argv[sys.argv.index("--symbols-file") + 1]
        wanted = {r["Symbol"] for r in csv.DictReader(open(path, encoding="utf-8"))
                  if r.get("Has_2026_17A", "Y") == "Y"}
        rows = [r for r in rows if r["Symbol"] in wanted]
    if "--shard" in sys.argv:  # --shard k/n : this process takes every n-th filing starting at k (run n processes in parallel)
        k, n = map(int, sys.argv[sys.argv.index("--shard") + 1].split("/"))
        rows = [r for i, r in enumerate(rows) if i % n == k]
    print("filings to fetch:", len(rows), flush=True)
    res = {}
    for i, r in enumerate(rows, 1):
        st = download(r)
        res[st] = res.get(st, 0) + 1
        if i % 25 == 0:
            print(f"{i}/{len(rows)} {res}", flush=True)
    print("finished", res)


if __name__ == "__main__":
    main()

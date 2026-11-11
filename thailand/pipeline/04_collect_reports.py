"""Step 4 – download each company's Form 56-1 One Report 2025 from the SEC's public disclosure system and unpack it.

Usage: python -I thailand/pipeline/04_collect_reports.py all | pilot | TICKER[:f56/<file>.zip] ... [out=docs_<k>.csv]
       (out= lets parallel workers keep their own list; merge with: 04_collect_reports.py merge)
       (TICKER:path uses a report path read by hand from the factsheet, for tests before step 3 has finished)

The file name comes from the SET factsheet (step 3: data/factsheet.csv, or the factsheet already in the web cache, so
this step never sends extra requests to SET). The zip is downloaded once from market.sec.or.th (robots.txt allows
/public/idisc/Download) to raw/docs/<TICKER>/ with a .meta.json (URL, time, SHA256); PDF members are unpacked
to <zip stem>__zip/ (PDF only, names flattened, size-capped – shared/archives.py). A 403/429 stops the run.
Member_Role: E_FORM (SEC e-form rendering, holds the structured director/executive fields), STRUCTURE (structured
data part), MAIN (the designed report).
Output: data/docs.csv (one row per PDF; rows of earlier runs are kept)
"""
import sys
from importlib import import_module
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

import hashlib
import json
import time
from urllib.parse import urlparse

import requests

import common
from archives import extract_pdfs
from common import now_iso, read_csv, throttle, write_csv
from config import DATA, RAW_DOCS, ROOT, SEC_DOWNLOAD, SET_FACTSHEET

FIELDS = ["Ticker_Local", "Doc_Kind", "Report_Lang", "Report_Path", "Source_URL", "Listing_URL", "Container_File",
          "Member_Name", "Member_Role", "Local_File", "SHA256", "Bytes", "Downloaded_At", "Status"]


def download(url: str, dest: Path, *, tries: int = 6, window: int = 30, min_bytes: int = 50_000) -> dict:
    """Stream url to dest once (dest + .meta.json, same format as common.download). The SEC server sometimes trickles a
    transfer for hours: a transfer that receives less than min_bytes in a window of seconds is dropped and retried."""
    meta_path = dest.with_name(dest.name + ".meta.json")
    if dest.exists() and meta_path.exists():
        return json.loads(meta_path.read_text())
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    for attempt in range(tries):
        throttle(urlparse(url).netloc)
        try:
            with common.session().get(url, timeout=60, stream=True) as r:
                r.raise_for_status()
                h, t0, got = hashlib.sha256(), time.time(), 0
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(1 << 16):
                        f.write(chunk)
                        h.update(chunk)
                        got += len(chunk)
                        if time.time() - t0 > window:
                            if got < min_bytes:
                                raise requests.ConnectionError(f"slow transfer: {got} bytes in {window}s")
                            t0, got = time.time(), 0
                meta = {"url": url, "final_url": r.url, "status": r.status_code, "content_type": r.headers.get("Content-Type", ""),
                        "fetched_at": now_iso(), "sha256": h.hexdigest(), "bytes": tmp.stat().st_size}
            tmp.replace(dest)
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
            return meta
        except requests.RequestException as e:
            tmp.unlink(missing_ok=True)
            if isinstance(e, requests.HTTPError) and e.response is not None and e.response.status_code < 500:
                raise
            time.sleep(10 * (attempt + 1))
    raise requests.ConnectionError(f"gave up after {tries} tries: {url}")


def role(member: str) -> str:
    m = Path(member).name.upper()
    return "STRUCTURE" if "STRUCTURE" in m else ("E_FORM" if m.startswith("E_ONE") or "_E_ONE" in m else "MAIN")


def factsheet_rows(tickers: list[str]) -> dict[str, dict]:
    rows = {r["Ticker_Local"]: r for r in read_csv(DATA / "factsheet.csv")} if (DATA / "factsheet.csv").exists() else {}
    fs = import_module("03_factsheet")
    for t in tickers:
        if t in rows:
            continue
        cached = [common._cache_paths(SET_FACTSHEET.format(lang=lang, ticker=t))[0].exists() for lang in ("en", "th")]
        if cached[0] and (cached[1] or fs.LINK_RE.search(common.fetch_text(SET_FACTSHEET.format(lang="en", ticker=t))[0])):
            rows[t] = fs.parse(t)  # served from the cache
    return rows


def main():
    arg = [a for a in sys.argv[1:] if not a.startswith("out=")] or ["all"]
    out_name = next((a[4:] for a in sys.argv[1:] if a.startswith("out=")), "docs.csv")
    if arg == ["merge"]:  # docs.csv + every worker's docs_*.csv; a ticker's OK rows win over failure rows
        rows = [r for f in [DATA / "docs.csv", *sorted(DATA.glob("docs_*.csv"))] if f.exists() for r in read_csv(f)]
        ok_t = {r["Ticker_Local"] for r in rows if r["Status"] == "OK"}
        seen, merged = set(), []
        for r in rows:
            k = (r["Ticker_Local"], r["Local_File"], r["Status"])
            if k in seen or (r["Status"] != "OK" and r["Ticker_Local"] in ok_t):
                continue
            seen.add(k)
            merged.append(r)
        write_csv(DATA / "docs.csv", merged, FIELDS)
        print(len({r["Ticker_Local"] for r in merged if r["Status"] == "OK"}), "companies with a One Report after merge")
        return
    if arg == ["all"]:
        tickers = [r["Ticker_Local"] for r in read_csv(DATA / "factsheet.csv")]
    elif arg == ["pilot"]:
        tickers = (DATA / "pilot_tickers.txt").read_text().split()
    else:
        tickers = [a.split(":")[0] for a in arg]
    fsrows = factsheet_rows(tickers)
    for a in arg:
        if ":" in a:
            t, path = a.split(":", 1)
            fsrows[t] = {"Report_Path": path, "Report_Lang": path[-5], "Report_Label_Year": "2025",
                         "URL_en": SET_FACTSHEET.format(lang="en", ticker=t)}
    old = read_csv(DATA / out_name) if (DATA / out_name).exists() else []
    done = {r["Ticker_Local"] for r in old if r["Status"] == "OK"}
    out = [r for r in old if r["Status"] == "OK" or r["Ticker_Local"] not in tickers]  # failed tickers are retried
    for i, t in enumerate(tickers, 1):
        f = fsrows.get(t)
        if t in done:
            continue
        if not f or not f.get("Report_Path"):
            out.append({"Ticker_Local": t, "Status": "NO_FACTSHEET" if not f else "NO_REPORT_LINK"})
            continue
        url = SEC_DOWNLOAD.format(path=f["Report_Path"])
        zip_path = RAW_DOCS / t / Path(f["Report_Path"]).name
        base = {"Ticker_Local": t, "Doc_Kind": f"AR{f.get('Report_Label_Year') or ''}", "Report_Lang": f["Report_Lang"],
                "Report_Path": f["Report_Path"], "Source_URL": url, "Listing_URL": f.get("URL_en", "")}
        try:
            meta = download(url, zip_path)
            members = extract_pdfs(zip_path)
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else 0
            if code in (403, 429):
                raise SystemExit(f"{code} from {url} – stopping (no workaround)")
            out.append(base | {"Status": f"HTTP_{code}"})
            continue
        except Exception as e:  # bad zip, network error: recorded, the next run retries
            out.append(base | {"Status": f"ERROR {type(e).__name__}: {e}"[:200]})
            continue
        for name, p in members:
            out.append(base | {"Container_File": str(zip_path.relative_to(ROOT)), "Member_Name": name, "Member_Role": role(name),
                               "Local_File": str(p.relative_to(ROOT)), "SHA256": meta["sha256"], "Bytes": p.stat().st_size,
                               "Downloaded_At": meta["fetched_at"], "Status": "OK"})
        if i % 25 == 0:
            write_csv(DATA / out_name, out, FIELDS)
            print(i, "companies", flush=True)
    write_csv(DATA / out_name, out, FIELDS)
    ok = {r["Ticker_Local"] for r in out if r["Status"] == "OK"}
    print(len(ok), "companies with a One Report |", sum(1 for r in out if r["Status"] != "OK"), "without")


if __name__ == "__main__":
    main()

"""Step 6a – fallback documents for in-scope companies without a readable 2025 annual report (NO_SOURCE in 07).

Usage: python -I pipeline/06a_fallback_docs.py full

For every collected company whose docs.csv has no readable AR2025 PDF (>= 5 pages):
  1. AR2025 archives in RAR format (recorded but not unpacked by the first pass) are unpacked (03b extract_pdfs_rar).
  2. Vietstock annual reports filed under report year 2026 or 2024 (Doc_Kind AR2026 / AR2024: the 2024 report, published
     in 2025, names the managers in office at its date; it is not a FY2025 source and is kept apart).
  3. From the Vietstock index (03b): the annual 2025 governance report (GOV2025) and the 2026 AGM documents
     (AGM2026: board / supervisory reports on 2025, candidate CVs, often the 2025 AR itself).
  4. Links found by hand on company websites: data/manual/fallback_urls.csv (with where and why).
Files go to raw/docs/<TICKER>/fallback/ (archives next to their first-pass copy). Output: data/<run>/docs_fallback.csv
(columns of docs.csv + Found_Via, Note) for 03c (python -I pipeline/03c_extract_text.py full docs_fallback.csv --fast).
"""
import re
import subprocess
import sys
import zipfile
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import download, read_csv, sha256_bytes, write_csv
from config import DATA, RAW_DOCS, ROOT
from sources_vietstock import list_documents, parse_ms_date

cd = import_module("03b_collect_docs")
FIELDS = cd.DOC_FIELDS + ["Found_Via", "Note"]


def no_source_tickers(R: Path) -> list[str]:
    collected = {t for f in (R / "shards").glob("done_*.txt") for t in f.read_text().split()}
    readable = {s["Ticker_Local"] for s in read_csv(R / "pdf_stats.csv")
                if s["Doc_Kind"] == "AR2025" and not s["Error"] and s["N_Pages"] and int(s["N_Pages"]) >= 5}
    return sorted(collected - readable)


def fetch(t: str, kind: str, title: str, url: str, uploaded: str, found_via: str, note: str,
          folder: str = "fallback") -> list[dict]:
    base = {k: "" for k in FIELDS} | {"Ticker_Local": t, "Doc_Kind": kind, "Title": title, "Source_URL": url,
                                      "Uploaded_At": uploaded, "Found_Via": found_via, "Note": note}
    path = url.split("?")[0]  # some links carry "?ver=..."
    parts = path.split("/")
    prefix = "_".join(parts[-5:-3]) if "vietstock" in parts[2] else parts[2]
    dest = RAW_DOCS / t / folder / cd.safe_name(prefix + "_" + parts[-1])
    try:
        meta = download(url, dest)
    except Exception as e:
        return [{**base, "Status": f"DOWNLOAD_ERROR: {e!r}"[:200]}]
    ext = dest.suffix.lower()
    try:
        files = ([("", dest)] if ext == ".pdf" else cd.extract_pdfs(dest) if ext == ".zip"
                 else cd.extract_pdfs_rar(dest) if ext == ".rar" else None)
    except (zipfile.BadZipFile, ValueError, subprocess.CalledProcessError) as e:
        return [{**base, "Local_File": str(dest.relative_to(ROOT)), "Status": f"ARCHIVE_ERROR: {e!r}"[:200]}]
    if files is None:
        return [{**base, "Local_File": str(dest.relative_to(ROOT)), "Status": f"NOT_EXTRACTED_{ext.lstrip('.').upper()}"}]
    return [{**base, "Container_File": str(dest.relative_to(ROOT)) if member else "", "Member_Name": member,
             "Local_File": str(f.relative_to(ROOT)), "SHA256": meta["sha256"] if not member else sha256_bytes(f.read_bytes()),
             "Bytes": f.stat().st_size, "Downloaded_At": meta["fetched_at"], "Status": "OK"} for member, f in files]


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "full"
    R = DATA / run
    tickers = no_source_tickers(R)
    docs = read_csv(R / "docs.csv")
    index = [r for f in sorted((R / "shards").glob("doc_index_*.csv")) for r in read_csv(f)]
    manual = read_csv(DATA / "manual" / "fallback_urls.csv")
    rows = []
    for n, t in enumerate(tickers, 1):
        # 1. RAR annual reports from the first pass
        for d in docs:
            if d["Ticker_Local"] == t and d["Status"] == "NOT_EXTRACTED_RAR":
                for member, f in cd.extract_pdfs_rar(ROOT / d["Local_File"]):
                    rows.append({**{k: d.get(k, "") for k in FIELDS}, "Container_File": d["Local_File"], "Member_Name": member,
                                 "Local_File": str(f.relative_to(ROOT)), "SHA256": sha256_bytes(f.read_bytes()),
                                 "Bytes": f.stat().st_size, "Status": "OK", "Duplicate_Of": "",
                                 "Found_Via": "Vietstock (first pass, RAR unpacked)", "Note": ""})
        # 2. annual reports listed under a neighbouring report year
        for year in (2026, 2024):
            for d in list_documents(t, 2, year):
                rows += fetch(t, f"AR{year}", (d.get("Title") or "").strip(), d["Url"].replace("http://", "https://", 1),
                              parse_ms_date(d.get("LastUpdate", "")), f"Vietstock annual reports, report year {year}",
                              "Check the fiscal year the report covers before use")
        # 3. governance report 2025 and AGM 2026 documents from the index
        for r in index:
            if r["Ticker_Local"] != t:
                continue
            kind = cd.wanted(int(r["Doc_Type_ID"]), int(r["Report_Year"]), r["Title"])
            if kind == "GOV2025" or (r["Doc_Type_ID"] == "5" and r["Report_Year"] == "2026"):
                rows += fetch(t, kind or "AGM2026", r["Title"], r["Url"].replace("http://", "https://", 1), r["Uploaded_At"],
                              "Vietstock index (03b)", "")
        # 4. company websites (found by hand)
        for m in manual:
            if m["Ticker_Local"] == t:
                rows += fetch(t, m["Doc_Kind"], m["Title"], m["Url"], "", m["Found_Via"], m["Note"])
        print(f"{n}/{len(tickers)} {t}: {sum(1 for r in rows if r['Ticker_Local'] == t)} files", flush=True)
    seen_sha = {}
    for r in rows:
        if r["Status"] == "OK":
            r["Duplicate_Of"] = seen_sha.get(r["SHA256"], "")
            seen_sha.setdefault(r["SHA256"], r["Local_File"])
    write_csv(R / "docs_fallback.csv", rows, FIELDS)
    print("companies", len(tickers), "| files", len(rows), "| OK", sum(r["Status"] == "OK" for r in rows),
          "| companies with an OK file", len({r["Ticker_Local"] for r in rows if r["Status"] == "OK"}))


if __name__ == "__main__":
    main()

"""Step 3b/4 – index each company's 2025 disclosure documents on Vietstock and download the key ones.

Usage: python -I vietnam/pipeline/03b_collect_docs.py pilot | full <shard k> <n shards>

Indexed (title + URL, not downloaded): annual reports, governance reports, AGM documents and board
resolutions/notices for report years 2025 and 2026 – the later ones are used to verify candidates.
Downloaded to raw/docs/<TICKER>/: the 2025 annual report(s); in the pilot also the 2025 annual governance report(s).
Zip and RAR archives are unpacked (PDF members only, names flattened, size-capped; RAR with bsdtar from the official
Ubuntu libarchive-tools package, unpacked without root into .tools/bsdtar).

Outputs (data/<run>/): doc_index.csv (every listed document), docs.csv (one row per downloaded PDF).
"""
import csv
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2] / "shared")]  # python -I; country config first
from archives import extract_pdfs, extract_pdfs_rar, safe_name  # shared/; 05b, 05d, 06a call them as cd.*
from common import download, read_csv, sha256_bytes, strip_accents, write_csv
from config import DATA, RAW_DOCS, ROOT
from sources_vietstock import DOC_TYPES, list_documents, parse_ms_date

INDEX_TYPES = [(2, 2025), (9, 2025), (5, 2025), (5, 2026), (23, 2025), (23, 2026)]
DOWNLOAD_KINDS_FULL = {"AR2025"}  # user decision 2026-11-01: other documents only on demand
INDEX_FIELDS = ["Ticker_Local", "Doc_Type_ID", "Doc_Type", "Report_Year", "FileInfoID", "Title", "Url", "Uploaded_At",
                "Source"]
DOC_FIELDS = ["Ticker_Local", "Doc_Kind", "Title", "Source_URL", "Uploaded_At", "Container_File", "Member_Name",
              "Local_File", "SHA256", "Bytes", "Downloaded_At", "Status", "Duplicate_Of"]


def wanted(doc_type: int, year: int, title: str) -> str:
    """Doc_Kind to download, or '' to only index."""
    t = strip_accents(title)
    if doc_type == 2 and year == 2025:
        return "AR2025"
    if doc_type == 9 and year == 2025 and "nam 2025" in t and "6 thang" not in t:
        return "GOV2025"
    return ""


def tickers_for(run: str) -> list[str]:
    if run == "pilot":
        return [r["Ticker_Local"] for r in read_csv(DATA / "pilot_sample.csv")]
    return [c["Ticker_Local"] for c in read_csv(DATA / "companies_step2.csv")
            if c["Manager_Search"] == "1" and c["Security_Class"] == "COMPANY_VN"]


def append_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="raise")
        if new:
            w.writeheader()
        w.writerows(rows)


def collect(t: str, run: str) -> tuple[list[dict], list[dict]]:
    """Index one ticker's documents and download the wanted ones; returns (index rows, doc rows)."""
    index, docs, seen_sha = [], [], {}
    for doc_type, year in INDEX_TYPES:
        for d in list_documents(t, doc_type, year):
            index.append({"Ticker_Local": t, "Doc_Type_ID": doc_type, "Doc_Type": DOC_TYPES.get(doc_type, ""),
                          "Report_Year": year, "FileInfoID": d.get("FileInfoID", ""), "Title": (d.get("Title") or "").strip(),
                          "Url": d.get("Url", ""), "Uploaded_At": parse_ms_date(d.get("LastUpdate", "")),
                          "Source": "Vietstock Finance – Tải tài liệu"})
            kind = wanted(doc_type, year, d.get("Title") or "")
            if not kind or (run != "pilot" and kind not in DOWNLOAD_KINDS_FULL):
                continue
            url = d["Url"].replace("http://", "https://", 1)
            base = {"Ticker_Local": t, "Doc_Kind": kind, "Title": (d.get("Title") or "").strip(), "Source_URL": url,
                    "Uploaded_At": parse_ms_date(d.get("LastUpdate", "")), "Container_File": "", "Member_Name": "",
                    "Local_File": "", "SHA256": "", "Bytes": "", "Downloaded_At": "", "Status": "", "Duplicate_Of": ""}
            # folder per exchange path keeps same-named files from different folders apart
            path = url.split("?")[0]  # some links carry "?ver=..."
            dest = RAW_DOCS / t / safe_name("_".join(path.split("/")[-5:-3]) + "_" + path.split("/")[-1])
            try:
                meta = download(url, dest)
            except Exception as e:
                docs.append({**base, "Status": f"DOWNLOAD_ERROR: {e!r}"[:200]})
                continue
            ext = dest.suffix.lower()
            if ext == ".pdf":
                files = [("", dest)]
            elif ext in (".zip", ".rar"):
                try:
                    files = extract_pdfs(dest) if ext == ".zip" else extract_pdfs_rar(dest)
                except (zipfile.BadZipFile, ValueError, subprocess.CalledProcessError) as e:
                    docs.append({**base, "Local_File": str(dest.relative_to(ROOT)), "Status": f"ZIP_ERROR: {e!r}"[:200]})
                    continue
            else:
                docs.append({**base, "Local_File": str(dest.relative_to(ROOT)), "SHA256": meta["sha256"],
                             "Bytes": meta["bytes"], "Downloaded_At": meta["fetched_at"],
                             "Status": f"NOT_EXTRACTED_{ext.lstrip('.').upper() or 'NOEXT'}"})
                continue
            if not files:
                docs.append({**base, "Local_File": str(dest.relative_to(ROOT)), "Status": "NO_PDF_IN_ARCHIVE"})
            for member, f in files:
                sha = meta["sha256"] if not member else sha256_bytes(f.read_bytes())
                rel = str(f.relative_to(ROOT))
                docs.append({**base, "Container_File": str(dest.relative_to(ROOT)) if member else "",
                             "Member_Name": member, "Local_File": rel, "SHA256": sha, "Bytes": f.stat().st_size,
                             "Downloaded_At": meta["fetched_at"], "Status": "OK", "Duplicate_Of": seen_sha.get(sha, "")})
                seen_sha.setdefault(sha, rel)
    return index, docs


def main():
    """pilot: one pass, writes doc_index.csv/docs.csv. full [k n]: shard k of n (tickers i % n == k), appends
    shards/doc_index_k.csv + shards/docs_k.csv after every company and skips companies already done (resumable)."""
    run = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    out_dir = DATA / run
    tickers = tickers_for(run)
    if run == "pilot":
        index, docs = [], []
        for n, t in enumerate(tickers, 1):
            i, d = collect(t, run)
            index += i
            docs += d
            print(f"{n}/{len(tickers)} {t}: indexed {len(i)}, pdf {sum(r['Status'] == 'OK' for r in d)}", flush=True)
        write_csv(out_dir / "doc_index.csv", index, INDEX_FIELDS)
        write_csv(out_dir / "docs.csv", docs, DOC_FIELDS)
        return
    k, n_shards = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
    mine = [t for i, t in enumerate(tickers) if i % n_shards == k]
    shard_dir = out_dir / "shards"
    done_file = shard_dir / f"done_{k}.txt"
    done = set(done_file.read_text().split()) if done_file.exists() else set()
    for n, t in enumerate(mine, 1):
        if t in done:
            continue
        try:
            i, d = collect(t, run)
        except Exception as e:  # keep going; the company is retried on the next run
            print(f"{n}/{len(mine)} {t}: ERROR {e!r}", flush=True)
            continue
        append_csv(shard_dir / f"doc_index_{k}.csv", i, INDEX_FIELDS)
        append_csv(shard_dir / f"docs_{k}.csv", d, DOC_FIELDS)
        with done_file.open("a") as f:
            f.write(t + "\n")
        print(f"{n}/{len(mine)} {t}: indexed {len(i)}, pdf {sum(r['Status'] == 'OK' for r in d)}", flush=True)


if __name__ == "__main__":
    main()

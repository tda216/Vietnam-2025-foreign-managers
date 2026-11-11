"""Step 5b – download, on demand, the documents most likely to state a candidate's nationality.

Usage: python -I vietnam/pipeline/05b_verify_docs.py pilot|full

Only for companies with an unsettled HIGH-priority candidate (05a) or, in today's CafeF roster (03d), a name with
>= 2 non-Vietnamese tokens. From the Vietstock index (03b):
AGM documents for 2025 and 2026 (candidate CVs, "Thông tin cá nhân của ứng cử viên") and board resolutions /
notices whose title is about personnel (appointment, election, resignation, insider information form).
Files go to raw/docs/<TICKER>/verify/; the list is written as data/<run>/docs_verify.csv for 03c
(python -I vietnam/pipeline/03c_extract_text.py <run> docs_verify.csv).
"""
import re
import sys
from importlib import import_module
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2] / "shared")]  # python -I; country config first
from common import download, read_csv, sha256_bytes, strip_accents, write_csv
from config import DATA, RAW_DOCS, ROOT

cd = import_module("03b_collect_docs")
cand = import_module("05a_candidates")
PERSONNEL = re.compile(r"nhan su|bo nhiem|mien nhiem|tu nhiem|bau |bau bo sung|ung cu|de cu|cung cap thong tin|nguoi noi bo"
                       r"|thanh vien hdqt|thanh vien hoi dong|tong giam doc|ban kiem soat|ly lich")
FIELDS = ["Ticker_Local", "Doc_Kind", "Title", "Source_URL", "Container_File", "Member_Name", "Local_File", "SHA256",
          "Bytes", "Downloaded_At", "Status", "Duplicate_Of"]


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    out_dir = DATA / run
    cands = ([c for c in read_csv(out_dir / "candidates.csv") if c["Priority"] == "HIGH" and c["Settled"] != "1"]
             if (out_dir / "candidates.csv").exists() else [])
    tickers = {c["Ticker_Local"] for c in cands}
    if (out_dir / "roster_cafef.csv").exists():  # today's roster: names with >= 2 non-Vietnamese tokens (prefetch)
        tickers |= {r["Ticker_Local"] for r in read_csv(out_dir / "roster_cafef.csv")
                    if r["Name_Screen"] == "NON_VN_STYLE" and cand.non_vn_tokens(re.sub(r"^(Ông|Bà)\s+", "", r["Name_Raw"])) >= 2}
    if (out_dir / "docs_verify.csv").exists():  # keep companies fetched in an earlier pass (their candidates may be settled now)
        tickers |= {r["Ticker_Local"] for r in read_csv(out_dir / "docs_verify.csv")}
    tickers = sorted(tickers)
    if run == "full":
        index = [r for f in sorted((out_dir / "shards").glob("doc_index_*.csv")) for r in read_csv(f)]
    else:
        index = read_csv(out_dir / "doc_index.csv")
    rows, seen = [], set()
    for n, t in enumerate(tickers, 1):
        for r in index:
            if r["Ticker_Local"] != t:
                continue
            title = strip_accents(r["Title"])
            if not (r["Doc_Type_ID"] == "5" or (r["Doc_Type_ID"] == "23" and PERSONNEL.search(title))):
                continue
            url = r["Url"].replace("http://", "https://", 1)
            if url in seen:
                continue
            seen.add(url)
            kind = ("AGM" if r["Doc_Type_ID"] == "5" else "BOARD") + r["Report_Year"]
            base = {"Ticker_Local": t, "Doc_Kind": kind, "Title": r["Title"], "Source_URL": url, "Container_File": "",
                    "Member_Name": "", "Local_File": "", "SHA256": "", "Bytes": "", "Downloaded_At": "", "Status": "",
                    "Duplicate_Of": ""}
            path = url.split("?")[0]  # some links carry "?ver=..."
            dest = RAW_DOCS / t / "verify" / cd.safe_name("_".join(path.split("/")[-5:-3]) + "_" + path.split("/")[-1])
            try:
                meta = download(url, dest)
            except Exception as e:
                rows.append({**base, "Status": f"DOWNLOAD_ERROR: {e!r}"[:200]})
                continue
            ext = dest.suffix.lower()
            try:
                files = ([("", dest)] if ext == ".pdf" else cd.extract_pdfs(dest) if ext == ".zip"
                         else cd.extract_pdfs_rar(dest) if ext == ".rar" else None)
            except Exception as e:
                rows.append({**base, "Local_File": str(dest.relative_to(ROOT)), "Status": f"ZIP_ERROR: {e!r}"[:200]})
                continue
            if files is None:
                rows.append({**base, "Local_File": str(dest.relative_to(ROOT)), "Status": f"NOT_EXTRACTED_{ext.lstrip('.').upper()}"})
                continue
            for member, f in files:
                rows.append({**base, "Container_File": str(dest.relative_to(ROOT)) if member else "", "Member_Name": member,
                             "Local_File": str(f.relative_to(ROOT)),
                             "SHA256": meta["sha256"] if not member else sha256_bytes(f.read_bytes()),
                             "Bytes": f.stat().st_size, "Downloaded_At": meta["fetched_at"], "Status": "OK"})
        print(f"{n}/{len(tickers)} {t}: {sum(1 for r in rows if r['Ticker_Local'] == t)} files", flush=True)
    seen_sha = {}
    for r in rows:
        if r["Status"] == "OK":
            r["Duplicate_Of"] = seen_sha.get(r["SHA256"], "")
            seen_sha.setdefault(r["SHA256"], r["Local_File"])
    write_csv(out_dir / "docs_verify.csv", rows, FIELDS)
    print("companies", len(tickers), "| files", len(rows), "| OK", sum(r["Status"] == "OK" for r in rows))


if __name__ == "__main__":
    main()

"""Step 5d – older issuer documents for candidates whose nationality is still open (user decision 2026-11-01: search further).

Usage: python -I pipeline/05d_older_docs.py full [k n] [years=2020,2019,2018 out=docs_verify_old2]
       (shard k of n; the shard that finishes last merges; years/out default to YEARS and docs_verify_old)

Board members elected in earlier terms have their candidate CV ("Sơ yếu lý lịch", "Thông tin ứng cử viên") and insider
information forms in the AGM documents and personnel notices of the year they were elected. For every company with an
unsettled HIGH candidate (05a), this indexes Vietstock AGM documents (type 5) and board resolutions / notices (type 23) for
report years YEARS and downloads AGM documents whose title can hold CVs (AGM_CV, not AGM_SKIP) and personnel notices.
Files go to raw/docs/<TICKER>/verify_old/; the list is data/<run>/docs_verify_old.csv for 03c
(python -I pipeline/03c_extract_text.py full docs_verify_old.csv --fast [--no-ocr]).
"""
import re
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import read_csv, strip_accents, write_csv
from config import DATA
from sources_vietstock import list_documents, parse_ms_date

cd = import_module("03b_collect_docs")
vd = import_module("05b_verify_docs")
fb = import_module("06a_fallback_docs")
YEARS = (2024, 2023, 2022, 2021)
# AGM documents that can hold candidate CVs; minutes, resolutions and English copies are skipped
AGM_CV = re.compile(r"tai lieu|ung cu|de cu|ly lich|nhan su|bau |bau bo sung|thong tin|ho so|to trinh")
CANDIDATE_DOC = re.compile(r"ung cu|de cu|ly lich|ho so|ung vien|bau |bau bo sung|nhan su|thong tin ca nhan")
AGM_SKIP = re.compile(r"bien ban|nghi quyet|english|tieng anh|\(en\)|\ben\b|ket qua|bao cao tai chinh")


def main():
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    sys.argv = [a for a in sys.argv if "=" not in a]
    years = tuple(int(y) for y in opts["years"].split(",")) if "years" in opts else YEARS
    out = opts.get("out", "docs_verify_old")
    run = sys.argv[1] if len(sys.argv) > 1 else "full"
    R = DATA / run
    tickers = sorted({c["Ticker_Local"] for c in read_csv(R / "candidates.csv") if c["Priority"] == "HIGH" and c["Settled"] != "1"})
    if len(sys.argv) > 3:  # shard k of n, written to docs_verify_old_<k>.csv (merged by the last shard to finish)
        k, nsh = int(sys.argv[2]), int(sys.argv[3])
        tickers = [t for i, t in enumerate(tickers) if i % nsh == k]
    rows = []
    for n, t in enumerate(tickers, 1):
        for year in years:
            for doc_type in (5, 23):
                docs = list_documents(t, doc_type, year)
                if doc_type == 5:  # documents about candidates first; the whole AGM pack only when the year has none
                    agm = [d for d in docs if AGM_CV.search(strip_accents((d.get("Title") or "").lower()))
                           and not AGM_SKIP.search(strip_accents((d.get("Title") or "").lower()))]
                    specific = [d for d in agm if CANDIDATE_DOC.search(strip_accents((d.get("Title") or "").lower()))]
                    docs = specific or agm
                for d in docs:
                    title = (d.get("Title") or "").strip()
                    if doc_type == 23 and not vd.PERSONNEL.search(strip_accents(title.lower())):
                        continue
                    kind = ("AGM" if doc_type == 5 else "BOARD") + str(year)
                    for r in fb.fetch(t, kind, title, d["Url"].replace("http://", "https://", 1), parse_ms_date(d.get("LastUpdate", "")),
                                      f"Vietstock type {doc_type}, report year {year}", "", folder="verify_old"):
                        rows.append(r)
        print(f"{n}/{len(tickers)} {t}: {sum(1 for r in rows if r['Ticker_Local'] == t)} files", flush=True)
    seen_sha = {}
    for r in rows:
        if r["Status"] == "OK":
            r["Duplicate_Of"] = seen_sha.get(r["SHA256"], "")
            seen_sha.setdefault(r["SHA256"], r["Local_File"])
    if len(sys.argv) > 3:
        write_csv(R / f"{out}_{sys.argv[2]}.csv", rows, fb.FIELDS)
        parts = [R / f"{out}_{i}.csv" for i in range(int(sys.argv[3]))]
        if not all(f.exists() for f in parts):
            print("shard written; waiting for the other shards")
            return
        rows = [r for f in parts for r in read_csv(f)]
    write_csv(R / f"{out}.csv", rows, fb.FIELDS)
    print("companies", len(tickers), "| files", len(rows), "| OK", sum(r["Status"] == "OK" for r in rows))


if __name__ == "__main__":
    main()

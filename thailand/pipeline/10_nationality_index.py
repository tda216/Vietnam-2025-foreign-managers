"""Step 10 – page-text cache and an index of every nationality statement in all downloaded One Reports.

1. Page text of every PDF member (docs.csv Status OK) is written once to data/full/text/<TICKER>/<member>.jsonl.gz
   (one JSON string per page, 1-based page = line number). Later steps search this cache instead of re-reading PDFs.
2. Every statement of the form "Nationality: X" / "Nationality X" / "Age 59 Years / Malaysian" / "สัญชาติ X" (except the
   template line "Thai nationality: Yes/No" / "สัญชาติไทย: ใช่/ไม่ใช่") is written to data/nationality_index.csv with the
   250 characters before it and 120 after it, so that the profile it belongs to can be matched to a person by name –
   in the same company's report or in another issuer's report (rule NATIONALITY_FROM_OTHER_ISSUER).
Usage: python -I thailand/pipeline/10_nationality_index.py [workers]
"""
import gzip
import json
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

from common import read_csv, write_csv
from config import DATA, NATIONALITY_EN, ROOT

TEXT = DATA / "full" / "text"
STATEMENT = [
    ("LABEL", re.compile(r"(?i)(?<!thai )nationality\s*[:：]?\s*([A-Za-z]+(?:\s*\(Taiwan\))?)")),
    ("AGE_SLASH", re.compile(r"(?i)\b\d{2}\s*(?:years?(?:\s*old)?)?\s*/\s*([A-Za-z]+)")),
    ("LABEL_TH", re.compile(r"สัญชาติ(?!ไทย\s*[:：])\s*[:：]?\s*([฀-๿]+)")),
]


def cache_path(local_file: str) -> Path:
    p = Path(local_file)
    return TEXT / p.parts[2] / (p.parent.name + "__" + p.stem + ".jsonl.gz")  # raw/docs/<T>/<zip dir>/<member>


def pages(local_file: str) -> list[str]:
    """Page texts (whitespace collapsed) from the cache, building it on first use."""
    cp = cache_path(local_file)
    if cp.exists():
        with gzip.open(cp, "rt", encoding="utf-8") as f:
            return [json.loads(line) for line in f]
    import pymupdf
    out = [re.sub(r"\s+", " ", p.get_text()) for p in pymupdf.open(ROOT / local_file)]
    cp.parent.mkdir(parents=True, exist_ok=True)
    tmp = cp.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        f.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in out)
    tmp.rename(cp)
    return out


def scan(d: dict) -> list[dict]:
    hits = []
    try:
        texts = pages(d["Local_File"])
    except Exception as e:  # a broken member is reported, not fatal
        return [{"Ticker_Local": d["Ticker_Local"], "Local_File": d["Local_File"], "Pattern": "ERROR", "Value_Raw": str(e)[:200]}]
    for i, x in enumerate(texts, 1):
        for pat, rx in STATEMENT:
            for m in rx.finditer(x):
                v = m.group(1).strip()
                nat = NATIONALITY_EN.get(v.lower(), "")
                if not nat:
                    continue
                hits.append({"Ticker_Local": d["Ticker_Local"], "Local_File": d["Local_File"], "Page": i, "Pattern": pat,
                             "Value_Raw": v, "Nationality": nat, "Before": x[max(0, m.start() - 250):m.start()],
                             "After": x[m.end():m.end() + 120]})
    return hits


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    docs = [d for d in read_csv(DATA / "docs.csv") if d["Status"] == "OK" and d["Local_File"].lower().endswith(".pdf")]
    docs = list({d["Local_File"]: d for d in docs}.values())
    out = []
    with ProcessPoolExecutor(workers) as ex:
        for k, hits in enumerate(ex.map(scan, docs, chunksize=4), 1):
            out.extend(hits)
            if k % 100 == 0:
                print(f"{k}/{len(docs)} files | hits {len(out)}", flush=True)
    write_csv(DATA / "nationality_index.csv", out, ["Ticker_Local", "Local_File", "Page", "Pattern", "Value_Raw", "Nationality",
                                                    "Before", "After"])
    from collections import Counter
    print("files", len(docs), "| statements", len(out), dict(Counter(h["Nationality"] for h in out).most_common(15)))


if __name__ == "__main__":
    main()

"""Indonesia step 2 – foreign-ownership bounds from the KSEI holding-composition file.

KSEI (Indonesia's central securities depository) publishes, per security, the shares held in KSEI custody
by local and foreign investors of nine types. Shares outside KSEI custody (e.g. scrip blocks of controlling
holders) are not in the file, so per company:
    FO_Lower = foreign holdings at KSEI / Sec. Num   (all shares outside KSEI assumed local)
    FO_Upper = 1 - local holdings at KSEI / Sec. Num (all shares outside KSEI assumed foreign)
KSEI_Class = LOCAL (FO_Upper <= 50 %), FOREIGN_MAJORITY (FO_Lower > 50 %), else STRADDLE (owner rule
7 Nov 2026: settle STRADDLE from the AR 2025 shareholder-composition table or the >= 5 % holder list).

Downloads (only if missing) to raw/ksei/BalanceposEfek<date>.zip with a .meta.json (URL, time, SHA-256).
Output  data/fo_ksei_<date>.csv – one row per in-scope company, KSEI columns copied verbatim.

Run from the project root:  .venv/bin/python -I indonesia/pipeline/id02_ksei_fo.py [YYYYMMDD ...]
(default 20251230 = last trading day of 2025)
"""
import csv, datetime as dt, hashlib, json, sys, zipfile
from collections import Counter
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw" / "ksei"
URL = "https://www.ksei.co.id/storage/Download/BalanceposEfek{}.zip"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def fetch(date):
    p = RAW / f"BalanceposEfek{date}.zip"
    meta = p.with_suffix(".zip.meta.json")
    if not p.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        r = requests.get(URL.format(date), headers={"User-Agent": UA}, timeout=120)
        r.raise_for_status()
        if r.content[:2] != b"PK":
            sys.exit(f"{date}: not a zip (HTTP {r.status_code}, {len(r.content)} bytes)")
        p.write_bytes(r.content)
    if not meta.exists():
        meta.write_text(json.dumps({"url": URL.format(date), "file": p.name,
                                    "retrieved_utc": dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc).isoformat(timespec="seconds"),
                                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}, indent=1))
    z = zipfile.ZipFile(p)
    name = z.infolist()[0].filename
    lines = z.read(name).decode("latin-1").splitlines()
    head = lines[0].split("|")
    # header repeats "Total" for local and foreign: rename them
    cols, seen = [], 0
    for h in head:
        if h == "Total":
            h = ["Local Total", "Foreign Total"][seen]; seen += 1
        cols.append(h)
    return name, [dict(zip(cols, l.split("|"))) for l in lines[1:] if l.strip()]


def main():
    dates = sys.argv[1:] or ["20251230"]
    uni = [r for r in csv.DictReader((ROOT / "data" / "universe.csv").open(encoding="utf-8"))
           if r["Security_Kind"] == "COMPANY" and r["Exchange"] == "IJ"]
    for date in dates:
        fname, recs = fetch(date)
        by = {r["Code"]: r for r in recs if r["Type"] == "EQUITY"}
        out, cnt = [], Counter()
        for u in uni:
            k = by.get(u["Code"])
            row = {"Code": u["Code"], "Bloomberg_Ticker": u["Bloomberg_Ticker"], "Short_Name": u["Short_Name"],
                   "KSEI_File": fname}
            if not k:
                row.update({"KSEI_Class": "NOT_IN_FILE"}); cnt["NOT_IN_FILE"] += 1; out.append(row); continue
            n, loc, fo = float(k["Sec. Num"]), float(k["Local Total"]), float(k["Foreign Total"])
            lo, up = fo / n, (n - loc) / n
            cls = "FOREIGN_MAJORITY" if lo > 0.5 else "LOCAL" if up <= 0.5 else "STRADDLE"
            cnt[cls] += 1
            row.update({**{f"KSEI_{c}": v for c, v in k.items() if c != "Code"},
                        "KSEI_Coverage": round((loc + fo) / n, 6), "FO_Lower": round(lo, 6),
                        "FO_Upper": round(up, 6), "KSEI_Class": cls})
            out.append(row)
        cols = list(dict.fromkeys(c for r in out for c in r))
        p = ROOT / "data" / f"fo_ksei_{date}.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
        print(date, fname, dict(cnt), "->", p.relative_to(ROOT.parent))


if __name__ == "__main__":
    main()

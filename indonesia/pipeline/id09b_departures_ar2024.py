"""Indonesia step 9b – nationality of members who LEFT during 2025, from their profile in the AR 2024 (owner 9 Nov 2026).

Input   data/departures.csv (id09; names without a nationality label in the AR 2025) and the AR 2024 files from IDX
        (id03d --year 2024 -> data/idx_ar_files_2024.csv, raw/idx_ar/<CODE>/AR2024_*.pdf; untrusted, read with pymupdf).
For every departed name: pages of the AR 2024 where the name occurs (case-insensitive), and the nationality labels of
id06 within 400 characters of it. Screening only: a foreign result is read (page image) before a record is written;
the record cites the AR 2024 for nationality and the AR 2025 for the leaving date.
Output  data/departures_ar2024.csv  Code, Name, AR2025_Page, Status (FOREIGN / INDONESIAN / NO_LABEL / NAME_NOT_FOUND /
        NO_AR2024), Countries, AR2024_File, AR2024_Page, Snippet
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id09b_departures_ar2024.py
"""
import csv, importlib.util, re
from pathlib import Path

import fitz  # pymupdf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
D = ROOT / "data"
spec = importlib.util.spec_from_file_location("id06", HERE / "id06_screen.py")
id06 = importlib.util.module_from_spec(spec); spec.loader.exec_module(id06)


def rows(name):
    p = D / name
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def labels(t):
    found = []
    for kind, rx in id06.NAT_RES:
        for m in rx.finditer(t):
            if kind != "FOREIGN_NO_COUNTRY":
                found.append(id06.NAT[m.group(1)])
    for m in id06.CIT.finditer(t):
        b = id06.TAIL.search(t, max(0, m.start() - 40), m.start())
        if b:
            found.append(id06.NAT[b.group(1)])
    return found


def main():
    dep = [r for r in rows("departures.csv") if r["Has_Label_Near_Name"] == "0"]
    files = {}
    for r in rows("idx_ar_files_2024.csv"):
        if r.get("File") and r["Check"] not in ("NOT_A_PDF", "DOWNLOAD_FAILED"):
            files.setdefault(r["Code"], []).append(r["File"])
    cache, out = {}, []
    for r in dep:
        c, name = r["Code"], r["Name"].strip()
        base = {"Code": c, "Name": name, "AR2025_Page": r["Page"], "Countries": "", "AR2024_File": "", "AR2024_Page": "", "Snippet": ""}
        if c not in files:
            out.append(dict(base, Status="NO_AR2024")); continue
        best = None
        for f in files[c]:
            if f not in cache:
                try:
                    cache[f] = [id06.norm(p.get_text()) for p in fitz.open(ROOT / f)]
                except Exception:
                    cache[f] = []
            key = id06.norm(name)
            for k, t in enumerate(cache[f]):
                for m in re.finditer(re.escape(key), t):
                    w = t[max(0, m.start() - 400): m.end() + 400]
                    ls = labels(w)
                    if ls and (best is None or not best[2]):
                        best = (f, k + 1, ls, w)
                    elif best is None:
                        best = (f, k + 1, [], w)
        if best is None:
            out.append(dict(base, Status="NAME_NOT_FOUND")); continue
        f, pg, ls, w = best
        if not ls:  # no label within 400 characters: take the labels of the whole page (marked PAGE_LEVEL)
            t = cache[f][pg - 1]
            ls = labels(t)
            if ls:
                w = "PAGE_LEVEL " + w
        foreign = sorted({x for x in ls if x != "Indonesia"})
        st = "FOREIGN" if foreign else "INDONESIAN" if ls else "NO_LABEL"
        out.append(dict(base, Status=st, Countries=";".join(foreign or sorted(set(ls))), AR2024_File=f, AR2024_Page=pg,
                        Snippet=w[:600]))
    keys = ["Code", "Name", "AR2025_Page", "Status", "Countries", "AR2024_File", "AR2024_Page", "Snippet"]
    with (D / "departures_ar2024.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(out)
    from collections import Counter
    print("departed names", len(out), Counter(o["Status"] for o in out))


if __name__ == "__main__":
    main()

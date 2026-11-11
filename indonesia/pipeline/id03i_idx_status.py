"""Indonesia step 3i – trading status 2024–2026 from the IDX announcement titles (11 Nov 2026).

Why: the NO_SOURCE firms are on IDX suspension lists (missing audited FS 2025). This step shows, per firm, whether the
suspension was lifted, whether IDX announced a potential or actual delisting, and since when the stock is suspended.
Titles only – no attachment is downloaded. Same access as id03f / id03h: the announcement API of www.idx.id, one
thread, PAUSE seconds before every request, full stop on 403 / 429 / non-JSON.
Output  data/idx_status_titles.csv  Code, Date, Title, Tag   (Tag = SUSPEND / UNSUSPEND / DELIST_POTENTIAL / DELIST /
        FINE_WARNING / FS_FILED / AR_FILED / OTHER; only tagged titles are kept, plus one NO_TITLES row per empty code)
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id03i_idx_status.py (codes.csv | CODE ...) [--pause 3]
"""
import csv, importlib.util, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = HERE.parent / "data"
API = ("https://www.idx.id/primary/ListedCompany/GetAnnouncement?kodeEmiten={c}&emitenType=*&indexFrom={i}&pageSize=200"
       "&dateFrom=20240101&dateTo=20261111&lang=id&keyword=")
spec = importlib.util.spec_from_file_location("id03f", HERE / "id03f_idx_register.py")
id03f = importlib.util.module_from_spec(spec); spec.loader.exec_module(id03f)
id03d = id03f.id03d
TAGS = [("UNSUSPEND", r"pembukaan (kembali )?(penghentian sementara|suspensi)|pencabutan (penghentian sementara|suspensi)"),
        ("DELIST_POTENTIAL", r"potensi (penghapusan pencatatan|delisting)"),
        ("DELIST", r"penghapusan pencatatan|delisting"),
        ("SUSPEND", r"penghentian sementara perdagangan|suspensi"),
        ("FINE_WARNING", r"peringatan tertulis|denda"),
        ("FS_FILED", r"laporan keuangan (tahunan|auditan)|annual financial|financial statement"),
        ("AR_FILED", r"laporan tahunan|annual report")]


def tag(t):
    for k, rx in TAGS:
        if re.search(rx, t, re.I):
            return k
    return ""


def main():
    args = sys.argv[1:]
    pause = float(args[args.index("--pause") + 1]) if "--pause" in args else 3.0
    rest = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--pause")]
    codes = [r["Code"] for r in csv.DictReader(open(rest[0], encoding="utf-8-sig"))] if rest[0].endswith(".csv") else [c.upper() for c in rest]
    out = []
    try:
        for n, c in enumerate(codes, 1):
            reps, i = [], 0
            while True:
                r = id03d.call(API.format(c=c, i=i), pause)
                if r is None or r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
                    raise id03d.Blocked(f"answer {getattr(r, 'status_code', None)} for {c}")
                page = r.json().get("Replies", [])
                reps += page
                if len(page) < 200:
                    break
                i += 200
            rows = []
            for x in reps:
                a = x["pengumuman"]
                t = re.sub(r"\s+", " ", a.get("JudulPengumuman", "")).strip()
                k = tag(t)
                if k:
                    rows.append({"Code": c, "Date": a.get("TglPengumuman", "")[:10], "Title": t[:240], "Tag": k})
            out += sorted(rows, key=lambda r: r["Date"]) or [{"Code": c, "Date": "", "Title": f"{len(reps)} announcements, none tagged", "Tag": "NO_TITLES"}]
            print(n, c, len(reps), sorted({r["Tag"] for r in rows}), flush=True)
    except id03d.Blocked as e:
        print("BLOCKED – stopping at once:", e, flush=True)
    with (D / "idx_status_titles.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["Code", "Date", "Title", "Tag"]); w.writeheader(); w.writerows(out)
    print(len(out), "rows ->", D / "idx_status_titles.csv")


if __name__ == "__main__":
    main()

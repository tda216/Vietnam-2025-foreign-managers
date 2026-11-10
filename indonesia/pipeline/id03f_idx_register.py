"""Indonesia step 3f – BAE monthly register report for December 2025 from IDX (owner 10 Nov 2026, OPEN_DECISIONS 11a).

"Laporan Bulanan Registrasi Pemegang Efek" is filed by the share registrar (BAE) every month; the December 2025 report
(filed in January 2026) holds "Komposisi Kepemilikan Saham" at 31 Dec 2025 – scrip outside KSEI and KSEI custody, each
split national / foreign – and form X.H.1-1 (holders >= 5 %, column Status A/I = Asing / Indonesia). Used for FO of the
firms still REVIEW after hand reading.
Access: the announcement API of www.idx.id
  /primary/ListedCompany/GetAnnouncement?kodeEmiten=<CODE>&emitenType=*&indexFrom=0&pageSize=50&dateFrom=YYYYMMDD
      &dateTo=YYYYMMDD&lang=id&keyword=
returns attachment links on idx.co.id (which blocks scripts and is never used); the same file sits at
www.idx.id/Portals/0/StaticData/... (the path of the AR downloads, id03d). Same owner rule as id03d: one thread,
PAUSE seconds before every request, full stop on 403 / 429 / non-JSON.
Window: announcements dated 1 Jan – 20 Feb 2026 whose title contains "Registrasi Pemegang Efek"; the earliest one is
taken (= the December report; a later one in February is the January report and is skipped when an earlier exists).
Files are untrusted: saved as data in raw/idx_reg/<CODE>/, opened only with pymupdf, never executed.
Output  data/idx_reg_files.csv  Code, Ann_Date, Title, Part, File, URL, IDX_Original_Name, SHA256, Bytes, Pages, Status
Run from the project root (resumable: codes already in the output with a file are skipped):
  .venv/bin/python -I indonesia/pipeline/id03f_idx_register.py (review | codes.csv | CODE ...) [--pause 3]
  review = the firms with FO_Class REVIEW in data/fo_classification.csv
"""
import csv, datetime as dt, importlib.util, json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
D = ROOT / "data"
OUT = ROOT / "raw" / "idx_reg"
API = ("https://www.idx.id/primary/ListedCompany/GetAnnouncement?kodeEmiten={c}&emitenType=*&indexFrom=0&pageSize=50"
       "&dateFrom={a}&dateTo={b}&lang=id&keyword=")
TITLE = re.compile(r"registrasi\s+pemegang\s+efek", re.I)
spec = importlib.util.spec_from_file_location("id03d", HERE / "id03d_idx_ar.py")
id03d = importlib.util.module_from_spec(spec); spec.loader.exec_module(id03d)
id03 = id03d.id03


def rows(p):
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def www(url):
    """idx.co.id/StaticData/... -> www.idx.id/Portals/0/StaticData/... (same file; idx.co.id is not contacted)."""
    m = re.match(r"https?://(?:www\.)?idx\.co\.id/(?:Portals/0/)?(StaticData/.+)$", url)
    return f"https://www.idx.id/Portals/0/{m.group(1)}" if m else None


def one(code, pause):
    r = id03d.call(API.format(c=code, a="20260101", b="20260220"), pause)
    if r is None or r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
        if r is not None and "json" not in r.headers.get("content-type", ""):
            raise id03d.Blocked(f"non-JSON answer {r.status_code} for {code}")
        return [{"Code": code, "Status": "API_ERROR"}]
    reps = [x for x in r.json().get("Replies", []) if TITLE.search(x.get("pengumuman", {}).get("JudulPengumuman", ""))]
    if not reps:
        return [{"Code": code, "Status": "NO_REGISTER_REPORT"}]
    rep = min(reps, key=lambda x: x["pengumuman"].get("TglPengumuman", ""))
    ann = rep["pengumuman"]
    out = []
    for i, a in enumerate(rep.get("attachments", []), 1):
        base = {"Code": code, "Ann_Date": ann.get("TglPengumuman", "")[:10], "Title": ann.get("JudulPengumuman", "")[:200],
                "Part": i, "IDX_Original_Name": a.get("OriginalFilename", "")}
        url = www(a.get("FullSavePath", ""))
        if not url:
            out.append(dict(base, Status="UNKNOWN_LINK", URL=a.get("FullSavePath", ""))); continue
        time.sleep(pause)
        res = id03.fetch_pdf(url, OUT / code, pause=pause)
        if id03.BLOCKED:
            raise id03d.Blocked(id03.BLOCKED[-1])
        if res is None:
            out.append(dict(base, Status="DOWNLOAD_FAILED", URL=url)); continue
        tmp, h, n, _ = res
        f = OUT / code / f"REG202512_part{i}_{h[:12]}.pdf"
        tmp.replace(f)
        f.with_suffix(".meta.json").write_text(json.dumps({
            "source": "IDX announcement (www.idx.id, owner decision 10 Nov 2026)", "api": API.format(c=code, a="20260101", b="20260220"),
            "url": url, "idx_link": a.get("FullSavePath", ""), "title": ann.get("JudulPengumuman", ""),
            "announcement_date": ann.get("TglPengumuman", ""), "original_name": a.get("OriginalFilename", ""),
            "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "sha256": h, "bytes": n}, indent=1))
        try:
            import fitz  # pymupdf
            pages = len(fitz.open(f))
        except Exception:
            pages = 0
        out.append(dict(base, Status="OK", URL=url, File=str(f.relative_to(ROOT)), SHA256=h, Bytes=n, Pages=pages))
    return out or [{"Code": code, "Status": "NO_ATTACHMENT"}]


def main():
    args = sys.argv[1:]
    pause = float(args[args.index("--pause") + 1]) if "--pause" in args else 3.0
    rest = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--pause")]
    if rest == ["review"]:
        codes = [r["Code"] for r in rows(D / "fo_classification.csv") if r["FO_Class"] == "REVIEW"]
    elif rest and rest[0].endswith(".csv"):
        codes = [r["Code"] for r in csv.DictReader(open(rest[0], encoding="utf-8-sig"))]
    else:
        codes = [c.upper() for c in rest]
    p = D / "idx_reg_files.csv"
    old = rows(p)
    done = {r["Code"] for r in old if r.get("Status") == "OK"}
    todo = [c for c in codes if c not in done]
    print(f"{len(todo)} companies to query ({len(codes) - len(todo)} done), pause {pause}s", flush=True)
    new = []

    def save():
        keep = [r for r in old if r["Code"] not in {x["Code"] for x in new}]
        allr = sorted(keep + new, key=lambda r: (r["Code"], int(r.get("Part") or 0)))
        keys = ["Code", "Ann_Date", "Title", "Part", "File", "URL", "IDX_Original_Name", "SHA256", "Bytes", "Pages", "Status"]
        with p.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(allr)
    try:
        for i, c in enumerate(todo):
            rs = one(c, pause)
            new += rs
            print(i + 1, c, [(r["Status"], r.get("Pages", "")) for r in rs], rs[0].get("Ann_Date", ""), flush=True)
            if (i + 1) % 10 == 0:
                save()
    except id03d.Blocked as e:
        print("BLOCKED – stopping at once:", e, flush=True)
    save()
    from collections import Counter
    print("this run:", Counter(r["Status"] for r in new))


if __name__ == "__main__":
    main()

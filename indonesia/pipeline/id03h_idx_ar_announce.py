"""Indonesia step 3h – AR 2025 filed as an IDX announcement ("Penyampaian Laporan Tahunan ..."), 11 Nov 2026.

Lesson: some issuers file the annual report only as an announcement, not in the IDX financial-report repository that
id03d queries (GetFinancialReport, reportType rda). Example: GIAA, MNCN, WTON, CFIN, ESIP, HOPE, JAST had
"Penyampaian Laporan Tahunan" announcements in Apr–May 2026 while id03d found NO_AR_ON_IDX.
Access as approved for the AR (OPEN_DECISIONS 7a) and the BAE reports (11a): the announcement API of www.idx.id; the
attachment links point to idx.co.id (never contacted) and are fetched from www.idx.id/Portals/0/StaticData/...;
one thread, PAUSE seconds before every request, full stop on 403 / 429 / non-JSON.
Window 1 Jan – 11 Nov 2026; titles with "Laporan Tahunan" (not "Bukti Iklan", "Rencana", "Penjelasan", "Perubahan
Jadwal"). Files are untrusted data: raw/idx_ar_ann/<CODE>/, opened only with pymupdf; checked as id03 (year, AR words,
name in the first pages). The report year is checked again by the content QA of id10 (ar_file_looks_like_2024).
Output  data/idx_ar_ann_files.csv  Code, Ann_Date, Title, Part, File, URL, IDX_Original_Name, SHA256, Bytes, Pages, Check, Status
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id03h_idx_ar_announce.py (codes.csv | CODE ...) [--pause 3]
"""
import csv, datetime as dt, importlib.util, json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
D = ROOT / "data"
OUT = ROOT / "raw" / "idx_ar_ann"
API = ("https://www.idx.id/primary/ListedCompany/GetAnnouncement?kodeEmiten={c}&emitenType=*&indexFrom=0&pageSize=200"
       "&dateFrom=20260101&dateTo=20261111&lang=id&keyword=")
TITLE = re.compile(r"(?i)laporan tahunan|annual report")
NOT_TITLE = re.compile(r"(?i)bukti iklan|rencana|penjelasan|perubahan jadwal|keterlambatan")
spec = importlib.util.spec_from_file_location("id03f", HERE / "id03f_idx_register.py")
id03f = importlib.util.module_from_spec(spec); spec.loader.exec_module(id03f)
id03d, id03 = id03f.id03d, id03f.id03


def rows(p):
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def one(code, pause, names):
    r = id03d.call(API.format(c=code), pause)
    if r is None or r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
        if r is not None and "json" not in r.headers.get("content-type", ""):
            raise id03d.Blocked(f"non-JSON answer {r.status_code} for {code}")
        return [{"Code": code, "Status": "API_ERROR"}]
    reps = [x for x in r.json().get("Replies", []) if TITLE.search(x["pengumuman"].get("JudulPengumuman", ""))
            and not NOT_TITLE.search(x["pengumuman"].get("JudulPengumuman", ""))]
    if not reps:
        return [{"Code": code, "Status": "NO_AR_ANNOUNCEMENT"}]
    out = []
    for rep in sorted(reps, key=lambda x: x["pengumuman"].get("TglPengumuman", "")):
        ann = rep["pengumuman"]
        for i, a in enumerate(rep.get("attachments", []), 1):
            base = {"Code": code, "Ann_Date": ann.get("TglPengumuman", "")[:10], "Title": ann.get("JudulPengumuman", "")[:200],
                    "Part": len(out) + 1, "IDX_Original_Name": a.get("OriginalFilename", "")}
            if not a.get("OriginalFilename", "").lower().endswith(".pdf"):
                continue
            url = id03f.www(a.get("FullSavePath", ""))
            if not url:
                out.append(dict(base, Status="UNKNOWN_LINK", URL=a.get("FullSavePath", ""))); continue
            time.sleep(pause)
            res = id03.fetch_pdf(url, OUT / code, pause=pause)
            if id03.BLOCKED:
                raise id03d.Blocked(id03.BLOCKED[-1])
            if res is None:
                out.append(dict(base, Status="DOWNLOAD_FAILED", URL=url)); continue
            tmp, h, n, _ = res
            f = OUT / code / f"AR2025ANN_part{base['Part']}_{h[:12]}.pdf"
            tmp.replace(f)
            f.with_suffix(".meta.json").write_text(json.dumps({
                "source": "IDX announcement (www.idx.id; owner decisions 8 and 10 Nov 2026)", "api": API.format(c=code),
                "url": url, "idx_link": a.get("FullSavePath", ""), "title": ann.get("JudulPengumuman", ""),
                "announcement_date": ann.get("TglPengumuman", ""), "original_name": a.get("OriginalFilename", ""),
                "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "sha256": h, "bytes": n}, indent=1))
            pages, chk = id03.check_pdf(f, 2025, names.get(code, ""))
            out.append(dict(base, Status="OK", URL=url, File=str(f.relative_to(ROOT)), SHA256=h, Bytes=n, Pages=pages, Check=chk))
    return out or [{"Code": code, "Status": "NO_PDF_ATTACHMENT"}]


def main():
    args = sys.argv[1:]
    pause = float(args[args.index("--pause") + 1]) if "--pause" in args else 3.0
    rest = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--pause")]
    codes = [r["Code"] for r in csv.DictReader(open(rest[0], encoding="utf-8-sig"))] if rest and rest[0].endswith(".csv") else [c.upper() for c in rest]
    names = {u["Code"]: u.get("KSEI_Issuer") or u["Short_Name"] for u in rows(D / "universe.csv")}
    p = D / "idx_ar_ann_files.csv"
    old = rows(p)
    done = {r["Code"] for r in old}
    todo = [c for c in codes if c not in done]
    print(f"{len(todo)} companies to query ({len(codes) - len(todo)} done), pause {pause}s", flush=True)
    new = []

    def save():
        keep = [r for r in old if r["Code"] not in {x["Code"] for x in new}]
        keys = ["Code", "Ann_Date", "Title", "Part", "File", "URL", "IDX_Original_Name", "SHA256", "Bytes", "Pages", "Check", "Status"]
        with p.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader()
            w.writerows(sorted(keep + new, key=lambda r: (r["Code"], int(r.get("Part") or 0))))
    try:
        for i, c in enumerate(todo):
            rs = one(c, pause, names)
            new += rs
            print(i + 1, c, [(r["Status"], r.get("Pages", ""), r.get("Ann_Date", "")) for r in rs][:6], flush=True)
            if (i + 1) % 10 == 0:
                save()
    except id03d.Blocked as e:
        print("BLOCKED – stopping at once:", e, flush=True)
    save()
    from collections import Counter
    print("this run:", Counter(r["Status"] for r in new))


if __name__ == "__main__":
    main()

"""Indonesia step 3d – AR 2025 from IDX through www.idx.id (owner 8 Nov 2026, OPEN_DECISIONS 7).

idx.co.id answers scripts with 403 and is never worked around. The same IDX site at www.idx.id answers normally; the
owner allowed slow scripted downloads there: ONE thread, PAUSE seconds before every request, and a full stop as soon
as the site blocks (403 / 429 / non-JSON answer / challenge page) – then the rest goes back to manual download.

API (the site's own page "Laporan Keuangan dan Tahunan", period "Tahunan"):
  /primary/ListedCompany/GetFinancialReport?indexFrom=0&pageSize=12&year=2025&reportType=rda&EmitenType=s
      &periode=audit&kodeEmiten=<CODE>&SortColumn=KodeEmiten&SortOrder=asc
  -> Results[].Attachments[] (File_Name, File_Path, File_Modified). An annual report may come in parts
     (AnnualReport2025-<CODE>-att1.pdf, att2, ...); ESG / sustainability files are skipped.
Files are untrusted: saved as data (raw/idx_ar/<CODE>/), opened only with pymupdf, never executed.
Check per part as id03 (year + "annual report/laporan tahunan" + name in the first pages); when one part of a set is
VERIFIED, the other parts get SET_VERIFIED (later parts have no title page); with no VERIFIED part, a part whose
first pages show the year is IDX_RECORD (the IDX record – issuer code, report type rda, year – identifies it; e.g. CLAY's
first pages carry only www.cpr.co.id, not the company name).

Output  data/idx_ar_files.csv  Code, Year, Part, File, URL, IDX_File_Name, IDX_File_Modified, SHA256, Bytes, Pages, Check
        data/idx_ar_found.csv  Code, Status (FOUND / NO_AR_ON_IDX / API_ERROR / BLOCKED_STOP), Attachments, Selected
Run from the project root (resumable: companies already FOUND are skipped):
  .venv/bin/python -I indonesia/pipeline/id03d_idx_ar.py (manual | codes.csv | CODE ...) [--pause 3] [--year 2025]
  manual = data/manual_ar_list.csv in priority order; --year 2024 writes idx_ar_found_2024.csv / idx_ar_files_2024.csv
"""
import csv, datetime as dt, importlib.util, json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
D = ROOT / "data"
OUT = ROOT / "raw" / "idx_ar"
BASE = "https://www.idx.id"
API = (BASE + "/primary/ListedCompany/GetFinancialReport?indexFrom=0&pageSize=12&year={y}&reportType=rda&EmitenType=s"
       "&periode=audit&kodeEmiten={c}&SortColumn=KodeEmiten&SortOrder=asc")
AR_NAME = re.compile(r"annual\s*report|laporan\s*tahunan|integrated\s*report|(^|[^a-z])ar[\s_\-]?20\d\d", re.I)
SKIP_NAME = re.compile(r"esg|sustainab|keberlanjutan|(^|[^a-z])sr[\s_\-]?20\d\d", re.I)

spec = importlib.util.spec_from_file_location("id03", HERE / "id03_web_ar.py")
id03 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(id03)  # reuse get / fetch_pdf / check_pdf (same session, user agent, streaming + resume)


class Blocked(Exception):
    pass


def call(url, pause):
    time.sleep(pause)
    r = id03.get(url, 60)
    if r is None:
        return None
    if r.status_code in (403, 429) or "challenge" in r.text[:3000].lower() and "json" not in r.headers.get("content-type", ""):
        raise Blocked(f"{r.status_code} {url}")
    return r


def rows(name):
    p = D / name
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def save(name, rs, key):
    p = D / name
    old = [r for r in rows(name) if r["Code"] not in {x["Code"] for x in rs}]
    allr = sorted(old + rs, key=key)
    if allr:
        with p.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(dict.fromkeys(k for r in allr for k in r)))
            w.writeheader(); w.writerows(allr)


def one(code, year, pause, names):
    r = call(API.format(y=year, c=code), pause)
    if r is None or r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
        if r is not None and "json" not in r.headers.get("content-type", ""):
            raise Blocked(f"non-JSON answer {r.status_code} for {code}")
        return {"Code": code, "Status": "API_ERROR", "Attachments": "", "Selected": ""}, []
    att = [a for res in r.json().get("Results", []) for a in res.get("Attachments", [])
           if str(a.get("File_Type", "")).lower() == ".pdf"]
    pick = [a for a in att if AR_NAME.search(a["File_Name"]) and not SKIP_NAME.search(a["File_Name"])]
    if not pick:
        pick = [a for a in att if not SKIP_NAME.search(a["File_Name"])]  # unnamed parts: keep, the check decides
    found = {"Code": code, "Status": "FOUND" if pick else "NO_AR_ON_IDX",
             "Attachments": ";".join(a["File_Name"] for a in att), "Selected": ";".join(a["File_Name"] for a in pick)}
    files = []
    for i, a in enumerate(sorted(pick, key=lambda a: a["File_Name"])):
        url = BASE + a["File_Path"]
        time.sleep(pause)
        res = id03.fetch_pdf(url, OUT / code, pause=pause)
        if id03.BLOCKED:
            raise Blocked(id03.BLOCKED[-1])
        if res is None:
            files.append({"Code": code, "Year": year, "Part": i + 1, "File": "", "URL": url, "IDX_File_Name": a["File_Name"],
                          "IDX_File_Modified": a.get("File_Modified", ""), "Check": "DOWNLOAD_FAILED"})
            continue
        tmp, h, n, resp = res
        part = re.sub(r"[^A-Za-z0-9]+", "_", Path(a["File_Name"]).stem)[-40:]
        out = OUT / code / f"AR{year}_{part}_{h[:12]}.pdf"
        tmp.replace(out)
        out.with_suffix(".meta.json").write_text(json.dumps({
            "source": "IDX (www.idx.id, owner decision 8 Nov 2026)", "api": API.format(y=year, c=code), "url": url,
            "idx_file_name": a["File_Name"], "idx_file_modified": a.get("File_Modified", ""),
            "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "sha256": h, "bytes": n}, indent=1))
        pages, chk = id03.check_pdf(out, year, names.get(code, ""))
        files.append({"Code": code, "Year": year, "Part": i + 1, "File": str(out.relative_to(ROOT)), "URL": url,
                      "IDX_File_Name": a["File_Name"], "IDX_File_Modified": a.get("File_Modified", ""), "SHA256": h,
                      "Bytes": n, "Pages": pages, "Check": chk})
    return found, settle(files)


def settle(files):
    """One VERIFIED part verifies the set (SET_VERIFIED). Without one, the IDX filing record itself (issuer code,
    report type rda = annual report, year) identifies the file: IDX_RECORD when the first pages show the year."""
    ok = any(f["Check"] == "VERIFIED" for f in files)
    for f in files:
        if f["Check"].startswith("CHECK"):
            f["Check"] = "SET_VERIFIED" if ok else "IDX_RECORD" if "year=1" in f["Check"] else f["Check"]
    return files


def main():
    args = sys.argv[1:]
    opt = lambda k, d: args[args.index(k) + 1] if k in args else d
    pause, year = float(opt("--pause", 3)), int(opt("--year", 2025))
    rest = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] not in ("--pause", "--year"))]
    if rest == ["manual"]:
        codes = [r["Code"] for r in csv.DictReader((D / "manual_ar_list.csv").open(encoding="utf-8-sig"))]
    elif rest and rest[0].endswith(".csv"):
        codes = [r["Code"] for r in csv.DictReader(open(rest[0], encoding="utf-8-sig"))]
    else:
        codes = [c.upper() for c in rest]
    sfx = "" if year == 2025 else f"_{year}"  # other years (e.g. AR 2024 for members who left in 2025) in their own files
    F_FOUND, F_FILES = f"idx_ar_found{sfx}.csv", f"idx_ar_files{sfx}.csv"
    done = {r["Code"] for r in rows(F_FOUND) if r["Status"] == "FOUND"}
    names = {u["Code"]: u.get("KSEI_Issuer") or u["Short_Name"] for u in rows("universe.csv")}
    todo = [c for c in codes if c not in done]
    print(f"{len(todo)} companies to query ({len(codes) - len(todo)} already found), pause {pause}s", flush=True)
    found, files = [], []
    try:
        for i, c in enumerate(todo):
            f, fs = one(c, year, pause, names)
            found.append(f); files += fs
            print(i + 1, c, f["Status"], [x["Check"] for x in fs], flush=True)
            if (i + 1) % 10 == 0:  # save as we go: a stop keeps what was downloaded
                save(F_FOUND, found, lambda r: r["Code"]); save(F_FILES, files, lambda r: (r["Code"], int(r["Part"])))
    except Blocked as e:
        print("BLOCKED – stopping at once:", e, flush=True)
        found.append({"Code": "_STOP_", "Status": "BLOCKED_STOP", "Attachments": str(e), "Selected": dt.datetime.now().isoformat()})
    save(F_FOUND, found, lambda r: r["Code"])
    save(F_FILES, files, lambda r: (r["Code"], int(r["Part"])))
    from collections import Counter
    print("this run:", Counter(f["Status"] for f in found), Counter(x["Check"].split("(")[0] for x in files))


if __name__ == "__main__":
    main()

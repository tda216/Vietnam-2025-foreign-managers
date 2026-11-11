"""Indonesia step 3e – repair IDX downloads that were cut short (lesson 10 Nov 2026).

IDX (www.idx.id, behind Cloudflare) sends reports with Transfer-Encoding: chunked and no Content-Length; the connection
could end cleanly after ~20-30 MB, and the old fetch_pdf took that for a complete file (43 reports: 0 pages, or the
later pages missing). Detection: no "%%EOF" in the last 2 KB of the file. Repair: resume from the bytes already on disk
with an HTTP Range request until the server answers 416 (no further bytes), same owner rule as id03d (one thread,
PAUSE seconds before every request, full stop on 403 / 429).
A repaired file gets its own name (new hash) and replaces the old one in idx_ar_files*.csv; the old partial file is
kept where it was (an ownership row may cite its first pages, which are the same in the full file). Rows of the old
file are dropped from text_index.csv, so id05 extracts the full file next. A file that the server holds at the same
size (416 at once) is left as it is: SOURCE_SAME_SIZE (the issuer's upload itself has no %%EOF).
Files are untrusted data: written to raw/idx_ar/<CODE>/, opened only with pymupdf.
Output  data/idx_repair_log.csv  (Year, Code, Old_File, Old_Bytes, Status, New_File, New_Bytes, Pages, Check)
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id03e_idx_repair.py [--pause 3]
"""
import csv, datetime as dt, importlib.util, json, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
D = ROOT / "data"
spec = importlib.util.spec_from_file_location("id03d", HERE / "id03d_idx_ar.py")
id03d = importlib.util.module_from_spec(spec); spec.loader.exec_module(id03d)
id03 = id03d.id03


def rows(p):
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def write(p, rs):
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(dict.fromkeys(k for r in rs for k in r))); w.writeheader(); w.writerows(rs)


def has_eof(f):
    n = os.path.getsize(f)
    with open(f, "rb") as fh:
        fh.seek(max(0, n - 2048))
        return b"%%EOF" in fh.read()


def main():
    args = sys.argv[1:]
    pause = float(args[args.index("--pause") + 1]) if "--pause" in args else 3.0
    names = {u["Code"]: u.get("KSEI_Issuer") or u["Short_Name"] for u in rows(D / "universe.csv")}
    log_p = D / "idx_repair_log.csv"
    log = rows(log_p)
    seen = {(r["Year"], r["Old_File"]) for r in log if r["Status"] in ("REPAIRED", "SOURCE_SAME_SIZE")}
    replaced = set()
    try:
        for year, name in ((2025, "idx_ar_files.csv"), (2024, "idx_ar_files_2024.csv")):
            p = D / name
            fs = rows(p)
            bad = [r for r in fs if r.get("File") and (ROOT / r["File"]).exists() and not has_eof(ROOT / r["File"])
                   and (str(year), r["File"]) not in seen]
            print(year, len(bad), "files without %%EOF", flush=True)
            for i, r in enumerate(bad):
                old = ROOT / r["File"]; ob = old.stat().st_size
                time.sleep(pause)
                res = id03.fetch_pdf(r["URL"], old.parent, start=old, pause=pause)
                ent = {"Year": year, "Code": r["Code"], "Old_File": r["File"], "Old_Bytes": ob, "New_File": "", "New_Bytes": "",
                       "Pages": "", "Check": "", "Repaired_UTC": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
                if id03.BLOCKED:
                    raise id03d.Blocked(id03.BLOCKED[-1])
                if res is None:
                    print(i + 1, r["Code"], "FAILED", flush=True)
                    log.append(dict(ent, Status="FAILED")); continue
                tmp, h, n, resp = res
                if n == ob:
                    tmp.unlink(missing_ok=True)
                    print(i + 1, r["Code"], "SOURCE_SAME_SIZE", n, flush=True)
                    log.append(dict(ent, Status="SOURCE_SAME_SIZE", New_Bytes=n)); continue
                part = re.sub(r"[^A-Za-z0-9]+", "_", Path(r["IDX_File_Name"]).stem)[-40:]
                out = old.parent / f"AR{year}_{part}_{h[:12]}.pdf"
                tmp.replace(out)
                meta = old.with_suffix(".meta.json")
                m = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
                m.update({"sha256": h, "bytes": n, "repaired_from": r["File"], "repaired_from_bytes": ob,
                          "repaired_utc": ent["Repaired_UTC"], "url": r["URL"]})
                out.with_suffix(".meta.json").write_text(json.dumps(m, indent=1))
                pages, chk = id03.check_pdf(out, year, names.get(r["Code"], ""))
                print(i + 1, r["Code"], "REPAIRED", ob, "->", n, pages, "pages", chk, flush=True)
                log.append(dict(ent, Status="REPAIRED", New_File=str(out.relative_to(ROOT)), New_Bytes=n, Pages=pages, Check=chk))
                r.update({"File": str(out.relative_to(ROOT)), "SHA256": h, "Bytes": n, "Pages": pages, "Check": chk})
                replaced.add((r["Code"], ent["Old_File"]))
                write(p, fs)  # save as we go
            by = {}
            for r in fs:  # settle the sets again (one VERIFIED part verifies its siblings)
                by.setdefault(r["Code"], []).append(r)
            for c, rs in by.items():
                if any(x["File"] in {e["New_File"] for e in log if e["Status"] == "REPAIRED"} for x in rs):
                    for x in rs:
                        if x["Check"] in ("SET_VERIFIED", "IDX_RECORD"):
                            x["Check"] = id03.check_pdf(ROOT / x["File"], year, names.get(c, ""))[1]
                    id03d.settle(rs)
            write(p, fs)
    except id03d.Blocked as e:
        print("BLOCKED – stopping at once:", e, flush=True)
    write(log_p, log)
    ti = rows(D / "text_index.csv")
    keep = [t for t in ti if (t["Code"], t["File"]) not in replaced]
    if len(keep) != len(ti):
        write(D / "text_index.csv", keep)
    from collections import Counter
    print("log:", Counter(e["Status"] for e in log), "; text_index rows dropped:", len(ti) - len(keep))


if __name__ == "__main__":
    main()

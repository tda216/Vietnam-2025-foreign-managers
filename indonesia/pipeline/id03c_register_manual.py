"""Indonesia step 3c – register annual reports downloaded by hand from IDX (raw/manual_ar/<CODE>/*.pdf).

For every PDF without a .meta.json: write one (source IDX_MANUAL, file time, SHA-256, size) and check the first
pages (year 2025 + "annual report"/"laporan tahunan" + company name, as id03). Files are untrusted: opened only
with pymupdf, never executed.

Output  data/manual_ar_files.csv  Code, File, SHA256, Pages, Check
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id03c_register_manual.py
"""
import csv, datetime as dt, hashlib, json, re
from pathlib import Path

import fitz  # pymupdf

ROOT = Path(__file__).resolve().parents[1]
MAN = ROOT / "raw" / "manual_ar"


def check(path, year, company):
    try:
        doc = fitz.open(path)
        text = " ".join(doc[i].get_text() for i in range(min(6, doc.page_count))).lower()
        n = doc.page_count
    except Exception:
        return 0, "NOT_A_PDF"
    first = [w for w in re.findall(r"[a-z]+", company.lower()) if w not in ("pt", "tbk")][:1]
    ok = (str(year) in text, any(k in text for k in ("annual report", "integrated report", "laporan tahunan")),
          bool(first) and first[0] in text)
    if not text.strip():
        return n, "NO_TEXT_LAYER(OCR)"
    return n, "VERIFIED" if all(ok) else "CHECK(year={},ar={},name={})".format(*map(int, ok))


def main():
    uni = {r["Code"]: r for r in csv.DictReader((ROOT / "data" / "universe.csv").open(encoding="utf-8"))}
    out = []
    for f in sorted(MAN.glob("*/*.pdf")) if MAN.exists() else []:
        code = f.parent.name.upper()
        meta = f.with_suffix(".meta.json")
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        if not meta.exists():
            meta.write_text(json.dumps({"source": "IDX_MANUAL", "file": f.name, "sha256": h, "bytes": f.stat().st_size,
                                        "file_time_utc": dt.datetime.fromtimestamp(f.stat().st_mtime, dt.timezone.utc).isoformat(timespec="seconds"),
                                        "registered_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}, indent=1))
        u = uni.get(code, {})
        n, chk = check(f, 2025, u.get("KSEI_Issuer") or u.get("Short_Name", ""))
        out.append({"Code": code, "In_Universe": int(bool(u)), "File": str(f.relative_to(ROOT)), "SHA256": h,
                    "Pages": n, "Check": chk})
    p = ROOT / "data" / "manual_ar_files.csv"
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["Code", "In_Universe", "File", "SHA256", "Pages", "Check"])
        w.writeheader(); w.writerows(out)
    print("registered", len(out), "files;", sum(r["Check"] == "VERIFIED" for r in out), "verified")
    for r in out:
        if r["Check"] != "VERIFIED" or not r["In_Universe"]:
            print("  check:", r["Code"], r["File"], r["Check"], "" if r["In_Universe"] else "(code not in universe)")


if __name__ == "__main__":
    main()

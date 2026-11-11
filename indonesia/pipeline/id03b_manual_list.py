"""Indonesia step 3b – priority list of AR 2025 to download by hand from IDX (owner 8 Nov 2026).

Companies that need the AR 2025 (KSEI_Class LOCAL / STRADDLE, no KSEI holdings; FOREIGN_MAJORITY never – owner
8 Nov 2026) and whose report the script could not reach (data/ar_availability.csv after the second pass), or whose
download gave no checked AR 2025 (data/web_ar_files.csv, reviews in data/manual/ar_file_reviews.csv).
Priority: 1 = pilot company, 2 = FO straddles 50 % (the AR decides the class), 3 = LOCAL.

How to download (idx.co.id blocks scripts, a browser works):
  IDX > Perusahaan Tercatat > Laporan Keuangan & Tahunan (https://www.idx.co.id/id/perusahaan-tercatat/laporan-keuangan-dan-tahunan/)
  -> year 2025, "Tahunan" (annual), company code -> the annual-report PDF (not the financial statements).
  Page confirmed 8 Nov 2026 through the same IDX site at www.idx.id (idx.co.id answers 403 to scripts): title
  "Laporan Keuangan dan Tahunan", filters year, period (Triwulan 1-3, Tahunan) and company.
  Save it unchanged into indonesia/raw/manual_ar/<CODE>/ (one folder per company); id03c registers it.

Output  data/manual_ar_list.csv  (open in Excel; the Done column is for the person downloading)
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id03b_manual_list.py
"""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
IDX_PAGE = "https://www.idx.co.id/id/perusahaan-tercatat/laporan-keuangan-dan-tahunan/"


def rows(name):
    p = D / name
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def main():
    uni = {r["Code"]: r for r in rows("universe.csv") if r["Security_Kind"] == "COMPANY" and r["In_Scope"] == "1"}
    fo = {r["Code"]: r for r in rows("fo_ksei_20251230.csv")}
    av = {r["Code"]: r for r in rows("ar_availability.csv")}
    pilot = {r["Code"] for r in rows("pilot30.csv")}
    tried = {r["Code"] for r in rows("web_ar_found.csv")}  # download attempted (id03 without --check)
    conf = {r["File"] for r in rows("manual/ar_file_reviews.csv") if r["Decision"] == "CONFIRMED_AR2025"}
    rej = {r["File"] for r in rows("manual/ar_file_reviews.csv") if r["Decision"].startswith("REJECTED")}
    got = {r["Code"] for r in rows("web_ar_files.csv") if (r["Check"] == "VERIFIED" or r["File"] in conf) and r["File"] not in rej}
    got |= {r["Code"] for r in rows("idx_ar_files.csv") if r.get("File") and r["Check"] not in ("NOT_A_PDF", "DOWNLOAD_FAILED")}
    # IDX files count even when a scan fails the first-pages check: the IDX record (issuer, rda, year) identifies them
    mcap = sorted(uni, key=lambda c: -float(uni[c]["Market_Cap"] or 0))
    rank = {c: i + 1 for i, c in enumerate(mcap)}
    out = []
    for c, u in uni.items():
        f = fo.get(c, {})
        cls = f.get("KSEI_Class", "NOT_IN_FILE")
        if cls == "FOREIGN_MAJORITY":
            continue  # no AR needed: no manager search for any FM firm (owner, 8 Nov 2026)
        a = dict(av.get(c, {}))
        if c in got:
            continue  # AR 2025 downloaded and checked
        if a.get("Status") == "AVAILABLE_WEBSITE":
            if c not in tried:
                continue  # not downloaded yet: still expected from the website
            a["Status"] = "DOWNLOAD_NO_AR2025"  # link found by --check, but no 2025 report in the download
        grp = "LOCAL" if cls == "LOCAL" else "STRADDLE"
        prio = 1 if c in pilot else {"STRADDLE": 2, "LOCAL": 3}[grp]
        out.append({"Priority": prio, "Code": c, "Issuer_KSEI": u.get("KSEI_Issuer") or u["Short_Name"],
                    "FO_Group": grp, "Market_Cap_Rank": rank[c], "In_Pilot": int(c in pilot),
                    "Script_Status": a.get("Status", ""), "Company_Website": a.get("Website", ""),
                    "IDX_Page": IDX_PAGE, "Save_To": f"indonesia/raw/manual_ar/{c}/", "Done": ""})
    out.sort(key=lambda r: (r["Priority"], r["Market_Cap_Rank"]))
    with (D / "manual_ar_list.csv").open("w", newline="", encoding="utf-8-sig") as fh:  # BOM: Excel opens it cleanly
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print("manual list", len(out), Counter(r["Priority"] for r in out))


if __name__ == "__main__":
    main()

"""Indonesia step 7 – final FO class per in-scope company (owner rules of 7 and 8 Nov 2026).

  KSEI 30 Dec 2025 bounds decide LOCAL (FO_Upper <= 50 %) and FOREIGN_MAJORITY (FO_Lower > 50 %).
  STRADDLE / no KSEI holdings: the AR 2025.
    1. data/manual/ownership_ar.csv (read by hand, verbatim quote) wins.
    2. Auto-accept (OPEN_DECISIONS 6a) an AR local/foreign table from data/screen_composition.csv when all hold:
       foreign + local = 100 (+-1); first-column FO inside the KSEI bounds (+-0.5 point); |FO - 50| >= 5 points;
       a complete second column (other year) on the same side of 50. (Pilot: LPLI's first column was 2024.)
    2b. Named >= 5 % holders (owner 9 Nov 2026): one side (legal form) > 55 % with the implied FO inside the KSEI bounds.
    3. Otherwise FO_Class REVIEW (blank flag later), FO_Status NEEDS_MANUAL (AR text exists) or NO_AR.
  Managers are searched only for LOCAL (owner 8 Nov 2026: no search for any FOREIGN_MAJORITY firm).

Output  data/fo_classification.csv
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id07_fo_classify.py
"""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"


def rows(name):
    p = D / name
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def auto(cands, lo, hi):
    """First AR table row that passes the 6a conditions, else (None, reason of the best row)."""
    why = "NO_TABLE_ROW"
    for r in cands:
        f, l, f2, l2 = (num(r.get(k)) for k in ("Foreign_Pct", "Local_Pct", "Foreign_Pct_Col2", "Local_Pct_Col2"))
        if r.get("Method") != "LOCAL_FOREIGN_TABLE" or f is None or l is None:
            continue
        if abs(f + l - 100) > 1:
            why = "SUM_OFF"; continue
        if not (lo * 100 - 0.5 <= f <= hi * 100 + 0.5):
            why = "OUTSIDE_KSEI_BOUNDS"; continue
        if abs(f - 50) < 5:
            why = "WITHIN_5_POINTS_OF_50"; continue
        if f2 is not None and l2 is not None and (f2 > 50) != (f > 50):
            why = "COLUMNS_DISAGREE"; continue
        return r, ""
    for r in cands:  # owner 9 Nov 2026 (OPEN_DECISIONS 8a): named holders, one side > 55 % inside the KSEI bounds
        if r.get("Method") != "NAMED_HOLDERS":
            continue
        f, l = num(r.get("Foreign_Pct")) or 0.0, num(r.get("Local_Pct")) or 0.0
        if f + l > 100.5:
            why = "NAMED_SUM_OVER_100"; continue  # repeated holders or a subsidiaries table: read by hand
        if l > 55 and 100 - l >= lo * 100 - 0.5:
            return dict(r, _cls="LOCAL", _fo=f"<={100 - l:.2f}"), ""
        if f > 55 and f <= hi * 100 + 0.5:
            return dict(r, _cls="FOREIGN_MAJORITY", _fo=f">={f:.2f}"), ""
    return None, why


def main():
    uni = {r["Code"]: r for r in rows("universe.csv") if r["Security_Kind"] == "COMPANY" and r["In_Scope"] == "1"}
    fo = {r["Code"]: r for r in rows("fo_ksei_20251230.csv")}
    man = {r["Code"]: r for r in rows("manual/ownership_ar.csv")}
    comp = {}
    for r in rows("screen_composition.csv"):
        comp.setdefault(r["Code"], []).append(r)
    text = {r["Code"] for r in rows("text_index.csv") if r.get("SHA256")}
    out = []
    for c, u in sorted(uni.items()):
        k = fo.get(c, {})
        lo, hi = num(k.get("FO_Lower")), num(k.get("FO_Upper"))
        o = {"Code": c, "Company": u.get("KSEI_Issuer") or u["Short_Name"], "KSEI_Class": k.get("KSEI_Class", "NOT_IN_FILE"),
             "FO_Lower": k.get("FO_Lower", ""), "FO_Upper": k.get("FO_Upper", ""), "FO_Class": "", "FO_Pct": "",
             "FO_Pct_Col2": "", "FO_Source": "", "FO_Page": "", "FO_File": "", "FO_Evidence": "", "FO_Status": ""}
        if o["KSEI_Class"] in ("LOCAL", "FOREIGN_MAJORITY"):
            o.update(FO_Class=o["KSEI_Class"], FO_Source="KSEI_BOUNDS_20251230", FO_Status="SETTLED")
        elif c in man:
            m = man[c]
            o.update(FO_Class=m["FO_Class"], FO_Pct=m.get("FO_Pct", ""), FO_Source="AR2025_MANUAL:" + m.get("Method", ""),
                     FO_Page=m.get("Page", ""), FO_File=m.get("File", ""), FO_Evidence=m.get("Quote", ""), FO_Status="SETTLED")
        else:
            r, why = auto(comp.get(c, []), lo or 0.0, hi if hi is not None else 1.0)
            if r and r.get("_cls"):
                o.update(FO_Class=r["_cls"], FO_Pct=r["_fo"], FO_Source="AR2025_NAMED_HOLDERS_AUTO", FO_Page=r["Page"],
                         FO_File=r["File"], FO_Evidence=r["Rows"], FO_Status="SETTLED")
            elif r:
                f = float(r["Foreign_Pct"])
                o.update(FO_Class="FOREIGN_MAJORITY" if f > 50 else "LOCAL", FO_Pct=r["Foreign_Pct"],
                         FO_Pct_Col2=r.get("Foreign_Pct_Col2", ""), FO_Source="AR2025_TABLE_AUTO", FO_Page=r["Page"],
                         FO_File=r["File"], FO_Evidence=r["Rows"], FO_Status="SETTLED")
            else:
                o.update(FO_Class="REVIEW", FO_Status=("NEEDS_MANUAL:" + why) if c in text else "NO_AR")
        o["Search_Managers"] = int(o["FO_Class"] == "LOCAL")
        out.append(o)
    with (D / "fo_classification.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print("FO class:", Counter(o["FO_Class"] for o in out).most_common())
    print("source:", Counter(o["FO_Source"].split(":")[0] for o in out if o["FO_Source"]).most_common())
    print("open:", Counter(o["FO_Status"] for o in out if o["FO_Status"] != "SETTLED").most_common())


if __name__ == "__main__":
    main()

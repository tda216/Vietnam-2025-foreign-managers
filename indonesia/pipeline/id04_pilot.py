"""Indonesia step 4 – 30-company pilot (owner 8 Nov 2026), stratified, before downloading every report.

Population: in-scope companies that need the AR 2025 – KSEI_Class LOCAL or STRADDLE (30 Dec 2025), plus
FOREIGN_MAJORITY with FO_Lower <= 55 % (borderline: managers are searched).
Cells: FO group (LOCAL / STRADDLE / FM_BORDERLINE) x size (top 200 market cap / rest) x availability
(AUTO = AVAILABLE_WEBSITE in data/ar_availability.csv; MANUAL = everything else, downloaded by hand from IDX).
Allocation: 22 AUTO (LOCAL top 5, rest 6; STRADDLE top 4, rest 5; FM_BORDERLINE 2) + 8 MANUAL (2 per
LOCAL/STRADDLE x size cell). Forced in first, counted against their cells: 3 banks (Industry_Group "Banks"),
1 company whose year end is not December (stockanalysis screen). Within a cell, picks alternate between
companies with KSEI foreign holdings >= 10 % and < 10 % (more chance of foreign managers in the first group).
Seed 20261108.

Owner 8 Nov 2026: no manager search for any FOREIGN_MAJORITY firm. The pilot drawn that day is kept as drawn (this
code reproduces it); its two FM_BORDERLINE picks (BAUT, BNBR) and STRADDLE picks that the AR shows as FM are not searched.

Output  data/pilot30.csv
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id04_pilot.py
"""
import csv, random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
SEED = 20261108
AUTO_ALLOC = {("LOCAL", "TOP200"): 5, ("LOCAL", "REST"): 6, ("STRADDLE", "TOP200"): 4, ("STRADDLE", "REST"): 5,
              ("FM_BORDERLINE", "TOP200"): 1, ("FM_BORDERLINE", "REST"): 1}
MANUAL_ALLOC = {("LOCAL", "TOP200"): 2, ("LOCAL", "REST"): 2, ("STRADDLE", "TOP200"): 2, ("STRADDLE", "REST"): 2}


def rows(name):
    return list(csv.DictReader((D / name).open(encoding="utf-8")))


def main():
    uni = {r["Code"]: r for r in rows("universe.csv") if r["Security_Kind"] == "COMPANY" and r["In_Scope"] == "1"}
    fo = {r["Code"]: r for r in rows("fo_ksei_20251230.csv")}
    av = {r["Code"]: r for r in rows("ar_availability.csv")}
    fy = {r["Code"]: r["Fiscal_Year_Stockanalysis"] for r in rows("websites.csv")}
    mcap = sorted(uni, key=lambda c: -float(uni[c]["Market_Cap"] or 0))
    top = set(mcap[:200])
    pop = []
    for c, u in uni.items():
        f = fo.get(c, {})
        cls = f.get("KSEI_Class", "NOT_IN_FILE")
        if cls == "FOREIGN_MAJORITY":
            if float(f["FO_Lower"]) > 0.55:
                continue
            grp = "FM_BORDERLINE"
        elif cls in ("LOCAL", "STRADDLE"):
            grp = cls
        else:
            grp = "STRADDLE"  # no KSEI holdings (CNTB): FO from the AR, like a straddle
        pop.append({"Code": c, "Company": u["Short_Name"], "Industry_Group": u["Industry_Group"],
                    "FO_Group": grp, "Size": "TOP200" if c in top else "REST",
                    "Availability": "AUTO" if av.get(c, {}).get("Status") == "AVAILABLE_WEBSITE" else "MANUAL",
                    "AR_Status": av.get(c, {}).get("Status", ""), "AR_URL": av.get(c, {}).get("URL", ""),
                    "Website": av.get(c, {}).get("Website", ""),
                    "FO_Lower": f.get("FO_Lower", ""), "FO_Upper": f.get("FO_Upper", ""),
                    "Foreign10": int(float(f.get("FO_Lower") or 0) >= 0.10),
                    "Fiscal_Year": fy.get(c, ""), "Bank": int(u["Industry_Group"] == "Banks")})
    rng = random.Random(SEED)
    rng.shuffle(pop)
    alloc = {("AUTO",) + k: v for k, v in AUTO_ALLOC.items()}
    alloc.update({("MANUAL",) + k: v for k, v in MANUAL_ALLOC.items()})
    cell = lambda p: (p["Availability"], p["FO_Group"], p["Size"])
    picked, reason = [], {}

    def take(p, why):
        if p["Code"] in reason or alloc.get(cell(p), 0) <= 0:
            return False
        alloc[cell(p)] -= 1; picked.append(p); reason[p["Code"]] = why
        return True

    # forced: 3 banks (first in different cells), 1 non-December year end
    banks = 0
    for p in pop:
        if p["Bank"] and banks < 3 and not any(cell(q) == cell(p) for q in picked if q["Bank"]) and take(p, "FORCED_BANK"):
            banks += 1
    for p in pop:
        if p["Fiscal_Year"] and p["Fiscal_Year"] != "January - December" and take(p, "FORCED_NON_DEC_YEAR_END"):
            break
    for k in list(alloc):
        want = [p for p in pop if cell(p) == k and p["Code"] not in reason]
        hi = [p for p in want if p["Foreign10"]]
        lo = [p for p in want if not p["Foreign10"]]
        while alloc[k] > 0 and (hi or lo):
            src = hi if (hi and (not lo or sum(q["Foreign10"] for q in picked if cell(q) == k) <=
                                 sum(1 - q["Foreign10"] for q in picked if cell(q) == k))) else lo
            take(src.pop(0), "STRATIFIED_RANDOM")
    for p in picked:
        p["Pick_Reason"] = reason[p["Code"]]
    picked.sort(key=lambda p: (p["Availability"], p["FO_Group"], p["Size"], p["Code"]))
    with (D / "pilot30.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(picked[0])); w.writeheader(); w.writerows(picked)
    print("population", len(pop), Counter((p["Availability"], p["FO_Group"]) for p in pop).most_common())
    print("pilot", len(picked), Counter(cell(p) for p in picked))
    print("banks", sum(p["Bank"] for p in picked), "foreign>=10%", sum(p["Foreign10"] for p in picked),
          "non-Dec", [p["Code"] for p in picked if p["Fiscal_Year"] not in ("", "January - December")])
    print("unfilled cells:", {k: v for k, v in alloc.items() if v})


if __name__ == "__main__":
    main()

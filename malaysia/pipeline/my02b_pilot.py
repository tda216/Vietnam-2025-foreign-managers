"""Malaysia – draw the 30-company pilot (checkpoint 2), stratified and reproducible (seed 20261107).

Strata (counts): Main board Dec year-end 12, Main non-Dec 7, ACE Dec 4, ACE non-Dec 3, LEAP 2, REIT 2.
Only companies whose FY2025 annual report is in the index (data/ar_index.csv) are drawn, so the
pilot tests document retrieval and the director/shareholding pages, not the listing check.
Output: data/pilot30.csv

Run from the project root:  .venv/bin/python -I malaysia/pipeline/my02b_pilot.py
"""
import csv, datetime as dt, random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRATA = {("MAIN", "DEC"): 12, ("MAIN", "NONDEC"): 7, ("ACE", "DEC"): 4, ("ACE", "NONDEC"): 3,
          ("LEAP", "ANY"): 2, ("REIT", "ANY"): 2}


def main():
    univ = [u for u in csv.DictReader((ROOT / "data" / "universe.csv").open(encoding="utf-8"))
            if u["Exchange"] == "MK" and u["Stock_Code"] and u["In_Scope"] != "0"]
    fye = {}
    for r in csv.DictReader((ROOT / "data" / "ar_index.csv").open(encoding="utf-8")):
        try:
            d = dt.datetime.strptime(r["FY_End"], "%d-%b-%Y").date()
        except ValueError:
            continue
        if d.year == 2025 and r["AR_Ann_Date"]:
            fye[r["Stock_Code"]] = d
    pools = defaultdict(list)
    for u in univ:
        d = fye.get(u["Stock_Code"])
        if not d:
            continue
        if (u["Industry_Group"] or "").upper() == "REITS":
            key = ("REIT", "ANY")
        elif u["Bursa_Board"] == "LEAP":
            key = ("LEAP", "ANY")
        else:
            board = "ACE" if u["Bursa_Board"] == "ACE" else "MAIN"
            key = (board, "DEC" if (d.month, d.day) == (12, 31) else "NONDEC")
        pools[key].append(u)
    rng = random.Random(20261107)
    out = []
    for key, n in STRATA.items():
        pool = sorted(pools[key], key=lambda u: u["Stock_Code"])
        for u in rng.sample(pool, min(n, len(pool))):
            out.append({"Stock_Code": u["Stock_Code"], "Bursa_Stock_Name": u["Bursa_Stock_Name"],
                        "Company": u["Bursa_Company_Name"], "Stratum": "_".join(key),
                        "FY2025_End": fye[u["Stock_Code"]].isoformat(), "Market_Cap": u["Market_Cap"],
                        "Bloomberg_Ticker": u["Bloomberg_Ticker"]})
        print(key, "pool", len(pool), "drawn", min(n, len(pool)))
    with (ROOT / "data" / "pilot30.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print("pilot", len(out))


if __name__ == "__main__":
    main()

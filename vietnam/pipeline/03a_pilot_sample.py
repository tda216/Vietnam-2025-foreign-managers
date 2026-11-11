"""Step 3a – draw the 30-company pilot sample (reproducible, stratified by Bloomberg market-cap rank).

Strata among companies in the manager-search scope (Security_Class COMPANY_VN):
  LARGE = rank 1–100, MID = rank 101–500, SMALL_UPCOM = UPCoM at 31/12/2025 with rank > 500.
Output: data/pilot_sample.csv
"""
import random
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2] / "shared")]  # python -I; country config first
from common import read_csv, write_csv
from config import DATA

SEED = 20251231
PER_STRATUM = 10


def main():
    comps = [c for c in read_csv(DATA / "companies_step2.csv")
             if c["Manager_Search"] == "1" and c["Security_Class"] == "COMPANY_VN" and c["Mcap_Rank"]]
    rank = lambda c: int(c["Mcap_Rank"])
    strata = {
        "LARGE": [c for c in comps if rank(c) <= 100],
        "MID": [c for c in comps if 100 < rank(c) <= 500],
        "SMALL_UPCOM": [c for c in comps if rank(c) > 500 and c["Exchange_At_FO_Date"] == "UPCoM"],
    }
    rng = random.Random(SEED)
    out = []
    for name, pool in strata.items():
        for c in sorted(rng.sample(pool, PER_STRATUM), key=rank):
            out.append({"Stratum": name, "Ticker_Local": c["Ticker_Local"], "Company": c["Company"],
                        "Exchange_At_FO_Date": c["Exchange_At_FO_Date"], "Mcap_Rank": c["Mcap_Rank"],
                        "Foreign_Ownership_Pct": c["Foreign_Ownership_Pct"], "Ownership_Type": c["Ownership_Type"]})
        print(f"{name}: pool {len(pool)}")
    write_csv(DATA / "pilot_sample.csv", out, list(out[0].keys()))
    for r in out:
        print(f"  {r['Stratum']:11s} {r['Ticker_Local']:5s} {r['Exchange_At_FO_Date']:6s} rank={r['Mcap_Rank']:>5s} "
              f"FO={float(r['Foreign_Ownership_Pct']):6.2f}%  {r['Company'][:60]}")


if __name__ == "__main__":
    main()

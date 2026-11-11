"""Indonesia step 11 – manual QA sample (reproducible: fixed seed).

Draws a simple random sample of
  - 30 rows of Foreign_Managers (data/manual/manager_records.csv, Is_Foreign = 1)  -> data/qa_sample_records.csv
  - 30 NONE_FOUND LOCAL firms (Companies sheet of the workbook)                      -> data/qa_sample_companies.csv
A reviewer re-reads each item in the source and writes the verdict to data/manual/qa_review.csv
(Item_Type, Code, Item, Verdict OK / ERROR / MINOR, Check, Note, Reviewed_On). Errors are fixed through the usual batches.
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id11_qa_sample.py [seed]
"""
import csv, random, sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 20261110


def main():
    rng = random.Random(SEED)
    rec = [r for r in csv.DictReader((D / "manual" / "manager_records.csv").open(encoding="utf-8")) if r["Is_Foreign"] in ("1", "1.0")]
    sr = rng.sample(rec, 30)
    keys = ["Code", "Manager_Name", "Raw_Position", "Role_Group", "Nationality", "Local_File", "Page", "Evidence_Type",
            "Evidence_Quote", "Appointed_Date", "Resigned_Date", "Note"]
    with (D / "qa_sample_records.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(sr)
    wb = openpyxl.load_workbook(ROOT / "output" / "Indonesia_2025_Foreign_Managers.xlsx", read_only=True)
    it = wb["Companies"].iter_rows(values_only=True); h = next(it)
    none = sorted((dict(zip(h, r)) for r in it), key=lambda d: d["Code"])
    none = [d for d in none if d["Flag_Status"] == "NONE_FOUND"]
    sc = rng.sample(none, 30)
    keys = ["Code", "Company", "FO_Class", "AR2025_Source", "Indonesian_Labels", "Departed_Names_Unresolved"]
    with (D / "qa_sample_companies.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(sc)
    print(f"seed {SEED}: {len(sr)} of {len(rec)} records, {len(sc)} of {len(none)} NONE_FOUND firms")


if __name__ == "__main__":
    main()

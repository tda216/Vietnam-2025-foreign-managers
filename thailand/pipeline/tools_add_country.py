"""Append a reviewed batch to the hand-reviewed Thailand files and keep the batch as an audit trail.

Usage: python -I thailand/pipeline/tools_add_country.py data/manual/batches/<name>.json
Batch format (every list optional):
{
  "country": [ {Ticker_Local, Manager_Name, Nationality, Nationality_Raw, Country_Evidence_Type, Country_Quote, Country_Source,
                Country_Source_URL, Note} ],                      -> data/manual/country_records.csv (country of a "No" person)
  "records": [ {... manager_records.csv columns ...} ],           -> data/manual/manager_records.csv (new foreign / UNKNOWN rows)
  "candidate_decisions": [ {Ticker_Local, Name, Decision, Reason, Source_File, Page} ]  -> data/manual/candidate_decisions.csv
  "other_conflicts": [ {Ticker_Local, Name, Page, One_Report, Other_Source, Other_Source_URL, Default} ]
                                                   -> data/manual/other_source_conflicts.csv (One Report vs a non-BoardEx source)
  "conflict_decisions": [ {Ticker_Local, Name, Decision, Reason} ]  -> data/manual/conflict_decisions.csv
}
Checks: nationality is a value of config.NATIONALITY_EN (or UNKNOWN); evidence types are known; no duplicate keys. Nothing
is written if a check fails. Reviewed_On defaults to today.
"""
import csv
import json
import sys
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

from config import DATA, NATIONALITY_EN, ROOT

COUNTRY_EVIDENCE = {"BOARDEX", "DOC_FIELD", "CV", "DISCLOSURE_FORM", "WEBSITE", "NEWS", "BIRTHPLACE",
                    "INFERRED_STRONG", "INFERRED_MEDIUM", "INFERRED_WEAK"}
EVIDENCE = {"ONE_REPORT_FIELD", "BOARDEX", "DOC_FIELD", "CV", "DISCLOSURE_FORM", "WEBSITE", "NEWS", "BIRTHPLACE", "INFERRED"}
FILES = {"country": ("country_records.csv", ("Ticker_Local", "Manager_Name")),
         "records": ("manager_records.csv", ("Ticker_Local", "Manager_Name", "Raw_Position")),
         "candidate_decisions": ("candidate_decisions.csv", ("Ticker_Local", "Name")),
         "other_conflicts": ("other_source_conflicts.csv", ("Ticker_Local", "Name")),
         "conflict_decisions": ("conflict_decisions.csv", ("Ticker_Local", "Name"))}


def norm(*xs: str) -> tuple[str, ...]:
    return tuple(" ".join(str(x).lower().split()) for x in xs)


def main():
    path = Path(sys.argv[1])
    batch = json.loads((path if path.is_absolute() else ROOT / path).read_text(encoding="utf-8"))
    countries = set(NATIONALITY_EN.values()) | {"UNKNOWN"}
    errors, plan = [], {}
    for kind, (fname, keys) in FILES.items():
        rows = batch.get(kind, [])
        if not rows:
            continue
        f = DATA / "manual" / fname
        with open(f, encoding="utf-8") as fh:
            rd = csv.DictReader(fh)
            cols, old = rd.fieldnames, list(rd)
        seen = {norm(*(r[k] for k in keys)) for r in old}
        for r in rows:
            r.setdefault("Reviewed_On", date.today().isoformat())
            unknown_cols = set(r) - set(cols)
            if unknown_cols:
                errors.append(f"{kind}: unknown columns {sorted(unknown_cols)}")
            k = norm(*(r.get(x, "") for x in keys))
            if k in seen:
                errors.append(f"{kind}: duplicate {k}")
            seen.add(k)
            if "Nationality" in r and r["Nationality"] not in countries:
                errors.append(f"{kind}: nationality not in config.NATIONALITY_EN: {r['Nationality']!r} ({k})")
            if r.get("Country_Evidence_Type") and r["Country_Evidence_Type"] not in COUNTRY_EVIDENCE:
                errors.append(f"{kind}: Country_Evidence_Type {r['Country_Evidence_Type']!r} ({k})")
            if kind == "records" and r.get("Evidence_Type") not in EVIDENCE:
                errors.append(f"records: Evidence_Type {r.get('Evidence_Type')!r} ({k})")
        plan[kind] = (f, cols, rows)
    if errors:
        print("NOT WRITTEN –", len(errors), "problems:")
        for e in errors:
            print("  ", e)
        sys.exit(1)
    for kind, (f, cols, rows) in plan.items():
        with open(f, "a", encoding="utf-8", newline="") as fh:
            csv.DictWriter(fh, cols).writerows({c: r.get(c, "") for c in cols} for r in rows)
        print(f"{kind}: +{len(rows)} -> {f.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

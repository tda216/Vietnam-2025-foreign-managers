"""Append reviewed stockholder-nationality evidence to philippines/data/manual/holder_nationality_review.csv.

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph_add_holders.py <batch.json>

batch.json = {"holders": [{Symbol, Holder_Name, Pct_Of_Outstanding, Is_Foreign, Country, Nationality_Raw, Doc, Page,
                            Evidence_Quote, [Note]}]}
  Holder_Name    exactly as in philippines/data/holder_nationality.csv (the Top 100 list spelling), so ph07 can match it.
  Is_Foreign     1 = the source states a non-Filipino nationality/citizenship/place of incorporation for this holder;
                 0 = the source states Filipino; "" = still unknown after reading (keep the row: it records the search).
  Country        standard English name ("Philippines" when Is_Foreign = 0, "UNKNOWN" when foreign country not stated).
  Doc            substring of the saved attachment name under philippines/raw/pse/<Symbol>/ (e.g. the att_<id>_ prefix).
  Page           1-based PDF page. Evidence_Quote: verbatim text from that page.
Source, Source_URL, Local_File and Reviewed_On are filled automatically. Batches are copied to data/manual/batches/.
A later row for the same (Symbol, Holder_Name) supersedes an earlier one in ph07; earlier rows are kept (audit trail).
"""
import csv
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "philippines"
RAW = PH / "raw" / "pse"
MANUAL = PH / "data" / "manual"
FIELDS = ["Symbol", "Holder_Name", "Pct_Of_Outstanding", "Is_Foreign", "Country", "Nationality_Raw", "Source", "Source_URL",
          "Local_File", "Page", "Evidence_Quote", "Note", "Reviewed_On"]

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ph_add_records import NATIONALITIES, find_doc, read_csv, write_csv  # noqa: E402

COUNTRIES = NATIONALITIES | {"Philippines", "British Virgin Islands", "Cayman Islands", "Panama", "Samoa", "Luxembourg", "Mauritius",
                             "Jersey", "Guernsey", "Isle of Man", "Bahamas", "Marshall Islands", "Liechtenstein", "Cyprus", "Seychelles",
                             "Liberia"}


def main():
    batch_path = Path(sys.argv[1])
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    MANUAL.mkdir(parents=True, exist_ok=True)
    (MANUAL / "batches").mkdir(exist_ok=True)
    path = MANUAL / "holder_nationality_review.csv"
    rows = read_csv(path)
    for b in batch.get("holders", []):
        isf = str(b.get("Is_Foreign", ""))
        if isf not in ("1", "0", ""):
            raise SystemExit(f"Is_Foreign must be 1, 0 or blank: {b}")
        if b.get("Country", "") and b["Country"] not in COUNTRIES:
            raise SystemExit(f"Country not standard: {b['Country']} ({b['Symbol']} {b['Holder_Name']})")
        if isf in ("1", "0") and not b.get("Evidence_Quote"):
            raise SystemExit(f"Evidence_Quote required when Is_Foreign is 1 or 0 ({b['Symbol']} {b['Holder_Name']})")
        row = {k: "" for k in FIELDS}
        row.update({k: str(v) for k, v in b.items() if k in FIELDS})
        if b.get("Doc"):
            m, f, folder = find_doc(b["Symbol"], b["Doc"])
            row.update(Source=f"{m['template']} ({m['form']}) {m['report_no']}, announced {m['announced']}",
                       Source_URL=m["viewer_url"], Local_File=str((folder / f["saved_as"]).relative_to(ROOT)))
        row["Reviewed_On"] = b.get("Reviewed_On") or date.today().isoformat()
        rows.append(row)
    write_csv(path, FIELDS, rows)
    dest = MANUAL / "batches" / batch_path.name
    if batch_path.resolve() != dest.resolve():
        shutil.copy(batch_path, dest)
    print("holder rows added", len(batch.get("holders", [])), "| total", len(rows))


if __name__ == "__main__":
    main()

"""Append reviewed records and decisions to philippines/data/manual/ (the only place where facts are added).

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph_add_records.py <batch.json>

batch.json = {"records":   [{Symbol, Doc, Page, Manager_Name, Raw_Position, Role_Group, Nationality, Nationality_Raw, Is_Foreign,
                             Evidence_Quote, [Dual_Nationality, Appointed_Date, Resigned_Date, Evidence_Type, Other_Sources,
                             Note, Management_Include]}],
              "decisions": [{Symbol, Name, Decision, Reason, [Doc, Page]}]}

Symbol = PSE stock symbol (e.g. "MVC"). Doc = substring of the downloaded attachment's saved name (the 17-A PDF).
Company, Ticker, Source, Source_URL, Local_File and Reviewed_On are filled from the PSE filing metadata and the Bloomberg list.
Page is the 1-based PDF page. Nationality must be a standard English country name.
Batches are copied to philippines/data/manual/batches/ as the audit trail. Rows already present (same symbol, name,
raw position, role group, page) are not added twice. Edit nothing in raw/.
Decision values: NOT_A_PERSON, SAME_AS_RECORD, NOT_A_MANAGER, NOT_FY2025, NOT_FOREIGN_STATED, UNLISTED_SUBSIDIARY_ONLY,
LABEL_PAGE_REVIEWED, OCR_NOISE, NEEDS_REVIEW, LISTED_SUBSIDIARY_ROLE (role belongs to a listed subsidiary in the sample).
For BoardEx people (Name = BoardEx Manager_Name), ph10 applies NOT_A_MANAGER / NOT_FY2025 / UNLISTED_SUBSIDIARY_ONLY /
LISTED_SUBSIDIARY_ROLE / SAME_AS_RECORD / OWNER_DECISION_NOT_COUNTED / NOT_FOREIGN_STATED (filing states local nationality) as exclusions and NEEDS_REVIEW as 'eligibility unresolved' (not counted, keeps the company open).
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

REC_FIELDS = ["Company", "Ticker", "Symbol", "Year", "Manager_Name", "Raw_Position", "Role_Group", "Nationality", "Nationality_Raw",
              "Is_Foreign", "Dual_Nationality", "Appointed_Date", "Resigned_Date", "Source", "Source_URL", "Local_File", "Page",
              "Evidence_Type", "Evidence_Quote", "Other_Sources", "Reviewed_On", "Note", "Management_Include"]
DEC_FIELDS = ["Symbol", "Name", "Decision", "Reason", "Local_File", "Page", "Reviewed_On"]
ROLE_GROUPS = {"Board", "Supervisory", "Executive", "Other_Manager"}
NATIONALITIES = {  # standard English names accepted in the Philippines dataset
    "United States", "United Kingdom", "Singapore", "China", "Japan", "Australia", "Malaysia", "Taiwan", "India", "Indonesia",
    "France", "South Korea", "Denmark", "South Africa", "Switzerland", "Germany", "Spain", "Belgium", "Saudi Arabia", "Peru",
    "Czech Republic", "Sri Lanka", "Russia", "New Zealand", "Thailand", "Mexico", "Greece", "Canada", "Netherlands", "Italy",
    "Sweden", "Norway", "Ireland", "Israel", "Vietnam", "Brunei", "Dominican Republic", "Hong Kong", "Brazil", "Argentina", "Pakistan", "Bangladesh", "Nigeria",
    "Turkey", "Poland", "Austria", "Portugal", "Finland", "Cambodia", "Myanmar", "Lebanon", "Egypt", "United Arab Emirates",
    "Kuwait", "Qatar", "Bermuda", "Fiji", "Kosovo", "UNKNOWN",
}


def read_csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig"))) if p.exists() else []


def write_csv(p, fields, rows):
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def find_doc(symbol, doc):
    hits = []
    for mp in (RAW / symbol).glob("*/meta.json"):
        m = json.loads(mp.read_text(encoding="utf-8"))
        for f in m["files"]:
            if doc in f.get("saved_as", ""):
                hits.append((m, f, mp.parent))
    if len(hits) != 1:
        raise SystemExit(f"{len(hits)} documents match {symbol} / {doc!r}")
    return hits[0]


def main():
    batch_path = Path(sys.argv[1])
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    comps = {r["Ticker"].split()[0]: r for r in read_csv(PH / "data" / "companies_boardex.csv") if r["Ticker"].split()[1] == "PM"}
    MANUAL.mkdir(parents=True, exist_ok=True)
    (MANUAL / "batches").mkdir(exist_ok=True)
    rec_path, dec_path = MANUAL / "manager_records.csv", MANUAL / "candidate_decisions.csv"
    recs, decs = read_csv(rec_path), read_csv(dec_path)
    have = {(r["Symbol"], r["Manager_Name"], r["Raw_Position"], r["Role_Group"], r["Page"]) for r in recs}
    added = 0
    for b in batch.get("records", []):
        sym = b["Symbol"]
        if sym not in comps:
            raise SystemExit(f"unknown symbol {sym}")
        if b["Role_Group"] not in ROLE_GROUPS:
            raise SystemExit(f"bad Role_Group {b['Role_Group']} ({sym} {b['Manager_Name']})")
        if b["Nationality"] not in NATIONALITIES:
            raise SystemExit(f"nationality not standard: {b['Nationality']} ({sym} {b['Manager_Name']})")
        if not b.get("Evidence_Quote"):
            raise SystemExit(f"missing Evidence_Quote ({sym} {b['Manager_Name']})")
        m, f, folder = find_doc(sym, b["Doc"])
        c = comps[sym]
        row = {k: "" for k in REC_FIELDS}
        row.update({k: str(v) for k, v in b.items() if k in REC_FIELDS})
        row.update(Company=c["Company"], Ticker=c["Ticker"], Symbol=sym, Year="2025",
                   Source=f"{m['template']} ({m['form']}) {m['report_no']}, announced {m['announced']}",
                   Source_URL=m["viewer_url"], Local_File=str((folder / f["saved_as"]).relative_to(ROOT)),
                   Page=str(b["Page"]), Evidence_Type=b.get("Evidence_Type") or "DOC_FIELD",
                   Reviewed_On=b.get("Reviewed_On") or date.today().isoformat(), Is_Foreign=str(b.get("Is_Foreign", 1)))
        key = (sym, row["Manager_Name"], row["Raw_Position"], row["Role_Group"], row["Page"])
        if key in have:
            continue
        recs.append(row)
        have.add(key)
        added += 1
    for d in batch.get("decisions", []):
        row = {k: "" for k in DEC_FIELDS}
        row.update({k: str(v) for k, v in d.items() if k in DEC_FIELDS})
        if d.get("Doc"):
            m, f, folder = find_doc(d["Symbol"], d["Doc"])
            row["Local_File"] = str((folder / f["saved_as"]).relative_to(ROOT))
        row["Reviewed_On"] = d.get("Reviewed_On") or date.today().isoformat()
        decs.append(row)
    write_csv(rec_path, REC_FIELDS, recs)
    write_csv(dec_path, DEC_FIELDS, decs)
    dest = MANUAL / "batches" / batch_path.name
    if batch_path.resolve() != dest.resolve():
        shutil.copy(batch_path, dest)
    print("records added", added, "| decisions added", len(batch.get("decisions", [])), "| total records", len(recs))


if __name__ == "__main__":
    main()

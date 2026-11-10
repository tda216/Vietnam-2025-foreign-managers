"""Append reviewed company-level foreign-ownership (FO) decisions to philippines/data/manual/ownership_manual.csv.

Run from the repository root:  .venv/bin/python -I philippines/pipeline/ph_add_ownership.py <batch.json>

Use this when the FO of a company was read by hand (e.g. a Top 100 list the parser could not read, a 17-A statement of
foreign ownership, or a foreign-listed issuer). Holder-level evidence goes to ph_add_holders.py instead.

batch.json = {"ownership": [{Symbol, Ownership_Type, FO_Lower, FO_Upper, FO_As_Of_Date, FO_Method, Doc, Page, Evidence_Quote,
                              [Foreign_Ownership_Pct, Note]}]}
  Ownership_Type  FOREIGN_MAJORITY (FO > 50) | LOCAL (FO <= 50) | REVIEW (cannot be decided from the evidence).
                  Must agree with the bounds: FOREIGN_MAJORITY needs FO_Lower > 50; LOCAL needs FO_Upper <= 50.
  FO_Lower/Upper  percent of outstanding common shares (numbers). Equal when the FO is exact.
  FO_Method       short code, e.g. TOP100_MANUAL_READ, 17A_FOREIGN_OWNERSHIP_STATEMENT, PCD_PLUS_NAMED_HOLDERS.
Ticker/Company, Source, Source_URL, Local_File and Reviewed_On are filled automatically. A later row for a Symbol supersedes an
earlier one; earlier rows are kept as the audit trail.
"""
import csv
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "philippines"
MANUAL = PH / "data" / "manual"
FIELDS = ["Symbol", "Ticker", "Ownership_Type", "In_Scope", "Exclusion_Reason", "Foreign_Ownership_Pct", "FO_Lower", "FO_Upper",
          "FO_As_Of_Date", "FO_Method", "Source", "Source_URL", "Local_File", "Page", "Evidence_Quote", "Note", "Reviewed_On"]
# Ticker (Bloomberg) is required for companies without a PSE symbol (foreign-listed); In_Scope/Exclusion_Reason are optional.

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ph_add_records import find_doc, read_csv, write_csv  # noqa: E402


def main():
    batch_path = Path(sys.argv[1])
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    MANUAL.mkdir(parents=True, exist_ok=True)
    (MANUAL / "batches").mkdir(exist_ok=True)
    path = MANUAL / "ownership_manual.csv"
    rows = read_csv(path)
    for b in batch.get("ownership", []):
        t = b["Ownership_Type"]
        if t not in ("FOREIGN_MAJORITY", "LOCAL", "REVIEW"):
            raise SystemExit(f"bad Ownership_Type: {b}")
        if str(b.get("FO_Method", "")).startswith("OWNER_RULE"):
            # classification set by a research-owner rule (no FO figure); the rule and its date go in Evidence_Quote/Note
            if b.get("FO_Lower", "") != "" or b.get("FO_Upper", "") != "":
                raise SystemExit(f"OWNER_RULE rows carry no FO bounds: {b}")
        else:
            lo, hi = float(b["FO_Lower"]), float(b["FO_Upper"])
            if lo > hi:
                raise SystemExit(f"bad bounds: {b}")
            if (t == "FOREIGN_MAJORITY" and lo <= 50) or (t == "LOCAL" and hi > 50):
                raise SystemExit(f"Ownership_Type does not follow the 50% rule given the bounds: {b}")
        if not b.get("Evidence_Quote"):
            raise SystemExit(f"Evidence_Quote required ({b['Symbol']})")
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
    print("ownership rows added", len(batch.get("ownership", [])), "| total", len(rows))


if __name__ == "__main__":
    main()

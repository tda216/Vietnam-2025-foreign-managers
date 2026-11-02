"""Helper – append reviewed records to data/manual/manager_records.csv (and decisions to candidate_decisions.csv).

Usage: python -I pipeline/tools_add_records.py <run> <batch.json>
batch.json: {"records": [{Ticker_Local, Manager_Name, Raw_Position, Role_Group, Nationality, Nationality_Raw, Is_Foreign,
                          Local_File (or file substring), Page, Evidence_Quote, [Appointed_Date, Resigned_Date, Dual_Nationality,
                          Evidence_Type, Other_Sources, Note]}],
             "decisions": [{Ticker_Local, Name, Decision, Reason, [Page, Source_File]}]}
Source / Source_URL are filled from data/<run>/docs.csv or docs_verify.csv by Local_File; rows already present
(same ticker, name, raw position, page) are not added twice.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import read_csv
from config import DATA

KIND_NAME = {"AR2025": "Báo cáo thường niên 2025", "GOV2025": "Báo cáo tình hình quản trị công ty năm 2025",
             "AGM2025": "Tài liệu ĐHĐCĐ 2025", "AGM2026": "Tài liệu ĐHĐCĐ 2026", "BOARD2025": "Nghị quyết/Thông báo HĐQT 2025",
             "BOARD2026": "Nghị quyết/Thông báo HĐQT 2026", "AR2024": "Báo cáo thường niên 2024"}
KIND_NAME |= {f"AGM{y}": f"Tài liệu ĐHĐCĐ {y}" for y in range(2018, 2025)} | {f"BOARD{y}": f"Nghị quyết/Thông báo HĐQT {y}" for y in range(2018, 2025)}


def main():
    run, batch_file = sys.argv[1], sys.argv[2]
    batch = json.loads(Path(batch_file).read_text(encoding="utf-8"))
    docs = [d for f in ("docs.csv", "docs_verify.csv", "docs_fallback.csv", "docs_verify_old.csv", "docs_verify_old2.csv", "docs_web.csv") if (DATA / run / f).exists()
            for d in read_csv(DATA / run / f)]
    rec_path = DATA / "manual" / "manager_records.csv"
    recs = read_csv(rec_path)
    fields = list(recs[0].keys())
    have = {(r["Ticker_Local"], r["Manager_Name"], r["Raw_Position"], r["Role_Group"], r["Page"]) for r in recs}
    added = 0
    for b in batch.get("records", []):
        match = {x["Local_File"]: x for x in docs if x["Ticker_Local"] == b["Ticker_Local"] and b["Local_File"] in x["Local_File"]}
        if len(match) != 1:  # e.g. "GEG_Baocaothuongnien_2025" matches every member of the zip
            raise SystemExit(f"{len(match)} documents match {b['Ticker_Local']} {b['Local_File']}: {sorted(match)}")
        d = next(iter(match.values()))
        row = {k: "" for k in fields}
        row.update({k: v for k, v in b.items() if k in fields})
        row.update(Local_File=d["Local_File"], Source_URL=b.get("Source_URL") or d["Source_URL"],
                   Source=b.get("Source") or KIND_NAME.get(d["Doc_Kind"], d["Doc_Kind"]) + f" ({b['Ticker_Local']})",
                   Evidence_Type=("" if str(b.get("Is_Foreign", 1)) == "" else  # UNKNOWN: no nationality evidence yet
                                  b.get("Evidence_Type") or ("CV" if d["Doc_Kind"].startswith("AGM") else "DOC_FIELD")),
                   Reviewed_On=b.get("Reviewed_On", "2026-11-01"), Page=str(b["Page"]), Is_Foreign=str(b.get("Is_Foreign", 1)))
        key = (row["Ticker_Local"], row["Manager_Name"], row["Raw_Position"], row["Role_Group"], row["Page"])
        if key in have:
            continue
        recs.append(row)
        have.add(key)
        added += 1
    with rec_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(recs)
    dec_path = DATA / "manual" / "candidate_decisions.csv"
    dec = read_csv(dec_path)
    dfields = list(dec[0].keys())
    for b in batch.get("decisions", []):
        dec.append({k: "" for k in dfields} | {k: str(v) for k, v in b.items() if k in dfields} | {"Reviewed_On": "2026-11-01"})
    with dec_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=dfields)
        w.writeheader()
        w.writerows(dec)
    print("records added", added, "| decisions added", len(batch.get("decisions", [])), "| total records", len(recs))


if __name__ == "__main__":
    main()

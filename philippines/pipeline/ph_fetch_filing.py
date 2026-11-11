"""Reviewer helper: list a company's PSE Edge filings and download one filing (with meta.json: URL, time, SHA256).

Run from the repository root (python -I):
  .venv/bin/python -I philippines/pipeline/ph_fetch_filing.py list <Symbol> [from mm-dd-yyyy] [to mm-dd-yyyy]
  .venv/bin/python -I philippines/pipeline/ph_fetch_filing.py get  <Symbol> <Edge_No>
Downloads go to philippines/raw/pse/<Symbol>/<Edge_No>/ (untrusted data; never executed). Already downloaded = skipped.
"""
import csv
import importlib.util
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def company_id(sym):
    for r in csv.DictReader(open(ROOT / "philippines" / "data" / "pse_directory.csv", encoding="utf-8")):
        if r["Symbol"].upper() == sym.upper():
            return r["PSE_Company_ID"]
    raise SystemExit(f"{sym} not in the PSE directory")


def main():
    ph01 = load("ph01", "ph01_index_pse.py")
    cmd, sym = sys.argv[1], sys.argv[2].upper()
    cid = company_id(sym)
    if cmd == "list":
        frm = sys.argv[3] if len(sys.argv) > 3 else "01-01-2025"
        to = sys.argv[4] if len(sys.argv) > 4 else date.today().strftime("%m-%d-%Y")
        for ep in ("otherReports", "financialReports", "announcements"):
            for r in ph01.list_filings(ep, cid, frm, to):
                print(f"{r['Announced']:22} {r['Form']:8} {r['Edge_No']} {r['Report_No']:14} {r['Template']}")
    elif cmd == "get":
        edge = sys.argv[3]
        ph02 = load("ph02", "ph02_download_pse.py")
        row = None
        for ep in ("otherReports", "financialReports", "announcements"):
            for r in ph01.list_filings(ep, cid, "01-01-2018", date.today().strftime("%m-%d-%Y")):
                if r["Edge_No"] == edge:
                    row = r
                    break
            if row:
                break
        if row is None:
            raise SystemExit("edge number not found for this company")
        print(ph02.download({"Symbol": sym, **row}), "->", ROOT / "philippines" / "raw" / "pse" / sym / edge)


if __name__ == "__main__":
    main()

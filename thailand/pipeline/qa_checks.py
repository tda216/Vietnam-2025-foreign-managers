"""QA – automatic checks on the Thailand workbook, plus the random samples for the manual check.

Usage: python -I thailand/pipeline/qa_checks.py           checks; prints every violation, writes data/qa_report.csv
       python -I thailand/pipeline/qa_checks.py sample    also draws the manual-check samples (seed QA_SEED): 10% of the
                                                         Foreign_Managers rows, QA_ZERO_COMPANIES flag-0 companies and every
                                                         source conflict -> data/qa_sample_*.csv; results go to data/manual/qa_manual.csv
A check passes when it lists no violation. Same checks as the Vietnam workbook (pipeline/qa_checks.py), plus:
board count = table 7.2.1, the One Report page of a ONE_REPORT_FIELD row holds the name and "No", BOARDEX rows carry
a BoardEx id and an FY2025 role, and every One Report / BoardEx conflict has a decision.
"""
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

import pymupdf
from openpyxl import load_workbook

from common import read_csv, write_csv
from config import BLOOMBERG_FILE, DATA, FO_THRESHOLD, NATIONALITY_EN, OUTPUT, ROOT

QA_SEED = 20261107
QA_ZERO_COMPANIES = 30
EVIDENCE_TYPES = {"ONE_REPORT_FIELD", "BOARDEX", "DOC_FIELD", "CV", "DISCLOSURE_FORM", "WEBSITE", "NEWS", "BIRTHPLACE", "INFERRED"}
COUNTRY_EVIDENCE = {"", "BOARDEX", "DOC_FIELD", "CV", "DISCLOSURE_FORM", "WEBSITE", "NEWS", "BIRTHPLACE",
                    "INFERRED_STRONG", "INFERRED_MEDIUM", "INFERRED_WEAK"}
STATUSES = {"FOUND", "NONE_FOUND", "UNRESOLVED", "NO_SOURCE", "NOT_SEARCHED", "OUT_OF_SCOPE"}
_pages: dict[str, list[str]] = {}


def page_text(local_file: str, page: int) -> str:
    if local_file not in _pages:
        _pages[local_file] = [p.get_text() for p in pymupdf.open(ROOT / local_file)]
    pages = _pages[local_file]
    return pages[page - 1] if 0 < page <= len(pages) else ""


def sheet(wb, name: str) -> list[dict]:
    rows = wb[name].iter_rows(values_only=True)
    head = next(rows)
    return [dict(zip(head, ["" if v is None else v for v in r])) for r in rows]


def main():
    path = OUTPUT / "Thailand_2025_Foreign_Managers.xlsx"
    wb = load_workbook(path, read_only=True)
    comps, fm = sheet(wb, "Companies"), sheet(wb, "Foreign_Managers")
    out = []

    def fail(check: str, k: str, detail: str) -> None:
        out.append({"Check": check, "Key": k, "Detail": detail})

    # 1. one row per Bloomberg security; Bloomberg_Raw equals the input cell by cell
    if BLOOMBERG_FILE.exists():
        src = list(load_workbook(BLOOMBERG_FILE, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
        n_sec = sum(1 for r in src if isinstance(r[0], str) and r[0].endswith(" Equity"))
        if len(comps) != n_sec or len({c["Ticker"] for c in comps}) != n_sec:
            fail("companies_rows", "", f"Companies {len(comps)} rows, Bloomberg {n_sec} securities")
        raw = list(wb["Bloomberg_Raw"].iter_rows(values_only=True))
        if len(raw) != len(src):
            fail("bloomberg_raw_rows", "", f"{len(raw)} vs {len(src)}")
        for i, (a, b) in enumerate(zip(src, raw), 1):
            a, b = list(a), list(b) + [None] * (len(a) - len(b))
            if any(x != y and not (isinstance(x, (int, float)) and isinstance(y, (int, float)) and math.isclose(x, y, rel_tol=1e-12))
                   for x, y in zip(a, b)):
                fail("bloomberg_raw_cells", f"row {i}", "differs from the input file")

    # 2. ownership type follows the rule
    for c in comps:
        if str(c["In_Scope"]) != "1":
            continue
        fo, ot, bound = c["Foreign_Ownership_Pct"], c["Ownership_Type"], str(c["FO_Bound"])
        if fo != "":
            ok = ot == ("FOREIGN_MAJORITY" if float(fo) > FO_THRESHOLD else "LOCAL")
        elif bound.startswith(("<=", ">=")):
            op, x = bound.split()
            ok = ot == ("FOREIGN_MAJORITY" if op == ">=" and float(x) > FO_THRESHOLD else "LOCAL" if op == "<=" and float(x) <= FO_THRESHOLD else "REVIEW")
        else:
            ok = ot == "REVIEW"
        if not ok:
            fail("ownership_rule", c["Ticker"], f"FO {fo!r} bound {bound!r} -> {ot}")
        if c["Foreign_Ownership_Pct"] != "" and not c["FO_As_Of_Date"]:
            fail("ownership_date", c["Ticker"], "FO without an as-of date")

    # 3. company flags
    n_rec = Counter(r["Ticker"] for r in fm if str(r["Is_Foreign"]) == "1")
    core_rec = Counter(r["Ticker"] for r in fm if str(r["Is_Foreign"]) == "1" and r["Role_Group"] in ("Board", "Executive"))
    for c in comps:
        t, flag, st = c["Ticker_Local"], c["Foreign_Manager"], c["Flag_Status"]
        if st not in STATUSES:
            fail("flag_status_value", t, repr(st))
        if (flag == 1) != (st == "FOUND") or (flag == 0) != (st == "NONE_FOUND") or (flag == "" and st in ("FOUND", "NONE_FOUND")):
            fail("flag_vs_status", t, f"flag {flag!r} status {st}")
        if (flag == 1) != (n_rec[t] > 0):
            fail("flag_vs_records", t, f"flag {flag!r}, foreign records {n_rec[t]}")
        if st == "NONE_FOUND" and int(c["N_Unknown_Candidates"] or 0):
            fail("zero_with_open_candidates", t, f"{c['N_Unknown_Candidates']} open")
        if st == "NONE_FOUND" and not c["Verification_Level"]:
            fail("zero_without_level", t, "NONE_FOUND without Verification_Level")
        if c["Foreign_Manager_Core"] == 1 and not core_rec[t]:
            fail("core_flag", t, "Core = 1 without a Board/Executive record")
        if c["Board_Count_Check"] == "MISMATCH":
            fail("board_count", t, f"{c['N_Board_Report']} directors parsed, table 7.2.1 says {c['Total_7_2_1']}")

    # 4. manager rows
    allowed = set(NATIONALITY_EN.values()) | {"UNKNOWN"}
    bx_roles = {r["Role_Record_ID"]: r for r in read_csv(DATA / "boardex_roles.csv")}
    seen = Counter((r["Ticker"], r["Manager_ID"], r["Raw_Position"], r["Role_Group"]) for r in fm)
    for k, n in seen.items():
        if n > 1:
            fail("duplicate_record", " | ".join(k), f"{n} rows")
    for r in fm:
        k = f"{r['Ticker']} {r['Manager_Name']} / {r['Raw_Position']}"
        if not r["Source"]:
            fail("record_source", k, "no Source")
        if r["Evidence_Type"] not in EVIDENCE_TYPES:
            fail("record_evidence_type", k, repr(r["Evidence_Type"]))
        if str(r["Is_Foreign"]) == "1" and not (r["Evidence_Quote"] and r["Nationality_Raw"]):
            fail("record_quote", k, "Is_Foreign = 1 without Evidence_Quote / Nationality_Raw")
        if r["Nationality"] not in allowed:
            fail("record_nationality_value", k, repr(r["Nationality"]))
        if r["Country_Evidence_Type"] not in COUNTRY_EVIDENCE:
            fail("record_country_evidence", k, repr(r["Country_Evidence_Type"]))
        if r["Nationality"] not in ("UNKNOWN", "") and not r["Country_Evidence_Type"]:
            fail("record_country_evidence", k, "country without Country_Evidence_Type")
        if not r["Role_Group"]:
            fail("record_role_group", k, "no Role_Group")
        if r["Evidence_Type"] == "BOARDEX":
            ids = re.findall(r"role record (\d+)", r["Source"] + " " + r["Evidence_Quote"])
            if not r["BoardEx_Director_ID"]:
                fail("boardex_id", k, "BOARDEX row without BoardEx_Director_ID")
            for i in ids:
                if bx_roles.get(i, {}).get("FY2025_Valid") != "YES":
                    fail("boardex_period", k, f"role record {i} is not an FY2025 role")
        if r["Local_File"]:
            if not (ROOT / r["Local_File"]).exists():
                fail("record_file", k, f"missing file {r['Local_File']}")
                continue
            text = page_text(r["Local_File"], int(r["Page"] or 0))
            if not text:
                fail("record_page", k, f"page {r['Page']} not in {Path(r['Local_File']).name}")
            elif r["Evidence_Type"] == "ONE_REPORT_FIELD":
                tokens = [w for w in re.split(r"\s+", re.sub(r"[^\w\s]", " ", r["Name_Raw"])) if len(w) >= 3]
                if not any(w.lower() in text.lower() for w in tokens):
                    fail("record_name_on_page", k, f"name not on page {r['Page']}")
                if not re.search(r"(Thai nationality|สัญชาติไทย)\s*:\s*(No|ไม่ใช่)", text):
                    fail("record_no_on_page", k, f"no 'Thai nationality: No' on page {r['Page']}")
        elif r["Evidence_Type"] not in ("BOARDEX",) and not r["Source_URL"]:
            fail("record_locator", k, "neither Page + Local_File nor Source_URL")

    # 5. every One Report / BoardEx conflict has a decision
    if "Source_Conflicts" in wb.sheetnames:
        for x in sheet(wb, "Source_Conflicts"):
            if x["Decision"] in ("", "OPEN"):
                fail("conflict_open", f"{x['Ticker_Local']} {x['Name']}", f"{x['One_Report']} vs {x.get('BoardEx') or x.get('Other_Source', '')}")

    write_csv(DATA / "qa_report.csv", out, ["Check", "Key", "Detail"])
    print(f"checks run on {path.name}: {len(out)} violation(s)")
    for check, n in Counter(o["Check"] for o in out).most_common():
        print(f"  {check}: {n}")
    for o in out[:30]:
        print("   ", o)

    if "sample" in sys.argv:
        rng = random.Random(QA_SEED)
        recs = rng.sample(fm, min(math.ceil(0.10 * len(fm)), len(fm)))
        write_csv(DATA / "qa_sample_records.csv", recs, list(fm[0].keys()))
        zero = sorted((c for c in comps if c["Foreign_Manager"] == 0), key=lambda c: c["Ticker_Local"])
        picks = rng.sample(zero, min(QA_ZERO_COMPANIES, len(zero)))
        write_csv(DATA / "qa_sample_companies.csv", picks, list(comps[0].keys()))
        print(f"sample: {len(recs)} records, {len(picks)} flag-0 companies")


if __name__ == "__main__":
    main()

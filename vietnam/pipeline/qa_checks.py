"""Step 7 – automatic checks on the final workbook, plus the random samples for the manual check.

Usage: python -I vietnam/pipeline/qa_checks.py full            checks; prints every violation, writes data/<run>/qa_report.csv
       python -I vietnam/pipeline/qa_checks.py full sample     also draws the manual-check samples (seed QA_SEED):
                                                      ~10% of Foreign_Managers rows (all OCR rows not yet image-checked
                                                      included) and QA_ZERO_COMPANIES companies with flag 0
                                                      -> data/<run>/qa_sample_records.csv, qa_sample_companies.csv
A check passes when it lists no violation. The manual results go to data/manual/qa_manual.csv.
"""
import csv
import json
import math
import random
import re
import sys
from collections import Counter
from importlib import import_module
from pathlib import Path

from openpyxl import load_workbook

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2] / "shared")]  # python -I; country config first
from common import strip_accents, write_csv
from config import BLOOMBERG_FILE, DATA, FO_THRESHOLD, NATIONALITY_EN, OUTPUT, ROOT

QA_SEED = 20261101
QA_ZERO_COMPANIES = 30
EVIDENCE_TYPES = {"DOC_FIELD", "CV", "DISCLOSURE_FORM", "WEBSITE", "NEWS", "BIRTHPLACE", "INFERRED"}  # BIRTHPLACE: user decision 2026-11-02
STATUSES = {"FOUND", "NONE_FOUND", "UNRESOLVED", "NO_SOURCE", "NOT_SEARCHED", "OUT_OF_SCOPE"}
MANUAL_FO_METHODS = {"RULE_FOREIGN_LISTED_FOREIGN_CONTROLLER"}


def name_on_page(run: str, r: dict) -> bool:
    """The page text (03c JSONL; OCR text for scanned pages), or the page before it (profiles that run over a page
    break), holds one of the person's name tokens (>= 4 letters), or a 4-letter piece of it (OCR errors); True when
    the page text is not available."""
    f = DATA / run / "text" / r["Ticker"] / (Path(r["Local_File"]).name + ".jsonl")
    if not f.exists():
        return True
    want = {int(r["Page"]), int(r["Page"]) - 1}
    with f.open(encoding="utf-8") as fh:
        text = " ".join(pg["text"] for pg in map(json.loads, fh) if pg["page"] in want)
    text = re.sub(r"[^a-z]", "", strip_accents(text).lower())
    words = re.sub(r"[^a-z ]", " ", strip_accents(r["Manager_Name"]).lower()).split()
    tokens = [t for t in words if len(t) >= 4] or ["".join(words)]  # "Lee Ka Wai" -> "leekawai"
    return any(t[i:i + 4] in text for t in tokens for i in range(len(t) - 3))


def sheet(wb, name: str) -> list[dict]:
    rows = wb[name].iter_rows(values_only=True)
    head = next(rows)
    return [dict(zip(head, ["" if v is None else v for v in r])) for r in rows]


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "full"
    path = OUTPUT / ("Vietnam_2025_Foreign_Managers.xlsx" if run == "full" else f"Vietnam_2025_Foreign_Managers_{run}.xlsx")
    wb = load_workbook(path, read_only=True)
    comps, fm = sheet(wb, "Companies"), sheet(wb, "Foreign_Managers")
    out = []

    def fail(check: str, key: str, detail: str) -> None:
        out.append({"Check": check, "Key": key, "Detail": detail})

    # 1. one row per Bloomberg security; Bloomberg_Raw equals the input cell by cell
    src = list(load_workbook(BLOOMBERG_FILE, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
    raw = list(wb["Bloomberg_Raw"].iter_rows(values_only=True))
    n_sec = sum(1 for r in src if isinstance(r[0], str) and r[0].endswith(" Equity"))
    if len(comps) != n_sec or len({c["Ticker"] for c in comps}) != n_sec:
        fail("companies_rows", "", f"Companies {len(comps)} rows, Bloomberg {n_sec} securities")
    if len(raw) != len(src):
        fail("bloomberg_raw_rows", "", f"{len(raw)} vs {len(src)}")
    for i, (a, b) in enumerate(zip(src, raw), 1):
        a, b = list(a), list(b) + [None] * (len(a) - len(b))
        if any(x != y and not (isinstance(x, (int, float)) and isinstance(y, (int, float)) and math.isclose(x, y, rel_tol=1e-12))
               for x, y in zip(a, b)):
            fail("bloomberg_raw_cells", f"row {i}", "differs from the input file")

    # 2. ownership type follows the rule
    for c in comps:
        fo, ot, key = c["Foreign_Ownership_Pct"], c["Ownership_Type"], c["Ticker"]
        if str(c["In_Scope"]) != "1":
            continue
        if c["FO_Method"] in MANUAL_FO_METHODS:
            ok = ot == "FOREIGN_MAJORITY"
        elif fo == "" and str(c["FO_Bound"]).startswith((">=", "<=")):  # bound read from a filing (foreign-listed issuers)
            op, x = str(c["FO_Bound"]).split()
            ok = ot == ("FOREIGN_MAJORITY" if op == ">=" and float(x) > FO_THRESHOLD
                        else "LOCAL" if op == "<=" and float(x) <= FO_THRESHOLD else "REVIEW")
        elif fo == "":
            ok = ot == "REVIEW"
        else:
            ok = ot == ("FOREIGN_MAJORITY" if float(fo) > FO_THRESHOLD else "LOCAL")
        if not ok:
            fail("ownership_rule", key, f"FO {fo!r} -> {ot}")

    # 3. company flags
    n_rec = Counter(r["Ticker"] for r in fm if str(r["Is_Foreign"]) == "1")
    for c in comps:
        t, flag, st = c["Ticker_Local"], c["Foreign_Manager"], c["Flag_Status"]
        if st not in STATUSES:
            fail("flag_status_value", t, repr(st))
        if str(c["In_Scope"]) == "1" and str(c["Manager_Search"]) == "1" and st == "OUT_OF_SCOPE":
            fail("flag_status_scope", t, "searched company marked OUT_OF_SCOPE")
        if (flag == 1) != (st == "FOUND") or (flag == 0) != (st == "NONE_FOUND") or (flag == "" and st in ("FOUND", "NONE_FOUND")):
            fail("flag_vs_status", t, f"flag {flag!r} status {st}")
        if st == "NONE_FOUND" and int(c["N_Unknown_Candidates"] or 0):
            fail("zero_with_open_candidates", t, f"{c['N_Unknown_Candidates']} open")
        company_level = c["Flag_Basis"] == "COMPANY_LEVEL_STATEMENT"  # user decision 2026-11-01: unnamed foreign member
        if (flag == 1) != (n_rec[t] > 0 or company_level) or (company_level and n_rec[t]):
            fail("flag_vs_records", t, f"flag {flag!r}, foreign records {n_rec[t]}, basis {c['Flag_Basis']!r}")
        if n_rec[t] and c["Ownership_Type"] == "FOREIGN_MAJORITY" and str(c["Manager_Search"]) != "1":  # borderline 50-55% is searched
            fail("records_in_foreign_majority", t, "manager records for a FOREIGN_MAJORITY company")
        core = c["Foreign_Manager_Core"]
        if core == 1 and not company_level and not (int(c["N_Foreign_Board"] or 0) + int(c["N_Foreign_Supervisory"] or 0)
                                                    + int(c["N_Foreign_Executive"] or 0)):
            fail("core_flag", t, "Core = 1 without a Board/Supervisory/Executive record")

    # 4. manager rows: source, page or URL, evidence, nationality list, duplicates, page within the PDF
    allowed = set(NATIONALITY_EN.values()) | {"UNKNOWN"}
    pages = {}
    for f in ("pdf_stats.csv", "pdf_stats_verify.csv", "pdf_stats_fallback.csv", "pdf_stats_verify_old.csv"):
        if (DATA / run / f).exists():
            with (DATA / run / f).open(encoding="utf-8") as fh:
                pages |= {r["Local_File"]: r["N_Pages"] for r in csv.DictReader(fh)}
    seen = Counter((r["Ticker"], r["Manager_ID"], r["Raw_Position"], r["Role_Group"]) for r in fm)
    for k, n in seen.items():
        if n > 1:
            fail("duplicate_record", " | ".join(k), f"{n} rows")
    for r in fm:
        key = f"{r['Ticker']} {r['Manager_Name']} / {r['Raw_Position']}"
        if not r["Source"]:
            fail("record_source", key, "no Source")
        if not (r["Page"] and r["Local_File"]) and not r["Source_URL"]:
            fail("record_locator", key, "neither Page + Local_File nor Source_URL")
        if r["Evidence_Type"] not in EVIDENCE_TYPES and str(r["Is_Foreign"]) != "":  # UNKNOWN rows have no nationality evidence
            fail("record_evidence_type", key, repr(r["Evidence_Type"]))
        if str(r["Is_Foreign"]) == "1" and not (r["Evidence_Quote"] and r["Nationality_Raw"]):
            fail("record_quote", key, "Is_Foreign = 1 without Evidence_Quote / Nationality_Raw")
        for n in str(r["Nationality"]).split("; "):
            if n not in allowed:
                fail("record_nationality_value", key, repr(r["Nationality"]))
        if str(r["Is_Foreign"]) == "" and r["Evidence_Type"]:
            fail("record_unknown_evidence_type", key, f"UNKNOWN row with Evidence_Type {r['Evidence_Type']!r}")
        if r["Nationality"] == "UNKNOWN" and str(r["Is_Foreign"]) == "0":
            fail("record_unknown_is_0", key, "UNKNOWN nationality with Is_Foreign = 0")
        if not r["Role_Group"]:
            fail("record_role_group", key, "no Role_Group")
        if r["Local_File"]:
            if not (ROOT / r["Local_File"]).exists():
                fail("record_file", key, f"missing file {r['Local_File']}")
            elif r["Local_File"] in pages and pages[r["Local_File"]] and int(r["Page"]) > int(pages[r["Local_File"]]):
                fail("record_page", key, f"page {r['Page']} > {pages[r['Local_File']]} pages")
            elif not name_on_page(run, r):
                fail("record_name_on_page", key, f"no name token found on page {r['Page']} of {Path(r['Local_File']).name}")

    # 5. every main-AR page with a non-Vietnam nationality label is accounted for: a record or decision on that page,
    #    or a reviewed entry in data/manual/label_page_checks.csv (career text, English duplicate, word noise, ...)
    pr = import_module("05c_propose_records")
    seen_pages = {(r["Ticker"], str(r["Page"])) for r in fm}
    for f in ("candidate_decisions.csv", "label_page_checks.csv"):
        if (DATA / "manual" / f).exists():
            with (DATA / "manual" / f).open(encoding="utf-8") as fh:
                seen_pages |= {(d["Ticker_Local"], d["Page"]) for d in csv.DictReader(fh) if d["Page"]}
    with (DATA / run / "nationality_hits.csv").open(encoding="utf-8") as fh:
        for h in csv.DictReader(fh):
            nat = pr.nationality_en(h["Value_Raw"]) if h["Hit_Type"] == "FIELD" else ""
            foreign = h["Hit_Type"] == "COUNTRY_NEAR_FIELD" or (h["Hit_Type"] == "FIELD" and (
                h["Value_Class"] == "FOREIGN" or nat not in ("", "Vietnam")))
            if foreign and (h["Ticker_Local"], h["Page"]) not in seen_pages:
                seen_pages.add((h["Ticker_Local"], h["Page"]))
                fail("label_page_unreviewed", f"{h['Ticker_Local']} p{h['Page']}", (h["Value_Raw"] or h["Matched"])[:60])

    write_csv(DATA / run / "qa_report.csv", out, ["Check", "Key", "Detail"])
    print(f"checks run on {path.name}: {len(out)} violation(s)")
    for check, n in Counter(o["Check"] for o in out).most_common():
        print(f"  {check}: {n}")
    for o in out[:40]:
        print("   ", o)

    if "sample" in sys.argv:
        rng = random.Random(QA_SEED)
        forced = [r for r in fm if "image check pending" in str(r["Note"])]
        rest = [r for r in fm if r not in forced]
        n = max(0, math.ceil(0.10 * len(fm)) - len(forced))
        recs = forced + rng.sample(rest, min(n, len(rest)))
        write_csv(DATA / run / "qa_sample_records.csv",
                  [{"Why": "OCR, image check pending" if r in forced else "random 10%", **r} for r in recs],
                  ["Why"] + list(fm[0].keys()))
        zero = sorted((c for c in comps if c["Foreign_Manager"] == 0), key=lambda c: c["Ticker_Local"])
        picks = rng.sample(zero, min(QA_ZERO_COMPANIES, len(zero)))
        write_csv(DATA / run / "qa_sample_companies.csv", picks, list(comps[0].keys()))
        print(f"sample: {len(recs)} records ({len(forced)} forced), {len(picks)} flag-0 companies")


if __name__ == "__main__":
    main()

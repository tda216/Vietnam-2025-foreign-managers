"""Indonesia step 10 – workbook indonesia/output/Indonesia_2025_Foreign_Managers.xlsx (+ QA sheet).

Company flags (shared rules; missing is never 0):
  1   FOUND          at least one foreign-national manager recorded (any level) or a company-level statement
                     Foreign_Manager_Core = 1 when one of them is Board / Executive
  0   NONE_FOUND     LOCAL, AR 2025 screened (profiles carry nationality labels), no foreign manager; members who left in
                     2025 checked in the AR 2024 where available (unresolved names listed in Open_Items)
  ''  UNRESOLVED     LOCAL, AR 2025 read but the profiles carry no nationality label at all
  ''  NO_SOURCE      LOCAL, no AR 2025 (website, IDX)
  ''  FO_REVIEW      FO not settled (KSEI bounds straddle 50 %, AR table not usable yet) – managers not searched
  ''  NOT_SEARCHED_FM  FOREIGN_MAJORITY: no manager search (owner, 8 Nov 2026)
  ''  OUT_OF_SCOPE   funds / ETF / DIRE, foreign-listed, not listed in 2025
Run from the project root:  .venv/bin/python -I indonesia/pipeline/id10_build_workbook.py
"""
import csv, re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
M = D / "manual"
OUT = ROOT / "output" / "Indonesia_2025_Foreign_Managers.xlsx"


def rows(p):
    p = Path(p)
    return list(csv.DictReader(p.open(encoding="utf-8-sig"))) if p.exists() else []


def main():
    uni = rows(D / "universe.csv")
    fo = {r["Code"]: r for r in rows(D / "fo_classification.csv")}
    rec = rows(M / "manager_records.csv")
    cle = rows(M / "company_level_evidence.csv")
    dec = rows(M / "candidate_decisions.csv")
    own = rows(M / "ownership_ar.csv")
    reviews = rows(M / "ar_file_reviews.csv")
    docs = rows(D / "screen_docs.csv")
    dep = rows(D / "departures_ar2024.csv")
    tix = rows(D / "text_index.csv")
    web = {r["Code"]: r for r in rows(D / "web_ar_files.csv") if r["Check"] == "VERIFIED"}
    idx = {r["Code"]: r for r in rows(D / "idx_ar_files.csv") if r.get("File")}
    rejected = {r["File"] for r in reviews if r["Decision"].startswith("REJECTED")}

    by_code = defaultdict(list)
    for r in rec:
        by_code[r["Code"]].append(r)
    cle_codes = {r["Code"] for r in cle}
    labels = defaultdict(lambda: [0, 0])
    for d in docs:
        if d["File"] in rejected:
            continue
        labels[d["Code"]][0] += int(d["Indonesian_Labels"] or 0); labels[d["Code"]][1] += int(d["Foreign_Labels"] or 0)
    pages_by = Counter()
    for r in tix:
        if r.get("SHA256") and r["File"] not in rejected:
            pages_by[r["Code"]] += int(r.get("Pages") or 0)
    have_text = {c for c, n in pages_by.items() if n >= 30}  # cover letters / short attachments only = no AR text
    dep_open = Counter(r["Code"] for r in dep if r["Status"] in ("NO_LABEL", "NAME_NOT_FOUND", "NO_AR2024"))

    comp_rows, flags = [], Counter()
    for u in uni:
        c = u["Code"]
        f = fo.get(c, {})
        cls = f.get("FO_Class", "")
        rs = by_code.get(c, [])
        core = any(r["Role_Group"] in ("Board", "Executive") for r in rs)
        if u.get("In_Scope") != "1" or u.get("Security_Kind") != "COMPANY":
            st, fl, fc = "OUT_OF_SCOPE", "", ""
        elif cls == "FOREIGN_MAJORITY":
            st, fl, fc = "NOT_SEARCHED_FM", "", ""
        elif cls != "LOCAL":
            st, fl, fc = "FO_REVIEW", "", ""
        elif rs or c in cle_codes:
            st, fl, fc = "FOUND", 1, int(core or (c in cle_codes and any(x["Role_Group"] in ("Board", "Executive") for x in cle if x["Code"] == c)))
        elif c not in have_text:
            st, fl, fc = "NO_SOURCE", "", ""
        elif labels[c] == [0, 0]:
            st, fl, fc = "UNRESOLVED", "", ""
        else:
            st, fl, fc = "NONE_FOUND", 0, 0
        flags[st] += 1
        src = "IDX (www.idx.id)" if c in idx else "Company website" if c in web else ""
        comp_rows.append({
            "Country": "Indonesia", "Code": c, "Bloomberg_Ticker": u.get("Bloomberg_Ticker", ""), "Company": f.get("Company") or u.get("KSEI_Issuer") or u.get("Short_Name", ""),
            "Security_Kind": u.get("Security_Kind", ""), "Listing_Status": u.get("Listing_Status", ""), "In_Scope": u.get("In_Scope", ""),
            "Scope_Reason": u.get("Scope_Reason", ""), "Industry_Group": u.get("Industry_Group", ""), "Market_Cap": u.get("Market_Cap", ""),
            "KSEI_Class_20251230": f.get("KSEI_Class", ""), "FO_Lower_KSEI": f.get("FO_Lower", ""), "FO_Upper_KSEI": f.get("FO_Upper", ""),
            "FO_Class": cls, "FO_Pct_AR": f.get("FO_Pct", ""), "FO_Source": f.get("FO_Source", ""), "FO_Page": f.get("FO_Page", ""),
            "FO_File": f.get("FO_File", ""), "FO_Status": f.get("FO_Status", ""), "Manager_Search": int(cls == "LOCAL"),
            "AR2025_Source": src, "Foreign_Manager": fl, "Foreign_Manager_Core": fc, "Flag_Status": st,
            "Foreign_Manager_Rows": len(rs), "Foreign_Board_Exec_Rows": sum(r["Role_Group"] in ("Board", "Executive") for r in rs),
            "Company_Level_Statement": int(c in cle_codes), "Indonesian_Labels": labels[c][0] if c in labels else "",
            "Departed_Names_Unresolved": dep_open.get(c, "") if cls == "LOCAL" else ""})

    # QA (automatic checks; 0 violations expected)
    qa = []
    def check(name, bad, detail):
        qa.append({"Check": name, "Violations": len(bad), "Examples": "; ".join(map(str, bad[:8])), "Detail": detail})
    status = {r["Code"]: r["Flag_Status"] for r in comp_rows}
    check("record_in_non_local_firm", [f'{r["Code"]}:{r["Manager_Name"]}' for r in rec if status.get(r["Code"]) != "FOUND"],
          "Every record belongs to a LOCAL firm with Flag_Status FOUND (FO changes after a rerun must be reviewed)")
    check("record_missing_quote_or_page", [f'{r["Code"]}:{r["Manager_Name"]}' for r in rec if not r["Evidence_Quote"] or not r["Page"]],
          "Quote and PDF page present (quotes are machine-checked against the page when the batch is added)")
    check("record_bad_role_group", [r["Code"] for r in rec if r["Role_Group"] not in ("Board", "Executive", "Other_Manager")], "Role group valid")
    check("record_left_before_2025", [f'{r["Code"]}:{r["Manager_Name"]}' for r in rec if r["Resigned_Date"][:4].isdigit() and r["Resigned_Date"][:4] < "2025"],
          "FY2025 = held the position at any time in 2025")
    check("record_appointed_after_2025", [f'{r["Code"]}:{r["Manager_Name"]}' for r in rec if r["Appointed_Date"][:4].isdigit() and r["Appointed_Date"][:4] > "2025"],
          "Appointments in 2026 are not FY2025 (candidate decision NOT_FY2025)")
    dup = Counter((r["Code"], r["Manager_Name"].lower(), r["Raw_Position"].lower()) for r in rec)
    check("record_duplicate", [k for k, v in dup.items() if v > 1], "One row per person x position")
    check("flag_zero_without_source", [r["Code"] for r in comp_rows if r["Foreign_Manager"] == 0 and r["Code"] not in have_text],
          "A 0 flag needs a screened AR 2025")
    check("flag_set_outside_local", [r["Code"] for r in comp_rows if r["Foreign_Manager"] != "" and r["FO_Class"] != "LOCAL"],
          "Flags only for LOCAL firms")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "README"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "Listed Companies & Foreign Managers – Indonesia FY2025", f"Built {now} by indonesia/pipeline/id10_build_workbook.py",
        "", "Scope: Bloomberg list of IDX securities; companies listed in 2025 (KSEI master file); funds / ETF / DIRE and foreign-listed out.",
        "FO: KSEI holding composition 30 Dec 2025 (bounds) -> AR 2025 local/foreign table or named >= 5% holders where the bounds straddle 50% (owner rules 6a, 8a).",
        "Managers: LOCAL firms only (owner, 8 Nov 2026: no search for foreign-majority firms). Calendar 2025. Komisaris = Board, Direksi = Executive, C-suite = Executive, committee-only / heads = Other_Manager.",
        "Sources: AR 2025 from company websites or IDX (www.idx.id); AR 2024 for members who left during 2025. Every record: file, PDF page (1-based), verbatim quote (machine-checked), page image viewed when names are in graphics or pages hold several profiles.",
        "Flags: Foreign_Manager 1/0/blank (blank = no conclusion; see Flag_Status); Foreign_Manager_Core counts Board/Executive only.",
        "", "Flag_Status counts: " + ", ".join(f"{k} {v}" for k, v in flags.most_common()),
        f"Foreign_Managers rows: {len(rec)} in {len(by_code)} companies", "Open items: sheet Open_Items; method and decisions: indonesia/AGENTS.md, OPEN_DECISIONS.md"]
    for i, t in enumerate(lines, 1):
        ws.cell(i, 1, t)
    ws["A1"].font = Font(bold=True, size=13); ws.column_dimensions["A"].width = 160

    NUMRX = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE]-?\d+)?")

    TEXT = {"Code", "Bloomberg_Ticker", "Appointed_Date", "Resigned_Date", "As_Of", "FO_Pct", "FO_Pct_AR", "FO_Pct_Col2",
            "Reviewed_On", "Reviewed", "Name", "Manager_Name"}  # identifiers, dates ('2025' = year only) and bounds stay text

    def val(v, col=""):
        """Numbers read from CSV as text become numbers ('1' -> 1, '0.0853' -> 0.0853) so Stata / R / pandas see numeric
        columns; '' becomes a truly empty cell (missing). Kept as text: '<=44.77', '124;125', dates, '000123'."""
        if col in TEXT:
            return None if v == "" else v
        if isinstance(v, str):
            if v == "":
                return None
            if NUMRX.fullmatch(v):
                return float(v) if any(ch in v for ch in ".eE") else int(v)
        return v

    def sheet(name, data, cols=None):
        w = wb.create_sheet(name)
        cols = cols or (list(data[0].keys()) if data else ["(empty)"])
        w.append(cols)
        for r in data:
            w.append([val(r.get(c, ""), c) for c in cols])
        for j, c in enumerate(cols, 1):
            w.cell(1, j).font = Font(bold=True); w.cell(1, j).fill = PatternFill("solid", fgColor="DDEBF7")
            w.column_dimensions[get_column_letter(j)].width = min(45, max(10, len(c) + 2))
        w.freeze_panes = "A2"
    sheet("Companies", comp_rows)
    sheet("Foreign_Managers", rec)
    sheet("Company_Level_Evidence", cle)
    sheet("Ownership_AR_Manual", own)
    sheet("FO_Classification", list(fo.values()))
    sheet("Candidate_Decisions", dec)
    sheet("AR_File_Reviews", reviews)
    sheet("Departures_AR2024", [{k: v for k, v in r.items() if k != "Snippet"} for r in dep])
    open_items = [{"Type": "FO_REVIEW", "Code": r["Code"], "Detail": r["FO_Status"]} for r in comp_rows if r["Flag_Status"] == "FO_REVIEW"]
    open_items += [{"Type": r["Flag_Status"], "Code": r["Code"], "Detail": ""} for r in comp_rows if r["Flag_Status"] in ("NO_SOURCE", "UNRESOLVED")]
    known = {(r["Code"], w) for r in rec + [{"Code": d["Code"], "Manager_Name": d["Name"]} for d in dec]
             for w in r["Manager_Name"].lower().split() if len(w) > 3}
    open_items += [{"Type": "DEPARTED_NAME_UNRESOLVED", "Code": r["Code"], "Detail": f'{r["Name"]} ({r["Status"]})'} for r in dep
                   if r["Status"] in ("NO_LABEL", "NAME_NOT_FOUND", "NO_AR2024") and status.get(r["Code"]) in ("NONE_FOUND", "FOUND")
                   and not any((r["Code"], w) in known for w in r["Name"].lower().split() if len(w) > 3)]
    sheet("Open_Items", open_items, ["Type", "Code", "Detail"])
    sheet("QA", qa)
    wb.save(OUT)
    print("saved", OUT.relative_to(ROOT.parent), "| flags:", dict(flags), "| records", len(rec))
    for q in qa:
        print(f'  QA {q["Check"]}: {q["Violations"]}', q["Examples"][:120])


if __name__ == "__main__":
    main()

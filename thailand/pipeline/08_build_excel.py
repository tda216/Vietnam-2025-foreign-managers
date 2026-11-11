"""Step 8 – final workbook: thailand/output/Thailand_2025_Foreign_Managers.xlsx

Inputs: data/companies_step2.csv (step 6), data/roster.csv, records_auto.csv, candidates.csv, source_conflicts.csv
(step 7), data/report_stats.csv (step 5) and the hand-reviewed files in data/manual/:
  manager_records.csv     foreign people found by hand (resolved candidates); same columns as records_auto.csv
  country_records.csv     the country of a person whose One Report row says only "Thai nationality: No"
  candidate_decisions.csv how each open candidate was settled (FOREIGN -> manager_records, NOT_FOREIGN_STATED, ...)
  conflict_decisions.csv  decision on each One Report / BoardEx disagreement
Flag rules (company level, never turning missing into 0):
  FOUND (1)        at least one foreign person with an FY2025 position (any level)
  UNRESOLVED ("")  no foreign person yet, open candidates remain
  NONE_FOUND (0)   One Report parsed, no foreign person, no open candidate; Verification_Level says how strong the 0 is:
                   ALL_STATED (every listed director and executive has Thai nationality: Yes), BOARD_STATED (every
                   director stated; executives without the field passed the name screen), SCREEN_ONLY (no field)
  NO_SOURCE ("")   no One Report 2025 for the company; NOT_SEARCHED (foreign-listed); OUT_OF_SCOPE (funds)
Foreign_Manager_Core uses Board + Executive only (comparable across companies); Foreign_Manager adds BoardEx managers
below the executive list, which exist only for the companies BoardEx covers.
Flag_Basis: ONE_REPORT, BOARDEX (no report, BoardEx rows only) or OTHER_FILINGS (no Form 56-1: foreign-listing annual
report, other issuers' filings). Source_Basis: ONE_REPORT_2025 / ONE_REPORT_FY2025_JUL (fiscal year ending 31 Jul 2025) /
ONE_REPORT_2024_FALLBACK (no 2025 report available: last resort) / FOREIGN_LISTING_ANNUAL_REPORT; Source_Note from
data/manual/company_source_notes.csv.
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE), str(_HERE.parents[1] / "shared")]  # scripts run with python -I; Thailand config first

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

from common import now_iso, read_csv
from config import BLOOMBERG_FILE, DATA, FO_AS_OF, FO_THRESHOLD, OUTPUT, YEAR
from xlsx_tables import add_table

CORE = {"Board", "Executive"}
OPEN_DECISIONS = {"", "OPEN"}
FM_COLS = ["Company", "Ticker", "Year", "Manager_Name", "Raw_Position", "Nationality", "Source", "Page", "Manager_ID",
           "Name_Raw", "Nationality_Raw", "Is_Foreign", "Dual_Nationality", "Role_Group", "Appointed_Date", "Resigned_Date",
           "Evidence_Type", "Evidence_Quote", "Thai_Nationality_Stated", "Residing_In_Thailand", "Country_Evidence_Type",
           "Country_Quote", "Country_Source", "BoardEx_Director_ID", "BoardEx_Nationality", "Source_URL", "Local_File",
           "Other_Sources", "Reviewed_On", "Note", "Management_Include"]


def opt(name: str) -> list[dict]:
    p = DATA / name
    return read_csv(p) if p.exists() else []


def key(t: str, name: str) -> tuple[str, str]:
    return t, " ".join(name.lower().split())


def main():
    comps = read_csv(DATA / "companies_step2.csv")
    stats = {s["Ticker_Local"]: s for s in opt("report_stats.csv")}
    roster = opt("roster.csv")
    recs = opt("records_auto.csv") + opt("manual/manager_records.csv")
    country = {key(c["Ticker_Local"], c["Manager_Name"]): c for c in opt("manual/country_records.csv")}
    cands = opt("candidates.csv")
    cdec = {key(d["Ticker_Local"], d["Name"]): d for d in opt("manual/candidate_decisions.csv")}
    conflicts = opt("source_conflicts.csv")
    xdec = {key(d["Ticker_Local"], d["Name"]): d for d in opt("manual/conflict_decisions.csv")}

    # conflict decisions can turn a One Report "No" into a BoardEx error (never the reverse without a source)
    for r in recs:
        d = xdec.get(key(r["Ticker_Local"], r.get("Name_Raw") or r["Manager_Name"]))
        if d and d.get("Decision") == "DUAL_NATIONALITY":
            r["Dual_Nationality"] = "1"
        c = country.get(key(r["Ticker_Local"], r["Manager_Name"]))
        if c and r.get("Nationality") in ("", "UNKNOWN"):
            r.update(Nationality=c["Nationality"], Country_Evidence_Type=c["Country_Evidence_Type"],
                     Country_Quote=c.get("Country_Quote", ""), Country_Source=c.get("Country_Source", ""),
                     Other_Sources="; ".join(x for x in (r.get("Other_Sources", ""), c.get("Country_Source_URL", "")) if x),
                     Reviewed_On=c.get("Reviewed_On", ""), Note="; ".join(x for x in (r.get("Note", ""), c.get("Note", "")) if x))
    for c in cands:
        d = cdec.get(key(c["Ticker_Local"], c["Name"]))
        c["Decision"], c["Decision_Reason"] = ((d["Decision"], d.get("Reason", "")) if d else
                                               (c["Auto_Decision"], "automatic: " + c.get("Note", "")) if c.get("Auto_Decision") else ("OPEN", ""))

    # Manager_ID: one id per person within a company
    ids, per_t = {}, Counter()
    name_of = {c["Ticker_Local"]: c["Company"] for c in comps}
    for r in recs:
        k = (r["Ticker_Local"], r.get("BoardEx_Director_ID") or key("", r["Manager_Name"])[1])
        if k not in ids:
            per_t[r["Ticker_Local"]] += 1
            ids[k] = f"{r['Ticker_Local']}-{per_t[r['Ticker_Local']]:02d}"
        r["Manager_ID"] = ids[k]
    fm_rows = [{"Company": name_of.get(r["Ticker_Local"], ""), "Ticker": r["Ticker_Local"], "Year": YEAR,
                **{k: r.get(k, "") for k in FM_COLS if k not in ("Company", "Ticker", "Year")}} for r in recs]
    rec_t, ros_t, open_t = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in fm_rows:
        rec_t[r["Ticker"]].append(r)
    for p in roster:
        if p["Include_FY2025"] == "YES":
            ros_t[p["Ticker_Local"]].append(p)
    for c in cands:
        if c["Decision"] in OPEN_DECISIONS:
            open_t[c["Ticker_Local"]].append(c)

    # which report a company's flag rests on: One Report 2025 by default; AR2024 = last-resort fallback (no 2025 report);
    # data/manual/company_source_notes.csv adds a note (fiscal year not ending in December, foreign-listing annual report …)
    doc_kind = {d["Local_File"]: d["Doc_Kind"] for d in opt("docs.csv") if d.get("Status") == "OK"}
    notes = {n["Ticker_Local"]: n for n in opt("manual/company_source_notes.csv")}
    out, cov = [], []
    for c in comps:
        t = c["Ticker_Local"]
        foreign = [r for r in rec_t.get(t, []) if str(r["Is_Foreign"]) == "1"]
        core = [r for r in foreign if r["Role_Group"] in CORE]
        st = stats.get(t, {})
        has_report = st.get("Status") == "OK"
        ros = ros_t.get(t, [])
        open_c = open_t.get(t, [])
        if c["In_Scope"] != "1":
            flag, status = "", "OUT_OF_SCOPE"
        elif foreign:
            flag, status = 1, "FOUND"
        elif c["Security_Class"] == "FOREIGN_LISTED" and not has_report:
            flag, status = "", "NOT_SEARCHED"
        elif not has_report:
            flag, status = "", "NO_SOURCE"
        elif open_c:
            flag, status = "", "UNRESOLVED"
        else:
            flag, status = 0, "NONE_FOUND"
        stated = [p for p in ros if p["Thai_Nationality"] or p["Stated_In_Report"]]
        board = [p for p in ros if p["Role_Group"] == "Board"]
        level = ""
        if status == "NONE_FOUND":
            level = ("ALL_STATED" if len(stated) == len(ros) else
                     "BOARD_STATED" if board and all(p["Thai_Nationality"] for p in board) else "SCREEN_ONLY")
        open_core = [x for x in open_c if x["Role_Group"] in CORE]
        core_flag = 1 if core else (0 if flag == 0 or (flag == 1 and not open_core) else "")
        people = lambda rows: len({r["Manager_ID"] for r in rows})
        kind = doc_kind.get(st.get("Parsed_File", ""), "")
        note = notes.get(t, {})
        basis = note.get("Source_Basis") or ("ONE_REPORT_2024_FALLBACK" if kind == "AR2024" else "ONE_REPORT_2025" if has_report else "")
        if has_report:
            flag_basis = "ONE_REPORT"
        elif foreign:
            flag_basis = "BOARDEX" if all(r["Evidence_Type"] == "BOARDEX" for r in foreign) else "OTHER_FILINGS"
        else:
            flag_basis = ""
        out.append({**c, "Foreign_Manager": flag, "Foreign_Manager_Core": core_flag, "Flag_Status": status,
                    "Verification_Level": level,
                    "Flag_Basis": flag_basis, "Source_Basis": basis, "Source_Note": note.get("Note", ""),
                    "N_Foreign_Managers": people(foreign),
                    "N_Foreign_Board": people([r for r in foreign if r["Role_Group"] == "Board"]),
                    "N_Foreign_Executive": people([r for r in foreign if r["Role_Group"] == "Executive"]),
                    "N_Foreign_Other": people([r for r in foreign if r["Role_Group"] not in CORE]),
                    "N_Unknown_Candidates": len(open_c), "N_People_Stated": len(stated), "N_People_Total": len(ros),
                    "N_Board_Report": st.get("N_Board", ""), "Total_7_2_1": st.get("Total_7_2_1", ""),
                    "Board_Count_Check": st.get("Board_Count_Check", ""), "Report_File": st.get("Parsed_File", ""),
                    "Report_Lang": st.get("Report_Lang", ""),
                    "Foreign_Manager_Summary": "; ".join(dict.fromkeys(f"{r['Manager_Name']} – {r['Raw_Position']} ({r['Nationality']})"
                                                                       for r in foreign))})
        cov.append({"Ticker_Local": t, "Security_Class": c["Security_Class"], "In_BoardEx": c["In_BoardEx"],
                    "Report_Status": st.get("Status", "NOT_COLLECTED"), "Report_File": st.get("Parsed_File", ""),
                    "Member_Role": st.get("Member_Role", ""), "Report_Lang": st.get("Report_Lang", ""), "N_Pages": st.get("N_Pages", ""),
                    "N_Board": st.get("N_Board", ""), "N_Left": st.get("N_Left", ""), "N_Executive": st.get("N_Executive", ""),
                    "N_Board_Field": st.get("N_Board_Field", ""), "N_Exec_Field": st.get("N_Exec_Field", ""),
                    "Total_7_2_1": st.get("Total_7_2_1", ""), "Board_Count_Check": st.get("Board_Count_Check", ""),
                    "Open_Candidates": len(open_c), "Flag_Status": status})

    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    scope = [o for o in out if o["In_Scope"] == "1"]
    fs = Counter(o["Flag_Status"] for o in scope)
    loc = [o for o in scope if o["Ownership_Type"] == "LOCAL"]
    lines = [
        (f"Listed Companies & Foreign Managers – Thailand {YEAR} (built {now_iso()})", True), ("", False),
        ("Danh sách gốc: Bloomberg (955 mã có trụ sở ở Thái Lan). Quỹ / REIT / ETF / quỹ hạ tầng nằm ngoài phạm vi (In_Scope = 0).", False),
        (f"Sở hữu nước ngoài (FO): mục tiêu là ngày {FO_AS_OF}; > {FO_THRESHOLD:g}% → FOREIGN_MAJORITY, ≤ {FO_THRESHOLD:g}% → LOCAL, thiếu → REVIEW. "
         "Thứ tự nguồn: số có bản quyền (khi có) > hồ sơ công ty (mã niêm yết ở nước ngoài) > bảng cổ đông theo quốc tịch trong One Report 2025 "
         "> trang factsheet SET (số tại ngày crawl, 11/2026; xem FO_As_Of_Date và FO_Date_Gap_Days). Không có số mà Foreign Limit ≤ 50% → "
         "FO_Bound '<= limit' → LOCAL. NVDR KHÔNG cộng vào FO (quyết định 07/11/2026): xem NVDR_Pct, FO_Plus_NVDR, NVDR_Sensitive.", False),
        ("Manager = người giữ chức HĐQT, ban điều hành hoặc quản lý khác tại chính công ty niêm yết bất kỳ lúc nào trong năm 2025.", False),
        ("Người nước ngoài: One Report 2025 (Form 56-1, mẫu của SEC) ghi 'Thai nationality: Yes/No' cho từng giám đốc (và ban điều hành ở "
         "dạng e-form) → Evidence_Type = ONE_REPORT_FIELD. One Report quyết định (07/11/2026); BoardEx dùng để điền tên nước và bổ sung quản lý "
         "dưới ban điều hành (Evidence_Type = BOARDEX). Mâu thuẫn hai nguồn: sheet Source_Conflicts.", False),
        ("Tên nước (Nationality): One Report chỉ ghi Thai Yes/No. Nước lấy từ BoardEx, tiểu sử, hồ sơ ứng viên ĐHĐCĐ, website/báo chí; "
         "chỉ khi đã tìm hết mới suy luận (Country_Evidence_Type = INFERRED_STRONG/MEDIUM/WEAK). Chưa tìm được → UNKNOWN (Is_Foreign vẫn = 1).", False),
        ("Page = số trang PDF (1-based) của file One Report trong Local_File; Source_URL = đường tải công khai của SEC.", False),
        ("Source_Basis (sheet Companies): ONE_REPORT_2025; ONE_REPORT_FY2025_JUL (năm tài chính kết thúc 31/07/2025); "
         "ONE_REPORT_2024_FALLBACK (chưa có bản 2025 – nguồn cuối cùng, có thể thiếu người nhận chức sau); FOREIGN_LISTING_ANNUAL_REPORT "
         "(công ty Thái niêm yết ở nước ngoài, không có Form 56-1: báo cáo thường niên trên sàn nước ngoài). Ghi chú ở Source_Note.", False),
        ("", False), ("Cờ công ty", True),
        ("Foreign_Manager_Core (HĐQT + ban điều hành) là biến chính. Foreign_Manager tính thêm quản lý cấp dưới, chỉ có ở công ty BoardEx phủ. "
         "0 = NONE_FOUND kèm Verification_Level (ALL_STATED / BOARD_STATED / SCREEN_ONLY). Để trống = UNRESOLVED / NO_SOURCE / NOT_SEARCHED / OUT_OF_SCOPE.", False),
        ("", False), ("Tóm tắt", True),
        (f"Trong phạm vi: {len(scope)} | Flag_Status: " + ", ".join(f"{k} {v}" for k, v in fs.most_common()), False),
        (f"LOCAL: {len(loc)} | Flag_Status: " + ", ".join(f"{k} {v}" for k, v in Counter(o['Flag_Status'] for o in loc).most_common()), False),
        (f"Bản ghi Foreign_Managers: {len(fm_rows)} | Evidence_Type: " + ", ".join(f"{k} {v}" for k, v in Counter(r['Evidence_Type'] for r in fm_rows).most_common()), False),
    ]
    for text, bold in lines:
        ws.append([text])
        if bold:
            ws.cell(ws.max_row, 1).font = Font(bold=True, size=12)
    ws.column_dimensions["A"].width = 160
    add_table(wb, "Companies", out, list(out[0].keys()))
    add_table(wb, "Foreign_Managers", fm_rows, FM_COLS, widths={"Evidence_Quote": 90, "Country_Quote": 60, "Source_URL": 50})
    ros_cols = ["Ticker_Local", "Section", "Seq", "Name_Raw", "Role_Group", "Position_Raw", "Thai_Nationality", "Residing_In_Thailand",
                "Stated_In_Report", "Date_Assumed", "Date_Ended", "Include_FY2025", "FY_Note", "Page", "Local_File", "Report_Lang",
                "BoardEx_Director_ID", "BoardEx_Nationality", "Match_Score"]
    add_table(wb, "Management_Roster", roster, ros_cols)
    if conflicts:
        for x in conflicts:
            d = xdec.get(key(x["Ticker_Local"], x["Name"]), {})
            x["Decision"], x["Decision_Reason"] = d.get("Decision", "OPEN"), d.get("Reason", "")
        add_table(wb, "Source_Conflicts", conflicts, list(conflicts[0].keys()))
    if cands:
        add_table(wb, "Review_Open", sorted(cands, key=lambda c: (c["Decision"] not in OPEN_DECISIONS, c["Ticker_Local"])),
                      list(dict.fromkeys(k for c in cands for k in c)))
    obs = opt("ownership_observations.csv")
    if obs:
        add_table(wb, "Ownership_Observations", obs, list(dict.fromkeys(k for r in obs for k in r)))
    add_table(wb, "Coverage_Log", cov, list(cov[0].keys()))
    if BLOOMBERG_FILE.exists():  # verbatim copy of the input sheet (values); the workbook is git-ignored (licensed data)
        wr = wb.create_sheet("Bloomberg_Raw")
        for row in load_workbook(BLOOMBERG_FILE, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True):
            wr.append(list(row))
    OUTPUT.mkdir(exist_ok=True)
    path = OUTPUT / "Thailand_2025_Foreign_Managers.xlsx"
    wb.save(path)
    print("saved", path, "|", dict(fs), "| LOCAL", dict(Counter(o["Flag_Status"] for o in loc)))


if __name__ == "__main__":
    main()

"""Step 7 – final workbook: output/Vietnam_2025_Foreign_Managers[_<run>].xlsx

Usage: python -I pipeline/07_build_excel.py full|pilot

Sheets: README, Companies (1 row per Bloomberg security, flags), Foreign_Managers (1 row per person x position:
records with Is_Foreign = 1 and UNKNOWN candidates), Candidates (screening list and how each was settled),
Candidate_Decisions, Coverage_Log (documents and search steps per company), Ownership_Observations,
Names_In_AR (person mentions, for roster checks), Roster_CafeF_Now, Bloomberg_Raw (verbatim copy).

Flag rules (company level, never turning missing into 0):
  Foreign_Manager = 1   at least one record with Is_Foreign = 1 (any level); Foreign_Manager_Core uses Board/Supervisory/Executive only.
                        Also (user decision 2026-11-01, Flag_Basis COMPANY_LEVEL_STATEMENT) when the source states that the board has
                        a foreign-national member without naming them (data/manual/company_level_evidence.csv); the person stays UNKNOWN
  blank + UNRESOLVED    a HIGH-priority candidate or an UNKNOWN record is still open (and nothing foreign found yet)
  blank + NO_SOURCE     no readable 2025 annual report, 2025 annual governance report, or (user decision 2026-11-01, noted in
                        Source_Basis) 2024 annual report
  blank + OUT_OF_SCOPE  not in scope, or FOREIGN_MAJORITY (not searched)
  blank + NOT_SEARCHED  in scope but the documents were not processed yet (incl. main AR OCR still pending)
  0 + NONE_FOUND        AR read and names screened, no open HIGH candidate (LOW = single odd token, mostly OCR noise)
"""
import sys
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import now_iso, read_csv
from config import BLOOMBERG_FILE, DATA, FO_AS_OF, FO_THRESHOLD, OUTPUT, YEAR

ck1 = import_module("02e_checkpoint1_excel")
ppl = import_module("03e_people_from_text")
ocr = import_module("03c_extract_text")
CORE = {"Board", "Supervisory", "Executive"}


def opt(path: Path) -> list[dict]:
    return read_csv(path) if path.exists() else []


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "full"
    R = DATA / run
    comps = read_csv(DATA / "companies_step2.csv")
    stats, cands = opt(R / "pdf_stats.csv"), opt(R / "candidates.csv")
    fallback = opt(R / "pdf_stats_fallback.csv")  # 06a: RAR / website ARs, governance reports, AR2024 (AGM2026 not a basis)
    stats += [s for s in fallback if s["Doc_Kind"] in ("AR2025", "GOV2025", "AR2024")]
    company_level = {e["Ticker_Local"]: e for e in opt(DATA / "manual" / "company_level_evidence.csv")}
    docs = opt(R / "docs.csv")
    records = read_csv(DATA / "manual" / "manager_records.csv")
    decisions = opt(DATA / "manual" / "candidate_decisions.csv")
    in_run = {d["Ticker_Local"] for d in docs} | {s["Ticker_Local"] for s in fallback}
    ok_docs = [d for d in docs if d["Status"] == "OK" and not d["Duplicate_Of"]]
    collected = {t for f in (R / "shards").glob("done_*.txt") for t in f.read_text().split()} if run == "full" else set()
    ar_done = {}
    if run == "full":
        for f in ocr.main_ar_files(ok_docs):
            d = next(x for x in ok_docs if x["Local_File"] == f)
            ar_done[d["Ticker_Local"]] = ocr.fs_stop_file(R, d).exists()  # True = OCR / page pass finished

    # Manager_ID: one id per person within a company, in record order
    ids, per_t = {}, Counter()
    for r in records:
        k = (r["Ticker_Local"], ppl.name_key(r["Manager_Name"]))
        if k not in ids:
            per_t[r["Ticker_Local"]] += 1
            ids[k] = f"{r['Ticker_Local']}-{per_t[r['Ticker_Local']]:02d}"
    name_of = {c["Ticker_Local"]: c["Company"] for c in comps}
    fm_rows = [{"Company": name_of.get(r["Ticker_Local"], ""), "Ticker": r["Ticker_Local"], "Year": YEAR,
                "Manager_ID": ids[(r["Ticker_Local"], ppl.name_key(r["Manager_Name"]))], **r,
                "Management_Include": ""} for r in records]
    rec_t = defaultdict(list)
    for r in fm_rows:
        rec_t[r["Ticker"]].append(r)
    st_t = defaultdict(list)
    for s in stats:
        st_t[s["Ticker_Local"]].append(s)
    open_hi = Counter(c["Ticker_Local"] for c in cands if c["Priority"] == "HIGH" and c["Settled"] != "1")
    n_cand = Counter((c["Ticker_Local"], c["Priority"]) for c in cands)

    out, cov = [], []
    for c in comps:
        t = c["Ticker_Local"]
        recs = rec_t.get(t, [])
        foreign = [r for r in recs if r["Is_Foreign"] == "1"]
        unknown = {r["Manager_ID"] for r in recs if r["Is_Foreign"] == ""}
        people = lambda rows: len({r["Manager_ID"] for r in rows})
        ar = [s for s in st_t.get(t, []) if s["Doc_Kind"] == "AR2025" and not s["Error"] and s["N_Pages"] and int(s["N_Pages"]) >= 5]
        gov = [s for s in st_t.get(t, []) if s["Doc_Kind"] == "GOV2025" and not s["Error"] and s["N_Pages"]]
        ar24 = [s for s in st_t.get(t, []) if s["Doc_Kind"] == "AR2024" and not s["Error"] and s["N_Pages"] and int(s["N_Pages"]) >= 5]
        basis = "AR2025" if ar else ("GOV2025" if gov else ("AR2024" if ar24 else ""))
        cl = company_level.get(t)
        if c["In_Scope"] != "1" or c["Manager_Search"] != "1":
            flag, status = "", "OUT_OF_SCOPE"
        elif foreign or cl:
            flag, status = 1, "FOUND"
        elif (t not in in_run and t not in collected) or (run == "full" and t in ar_done and not ar_done[t]):
            flag, status = "", "NOT_SEARCHED"
        elif t not in in_run:  # collected, but no 2025 annual report listed on Vietstock
            flag, status = "", "NO_SOURCE"
        elif not basis:
            flag, status = "", "NO_SOURCE"
        elif open_hi[t] or unknown:
            flag, status = "", "UNRESOLVED"
        else:
            flag, status = 0, "NONE_FOUND"
        core = [r for r in foreign if r["Role_Group"] in CORE] + ([cl] if cl and cl["Role_Group"] in CORE else [])
        out.append({
            **{k: c.get(k, "") for k in ["Country", "Ticker", "Ticker_Local", "Company", "Company_Name_VN", "Exchange_At_FO_Date",
                                        "Exchange", "ISIN", "Industry_Group", "Security_Class", "In_Scope", "Exclusion_Reason",
                                        "Foreign_Ownership_Pct", "FO_Bound", "FO_As_Of_Date", "Ownership_Type", "FO_Method",
                                        "FO_Source", "FO_Source_URL", "FO_Page", "Manager_Search", "Manager_Search_Reason",
                                        "Mcap_Rank", "Deep_Prelim", "Deep_Reason_Prelim"]},
            "Foreign_Manager": flag,
            "Foreign_Manager_Core": (1 if core else (0 if flag == 0 or (flag == 1 and not unknown and not open_hi[t]) else "")) if flag != "" else "",
            "Flag_Status": status,
            "Flag_Basis": ("PERSON_RECORD" if foreign else "COMPANY_LEVEL_STATEMENT" if cl else basis) if status in ("FOUND", "NONE_FOUND") else "",
            "N_Foreign_Managers": people(foreign), "N_Foreign_Unnamed": 1 if cl and not foreign else 0,
            "N_Foreign_Board": people([r for r in foreign if r["Role_Group"] == "Board"]),
            "N_Foreign_Supervisory": people([r for r in foreign if r["Role_Group"] == "Supervisory"]),
            "N_Foreign_Executive": people([r for r in foreign if r["Role_Group"] == "Executive"]),
            "N_Foreign_Other": people([r for r in foreign if r["Role_Group"] not in CORE]),
            "N_Unknown_Candidates": len(unknown) + open_hi[t],
            "Foreign_Manager_Summary": "; ".join(list(dict.fromkeys(f"{r['Manager_Name']} – {r['Raw_Position']} ({r['Nationality']})"
                                                                    for r in foreign))
                                                 + ([f"(unnamed {cl['Role_Group']} member – {cl['Nationality_Stated']}, company-level statement p{cl['Page']})"]
                                                    if cl and not foreign else [])),
        })
        main_ar = max(ar, key=lambda s: (s["N_OCR_Pages"] != "" and s.get("OCR_Stopped_At_FS_Page", "") != "", int(s["N_Pages"])),
                      default=None)
        cov.append({"Ticker_Local": t, "In_Run": int(t in in_run), "Main_AR_OCR_Done": int(ar_done[t]) if t in ar_done else "",
                    "Search_Depth": "STANDARD" if t in in_run else "",
                    "Deep_Prelim": c.get("Deep_Prelim", ""),
                    "Source_Basis": basis, "AR2025_PDFs": len(ar), "GOV2025_PDFs": len(gov), "AR2024_PDFs": len(ar24),
                    "Source_Basis_Note": ("2024 annual report (published 2025): managers in office at its date; not a FY2025 report"
                                          if basis == "AR2024" else ""),
                    "Fallback_Not_Basis": ", ".join(f"{k} {v}" for k, v in sorted(Counter(
                        s["Doc_Kind"] for s in fallback if s["Ticker_Local"] == t and s["Doc_Kind"] not in ("AR2025", "GOV2025", "AR2024")).items())),
                    "Main_AR_File": main_ar["Local_File"] if main_ar else "",
                    "Main_AR_Pages": main_ar["N_Pages"] if main_ar else "",
                    "Main_AR_Text_Pages": main_ar["N_Text_Pages"] if main_ar else "",
                    "Main_AR_OCR_Pages": main_ar["N_OCR_Pages"] if main_ar else "",
                    "OCR_Stopped_At_FS_Page": main_ar.get("OCR_Stopped_At_FS_Page", "") if main_ar else "",
                    "AR_Nationality_Labels": sum(int(s["N_Field_Hits"] or 0) for s in ar),
                    "Candidates_HIGH": n_cand[(t, "HIGH")], "Candidates_LOW": n_cand[(t, "LOW")],
                    "Open_HIGH": open_hi[t], "Records": len(recs), "Flag_Status": status})

    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    scope = [o for o in out if o["In_Scope"] == "1"]
    fs = Counter(o["Flag_Status"] for o in scope)
    lines = [
        (f"Listed Companies & Foreign Managers – Vietnam {YEAR} ({run}, built {now_iso()})", True), ("", False),
        (f"Sở hữu nước ngoài: đo tại {FO_AS_OF} (file VSDC 'FOL 31.12.2025'); > {FO_THRESHOLD:g}% → FOREIGN_MAJORITY, "
         f"≤ {FO_THRESHOLD:g}% → LOCAL, thiếu → REVIEW. Mọi giá trị FO thu được: sheet Ownership_Observations; các mã xác định thủ công "
         "(niêm yết ở nước ngoài, hủy niêm yết): data/manual/ownership_manual.csv. Hướng dẫn sử dụng: output/BAO_CAO_BAN_GIAO.md.", False),
        ("Manager = người giữ chức HĐQT / BKS (UBKT) / Ban điều hành / quản lý khác tại chính công ty niêm yết bất kỳ lúc nào "
         "trong năm 2025 (chức danh ở công ty con không tính).", False),
        ("Quốc tịch chỉ lấy khi nguồn ghi rõ; tên chỉ dùng để sàng lọc. Quốc tịch kép: Is_Foreign = 1 + Dual_Nationality = 1. "
         "'Người nước ngoài' không ghi nước → Is_Foreign = 1, Nationality = UNKNOWN. Nguồn mâu thuẫn → giữ câu ghi cho từng "
         "người + ghi chú NATIONALITY_CONFLICT.", False),
        ("Evidence_Type: DOC_FIELD (BCTN/báo cáo quản trị), CV (tài liệu ĐHĐCĐ), WEBSITE (website công ty), NEWS (báo chí ghi rõ "
         "quốc tịch), BIRTHPLACE (chỉ có nơi sinh ở nước ngoài); tài liệu của tổ chức khác về cùng một người được chấp nhận khi xác nhận được danh tính.", False),
        ("Page = số trang PDF (1-based). Trang OCR đã được mở ảnh để đối chiếu trước khi ghi bản ghi.", False),
        ("", False), ("Cờ công ty", True),
        ("Foreign_Manager = 1: có ≥ 1 người nước ngoài (mọi cấp). Foreign_Manager_Core: chỉ HĐQT/BKS/Ban điều hành "
         "(so sánh được giữa các công ty). 0 = NONE_FOUND: đã đọc BCTN 2025 + sàng lọc tên, không còn ứng viên HIGH; "
         "không có nghĩa là đã xác minh quốc tịch từng người (người nước ngoài mang tên Việt/Hán-Việt chỉ lộ ra khi nguồn ghi quốc tịch). "
         "Để trống = UNRESOLVED / NO_SOURCE / NOT_SEARCHED / OUT_OF_SCOPE.", False),
        ("Quyết định 01/11/2026: (1) BCTN chỉ ghi 'HĐQT có 1 thành viên quốc tịch nước ngoài' mà không nêu tên → cờ = 1, "
         "Flag_Basis = COMPANY_LEVEL_STATEMENT (sheet Company_Level_Evidence), người vẫn UNKNOWN; (2) không có BCTN 2025 và báo cáo "
         "quản trị 2025 → dùng BCTN 2024 (Source_Basis = AR2024, nhân sự tại thời điểm công bố đầu 2025); (3) thành viên chỉ thuộc "
         "tiểu ban của HĐQT → UNKNOWN, Role_Group = Other_Manager.", False),
        ("Quyết định 02/11/2026: (1) nguồn mô tả 'người Hàn Quốc', 'người Pháp', 'người Đức gốc Việt', 'Korean banker'… (không có chữ "
         "'quốc tịch') được chấp nhận là quốc tịch (Note: NATIONALITY_FROM_DESCRIPTOR); (2) nơi sinh ở nước ngoài được dùng làm quốc tịch "
         "khi không nguồn nào ghi quốc tịch, đánh dấu riêng Evidence_Type = BIRTHPLACE để lọc / chạy robustness (nơi sinh ≠ quốc tịch "
         "trong một số ca đã xác minh, ví dụ AGG Louis T Nguyen sinh tại Việt Nam, quốc tịch Hoa Kỳ).", False),
        ("Quyết định 02/11/2026 (bổ sung): manager không có nguồn nào ghi quốc tịch/nơi sinh sau khi đã tìm hết → quốc tịch được SUY LUẬN "
         "và tính vào cờ: Evidence_Type = INFERRED, Nationality_Raw = INFERRED, Note = INFERRED_STRONG / INFERRED_MEDIUM / INFERRED_WEAK + căn cứ "
         "(STRONG: đại diện của cổ đông/tập đoàn nước ngoài có nêu tên; MEDIUM: sự nghiệp/công ty mẹ ở nước đó + tên; WEAK: chỉ dựa vào tên). "
         "Lọc Evidence_Type ≠ INFERRED để có bộ chỉ gồm bằng chứng trực tiếp.", False),
        ("Ứng viên LOW (một âm tiết lạ, phần lớn là lỗi OCR) được đọc lướt; tên người nước ngoài thật (thường là tên Hoa/Hàn "
         "trùng dạng âm tiết Việt) được nâng lên HIGH (data/manual/candidate_promotions.csv). LOW còn lại không chặn cờ 0.", False),
        ("", False), ("Tóm tắt (trong phạm vi)", True),
        (f"Công ty trong phạm vi: {len(scope)} | Flag_Status: " + ", ".join(f"{k} {v}" for k, v in fs.most_common()), False),
        (f"Bản ghi Foreign_Managers: {len(fm_rows)} (Is_Foreign = 1: {sum(r['Is_Foreign'] == '1' for r in fm_rows)}; "
         f"UNKNOWN: {sum(r['Is_Foreign'] == '' for r in fm_rows)})", False),
    ]
    for text, bold in lines:
        ws.append([text])
        if bold:
            ws.cell(ws.max_row, 1).font = Font(bold=True, size=12)
    ws.column_dimensions["A"].width = 160

    fm_cols = ["Company", "Ticker", "Year", "Manager_Name", "Raw_Position", "Nationality", "Source", "Page", "Manager_ID",
               "Nationality_Raw", "Is_Foreign", "Dual_Nationality", "Role_Group", "Appointed_Date", "Resigned_Date",
               "Evidence_Type", "Evidence_Quote", "Source_URL", "Local_File", "Other_Sources", "Reviewed_On", "Note",
               "Management_Include"]
    ck1.add_table(wb, "Companies", out, list(out[0].keys()))
    ck1.add_table(wb, "Foreign_Managers", fm_rows, fm_cols, widths={"Evidence_Quote": 90, "Other_Sources": 60, "Source_URL": 50})
    if cands:
        ck1.add_table(wb, "Candidates", sorted(cands, key=lambda c: (c["Priority"] != "HIGH", c["Settled"], c["Ticker_Local"])),
                      list(cands[0].keys()), widths={"Hint_Snippet": 80})
    if decisions:
        ck1.add_table(wb, "Candidate_Decisions", decisions, list(decisions[0].keys()), widths={"Reason": 100})
    # one row per company that still has unconfirmed persons (open HIGH candidates or UNKNOWN records), for review
    open_names = defaultdict(list)
    for x in cands:
        if x["Priority"] == "HIGH" and x["Settled"] != "1":
            open_names[x["Ticker_Local"]].append(f"{x['Name']} (p{(x['Pages_AR'] or x['Pages_GOV'] or x['Hint_Page']).split(';')[0]})")
    for r in fm_rows:
        if r["Is_Foreign"] == "":
            open_names[r["Ticker"]].append(f"{r['Manager_Name']} – {r['Raw_Position']} (UNKNOWN record, p{r['Page']})")
    review = [{"Ticker_Local": o["Ticker_Local"], "Company": o["Company"], "Flag_Status": o["Flag_Status"],
               "Foreign_Manager": o["Foreign_Manager"], "Mcap_Rank": o["Mcap_Rank"], "Deep_C3": o["Deep_Prelim"],
               "N_Open": len(open_names[o["Ticker_Local"]]), "Open_Persons": "; ".join(open_names[o["Ticker_Local"]]),
               "Confirmed_Foreign": o["Foreign_Manager_Summary"]}
              for o in out if open_names.get(o["Ticker_Local"]) and o["Flag_Status"] in ("FOUND", "UNRESOLVED")]
    review.sort(key=lambda r: (r["Flag_Status"] != "UNRESOLVED", int(r["Mcap_Rank"] or 9999)))
    if review:
        ck1.add_table(wb, "Review_Open", review, list(review[0].keys()), widths={"Open_Persons": 120, "Confirmed_Foreign": 80})
    ck1.add_table(wb, "Coverage_Log", cov, list(cov[0].keys()))
    if company_level:
        ck1.add_table(wb, "Company_Level_Evidence", list(company_level.values()), list(next(iter(company_level.values())).keys()),
                      widths={"Evidence_Quote": 90})
    obs = opt(DATA / "ownership_observations.csv")
    obs += [{"Ticker": r["Ticker"], "Ticker_Local": r["Ticker_Local"], "Foreign_Ownership_Pct": r["CafeF_FO_Pct"],
             "FO_As_Of_Date": r["CafeF_Date"], "FO_Method": "CAFEF_DANGSOHUU", "Source": r["Source"],
             "Source_URL": r["Source_URL"], "Note": r["Note"]} for r in opt(DATA / "fo_cafef_20251231.csv")]
    if obs:
        ck1.add_table(wb, "Ownership_Observations", obs, list(dict.fromkeys(k for r in obs for k in r)))
    names = [p for p in opt(R / "people_mentions.csv") if p["Pages_AR"]]
    if names:
        ck1.add_table(wb, "Names_In_AR", names, list(names[0].keys()))
    roster = opt(R / "roster_cafef.csv")
    if roster:
        ck1.add_table(wb, "Roster_CafeF_Now", roster, list(roster[0].keys()))
    # Bloomberg_Raw: verbatim copy of the input sheet (values)
    src = load_workbook(BLOOMBERG_FILE, read_only=True, data_only=True).worksheets[0]
    wr = wb.create_sheet("Bloomberg_Raw")
    for row in src.iter_rows(values_only=True):
        wr.append(list(row))

    OUTPUT.mkdir(exist_ok=True)
    path = OUTPUT / ("Vietnam_2025_Foreign_Managers.xlsx" if run == "full" else f"Vietnam_2025_Foreign_Managers_{run}.xlsx")
    wb.save(path)
    print("saved", path, "|", dict(fs))


if __name__ == "__main__":
    main()

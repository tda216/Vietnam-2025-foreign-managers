"""Step 3g – Checkpoint 2 workbook: pilot of 30 companies (document route, scan share, nationality fields,
foreign managers found, candidates still open, automatic-vs-manual comparison).

Inputs: data/pilot/*.csv (03b–03e), data/manual/manager_records.csv (records read on the PDF page / web source),
        data/manual/pilot_review.csv (per-company manual reading of the AR management pages).
Output: output/Checkpoint2_Pilot_FY2025.xlsx
"""
import sys
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2] / "shared")]  # python -I; country config first
from common import read_csv
from config import DATA, OUTPUT, YEAR

ck1 = import_module("02e_checkpoint1_excel")
P = DATA / "pilot"
MANUAL = DATA / "manual"


def is_english(path: str) -> bool:
    f = path.lower()
    return any(k in f for k in ("_en_", "eng", "english", "annualreport", "annual_report", "anual", "annunal"))


def main():
    sample = read_csv(DATA / "pilot_sample.csv")
    docs = read_csv(P / "docs.csv")
    stats = read_csv(P / "pdf_stats.csv")
    links = read_csv(P / "nationality_links.csv")
    people = read_csv(P / "people_mentions.csv")
    cafef = read_csv(P / "roster_cafef.csv")
    records = read_csv(MANUAL / "manager_records.csv")
    review = {r["Ticker_Local"]: r for r in read_csv(MANUAL / "pilot_review.csv")} if (MANUAL / "pilot_review.csv").exists() else {}

    deep = {c["Ticker_Local"]: c for c in read_csv(DATA / "companies_step2.csv") if c["Security_Class"] == "COMPANY_VN"}
    by_t = lambda rows: defaultdict(list, {k: [r for r in rows if r["Ticker_Local"] == k] for k in {r["Ticker_Local"] for r in rows}})
    st_t, ln_t, pp_t, cf_t, rec_t = by_t(stats), by_t(links), by_t(people), by_t(cafef), by_t(records)

    comp_rows = []
    for s in sample:
        t = s["Ticker_Local"]
        ar = [x for x in st_t[t] if x["Doc_Kind"] == "AR2025" and x["N_Pages"] and int(x["N_Pages"]) >= 5]
        main_ar = max([x for x in ar if not is_english(x["Local_File"])] or ar, key=lambda x: int(x["N_Pages"]), default=None)
        ar_links = [l for l in ln_t[t] if l["Doc_Kind"] == "AR2025"]
        vals = Counter(l["Value_Class"] for l in ar_links)
        foreign_recs = {r["Manager_Name"] for r in rec_t[t] if r["Is_Foreign"] == "1"}
        unknown_recs = {r["Manager_Name"] for r in rec_t[t] if r["Is_Foreign"] == ""}
        rv = review.get(t, {})
        if foreign_recs:
            flag, status = 1, "FOUND"
        elif unknown_recs or rv.get("Open_Candidates"):
            flag, status = "", "UNRESOLVED"
        elif rv.get("Reviewed") == "1":
            flag, status = 0, ("NONE_FOUND_VERIFIED" if rv.get("AR_Nationality_For_All") == "1" else "NONE_FOUND")
        else:
            flag, status = "", "NOT_REVIEWED"
        comp_rows.append({
            "Stratum": s["Stratum"], "Ticker_Local": t, "Company": s["Company"], "Exchange_At_FO_Date": s["Exchange_At_FO_Date"],
            "Mcap_Rank": s["Mcap_Rank"], "Foreign_Ownership_Pct": s["Foreign_Ownership_Pct"],
            "Deep_Prelim": deep.get(t, {}).get("Deep_Prelim", ""), "Deep_Reason_Prelim": deep.get(t, {}).get("Deep_Reason_Prelim", ""),
            "AR2025_Found": int(bool(ar)), "AR_Route": "Vietstock document list" if ar else "",
            "AR_PDF_Files": len(ar), "Main_AR_Pages": main_ar["N_Pages"] if main_ar else "",
            "Main_AR_Text_Layer": ("" if not main_ar else "TEXT" if float(main_ar["Text_Page_Share"] or 0) >= 0.9
                                   else "SCANNED" if float(main_ar["Text_Page_Share"] or 0) < 0.1 else "PARTIAL"),
            "Main_AR_OCR_Pages": main_ar["N_OCR_Pages"] if main_ar else "",
            "Main_AR_File": main_ar["Local_File"] if main_ar else "",
            "AR_Nationality_Labels": len(ar_links), "AR_Labels_VN_Value": vals["VIETNAM"], "AR_Labels_Foreign_Value": vals["FOREIGN"],
            "AR_Has_Nationality_Field_Auto": int(vals["VIETNAM"] + vals["FOREIGN"] > 0),
            "AR_Has_Nationality_Field_Manual": rv.get("AR_Has_Nationality_Field", ""),
            "AR_Nationality_For_All_Manual": rv.get("AR_Nationality_For_All", ""),
            "Names_In_AR": sum(1 for p in pp_t[t] if p["Pages_AR"]),
            "NonVN_Style_Names_AR": sum(1 for p in pp_t[t] if p["Pages_AR"] and p["Name_Screen"] == "NON_VN_STYLE"),
            "CafeF_Roster_Now": len(cf_t[t]), "NonVN_Style_CafeF_Now": sum(1 for r in cf_t[t] if r["Name_Screen"] == "NON_VN_STYLE"),
            "Foreign_Manager": flag, "Flag_Status": status, "N_Foreign_Managers": len(foreign_recs),
            "N_Unknown_Candidates": len(unknown_recs),
            "Foreign_Manager_Summary": "; ".join(sorted({f"{r['Manager_Name']} – {r['Raw_Position']} ({r['Nationality']})"
                                                         for r in rec_t[t] if r["Is_Foreign"] == "1"})),
            "Review_Note": rv.get("Note", ""),
        })

    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    n = len(comp_rows)
    cnt = lambda f: sum(1 for r in comp_rows if f(r))
    lines = [
        ("Checkpoint 2 – Pilot 30 công ty (FY2025)", True), ("", False),
        ("Mẫu: 10 LARGE (vốn hóa 1–100), 10 MID (101–500), 10 SMALL_UPCOM (UPCoM, > 500); seed 20251231 (data/pilot_sample.csv).", False),
        (f"BCTN 2025 tìm thấy: {cnt(lambda r: r['AR2025_Found'])}/{n} – tất cả qua danh sách tài liệu Vietstock (/data/getdocument).", False),
        (f"Lớp text của BCTN chính: TEXT {cnt(lambda r: r['Main_AR_Text_Layer'] == 'TEXT')}, PARTIAL "
         f"{cnt(lambda r: r['Main_AR_Text_Layer'] == 'PARTIAL')}, SCANNED {cnt(lambda r: r['Main_AR_Text_Layer'] == 'SCANNED')} "
         "→ trang không có text được OCR (Tesseract vie+eng, 300 dpi).", False),
        (f"BCTN có trường quốc tịch (đọc tay): đủ cho người được giới thiệu {cnt(lambda r: r['AR_Has_Nationality_Field_Manual'] == '1')}, "
         f"chỉ một phần {cnt(lambda r: r['AR_Has_Nationality_Field_Manual'] == 'PARTIAL')}, không có "
         f"{cnt(lambda r: r['AR_Has_Nationality_Field_Manual'] == '0')} (/{n}). Tự động (nhãn + giá trị quốc gia): "
         f"{cnt(lambda r: r['AR_Has_Nationality_Field_Auto'] == 1)}/{n}.", False),
        (f"Có người nước ngoài (đã xác minh): {cnt(lambda r: r['Foreign_Manager'] == 1)} công ty; "
         f"chưa kết luận: {cnt(lambda r: r['Flag_Status'] == 'UNRESOLVED')}; không có: "
         f"{cnt(lambda r: r['Foreign_Manager'] == 0)}.", False),
        ("Cờ 0 ở pilot = NONE_FOUND: đã đọc BCTN + sàng lọc tên, không còn ứng viên; KHÔNG phải 'đã xác minh quốc tịch từng người' "
         "(người nước ngoài mang tên Việt/Hán-Việt chỉ lộ ra khi nguồn ghi quốc tịch). Tìm sâu (website/tin tức) ở pilot mới chạy "
         "cho các ứng viên, chưa chạy cho các công ty nhóm C3 có cờ 0.", False),
        ("", False), ("Sheet", True),
        ("Pilot_Companies: chỉ số theo công ty; Foreign_Managers: bản ghi (đúng cột spec + bằng chứng); "
         "Nationality_Links: mọi nhãn quốc tịch tìm thấy, gắn với tên gần nhất; Names_NonVN_Style: tên cần ưu tiên tra "
         "(chỉ để sàng lọc, không phải bằng chứng); PDF_Stats; Roster_CafeF_Now (roster hiện tại, không phải 2025); Doc_Index.", False),
        ("Page = số trang PDF (1-based). OCR = 1: trang đọc bằng OCR, đã mở ảnh trang để kiểm tra trước khi ghi bản ghi.", False),
    ]
    for text, bold in lines:
        ws.append([text])
        if bold:
            ws.cell(ws.max_row, 1).font = Font(bold=True, size=12)
    ws.column_dimensions["A"].width = 160

    company = {x["Ticker_Local"]: x["Company"] for x in sample}
    records = [{**r, "Company": company.get(r["Ticker_Local"], ""), "Year": YEAR} for r in records]
    rec_cols = ["Company", "Ticker_Local", "Year", "Manager_Name", "Raw_Position", "Role_Group", "Nationality", "Nationality_Raw", "Is_Foreign",
                "Dual_Nationality", "Appointed_Date", "Resigned_Date", "Source", "Page", "Evidence_Type", "Evidence_Quote",
                "Source_URL", "Local_File", "Other_Sources", "Reviewed_On", "Note"]
    ck1.add_table(wb, "Pilot_Companies", comp_rows, list(comp_rows[0].keys()))
    ck1.add_table(wb, "Foreign_Managers", records, rec_cols, widths={"Evidence_Quote": 90, "Other_Sources": 60, "Source_URL": 50})
    if (MANUAL / "candidate_decisions.csv").exists():
        cd = read_csv(MANUAL / "candidate_decisions.csv")
        ck1.add_table(wb, "Candidate_Decisions", cd, list(cd[0].keys()), widths={"Reason": 100})
    ck1.add_table(wb, "Nationality_Links", sorted(links, key=lambda l: (l["Value_Class"] != "FOREIGN", l["Ticker_Local"])),
                  list(links[0].keys()), widths={"Snippet": 100})
    ck1.add_table(wb, "Names_NonVN_Style", [p for p in people if p["Name_Screen"] == "NON_VN_STYLE"], list(people[0].keys()))
    ck1.add_table(wb, "PDF_Stats", stats, list(stats[0].keys()))
    ck1.add_table(wb, "Roster_CafeF_Now", cafef, list(cafef[0].keys()))
    ck1.add_table(wb, "Doc_Index", read_csv(P / "doc_index.csv"), list(read_csv(P / "doc_index.csv")[0].keys()),
                  widths={"Title": 80, "Url": 60})
    if (MANUAL / "pilot_review.csv").exists():
        rv = read_csv(MANUAL / "pilot_review.csv")
        ck1.add_table(wb, "Manual_Review", rv, list(rv[0].keys()), widths={"Note": 100})
    path = OUTPUT / "Checkpoint2_Pilot_FY2025.xlsx"
    wb.save(path)
    print("saved", path)


if __name__ == "__main__":
    main()

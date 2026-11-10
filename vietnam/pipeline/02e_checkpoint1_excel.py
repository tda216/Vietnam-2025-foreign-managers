"""Step 2e – Checkpoint 1 workbook: preliminary ownership classification at 31/12/2025 for user review.

Output: output/Checkpoint1_Ownership_FY2025.xlsx
"""
import sys
from collections import Counter
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts run with python -I
from common import read_csv
from config import DATA, FO_AS_OF, FO_BORDERLINE_UPPER, FO_THRESHOLD, OUTPUT

HEAD_FILL = PatternFill("solid", fgColor="1F3864")
HEAD_FONT = Font(bold=True, color="FFFFFF")
NUMERIC = {"Foreign_Ownership_Pct", "CafeF_FO_Pct", "Diff_PP", "Market_Cap_LCL", "Mcap_Rank", "FO_Page",
           "In_Scope", "Manager_Search", "Deep_Prelim", "Qty_Issued", "Qty_Foreign_Held", "Max_Foreign_Ratio_Pct", "Page",
           "Bloomberg_Row"}

COMPANY_COLS = ["Ticker", "Ticker_Local", "Company", "Company_Name_VN", "Bloomberg_Short_Name", "Exchange_At_FO_Date",
                "Exchange", "Industry_Group", "ISIN", "Security_Class", "In_Scope", "Exclusion_Reason",
                "Foreign_Ownership_Pct", "FO_Bound", "FO_As_Of_Date", "Ownership_Type", "FO_Method", "FO_Source",
                "FO_Source_URL", "FO_Page", "FO_Note",
                "CafeF_FO_Pct", "Diff_PP", "Manager_Search", "Manager_Search_Reason", "Market_Cap_LCL", "Mcap_Rank",
                "Deep_Prelim", "Deep_Reason_Prelim", "Bloomberg_Row"]


def cell_value(col, v):
    if isinstance(v, str):
        v = ILLEGAL_CHARACTERS_RE.sub("", v)  # control characters Excel cannot store (display copy only; CSVs keep them)
    if col in NUMERIC and v not in ("", None):
        try:
            f = float(v)
            return int(f) if f.is_integer() and col not in ("Foreign_Ownership_Pct", "CafeF_FO_Pct", "Diff_PP") else f
        except ValueError:
            return v
    return v


def add_table(wb, title, rows, cols, widths=None):
    ws = wb.create_sheet(title)
    ws.append(cols)
    for c in ws[1]:
        c.fill, c.font, c.alignment = HEAD_FILL, HEAD_FONT, Alignment(wrap_text=True, vertical="top")
    for r in rows:
        ws.append([cell_value(c, r.get(c, "")) for c in cols])
    ws.freeze_panes = "C2" if len(cols) > 3 else "A2"
    ws.auto_filter.ref = ws.dimensions
    for i, c in enumerate(cols, start=1):
        w = (widths or {}).get(c) or min(max(len(c) + 2, *(len(str(r.get(c, ""))) + 1 for r in rows[:300]), 10), 60) if rows else len(c) + 2
        ws.column_dimensions[get_column_letter(i)].width = w
        if c in ("Foreign_Ownership_Pct", "CafeF_FO_Pct"):
            for cell in ws[get_column_letter(i)][1:]:
                cell.number_format = "0.00"
    return ws


def main():
    comps = read_csv(DATA / "companies_step2.csv")
    cafef_path = DATA / "fo_cafef_20251231.csv"
    cafef = {r["Ticker"]: r for r in read_csv(cafef_path)} if cafef_path.exists() else {}
    for c in comps:
        x = cafef.get(c["Ticker"], {})
        c["CafeF_FO_Pct"], c["Diff_PP"] = x.get("CafeF_FO_Pct", ""), x.get("Diff_PP", "")
    scope = [c for c in comps if c["In_Scope"] == "1"]
    fo = lambda c: float(c["Foreign_Ownership_Pct"]) if c["Foreign_Ownership_Pct"] else None

    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    ot = Counter(c["Ownership_Type"] for c in scope)
    n_cafef = sum(1 for c in scope if c["CafeF_FO_Pct"] != "")
    n_diff = sum(1 for c in scope if c["Diff_PP"] != "" and abs(float(c["Diff_PP"])) > 0.10)
    lines = [
        ("Checkpoint 1 – Phân loại sở hữu nước ngoài (sơ bộ), FY2025", True),
        ("", False),
        (f"Mốc đo: {FO_AS_OF} (file VSDC 'FOL 31.12.2025', HOSE & HNX công bố; HOSE và HNX dùng chung một file, cùng SHA256).", False),
        ("Công thức: Foreign_Ownership_Pct = Số CP NĐTNN đang nắm giữ / Tổng số CP phát hành × 100 (file không có cột %; số gốc ở sheet VSDC_Raw).", False),
        ("Kiểm tra parse: tổng từng khu vực (HOSE/STO, HNX/STX, UPCoM/UPX, DEPOX) khớp đúng dòng 'Tổng' in trong file.", False),
        (f"Quy tắc: FO > {FO_THRESHOLD:g}% → FOREIGN_MAJORITY; FO ≤ {FO_THRESHOLD:g}% (kể cả đúng {FO_THRESHOLD:g}) → LOCAL; không có số liệu → REVIEW.", False),
        (f"Phạm vi tìm manager: LOCAL + REVIEW + FOREIGN_MAJORITY sát ngưỡng ({FO_THRESHOLD:g}–{FO_BORDERLINE_UPPER:g}%).", False),
        ("Nguồn thứ hai (đối chiếu, không ghi đè): CafeF – lịch sử giao dịch khối ngoại, cột 'DangSoHuu' ngày giao dịch cuối ≤ 31/12/2025.", False),
        ("Đây là phân loại SƠ BỘ: bước đọc BCTN 2025 sẽ đối chiếu thêm và gắn FO_Conflict nếu lệch phân loại.", False),
        ("Mã VSDC không phủ (niêm yết nước ngoài, hủy niêm yết) được xác định thủ công từ hồ sơ gốc – sheet Manual_Ownership "
         "(FO_Bound = cận trên/dưới có bằng chứng khi tài liệu không cho đủ để tính con số chính xác).", False),
        ("Quy tắc bổ sung (bạn duyệt 01/11/2026), chỉ cho mã niêm yết ở nước ngoài: cổ đông lớn nhất/kiểm soát có quốc tịch hoặc "
         "nơi đăng ký nước ngoài theo tài liệu, VÀ danh sách cổ đông được công bố không có cổ đông Việt Nam nào → FOREIGN_MAJORITY "
         "(FO_Method = RULE_FOREIGN_LISTED_FOREIGN_CONTROLLER; FO_Bound vẫn giữ phần chứng minh được). Áp dụng: 1341 TT, 900140 KS.", False),
        ("Vốn hóa Bloomberg tính theo đồng tiền nơi niêm yết; Mcap_Rank chỉ xếp hạng các công ty niêm yết tại VN (VND).", False),
        ("", False),
        ("Tóm tắt", True),
        (f"Tổng mã Bloomberg: {len(comps)} | trong phạm vi: {len(scope)}", False),
        (f"LOCAL: {ot['LOCAL']} | FOREIGN_MAJORITY: {ot['FOREIGN_MAJORITY']} | REVIEW: {ot['REVIEW']}", False),
        (f"Sẽ tìm manager: {sum(1 for c in scope if c['Manager_Search'] == '1')} công ty", False),
        (f"Danh sách tìm sâu (C3) sơ bộ – top 200 vốn hóa ∪ FO ≥ 10%, trong các công ty sẽ tìm manager: "
         f"{sum(1 for c in scope if c['Deep_Prelim'] == '1')} công ty "
         "(sẽ bổ sung: cổ đông lớn NN ≥ 5% và công ty đã thấy foreign board/exec sau bước 5)", False),
        (f"Đối chiếu CafeF: có số liệu {n_cafef} mã; lệch > 0,10 điểm %: {n_diff} mã (xem cột Diff_PP); "
         "không mã nào đổi phân loại", False),
        ("", False),
        ("Cần bạn xem", True),
        (f"1. Sheet REVIEW: {ot['REVIEW']} mã chưa đủ bằng chứng để phân loại (chi tiết + bằng chứng ở sheet Manual_Ownership).", False),
        ("   (mã không có ISIN 1871201D nằm ngoài phạm vi nên không tính vào đây)", False),
        (f"2. Sheet FOREIGN_MAJORITY: {ot['FOREIGN_MAJORITY']} công ty; chỉ các mã sát ngưỡng {FO_THRESHOLD:g}–{FO_BORDERLINE_UPPER:g}% "
         "vẫn được tìm manager.", False),
        ("3. Sheet Borderline_45_55: các công ty sát ngưỡng 50%.", False),
        ("4. Ngoài phạm vi (In_Scope = 0): quỹ/ETF, mã không có ISIN, CE1 (hủy niêm yết 04/03/2025, không có BCTN 2025), "
         "NBS (hủy niêm yết 07/2017).", False),
    ]
    for text, bold in lines:
        ws.append([text])
        if bold:
            ws.cell(ws.max_row, 1).font = Font(bold=True, size=12)
    ws.column_dimensions["A"].width = 150

    # Summary by exchange × ownership type
    ws2 = wb.create_sheet("Summary")
    exch = ["HOSE", "HNX", "UPCoM", ""]
    ws2.append(["Ownership_Type"] + [e or "(không có trong VSDC)" for e in exch] + ["Tổng"])
    for t in ("LOCAL", "FOREIGN_MAJORITY", "REVIEW"):
        vals = [sum(1 for c in scope if c["Ownership_Type"] == t and c["Exchange_At_FO_Date"] == e) for e in exch]
        ws2.append([t] + vals + [sum(vals)])
    ws2.append([])
    ws2.append(["Phân bố FO% (công ty có số liệu)", "Số công ty"])
    vals = [fo(c) for c in scope if fo(c) is not None]
    ws2.append(["= 0", sum(1 for x in vals if x == 0)])
    for lo, hi in [(0, 1), (1, 5), (5, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 55), (55, 100)]:
        ws2.append([f"({lo}, {hi}]", sum(1 for x in vals if lo < x <= hi)])
    for row in (ws2[1], ws2[6]):
        for c in row:
            c.fill, c.font = HEAD_FILL, HEAD_FONT
    for col in "ABCDEF":
        ws2.column_dimensions[col].width = 26

    add_table(wb, "Companies", comps, COMPANY_COLS)
    add_table(wb, "REVIEW", [c for c in scope if c["Ownership_Type"] == "REVIEW"], COMPANY_COLS)
    by_fo = lambda c: (fo(c) is None, fo(c) or 0.0)  # bound-only (manual) rows last
    add_table(wb, "FOREIGN_MAJORITY", sorted((c for c in scope if c["Ownership_Type"] == "FOREIGN_MAJORITY"), key=by_fo), COMPANY_COLS)
    add_table(wb, "Borderline_45_55", sorted((c for c in scope if fo(c) is not None and 45 <= fo(c) <= 55), key=fo), COMPANY_COLS)
    add_table(wb, "Deep_Prelim", sorted((c for c in scope if c["Deep_Prelim"] == "1"), key=lambda c: int(c["Mcap_Rank"] or 99999)), COMPANY_COLS)
    if cafef:
        diffs = [c for c in scope if c["Diff_PP"] != "" and abs(float(c["Diff_PP"])) > 0.10]
        add_table(wb, "CafeF_Diff_gt_0.1pp", sorted(diffs, key=lambda c: -abs(float(c["Diff_PP"]))), COMPANY_COLS)
    manual_path = DATA / "manual" / "ownership_manual.csv"
    if manual_path.exists():
        manual = read_csv(manual_path)
        add_table(wb, "Manual_Ownership", manual, list(manual[0].keys()),
                  widths={"FO_Note": 100, "FO_Source_URL": 60, "FO_Source": 50})
    vsdc_cols = ["Exchange_Section", "Exchange", "STT", "Ticker_Local", "ISIN", "Qty_Issued", "Max_Foreign_Ratio_Pct",
                 "Qty_Foreign_Permitted", "Qty_Foreign_Held", "Qty_Room_Remaining", "Foreign_Ownership_Pct", "Page"]
    add_table(wb, "VSDC_Raw", read_csv(DATA / "fo_vsdc_20251231.csv"), vsdc_cols)

    OUTPUT.mkdir(exist_ok=True)
    path = OUTPUT / "Checkpoint1_Ownership_FY2025.xlsx"
    wb.save(path)
    print("saved", path)


if __name__ == "__main__":
    main()

# Báo cáo bàn giao – Công ty niêm yết và nhà quản lý nước ngoài, Thái Lan FY2025

Ngày bàn giao: 09/11/2026 · File dữ liệu: `Thailand_2025_Foreign_Managers.xlsx` (bản build 09/11/2026, kiểm tra tự động không có lỗi, mẫu kiểm tra thủ công không có lỗi)

---

## 1. Kết luận

**Trong 842 công ty niêm yết LOCAL (sở hữu nước ngoài ≤ 50%), có 215 công ty (26%) có ít nhất một người mang quốc tịch nước ngoài giữ chức quản lý trong năm 2025.**

| Nhóm công ty LOCAL | Số công ty | `Foreign_Manager` |
|---|---|---|
| Có người nước ngoài (FOUND) | 215 | 1 |
| Không tìm thấy người nước ngoài (NONE_FOUND) | 625 | 0 |
| Còn người điều hành chưa xác định (BTG, PTTGC) | 2 | để trống |

Những điểm chính:

1. **Tỷ lệ cao hơn Việt Nam nhiều** (26% so với 9%). Lý do chính là cách đo: mẫu báo cáo bắt buộc của SEC Thái Lan ghi "Thai nationality: Yes/No" cho **từng giám đốc**, nên người nước ngoài không thể "ẩn" như ở Việt Nam. 190/215 công ty có cờ dựa trên khai trực tiếp: dòng "Thai nationality: No", hoặc câu ghi quốc tịch trong tài liệu.
2. **Người nước ngoài chủ yếu ngồi ở HĐQT.** Ở 215 công ty có 600 người nước ngoài:
   - 450 người ở HĐQT;
   - 232 người ở ban điều hành;
   - 16 người ở cấp quản lý khác.

   Một người có thể thuộc nhiều nhóm. Giám đốc kiêm người điều hành có một dòng cho mỗi chức danh.
3. **Quốc tịch tập trung ở châu Á.** Đông nhất là Nhật Bản (121 người), tiếp theo là Đài Loan (49), Singapore (40), Ấn Độ (38), Trung Quốc (35) và Malaysia (30). Còn 113 người chưa xác định được tên nước (cập nhật 13/11/2026 sau hai vòng tìm trên web). Xem mục 6.
4. **Công ty lớn có tỷ lệ cao hơn.** Trong 174 công ty LOCAL thuộc top 200 vốn hóa, 74 công ty (43%) có người nước ngoài.
5. **Cờ 0 ở Thái Lan đáng tin hơn ở Việt Nam.** Ở 382/625 công ty cờ 0, mọi giám đốc và người điều hành đều khai "Thai nationality: Yes". Ở 243 công ty còn lại, HĐQT khai đủ; ban điều hành không có trường này nhưng mọi tên đều là tên Thái.

**Cập nhật 09/11/2026 (sau bản bàn giao đầu):**
- 12 công ty LOCAL được bổ sung, vì trước đó tra sai mã SET hoặc thiếu One Report. Ví dụ:
  - S&J, SE-ED, F&D, M-CHAI, Q-CON và L&E bị Bloomberg viết khác mã;
  - LRH, SVI, GLAND và BPP đã hủy niêm yết hoặc bị đình chỉ;
  - TNH và CITY có năm tài chính kết thúc tháng 7.
- 3 công ty Thái niêm yết ở nước ngoài và do người Thái kiểm soát (THBEV, IFBH, Mermaid) đã được tìm người quản lý từ báo cáo trên SGX/HKEX.

---

## 2. Nội dung bàn giao

### 2.1. File chính: `Thailand_2025_Foreign_Managers.xlsx`

| Sheet | Mỗi dòng là | Mức độ cần dùng |
|---|---|---|
| **Companies** | 1 mã trong danh sách Bloomberg (955 dòng) | **Chính**: phân loại sở hữu và cờ người nước ngoài |
| **Foreign_Managers** | 1 người × 1 chức danh (905 dòng, 702 dòng thuộc công ty LOCAL) | **Chính**: danh sách người nước ngoài, kèm nguồn, trang và căn cứ tên nước. Vài dòng có `Is_Foreign` trống: có tên trong tài liệu nhưng không xác định được nước, nên không tính vào cờ |
| Management_Roster | 1 người trong danh sách HĐQT và ban điều hành của One Report (14.082 dòng) | Mẫu số nếu cần tính tỷ lệ người nước ngoài trên tổng số manager |
| README | – | Định nghĩa và các quy tắc đã chốt |
| Source_Conflicts | 10 dòng | One Report và BoardEx ghi khác nhau. Tất cả đã được quyết định, giữ theo One Report |
| Review_Open | 1 tên đã sàng lọc | Vết kiểm toán: lý do giữ hoặc loại từng tên. Còn 3 tên để mở (AWC, BTG, PTTGC) |
| Ownership_Observations | 1 giá trị × 1 nguồn | Mọi số sở hữu nước ngoài thu thập được |
| Coverage_Log | 1 mã | File báo cáo đã đọc, số giám đốc đếm được, kết quả đối chiếu với bảng 7.2.1 |
| Bloomberg_Raw | 1 mã | Bản sao nguyên trạng file Bloomberg đầu vào |

### 2.2. Tài liệu kèm theo

- `BAO_CAO_BAN_GIAO.md`: tài liệu này.
- `methodology.md`: phương pháp chi tiết, chỉ nêu những điểm khác Việt Nam.
- Repo chứa code (`thailand/pipeline/`, phần dùng chung với các nước khác ở `shared/`) và mọi quyết định duyệt tay (`thailand/data/manual/`). Có hai thứ không nằm trong repo:
  - Bản PDF gốc của One Report (khoảng 36 GB).
  - File Excel kết quả. File này chứa dữ liệu Bloomberg và BoardEx có bản quyền, còn repo là công khai.

---

## 3. Hướng dẫn sử dụng

### 3.1. Chọn mẫu phân tích

Trong sheet **Companies**, lọc `In_Scope = 1` và `Ownership_Type = LOCAL`. Kết quả còn 842 công ty.

- 79 quỹ, REIT, ETF và quỹ hạ tầng có `In_Scope = 0`.
- 30 công ty là FOREIGN_MAJORITY. Cờ của các công ty này vẫn được tính, nhưng ban điều hành chỉ được kiểm tra trong One Report và BoardEx. Trong đó có 4 mã niêm yết ở nước ngoài mà không có cổ đông Thái kiểm soát (Fabrinet, Flagship Minerals, Platt Nera, Green River), theo quy tắc chốt ngày 09/11/2026.
- 4 mã là REVIEW (không có số sở hữu nước ngoài):
  - AKS: đã hủy niêm yết, cổ đông lớn nhất là một tài khoản nominee;
  - ZUUS, BKMP, VPSN: mã OTC ở Mỹ không đọc được hồ sơ (SEC EDGAR chặn User-Agent của dự án; VPSN bị SEC Mỹ đình chỉ từ 2007).
    Ngày 13/11/2026 đã tìm bản sao hồ sơ trên trang khác nhưng không mở được trang nào. Riêng ZUUS có đầu mối (chưa phải bằng chứng): một người nắm khoảng 76%. Nhóm có thể gỡ được nếu cung cấp file 10-K, hoặc một email chung của dự án (không phải email cá nhân) để khai báo với SEC.
- Cột `Source_Basis` cho biết cờ dựa trên báo cáo nào:
  - `ONE_REPORT_2025` (833 công ty LOCAL);
  - `ONE_REPORT_FY2025_JUL`: TNH, CITY;
  - `ONE_REPORT_2024_FALLBACK`: QDC, MVP, TAPAC, MILL. Chưa có bản 2025, nên có thể thiếu người nhận chức trong năm 2025;
  - `FOREIGN_LISTING_ANNUAL_REPORT`: THBEV, 6603, MMT.

### 3.2. Biến cờ

| Cột | Ý nghĩa |
|---|---|
| **`Foreign_Manager_Core`** (khuyên dùng) | 1 nếu có người nước ngoài ở HĐQT hoặc ban điều hành. Nhóm LOCAL có 211 công ty bằng 1. So sánh được giữa các công ty |
| `Foreign_Manager` | Tính thêm quản lý cấp dưới ban điều hành (215 công ty). Nhóm cấp dưới chỉ có dữ liệu ở công ty BoardEx phủ, nên chỉ dùng làm biến bổ sung |
| `Flag_Basis`, `Source_Basis`, `Source_Note` | Cờ dựa trên One Report, BoardEx hay tài liệu khác; báo cáo năm nào; ghi chú nguồn của từng công ty |
| `Flag_Status`, `Verification_Level` | FOUND / NONE_FOUND (kèm ALL_STATED hoặc BOARD_STATED) / để trống |
| `N_Foreign_Board`, `N_Foreign_Executive`, `N_Foreign_Other`, `Foreign_Manager_Summary` | Số người theo nhóm chức danh, và danh sách người dạng một dòng chữ |

**Ô để trống là thiếu dữ liệu, không phải 0.**

### 3.3. Kiểm tra độ vững theo mức bằng chứng

Ở Thái Lan có hai câu hỏi riêng, mỗi câu có cột căn cứ riêng:

**(a) Người đó có phải người nước ngoài không?** Xem cột `Evidence_Type`:

| Mức | `Evidence_Type` | Nghĩa | Số công ty LOCAL có cờ = 1 (cộng dồn) |
|---|---|---|---|
| A. Khai trực tiếp | `ONE_REPORT_FIELD`, `DOC_FIELD` | Dòng "Thai nationality: No", hoặc câu ghi quốc tịch trong tài liệu | 190 (Core: 190) |
| B. A + BoardEx | `BOARDEX` | Quản lý cấp dưới mà BoardEx ghi quốc tịch nước ngoài | 197 (Core: 192) |
| C. B + suy luận | `INFERRED` | Người không có trường quốc tịch (danh sách ban điều hành, hoặc công ty niêm yết ở nước ngoài) mà hồ sơ chỉ ra một nước; căn cứ ở `Note` | 215 (Core: 211) |

Ở các định nghĩa chặt hơn, công ty chỉ đạt mức yếu hơn ngưỡng được để trống, không gán 0. Số công ty có cờ 0 luôn là 625.

**(b) Nước nào?** Xem cột `Country_Evidence_Type`. Đây là căn cứ của **tên nước**, không ảnh hưởng tới cờ:

| Giá trị | Nghĩa | Số người (LOCAL) |
|---|---|---|
| `DOC_FIELD` | Tài liệu ghi "Nationality: X", "สัญชาติ X" hoặc "Singaporean"…: One Report, thư mời ĐHĐCĐ, báo cáo của công ty khác có cùng người, sổ đăng ký công ty Anh (Companies House) | 65 |
| `BOARDEX` | BoardEx ghi quốc tịch | 79 |
| `INFERRED_STRONG` | Tiểu sử ghi người đó làm việc cho cổ đông hoặc công ty mẹ nước ngoài có tên (ví dụ Meiji Yasuda, JERA, Banyan Tree) | 23 |
| `INFERRED_MEDIUM` | Tiểu sử nêu nơi học hoặc nơi làm việc ở nước đó, và tên phù hợp; hoặc nguồn chỉ nói "đến từ" nước đó (D Lucinda Chen, SMO Johson Lim – quyết định 13/11/2026) | 104 |
| `INFERRED_WEAK` | Chỉ dựa vào tên, như tên Nhật, Hàn, Ấn, tên Đài Loan viết theo Wade-Giles | 208 |
| `WEBSITE` / `NEWS` / `CV` | Trang web công ty, báo chí, CV ghi rõ quốc tịch hoặc mô tả "người X" | 2 / 3 / 1 |
| `BIRTHPLACE` | Chỉ có nơi sinh ở nước ngoài | 2 |
| trống (`Nationality = UNKNOWN`) | Không suy luận được tên nước. Người đó vẫn là người nước ngoài | 113 |

Nếu nghiên cứu cần phân tích theo nước, nên kiểm tra độ vững khi bỏ nhóm `INFERRED_WEAK`.

### 3.4. Sheet Foreign_Managers

- Nối với Companies bằng `Foreign_Managers.Ticker` = `Companies.Ticker_Local`.
  - Lưu ý: Fabrinet (niêm yết ở Mỹ) có mã `FN_US`, để không trùng với FN Factory Outlet (`FN`).
- Các cột theo yêu cầu: Company · Ticker · Year · Manager_Name · Raw_Position · Nationality · Source · Page.
- Các cột riêng của Thái Lan:
  - `Thai_Nationality_Stated`: Yes/No như khai trong báo cáo.
  - `Residing_In_Thailand`.
  - `Country_Evidence_Type`, `Country_Quote`, `Country_Source`.
  - `BoardEx_Director_ID`, `BoardEx_Nationality`.
- `Management_Include` được để trống để nhóm nghiên cứu tự quyết định.
- 19 dòng có `Note` bắt đầu bằng `COMMITTEE_ONLY` (quyết định 13/11/2026). Đây là người chỉ có tên trong Ủy ban điều hành (tiểu ban của HĐQT), có dòng "Thai nationality: No", nhưng không nằm trong danh sách HĐQT hay ban điều hành. Họ được ghi với `Is_Foreign` để trống, nên **không** tính vào cờ. Nếu nhóm coi họ là quản lý thì bật `Management_Include`: khi đó `Foreign_Manager` của AF, OGC, PRM, SSF đổi từ 0 sang 1, còn `Foreign_Manager_Core` không đổi. Riêng AF: người này mang tên Thái, có thể báo cáo điền sai.
- Một người giữ hai chức danh thì có hai dòng, cùng `Manager_ID`.

### 3.5. Tra lại nguồn của một dòng

- `Evidence_Quote` chép nguyên văn dòng khai, ví dụ "… – Director – Thai nationality: No; Residing in Thailand: No".
- `Page` là số trang của file PDF, đếm từ 1. File nằm ở `Local_File`, tải lại được từ `Source_URL` (SEC).
- Căn cứ tên nước nằm ở `Country_Quote` và `Note`.

### 3.6. Code mẫu (Python, pandas)

```python
import pandas as pd

f = "Thailand_2025_Foreign_Managers.xlsx"
co = pd.read_excel(f, sheet_name="Companies")
fm = pd.read_excel(f, sheet_name="Foreign_Managers")

# Mẫu phân tích: công ty trong phạm vi, sở hữu nước ngoài ≤ 50%
df = co[(co["In_Scope"] == 1) & (co["Ownership_Type"] == "LOCAL")].copy()

# Mức bằng chứng "là người nước ngoài" (0 = khai trực tiếp, 1 = BoardEx, 2 = suy luận)
LEVEL = {"ONE_REPORT_FIELD": 0, "DOC_FIELD": 0, "BOARDEX": 1, "INFERRED": 2}
fm = fm[pd.to_numeric(fm["Is_Foreign"], errors="coerce") == 1].copy()
fm["Level"] = fm["Evidence_Type"].map(LEVEL)
core = fm[fm["Role_Group"].isin(["Board", "Executive"])]
df["Best_Level_Core"] = df["Ticker_Local"].map(core.groupby("Ticker")["Level"].min())

# Cờ Core chỉ dựa trên dòng khai trực tiếp; công ty chỉ có suy luận → để trống
df["FM_core_stated"] = df["Foreign_Manager_Core"].where(
    ~((df["Foreign_Manager_Core"] == 1) & (df["Best_Level_Core"] > 0)))
```

---

## 4. Phương pháp tóm tắt

1. **Danh sách và phạm vi**: lấy từ Bloomberg (955 mã); quỹ, REIT và ETF nằm ngoài phạm vi.
2. **Sở hữu nước ngoài**, xem chi tiết ở `methodology.md` mục 2:
   - Nguồn chính là mục "Foreign Shareholders" trên trang factsheet của SET. Đây là số tại 11/2026, không phải 31/12/2025, vì chưa có số có bản quyền.
   - 87 công ty có dấu hiệu bất thường được đọc tay danh sách cổ đông lớn trong One Report. Kết quả:
     - BAY và CIMBT chuyển sang FOREIGN_MAJORITY, vì cổ đông nước ngoài được miễn hạn mức.
     - SPG chuyển sang LOCAL.
   - Công ty đã hủy niêm yết và mã niêm yết ở nước ngoài: đọc cổ đông lớn trong One Report, báo cáo trên sàn nước ngoài hoặc thông báo SGX (`data/manual/ownership_manual.csv`, 15 công ty).
3. **Người nước ngoài**:
   - Tải One Report 2025 của 864 công ty từ SEC và tách tự động danh sách HĐQT, người rời chức trong năm và ban điều hành. Factsheet không có link (công ty hủy niêm yết, bản mới chưa tải được) thì lấy từ danh sách hồ sơ 56-1 của SEC.
   - Công ty Thái niêm yết ở nước ngoài (THBEV, IFBH, Mermaid): đọc báo cáo thường niên trên SGX/HKEX.
   - Kiểm tra đủ người bằng bảng tổng số giám đốc 7.2.1 và số thứ tự liên tục.
   - Ghép với BoardEx để lấy tên nước và quản lý cấp dưới.
4. **Tên nước**: lấy theo thứ tự BoardEx → câu ghi quốc tịch trong tiểu sử (kể cả báo cáo của công ty khác có cùng người) → suy luận ba mức. Không suy luận được thì giữ UNKNOWN.
5. **Duyệt tay**: mọi quyết định nằm ở `thailand/data/manual/`, theo từng đợt có lưu vết ở `batches/*.json`.

## 5. Kiểm tra chất lượng

- **Kiểm tra tự động** (`qa_checks.py`): 0 vi phạm. Kiểm tra số dòng, quy tắc phân loại, nguồn, trang, trích dẫn, quốc tịch thuộc danh sách chuẩn, trùng lặp, và mâu thuẫn chưa quyết định.
- **Mẫu thủ công lần 1**: 81 dòng Foreign_Managers (10%) và 30 công ty cờ 0, **0 lỗi**.
  - Mỗi dòng đã được đọc trong khối thông tin của chính người đó; 2 trang được xem trên ảnh.
  - Ở 30 công ty cờ 0, tìm toàn văn mọi file báo cáo không thấy câu "Thai nationality: No" nào bị bỏ sót.
- **Kiểm tra độc lập lần 2** (09/11/2026), cho mọi dòng thêm sau bản bàn giao đầu: 31 dòng người nước ngoài, 11 dòng tên nước và 10 công ty mới có cờ 0.
  - Phát hiện 4 lỗi ở dòng người, 2 lỗi ở dòng tên nước và 2 chỗ sót người. Tất cả đã sửa, có lưu vết ở `batches/2026-11-09_06_qa_corrections.json` và `qa_manual.csv`.
  - Chỗ sót đáng kể nhất: HĐQT cũ của F&D từ chức tháng 5/2025 nhưng không có trong mẫu 2025. Đã đọc One Report 2024 và ghi 2 người.
  - 10 công ty cờ 0 không sót ai.
- **Lỗi phát hiện trong lúc làm và đã sửa**:
  - Ủy ban kiểm toán bị đọc thành HĐQT (FMT).
  - Hai anh chị em bị ghép vào cùng một hồ sơ BoardEx (SIS).
  - Fabrinet trùng mã với FN Factory Outlet.
  - Từ khóa công ty mẹ khớp nhầm với công ty con ở Thái Lan cùng tên.
  - Bloomberg bỏ ký tự "&"/"-" khỏi mã SET, làm 7 công ty bị tra sai factsheet.
  - Giám đốc kiêm người điều hành chỉ có dòng HĐQT. Bước 07 nay ghi thêm 67 dòng Executive; cờ công ty không đổi.

## 6. Giới hạn cần lưu ý khi phân tích

- **Ngày của số sở hữu nước ngoài**: số lấy từ factsheet tháng 11/2026, lệch 310 ngày so với 31/12/2025. Hạn mức nước ngoài thường là 49%, nên phân loại hiếm khi đổi. 14 công ty nhạy với NVDR (FO ≤ 50% < FO + NVDR), trong đó có KBANK và F&D: xem cột `NVDR_Sensitive`.
  - Không có nguồn công khai cho đúng ngày 31/12/2025. Bản lưu trữ web của factsheet chỉ chứa trang chặn bot.
- **Người có hai quốc tịch** khai "Thai nationality: Yes" được tính là người Thái. Ví dụ NRF Dan Pathomvanich: sổ đăng ký công ty Anh ghi "American", nhưng được giữ là người Thái theo One Report (quyết định 13/11/2026; xem sheet `Source_Conflicts`).
- **Tên nước**: 113 người nước ngoài (19%) chưa có tên nước, và 208 người chỉ có suy luận theo tên. Mọi người UNKNOWN đã được tìm trên web hai vòng (10–11/11/2026); những người còn lại không có nguồn nào ghi quốc tịch.
- **Quản lý cấp dưới** chỉ có ở công ty BoardEx phủ (331/842 công ty LOCAL). Vì vậy nên dùng `Foreign_Manager_Core`.
- **Báo cáo không phải bản 2025**:
  - QDC, MVP, TAPAC, MILL dùng One Report 2024 vì chưa có bản 2025 trên SEC. Đã thử lại ngày 13/11/2026: file 2025 của QDC và MVP vẫn báo "không tìm thấy" (SEC còn yêu cầu MVP nộp lại báo cáo tài chính 2025); TAPAC và MILL chưa nộp. Có thể chạy lại khi SEC đăng.
  - TNH và CITY dùng năm tài chính kết thúc 31/07/2025.
- **Quy tắc cho mã niêm yết ở nước ngoài không có cổ đông kiểm soát** (quyết định 09/11/2026): phần cổ đông không xác định được coi là nước ngoài. Quy tắc này áp cho FN_US, FLG và 1949. Flagship Minerals thực tế đăng ký ở Singapore và điều hành từ Chile; Bloomberg ghi trụ sở ở Thái Lan.
- **Quyền dữ liệu**:
  - Điều khoản SET chỉ cho phép dùng cá nhân, phi thương mại. Nếu bàn giao cho mục đích thương mại, cần xin phép SET hoặc thay bằng số có bản quyền.
  - Các cột lấy từ BoardEx và Bloomberg cần đối chiếu với điều khoản WRDS/BoardEx của nhóm.

## 7. Cập nhật và tái tạo dữ liệu

```bash
# chạy từ thư mục gốc của repo; luôn dùng python -I (đọc file tải về không tin cậy)
.venv/bin/python -I thailand/pipeline/01_universe.py
.venv/bin/python -I thailand/pipeline/02_boardex.py
.venv/bin/python -I thailand/pipeline/03_factsheet.py          # dùng cache; chỉ tải trang mới
.venv/bin/python -I thailand/pipeline/04_collect_reports.py all
.venv/bin/python -I thailand/pipeline/05_parse_template.py     # KHÔNG truyền "full": tham số là danh sách mã
.venv/bin/python -I thailand/pipeline/06_ownership.py
.venv/bin/python -I thailand/pipeline/07_people.py
.venv/bin/python -I thailand/pipeline/10_nationality_index.py 10   # cache text + chỉ mục quốc tịch
.venv/bin/python -I thailand/pipeline/11_country_context.py
.venv/bin/python -I thailand/pipeline/08_build_excel.py && .venv/bin/python -I thailand/pipeline/qa_checks.py
```

- Thêm quyết định duyệt tay bằng `thailand/pipeline/tools_add_country.py <batch.json>`.
- Khi SEC đăng One Report 2025 của QDC, MVP, TAPAC hoặc MILL: chạy `04_collect_reports.py MÃ:f56/<file>.zip`, sửa `Doc_Kind` trong `docs.csv`, xóa dòng tương ứng trong `data/manual/company_source_notes.csv`, rồi chạy lại từ bước 05 cho các mã đó.
- Mã SET khác mã Bloomberg: thêm vào `data/manual/set_symbol_manual.csv`, rồi chạy `03_factsheet.py update MÃ`.
- Khi có số FO có bản quyền tại 31/12/2025: đặt vào `thailand/data/manual/fo_licensed.csv`, rồi chạy lại từ bước 06.

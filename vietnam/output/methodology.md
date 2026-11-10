# Phương pháp – Listed Companies & Foreign Managers, Vietnam FY2025

Bản mô tả phương pháp chi tiết, đi kèm `Vietnam_2025_Foreign_Managers.xlsx`. Kết luận, số liệu và hướng dẫn sử dụng nằm ở `BAO_CAO_BAN_GIAO.md`.

## 1. Phạm vi
- Danh sách gốc: `Bloomberg-Vietnam2025_8520.xlsx` (1.599 mã, xuất ngày 27/10/2026), giữ nguyên trong sheet `Bloomberg_Raw`.
- Ngoài phạm vi: 21 ETF / quỹ đóng và mã không có dữ liệu (1871201D). Các mã này vẫn có dòng trong `Companies` với `In_Scope = 0`.
- Công ty có trụ sở tại Việt Nam nhưng niêm yết ở nước ngoài: FO được xác định thủ công từ hồ sơ công bố (`data/manual/ownership_manual.csv`).
- Năm: FY2025. Một manager được tính nếu giữ chức tại chính công ty niêm yết vào bất kỳ thời điểm nào trong năm 2025. Chức danh ở công ty con không tính.

## 2. Sở hữu nước ngoài
- FO đo tại 31/12/2025, theo file VSDC "FOL 31.12.2025" (HOSE/HNX/UPCoM).
- Quy tắc chung cho cả 5 nước:
  - FO > 50% → `FOREIGN_MAJORITY`.
  - FO ≤ 50% → `LOCAL`.
  - Thiếu FO → `REVIEW`.
- Quy tắc bổ sung (01/11/2026): công ty niêm yết ở nước ngoài có cổ đông kiểm soát là người/tổ chức nước ngoài và danh sách cổ đông công bố không có cổ đông Việt Nam → `FOREIGN_MAJORITY` (`FO_Method = RULE_FOREIGN_LISTED_FOREIGN_CONTROLLER`).
- Chỉ tìm manager ở công ty `LOCAL` (cùng nhóm sát ngưỡng ≤ 55%, để đề phòng phải phân loại lại).

## 3. Nguồn và cách đọc
| Bước | Nguồn | Cách dùng |
|---|---|---|
| 3b | Vietstock – mục "Tải tài liệu" (BCTN, báo cáo quản trị, tài liệu ĐHĐCĐ, nghị quyết/thông báo HĐQT) | Lập chỉ mục mọi tài liệu năm 2025–2026; tải BCTN 2025 |
| 3c | BCTN 2025 bản tiếng Việt (bản chính) | Lấy text theo trang. Trang scan được OCR bằng Tesseract (vie), theo thứ tự trang, dừng ở trang mở đầu báo cáo tài chính kiểm toán (giới hạn 60 trang) |
| 5b | Tài liệu ĐHĐCĐ 2025/2026, thông báo nhân sự | Chỉ dùng cho công ty còn ứng viên chưa rõ quốc tịch (CV ứng viên, bản cung cấp thông tin người nội bộ) |
| 6a | Nguồn dự phòng cho công ty không có BCTN 2025 đọc được | BCTN dạng RAR được giải nén; BCTN trên website công ty; báo cáo tình hình quản trị năm 2025 (GOV2025); tài liệu ĐHĐCĐ 2026. BCTN 2024 được giữ riêng, không dùng làm cơ sở cho FY2025 |
| 5d | Tài liệu ĐHĐCĐ và thông báo HĐQT cũ hơn (2018–2024) | Tìm CV / bản cung cấp thông tin của những người giữ chức từ trước 2025 mà BCTN 2025 không ghi quốc tịch |
| – | Website công ty, báo chí, bản cung cấp thông tin người nội bộ đăng trên các trang tin chứng khoán | Chỉ chấp nhận khi ghi quốc tịch (hoặc mô tả "người X") của đúng người đó; trích nguyên văn vào `Evidence_Quote` / `Other_Sources` |

Mỗi tài liệu tải về được lưu kèm URL, thời điểm tải và SHA256 (`*.meta.json`). Số trang là số trang PDF, tính từ 1.

## 4. Xác định người nước ngoài
1. **Sàng lọc** (chỉ để ưu tiên đọc, không phải bằng chứng):
   - Nhãn "Quốc tịch/Nationality" có giá trị không phải Việt Nam.
   - Cụm "người nước ngoài".
   - Tên có ≥ 2 âm tiết không thuộc tiếng Việt.
   - Tên được nâng hạng thủ công (`candidate_promotions.csv`).
2. **Ghi nhận**: một người chỉ được ghi `Is_Foreign = 1` khi nguồn ghi rõ quốc tịch của chính người đó. Mỗi bản ghi có trích dẫn (`Evidence_Quote`), nguồn, URL và trang.
   - Trang OCR và trang bố cục hai cột được mở ảnh trang để đối chiếu.
   - Quốc tịch kép: `Is_Foreign = 1`, `Dual_Nationality = 1`.
   - "Người nước ngoài" không ghi nước: `Nationality = UNKNOWN`.
   - Quốc tịch lấy từ tài liệu của tổ chức khác về cùng một người: ghi chú `NATIONALITY_FROM_OTHER_ISSUER`.
3. **Khi không có nguồn ghi quốc tịch**: các quy tắc dưới đây do nhóm nghiên cứu quyết định ngày 02/11/2026. Mọi trường hợp đều được gắn nhãn riêng để lọc.
   - Mô tả "người Hàn Quốc", "người Pháp", "Korean banker"… được chấp nhận là quốc tịch, ghi chú `NATIONALITY_FROM_DESCRIPTOR`. Các dòng này vẫn tính là bằng chứng trực tiếp.
   - Nơi sinh hoặc nguyên quán ở nước ngoài được dùng làm quốc tịch, với `Evidence_Type = BIRTHPLACE`.
   - Nếu đã tìm hết nguồn mà không có cả quốc tịch lẫn nơi sinh, quốc tịch được **suy luận** và tính vào cờ: `Evidence_Type = INFERRED`, `Nationality_Raw = INFERRED`. Cột `Note` ghi mức độ và căn cứ:
     - `INFERRED_STRONG`: đại diện của cổ đông hoặc tập đoàn nước ngoài có nêu tên.
     - `INFERRED_MEDIUM`: sự nghiệp, học vấn hoặc công ty mẹ ở nước đó, kết hợp với tên.
     - `INFERRED_WEAK`: chỉ dựa vào tên.
   - Ảnh chân dung không bao giờ được dùng làm căn cứ. Người không suy ra được nước nào được giữ là `UNKNOWN` (Is_Foreign để trống).
4. **Loại trừ**: mỗi ứng viên bị loại đều có lý do và trang trong `candidate_decisions.csv` (lỗi OCR, không phải manager, ngoài FY2025, chỉ ở công ty con, nguồn ghi Việt Nam…).

## 5. Cờ công ty
| Flag_Status | Foreign_Manager | Ý nghĩa |
|---|---|---|
| FOUND | 1 | Có ≥ 1 bản ghi `Is_Foreign = 1` (mọi cấp), hoặc nguồn nói HĐQT có thành viên quốc tịch nước ngoài mà không nêu tên (`Flag_Basis = COMPANY_LEVEL_STATEMENT`, sheet `Company_Level_Evidence`; người vẫn là UNKNOWN). `Foreign_Manager_Core` chỉ tính HĐQT/BKS/Ban điều hành |
| NONE_FOUND | 0 | Đã đọc nguồn cơ sở và không còn ứng viên mở. Nguồn cơ sở theo thứ tự ưu tiên: BCTN 2025 → báo cáo quản trị 2025 → BCTN 2024 (`Coverage_Log.Source_Basis`; BCTN 2024 phản ánh nhân sự tại thời điểm công bố, đầu năm 2025, có ghi chú) |
| UNRESOLVED | trống | Còn ứng viên HIGH hoặc bản ghi UNKNOWN |
| NO_SOURCE | trống | Không có BCTN 2025, báo cáo quản trị 2025 hay BCTN 2024 đọc được |
| NOT_SEARCHED / OUT_OF_SCOPE | trống | Chưa xử lý / ngoài phạm vi hoặc FOREIGN_MAJORITY |

Quyết định ngày 01/11/2026:
- Câu ở cấp công ty ("1 thành viên quốc tịch nước ngoài") đủ để đặt cờ = 1.
- BCTN 2024 được dùng làm cơ sở cuối cùng, có ghi chú.
- Người chỉ thuộc tiểu ban của HĐQT được ghi UNKNOWN, `Role_Group = Other_Manager`, để lọc bằng cột `Management_Include`.

Giá trị thiếu không bao giờ bị chuyển thành 0. Cờ 0 không có nghĩa là quốc tịch của từng thành viên đã được xác minh: người nước ngoài mang tên Việt hoặc Hán-Việt chỉ lộ ra khi nguồn ghi quốc tịch.

## 6. Kiểm tra chất lượng
`pipeline/qa_checks.py` kiểm tra tự động (lần build cuối không có vi phạm):
- `Bloomberg_Raw` khớp từng ô với file gốc; mỗi mã Bloomberg có đúng một dòng.
- `Ownership_Type` khớp FO% theo quy tắc.
- Cờ khớp với trạng thái và với bản ghi; không có cờ 0 khi còn ứng viên mở.
- Mỗi bản ghi có nguồn, có trang + file (hoặc URL), có loại bằng chứng, có trích dẫn quốc tịch; quốc tịch thuộc danh sách chuẩn.
- Không có bản ghi trùng; trang không vượt quá số trang của PDF; tên người có trên trang được ghi (hoặc trang liền trước).
- Mọi trang BCTN có nhãn quốc tịch không phải Việt Nam đều đã được đối chiếu với một bản ghi, một quyết định, hoặc một dòng trong `data/manual/label_page_checks.csv`.

Kiểm tra thủ công: `qa_checks.py` đã tạo mẫu ngẫu nhiên (seed 20261101) gồm các dòng Foreign_Managers và 30 công ty có cờ 0 (`data/full/qa_sample_records.csv`, `data/full/qa_sample_companies.csv`). Tại thời điểm bàn giao (02/11/2026), mẫu này **chưa** được mở trang nguồn để rà soát.

## 7. Giới hạn
- Nguồn không ghi quốc tịch → suy luận (INFERRED) hoặc UNKNOWN. Nhiều BCTN chỉ ghi quốc tịch cho một phần thành viên. Có 45 công ty LOCAL mà cờ = 1 chỉ dựa trên suy luận (xem `BAO_CAO_BAN_GIAO.md`, mục 3.3).
- Nơi sinh ≠ quốc tịch trong một số ca đã xác minh (ví dụ người sinh tại Việt Nam, quốc tịch Hoa Kỳ).
- OCR (Tesseract, mô hình `vie`, 200 dpi) có thể đọc sai tên. Mọi bản ghi lấy từ trang OCR đều được đối chiếu ảnh trang.
- Danh sách Bloomberg là ảnh chụp tháng 10/2026. Các mã đã hủy niêm yết trước thời điểm đó không có trong danh sách.
- FO theo VSDC không phản ánh quyền kiểm soát gián tiếp qua pháp nhân trong nước.
- Chức danh cấp dưới Ban điều hành (Giám đốc khối…) chỉ có khi tài liệu tự liệt kê, nên `Foreign_Manager_Core` là biến so sánh được giữa các công ty.

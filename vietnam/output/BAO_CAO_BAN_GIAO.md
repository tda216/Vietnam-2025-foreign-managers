# Báo cáo bàn giao – Công ty niêm yết và nhà quản lý nước ngoài, Việt Nam FY2025

Ngày cập nhật: 04/11/2026 · File dữ liệu đối chiếu: `1_Vietnam_2025_Foreign_Managers.xlsx` (bản Excel hiện hành)

---

## 1. Kết luận

**Trong 1.553 công ty niêm yết LOCAL (sở hữu nước ngoài ≤ 50% tại 31/12/2025), có 146 công ty (9,4%) có `Foreign_Manager = 1` trong năm 2025.** Cờ này tính tất cả các nhóm chức danh đã định nghĩa trong workbook, gồm HĐQT, Ban kiểm soát, Ban điều hành và cấp quản lý khác; vì vậy cần xem riêng số liệu về chức danh điều hành bên dưới.

| Chỉ số trong nhóm LOCAL | Số công ty | Cách hiểu |
|---|---:|---|
| Có người nước ngoài theo biến `Foreign_Manager` | 146 | `Foreign_Manager = 1` |
| Có ở HĐQT, BKS hoặc Ban điều hành theo biến `Foreign_Manager_Core` | 145 | `Foreign_Manager_Core = 1` |
| Có chức danh điều hành/cấp quản lý có thể tác động hoạt động | 36 | Có `Executive` hoặc `Other_Manager`: 34 công ty có `Executive` + 4 có `Other_Manager` − 2 công ty trùng (NVB, TYA) = 36 công ty duy nhất |
| Trong 36 công ty trên, đồng thời có người nước ngoài ở HĐQT | 22 | Có thể là cùng người hoặc người khác trong cùng công ty |
| Trong 36 công ty trên, đồng thời có Chủ tịch HĐQT nước ngoài | 12 | Ở cấp công ty; không khẳng định người giữ chức điều hành cũng là Chủ tịch |
| `Foreign_Manager = 0` | 1.356 | Không tìm thấy theo tiêu chí và nguồn đã rà |
| `Foreign_Manager` để trống | 51 | 49 `NO_SOURCE`, 1 `NOT_SEARCHED`, và 1 `UNRESOLVED` (VPX) |

**Lưu ý về SVN:** `Foreign_Manager = 1` theo quy tắc mã hóa riêng mà chủ nghiên cứu vừa chỉ định. Quốc tịch/quốc gia thực tế của Michael Marc Lee vẫn `UNKNOWN`; đây không phải xác minh ông có quốc tịch nước ngoài. `Flag_Status = FOUND` và biến nhị phân hiện thống nhất.

Những điểm chính:

1. **Vai trò HĐQT và điều hành được tính riêng.** Có 131 công ty có bằng chứng về người nước ngoài ở HĐQT: 128 công ty có người được nêu tên trong `Foreign_Managers` và 3 công ty có bằng chứng cấp công ty nhưng không nêu tên. Có 14 công ty có người nước ngoài ở BKS, 34 công ty có người ở nhóm `Executive`, và 4 công ty ở nhóm `Other_Manager`. Hai công ty NVB và TYA nằm ở cả `Executive` lẫn `Other_Manager`, nên tổng số công ty duy nhất có một trong hai nhóm là 34 + 4 − 2 = 36.
2. **Trong 22 công ty vừa có chức danh điều hành/cấp quản lý vừa có thành viên HĐQT nước ngoài, 15 công ty có cùng một người giữ cả hai nhóm chức danh.** Có 12 công ty có Chủ tịch HĐQT nước ngoài. Trong dữ liệu hiện tại, không có trường hợp nào trong 12 công ty mà cùng một người vừa là Chủ tịch HĐQT vừa giữ chức điều hành/cấp quản lý. Có chức danh ngoài HĐQT tự nó không chứng minh quyền kiểm soát công ty.
3. **Quốc tịch tập trung ở châu Á**, tổng cộng 30 nhóm quốc tịch trong workbook. Theo 270 `Manager_ID` được đánh dấu nước ngoài, nhiều nhất là Nhật Bản (73 người), Đài Loan (33), Hàn Quốc (27), Singapore (18), Hoa Kỳ (15), Ấn Độ (15), Trung Quốc (14) và Malaysia (11).
4. **Công ty lớn có tỷ lệ cao hơn hẳn.** Trong 193 công ty LOCAL thuộc top 200 vốn hóa, 55 công ty (khoảng 28%) có `Foreign_Manager = 1`. Tỷ lệ chung của nhóm LOCAL là 9,4%.
5. **Độ chắc chắn khác nhau giữa các công ty.** 98 công ty có bằng chứng trực tiếp: nguồn ghi rõ quốc tịch. 2 công ty chỉ dựa vào nơi sinh. 46 công ty được mã hóa theo hướng suy luận/quy tắc chủ nghiên cứu, trong đó SVN là ngoại lệ do chủ nghiên cứu chỉ định và không phải quốc tịch đã xác minh. Mục 3.3 hướng dẫn cách chạy kiểm tra độ vững theo các mức bằng chứng này.
6. **Cờ 0 có nghĩa là "không tìm thấy", không có nghĩa là "đã xác minh quốc tịch từng người".** Người nước ngoài mang tên Việt hoặc tên Hán-Việt chỉ được phát hiện khi tài liệu ghi quốc tịch của họ.

---

## 2. Nội dung bàn giao

### 2.1. File chính: `1_Vietnam_2025_Foreign_Managers.xlsx`

| Sheet | Mỗi dòng là | Mức độ cần dùng |
|---|---|---|
| **Companies** | 1 mã trong danh sách Bloomberg (1.599 dòng) | **Chính**: phân loại sở hữu và cờ người nước ngoài |
| **Foreign_Managers** | 1 người × 1 chức danh (326 dòng; 289 dòng được mã hóa nước ngoài, 37 dòng chưa rõ phân loại) | **Chính**: danh sách người kèm chức danh, nguồn và trang |
| README | – | Định nghĩa cột và các quy tắc đã chốt. Nên đọc một lần |
| Coverage_Log | 1 mã | Đã đọc tài liệu nào cho từng công ty. Tra khi cần giải thích một giá trị 0 hoặc giá trị trống |
| Company_Level_Evidence | 3 dòng | 3 công ty mà báo cáo chỉ ghi "HĐQT có thành viên quốc tịch nước ngoài", không nêu tên |
| Ownership_Observations | 1 giá trị × 1 nguồn | Mọi giá trị sở hữu nước ngoài thu thập được, dùng để kiểm tra phân loại |
| Review_Open | 44 công ty | Các công ty còn ứng viên/chức danh cần rà soát; gồm cả công ty đã có người nước ngoài xác nhận nhưng còn tên mở khác |
| Candidates, Candidate_Decisions | 1 tên | Vết kiểm toán: các tên đã sàng lọc và lý do giữ hoặc loại từng tên |
| Names_In_AR, Roster_CafeF_Now | 1 tên | Dữ liệu thô dùng để đối chiếu |
| Bloomberg_Raw | 1 mã | Bản sao nguyên trạng file Bloomberg đầu vào |

### 2.2. Tài liệu kèm theo

- `BAO_CAO_BAN_GIAO.md`: tài liệu này.
- `methodology.md`: mô tả phương pháp chi tiết.
- Repo GitHub chứa code thu thập (`vietnam/pipeline/`, phần dùng chung ở `shared/`) và mọi quyết định duyệt tay (`vietnam/data/manual/`). Bản PDF gốc (khoảng 88 GB) không nằm trong repo; nhóm dữ liệu lưu giữ và cung cấp khi được yêu cầu.

---

## 3. Hướng dẫn sử dụng

### 3.1. Chọn mẫu phân tích

Trong sheet **Companies**, lọc `In_Scope = 1` và `Ownership_Type = LOCAL`. Kết quả còn 1.553 công ty.

- `Ownership_Type` dựa trên tỷ lệ sở hữu nước ngoài (`Foreign_Ownership_Pct`) tại 31/12/2025. Trên 50% là `FOREIGN_MAJORITY`, từ 50% trở xuống là `LOCAL`, không có số liệu là `REVIEW`.
- 5 công ty FOREIGN_MAJORITY sát ngưỡng (50–55%: DHG, IMP, TKU, TNH, VNM) vẫn có cờ, vì đã được tìm để phòng trường hợp phải phân loại lại. Bộ lọc `LOCAL` sẽ tự loại chúng.

### 3.2. Biến cờ

| Cột | Ý nghĩa |
|---|---|
| **`Foreign_Manager_Core`** (khuyên dùng làm biến chính) | 1 nếu có người nước ngoài ở HĐQT, BKS hoặc Ban điều hành (TGĐ, Phó TGĐ, Giám đốc tài chính, Kế toán trưởng…). Ba nhóm này được tìm theo cùng một cách ở mọi công ty, nên **so sánh được giữa các công ty**. Nhóm LOCAL có 145 công ty bằng 1 |
| `Foreign_Manager` | Như trên, tính thêm cấp quản lý khác (Giám đốc khối, cố vấn…). Nhóm LOCAL có 146 công ty bằng 1. Cấp quản lý khác chỉ có số liệu khi tài liệu tự liệt kê, nên chỉ dùng làm biến bổ sung |
| Phân tích chức danh điều hành | 36 công ty LOCAL có `Executive` hoặc `Other_Manager`: 34 + 4 − 2 công ty trùng (NVB, TYA). Nếu chỉ tính `Executive`, có 34 công ty. Đây là cách đo gần hơn với người có thể tham gia quyết định hoạt động thường ngày. |
| Kết hợp với HĐQT | Trong 36 công ty có chức danh điều hành/cấp quản lý, 22 công ty cũng có người nước ngoài ở HĐQT; 12 có Chủ tịch HĐQT nước ngoài. Đây là sự hiện diện ở cấp công ty, không đồng nghĩa chức danh quản lý ngoài HĐQT có quyền kiểm soát. |
| `Flag_Status` | Trạng thái tìm kiếm. Dùng `Foreign_Manager` cho biến nhị phân. Riêng SVN được mã hóa bằng 1 theo quy tắc của chủ nghiên cứu; quốc tịch vẫn UNKNOWN |
| `N_Foreign_Managers`, `N_Foreign_Board`, `N_Foreign_Supervisory`, `N_Foreign_Executive`, `N_Foreign_Other` | Số người được nêu tên theo từng nhóm chức danh; 3 bằng chứng HĐQT cấp công ty không nêu tên nằm riêng ở `Company_Level_Evidence` |
| `Foreign_Manager_Summary` | Tên, chức danh và quốc tịch của từng người, dạng một dòng chữ |

**Ô để trống là thiếu dữ liệu, không phải 0.** Khi nạp vào Stata, R hoặc Python, hãy giữ các ô này là missing.

### 3.3. Kiểm tra độ vững theo mức bằng chứng

Mỗi người nước ngoài trong sheet **Foreign_Managers** có cột `Evidence_Type`:

| Mức | `Evidence_Type` | Nghĩa |
|---|---|---|
| Trực tiếp | `DOC_FIELD`, `CV`, `DISCLOSURE_FORM`, `NEWS`, `WEBSITE` | Nguồn ghi rõ quốc tịch: báo cáo thường niên hoặc báo cáo quản trị, CV ứng viên, bản cung cấp thông tin người nội bộ, báo chí, website công ty. Các mô tả kiểu "người Hàn Quốc" cũng được chấp nhận |
| Nơi sinh | `BIRTHPLACE` | Không nguồn nào ghi quốc tịch, chỉ có nơi sinh hoặc nguyên quán ở nước ngoài |
| Suy luận | `INFERRED`; cột `Note` mở đầu bằng `INFERRED_STRONG` / `INFERRED_MEDIUM` / `INFERRED_WEAK` | Không có nguồn nào ghi quốc tịch hay nơi sinh, dù đã tìm hết các nguồn. **Mạnh**: đại diện của cổ đông hoặc tập đoàn nước ngoài có nêu tên. **Trung bình**: sự nghiệp hoặc học vấn ở nước đó, kết hợp với tên. **Yếu**: chỉ dựa vào tên |

Số công ty LOCAL có cờ = 1 theo từng ngưỡng bằng chứng (cộng dồn):

| Định nghĩa | Cờ = 1 | Cờ = 0 | Để trống |
|---|---|---|---|
| A. Chỉ bằng chứng trực tiếp, gồm cả 3 công ty có câu cấp công ty | 98 | 1.356 | 99 |
| B. A + nơi sinh | 100 | 1.356 | 97 |
| C. B + suy luận mạnh | 108 | 1.356 | 89 |
| D. C + suy luận trung bình | 119 | 1.356 | 78 |
| E. Tất cả (= `Foreign_Manager`) | 146 | 1.356 | 51 |

SVN chỉ được tính ở mức E theo quy tắc mã hóa chủ nghiên cứu; không được tính vào A–D. Ở các định nghĩa chặt hơn, công ty chỉ đạt mức bằng chứng yếu hơn ngưỡng được để trống, không gán 0. Lý do là công ty đó có người nghi là nước ngoài, chỉ chưa chứng minh được. Nếu muốn, có thể chạy thêm một phiên bản gán 0 cho những công ty này.

### 3.4. Sheet Foreign_Managers

- Nối với Companies bằng `Foreign_Managers.Ticker` = `Companies.Ticker_Local`.
- Các cột theo yêu cầu: Company · Ticker · Year · Manager_Name · Raw_Position · Nationality · Source · Page.
  - `Raw_Position` giữ nguyên chữ của nguồn.
  - `Role_Group` là nhóm đã chuẩn hóa: Board / Supervisory / Executive / Other_Manager.
- `Nationality` là tên nước chuẩn hóa bằng tiếng Anh.
  - `Nationality_Raw` là nguyên văn của nguồn.
  - Người có hai quốc tịch được ghi `Dual_Nationality = 1`.
- `Is_Foreign = 1` là người nước ngoài.
  - 37 dòng để trống `Is_Foreign` thuộc 37 `Manager_ID`; một `Manager_ID` còn có một dòng chức danh khác đã mã hóa 1. SVN/Michael Marc Lee được mã hóa `Is_Foreign=1` theo quy tắc riêng của chủ nghiên cứu, nhưng `Nationality=UNKNOWN`.
  - Có 306 `Manager_ID` duy nhất, trong đó 270 có ít nhất một dòng `Is_Foreign=1`. Một người có thể có nhiều dòng nếu giữ nhiều chức danh.
- **`Management_Include` được để trống để nhóm nghiên cứu tự quyết** có tính người đó là "manager" theo định nghĩa của nghiên cứu hay không. Ví dụ: cố vấn HĐQT, thành viên chỉ thuộc tiểu ban.
- Một người giữ hai chức danh thì có hai dòng, cùng `Manager_ID`.

### 3.5. Tra lại nguồn của một dòng

- `Evidence_Quote` chép nguyên văn câu ghi chức danh và quốc tịch.
- `Source` cho biết tên tài liệu, `Source_URL` là đường dẫn tải.
- `Page` là **số trang của file PDF, đếm từ 1**. Số này có thể khác số in ở chân trang.
- Nguồn bổ sung, ví dụ bài báo ghi quốc tịch, nằm ở `Other_Sources`. Căn cứ của các trường hợp suy luận nằm ở `Note`.

### 3.6. Code mẫu (Python, pandas)

```python
import pandas as pd

f = "1_Vietnam_2025_Foreign_Managers.xlsx"
co = pd.read_excel(f, sheet_name="Companies")
fm = pd.read_excel(f, sheet_name="Foreign_Managers")

# Mẫu phân tích: công ty trong phạm vi, sở hữu nước ngoài ≤ 50%
df = co[(co["In_Scope"] == 1) & (co["Ownership_Type"] == "LOCAL")].copy()

# Mức bằng chứng của từng người nước ngoài (0 = trực tiếp ... 4 = suy luận yếu)
LEVEL = {"BIRTHPLACE": 1, "INFERRED_STRONG": 2, "INFERRED_MEDIUM": 3, "INFERRED_WEAK": 4}
fm = fm[pd.to_numeric(fm["Is_Foreign"], errors="coerce") == 1].copy()
tag = fm["Evidence_Type"].where(fm["Evidence_Type"] != "INFERRED",
                                fm["Note"].fillna("").str.split(":").str[0])
fm["Level"] = tag.map(LEVEL).fillna(0)

# Mức bằng chứng mạnh nhất của mỗi công ty; công ty có câu cấp công ty (không nêu tên) = 0
best = fm.groupby("Ticker")["Level"].min()
df["Best_Level"] = df["Ticker_Local"].map(best)
df.loc[(df["Foreign_Manager"] == 1) & df["Best_Level"].isna(), "Best_Level"] = 0

# Cờ theo từng ngưỡng (bảng ở mục 3.3); công ty chỉ đạt mức yếu hơn ngưỡng → để trống
for k, name in enumerate(["FM_direct", "FM_birthplace", "FM_inf_strong", "FM_inf_medium", "FM_all"]):
    df[name] = df["Foreign_Manager"].where(~((df["Foreign_Manager"] == 1) & (df["Best_Level"] > k)))
```

Nếu dùng Stata hoặc Excel, cách làm tương tự:
1. Trong Foreign_Managers, giữ các dòng `Is_Foreign = 1`.
2. Gán mức bằng chứng cho từng dòng theo `Evidence_Type`; với `INFERRED` thì lấy phần đầu cột `Note`.
3. Lấy mức nhỏ nhất (mạnh nhất) theo `Ticker`, rồi ghép vào Companies.

---

## 4. Phương pháp tóm tắt

Chi tiết xem `methodology.md`.

1. **Danh sách công ty**:
   - Đầu vào là file Bloomberg gồm 1.599 mã, xuất ngày 27/10/2026.
   - 1.575 mã nằm trong phạm vi.
   - Ngoài phạm vi: 21 ETF và quỹ đóng, 2 mã đã hủy niêm yết, 1 mã không có dữ liệu.
2. **Sở hữu nước ngoài**:
   - Nguồn chính là file VSDC "FOL 31.12.2025" do HOSE và HNX công bố.
   - 5 công ty Việt Nam niêm yết ở nước ngoài được xác định từ hồ sơ công bố của chính họ.
3. **Định nghĩa manager**:
   - Người giữ chức ở HĐQT, BKS (hoặc Ủy ban kiểm toán), Ban điều hành hoặc cấp quản lý khác **tại chính công ty niêm yết**, vào bất kỳ thời điểm nào trong năm 2025.
   - Chức danh ở công ty con không tính.
4. **Nguồn tìm người và quốc tịch**, theo thứ tự ưu tiên:
   - Báo cáo thường niên 2025: cơ sở chính, đọc cho 1.465 công ty.
   - Báo cáo tình hình quản trị năm 2025: dùng cho công ty không có báo cáo thường niên 2025.
   - Báo cáo thường niên 2024: phương án cuối cùng, chỉ dùng cho 11 công ty và có ghi chú.
   - Để xác minh từng người, tìm thêm trong: tài liệu ĐHĐCĐ 2018–2026 (CV ứng viên), thông báo của HĐQT, bản cung cấp thông tin người nội bộ, website công ty và báo chí.
   - Trang scan được nhận dạng chữ (OCR), sau đó mở ảnh trang để đối chiếu trước khi ghi.
5. **Quy tắc quốc tịch**:
   - Ưu tiên nguồn ghi rõ quốc tịch.
   - Theo quyết định ngày 02/11/2026: chấp nhận mô tả kiểu "người Hàn Quốc"; dùng nơi sinh ở nước ngoài khi không có nguồn nào khác, gắn nhãn `BIRTHPLACE`; cho phép suy luận khi đã tìm hết nguồn, gắn nhãn `INFERRED` kèm mức độ.
   - Mọi trường hợp đều được gắn nhãn để có thể lọc riêng.
6. **Không xóa và không sửa dữ liệu gốc.** Mỗi tên bị loại đều có lý do và trang nguồn (sheet `Candidate_Decisions`). Giá trị thiếu không bao giờ bị chuyển thành 0.

---

## 5. Kiểm tra chất lượng

- **Kiểm tra tự động:** bản build ngày 02/11/2026 in ra 0 vi phạm. File Excel đã được cập nhật thủ công sau lần build đó; chưa chạy lại toàn bộ `qa_checks.py` trên bản ngày 04/11/2026. Các số liệu trong mục 1 và các phần liên quan đã được tính lại trực tiếp từ workbook hiện hành. Các điểm kiểm tra của lần build trước:
  - Bloomberg_Raw khớp từng ô với file gốc.
  - Phân loại sở hữu khớp với tỷ lệ sở hữu nước ngoài và quy tắc.
  - Cờ khớp với các bản ghi người; không có cờ 0 khi còn tên chưa xác định.
  - Mọi dòng người nước ngoài có nguồn, trang, loại bằng chứng và trích dẫn.
  - Quốc tịch thuộc danh sách chuẩn; không có dòng trùng.
  - Tên người có mặt trên đúng trang ghi trong `Page`.
- **Đối chiếu ảnh trang:** mọi bản ghi lấy từ trang scan (OCR) hoặc trang trình bày hai cột đều đã được mở ảnh trang để đối chiếu. Nhờ bước này, đã phát hiện và sửa vài trường hợp chức danh hoặc tiểu sử của hai người bị trộn với nhau.
- **Đối chiếu nhãn quốc tịch:** mọi trang báo cáo có nhãn quốc tịch khác Việt Nam đều đã được khớp với một bản ghi, một quyết định loại, hoặc một ghi chú kiểm tra trang.
- **Kiểm tra thủ công theo mẫu ngẫu nhiên:** đã tạo sẵn mẫu, gồm 17 dòng Foreign_Managers và 30 công ty có cờ 0 (`data/full/qa_sample_*.csv`), nhưng **chưa thực hiện tại thời điểm bàn giao**.

---

## 6. Giới hạn cần lưu ý khi phân tích

1. **Cờ 0 có thể bỏ sót** người nước ngoài mang tên Việt hoặc tên Hán-Việt, khi tài liệu không ghi quốc tịch.
2. **Có 45 công ty LOCAL mà cờ = 1 chỉ dựa trên suy luận**, trong đó 26 công ty chỉ dựa vào tên. Nên chạy kiểm tra độ vững theo mục 3.3.
3. **Nơi sinh không đồng nghĩa với quốc tịch.** Đã gặp trường hợp người sinh ở Việt Nam nhưng mang quốc tịch Hoa Kỳ.
4. **Quốc tịch kép chỉ được ghi khi nguồn nói rõ.** Một số người gốc Việt có thể đồng thời giữ quốc tịch Việt Nam; ghi chú ở cột `Note`.
5. **Cấp quản lý dưới Ban điều hành không được tìm đồng đều** giữa các công ty. Vì vậy nên dùng `Foreign_Manager_Core` làm biến chính.
6. **51 công ty LOCAL chưa có kết luận `Foreign_Manager`:**
   - 49 công ty không có báo cáo nào đọc được.
   - 1 công ty còn người chưa xác định được quốc tịch và mang trạng thái `UNRESOLVED`: VPX (Giám đốc CNTT Steve Yam).
   - 1 công ty chưa tìm: VinFast (VFS, niêm yết ở Mỹ).
   - SVN đã được tính vào `Foreign_Manager=1` theo quy tắc riêng của chủ nghiên cứu; quốc tịch/quốc gia thực tế của Michael Marc Lee vẫn UNKNOWN.
7. **11 công ty dùng báo cáo thường niên 2024 làm cơ sở.** Danh sách nhân sự của các công ty này là danh sách tại thời điểm công bố, tức đầu năm 2025.
8. **Tỷ lệ sở hữu theo VSDC chỉ tính sở hữu trực tiếp.** Quyền kiểm soát gián tiếp qua pháp nhân trong nước không được phản ánh.
9. **Danh sách Bloomberg là ảnh chụp tháng 10/2026.** Các mã đã hủy niêm yết trước thời điểm đó không có trong danh sách.

---

## 7. Cập nhật và tái tạo dữ liệu

- Mọi bổ sung hoặc chỉnh sửa đều đi qua các file duyệt tay trong `vietnam/data/manual/`:
  - `manager_records.csv`: bản ghi người nước ngoài.
  - `candidate_decisions.csv`: quyết định giữ hoặc loại từng tên.
  - `company_level_evidence.csv`: câu ghi ở cấp công ty.
  - `ownership_manual.csv`: sở hữu xác định thủ công.
- Sau khi sửa các file trên, chạy lại (từ thư mục gốc của repo) `vietnam/pipeline/05a_candidates.py`, rồi `vietnam/pipeline/07_build_excel.py`, rồi `vietnam/pipeline/qa_checks.py`. Kết quả là file Excel mới, có kiểm tra tự động.
- Cách làm (cấu trúc cột, quy tắc sở hữu, cờ, mức bằng chứng) dùng lại được cho các nước khác; chỉ cần thay phần lấy nguồn tài liệu.

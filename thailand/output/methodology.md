# Phương pháp – Listed Companies & Foreign Managers, Thailand FY2025

Thái Lan là nước thứ 2 trong 5 nước, dùng chung quy tắc với Việt Nam. Tài liệu này chỉ mô tả các điểm riêng của Thái Lan. Những gì giống Việt Nam xem ở `output/methodology.md`.

## 1. Phạm vi

- **Danh sách gốc**: file Bloomberg (`Bloomberg-Thailan2025_9666.xlsx`), gồm 955 mã có trụ sở ở Thái Lan. Giá trị được chép nguyên.
  - 945 mã niêm yết trên SET/mai.
  - 10 mã niêm yết ở nước ngoài: Fabrinet (Mỹ), THBEV (Singapore), 6603 (Hồng Kông)…
  - **Mã Bloomberg khác mã SET** (sửa 09/11/2026): Bloomberg bỏ "&" và "-" khỏi mã SET, nên factsheet từng bị tra sai mã. Bảng đối chiếu nằm ở `data/manual/set_symbol_manual.csv`:
    - S&J → SNJ, SE-ED → SEED, F&D → FND, M-CHAI → MCHAI, Q-CON → QCON, L&E → LNE.
    - BANPUU là Banpu PCL trước khi sáp nhập với Banpu Power năm 2026. Mã SET BANPU hiện là công ty kế thừa.
  - CTARAF là quỹ bất động sản (Centara Hotels & Resorts Leasehold Property Fund), nên đã chuyển ra ngoài phạm vi.
- **Ngoài phạm vi (`In_Scope = 0`)**: 79 quỹ, REIT, ETF và quỹ hạ tầng. Lọc theo nhóm ngành Bloomberg, cộng một danh sách tay trong `data/manual/security_class_manual.csv`.
- **Năm**: FY2025, nghĩa là giữ chức vào bất kỳ lúc nào trong năm 2025.
  - Loại người nhận chức sau 31/12/2025, kể cả người được đánh dấu "(***)" trong báo cáo.
  - Loại người rời chức trước 1/1/2025.
- **Manager** gồm ba nhóm:
  - HĐQT (Board), gồm cả thành viên rời chức trong năm.
  - Ban điều hành (Executive), theo danh sách 7.4 của One Report.
  - Quản lý khác (Other_Manager), chỉ lấy từ BoardEx và chỉ khi BoardEx ghi quốc tịch nước ngoài.
- Thái Lan không có Ban kiểm soát, nên không có nhóm Supervisory.

## 2. Sở hữu nước ngoài (FO)

- **Ngưỡng**: > 50% là `FOREIGN_MAJORITY`, ≤ 50% là `LOCAL`, không có số là `REVIEW`.
- **Thứ tự nguồn** (quyết định 07/11/2026), lấy nguồn đầu tiên có số:
  1. Số có bản quyền đúng ngày 31/12/2025, đặt ở `data/manual/fo_licensed.csv`. **Hiện chưa có.**
  2. Hồ sơ công ty, đặt ở `data/manual/ownership_manual.csv`. Dùng cho các trường hợp sau:
     - Mã niêm yết ở nước ngoài có cổ đông kiểm soát:
       - 6603, THBEV (cổ đông Thái);
       - MMT: Thoresen Thai Agencies nắm trực tiếp 58,18%, theo One Report 2025 của TTA.
     - Cổ đông nước ngoài được miễn hạn mức: BAY (MUFG 76,88%), CIMBT (CIMB 94,83%).
     - Báo cáo có lớp chữ hỏng: SPG.
     - Công ty đã hủy niêm yết hoặc bị đình chỉ, không còn factsheet. Số lấy từ danh sách cổ đông lớn trong One Report 2025:
       - LRH: 85,65% qua hai công ty đăng ký ở Thái Lan của Banyan Tree. Theo quy tắc sở hữu gián tiếp bên dưới, phần này không tính là nước ngoài.
       - SVI, GLAND, BPP: cổ đông Thái nắm 58–97%.
     - UOBKH: UOB-Kay Hian Holdings (Singapore) và công ty con BVI nắm 89,58%, theo thông báo SGX ngày 19/05/2025.
   - Mã niêm yết ở nước ngoài **không có cổ đông kiểm soát** (quyết định 09/11/2026, `FO_Method = RULE_FOREIGN_LISTED_NO_THAI_CONTROLLER`):
     - Cổ phiếu nằm ở sàn và lưu ký nước ngoài, nên phần không xác định được coi là nước ngoài, và `FO_Bound = ">= 100 − tỷ lệ của cổ đông Thái đã xác định"`.
     - Cổ đông Thái < 50% thì xếp `FOREIGN_MAJORITY`.
     - Kết quả:
       - FN_US: proxy 2025, không có cổ đông Thái, ≥ 99,76%.
       - 1949: công ty của hai nhà sáng lập người Thái nắm 10,63%, ≥ 89,37%.
       - FLG: một giám đốc người Thái nắm 1,90%, ≥ 98,10%. Công ty này đăng ký ở Singapore và điều hành từ Chile; tài sản ở Thái Lan nằm trong các công ty con.
     - 8444 (Green River) không cần dùng quy tắc: các cổ đông đã rõ là người Đài Loan hoặc đăng ký ở Samoa nắm 50,36% (`FILING_BOUND_FOREIGN_HOLDER`).
   - Ba mã OTC ở Mỹ (ZUUS, BKMP, VPSN) để `REVIEW`, vì không đọc được hồ sơ: SEC EDGAR trả 403 cho User-Agent của dự án và dự án không lách. AKS (đã hủy niêm yết) cũng chưa đủ căn cứ.
  3. Bảng "cổ đông theo quốc tịch" trong One Report 2025. Chỉ dùng khi bảng có ngày. Hiện có 3 công ty.
  4. Trang factsheet SET, mục "Foreign Shareholders". Đây là số tại ngày crawl (06/11/2026), không phải 31/12/2025. Cột `FO_Date_Gap_Days` ghi độ lệch ngày.
- **Factsheet ghi "-"**: nếu `Foreign Limit` ≤ 50% thì đặt `FO_Bound = "<= limit"`, xếp `LOCAL` (`FO_Method = LIMIT_BOUND`). Có 43 công ty như vậy.
- **NVDR không cộng vào FO.** NVDR là chứng chỉ không có quyền biểu quyết, nhà đầu tư nước ngoài thường dùng để vượt hạn mức. Các cột liên quan:
  - `NVDR_Pct`.
  - `FO_Plus_NVDR`.
  - `NVDR_Sensitive = 1` khi FO ≤ 50% < FO + NVDR.
- **Hạn chế của factsheet**: số này chỉ đếm sổ cổ đông nước ngoài trong hạn mức, nên bỏ sót cổ đông chiến lược được miễn hạn mức. Ví dụ BAY: factsheet 25%, thực tế MUFG nắm 76,88%. Vì vậy mọi công ty sau được đọc tay danh sách cổ đông lớn trong One Report:
  - FO 40–60%;
  - đang ở sát hạn mức;
  - hạn mức > 50%;
  - có cổ đông lớn nghi là nước ngoài.

  Có 87 công ty được đọc. Quyết định và căn cứ ghi ở `data/manual/fo_review.csv` và hiện ở các cột `FO_Review_Decision`, `FO_Review_Basis`.
  - Ví dụ F&D: ông Chang Chih-Hao nắm 95,39% sau đợt chào mua tháng 5/2025. Phần vượt hạn mức 49% nằm qua NVDR, nên FO vẫn là 49% và công ty có `NVDR_Sensitive = 1`.
- **Sở hữu gián tiếp** qua công ty đăng ký ở Thái Lan **không** tính là nước ngoài, giống quy tắc sổ cổ đông. Ví dụ:
  - SHANG.
  - ASK: Chailease Capital (Thailand).
  - FPT: Frasers Property Holdings (Thailand).
  - MRDIYT: MR. D.I.Y. Co., Ltd.

## 3. Nguồn và cách đọc

- **One Report 2025 (Form 56-1)**:
  - Tên file lấy từ trang factsheet SET. Robots của trang này cho phép truy cập.
  - File tải qua `market.sec.or.th/public/idisc/Download`. Robots cũng cho phép.
  - Không dùng API của SET (bị chặn bot) và không dùng `weblink.set.or.th` (robots cấm).
  - User-Agent ghi đúng tên công cụ; mỗi host cách nhau ≥ 3 giây; gặp 403/429 thì dừng.
  - **Khi factsheet không có link**, vì công ty đã hủy niêm yết, bị đình chỉ, hoặc bản mới chưa tải được: lấy file từ danh sách hồ sơ 56-1 của SEC. Đường dẫn là `market.sec.or.th/public/idisc/en/FinancialReport/R561-<id>`, với id lấy từ trang `…/companyprofile/listed/<mã>`. Robots chỉ cấm `*.aspx`. Theo cách này:
    - SVI, GLAND, BPP, LRH, BANPUU (Banpu cũ) lấy được One Report 2025.
    - TNH và CITY có năm tài chính kết thúc 31/07/2025 (`Source_Basis = ONE_REPORT_FY2025_JUL`).
  - **Không có bản 2025** thì dùng One Report 2024 làm nguồn cuối cùng, có ghi chú (quy tắc AR2024 của Việt Nam). Trường hợp này áp dụng cho QDC, MVP và AKS (`Source_Basis = ONE_REPORT_2024_FALLBACK`). Người nhận chức sau ngày lập báo cáo 2024 có thể bị thiếu.
- **Công ty Thái niêm yết ở nước ngoài** (THBEV, 6603, MMT) không nộp Form 56-1. Nguồn thay thế là báo cáo thường niên 2025 trên SGX/HKEX (`Source_Basis = FOREIGN_LISTING_ANNUAL_REPORT`). THBEV còn được đối chiếu với báo cáo 2024 để tìm người rời chức.
- **Mẫu chuẩn của SEC** ghi cho từng giám đốc, kể cả người rời chức trong năm:
  - **"Thai nationality: Yes/No"** (tiếng Thái: "สัญชาติไทย: ใช่/ไม่ใช่");
  - "Residing in Thailand".

  Ở dạng e-form (khoảng một nửa số báo cáo), danh sách ban điều hành 7.4.1 cũng có hai trường này.
- **Bước 05** tách người theo mẫu:
  - Đọc mọi file PDF trong bộ hồ sơ và chọn file ghi được nhiều quốc tịch nhất.
  - Kiểm tra đủ người theo hai cách:
    - đếm số giám đốc, so với bảng tổng 7.2.1 (477 công ty LOCAL khớp);
    - với dạng e-form không có bảng 7.2.1, kiểm tra số thứ tự liên tục.
- **Bước 07**: giám đốc có "Thai nationality: No" mà cũng nằm trong danh sách ban điều hành không có trường quốc tịch được ghi thêm một dòng Executive. Bằng chứng của dòng này là mục giám đốc của chính người đó (sửa 09/11/2026, thêm 67 dòng).
- **Người rời chức không có trong mẫu**: mẫu "left during the year" có thể thiếu người. Ví dụ ở F&D, cả HĐQT cũ từ chức tháng 5/2025 sau đợt chào mua, và hai người nước ngoài được lấy từ One Report 2024.
- **Bước 10** đọc toàn văn mọi báo cáo một lần:
  - Lưu text vào `data/full/text/`.
  - Lập chỉ mục mọi câu "Nationality: X" / "สัญชาติ X" trong phần tiểu sử.

## 4. Xác định người nước ngoài

**One Report quyết định một người có phải người nước ngoài không** (quyết định 07/11/2026). BoardEx chỉ dùng để điền tên nước và bổ sung quản lý cấp dưới.

| `Evidence_Type` | Khi nào |
|---|---|
| `ONE_REPORT_FIELD` | Dòng "Thai nationality: No" của chính người đó |
| `DOC_FIELD` | Người trong danh sách ban điều hành không có trường quốc tịch, nhưng phần tiểu sử ghi rõ quốc tịch |
| `BOARDEX` | Quản lý dưới ban điều hành mà BoardEx ghi quốc tịch nước ngoài, với chức danh còn hiệu lực trong 2025 |
| `INFERRED` | Người trong danh sách ban điều hành không có trường quốc tịch, có tên không phải tên Thái, và không nguồn nào ghi quốc tịch. Ghi chú (`Note`) nêu căn cứ |

**Mâu thuẫn giữa One Report và BoardEx** (10 trường hợp, sheet `Source_Conflicts`) được giữ theo One Report và kiểm tra tay. Thường đó là BoardEx gán nhầm người, ví dụ gia đình Leungsuwan bị ghi Tanzania.

**Cách ghép tên với BoardEx** (sửa 09/11/2026):
- Ghép trong cùng một công ty, theo độ giống tên (≥ 88).
- Không bao giờ ghép chỉ bằng họ. Trước đây, khi BoardEx để trống tên gọi, một biến thể chỉ còn họ (ví dụ "Uer-Anant") cho điểm 100 với mọi người thân cùng họ. Lỗi này gây 34 cặp ghép nhầm, đều là người Thái, nên không ảnh hưởng tới người nước ngoài hay cờ công ty.
- Khi hai hồ sơ BoardEx hòa điểm (thường là hai hồ sơ của cùng một người, ví dụ ANI Nichol Yeo), chọn mã nhỏ hơn để mọi lần chạy cho cùng kết quả.
- Nếu hai hồ sơ hòa điểm mà ghi quốc tịch khác nhau thì không ghép. Hiện chưa có trường hợp nào như vậy.

**Người trong danh sách ban điều hành không có trường quốc tịch** (184 dòng ứng viên) được xử lý như sau:
- 80 tên Thái: đóng với `THAI_NAME_NO_FIELD`. Công ty mang `Verification_Level = BOARD_STATED`.
- 2 người tiểu sử cho thấy là người Thái (TIDLOR, ICC): `NOT_FOREIGN_*`.
- 32 dòng ở công ty FOREIGN_MAJORITY: không tìm sâu (`NOT_SEARCHED_FOREIGN_MAJORITY`).
- Còn lại: ghi thành bản ghi `DOC_FIELD` hoặc `INFERRED`.
- 3 người không đủ căn cứ (AWC, BTG, PTTGC) được để mở.

**Tên nước** (`Nationality`, căn cứ ở `Country_Evidence_Type`). One Report chỉ cho biết có phải người Thái hay không. Tên nước được tìm theo từng công ty, theo thứ tự (quyết định 08/11/2026):
1. BoardEx (`BOARDEX`).
2. Câu ghi quốc tịch trong tiểu sử (`DOC_FIELD`). Có thể lấy từ báo cáo của chính công ty, hoặc của công ty khác có cùng người đó (Note: `NATIONALITY_FROM_OTHER_ISSUER`).
3. Suy luận, chỉ khi các bước trên không có kết quả:
   - `INFERRED_STRONG`: tiểu sử của chính người đó ghi rằng họ làm việc cho cổ đông hoặc công ty mẹ nước ngoài có tên, ví dụ "Senior Managing Executive Officer, Meiji Yasuda Life Insurance". Công ty con ở Thái Lan cùng tên **không** được tính. Lấy nước của cổ đông đó.
   - `INFERRED_MEDIUM`: tiểu sử của chính người đó nêu nơi học hoặc nơi làm việc ở nước X (phải có tên nước hoặc tên trường đặt ở nước X), và tên phù hợp với X.
   - `INFERRED_WEAK`: chỉ dựa vào tên mang đặc trưng một nước, như tên Nhật, Hàn, Việt, Ấn, tên Đài Loan viết theo Wade-Giles. Tên tiếng Anh hoặc tên Hoa ở Malaysia/Singapore **không** đủ để chọn nước.
   - Không suy luận được thì giữ `UNKNOWN`. Người đó vẫn là người nước ngoài (`Is_Foreign = 1`).

**Công ty niêm yết ở nước ngoài** (THBEV, 6603, MMT): báo cáo không có trường quốc tịch, nên mỗi người được xác định như ở Việt Nam:
- Có câu ghi quốc tịch → `DOC_FIELD`. Câu đó có thể nằm ở:
  - báo cáo của công ty khác (Michael Chye: F&N Holdings Bhd ghi "Singaporean"; Thevenin: One Report của TTA ghi "Thai nationality: No");
  - câu cấp công ty xác định được người. Ví dụ THBEV: "ủy ban kiểm toán gồm 3 người Thái và 1 người Singapore", và Timothy Chia là thành viên duy nhất không phải người Thái.
- Không có câu nào → suy luận theo các mức ở trên.
- Không suy luận được nước nào → dòng UNKNOWN (`Is_Foreign` trống, không tính vào cờ): Ong Ying Shyun (6603), Simon Wilde (MMT).
- Tên Thái được coi là người Thái.
- Chức ở công ty con không tính, ví dụ các Country Manager của Mermaid ở Ả Rập Xê Út, Qatar, UAE và Anh.

Chưa tìm thêm trên web hoặc trong tài liệu ĐHĐCĐ cho từng người: thử nghiệm cho thấy hồ sơ ứng viên ĐHĐCĐ hiếm khi ghi quốc tịch. Riêng các ca quyết định cờ của công ty thì có tìm web.

## 5. Cờ công ty

| Cột | Ý nghĩa |
|---|---|
| `Foreign_Manager_Core` | **Biến chính.** 1 nếu có người nước ngoài ở HĐQT hoặc ban điều hành |
| `Foreign_Manager` | Tính thêm quản lý cấp dưới. Nhóm này chỉ có dữ liệu ở công ty BoardEx phủ |
| `Flag_Status` | FOUND · NONE_FOUND · UNRESOLVED (còn người chưa quyết định) · NO_SOURCE (không có One Report 2025) · NOT_SEARCHED (mã niêm yết ở nước ngoài) · OUT_OF_SCOPE |
| `Verification_Level` (khi NONE_FOUND) | `ALL_STATED`: mọi người trong mẫu đều ghi Thai nationality. `BOARD_STATED`: HĐQT ghi đủ; ban điều hành không có trường nhưng mọi tên đều là tên Thái |
| `Flag_Basis` | `ONE_REPORT` · `BOARDEX` (không có báo cáo, chỉ có dòng BoardEx) · `OTHER_FILINGS` (báo cáo trên sàn nước ngoài, hồ sơ của công ty khác) |
| `Source_Basis`, `Source_Note` | Cờ dựa trên báo cáo nào: `ONE_REPORT_2025` · `ONE_REPORT_FY2025_JUL` · `ONE_REPORT_2024_FALLBACK` · `FOREIGN_LISTING_ANNUAL_REPORT`. Ghi chú từ `data/manual/company_source_notes.csv` |

Ô trống là thiếu dữ liệu, không phải 0.

## 6. Kiểm tra chất lượng

- **`qa_checks.py`**: 0 vi phạm. Các kiểm tra gồm:
  - số dòng khớp Bloomberg;
  - quy tắc FO và ngày;
  - cờ khớp với bản ghi;
  - nguồn, trang và trích dẫn có đủ;
  - mỗi dòng `ONE_REPORT_FIELD` có trang chứa đúng tên và chữ "No";
  - quốc tịch thuộc danh sách chuẩn;
  - mọi mâu thuẫn đã có quyết định;
  - không trùng người × chức danh.
- **Mẫu thủ công**: 81 bản ghi (10%) và 30 công ty có cờ 0. Kết quả: **0 lỗi**. Chi tiết ở `data/manual/qa_manual.csv`.
- **Kiểm tra độc lập lần 2** (09/11/2026): kiểm tra mọi dòng thêm sau bản bàn giao đầu, gồm 31 dòng người, 11 dòng tên nước và 10 công ty cờ 0. Tìm ra 6 lỗi và 2 chỗ sót người; tất cả đã sửa (`batches/2026-11-09_06_qa_corrections.json`, `_07_qa_additions.json`).
  - Bản ghi: đọc khối thông tin của từng người. Hai trang đọc lại trên ảnh vì lớp chữ không rõ thứ tự.
  - Công ty cờ 0: tìm toàn văn mọi file báo cáo không thấy câu "Thai nationality: No" nào bị bỏ sót.

## 7. Giới hạn

- **Ngày của số FO**: lấy theo factsheet tháng 11/2026 cho tới khi có số có bản quyền tại 31/12/2025. Hạn mức nước ngoài thường là 49%, nên ít khi làm đổi phân loại.
- **Người có hai quốc tịch** khai "Thai nationality: Yes" sẽ không lộ ra. Ví dụ: chủ tịch BGRIM sinh ở Đức nhưng khai là người Thái.
- **Tên nước** của 115 người nước ngoài ở công ty LOCAL vẫn là UNKNOWN (154 trước hai vòng tìm trên web 10–11/11/2026: batch `2026-11-10_01_web_country_round1.json`, `2026-11-11_01_web_country_round2.json`). Ngoài ra 208 người chỉ có suy luận yếu (theo tên).
- **Quản lý cấp dưới ban điều hành** chỉ có ở công ty BoardEx phủ (331/842 công ty LOCAL). Vì vậy `Foreign_Manager` không so sánh được giữa các công ty; hãy dùng `Foreign_Manager_Core`.
- **Báo cáo không phải bản 2025**:
  - QDC, MVP, TAPAC và MILL dùng One Report 2024 (`ONE_REPORT_2024_FALLBACK`).
  - TNH và CITY dùng năm tài chính kết thúc 31/07/2025.
  - Còn 4 mã ở `REVIEW`: AKS, ZUUS, BKMP và VPSN.
- **STRONG và nơi học**: theo quy tắc viết, người có tiểu sử ghi chức ở công ty mẹ nước ngoài được gán nước của công ty mẹ, kể cả khi nơi học chỉ ra nước khác. Ví dụ LRH Stuart Reading: Singapore (STRONG), dù học và lấy chứng chỉ kế toán ở Úc; phương án khác được ghi ở `Note`.
- **Quyền dữ liệu**: điều khoản SET chỉ cho dùng cá nhân, phi thương mại. Cột lấy từ BoardEx cần đối chiếu điều khoản WRDS/BoardEx của nhóm. File Excel không được đưa lên repo công khai.

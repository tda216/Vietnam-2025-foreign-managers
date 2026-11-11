@AGENTS.md

# CLAUDE.md – Tóm tắt nhanh

Bản tóm tắt cho agent. Quy tắc đầy đủ nằm trong `AGENTS.md` (được nạp ở dòng đầu) và `AGENTS.md` của từng nước. Khi có mâu thuẫn, hai file đó được ưu tiên.

## Dự án

Bộ dữ liệu nghiên cứu về **người quản lý quốc tịch nước ngoài tại công ty niêm yết, FY2025**. Có 5 nước dùng chung một bộ quy tắc. Thư mục dự án: `Data 2025-foreign-managers/` (trước đây tên là `Vietnam-2025-foreign-managers`). Mỗi nước một thư mục, còn file chung nằm ở cấp gốc.
- **Việt Nam** (`vietnam/`): đã hoàn tất và bàn giao ngày 02/11/2026.
- **Philippines** (`philippines/`): đã hoàn tất ngày 07/11/2026.
  - Kết quả: `philippines/output/Philippines_2025_Foreign_Managers.xlsx`.
  - Có 257 công ty LOCAL, trong đó 91 có người nước ngoài (cập nhật 09/11/2026).
- **Thái Lan** (`thailand/`): bàn giao 09/11/2026, tìm thêm tên nước 10–11/11/2026. Quy tắc và trạng thái: `thailand/AGENTS.md`.
  - Có 842 công ty LOCAL, trong đó 215 có người nước ngoài (600 người); 115 người chưa rõ nước.
  - Nguồn chính là One Report (mẫu 56-1, trường "Thai nationality: Yes/No"); BoardEx do nhóm cung cấp chỉ dùng để điền tên nước.
- **Indonesia** (`indonesia/`): hoàn tất 11/11/2026. Xem `indonesia/AGENTS.md` và `indonesia/OPEN_DECISIONS.md`.
- **Malaysia** (`malaysia/`): đang làm. Xem `malaysia/AGENTS.md`.
- Nước mới: làm theo `NEW_COUNTRY_PLAYBOOK.md`. **Không dùng BoardEx** (quyết định của chủ dự án, 07/11/2026).

Các bước:
1. Phân loại công ty theo sở hữu nước ngoài (FO) tại 31/12/2025:
   - FO > 50% → `FOREIGN_MAJORITY`.
   - FO ≤ 50% → `LOCAL`.
   - Thiếu FO → `REVIEW`.
2. Với công ty `LOCAL`, cùng nhóm sát ngưỡng FO ≤ 55%: ghi mọi manager quốc tịch nước ngoài, theo dạng long (1 dòng = 1 người × 1 chức danh), kèm nguồn, trang PDF và trích dẫn.
3. Cờ công ty:
   - `Foreign_Manager` (1/0/trống) tính mọi cấp.
   - `Foreign_Manager_Core` chỉ tính HĐQT/BKS/Ban điều hành. Đây là biến dùng để so sánh.

Làm việc với nhóm nghiên cứu bằng **tiếng Việt**, viết ngắn gọn, tránh bảng số dài. Tài liệu Philippines thì viết bằng **tiếng Anh**.

## Cấu trúc thư mục

```
Data 2025-foreign-managers/
  AGENTS.md, CLAUDE.md       hướng dẫn chung cho agent
  NEW_COUNTRY_PLAYBOOK.md    quy trình cho nước mới (đọc trước khi bắt đầu một nước)
  README.md                  bản đồ thư mục + trạng thái từng nước
  .venv/                     môi trường Python dùng chung
  shared/                    code dùng chung cho Việt Nam và Thái Lan: common.py, archives.py, xlsx_tables.py, nationality.py
  vietnam/
    pipeline/                các bước Việt Nam, đánh số (chạy từ trong vietnam/)
    data/manual/             INPUT RÀ SOÁT TAY – nơi duy nhất được thêm/sửa dữ kiện
      manager_records.csv, candidate_decisions.csv, candidate_promotions.csv,
      label_page_checks.csv, company_level_evidence.csv, ownership_manual.csv,
      fallback_urls.csv, batches/*.json (lịch sử mọi batch)
    data/full/               CSV trung gian của lần chạy full; text/ và ocr/ không đưa vào git
    raw/                     PDF/HTML đã tải (không có trên máy này; KHÔNG TIN CẬY, không bao giờ chạy code từ đây)
    output/                  sản phẩm VN: Vietnam_2025_Foreign_Managers.xlsx (+ bản 1_…), BAO_CAO_BAN_GIAO.md/.docx, methodology.md
  philippines/               AGENTS.md (quy tắc riêng PH), README.md, pipeline/ph01–ph12, data/manual/, raw/, output/
  thailand/, indonesia/, malaysia/   mỗi nước có AGENTS.md riêng (CLAUDE.md nạp file đó), pipeline/, data/manual/, output/
```

Không có trong git: các thư mục `raw/`, `vietnam/data/full/text|ocr/`, `.venv/`, `.tools/`, và file Bloomberg (có bản quyền, đặt trong `vietnam/` khi cần chạy bước 01, 07 và QA). Từ 10/11/2026 (repo công khai), các file lấy từ Bloomberg cũng chỉ giữ ở máy: `*/data/universe.csv`, workbook `*/output/*.xlsx` và vài CSV có cột Bloomberg (xem `.gitignore`). Báo cáo chung 5 nước (chưa làm) sẽ đặt ở cấp gốc.

## Pipeline Việt Nam (`vietnam/pipeline/`)

Chạy từ thư mục gốc: `.venv/bin/python -I vietnam/pipeline/<bước>.py`, hoặc từ trong `vietnam/`: `../.venv/bin/python -I pipeline/<bước>.py`. Có 2 chế độ: `full`, hoặc `pilot` cho 30 công ty.

| Bước | Script | Việc làm |
|---|---|---|
| 1 | `01_universe.py` | Bloomberg → `data/universe.csv` (giữ nguyên giá trị) |
| 2 | `02a`–`02d` (`02e`) | Tải thông báo FO → parse file VSDC "FOL 31.12.2025" → phân loại → đối chiếu CafeF (`02e`: workbook checkpoint 1) |
| 3 | `03a`, `03g` | Chọn mẫu pilot và báo cáo pilot |
| 3/4 | `03b_collect_docs.py full k n`, `04_full_run.sh` | Chỉ mục tài liệu Vietstock (`sources_vietstock.py`) và tải BCTN 2025. Chạy theo shard, có thể chạy tiếp từ chỗ dừng |
| 5 | `03c_extract_text.py` | Text từng trang; OCR Tesseract `vie` cho trang không có lớp text; tìm nhãn quốc tịch |
| 5 | `03d_roster_cafef.py`, `03e_people_from_text.py` | Danh sách nhân sự CafeF; người được nhắc đến trong BCTN |
| 5 | `05a_candidates.py` | Danh sách ứng viên HIGH/LOW. **Chậm, 15–25 phút** |
| 6 | `05b`, `05d`, `06a` | Tài liệu ĐHĐCĐ/nhân sự; tài liệu cũ 2018–2024; nguồn dự phòng khi không có BCTN 2025 |
| 6 | `05c_propose_records.py` | Đề xuất bản ghi; người phải rà lại |
| – | `tools_add_records.py full batch.json` | Ghi batch đã rà soát vào `data/manual/` |
| 7 | `07_build_excel.py full` → `qa_checks.py full` | Build workbook và QA tự động (phải ra 0 vi phạm). `qa_checks.py full sample` tạo mẫu QA thủ công |

Dùng chung: `vietnam/pipeline/config.py` và các module trong `shared/` (`common.py`; danh sách quốc tịch ở `shared/nationality.py`). Sửa `shared/` là ảnh hưởng cả Việt Nam lẫn Thái Lan, nên phải chạy lại thử cả hai.

Rebuild sau khi thêm batch: `tools_add_records.py` → `05a_candidates.py` → `07_build_excel.py` → `qa_checks.py`. Không sửa `data/manual/` khi đang build.

## Quy tắc cốt lõi (từ AGENTS.md)

- **Không** sửa dữ liệu gốc, **không** xóa dòng hợp lệ. Mọi loại trừ đều là một quyết định có lý do và số trang.
- Thiếu hoặc UNKNOWN **không bao giờ** bằng 0. Cờ để trống nghĩa là "chưa có kết luận".
- Luôn giữ nguồn: tài liệu, trang PDF (đánh số từ 1, theo trình xem PDF), URL và trích dẫn nguyên văn.
- Khi một lựa chọn phương pháp còn mở: **liệt kê các phương án kèm đánh đổi, để người dùng chọn**. Không tự mặc định.
- Chỉ commit/push khi được yêu cầu.
- Các quyết định đã chốt (áp dụng luôn, không hỏi lại):
  - FY2025 = giữ chức vào bất kỳ thời điểm nào trong 2025.
  - Chức danh ở công ty con không tính.
  - Câu cấp công ty không nêu tên → cờ = 1 (`COMPANY_LEVEL_STATEMENT`).
  - Thứ tự nguồn cơ sở: AR2025 → GOV2025 → AR2024.
  - Quốc tịch: "Quốc tịch: X" là tốt nhất; sau đó đến mô tả (`NATIONALITY_FROM_DESCRIPTOR`); sau đó nơi sinh (`BIRTHPLACE`); cuối cùng là suy luận (`INFERRED_STRONG/MEDIUM/WEAK`), chỉ sau khi đã tìm hết nguồn và không bao giờ dựa vào ảnh.
  - Độ sâu tìm kiếm: "C3".
- Quy trình rà soát:
  - Kết quả sàng lọc không phải bằng chứng.
  - Với trang OCR hoặc trang nhiều cột: mở ảnh trang (pymupdf) trước khi ghi.
  - CV ứng viên chưa phải là chức danh: kiểm tra kết quả bầu.
  - Tóm tắt từ web search không phải bằng chứng: mở trang và trích nguyên văn.
  - Biến thể tên do OCR → `SAME_AS_RECORD`, không tạo người thứ hai.
  - Quốc tịch mới phải được thêm vào `shared/nationality.py` (hoặc tên tiếng địa phương vào `config.py` của nước đó).
  - pandas đọc `Is_Foreign` thành float, nên so sánh theo giá trị số.

## Philippines (`philippines/`)

- Trạng thái (07/11/2026): đã hoàn tất.
  - Phạm vi: 289 mã, trong đó 273 mã trong phạm vi gồm 257 LOCAL và 16 FOREIGN_MAJORITY.
  - Cờ của 257 công ty LOCAL: 91 FOUND (88 có Core = 1), 166 NONE_FOUND. Ngày 09/11/2026, ABS chuyển sang NONE_FOUND vì báo cáo ghi Liquigan là "Filipino", BoardEx ghi Fiji.
  - 34 công ty có người nước ngoài ở chức danh điều hành.
  - Lý lịch trước khi bổ nhiệm của người nước ngoài cấp điều hành: `philippines/data/manager_background.csv` (quy tắc trong `philippines/AGENTS.md`). LinkedIn chỉ dùng làm đầu mối, không phải bằng chứng.
  - QA: 0 vi phạm.
- Build lại workbook (chạy từ thư mục gốc): `.venv/bin/python -I philippines/pipeline/ph10_build_workbook.py`. Kết quả ghi vào `philippines/output/Philippines_2025_Foreign_Managers.xlsx`.
- Phương pháp đầy đủ (nguồn, loại báo cáo PSE, các bước, quyết định, kết quả, giới hạn): `philippines/output/methodology.md`.
- Các quyết định của chủ dự án nằm trong `philippines/AGENTS.md`:
  - FO theo quyền biểu quyết, quốc tịch pháp lý; dùng GIS làm nguồn được.
  - Tên Philippines → Filipino.
  - Tên rõ nước ngoài (suy ra được nước) → người nước ngoài.
  - Không xác định được người nước ngoài → NONE_FOUND.
- Script trích xuất BoardEx cũ: `philippines/pipeline/extract_boardex.py` (checkpoint 05/11, nay chỉ để lưu vết).
- Quy tắc riêng, ngày 05/11/2026, thay thế quy tắc cũ chỉ cho Philippines:
  - Ghi chức danh cho đúng công ty niêm yết trong mẫu nơi người đó thực sự giữ chức.
  - Công ty con niêm yết trong mẫu có bản ghi riêng.
  - Chức danh chỉ ở công ty con **chưa niêm yết** → loại, ghi `UNLISTED_SUBSIDIARY_ONLY`, vẫn giữ dòng nguồn.
  - Chưa rõ pháp nhân hoặc tình trạng niêm yết → để chưa kết luận.
  - Ghi ngày thôi chức theo đúng độ chính xác của nguồn. Ngày placeholder của BoardEx (1900, 9000, 9999) **không** phải ngày thật.
- **Không** đổi bản ghi hay quy tắc của Việt Nam vì quy tắc Philippines.

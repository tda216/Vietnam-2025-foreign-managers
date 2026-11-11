# Công ty niêm yết và người quản lý nước ngoài – FY2025

Bộ dữ liệu nghiên cứu cho 5 nước, cùng một bộ quy tắc:
- Phân loại mỗi công ty niêm yết theo sở hữu nước ngoài tại 31/12/2025: trên 50% là `FOREIGN_MAJORITY`, từ 50% trở xuống là `LOCAL`.
- Với công ty `LOCAL`, liệt kê mọi người quốc tịch nước ngoài giữ chức quản lý trong năm 2025, kèm nguồn và số trang.

| Nước | Thư mục | Báo cáo bàn giao |
|---|---|---|
| Việt Nam | [`vietnam/`](vietnam/) | [vietnam/output/BAO_CAO_BAN_GIAO.md](vietnam/output/BAO_CAO_BAN_GIAO.md) |
| Thái Lan | [`thailand/`](thailand/) | [thailand/output/BAO_CAO_BAN_GIAO.md](thailand/output/BAO_CAO_BAN_GIAO.md) |

Mỗi nước có cấu trúc giống nhau:
- `pipeline/`: code.
- `data/manual/`: các quyết định duyệt tay.
- `data/`: dữ liệu trung gian.
- `output/`: kết quả và tài liệu phương pháp.

Code dùng chung cho mọi nước nằm ở `shared/`.

Không nằm trong repo:
- Dữ liệu có bản quyền (Bloomberg, BoardEx).
- Bản PDF gốc.
- File Excel của Thái Lan.

Cách chạy lại và quy tắc làm việc: xem [AGENTS.md](AGENTS.md) và `AGENTS.md` trong thư mục từng nước.

# Indonesia – các điểm cần chủ dự án quyết định

Cập nhật liên tục. Mỗi điểm gồm các phương án, đánh đổi và phương án đề xuất. Trả lời theo số, ví dụ "1a, 2b".
Đã chốt ngày 07/11/2026 (không hỏi lại):
- FO: dùng KSEI 30/12/2025, phần còn thiếu lấy từ BCTN 2025.
- Quỹ, ETF và DIRE: loại khỏi phạm vi.
- Chức danh: Komisaris → Board, Direksi → Executive, DPS → Other_Manager.
- BCTN: website công ty trước, phần thiếu tải tay từ IDX.

Chi tiết các quyết định đã chốt nằm trong `AGENTS.md`.

---

## 1. Năm mã Bloomberg không có trong danh mục chứng khoán KSEI năm 2025 – ĐÃ CHỐT 08/11/2026: phương án a

Kiểm tra theo danh mục chứng khoán ("Master File Efek") của KSEI ngày 02/01/2025 và 30/12/2025. Danh mục này ghi cả mã bị tạm ngừng giao dịch, ví dụ SRIL (Sritex) vẫn có tên. Đã có 953 công ty nằm trong danh mục, trong đó CNTB có toàn bộ cổ phần ở dạng giấy nhưng vẫn ACTIVE. Năm mã sau không có tên ở cả hai ngày:

| Mã | Ghi chú |
|---|---|
| 1789071D "SILOAM GLENEAGLE" | Dòng mã cũ của Bloomberg (đuôi "D" = đã hủy). SILO (Siloam) có dòng riêng. Không có trong bất kỳ file KSEI nào |
| ITTG Leo Investments, FINN First Indo American Leasing | Bloomberg không có giá. Đã vắng trong danh mục từ 02/01/2024. KSEI vẫn còn lưu ký cổ phần |
| PRIM Royal Prima, AMAN Makmur Berkah Amanda | Như trên, nhưng Bloomberg vẫn có giá (83 và 202 rupiah). Có thể là giá cuối cùng trước khi bị đình chỉ hoặc hủy niêm yết |

- **a. (đề xuất)** Loại cả 5 mã khỏi phạm vi (`In_Scope = 0`, lý do `NOT_LISTED_IN_2025`), giữ dòng.
- **b.** Loại ngay 1789071D, ITTG và FINN. Với PRIM và AMAN, anh/chị mở idx.co.id trên trình duyệt (script bị chặn) để xem ngày hủy niêm yết; nếu hủy trong năm 2025 thì giữ trong phạm vi. Mất khoảng 5 phút.

## 2. Công ty có năm tài chính không kết thúc ngày 31/12 – ĐÃ CHỐT 08/11/2026: phương án a

Theo dữ liệu tham khảo của stockanalysis.com (còn phải xác nhận lại trên BCTN), 899 công ty kết thúc năm tài chính vào tháng 12. Chỉ có 6 công ty khác:
- IKBI, HEXA: tháng 4 đến tháng 3.
- RIGS, CANI, AMOR: tháng 7 đến tháng 6.
- AMIN: tháng 2 đến tháng 1.

Còn 53 công ty chưa rõ.

- **a. (đề xuất)** Tính theo **năm dương lịch 2025**, giống lựa chọn của anh/chị cho Malaysia: giữ chức vào bất kỳ lúc nào từ 01/01 đến 31/12/2025. Khi cần, đọc cả hai BCTN có phần trùng với năm 2025. Cách này nhất quán giữa các nước, và chỉ tốn thêm cho khoảng 6 công ty.
- **b.** Tính theo năm tài chính kết thúc trong 2025 (mặc định chung "FY"): mỗi công ty chỉ cần một BCTN, nhưng khoảng thời gian lệch vài tháng so với các công ty khác.

FO vẫn lấy theo KSEI ngày 30/12/2025 như đã chốt. Riêng 4 công ty thuộc nhóm "kẹp quanh 50%" (IKBI, HEXA, AMIN, AMOR), bảng cổ đông trong BCTN sẽ có ngày cuối năm tài chính của công ty; tôi sẽ ghi rõ ngày đó.

## 3. Lấy phần BCTN 2025 mà script không tải được – ĐÃ CHỐT 08/11/2026: phương án a

Kết quả kiểm tra ngày 08/11/2026 trên 958 công ty (`data/ar_availability.csv`):
- **404 công ty tự động lấy được** từ website. Một số ít link thực ra là BCTN 2024 đăng trong năm 2025 (ví dụ TAMA, BYAN, PEHA); khi tải về, script sẽ kiểm tra trang đầu để loại các trường hợp này.
- **554 công ty không tự động được**:
  - 358 công ty: đọc được website nhưng không thấy file BCTN 2025.
  - 66 công ty: website chỉ hiển thị bằng JavaScript.
  - 62 công ty: website không phản hồi.
  - 54 công ty: website chặn script.
  - 14 công ty còn lại: không có website, chỉ có link về IDX, hoặc lỗi script.
- Tỷ lệ tự động tương tự giữa công ty lớn và nhỏ (48% trong top 200 vốn hóa, 44% với phần còn lại).
- Trong 859 công ty cần BCTN (530 LOCAL + 329 phải dùng BCTN để xác định FO), có 360 công ty tự động được.

Về nguyên tắc, mọi BCTN đều có trên IDX (bắt buộc nộp, hạn 30/04/2026) và mở được bằng trình duyệt.

- **a. (đề xuất)** Chạy thêm một vòng script cho 554 công ty này, không tốn công tay: đọc sâu hơn (60 trang thay vì 30), chạy lại các site lỗi, và dò thêm các đường dẫn hay gặp như `/hubungan-investor`, `/laporan-tahunan`. Phần còn lại, tôi lập danh sách theo thứ tự ưu tiên (các công ty phải xác định FO trước, rồi đến LOCAL) để anh/chị tải tay trên IDX. Ước tính 1–2 phút mỗi file.
- **b.** Không chạy thêm vòng nào, lập ngay danh sách tải tay khoảng 500 file. Nhanh hơn với tôi nhưng tốn công tay nhiều hơn.
- **c.** Chỉ làm với khoảng 400 công ty tự động lấy được. Mẫu sẽ bị lệch: thiếu khoảng một nửa số công ty và không đại diện cho toàn sàn.

## 4. Có chạy pilot 30 công ty trước khi tải hết không – ĐÃ CHỐT 08/11/2026: phương án a

- **a. (đề xuất)** Có. Chọn 30 công ty phân tầng (LOCAL / phải xác định FO; lớn / nhỏ; ngân hàng; có/không có người nước ngoài). Trong đó khoảng 8 công ty lấy từ danh sách tải tay, để thử cả quy trình đó. Mục tiêu là kiểm tra cách đọc bảng cổ đông và quốc tịch trên BCTN Indonesia trước khi làm cho 859 công ty.
- **b.** Không. Tải hết rồi chạy luôn cho toàn bộ: nhanh hơn, nhưng lỗi định dạng sẽ phát hiện muộn.

<!-- Thêm các điểm mới bên dưới -->


## 5. FO dùng để xác định nhóm "sát ngưỡng" (FM có FO ≤ 55%) – ĐÃ CHỐT 08/11/2026: không có nhóm sát ngưỡng

Trả lời của chủ dự án: "công ty trên 50% không phải tìm quản lý nước ngoài". Với Indonesia, mọi công ty FOREIGN_MAJORITY (FO > 50%) đều không tìm người quản lý, kể cả khi FO trong khoảng 50–55%. Quy tắc của Việt Nam và Philippines giữ nguyên.

Các phương án đã đưa ra:

Theo quy tắc chung, với công ty FOREIGN_MAJORITY có FO ≤ 55%, vẫn phải tìm người quản lý nước ngoài. File KSEI chỉ cho một **khoảng** FO, không cho một con số. Hiện có 8 công ty FM có cận dưới của KSEI ≤ 55%. Ví dụ BNBR: KSEI cho khoảng 52,7–83,1%, còn bảng cổ đông trong BCTN ghi 83,07%.

- **a. (đề xuất)** Nếu BCTN có bảng cổ đông nội/ngoại thì dùng số trong BCTN. Chỉ khi BCTN không có bảng mới dùng cận dưới của KSEI. Cách này khớp với quyết định ngày 0 ("KSEI, phần thiếu lấy từ BCTN"). BNBR sẽ không còn là "sát ngưỡng".
- **b.** Luôn dùng cận dưới của KSEI. Cách này tìm thêm vài công ty (chi phí nhỏ), nhưng sẽ gắn nhãn "sát ngưỡng" cho công ty thực ra có FO trên 80%.

## 6. Có cần đọc tay từng trang bảng cổ đông của 329 công ty "kẹp quanh 50%" không – ĐÃ CHỐT 08/11/2026: phương án a

Thử trên pilot: script đọc được FO từ BCTN cho cả 9/9 công ty "kẹp quanh 50%".
- 6 công ty đọc được bảng nội/ngoại có tổng bằng 100%.
- 3 công ty còn lại xác định qua cổ đông lớn ≥ 5% theo loại pháp nhân: PT/Persero/Nhà nước là trong nước, Ltd/Pte/Inc là nước ngoài.
- Cả 9 giá trị đều nằm trong khoảng KSEI.

Bước kiểm tra tự động như vậy là khá chặt.

- **a. (đề xuất)** Tự động chấp nhận khi đủ 4 điều kiện:
  - bảng nội/ngoại có tổng bằng 100% (±1);
  - FO nằm trong khoảng KSEI;
  - FO cách 50% ít nhất 5 điểm;
  - nếu bảng có hai cột (2024 và 2025), cả hai cột cùng phía so với 50%.

  Vẫn ghi trang và các dòng đọc được làm nguồn. Mọi trường hợp khác (gần 50%, xác định qua cổ đông lớn, bảng lệch) đều đọc tay và trích nguyên văn. Ước tính 60–70% được chấp nhận tự động.
- **b.** Đọc tay trang của tất cả 329 công ty. Chắc chắn nhất, nhưng tốn khoảng 10–15 giờ.
- **c.** Chấp nhận mọi kết quả có tổng bằng 100% và nằm trong khoảng KSEI, không xét khoảng cách tới 50%. Nhanh nhất, nhưng rủi ro ở các công ty sát 50%.

## 7. Có cho script tải BCTN từ IDX qua địa chỉ www.idx.id không – ĐÃ CHỐT 08/11/2026: phương án a (cho phép, tải chậm)

Ngày 08/11/2026: `idx.co.id` chặn script (403) và tôi không lách qua. Tuy nhiên, cùng trang web IDX còn mở ở địa chỉ `www.idx.id`, và địa chỉ này trả lời script bình thường (200), không có lớp chặn bot. Trang tại `www.idx.id` khai báo địa chỉ chính thức (canonical) là idx.co.id. Qua đó tôi đã xác nhận trang "Laporan Keuangan dan Tahunan" có bộ lọc năm, kỳ (Tahunan) và mã công ty. Tôi chưa thử tải file nào.

- **a. (đề xuất)** Cho phép. Script tải 489 BCTN còn thiếu từ `www.idx.id`, chậm (vài giây một file, một luồng), ghi URL, thời điểm tải và SHA-256 cho từng file, đồng thời kiểm tra trang đầu như với file từ website công ty. Nếu `www.idx.id` bắt đầu chặn hoặc hiện trang thử thách, dừng ngay và chuyển sang tải tay. Tiết kiệm khoảng 8–16 giờ tải tay. Rủi ro: IDX có thể không muốn bị tải tự động, vì idx.co.id đang chặn.
- **b.** Không. Giữ cách tải tay trên trình duyệt như đã chốt.

## 8. FO của 181 công ty "kẹp quanh 50%" mà quy tắc 6a chưa tự chấp nhận được – ĐÃ CHỐT 09/11/2026: phương án a

Sau khi chạy toàn bộ: 125 công ty được tự chấp nhận theo 6a. Còn 181 công ty phải đọc tay, vì bảng không tổng đủ 100%, hoặc không có bảng nội/ngoại, hoặc chỉ có danh sách cổ đông lớn. Trong 181 công ty này:
- 52 công ty có các pháp nhân Indonesia (PT, Persero, Nhà nước) cùng nắm trên 55%, giá trị nằm trong khoảng KSEI → LOCAL rõ ràng.
- 5 công ty có pháp nhân nước ngoài (Ltd, Pte, Inc, Sdn Bhd) nắm trên 55% → FOREIGN_MAJORITY rõ ràng.
- 124 công ty còn lại cần đọc trang.

- **a. (đề xuất)** Tự chấp nhận thêm 57 công ty theo cổ đông lớn, với điều kiện: một phía nắm trên 55% và nằm trong khoảng KSEI. Vẫn ghi trang và các dòng đọc được. Với 124 công ty còn lại, tôi cải thiện script thêm một vòng rồi đọc tay phần còn sót. Ước tính 3–5 giờ.
- **b.** Đọc tay cả 181 công ty. Ước tính 6–9 giờ.
- **c.** Chỉ tự chấp nhận 57 công ty; 124 công ty còn lại để REVIEW (cờ để trống) và ghi rõ trong báo cáo.

## 9. Người thôi chức trong năm 2025 – ĐÃ CHỐT 09/11/2026: phương án a

Người thôi chức trong năm 2025 không có trang lý lịch trong BCTN 2025 (bài học từ MBMA). Script tìm thấy 483 lượt nhắc đến người thôi chức ở 154 công ty LOCAL. Trong đó có 346 tên mà BCTN 2025 không ghi quốc tịch ở gần. Nếu bỏ qua, có thể sót người nước ngoài ở các công ty hiện được kết luận NONE_FOUND.

- **a. (đề xuất)** Script tải BCTN 2024 từ IDX (cùng cách đã được duyệt ở câu 7) cho các công ty này, rồi tìm nhãn quốc tịch gần tên những người đã thôi chức. Ai được ghi quốc tịch nước ngoài thì tôi đọc tay và ghi bản ghi; nguồn ghi là BCTN 2024, kèm ngày thôi chức lấy từ BCTN 2025. Ai không có thông tin thì ghi vào phần hạn chế. Tốn thêm khoảng 150 file tải và vài giờ chạy máy, ít việc tay.
- **b.** Không kiểm tra người thôi chức; ghi rõ hạn chế này trong methodology. Nhanh hơn, nhưng cờ NONE_FOUND có thể bị thiếu.

<!-- Ghi chú làm việc (không phải câu hỏi): EAST – Khalid Bin Omar Abdat, Presiden Direktur, Warga Negara Singapura (AR 2025 p16), nắm 43,74%; FO của EAST chưa chốt (nhóm sáng lập 61,52%, quốc tịch các thành viên khác chưa rõ). Nếu EAST là LOCAL thì phải ghi ông. -->

## 10. 13 người thôi chức trong năm 2025, tên trông như người nước ngoài nhưng không nguồn nào ghi quốc tịch – ĐÃ CHỐT 10/11/2026: phương án a

Ví dụ: Lim Sung Pil (ACRO), Grant Roy Lutz (AISA), Chiew Sin Cheok (AUTO), Subhas Chandra Lakhotia (BEER), Sami Veikko Tapio Miettinen (MDLN), Lee Joo Hwan (NOBU), Daisuke Morishita (SCCO). Danh sách đủ nằm trong sheet Open_Items của workbook. Tôi đã tìm trong cả BCTN 2025 lẫn BCTN 2024 mà không thấy nhãn quốc tịch.

- **a. (đề xuất)** Tìm thêm trên web/tin tức cho 13 người này, ước tính khoảng 1 giờ. Ai có nguồn thì ghi bản ghi kèm URL và trích dẫn. Ai vẫn không có nguồn thì chỉ suy luận khi tên cho thấy rõ một nước (giống quy tắc đã dùng cho Philippines), ghi `INFERRED_WEAK` và tính vào cờ. Còn lại để vào phần hạn chế.
- **b.** Không tìm thêm và không suy luận: để cả 13 người vào phần hạn chế. Ở Indonesia có nhiều người gốc Hoa hoặc gốc Ấn mang tên nước ngoài nhưng quốc tịch Indonesia, nên suy luận theo tên có thể sai.
- **c.** Suy luận ngay theo tên cho cả 13 người (`INFERRED_WEAK`), không tìm thêm.

## 11. FO của 49 công ty còn REVIEW – báo cáo tháng của BAE tháng 12/2025 – ĐÃ CHỐT 10/11/2026: phương án a

Sau khi đọc tay ngày 10/11, còn 49 công ty chưa chốt FO. Lý do chính:
- Cổ đông lớn là cá nhân, BCTN không ghi quốc tịch. Ví dụ: Lisa Muchtar nắm 56% CSMI, Hetty Soetikno nắm 66% MDLA. Ngoài ra còn ASPR, NZIA, OBAT, RGAS, TYRE, WIIM, RUNS, KIJA.
- Không có bảng phân loại trong nước/nước ngoài: BISI, INPC, MARK.
- Số liệu mâu thuẫn: CTTH, BCTN ghi nước ngoài 57%, KSEI cho tối đa 52%.
- Số liệu cũ: AREA, BCTN 2025 chỉ có cơ cấu năm 2023.
- 16 công ty chưa có BCTN.

Nguồn mới tìm được là báo cáo tháng "Laporan Bulanan Registrasi Pemegang Efek" mà BAE nộp lên IDX. Bản tháng 12/2025 được nộp vào tháng 1/2026. Báo cáo có:
- Bảng "Komposisi Kepemilikan Saham" tại 31/12/2025. Bảng tách cổ phiếu chứng chỉ (nằm ngoài KSEI, đây chính là khoảng trống trong biên KSEI) và cổ phiếu lưu ký KSEI; mỗi phần lại tách trong nước/nước ngoài.
- Mẫu X.H.1-1, danh sách cổ đông ≥ 5%, có cột "Status A/I" (Asing/Indonesia).

Thử với CSMI: Lisa Muchtar có Status "I", phần nước ngoài 0,47% → LOCAL.

Về cách truy cập: API thông báo của www.idx.id trả về đường dẫn file trên idx.co.id (tên miền chặn script, tôi không lách). Cùng file đó có sẵn ở đường dẫn tương ứng trên www.idx.id (`/Portals/0/StaticData/...`). Đây đúng là thư mục mà các BCTN đã tải theo câu 7 cũng nằm trong. Phần lớn báo cáo là bản scan, nên phải đọc ảnh trang.

- **a. (đề xuất)** Dùng báo cáo BAE tháng 12/2025 cho 49 công ty REVIEW. Tải chậm từ www.idx.id (1 luồng, nghỉ 3 giây, dừng ngay nếu bị chặn). Đọc ảnh bảng thành phần và cột A/I, rồi ghi trang và số liệu vào `Ownership_AR_Manual`, phương pháp `BAE_REGISTER_202512`. Ước tính 1,5–2,5 giờ. Đây là nguồn chính thức tại đúng ngày 31/12/2025, giải quyết được cả các ca mâu thuẫn và ca số liệu cũ.
- **b.** Quy tắc tên như Philippines: cá nhân mang tên Indonesia được coi là người Indonesia. Nhanh, nhưng chỉ giải quyết khoảng 10 công ty. Ở Indonesia có nhiều tên gốc Hoa mà không rõ là người Indonesia hay Singapore/Malaysia (ví dụ Tan Kian Gee ở RUNS).
- **c.** Giữ REVIEW (cờ để trống) cho 49 công ty và ghi vào phần hạn chế.

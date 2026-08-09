# TỰ-SỬA — TIẾN TRÌNH & LỘ TRÌNH MỞ RỘNG (vòng tự-tìm-lỗi/tự-vá của GIAO)

> Trung thực: bắt đầu HẸP (rule-based), mở rộng dần tới tự-sửa tổng-quát (cắm-LLM). Mỗi Stage có
> tiêu-chí ĐO-ĐƯỢC bằng harness. Cổng CDFL xuyên suốt: chỉ NHẬN bản vá nếu test chuyển tối→sáng
> VÀ không phá test khác. Người dùng sẽ mở ra kiểm như Kali — nên mỗi Stage phải THẬT, đo-được.

## Khung TIẾN TRÌNH (bất biến qua mọi Stage)
`chạy-test → ĐỊNH-VỊ-lỗi → SINH-bản-vá → ÁP → KIỂM-toàn-bộ → CỔNG-CDFL (nhận/hoàn-tác)`
- Khác nhau giữa các Stage = **bộ SINH-bản-vá** (từ rule hẹp → LLM tổng-quát) + **ĐỊNH-VỊ** (từ oracle → fault-localization).

## Các STAGE (đo bằng: lớp-lỗi tự-sửa được / không phá regression)
| Stage | Năng lực SINH-vá | Lớp lỗi sửa được | Trạng thái |
|---|---|---|---|
| **1** | oracle-repair hằng: đọc `expected E got G` → thay literal G→E | sai HẰNG-SỐ trả về | ✅ XONG (`vong_tu_sua.py`, audit) |
| **2** | + mutation TOÁN-TỬ (`+,-,*,//`) và SO-SÁNH (`==,<,>…`) | sai TOÁN-TỬ, off-by-operator | ✅ XONG (vá `x+x`→`x*x`, CDFL loại vá sai) |
| **3** | + OFF-BY-ONE (±1 hằng-số) + boundary | sai-biên, lệch-±1 | ✅ XONG (vá i>4→i>5, CDFL loại 15 vá sai) |
| **4** | ĐỊNH-VỊ lỗi: spectrum (tệp ở test-fail, không ở test-pass) | lỗi đa-tệp, không cần chỉ đích | ✅ XONG (định-vị _lb→vá, không đụng _la) |
| **5** | CẮM LLM: `tác_tử_vá(ngữ-cảnh, lỗi)` qua host-capability → vá tổng-quát | lỗi LOGIC tổng-quát | ⏳ (cần API-key host) |
| **6** | CHỦ ĐỘNG: tự sinh test (property-based) → tìm lỗi tiềm-ẩn → vá | lỗi CHƯA-lộ | ⏳ |

## Tiêu-chí AN-TOÀN (mọi Stage)
- **Regression-safe:** chỉ nhận vá khi chạy LẠI toàn-bộ harness liên-quan vẫn sáng (không chỉ test mục-tiêu).
- **CDFL no-đốm-tối:** vá "tin là đúng nhưng test tối" → HOÀN-TÁC (không giữ ảo-tưởng).
- **Giới-hạn KHAI BÁO:** mỗi Stage ghi rõ lớp-lỗi NGOÀI tầm → báo "cần Stage cao hơn / cần LLM", KHÔNG vá bừa.

## Chỗ-cắm-LLM (Stage 5 — thật khi có capability)
`sinh_va(src, lỗi)` hiện rule-based. Thay bằng: gọi LLM (host cấp `--cho-ai`) với ngữ-cảnh
(tệp + test + lỗi + harness) → nhận diff → vẫn qua CỔNG CDFL. Sandbox hiện KHÔNG có API → dùng rule-based;
khi host cấp, đổi 1 hàm là lên tổng-quát.

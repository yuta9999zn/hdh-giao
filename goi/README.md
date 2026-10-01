# goi/ — gói nguồn của hệ sinh thái HĐH-GIAO

Mỗi thư mục là một gói. Ba tệp:

| tệp | nội dung |
|---|---|
| `GOI` | `tên` · `phiên` (1.0 / 1.0.2) · `nhóm` · `mô_tả` · `giấy_phép` (SPDX) · `phụ_thuộc` (a, b>=1.0, c/d) · `năng_lực` (mạng, gốc, đĩa, xoá, ghi) · `duy_trì` |
| `than` | kịch bản vỏ HĐH-GIAO, cài vào `/lệnh/<tên>` — có `$1 $2 $*`, ống `\|`, `>`, `&&` |
| `kiem` | `người: an\|gốc` · `chạy: <dòng>` (nhiều dòng được) · `chứa: <chữ>` · `không_chứa: <chữ>` |

Làm gói mới: `sh goi.sh moi <tên> <nhóm> <mô tả…>` → sửa `than` + `kiem` → `sh goi.sh kiem <tên>` →
`sh goi.sh thu <tên>`. Chính sách nhận công cụ: `../LO_TRINH_HE_SINH_THAI.md`. Nhóm: an-ninh/kiểm-toán ·
an-ninh/giám-sát · an-ninh/điều-tra · hệ-thống · tệp · văn-bản · phát-triển · khoa-học.

Công cụ AN NINH chỉ soi/đọc/báo cáo trên CHÍNH máy này; việc sửa (xoá/đĩa/mạng) là gói riêng ngoài nhóm
an-ninh và đi qua cổng người duyệt của HĐH (xem gói `dọn_nhà`: `xoá` chờ `duyệt`).

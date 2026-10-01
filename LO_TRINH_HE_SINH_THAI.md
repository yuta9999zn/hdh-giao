# Lộ trình: hệ sinh thái HĐH-GIAO (học Kali Linux)

Kali không mạnh vì nhân Linux — nó mạnh vì **hệ sinh thái**: hàng trăm công cụ chia nhóm, siêu-gói
`kali-tools-*`, quy trình đóng gói có kiểm tra, kho ký số, ảnh cài đặt cho nhiều nền, tài liệu và cộng
đồng. HĐH-GIAO đã có phần lõi của `apt` (cài/gỡ/nâng/lùi, phụ thuộc có phiên bản, mục lục ký kép, gói tự
khai năng lực). Lộ trình này dựng phần còn lại.

**Trọng tâm** (chốt 2026-10-01): **an ninh phòng thủ** + **hệ sinh thái chung**. Công cụ an ninh ở đây
soi, kiểm toán, giám sát, điều tra **chính máy mình** — không có công cụ tấn công máy người khác.

## Chính sách nhận công cụ vào kho (học Kali "tool policy", chặt hơn)

1. **Gói là dữ liệu**, không có script chạy lúc cài (khác `postinst` chạy root của apt).
2. **Tự khai năng lực** (`xoá`, `mạng`, `đĩa`, `gốc`…). `sh goi.sh kiem` **suy năng lực từ thân gói**: dùng
   lệnh cần năng lực mà không khai ⇒ RỚT; khai thừa ⇒ cảnh báo. Năng lực nhạy cảm ⇒ người dùng phải đồng ý.
3. **Phòng thủ, trên máy mình**: công cụ an ninh chỉ đọc/soi/báo cáo. Việc sửa chữa (xoá, đổi quyền) phải
   là gói riêng, khai năng lực, và đi qua cổng người duyệt của HĐH.
4. **Có kiểm thử**: mỗi gói có tệp `kiem` — `sh goi.sh thu` cài gói vào một HĐH sạch qua ĐÚNG đường cài thật
   (kiểm chữ ký kép → kiểm băm → kéo phụ thuộc) rồi chạy và đối chiếu đầu ra. Không có kiểm thử ⇒ không vào kho.
5. **Ký kép** ML-DSA-65 + Ed25519 cho mục lục (v0.42). Khoá riêng nằm ngoài HĐH.
6. **Giấy phép** SPDX bắt buộc trong manifest.

## Mốc 1 — Bộ công cụ làm gói + CI + bộ gói đầu tiên — ✅ 2026-10-01

Bộ công cụ **viết bằng GIAO** (`goi.giao`), chạy trên GVM-64; `goi.sh` chỉ làm vào/ra tệp (máy không thấy
thư mục). Không Python.

```
sh goi.sh liet                         # liệt kê theo nhóm + siêu-gói
sh goi.sh moi <tên> <nhóm> <mô tả…>    # tạo khung goi/<tên>/{GOI, than, kiem}
sh goi.sh kiem [tên…]                  # lint: manifest · phụ thuộc + vòng · SUY NĂNG LỰC từ thân · chính sách
sh goi.sh thu [tên…]                   # khởi HĐH SẠCH trong máy, cài qua đường thật, chạy, đối chiếu
sh goi.sh khoa                         # cặp khoá kép của kho (.khoa/kho_goi/, không commit)
sh goi.sh dung                         # dựng kho ký kép ở kho_dung/ (mục_lục · chữ_ký · khoá_công · gói/)
sh kiem_goi.sh                         # nghiệm thu bộ công cụ (trong CI)
```

| việc | trạng thái |
|---|---|
| Định dạng gói nguồn `goi/<tên>/{GOI, than, kiem}` | ✅ |
| `goi.giao`: `moi` · `kiem` · `thu` · `khoa` · `dung` · `liet` — GIAO trên GVM-64 | ✅ |
| Nhóm kiểu menu Kali + siêu-gói `bộ_*` sinh từ nhóm (`bộ_an_ninh` gom mọi nhóm an ninh) | ✅ |
| CI: `kiem_goi.sh` (15/15: kho thật + 10 kiểu gói xấu + khung mới) | ✅ |
| 18 gói đầu tiên: 11 an ninh phòng thủ (kiểm toán 6 · giám sát 3 · điều tra 2) + 7 chung | ✅ |
| Hai lỗi vỏ HĐH do `goi.giao thu` tìm ra (thiếu đối số làm sập vỏ · `&&` không dừng) — đã sửa | ✅ |

## Mốc 2 — Nhiều công cụ (20–30 công cụ thật)

| việc | trạng thái |
|---|---|
| Kiểm toán cấu hình, giám sát đăng nhập, toàn vẹn tệp lệnh, điều tra sự cố | ⬜ |
| Tiện ích chung: tệp, văn bản, phát triển (dịch/kiểm GIAO), khoa học/lượng tử | ⬜ |
| Công cụ là chương trình GIAO dịch sẵn (`#!mã-máy`), không chỉ kịch bản vỏ — `dịch` cần năng lực `máy` của HĐH | ⬜ |

## Mốc 3 — Ảnh HĐH + tài liệu

| việc | trạng thái |
|---|---|
| Bản phát hành tải về chạy được: GVM-64 + bộ gói cơ bản + kho ký kép | ⬜ |
| Trang tài liệu (công cụ theo nhóm, cách viết gói, chính sách) sinh từ manifest | ⬜ |
| Kênh phát hành (lăn / ổn định), mirror | ⬜ |

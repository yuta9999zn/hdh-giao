# Lộ trình: HĐH-GIAO dùng được máy lượng tử và an toàn trước máy lượng tử

HĐH-GIAO **không** trở thành máy lượng tử: không hệ điều hành nào chạy trên qubit, kể cả ở IBM hay
Google. Máy lượng tử là **bộ tăng tốc** (như GPU cho CPU). Hai hướng có giá trị thật:

1. **Biết dùng máy lượng tử:** HĐH điều phối việc lượng tử (dịch mạch, chọn nơi chạy, gửi, nhận kết
   quả) và đưa kết quả đo thẳng vào ngữ nghĩa ba trị (trước khi đo là `ẩn`, kết quả là `tri` có γ).
2. **An toàn trước máy lượng tử:** mật mã hậu lượng tử cho chữ ký và trao đổi khoá; mật khẩu dùng hàm
   băm tốn bộ nhớ đã được thẩm định; nguồn ngẫu nhiên tốt.

Nguyên tắc xuyên suốt: **không tự viết mật mã** (biên dịch thư viện đã thẩm định sang WASM); GVM-64
**không có mạng** (phần mạng nằm ở một tiến trình môi giới ngoài hộp cát); mọi việc bất khả hồi là
**cần người duyệt**; dự đoán **niêm phong trước, chấm sau**.

```
 chương trình GIAO ──giaoc64.giao (tự thân)──► .g64 ──► GVM-64 (WASM, hộp cát: stdin/stdout, đồng hồ*, random_get)
        │                                                  │   ├─ lib_lượng_tử.giao: mô phỏng ≤ 26 qubit, gộp cổng, SIMD
        │                                                  │   └─ argon2.wasm (--preload): Argon2 tham chiếu C
        │                                                  ▼
        └──────────────► moi_gioi_luong_tu.py (NGOÀI hộp cát, nơi DUY NHẤT có mạng)
                           cần_người_duyệt → niêm phong → IBM Quantum (SamplerV2) → chấm XEB/γ trên GVM-64
```

Trạng thái ghi theo ngày; ✅ xong và có kiểm · 🟡 làm một phần · ⬜ chưa làm.

## Giai đoạn 1 — Nền an toàn

| việc | trạng thái | ở đâu / kiểm bằng gì |
|---|---|---|
| `random_get` vào danh sách hàm WASI của GVM-64 | ✅ 2026-09-30 | builtin `ngẫu_hệ()` (giao.py: `secrets`); `GVM64.md` › An toàn |
| Muối lấy từ nguồn ngẫu nhiên HĐH, không từ hằng số/đồng hồ | ✅ 2026-09-30 | `muối_a2_hệ()` 16 byte; `kiem_muoi_he.giao`, `kiem_argon2.giao` ⑤ |
| Băm lại mật khẩu bị lỗi "16 muối" | ✅ 2026-09-30 | `xác_thực` băm lại khi đăng nhập đúng; `bóng_yếu()` liệt kê người phải buộc đặt lại |
| Ghim SHA-256 của module Argon2, kiểm trước mỗi lần nạp | ✅ 2026-09-30 | `wasm/argon2.sha256` (bản dựng tái lập được); `kiem_ghim_argon2.py` |
| Mật khẩu dùng **Argon2id** (mã tham chiếu, không tự viết) | ✅ 2026-09-30 | `ben_ngoai/argon2` → wasi-sdk → `wasm/argon2.wasm`; 3 vector RFC 9106 khớp (`kiem_argon2.giao`); `$g1/g2/g3$` băm lại khi đăng nhập |
| Hàm `ngẫu_nhiên_an_toàn(n)` trả n byte | ⬜ | hiện có `ngẫu_hệ()` (31 bit/lần); bọc thành n byte là việc nhỏ |

## Giai đoạn 2 — Mật mã hậu lượng tử (cho chữ ký và trao đổi khoá, KHÔNG cho mật khẩu)

| việc | trạng thái | ghi chú |
|---|---|---|
| Ký các mục của sổ niêm phong bằng ML-DSA + Ed25519 (ký kép) | ✅ 2026-09-30 | `niem_phong.py` + `ky_kep.py` → `wasm/ky_lenh.wasm`; `kiem_ky_kep.py` 17/17 |
| Ký bản cập nhật HĐH bằng ML-DSA + Ed25519 | ⬜ | |
| Kết nối mạng (môi giới, MCP qua mạng) dùng TLS lai X25519 + ML-KEM | ⬜ | MCP hiện chạy qua stdio cục bộ; ảnh hưởng chính là môi giới gọi IBM |
| Nguồn: biên dịch **mldsa-native v2.0.0** (ML-DSA-65) + **Monocypher 4.0.3** (Ed25519) sang WASM bằng wasi-sdk | ✅ 2026-10-01 | `wasm/dung_ky.sh`, ghim `wasm/ky.sha256`; thay PQClean (đã lưu trữ) — so chéo 40/40 trùng từng byte |
| Vân tay khoá sổ ghim trong kho, độc lập với `.khoa/` | ✅ 2026-10-01 | `khoa_niem_phong.ghim`; tráo khoá / mất khoá ⇒ từ chối, không tự tạo khoá mới |
| Kiểm bằng vector chính thức | ✅ 2026-09-30 | ML-DSA-65: NIST ACVP keyGen 25 · sigGen 15 · sigVer 15; Ed25519: RFC 8032 §7.1 (5) + ACVP sigVer (5) |

## Giai đoạn 3 — Tác vụ lượng tử trong HĐH

| việc | trạng thái | ghi chú |
|---|---|---|
| Mạch → OpenQASM 2/3, gộp cổng | ✅ | `lib_lượng_tử.giao` (`sang_qasm`, `sang_qasm3`, `hợp_nhất_cổng`) |
| Kết quả đo là `tri` có γ; trước khi đo là `ẩn` | ✅ | `tạo_tri`, `chấm_mẫu` |
| Bộ mô phỏng nội bộ ≤ 26 qubit, khớp Aer tới 1e-16 | ✅ | GVM-64 + SIMD; `bench_gvm64.py` |
| Cú pháp khối `lượng_tử { … }` | ⬜ | chỉ là lớp vỏ trên thư viện; cần sửa bộ phân tích ở CẢ `giao.py` lẫn `giaoc64.giao` |
| Đối tượng tác vụ (mạch, shots, nơi chạy, trạng thái `ẩn` khi đang chờ) | ⬜ | |
| Quy tắc chọn nơi chạy: ≤ 26 qubit → GVM-64, lớn hơn → đám mây | ⬜ | |

## Giai đoạn 4 — Kết nối máy lượng tử thật

| việc | trạng thái | ghi chú |
|---|---|---|
| Tiến trình môi giới ngoài hộp cát, nơi duy nhất gọi API đám mây | ✅ 2026-09-30 | `moi_gioi_luong_tu.py` |
| Gửi mạch = **cần người duyệt** | ✅ | mặc định chạy khô (mã 2); chỉ gửi với `--duyệt` |
| Niêm phong dự đoán trước khi gửi, chấm bằng γ/XEB sau | ✅ | `niem_phong.py`; chấm tính trên GVM-64; `kiem_moi_gioi.py` |
| Chạy thật trên IBM Quantum, ghi số liệu nhiễu thật | ⬜ | cần token của chủ dự án (`QISKIT_IBM_TOKEN`) |
| Nguồn ngẫu nhiên lượng tử (QRNG trên đám mây) trộn thêm vào `ngẫu_hệ` | ⬜ | tuỳ chọn; `random_get` của HĐH đã đủ cho muối |

## Việc đang chờ quyết định

- ~~Ngữ nghĩa luật `trôi`~~ — đã chọn (C) "thuần thế giới", làm xong v0.39.0.

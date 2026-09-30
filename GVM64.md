# GVM-64: máy tính toán của GIAO (WebAssembly/WASI, không có Python lúc chạy)

GVM-64 chạy chương trình GIAO **không qua Python lúc chạy**. Trình biên dịch `giaoc64.py` (chạy lúc
dựng) hạ chương trình GIAO xuống bytecode. Máy `wasm/gvm64.wasm` (AssemblyScript → WebAssembly) chạy
bytecode đó dưới **wasmtime**.

```
python giaoc64.py chương_trình.giao                   # → chương_trình.g64 (lúc dựng)
wasmtime run wasm/gvm64.wasm -- [--bước N] [--trần-ds N] [--cho-giờ] < chương_trình.g64
sh wasm/dung_gvm64.sh                                  # dựng lại gvm64.wasm (cần Node để chạy asc)
python kiem_gvm64.py [tệp.giao…]                       # đối chiếu với trình thông dịch, từng ký tự
python bench_gvm64.py --cỡ 20 24 26 [--qiskit <py>]    # đo sức mô phỏng lượng tử
```

## Vì sao là một máy MỚI, không vá GVM 16/32-bit

GVM 16/32-bit gắn với Verilog/FPGA nên được giữ nguyên. Máy đó có ba giới hạn chặn tính toán nặng:
- **Thẻ kiểu nằm ở bit 30**, nên số ≥ 2^30 bị hiểu nhầm thành con trỏ. SHA-256 và LCG đều vướng.
- **Số thực là điểm cố định 4 chữ số**, không đủ cho biên độ lượng tử.
- **RAM 64K ô.**

Ở GVM-64, mỗi ô mang **loại + 64 bit**. Có đủ các loại: ẩn, số nguyên i64, **số lớn tuỳ ý** (tự nâng
khi tràn, như Python), thực f64 IEEE, chuỗi (đếm theo điểm mã), danh sách, bản, hàm/closure, tri,
`mảng` f64 và builtin. Heap có bộ dọn rác incremental.

**Lệnh khối** trên `mảng` là các vòng lặp native: `m_biến_đổi_cặp` (cánh bướm 2×2), `m_nhân_chọn`
(cổng chéo), `m_đổi_chọn` (X/CX/SWAP), `m_tổng_mô2_chọn`, `m_rút`… Chúng giữ thứ tự cộng dồn giống
bản tham chiếu, nên kết quả khớp từng bit.

## An toàn: vì sao là WASI + wasmtime, không phải Node

`gvm64.wasm` **chỉ import 7 hàm WASI**:
- `fd_read`: đọc chương trình từ stdin;
- `fd_write`: ghi stdout/stderr;
- `args_sizes_get`, `args_get`: đọc cờ;
- `clock_time_get`: đồng hồ, chỉ đưa cho chương trình GIAO khi có `--cho-giờ`;
- `random_get`: byte ngẫu nhiên của HĐH cho builtin `ngẫu_hệ()` (muối mật khẩu). Không mở tệp hay
  mạng nên không cần cờ. Lỗi thì máy dừng bằng bẫy, không lặng lẽ trả số đoán được;
- `proc_exit`: thoát.

Máy không thấy thư mục nào, không có mạng, không chạy được tiến trình. Kiểm lại bằng
`WebAssembly.Module.imports`.

- **wasmtime** (Rust, Bytecode Alliance) là vỏ chính. Hộp cát mặc định chặt: không cấp thư mục thì
  không có tệp nào.
- **Node** (`wasm/giao64.mjs`) chỉ là vỏ dự phòng để kiểm, **không phải hộp cát**. Chính Node cảnh báo
  `--allow-wasi` "could invalidate the permission model". Thực tế trên máy này, `node:wasi` đã
  **segfault** trên 3 chương trình, trong khi wasmtime chạy cùng chương trình đó và báo lỗi sạch.
- Năng lực cần tệp, mạng, mmio hay phần cứng (`đọc_tệp`, `tim`/`nhúng` LLM, `mmio`, `máy`,
  `phần_cứng`) **cố ý không có** trên GVM-64. Chương trình dùng chúng sẽ báo lỗi rõ ràng.

## Đã kiểm chứng (`kiem_gvm64.py`, trong `kiem_toan_bo.py`)

Đối chiếu mọi chương trình GIAO trong dự án giữa trình thông dịch và GVM-64, **so stdout từng ký tự**,
với cùng cờ host mà CI dùng:
- **131 khớp · 0 lệch.**
- 12 chương trình cần năng lực host (tệp/mạng/mmio/phần cứng/LLM) hoặc in thời gian đo thật.
- 9 chương trình chưa biên dịch được, vì dùng tầng CDFL `vật/tâm/học/giao/trôi`.

Các lỗi thật tìm và sửa được trong lúc đối chiếu:
- Chuỗi có emoji bị đếm theo UTF-16 → đổi sang đếm theo điểm mã. Vector SHA-256 thứ 4 giờ đúng.
- Thiếu số lớn → thêm số lớn tuỳ ý. `$g1$` mật khẩu, `lib_bit` và `lib_thập_phân` giờ khớp.
- Dùng sai runtime dọn rác (lỗi khi dùng `--use abort` trỏ vào hàm của mình) → chuyển sang
  `--use abort=`, lỗi nội bộ thành bẫy WASM.

## Số đo (máy 20 luồng, RAM 15.6 GB; Qiskit 2.5.2 / Aer 0.17.2; CÙNG mạch QASM do GIAO xuất)

**Đọc bảng cho đúng:** Aer **mặc định chạy đa luồng**. Cột "Aer 1 luồng" là Aer bị ÉP về 1 luồng
(`max_parallel_threads=1`) để so từng lõi với GVM-64 (hiện 1 luồng). So với Aer cấu hình mặc định
thì xem cột "Aer 20 luồng": ở đó GVM-64 **chậm hơn** 3–9 lần sau gộp cổng. Khi trích số, luôn ghi
rõ đang so với cấu hình nào.

| mạch | n | GIAO thông dịch | **GVM-64** | Aer 1 luồng | Aer 20 luồng | Qiskit numpy |
|---|---|---|---|---|---|---|
| QFT | 20 | 23.4 s · 89 MB | **0.39 s · 44 MB** | 0.28 s · 108 MB | 0.07 s | 4.9 s |
| ngẫu nhiên | 20 | 49.7 s · 88 MB | **1.16 s · 44 MB** | 0.12 s · 108 MB | 0.05 s | 5.0 s |
| QFT | 24 | 514 s · 405 MB | **8.8 s · 285 MB** | 17.2 s · 332 MB | 3.8 s | 216 s |
| ngẫu nhiên | 24 | ~24 phút (bản cũ) | **22.7 s · 291 MB** | 13.7 s · 332 MB | 1.05 s | 153 s |
| QFT | 26 | không chạy nổi | **40.4 s · 1065 MB** | 30.5 s · 1100 MB | 13.0 s | (cần ~4.4 GB, không chạy) |
| ngẫu nhiên | 26 | không chạy nổi | **97.0 s · 1060 MB** | 8.5 s · 1100 MB | 4.5 s | — |

**Sau khi gộp cổng (v0.35, `hợp_nhất_cổng` viết bằng GIAO):**

| mạch | n | GVM-64 chưa gộp | **GVM-64 gộp cổng** | Aer 1 luồng | Aer 20 luồng |
|---|---|---|---|---|---|
| ngẫu nhiên | 20 | 1.16 s | **0.28 s** | 0.12 s | 0.05 s |
| ngẫu nhiên | 24 | 22.7 s | **4.5 s** | 13.7 s | 1.05 s |
| ngẫu nhiên | 26 | 97 s | **19.6 s** | 8.5 s | 4.5 s |
| QFT | 26 | 40.4 s | **39.1 s** | 30.5 s | 13.0 s |

- **Độ đúng:** mọi biên độ khớp Aer tới **10⁻¹⁶ – 10⁻²⁰**, và ⟨ψ|ψ⟩ = 1.000000000000.
- **QFT:** GVM-64 xấp xỉ Aer ép 1 luồng. Ở 24 qubit nó nhanh hơn Aer ép 1 luồng (8.8 s so với
  17.2 s), nhưng chậm hơn Aer mặc định 20 luồng (3.8 s).
- **RAM** bằng hoặc thấp hơn Aer (16 byte mỗi biên độ).
- **Mạch ngẫu nhiên:** trước khi gộp cổng thì chậm hơn Aer 1 luồng 7–11 lần, vì mỗi cổng duyệt cả
  1 GB trạng thái (giới hạn băng thông bộ nhớ). **Gộp cổng** (v0.35, viết bằng GIAO) đưa về chậm hơn
  **2.3 lần** Aer ép 1 luồng ở 26 qubit, và nhanh hơn Aer ép 1 luồng ở 24 qubit (vẫn chậm hơn Aer
  mặc định đa luồng 4.3 lần). Hai bước tiếp theo: SIMD 128-bit
  của WASM, và đa luồng (WASM threads).

**Mật khẩu:** `kiem_lib_mật_khẩu.giao` trên GVM-64 **không cần nới trần bước** và chạy xong trong
0.69 s. Trình thông dịch chạm trần 5 triệu bước; nới `--bước 200000000` thì mất 8.52 s. Đầu ra trùng
khít.

## Giới hạn

- **wasm32 tối đa 4 GB bộ nhớ**, nên mô phỏng lượng tử tối đa khoảng 27 qubit.
- **Chưa có SIMD, chưa có đa luồng.** Aer 20 luồng nhanh hơn 3–9 lần (sau gộp cổng).
- **Trình biên dịch vẫn viết bằng Python**, nhưng chỉ chạy lúc dựng. Lúc chạy không có Python.
  Tự thân hoá `giaoc64` bằng GIAO rồi chạy chính nó trên GVM-64 là bước sau.
- **Tầng CDFL chưa biên dịch được:** `vật/tâm/học/giao/trôi/khi viên_mãn/de`.
- `log`/`mũ` dùng thư viện toán của AssemblyScript, có thể lệch ở chữ số cuối so với libm của Python.
  Chưa thấy lệch trong đầu ra (in `%.4g`).

# GVM-64: máy tính toán của GIAO (WebAssembly/WASI, không có Python lúc chạy)

GVM-64 chạy chương trình GIAO **không qua Python lúc chạy**. Trình biên dịch `giaoc64.py` (chạy lúc
dựng) hạ chương trình GIAO xuống bytecode. Máy `wasm/gvm64.wasm` (AssemblyScript → WebAssembly) chạy
bytecode đó dưới **wasmtime**.

```
python giaoc64.py chương_trình.giao                   # → chương_trình.g64 (lúc dựng)
wasmtime run --preload argon2=wasm/argon2.wasm wasm/gvm64.wasm -- [--bước N] [--trần-ds N] [--cho-giờ] < chương_trình.g64
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

**Module thứ hai: `argon2.wasm`** (v0.38). Builtin `argon2` gọi 3 hàm (`a2_dat`, `a2_chay`, `a2_lay`)
của một module WASM riêng, dựng từ **mã tham chiếu C của Argon2** (`ben_ngoai/argon2`, không sửa) bằng
wasi-sdk (`sh wasm/dung_argon2.sh`). Module ấy **không import gì cả**, nên nó không thêm quyền nào; nó
chỉ là mã chạy trong cùng hộp cát. Vì vậy mọi lệnh chạy máy giờ có thêm
`--preload argon2=wasm/argon2.wasm`. Trình thông dịch gọi đúng mã ấy qua `wasm/argon2_lenh.wasm` dưới
wasmtime (không cấp thư mục), nên hai máy dùng **một** bản Argon2, không có bản Python nào.

- **wasmtime** (Rust, Bytecode Alliance) là vỏ chính. Hộp cát mặc định chặt: không cấp thư mục thì
  không có tệp nào.
- **Node** (`wasm/giao64.mjs`) chỉ là vỏ dự phòng để kiểm, **không phải hộp cát**. Chính Node cảnh báo
  `--allow-wasi` "could invalidate the permission model". Thực tế trên máy này, `node:wasi` đã
  **segfault** trên 3 chương trình, trong khi wasmtime chạy cùng chương trình đó và báo lỗi sạch.
- Năng lực cần tệp, mạng, mmio hay phần cứng (`đọc_tệp`, `tim`/`nhúng` LLM, `mmio`, `máy`,
  `phần_cứng`) **cố ý không có** trên GVM-64. Chương trình dùng chúng sẽ báo lỗi rõ ràng.

## Tự thân hoá: trình biên dịch viết bằng GIAO (`giaoc64.giao`)

```
sh tu_bien_dich.sh chương_trình.giao > chương_trình.g64     # KHÔNG Python: GIAO dịch GIAO trên GVM-64
python kiem_tu_bien_dich.py [tệp…]                           # so từng byte với giaoc64.py + điểm bất động
```

`giaoc64.giao` là bản chép 1-1 của bộ tách từ, bộ phân tích (giao.py) và bộ sinh mã (giaoc64.py), viết
bằng GIAO, dịch sẵn ở `wasm/giaoc64_tu.g64`. Máy không thấy thư mục nào: `tu_bien_dich.sh` gói tệp chính,
mọi tệp nó `nhập` (bao đóng), `chuẩn.giao` và `_cdfl.giao` vào stdin, mỗi mục có đếm độ dài byte (có tệp
chứa byte NUL trong chuỗi). Hai builtin I/O mới không mở năng lực nào: `vào_còn()` đọc phần stdin còn
lại, `ra_byte(ds)` ghi byte thô ra stdout. Số thực trong mã nguồn đổi sang IEEE-754 bằng số lớn chính
xác, làm tròn nửa-về-chẵn như `float()` của Python. Dòng kiểu CRLF được chuẩn hoá như chế độ văn bản
của Python.

- **219 chương trình của dự án: .g64 trùng TỪNG BYTE với giaoc64.py.**
- **Điểm bất động:** `giaoc64.giao` tự dịch chính nó ra đúng bản mồi (86 KB), và thế hệ thứ hai dịch
  lại vẫn trùng. Từ đây `giaoc64.py` chỉ còn là bản mồi và bộ đối chiếu.
- Chương trình nhỏ dịch trong khoảng 0.4 s; thư viện lớn (`lib_tu_xa.giao`, ~430 KB .g64) vài giây.

## Đã kiểm chứng (`kiem_gvm64.py`, trong `kiem_toan_bo.py`)

Đối chiếu mọi chương trình GIAO trong dự án giữa trình thông dịch và GVM-64, **so stdout từng ký tự**,
với cùng cờ host mà CI dùng:
- **143 khớp · 0 lệch · 0 chưa biên dịch được.**
- 13 chương trình cần năng lực host (tệp/mạng/mmio/phần cứng/LLM) hoặc in thời gian đo thật.

**Tầng CDFL** (`vật/tâm/học/giao/trôi/khi viên_mãn/de`) không thêm lệnh máy nào. `giaoc64` hạ cú pháp
xuống lời gọi thư viện `_cdfl.giao`, viết bằng GIAO: kho tâm/vật, học (α = 0.5), cộng hưởng (F.4), luật
trôi và DE bốn mặt, bám từng dòng ngữ nghĩa của `giao.py`. Lỗi (`tâm 'x' chưa khai báo`…) đi qua builtin
nội bộ `__ném`, bắt được bằng `thử`. `kiem_cdfl_gvm64.giao` phủ các nhánh biên. Khác biệt duy nhất đã
biết: biểu thức luật trôi được tính trong môi trường lúc ĐĂNG KÝ (bao đóng), còn `giao.py` tính trong
môi trường lúc NHỊP trôi; chỉ lệch khi luật đọc biến cục bộ bị đổi giữa hai lúc.

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

**Sau SIMD 128-bit (v0.36, f64x2):** hai biên độ liền kề một lượt ở các lõi `m_biến_đổi_cặp`,
`m_nhân_chọn`, `m_biến_đổi_bốn` (khi bit 0 là bit tự do). Mỗi làn làm đúng phép vô hướng theo đúng thứ tự,
không FMA, nên kết quả **khớp từng bit** với lõi vô hướng (đã so biên độ đủ chữ số và ⟨ψ|ψ⟩ ở 20 và 24
qubit, QFT và ngẫu nhiên). `--không-simd` tắt SIMD trên cùng tệp máy để đo A/B.

| mạch | n | GVM-64 vô hướng | **GVM-64 SIMD** | Aer ép 1 luồng | Aer mặc định (20 luồng) |
|---|---|---|---|---|---|
| QFT | 24 | 9.57 s | **4.72 s** | 17.2 s | 3.8 s |
| ngẫu nhiên | 24 | 4.77 s | **2.17 s** | 13.7 s | 1.05 s |
| QFT | 26 | 39.1 s | **21.0 s** | 30.5 s | 13.0 s |
| ngẫu nhiên | 26 | 19.6 s | **9.1 s** | 8.5 s | 4.5 s |

Biên độ vẫn khớp Aer tới 10⁻¹⁶ – 10⁻²⁰. RAM không đổi (~1.07 GB ở 26 qubit). So với Aer **mặc định**
(đa luồng) GVM-64 còn chậm hơn 1.6–2 lần; so với Aer ép 1 luồng thì QFT nhanh hơn, mạch ngẫu nhiên xấp xỉ.

- **Độ đúng:** mọi biên độ khớp Aer tới **10⁻¹⁶ – 10⁻²⁰**, và ⟨ψ|ψ⟩ = 1.000000000000.
- **QFT:** GVM-64 xấp xỉ Aer ép 1 luồng. Ở 24 qubit nó nhanh hơn Aer ép 1 luồng (8.8 s so với
  17.2 s), nhưng chậm hơn Aer mặc định 20 luồng (3.8 s).
- **RAM** bằng hoặc thấp hơn Aer (16 byte mỗi biên độ).
- **Mạch ngẫu nhiên:** trước khi gộp cổng thì chậm hơn Aer 1 luồng 7–11 lần, vì mỗi cổng duyệt cả
  1 GB trạng thái (giới hạn băng thông bộ nhớ). **Gộp cổng** (v0.35, viết bằng GIAO) đưa về chậm hơn
  **2.3 lần** Aer ép 1 luồng ở 26 qubit, và nhanh hơn Aer ép 1 luồng ở 24 qubit (vẫn chậm hơn Aer
  mặc định đa luồng 4.3 lần). SIMD (v0.36) giảm tiếp một nửa, xem bảng trên.

**Mật khẩu:** `kiem_lib_mật_khẩu.giao` trên GVM-64 **không cần nới trần bước** và chạy xong trong
0.69 s. Trình thông dịch chạm trần 5 triệu bước; nới `--bước 200000000` thì mất 8.52 s. Đầu ra trùng
khít.

## Giới hạn

- **wasm32 tối đa 4 GB bộ nhớ**, nên mô phỏng lượng tử tối đa khoảng 27 qubit.
- **Chưa có đa luồng — bị chặn ở vỏ, không phải ở máy.** Đã thử (v0.36): WASM có shared memory +
  atomics, nhưng tạo luồng cần import `wasi::thread-spawn` (đề xuất wasi-threads). **wasmtime 49 đã
  bỏ hẳn nó**: `-S threads` báo "no longer supported", module có import ấy không khởi tạo được.
  Node `node:wasi` cũng không có. Các đường còn lại đều đổi lấy an toàn hoặc công sức lớn:
  (1) quay về wasmtime cũ còn wasi-threads (thử nghiệm, đã bị bỏ — không nên);
  (2) tự viết vỏ Rust nhúng thư viện wasmtime, tự cấp `thread-spawn` (hàng trăm dòng Rust, và
  AssemblyScript còn phải tránh GC trong luồng phụ: mỗi luồng là một instance mới dùng chung bộ nhớ,
  chạy lại khởi tạo tĩnh); (3) chờ đề xuất shared-everything-threads. Hiện Aer mặc định (đa luồng) nhanh
  hơn GVM-64 1.6–2 lần.
- Tokenizer của `giaoc64.giao` nhận chữ cái theo các khối Unicode liệt kê trong mã (Latin, tiếng Việt,
  Hy Lạp, Kirin, CJK, kana, Hangul) thay cho `str.isalpha()` của Python, và chỉ nhận chữ số ASCII.
  Tên dùng chữ ở khối khác sẽ bị cả hai từ chối khác cách. Mọi tệp trong dự án đều trùng từng byte.
- `log`/`mũ` dùng thư viện toán của AssemblyScript, có thể lệch ở chữ số cuối so với libm của Python.
  Chưa thấy lệch trong đầu ra (in `%.4g`).

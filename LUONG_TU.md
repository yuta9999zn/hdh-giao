# GIAO và tính toán lượng tử

> **Tóm tắt trung thực.** GIAO **không phải** máy tính lượng tử và cũng không chạy nhanh hơn nhờ
> "lượng tử". Tài liệu này mô tả một **thư viện mô phỏng** viết bằng GIAO (`lib_lượng_tử.giao`).
> Thư viện chạy trên máy cổ điển, và mạch dựng bằng nó **xuất được ra OpenQASM** để chạy trên phần
> cứng qubit thật (IBM Quantum, AWS Braket…). Thư viện cũng nối phép đo lượng tử với ngữ nghĩa ba
> trị sẵn có của GIAO.

## 1. Khác biệt cốt lõi

| | GIAO (ba trị + γ) | Qubit |
|---|---|---|
| Lưu ở đâu | số thực/bit thường trên transistor | trạng thái vật lý (ion, mạch siêu dẫn…) |
| "Chưa biết" | `ẩn` = **thiếu thông tin** | chồng chập = **biên độ phức** của cả 0 và 1 |
| Giao thoa | không | biên độ cộng/triệt tiêu nhau |
| Vướng víu | không | có |
| Đo | đọc giá trị, không đổi gì | làm **sụp** trạng thái, ngẫu nhiên |

Vì vậy thư viện này mô phỏng **đủ 2^n biên độ phức** bằng số thực, và chi phí tăng **mũ** theo n.

## 2. Đã triển khai

| Bước | Có gì | Tệp |
|---|---|---|
| Số phức + đại số tuyến tính | `phức`, `p_nhân`, `p_mũ_i`, `mt_nhân`, `mt_dagger`, `mt_kron`, `mt_vết` | `lib_lượng_tử.giao` §1–2 |
| Mô phỏng qubit (state vector) | `trạng_thái`, `áp_h/x/y/z/cx/cz/ccx/swap`, `cổng_rx/ry/rz/p`, `đo_qubit`, `phân_phối` | §3 |
| Ba trị ↔ phép đo | `tri_qubit` (chồng chập → **ẩn**), `đo_qubit` → `tri(bit, γ = xác suất)` | §4 |
| Trị riêng Hermitian + entropy von Neumann | `trị_riêng_hermitian` (Jacobi), `vết_riêng`, `entropy_von_neumann`, `độ_vướng`, `thông_tin_tương_hỗ(_ρ)` | §5 |
| Cú pháp cổng + OpenQASM | `mạch(n)`, `H`, `CX`/`CNOT`, `RZ`, `CCX`, `ĐO`… → `chạy_mạch`, `lấy_mẫu`, `sang_qasm` (2.0), `sang_qasm3` (3.0) | §6 |
| Lõi ngôn ngữ | builtin mới `tạo_tri(giá_trị, γ)`, `γ_của(tri)`; cờ `--trần-ds N` | `giao.py` |
| Kiểu `mảng` (phép trên cả mảng) | `mảng_không`, `m_chọn`, `m_đặt_chọn`, `m_tổ_hợp`, `m_nhân_số`, `m_tổng_mô2`, `m_tích_trong`, `m_rút`… | `giao_mang.py` |

### Hai lõi, cùng ngữ nghĩa

| Lõi | ψ lưu thế nào | Một cổng chạy ra sao | Dùng khi |
|---|---|---|---|
| **mảng** (mặc định) | `{n, v}`, với `v` là kiểu `mảng`: 2 `array('d')` liền khối, 16 byte/biên độ | MỘT phép tại chỗ theo khúc: `m_biến_đổi_cặp`, `m_nhân_chọn` (cổng chéo) hoặc `m_đổi_chọn` (X/CX/SWAP) | mọi lúc |
| **GIAO thuần** | `{n, re, im}` (danh sách GIAO) | vòng lặp GIAO qua N/2 cặp, **từng phần tử đi qua trình thông dịch** | chuẩn đối chiếu; `dùng_lõi_mảng(tối)` |

Lõi mảng làm theo **cách numpy chạy nhưng không dùng numpy**. Numpy nhanh không nhờ thuật toán khác
mà vì từng phần tử không phải đi qua trình thông dịch: mỗi lệnh ở tầng ngôn ngữ là một phép trên cả
mảng, còn vòng lặp theo phần tử chạy ở tầng dưới. Ở GIAO, tầng dưới đó là mã C sẵn có của CPython
(lát cắt danh sách, list comprehension, `itertools.accumulate`, `bisect`). `giao_mang.py` chỉ dùng
thư viện chuẩn. Thuật toán cổng vẫn viết bằng GIAO trong `lib_lượng_tử.giao`. `giao_mang.py` chỉ
cung cấp phép toán mảng tổng quát và **không biết gì về qubit**.

Hai lõi cho kết quả **trùng nhau tuyệt đối** (lệch 0.0) trên 24 mạch ngẫu nhiên, cả khi rút mẫu.
Điều này được kiểm trong `kiem_luong_tu.py`.

"Cú pháp cổng" là **hàm GIAO trên dữ liệu mạch**, không phải từ khoá mới của trình phân tích cú
pháp. Cách này không đụng tới parser, bộ biên dịch GVM hay WASM, và mạch vẫn là dữ liệu thường nên
có thể in, duyệt hay biến đổi được.

### Quy ước
- Qubit `q` tương ứng với bit `q` của chỉ số biên độ (little-endian, **giống Qiskit**). Chuỗi kết
  quả in theo thứ tự `c[n-1]…c[0]`, nên số đếm khớp trực tiếp với IBM Quantum.
- Phép đo dùng hạt giống (seed) **tất định** qua `ngẫu()` của thư viện chuẩn, nên chạy lại sẽ ra
  cùng kết quả. Muốn dùng entropy thật thì host cấp `--cho-ngẫu`, rồi tự lấy seed từ `ngẫu_mạnh`.
- `"…" + tri` chỉ lấy **giá trị** của tri, còn `"…" + ẩn` cho ra `ẩn` (đúng ngữ nghĩa ba trị). Muốn
  in đầy đủ thì dùng `hiện(x)`.

### Ngữ nghĩa ba trị của phép đo
- **Trước khi đo**, qubit ở chồng chập cho `tri_qubit(ψ, q)` = **`ẩn`**. Thư viện không gán giá trị
  cho cái chưa quan sát, và `tri_qubit(ψ,0) == 1` cũng cho `ẩn` (logic ba ngả). Qubit đã xác định
  (P = 0 hoặc 1) cho `tri(bit, γ=+1, sáng)`.
- **Sau khi đo**, kết quả là `tri(bit, γ = P(bit), sáng)`. Đã quan sát thì là sáng, còn γ cho biết
  kết quả ấy dễ đoán tới đâu (γ = 0.5 nghĩa là ngẫu nhiên thuần).
- Đo một nửa cặp Bell làm nửa kia chuyển từ `ẩn` sang `tri(…, γ=+1)`, dù nửa đó chưa hề bị đo. Đó
  là "tri thức chung" do vướng víu, và `lượng_tử_hilbert.giao` đo được nó bằng I(I:M).

### γ chấm mẫu đo — Phụ lục F.4 ≈ XEB

`chấm_mẫu(đếm, ψ, ε)` chấm các mẫu đo `đếm`, lấy từ "máy" ρ (phần cứng thật hoặc mô phỏng có nhiễu),
so với mô hình lý tưởng σ(x) = |⟨x|ψ⟩|² và nền đều u = 2⁻ⁿ:

  γ = [S(ρ‖u) − S(ρ‖σ)] / [S(ρ‖u) + S(ρ‖σ)],  với tử số = E_ρ[ln σ − ln u] = XEB dạng log.

Hàm trả về `tri(xeb_tuyến_tính, γ)`. Mạch ngẫu nhiên 6 qubit với nhiễu khử cực toàn cục cho
(`lượng_tử_xeb.giao`, 4000 mẫu):

| độ trung thực | XEB tuyến tính | γ (F.4) |
|---|---|---|
| 1.0 | 1.67 | +0.98 sáng |
| 0.8 | 1.36 | +0.75 sáng |
| 0.6 | 1.02 | +0.18 sáng |
| 0.5 | 0.84 | −0.18 **tối** |
| 0.0 (máy ngẫu nhiên thuần) | −0.04 | −0.98 tối |

- **XEB tuyến tính** giảm tỉ lệ với độ trung thực. Đây là thước đo Google dùng, ước lượng được ở mọi
  cỡ n, và chỉ cần p(x) của các chuỗi đã gặp.
- **γ đặt ngưỡng đạt/rớt tại độ trung thực ≈ 0.56.** Mẫu nhiễu rơi vào chuỗi mà σ cho xác suất thấp
  bị phạt theo log. Với phân phối Porter–Thomas, tử số ≈ 0.42·λ − 0.58·(1−λ), nên γ **đổi dấu khi độ
  trung thực ≈ 0.56**. Không nên nói "γ nghiêm hơn XEB": XEB **ước lượng** độ trung thực (một con
  số), còn γ là một phép **đạt/rớt** có dấu. Hai thước đo khác bản chất. γ trả lời
  một câu hỏi khác XEB: *"mô hình lý tưởng có giải thích máy này tốt hơn không biết gì không?"*
  γ < 0 nghĩa là tin mô hình lý tưởng về máy này là ảo tưởng, đúng nghĩa đốm tối của F.4.
- **ε = 0** là định nghĩa gốc. Chỉ cần gặp một chuỗi mà σ cho xác suất 0 (ví dụ `01` trên cặp Bell
  có nhiễu) là S(ρ‖σ) = ∞, nên γ = −1. Dùng ε > 0 để mô hình "khiêm tốn": σ_ε = (1−ε)σ + εu.
- `γ_mẫu` ước lượng ρ bằng tần suất, nên chỉ chuẩn khi số mẫu ≫ 2ⁿ. Ở n lớn thì dùng `xeb_tuyến_tính`.
- Nhiễu mô phỏng ở đây là **khử cực toàn cục** (`lấy_mẫu_nhiễu`), mô hình thô nhất, không thay được
  nhiễu thật của phần cứng. Giá trị thật của γ/XEB là chấm mẫu **từ máy lượng tử thật** (mục 6).

### Gộp cổng (gate fusion)

`hợp_nhất_cổng(ds)` (tự động trong `trạng_thái_cuối` / `chạy_mạch`, tắt bằng `dùng_hợp_nhất(tối)`)
dồn cổng 1-qubit thành 2×2 và cổng 2-qubit cùng mọi cổng lân cận trên cặp đó thành một 4×4, rồi duyệt
bộ nhớ MỘT lần. Mạch gốc và QASM giữ nguyên. Kết quả: mạch ngẫu nhiên 26 qubit trên GVM-64 từ 97 s
còn 19.6 s (xem `GVM64.md`).

## 3. Chạy

```
python giao.py lượng_tử_bell.giao          # chồng chập → vướng víu → đo → shots → QASM
python giao.py lượng_tử_grover.giao        # Grover 3 qubit: P(|101⟩) 0.125 → 0.781 → 0.945
python giao.py lượng_tử_dịch_chuyển.giao   # teleportation: độ trung thực 1 với mọi kết quả đo
python giao.py lượng_tử_hilbert.giao       # I(I:M) đầy đủ: Bell = 2·ln2 (gấp đôi trần cổ điển)
python giao.py lượng_tử_ghz.giao           # GHZ 20 qubit (1.048.576 biên độ) trên lõi mảng, ~9 giây
python giao.py lượng_tử_xeb.giao           # γ (F.4) / XEB chấm mẫu theo mức nhiễu
python kiem_luong_tu.py                    # đối chiếu độc lập (27 mục, cả hai lõi)
python bench_luong_tu.py --cỡ 20 24 26 --qiskit <python có qiskit>   # đo sức, so với Qiskit
```

Các tệp demo nằm ở **gốc** chứ không ở `examples/`, vì `nhập` chỉ nạp tệp trong thư mục của chương
trình chính.

Ví dụ ngắn:

```
nhập "lib_lượng_tử.giao"
đặt m = mạch(2)
H(m, 0)
CX(m, 0, 1)
ĐO_HẾT(m)
in_đếm(lấy_mẫu(m, 1000, 7))     #   00: 511   11: 489
rọi sang_qasm(m)                 # OpenQASM 2.0
```

## 4. Đã kiểm chứng những gì (`kiem_luong_tu.py`, nằm trong `kiem_toan_bo.py`)

Bộ tham chiếu viết bằng numpy, dựng **ma trận unita đầy đủ bằng tích Kronecker**. Cách này khác hẳn
cách thư viện GIAO áp cổng theo cặp biên độ. Các mục kiểm:

Tham chiếu dùng numpy **chỉ trong bộ kiểm**. Thư viện và lõi mảng không dùng numpy.

- Phép `m_chọn`/`m_đặt_chọn` so với duyệt vét cạn: 300 ca ngẫu nhiên, 0 sai.
- 24 mạch ngẫu nhiên (2–4 qubit, 20 cổng, đủ mọi loại cổng), **cả hai lõi**: biên độ lệch ≤ 1e-15.
  Hai lõi trùng nhau tuyệt đối.
- `ma_trận_rút_gọn` (tính thẳng từ ψ) trùng với `vết_riêng` của ρ đầy đủ.
- QASM 2.0 và 3.0 xuất ra được **đọc lại bằng một parser riêng** rồi mô phỏng: độ trung thực = 1.
- Trị riêng Hermitian (Jacobi bằng GIAO) so với `numpy.linalg.eigvalsh`: lệch ≤ 1e-14.
- Entropy vướng víu và thông tin tương hỗ trên trạng thái 3 qubit ngẫu nhiên. Bell: S = ln2, I = 2·ln2.
- `|+⟩⟨+|` (không chéo) cho S = 0. Cách rút gọn chéo cũ của `examples/hilbert.giao` sẽ ra ln2, tức
  là **sai**.
- Ngữ nghĩa ba trị, γ = xác suất, và lấy mẫu (có cả đo giữa mạch). Cùng seed thì hai lõi rút ra
  số đếm y hệt nhau.

**Chưa kiểm:** chưa gửi mạch lên phần cứng thật, vì máy này không cài Qiskit/Braket và không có
tài khoản. QASM mới được kiểm bằng parser tự viết, **chưa** qua `qiskit.qasm2.loads`.

## 5. Giới hạn

- **Quy mô** (đo bằng `bench_luong_tu.py` trên máy này, RAM 15.6 GB):

  | qubit | lõi GIAO thuần | lõi mảng | tăng tốc |
  |---|---|---|---|
  | 10 | 0.014 s/cổng | 0.0003 s/cổng | ~50× |
  | 16 | 0.87 s/cổng | 0.005 s/cổng | ~175× |
  | 20 | ~14 s/cổng (ngoại suy) | 0.13 s/cổng | ~110× |
  | 24 | ~4 phút/cổng (ngoại suy) | 2.9 s/cổng | ~80× |
  | 25 | ~8 phút/cổng (ngoại suy) | 7.9 s/cổng | ~60× |

  Ở 25 qubit, vector trạng thái là danh sách 2^25 số phức Python (~1.3 GB), tổng cộng vài GB kể cả
  các mảng tạm. Tốc độ mỗi biên độ giảm dần ở cỡ lớn vì áp lực bộ nhớ. Bằng numpy sẽ nhanh thêm
  khoảng 10–30 lần (ước lượng, chưa đo). Cái giá của việc không phụ thuộc thư viện ngoài nằm ở đây.
- Lõi GIAO thuần vẫn vướng trần mặc định: khoảng 10 qubit/30 cổng trong 5 triệu bước. Vượt 19 qubit
  cần `--trần-ds`. Lõi mảng không tạo danh sách GIAO dài 2^n, trừ `phân_phối`, nên không vướng trần này.
- `trị_riêng_hermitian` dùng Jacobi trên ma trận nhúng thực 2n×2n, hợp với ma trận mật độ ≤ 3 qubit
  (8×8). Lớn hơn thì cần nới `--bước`.
- Chưa có nhiễu (noise), kênh lượng tử, cổng điều khiển bằng bit cổ điển (`if (c==1)`) hay cổng
  tuỳ ý `u3`. Teleportation dùng "đo trễ" để tránh cần điều khiển cổ điển.
- Ngẫu nhiên mặc định là LCG tất định, đủ cho mô phỏng nhưng **không** dùng làm mật mã.

## 5b. Đo sức với Qiskit trên cùng máy (2026-09-29)

`bench_luong_tu.py --cỡ 20 24 26 --qiskit …`. Mỗi ca chạy trong một tiến trình riêng, RAM là đỉnh
working set. Mạch do GIAO dựng và **xuất ra QASM**, Qiskit đọc lại **đúng mạch đó**. Máy dùng CPU 20
luồng, RAM 15.6 GB, Qiskit 2.5.2, Aer 0.17.2 (statevector, double, có gate fusion mặc định).

| mạch | n | GIAO (lõi mảng) | Qiskit Aer 1 luồng | Qiskit Aer 20 luồng | Qiskit `Statevector` (numpy) |
|---|---|---|---|---|---|
| QFT | 20 | 48.9 s · 117 MB | 0.28 s · 108 MB | 0.07 s · 109 MB | 4.9 s · 132 MB |
| ngẫu nhiên (5 lớp) | 20 | 69.7 s · 115 MB | 0.12 s · 108 MB | 0.05 s · 109 MB | 5.0 s · 132 MB |
| QFT | 24 | 1463 s (24 phút) · 1500 MB | 17.2 s · 332 MB | 3.8 s · 334 MB | 216 s · 1092 MB |
| ngẫu nhiên (5 lớp) | 24 | 1445 s (24 phút) · 1494 MB | 13.7 s · 332 MB | 1.05 s · 333 MB | 153 s · 1092 MB |
| QFT / ngẫu nhiên | 26 | **không chạy xong** (xem dưới) | — | — | — |

**Đúng:** ở 20 qubit, độ trung thực |⟨ψ_GIAO|ψ_Aer⟩|² = **1.000000000000** trên cả QFT lẫn mạch ngẫu
nhiên, với cả ba chế độ Qiskit. Tức là GIAO tính đúng, và QASM nó xuất (gồm `cu1`, SWAP tách 3 CX)
cũng đúng.

**GIAO đang ở đâu:**
- chậm hơn Aer 1 luồng khoảng **85–580 lần** (so công bằng: cả hai đều đơn luồng);
- chậm hơn Aer 20 luồng khoảng **380–1400 lần**;
- chậm hơn Qiskit `Statevector` thuần numpy khoảng **7–14 lần**;
- **RAM gấp ~4.5 lần Aer** ở 24 qubit (1.5 GB so với 332 MB). Mỗi biên độ là một đối tượng `complex`
  Python, tức 32 byte đối tượng + 8 byte con trỏ, so với 16 byte liền khối của Aer, cộng thêm mảng tạm.

**Cập nhật v0.33 — lưu array('d') 16 byte/biên độ + phép tại chỗ theo khúc:**

| mạch | n | GIAO v0.32 | **GIAO v0.33** | Aer 1 luồng |
|---|---|---|---|---|
| QFT | 20 | 48.9 s · 117 MB | **23.4 s · 89 MB** | 0.28 s · 108 MB |
| ngẫu nhiên | 20 | 69.7 s · 115 MB | **49.7 s · 88 MB** | 0.12 s · 108 MB |
| QFT | 24 | 1463 s · 1500 MB | **514 s · 405 MB** | 17.2 s · 332 MB |

RAM ở 24 qubit giờ chỉ gấp **1.2 lần Aer**, so với 4.5 lần trước đây. Phần chênh là tiến trình Python
+ GIAO nền và khúc tạm. Tốc độ so với Aer 1 luồng còn chậm khoảng **30–400 lần**. Chênh lệch này là
chi phí xử lý từng phần tử bằng đối tượng Python (khoảng 180 ns, so với vài ns của vòng lặp C/SIMD
trong Aer), và bản thân thư viện chuẩn không có cách nào xoá được.

**XEB, mô phỏng không nhiễu, 20 qubit:** mạch 20 lớp (1010 cổng): XEB = 2.757, kỳ vọng
N·Σp² − 1 = 2.785, nên độ trung thực ước lượng là **0.990**. Với nhiễu 30% thì ra 0.686 (lý thuyết
0.7). Mạch 1 chiều 20 lớp chưa đạt Porter–Thomas hoàn toàn, nên XEB thô khác 1; phải đọc tỉ số với
giá trị kỳ vọng.

**26 qubit (bản v0.32) không chạy xong.** Claude Code dừng tiến trình khi máy sắp cạn RAM. Ngoại suy từ 24 qubit,
GIAO cần khoảng **6 GB** và **~1.5–2 giờ mỗi mạch**, trong khi Aer chỉ cần khoảng 1.1 GB. Với 15.6 GB
RAM dùng chung cho cả những thứ khác đang chạy, 26 qubit là **trần thực tế** của cách lưu hiện tại.

**Vì sao chậm, và vì sao không tối ưu thêm được bằng thư viện chuẩn:** thời gian mỗi phần tử tăng
từ ~30 ns (dữ liệu mới) lên ~180–280 ns sau nhiều cổng. Nguyên nhân là các đối tượng `complex` bị
pymalloc rải khắp bộ nhớ, nên mỗi lần duyệt đều trượt cache. Đã thử `array('d')` liền khối, nhưng
còn **chậm hơn** (256–331 ns), vì mỗi phép tính vẫn phải đóng gói thành `float` Python. Numpy và Aer
nhanh nhờ vòng lặp native trên bộ nhớ liền khối. Thư viện chuẩn Python không có vòng lặp như vậy,
nên đây là giới hạn của hướng "không phụ thuộc thư viện ngoài". Hướng thoát là nâng GVM/WASM (mục 8).

## 6. Chạy trên máy lượng tử thật — môi giới `moi_gioi_luong_tu.py`

GVM-64 không có mạng, và không nên có. Việc gọi IBM Quantum dồn vào **một** tiến trình môi giới chạy
ngoài hộp cát; mọi phần tính toán vẫn là GIAO trên GVM-64:

```
python moi_gioi_luong_tu.py mạch_mẫu_ibm.giao                         # chạy khô: in QASM, "cần_người_duyệt", mã 2
python moi_gioi_luong_tu.py mạch_mẫu_ibm.giao --giả-lập 0.02 --duyệt  # thử CẢ quy trình, không cần token
QISKIT_IBM_TOKEN=… python moi_gioi_luong_tu.py mạch_mẫu_ibm.giao --shots 1000 --đoán-xeb vừa --duyệt
```

1. `mạch.giao` đặt biến `m` (đã `ĐO_HẾT`). Môi giới dịch nó bằng **trình biên dịch GIAO tự thân**
   (`tu_bien_dich.sh`) và chạy trên GVM-64 để lấy OpenQASM 2.0.
2. **Cổng người duyệt:** gửi mạch tốn hạn mức và không rút lại được, nên không có `--duyệt` thì chỉ in
   mạch rồi thoát. Thiếu token thì cũng dừng trước bước niêm phong.
3. **Niêm phong** dự đoán (dấu γ, khoảng XEB) vào `niem_phong.py` sau khi người duyệt, trước khi gửi.
4. Gửi bằng `SamplerV2` (`qiskit-ibm-runtime`), lưu số đếm ở `__pycache__/luong_tu_that/`.
5. **Chấm trên GVM-64:** `chấm_mẫu(đếm, ψ_lý_tưởng, ε)` → XEB tuyến tính + γ, rồi chấm niêm phong.

Token chỉ đọc từ biến môi trường `QISKIT_IBM_TOKEN`, không ghi ra đĩa. Chế độ `--giả-lập p` thay máy
thật bằng Aer có nhiễu khử cực p mỗi cổng, để kiểm cả quy trình khi chưa có token. Mạch mẫu 4 qubit,
độ sâu 3, p = 0.02: XEB = 0.674, γ = +0.513; p = 0.3: XEB = 0.001, γ = −0.997 (tối).
`kiem_moi_gioi.py` kiểm cổng duyệt + thứ tự niêm phong (trong `kiem_toan_bo.py`).
**Chưa chạy trên máy IBM thật** — cần token của chủ dự án.

## 7. Nên gọi dự án thế nào

Nên nói: *"GIAO có thư viện mô phỏng lượng tử và xuất mạch ra OpenQASM để chạy trên máy lượng tử
thật."* Không nên gọi GIAO/GVM/FPGA là "máy tính lượng tử". Phần cứng của dự án (Verilog/FPGA) vẫn
là cổ điển, và muốn có qubit vật lý thì không thể viết thêm phần mềm mà ra được.

## 8. Hướng tiếp

1. Nâng GVM (số thực IEEE 64-bit, heap lớn) để biên dịch chính `lib_lượng_tử.giao` sang WASM, tức
   là bỏ luôn Python.
2. Khai thác cấu trúc thay vì cứ 2^n: bộ mô phỏng stabilizer cho mạch Clifford (hàng nghìn qubit),
   MPS cho mạch ít vướng víu. Đây là cách **duy nhất** vượt được giới hạn 2^n khi mô phỏng chính xác.
3. Ma trận mật độ + kênh nhiễu (depolarizing, amplitude damping) để mô phỏng giống phần cứng thật.
4. Đọc OpenQASM **vào** GIAO (hiện mới xuất ra).
5. Chạy `moi_gioi_luong_tu.py` trên IBM Quantum thật (cần token) rồi ghi số liệu thật vào tài liệu này.

# RANH GIỚI — hai tầng thực thi của GIAO

> Tuyên bố RÕ: GIAO có **HAI mô hình thực thi**. Đừng nhầm phạm vi của chúng.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  THÔNG DỊCH  (giao.py)  =  NGÔN NGỮ ĐẦY ĐỦ                                │
│  tree-walking, như Python/Ruby. Mọi tính năng. Đây là đường CHÍNH.        │
└─────────────────────────────────────────────────────────────────────────┘
                 │  giaoc.py biên dịch một PHẦN CON xuống ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  MÁY / GVM  (giaoc.py → bytecode)  =  LÕI SỐ HỌC, neo xuống phần cứng     │
│  chạy đồng nhất trên 5 substrate: Python-sim · model · Verilog · FPGA ·   │
│  WASM. KHÔNG phải cả ngôn ngữ — là một CORE biên dịch được.               │
└─────────────────────────────────────────────────────────────────────────┘
```

**Quy tắc một dòng:** *Thông dịch là NGÔN NGỮ; Máy là một LÕI con biên dịch được để
chạy trên phần cứng/đa-substrate.* Cái máy chạy được trên FPGA/WASM **không phải** toàn
bộ GIAO — nó là phần số học/luồng-điều-khiển có thể hạ xuống cổng logic.

---

## Bảng phạm vi (đã kiểm bằng `giaoc.py`)

### ✅ Chạy trên CẢ HAI (máy + thông dịch)
| Tính năng | |
|---|---|
| Số nguyên, chuỗi, danh sách `[…]` | `+ − * ` , so sánh `== != < > <= >=` |
| `nếu / khác` (HAI ngả) | `lặp <n> { }` (n **hằng**) |
| Hàm + đệ quy + nhiều tham số | `đầu/đuôi/dài/ghép`, index `l[i]` |
| **biến CỤC BỘ theo khung** (`đặt` trong hàm) | per-call (`DÀNH_CB/LƯU_THAM_I`) → đệ-quy-có-biến + closure-giữ-state ĐÚNG |
| **`sáng/tối`** → `1/0`; `rọi` tự-suy-kiểu | `TruthLit`; `RỌI_AUTO` (con trỏ chuỗi→chuỗi, ngược→số) |
| Chuỗi trên heap (`RỌI_CHUỖI`) | `là_số/là_ds` + **thẻ 32-bit** + `==` cấu trúc + `+` đa hình |
| `vật/tâm/học/giao/rọi` (lõi CDFL số) | `rọi_ds` |
| **closure / hàm vô danh** `hàm(x){…}` | bắt biến lexical, gọi bậc cao, lam lồng — `GỌI_CLOSURE` |
| **`bản` (map/record)** — tham chiếu mutable | `bản() đặt_khoá lấy_khoá có_khoá xoá_khoá khoá giá_trị dài m[k]`; thiếu khoá→`ẩn` |
| **`lặp x trong <ds/chuỗi/bản>`** + **`dừng`** | DUYỆT không-đệ-quy (car/cdr); bản→duyệt KHOÁ; vòng lồng; thoát sớm |
| **SỐ THỰC** `1.5 0.1 -4.5` `+ − * /` so sánh | điểm-cố-định ×10000 (DSP nguyên, KHÔNG FPU); `FNHÂN/FCHIA/RỌI_THỰC` |
| **`mãi { }`** (vòng liên tục) + **`dừng`** | vòng không-điều-kiện tới khi `dừng` (dùng chung ngăn-xếp-thoát) |
| **`thử { } bắt (e) { }`** (ngoại lệ) | ngăn xếp HANDLER + `NÉM` gỡ-cuộn; chỉ-mục-ngoài-phạm-vi NÉM mã lỗi |

### ⛔ CHỈ thông dịch (máy báo **lỗi RANH GIỚI sạch**, không biên dịch-sai)
| Tính năng | Vì sao không xuống máy |
|---|---|
| `ngờ` (rẽ **BA NGẢ** — nhánh `ẩn`) | máy nhị-phân-hoá cond → chỉ 2 ngả |
| `trôi` / `trôi_nhịp` | thế giới tự trôi (động học runtime) |
| `de` (DE bốn mặt) | truy vấn vùng tối — cần trạng thái runtime đầy đủ |
| `khi viên_mãn` | kích hoạt theo γ runtime |
| **`nhập`** (module) | nạp nguồn lúc chạy |
| **capability I/O** (`đọc_tệp/chạy/ghi_tệp/liệt_kê`) | I/O — không thuộc lõi số |
| **`tim/nhúng`** (LLM) | cơ quan I/O ngoài (Ollama) |
| `cộng_hưởng` builtin, `loại/nguyên/thêm/gom/đảo/nối/tách/…` | builtin thư viện — chỉ thông dịch |

> Báo lỗi: `python giaoc.py x.giao` gặp tính năng chỉ-thông-dịch → in
> `[GIAOC — RANH GIỚI] … KHÔNG biên dịch xuống máy …` rồi thoát. Ranh giới **tự thực thi**,
> không còn "biên dịch-nhưng-sai" (trước đây `ngờ` bị bỏ nhánh, `float` bị cắt — nay là lỗi).

---

## Vì sao thiết kế NHƯ VẬY (không phải khuyết điểm — là lựa chọn)

- **KHÔNG fork ngôn ngữ.** GIAO ở MỘT nơi (Python, `giao.py`). Máy không phải bản GIAO thứ
  hai; nó là một *trình biên dịch* hạ lõi số xuống phần cứng. Thêm substrate (WASM…) = thêm
  nơi cho LÕI chạy, không phải viết lại ngôn ngữ.
- **Cái đáng neo xuống silicon là LÕI SỐ.** `tim`/LLM, I/O, DE, closure là *cơ quan mềm* hợp
  với host (Python). Số học/luồng-điều-khiển/đệ quy/heap là *cơ quan cứng* hợp với cổng logic.
  Ranh giới này trùng với ranh giới "cái gì nên ở phần cứng".
- **Tự thân hoá vẫn trọn vẹn ở tầng máy:** `giaoc.giao` (trình biên dịch viết bằng GIAO) nằm
  HOÀN TOÀN trong phần con biên-dịch-được ⇒ tự biên dịch xuống GVM và chạy trên cả 5 substrate.

## Muốn mở rộng phần con của máy?

Cơ học, cùng khuôn: thêm opcode + luật biên dịch trong `giaoc.py` (và mirror sang `gvm_may.py`
+ `wasm/gvm.ts`, conformance bằng `wasm/kiem.mjs`). **Closure đã làm theo đúng khuôn này**
(mốc 3a): closure = khối heap `[code_addr, ncap, bắt…]`, opcode `GỌI_CLOSURE` dựng khung
`[bắt…, đối…]` rồi nhảy; phân tích biến-tự-do ở compiler chọn ô THAM_I cần bắt. **`bản`
(map/record) cũng đã xuống máy (mốc 3b)**: con trỏ tham chiếu tới ô-đầu mutable → alist node
`[khoá, giá, kế]`; `đặt_khoá` chèn-đầu O(1)/sửa-tại-chỗ; khoá so cấu trúc qua `__bằng`;
thiếu khoá → `ẩn`. **`lặp x trong` + `dừng` cũng đã xuống máy (mốc 3c)**: duyệt cons-list bằng
car/cdr (không đệ quy), bản→duyệt KHOÁ; vòng lồng + thoát sớm. Cả ba **không thêm opcode** mới ở
WASM (3b/3c) — chỉ luật biên dịch + ô heap. Đây là **ranh giới có chủ đích**, tài liệu hoá,
tự-thực-thi — và đang **thu hẹp dần** một cách có kiểm soát. **Số thực (3d)** cũng đã xuống máy
bằng điểm-cố-định ×10000 (opcode `FNHÂN/FCHIA/RỌI_THỰC`, trung gian 64-bit) — số nguyên DSP,
KHÔNG FPU, vẫn chạy được trên silicon số nguyên. **`mãi` + `thử/bắt` (3e)** đưa nốt vòng-liên-tục
và NGOẠI LỆ xuống máy: ngăn xếp HANDLER + opcode `NÉM` gỡ-cuộn (unwind) mọi khung lồng về nhánh
`bắt`. Khác thông dịch: trị-lỗi máy là **MÃ SỐ** (vd `1` = chỉ-mục-ngoài-phạm-vi) chứ không phải
chuỗi-thông-điệp; nguồn NÉM hiện có là **chỉ mục danh sách ngoài phạm vi** (`l[i]` quá cỡ) — đúng
một lỗi runtime mà *máy phát hiện được* và *thông dịch cũng bắt*. (Các lỗi-kiểu khác của thông dịch
không sinh ra trên máy vô-kiểu, nên không cần bắt.)

**Cột mốc hợp lưu — HĐH-GIAO chạy như MÃ MÁY.** Khi `đặt`-trong-hàm thành **ô-khung per-call**
(`DÀNH_CB`/`LƯU_THAM_I`), closure bắt-theo-trị mới giữ được STATE RIÊNG mỗi lần gọi — điều kiện
đủ để nhân hệ điều hành `examples/hdh.giao` (bảng tiến trình = `bản`, tiến trình = closure-giữ-state,
lập lịch hợp tác = `mãi`+`lặp`, syscall + cổng an toàn) **biên dịch trọn xuống 16968 từ-lệnh GVM và
chạy khớp TỪNG DÒNG với thông dịch** (cả trên WASM, byte-for-byte). HĐH viết-bằng-GIAO không còn
khoá ở thông dịch. Chạy: `python chay_hdh_may.py` (GVM) · `node wasm/chay_hdh.mjs` (boot trên WASM).
Lưu ý trung thực: GVM-Python là *CPU mô phỏng* (chậm); đường triển khai nhanh là WASM/native — và
với nhân nặng-heap này WASM ≈ tốc-độ thông dịch (tăng tốc lớn dành cho lõi-số thuần).

**Ranh giới NGƯỢC — vài thứ chỉ-MÁY/SILICON (thông dịch KHÔNG có).** Lập lịch **preemptive** cần
cướp-CPU mức-lệnh + chuyển-ngữ-cảnh phần cứng — tree-walker không mô hình hoá được. Nên 3 builtin
`xuất(x)` · `tác_vụ(hàm)` · `lịch_học(lượng_tử)` (→ opcode `XUẤT/TÁC_VỤ/HẸN_GIỜ/LỊCH_HỌC`) là **MÁY/
SILICON-only**; γ-scheduler biết-học (`GVM.lập_lịch_học`) có chính sách **TRÙNG TỪNG WIRE** với
`hw/gvm.v` (chứng minh 3000/3000 ca). Ví dụ `examples/hdh_preempt.giao` (chạy `chay_hdh_preempt.py`)
là **chỉ-máy** (bỏ qua ở quét thông dịch). Đây là chiều ngược của ranh giới: lõi-tính-toán đầy đủ ở
thông dịch, còn **điều-khiển-phần-cứng** (preempt/ngắt/SIP/đa-nhiệm) đầy đủ ở máy/silicon.
**CÔ LẬP FAULT:** mỗi tiến trình có ngăn-xếp + ngăn-xếp-HANDLER RIÊNG; NÉM-chưa-bắt lan tới NHÂN
(supervisor) → nhân CÔ LẬP (giết) tiến trình lỗi, tiến trình khác chạy tiếp; tiến trình tự bọc
`thử/bắt` thì phục hồi nội bộ. Ví dụ `examples/hdh_fault.giao` (chỉ-máy). Một tiến trình sập KHÔNG
kéo sập cả hệ — `thử/bắt` (mốc 3e) làm cả việc PHỤC HỒI nội bộ lẫn ranh-giới CÔ LẬP của nhân.

> **Ba lưu ý ngữ nghĩa (do NIL=0 + neo ABI số nguyên):**
> 1. Toán tử `+`/`==`/`!=` ĐA HÌNH (nối/so chuỗi-danh-sách) chỉ chạy ở **chế độ THẺ**. Compiler
>    TỰ bật thẻ khi thấy toán hạng Str/ListLit hoặc duyệt chuỗi literal (`uses_tag`). Nên `"a"+"b"`,
>    `5+"x"`, `lặp ch trong "…"` đều đúng — không còn "biên dịch-nhưng-sai".
> 2. Chuỗi/danh sách RỖNG = `NIL` = `0` (không thẻ) ⇒ trùng SỐ 0. Do đó `"" + x` cho `"0"+x`
>    (máy không phân biệt "" với số 0). Dựng chuỗi nên gieo mầm bằng phần tử thật hoặc `ghép`,
>    không gieo bằng `""`. (Đánh đổi có chủ đích để giữ idiom `l == 0`/`dài == 0`.)
> 3. **SỐ THỰC = điểm-cố-định thập phân ×10000** (số nguyên DSP, KHÔNG FPU — hợp silicon).
>    Khác thông dịch (IEEE double): (a) máy ÷ giữa hai SỐ NGUYÊN là chia-nguyên — số thực chỉ
>    khi có toán hạng `.`; (b) `rọi` số thực in tối đa **4 chữ số lẻ** (vs `:.4g`=4 chữ số *có
>    nghĩa* của thông dịch) — khớp với giá trị nhỏ, lệch khi >4 chữ số nghĩa; (c) `0.1+0.2`
>    cho ĐÚNG `0.3` (điểm-cố-định không lệch như IEEE); (d) số thực **chưa** truyền được qua
>    đối hàm người dùng (tham số máy không mang kiểu) → báo lỗi RANH GIỚI sạch; (e) lưu vào
>    danh sách/bản thì MẤT dấu-thực (in lại như số nguyên ×10000). Phạm vi |x| < ~214748.

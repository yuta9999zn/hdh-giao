# GVM trên WASM — substrate thứ 5 của máy GIAO

> Cùng cái máy trit/γ của GIAO, nay chạy trong **WebAssembly** — host bất kỳ
> (Node, trình duyệt, edge runtime) nạp được. Đây KHÔNG phải fork ngôn ngữ: GIAO vẫn
> ở Python; WASM chỉ là **một nơi nữa cho cái MÁY chạy**, sau:
>
> `Python-sim (gvm_may.py) · model chu-kỳ (hw/gvm_model.py) · Verilog (hw/gvm.v) · FPGA · → WASM`

## Vì sao WASM hợp GIAO

- **Không I/O bẩm sinh** = đúng object-capability của GIAO. `RỌI` không có sẵn trong wasm;
  host **cấp** nó như một import (`env.roi`). Năng lực là *quà của host*, y hệt `đọc_tệp`/
  `chạy` ở tầng ngôn ngữ. WASM và capability-I/O cộng hưởng.
- **Nhỏ & tất định**: `gvm.wasm` ~2KB, chạy mọi nơi, kết quả tái lập 100%.
- **Không fork**: chỉ ~110 dòng AssemblyScript mirror `gvm_may.py` cho *đủ opcode* chạy vòng
  hội tụ; ngữ nghĩa GIAO vẫn một nguồn (Python). Conformance bằng golden test (so 4 tầng).

## Tệp

| | |
|---|---|
| `gvm.ts` | GVM ĐẦY ĐỦ bằng AssemblyScript (→ wasm) — TRỌN bộ lệnh `gvm_may.py`, width 16/32-bit, heap 64K, khung gọi hàm, chuỗi/thẻ. `nap`/`chay(bit)` = export; RỌI = host import |
| `sinh.py` | Pipeline 1 ca: `examples/giaoc.giao` → biến `mã` (17 từ-lệnh) → `program.json` |
| `chay.mjs` | Harness Node 1 ca: nạp wasm, cấp năng lực RỌI, chạy vòng hội tụ |
| `sinh_tat_ca.py` | Sinh **11 ca đối chiếu** → `cases.json` (biên dịch + chạy trên GVM Python lấy golden) |
| `kiem.mjs` | Chạy 11 ca trên wasm, **so KHỚP từng output với GVM Python** |
| `gvm.wasm` | Artifact đã build (~3.7KB) |

## Dựng lại & chạy

```bash
# build wasm 1 lần (cần Node; npx tự tải assemblyscript lần đầu)
npx -y -p assemblyscript asc wasm/gvm.ts --outFile wasm/gvm.wasm --optimize --runtime stub

# demo 1 ca (vòng hội tụ):
python wasm/sinh.py && node wasm/chay.mjs

# ★ ĐỐI CHIẾU TRỌN BỘ: 11 ca chạy trên wasm phải KHỚP từng output với GVM Python
python wasm/sinh_tat_ca.py && node wasm/kiem.mjs
```

Kết quả mong đợi (KHỚP thông dịch / GVM mềm / Verilog):
```
tối=18  γ=-0.03      (niềm tin 18 vs thực tại 37 — đốm tối)
sáng=27 γ=+0.46
sáng=32 γ=+0.73
sáng=34 γ=+0.84
sáng=35 γ=+0.89
sáng=36 γ=+0.95
sáng=36 γ=+0.95      (hội tụ chạm sàn tối, viên mãn cục bộ)
```

## ★ PLAYGROUND TRÌNH DUYỆT (không Node, không cài gì) — `playground.html`

Viết GIAO và chạy NGAY trong trình duyệt, sandbox an toàn, **không cần Node/Python/cài đặt**:
`wasm/lam_playground.py` sinh ra `wasm/playground.html` TỰ CHỨA (~88 KB) — nhúng `giao.py` +
`chuẩn.giao` (base64) và dùng **Pyodide** (CPython→WASM) chạy **TRỌN trình thông dịch** trong
trình duyệt. Mở bằng `file://` là dùng (chỉ cần internet tải Pyodide từ CDN lần đầu).

```bash
python wasm/lam_playground.py     # sinh lại playground.html (chạy lại khi sửa giao.py/chuẩn.giao)
# rồi mở wasm/playground.html bằng trình duyệt bất kỳ — Ctrl-Enter để chạy

# (tuỳ chọn) KIỂM CHỨNG bằng trình duyệt THẬT (headless Chrome/Edge, qua puppeteer-core):
npm install puppeteer-core        # dev-only, KHÔNG tải Chromium (dùng Chrome/Edge sẵn có)
node wasm/kiem_playground.mjs     # mở playground → đợi Pyodide → chạy GIAO → so kết quả
```
> ✅ **Đã kiểm chứng LIVE**: `kiem_playground.mjs` mở `playground.html` trong headless Chrome,
> chạy chương trình GIAO (map/closure/ba-trị) qua Pyodide → output đúng từng dòng
> (`5`, `7`, `[1, 4, 9]`, `ẩn`). Playground hoạt động thật trong trình duyệt, không Node runtime.
> Đây là câu trả lời cho lo ngại "Node nhiều lỗ hổng": playground chạy trong **sandbox trình
> duyệt** (không fs/net mặc định), KHÔNG Node. Cùng `gvm.wasm` (lõi máy) cũng chạy ở browser.

## Trong trình duyệt (lõi máy gvm.wasm)

Cùng `gvm.wasm` chạy được ở browser — `WebAssembly.instantiate(bytes, {env:{roi, abort}})`,
`roi` đẩy ra DOM/console. Không cần Python/Node ở runtime: máy GIAO chạy bằng wasm thuần,
host chỉ cấp năng lực hiển thị.

## Phạm vi đã đạt (20/20 ca KHỚP wasm ⟷ Python)

GVM-wasm nay chạy **MỌI chương trình do giaoc sinh** — đã đối chiếu byte-for-byte:

| ca | nội dung |
|---|---|
| 7,8 | danh sách (heap cons-cell) + đệ quy: `tổng([..])` |
| 9 | chuỗi + `dài`/`ghép` trên heap: `"Giao thoa"` |
| 10 | hàm NHIỀU THAM SỐ (khung) + đệ quy: `luỹ(2,10)=1024` |
| 11 | `l[i]` + so sánh `</>/==` + hàm trợ giúp |
| 12 | eval dispatch theo thẻ số |
| **13** | **THẺ 32-bit**: `là_số`/`là_ds` + `==` cấu trúc + `+` đa hình |
| giai_thua | đệ quy `giai_thừa(5)=120` |
| hoi_tu / →mã | vòng hội tụ CDFL `tối=18 → sáng=36` |
| **★ giaoc.giao** | **trình biên dịch viết bằng GIAO (8357 từ-lệnh, 32-bit) chạy trên WASM → tự sinh bytecode** |

Bộ lệnh đầy đủ: số học/so-sánh width-aware (16/32-bit), heap 64K, khung gọi hàm
(`GỌI_N`/`THAM_I`/`TRẢ_VỀ_N`), nhảy gián tiếp, chuỗi, thẻ (trong suốt — chỉ `RỌI_CHUỖI`/
`RỌI_DS` gỡ thẻ). Conformance bằng `kiem.mjs` (golden từ GVM Python).

Còn ở Python (không thuộc tầng máy): trình thông dịch đầy đủ + LLM `tim` + capability I/O.
WASM là substrate cho *MÁY* (bytecode đã biên dịch), không phải cho cả interpreter — đây là
lựa chọn **KHÔNG fork ngôn ngữ** có chủ đích (xem CHANGELOG).

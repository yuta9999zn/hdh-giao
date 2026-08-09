# GVM trên FPGA — nạp lõi quyết định tác tử CDFL lên silicon thật

Gói này biến **lõi quyết định** của tác tử CDFL (Ψ học được + lookahead + cổng phê duyệt,
biên dịch từ `examples/tac_tu_may.giao`) thành một thiết kế FPGA **tổng-hợp-được**, xuất
kết quả `RỌI` ra **LED + UART** ngoài đời. Trái tim LLM ở ngoài (cơ quan I/O); cái neo lên
phần cứng là lõi số nguyên — chạy như sóng điện qua các cổng NAND.

> ⚠ **PHẠM-VI (trung-thực):** gói này là core tác-tử BẢN-ĐẦU (`gvm_core.v`, Jun-2025, con-trỏ 8-bit/heap-10-bit). Nó **KHÔNG** chứa các tiến-hoá sau của core chính `../gvm.v` (503 dòng): ba-trị silicon (ẩn/tối), γ-scheduler biết-học, SIP bảo-vệ-nhớ, 4 nhân HĐH. Đã **mô-phỏng iverilog đúng** nhưng **CHƯA synth** (yosys chưa cài → chưa có bitstream). Muốn nạp silicon CDFL ĐẦY-ĐỦ cần tái-sinh gói FPGA từ `../gvm.v` trước.

## Tệp
| Tệp | Vai trò |
|---|---|
| `gvm_core.v` | CPU GVM (dựng từ NAND) — bản FPGA: rom 2048 · ram 1024 · stack/return-stack 256; ROM nạp `$readmemh("program.hex")` |
| `uart_tx.v` | Bộ phát UART 8N1 |
| `gvm_top.v` | Top-level: bọc lõi + LED (byte thấp RỌI, đèn DỪNG) + UART (mỗi RỌI gửi 2 byte cao/thấp) |
| `program.hex` | ROM lệnh (1697 từ-lệnh) — sinh bởi `python ../lam_verilog.py` (hoặc `giaoc`) |
| `icebreaker.pcf` | Ràng buộc chân iCE40 (iCEBreaker) — dòng mã nguồn mở |
| `arty_a7.xdc` | Ràng buộc chân Xilinx (Arty A7) — Vivado |

**Số liệu tài nguyên (đã đo):** đỉnh stack 117, return-stack 24, heap 474 ô → tổng nhớ ~58 kbit,
vừa cả FPGA nhỏ. Chạy 1,191,838 chu kỳ rồi DỪNG. Đã **mô phỏng kiểm chứng** (iverilog):
UART xuất đúng **13 giá trị** — `[65533, 0]` lặp 6 lần rồi `0` (−3 ≡ 65533 16-bit), khớp 4 tầng phần mềm.

## Sinh lại program.hex
```
python ../lam_verilog.py        # biên dịch tac_tu_may.giao → program.hex (+ kiểm bằng iverilog)
```

## A) Lattice iCE40 — dòng MÃ NGUỒN MỞ (khuyến nghị cho "nạp thật")
Cài bộ công cụ (gồm yosys, nextpnr-ice40, icepack, openFPGALoader): tải **OSS CAD Suite**
(github.com/YosysHQ/oss-cad-suite-build/releases) — giải nén, thêm `bin/` vào PATH.
```
# (program.hex phải ở thư mục hiện hành để $readmemh nạp lúc synth)
yosys -p "synth_ice40 -top gvm_top -json gvm.json" gvm_core.v uart_tx.v gvm_top.v
nextpnr-ice40 --up5k --package sg48 --pcf icebreaker.pcf --json gvm.json --asc gvm.asc
icepack gvm.asc gvm.bin
openFPGALoader -b ice40_generic gvm.bin      # hoặc: iceprog gvm.bin
```
Cắm USB-UART, mở terminal 115200 8N1 → đọc chuỗi byte (mỗi RỌI = 2 byte cao/thấp:
`FF FD` = 65533, `00 00` = 0). Trọn 13 giá trị ⇒ 26 byte: `FF FD 00 00` lặp 6 lần rồi
`00 00`. LED đỏ sáng = CPU đã DỪNG.

## B) Xilinx — Vivado
1. Tạo project, thêm `gvm_core.v uart_tx.v gvm_top.v`; **Add Sources → program.hex** (để cạnh nguồn).
2. Set top = `gvm_top`; chỉnh `CLK_HZ` cho khớp clock bo (Arty = 100_000_000).
3. Thêm `arty_a7.xdc`. Generate Bitstream → Open Hardware Manager → Program Device.

## C) Intel/Altera — Quartus
1. New Project, thêm 3 tệp `.v` + `program.hex`; top = `gvm_top`; đặt `CLK_HZ`.
2. Gán chân (Pin Planner) theo bo (clk/rst_n/uart_tx/led); Compile → Programmer (.sof) → nạp.

## Lưu ý phần cứng thật
- `OP_NHAN`/`OP_CHIA` đang để `*`/`/` suy ra mạch — tổng hợp được nhưng nên thay bằng
  multiplier (DSP) / divider nhiều-chu-kỳ nếu cần tần số cao. Lõi tác tử KHÔNG dùng phép chia
  trên đường nóng nên ổn ở clock vừa phải.
- Sửa cực tính `rst_n` và `CLK_HZ` cho đúng bo. Đổi gán chân LED nếu không gắn PMOD 8-LED.

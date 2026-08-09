# -*- coding: utf-8 -*-
"""
lam_trap.py — ★★ GỌI-HỆ TRÊN SILICON: tiến trình do HĐH sinh ra, chạy trên CỔNG LOGIC THẬT,
xin nhân phục vụ qua bắt tay trap_valid ⟷ trap_ack.
================================================================================
Đường đi:
  chương trình GIAO (tập con máy)  →  giaoc  →  bytecode  →  program_trap.hex
  gvm.v (CPU dựng từ NAND, nay có opcode 72 GỌI_HỆ)  →  iverilog  →  vvp
  trap_tb.v đóng vai NHÂN: thấy trap_valid thì đọc số hiệu + đối, phục vụ, trả kết quả.

Chạy:  python hw/lam_trap.py
"""
import os, sys, subprocess, shutil

GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW  = os.path.join(GỐC, "hw")
sys.path.insert(0, GỐC)
import giaoc

# ── 1) chương trình: xin nhân vài việc rồi tính trên kết quả ──
NGUỒN = """
đặt a = gọi_hệ(11)          # 11 = "ở"  → nhân trả 700 (quy ước testbench)
rọi a
đặt b = gọi_hệ(50, 21)      # 50 = "nhân đôi" → nhân trả 42
rọi b
rọi a + b
đặt c = gọi_hệ(50, b)       # xin tiếp trên chính kết quả vừa nhận
rọi c
đặt d = gọi_hệ(51, 5, 9)              # ★ HAI đối  → nhân trả 5 + 9
rọi d
đặt e = gọi_hệ(52, 1, 2, 3)           # ★ BA đối   → nhân trả 1 + 20 + 300 (chứng minh ĐÚNG THỨ TỰ)
rọi e
rọi gọi_hệ(52, a, d, gọi_hệ(50, 4))   # lồng nhau: đối tự nó là một lời xin khác
"""

words = giaoc.compile_program(giaoc.Parser(giaoc.tokenize(NGUỒN)).parse(), False)
with open(os.path.join(HW, "program_trap.hex"), "w") as f:
    f.write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
print(f"1) GIAO → bytecode: {len(words)} từ-lệnh (có opcode 72 GỌI_HỆ)")

# ── 2) gvm.v → gvm_trap.v (boot ROM → $readmemh) ──
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin")
i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_trap.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("program_trap.hex", rom);\n\n' + gv[i1:])
print("2) gvm.v → gvm_trap.v (nạp ROM từ tệp)")

# ── 3) testbench = NHÂN bằng phần cứng ──
TB = r'''`timescale 1ns/1ps
// trap_tb.v — TESTBENCH ĐÓNG VAI NHÂN: phục vụ gọi-hệ cho CPU trên cổng logic.
module trap_tb;
  reg clk = 0, rst = 1;
  wire [15:0] out_data;  wire out_valid, halt;
  wire        trap_valid; wire [7:0] trap_num, trap_nargs;
  wire [15:0] trap_arg, trap_arg1, trap_arg2;
  reg         trap_ack = 0; reg [15:0] trap_ret = 0;
  integer     n_trap = 0, n_out = 0, cyc = 0;

  gvm #(.MEM(4096)) dut(.clk(clk), .rst(rst),
        .out_data(out_data), .out_valid(out_valid), .halt(halt),
        .dbg_a(16'd0), .dbg_re(1'b0), .dbg_we(1'b0), .dbg_wd(0),
        .trap_valid(trap_valid), .trap_num(trap_num), .trap_arg(trap_arg),
        .trap_arg1(trap_arg1), .trap_arg2(trap_arg2),
        .trap_nargs(trap_nargs), .trap_ack(trap_ack), .trap_ret(trap_ret));

  always #5 clk = ~clk;
  initial begin #12 rst = 0; #200000 begin $display("HET GIO"); $finish; end end

  always @(posedge clk) if (!rst) cyc = cyc + 1;

  // ★ NHÂN (bằng phần cứng): thấy trap_valid → phục vụ → trả kết quả → ack đúng 1 chu kỳ
  always @(posedge clk) begin
    if (!rst && trap_valid && !trap_ack) begin
      n_trap = n_trap + 1;
      case (trap_num)
        8'd11: trap_ret <= 16'd700;                 // "ở"        → 700
        8'd50: trap_ret <= trap_arg << 1;           // "nhân đôi" → 2×đối
        8'd51: trap_ret <= trap_arg + trap_arg1;                        // ★ 2 đối
        8'd52: trap_ret <= trap_arg + 16'd10*trap_arg1 + 16'd100*trap_arg2;  // ★ 3 đối, có thứ tự
        default: trap_ret <= 16'hFFFF;              // không hiểu → −1
      endcase
      $display("   [nhan] chu ky %0d: TRAP so=%0d nargs=%0d doi=%0d,%0d,%0d",
               cyc, trap_num, trap_nargs, trap_arg, trap_arg1, trap_arg2);
      trap_ack <= 1'b1;
    end else trap_ack <= 1'b0;
  end

  always @(posedge clk) if (out_valid) begin
    n_out = n_out + 1;
    $display("   [CPU ] chu ky %0d: ROI = %0d", cyc, out_data);
  end

  always @(posedge clk) if (halt) begin
    $display("   CPU DUNG sau %0d chu ky · %0d lan trap · %0d lan roi", cyc, n_trap, n_out);
    $finish;
  end
endmodule
'''
open(os.path.join(HW, "trap_tb.v"), "w", encoding="utf-8").write(TB)
print("3) trap_tb.v — testbench đóng vai NHÂN (phục vụ trap ngay trên cổng logic)")

# ── 4) chạy iverilog ──
iv = shutil.which("iverilog") or r"D:\iverilog\bin\iverilog.exe"
vp = shutil.which("vvp") or r"D:\iverilog\bin\vvp.exe"
if not os.path.exists(iv):
    print("⚠ Không thấy iverilog — bỏ qua bước mô phỏng.")
    sys.exit(0)

print("\n4) BIÊN DỊCH VERILOG + CHẠY (cổng logic thật):")
# iverilog không nuốt được đường dẫn có dấu tiếng Việt ⇒ dùng TÊN TƯƠNG ĐỐI với cwd=hw
r = subprocess.run([iv, "-o", "gvm_trap.vvp", "gvm_trap.v", "trap_tb.v"],
                   capture_output=True, text=True, cwd=HW)
if r.returncode != 0:
    print(r.stdout + r.stderr); sys.exit(1)
r = subprocess.run([vp, "gvm_trap.vvp"], capture_output=True, text=True, cwd=HW)
print(r.stdout + r.stderr)

# ── 5) đối chiếu với GVM phần mềm ──
sys.path.insert(0, GỐC)
from gvm_may import GVM
g = GVM(words, world={}, bit=16)
kq = []
for _ in range(200):
    g.run(max_steps=10000)
    if getattr(g, "trap_pending", False):
        số, đối = g.trap
        if   số == 11: ret = 700
        elif số == 50: ret = (đối[0] << 1) & 0xFFFF
        elif số == 51: ret = (đối[0] + đối[1]) & 0xFFFF
        elif số == 52: ret = (đối[0] + 10*đối[1] + 100*đối[2]) & 0xFFFF
        else:          ret = 0xFFFF
        import gvm_may as _gm
        g.stack.append(_gm.KNOWN(ret)); g.trap = None; g.trap_pending = False
        kq.append((số, ret))
        continue
    if getattr(g, "halted", False): break
pm = [x[2] for x in g.xuất if x[0] == "ô"]          # ["ô", trạng, GIÁ TRỊ]
import re
pc = [int(m) for m in re.findall(r"ROI = (\d+)", r.stdout + r.stderr)]
print("5) ĐỐI CHIẾU phần mềm ⟷ phần cứng (cổng logic):")
print(f"   phần mềm (gvm_may): {pm}")
print(f"   phần cứng (gvm.v) : {pc}")
print(f"   trap phần mềm     : {kq}")
print("   " + ("✓ TRÙNG KHÍT — cùng một ngữ nghĩa gọi-hệ từ GIAO xuống cổng logic"
               if pm == pc and pm else "✗ LỆCH — phải sửa trước khi tin"))
sys.exit(0 if (pm == pc and pm) else 1)

# -*- coding: utf-8 -*-
"""
lam_verilog32.py — LÕI GVM 32-BIT trên VERILOG: chạy chương trình HEAP (ABI thẻ) gate-level.
================================================================================
Lõi 16-bit (lam_verilog.py) chỉ chạy chương trình vô hướng. Ở đây WORD=32 → bit-30 THẺ hoạt
động → danh sách/heap + là_số/là_ds + GỌI HÀM theo khung chạy TRÊN CỔNG LOGIC (iverilog),
đối chiếu BYTE với GVM phần mềm. Đây là điều cần để nhân nặng-heap tiến tới gate-level.

  python hw/lam_verilog32.py
"""
import sys, os, subprocess, shutil, io, contextlib
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from giaoc import compile_source_bit
from gvm_may import GVM

SRC = open(os.path.join(GỐC, "examples", "heap32_gvm.giao"), encoding="utf-8").read()
words, bit = compile_source_bit(SRC)
assert bit == 32, "chương trình này phải là 32-bit (dùng thẻ)"

# tham chiếu PHẦN MỀM
g = GVM(words, world={}, bit=32)
buf = io.StringIO()
with contextlib.redirect_stdout(buf): g.run(max_steps=10_000_000)
pm = [int(l.split("=")[1].split()[0]) for l in buf.getvalue().splitlines() if l.strip().startswith("sáng=")]

# 1) ROM lệnh (16-bit/lệnh) → hex
open(os.path.join(HW, "program32.hex"), "w").write(
    "\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")

# 2) gvm.v → gvm_prog32.v (boot ROM cứng → $readmemh)
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_prog32.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("program32.hex", rom);\n\n' + gv[i1:])

# 3) testbench — WORD=32, out_data 32-bit, RAM 8192 (đủ heap)
tb = '''`timescale 1ns/1ps
module run32_tb;
  reg clk=0, rst=1; reg [31:0] ncyc=0;
  wire [31:0] out_data; wire out_valid, halt;
  gvm #(.MEM(8192), .WORD(32)) dut(.clk(clk),.rst(rst),.out_data(out_data),.out_valid(out_valid),.halt(halt));
  always #5 clk = ~clk;
  initial begin #12 rst=0; #20000000 begin $display("HET GIO"); $finish; end end
  always @(posedge clk) begin
    if (!rst) ncyc <= ncyc + 1;
    if (out_valid) $display("ROI=%0d", $signed(out_data));
    if (halt) begin $display("CPU DUNG."); $display("CYCLES=%0d", ncyc); $finish; end
  end
endmodule
'''
open(os.path.join(HW, "run32_tb.v"), "w").write(tb)
print(f"Đã sinh: program32.hex ({len(words)} từ-lệnh, 32-bit), gvm_prog32.v, run32_tb.v")

iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
if not os.path.exists(iv):
    print("Chưa có iverilog — chạy tay: cd hw && iverilog -o p.vvp gvm_prog32.v run32_tb.v && vvp p.vvp")
    sys.exit(0)
subprocess.run([iv, "-o", "gvm_prog32.vvp", "gvm_prog32.v", "run32_tb.v"], cwd=HW, check=True)
r = subprocess.run([vvp, "gvm_prog32.vvp"], cwd=HW, capture_output=True, text=True)
hw_out = [int(l.split("=")[1]) for l in r.stdout.splitlines() if l.startswith("ROI=")]
cyc = next((l.split("=")[1] for l in r.stdout.splitlines() if l.startswith("CYCLES=")), "?")

print("=" * 70)
print("LÕI GVM 32-BIT TRÊN VERILOG (iverilog) — chương trình HEAP có THẺ")
print("=" * 70)
print(f"   PHẦN MỀM (GVM 32-bit) : {pm}")
print(f"   VERILOG (gvm.v WORD=32): {hw_out}   (dừng sau {cyc} chu kỳ)")
print(f"   {'✅ TRÙNG KHỚP — lõi heap 32-bit chạy GATE-LEVEL' if hw_out == pm else '✗ LỆCH'}")
if "CPU DUNG." not in r.stdout:
    print("   ⚠ CPU chưa DỪNG:", r.stdout[-300:])

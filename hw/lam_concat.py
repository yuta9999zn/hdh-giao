# -*- coding: utf-8 -*-
"""Chẩn đoán: nối chuỗi tích lũy gate-level — tìm vòng/heap-addr lệch (double-tag)."""
import sys, os, subprocess, shutil, io, contextlib
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from giaoc import compile_source_bit
from gvm_may import GVM

words, bit = compile_source_bit(open(os.path.join(GỐC, "examples", "heap32_concat.giao"), encoding="utf-8").read())
g = GVM(words, world={}, bit=32)
with contextlib.redirect_stdout(io.StringIO()): g.run(max_steps=20_000_000)
pm = [g.s(x[2]) for x in g.xuất]   # dãy số dài(s)

open(os.path.join(HW, "prog_cc.hex"), "w").write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_cc.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  integer __zz;\n  initial $readmemh("prog_cc.hex", rom);\n'
              '  initial begin for(__zz=0;__zz<16384;__zz=__zz+1) begin ram[__zz]=0; stk_st[__zz]=2\'b01; end end\n\n' + gv[i1:])
tb = '''`timescale 1ns/1ps
module cc_tb;
  reg clk=0, rst=1; wire [31:0] od; wire ov, h; wire [2:0] ok; integer n=0;
  gvm #(.MEM(16384), .WORD(32)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin n=n+1;
    if (ov && ok==3'd0) $display("NUM=%0d", $signed(od));
    if (h) begin $display("DUNG"); $finish; end
    if (n>=3000000) begin $display("HETGIO"); $finish; end
  end endmodule
'''
open(os.path.join(HW, "cc_tb.v"), "w").write(tb)
iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
subprocess.run([iv, "-o", "gvm_cc.vvp", "gvm_cc.v", "cc_tb.v"], cwd=HW, check=True)
r = subprocess.run([vvp, "gvm_cc.vvp"], cwd=HW, capture_output=True, text=True, timeout=400)
hw = [int(l.split("=")[1]) for l in r.stdout.splitlines() if l.startswith("NUM=")]
print("PM:", pm)
print("HW:", hw)
print("DỪNG:", "DUNG" in r.stdout)
for k in range(max(len(pm), len(hw))):
    a = pm[k] if k < len(pm) else "—"; b = hw[k] if k < len(hw) else "—"
    if a != b: print(f"★ LỆCH ĐẦU TIÊN ở vòng {k+1}: PM={a} HW={b}"); break
else:
    print("✅ KHỚP TOÀN BỘ")

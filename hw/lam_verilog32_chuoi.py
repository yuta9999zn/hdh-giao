# -*- coding: utf-8 -*-
"""
lam_verilog32_chuoi.py — LÕI 32-BIT GIÀU: CLOSURE + CHUỖI chạy GATE-LEVEL.
================================================================================
Dùng 3 opcode vừa thêm vào hw/gvm.v: ĐỔI, RỌI_CHUỖI, GỌI_CLOSURE.
Verilog xuất: out_kind = 0(SỐ) · 1(KÝ-TỰ) · 2(HẾT-CHUỖI). Harness GHÉP ký tự → chuỗi,
rồi đối chiếu với GVM phần mềm (số ↔ số, chuỗi ↔ chuỗi).
"""
import sys, os, subprocess, shutil, io, contextlib
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from giaoc import compile_source_bit
from gvm_may import GVM

SRC = open(os.path.join(GỐC, "examples", "heap32_chuoi.giao"), encoding="utf-8").read()
words, bit = compile_source_bit(SRC)
assert bit == 32

# tham chiếu PHẦN MỀM → danh sách ["số",n] | ["chuỗi",s]
g = GVM(words, world={}, bit=32)
with contextlib.redirect_stdout(io.StringIO()): g.run(max_steps=10_000_000)
pm = [("chuỗi", x[1]) if x[0] == "chuỗi" else ("số", x[2]) for x in g.xuất]

open(os.path.join(HW, "prog32c.hex"), "w").write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_p32c.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("prog32c.hex", rom);\n\n' + gv[i1:])

tb = '''`timescale 1ns/1ps
module c32_tb;
  reg clk=0, rst=1; wire [31:0] od; wire ov, h; wire [2:0] ok;
  gvm #(.MEM(8192), .WORD(32)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; #30000000 begin $display("HET GIO"); $finish; end end
  always @(posedge clk) begin
    if (ov) begin
      if      (ok==2'd0) $display("NUM=%0d", $signed(od));
      else if (ok==2'd1) $display("CHR=%0d", od);
      else               $display("SEND");
    end
    if (h) begin $display("DUNG"); $finish; end
  end
endmodule
'''
open(os.path.join(HW, "c32_tb.v"), "w").write(tb)

iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
if not os.path.exists(iv):
    print("Chưa có iverilog — chạy tay: cd hw && iverilog -o c.vvp gvm_p32c.v c32_tb.v && vvp c.vvp"); sys.exit(0)
subprocess.run([iv, "-o", "gvm_p32c.vvp", "gvm_p32c.v", "c32_tb.v"], cwd=HW, check=True)
r = subprocess.run([vvp, "gvm_p32c.vvp"], cwd=HW, capture_output=True, text=True)

# GHÉP luồng xuất phần cứng → [("số",n)|("chuỗi",s)]
hw_out, buf = [], []
for l in r.stdout.splitlines():
    if l.startswith("NUM="): hw_out.append(("số", int(l.split("=")[1])))
    elif l.startswith("CHR="): buf.append(chr(int(l.split("=")[1])))
    elif l.startswith("SEND"): hw_out.append(("chuỗi", "".join(buf))); buf = []

print("=" * 72)
print("LÕI GVM 32-BIT TRÊN VERILOG — CLOSURE + CHUỖI (ĐỔI · RỌI_CHUỖI · GỌI_CLOSURE)")
print("=" * 72)
print(f"   PHẦN MỀM : {pm}")
print(f"   VERILOG  : {hw_out}")
print(f"   {'✅ TRÙNG KHỚP — closure + chuỗi chạy GATE-LEVEL' if hw_out == pm else '✗ LỆCH'}")

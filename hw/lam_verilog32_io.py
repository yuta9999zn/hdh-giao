# -*- coding: utf-8 -*-
"""
lam_verilog32_io.py — LÕI 32-BIT GIÀU: SỐ THỰC điểm-cố-định + IN DANH SÁCH gate-level.
================================================================================
Dùng các opcode vừa thêm vào hw/gvm.v: FNHÂN · FCHIA · RỌI_THỰC · RỌI_DS.
GVM là máy SỐ NGUYÊN (không FPU) → số thực = round(x×10000), × và ÷ qua nhân/chia 64-bit (DSP).
Verilog xuất out_kind: 0(SỐ) · 3(SỐ-THỰC ×10000) · 4(PHẦN-TỬ-DS) · 5(HẾT-DS).
Harness định dạng số thực (fmt_fixed) + ghép danh-sách, rồi đối chiếu với GVM phần mềm.

  python hw/lam_verilog32_io.py
"""
import sys, os, subprocess, shutil, io, contextlib
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from giaoc import compile_source_bit
from gvm_may import GVM, fmt_fixed

SRC = open(os.path.join(GỐC, "examples", "heap32_io.giao"), encoding="utf-8").read()
words, bit = compile_source_bit(SRC)
assert bit == 32

# tham chiếu PHẦN MỀM → [("thực",s) | ("số",n) | ("ds",[…])]
g = GVM(words, world={}, bit=32)
with contextlib.redirect_stdout(io.StringIO()): g.run(max_steps=10_000_000)
def _pm(x):
    if x[0] == "ds":    return ("ds", list(x[1]))
    if x[0] == "chuỗi": return ("thực", x[1])      # RỌI_THỰC → chuỗi thập phân
    return ("số", x[2])                             # RỌI (ô) → số
pm = [_pm(x) for x in g.xuất]

open(os.path.join(HW, "prog32io.hex"), "w").write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_p32io.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("prog32io.hex", rom);\n\n' + gv[i1:])

tb = '''`timescale 1ns/1ps
module io32_tb;
  reg clk=0, rst=1; wire [31:0] od; wire ov, h; wire [2:0] ok;
  gvm #(.MEM(8192), .WORD(32)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; #30000000 begin $display("HET GIO"); $finish; end end
  always @(posedge clk) begin
    if (ov) begin
      if      (ok==3'd0) $display("NUM=%0d", $signed(od));
      else if (ok==3'd3) $display("FIX=%0d", $signed(od));
      else if (ok==3'd4) $display("DSE=%0d", $signed(od));
      else if (ok==3'd5) $display("DSEND");
    end
    if (h) begin $display("DUNG"); $finish; end
  end
endmodule
'''
open(os.path.join(HW, "io32_tb.v"), "w").write(tb)

iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
if not os.path.exists(iv):
    print("Chưa có iverilog — chạy tay: cd hw && iverilog -o io.vvp gvm_p32io.v io32_tb.v && vvp io.vvp"); sys.exit(0)
subprocess.run([iv, "-o", "gvm_p32io.vvp", "gvm_p32io.v", "io32_tb.v"], cwd=HW, check=True)
r = subprocess.run([vvp, "gvm_p32io.vvp"], cwd=HW, capture_output=True, text=True)

# GHÉP luồng xuất phần cứng → [("thực",s) | ("số",n) | ("ds",[…])]
hw_out, ds = [], []
for l in r.stdout.splitlines():
    if   l.startswith("NUM="): hw_out.append(("số", int(l.split("=")[1])))
    elif l.startswith("FIX="): hw_out.append(("thực", fmt_fixed(int(l.split("=")[1]))))
    elif l.startswith("DSE="): ds.append(int(l.split("=")[1]))
    elif l.startswith("DSEND"): hw_out.append(("ds", ds)); ds = []

print("=" * 74)
print("LÕI GVM 32-BIT TRÊN VERILOG — SỐ THỰC + DANH SÁCH (FNHÂN · FCHIA · RỌI_THỰC · RỌI_DS)")
print("=" * 74)
print(f"   PHẦN MỀM : {pm}")
print(f"   VERILOG  : {hw_out}")
ok = hw_out == pm and "DUNG" in r.stdout
print(f"   {'✅ TRÙNG KHỚP — số thực điểm-cố-định + in danh-sách chạy GATE-LEVEL' if ok else '✗ LỆCH'}")
sys.exit(0 if ok else 1)

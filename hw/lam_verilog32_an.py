# -*- coding: utf-8 -*-
"""
lam_verilog32_an.py — RÀO BA-TRỊ 'ẩn' chạy GATE-LEVEL: ô ngăn xếp MANG TRẠNG-THÁI.
================================================================================
Verilog `hw/gvm.v` nay có mảng `stk_st` (ẩn/sáng/tối) SONG SONG ngăn xếp:
  • `ẨN` đẩy ô ẩn · số học LAN TRUYỀN ẩn (chạm ẩn → ẩn, val=0) · FCHIA chia-0 → ẩn ·
  • TRẢ_VỀ_N giữ trạng-thái (hàm rơi-khỏi-thân trả ẩn) · NHẢY_NẾU_0 coi ẩn ≠ 0 ·
  • RỌI/RỌI_AUTO/RỌI_THỰC gặp ẩn → out_kind=6 (dấu ẩn).
Đối chiếu BYTE với GVM phần mềm: ẩn↔ẩn, sáng↔số, số-thực↔chuỗi.

  python hw/lam_verilog32_an.py
"""
import sys, os, subprocess, shutil, io, contextlib
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from giaoc import compile_source_bit
from gvm_may import GVM, fmt_fixed, ST_AN

SRC = open(os.path.join(GỐC, "examples", "heap32_an.giao"), encoding="utf-8").read()
words, bit = compile_source_bit(SRC)
assert bit == 32

# tham chiếu PHẦN MỀM → [("ẩn",) | ("số",n) | ("thực",s)]
g = GVM(words, world={}, bit=32)
with contextlib.redirect_stdout(io.StringIO()): g.run(max_steps=10_000_000)
def _pm(x):
    if x[0] == "ô":     return ("ẩn",) if x[1] == ST_AN else ("số", g.s(x[2]))
    if x[0] == "chuỗi": return ("thực", x[1])
    return ("?", x)
pm = [_pm(x) for x in g.xuất]

open(os.path.join(HW, "prog32an.hex"), "w").write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_p32an.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("prog32an.hex", rom);\n\n' + gv[i1:])

tb = '''`timescale 1ns/1ps
module an32_tb;
  reg clk=0, rst=1; wire [31:0] od; wire ov, h; wire [2:0] ok;
  gvm #(.MEM(8192), .WORD(32)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; #30000000 begin $display("HET GIO"); $finish; end end
  always @(posedge clk) begin
    if (ov) begin
      if      (ok==3'd0) $display("NUM=%0d", $signed(od));
      else if (ok==3'd3) $display("FIX=%0d", $signed(od));
      else if (ok==3'd6) $display("AN");
      else if (ok==3'd7) $display("OUT=%0d", $signed(od));
    end
    if (h) begin $display("DUNG"); $finish; end
  end
endmodule
'''
open(os.path.join(HW, "an32_tb.v"), "w").write(tb)

iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
if not os.path.exists(iv):
    print("Chưa có iverilog — chạy tay: cd hw && iverilog -o an.vvp gvm_p32an.v an32_tb.v && vvp an.vvp"); sys.exit(0)
subprocess.run([iv, "-o", "gvm_p32an.vvp", "gvm_p32an.v", "an32_tb.v"], cwd=HW, check=True)
r = subprocess.run([vvp, "gvm_p32an.vvp"], cwd=HW, capture_output=True, text=True)

hw_out = []
for l in r.stdout.splitlines():
    if   l.startswith("NUM="): hw_out.append(("số", int(l.split("=")[1])))
    elif l.startswith("FIX="): hw_out.append(("thực", fmt_fixed(int(l.split("=")[1]))))
    elif l.strip() == "AN":    hw_out.append(("ẩn",))
    elif l.startswith("OUT="): hw_out.append(("xuất", int(l.split("=")[1])))

print("=" * 76)
print("RÀO BA-TRỊ 'ẩn' TRÊN VERILOG — ô ngăn xếp mang TRẠNG-THÁI (ẩn ↔ sáng) GATE-LEVEL")
print("=" * 76)
print(f"   PHẦN MỀM : {pm}")
print(f"   VERILOG  : {hw_out}")
ok = hw_out == pm and "DUNG" in r.stdout
print(f"   {'✅ TRÙNG KHỚP — ẩn (DE/chưa-biết) lan-truyền đúng ở SILICON' if ok else '✗ LỆCH'}")
if not ok: print("   stdout:", r.stdout[-400:])
sys.exit(0 if ok else 1)

# -*- coding: utf-8 -*-
"""
lam_sync.py — ĐỒNG-BỘ-HOÁ (hdh_sync_may.giao: lock/semaphore + đánh-thức γ-công-bằng) chạy GATE-LEVEL.
================================================================================
Bản máy của lib_đồng_bộ → biên-dịch GVM → chạy trên hw/gvm.v (iverilog), đối-chiếu BYTE luồng chuỗi
với GVM phần mềm. Chứng: sync primitives (kể cả wake σ-cao-nhất) thực-thi tới mức CỔNG LOGIC.
  python hw/lam_sync.py
"""
import sys, os, subprocess, shutil, io, contextlib
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from giaoc import compile_source_bit
from gvm_may import GVM

words, bit = compile_source_bit(open(os.path.join(GỐC, "hdh_sync_may.giao"), encoding="utf-8").read())
assert bit == 32
print(f"   sync máy → {len(words)} từ-lệnh GVM (32-bit)")
g = GVM(words, world={}, bit=bit)
with contextlib.redirect_stdout(io.StringIO()): g.run(max_steps=80_000_000)
pm = [("chuỗi", x[1]) for x in g.xuất if x[0] == "chuỗi"]
print(f"   phần mềm: {len(pm)} dòng, dừng sau {g.steps_run} bước")

open(os.path.join(HW, "prog_sync.hex"), "w").write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_sync.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  integer __zz;\n  initial $readmemh("prog_sync.hex", rom);\n'
              '  initial begin for(__zz=0; __zz<32768; __zz=__zz+1) begin ram[__zz]=0; stk_st[__zz]=2\'b01; end end\n\n'
    + gv[i1:])

tb = '''`timescale 1ns/1ps
module sync_tb;
  reg clk=0, rst=1; wire [31:0] od; wire ov, h; wire [2:0] ok; integer n=0;
  gvm #(.MEM(32768), .WORD(32)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin n=n+1;
    if (ov) begin
      if      (ok==3'd1) $display("CHR=%0d", od);
      else if (ok==3'd2) $display("SEND");
      else if (ok==3'd0) $display("NUM=%0d", $signed(od));
    end
    if (h) begin $display("DUNG n=%0d", n); $finish; end
    if (n>=6000000) begin $display("HETGIO"); $finish; end
  end endmodule
'''
open(os.path.join(HW, "sync_tb.v"), "w").write(tb)
iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
if not os.path.exists(iv): print("Chưa có iverilog."); sys.exit(0)
print("   biên dịch + chạy iverilog...")
subprocess.run([iv, "-o", "gvm_sync.vvp", "gvm_sync.v", "sync_tb.v"], cwd=HW, check=True)
r = subprocess.run([vvp, "gvm_sync.vvp"], cwd=HW, capture_output=True, text=True, timeout=900)

hw_out, buf = [], []
for l in r.stdout.splitlines():
    if   l.startswith("CHR="): buf.append(chr(int(l.split("=")[1])))
    elif l.startswith("SEND"): hw_out.append(("chuỗi", "".join(buf))); buf = []
    elif l.startswith("NUM="): hw_out.append(("số", int(l.split("=")[1])))
ncyc = next((l.split("n=")[1] for l in r.stdout.splitlines() if l.startswith("DUNG")), "?")

print("=" * 78)
print(f"SYNC PRIMITIVES ({len(words)} từ) CHẠY GATE-LEVEL — dừng {ncyc} chu kỳ")
print("=" * 78)
khớp = hw_out == pm
print(f"   phần mềm {len(pm)} dòng · phần cứng {len(hw_out)} dòng · DỪNG {'DUNG' in r.stdout}")
if khớp:
    for _, s in hw_out: print("      ⟨silicon⟩ " + s)
    print("   ✅ TRÙNG KHỚP BYTE — lock/semaphore + đánh-thức γ-công-bằng chạy trên CỔNG LOGIC")
else:
    for i,(a,b) in enumerate(zip(pm,hw_out)):
        if a!=b: print(f"   lệch {i}: PM={a!r}  HW={b!r}"); break
    print(f"   (pm[{len(pm)}] hw[{len(hw_out)}])")
sys.exit(0 if khớp else 1)

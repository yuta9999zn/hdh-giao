# -*- coding: utf-8 -*-
"""
lam_toi.py — BA-TRỊ 'tối' (cộng hưởng âm) chạy GATE-LEVEL: SO_SÁNH + NHẢY_TỐI.
================================================================================
Tầng tác-tử CDFL: SO_SÁNH đo CỘNG HƯỞNG γ giữa NIỀM-TIN (a) và THỰC-TẠI (b):
  γ = 1 − 2·|b−a|/max(|b|,1)  →  sáng (γ>0, khớp) · tối (γ<0, ẢO TƯỞNG) · ẩn (γ=0).
Verilog phơi out_state (0 ẩn·1 sáng·2 tối). NHẢY_TỐI rẽ khi ô = tối (thay cờ ZF/CF).
Chương trình HAND-ASSEMBLED (compiler GIAO không phát opcode tác-tử) → đối chiếu BYTE với GVM phần mềm.

  python hw/lam_toi.py
"""
import sys, os, subprocess, shutil, io, contextlib
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from gvm_may import OPS, GVM, ST_NAME

def W(op, a=0): return (OPS[op] << 8) | (a & 0xFF)
# (niềm-tin a, thực-tại b) → SO_SÁNH → RỌI; rồi test NHẢY_TỐI (a=10,b=100 → tối → RỌI 222)
P = [
    W("NẠP",10), W("NẠP",12), W("SO_SÁNH"), W("RỌI"),     # 2d=4<12 → SÁNG, val 10
    W("NẠP",10), W("NẠP",100),W("SO_SÁNH"), W("RỌI"),     # 2d=180>100 → TỐI, val 10
    W("NẠP",10), W("NẠP",20), W("SO_SÁNH"), W("RỌI"),     # 2d=20==20 → ẨN, val 0
    W("NẠP",50), W("NẠP",50), W("SO_SÁNH"), W("RỌI"),     # d=0 → SÁNG, val 50
    W("NẠP",10), W("NẠP",5),  W("SO_SÁNH"), W("RỌI"),     # 2d=10>5 → TỐI, val 10
    # NHẢY_TỐI: (10,100)→tối → nhảy 29 → RỌI 222; nếu không → RỌI 111
    W("NẠP",10), W("NẠP",100),W("SO_SÁNH"), W("NHÂN_BẢN"),# 20..23
    W("NHẢY_TỐI",29),                                      # 24
    W("BỎ"), W("NẠP",111), W("RỌI"), W("NHẢY",32),        # 25..28 (sáng/ẩn path)
    W("BỎ"), W("NẠP",222), W("RỌI"),                      # 29..31 (Ltoi)
    W("DỪNG"),                                             # 32 (Lend)
]

# tham chiếu PHẦN MỀM (gvm_may có SO_SÁNH/resonance + branch_state)
g = GVM(P, world={}, bit=16)
with contextlib.redirect_stdout(io.StringIO()): g.run(max_steps=100000)
pm = [(ST_NAME[x[1]], x[2]) for x in g.xuất]   # [(tên-mặt, val)]

open(os.path.join(HW, "prog_toi.hex"), "w").write("\n".join(f"{w & 0xFFFF:04x}" for w in P) + "\n")
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_toi.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("prog_toi.hex", rom);\n\n' + gv[i1:])

tb = '''`timescale 1ns/1ps
module toi_tb;
  reg clk=0, rst=1; wire [15:0] od; wire ov, h; wire [1:0] st;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_state(st),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; #2000000 begin $display("HETGIO"); $finish; end end
  always @(posedge clk) begin
    if (ov) $display("ROI st=%0d val=%0d", st, $signed(od));
    if (h) begin $display("DUNG"); $finish; end
  end endmodule
'''
open(os.path.join(HW, "toi_tb.v"), "w").write(tb)
iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
subprocess.run([iv, "-o", "gvm_toi.vvp", "gvm_toi.v", "toi_tb.v"], cwd=HW, check=True)
r = subprocess.run([vvp, "gvm_toi.vvp"], cwd=HW, capture_output=True, text=True, timeout=120)
NAME = {0: "ẩn", 1: "sáng", 2: "tối"}
hw = []
for l in r.stdout.splitlines():
    if l.startswith("ROI"):
        t = dict(x.split("=") for x in l.split()[1:]); hw.append((NAME[int(t["st"])], int(t["val"])))

print("=" * 76)
print("BA-TRỊ 'tối' TRÊN VERILOG — CỘNG HƯỞNG γ (SO_SÁNH) + rẽ NHẢY_TỐI chạy GATE-LEVEL")
print("=" * 76)
print(f"   PHẦN MỀM : {pm}")
print(f"   VERILOG  : {hw}")
ok = hw == pm and "DUNG" in r.stdout
print(f"   {'✅ TRÙNG KHỚP — sáng/TỐI/ẩn (cộng hưởng γ) + NHẢY_TỐI chạy ở SILICON' if ok else '✗ LỆCH'}")
if not ok: print("   stdout:", r.stdout[-400:])
sys.exit(0 if ok else 1)

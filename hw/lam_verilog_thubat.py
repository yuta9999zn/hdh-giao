# -*- coding: utf-8 -*-
"""
lam_verilog_thubat.py — THỬ/BẮT (ngoại lệ) chạy GATE-LEVEL trên hw/gvm.v.
================================================================================
Dùng opcode mới: BẮT_ĐẦU_THỬ (mở vùng thử, đẩy handler) · HẾT_THỬ (gỡ handler) ·
NÉM (gỡ-cuộn: khôi phục sp/fp/rsp về điểm 'thử', trao trị-lỗi, nhảy 'bắt').
Chương trình `examples/thu_bat_mai_gvm.giao`: chỉ-mục danh-sách NGOÀI phạm vi → NÉM → 'bắt'
→ phục hồi, KHÔNG sập. Đối chiếu BYTE luồng RỌI với GVM phần mềm.

  python hw/lam_verilog_thubat.py
"""
import sys, os, subprocess, shutil, io, contextlib
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from giaoc import compile_source_bit
from gvm_may import GVM

SRC = open(os.path.join(GỐC, "examples", "thu_bat_mai_gvm.giao"), encoding="utf-8").read()
words, bit = compile_source_bit(SRC)

g = GVM(words, world={}, bit=bit)
with contextlib.redirect_stdout(io.StringIO()): g.run(max_steps=5_000_000)
pm = [g.s(x[2]) for x in g.xuất]            # luồng số (tất cả sáng)

open(os.path.join(HW, "prog_tb.hex"), "w").write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_tb_thu.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("prog_tb.hex", rom);\n\n' + gv[i1:])

W = 16 if bit == 16 else 32
tb = f'''`timescale 1ns/1ps
module thu_tb;
  reg clk=0, rst=1; wire [{W-1}:0] od; wire ov, h; wire [2:0] ok;
  gvm #(.MEM(4096), .WORD({W})) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; #20000000 begin $display("HET GIO"); $finish; end end
  always @(posedge clk) begin
    if (ov && ok==3'd0) $display("NUM=%0d", $signed(od));
    if (h) begin $display("DUNG"); $finish; end
  end
endmodule
'''
open(os.path.join(HW, "thu_tb.v"), "w").write(tb)

iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
if not os.path.exists(iv):
    print("Chưa có iverilog."); sys.exit(0)
subprocess.run([iv, "-o", "gvm_tb_thu.vvp", "gvm_tb_thu.v", "thu_tb.v"], cwd=HW, check=True)
r = subprocess.run([vvp, "gvm_tb_thu.vvp"], cwd=HW, capture_output=True, text=True)
hw_out = [int(l.split("=")[1]) for l in r.stdout.splitlines() if l.startswith("NUM=")]

print("=" * 76)
print("THỬ/BẮT (ngoại lệ) TRÊN VERILOG — gỡ-cuộn NÉM về handler, phục hồi GATE-LEVEL")
print("=" * 76)
print(f"   PHẦN MỀM : {pm}")
print(f"   VERILOG  : {hw_out}")
ok = hw_out == pm and "DUNG" in r.stdout
print(f"   {'✅ TRÙNG KHỚP — thử/bắt + NÉM gỡ-cuộn + phục hồi chạy GATE-LEVEL' if ok else '✗ LỆCH'}")
if not ok: print("   stdout:", r.stdout[-400:])
sys.exit(0 if ok else 1)

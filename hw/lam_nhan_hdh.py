# -*- coding: utf-8 -*-
"""
lam_nhan_hdh.py — NHÂN HĐH-GIAO HỢP-TÁC (examples/hdh.giao, 14490 từ) chạy GATE-LEVEL.
================================================================================
Đây là NHÂN ĐẦY ĐỦ: khởi động, sinh 4 tiến trình (đếm-A/fib-B/đếm-C/giám-sát), lập lịch
hợp-tác (interleave), CỔNG CDFL chặn syscall bất-khả-hồi ('format ổ đĩa' → xin phép, không tự
chạy), rồi DỪNG. Dùng MỌI opcode đã đưa xuống silicon: closure (GỌI_CLOSURE), chuỗi (RỌI_CHUỖI),
ẩn ba-trị (ẨN/RỌI_AUTO), khung gọi-hàm, thử/bắt (NÉM). Đối chiếu BYTE luồng chuỗi với GVM phần mềm.

  python hw/lam_nhan_hdh.py
(Chạy LÂU: ~vài trăm nghìn chu kỳ trên iverilog. Kiên nhẫn.)
"""
import sys, os, subprocess, shutil, io, contextlib
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from giaoc import compile_source_bit
from gvm_may import GVM

SRC = open(os.path.join(GỐC, "examples", "hdh.giao"), encoding="utf-8").read()
words, bit = compile_source_bit(SRC)
assert bit == 32
print(f"   nhân HỢP-TÁC → {len(words)} từ-lệnh GVM (32-bit)")

g = GVM(words, world={}, bit=bit)
with contextlib.redirect_stdout(io.StringIO()): g.run(max_steps=50_000_000)
pm = [("chuỗi", x[1]) if x[0] == "chuỗi" else ("số", x[2]) for x in g.xuất]
print(f"   phần mềm: {len(pm)} mục xuất, dừng sau {g.steps_run} bước")

open(os.path.join(HW, "prog_hdh.hex"), "w").write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
# nạp ROM + ZERO-INIT RAM/cờ-trạng-thái (khớp GVM phần mềm: ram khởi 0 → bộ dựng chuỗi đúng)
open(os.path.join(HW, "gvm_hdh.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  integer __zz;\n'
              '  initial $readmemh("prog_hdh.hex", rom);\n'
              '  initial begin for(__zz=0; __zz<16384; __zz=__zz+1) begin ram[__zz]=0; stk_st[__zz]=2\'b01; end end\n\n'
    + gv[i1:])

tb = '''`timescale 1ns/1ps
module hdh_tb;
  reg clk=0, rst=1; wire [31:0] od; wire ov, h; wire [2:0] ok; integer ncyc=0;
  gvm #(.MEM(16384), .WORD(32)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin
    ncyc = ncyc + 1;
    if (ov) begin
      if      (ok==3'd0) $display("NUM=%0d", $signed(od));
      else if (ok==3'd1) $display("CHR=%0d", od);
      else if (ok==3'd2) $display("SEND");
      else if (ok==3'd6) $display("AN");
    end
    if (h) begin $display("DUNG ncyc=%0d", ncyc); $finish; end
    if (ncyc >= 4000000) begin $display("HET GIO ncyc=%0d", ncyc); $finish; end
  end
endmodule
'''
open(os.path.join(HW, "hdh_tb.v"), "w").write(tb)

iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
if not os.path.exists(iv):
    print("Chưa có iverilog."); sys.exit(0)
print("   biên dịch + chạy iverilog (lâu)...")
subprocess.run([iv, "-o", "gvm_hdh.vvp", "gvm_hdh.v", "hdh_tb.v"], cwd=HW, check=True)
r = subprocess.run([vvp, "gvm_hdh.vvp"], cwd=HW, capture_output=True, text=True, timeout=600)

hw_out, buf = [], []
for l in r.stdout.splitlines():
    if   l.startswith("NUM="): hw_out.append(("số", int(l.split("=")[1])))
    elif l.startswith("CHR="): buf.append(chr(int(l.split("=")[1])))
    elif l.startswith("SEND"): hw_out.append(("chuỗi", "".join(buf))); buf = []
    elif l.strip() == "AN":   hw_out.append(("ẩn",))
ncyc = next((l.split("ncyc=")[1] for l in r.stdout.splitlines() if "ncyc=" in l), "?")

print("=" * 80)
print(f"NHÂN HĐH-GIAO HỢP-TÁC ĐẦY ĐỦ ({len(words)} từ) CHẠY GATE-LEVEL — dừng sau {ncyc} chu kỳ")
print("=" * 80)
khớp = hw_out == pm
print(f"   phần mềm: {len(pm)} mục · phần cứng: {len(hw_out)} mục · DỪNG: {'DUNG' in r.stdout}")
if khớp:
    for _, s in [x for x in hw_out if x[0] == "chuỗi"][:6]:
        print(f"      ⟨silicon⟩ {s}")
    print("      ...")
    print(f"   ✅ TRÙNG KHỚP BYTE — toàn bộ nhân HĐH-GIAO chạy trên CỔNG LOGIC")
else:
    print("   ✗ LỆCH — chi tiết quanh chỗ lệch:")
    for i in range(18, max(len(pm), len(hw_out))):
        a = pm[i] if i < len(pm) else "—"; b = hw_out[i] if i < len(hw_out) else "—"
        mark = "  ✓" if a == b else "  ✗"
        print(f"      [{i:2}]{mark} PM={a!r}")
        print(f"           HW={b!r}")
    print(f"   (pm[{len(pm)}] hw[{len(hw_out)}])")
sys.exit(0 if khớp else 1)

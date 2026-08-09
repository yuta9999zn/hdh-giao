# -*- coding: utf-8 -*-
"""
lam_nhan_fault.py — NHÂN HĐH CÔ-LẬP-FAULT (examples/hdh_fault.giao, bytecode THẬT) gate-level.
================================================================================
3 tiến trình dưới γ-scheduler SILICON, mỗi tiến trình có NGĂN-XẾP-HANDLER (try/bắt) RIÊNG:
  • tt#0 khoẻ   — đếm + XUẤT liên tục (không lỗi).
  • tt#1 tự_chữa — lỗi MỖI lượt nhưng thử/bắt PHỤC HỒI (XUẤT 900) → không bao giờ sập.
  • tt#2 hỏng    — NÉM chưa-bắt → nhân CÔ LẬP (giết) → hệ chạy tiếp, KHÔNG sập.
Verify gate-level: tt#2 chết (dut.t_dead[2]=1) sau ~1 XUẤT; tt#0/tt#1 sống & XUẤT tiếp; CPU không halt.

  python hw/lam_nhan_fault.py [chu_kỳ]
"""
import sys, os, subprocess, shutil, io, contextlib
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from giaoc import compile_source_bit
from gvm_may import GVM

CHU_KỲ = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
words, bit = compile_source_bit(open(os.path.join(GỐC, "examples", "hdh_fault.giao"), encoding="utf-8").read())
print(f"   nhân cô-lập-fault → {len(words)} từ-lệnh ({bit}-bit)")

# tham chiếu phần mềm (lập_lịch_học) → task nào bị cô lập
g = GVM(words, world={}, bit=bit)
with contextlib.redirect_stdout(io.StringIO()): g.run(max_steps=10_000_000)
pm_lỗi = getattr(g, "sched_lỗi", None)   # vd [None, None, 1] → tt#2 lỗi

open(os.path.join(HW, "prog_flt.hex"), "w").write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_flt.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("prog_flt.hex", rom);\n\n' + gv[i1:])

tb = f'''`timescale 1ns/1ps
module flt_tb;
  reg clk=0, rst=1; wire [15:0] od; wire ov, h; wire [2:0] ok; wire [7:0] proc; integer n=0;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.out_proc(proc),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin n=n+1;
    if (ov && (ok==3'd7 || ok==3'd0)) $display("XUAT proc=%0d val=%0d", proc, $signed(od));
    if (h) begin $display("HALT n=%0d", n); $finish; end
    if (n>={CHU_KỲ}) begin
      $display("DEAD %0d %0d %0d", dut.t_dead[0], dut.t_dead[1], dut.t_dead[2]);
      $display("SIGMA %0d %0d %0d", dut.sigma[0], dut.sigma[1], dut.sigma[2]);
      $finish;
    end
  end endmodule
'''
open(os.path.join(HW, "flt_tb.v"), "w").write(tb)
iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
subprocess.run([iv, "-o", "gvm_flt.vvp", "gvm_flt.v", "flt_tb.v"], cwd=HW, check=True)
r = subprocess.run([vvp, "gvm_flt.vvp"], cwd=HW, capture_output=True, text=True, timeout=400)

per = {0: [], 1: [], 2: []}
for l in r.stdout.splitlines():
    if l.startswith("XUAT"):
        t = dict(x.split("=") for x in l.split()[1:]); per.setdefault(int(t["proc"]), []).append(int(t["val"]))
dead = next((l for l in r.stdout.splitlines() if l.startswith("DEAD")), "")
halted = "HALT" in r.stdout
d = [int(x) for x in dead.split()[1:]] if dead else [0,0,0]

print("=" * 78)
print(f"NHÂN HĐH CÔ-LẬP-FAULT (bytecode THẬT) trên γ-scheduler SILICON — {CHU_KỲ} chu kỳ")
print("=" * 78)
TÊN = {0: "khoẻ", 1: "tự_chữa", 2: "hỏng"}
for p in sorted(per):
    v = per[p]
    print(f"   tt#{p} {TÊN[p]:9}: {len(v):4} XUẤT (giá trị {sorted(set(v))[:4]}{'…' if len(set(v))>4 else ''})  ·  CHẾT={'CÓ' if d[p] else 'không'}")
print(f"   phần mềm: tt bị lỗi/cô-lập = {pm_lỗi}")
# tiêu chí: tt#2 chết, tt#0&tt#1 sống & có XUẤT, hệ KHÔNG halt
ok = (d == [0,0,1]) and len(per[0])>5 and len(per[1])>2 and (set(per[1])=={900}) and len(per[2])<=2 and not halted
print("-" * 78)
print(f"   {'✅ CÔ LẬP FAULT GATE-LEVEL: tt#2(hỏng) bị cách ly, tt#0/tt#1 chạy tiếp, hệ KHÔNG sập' if ok else '✗ CHƯA ĐẠT'}")
if not ok: print(r.stdout[-500:])
sys.exit(0 if ok else 1)

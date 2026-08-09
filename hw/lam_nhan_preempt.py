# -*- coding: utf-8 -*-
"""
lam_nhan_preempt.py — NHÂN HĐH PREEMPTIVE (bytecode THẬT) chạy trên γ-scheduler SILICON.
================================================================================
KHÁC lam_lichhoc.py (chương-trình-viết-tay): ở đây nạp CHÍNH bytecode biên dịch từ
examples/hdh_preempt.giao — tiến trình = HÀM (khung/biến-cục-bộ per-task), `xuất(i)` = opcode
XUẤT (out_kind=7 + out_proc=cur). γ-scheduler PHẦN CỨNG cướp CPU, HỌC σ, throttle spin.
Đọc σ học được thẳng từ thanh ghi dut.sigma[i]; đếm XUẤT mỗi tiến trình qua out_proc.

  python hw/lam_nhan_preempt.py
"""
import os, sys, subprocess, shutil, io, contextlib
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from giaoc import compile_source_bit
from gvm_may import GVM
NT_REG = 3   # số tiến trình đăng ký (kernel: đếm_nhanh/spin/đếm_chậm)

CHU_KỲ = int(sys.argv[1]) if len(sys.argv) > 1 else 6000

SRC = open(os.path.join(GỐC, "examples", "hdh_preempt.giao"), encoding="utf-8").read()
words, bit = compile_source_bit(SRC)
print(f"   nhân preemptive → {len(words)} từ-lệnh GVM ({bit}-bit)")

# ── tham chiếu PHẦN MỀM: γ-scheduler (lập_lịch_học) → σ + phân bổ lệnh ──
g = GVM(words, world={}, bit=bit)
with contextlib.redirect_stdout(io.StringIO()): g.run(max_steps=10_000_000)
pm_sigma = getattr(g, "sched_σ", None); pm_lệnh = getattr(g, "sched_lệnh", None)

# ── nạp bytecode vào Verilog (16-bit), tb đọc out_proc + dut.sigma ──
open(os.path.join(HW, "prog_nhanp.hex"), "w").write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_nhanp.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("prog_nhanp.hex", rom);\n\n' + gv[i1:])

tb = f'''`timescale 1ns/1ps
module nhanp_tb;
  reg clk=0, rst=1; wire [15:0] od; wire ov, h; wire [2:0] ok; wire [7:0] proc;
  wire sevt, srho; wire [7:0] scur; integer ncyc=0;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),
                        .out_proc(proc),.sched_evt(sevt),.sched_cur(scur),.sched_rho(srho),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin
    if (!rst) ncyc = ncyc + 1;
    if (ov && (ok==3'd7 || ok==3'd0)) $display("XUAT proc=%0d val=%0d", proc, $signed(od));
    if (sevt) $display("SCHED cur=%0d rho=%0d", scur, srho);    // ★ vết quyết-định lập-lịch
    if (ncyc >= {CHU_KỲ}) begin
      $display("SIGMA %0d %0d %0d", dut.sigma[0], dut.sigma[1], dut.sigma[2]);
      $display("NTASK %0d", dut.ntask);
      $finish;
    end
  end
endmodule
'''
open(os.path.join(HW, "nhanp_tb.v"), "w").write(tb)

iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
if not os.path.exists(iv):
    print("Chưa có iverilog."); sys.exit(0)
subprocess.run([iv, "-o", "gvm_nhanp.vvp", "gvm_nhanp.v", "nhanp_tb.v"], cwd=HW, check=True)
r = subprocess.run([vvp, "gvm_nhanp.vvp"], cwd=HW, capture_output=True, text=True)

# ── phân tích luồng XUẤT + vết lập-lịch phần cứng ──
per = {0: [], 1: [], 2: []}; trace = []
for l in r.stdout.splitlines():
    if l.startswith("XUAT"):
        toks = dict(t.split("=") for t in l.split()[1:])
        p = int(toks["proc"]); per.setdefault(p, []).append(int(toks["val"]))
    elif l.startswith("SCHED"):
        toks = dict(t.split("=") for t in l.split()[1:])
        trace.append((int(toks["cur"]), int(toks["rho"])))
hw_sig = [int(x) for x in next((l for l in r.stdout.splitlines() if l.startswith("SIGMA")), "S 0 0 0").split()[1:]]
ntask = next((l for l in r.stdout.splitlines() if l.startswith("NTASK")), "")

# ── ★ ĐỐI CHIẾU CHẶT: replay vết quyết-định phần cứng qua CHÍNH SÁCH phần mềm γ_cập_nhật ──
σ = [128] * NT_REG; cred = [0] * NT_REG
for cur, rho in trace:
    σ, cred, _ = GVM.γ_cập_nhật(σ, cred, cur, bool(rho), NT_REG)
khớp_σ = (σ == hw_sig[:NT_REG])

print("=" * 78)
print(f"NHÂN HĐH PREEMPTIVE (bytecode THẬT) trên γ-scheduler SILICON — {CHU_KỲ} chu kỳ")
print("=" * 78)
print(f"   {ntask}   ·  {len(trace)} lần CHUYỂN NGỮ CẢNH (preemption phần cứng)")
TÊN = {0: "đếm_nhanh (+1)", 1: "spin_vô_ích", 2: "đếm_chậm (+10)"}
for p in sorted(per):
    vals = per[p]
    print(f"   tt#{p} {TÊN.get(p,''):16}: {len(vals):4} XUẤT" + (f"  → tới {max(vals)}" if vals else "  ← KHÔNG xuất (đói CPU)"))
print(f"   σ học được (PHẦN CỨNG)        : {hw_sig[:NT_REG]}   (255≈hữu ích · 0≈vô ích)")
print(f"   σ replay vết-HW qua chính-sách: {σ}   {'✅ KHỚP byte' if khớp_σ else '✗ LỆCH'}")
throttled = per.get(1, []) == [] and hw_sig[1] < hw_sig[0] and hw_sig[1] < hw_sig[2]
print("-" * 78)
ok = (ntask.endswith("3")) and khớp_σ and throttled
print(f"   {'✅ NHÂN HĐH PREEMPTIVE CHẠY GATE-LEVEL: 3 tiến trình, σ-học khớp chính sách, spin bị throttle' if ok else '✗ CHƯA ĐẠT'}")
if not ok: print(r.stdout[-600:])
sys.exit(0 if ok else 1)

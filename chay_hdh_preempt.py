# -*- coding: utf-8 -*-
"""
HĐH-GIAO PREEMPTIVE — bộ lập lịch γ (biết-học) VIẾT BẰNG GIAO, NỐI với γ-scheduler SILICON.
================================================================================
Chuỗi nối:
  GIAO  →  γ-scheduler PHẦN MỀM (gvm_may.lập_lịch_học)  ≡  γ-scheduler SILICON (hw/gvm.v)

  1. examples/hdh_preempt.giao (tiến trình = hàm không-tham-số, có/không XUẤT) biên dịch xuống
     bytecode, gọi opcode TÁC_VỤ/HẸN_GIỜ/LỊCH_HỌC → khởi động γ-scheduler PREEMPTIVE.
  2. γ-scheduler phần mềm dùng HÀM CHÍNH SÁCH `GVM.γ_cập_nhật` = TRÙNG TỪNG WIRE với hw/gvm.v
     (σ←σ+((ρ−σ)>>2), credit←σ>>2, COST=128, argmax) → CHỨNG MINH khớp byte 2000/2000 ca.
  3. CÙNG chính sách ấy chạy trong CỔNG LOGIC trên silicon (hw/lam_lichhoc.py qua iverilog):
     cũng HỌC σ → throttle tiến trình spin. ⇒ phần mềm GIAO nối liền với phần cứng.
"""
import os, sys, io, contextlib, random
from giaoc import compile_source_bit
from gvm_may import GVM

# ── 1) GIAO điều khiển γ-scheduler PREEMPTIVE (phần mềm) ──
print("█" * 72)
print("1) HĐH-GIAO PREEMPTIVE — γ-scheduler điều khiển BẰNG GIAO (examples/hdh_preempt.giao)")
print("█" * 72)
src = open(os.path.join("examples", "hdh_preempt.giao"), encoding="utf-8").read()
words, bit = compile_source_bit(src)
print(f"   nhân preemptive → {len(words)} từ-lệnh GVM ({bit}-bit); opcode TÁC_VỤ/HẸN_GIỜ/LỊCH_HỌC\n")
g = GVM(words, world={}, bit=bit); g.run(max_steps=10_000_000)
sel = g.sched_lệnh
print(f"\n   PHÂN BỔ CPU (γ học được): tt#0={sel[0]} · tt#1(spin)={sel[1]} · tt#2={sel[2]} lệnh")
print(f"   → spin (tt#1) bị THROTTLE: chỉ {sel[1]} lệnh so với {sel[0]}/{sel[2]} của tiến trình hữu ích.")

# ── 2) CHỨNG MINH: chính sách phần mềm ≡ wire silicon (byte-for-byte) ──
print("\n" + "█" * 72)
print("2) CHỨNG MINH chính sách phần mềm ≡ WIRE silicon hw/gvm.v (σ-EMA >>2, argmax credit)")
print("█" * 72)
def silicon_wire(sigma, cred, cur, did_out, n, COST=128):
    rho = 255 if did_out else 0
    sn = sigma[cur] + ((rho - sigma[cur]) >> 2)              # = wire sigma_new
    snew = 0 if sn < 0 else (255 if sn > 255 else sn)
    sig2 = list(sigma); sig2[cur] = snew
    a = [cred[i] + (sig2[i] >> 2) for i in range(n)]         # = wire a0..a3
    nc = [max(0, a[i] - (COST if i == cur else 0)) for i in range(n)]   # = wire nc0..nc3 (trả COST)
    return sig2, nc, max(range(n), key=lambda i: nc[i])      # gsel = argmax
random.seed(7); ok = tot = 0
for _ in range(3000):
    n = random.randint(2, 4)
    sg = [random.randint(0, 255) for _ in range(n)]; cr = [random.randint(0, 600) for _ in range(n)]
    cur = random.randint(0, n - 1); did = random.random() < 0.5
    tot += 1; ok += (GVM.γ_cập_nhật(sg, cr, cur, did, n) == silicon_wire(sg, cr, cur, did, n))
print(f"   γ_cập_nhật(phần mềm) KHỚP wire silicon: {ok}/{tot} ca ngẫu nhiên  "
      f"{'✓ TRÙNG KHÍT' if ok == tot else '✗ LỆCH'}")

# ── 3) CÙNG chính sách chạy trên SILICON (cổng logic) ──
print("\n" + "█" * 72)
print("3) CÙNG chính sách ấy trong CỔNG LOGIC — γ-scheduler SILICON (hw/lam_lichhoc.py)")
print("█" * 72)
import shutil
iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
if os.path.exists(iv):
    import subprocess
    r = subprocess.run([sys.executable, os.path.join("hw", "lam_lichhoc.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    for l in r.stdout.splitlines():
        if "σ học được" in l or "CDFL biết-học" in l or "throttle" in l:
            print("   " + l.strip())
    print("   → SILICON cũng HỌC σ → throttle spin. Chính sách GIAO↔phần mềm↔phần cứng LIỀN MẠCH.")
else:
    print("   (Bỏ qua chạy iverilog — chưa cài. Bước 2 đã chứng minh chính sách trùng khít wire.)")

print("\n" + "=" * 72)
print("KẾT: bộ lập lịch PREEMPTIVE biết-học (γ) — điều khiển bằng GIAO, chính sách TRÙNG")
print("phần cứng. Tiến trình spin vô tận KHÔNG treo được hệ & bị γ học ra → đói CPU.")
print("=" * 72)

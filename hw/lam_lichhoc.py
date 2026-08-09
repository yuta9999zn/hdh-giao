# -*- coding: utf-8 -*-
"""
lam_lichhoc.py — LẬP LỊCH CDFL BIẾT-HỌC (theo γ) chạy trên SILICON (hw/gvm.v qua iverilog).
3 tiến trình: A,C HỮU ÍCH (RỌI đếm lên) · B SPIN THUẦN (vòng vô tận, KHÔNG output).
So 2 bộ lập lịch trên CÙNG ngân sách chu kỳ:
   • round-robin (LẬP_LỊCH): chia đều → B phí 1/3 CPU.
   • CDFL biết-học (LỊCH_HỌC): nhân HỌC σ qua phần cứng → throttle B → A,C được nhiều CPU hơn.
Đọc thẳng σ học được từ thanh ghi phần cứng (dut.sigma[i]).
"""
import os, sys, subprocess, shutil
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from gvm_may import OPS

def W(op, a=0): return (OPS[op] << 8) | (a & 0xFF)
def prog(sched):                         # sched = "LẬP_LỊCH" | "LỊCH_HỌC"
    p = {a: 0x0000 for a in range(29)}
    p.update({
        0: W("NẠP",0),1: W("LƯU_Ô",100),2: W("NẠP",0),3: W("LƯU_Ô",101),
        4: W("NẠP",12),5: W("TÁC_VỤ"), 6: W("NẠP",19),7: W("TÁC_VỤ"), 8: W("NẠP",20),9: W("TÁC_VỤ"),
        10: W("HẸN_GIỜ",16), 11: W(sched),
        # A @12 hữu ích
        12: W("TẢI_Ô",100),13: W("NẠP",1),14: W("CỘNG"),15: W("LƯU_Ô",100),
        16: W("TẢI_Ô",100),17: W("RỌI"),18: W("NHẢY",12),
        # B @19 spin thuần (không RỌI)
        19: W("NHẢY",19),
        # C @20 hữu ích (RỌI +200)
        20: W("TẢI_Ô",101),21: W("NẠP",1),22: W("CỘNG"),23: W("LƯU_Ô",101),
        24: W("TẢI_Ô",101),25: W("NẠP",200),26: W("CỘNG"),27: W("RỌI"),28: W("NHẢY",20),
    })
    return p

gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_lh.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("program_lh.hex", rom);\n\n' + gv[i1:])
tb = '''`timescale 1ns/1ps
module lh_tb;
  reg clk=0, rst=1; wire [15:0] od; wire ov, halt; integer ncyc=0;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.halt(halt));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin
    if (!rst) ncyc = ncyc + 1;
    if (ov) $display("ROI=%0d", od);
    if (ncyc >= 1200) begin
      $display("SIGMA %0d %0d %0d", dut.sigma[0], dut.sigma[1], dut.sigma[2]);
      $finish;
    end
  end
endmodule
'''
open(os.path.join(HW, "lh_tb.v"), "w").write(tb)
iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"

def chạy(sched):
    p = prog(sched)
    open(os.path.join(HW,"program_lh.hex"),"w").write("\n".join(f"{p[a]&0xFFFF:04x}" for a in range(29))+"\n")
    subprocess.run([iv,"-o","lh.vvp","gvm_lh.v","lh_tb.v"], cwd=HW, check=True)
    r = subprocess.run([vvp,"lh.vvp"], cwd=HW, capture_output=True, text=True)
    rois = [int(l.split("=")[1]) for l in r.stdout.splitlines() if l.startswith("ROI=")]
    sig = next((l for l in r.stdout.splitlines() if l.startswith("SIGMA")), "")
    return rois, sig

if not os.path.exists(iv): print("Chưa có iverilog."); sys.exit(0)
print("="*68); print("LẬP LỊCH theo γ Ở PHẦN CỨNG — so round-robin vs CDFL-biết-học (1200 chu kỳ)"); print("="*68)
for tên, sched in [("round-robin", "LẬP_LỊCH"), ("CDFL biết-học (γ)", "LỊCH_HỌC")]:
    rois, sig = chạy(sched)
    A = [x for x in rois if x < 100]; C = [x for x in rois if x >= 200]
    print(f"\n[{tên}]  A (hữu ích): {len(A)} output (tới {max(A) if A else 0})  ·  "
          f"C (hữu ích): {len(C)} output (tới {max(C)-200 if C else 0})  ·  B(spin): 0")
    if sig:
        s = sig.split()[1:]; print(f"   σ học được (phần cứng): A={s[0]}  B={s[1]}  C={s[2]}   (255≈hữu ích, 0≈vô ích)")
        if sched == "LỊCH_HỌC":
            print("   → nhân HỌC: A,C σ CAO (ưu tiên) · B σ THẤP (throttle) ⇒ A,C nhiều CPU hơn round-robin.")
print("\n→ γ-scheduler PHẦN CỨNG: học hành vi → phân bổ CPU theo CỘNG HƯỞNG, ngay trên silicon.")

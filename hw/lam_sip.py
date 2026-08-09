# -*- coding: utf-8 -*-
"""
lam_sip.py — CÔ LẬP TIẾN TRÌNH (SIP) bằng BASE+BOUND, KHÔNG MMU, trên SILICON (hw/gvm.v).
Hai tiến trình A,B dùng CÙNG địa chỉ ẢO ram[0] làm bộ đếm.
  • KHÔNG SIP: chia chung phys ram[0] → GIẪM ĐẠP nhau (A đếm nhảy cóc 1,3,5..).
  • CÓ SIP   : mỗi task có vùng nhớ riêng (relocate base+bound) → CÔ LẬP, A đếm 1,2,3,4..
Phần 2: một task chạm địa chỉ vượt biên (≥128) → phần cứng phát FAULT (911) → chặn.
"""
import os, sys, subprocess, shutil
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from gvm_may import OPS

def W(op, a=0): return (OPS[op] << 8) | (a & 0xFF)

def build(sip, rogue=False):
    boot = [W("NẠP",0),W("LƯU_Ô",0),W("NẠP",0),W("LƯU_Ô",128),  # zero ô đếm 2 vùng
            W("NẠP",0),W("TÁC_VỤ"),W("NẠP",0),W("TÁC_VỤ"),W("HẸN_GIỜ",16)]
    if sip: boot.append(W("BẬT_SIP"))
    boot.append(W("LẬP_LỊCH"))
    L = len(boot); EA = L; EB = L + 7
    boot[4] = W("NẠP",EA); boot[6] = W("NẠP",EB)
    A = [W("TẢI_Ô",0),W("NẠP",1),W("CỘNG"),W("LƯU_Ô",0),W("TẢI_Ô",0),W("RỌI"),W("NHẢY",EA)]
    if rogue:   # task B chạm ngoài vùng (≥128 = mbound) → FAULT. LƯU_GIÁN: [addr, val]
        B = [W("NẠP",200),W("NẠP",1),W("LƯU_GIÁN"),W("NHẢY",EB)]   # ghi ram[200] (NGOÀI biên 128)
    else:
        B = [W("TẢI_Ô",0),W("NẠP",1),W("CỘNG"),W("LƯU_Ô",0),W("TẢI_Ô",0),W("NẠP",100),W("CỘNG"),W("RỌI"),W("NHẢY",EB)]
    return boot + A + ([0]*(7-len(A)) if False else []) + B  # A là 7, B ngay sau

gv = open(os.path.join(HW,"gvm.v"),encoding="utf-8").read()
i0=gv.index("  initial begin"); i1=gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW,"gvm_sip.v"),"w",encoding="utf-8").write(gv[:i0]+'  initial $readmemh("program_sip.hex", rom);\n\n'+gv[i1:])
tb='''`timescale 1ns/1ps
module sip_tb; reg clk=0,rst=1; wire [15:0] od; wire ov,halt; integer ncyc=0;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.halt(halt));
  always #5 clk=~clk; initial begin #12 rst=0; end
  always @(posedge clk) begin if(!rst) ncyc=ncyc+1;
    if(ov) $display("ROI=%0d",od);
    if(halt||ncyc>=700) begin if(halt) $display("HALT"); $finish; end end
endmodule
'''
open(os.path.join(HW,"sip_tb.v"),"w").write(tb)
iv=shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"; vvp=shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
def chạy(code):
    open(os.path.join(HW,"program_sip.hex"),"w").write("\n".join(f"{w&0xFFFF:04x}" for w in code)+"\n")
    subprocess.run([iv,"-o","sip.vvp","gvm_sip.v","sip_tb.v"],cwd=HW,check=True)
    r=subprocess.run([vvp,"sip.vvp"],cwd=HW,capture_output=True,text=True)
    rois=[int(l.split("=")[1]) for l in r.stdout.splitlines() if l.startswith("ROI=")]
    return rois, ("HALT" in r.stdout)
if not os.path.exists(iv): print("Chưa có iverilog."); sys.exit(0)
print("="*64); print("SIP — CÔ LẬP TIẾN TRÌNH bằng BASE+BOUND (không MMU) trên silicon"); print("="*64)
for tên,sip in [("KHÔNG SIP (chung ram[0])","off"),("CÓ SIP (vùng nhớ riêng)","on")]:
    rois,_=chạy(build(sip=="on"))
    A=[x for x in rois if x<100]
    cons = all(A[i+1]==A[i]+1 for i in range(len(A)-1)) if len(A)>1 else False
    print(f"\n[{tên}] task A (dùng ram[0]): {A[:10]}")
    print(f"   A đếm LIÊN TỤC 1,2,3..? {'CÓ ✓ (cô lập)' if cons else 'KHÔNG (bị giẫm đạp)'}")
print("\n[BOUND] task B ghi địa chỉ ngoài vùng (≥128) với SIP bật:")
rois,halted=chạy(build(True,rogue=True))
print(f"   output={rois}  ·  fault 911 + HALT? {'CÓ ✓ (cô lập chặn)' if (911 in rois and halted) else 'KHÔNG'}")
print("\n→ SIP base+bound: tiến trình KHÔNG chạm được bộ nhớ task khác — cô lập bằng CỔNG LOGIC, KHÔNG MMU.")

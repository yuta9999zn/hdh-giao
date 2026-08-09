# -*- coding: utf-8 -*-
"""
lam_danhiem.py — ĐA NHIỆM TIỀN-ĐỊNH chạy trên SILICON (hw/gvm.v qua iverilog).
2 tiến trình đếm VÔ TẬN trên MỘT CPU; TIMER PHẦN CỨNG tự CONTEXT-SWITCH (lưu/nạp ngân
hàng thanh ghi mỗi task). Nếu thấy output A (1,2,3..) và B (101,102..) XEN KẼ ⇒ hai tiến
trình chạy ĐỒNG THỜI nhờ chuyển ngữ cảnh BẰNG CỔNG LOGIC — không phần mềm điều phối.
"""
import os, sys, subprocess, shutil
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from gvm_may import OPS, disasm_word

def W(op, arg=0): return (OPS[op] << 8) | (arg & 0xFF)
prog = {a: 0x0000 for a in range(29)}
prog.update({
    0: W("NẠP",0), 1: W("LƯU_Ô",100), 2: W("NẠP",0), 3: W("LƯU_Ô",101),  # zero-hoá bộ đếm
    4: W("NẠP", 10), 5: W("TÁC_VỤ"),     # đăng ký task 0 (entry @10, sp base 0)
    6: W("NẠP", 20), 7: W("TÁC_VỤ"),     # đăng ký task 1 (entry @20, sp base 64)
    8: W("HẸN_GIỜ", 20), 9: W("LẬP_LỊCH"),  # chu kỳ 20 · khởi động đa nhiệm
    # task A @10 — đếm ram[100] lên VÔ TẬN, RỌI
    10: W("TẢI_Ô",100),11: W("NẠP",1),12: W("CỘNG"),13: W("LƯU_Ô",100),
    14: W("TẢI_Ô",100),15: W("RỌI"),16: W("NHẢY",10),
    # task B @20 — đếm ram[101] lên VÔ TẬN, RỌI +100 (để phân biệt với A)
    20: W("TẢI_Ô",101),21: W("NẠP",1),22: W("CỘNG"),23: W("LƯU_Ô",101),
    24: W("TẢI_Ô",101),25: W("NẠP",100),26: W("CỘNG"),27: W("RỌI"),28: W("NHẢY",20),
})
with open(os.path.join(HW, "program_dn.hex"), "w") as f:
    f.write("\n".join(f"{prog[a] & 0xFFFF:04x}" for a in range(29)) + "\n")

gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_dn.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("program_dn.hex", rom);\n\n' + gv[i1:])

tb = '''`timescale 1ns/1ps
module dn_tb;
  reg clk=0, rst=1; wire [15:0] od; wire ov, halt; integer nout=0;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.halt(halt));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin
    if (ov) begin $display("ROI=%0d", od); nout=nout+1; if (nout>=24) $finish; end
  end
endmodule
'''
open(os.path.join(HW, "dn_tb.v"), "w").write(tb)
print("Đã sinh: program_dn.hex, gvm_dn.v, dn_tb.v")

iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
if os.path.exists(iv):
    subprocess.run([iv, "-o", "dn.vvp", "gvm_dn.v", "dn_tb.v"], cwd=HW, check=True)
    r = subprocess.run([vvp, "dn.vvp"], cwd=HW, capture_output=True, text=True)
    rois = [int(l.split("=")[1]) for l in r.stdout.splitlines() if l.startswith("ROI=")]
    A = [x for x in rois if x < 100]; B = [x for x in rois if x >= 100]
    print("VERILOG xuất (xen kẽ 2 tiến trình):", rois)
    print(f"  task A (đếm 1,2,3..): {A}")
    print(f"  task B (đếm 101,102..): {B}")
    # xen kẽ = có ít nhất một chỗ A→B hoặc B→A liền kề; cả hai cùng tiến
    xen = any((rois[i] < 100) != (rois[i+1] < 100) for i in range(len(rois)-1))
    tiến = len(A) >= 3 and len(B) >= 3 and A == sorted(A) and B == sorted(B)
    ok = xen and tiến
    print(("\n✓ ĐA NHIỆM TIỀN-ĐỊNH TRÊN SILICON: A và B chạy ĐỒNG THỜI trên MỘT CPU, "
           "timer phần cứng tự context-switch (không phần mềm điều phối).") if ok
          else "\n✗ chưa thấy đa nhiệm xen kẽ đúng kỳ vọng")
    sys.exit(0 if ok else 1)
else:
    print("Chưa có iverilog.")

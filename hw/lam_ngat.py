# -*- coding: utf-8 -*-
"""
lam_ngat.py — KIỂM CHỨNG NGẮT TIMER PHẦN CỨNG trong hw/gvm.v (qua iverilog).
Nạp một chương trình: MAIN đếm 8→1 (RỌI mỗi số), còn TIMER PHẦN CỨNG cứ mỗi 'period'
chu kỳ lại CƯỚP CPU, nhảy vào HANDLER (RỌI 99 = "⚡tick"), rồi IRET quay về MAIN.
Nếu thấy 99 XEN GIỮA 8..1 ⇒ ngắt phần cứng PREEMPT được chương trình đang chạy (silicon).
"""
import os, sys, subprocess, shutil
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(GỐC, "hw"); sys.path.insert(0, GỐC)
from gvm_may import OPS, disasm_word

def W(op, arg=0): return (OPS[op] << 8) | (arg & 0xFF)
prog = {a: 0x0000 for a in range(34)}                      # mặc định DỪNG
prog.update({
    0:  W("NẠP", 30),  1: W("BẬT_NGẮT"),  2: W("HẸN_GIỜ", 30),   # cài handler@30, chu kỳ 30
    3:  W("NẠP", 8),   4: W("LƯU_Ô", 0),                          # main: đếm ram[0]=8
    5:  W("TẢI_Ô", 0), 6: W("NHẢY_NẾU_0", 16),                    # @5 loop: nếu 0 → @16
    7:  W("TẢI_Ô", 0), 8: W("RỌI"),                               # in bộ đếm
    9:  W("TẢI_Ô", 0), 10: W("NẠP", 1), 11: W("TRỪ"), 12: W("LƯU_Ô", 0),
    13: W("NHẢY", 5),                                             # lặp
    16: W("TẮT_NGẮT"), 17: W("DỪNG"),
    30: W("NẠP", 99),  31: W("RỌI"), 32: W("NGẮT_VỀ"),           # handler: RỌI 99 rồi IRET
})
with open(os.path.join(HW, "program_ngat.hex"), "w") as f:
    f.write("\n".join(f"{prog[a] & 0xFFFF:04x}" for a in range(34)) + "\n")

# patch gvm.v: boot ROM cứng → $readmemh
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_ngat.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("program_ngat.hex", rom);\n\n' + gv[i1:])

tb = '''`timescale 1ns/1ps
module ngat_tb;
  reg clk=0, rst=1; wire [15:0] od; wire ov, halt; reg [31:0] ncyc=0;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.halt(halt));
  always #5 clk = ~clk;
  initial begin #12 rst=0; #200000 begin $display("HET GIO"); $finish; end end
  always @(posedge clk) begin
    if (!rst) ncyc <= ncyc + 1;
    if (ov) $display("ROI=%0d", od);
    if (halt) begin $display("DUNG@%0d", ncyc); $finish; end
  end
endmodule
'''
open(os.path.join(HW, "ngat_tb.v"), "w").write(tb)
print("Đã sinh: program_ngat.hex, gvm_ngat.v, ngat_tb.v")
for a in range(34):
    if prog[a]: print(f"  {a:02d}:  {disasm_word(prog[a])}")

iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
if os.path.exists(iv):
    subprocess.run([iv, "-o", "ngat.vvp", "gvm_ngat.v", "ngat_tb.v"], cwd=HW, check=True)
    r = subprocess.run([vvp, "ngat.vvp"], cwd=HW, capture_output=True, text=True)
    rois = [int(l.split("=")[1]) for l in r.stdout.splitlines() if l.startswith("ROI=")]
    print("\nVERILOG xuất (RỌI):", rois)
    chính = [x for x in rois if x != 99]
    ngắt  = [x for x in rois if x == 99]
    xen = any(rois[i] == 99 and i > 0 and i < len(rois)-1 and rois[i-1] != 99 for i in range(len(rois)))
    ok = chính == [8,7,6,5,4,3,2,1] and len(ngắt) > 0 and xen
    print(f"  main đếm: {chính}   ·   handler 'tick' (99): {len(ngắt)} lần")
    print(("\n✓ NGẮT TIMER PHẦN CỨNG HOẠT ĐỘNG: handler XEN GIỮA main (8..1 vẫn xong) "
           "⇒ PREEMPTION Ở SILICON." ) if ok else "\n✗ chưa thấy preemption đúng kỳ vọng")
    sys.exit(0 if ok else 1)
else:
    print("Chưa có iverilog.")

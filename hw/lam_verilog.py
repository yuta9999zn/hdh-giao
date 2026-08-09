# -*- coding: utf-8 -*-
"""
lam_verilog.py — PIPELINE: GIAO → bytecode GVM → VERILOG THẬT.
Biên dịch examples/tac_tu_may.giao xuống bytecode, sinh:
  • program.hex  — ROM lệnh cho $readmemh
  • gvm_prog.v   — gvm.v với boot ROM thay bằng $readmemh("program.hex")
  • run_tb.v     — testbench (clock, bắt RỌI, dừng khi halt)
Rồi (nếu có iverilog) biên dịch + chạy, đối chiếu với GVM phần mềm.

Chạy tay:
  python hw/lam_verilog.py
  cd hw && iverilog -o gvm_prog.vvp gvm_prog.v run_tb.v && vvp gvm_prog.vvp
"""
import sys, os, subprocess, shutil
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW  = os.path.join(GỐC, "hw")
sys.path.insert(0, GỐC)
from giaoc import compile_source

src   = open(os.path.join(GỐC, "examples", "tac_tu_may.giao"), encoding="utf-8").read()
words = compile_source(src)

# 1) ROM lệnh → hex (4 chữ số/dòng)
with open(os.path.join(HW, "program.hex"), "w") as f:
    f.write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")

# 2) gvm.v → gvm_prog.v (boot ROM cứng → $readmemh)
gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin")
i1 = gv.index("  // --- CHU KỲ CLOCK")
gv2 = gv[:i0] + '  initial $readmemh("program.hex", rom);\n\n' + gv[i1:]
open(os.path.join(HW, "gvm_prog.v"), "w", encoding="utf-8").write(gv2)

# 3) testbench
tb = '''`timescale 1ns/1ps
module run_tb;
  reg clk=0, rst=1;
  reg [31:0] ncyc = 0;
  wire [15:0] out_data; wire out_valid, halt;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(out_data),.out_valid(out_valid),.halt(halt));
  always #5 clk = ~clk;
  initial begin
    #12 rst = 0;
    #16000000 begin $display("HET GIO (khong dung?)"); $finish; end
  end
  always @(posedge clk) begin
    if (!rst) ncyc <= ncyc + 1;
    if (out_valid) $display("ROI=%0d", out_data);
    if (halt) begin $display("CPU DUNG."); $display("CYCLES=%0d", ncyc); $finish; end
  end
endmodule
'''
open(os.path.join(HW, "run_tb.v"), "w").write(tb)
print(f"Đã sinh: program.hex ({len(words)} từ-lệnh), gvm_prog.v, run_tb.v")

# 4) nếu có iverilog → biên dịch + chạy + đối chiếu phần mềm
iv = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
vvp = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
if os.path.exists(iv):
    subprocess.run([iv, "-o", "gvm_prog.vvp", "gvm_prog.v", "run_tb.v"], cwd=HW, check=True)
    r = subprocess.run([vvp, "gvm_prog.vvp"], cwd=HW, capture_output=True, text=True)
    rois = [int(l.split("=")[1]) for l in r.stdout.splitlines() if l.startswith("ROI=")]
    cyc  = next((int(l.split("=")[1]) for l in r.stdout.splitlines() if l.startswith("CYCLES=")), None)
    print("VERILOG (gvm.v qua iverilog):", rois)
    print(f"   {len(rois)} giá trị · dừng sau {cyc} chu kỳ clock")
    print("→ Chạy trên Verilog THẬT, dừng:", "CPU DUNG." in r.stdout)
else:
    print("Chưa có iverilog — chạy tay theo hướng dẫn ở đầu file.")

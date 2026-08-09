`timescale 1ns/1ps
module dn_tb;
  reg clk=0, rst=1; wire [15:0] od; wire ov, halt; integer nout=0;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.halt(halt));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin
    if (ov) begin $display("ROI=%0d", od); nout=nout+1; if (nout>=24) $finish; end
  end
endmodule

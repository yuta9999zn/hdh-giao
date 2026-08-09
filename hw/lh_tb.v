`timescale 1ns/1ps
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

`timescale 1ns/1ps
module toi_tb;
  reg clk=0, rst=1; wire [15:0] od; wire ov, h; wire [1:0] st;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_state(st),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; #2000000 begin $display("HETGIO"); $finish; end end
  always @(posedge clk) begin
    if (ov) $display("ROI st=%0d val=%0d", st, $signed(od));
    if (h) begin $display("DUNG"); $finish; end
  end endmodule

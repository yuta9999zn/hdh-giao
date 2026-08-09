`timescale 1ns/1ps
module cc_tb;
  reg clk=0, rst=1; wire [31:0] od; wire ov, h; wire [2:0] ok; integer n=0;
  gvm #(.MEM(16384), .WORD(32)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin n=n+1;
    if (ov && ok==3'd0) $display("NUM=%0d", $signed(od));
    if (h) begin $display("DUNG"); $finish; end
    if (n>=3000000) begin $display("HETGIO"); $finish; end
  end endmodule

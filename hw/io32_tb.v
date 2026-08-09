`timescale 1ns/1ps
module io32_tb;
  reg clk=0, rst=1; wire [31:0] od; wire ov, h; wire [2:0] ok;
  gvm #(.MEM(8192), .WORD(32)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; #30000000 begin $display("HET GIO"); $finish; end end
  always @(posedge clk) begin
    if (ov) begin
      if      (ok==3'd0) $display("NUM=%0d", $signed(od));
      else if (ok==3'd3) $display("FIX=%0d", $signed(od));
      else if (ok==3'd4) $display("DSE=%0d", $signed(od));
      else if (ok==3'd5) $display("DSEND");
    end
    if (h) begin $display("DUNG"); $finish; end
  end
endmodule

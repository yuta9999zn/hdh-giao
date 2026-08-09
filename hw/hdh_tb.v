`timescale 1ns/1ps
module hdh_tb;
  reg clk=0, rst=1; wire [31:0] od; wire ov, h; wire [2:0] ok; integer ncyc=0;
  gvm #(.MEM(16384), .WORD(32)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin
    ncyc = ncyc + 1;
    if (ov) begin
      if      (ok==3'd0) $display("NUM=%0d", $signed(od));
      else if (ok==3'd1) $display("CHR=%0d", od);
      else if (ok==3'd2) $display("SEND");
      else if (ok==3'd6) $display("AN");
    end
    if (h) begin $display("DUNG ncyc=%0d", ncyc); $finish; end
    if (ncyc >= 4000000) begin $display("HET GIO ncyc=%0d", ncyc); $finish; end
  end
endmodule

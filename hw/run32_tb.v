`timescale 1ns/1ps
module run32_tb;
  reg clk=0, rst=1; reg [31:0] ncyc=0;
  wire [31:0] out_data; wire out_valid, halt;
  gvm #(.MEM(8192), .WORD(32)) dut(.clk(clk),.rst(rst),.out_data(out_data),.out_valid(out_valid),.halt(halt));
  always #5 clk = ~clk;
  initial begin #12 rst=0; #20000000 begin $display("HET GIO"); $finish; end end
  always @(posedge clk) begin
    if (!rst) ncyc <= ncyc + 1;
    if (out_valid) $display("ROI=%0d", $signed(out_data));
    if (halt) begin $display("CPU DUNG."); $display("CYCLES=%0d", ncyc); $finish; end
  end
endmodule

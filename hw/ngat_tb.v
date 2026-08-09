`timescale 1ns/1ps
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

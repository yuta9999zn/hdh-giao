`timescale 1ns/1ps
module flt_tb;
  reg clk=0, rst=1; wire [15:0] od; wire ov, h; wire [2:0] ok; wire [7:0] proc; integer n=0;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),.out_proc(proc),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin n=n+1;
    if (ov && (ok==3'd7 || ok==3'd0)) $display("XUAT proc=%0d val=%0d", proc, $signed(od));
    if (h) begin $display("HALT n=%0d", n); $finish; end
    if (n>=12000) begin
      $display("DEAD %0d %0d %0d", dut.t_dead[0], dut.t_dead[1], dut.t_dead[2]);
      $display("SIGMA %0d %0d %0d", dut.sigma[0], dut.sigma[1], dut.sigma[2]);
      $finish;
    end
  end endmodule

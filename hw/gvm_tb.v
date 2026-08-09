// gvm_tb.v — Testbench mô phỏng GVM. Chạy: iverilog -o gvm gvm.v gvm_tb.v && vvp gvm
`timescale 1ns/1ps
module gvm_tb;
  reg clk = 0, rst = 1;
  wire [15:0] out_data; wire out_valid, halt;

  gvm #(.MEM(256)) dut(.clk(clk), .rst(rst), .out_data(out_data),
                       .out_valid(out_valid), .halt(halt));

  always #5 clk = ~clk;            // clock 100 MHz

  initial begin
    #12 rst = 0;                   // nhả reset sau vài chu kỳ
    #5000 begin
      $display("HẾT GIỜ — không dừng?"); $finish;
    end
  end

  always @(posedge clk) begin
    if (out_valid) $display("RỌI = %0d", out_data);     // mong đợi 15
    if (halt)      begin $display("CPU DỪNG."); $finish; end
  end
endmodule

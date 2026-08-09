`timescale 1ns/1ps
// trap_tb.v — TESTBENCH ĐÓNG VAI NHÂN: phục vụ gọi-hệ cho CPU trên cổng logic.
module trap_tb;
  reg clk = 0, rst = 1;
  wire [15:0] out_data;  wire out_valid, halt;
  wire        trap_valid; wire [7:0] trap_num, trap_nargs;
  wire [15:0] trap_arg, trap_arg1, trap_arg2;
  reg         trap_ack = 0; reg [15:0] trap_ret = 0;
  integer     n_trap = 0, n_out = 0, cyc = 0;

  gvm #(.MEM(4096)) dut(.clk(clk), .rst(rst),
        .out_data(out_data), .out_valid(out_valid), .halt(halt),
        .dbg_a(16'd0), .dbg_re(1'b0), .dbg_we(1'b0), .dbg_wd(0),
        .trap_valid(trap_valid), .trap_num(trap_num), .trap_arg(trap_arg),
        .trap_arg1(trap_arg1), .trap_arg2(trap_arg2),
        .trap_nargs(trap_nargs), .trap_ack(trap_ack), .trap_ret(trap_ret));

  always #5 clk = ~clk;
  initial begin #12 rst = 0; #200000 begin $display("HET GIO"); $finish; end end

  always @(posedge clk) if (!rst) cyc = cyc + 1;

  // ★ NHÂN (bằng phần cứng): thấy trap_valid → phục vụ → trả kết quả → ack đúng 1 chu kỳ
  always @(posedge clk) begin
    if (!rst && trap_valid && !trap_ack) begin
      n_trap = n_trap + 1;
      case (trap_num)
        8'd11: trap_ret <= 16'd700;                 // "ở"        → 700
        8'd50: trap_ret <= trap_arg << 1;           // "nhân đôi" → 2×đối
        8'd51: trap_ret <= trap_arg + trap_arg1;                        // ★ 2 đối
        8'd52: trap_ret <= trap_arg + 16'd10*trap_arg1 + 16'd100*trap_arg2;  // ★ 3 đối, có thứ tự
        default: trap_ret <= 16'hFFFF;              // không hiểu → −1
      endcase
      $display("   [nhan] chu ky %0d: TRAP so=%0d nargs=%0d doi=%0d,%0d,%0d",
               cyc, trap_num, trap_nargs, trap_arg, trap_arg1, trap_arg2);
      trap_ack <= 1'b1;
    end else trap_ack <= 1'b0;
  end

  always @(posedge clk) if (out_valid) begin
    n_out = n_out + 1;
    $display("   [CPU ] chu ky %0d: ROI = %0d", cyc, out_data);
  end

  always @(posedge clk) if (halt) begin
    $display("   CPU DUNG sau %0d chu ky · %0d lan trap · %0d lan roi", cyc, n_trap, n_out);
    $finish;
  end
endmodule

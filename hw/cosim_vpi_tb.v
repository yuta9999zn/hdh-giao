`timescale 1ns/1ps
// ============================================================
// cosim_vpi_tb.v — ĐỒNG MÔ PHỎNG QUA VPI: cổng logic ⟷ nhân HĐH-GIAO thật, KHÔNG qua tệp.
// ------------------------------------------------------------
// So với `cosim_tb.v` (điểm hẹn TỆP): ở đây testbench không gói đối, không dò tệp, không `wait`.
// Nó chỉ gọi `$giao_trap(...)` — một hàm hệ thống do `giao_vpi.c` cài vào bộ mô phỏng. Lời gọi ấy
// CHẶN NGAY tại thời điểm mô phỏng này: C duyệt thẳng `dut.ram[]` lấy chuỗi đối, hỏi nhân qua
// socket, cấp chuỗi trả về vào heap của CPU, rồi trả con trỏ. Mỗi lời xin tốn ĐÚNG 2 chu kỳ.
// ============================================================
module cosim_vpi_tb;
  reg clk = 0, rst = 1;
  wire [31:0] out_data;  wire out_valid, halt;  wire [2:0] out_kind;
  wire        trap_valid; wire [7:0] trap_num, trap_nargs;
  wire [31:0] trap_arg, trap_arg1, trap_arg2;
  reg         trap_ack = 0; reg [31:0] trap_ret = 0;
  integer     n_trap = 0, cyc = 0, i = 0;

  gvm #(.MEM(4096), .WORD(32)) dut(.clk(clk), .rst(rst),
        .out_data(out_data), .out_valid(out_valid), .out_kind(out_kind), .halt(halt),
        .dbg_a(16'd0), .dbg_re(1'b0), .dbg_we(1'b0), .dbg_wd(0),
        .trap_valid(trap_valid), .trap_num(trap_num), .trap_arg(trap_arg),
        .trap_arg1(trap_arg1), .trap_arg2(trap_arg2),
        .trap_nargs(trap_nargs), .trap_ack(trap_ack), .trap_ret(trap_ret));

  always #5 clk = ~clk;
  initial begin #12 rst = 0; #40000000 begin $display("   HET GIO"); $finish; end end
  always @(posedge clk) if (!rst) cyc = cyc + 1;

  // ── in ra những gì CPU RỌI (tự mã hoá UTF-8 — cắt xuống 8 bit sẽ hỏng chữ tiếng Việt) ──
  reg [31:0] obuf [0:1023]; integer olen = 0; reg [31:0] cp;
  always @(posedge clk) if (out_valid) begin
    if (out_kind == 3'd1) begin obuf[olen] = out_data; olen = olen + 1; end
    else if (out_kind == 3'd2) begin
      $write("   [CPU-silicon] ");
      for (i = 0; i < olen; i = i + 1) begin
        cp = obuf[i];
        if (cp < 32'h80) $write("%c", cp[7:0]);
        else if (cp < 32'h800) begin
          $write("%c", 8'hC0 | cp[10:6]);  $write("%c", 8'h80 | cp[5:0]);
        end else begin
          $write("%c", 8'hE0 | cp[15:12]); $write("%c", 8'h80 | cp[11:6]); $write("%c", 8'h80 | cp[5:0]);
        end
      end
      $write("\n"); olen = 0;
    end else $display("   [CPU-silicon] %0d", out_data);
  end

  // ★ TOÀN BỘ ĐIỂM HẸN GỌN TRONG MỘT DÒNG. `!trap_ack` chặn phục vụ trùng:
  //   chu kỳ A: valid=1, ack=0 → gọi nhân, ack<=1 · chu kỳ B: CPU lấy mẫu ack, ta hạ ack
  always @(posedge clk) begin
    if (!rst && trap_valid && !trap_ack) begin
      n_trap  = n_trap + 1;
      trap_ret <= $giao_trap(trap_num, trap_nargs, trap_arg, trap_arg1, trap_arg2);
      trap_ack <= 1'b1;
    end else trap_ack <= 1'b0;
  end

  always @(posedge clk) if (halt) begin
    $display("   CPU DUNG sau %0d chu ky · %0d lan xin nhan (%0d lan qua VPI)",
             cyc, n_trap, $giao_dem);
    $finish;
  end
endmodule

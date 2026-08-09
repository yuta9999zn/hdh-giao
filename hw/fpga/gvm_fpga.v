// gvm_fpga.v — TOP WRAPPER nạp GVM CDFL (hw/gvm.v hiện-tại) lên iCE40 UP5K (iCEBreaker).
//   Rút ~45 chân I/O của `gvm` xuống 5 chân khớp icebreaker.pcf (clk/rst_n/uart_tx/led_halt/led[0]).
//   GỘP mọi output (XOR-reduce) vào led[0] để yosys GIỮ TRỌN lõi (không trim phần không nối).
//   Power-on-reset 255 chu kỳ + nút rst_n (mức thấp). gvm dùng RESET ĐỒNG-BỘ.
//   Dùng: đặt MEM=256 (vừa UP5K). Synth: yosys (đọc ../gvm.v + file này), top=gvm_fpga.
module gvm_fpga #(parameter MEM = 256, parameter WORD = 16) (
  input  clk,
  input  rst_n,            // nút bấm mức-thấp (1=chạy, 0=reset)
  output led_halt,         // LED đỏ = CPU DỪNG
  output led_act,          // LED xanh = "nhịp" output (XOR mọi cổng ra)
  output uart_tx           // giữ chân (mức = out_valid)
);
  reg [7:0] por = 8'd0;                         // bộ đếm power-on-reset
  always @(posedge clk) if (por != 8'hFF) por <= por + 8'd1;
  wire rst = (por != 8'hFF) | ~rst_n;           // reset lúc nạp + khi giữ nút

  wire [WORD-1:0] od; wire ov, h, se, sr; wire [2:0] ok; wire [7:0] op, sc; wire [1:0] os;
  gvm #(.MEM(MEM), .WORD(WORD)) cpu (
    .clk(clk), .rst(rst),
    .out_data(od), .out_valid(ov), .out_kind(ok), .out_proc(op), .out_state(os),
    .sched_evt(se), .sched_cur(sc), .sched_rho(sr), .halt(h)
  );

  assign led_halt = h;
  assign led_act  = ^{od, ok, op, os, sc, ov, se, sr};   // gộp MỌI output → giữ trọn lõi gate-level
  assign uart_tx  = ov;
endmodule

`timescale 1ns/1ps
// ============================================================
// bo_tb.v — MÔ PHỎNG CHÍNH CÁI ĐỈNH SẼ NẠP LÊN BO (`gvm_bo.v`), qua DÂY UART THẬT.
// ------------------------------------------------------------
// Testbench này KHÔNG đụng vào chân trap. Nó chỉ là **sợi cáp USB-UART**: cắm một cặp uart_rx/uart_tx
// ngược chiều với bo, rồi bơm từng byte qua VPI tới máy chủ đang chạy nhân HĐH-GIAO thật.
// Nhờ vậy toàn bộ đường đi — cầu byte, khung 0xA5/0xB5/0x4D/0x57/0x5A, UART 8N1, cấp heap từ xa —
// được kiểm ĐÚNG NHƯ khi bitstream chạy trên silicon; chỉ khác cái đồng hồ.
// ============================================================
module bo_tb;
  reg clk = 0, rst_n = 0;
  wire bo_tx;  wire [7:0] led;
  wire bo_rx;

  localparam CHIA = 4;                       // mô phỏng: baud cao cho nhanh (bo thật dùng 25)

  gvm_bo #(.CHIA(CHIA), .MEM(4096)) bo(
      .clk(clk), .rst_n(rst_n), .uart_rx(bo_rx), .uart_tx(bo_tx), .led(led));

  always #5 clk = ~clk;
  initial begin #40 rst_n = 1; #200000000 begin $display("   HET GIO"); $finish; end end

  integer cyc = 0;
  always @(posedge clk) cyc = cyc + 1;

  // ── đầu CÁP phía máy chủ: nhận byte bo phát lên ──
  wire [7:0] cap_byte; wire cap_co;
  uart_rx #(.CHIA(CHIA)) cap_rx(.clk(clk), .rst(~rst_n), .rx(bo_tx),
                                .byte_ra(cap_byte), .co(cap_co));
  integer n_len = 0, n_xuong = 0;
  always @(posedge clk) if (cap_co) begin
    $giao_byte_ra(cap_byte);                 // → socket → nhân GIAO
    n_len = n_len + 1;
  end

  // ── đầu CÁP phía máy chủ: phát byte nhân gửi xuống ──
  reg        cap_gui = 0; reg [7:0] cap_ra = 0; wire cap_ranh;

  uart_tx #(.CHIA(CHIA)) cap_tx(.clk(clk), .rst(~rst_n), .gui(cap_gui), .byte_vao(cap_ra),
                                .tx(bo_rx), .ranh(cap_ranh));


  integer b = 0;
  always @(posedge clk) begin
    cap_gui <= 1'b0;
    if (rst_n && cap_ranh && !cap_gui) begin
      b = $giao_byte_vao;                    // −1 = chưa có gì
      if (b >= 0) begin cap_ra <= b; cap_gui <= 1'b1; n_xuong = n_xuong + 1; end
    end
  end

  // ── CPU dừng: bo phát 0xC5, nhưng ta đợi hàng byte rút hết rồi mới nghỉ ──
  integer nghi = 0;
  always @(posedge clk) if (bo.halt) begin
    nghi = nghi + 1;
    if (nghi > 20000) begin
      $display("   BO DUNG sau %0d chu ky · %0d byte len · %0d byte xuong", cyc, n_len, n_xuong);
      $finish;
    end
  end
endmodule

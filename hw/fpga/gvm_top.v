// gvm_top.v — TOP-LEVEL cho FPGA THẬT.
// Bọc gvm_core (CPU GVM dựng từ NAND) + xuất RỌI ra phần cứng:
//   • led[7:0]  = byte thấp của giá trị RỌI gần nhất (THẤY trực tiếp: 65533&0xFF=0xFD, rồi 0x00)
//   • led_halt  = CPU đã DỪNG
//   • uart_tx   = mỗi RỌI gửi 2 byte (cao, thấp) @ BAUD → host log đủ chuỗi [65533,0,...]
// Lõi quyết định tác tử (Ψ+lookahead+cổng phê duyệt) chạy ngay khi nhả reset.
module gvm_top #(
  parameter integer CLK_HZ = 12_000_000,   // clock bo (sửa theo bo của bạn)
  parameter integer BAUD   = 115200
) (
  input        clk,
  input        rst_n,        // nút reset (mức thấp tích cực) — đổi cực tính nếu bo khác
  output [7:0] led,
  output       led_halt,
  output       uart_tx
);
  wire rst = ~rst_n;
  wire [15:0] out_data; wire out_valid, halt;

  gvm_core #(.ROM_DEPTH(2048), .RAM_DEPTH(1024)) core (
    .clk(clk), .rst(rst), .out_data(out_data), .out_valid(out_valid), .halt(halt));

  // LED: giữ byte thấp của RỌI gần nhất; 1 LED báo dừng
  reg [15:0] last;
  always @(posedge clk or posedge rst)
    if (rst) last <= 16'd0; else if (out_valid) last <= out_data;
  assign led      = last[7:0];
  assign led_halt = halt;

  // UART: gửi mỗi RỌI thành 2 byte (cao trước, thấp sau)
  wire tx_busy;
  reg  [7:0]  tx_data;
  reg         tx_send;
  reg         phase;          // 0 = chờ gửi byte cao, 1 = chờ gửi byte thấp
  reg  [15:0] pend;
  reg         has;
  uart_tx #(.DIV(CLK_HZ / BAUD)) u (
    .clk(clk), .rst(rst), .send(tx_send), .data(tx_data), .tx(uart_tx), .busy(tx_busy));

  always @(posedge clk or posedge rst) begin
    if (rst) begin tx_send <= 1'b0; phase <= 1'b0; has <= 1'b0; end
    else begin
      tx_send <= 1'b0;
      if (out_valid) begin pend <= out_data; has <= 1'b1; phase <= 1'b0; end
      else if (has && !tx_busy && !tx_send) begin
        if (phase == 1'b0) begin tx_data <= pend[15:8]; tx_send <= 1'b1; phase <= 1'b1; end
        else               begin tx_data <= pend[7:0];  tx_send <= 1'b1; has   <= 1'b0; end
      end
    end
  end
endmodule

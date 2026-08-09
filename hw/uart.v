// ============================================================
// uart.v — UART 8N1 tối giản (chỉ để nối chân trap của GVM ra ngoài bo).
// ============================================================
module uart_tx #(parameter CHIA = 25) (            // CHIA = f_clk / baud
  input clk, input rst,
  input       gui,        // xung 1 chu kỳ: bắt đầu phát `byte_vào`
  input [7:0] byte_vao,
  output reg  tx,
  output      ranh
);
  reg [15:0] dem = 0;
  reg [3:0]  bit_i = 0;
  reg [9:0]  khung = 10'h3FF;                       // [start, 8 dữ liệu, stop]
  reg        ban = 0;
  assign ranh = ~ban;

  initial tx = 1'b1;
  always @(posedge clk) begin
    if (rst) begin ban <= 0; tx <= 1'b1; dem <= 0; bit_i <= 0; end
    else if (!ban) begin
      tx <= 1'b1;
      if (gui) begin khung <= {1'b1, byte_vao, 1'b0}; ban <= 1; dem <= 0; bit_i <= 0; end
    end else begin
      tx <= khung[0];
      if (dem == CHIA - 1) begin
        dem <= 0; khung <= {1'b1, khung[9:1]};
        if (bit_i == 4'd9) ban <= 0; else bit_i <= bit_i + 1;
      end else dem <= dem + 1;
    end
  end
endmodule

module uart_rx #(parameter CHIA = 25) (
  input clk, input rst, input rx,
  output reg [7:0] byte_ra,
  output reg       co                                // xung 1 chu kỳ khi nhận xong 1 byte
);
  reg [15:0] dem = 0;
  reg [3:0]  bit_i = 0;
  reg        ban = 0;
  reg        rx1 = 1'b1, rx2 = 1'b1;                 // đồng bộ hai tầng

  always @(posedge clk) begin
    rx1 <= rx; rx2 <= rx1;
    co  <= 1'b0;
    if (rst) begin ban <= 0; dem <= 0; bit_i <= 0; end
    else if (!ban) begin
      if (!rx2) begin ban <= 1; dem <= 0; bit_i <= 0; end           // thấy cạnh xuống = start
    end else begin
      // bit dữ liệu đầu lấy mẫu sau 1,5 bit (giữa bit 0); các bit sau cứ mỗi 1 bit.
      // bit_i == 8 là nhịp của STOP: đợi hết rồi mới nhả, kẻo bit 7 = 0 bị hiểu nhầm là start mới.
      if (dem == ((bit_i == 4'd0) ? (CHIA + (CHIA >> 1) - 1) : (CHIA - 1))) begin
        dem <= 0;
        if (bit_i == 4'd8) begin ban <= 0; co <= 1'b1; end
        else begin byte_ra <= {rx2, byte_ra[7:1]}; bit_i <= bit_i + 1; end
      end else dem <= dem + 1;
    end
  end
endmodule

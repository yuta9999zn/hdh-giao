// uart_tx.v — Bộ phát UART 8N1 (gửi RỌI ra chân TX, host đọc bằng terminal).
// DIV = CLK_HZ / BAUD (số chu kỳ mỗi bit). Khung 10-bit: {stop=1, data[7:0], start=0},
// dịch ra LSB trước; khi rảnh sh=toàn 1 → tx=1 (mức nghỉ).
module uart_tx #(parameter integer DIV = 104) (
  input            clk,
  input            rst,
  input            send,        // xung 1 chu kỳ: bắt đầu gửi 'data'
  input  [7:0]     data,
  output           tx,
  output reg       busy
);
  reg [9:0]  sh = 10'h3FF;
  reg [3:0]  nbits;
  reg [15:0] cnt;
  assign tx = sh[0];
  always @(posedge clk or posedge rst) begin
    if (rst) begin sh <= 10'h3FF; busy <= 1'b0; cnt <= 0; nbits <= 0; end
    else if (!busy) begin
      if (send) begin sh <= {1'b1, data, 1'b0}; busy <= 1'b1; cnt <= 0; nbits <= 0; end
    end else begin
      if (cnt == DIV-1) begin
        cnt   <= 0;
        sh    <= {1'b1, sh[9:1]};          // dịch ra, đệm 1 (nghỉ)
        nbits <= nbits + 4'd1;
        if (nbits == 4'd9) busy <= 1'b0;   // đã gửi đủ 10 bit
      end else cnt <= cnt + 16'd1;
    end
  end
endmodule

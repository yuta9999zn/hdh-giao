`timescale 1ns/1ps
module fpga_tb;
  reg clk=0, rst_n=0;
  wire [7:0] led; wire led_halt, uart_tx;
  // CLK/BAUD nhỏ để mô phỏng nhanh (DIV=10)
  gvm_top #(.CLK_HZ(1000000), .BAUD(100000)) dut(
    .clk(clk), .rst_n(rst_n), .led(led), .led_halt(led_halt), .uart_tx(uart_tx));
  always #5 clk = ~clk;

  // thu byte UART qua đường nội bộ tx_send/tx_data (tránh phải dựng UART RX)
  integer nb = 0; reg [7:0] bytes [0:63];
  reg tx_seen = 0;
  always @(posedge clk) begin
    if (dut.tx_send) begin bytes[nb] = dut.tx_data; nb = nb + 1; end
    if (uart_tx == 0) tx_seen = 1;     // chân TX có kéo xuống (start bit) → có truyền thật
  end

  integer i, v; integer nval = 0; integer ok = 1;
  // kỳ vọng: 65533,0,65533,0,65533,0,65533,0,65533,0,65533,0,0
  integer exp [0:12];
  initial begin
    exp[0]=65533;exp[1]=0;exp[2]=65533;exp[3]=0;exp[4]=65533;exp[5]=0;exp[6]=65533;
    exp[7]=0;exp[8]=65533;exp[9]=0;exp[10]=65533;exp[11]=0;exp[12]=0;
    #12 rst_n = 1;
    #16000000 begin $display("HET GIO"); $finish; end
  end

  always @(posedge clk) if (led_halt) begin
    #200;  // chờ nốt UART xả
    $display("LED (byte thap ROI cuoi) = %0d (0x%02h)", led, led);
    $display("chan TX co truyen (start bit) = %0d", tx_seen);
    $display("So byte UART = %0d -> ghep thanh %0d gia tri:", nb, nb/2);
    for (i=0; i+1<nb; i=i+2) begin
      v = (bytes[i]<<8) | bytes[i+1];
      if (v !== exp[nval]) begin ok=0; $display("  [%0d] = %0d  != ky vong %0d  ✗", nval, v, exp[nval]); end
      else $display("  [%0d] = %0d  ✓", nval, v);
      nval = nval + 1;
    end
    $display(ok ? "==> UART KHOP [65533,0x6,0] — TOP-LEVEL DUNG" : "==> SAI");
    $finish;
  end
endmodule

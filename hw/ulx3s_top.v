// ============================================================
// ulx3s_top.v — vỏ bọc cho bo ULX3S (Lattice ECP5). Chỉ đổi TÊN CHÂN, không đổi logic.
// Bo khác thì viết một vỏ tương tự + tệp ràng buộc chân của bo ấy; `gvm_bo.v` giữ nguyên.
// ============================================================
module ulx3s_top (
  input        clk_25mhz,
  input  [6:0] btn,
  output [7:0] led,
  output       ftdi_rxd,      // FPGA → máy chủ
  input        ftdi_txd,      // máy chủ → FPGA
  output       wifi_gpio0     // phải giữ MỨC CAO, kẻo ESP32 reset bo
);
  assign wifi_gpio0 = 1'b1;

  // 25 MHz / 25 = 1 Mbaud
  gvm_bo #(.CHIA(25), .MEM(4096)) bo(
      .clk(clk_25mhz),
      .rst_n(btn[0]),          // nút PWR trên ULX3S: nhả = 1, nhấn = 0
      .uart_rx(ftdi_txd),
      .uart_tx(ftdi_rxd),
      .led(led));
endmodule

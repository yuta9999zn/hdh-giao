## arty_a7.xdc — ràng buộc chân cho Digilent Arty A7 (Xilinx Artix-7). Dùng với Vivado.
## clk = 100 MHz onboard → đặt CLK_HZ=100_000_000 khi instance gvm_top.
## KIỂM LẠI theo Master XDC của bo bạn (A7-35T vs A7-100T có thể khác).

set_property -dict { PACKAGE_PIN E3  IOSTANDARD LVCMOS33 } [get_ports { clk }]
create_clock -add -name sys_clk -period 10.00 [get_ports { clk }]

## nút reset (mức thấp): dùng BTN0; logic top đảo (rst_n)
set_property -dict { PACKAGE_PIN D9  IOSTANDARD LVCMOS33 } [get_ports { rst_n }]

## UART TX (FPGA → USB-UART). Arty: uart_txd_in (host nhận) = A9.
set_property -dict { PACKAGE_PIN A9  IOSTANDARD LVCMOS33 } [get_ports { uart_tx }]

## 4 LED onboard cho byte thấp [3:0]; led_halt dùng LED4 (RGB) hoặc 1 LED rời.
set_property -dict { PACKAGE_PIN H5  IOSTANDARD LVCMOS33 } [get_ports { led[0] }]
set_property -dict { PACKAGE_PIN J5  IOSTANDARD LVCMOS33 } [get_ports { led[1] }]
set_property -dict { PACKAGE_PIN T9  IOSTANDARD LVCMOS33 } [get_ports { led[2] }]
set_property -dict { PACKAGE_PIN T10 IOSTANDARD LVCMOS33 } [get_ports { led[3] }]
## led[4..7]: dùng PMOD nếu cần thêm; led_halt:
set_property -dict { PACKAGE_PIN G6  IOSTANDARD LVCMOS33 } [get_ports { led_halt }]  ## LD4 green

## program.hex phải nằm cùng thư mục nguồn để $readmemh nạp khi tổng hợp.

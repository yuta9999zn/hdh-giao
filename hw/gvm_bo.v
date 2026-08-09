// ============================================================
// gvm_bo.v — ĐỈNH CHO BO FPGA THẬT: GVM + cầu UART nối chân trap ra máy chủ.
// ------------------------------------------------------------
// Trên bo không có Python, nên nhân HĐH-GIAO vẫn ở MÁY CHỦ — nối qua UART. Đúng cái kiến trúc đã
// dựng từ đầu: **CPU không tự làm I/O, nó chìa lời xin ra rồi chờ nhân**. Chỉ khác: dây bây giờ là
// dây đồng thật, không phải socket.
//
// KHUNG BYTE (bo → chủ):
//   0xA5  số  nargs  đ0[4]  đ1[4]  đ2[4]  0x00    (16 byte) — xin gọi-hệ
//   0xB5  kind  dữ_liệu[4]                        (6 byte)  — CPU RỌI
//   0x4D  dữ_liệu[4]                              (5 byte)  — trả lời lệnh ĐỌC ô nhớ
//   0xC5                                          (1 byte)  — CPU đã DỪNG
// KHUNG BYTE (chủ → bo):
//   0x4D  địa_chỉ[2]                — đọc ô nhớ (để duyệt chuỗi đối nằm trong heap của CPU)
//   0x57  địa_chỉ[2]  dữ_liệu[4]    — ghi ô nhớ (để cấp chuỗi trả về vào heap của CPU)
//   0x5A  kết_quả[4]                — phục vụ xong, đây là kết quả → CPU chạy tiếp
// Mọi số nhiều byte đều LITTLE-ENDIAN.
// ============================================================
module gvm_bo #(parameter CHIA = 25, parameter MEM = 4096) (   // CHIA = f_clk / baud
  input        clk,
  input        rst_n,          // nút reset (tích cực THẤP)
  input        uart_rx,        // từ máy chủ
  output       uart_tx,        // tới máy chủ
  output [7:0] led
);
  wire rst = ~rst_n;

  // ── lõi GVM ──
  wire [31:0] out_data;  wire out_valid, halt;  wire [2:0] out_kind;
  wire        trap_valid; wire [7:0] trap_num, trap_nargs;
  wire [31:0] trap_arg, trap_arg1, trap_arg2;
  reg         trap_ack; reg [31:0] trap_ret;
  reg  [15:0] dbg_a; reg dbg_we; reg [31:0] dbg_wd;   // dbg_re = xin_doc (xung 1 chu kỳ)
  wire [31:0] dbg_q;

  gvm #(.MEM(MEM), .WORD(32)) loi(.clk(clk), .rst(rst),
        .out_data(out_data), .out_valid(out_valid), .out_kind(out_kind), .halt(halt),
        .trap_valid(trap_valid), .trap_num(trap_num), .trap_arg(trap_arg),
        .trap_arg1(trap_arg1), .trap_arg2(trap_arg2), .trap_nargs(trap_nargs),
        .trap_ack(trap_ack), .trap_ret(trap_ret),
        .dbg_a(dbg_a), .dbg_re(xin_doc), .dbg_we(dbg_we), .dbg_wd(dbg_wd), .dbg_q(dbg_q));

  // ── UART ──
  reg        tx_gui; reg [7:0] tx_byte;  wire tx_ranh;
  wire [7:0] rx_byte; wire rx_co;
  uart_tx #(.CHIA(CHIA)) u_tx(.clk(clk), .rst(rst), .gui(tx_gui), .byte_vao(tx_byte),
                              .tx(uart_tx), .ranh(tx_ranh));
  uart_rx #(.CHIA(CHIA)) u_rx(.clk(clk), .rst(rst), .rx(uart_rx),
                              .byte_ra(rx_byte), .co(rx_co));

  // ── HÀNG BYTE CHỜ PHÁT ──
  reg [7:0] hang [0:511];
  reg [8:0] h_ghi, h_doc;
  wire      hang_trong = (h_ghi == h_doc);

  // ── HÀNG SỰ KIỆN RỌI (CPU in ra lúc cầu đang bận thì KHÔNG được mất) ──
  reg [34:0] roi_hang [0:63];        // {kind[2:0], data[31:0]}
  reg [5:0]  r_ghi, r_doc;
  always @(posedge clk) begin
    if (rst) r_ghi <= 0;
    else if (out_valid) begin roi_hang[r_ghi] <= {out_kind, out_data}; r_ghi <= r_ghi + 1; end
  end

  // ── cờ dùng chung, mỗi cờ đúng MỘT chủ (khối "cờ" ở dưới) ──
  reg trap_da_gui, doc_cho, dung_da_gui;
  reg xin_doc, trap_xong;

  localparam P_RANH=0, P_TRAP=1, P_ROI=2, P_DOC=3, P_DUNG=4;
  reg [2:0]  p_tt; reg [4:0] p_i; reg [31:0] p_dl; reg [2:0] p_kind;

  wire p_ranh = (p_tt == P_RANH);
  wire co_trap = trap_valid && !trap_da_gui;
  wire lay_doc  = p_ranh && doc_cho;
  wire mo_trap  = p_ranh && !doc_cho && co_trap;
  wire lay_roi  = p_ranh && !doc_cho && !co_trap && (r_doc != r_ghi);
  wire lay_dung = p_ranh && !doc_cho && !co_trap && (r_doc == r_ghi) && halt && !dung_da_gui;

  // ── BỘ PHÁT: mỗi chu kỳ đẩy ĐÚNG MỘT byte vào hàng ──
  always @(posedge clk) begin
    if (rst) begin h_ghi <= 0; p_tt <= P_RANH; p_i <= 0; r_doc <= 0; end
    else case (p_tt)
      P_RANH: begin
        p_i <= 0;
        if      (lay_doc)  begin p_tt <= P_DOC;  p_dl <= dbg_q; end
        else if (mo_trap)  begin p_tt <= P_TRAP; end
        else if (lay_roi)  begin p_tt <= P_ROI;
                                 {p_kind, p_dl} <= roi_hang[r_doc]; r_doc <= r_doc + 1; end
        else if (lay_dung) begin p_tt <= P_DUNG; end
      end
      P_TRAP: begin
        case (p_i)
          5'd0:  hang[h_ghi] <= 8'hA5;
          5'd1:  hang[h_ghi] <= trap_num;
          5'd2:  hang[h_ghi] <= trap_nargs;
          5'd3:  hang[h_ghi] <= trap_arg[7:0];     5'd4:  hang[h_ghi] <= trap_arg[15:8];
          5'd5:  hang[h_ghi] <= trap_arg[23:16];   5'd6:  hang[h_ghi] <= trap_arg[31:24];
          5'd7:  hang[h_ghi] <= trap_arg1[7:0];    5'd8:  hang[h_ghi] <= trap_arg1[15:8];
          5'd9:  hang[h_ghi] <= trap_arg1[23:16];  5'd10: hang[h_ghi] <= trap_arg1[31:24];
          5'd11: hang[h_ghi] <= trap_arg2[7:0];    5'd12: hang[h_ghi] <= trap_arg2[15:8];
          5'd13: hang[h_ghi] <= trap_arg2[23:16];  5'd14: hang[h_ghi] <= trap_arg2[31:24];
          default: hang[h_ghi] <= 8'h00;
        endcase
        h_ghi <= h_ghi + 1;
        if (p_i == 5'd15) p_tt <= P_RANH; else p_i <= p_i + 1;
      end
      P_ROI: begin
        case (p_i)
          5'd0: hang[h_ghi] <= 8'hB5;            5'd1: hang[h_ghi] <= {5'b0, p_kind};
          5'd2: hang[h_ghi] <= p_dl[7:0];        5'd3: hang[h_ghi] <= p_dl[15:8];
          5'd4: hang[h_ghi] <= p_dl[23:16];      default: hang[h_ghi] <= p_dl[31:24];
        endcase
        h_ghi <= h_ghi + 1;
        if (p_i == 5'd5) p_tt <= P_RANH; else p_i <= p_i + 1;
      end
      P_DOC: begin
        case (p_i)
          5'd0: hang[h_ghi] <= 8'h4D;            5'd1: hang[h_ghi] <= p_dl[7:0];
          5'd2: hang[h_ghi] <= p_dl[15:8];       5'd3: hang[h_ghi] <= p_dl[23:16];
          default: hang[h_ghi] <= p_dl[31:24];
        endcase
        h_ghi <= h_ghi + 1;
        if (p_i == 5'd4) p_tt <= P_RANH; else p_i <= p_i + 1;
      end
      P_DUNG:  begin hang[h_ghi] <= 8'hC5; h_ghi <= h_ghi + 1; p_tt <= P_RANH; end
      default: p_tt <= P_RANH;
    endcase
  end

  // ── BỘ RÚT: hàng → uart_tx ──
  always @(posedge clk) begin
    tx_gui <= 1'b0;
    if (rst) h_doc <= 0;
    else if (!hang_trong && tx_ranh && !tx_gui) begin
      tx_byte <= hang[h_doc]; tx_gui <= 1'b1; h_doc <= h_doc + 1;
    end
  end

  // ── BỘ THU LỆNH TỪ MÁY CHỦ (chủ duy nhất của dbg_*, trap_ack/ret) ──
  localparam T_LENH=0, T_DOC_DC=1, T_GHI_DC=2, T_GHI_DL=3, T_TRA=4;
  reg [2:0]  t_tt; reg [2:0] t_i; reg [31:0] t_dl; reg [15:0] t_dc;

  always @(posedge clk) begin
    dbg_we <= 1'b0; trap_ack <= 1'b0; xin_doc <= 1'b0; trap_xong <= 1'b0;
    if (rst) begin t_tt <= T_LENH; t_i <= 0; end
    else if (rx_co) case (t_tt)
      T_LENH: begin
        t_i <= 0;
        if      (rx_byte == 8'h4D) t_tt <= T_DOC_DC;
        else if (rx_byte == 8'h57) t_tt <= T_GHI_DC;
        else if (rx_byte == 8'h5A) t_tt <= T_TRA;
      end
      T_DOC_DC: begin
        if (t_i == 0) begin t_dc[7:0] <= rx_byte; t_i <= 1; end
        else begin dbg_a <= {rx_byte, t_dc[7:0]}; xin_doc <= 1'b1; t_tt <= T_LENH; end
      end
      T_GHI_DC: begin
        if (t_i == 0) begin t_dc[7:0] <= rx_byte; t_i <= 1; end
        else begin t_dc[15:8] <= rx_byte; t_tt <= T_GHI_DL; t_i <= 0; end
      end
      T_GHI_DL: begin
        t_dl <= {rx_byte, t_dl[31:8]};
        if (t_i == 3'd3) begin
          dbg_a <= t_dc; dbg_wd <= {rx_byte, t_dl[31:8]}; dbg_we <= 1'b1; t_tt <= T_LENH;
        end else t_i <= t_i + 1;
      end
      T_TRA: begin
        t_dl <= {rx_byte, t_dl[31:8]};
        if (t_i == 3'd3) begin
          trap_ret <= {rx_byte, t_dl[31:8]}; trap_ack <= 1'b1; trap_xong <= 1'b1; t_tt <= T_LENH;
        end else t_i <= t_i + 1;
      end
      default: t_tt <= T_LENH;
    endcase
  end

  // ── CỜ: mỗi cờ một chủ, đặt bởi bên này, xoá bởi bên kia ──
  always @(posedge clk) begin
    if (rst) begin trap_da_gui <= 0; doc_cho <= 0; dung_da_gui <= 0; end
    else begin
      if (mo_trap)       trap_da_gui <= 1'b1;
      else if (trap_xong) trap_da_gui <= 1'b0;
      if (xin_doc)       doc_cho <= 1'b1;
      else if (lay_doc)  doc_cho <= 1'b0;
      if (lay_dung)      dung_da_gui <= 1'b1;
    end
  end

  assign led = {halt, trap_valid, trap_da_gui, ~hang_trong, out_valid, p_tt};
endmodule

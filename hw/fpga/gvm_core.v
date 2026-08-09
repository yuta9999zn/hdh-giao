// ============================================================================
// ⚠⚠⚠ DI-SẢN (LEGACY) — core FPGA BẢN-ĐẦU, KHÔNG phải silicon CDFL hiện-tại ⚠⚠⚠
// ----------------------------------------------------------------------------
// Tệp này (Jun-2025) là core "bring-up" chạy LÕI QUYẾT-ĐỊNH tác-tử (nhan_ai_cdfl),
// đã MÔ-PHỎNG iverilog đúng ([65533,0]×6) — NHƯNG đã TỤT LẠI so với core chính ../gvm.v
// (503 dòng). Nó THIẾU: ba-trị silicon (ẩn/tối, stk_st/ST_SANG) · γ-scheduler biết-học
// (sigma/cred >>2) · SIP bảo-vệ-nhớ (mbase/mbound) · 4 nhân HĐH · con-trỏ 16-bit
// (ở đây sp/fp/rsp = 8-bit, địa-chỉ heap = [9:0] 10-bit). ⇒ SYNTH tệp này CHỈ ra CPU CŨ.
//   • Muốn nạp silicon CDFL ĐẦY-ĐỦ: dùng gvm_fpga.v (wrapper instantiate ../gvm.v THẬT) — ĐÃ LÀM.
//   • CẬP-NHẬT (2026-06-19): yosys/nextpnr ĐÃ cài & chạy trên gvm_fpga.v (KHÔNG phải tệp này) →
//     bitstream gvm_fpga.bin THẬT (3680 LC/69%, 14.04 MHz, nextpnr.log). Tệp DI-SẢN này KHÔNG được synth.
// ============================================================================
// gvm_core.v — GVM (máy trit/γ) MÔ TẢ PHẦN CỨNG cho FPGA (Verilog tổng hợp được)
// ----------------------------------------------------------------------------
// Khi nạp lên FPGA, GVM chạy bằng cổng logic thật, Python BIẾN MẤT khỏi tầng máy.
// Hạt mồi cuối cùng = một cổng NAND vật lý.
//
// Tầng (đúng tinh thần gvm.py — mọi thứ từ NAND):
//   NAND → NOT/AND/OR/XOR → full_adder → adderN (ALU rộng WORD-bit)
//   → CPU ngăn xếp + RAM + boot ROM, điều khiển bằng CLOCK (fetch→decode→execute)
//
// ĐỘ RỘNG TỪ là THAM SỐ: gvm #(.MEM(4096), .WORD(16/32/64/128/256)). Dữ liệu (ram/stack/
// thanh ghi/ALU) rộng WORD-bit; LỆNH luôn 16-bit [opcode:8][operand:8]; con trỏ sp/fp 8-bit.
// Boot ROM kiểm chứng: gọi hàm/heap/÷/so sánh/×/nhảy gián tiếp → [42,99,3,1,54,7].
// ============================================================================

// ===== TẦNG CỔNG: dựng mọi thứ từ DUY NHẤT cổng NAND =====
module nand2(input a, input b, output y); assign y = ~(a & b); endmodule
module inv1 (input a, output y);            nand2 g(a, a, y); endmodule
module and2 (input a, input b, output y);   wire n; nand2 g1(a,b,n); inv1 g2(n,y); endmodule
module or2  (input a, input b, output y);   wire na,nb; inv1 g1(a,na); inv1 g2(b,nb); nand2 g3(na,nb,y); endmodule
module xor2 (input a, input b, output y);
  wire n, an, bn;
  nand2 g1(a,b,n); nand2 g2(a,n,an); nand2 g3(b,n,bn); nand2 g4(an,bn,y);
endmodule

// full-adder từ cổng
module full_adder(input a, input b, input cin, output s, output cout);
  wire t, ab, tc;
  xor2 x1(a, b, t);  xor2 x2(t, cin, s);
  and2 a1(a, b, ab); and2 a2(t, cin, tc);
  or2  o1(ab, tc, cout);
endmodule

// cộng N-bit ripple-carry từ full_adder (TRỪ = a + ~b + 1). N là THAM SỐ.
module adderN #(parameter N = 16)
  (input [N-1:0] a, input [N-1:0] b, input cin, output [N-1:0] s, output cout);
  wire [N:0] c; assign c[0] = cin;
  genvar i;
  generate for (i = 0; i < N; i = i + 1) begin: fa
    full_adder f(a[i], b[i], c[i], s[i], c[i+1]);
  end endgenerate
  assign cout = c[N];
endmodule

// ===== CPU NGĂN XẾP GVM =====
// WORD = độ rộng DỮ LIỆU (16/32/64/128/256...). Lệnh luôn 16-bit [opcode:8][operand:8].
module gvm_core #(parameter ROM_DEPTH = 2048, parameter RAM_DEPTH = 1024, parameter WORD = 16) (
  input  clk,                     // mạch CLOCK điều khiển chu kỳ
  input  rst,                     // nạp lại (power-on reset)
  output reg [WORD-1:0] out_data, // cổng xuất (RỌI) — nối UART/đèn LED ngoài đời
  output reg            out_valid,// xung báo có dữ liệu xuất
  output reg            halt      // CPU đã DỪNG
);
  // --- opcode (khớp GVM phần mềm) ---
  localparam OP_DUNG=0, OP_NAP=1, OP_CONG=10, OP_TRU=11, OP_NHAN=12, OP_ROI=14,
             OP_NHAY=15, OP_NHAN_BAN=20, OP_BO=21, OP_DICH_TRAI=26,
             OP_NHAY_X=35, OP_NHAY_0_X=36,             // nhảy GIÁN TIẾP (địa chỉ từ ngăn xếp)
             OP_TAI_O=24, OP_LUU_O=25, OP_NHAY_0=28,
             OP_TAI_GIAN=29, OP_LUU_GIAN=30,           // heap: nạp/lưu gián tiếp
             OP_GOI_N=38, OP_THAM_I=39, OP_TRA_VE_N=40, // gọi hàm theo KHUNG
             OP_BANG=41, OP_KHAC=42, OP_BE_HON=43,      // so sánh → đẩy 1/0
             OP_LON_HON=44, OP_BE_BANG=45, OP_LON_BANG=46,
             OP_CHIA=47;                                // chia số nguyên có dấu

  // --- BỘ NHỚ ---  (rom/instr = LỆNH 16-bit; ram/stack/ip/out = DỮ LIỆU WORD-bit)
  reg [15:0]     rom   [0:ROM_DEPTH-1];   // boot ROM (lệnh 16-bit)
  reg [WORD-1:0] ram   [0:RAM_DEPTH-1];   // RAM dữ liệu
  reg [WORD-1:0] stack [0:255];   // ngăn xếp toán hạng
  reg [WORD-1:0] ip;                // con trỏ lệnh (nhận đích nhảy từ ngăn xếp)
  reg [7:0]      sp;                // con trỏ đỉnh ngăn xếp
  reg [7:0]      fp;                // con trỏ KHUNG (đáy tham số hàm hiện hành)
  reg [7:0]      rsp;              // con trỏ ngăn xếp trả về
  reg [WORD-1:0] rstk_ip [0:255]; // ngăn xếp địa chỉ trả về
  reg [7:0]      rstk_fp [0:255]; // ngăn xếp khung cũ (để khôi phục fp)
  reg [15:0]     instr;             // lệnh đang giải mã (16-bit)
  reg            state;             // FSM: 0=FETCH, 1=EXECUTE
  localparam S_FETCH=1'b0, S_EXEC=1'b1;

  wire [7:0] opcode  = instr[15:8];
  wire [7:0] operand = instr[7:0];

  // --- ALU dựng từ adderN (cổng NAND), rộng WORD ---
  wire            do_sub  = (opcode == OP_TRU);
  wire [WORD-1:0] alu_a   = stack[sp-2];
  wire [WORD-1:0] alu_braw= stack[sp-1];
  wire [WORD-1:0] alu_b   = do_sub ? ~alu_braw : alu_braw;   // trừ = a + ~b + 1
  wire [WORD-1:0] alu_y;  wire alu_co;
  adderN #(WORD) alu(alu_a, alu_b, do_sub, alu_y, alu_co);

  // --- boot ROM: GỌI HÀM (khung) + HEAP ---
  //   hàm nhân_đôi(x) = x + x  (addr 1);  main gọi nhân_đôi(21)=42 → RỌI;
  //   rồi heap: ram[50]=99 (LƯU_GIÁN), đọc lại (TẢI_GIÁN) → RỌI. Xuất [42, 99].
  initial $readmemh("program.hex", rom);

  // --- CHU KỲ CLOCK: fetch → execute ---
  always @(posedge clk or posedge rst) begin
    if (rst) begin
      ip <= 0; sp <= 0; fp <= 0; rsp <= 0; state <= S_FETCH; halt <= 0; out_valid <= 0; out_data <= 0;
    end else if (!halt) begin
      out_valid <= 0;
      if (state == S_FETCH) begin
        instr <= rom[ip]; ip <= ip + 1; state <= S_EXEC;
      end else begin
        state <= S_FETCH;
        case (opcode)
          OP_NAP:     begin stack[sp] <= { {(WORD-8){1'b0}}, operand }; sp <= sp + 8'd1; end
          OP_TAI_O:   begin stack[sp] <= ram[operand];    sp <= sp + 8'd1; end
          OP_LUU_O:   begin ram[operand] <= stack[sp-1];  sp <= sp - 8'd1; end
          OP_CONG:    begin stack[sp-2] <= alu_y;         sp <= sp - 8'd1; end  // do_sub=0
          OP_TRU:     begin stack[sp-2] <= alu_y;         sp <= sp - 8'd1; end  // do_sub=1
          // nhân (suy ra DSP/multiplier; lấy 16 bit thấp). Bản FPGA thật nên pipeline.
          OP_NHAN:    begin stack[sp-2] <= $signed(stack[sp-2]) * $signed(stack[sp-1]); sp <= sp - 8'd1; end
          // chia số nguyên có dấu, cắt-về-0 (b=0 → 0). NOTE: bản FPGA thật nên dùng
          // divider nhiều-chu-kỳ; ở đây để '/' suy ra mạch chia cho mô phỏng/kiểm chứng.
          OP_CHIA:    begin
            stack[sp-2] <= (stack[sp-1] == 0) ? 0
                            : ($signed(stack[sp-2]) / $signed(stack[sp-1]));
            sp <= sp - 8'd1;
          end
          // so sánh (pop b,a; đẩy 1/0). Thứ tự dùng có dấu.
          OP_BANG:    begin stack[sp-2] <= (stack[sp-2]==stack[sp-1]) ? 1:0; sp <= sp-8'd1; end
          OP_KHAC:    begin stack[sp-2] <= (stack[sp-2]!=stack[sp-1]) ? 1:0; sp <= sp-8'd1; end
          OP_BE_HON:  begin stack[sp-2] <= ($signed(stack[sp-2]) <  $signed(stack[sp-1])) ? 1:0; sp <= sp-8'd1; end
          OP_LON_HON: begin stack[sp-2] <= ($signed(stack[sp-2]) >  $signed(stack[sp-1])) ? 1:0; sp <= sp-8'd1; end
          OP_BE_BANG: begin stack[sp-2] <= ($signed(stack[sp-2]) <= $signed(stack[sp-1])) ? 1:0; sp <= sp-8'd1; end
          OP_LON_BANG:begin stack[sp-2] <= ($signed(stack[sp-2]) >= $signed(stack[sp-1])) ? 1:0; sp <= sp-8'd1; end
          OP_NHAN_BAN:begin stack[sp] <= stack[sp-1];     sp <= sp + 8'd1; end
          OP_BO:      begin                               sp <= sp - 8'd1; end
          OP_ROI:     begin out_data <= stack[sp-1]; out_valid <= 1; sp <= sp - 8'd1; end
          OP_NHAY:    begin ip <= { {(WORD-8){1'b0}}, operand }; end
          OP_NHAY_0:  begin if (stack[sp-1] == 0) ip <= { {(WORD-8){1'b0}}, operand }; sp <= sp - 8'd1; end
          OP_DICH_TRAI: begin stack[sp-1] <= stack[sp-1] << operand; end          // dịch trái (nạp hằng 16-bit)
          OP_NHAY_X:    begin ip <= stack[sp-1]; sp <= sp - 8'd1; end              // nhảy tới địa chỉ ở đỉnh
          OP_NHAY_0_X:  begin if (stack[sp-1] == 0) ip <= stack[sp-2];         // [target, cond]
                              sp <= sp - 8'd2; end
          // --- HEAP: nạp/lưu gián tiếp (địa chỉ 16-bit từ ngăn xếp) ---
          OP_TAI_GIAN:begin stack[sp-1] <= ram[stack[sp-1][9:0]]; end           // [addr]→[ram[addr]]
          OP_LUU_GIAN:begin ram[stack[sp-2][9:0]] <= stack[sp-1]; sp <= sp - 8'd2; end // [addr,val]→ram[addr]=val
          // --- GỌI HÀM theo KHUNG: tham số nằm trên ngăn xếp; fp trỏ đáy khung ---
          OP_GOI_N: begin                                   // [arg0..argN-1, target], operand=N
            rstk_ip[rsp] <= ip; rstk_fp[rsp] <= fp; rsp <= rsp + 8'd1;
            fp <= sp - 8'd1 - operand[7:0];                 // đáy khung = nơi arg0 bắt đầu
            ip <= stack[sp-1];                              // nhảy tới target
            sp <= sp - 8'd1;                                // chỉ bỏ target; tham số ở lại làm khung
          end
          OP_THAM_I:  begin stack[sp] <= stack[fp + operand[7:0]]; sp <= sp + 8'd1; end  // đọc tham số thứ i
          OP_TRA_VE_N: begin                                // trị trả về ở đỉnh; gấp khung
            stack[fp] <= stack[sp-1];                       // đặt kết quả tại đáy khung
            sp  <= fp + 8'd1;                               // bỏ toàn khung, chừa kết quả
            ip  <= rstk_ip[rsp-1];                          // khôi phục ip & fp người gọi
            fp  <= rstk_fp[rsp-1];
            rsp <= rsp - 8'd1;
          end
          OP_DUNG:    begin halt <= 1; end
          default:    begin halt <= 1; end  // lệnh lạ → dừng an toàn
        endcase
      end
    end
  end
endmodule

// ============================================================================
// gvm.v — GVM (máy trit/γ) MÔ TẢ PHẦN CỨNG cho FPGA (Verilog tổng hợp được)
// ----------------------------------------------------------------------------
// Đây là cây cầu xuống SILICON: khi nạp lên FPGA, GVM chạy bằng cổng logic thật,
// Python BIẾN MẤT khỏi tầng máy. Hạt mồi cuối cùng = một cổng NAND vật lý.
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
module gvm #(parameter MEM = 4096, parameter WORD = 16) (
  input  clk,                     // mạch CLOCK điều khiển chu kỳ
  input  rst,                     // nạp lại (power-on reset)
  output reg [WORD-1:0] out_data, // cổng xuất (RỌI) — nối UART/đèn LED ngoài đời
  output reg            out_valid,// xung báo có dữ liệu xuất
  output reg [2:0]      out_kind, // 0=SỐ · 1=KÝ-TỰ · 2=HẾT-CHUỖI · 3=SỐ-THỰC(×10000) · 4=PHẦN-TỬ-DS · 5=HẾT-DS
  output reg [7:0]      out_proc, // tiến trình phát (cur) — cho XUẤT/nhãn console; vô hại nếu không nối
  output reg [1:0]      out_state,// TRẠNG-THÁI ba-trị ô khi RỌI: 0=ẩn · 1=sáng · 2=tối (cộng hưởng γ)
  output reg            sched_evt,// ★ xung 1 chu kỳ khi γ-scheduler CHUYỂN NGỮ CẢNH (để đối chiếu chính sách)
  output reg [7:0]      sched_cur,// tiến trình VỪA CHẠY (outgoing) tại lần chuyển
  output reg            sched_rho,// ρ của outgoing (did_out: có XUẤT trong lượng tử?)
  output reg            halt      // CPU đã DỪNG
);
  // --- opcode (khớp GVM phần mềm) ---
  localparam OP_DUNG=0, OP_NAP=1, OP_CONG=10, OP_TRU=11, OP_NHAN=12, OP_ROI=14,
             OP_NHAY=15, OP_NHAN_BAN=20, OP_BO=21, OP_DOI=22, OP_DICH_TRAI=26,
             OP_ROI_CHUOI=34, OP_ROI_AUTO=65, OP_GOI_CLOSURE=58,  // in chuỗi · in tự-suy-kiểu · gọi closure
             OP_DANH_CB=66, OP_LUU_THAM_I=67,           // dành ô cục bộ · ghi ô khung (biến cục bộ per-call)
             OP_NHAY_X=35, OP_NHAY_0_X=36,             // nhảy GIÁN TIẾP (địa chỉ từ ngăn xếp)
             OP_TAI_O=24, OP_LUU_O=25, OP_NHAY_0=28,
             OP_TAI_GIAN=29, OP_LUU_GIAN=30,           // heap: nạp/lưu gián tiếp
             OP_GOI_N=38, OP_THAM_I=39, OP_TRA_VE_N=40, // gọi hàm theo KHUNG
             OP_BANG=41, OP_KHAC=42, OP_BE_HON=43,      // so sánh → đẩy 1/0
             OP_LON_HON=44, OP_BE_BANG=45, OP_LON_BANG=46,
             OP_CHIA=47,                                // chia số nguyên có dấu
             OP_BAT_NGAT=50, OP_TAT_NGAT=51,            // NGẮT TIMER: bật/tắt
             OP_HEN_GIO=52, OP_NGAT_VE=53,              // đặt chu kỳ / IRET (quay về)
             OP_TAC_VU=54, OP_LAP_LICH=55,              // đăng ký tiến trình / khởi động đa nhiệm tiền-định
             OP_LICH_HOC=56,                            // khởi động LẬP LỊCH CDFL BIẾT-HỌC (theo γ)
             OP_BAT_SIP=57,                             // bật CÔ LẬP tiến trình (base+bound, không MMU)
             OP_ROI_DS=48, OP_FNHAN=59, OP_FCHIA=60,    // in danh-sách số (PEEK) · số thực ×(a·b)/10000 · ÷(a·10000)/b
             OP_ROI_THUC=61, OP_NEM=64,                 // in số thực (harness định dạng) · NÉM (gỡ-cuộn về handler; rỗng → DỪNG)
             OP_AN=2, OP_XUAT=49,                       // ẨN: đẩy ô ẩn (DE/chưa-biết) · XUẤT: MMIO console (kèm nhãn tiến trình)
             OP_BAT_DAU_THU=62, OP_HET_THU=63,          // thử/bắt: mở vùng thử (đẩy handler) · đóng vùng thử (gỡ handler)
             OP_SO_SANH=13,                             // CỘNG HƯỞNG: γ(niềm-tin,thực-tại) → sáng/tối/ẩn (ba-trị tác-tử)
             OP_NHAY_SANG=16, OP_NHAY_TOI=17, OP_NHAY_AN=18;  // rẽ theo TRẠNG-THÁI (thay cờ ZF/CF): khớp/ảo-tưởng/chưa-soi

  // --- BỘ NHỚ ---  (rom/instr = LỆNH 16-bit; ram/stack/ip/out = DỮ LIỆU WORD-bit)
  reg [15:0]     rom   [0:MEM-1];   // boot ROM (lệnh 16-bit)
  reg [WORD-1:0] ram   [0:MEM-1];   // RAM dữ liệu
  reg [WORD-1:0] stack [0:MEM-1];   // ngăn xếp toán hạng
  reg [WORD-1:0] ip;                // con trỏ lệnh (nhận đích nhảy từ ngăn xếp)
  // con trỏ ngăn xếp 16-BIT (nhân hợp-tác hdh.giao gộp toán-hạng+khung → đỉnh có thể >255)
  reg [15:0]     sp;                // con trỏ đỉnh ngăn xếp
  reg [15:0]     fp;                // con trỏ KHUNG (đáy tham số hàm hiện hành)
  reg [15:0]     rsp;              // con trỏ ngăn xếp trả về
  reg [WORD-1:0] rstk_ip [0:MEM-1]; // ngăn xếp địa chỉ trả về
  reg [15:0]     rstk_fp [0:MEM-1]; // ngăn xếp khung cũ (để khôi phục fp)
  reg [15:0]     instr;             // lệnh đang giải mã (16-bit)
  reg [2:0]      state;             // FSM: FETCH/EXEC + ĐA-CHU-KỲ cho chuỗi/closure/danh-sách
  localparam S_FETCH=3'd0, S_EXEC=3'd1, S_STR=3'd2, S_CLO=3'd3, S_DS=3'd4;
  reg [WORD-1:0] str_a;             // RỌI_CHUỖI: địa chỉ ô đang duyệt (heap char-list)
  reg [WORD-1:0] ds_a;              // RỌI_DS: địa chỉ cons-cell đang duyệt (in danh-sách số, PEEK)
  // --- Ô NGĂN XẾP MANG TRẠNG-THÁI BA-TRỊ (CDFL): mảng cờ SONG SONG với stack[] ---
  //   ẩn(DE/chưa-biết)=00 · sáng(đã-biết,+)=01 · tối(đã-biết,−)=10. RAM/heap KHÔNG mang trạng-thái
  //   (LƯU_*/TẢI_* chỉ chuyển val → tải lại = sáng), đúng khít GVM phần mềm. Chỉ NGĂN XẾP cần cờ.
  localparam [1:0] ST_AN=2'b00, ST_SANG=2'b01, ST_TOI=2'b10;
  reg [1:0] stk_st [0:MEM-1];       // trạng-thái mỗi ô ngăn xếp toán hạng
  // --- NGĂN XẾP HANDLER (thử/bắt): điểm 'bắt' + sâu các ngăn xếp lúc vào 'thử' → GỠ-CUỘN khi NÉM ---
  reg [WORD-1:0] h_ip  [0:31];      // địa chỉ nhánh 'bắt'
  reg [15:0]     h_sp  [0:31], h_fp [0:31], h_rsp [0:31];  // sp/fp/rsp lúc mở 'thử' (để khôi phục)
  reg [15:0]     hsp;               // con trỏ ngăn xếp handler (= hbase của task → không có vùng thử)
  // 'ẩn LAN TRUYỀN': nhị-nguyên chạm ẩn → ẩn (tiên đề DE ở tầng máy)
  wire bin_an = (stk_st[sp-1] == ST_AN) || (stk_st[sp-2] == ST_AN);
  // GỌI_CLOSURE: chép 'bắt' từ heap + dịch 'đối' để dựng khung [bắt…, đối…]
  reg [WORD-1:0] clo_code;          // địa chỉ mã closure
  reg [7:0]      clo_ncap, clo_n, clo_k;  // số-bắt · số-đối · bộ đếm (đều ≤ operand 8-bit)
  reg [15:0]     clo_base;                // đáy khung closure (chỉ-mục ngăn xếp 16-bit)
  reg [WORD-1:0] clo_cp;            // địa chỉ khối closure (đã gỡ thẻ)
  localparam [WORD-1:0] UNTAG = 32'h3FFFFFFF;   // mặt nạ gỡ thẻ: giữ 30 bit thấp (WORD<30 ⇒ toàn 1 = không thẻ)
  // --- NGẮT TIMER PHẦN CỨNG (preemption ở silicon) ---
  reg            ie;                // cho phép ngắt (interrupt enable)
  reg            in_isr;            // đang trong trình phục vụ ngắt (chặn lồng)
  reg [WORD-1:0] ivec;              // địa chỉ handler (interrupt vector)
  reg [WORD-1:0] saved_ip;          // ip bị ngắt (để IRET quay về)
  reg [WORD-1:0] timer;             // bộ đếm chu kỳ clock
  reg [WORD-1:0] period;            // chu kỳ ngắt (0 = tắt)
  // --- ĐA NHIỆM TIỀN-ĐỊNH ở silicon: NGÂN HÀNG THANH GHI mỗi tiến trình ---
  localparam NT = 4;                // số tiến trình tối đa
  reg [WORD-1:0] t_ip  [0:NT-1];    // ip mỗi tiến trình
  reg [15:0]     t_sp  [0:NT-1];    // sp (ngăn xếp mỗi task ở vùng riêng → switch = hoán con trỏ)
  reg [15:0]     t_fp  [0:NT-1];
  reg [15:0]     t_rsp [0:NT-1];
  reg [15:0]     t_hsp [0:NT-1];    // con trỏ NGĂN-XẾP-HANDLER mỗi task (try/bắt RIÊNG → cô lập)
  reg            t_dead[0:NT-1];    // task BỊ CÔ LẬP (NÉM chưa-bắt) → scheduler bỏ qua, hệ chạy tiếp
  reg [7:0]      cur;               // tiến trình hiện hành
  reg [7:0]      ntask;             // số tiến trình đã đăng ký
  reg            sched_on;          // bật lập lịch tiền-định theo timer
  reg            sched_mode;        // 0=round-robin · 1=CDFL biết-học (theo γ)
  integer        ri;                // biến vòng for khởi tạo σ/cred
  wire [7:0]     nxt = (cur + 8'd1 >= ntask) ? 8'd0 : cur + 8'd1;   // round-robin
  // --- LẬP LỊCH CDFL BIẾT-HỌC: σ (niềm tin độ-hữu-ích) + credit (∝ cộng hưởng) + did_out ---
  reg [15:0] sigma [0:NT-1];        // σ học được, 0..255 (≈0..1)
  reg [15:0] cred  [0:NT-1];        // tín nhiệm tích luỹ (∝ σ) → chọn task chạy
  reg        did_out [0:NT-1];      // task có XUẤT/RỌI trong lượng tử? (ρ)
  localparam [15:0] COST = 16'd128; // chi phí một lượt chạy
  // học outgoing 'cur': σ ← σ + (ρ − σ)>>2   (động học tiên đề 5, α=1/4, dịch bit)
  wire [15:0] rho_cur = did_out[cur] ? 16'd255 : 16'd0;
  wire signed [16:0] diff = $signed({1'b0,rho_cur}) - $signed({1'b0,sigma[cur]});
  wire signed [17:0] sn = $signed({2'b0,sigma[cur]}) + (diff >>> 2);   // σ + (ρ−σ)>>2, cộng CÓ DẤU
  wire [15:0] sigma_new = (sn[17]) ? 16'd0 : (sn > 18'sd255 ? 16'd255 : sn[15:0]);  // clamp 0..255
  // credit: cộng dồn σ>>2 mỗi lượt; outgoing trả COST (bão hoà 0) → chọn MAX
  wire [15:0] a0 = cred[0] + (sigma[0]>>2);  wire [15:0] a1 = cred[1] + (sigma[1]>>2);
  wire [15:0] a2 = cred[2] + (sigma[2]>>2);  wire [15:0] a3 = cred[3] + (sigma[3]>>2);
  wire [15:0] p0 = (cur==0) ? COST:0; wire [15:0] p1 = (cur==1) ? COST:0;
  wire [15:0] p2 = (cur==2) ? COST:0; wire [15:0] p3 = (cur==3) ? COST:0;
  wire [15:0] nc0 = (a0>p0)?a0-p0:0; wire [15:0] nc1 = (a1>p1)?a1-p1:0;
  wire [15:0] nc2 = (a2>p2)?a2-p2:0; wire [15:0] nc3 = (a3>p3)?a3-p3:0;
  // argmax credit (chỉ trong số task đã đăng ký) → tiến trình chạy kế
  wire [15:0] e1 = (ntask>1)?nc1:16'd0, e2=(ntask>2)?nc2:16'd0, e3=(ntask>3)?nc3:16'd0;
  wire [15:0] m01=(nc0>=e1)?nc0:e1;  wire [7:0] i01=(nc0>=e1)?8'd0:8'd1;
  wire [15:0] m23=(e2>=e3)?e2:e3;    wire [7:0] i23=(e2>=e3)?8'd2:8'd3;
  wire [7:0]  gsel=(m01>=m23)?i01:i23;
  // --- CÔ LẬP FAULT: chọn argmax BỎ QUA task chết. credit hiệu dụng = sống?(nc+1):0 (luôn > chết=0)
  //   ⇒ khi KHÔNG có task chết, gsel_live ≡ gsel (cộng 1 giữ nguyên thứ tự). ---
  wire lv0=(ntask>0)&&!t_dead[0], lv1=(ntask>1)&&!t_dead[1], lv2=(ntask>2)&&!t_dead[2], lv3=(ntask>3)&&!t_dead[3];
  wire [16:0] lc0=lv0?(nc0+17'd1):0, lc1=lv1?(nc1+17'd1):0, lc2=lv2?(nc2+17'd1):0, lc3=lv3?(nc3+17'd1):0;
  wire [16:0] lm01=(lc0>=lc1)?lc0:lc1; wire [7:0] li01=(lc0>=lc1)?8'd0:8'd1;
  wire [16:0] lm23=(lc2>=lc3)?lc2:lc3; wire [7:0] li23=(lc2>=lc3)?8'd2:8'd3;
  wire [7:0]  gsel_live=(lm01>=lm23)?li01:li23;
  wire        any_live = lv0||lv1||lv2||lv3;
  // chọn khi FAULT: loại luôn 'cur' (đang bị giết) khỏi ứng viên
  wire fl0=lv0&&(cur!=0), fl1=lv1&&(cur!=1), fl2=lv2&&(cur!=2), fl3=lv3&&(cur!=3);
  wire [16:0] fc0=fl0?(nc0+17'd1):0, fc1=fl1?(nc1+17'd1):0, fc2=fl2?(nc2+17'd1):0, fc3=fl3?(nc3+17'd1):0;
  wire [16:0] fm01=(fc0>=fc1)?fc0:fc1; wire [7:0] fi01=(fc0>=fc1)?8'd0:8'd1;
  wire [16:0] fm23=(fc2>=fc3)?fc2:fc3; wire [7:0] fi23=(fc2>=fc3)?8'd2:8'd3;
  wire [7:0]  gsel_fault=(fm01>=fm23)?fi01:fi23;
  wire        any_other_live = fl0||fl1||fl2||fl3;   // còn task sống KHÁC 'cur'?
  wire [15:0] hbase = sched_on ? {cur, 3'b0} : 16'd0; // đáy ngăn-xếp-handler của task cur (cur*8)
  // --- SIP: CÔ LẬP tiến trình bằng BASE+BOUND (không MMU) ---
  reg [15:0] mbase  [0:NT-1];         // gốc vùng nhớ mỗi task (địa chỉ ảo → vật lý)
  reg [15:0] mbound [0:NT-1];         // kích thước vùng (địa chỉ ảo phải < mbound)
  reg        sip_on;                  // bật cô lập
  // ĐỊA CHỈ VẬT LÝ 16-BIT: heap thật tới ~MEM (16384) — KHÔNG được cắt 12-bit (lỗi cũ: heap≥4096 wrap).
  //   SIP (vùng 128) vẫn đúng vì địa-chỉ-ảo nhỏ; non-SIP nay dùng TRỌN địa chỉ từ ngăn xếp.
  wire [15:0] rel_o  = sip_on ? (mbase[cur] + {8'b0, operand})          : {8'b0, operand};   // TẢI_Ô/LƯU_Ô (operand 8-bit)
  wire [15:0] rel_s1 = sip_on ? (mbase[cur] + stack[sp-1][15:0])        : stack[sp-1][15:0]; // TẢI_GIÁN (heap)
  wire [15:0] rel_s2 = sip_on ? (mbase[cur] + stack[sp-2][15:0])        : stack[sp-2][15:0]; // LƯU_GIÁN (heap)
  wire viol_o  = sip_on && (operand           >= mbound[cur]);          // vượt biên → FAULT
  wire viol_s1 = sip_on && (stack[sp-1][11:0] >= mbound[cur]);
  wire viol_s2 = sip_on && (stack[sp-2][11:0] >= mbound[cur]);

  wire [7:0] opcode  = instr[15:8];
  wire [7:0] operand = instr[7:0];

  // --- ALU dựng từ adderN (cổng NAND), rộng WORD ---
  wire            do_sub  = (opcode == OP_TRU);
  wire [WORD-1:0] alu_a   = stack[sp-2];
  wire [WORD-1:0] alu_braw= stack[sp-1];
  wire [WORD-1:0] alu_b   = do_sub ? ~alu_braw : alu_braw;   // trừ = a + ~b + 1
  wire [WORD-1:0] alu_y;  wire alu_co;
  adderN #(WORD) alu(alu_a, alu_b, do_sub, alu_y, alu_co);

  // --- SỐ THỰC điểm-cố-định ×10000: trung gian 64-bit CÓ DẤU (suy ra DSP), '/' Verilog cắt-về-0 ---
  //   FNHÂN = (a·b)/10000 · FCHIA = (a·10000)/b (b=0 → 0). Trùng khít fbin() phần mềm / i64 wasm.
  wire signed [63:0] f_a64 = {{(64-WORD){stack[sp-2][WORD-1]}}, stack[sp-2]};   // sign-extend a → 64-bit
  wire signed [63:0] f_b64 = {{(64-WORD){stack[sp-1][WORD-1]}}, stack[sp-1]};   // sign-extend b → 64-bit
  wire signed [63:0] fmul_q = (f_a64 * f_b64) / 64'sd10000;                     // (a·b)/10000, trunc-về-0
  wire signed [63:0] fdiv_q = (stack[sp-1] == 0) ? 64'sd0 : (f_a64 * 64'sd10000) / f_b64;  // (a·10000)/b
  wire fdiv_an = (stk_st[sp-1] == ST_AN) || (stk_st[sp-2] == ST_AN) || (stack[sp-1] == 0);  // chia 0 → ẩn
  // CHIA/NHÂN có-dấu TÍNH RIÊNG ở wire signed (self-determined) — KHÔNG để ternary unsigned ép
  //   thành chia-unsigned (lỗi: −200/2 ra 0x7FFFFF9C thay −100; chỉ lộ với SỐ ÂM).
  wire signed [WORD-1:0] chia_q = (stack[sp-1] == 0) ? 0 : ($signed(stack[sp-2]) / $signed(stack[sp-1]));
  wire signed [WORD-1:0] nhan_p = $signed(stack[sp-2]) * $signed(stack[sp-1]);

  // --- CỘNG HƯỞNG γ (SO_SÁNH): a=niềm-tin (stack[sp-2]), b=thực-tại (stack[sp-1]).
  //   γ = 1 − 2·|b−a|/max(|b|,1) ⇒ STATE chỉ cần SO INTEGER (khỏi chia): 2d<scale→sáng · >→tối · =→ẩn.
  //   (val unsigned khớp gvm_may.resonance; |b|=b vì val ≥ 0). Hoặc input ẩn → ẩn.
  wire [WORD-1:0] so_a = stack[sp-2], so_b = stack[sp-1];
  wire [WORD-1:0] so_dabs = (so_b >= so_a) ? (so_b - so_a) : (so_a - so_b);   // |b−a|
  wire [WORD-1:0] so_scale = (so_b == 0) ? {{(WORD-1){1'b0}},1'b1} : so_b;    // max(|b|,1)
  wire [WORD+1:0] so_2d = {2'b00, so_dabs} << 1;                              // 2·d (đủ rộng, không tràn)
  wire [WORD+1:0] so_scale_e = {2'b00, so_scale};
  wire so_an_in = (stk_st[sp-1] == ST_AN) || (stk_st[sp-2] == ST_AN);
  wire [1:0] so_st = so_an_in ? ST_AN
                   : (so_2d <  so_scale_e) ? ST_SANG
                   : (so_2d >  so_scale_e) ? ST_TOI : ST_AN;

  // --- boot ROM: GỌI HÀM (khung) + HEAP ---
  //   hàm nhân_đôi(x) = x + x  (addr 1);  main gọi nhân_đôi(21)=42 → RỌI;
  //   rồi heap: ram[50]=99 (LƯU_GIÁN), đọc lại (TẢI_GIÁN) → RỌI. Xuất [42, 99].
  initial $readmemh("prog_d.hex",rom);

  // --- CHU KỲ CLOCK: fetch → execute ---
  always @(posedge clk or posedge rst) begin
    if (rst) begin
      ip <= 0; sp <= 0; fp <= 0; rsp <= 0; state <= S_FETCH; halt <= 0; out_valid <= 0; out_data <= 0; out_kind <= 0; out_proc <= 0;
      sched_evt <= 0; sched_cur <= 0; sched_rho <= 0; hsp <= 0; out_state <= 0;
      ie <= 0; in_isr <= 0; ivec <= 0; saved_ip <= 0; timer <= 0; period <= 0;   // ngắt tắt lúc reset
      cur <= 0; ntask <= 0; sched_on <= 0; sched_mode <= 0; sip_on <= 0;          // đa nhiệm/SIP tắt lúc reset
      for (ri = 0; ri < NT; ri = ri + 1) begin sigma[ri] <= 16'd128; cred[ri] <= 0; did_out[ri] <= 0; t_dead[ri] <= 0; t_hsp[ri] <= 0; end
    end else if (!halt) begin
      out_valid <= 0; sched_evt <= 0;
      timer <= timer + 1;                          // ĐỒNG HỒ phần cứng chạy mỗi chu kỳ clock
      if (state == S_FETCH) begin
        if (sched_on && period != 0 && timer >= period) begin
          // ★★ CONTEXT-SWITCH PHẦN CỨNG: lưu ngân hàng task hiện hành (kèm ngăn-xếp-handler)
          t_ip[cur] <= ip; t_sp[cur] <= sp; t_fp[cur] <= fp; t_rsp[cur] <= rsp; t_hsp[cur] <= hsp;
          timer <= 0;
          if (sched_mode) begin
            // ★★★ LẬP LỊCH CDFL: HỌC σ (tiến trình outgoing) + cập nhật credit + chọn argmax (BỎ QUA task chết)
            sigma[cur] <= sigma_new; did_out[cur] <= 1'b0;
            cred[0] <= nc0; cred[1] <= nc1; cred[2] <= nc2; cred[3] <= nc3;
            sched_evt <= 1'b1; sched_cur <= cur; sched_rho <= did_out[cur];  // ★ phơi quyết-định lập-lịch
            if (!any_live) halt <= 1'b1;                                     // mọi task chết → DỪNG
            else begin
              cur <= gsel_live;
              ip <= t_ip[gsel_live]; sp <= t_sp[gsel_live]; fp <= t_fp[gsel_live]; rsp <= t_rsp[gsel_live]; hsp <= t_hsp[gsel_live];
            end
          end else begin
            // round-robin (giữ nguyên — bỏ qua chết chưa cần cho RR)
            cur <= nxt;
            ip <= t_ip[nxt]; sp <= t_sp[nxt]; fp <= t_fp[nxt]; rsp <= t_rsp[nxt]; hsp <= t_hsp[nxt];
          end
        end else if (ie && !in_isr && period != 0 && timer >= period) begin
          // ★ NGẮT TIMER kiểu handler (giữ tương thích): lưu ip, nhảy handler
          saved_ip <= ip; ip <= ivec; in_isr <= 1'b1; timer <= 0;
        end else begin
          instr <= rom[ip]; ip <= ip + 1; state <= S_EXEC;
        end
      end else if (state == S_EXEC) begin
        state <= S_FETCH;
        case (opcode)
          OP_NAP:     begin stack[sp] <= { {(WORD-8){1'b0}}, operand }; stk_st[sp] <= ST_SANG; sp <= sp + 8'd1; end
          OP_AN:      begin stack[sp] <= 0; stk_st[sp] <= ST_AN; sp <= sp + 8'd1; end   // đẩy ô ẩn (DE/chưa-biết)
          OP_TAI_O:   begin if (viol_o) begin out_data<=16'd911; out_valid<=1; halt<=1; end  // ★ SIP fault
                            else begin stack[sp] <= ram[rel_o]; stk_st[sp] <= ST_SANG; sp <= sp + 8'd1; end end  // tải RAM = sáng
          OP_LUU_O:   begin if (viol_o) begin out_data<=16'd911; out_valid<=1; halt<=1; end
                            else begin ram[rel_o] <= stack[sp-1]; sp <= sp - 8'd1; end end
          //   số học LAN TRUYỀN ẩn: chạm ẩn → kết quả ẩn (val=0, ≡ ANCELL phần mềm), ngược lại sáng.
          OP_CONG:    begin stack[sp-2] <= bin_an ? {WORD{1'b0}} : alu_y; stk_st[sp-2] <= bin_an ? ST_AN : ST_SANG; sp <= sp - 8'd1; end  // do_sub=0
          OP_TRU:     begin stack[sp-2] <= bin_an ? {WORD{1'b0}} : alu_y; stk_st[sp-2] <= bin_an ? ST_AN : ST_SANG; sp <= sp - 8'd1; end  // do_sub=1
          // nhân (suy ra DSP/multiplier; lấy 16 bit thấp). Bản FPGA thật nên pipeline.
          OP_NHAN:    begin stack[sp-2] <= bin_an ? {WORD{1'b0}} : nhan_p; stk_st[sp-2] <= bin_an ? ST_AN : ST_SANG; sp <= sp - 8'd1; end
          // chia số nguyên có dấu, cắt-về-0 (b=0 → 0). NOTE: bản FPGA thật nên dùng
          // divider nhiều-chu-kỳ; ở đây để '/' suy ra mạch chia cho mô phỏng/kiểm chứng.
          OP_CHIA:    begin
            stack[sp-2] <= bin_an ? {WORD{1'b0}} : chia_q;   // chia CÓ DẤU (wire signed, đúng cả số âm)
            stk_st[sp-2] <= bin_an ? ST_AN : ST_SANG;
            sp <= sp - 8'd1;
          end
          // --- SỐ THỰC điểm-cố-định ×10000 (DSP 64-bit, cắt-về-0) ---
          OP_FNHAN:   begin stack[sp-2] <= bin_an  ? {WORD{1'b0}} : fmul_q[WORD-1:0]; stk_st[sp-2] <= bin_an  ? ST_AN : ST_SANG; sp <= sp - 8'd1; end
          OP_FCHIA:   begin stack[sp-2] <= fdiv_an ? {WORD{1'b0}} : fdiv_q[WORD-1:0]; stk_st[sp-2] <= fdiv_an ? ST_AN : ST_SANG; sp <= sp - 8'd1; end  // chia 0 → ẩn
          // in số thực: ẩn → out_kind=6 (dấu ẩn); ngược lại phát trị ×10000 thô + out_kind=3 → định dạng thập phân
          OP_ROI_THUC:begin out_data <= stack[sp-1]; out_valid <= 1; out_kind <= (stk_st[sp-1]==ST_AN) ? 3'd6 : 3'd3; sp <= sp - 8'd1; did_out[cur] <= 1'b1; end
          // in DANH-SÁCH số: PEEK (KHÔNG pop con trỏ) → duyệt heap đa-chu-kỳ ở S_DS
          OP_ROI_DS:  begin ds_a <= stack[sp-1] & UNTAG; state <= S_DS; end
          // CỘNG HƯỞNG: pop thực-tại b, đặt ô = (val niềm-tin a, TRẠNG-THÁI sáng/tối/ẩn theo γ)
          OP_SO_SANH: begin stack[sp-2] <= so_an_in ? {WORD{1'b0}} : stack[sp-2]; stk_st[sp-2] <= so_st; sp <= sp - 8'd1; end
          // --- THỬ/BẮT (ngoại lệ) ---
          OP_BAT_DAU_THU: begin                            // mở vùng thử: pop địa chỉ 'bắt', lưu sâu các ngăn xếp
            h_ip[hsp] <= stack[sp-1]; h_sp[hsp] <= sp - 8'd1; h_fp[hsp] <= fp; h_rsp[hsp] <= rsp;
            hsp <= hsp + 8'd1; sp <= sp - 8'd1;
          end
          OP_HET_THU: begin hsp <= hsp - 8'd1; end          // thử xong êm → gỡ handler trên cùng
          // NÉM: pop trị-lỗi → GỠ-CUỘN về handler gần nhất (của TASK NÀY: hsp > hbase).
          //   Rỗng handler (hsp==hbase): dưới scheduler → CÔ LẬP task (giết, chuyển task sống, hệ chạy tiếp);
          //   ngoài scheduler → DỪNG (≡ fault phần mềm rỗng handler).
          OP_NEM: begin
            if (hsp == hbase) begin
              if (sched_on) begin                            // ★ CÔ LẬP FAULT phần cứng: giết task, hệ KHÔNG sập
                t_dead[cur] <= 1'b1;
                sigma[cur] <= sigma_new; did_out[cur] <= 1'b0;   // vẫn HỌC σ tiến trình outgoing
                cred[0] <= nc0; cred[1] <= nc1; cred[2] <= nc2; cred[3] <= nc3;
                sched_evt <= 1'b1; sched_cur <= cur; sched_rho <= did_out[cur];
                timer <= 0;
                if (any_other_live) begin                    // chuyển sang task SỐNG khác cur
                  cur <= gsel_fault;
                  ip <= t_ip[gsel_fault]; sp <= t_sp[gsel_fault]; fp <= t_fp[gsel_fault];
                  rsp <= t_rsp[gsel_fault]; hsp <= t_hsp[gsel_fault];
                end else halt <= 1'b1;                        // mọi task chết → DỪNG
              end else begin out_data <= stack[sp-1]; out_valid <= 1; out_kind <= 3'd0; halt <= 1; end
            end else begin
              sp  <= h_sp[hsp-16'd1] + 16'd1;                // gỡ-cuộn độ sâu + chừa 1 ô trị-lỗi
              fp  <= h_fp[hsp-16'd1];
              rsp <= h_rsp[hsp-16'd1];
              stack[h_sp[hsp-16'd1]]  <= stack[sp-1];        // trao trị-lỗi cho nhánh 'bắt'
              stk_st[h_sp[hsp-16'd1]] <= ST_SANG;
              ip  <= h_ip[hsp-16'd1];
              hsp <= hsp - 16'd1;
            end
          end
          // so sánh (pop b,a; đẩy 1/0). Đọc val bỏ trạng-thái → kết quả LUÔN sáng (≡ phần mềm).
          OP_BANG:    begin stack[sp-2] <= (stack[sp-2]==stack[sp-1]) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_KHAC:    begin stack[sp-2] <= (stack[sp-2]!=stack[sp-1]) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_BE_HON:  begin stack[sp-2] <= ($signed(stack[sp-2]) <  $signed(stack[sp-1])) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_LON_HON: begin stack[sp-2] <= ($signed(stack[sp-2]) >  $signed(stack[sp-1])) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_BE_BANG: begin stack[sp-2] <= ($signed(stack[sp-2]) <= $signed(stack[sp-1])) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_LON_BANG:begin stack[sp-2] <= ($signed(stack[sp-2]) >= $signed(stack[sp-1])) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_NHAN_BAN:begin stack[sp] <= stack[sp-1]; stk_st[sp] <= stk_st[sp-1]; sp <= sp + 8'd1; end  // nhân bản kèm trạng-thái
          OP_BO:      begin                               sp <= sp - 8'd1; end
          // in: ẩn → out_kind=6 (dấu ẩn); ngược lại số out_kind=0
          OP_ROI:     begin out_data <= stack[sp-1]; out_valid <= 1; out_kind <= (stk_st[sp-1]==ST_AN) ? 3'd6 : 3'd0; out_state <= stk_st[sp-1]; sp <= sp - 8'd1; did_out[cur] <= 1'b1; end
          OP_DOI:     begin stack[sp-1] <= stack[sp-2]; stack[sp-2] <= stack[sp-1];
                            stk_st[sp-1] <= stk_st[sp-2]; stk_st[sp-2] <= stk_st[sp-1]; end   // hoán đỉnh ↔ kế-đỉnh (kèm trạng-thái)
          OP_XUAT:    begin out_data <= stack[sp-1]; out_valid <= 1; out_kind <= 3'd7; out_proc <= cur; sp <= sp - 8'd1; did_out[cur] <= 1'b1; end  // MMIO console (nhãn=cur)
          OP_ROI_CHUOI: begin str_a <= stack[sp-1] & UNTAG; sp <= sp - 8'd1; state <= S_STR; end  // duyệt heap, in từng ký tự
          OP_ROI_AUTO: begin                               // in TỰ-SUY-KIỂU lúc chạy
            if (stk_st[sp-1] == ST_AN) begin               // ẩn → dấu ẩn (out_kind=6)
              out_data <= stack[sp-1]; out_valid <= 1; out_kind <= 3'd6; sp <= sp - 8'd1; did_out[cur] <= 1'b1;
            end else if ((stack[sp-1] & 32'hC0000000) == 32'h40000000) begin   // con trỏ chuỗi (bit30=1,bit31=0)
              str_a <= stack[sp-1] & UNTAG; sp <= sp - 8'd1; state <= S_STR;
            end else begin                                 // số (kể cả 16-bit: luôn nhánh này)
              out_data <= stack[sp-1]; out_valid <= 1; out_kind <= 3'd0; sp <= sp - 8'd1; did_out[cur] <= 1'b1;
            end
          end
          OP_GOI_CLOSURE: begin                            // [đối0..đốiN-1, con-trỏ-closure], operand=N
            clo_cp   <= stack[sp-1] & UNTAG;               // gỡ thẻ
            clo_code <= ram[stack[sp-1] & UNTAG];          // ram[cp]   = địa chỉ mã
            clo_ncap <= ram[(stack[sp-1] & UNTAG) + 1];    // ram[cp+1] = số biến bắt
            clo_n    <= operand[7:0];
            clo_base <= sp - 8'd1 - operand[7:0];          // đáy khung = nơi đối0
            clo_k    <= 8'd0;
            rstk_ip[rsp] <= ip; rstk_fp[rsp] <= fp; rsp <= rsp + 8'd1;   // lưu điểm trả về
            sp       <= sp - 8'd1;                         // bỏ con trỏ closure
            state    <= S_CLO;
          end
          OP_NHAY:    begin ip <= { {(WORD-8){1'b0}}, operand }; end
          //   rẽ-nếu-0: ô ẩn KHÔNG kích nhánh (ẩn ≠ 0) — ≡ phần mềm `st != ẩn && val == 0`.
          OP_NHAY_0:  begin if (stack[sp-1] == 0 && stk_st[sp-1] != ST_AN) ip <= { {(WORD-8){1'b0}}, operand }; sp <= sp - 8'd1; end
          // RẼ theo TRẠNG-THÁI ba-trị (pop ô, nhảy nếu khớp mặt) — thay cờ ZF/CF bằng CỘNG HƯỞNG
          OP_NHAY_SANG: begin if (stk_st[sp-1]==ST_SANG) ip <= { {(WORD-8){1'b0}}, operand }; sp <= sp - 8'd1; end
          OP_NHAY_TOI:  begin if (stk_st[sp-1]==ST_TOI)  ip <= { {(WORD-8){1'b0}}, operand }; sp <= sp - 8'd1; end
          OP_NHAY_AN:   begin if (stk_st[sp-1]==ST_AN)   ip <= { {(WORD-8){1'b0}}, operand }; sp <= sp - 8'd1; end
          OP_DICH_TRAI: begin stack[sp-1] <= stack[sp-1] << operand; end          // dịch trái (in-place: trạng-thái giữ nguyên = lan-truyền ẩn)
          OP_NHAY_X:    begin ip <= stack[sp-1]; sp <= sp - 8'd1; end              // nhảy tới địa chỉ ở đỉnh
          OP_NHAY_0_X:  begin if (stack[sp-1] == 0 && stk_st[sp-1] != ST_AN) ip <= stack[sp-2];  // [target, cond]; ẩn → không nhảy
                              sp <= sp - 8'd2; end
          // --- HEAP: nạp/lưu gián tiếp (địa chỉ 16-bit từ ngăn xếp) ---
          OP_TAI_GIAN:begin if (viol_s1) begin out_data<=16'd911; out_valid<=1; halt<=1; end
                            else begin stack[sp-1] <= ram[rel_s1]; stk_st[sp-1] <= ST_SANG; end end  // tải heap = sáng
          OP_LUU_GIAN:begin if (viol_s2) begin out_data<=16'd911; out_valid<=1; halt<=1; end
                            else begin ram[rel_s2] <= stack[sp-1]; sp <= sp - 8'd2; end end // relocated
          // --- GỌI HÀM theo KHUNG: tham số nằm trên ngăn xếp; fp trỏ đáy khung ---
          OP_GOI_N: begin                                   // [arg0..argN-1, target], operand=N
            rstk_ip[rsp] <= ip; rstk_fp[rsp] <= fp; rsp <= rsp + 8'd1;
            fp <= sp - 8'd1 - operand[7:0];                 // đáy khung = nơi arg0 bắt đầu
            ip <= stack[sp-1];                              // nhảy tới target
            sp <= sp - 8'd1;                                // chỉ bỏ target; tham số ở lại làm khung
          end
          //   THAM_I LUÔN đẩy sáng: tham số/cục-bộ đi qua mô hình pstack phần mềm (chỉ val) → tải lại = sáng.
          OP_THAM_I:  begin stack[sp] <= stack[fp + operand[7:0]]; stk_st[sp] <= ST_SANG; sp <= sp + 8'd1; end  // đọc ô THAM_I thứ i
          OP_DANH_CB: begin sp <= sp + operand[7:0]; end                                 // dành n ô cục bộ cuối khung
          OP_LUU_THAM_I: begin stack[fp + operand[7:0]] <= stack[sp-1]; stk_st[fp + operand[7:0]] <= stk_st[sp-1]; sp <= sp - 8'd1; end  // ghi ô khung thứ i
          OP_TRA_VE_N: begin                                // trị trả về ở đỉnh; gấp khung
            stack[fp] <= stack[sp-1]; stk_st[fp] <= stk_st[sp-1];  // đặt kết quả (KÈM trạng-thái: hàm trả ẩn → ẩn)
            sp  <= fp + 8'd1;                               // bỏ toàn khung, chừa kết quả
            ip  <= rstk_ip[rsp-1];                          // khôi phục ip & fp người gọi
            fp  <= rstk_fp[rsp-1];
            rsp <= rsp - 8'd1;
          end
          // --- NGẮT TIMER phần cứng ---
          OP_BAT_NGAT: begin ivec <= stack[sp-1]; sp <= sp - 8'd1; ie <= 1'b1; end  // handler ở đỉnh
          OP_TAT_NGAT: begin ie <= 1'b0; end
          OP_HEN_GIO:  begin period <= { {(WORD-8){1'b0}}, operand }; timer <= 0; end // chu kỳ = operand
          OP_NGAT_VE:  begin ip <= saved_ip; in_isr <= 1'b0; end                      // IRET: quay về điểm bị ngắt
          // --- ĐA NHIỆM TIỀN-ĐỊNH ---
          OP_TAC_VU: begin                                                            // [entry_ip] → đăng ký task
            t_ip[ntask] <= stack[sp-1];
            t_sp[ntask] <= ntask << 6;      // sp base = i*64 (ngăn xếp riêng mỗi task)
            t_fp[ntask] <= ntask << 6;
            t_rsp[ntask] <= ntask << 5;     // rsp base = i*32
            mbase[ntask] <= ntask << 7;     // VÙNG NHỚ riêng = [i*128, i*128+128) → CÔ LẬP
            mbound[ntask] <= 16'd128;
            t_hsp[ntask] <= ntask << 3;     // ngăn-xếp-handler riêng = [i*8, i*8+8) → try/bắt CÔ LẬP
            t_dead[ntask] <= 1'b0;
            ntask <= ntask + 8'd1; sp <= sp - 8'd1;
          end
          OP_LAP_LICH: begin                                                          // khởi động: nạp task 0
            cur <= 0; sched_on <= 1'b1; sched_mode <= 1'b0; timer <= 0;
            ip <= t_ip[0]; sp <= t_sp[0]; fp <= t_fp[0]; rsp <= t_rsp[0]; hsp <= t_hsp[0];
          end
          OP_LICH_HOC: begin                                                          // khởi động LẬP LỊCH BIẾT-HỌC (γ)
            cur <= 0; sched_on <= 1'b1; sched_mode <= 1'b1; timer <= 0;
            ip <= t_ip[0]; sp <= t_sp[0]; fp <= t_fp[0]; rsp <= t_rsp[0]; hsp <= t_hsp[0];
          end
          OP_BAT_SIP: begin sip_on <= 1'b1; end                                        // bật CÔ LẬP tiến trình
          OP_DUNG:    begin halt <= 1; end
          default:    begin halt <= 1; end  // lệnh lạ → dừng an toàn
        endcase
      end else if (state == S_STR) begin
        // RỌI_CHUỖI: duyệt cons-list mã-ký-tự, in TỪNG ký tự rồi xung HẾT-CHUỖI
        if (str_a == 0) begin
          out_data <= 0; out_valid <= 1; out_kind <= 2'd2;   // HẾT chuỗi
          did_out[cur] <= 1'b1; state <= S_FETCH;
        end else begin
          out_data <= ram[str_a] & 32'h1FFFFF;                // mã ký tự (21 bit thấp)
          out_valid <= 1; out_kind <= 2'd1;
          str_a <= ram[str_a + 1] & UNTAG;                    // sang ô kế (cdr, gỡ thẻ)
        end
      end else if (state == S_DS) begin
        // RỌI_DS: duyệt cons-list SỐ, in TỪNG số (kind=4) rồi xung HẾT-DS (kind=5).
        if (ds_a == 0) begin
          out_data <= 0; out_valid <= 1; out_kind <= 3'd5;     // HẾT danh sách
          did_out[cur] <= 1'b1; state <= S_FETCH;
        end else begin
          out_data <= ram[ds_a]; out_valid <= 1; out_kind <= 3'd4;  // phần tử số (car)
          ds_a <= ram[ds_a + 1] & UNTAG;                       // sang cons kế (cdr, gỡ thẻ)
        end
      end else begin
        // S_CLO — GỌI_CLOSURE: dựng khung [bắt…, đối…] rồi nhảy mã closure
        if (clo_k < clo_n) begin
          // PHA 1: dịch ĐỐI lên 'ncap' ô (xử lý từ đối CAO xuống để khỏi đè)
          stack[clo_base + clo_ncap + (clo_n-8'd1-clo_k)] <= stack[clo_base + (clo_n-8'd1-clo_k)];
          clo_k <= clo_k + 8'd1;
        end else if (clo_k < clo_n + clo_ncap) begin
          // PHA 2: chép BẮT từ heap vào đáy khung
          stack[clo_base + (clo_k - clo_n)] <= ram[clo_cp + 8'd2 + (clo_k - clo_n)];
          clo_k <= clo_k + 8'd1;
        end else begin
          fp <= clo_base; sp <= clo_base + clo_ncap + clo_n;  // khung = [bắt…, đối…]
          ip <= clo_code; state <= S_FETCH;                   // nhảy vào mã closure
        end
      end
    end
  end
endmodule

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
  output reg            halt,     // CPU đã DỪNG
  // ★ GỌI-HỆ (trap): CPU KHÔNG tự làm I/O — nó dừng lại, chìa số hiệu + đối ra ngoài rồi CHỜ NHÂN.
  //   Đúng mô hình `syscall` của CPU thật: bắt tay trap_valid → trap_ack, kết quả vào trap_ret.
  output reg            trap_valid, // 1 = đang xin nhân phục vụ (giữ tới khi có trap_ack)
  output reg [7:0]      trap_num,   // số hiệu gọi-hệ
  output reg [WORD-1:0] trap_arg,   // đối thứ 0
  output reg [WORD-1:0] trap_arg1,  // đối thứ 1  (đọc thêm 1 chu-kỳ từ ngăn xếp)
  output reg [WORD-1:0] trap_arg2,  // đối thứ 2  (đọc thêm 2 chu-kỳ)
  output reg [7:0]      trap_nargs, // số đối thật sự (0..3)
  input                 trap_ack,   // nhân báo: đã phục vụ xong
  input      [WORD-1:0] trap_ret,   // giá trị nhân trả về (đẩy vào ngăn xếp)
  // ★ CỔNG SOI/CẤP BỘ NHỚ cho cầu ngoài (UART trên bo thật, hoặc VPI khi mô phỏng).
  //   Nhân ở ngoài cần ĐỌC heap để lấy chuỗi đối, và GHI heap để cấp chuỗi trả về.
  //   Chỉ dùng lúc CPU đang ĐỨNG ở S_TRAP ⇒ không bao giờ tranh chấp với chính CPU.
  //   Không nối thì vô hại: dbg_we=0 nên không ghi gì.
  input      [15:0]     dbg_a,      // địa chỉ soi/cấp
  input                 dbg_re,     // 1 = đọc (chiếm cổng đọc RAM đúng chu kỳ này)
  input                 dbg_we,     // 1 = ghi
  input      [WORD-1:0] dbg_wd,     // dữ liệu ghi
  output     [WORD-1:0] dbg_q       // dữ liệu đọc (trễ 1 chu kỳ, chính là ram_q)
);
  // --- opcode (khớp GVM phần mềm) ---
  localparam OP_DUNG=0, OP_NAP=1, OP_CONG=10, OP_TRU=11, OP_NHAN=12, OP_ROI=14,
             OP_NHAY=15, OP_NHAN_BAN=20, OP_BO=21, OP_DOI=22, OP_DICH_TRAI=26,
             OP_ROI_CHUOI=34, OP_ROI_AUTO=65, OP_GOI_CLOSURE=58,  // in chuỗi · in tự-suy-kiểu · gọi closure
             OP_DANH_CB=66, OP_LUU_THAM_I=67,           // dành ô cục bộ · ghi ô khung (biến cục bộ per-call)
             OP_NHAY_X=35, OP_NHAY_0_X=36,             // nhảy GIÁN TIẾP (địa chỉ từ ngăn xếp)
             OP_GOI_HE=72,                              // ★ TRAP: xin NHÂN phục vụ (syscall)
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
             OP_CONG_HANG=68,                           // ★ SIÊU-LỆNH add-immediate: top + operand (gộp NẠP k; CỘNG)
             OP_NHAN_CONG_HANG=69,                      // ★ SIÊU-LỆNH #2 dup+add-imm: [x]→[x,x+operand] (gộp NHÂN_BẢN; CỘNG_HẰNG k; heap-cons)
             OP_GHI_TRUONG=70,                          // ★ SIÊU-LỆNH #3 store-field: ram[top]=ram[operand], giữ top (gộp NHÂN_BẢN; TẢI_Ô r; LƯU_GIÁN)
             OP_DICH_CONG_BYTE=71,                      // ★ SIÊU-LỆNH #4 dựng-hằng: stack[sp-1]=(top<<8)+operand (gộp DỊCH_TRÁI 8; CỘNG_HẰNG k)
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
  reg [7:0]      trap_n, trap_k;     // số đối của lần gọi-hệ này · bộ đếm chu-kỳ đọc thêm
  reg [4:0]      state;             // FSM: FETCH/EXEC + ĐA-CHU-KỲ + ĐỌC-BRAM ram/stack (prefetch toán-hạng, trễ 1 chu kỳ)
  localparam S_FETCH=5'd0, S_EXEC=5'd1, S_STR=5'd2, S_CLO=5'd3, S_DS=5'd4, S_DIV=5'd5,
             S_TAIO=5'd6,  S_TAIG=5'd7,  S_CLOR1=5'd8, S_CLOR2=5'd9, S_CLO2=5'd10,
             S_STRC=5'd11, S_STRN=5'd12, S_DSC=5'd13,  S_DSN=5'd14,
             S_OPB=5'd15,  S_OPA=5'd16,  S_THAMI=5'd17, S_DOI2=5'd18, S_CLO1R=5'd19,
             S_FOP=5'd20,  // tầng PIPELINE F-op: S_EXEC NHÂN→fprod; S_FOP NEGATE→div_acc/div_dor (cắt đường tới-hạn)
             S_MUL=5'd21,  // tầng PIPELINE NHÂN: S_EXEC nhân→nhan_r; S_MUL ghi (đồng-bộ, lợi timing ở WORD lớn)
             S_GHITRUONG=5'd22,
             S_TRAP=5'd23,   // ★ chờ nhân phục vụ gọi-hệ (giữ trap_valid tới khi trap_ack)
             S_TRAPA=5'd24;  // ★ đọc NỐT các đối sâu trong ngăn xếp (gọi-hệ ≥2 đối)  // ★ SIÊU-LỆNH #3: S_EXEC đọc ram[rel_o]→ram_q; S_GHITRUONG ghi ram[rel_s1]=ram_q (RAM-to-RAM 2 chu-kỳ)
  // RAM + STACK = BRAM ĐỌC-ĐỒNG-BỘ: mọi đọc qua `<reg>_q <= mem[addr]` (đăng-ký) → yosys suy SB_RAM40 (1R1W);
  //   trạng-thái-chờ kế tiêu-thụ. Ghi giữ nguyên (mem[wa]<=wd, đã đăng-ký).
  reg [WORD-1:0] ram_q;             // dữ liệu RAM đọc được (trễ 1 chu kỳ)
  // STACK BRAM: đọc đồng-bộ qua stack_q; PREFETCH 2 toán-hạng đỉnh vào opA(=stack[sp-2]) opB(=stack[sp-1])
  //   trước S_EXEC (S_FETCH→S_OPB→S_OPA→S_EXEC). stk_st GIỮ thanh-ghi tổ-hợp (2-bit nhỏ, đọc trực tiếp).
  reg [WORD-1:0] stack_q;           // dữ liệu STACK đọc được (trễ 1 chu kỳ)
  reg [WORD-1:0] opA, opB;          // toán-hạng prefetch: opA=stack[sp-2] (a/NOS), opB=stack[sp-1] (b/TOS)
  // RSTK BRAM: rstk_ip/rstk_fp CHỈ đọc ở TRA_VE_N tại rsp-1 → đọc-đăng-ký rsp-1 MỖI chu kỳ; prefetch
  //   (S_OPB/S_OPA) đủ thời-gian để rstk_*_q ổn-định trước S_EXEC (rsp không đổi trong prefetch).
  reg [WORD-1:0] rstk_ip_q;         // rstk_ip[rsp-1] đọc được
  reg [15:0]     rstk_fp_q;         // rstk_fp[rsp-1] đọc được
  // STK_ST BRAM (2-bit ba-trị, SONG SONG stack): prefetch stA(=stk_st[sp-2]) stB(=stk_st[sp-1]) như opA/opB.
  reg [1:0]      stk_st_q;          // trạng-thái đọc được (trễ 1 chu kỳ)
  reg [1:0]      stA, stB;          // stA=stk_st[sp-2], stB=stk_st[sp-1] (prefetch)
  // --- CHIA TUẦN-TỰ (restoring divider): thay chia tổ-hợp 64-bit của F-ops → tiết kiệm LUT lớn ---
  reg [127:0] div_acc;              // {rem[63:0], quo[63:0]} thanh-ghi dịch
  reg [63:0]  div_dor;              // |số chia| (ước số), 64-bit không dấu
  reg [6:0]   div_i;                // bộ đếm vòng (0..64)
  reg         div_neg;              // thương ÂM (XOR dấu)
  reg [15:0]  div_dst;              // chỉ-mục ngăn xếp ghi kết quả (= sp-2 lúc vào)
  wire [63:0] div_q_signed = div_neg ? (~div_acc[63:0] + 64'd1) : div_acc[63:0];  // thương CÓ DẤU 64-bit
  // PIPELINE F-op: S_EXEC chỉ NHÂN (đăng-ký fprod/fdor_raw); S_FOP mới NEGATE → div_acc/div_dor.
  //   Tách nhân↔negate sang 2 chu kỳ → KHÔNG còn đường nhân-64-bit-rồi-negate-64-bit trong 1 chu kỳ.
  reg signed [63:0] fprod;          // tích (số bị chia, CÓ DẤU): FNHÂN=a·b · FCHIA=a·10000
  reg signed [63:0] fdor_raw;       // ước số CÓ DẤU (trước lấy |.|): FNHÂN=10000 · FCHIA=b
  reg [WORD-1:0]    nhan_r;         // PIPELINE NHÂN: tích WORD-bit (đăng-ký ở S_EXEC, ghi ở S_MUL)
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
  wire bin_an = (stB == ST_AN) || (stA == ST_AN);   // stB=stk_st[sp-1], stA=stk_st[sp-2] (prefetch)
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
  wire [15:0] rel_s1 = sip_on ? (mbase[cur] + opB[15:0])                : opB[15:0]; // TẢI_GIÁN (heap) — opB=stack[sp-1]
  wire [15:0] rel_s2 = sip_on ? (mbase[cur] + opA[15:0])                : opA[15:0]; // LƯU_GIÁN (heap) — opA=stack[sp-2]
  wire viol_o  = sip_on && (operand           >= mbound[cur]);          // vượt biên → FAULT
  wire viol_s1 = sip_on && (opB[11:0] >= mbound[cur]);
  wire viol_s2 = sip_on && (opA[11:0] >= mbound[cur]);

  wire [7:0] opcode  = instr[15:8];
  wire [7:0] operand = instr[7:0];

  // --- ALU dựng từ adderN (cổng NAND), rộng WORD ---
  wire            do_sub  = (opcode == OP_TRU);
  wire [WORD-1:0] alu_a   = opA;   // stack[sp-2] (prefetch)
  wire [WORD-1:0] alu_braw= opB;   // stack[sp-1] (prefetch)
  wire [WORD-1:0] alu_b   = do_sub ? ~alu_braw : alu_braw;   // trừ = a + ~b + 1
  wire [WORD-1:0] alu_y;  wire alu_co;
  adderN #(WORD) alu(alu_a, alu_b, do_sub, alu_y, alu_co);

  // --- SỐ THỰC điểm-cố-định ×10000: trung gian 64-bit CÓ DẤU (suy ra DSP), '/' Verilog cắt-về-0 ---
  //   FNHÂN = (a·b)/10000 · FCHIA = (a·10000)/b (b=0 → 0). Trùng khít fbin() phần mềm / i64 wasm.
  wire signed [63:0] f_a64 = {{(64-WORD){opA[WORD-1]}}, opA};   // sign-extend a(=stack[sp-2]) → 64-bit
  wire signed [63:0] f_b64 = {{(64-WORD){opB[WORD-1]}}, opB};   // sign-extend b(=stack[sp-1]) → 64-bit
  //   GIỜ chỉ giữ phần NHÂN tổ-hợp (vào DSP); phần CHIA /10000 và /b làm TUẦN-TỰ ở S_DIV (bỏ chia 64-bit tổ-hợp).
  wire signed [63:0] fmul_prod = f_a64 * f_b64;            // (a·b) — chia /10000 ở S_DIV
  wire signed [63:0] fdiv_prod = f_a64 * 64'sd10000;       // (a·10000) — chia /b ở S_DIV
  wire fdiv_an = (stB == ST_AN) || (stA == ST_AN) || (opB == 0);  // chia 0 → ẩn (stB/stA/opB prefetch)
  // CHIA/NHÂN có-dấu TÍNH RIÊNG ở wire signed (self-determined) — KHÔNG để ternary unsigned ép
  //   thành chia-unsigned (lỗi: −200/2 ra 0x7FFFFF9C thay −100; chỉ lộ với SỐ ÂM).
  //   CHIA giờ đi qua divider TUẦN-TỰ (S_FOP→S_DIV) — KHÔNG còn wire chia tổ-hợp (đường tới-hạn cũ).
  wire signed [WORD-1:0] nhan_p = $signed(opA) * $signed(opB);   // nhân → DSP (nhanh), giữ tổ-hợp

  // --- CỘNG HƯỞNG γ (SO_SÁNH): a=niềm-tin (stack[sp-2]), b=thực-tại (stack[sp-1]).
  //   γ = 1 − 2·|b−a|/max(|b|,1) ⇒ STATE chỉ cần SO INTEGER (khỏi chia): 2d<scale→sáng · >→tối · =→ẩn.
  //   (val unsigned khớp gvm_may.resonance; |b|=b vì val ≥ 0). Hoặc input ẩn → ẩn.
  wire [WORD-1:0] so_a = opA, so_b = opB;   // stack[sp-2], stack[sp-1] (prefetch)
  wire [WORD-1:0] so_dabs = (so_b >= so_a) ? (so_b - so_a) : (so_a - so_b);   // |b−a|
  wire [WORD-1:0] so_scale = (so_b == 0) ? {{(WORD-1){1'b0}},1'b1} : so_b;    // max(|b|,1)
  wire [WORD+1:0] so_2d = {2'b00, so_dabs} << 1;                              // 2·d (đủ rộng, không tràn)
  wire [WORD+1:0] so_scale_e = {2'b00, so_scale};
  wire so_an_in = (stB == ST_AN) || (stA == ST_AN);   // stB/stA prefetch
  wire [1:0] so_st = so_an_in ? ST_AN
                   : (so_2d <  so_scale_e) ? ST_SANG
                   : (so_2d >  so_scale_e) ? ST_TOI : ST_AN;

  // ★ ĐỊA-CHỈ ĐỌC GỘP (1 cổng) cho STACK/RAM BRAM: yosys CHỈ suy SB_RAM40 khi memory có ĐÚNG 1 câu đọc.
  //   Nhiều câu `_q<=mem[..]` ở nhiều state → yosys coi NHIỀU cổng đọc → rớt về thanh-ghi. Nên mux địa-chỉ theo state.
  wire [15:0] stk_ra = (state==S_OPB) ? (sp - 16'd2)                                  // prefetch opA(=stack[sp-2])
                     : (state==S_EXEC && opcode==OP_THAM_I) ? (fp + {8'b0, operand})  // THAM_I đọc ô khung
                     : (state==S_CLO  && clo_k < clo_n) ? (clo_base + (clo_n-8'd1-clo_k))  // closure pha1 đọc ĐỐI
                     : (state==S_TRAPA) ? (sp - 16'd3 - {8'b0, trap_k})               // gọi-hệ ≥2 đối: đọc sâu dần
                     : (sp - 16'd1);                                                  // S_FETCH & mặc-định: prefetch opB(=stack[sp-1])
  wire [15:0] ram_ra = dbg_re                                     ? dbg_a   // ★ cầu ngoài soi heap:
                     // CPU đang ĐỨNG ở S_TRAP nên cổng đọc rảnh. KHÔNG mở cổng đọc thứ ba —
                     // BRAM (DP16KD) chỉ có HAI cổng; thêm nữa là cả 4096×32 rơi xuống LUT.
                     : (state==S_EXEC && opcode==OP_TAI_O)       ? rel_o
                     : (state==S_EXEC && opcode==OP_GHI_TRUONG)  ? rel_o   // ★ #3: đọc cell r (= TẢI_Ô); ghi ở S_GHITRUONG
                     : (state==S_EXEC && opcode==OP_TAI_GIAN)    ? rel_s1
                     : (state==S_EXEC && opcode==OP_GOI_CLOSURE) ? (opB & UNTAG)         // ram[cp]
                     : (state==S_CLOR1)                          ? (clo_cp + 16'd1)      // ram[cp+1]
                     : (state==S_CLO && clo_k >= clo_n)          ? (clo_cp + 16'd2 + (clo_k - clo_n))  // pha2 BẮT
                     : (state==S_STR)  ? str_a
                     : (state==S_STRC) ? (str_a + 16'd1)
                     : (state==S_DS)   ? ds_a
                     : (state==S_DSC)  ? (ds_a + 16'd1)
                     : 16'd0;
  // stk_st CHỈ đọc ở sp-1/sp-2 (prefetch song-song opA/opB) → mux 1 cổng như stk_ra (không THAM_I/closure).
  wire [15:0] stst_ra = (state==S_OPB) ? (sp - 16'd2) : (sp - 16'd1);

  // --- boot ROM: GỌI HÀM (khung) + HEAP ---
  //   hàm nhân_đôi(x) = x + x  (addr 1);  main gọi nhân_đôi(21)=42 → RỌI;
  //   rồi heap: ram[50]=99 (LƯU_GIÁN), đọc lại (TẢI_GIÁN) → RỌI. Xuất [42, 99].
  initial begin
    rom[0]=16'h0F05;  // NHẢY 5        ; nhảy qua thân hàm
    rom[1]=16'h2700;  // THAM_I 0      ; nhân_đôi: push x
    rom[2]=16'h2700;  // THAM_I 0      ; push x
    rom[3]=16'h0A00;  // CỘNG          ; x+x
    rom[4]=16'h2800;  // TRẢ_VỀ_N
    rom[5]=16'h0115;  // NẠP 21        ; main: đối số
    rom[6]=16'h0101;  // NẠP 1         ; địa chỉ hàm (=1)
    rom[7]=16'h2601;  // GỌI_N 1       ; nhân_đôi(21) -> 42
    rom[8]=16'h0E00;  // RỌI           ; xuất 42
    rom[9]=16'h0132;  // NẠP 50        ; địa chỉ heap
    rom[10]=16'h0163; // NẠP 99        ; giá trị
    rom[11]=16'h1E00; // LƯU_GIÁN      ; ram[50] = 99
    rom[12]=16'h0132; // NẠP 50
    rom[13]=16'h1D00; // TẢI_GIÁN      ; push ram[50] = 99
    rom[14]=16'h0E00; // RỌI           ; xuất 99
    rom[15]=16'h0111; // NẠP 17
    rom[16]=16'h0105; // NẠP 5
    rom[17]=16'h2F00; // CHIA          ; 17/5 = 3 (số nguyên)
    rom[18]=16'h0E00; // RỌI           ; xuất 3
    rom[19]=16'h0108; // NẠP 8
    rom[20]=16'h0105; // NẠP 5
    rom[21]=16'h2C00; // LỚN_HƠN       ; 8>5 → 1
    rom[22]=16'h0E00; // RỌI           ; xuất 1
    rom[23]=16'h0106; // NẠP 6
    rom[24]=16'h0109; // NẠP 9
    rom[25]=16'h0C00; // NHÂN          ; 6*9 = 54
    rom[26]=16'h0E00; // RỌI           ; xuất 54
    // nạp địa chỉ 16-bit (NẠP hi; DỊCH_TRÁI 8; NẠP lo; CỘNG) rồi NHẢY_X tới 34
    rom[27]=16'h0100; // NẠP 0         ; byte cao
    rom[28]=16'h1A08; // DỊCH_TRÁI 8
    rom[29]=16'h0122; // NẠP 34        ; byte thấp → địa chỉ 34
    rom[30]=16'h0A00; // CỘNG
    rom[31]=16'h2300; // NHẢY_X        ; nhảy tới 34 (bỏ qua 32–33)
    rom[32]=16'h016F; // NẠP 111       ; (bị BỎ QUA)
    rom[33]=16'h0E00; // RỌI           ; (bị BỎ QUA — nếu chạy sẽ xuất 111)
    rom[34]=16'h0107; // NẠP 7         ; đích nhảy
    rom[35]=16'h0E00; // RỌI           ; xuất 7
    rom[36]=16'h0000; // DỪNG
  end

  // --- CHU KỲ CLOCK: fetch → execute ---
  //   RESET ĐỒNG-BỘ (KHÔNG 'or posedge rst'): để stack/ram (đọc-đăng-ký) MAP ĐƯỢC SB_RAM40 —
  //   thanh-ghi-đọc BRAM không hỗ-trợ async-reset nên async-reset-domain ép memory về thanh-ghi.
  //   Hành-vi giống hệt: testbench giữ rst=1 qua cạnh clk đầu → reset vẫn áp ở cạnh đầu.
  assign dbg_q = ram_q;         // ★ cầu ngoài đọc qua CHÍNH cổng đọc của CPU (xem ram_ra)

  always @(posedge clk) begin
    if (rst) begin
      ip <= 0; sp <= 0; fp <= 0; rsp <= 0; state <= S_FETCH; halt <= 0; out_valid <= 0; out_data <= 0; out_kind <= 0; out_proc <= 0;
      sched_evt <= 0; sched_cur <= 0; sched_rho <= 0; hsp <= 0; out_state <= 0;
      trap_valid <= 0; trap_num <= 0; trap_arg <= 0; trap_arg1 <= 0; trap_arg2 <= 0;
      trap_nargs <= 0; trap_n <= 0; trap_k <= 0;
      ie <= 0; in_isr <= 0; ivec <= 0; saved_ip <= 0; timer <= 0; period <= 0;   // ngắt tắt lúc reset
      cur <= 0; ntask <= 0; sched_on <= 0; sched_mode <= 0; sip_on <= 0;          // đa nhiệm/SIP tắt lúc reset
      for (ri = 0; ri < NT; ri = ri + 1) begin sigma[ri] <= 16'd128; cred[ri] <= 0; did_out[ri] <= 0; t_dead[ri] <= 0; t_hsp[ri] <= 0; end
    end else if (!halt) begin
      out_valid <= 0; sched_evt <= 0;
      // ★ cầu ngoài CẤP heap (chuỗi nhân trả về). Đặt TRƯỚC case nên lệnh nào ghi ram cùng chu kỳ
      //   vẫn thắng — nhưng không bao giờ xảy ra: dbg_we chỉ bật khi CPU đứng ở S_TRAP.
      if (dbg_we) ram[dbg_a] <= dbg_wd;
      if (state == S_EXEC) timer <= timer + 1;     // ★ HỢP-NHẤT GRANULARITY: đếm theo LỆNH (1/op ở S_EXEC, mỗi lệnh đúng 1 S_EXEC) — KHỚP software (timer_period=số LỆNH). HẸN_GIỜ/fault `timer<=0` nằm SAU trong case → override.
      stack_q <= stack[stk_ra];                    // ★ ĐỌC STACK (1 cổng, địa-chỉ mux) → BRAM-eligible; consumer dùng ở state kế
      ram_q   <= ram[ram_ra];                      // ★ ĐỌC RAM   (1 cổng, địa-chỉ mux) → BRAM-eligible
      rstk_ip_q <= rstk_ip[rsp-16'd1];             // ★ ĐỌC RSTK (1 cổng, rsp-1) → BRAM; TRA_VE_N dùng (prefetch đủ trễ)
      rstk_fp_q <= rstk_fp[rsp-16'd1];
      stk_st_q  <= stk_st[stst_ra];                // ★ ĐỌC STK_ST (1 cổng) → BRAM-eligible; stB/stA tiêu-thụ ở S_OPB/S_OPA
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
              // ★ VÁ HAZARD: chọn-LẠI-cùng-task (gsel_live==cur) ⇒ t_ip[cur]<=ip (dòng trên) & ip<=t_ip[cur]
              //   chạy CÙNG chu-kỳ → non-blocking đọc t_ip CŨ (stale) → wild-jump. Giữ STATE hiện-tại khi cùng-task.
              ip  <= (gsel_live==cur) ? ip  : t_ip[gsel_live];   sp  <= (gsel_live==cur) ? sp  : t_sp[gsel_live];
              fp  <= (gsel_live==cur) ? fp  : t_fp[gsel_live];   rsp <= (gsel_live==cur) ? rsp : t_rsp[gsel_live];
              hsp <= (gsel_live==cur) ? hsp : t_hsp[gsel_live];
            end
          end else begin
            // round-robin: cùng vá hazard chọn-lại-cùng-task (nxt==cur khi 1 task sống)
            cur <= nxt;
            ip  <= (nxt==cur) ? ip  : t_ip[nxt];   sp  <= (nxt==cur) ? sp  : t_sp[nxt];
            fp  <= (nxt==cur) ? fp  : t_fp[nxt];   rsp <= (nxt==cur) ? rsp : t_rsp[nxt];   hsp <= (nxt==cur) ? hsp : t_hsp[nxt];
          end
        end else if (ie && !in_isr && period != 0 && timer >= period) begin
          // ★ NGẮT TIMER kiểu handler (giữ tương thích): lưu ip, nhảy handler
          saved_ip <= ip; ip <= ivec; in_isr <= 1'b1; timer <= 0;
        end else begin
          instr <= rom[ip]; ip <= ip + 1; state <= S_OPB;   // PREFETCH: stk_ra=sp-1 (mặc-định) → stack_q=stack[sp-1]
        end
      end else if (state == S_TRAPA) begin
        // stack_q ứng với địa chỉ đặt ở chu-kỳ TRƯỚC (sp-3-trap_k) ⇒ chu-kỳ đầu chỉ để dựng địa chỉ.
        if (trap_k == 8'd0) trap_k <= 8'd1;
        else if (trap_n == 8'd2) begin
          trap_num <= stack_q[7:0]; sp <= sp - 8'd3; trap_valid <= 1'b1; state <= S_TRAP;
        end else begin                                        // 3 đối: đọc đối0 rồi mới tới số hiệu
          if (trap_k == 8'd1) begin trap_arg <= stack_q; trap_k <= 8'd2; end
          else begin
            trap_num <= stack_q[7:0]; sp <= sp - 8'd4; trap_valid <= 1'b1; state <= S_TRAP;
          end
        end
      end else if (state == S_TRAP) begin
        // ★ CHỜ NHÂN. Không đếm timer, không chạy lệnh nào — CPU thật sự đứng im.
        if (trap_ack) begin
          stack[sp] <= trap_ret; stk_st[sp] <= ST_SANG; sp <= sp + 8'd1;   // đẩy kết quả
          trap_valid <= 1'b0; state <= S_FETCH;
        end
      end else if (state == S_OPB) begin
        opB <= stack_q; stB <= stk_st_q; state <= S_OPA;  // opB/stB=stack/stk_st[sp-1]; đang đọc [sp-2] cho S_OPA
      end else if (state == S_OPA) begin
        opA <= stack_q; stA <= stk_st_q; state <= S_EXEC;            // opA/stA=stack/stk_st[sp-2]; sang EXEC
      end else if (state == S_EXEC) begin
        state <= S_FETCH;
        case (opcode)
          OP_NAP:     begin stack[sp] <= { {(WORD-8){1'b0}}, operand }; stk_st[sp] <= ST_SANG; sp <= sp + 8'd1; end
          OP_AN:      begin stack[sp] <= 0; stk_st[sp] <= ST_AN; sp <= sp + 8'd1; end   // đẩy ô ẩn (DE/chưa-biết)
          OP_TAI_O:   begin if (viol_o) begin out_data<=16'd911; out_valid<=1; halt<=1; end  // ★ SIP fault
                            else begin state <= S_TAIO; end end          // ram_ra=rel_o → ram_q=ram[rel_o]; S_TAIO đẩy lên ngăn xếp
          OP_LUU_O:   begin if (viol_o) begin out_data<=16'd911; out_valid<=1; halt<=1; end
                            else begin if (!dbg_we) ram[rel_o] <= opB; sp <= sp - 8'd1; end end   // LƯU_Ô: ghi opB(=stack[sp-1])
          //   số học LAN TRUYỀN ẩn: chạm ẩn → kết quả ẩn (val=0, ≡ ANCELL phần mềm), ngược lại sáng.
          OP_CONG:    begin stack[sp-2] <= bin_an ? {WORD{1'b0}} : alu_y; stk_st[sp-2] <= bin_an ? ST_AN : ST_SANG; sp <= sp - 8'd1; end  // do_sub=0
          OP_CONG_HANG: begin   // ★ siêu-lệnh add-immediate: stack[sp-1] = top + operand (sp GIỮ; pop1+push1). Ẩn lan-truyền.
                        stack[sp-1]  <= (stB==ST_AN) ? {WORD{1'b0}} : (opB + {{(WORD-8){1'b0}}, operand});
                        stk_st[sp-1] <= (stB==ST_AN) ? ST_AN : ST_SANG; end
          OP_NHAN_CONG_HANG: begin   // ★ siêu-lệnh #2 dup+add-imm: stack[sp] = top + operand, sp+1 (GIỮ x ở sp-1). Ẩn lan-truyền.
                        stack[sp]    <= (stB==ST_AN) ? {WORD{1'b0}} : (opB + {{(WORD-8){1'b0}}, operand});
                        stk_st[sp]   <= (stB==ST_AN) ? ST_AN : ST_SANG; sp <= sp + 8'd1; end
          OP_GHI_TRUONG: begin   // ★ siêu-lệnh #3 store-field: ram_ra=rel_o (đọc cell r)→ram_q; S_GHITRUONG ghi ram[rel_s1=top]=ram_q. sp GIỮ.
                        if (viol_o || viol_s1) begin out_data<=16'd911; out_valid<=1; halt<=1; end  // SIP fault (đọc r HOẶC ghi top)
                        else state <= S_GHITRUONG; end
          OP_DICH_CONG_BYTE: begin   // ★ siêu-lệnh #4 dựng-hằng: stack[sp-1] = (top<<8)+operand (sp GIỮ). (top<<8) cắt-về WORD-bit ≡ &MASK; byte-thấp 0 nên +operand không tràn. Ẩn lan-truyền.
                        stack[sp-1]  <= (stB==ST_AN) ? {WORD{1'b0}} : ((opB << 8) + {{(WORD-8){1'b0}}, operand});
                        stk_st[sp-1] <= (stB==ST_AN) ? ST_AN : ST_SANG; end
          OP_TRU:     begin stack[sp-2] <= bin_an ? {WORD{1'b0}} : alu_y; stk_st[sp-2] <= bin_an ? ST_AN : ST_SANG; sp <= sp - 8'd1; end  // do_sub=1
          // nhân → DSP; PIPELINE: ẩn→1 chu kỳ; ngược lại đăng-ký tích→S_MUL ghi (rút đường nhân khỏi chu-kỳ EXEC)
          OP_NHAN:    begin
            if (bin_an) begin stack[sp-2] <= {WORD{1'b0}}; stk_st[sp-2] <= ST_AN; sp <= sp - 8'd1; end
            else begin nhan_r <= nhan_p; div_dst <= sp - 16'd2; sp <= sp - 8'd1; state <= S_MUL; end
          end
          // chia số nguyên có dấu, cắt-về-0 (b=0 → 0). NOTE: bản FPGA thật nên dùng
          // divider nhiều-chu-kỳ; ở đây để '/' suy ra mạch chia cho mô phỏng/kiểm chứng.
          OP_CHIA:    begin   // PIPELINE: chia qua divider TUẦN-TỰ (S_FOP→S_DIV) — bỏ chia 16-bit tổ-hợp (đường tới-hạn)
            if (bin_an)        begin stack[sp-2] <= {WORD{1'b0}}; stk_st[sp-2] <= ST_AN;   sp <= sp - 8'd1; end  // ẩn lan-truyền
            else if (opB == 0) begin stack[sp-2] <= {WORD{1'b0}}; stk_st[sp-2] <= ST_SANG; sp <= sp - 8'd1; end  // chia 0 → 0 (khít chia_q cũ)
            else begin fprod <= f_a64; fdor_raw <= f_b64; div_dst <= sp - 16'd2; sp <= sp - 8'd1; state <= S_FOP; end  // |opA|/|opB|, dấu = XOR
          end
          // --- SỐ THỰC điểm-cố-định ×10000 (DSP 64-bit, cắt-về-0) ---
          //   F-ops: ẩn → 1 chu kỳ (0/ẩn); ngược lại NẠP divider rồi sang S_DIV (chia /10000 hoặc /b tuần-tự).
          OP_FNHAN:   begin   // PIPELINE: chỉ NHÂN (a·b)→fprod ở đây; NEGATE→div_* ở S_FOP
            if (bin_an) begin stack[sp-2] <= {WORD{1'b0}}; stk_st[sp-2] <= ST_AN; sp <= sp - 8'd1; end
            else begin
              fprod <= fmul_prod;      // a·b (số chia 10000>0)
              fdor_raw <= 64'sd10000;
              div_dst <= sp - 16'd2; sp <= sp - 8'd1; state <= S_FOP;
            end
          end
          OP_FCHIA:   begin   // chia 0/ẩn → ẩn (1 chu kỳ); ngược lại |a·10000| / |b| tuần-tự (qua S_FOP)
            if (fdiv_an) begin stack[sp-2] <= {WORD{1'b0}}; stk_st[sp-2] <= ST_AN; sp <= sp - 8'd1; end
            else begin
              fprod <= fdiv_prod;      // a·10000
              fdor_raw <= f_b64;       // b (CÓ DẤU; |.| ở S_FOP)
              div_dst <= sp - 16'd2; sp <= sp - 8'd1; state <= S_FOP;
            end
          end
          // in số thực: ẩn → out_kind=6 (dấu ẩn); ngược lại phát trị ×10000 thô + out_kind=3 → định dạng thập phân
          OP_ROI_THUC:begin out_data <= opB; out_valid <= 1; out_kind <= (stB==ST_AN) ? 3'd6 : 3'd3; sp <= sp - 8'd1; did_out[cur] <= 1'b1; end
          // in DANH-SÁCH số: PEEK (KHÔNG pop con trỏ) → duyệt heap đa-chu-kỳ ở S_DS
          OP_ROI_DS:  begin ds_a <= opB & UNTAG; state <= S_DS; end
          // CỘNG HƯỞNG: pop thực-tại b, đặt ô = (val niềm-tin a, TRẠNG-THÁI sáng/tối/ẩn theo γ)
          OP_SO_SANH: begin stack[sp-2] <= so_an_in ? {WORD{1'b0}} : opA; stk_st[sp-2] <= so_st; sp <= sp - 8'd1; end  // giữ niềm-tin a(=opA)
          // --- THỬ/BẮT (ngoại lệ) ---
          OP_BAT_DAU_THU: begin                            // mở vùng thử: pop địa chỉ 'bắt', lưu sâu các ngăn xếp
            h_ip[hsp] <= opB; h_sp[hsp] <= sp - 8'd1; h_fp[hsp] <= fp; h_rsp[hsp] <= rsp;   // opB=stack[sp-1]=địa chỉ 'bắt'
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
              end else begin out_data <= opB; out_valid <= 1; out_kind <= 3'd0; halt <= 1; end   // opB=trị-lỗi
            end else begin
              sp  <= h_sp[hsp-16'd1] + 16'd1;                // gỡ-cuộn độ sâu + chừa 1 ô trị-lỗi
              fp  <= h_fp[hsp-16'd1];
              rsp <= h_rsp[hsp-16'd1];
              stack[h_sp[hsp-16'd1]]  <= opB;                // trao trị-lỗi (opB=stack[sp-1]) cho nhánh 'bắt'
              stk_st[h_sp[hsp-16'd1]] <= ST_SANG;
              ip  <= h_ip[hsp-16'd1];
              hsp <= hsp - 16'd1;
            end
          end
          // so sánh (pop b,a; đẩy 1/0). Đọc val bỏ trạng-thái → kết quả LUÔN sáng (≡ phần mềm).
          OP_BANG:    begin stack[sp-2] <= (opA==opB) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_KHAC:    begin stack[sp-2] <= (opA!=opB) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_BE_HON:  begin stack[sp-2] <= ($signed(opA) <  $signed(opB)) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_LON_HON: begin stack[sp-2] <= ($signed(opA) >  $signed(opB)) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_BE_BANG: begin stack[sp-2] <= ($signed(opA) <= $signed(opB)) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_LON_BANG:begin stack[sp-2] <= ($signed(opA) >= $signed(opB)) ? 1:0; stk_st[sp-2] <= ST_SANG; sp <= sp-8'd1; end
          OP_NHAN_BAN:begin stack[sp] <= opB; stk_st[sp] <= stB; sp <= sp + 8'd1; end  // nhân bản opB/stB(=[sp-1]) kèm trạng-thái
          OP_BO:      begin                               sp <= sp - 8'd1; end
          // in: ẩn → out_kind=6 (dấu ẩn); ngược lại số out_kind=0
          OP_GOI_HE: begin
            // operand = SỐ ĐỐI (0..3). Ngăn xếp: [… , số_hiệu, đối0, đối1, đối2] — đỉnh là đối cuối.
            // Chỉ có 2 toán hạng được prefetch (opB=đỉnh, opA=kế) ⇒ ≥2 đối phải ĐỌC THÊM ở S_TRAPA.
            trap_n <= operand; trap_nargs <= operand; trap_k <= 8'd0;
            if (operand == 8'd0) begin
              trap_num <= opB[7:0]; trap_arg <= {WORD{1'b0}}; sp <= sp - 8'd1;
              trap_valid <= 1'b1; state <= S_TRAP;
            end else if (operand == 8'd1) begin
              trap_num <= opA[7:0]; trap_arg <= opB;          sp <= sp - 8'd2;
              trap_valid <= 1'b1; state <= S_TRAP;
            end else if (operand == 8'd2) begin
              trap_arg1 <= opB; trap_arg <= opA;              // số hiệu nằm ở sp-3 → đọc ở S_TRAPA
              state <= S_TRAPA;
            end else begin                                     // 3 đối
              trap_arg2 <= opB; trap_arg1 <= opA;              // đối0 ở sp-3, số hiệu ở sp-4
              state <= S_TRAPA;
            end
            did_out[cur] <= 1'b1;                             // ρ=1: gọi-hệ là làm việc thật
          end
          OP_ROI:     begin out_data <= opB; out_valid <= 1; out_kind <= (stB==ST_AN) ? 3'd6 : 3'd0; out_state <= stB; sp <= sp - 8'd1; did_out[cur] <= 1'b1; end
          OP_DOI:     begin stack[sp-1] <= opA; stk_st[sp-1] <= stA;   // hoán đỉnh↔kế-đỉnh: [sp-1]<=opA/stA giờ; [sp-2]<=opB/stB ở S_DOI2 (BRAM 1 cổng ghi)
                            state <= S_DOI2; end
          OP_XUAT:    begin out_data <= opB; out_valid <= 1; out_kind <= 3'd7; out_proc <= cur; sp <= sp - 8'd1; did_out[cur] <= 1'b1; end  // MMIO console (nhãn=cur)
          OP_ROI_CHUOI: begin str_a <= opB & UNTAG; sp <= sp - 8'd1; state <= S_STR; end  // duyệt heap, in từng ký tự (opB=con trỏ)
          OP_ROI_AUTO: begin                               // in TỰ-SUY-KIỂU lúc chạy (opB=stack[sp-1])
            if (stB == ST_AN) begin                        // ẩn → dấu ẩn (out_kind=6); stB=stk_st[sp-1]
              out_data <= opB; out_valid <= 1; out_kind <= 3'd6; sp <= sp - 8'd1; did_out[cur] <= 1'b1;
            end else if ((opB & 32'hC0000000) == 32'h40000000) begin   // con trỏ chuỗi (bit30=1,bit31=0)
              str_a <= opB & UNTAG; sp <= sp - 8'd1; state <= S_STR;
            end else begin                                 // số (kể cả 16-bit: luôn nhánh này)
              out_data <= opB; out_valid <= 1; out_kind <= 3'd0; sp <= sp - 8'd1; did_out[cur] <= 1'b1;
            end
          end
          OP_GOI_CLOSURE: begin                            // [đối0..đốiN-1, con-trỏ-closure], operand=N (opB=con trỏ closure)
            clo_cp   <= opB & UNTAG;                       // gỡ thẻ (ram_ra=opB&UNTAG → ram_q=ram[cp] cho S_CLOR1)
            clo_n    <= operand[7:0];
            clo_base <= sp - 8'd1 - operand[7:0];          // đáy khung = nơi đối0
            clo_k    <= 8'd0;
            rstk_ip[rsp] <= ip; rstk_fp[rsp] <= fp; rsp <= rsp + 8'd1;   // lưu điểm trả về
            sp       <= sp - 8'd1;                         // bỏ con trỏ closure
            state    <= S_CLOR1;
          end
          OP_NHAY:    begin ip <= { {(WORD-8){1'b0}}, operand }; end
          //   rẽ-nếu-0: ô ẩn KHÔNG kích nhánh (ẩn ≠ 0) — ≡ phần mềm `st != ẩn && val == 0`.
          OP_NHAY_0:  begin if (opB == 0 && stB != ST_AN) ip <= { {(WORD-8){1'b0}}, operand }; sp <= sp - 8'd1; end
          // RẼ theo TRẠNG-THÁI ba-trị (pop ô, nhảy nếu khớp mặt) — thay cờ ZF/CF bằng CỘNG HƯỞNG
          OP_NHAY_SANG: begin if (stB==ST_SANG) ip <= { {(WORD-8){1'b0}}, operand }; sp <= sp - 8'd1; end
          OP_NHAY_TOI:  begin if (stB==ST_TOI)  ip <= { {(WORD-8){1'b0}}, operand }; sp <= sp - 8'd1; end
          OP_NHAY_AN:   begin if (stB==ST_AN)   ip <= { {(WORD-8){1'b0}}, operand }; sp <= sp - 8'd1; end
          OP_DICH_TRAI: begin stack[sp-1] <= opB << operand; end                  // dịch trái opB(=stack[sp-1]) (trạng-thái giữ = lan-truyền ẩn)
          OP_NHAY_X:    begin ip <= opB; sp <= sp - 8'd1; end                      // nhảy tới địa chỉ ở đỉnh (opB)
          OP_NHAY_0_X:  begin if (opB == 0 && stB != ST_AN) ip <= opA;    // [target=opA, cond=opB/stB]; ẩn → không nhảy
                              sp <= sp - 8'd2; end
          // --- HEAP: nạp/lưu gián tiếp (địa chỉ 16-bit từ ngăn xếp) ---
          OP_TAI_GIAN:begin if (viol_s1) begin out_data<=16'd911; out_valid<=1; halt<=1; end
                            else begin state <= S_TAIG; end end  // ram_ra=rel_s1 → ram_q=ram[rel_s1]; S_TAIG ghi đỉnh
          OP_LUU_GIAN:begin if (viol_s2) begin out_data<=16'd911; out_valid<=1; halt<=1; end
                            else begin if (!dbg_we) ram[rel_s2] <= opB; sp <= sp - 8'd2; end end // relocated (ghi opB=stack[sp-1])
          // --- GỌI HÀM theo KHUNG: tham số nằm trên ngăn xếp; fp trỏ đáy khung ---
          OP_GOI_N: begin                                   // [arg0..argN-1, target], operand=N
            rstk_ip[rsp] <= ip; rstk_fp[rsp] <= fp; rsp <= rsp + 8'd1;
            fp <= sp - 8'd1 - operand[7:0];                 // đáy khung = nơi arg0 bắt đầu
            ip <= opB;                                      // nhảy tới target (opB=stack[sp-1])
            sp <= sp - 8'd1;                                // chỉ bỏ target; tham số ở lại làm khung
          end
          //   THAM_I LUÔN đẩy sáng: đọc ô khung stack[fp+i] (BRAM, trễ) → S_THAMI đẩy lên đỉnh.
          OP_THAM_I:  begin state <= S_THAMI; end  // stk_ra=fp+i → stack_q=stack[fp+i]; S_THAMI đẩy lên đỉnh
          OP_DANH_CB: begin sp <= sp + operand[7:0]; end                                 // dành n ô cục bộ cuối khung
          OP_LUU_THAM_I: begin stack[fp + operand[7:0]] <= opB; stk_st[fp + operand[7:0]] <= stB; sp <= sp - 8'd1; end  // ghi ô khung thứ i (opB/stB=[sp-1])
          OP_TRA_VE_N: begin                                // trị trả về ở đỉnh; gấp khung
            stack[fp] <= opB; stk_st[fp] <= stB;  // đặt kết quả opB/stB(=[sp-1]) (KÈM trạng-thái: hàm trả ẩn → ẩn)
            sp  <= fp + 8'd1;                               // bỏ toàn khung, chừa kết quả
            ip  <= rstk_ip_q;                               // khôi phục ip & fp người gọi (rstk_*_q = rstk[rsp-1], đọc-đăng-ký)
            fp  <= rstk_fp_q;
            rsp <= rsp - 8'd1;
          end
          // --- NGẮT TIMER phần cứng ---
          OP_BAT_NGAT: begin ivec <= opB; sp <= sp - 8'd1; ie <= 1'b1; end  // handler ở đỉnh (opB)
          OP_TAT_NGAT: begin ie <= 1'b0; end
          OP_HEN_GIO:  begin period <= { {(WORD-8){1'b0}}, operand }; timer <= 0; end // chu kỳ = operand
          OP_NGAT_VE:  begin ip <= saved_ip; in_isr <= 1'b0; end                      // IRET: quay về điểm bị ngắt
          // --- ĐA NHIỆM TIỀN-ĐỊNH ---
          OP_TAC_VU: begin                                                            // [entry_ip] → đăng ký task
            t_ip[ntask] <= opB;             // entry_ip = opB(=stack[sp-1])
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
        // RỌI_CHUỖI: duyệt cons-list mã-ký-tự. ĐỌC BRAM (trễ): yêu cầu ram[str_a] → S_STRC in.
        if (str_a == 0) begin
          out_data <= 0; out_valid <= 1; out_kind <= 2'd2;   // HẾT chuỗi
          did_out[cur] <= 1'b1; state <= S_FETCH;
        end else begin
          state <= S_STRC;                                   // ram_ra=str_a → ram_q=mã ký tự
        end
      end else if (state == S_STRC) begin
        out_data <= ram_q & 32'h1FFFFF; out_valid <= 1; out_kind <= 2'd1;  // in ký tự (21 bit thấp)
        state <= S_STRN;                                     // ram_ra=str_a+1 → ram_q=ô kế (cdr)
      end else if (state == S_STRN) begin
        str_a <= ram_q & UNTAG; state <= S_STR;              // sang ô kế (gỡ thẻ), lặp
      end else if (state == S_DS) begin
        // RỌI_DS: duyệt cons-list SỐ. ĐỌC BRAM (trễ) tương tự S_STR.
        if (ds_a == 0) begin
          out_data <= 0; out_valid <= 1; out_kind <= 3'd5;     // HẾT danh sách
          did_out[cur] <= 1'b1; state <= S_FETCH;
        end else begin
          state <= S_DSC;                                      // ram_ra=ds_a → ram_q=phần tử số
        end
      end else if (state == S_DSC) begin
        out_data <= ram_q; out_valid <= 1; out_kind <= 3'd4;   // in số (car)
        state <= S_DSN;                                        // ram_ra=ds_a+1 → ram_q=cons kế (cdr)
      end else if (state == S_DSN) begin
        ds_a <= ram_q & UNTAG; state <= S_DS;                  // sang cons kế (gỡ thẻ), lặp
      end else if (state == S_FOP) begin
        // TẦNG PIPELINE F-op: lấy |.| (negate) tích & ước-số (ĐÃ tách khỏi nhân ở S_EXEC) → nạp divider.
        div_neg <= fprod[63] ^ fdor_raw[63];                                       // dấu thương = dấu(tích) XOR dấu(ước)
        div_acc <= { 64'd0, (fprod[63]   ? (~fprod   + 64'd1) : fprod) };          // |số bị chia|
        div_dor <= fdor_raw[63] ? (~fdor_raw + 64'd1) : fdor_raw;                  // |ước số|
        div_i <= 7'd0; state <= S_DIV;
      end else if (state == S_MUL) begin
        stack[div_dst] <= nhan_r; stk_st[div_dst] <= ST_SANG; state <= S_FETCH;   // PIPELINE NHÂN: ghi tích (sáng)
      end else if (state == S_DIV) begin
        // CHIA TUẦN-TỰ (restoring): 64 vòng dịch-trừ; xong → ghi thương CÓ DẤU (slice WORD bit) rồi về FETCH.
        if (div_i < 7'd64) begin
          if (div_acc[126:63] >= div_dor)                                  // rem-sau-dịch ≥ ước số → trừ, bit thương = 1
            div_acc <= { (div_acc[126:63] - div_dor), div_acc[62:0], 1'b1 };
          else
            div_acc <= { div_acc[126:0], 1'b0 };                           // chỉ dịch trái (bit thương = 0)
          div_i <= div_i + 7'd1;
        end else begin
          stack[div_dst]  <= div_q_signed[WORD-1:0];                       // thương ×10000 thô (khít fmul_q/fdiv_q cũ)
          stk_st[div_dst] <= ST_SANG;
          state <= S_FETCH;
        end
      end else if (state == S_TAIO) begin
        stack[sp] <= ram_q; stk_st[sp] <= ST_SANG; sp <= sp + 8'd1; state <= S_FETCH;  // TẢI_Ô: đẩy ram_q (sáng)
      end else if (state == S_GHITRUONG) begin
        if (!dbg_we) ram[rel_s1] <= ram_q; state <= S_FETCH;   // ★ #3 store-field: ghi ram[top=rel_s1] = ram_q(=ram[r]). sp GIỮ (rel_s1 dùng opB còn-giữ).
      end else if (state == S_TAIG) begin
        stack[sp-1] <= ram_q; stk_st[sp-1] <= ST_SANG; state <= S_FETCH;               // TẢI_GIÁN: ghi đỉnh (sáng)
      end else if (state == S_CLOR1) begin
        clo_code <= ram_q; state <= S_CLOR2;             // ram[cp]→code; ram_ra=cp+1 → ram_q=ram[cp+1] cho S_CLOR2
      end else if (state == S_CLOR2) begin
        clo_ncap <= ram_q; state <= S_CLO;                                             // ram[cp+1]→ncap; vào dựng khung
      end else if (state == S_CLO) begin
        // GỌI_CLOSURE: dựng khung [bắt…, đối…] rồi nhảy mã closure
        if (clo_k < clo_n) begin
          // PHA 1: dịch ĐỐI — stk_ra=clo_base+(clo_n-1-clo_k) → stack_q=stack[src]; S_CLO1R ghi stack[dst] (KHÔNG tăng clo_k ở đây)
          state <= S_CLO1R;
        end else if (clo_k < clo_n + clo_ncap) begin
          state <= S_CLO2;  // PHA 2: ram_ra=cp+2+(clo_k-clo_n) → ram_q=BẮT từ heap; S_CLO2 ghi
        end else begin
          fp <= clo_base; sp <= clo_base + clo_ncap + clo_n;  // khung = [bắt…, đối…]
          ip <= clo_code; state <= S_FETCH;                   // nhảy vào mã closure
        end
      end else if (state == S_CLO1R) begin
        stack[clo_base + clo_ncap + (clo_n-8'd1-clo_k)] <= stack_q; clo_k <= clo_k + 8'd1; state <= S_CLO;  // PHA1 ghi dịch ĐỐI
      end else if (state == S_CLO2) begin
        stack[clo_base + (clo_k - clo_n)] <= ram_q; clo_k <= clo_k + 8'd1; state <= S_CLO;  // ghi BẮT, lặp PHA2
      end else if (state == S_THAMI) begin
        stack[sp] <= stack_q; stk_st[sp] <= ST_SANG; sp <= sp + 8'd1; state <= S_FETCH;     // THAM_I: đẩy ô khung (sáng)
      end else if (state == S_DOI2) begin
        stack[sp-2] <= opB; stk_st[sp-2] <= stB; state <= S_FETCH;                           // ĐỔI: ghi nốt [sp-2]<=opB/stB
      end else begin
        state <= S_FETCH;                                     // an toàn (state lạ)
      end
    end
  end
endmodule

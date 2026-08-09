`timescale 1ns/1ps
// ============================================================
// cosim_tb.v — ĐỒNG MÔ PHỎNG: CPU trên CỔNG LOGIC ⟷ NHÂN HĐH-GIAO THẬT (chạy ở tiến trình Python)
// ------------------------------------------------------------
// Testbench này KHÔNG tự phục vụ gọi-hệ nữa (đó là bản trap_tb.v). Nó chỉ làm BƯU TÁ:
//   1. thấy trap_valid  → gói số hiệu + đối (nếu đối là con trỏ chuỗi thì DUYỆT HEAP của chính CPU
//                          để lấy ra từng mã ký tự) → ghi vào `trap_req.txt`
//   2. chờ `trap_res.txt` có đúng số thứ tự ấy      → đọc kết quả nhân trả về
//   3. nếu kết quả là CHUỖI thì CẤP PHÁT vào heap của CPU (ram[250] = HEAP_PTR, ô cons [mã, đuôi])
//      rồi trả CON TRỎ; nếu là SỐ thì trả thẳng
//   4. bật trap_ack một chu kỳ → CPU chạy tiếp
// Nhờ vậy tiến trình chạy trên cổng logic xin việc của CHÍNH cái nhân GIAO, chịu đủ uid + quyền +
// cổng bất-khả-hồi + nhật ký audit — chứ không phải một testbench đóng giả.
// ============================================================
module cosim_tb;
  reg clk = 0, rst = 1;
  wire [31:0] out_data;  wire out_valid, halt;  wire [2:0] out_kind;
  wire        trap_valid; wire [7:0] trap_num, trap_nargs;
  wire [31:0] trap_arg, trap_arg1, trap_arg2;
  reg         trap_ack = 0; reg [31:0] trap_ret = 0;

  integer seq = 0, cyc = 0, fd = 0, i = 0, j = 0, k = 0, code = 0;
  reg [31:0] cur_arg;
  integer r_seq, r_kind, r_len, r_val;
  integer n_trap = 0;
  reg     da_gui = 0;   // ★ chống GỬI TRÙNG: trap_valid còn giữ 1 chu kỳ sau khi ack
  reg [31:0] a, hp, con, ch [0:1023];

  gvm #(.MEM(4096), .WORD(32)) dut(.clk(clk), .rst(rst),
        .out_data(out_data), .out_valid(out_valid), .out_kind(out_kind), .halt(halt),
        .dbg_a(16'd0), .dbg_re(1'b0), .dbg_we(1'b0), .dbg_wd(0),
        .trap_valid(trap_valid), .trap_num(trap_num), .trap_arg(trap_arg),
        .trap_arg1(trap_arg1), .trap_arg2(trap_arg2),
        .trap_nargs(trap_nargs), .trap_ack(trap_ack), .trap_ret(trap_ret));

  always #5 clk = ~clk;
  initial begin #12 rst = 0; #40000000 begin $display("   HET GIO"); $finish; end end
  always @(posedge clk) if (!rst) cyc = cyc + 1;

  // ── in ra những gì CPU RỌI ──
  // Giữ NGUYÊN mã Unicode rồi tự mã hoá UTF-8 khi in. (Bẫy đã gặp: cắt xuống 8 bit thì chữ tiếng
  // Việt thành byte rác — luồng đọc `vvp` phía Python chết vì giải mã hỏng, mất SẠCH mọi dòng in.)
  reg [31:0] obuf [0:1023]; integer olen = 0; reg [31:0] cp;
  always @(posedge clk) if (out_valid) begin
    if (out_kind == 3'd1) begin                    // ký tự của chuỗi
      obuf[olen] = out_data; olen = olen + 1;
    end else if (out_kind == 3'd2) begin           // hết chuỗi
      $write("   [CPU-silicon] ");
      for (i = 0; i < olen; i = i + 1) begin
        cp = obuf[i];
        if (cp < 32'h80) $write("%c", cp[7:0]);
        else if (cp < 32'h800) begin
          $write("%c", 8'hC0 | cp[10:6]);  $write("%c", 8'h80 | cp[5:0]);
        end else begin
          $write("%c", 8'hE0 | cp[15:12]); $write("%c", 8'h80 | cp[11:6]); $write("%c", 8'h80 | cp[5:0]);
        end
      end
      $write("\n"); olen = 0;
    end else $display("   [CPU-silicon] %0d", out_data);
  end

  // ── BƯU TÁ: trap → tệp → nhân GIAO thật → tệp → trap_ack ──
  // Dùng `wait` TƯỜNG MINH thay vì cờ chống-trùng: bắt tay đúng một lần cho mỗi trap.
  //   (Bẫy đã gặp: `always @(posedge clk)` + gán KHÔNG-CHẶN cho ack làm trap bị gửi HAI lần —
  //    nhân phục vụ hai lượt cho cùng một lời xin, số hiệu lệch hẳn đi.)
  initial forever begin
    wait (!rst && trap_valid);
    seq = seq + 1; n_trap = n_trap + 1;

    // (a)+(b) gói TỪNG ĐỐI: nếu là con trỏ chuỗi (bit30=1) thì duyệt heap CPU lấy mã ký tự.
    fd = $fopen("trap_req.txt", "w");
    $fwrite(fd, "%0d %0d %0d", seq, trap_num, trap_nargs);
    for (j = 0; j < trap_nargs; j = j + 1) begin
      cur_arg = (j == 0) ? trap_arg : ((j == 1) ? trap_arg1 : trap_arg2);
      k = 0;
      if ((cur_arg & 32'h40000000) != 0) begin
        a = cur_arg & 32'h3FFFFFFF;
        while (a != 0 && k < 1000) begin
          ch[k] = dut.ram[a] & 32'h1FFFFF; k = k + 1;
          a = dut.ram[a + 1] & 32'h3FFFFFFF;
        end
      end
      if (k > 0) begin
        $fwrite(fd, " 1 %0d", k);
        for (i = 0; i < k; i = i + 1) $fwrite(fd, " %0d", ch[i]);
      end else $fwrite(fd, " 0 1 %0d", cur_arg);      // SỐ: là_chuỗi=0, dài=1, giá trị
    end
    $fwrite(fd, "\n"); $fclose(fd);
    $display("   [silicon->nhan] chu ky %0d: xin goi-he so=%0d nargs=%0d", cyc, trap_num, trap_nargs);

    // (c) chờ nhân trả lời
    r_seq = -1;
    while (r_seq != seq) begin
      #200;
      fd = $fopen("trap_res.txt", "r");
      if (fd != 0) begin
        code = $fscanf(fd, "%d %d %d", r_seq, r_kind, r_len);
        if (code == 3 && r_seq == seq) begin
          if (r_kind == 1) begin                        // CHUỖI → cấp vào heap của CPU
            for (i = 0; i < r_len; i = i + 1) code = $fscanf(fd, "%d", ch[i]);
            hp = dut.ram[250]; if (hp < 300) hp = 300;
            con = 0;
            for (i = r_len - 1; i >= 0; i = i - 1) begin
              dut.ram[hp] = ch[i]; dut.ram[hp+1] = con;
              con = hp | 32'h40000000;                  // MỌI con trỏ mang THẺ (kể cả đuôi)
              hp = hp + 2;
            end
            dut.ram[250] = hp; trap_ret = con;
          end else begin
            code = $fscanf(fd, "%d", r_val); trap_ret = r_val;
          end
        end
        $fclose(fd);
      end
    end
    $display("   [nhan→silicon] chu ky %0d: nhan da phuc vu (kind=%0d)", cyc, r_kind);

    // (d) bắt tay ĐÚNG MỘT LẦN rồi đợi CPU thật sự nhận (trap_valid hạ)
    // `#1` đẩy phép gán RA KHỎI cạnh clock ⇒ không tranh chấp với chính CPU lấy mẫu ở cạnh ấy.
    @(posedge clk); #1 trap_ack = 1'b1;      // dựng ack
    @(posedge clk);                          // CPU lấy mẫu ack ở cạnh này
    @(posedge clk); #1 trap_ack = 1'b0;      // hạ sau khi CHẮC CHẮN đã được lấy mẫu
    wait (trap_valid == 0);
  end

  always @(posedge clk) if (halt) begin
    $display("   CPU DUNG sau %0d chu ky · %0d lan xin nhan", cyc, n_trap);
    fd = $fopen("trap_req.txt", "w"); $fwrite(fd, "-1 0 0 0 0 0\n"); $fclose(fd);  // báo nhân nghỉ
    $finish;
  end
endmodule

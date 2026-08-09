`timescale 1ns/1ps
module nhanp_tb;
  reg clk=0, rst=1; wire [15:0] od; wire ov, h; wire [2:0] ok; wire [7:0] proc;
  wire sevt, srho; wire [7:0] scur; integer ncyc=0;
  gvm #(.MEM(4096)) dut(.clk(clk),.rst(rst),.out_data(od),.out_valid(ov),.out_kind(ok),
                        .out_proc(proc),.sched_evt(sevt),.sched_cur(scur),.sched_rho(srho),.halt(h));
  always #5 clk = ~clk;
  initial begin #12 rst=0; end
  always @(posedge clk) begin
    if (!rst) ncyc = ncyc + 1;
    if (ov && (ok==3'd7 || ok==3'd0)) $display("XUAT proc=%0d val=%0d", proc, $signed(od));
    if (sevt) $display("SCHED cur=%0d rho=%0d", scur, srho);    // ★ vết quyết-định lập-lịch
    if (ncyc >= 6000) begin
      $display("SIGMA %0d %0d %0d", dut.sigma[0], dut.sigma[1], dut.sigma[2]);
      $display("NTASK %0d", dut.ntask);
      $finish;
    end
  end
endmodule

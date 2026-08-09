# -*- coding: utf-8 -*-
"""
lam_bo_mo_phong.py — chạy CHÍNH cái đỉnh sẽ nạp lên bo (`gvm_bo.v`) trong iverilog,
nối với nhân HĐH-GIAO thật qua **dây UART** (mô phỏng tới từng bit).
================================================================================
Đây là bước kiểm cuối trước khi cắm bo: nếu bản này chạy đúng thì bitstream sinh từ CÙNG mã nguồn
ấy cũng chạy đúng — chỉ khác cái đồng hồ và sợi cáp là thật.

    python hw/lam_bo_mo_phong.py
"""
import os, sys, socket, subprocess, shutil, time

GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW  = os.path.join(GỐC, "hw")
sys.path.insert(0, GỐC)
sys.path.insert(0, HW)
import giaoc
import nhan_qua_uart as nqu

NGUỒN = """
đặt tên = gọi_hệ(0, "/hệ/tên_máy")
rọi tên
đặt ghi = gọi_hệ(2, "/tạm/từ_bo", 644, "dòng này do BO FPGA viết")
rọi ghi
đặt hết = gọi_hệ(0, "/tạm/từ_bo")
rọi hết
đặt mk = gọi_hệ(0, "/hệ/mật_khẩu")
rọi mk
đặt x = gọi_hệ(6, "/tạm/rác")
rọi x
đặt ai = gọi_hệ(12)
rọi ai
"""


class ỐngSocket:
    "Ống byte tới bo ĐANG MÔ PHỎNG (qua VPI + socket)."
    def __init__(self, con): self.con = con
    def đọc(self, n):
        try: return self.con.recv(n)
        except (ConnectionResetError, OSError): return b""
    def ghi(self, b): self.con.sendall(b)


def chạy(kể=True):
    iv  = shutil.which("iverilog") or r"D:\iverilog\bin\iverilog.exe"
    vp  = shutil.which("vvp")      or r"D:\iverilog\bin\vvp.exe"
    gcc = shutil.which("gcc")      or r"D:\mingw64\mingw64\bin\gcc.exe"
    if not os.path.exists(iv) or not os.path.exists(gcc):
        print("⚠ cần iverilog + gcc — bỏ qua."); return 0
    IV_GỐC = os.path.dirname(os.path.dirname(iv))
    DỰNG = os.environ.get("GIAO_VPI_DUNG", HW)      # đường dẫn dự án nay KHÔNG DẤU ⇒ dlopen nuốt được
    os.makedirs(DỰNG, exist_ok=True)

    # 1) chương trình cho CPU trên bo
    words = giaoc.compile_program(giaoc.Parser(giaoc.tokenize(NGUỒN)).parse(), True)
    with open(os.path.join(HW, "program_bo.hex"), "w") as f:
        f.write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
    gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
    i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
    open(os.path.join(HW, "gvm_bo_rom.v"), "w", encoding="utf-8").write(
        gv[:i0] + '  initial $readmemh("program_bo.hex", rom);\n\n' + gv[i1:])
    if kể: print(f"chương trình cho bo: {len(words)} từ-lệnh (32-bit có thẻ)")

    # 2) module VPI (chỉ dựng lại khi .c đổi)
    VPI_RA, VPI_NG = os.path.join(DỰNG, "giao_vpi.vpi"), os.path.join(HW, "giao_vpi.c")
    if not os.path.exists(VPI_RA) or os.path.getmtime(VPI_RA) < os.path.getmtime(VPI_NG):
        r = subprocess.run([gcc, "-O2", "-shared", "-o", VPI_RA, "giao_vpi.c",
                            "-I", os.path.join(IV_GỐC, "include", "iverilog"),
                            "-L", os.path.join(IV_GỐC, "lib"), "-lvpi", "-lws2_32"],
                           capture_output=True, text=True, cwd=HW)
        if r.returncode != 0: print("dựng VPI hỏng:\n" + r.stdout + r.stderr); return 1

    r = subprocess.run([iv, "-o", "bo.vvp", "gvm_bo_rom.v", "uart.v", "gvm_bo.v", "bo_tb.v"],
                       capture_output=True, text=True, cwd=HW)
    if r.returncode != 0: print(r.stdout + r.stderr); return 1
    if kể: print("gvm_bo.v + uart.v + bo_tb.v → bo.vvp  (mô phỏng ĐÚNG cái đỉnh sẽ nạp lên bo)")

    # 3) nhân + cổng
    rt, G = nqu.dựng_nhân()
    srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0)); srv.listen(1)
    CỔNG = srv.getsockname()[1]
    if kể:
        print(f"nhân HĐH-GIAO nghe ở cổng {CỔNG}; tiến trình trên bo = tt{rt.glob['SILIC']}, uid 1000\n")
        print("════ CHẠY: bo (gvm_bo.v) ⟷ dây UART ⟷ nhân GIAO ════")

    NHẬT_KÝ = os.path.join(HW, "bo_log.txt")
    _log = open(NHẬT_KÝ, "w", encoding="utf-8")
    env = dict(os.environ, GIAO_CONG=str(CỔNG))
    t0 = time.time()
    proc = subprocess.Popen([vp, "-M" + DỰNG, "-mgiao_vpi", "bo.vvp"],
                            cwd=HW, stdout=_log, stderr=subprocess.STDOUT, env=env)
    srv.settimeout(60)
    try:
        con, _ = srv.accept()
    except socket.timeout:
        print("⚠ bo không nối tới nhân — xem bo_log.txt"); proc.kill(); return 1
    con.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    phiên = nqu.PhiênBo(ỐngSocket(con), rt, G, kể=kể)
    phiên.vòng()
    try: con.close()
    except OSError: pass
    srv.close()
    try: proc.wait(timeout=120)
    except subprocess.TimeoutExpired: proc.kill()
    _log.close()

    if kể:
        print("\n════ NHẬT KÝ BO (vvp) ════")
        with open(NHẬT_KÝ, encoding="utf-8", errors="replace") as f:
            for d in f:
                if d.strip() and "readmemh" not in d: print("   " + d.rstrip())
        print("\n════ HẬU KIỂM (hỏi lại nhân GIAO) ════")
        G('rọi "   /tạm/từ_bo = [" + gọi(M, KHỞI, GH_ĐỌC, ["/tạm/từ_bo"]) + "]"')
        G('rọi "   /tạm/rác còn không? " + loại(gọi(M, KHỞI, GH_SOI, ["/tạm/rác"])) + "  (danh_sách = CÒN)"')
        G('rọi "   nhật ký audit — việc tiến trình TRÊN BO đã xin:"')
        G('lặp d trong nhật_ký_gần(M, 16) { nếu d[1] == SILIC { rọi "      nhịp " + d[0] + "  tt" + d[1] + "  " + d[2] + "  " + d[3] } }')
        print(f"\n→ {phiên.n_xin} lời xin qua DÂY UART, {time.time() - t0:.1f}s mô phỏng.")
        print("  Cùng mã nguồn này tổng hợp ra bitstream thì chạy y hệt trên silicon.")
    return 0 if phiên.n_xin >= 6 else 1


if __name__ == "__main__":
    sys.exit(chạy())

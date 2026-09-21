# -*- coding: utf-8 -*-
"""
lam_cosim_vpi.py — ★★ ĐỒNG MÔ PHỎNG QUA **VPI**: bỏ điểm hẹn tệp, nhân GIAO thành hàm hệ thống
================================================================================
Bản `lam_cosim.py` cho cổng logic và nhân hẹn nhau qua TỆP: testbench phải `#200` rồi mở tệp dò
lại — mỗi lời xin đốt hàng nghìn chu kỳ mô phỏng CHỈ ĐỂ ĐỢI (lần đo: 2.327.815 chu kỳ cho 8 lời xin).

Nay dùng **VPI**: `hw/giao_vpi.c` cài `$giao_trap(...)` vào chính bộ mô phỏng. Lời gọi ấy chặn ngay
tại thời điểm mô phỏng đó — C duyệt thẳng `dut.ram[]` để lấy chuỗi đối, hỏi nhân GIAO thật qua
socket, cấp chuỗi trả về vào heap của CPU, rồi trả con trỏ. Không một chu kỳ nào bị đốt để đợi.

    python hw/lam_cosim_vpi.py
"""
import os, sys, socket, subprocess, shutil, time

GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW  = os.path.join(GỐC, "hw")
sys.path.insert(0, GỐC)
import giaoc
from giao import tokenize, Parser, Runtime, nạp_chuẩn

# ── 1) NHÂN HĐH-GIAO thật ──
rt = Runtime(); rt.base_dir = GỐC; rt.MAX_STEPS = 200_000_000
nạp_chuẩn(rt)
def G(mã): rt.exec_block(Parser(tokenize(mã)).parse())
G('nhập "lib_vỏ.giao"')
G('''
đặt M = khởi_máy()
thêm_người(M, 0, "gốc")  thêm_người(M, 1000, "an")
đặt KHỞI = sinh_tt(M, "khởi", 0, 0, "/")
gọi(M, KHỞI, GH_TẠO_THƯ, ["/hệ", 755])   gọi(M, KHỞI, GH_TẠO_THƯ, ["/tạm", 777])
gọi(M, KHỞI, GH_TẠO, ["/hệ/tên_máy", 644, "giao-01"])
gọi(M, KHỞI, GH_TẠO, ["/hệ/mật_khẩu", 600, "gốc:*"])
gọi(M, KHỞI, GH_TẠO, ["/tạm/rác", 666, "bỏ đi được"])
đặt SILIC = sinh_tt(M, "tt-silicon", 5, 1000, "/tạm")   # tiến trình chạy trên CỔNG LOGIC, uid 1000
''')
TID = rt.glob["SILIC"]
print("┌───────────────────────────────────────────────────────────────┐")
print("│  ĐỒNG MÔ PHỎNG QUA VPI — không còn điểm hẹn tệp               │")
print("└───────────────────────────────────────────────────────────────┘")
print(f"nhân: lib_gọi_hệ.giao (thông dịch) · tiến trình silicon = tt{TID}, uid 1000 ('an')\n")

def phục_vụ(số, đối):
    "Gọi CHÍNH `gọi(máy, tid, số, đối)` — nên uid/quyền/cổng/audit đều áp dụng."
    rt.glob["__số"] = số
    rt.glob["__đối"] = list(đối)
    G('đặt __kq = gọi(M, SILIC, __số, __đối)')
    G('đặt __lỗi = lỗi_cuối(M)')
    return rt.glob["__kq"], rt.glob["__lỗi"]

# ── 2) chương trình cho CPU silicon (gọi-hệ 0, 1, 2 và 3 đối) ──
NGUỒN = """
đặt tên = gọi_hệ(0, "/hệ/tên_máy")                       # 1 đối — đọc, được phép
rọi tên
đặt ghi = gọi_hệ(2, "/tạm/từ_silicon", 644, "dòng này do CỔNG LOGIC viết")   # ★ 3 ĐỐI — tạo tệp
rọi ghi
đặt lại = gọi_hệ(0, "/tạm/từ_silicon")                   # đọc lại chính tệp mình vừa tạo
rọi lại
đặt th = gọi_hệ(3, "/tạm/từ_silicon", " + thêm nữa")     # ★ 2 ĐỐI — nối thêm
rọi th
đặt hết = gọi_hệ(0, "/tạm/từ_silicon")
rọi hết
đặt mk = gọi_hệ(0, "/hệ/mật_khẩu")                       # uid 1000 sẽ BỊ CẤM
rọi mk
đặt x = gọi_hệ(6, "/tạm/rác")                            # xoá — vướng CỔNG BẤT-KHẢ-HỒI
rọi x
đặt ai = gọi_hệ(12)                                      # 0 đối — tôi là ai
rọi ai
"""
words = giaoc.compile_program(giaoc.Parser(giaoc.tokenize(NGUỒN)).parse(), True)   # 32-bit CÓ THẺ
with open(os.path.join(HW, "program_vpi.hex"), "w") as f:
    f.write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
print(f"chương trình cho silicon: {len(words)} từ-lệnh (32-bit có thẻ)\n")

gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_vpi.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("program_vpi.hex", rom);\n\n' + gv[i1:])

# ── 3) dựng module VPI (C) ──
iv  = shutil.which("iverilog") or r"D:\iverilog\bin\iverilog.exe"
vp  = shutil.which("vvp")      or r"D:\iverilog\bin\vvp.exe"
gcc = shutil.which("gcc")      or r"D:\mingw64\mingw64\bin\gcc.exe"
if not os.path.exists(iv):  print("⚠ chưa có iverilog — dừng.");         sys.exit(0)
if not os.path.exists(gcc): print("⚠ chưa có gcc (cần dựng VPI) — dừng."); sys.exit(0)
IV_GỐC = os.path.dirname(os.path.dirname(iv))

# `vvp` nạp module VPI bằng dlopen ANSI ⇒ đường dẫn dự án PHẢI KHÔNG DẤU. Từ 2026-07-29 dự án
# nằm ở E:\HeDieuHanh\GIAO nên dựng thẳng cạnh mã nguồn được, không phải chép đi đâu nữa.
DỰNG = os.environ.get("GIAO_VPI_DUNG", HW)
os.makedirs(DỰNG, exist_ok=True)

VPI_RA = os.path.join(DỰNG, "giao_vpi.vpi")
VPI_NGUỒN = os.path.join(HW, "giao_vpi.c")
cần_dựng = (not os.path.exists(VPI_RA)
            or os.path.getmtime(VPI_RA) < os.path.getmtime(VPI_NGUỒN))
if cần_dựng:
    r = subprocess.run([gcc, "-O2", "-shared", "-o", VPI_RA, "giao_vpi.c",
                        "-I", os.path.join(IV_GỐC, "include", "iverilog"),
                        "-L", os.path.join(IV_GỐC, "lib"), "-lvpi", "-lws2_32"],
                       capture_output=True, text=True, cwd=HW)
    if r.returncode != 0: print("dựng VPI hỏng:\n" + r.stdout + r.stderr); sys.exit(1)
print(f"1) giao_vpi.c → {VPI_RA}  (module VPI" + (" — vừa dựng)" if cần_dựng else " — dùng lại bản cũ)"))

r = subprocess.run([iv, "-o", "gvm_vpi.vvp", "gvm_vpi.v", "cosim_vpi_tb.v"],
                   capture_output=True, text=True, cwd=HW)
if r.returncode != 0: print(r.stdout + r.stderr); sys.exit(1)
print("2) gvm.v + cosim_vpi_tb.v → gvm_vpi.vvp")

# ── 4) mở cổng cho nhân, chạy mô phỏng ──
srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", 0)); srv.listen(1)
CỔNG = srv.getsockname()[1]
print(f"3) nhân GIAO nghe ở cổng {CỔNG} (điểm hẹn = SOCKET, không phải tệp)\n")

NHẬT_KÝ = os.path.join(HW, "vpi_log.txt")
_log = open(NHẬT_KÝ, "w", encoding="utf-8")
env = dict(os.environ, GIAO_CONG=str(CỔNG))
t0 = time.time()
proc = subprocess.Popen([vp, "-M" + DỰNG, "-mgiao_vpi", "gvm_vpi.vvp"],
                        cwd=HW, stdout=_log, stderr=subprocess.STDOUT, env=env)

print("════ CHẠY: cổng logic ⟷ nhân GIAO (qua VPI) ════")
srv.settimeout(60)
try:
    con, _ = srv.accept()
except socket.timeout:
    print("⚠ bộ mô phỏng không nối tới nhân — xem vpi_log.txt"); proc.kill(); sys.exit(1)
con.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

đệm, n_xin = b"", 0
while True:
    while b"\n" not in đệm:
        try:
            k = con.recv(65536)
        except ConnectionResetError:        # bộ mô phỏng $finish ⇒ Windows đá socket
            k = b""
        if not k: break
        đệm += k
    if b"\n" not in đệm: break                      # bộ mô phỏng đã đóng ⇒ CPU dừng
    dòng, đệm = đệm.split(b"\n", 1)
    t = dòng.decode("utf-8").split()
    if not t: continue
    số, nargs = int(t[0]), int(t[1])
    đối, p = [], 2
    for _ in range(nargs):                          # mỗi đối: "là_chuỗi độ_dài mã…"
        là_ch, dài = int(t[p]), int(t[p + 1]); p += 2
        phần = t[p:p + dài]; p += dài
        đối.append("".join(chr(int(c)) for c in phần) if là_ch else int(phần[0]))

    kq, lỗi = phục_vụ(số, đối)
    n_xin += 1
    if isinstance(kq, list): kq = " ".join(str(x) for x in kq)
    if isinstance(kq, str) and kq not in ("sáng", "tối"):
        trả = f"1 {len(kq)} " + " ".join(str(ord(c)) for c in kq)
    else:
        v = 1 if kq == "sáng" else (0 if kq == "tối" else (-1 if not isinstance(kq, (int, float)) else int(kq)))
        trả = f"0 1 {v & 0xFFFFFFFF}"
    con.sendall((trả + "\n").encode("utf-8"))
    nhãn = kq if not isinstance(kq, str) or len(str(kq)) < 44 else str(kq)[:44] + "…"
    print(f"   [NHÂN GIAO ] #{n_xin} gọi-hệ {số} đối={đối} → {nhãn}" + (f"   ({lỗi})" if lỗi else ""))

con.close(); srv.close()
proc.wait(timeout=60)
_log.close()
GIÂY = time.time() - t0

print("\n════ NHẬT KÝ CỔNG LOGIC (vvp) ════")
with open(NHẬT_KÝ, encoding="utf-8", errors="replace") as f:
    for dòng in f:
        if dòng.strip() and "readmemh" not in dòng: print(dòng.rstrip())

# ── 5) hậu kiểm bằng CHÍNH nhân ──
print("\n════ HẬU KIỂM (hỏi lại nhân GIAO) ════")
G('rọi "   /tạm/từ_silicon = [" + gọi(M, KHỞI, GH_ĐỌC, ["/tạm/từ_silicon"]) + "]"')
G('rọi "   /tạm/rác còn không? " + loại(gọi(M, KHỞI, GH_SOI, ["/tạm/rác"])) + "  (danh_sách = CÒN)"')
G('rọi "   nhật ký audit — những việc tiến trình SILICON đã xin:"')
G('lặp d trong nhật_ký_gần(M, 16) { nếu d[1] == SILIC { rọi "      nhịp " + d[0] + "  tt" + d[1] + "  " + d[2] + "  " + d[3] } }')
print(f"\n→ {n_xin} lời xin, xong trong {GIÂY:.1f}s. Điểm hẹn là VPI + socket: mỗi lời xin tốn")
print("  ĐÚNG 2 chu kỳ mô phỏng (bắt tay trap_valid/trap_ack), không chu kỳ nào bị đốt để đợi.")

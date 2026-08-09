# -*- coding: utf-8 -*-
"""
lam_cosim.py — ★★★★★ ĐỒNG MÔ PHỎNG: tiến trình chạy trên CỔNG LOGIC xin việc của NHÂN HĐH-GIAO THẬT
================================================================================
Trước đây "nhân" phục vụ trap là một testbench đóng giả. Nay là NHÂN THẬT:
    CPU gate-level (iverilog chạy hw/gvm.v, dựng từ NAND)
        ⟷  điểm hẹn tệp trap_req.txt / trap_res.txt  ⟷
    NHÂN HĐH-GIAO (lib_gọi_hệ.giao chạy trên trình thông dịch, trong tiến trình Python này)

Nên tiến trình trên silicon chịu ĐÚNG mọi thứ mà tiến trình phần mềm phải chịu:
uid · quyền rwx · cổng BẤT-KHẢ-HỒI · nhật ký audit.

    python hw/lam_cosim.py
"""
import os, sys, subprocess, shutil, time, threading

GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW  = os.path.join(GỐC, "hw")
sys.path.insert(0, GỐC)
import giaoc
from giao import tokenize, Parser, Runtime, nạp_chuẩn

REQ = os.path.join(HW, "trap_req.txt")
RES = os.path.join(HW, "trap_res.txt")
for f in (REQ, RES):
    try:
        if os.path.exists(f): os.remove(f)
    except OSError:                      # lần chạy trước còn giữ tệp — ghi đè là đủ
        open(f, "w").close()

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
print("│  ĐỒNG MÔ PHỎNG — cổng logic xin việc của NHÂN HĐH-GIAO THẬT   │")
print("└───────────────────────────────────────────────────────────────┘")
print(f"nhân: lib_gọi_hệ.giao (thông dịch) · tiến trình silicon = tt{TID}, uid 1000 ('an')\n")

def phục_vụ(số, đối):
    "Gọi CHÍNH `gọi(máy, tid, số, đối)` — nên uid/quyền/cổng/audit đều áp dụng."
    rt.glob["__số"] = số
    rt.glob["__đối"] = list(đối)
    G('đặt __kq = gọi(M, SILIC, __số, __đối)')
    kq = rt.glob["__kq"]
    G('đặt __lỗi = lỗi_cuối(M)')
    return kq, rt.glob["__lỗi"]

# ── 2) chương trình cho CPU silicon (tập con máy; gọi-hệ 0, 1, 2 và 3 đối) ──
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
with open(os.path.join(HW, "program_cosim.hex"), "w") as f:
    f.write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
print(f"chương trình cho silicon: {len(words)} từ-lệnh (32-bit có thẻ)")
for d in NGUỒN.strip().splitlines():
    if d.strip().startswith("đặt") or d.strip().startswith("rọi"): print("   " + d.strip())
print()

gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
open(os.path.join(HW, "gvm_cosim.v"), "w", encoding="utf-8").write(
    gv[:i0] + '  initial $readmemh("program_cosim.hex", rom);\n\n' + gv[i1:])

iv = shutil.which("iverilog") or r"D:\iverilog\bin\iverilog.exe"
vp = shutil.which("vvp") or r"D:\iverilog\bin\vvp.exe"
if not os.path.exists(iv):
    print("⚠ chưa có iverilog — dừng."); sys.exit(0)
r = subprocess.run([iv, "-o", "gvm_cosim.vvp", "gvm_cosim.v", "cosim_tb.v"],
                   capture_output=True, text=True, cwd=HW)
if r.returncode != 0: print(r.stdout + r.stderr); sys.exit(1)

# ── 3) chạy mô phỏng + phục vụ trap song song ──
print("════ CHẠY: cổng logic ⟷ nhân GIAO ════")
# vvp GHI THẲNG RA TỆP (không qua ống): ống bị đệm khối, luồng đọc dễ mất sạch dữ liệu.
NHẬT_KÝ = os.path.join(HW, "cosim_log.txt")
_log = open(NHẬT_KÝ, "w", encoding="utf-8")
proc = subprocess.Popen([vp, "gvm_cosim.vvp"], cwd=HW, stdout=_log, stderr=subprocess.STDOUT)

đã_phục_vụ = set()
t0 = time.time()
while proc.poll() is None and time.time() - t0 < 180:
    try:
        with open(REQ, encoding="utf-8") as f: dòng = f.read().split()
    except (OSError, ValueError):
        time.sleep(0.01); continue
    if len(dòng) < 3: time.sleep(0.01); continue
    seq = int(dòng[0])
    if seq < 0: break                                  # CPU đã dừng
    if seq in đã_phục_vụ: time.sleep(0.005); continue
    số, nargs = int(dòng[1]), int(dòng[2])
    # mỗi đối: "là_chuỗi độ_dài mã…"  (số ⇒ là_chuỗi=0, độ_dài=1, giá trị)
    đối, p_ = [], 3
    try:
        for _ in range(nargs):
            là_ch, n = int(dòng[p_]), int(dòng[p_ + 1]); p_ += 2
            phần = dòng[p_:p_ + n]; p_ += n
            đối.append("".join(chr(int(c)) for c in phần) if là_ch else int(phần[0]))
    except (IndexError, ValueError):
        time.sleep(0.01); continue
    kq, lỗi = phục_vụ(số, đối)

    if isinstance(kq, list):                    # danh sách (liệt/soi/ai) → ghép thành MỘT chuỗi
        kq = " ".join(str(x) for x in kq)
    if isinstance(kq, str) and kq not in ("sáng", "tối"):
        mã_kq, tải = 1, [str(len(kq))] + [str(ord(c)) for c in kq]
    else:
        v = 1 if kq == "sáng" else (0 if kq == "tối" else (-1 if not isinstance(kq, (int, float)) else int(kq)))
        mã_kq, tải = 0, ["1", str(v & 0xFFFFFFFF)]
    tmp = RES + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(f"{seq} {mã_kq} " + " ".join(tải) + "\n")
    for _ in range(200):            # vvp có thể đang MỞ trap_res.txt để đọc → Windows chặn thay tệp
        try:
            os.replace(tmp, RES); break
        except PermissionError:
            time.sleep(0.005)
    đã_phục_vụ.add(seq)
    nhãn = kq if not isinstance(kq, str) or len(str(kq)) < 40 else str(kq)[:40] + "…"
    print(f"   [NHÂN GIAO ] #{seq} gọi-hệ {số} đối={đối} → {nhãn}" + (f"   ({lỗi})" if lỗi else ""))

proc.wait(timeout=30)
time.sleep(0.2)
_log.close()
print("\n════ NHẬT KÝ CỔNG LOGIC (vvp) ════")
with open(NHẬT_KÝ, encoding="utf-8", errors="replace") as f:
    for dòng in f:
        if dòng.strip() and "readmemh" not in dòng: print(dòng.rstrip())

# ── 4) hậu kiểm bằng CHÍNH nhân ──
print("\n════ HẬU KIỂM (hỏi lại nhân GIAO) ════")
G('rọi "   /tạm/từ_silicon = [" + gọi(M, KHỞI, GH_ĐỌC, ["/tạm/từ_silicon"]) + "]"')
G('rọi "   /tạm/rác còn không? " + loại(gọi(M, KHỞI, GH_SOI, ["/tạm/rác"])) + "  (danh_sách = CÒN)"')
G('rọi "   nhật ký audit — những việc tiến trình SILICON đã xin:"')
G('lặp d trong nhật_ký_gần(M, 16) { nếu d[1] == SILIC { rọi "      nhịp " + d[0] + "  tt" + d[1] + "  " + d[2] + "  " + d[3] } }')
print("\n→ Tiến trình chạy trên CỔNG LOGIC đã xin việc của chính nhân HĐH-GIAO, và chịu đủ")
print("  uid · quyền rwx · cổng bất-khả-hồi · nhật ký audit — như mọi tiến trình khác.")

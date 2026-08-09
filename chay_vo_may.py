# -*- coding: utf-8 -*-
"""
chay_vo_may.py — ★★ VỎ LỆNH CHẠY TRÊN MÁY: nạp `vỏ_máy.giao` → bytecode GVM → chạy như TIẾN TRÌNH
================================================================================
Python ở đây lại chỉ làm BỘ ĐIỀU KHIỂN ĐĨA: đọc tệp nguồn của vỏ từ đĩa thật rồi đưa vào HĐH
(giống Linux nạp /bin/sh từ đĩa). Toàn bộ phần còn lại — biên dịch, sinh tiến trình, lập lịch,
phục vụ gọi-hệ — nằm trong GIAO.

    python chay_vo_may.py
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from giao import tokenize, Parser, Runtime, nạp_chuẩn

rt = Runtime(); rt.base_dir = HERE
rt.MAX_STEPS = 200_000_000
rt.cấp_quyền("máy")                      # HĐH được phép nạp bytecode lên GVM + cướp CPU
nạp_chuẩn(rt)

def G(mã): rt.exec_block(Parser(tokenize(mã)).parse())

G('nhập "lib_vỏ.giao"\nnhập "lib_chương_trình.giao"')

# ── dựng một máy nhỏ ──
G('''
đặt M = khởi_máy()
thêm_người(M, 0, "gốc")  thêm_người(M, 1000, "an")
đặt KHỞI = sinh_tt(M, "khởi", 0, 0, "/")
gọi(M, KHỞI, GH_TẠO_THƯ, ["/hệ", 755])   gọi(M, KHỞI, GH_TẠO_THƯ, ["/tạm", 777])
gọi(M, KHỞI, GH_TẠO_THƯ, ["/nhà", 755])
gọi(M, KHỞI, GH_TẠO, ["/hệ/tên_máy", 644, "giao-01"])
gọi(M, KHỞI, GH_TẠO, ["/hệ/mật_khẩu", 600, "gốc:*"])
gọi(M, KHỞI, GH_TẠO, ["/tạm/rác", 666, "bỏ đi được"])
gọi(M, KHỞI, GH_TẠO, ["/tạm/ghi_chú", 644, "dòng của người"])
nạp_chương_trình(M)
bật_lịch_γ(M, sáng)
đặt_lượng_tử(M, 400)
đặt VỎ_NGƯỜI = sinh_tt(M, "vỏ", 5, 1000, "/tạm")
''')

# ── NẠP NGUỒN VỎ TỪ ĐĨA (việc duy nhất của Python ở đây) ──
with open(os.path.join(HERE, "vỏ_máy.giao"), encoding="utf-8") as f:
    nguồn_vỏ = f.read()
rt.glob["__nguồn_vỏ"] = nguồn_vỏ
G('đăng_ký_ct_máy(M, "vỏ_máy", __nguồn_vỏ)')

print("┌───────────────────────────────────────────────────────────────┐")
print("│  HĐH-GIAO — VỎ LỆNH CHẠY BẰNG BYTECODE trên máy GVM           │")
print("└───────────────────────────────────────────────────────────────┘")
print(f"nguồn vỏ: {len(nguồn_vỏ)} ký tự  →  biên dịch xuống GVM khi `sinh`")

# ── xếp sẵn mấy dòng lệnh cho vỏ máy xử lý ──
LỆNH = ["tôi", "ở", "đếm_từ một hai ba", "xem /hệ/tên_máy", "liệt /tạm", "soi /tạm/ghi_chú",
        "xem /hệ/mật_khẩu", "xoá /tạm/rác", "ghi /tạm/vm_ghi xong-rồi",
        "xem /tạm/vm_ghi", "múa hát"]
for l in LỆNH:
    rt.glob["__dòng"] = l
    G('xếp_lệnh(M, __dòng)')
print(f"đã xếp {len(LỆNH)} dòng lệnh vào hàng đợi của nhân\n")

for l in LỆNH: print("   $", l)
print()

G('đặt_khoá(M, "kể", sáng)')
G('đặt S = gọi(M, VỎ_NGƯỜI, GH_SINH, ["vỏ_máy", 5])')
print(f"── sinh vỏ máy = tiến-trình tt{rt.glob['S']} (uid 1000, kế thừa từ vỏ của \"an\") ──\n")
G('đặt _lát = chạy_tới_hết(M, 900)')

G('rọi ""')
G('rọi "── tổng kết ──"')
G('rọi "vỏ máy đã tiêu " + lệnh_đã_chạy(M, S) + " lệnh máy · " + γ_soi(M, S)[2] + " lát CPU · σ=" + γ_soi(M, S)[0]')
G('rọi "/tạm/rác còn không? " + loại(gọi(M, KHỞI, GH_SOI, ["/tạm/rác"]))')
G('rọi "/tạm/vm_ghi = " + gọi(M, KHỞI, GH_ĐỌC, ["/tạm/vm_ghi"])')
G('rọi ""')
G('rọi "→ Vòng lặp phân giải lệnh của vỏ này là BYTECODE chạy trên GVM. Nó bị cắt CPU theo lượng tử,"')
G('rọi "  bị lịch γ xếp hàng, và chỉ chạm được thế giới qua opcode GỌI_HỆ — nên vẫn dính đủ mọi cổng."')

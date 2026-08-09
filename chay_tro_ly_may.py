# -*- coding: utf-8 -*-
"""
chay_tro_ly_may.py — ★★★ TRÁI TIM THÀNH THIẾT BỊ: lõi quyết định của trợ lý chạy bằng BYTECODE
================================================================================
Trái tim là mạng nơ-ron ⇒ không bao giờ là bytecode GVM được. Nên nó được phơi ra như THIẾT BỊ:
    gọi_hệ(27, "chữ")       → SỐ HIỆU vector (vector ở nhân)
    gọi_hệ(28, sh_a, sh_b)  → γ × 1000
Phần QUYẾT ĐỊNH — chấm điểm, chọn, áp ngưỡng, từ chối — nay là bytecode chạy trên GVM.
    tim CẢM · máy XÉT · nhân LÀM (quyền + cổng bất-khả-hồi vẫn nguyên)

    python chay_tro_ly_may.py
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from giao import tokenize, Parser, Runtime, nạp_chuẩn

rt = Runtime(); rt.base_dir = HERE
rt.MAX_STEPS = 200_000_000
rt.cấp_quyền("máy")
nạp_chuẩn(rt)
def G(mã): rt.exec_block(Parser(tokenize(mã)).parse())

G('nhập "lib_vỏ.giao"\nnhập "lib_chương_trình.giao"')
G('''
đặt M = khởi_máy()
thêm_người(M, 0, "gốc")  thêm_người(M, 1000, "an")
đặt KHỞI = sinh_tt(M, "khởi", 0, 0, "/")
gọi(M, KHỞI, GH_TẠO_THƯ, ["/hệ", 755])  gọi(M, KHỞI, GH_TẠO_THƯ, ["/tạm", 777])
gọi(M, KHỞI, GH_TẠO_THƯ, ["/tb", 755])
gọi(M, KHỞI, GH_GẮN_TB, ["/tb/tim", 444, "tim"])
gọi(M, KHỞI, GH_TẠO, ["/hệ/nhật_ký", 644, "nhịp 2  đĩa: /tạm đầy 91%"])
gọi(M, KHỞI, GH_TẠO, ["/tạm/rác1", 666, "x"])  gọi(M, KHỞI, GH_TẠO, ["/tạm/rác2", 666, "y"])
nạp_chương_trình(M)
đặt_lượng_tử(M, 400)
bật_lịch_γ(M, sáng)
đặt VỎ = sinh_tt(M, "vỏ", 5, 1000, "/tạm")
''')

with open(os.path.join(HERE, "trợ_lý_máy.giao"), encoding="utf-8") as f:
    nguồn = f.read()
rt.glob["__nguồn_tl"] = nguồn
G('đăng_ký_ct_máy(M, "trợ_lý_máy", __nguồn_tl)')

print("┌───────────────────────────────────────────────────────────────┐")
print("│  HĐH-GIAO — TIM LÀ THIẾT BỊ, phần QUYẾT ĐỊNH chạy bằng bytecode│")
print("└───────────────────────────────────────────────────────────────┘")
G('đặt _mồi = nhúng("mồi tim")')          # đập một nhịp để `/tb/tim` soi được backend thật
G('rọi "trái tim (soi qua thiết bị /tb/tim): " + gọi(M, KHỞI, GH_ĐỌC, ["/tb/tim"])')
print(f"nguồn lõi trợ lý: {len(nguồn)} ký tự → bytecode GVM\n")

LỜI = ["xem nhật ký hệ thống có gì bất thường không",
       "trong thư mục tạm đang có những tệp nào",
       "cho tôi biết tôi đang là ai",
       "làm giúp tôi một bài thơ về mùa thu Hà Nội"]
for l in LỜI:
    rt.glob["__l"] = l
    G('xếp_lệnh(M, __l)')
print("bốn lời nhờ đã xếp hàng:")
for l in LỜI: print("   ·", l)
print("\n════ Lõi trợ lý (BYTECODE) tự chấm γ, tự chọn, tự từ chối ════")
print("   (mỗi lời: ba số đầu là γ×1000 của ba kỹ năng, rồi tới kết quả; −1 = TỪ CHỐI)\n")

G('đặt_khoá(M, "kể", sáng)')
G('đặt TL = gọi(M, VỎ, GH_SINH, ["trợ_lý_máy", 5])')
G('đặt _ = chạy_tới_hết(M, 600)')

print()
G('rọi "── tổng kết ──"')
G('rọi "lõi trợ lý đã tiêu " + lệnh_đã_chạy(M, TL) + " lệnh máy · " + γ_soi(M, TL)[2] + " lát CPU · σ=" + γ_soi(M, TL)[0]')
G('rọi "số vector tim đã cấp cho máy: " + dài(lấy_khoá(M, "kho_vector"))')
G('rọi ""')
G('rọi "→ Máy KHÔNG hề thấy vector — nó chỉ cầm SỐ HIỆU và hỏi nhân γ. Nhưng phần quyết định"')
G('rọi "  (chấm điểm · chọn · áp ngưỡng · từ chối) đã là bytecode chạy trên máy dựng từ NAND."')

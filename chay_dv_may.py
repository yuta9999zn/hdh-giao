# -*- coding: utf-8 -*-
"""
chay_dv_may.py — ★★★ DỊCH VỤ NỀN CHẠY BẰNG BYTECODE: ngủ chờ tin, dậy làm việc, ngủ tiếp
================================================================================
Chứng minh tiến trình MÁY biết NGỦ như một daemon thật (không quay vòng bận):
  • `gọi_hệ(19)` (nhận) mà hộp thư rỗng → nhân trả −1 VÀ đỗ tiến trình sang trạng "chặn"
  • ai `gửi` tin → nhân đánh thức → máy chạy tiếp NGAY SAU trap, ghi nhật ký, rồi ngủ lại
Python chỉ đọc tệp nguồn từ đĩa (bộ điều khiển đĩa), phần còn lại nằm trong GIAO.

    python chay_dv_may.py
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
gọi(M, KHỞI, GH_TẠO, ["/hệ/nhật_ký", 644, "nhịp 0  khởi: nhân lên"])
nạp_chương_trình(M)
bật_lịch_γ(M, sáng)
đặt_lượng_tử(M, 300)
''')

with open(os.path.join(HERE, "nhật_ký_máy.giao"), encoding="utf-8") as f:
    nguồn = f.read()
rt.glob["__nguồn_dv"] = nguồn
G('đăng_ký_ct_máy(M, "nhật_ký_máy", __nguồn_dv)')

print("┌───────────────────────────────────────────────────────────────┐")
print("│  HĐH-GIAO — DỊCH VỤ NỀN chạy bằng BYTECODE, biết NGỦ như daemon│")
print("└───────────────────────────────────────────────────────────────┘")
print(f"nguồn dịch vụ: {len(nguồn)} ký tự → bytecode GVM\n")

def trạng(tid_biến):
    G(f'đặt __ts = trạng(lấy_khoá(M, "nhân"), {tid_biến})')
    return rt.glob["__ts"]

print("════ 1. Sinh dịch vụ MÁY rồi quay nhân — nó phải TỰ NGỦ ════")
G('đặt_khoá(M, "kể", sáng)')
G('đặt DV = gọi(M, KHỞI, GH_SINH, ["nhật_ký_máy", 3])')
G('đặt _ = vòng_nhân(M, 6)')
print(f"   → sau 6 lát: tt{rt.glob['DV']} trạng = {trạng('DV')}   (ngủ, KHÔNG đốt CPU)")
G('rọi "   lát CPU đã tiêu: " + γ_soi(M, DV)[2] + " · lệnh máy: " + lệnh_đã_chạy(M, DV)')

print("\n════ 2. Quay nhân thêm 10 lát nữa — dịch vụ vẫn ngủ, không tốn lát nào ════")
G('đặt _ = vòng_nhân(M, 10)')
G('rọi "   lát CPU vẫn là: " + γ_soi(M, DV)[2] + " (không tăng) · trạng = " + trạng(lấy_khoá(M, "nhân"), DV)')

print("\n════ 3. GỬI TIN → nhân đánh thức → dịch vụ dậy ghi rồi NGỦ LẠI ════")
for tin in ["đĩa /tạm sắp đầy", "mạng chập chờn", "có người đăng nhập"]:
    rt.glob["__tin"] = tin
    G('gọi(M, KHỞI, GH_GỬI, [DV, __tin])')
    G('đặt _ = vòng_nhân(M, 8)')
    G(f'rọi "   sau khi gửi: trạng = " + trạng(lấy_khoá(M, "nhân"), DV) + " · lát = " + γ_soi(M, DV)[2]')

print("\n════ 4. NHẬT KÝ HỆ — do BYTECODE ghi, qua đúng cổng gọi-hệ ════")
G('lặp d trong tách(gọi(M, KHỞI, GH_ĐỌC, ["/hệ/nhật_ký"]), "\\n") { nếu dài(d) > 0 { rọi "   " + d } }')

print("\n════ 5. Tổng kết ════")
G('rọi "   dịch vụ đã tiêu " + lệnh_đã_chạy(M, DV) + " lệnh máy trong " + γ_soi(M, DV)[2] + " lát CPU"')
G('rọi "   σ (độ hữu ích học được) = " + γ_soi(M, DV)[0] + " · trạng cuối = " + trạng(lấy_khoá(M, "nhân"), DV)')
G('rọi ""')
G('rọi "→ Daemon thật: ngủ trên hàng đợi, dậy đúng lúc có việc, ghi qua nhân, rồi ngủ tiếp —"')
G('rọi "  mà thân của nó là bytecode chạy trên chính cái máy dựng từ NAND."')

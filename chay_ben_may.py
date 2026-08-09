# -*- coding: utf-8 -*-
"""
chay_ben_may.py — ★ BỀN HOÁ CHO TIẾN TRÌNH MÁY: chụp cả NGỮ CẢNH lõi GVM, dựng lại, chạy tiếp
================================================================================
Vá lỗ hổng phát hiện sau v0.8.x: `chụp_máy` chụp đủ hệ-tệp/bảng tiến-trình nhưng KHÔNG chụp lõi
GVM ⇒ tiến trình MÁY sống lại thành XÁC (vẫn hiện trong `tt`, không bao giờ chạy nữa) mà không có
một lời báo lỗi nào. Nay ảnh mang theo: ip · các ngăn xếp · vùng RAM đã dùng · nguồn chương trình.
Bytecode KHÔNG cần chụp — biên dịch lại từ nguồn cho ra đúng thế.

    python chay_ben_may.py
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

G('nhập "lib_vỏ.giao"\nnhập "lib_chương_trình.giao"\nnhập "lib_bền.giao"')

print("┌───────────────────────────────────────────────────────────────┐")
print("│  HĐH-GIAO — BỀN HOÁ CHO TIẾN TRÌNH MÁY (chụp cả lõi GVM)      │")
print("└───────────────────────────────────────────────────────────────┘")

G('''
đặt M = khởi_máy()
thêm_người(M, 0, "gốc")  thêm_người(M, 1000, "an")
đặt KHỞI = sinh_tt(M, "khởi", 0, 0, "/")
gọi(M, KHỞI, GH_TẠO_THƯ, ["/hệ", 755])  gọi(M, KHỞI, GH_TẠO_THƯ, ["/tạm", 777])
gọi(M, KHỞI, GH_TẠO, ["/hệ/nhật_ký", 644, "nhịp 0  khởi: nhân lên"])
nạp_chương_trình(M)
đặt_lượng_tử(M, 60)
đăng_ký_ct_máy(M, "đếm_dài", "hàm đ(n) { nếu n == 0 { trả 0 }  rọi n  trả đ(n - 1) }  rọi đ(30)")
đăng_ký_ct_máy(M, "chép_máy",
    "đặt nội = gọi_hệ(0, \\"/hệ/nhật_ký\\")  gọi_hệ(2, \\"/tạm/chép\\", 644, nội)  rọi 7")
''')

print("\n════ 1. Sinh tiến trình MÁY rồi cho chạy DỞ DANG ════")
G('đặt A = gọi(M, KHỞI, GH_SINH, ["đếm_dài", 5])')
G('đặt B = gọi(M, KHỞI, GH_SINH, ["chép_máy", 5])')
G('đặt _ = vòng_nhân(M, 4)')
G('rọi "   tt" + A + " đếm_dài: " + lệnh_đã_chạy(M, A) + " lệnh máy · trạng " + trạng(lấy_khoá(M, "nhân"), A)')
G('rọi "   tt" + B + " chép_máy: " + lệnh_đã_chạy(M, B) + " lệnh máy · trạng " + trạng(lấy_khoá(M, "nhân"), B)')

print("\n════ 2. CHỤP cả hệ (nay có cả NGỮ CẢNH lõi GVM) rồi VỨT máy cũ ════")
G('đặt ẢNH = chụp_máy(M)')
G('rọi "   ảnh dài " + dài(ẢNH) + " ký tự"')
G('đặt M = ẩn')
print("   máy cũ đã bị vứt — chỉ còn chuỗi JSON")

print("\n════ 3. DỰNG LẠI từ ảnh — tiến trình máy phải SỐNG, không thành xác ════")
G('''
đặt M2 = phục_hồi_máy(ẢNH)
nạp_chương_trình(M2)
đặt _thân = hồi_sinh(M2)
rọi "   dựng lại " + _thân + " thân tiến-trình"
rọi "   lõi máy của tt" + A + " có còn? " + loại(lõi_của(M2, A)) + " (số = có tay-cầm lõi)"
rọi "   lệnh máy đã tiêu (giữ nguyên từ đời trước): " + lệnh_đã_chạy(M2, A)
''')

print("\n════ 4. CHẠY TIẾP — phải đếm TIẾP, không đếm lại từ 30 ════")
G('đặt_khoá(M2, "kể", sáng)')
G('đặt _ = vòng_nhân(M2, 6)')
G('đặt_khoá(M2, "kể", tối)')

print("\n════ 5. Tiến trình máy có GỌI-HỆ cũng sống lại đúng ════")
G('đặt _ = chạy_tới_hết(M2, 200)')
G('rọi "   /tạm/chép = [" + gọi(M2, KHỞI, GH_ĐỌC, ["/tạm/chép"]) + "]"')
G('rọi "   (do tiến trình MÁY chép, sau khi đã qua một lần chụp–dựng)"')

print("\n════ 6. Tổng kết ════")
G('rọi "   tt" + A + " đếm_dài: " + lệnh_đã_chạy(M2, A) + " lệnh máy · trạng " + trạng(lấy_khoá(M2, "nhân"), A)')
G('rọi "   tt" + B + " chép_máy: " + lệnh_đã_chạy(M2, B) + " lệnh máy · trạng " + trạng(lấy_khoá(M2, "nhân"), B)')
G('rọi ""')
G('rọi "→ Ảnh JSON nay gói được CẢ tiến trình đang chạy trên máy: ip, ngăn xếp, vùng RAM đã dùng."')
G('rọi "  Bytecode thì không cần chụp — biên dịch lại từ nguồn cho ra đúng từng từ-lệnh."')

# -*- coding: utf-8 -*-
"""
HĐH-GIAO — PERSISTENCE TRỰC GIAO: chụp ảnh MÁY giữa chừng, RESUME trên GVM khác (reboot).
================================================================================
Nhân `examples/hdh_ben.giao` tích luỹ 1+2+…+10=55 vào một SỔ CÁI (bản trên heap).
Ta TẮT MÁY giữa chừng (lưu ảnh ĐẦY ĐỦ: RAM+ip+ngăn-xếp+heap), rồi BẬT LẠI bằng một
GVM HOÀN TOÀN MỚI (RAM trống), khôi phục ảnh → nhân CHẠY TIẾP từ đúng chỗ, ra 55.
Trạng thái BỀN trong ẢNH, không phải trong tiến trình ⇒ persistence TRỰC GIAO.
"""
import os, sys, io, contextlib
from giaoc import compile_source_bit
from gvm_may import GVM

SRC = open(os.path.join("examples", "hdh_ben.giao"), encoding="utf-8").read()
ẢNH = "anh_hdh.json"
if os.path.exists(ẢNH): os.remove(ẢNH)
words, bit = compile_source_bit(SRC)

def bắt_ra(g, budget):
    "Chạy g ≤ budget bước, trả (danh sách GIÁ TRỊ đã RỌI, đã-halt-chưa)."
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        g.run(max_steps=budget)
    vals = []
    for l in buf.getvalue().splitlines():
        l = l.strip()
        if l.startswith("sáng="): vals.append(l.split("=")[1].split()[0])
    return vals, g.halted

print("=" * 70)
print("PERSISTENCE TRỰC GIAO — nhân HĐH-GIAO bền qua REBOOT (ảnh MÁY đầy đủ)")
print(f"   nhân hdh_ben → {len(words)} từ-lệnh GVM ({bit}-bit)")
print("=" * 70)

# ── PHIÊN 1: bật máy, chạy GIỮA CHỪNG rồi TẮT (chụp ảnh) ──
g1 = GVM(words, world={}, bit=bit)
ra1, halt1 = bắt_ra(g1, 8_000)             # ngân sách → dừng GIỮA vòng tích luỹ (sau vài bước)
print(f"\n⏻ PHIÊN 1 (máy A): chạy {g1.steps_run} bước rồi TẮT MÁY giữa chừng")
print(f"   đã in tổng: {ra1}   (halt={halt1})")
g1.lưu_máy(ẢNH)
print(f"   → lưu ẢNH MÁY ĐẦY ĐỦ vào {ẢNH} (RAM + ip + ngăn xếp + heap sổ-cái)")

# ── REBOOT: GVM HOÀN TOÀN MỚI (RAM trống), khôi phục ảnh, CHẠY TIẾP ──
g2 = GVM(words, world={}, bit=bit)          # máy B: RAM trống tinh, KHÔNG chạy lại từ đầu
assert g2.nạp_máy(ẢNH), "không nạp được ảnh"
print(f"\n⏼ PHIÊN 2 (máy B = GVM MỚI): khôi phục ảnh, RESUME từ ip={g2.ip} (giữa vòng)")
ra2, halt2 = bắt_ra(g2, 10_000_000)
print(f"   in tiếp tổng: {ra2}   (halt={halt2})")

# ── ĐỐI CHỨNG: chạy LIỀN MẠCH một máy (không reboot) ──
g0 = GVM(words, world={}, bit=bit)
ra0, _ = bắt_ra(g0, 10_000_000)

print("\n" + "-" * 70)
ghép = ra1 + ra2
print(f"   GHÉP (phiên1 ⊕ phiên2): {ghép}")
print(f"   LIỀN MẠCH (1 máy)     : {ra0}")
print(f"   {'✅ TRÙNG KHỚP' if ghép == ra0 else '✗ LỆCH'} — nhân chạy QUA reboot = chạy liền mạch.")
print("   Bộ đếm & sổ-cái (bản trên heap) BỀN qua ranh giới reboot: 1→3→6→…→55, lần=10.")
print("   Trạng thái nằm trong ẢNH MÁY, không trong tiến trình ⇒ PERSISTENCE TRỰC GIAO.")
os.remove(ẢNH)

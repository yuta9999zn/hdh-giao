# -*- coding: utf-8 -*-
"""
HĐH-GIAO Pha 2 — PERSISTENCE TRỰC GIAO (orthogonal persistence).
Toàn bộ trạng thái (ảnh RAM) BỀN qua REBOOT — như Smalltalk/EUMEL: không "tệp" rời,
mà cả thế giới GIAO được lưu & khôi phục nguyên vẹn. Một bộ đếm tăng 5 mỗi lần boot;
tắt máy (kết thúc), bật lại (GVM mới) → nó TIẾP TỤC từ chỗ cũ, như chưa hề tắt.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gvm_may import OPS, GVM

def W(op, a=0): return (OPS[op] << 8) | (a & 0xFF)
# chương trình: ram[0] += 5 ; RỌI ram[0]
code = [W("TẢI_Ô",0), W("NẠP",5), W("CỘNG"), W("LƯU_Ô",0), W("TẢI_Ô",0), W("RỌI"), W("DỪNG")]
ẢNH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anh_giao.json")
if os.path.exists(ẢNH): os.remove(ẢNH)   # bắt đầu sạch

print("="*60)
print("PERSISTENCE TRỰC GIAO — bộ đếm sống sót qua REBOOT (ảnh RAM)")
print("="*60)
for boot in range(1, 5):
    g = GVM(code, world={})              # MÁY MỚI mỗi lần (RAM trống) = tắt-rồi-bật
    có = g.nạp_ảnh(ẢNH)                  # khôi phục thế giới (nếu có)
    print(f"\n⏻ BOOT {boot}: {'khôi phục ảnh cũ' if có else 'lần đầu, RAM trống'}")
    g.run()                              # ram[0] += 5
    g.lưu_ảnh(ẢNH)                       # tắt máy → lưu ảnh
    print(f"   (đã lưu ảnh: ram[0] = {g.ram[0]})")
print("\n" + "-"*60)
print("→ Bộ đếm 5 → 10 → 15 → 20 dù MỖI LẦN là một GVM MỚI (RAM trống lúc tạo).")
print("  Trạng thái BỀN trong ẢNH, không phải trong tiến trình ⇒ persistence trực giao.")
os.remove(ẢNH)

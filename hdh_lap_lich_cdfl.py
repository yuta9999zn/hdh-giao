# -*- coding: utf-8 -*-
"""
HĐH-GIAO Pha 1 (#4) — BỘ LẬP LỊCH CDFL BIẾT-HỌC.
Khác round-robin (chia đều mù quáng), nhân HỌC hành vi từng tiến trình rồi cấp CPU
theo CỘNG HƯỞNG γ — đúng tinh thần "GIAO biết học, hiểu rồi thì hành động nhanh":

  • Quan sát ρ = tiến trình có làm VIỆC HỮU ÍCH (XUẤT) trong lượng tử không.
  • HỌC: σ ← σ + α·(ρ − σ)   (động học tiên đề 5 — niềm tin học về thực tại).
  • γ = cộng_hưởng(σ, lý-tưởng) — tiến trình spin vô ích → σ→0 → γ<0 = ĐỐM TỐI.
  • Cấp lượng tử THEO σ: hữu ích (σ cao) → lượng tử ĐẦY; spin (σ thấp) → THROTTLE còn 1.
  • Chưa biết (σ=ẩn = DE) → cho lượng tử thăm dò; KHÔNG bao giờ bỏ đói (an toàn).

3 tiến trình: A,C làm việc (XUẤT) · B = SPIN THUẦN (vòng vô tận, KHÔNG output = vô ích).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gvm_may import OPS, GVM
from giao import tokenize, Parser, Runtime

# ── lương tri = GIAO: cộng_hưởng (builtin) ──
_rt = Runtime()
def cộng_hưởng(σ, ρ):
    _rt.exec_block(Parser(tokenize(f"đặt __k = cộng_hưởng({σ!r}, {ρ!r})")).parse())
    return float(_rt.glob["__k"])
def học(σ, ρ, α=0.5):                       # σ=None (ẩn/DE) → khai mở = quan sát ρ
    return ρ if σ is None else σ + α * (ρ - σ)

def w(mn, a=0): return (OPS[mn] << 8) | (a & 0xFF)
code = [
    # A @0 — đếm 3, có XUẤT (hữu ích)
    w("NẠP",3), w("LƯU_Ô",200), w("TẢI_Ô",200), w("NHẢY_NẾU_0",11),
    w("TẢI_Ô",200), w("XUẤT"), w("TẢI_Ô",200), w("NẠP",1), w("TRỪ"), w("LƯU_Ô",200),
    w("NHẢY",2), w("DỪNG"),
    # B @12 — SPIN THUẦN: chỉ NHẢY về chính nó, KHÔNG output, KHÔNG kết thúc
    w("NHẢY",12),
    # C @13 — đếm 2, có XUẤT
    w("NẠP",2), w("LƯU_Ô",201), w("TẢI_Ô",201), w("NHẢY_NẾU_0",24),
    w("TẢI_Ô",201), w("XUẤT"), w("TẢI_Ô",201), w("NẠP",1), w("TRỪ"), w("LƯU_Ô",201),
    w("NHẢY",15), w("DỪNG"),
]
NHIỆM_VỤ = [("A",0), ("B-spin",12), ("C",13)]
BASE = 4

print("="*70)
print("HĐH-GIAO — BỘ LẬP LỊCH CDFL BIẾT-HỌC (lập lịch theo cộng hưởng γ)")
print("B-spin = vòng vô tận KHÔNG làm việc hữu ích. Xem nhân HỌC & THROTTLE nó.")
print("="*70)
g = GVM(code, world={})
ctx = g.tiến_trình(NHIỆM_VỤ)
for c in ctx: c["σ"] = None; c["γ"] = 0.0
lượt = 0
while any(c["sống"] for c in ctx) and lượt < 16:
    # ưu tiên: σ cao trước; chưa biết (None) coi như 1.0 (cho thăm dò DE)
    thứ_tự = sorted([c for c in ctx if c["sống"]], key=lambda c: -(1.0 if c["σ"] is None else c["σ"]))
    for c in thứ_tự:
        q = BASE if c["σ"] is None else max(1, round(BASE * c["σ"]))   # THROTTLE theo σ học được
        g.chạy_lát(c, q)
        ρ = 1.0 if c.get("thăm", 1) > 1 else 0.0                       # nhiều IP = TIẾN TRIỂN; 1 IP = spin vô ích
        c["σ"] = học(c["σ"], ρ); c["γ"] = cộng_hưởng(c["σ"], 1.0)
    lượt += 1
    phần = []
    for c in ctx:
        σ = c["σ"]
        s_σ = "ẩn" if σ is None else f"{σ:.2f}"
        s_q = "?" if σ is None else str(max(1, round(BASE * σ)))
        phần.append(f"{c['tên']}:σ={s_σ},γ={c['γ']:+.2f},q={s_q}")
    print(f"  [lượt {lượt:2}] " + "  ".join(phần))

print("-"*70)
for c in ctx:
    nhãn = "ĐỐM TỐI (spin vô ích) → bị THROTTLE" if c["γ"] < 0 else "hữu ích → ưu tiên"
    tt = "xong ✓" if not c["sống"] else "còn chạy"
    print(f"  · {c['tên']:8} {tt:9} · {c['lệnh']:3} lệnh CPU · γ={c['γ']:+.2f}  [{nhãn}]")
b = next(c for c in ctx if c["tên"]=="B-spin")
print("-"*70)
print(f"→ Nhân HỌC ra B-spin vô ích (γ={b['γ']:+.2f}=đốm tối) → chỉ cấp {max(1,round(BASE*b['σ']))} lệnh/lượt")
print(f"  (round-robin sẽ cấp {BASE} lệnh/lượt = phí). A,C hữu ích được ưu tiên & xong nhanh.")
print("  ⇒ OS THÍCH NGHI: hiểu hành vi rồi PHÂN BỔ THEO CỘNG HƯỞNG — Kali/Linux không có ở tầng nhân.")

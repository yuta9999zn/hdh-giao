# -*- coding: utf-8 -*-
"""
HĐH-GIAO Pha 1 — ĐA NHIỆM TIỀN-ĐỊNH (preemptive) trên GVM.
Chứng minh mốc Pha 1: một tiến trình CHẠY LOẠN (vòng vô tận, KHÔNG nhường CPU)
KHÔNG treo được hệ — nhân CƯỚP CPU sau mỗi lượng tử thời gian (≈ ngắt timer phần cứng).

3 tiến trình chạy xen kẽ trên MỘT nhân:
  A — đếm 3..1 rồi DỪNG       (tiến trình ngoan)
  B — in 9 rồi NHẢY về chính nó MÃI MÃI, không DỪNG   (★ CHẠY LOẠN)
  C — đếm 2..1 rồi DỪNG
Hợp tác (cooperative) sẽ TREO ở B. Tiền-định (preemptive) thì A,C VẪN XONG.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gvm_may import OPS, GVM, disasm_word

def w(mn, arg=0): return (OPS[mn] << 8) | (arg & 0xFF)

# Mã máy 3 tiến trình ghép trong MỘT mảng (địa chỉ tuyệt đối):
code = [
    # ── Tiến trình A @0  (đếm bộ nhớ ram[200] = 3 → 0) ──
    w("NẠP", 3), w("LƯU_Ô", 200),
    w("TẢI_Ô", 200), w("NHẢY_NẾU_0", 11),               # @2 lặp: nếu 0 → @11 DỪNG
    w("TẢI_Ô", 200), w("XUẤT"),                          # in bộ đếm
    w("TẢI_Ô", 200), w("NẠP", 1), w("TRỪ"), w("LƯU_Ô", 200),
    w("NHẢY", 2), w("DỪNG"),                             # @10 lặp lại · @11 hết
    # ── Tiến trình B @12  (★ CHẠY LOẠN — vòng vô tận, KHÔNG DỪNG) ──
    w("NẠP", 9), w("XUẤT"), w("NHẢY", 12),
    # ── Tiến trình C @15  (đếm ram[201] = 2 → 0) ──
    w("NẠP", 2), w("LƯU_Ô", 201),
    w("TẢI_Ô", 201), w("NHẢY_NẾU_0", 26),               # @17 lặp
    w("TẢI_Ô", 201), w("XUẤT"),
    w("TẢI_Ô", 201), w("NẠP", 1), w("TRỪ"), w("LƯU_Ô", 201),
    w("NHẢY", 17), w("DỪNG"),                            # @25 · @26 hết
]
NHIỆM_VỤ = [("A", 0), ("B-loạn", 12), ("C", 15)]

print("=" * 66)
print("HĐH-GIAO Pha 1 — LẬP LỊCH TIỀN-ĐỊNH (preemptive) · lượng tử = 4 lệnh")
print("3 tiến trình; B-loạn = vòng vô tận KHÔNG nhường CPU. Xem hệ có treo không.")
print("=" * 66)
g = GVM(code, world={})
kq = g.chạy_đa_nhiệm(NHIỆM_VỤ, lượng_tử=4, tối_đa_lượt=12)
print("-" * 66)
print(f"Sau {kq['lượt']} lượt lập lịch:")
for c in kq["ctx"]:
    tt = "ĐÃ XONG ✓" if not c["sống"] else "CÒN CHẠY (bị cướp CPU liên tục)"
    print(f"  · {c['tên']:8} — {tt:36} {c['lệnh']} lệnh · bị preempt {c['preempt']} lần")
print("-" * 66)
print("→ A và C VẪN HOÀN THÀNH dù B chạy loạn vô tận. Nhân CƯỚP được CPU khỏi B")
print("  mỗi lượng tử (≈ ngắt timer) ⇒ MỘT TIẾN TRÌNH LOẠN KHÔNG TREO ĐƯỢC HỆ.")
print("  (Cooperative — như examples/hdh.giao — sẽ treo vĩnh viễn ở B.)")

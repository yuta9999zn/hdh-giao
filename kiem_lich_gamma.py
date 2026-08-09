# -*- coding: utf-8 -*-
"""
kiem_lich_gamma.py — CHỨNG MINH: bộ lập lịch γ của HĐH (viết bằng GIAO) TRÙNG TỪNG PHÉP với
chính sách γ-scheduler ở TẦNG MÁY (`gvm_may.GVM.γ_cập_nhật`) — vốn đã được chứng là trùng
wire silicon `hw/gvm.v`. Nối được ⇒ lịch của HĐH và lịch của phần cứng LÀ MỘT.

    python kiem_lich_gamma.py
"""
import os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from giao import tokenize, Parser, Runtime, nạp_chuẩn
from gvm_may import GVM

rt = Runtime(); rt.base_dir = HERE; nạp_chuẩn(rt)
rt.exec_block(Parser(tokenize('nhập "lib_lịch_γ.giao"')).parse())

def γ_giao(σ, cred, cur, có_ích, n):
    "Gọi hàm γ_bước VIẾT BẰNG GIAO."
    rt.glob["__σ"] = list(σ); rt.glob["__c"] = list(cred)
    rt.glob["__cur"] = cur; rt.glob["__ích"] = "sáng" if có_ích else "tối"; rt.glob["__n"] = n
    rt.exec_block(Parser(tokenize("đặt __kq = γ_bước(__σ, __c, __cur, __ích, __n)")).parse())
    kq = rt.glob["__kq"]
    return [int(x) for x in kq[0]], [int(x) for x in kq[1]], int(kq[2])

random.seed(11)
tổng = khớp = 0
lệch = []
for _ in range(2000):
    n = random.randint(2, 5)
    σ = [random.randint(0, 255) for _ in range(n)]
    cred = [random.randint(0, 600) for _ in range(n)]
    cur = random.randint(0, n - 1)
    ích = random.random() < 0.5
    a_σ, a_c, a_sel = γ_giao(σ, cred, cur, ích, n)
    b_σ, b_c, b_sel = GVM.γ_cập_nhật(σ, cred, cur, ích, n)
    tổng += 1
    if (a_σ, a_c, a_sel) == (list(b_σ), list(b_c), b_sel): khớp += 1
    elif len(lệch) < 3: lệch.append((σ, cred, cur, ích, (a_σ, a_c, a_sel), (b_σ, b_c, b_sel)))

print("=" * 68)
print("LỊCH γ CỦA HĐH (GIAO)  ⟷  LỊCH γ CỦA MÁY/SILICON (gvm_may ≡ hw/gvm.v)")
print("=" * 68)
print(f"  {khớp}/{tổng} ca ngẫu nhiên KHỚP HOÀN TOÀN (σ mới · credit mới · tiến trình được chọn)")
for l in lệch: print("   ✗ lệch:", l)
print("=" * 68)
print("  ✓ TRÙNG KHÍT — cùng một chính sách CDFL từ vỏ lệnh xuống tới cổng logic."
      if khớp == tổng else "  ✗ LỆCH — phải sửa trước khi tin.")
sys.exit(0 if khớp == tổng else 1)

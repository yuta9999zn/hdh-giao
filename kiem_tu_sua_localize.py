# -*- coding: utf-8 -*-
"""kiem_tu_sua_localize.py — kiểm STAGE 4 (định-vị+sửa) tự-chứa: 2 lib (1 đúng,1 lỗi) + suite → tự tìm tệp lỗi → vá."""
import subprocess, sys, os
P = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
F = {n: os.path.join(P, n) for n in ("_la.giao","_lb.giao","_t1.giao","_t2.giao")}
try:
    open(F["_la.giao"],"w",encoding="utf-8").write("hàm cộng(a, b) { trả a + b }\n")
    open(F["_lb.giao"],"w",encoding="utf-8").write("hàm nhân(a, b) { trả a + b }\n")   # LỖI: nên a*b
    open(F["_t1.giao"],"w",encoding="utf-8").write('nhập "_la.giao"\nđặt g = cộng(2,3)\nnếu g == 5 { rọi "PASS" } khác { rọi "FAIL expected 5 got " + g }\n')
    open(F["_t2.giao"],"w",encoding="utf-8").write('nhập "_lb.giao"\nđặt g = nhân(2,3)\nnếu g == 6 { rọi "PASS" } khác { rọi "FAIL expected 6 got " + g }\n')
    r = subprocess.run([sys.executable,"vong_tu_sua.py","--suite","_la.giao","_lb.giao","--","_t1.giao","_t2.giao"],
                       capture_output=True, text=True, env=ENV, cwd=P, encoding="utf-8")
    # xác minh: ĐỊNH-VỊ đúng _lb (không _la), _lb đã vá (a*b), _la KHÔNG đụng
    la = open(F["_la.giao"],encoding="utf-8").read(); lb = open(F["_lb.giao"],encoding="utf-8").read()
    ok = ("nghi (spectrum" in r.stdout and "'_lb.giao'" in r.stdout
          and "TỰ-SỬA THÀNH CÔNG" in r.stdout and "a * b" in lb and "a + b" in la)
    print("✅ STAGE 4: ĐỊNH-VỊ đúng _lb (không _la) → tự vá a+b→a*b" if ok else "✗ Stage 4 LỖI")
    sys.exit(0 if ok else 1)
finally:
    for f in F.values():
        if os.path.exists(f): os.remove(f)

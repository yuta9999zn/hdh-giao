# -*- coding: utf-8 -*-
"""kiem_tu_sua.py — kiểm VÒNG TỰ-SỬA tự-chứa: gieo lỗi → vòng tự-sửa → xác minh đã vá → dọn."""
import subprocess, sys, os
P = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
đích = os.path.join(P, "_tu_dich.giao"); test = os.path.join(P, "_tu_test.giao")
try:
    # 1) GIEO lỗi hằng (trả 64, đúng 128)
    open(đích, "w", encoding="utf-8").write("hàm ng() { trả 64 }\n")
    open(test, "w", encoding="utf-8").write(
        'nhập "_tu_dich.giao"\nđặt g = ng()\nnếu g == 128 { rọi "PASS" } khác { rọi "FAIL expected 128 got " + g }\n')
    # 2) chạy VÒNG TỰ-SỬA
    r = subprocess.run([sys.executable, "vong_tu_sua.py", "_tu_dich.giao", "_tu_test.giao"],
                       capture_output=True, text=True, env=ENV, cwd=P, encoding="utf-8")
    # 3) xác minh: vòng báo thành công + tệp ĐÃ vá + test PASS
    đã_vá = "trả 128" in open(đích, encoding="utf-8").read()
    t = subprocess.run([sys.executable, "giao.py", "_tu_test.giao"], capture_output=True, text=True, env=ENV, cwd=P, encoding="utf-8")
    ok = "TỰ-SỬA THÀNH CÔNG" in r.stdout and đã_vá and "PASS" in t.stdout
    print("✅ VÒNG TỰ-SỬA: gieo lỗi → tự vá → test PASS" if ok else "✗ vòng tự-sửa LỖI")
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "")
    sys.exit(0 if ok else 1)
finally:
    for f in (đích, test):
        if os.path.exists(f): os.remove(f)

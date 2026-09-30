# -*- coding: utf-8 -*-
"""kiem_tu_sua_du_manh.py — kiểm CỔNG ĐỦ-MẠNH của vòng tự-sửa (học từ vườn ươm z).
Test YẾU (chỉ kiểm `> 100`) vẫn chuyển sáng khi vá 64→128, nhưng 127/129 cũng sáng — test không chứng
minh được gì về bản vá. Cổng phải trả ẨN (mã 2) và HOÀN-TÁC; --nhận-ẩn thì giữ bản vá nhưng vẫn báo ẨN.
Test MẠNH (`== 128`) thì SÁNG (mã 0)."""
import subprocess, sys, os
P = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
đích = os.path.join(P, "_tdm_dich.giao"); test = os.path.join(P, "_tdm_test.giao")
GỐC = "hàm ng() { trả 64 }\n"
YẾU = 'nhập "_tdm_dich.giao"\nđặt g = ng()\nnếu g > 100 { rọi "PASS" } khác { rọi "FAIL expected 128 got " + g }\n'
MẠNH = 'nhập "_tdm_dich.giao"\nđặt g = ng()\nnếu g == 128 { rọi "PASS" } khác { rọi "FAIL expected 128 got " + g }\n'

def thử(nguồn_test, *cờ):
    open(đích, "w", encoding="utf-8").write(GỐC); open(test, "w", encoding="utf-8").write(nguồn_test)
    r = subprocess.run([sys.executable, "vong_tu_sua.py", "_tdm_dich.giao", "_tdm_test.giao", *cờ],
                       capture_output=True, text=True, env=ENV, cwd=P, encoding="utf-8")
    return r.returncode, r.stdout, open(đích, encoding="utf-8").read()

try:
    ca = []
    mã, out, sau = thử(YẾU)
    ca.append(("test YẾU → ẨN (mã 2), bản vá bị HOÀN-TÁC", mã == 2 and "ẨN" in out and sau == GỐC and "0/" in out))
    mã, out, sau = thử(YẾU, "--nhận-ẩn")
    ca.append(("test YẾU + --nhận-ẩn → vẫn ẨN (mã 2) nhưng GIỮ bản vá", mã == 2 and "trả 128" in sau))
    mã, out, sau = thử(MẠNH)
    ca.append(("test MẠNH → SÁNG (mã 0), giữ bản vá", mã == 0 and "SÁNG" in out and "trả 128" in sau and "đủ-mạnh" in out))
    for tên, ok in ca: print(f"  {'✓' if ok else '✗'} {tên}")
    đạt = sum(ok for _, ok in ca)
    print(f"CỔNG ĐỦ-MẠNH: {đạt}/{len(ca)} đạt")
    sys.exit(0 if đạt == len(ca) else 1)
finally:
    for f in (đích, test):
        if os.path.exists(f): os.remove(f)

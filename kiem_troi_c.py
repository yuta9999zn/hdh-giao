# -*- coding: utf-8 -*-
"""KIỂM LUẬT TRÔI (C) — "thuần thế giới", HAI MÁY KHỚP.
    python kiem_troi_c.py
  ① kiem_troi_c.giao: trình thông dịch ≡ giaoc64.py→GVM-64 ≡ giaoc64.giao (tự thân)→GVM-64, từng ký tự;
     hai trình biên dịch cho .g64 trùng từng byte.
  ② 10 luật vi phạm (biến cục bộ/tham số/biến lặp/tên bắt/hàm bao ngoài/hàm vô danh, tâm, de, hàm vô danh
     trong luật, gọi hàm cục bộ): CẢ BA đường đều từ chối LÚC ĐỌC MÃ, cùng lý do, cùng dòng:cột.
"""
import os, sys, re, shutil, subprocess
P = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, P)
from giao import GiaoSyntax
from giaoc64 import biên_dịch_tệp
from vo_gvm64 import lệnh_gvm64
WT = shutil.which("wasmtime") or r"D:\wasmtime\wasmtime.exe"
SH = shutil.which("sh") or r"C:\Program Files\Git\usr\bin\sh.exe"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
đạt = rớt = 0
def ca(tên, ok, ct=""):
    global đạt, rớt
    if ok: đạt += 1; print(f"  ✓ {tên}")
    else: rớt += 1; print(f"  ✗ {tên}  {ct}")

def gvm(g64):
    r = subprocess.run(lệnh_gvm64(), input=g64, capture_output=True, timeout=300)
    return r.returncode, r.stdout.decode("utf-8")
def tự_dịch(tệp):
    r = subprocess.run([SH, os.path.join(P, "tu_bien_dich.sh"), tệp], capture_output=True, timeout=600)
    return r.returncode, r.stdout, r.stderr.decode("utf-8", "replace")

print("[luật trôi (C) — hai máy khớp]")
tệp = os.path.join(P, "kiem_troi_c.giao")
r = subprocess.run([sys.executable, os.path.join(P, "giao.py"), tệp], capture_output=True, text=True, encoding="utf-8", env=ENV)
thông_dịch = r.stdout
g_py = biên_dịch_tệp(tệp); m1, o1 = gvm(g_py)
m2, g_tu, lỗi2 = tự_dịch(tệp); _, o2 = gvm(g_tu)
ca("trình thông dịch chạy sạch, đúng giá trị (toàn cục đọc tại MỖI nhịp; cục bộ chỗ bấm nhịp vô hại)",
   r.returncode == 0 and "nhịp 1: x=5 y=22 z=[5, 22]" in thông_dịch and "nhịp 2: x=105 y=64 z=[105, 64]" in thông_dịch
   and "nhịp 4: x=305" in thông_dịch and "nhịp 5: y=632" in thông_dịch, thông_dịch[-300:] + r.stderr[-300:])
ca("giaoc64.py → GVM-64 ≡ trình thông dịch (từng ký tự)", m1 == 0 and o1 == thông_dịch, o1[-200:])
ca("giaoc64.giao (tự thân) → GVM-64 ≡ trình thông dịch (từng ký tự)", m2 == 0 and o2 == thông_dịch, lỗi2[-200:])
ca("hai trình biên dịch cho .g64 TRÙNG TỪNG BYTE", g_tu == g_py)

VI_PHẠM = [   # (mã nguồn, cụm phải có trong lỗi, dòng)
    ("vật x = 0\nhàm f() {\n    đặt k = 1\n    trôi x = vật x + k\n}\n", "đọc biến CỤC BỘ 'k'", 4),
    ("vật x = 0\nhàm f(k) {\n    trôi x = vật x + k\n}\n", "đọc biến CỤC BỘ 'k'", 3),
    ("vật x = 0\nhàm f() {\n    lặp k trong [1] { đặt z = k }\n    trôi x = k\n}\n", "đọc biến CỤC BỘ 'k'", 4),
    ("vật x = 0\nhàm f() {\n    thử { đặt a = 1 } bắt (lỗi_) { đặt a = 2 }\n    trôi x = lỗi_\n}\n", "đọc biến CỤC BỘ 'lỗi_'", 4),
    ("vật x = 0\nhàm ngoài() {\n    đặt k = 3\n    hàm trong() { trôi x = vật x + k }\n}\n", "đọc biến CỤC BỘ 'k'", 4),
    ("vật x = 0\nđặt f = hàm(k) {\n    trôi x = k\n}\n", "đọc biến CỤC BỘ 'k'", 3),
    ("vật x = 0\ntâm x = 1\ntrôi x = tâm x\n", "đọc tâm 'x'", 3),
    ("vật x = 0\ntrôi x = de\n", "đọc de", 2),
    ("vật x = 0\ntrôi x = hàm() { trả 1 }\n", "chứa hàm vô danh", 2),
    ("vật x = 0\nhàm f() {\n    hàm g(v) { trả v }\n    trôi x = g(1)\n}\n", "đọc biến CỤC BỘ 'g'", 4),
]
print("\n[luật vi phạm — CẢ BA đường từ chối lúc đọc mã]")
for i, (nguồn, cụm, dòng) in enumerate(VI_PHẠM):
    t = os.path.join(P, f"_troi_vi_pham_{i}.giao")
    with open(t, "w", encoding="utf-8") as f: f.write(nguồn)
    try:
        r = subprocess.run([sys.executable, os.path.join(P, "giao.py"), t], capture_output=True, text=True, encoding="utf-8", env=ENV)
        a = r.returncode != 0 and cụm in r.stderr and f"(dòng {dòng}," in r.stderr and "chỉ được đọc vật, hằng số và biến toàn cục" in r.stderr
        try: biên_dịch_tệp(t); b = False
        except GiaoSyntax as e: b = cụm in e.msg and e.line == dòng
        m, _, lỗi = tự_dịch(t)
        c = m != 0 and cụm in lỗi and f"dòng {dòng}," in lỗi
        ca(f"#{i}: {cụm} (dòng {dòng}) — thông dịch {'✓' if a else '✗'} · giaoc64.py {'✓' if b else '✗'} · giaoc64.giao {'✓' if c else '✗'}",
           a and b and c, (r.stderr + lỗi)[-300:])
    finally:
        os.remove(t)
print(f"\nLUẬT TRÔI (C): {đạt}/{đạt + rớt}")
sys.exit(0 if rớt == 0 else 1)

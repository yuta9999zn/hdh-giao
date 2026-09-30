# -*- coding: utf-8 -*-
"""KIỂM GHIM SHA-256 CỦA ARGON2 — module Argon2 bị tráo thì KHÔNG máy nào chịu nạp.
    python kiem_ghim_argon2.py
Một "argon2.wasm" giả trả thẻ cố định sẽ làm MỌI mật khẩu khớp. Ghim: wasm/argon2.sha256 (bản dựng tái
lập được). Kiểm: tệp thật khớp ghim; bản sửa MỘT byte bị từ chối ở vỏ Python (vo_gvm64), tu_bien_dich.sh,
trình thông dịch (argon2_lenh.wasm) và vỏ Node.
"""
import os, sys, shutil, hashlib, subprocess, tempfile
P = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, P)
from vo_gvm64 import kiểm_ghim, lệnh_gvm64, LệchGhim
SH = shutil.which("sh") or r"C:\Program Files\Git\usr\bin\sh.exe"
đạt = rớt = 0
def ca(tên, ok, ct=""):
    global đạt, rớt
    if ok: đạt += 1; print(f"  ✓ {tên}")
    else: rớt += 1; print(f"  ✗ {tên}  {ct}")

def giả(tệp):
    "Bản sao sửa MỘT byte ở giữa tệp."
    d = bytearray(open(tệp, "rb").read()); d[len(d) // 2] ^= 0x01
    fd, t = tempfile.mkstemp(suffix=".wasm"); os.write(fd, d); os.close(fd); return t

print("[ghim SHA-256 của Argon2]")
A2 = os.path.join(P, "wasm", "argon2.wasm"); LENH = os.path.join(P, "wasm", "argon2_lenh.wasm")
try: kiểm_ghim(A2); kiểm_ghim(LENH); ok = True
except LệchGhim as e: ok = False; print(e)
ca("argon2.wasm và argon2_lenh.wasm thật KHỚP ghim wasm/argon2.sha256", ok)

g1, g2 = giả(A2), giả(LENH)
try:
    try: lệnh_gvm64(argon2=g1); ok = False
    except LệchGhim: ok = True
    ca("vỏ Python (vo_gvm64): argon2.wasm sửa 1 byte ⇒ từ chối nạp", ok)

    nguồn = os.path.join(P, "_ghim_thu.giao")
    with open(nguồn, "w", encoding="utf-8") as f: f.write('rọi "chạy"\n')
    try:
        r = subprocess.run([SH, os.path.join(P, "tu_bien_dich.sh"), nguồn], capture_output=True,
                           env=dict(os.environ, GIAO_ARGON2_WASM=g1), timeout=300)
        ca("tu_bien_dich.sh: argon2.wasm sửa 1 byte ⇒ từ chối (mã 3)", r.returncode == 3 and "KHÁC ghim" in r.stderr.decode("utf-8", "replace"))
        r = subprocess.run([SH, os.path.join(P, "tu_bien_dich.sh"), nguồn], capture_output=True, timeout=300)
        ca("tu_bien_dich.sh: tệp thật ⇒ chạy bình thường", r.returncode == 0 and len(r.stdout) > 1000)
    finally:
        os.remove(nguồn)

    mã_giao = 'rọi argon2(2, [1], [2, 2, 2, 2, 2, 2, 2, 2], [], [], 1, 8, 1, 4)\n'
    nguồn = os.path.join(P, "_ghim_thu2.giao")
    with open(nguồn, "w", encoding="utf-8") as f: f.write(mã_giao)
    try:
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(P, "giao.py"), nguồn], capture_output=True, text=True, encoding="utf-8", env=env)
        ca("trình thông dịch: argon2_lenh.wasm thật ⇒ chạy", r.returncode == 0 and r.stdout.strip().startswith("["), r.stderr[-200:])
        env["GIAO_ARGON2_LENH"] = g2
        r = subprocess.run([sys.executable, os.path.join(P, "giao.py"), nguồn], capture_output=True, text=True, encoding="utf-8", env=env)
        ca("trình thông dịch: argon2_lenh.wasm sửa 1 byte ⇒ từ chối", r.returncode != 0 and "KHÁC ghim" in r.stderr, r.stderr[-200:])
    finally:
        os.remove(nguồn)

    node = shutil.which("node")
    if node:
        wasm_tạm = tempfile.mkdtemp()
        for f in ("giao64.mjs", "gvm64.wasm", "argon2.sha256"): shutil.copy(os.path.join(P, "wasm", f), wasm_tạm)
        shutil.copy(g1, os.path.join(wasm_tạm, "argon2.wasm"))
        g64 = os.path.join(wasm_tạm, "x.g64")
        from giaoc64 import biên_dịch_tệp
        t = os.path.join(P, "_ghim_thu3.giao"); open(t, "w", encoding="utf-8").write('rọi 1\n')
        try: open(g64, "wb").write(biên_dịch_tệp(t))
        finally: os.remove(t)
        r = subprocess.run([node, os.path.join(wasm_tạm, "giao64.mjs"), g64], capture_output=True, timeout=120)
        ca("vỏ Node (giao64.mjs): argon2.wasm sửa 1 byte ⇒ từ chối (mã 3)", r.returncode == 3, r.stderr.decode("utf-8", "replace")[-200:])
        shutil.rmtree(wasm_tạm, ignore_errors=True)
    # module ký kép (ML-DSA-65 + Ed25519) cũng được ghim (wasm/ky.sha256)
    g3 = giả(os.path.join(P, "wasm", "ky_lenh.wasm"))
    try:
        mã = ("import sys; sys.path.insert(0, r'" + P + "'); import ky_kep\n"
              "try:\n    ky_kep.ed_khoá(bytes(32)); print('CHẠY')\nexcept Exception as e: print('CHẶN', type(e).__name__)\n")
        r1 = subprocess.run([sys.executable, "-c", mã], capture_output=True, text=True, encoding="utf-8",
                            env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        r2 = subprocess.run([sys.executable, "-c", mã], capture_output=True, text=True, encoding="utf-8",
                            env=dict(os.environ, PYTHONIOENCODING="utf-8", GIAO_KY_WASM=g3))
        ca("ky_lenh.wasm (ký kép): tệp thật chạy · bản sửa 1 byte ⇒ từ chối (LệchGhim)",
           r1.stdout.strip() == "CHẠY" and r2.stdout.strip() == "CHẶN LệchGhim", r1.stdout + r2.stdout + r2.stderr[-200:])
    finally:
        os.remove(g3)
finally:
    os.remove(g1); os.remove(g2)
print(f"\nGHIM ARGON2: {đạt}/{đạt + rớt}")
sys.exit(0 if rớt == 0 else 1)

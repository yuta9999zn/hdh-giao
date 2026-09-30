# -*- coding: utf-8 -*-
"""VỎ CHẠY GVM-64 — một chỗ duy nhất dựng lệnh wasmtime, và KIỂM SHA-256 của module nạp kèm trước khi nạp.

    from vo_gvm64 import lệnh_gvm64, kiểm_ghim
    subprocess.run(lệnh_gvm64(["--bước", "1000"]), input=g64, ...)

gvm64.wasm import 3 hàm của module `argon2` (mã Argon2 tham chiếu C). Module ấy được nạp bằng
`--preload argon2=wasm/argon2.wasm` — tức là mã CHẠY TRONG hộp cát cùng chương trình. Nếu ai đó thay tệp
ấy (một bản "Argon2" trả thẻ cố định chẳng hạn) thì mọi mật khẩu đều khớp. Vì thế trước mỗi lần nạp,
hash của tệp phải TRÙNG ghim trong wasm/argon2.sha256 (bản dựng tái lập được: sh wasm/dung_argon2.sh).
Lệch ghim ⇒ LỖI, không chạy (hỏng thì đóng, không mở).
"""
import os, shutil, hashlib

P = os.path.dirname(os.path.abspath(__file__))
WASMTIME = os.environ.get("GIAO_WASMTIME") or shutil.which("wasmtime") or r"D:\wasmtime\wasmtime.exe"
GHIM = os.path.join(P, "wasm", "argon2.sha256")

class LệchGhim(RuntimeError): pass

def _ghim(tệp_ghim=None):
    ra = {}
    with open(tệp_ghim or GHIM, encoding="utf-8") as f:
        for d in f:
            d = d.strip()
            if d: h, tên = d.split(None, 1); ra[os.path.basename(tên.lstrip("*"))] = h.lower()
    return ra

def kiểm_ghim(đường_dẫn, tên=None, tệp_ghim=None):
    "Ném LệchGhim nếu SHA-256 của tệp khác ghim (tên = tên trong tệp ghim, mặc định = basename)."
    tên = tên or os.path.basename(đường_dẫn)
    kỳ = _ghim(tệp_ghim).get(tên)
    if kỳ is None: raise LệchGhim(f"không có ghim cho {tên} trong {tệp_ghim or GHIM}")
    with open(đường_dẫn, "rb") as f: thật = hashlib.sha256(f.read()).hexdigest()
    if thật != kỳ:
        raise LệchGhim(f"{đường_dẫn}: SHA-256 {thật[:16]}… KHÁC ghim {kỳ[:16]}… — từ chối nạp "
                       f"(dựng lại: sh wasm/dung_argon2.sh; cố ý đổi: --ghim)")
    return thật

def lệnh_gvm64(cờ=(), argon2=None):
    "argv chạy GVM-64 dưới wasmtime, SAU KHI kiểm ghim argon2.wasm. argon2= để thử với tệp khác (kiểm thử)."
    a2 = argon2 or os.environ.get("GIAO_ARGON2_WASM") or os.path.join(P, "wasm", "argon2.wasm")
    kiểm_ghim(a2, "argon2.wasm")
    return [WASMTIME, "run", "--preload", "argon2=" + a2, os.path.join(P, "wasm", "gvm64.wasm"), "--", *cờ]

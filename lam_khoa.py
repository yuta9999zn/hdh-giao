# -*- coding: utf-8 -*-
"""
lam_khoa.py — SINH KHOÁ + KÝ MỤC LỤC KHO (việc của NGƯỜI GIỮ KHO, làm bên ngoài máy)
================================================================================
Phân vai giống hệt đời thật: Debian/Kali ký kho bằng khoá riêng của họ; máy người dùng chỉ có
khoá CÔNG để kiểm. Nên ở đây:

    KÝ    — script này (Python, zero-dependency: chỉ hashlib + secrets). Khoá RIÊNG nằm ngoài,
            KHÔNG bao giờ đi vào hệ điều hành.
    KIỂM  — `lib_chu_ky.giao` bên trong HĐH-GIAO, chỉ cần khoá công.

    python lam_khoa.py --sinh              # sinh cặp khoá RSA-2048 → khoa_rieng.txt / khoa_cong.txt
    python lam_khoa.py --ký "<nội dung>"   # ký một chuỗi → chữ ký hex
    python lam_khoa.py --ký-tệp <tệp>      # ký nội dung một tệp
    python lam_khoa.py --kiểm <tệp> <chữ ký hex>

KHÔNG dùng cho bí mật thật: sinh số nguyên tố ở đây là bản gọn để dạy/chạy dự án, chưa qua
thẩm định mật mã. Điều nó chứng minh là NGỮ NGHĨA: chỉ ai giữ khoá riêng mới ký nổi mục lục.
"""
import os, sys, hashlib, secrets

HERE = os.path.dirname(os.path.abspath(__file__))
TỆP_RIÊNG = os.path.join(HERE, "khoa_rieng.txt")
TỆP_CÔNG = os.path.join(HERE, "khoa_cong.txt")
E = 65537
DER = "3031300d060960864801650304020105000420"      # DigestInfo SHA-256


def _nguyên_tố(bit):
    "Số nguyên tố `bit` bit — Miller-Rabin 40 vòng."
    while True:
        n = secrets.randbits(bit) | (1 << (bit - 1)) | 1
        if n % 3 == 0 or n % 5 == 0: continue
        if _mr(n) and (n - 1) % E != 0:
            return n


def _mr(n, vòng=40):
    if n < 2: return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0: return n == p
    d, r = n - 1, 0
    while d % 2 == 0: d //= 2; r += 1
    for _ in range(vòng):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x == 1 or x == n - 1: continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1: break
        else:
            return False
    return True


def sinh(bit=2048):
    p = _nguyên_tố(bit // 2)
    q = _nguyên_tố(bit // 2)
    while q == p: q = _nguyên_tố(bit // 2)
    n = p * q
    d = pow(E, -1, (p - 1) * (q - 1) // _ước_chung(p - 1, q - 1))
    with open(TỆP_RIÊNG, "w", encoding="utf-8") as f:
        f.write(f"rsa|{d:x}|{n:x}\n")
    with open(TỆP_CÔNG, "w", encoding="utf-8") as f:
        f.write(f"rsa|{E}|{n:x}\n")
    print(f"  ✓ khoá riêng → {TỆP_RIÊNG}  (GIỮ KÍN, đừng đưa vào máy)")
    print(f"  ✓ khoá công  → {TỆP_CÔNG}")
    print(f"  vân tay: {hashlib.sha256(f'{n:x}'.encode()).hexdigest()[:16]}")


def _ước_chung(a, b):
    while b: a, b = b, a % b
    return a


def _khuôn(nội, k):
    "EM của PKCS#1 v1.5 + SHA-256, dạng chuỗi hex."
    băm = hashlib.sha256(nội.encode("utf-8")).hexdigest()
    return "0001" + "ff" * (k - 54) + "00" + DER + băm


def _nạp(tệp):
    with open(tệp, encoding="utf-8") as f:
        p = f.read().strip().split("|")
    return int(p[1], 16) if tệp == TỆP_RIÊNG else int(p[1]), int(p[2], 16)


def ký(nội):
    d, n = _nạp(TỆP_RIÊNG)
    k = (n.bit_length() + 7) // 8
    m = int(_khuôn(nội, k), 16)
    return f"{pow(m, d, n):0{k * 2}x}"


def kiểm(nội, sig_hex):
    e, n = _nạp(TỆP_CÔNG)
    k = (n.bit_length() + 7) // 8
    m = pow(int(sig_hex, 16), e, n)
    return f"{m:0{k * 2}x}" == _khuôn(nội, k)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("--sinh", "--sinh-khoa"):
        sinh()
    elif a[0] in ("--ký", "--ky"):
        print(ký(a[1]))
    elif a[0] in ("--ký-tệp", "--ky-tep"):
        with open(a[1], encoding="utf-8") as f: print(ký(f.read()))
    elif a[0] in ("--kiểm", "--kiem"):
        with open(a[1], encoding="utf-8") as f: nội = f.read()
        print("✓ chữ ký ĐÚNG" if kiểm(nội, a[2]) else "✗ chữ ký SAI")
    else:
        print(__doc__)

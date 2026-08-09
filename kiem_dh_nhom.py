# -*- coding: utf-8 -*-
"""
kiem_dh_nhom.py — kiểm SỐ NGUYÊN TỐ Diffie-Hellman trong lib_dh.giao đúng là nhóm chuẩn
================================================================================
Hằng số mật mã là chỗ dễ chép sai nhất mà lại khó thấy: sai một chữ thì bắt tay vẫn "chạy",
chỉ có điều nhóm không còn an toàn. Nên kiểm bằng ĐỊNH NGHĨA của chuẩn chứ không so chuỗi:

  RFC 3526 §3 (MODP Group 14):
      p = 2^2048 − 2^1984 − 1 + 2^64 × ( ⌊2^1918 × π⌋ + 124476 )

rồi kiểm p là số nguyên tố VÀ (p−1)/2 cũng nguyên tố (nhóm an toàn ⇒ không có nhóm con nhỏ).

    python kiem_dh_nhom.py
"""
import os, re, sys, secrets
from decimal import Decimal, getcontext

HERE = os.path.dirname(os.path.abspath(__file__))


def _pi(chữ_số=650):
    """π tới `chữ_số` chữ số thập phân, bằng công thức Machin — TÍNH chứ không dán.

    Dán vài trăm chữ số π rồi tưởng là đủ chính là chỗ tôi vừa sai: ⌊2^1918 × π⌋ cần tới ~580
    chữ số có nghĩa, thiếu là ra số khác hẳn mà nhìn không thấy."""
    getcontext().prec = chữ_số + 40

    def arctan_nghịch(x):                 # arctan(1/x) theo chuỗi Gregory
        x2 = x * x
        số_hạng = Decimal(1) / x
        tổng = số_hạng
        n = 1
        while True:
            số_hạng = -số_hạng / x2
            n += 2
            góp = số_hạng / n
            if góp == 0: break
            tổng += góp
        return tổng

    return 16 * arctan_nghịch(Decimal(5)) - 4 * arctan_nghịch(Decimal(239))


def _mr(n, k=16):
    d, r = n - 1, 0
    while d % 2 == 0: d //= 2; r += 1
    for _ in range(k):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1): continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1: break
        else:
            return False
    return True


def main():
    with open(os.path.join(HERE, "lib_dh.giao"), encoding="utf-8") as f:
        src = f.read()
    m = re.search(r'DH_P_HEX = "([0-9a-f]+)"', src)
    if not m:
        print("  ✗ không tìm thấy DH_P_HEX trong lib_dh.giao"); sys.exit(1)
    p = int(m.group(1), 16)

    pi = _pi(650)
    mong = 2**2048 - 2**1984 - 1 + 2**64 * (int(pi * Decimal(2)**1918) + 124476)

    rớt = 0
    for tên, đk in (
        ("p ĐÚNG công thức RFC 3526 nhóm 14", p == mong),
        ("p dài đúng 2048 bit", p.bit_length() == 2048),
        ("p là SỐ NGUYÊN TỐ (Miller-Rabin 16 vòng)", _mr(p)),
        ("(p−1)/2 cũng nguyên tố ⇒ NHÓM AN TOÀN (không có nhóm con nhỏ)", _mr((p - 1) // 2)),
        ("g = 2 như chuẩn", 'đặt DH_G = 2' in src),
    ):
        print(f"  {'✓' if đk else '✗'} {tên}")
        if not đk: rớt += 1
    sys.exit(1 if rớt else 0)


if __name__ == "__main__":
    main()

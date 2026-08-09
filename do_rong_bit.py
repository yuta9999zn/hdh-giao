# -*- coding: utf-8 -*-
"""
do_rong_bit.py — ĐỘ RỘNG TỪ của GVM là THAM SỐ (16/32/64/128/256-bit).
Cùng một chương trình biên dịch, chạy ở nhiều độ rộng → thấy số GÓI (wrap) khác nhau:
máy hẹp tràn, máy rộng giữ đúng. Chứng minh GVM nới được tới bộ nhớ/giá trị bất kỳ.
"""
import io, contextlib, re
from giaoc import compile_source
from gvm_may import GVM

SRC = "rọi 60000 * 60000 * 4"          # = 14,400,000,000
ĐÚNG = 60000 * 60000 * 4
words = compile_source(SRC)

print("="*60)
print(f"Chương trình: {SRC}   (giá trị đúng = {ĐÚNG:,})")
print("="*60)
for B in (16, 32, 64, 128, 256):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        GVM(words, world={}, bit=B).run()
    m = re.search(r"sáng=(\d+)", buf.getvalue())
    v = int(m.group(1)) if m else None
    dấu = "ĐÚNG" if v == ĐÚNG else "GÓI (wrap)"
    print(f"  {B:3d}-bit (mặt nạ 2^{B}−1):  {v:>14,}   {dấu}")
print("\n→ Độ rộng từ chỉ là THAM SỐ. 16/32-bit tràn (gói); 64-bit trở lên giữ ĐÚNG.")
print("  Nới lên 64-bit ⇒ địa chỉ 2^64 = 16 EB ≫ 1TB: dùng được mọi cỡ bộ nhớ.")

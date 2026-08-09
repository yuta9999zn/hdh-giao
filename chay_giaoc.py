# -*- coding: utf-8 -*-
"""
HARNESS — chạy trình biên dịch VIẾT BẰNG GIAO (examples/giaoc.giao) rồi
nạp bytecode nó sinh ra vào MÁY GVM.

Vai trò Python ở đây tối thiểu và rõ ràng:
  • host trình thông dịch GIAO (giao.py) để CHẠY trình biên dịch — nhưng LOGIC biên dịch
    là GIAO, không phải Python.
  • CPU của máy GVM (chạy bit).
Bytecode được sinh ra BỞI mã GIAO (biến toàn cục 'mã'), không phải bởi giaoc.py (Python).
"""
import sys
from giao import tokenize, Parser, Runtime
from gvm_may import GVM, disasm_word

src = open("examples/giaoc.giao", encoding="utf-8").read()
rt = Runtime()
rt.exec_block(Parser(tokenize(src)).parse())   # chạy trình biên dịch GIAO

ma = rt.glob.get("mã")                          # bytecode do mã GIAO sinh ra
if ma is None:
    print("Không thấy biến 'mã'", file=sys.stderr); sys.exit(1)

print("\n" + "="*62)
print("BYTECODE (do trình biên dịch GIAO sinh) — giải mã kiểm chứng")
print("="*62)
for i, w in enumerate(ma):
    print(f"  {i:02d}:  {disasm_word(int(w))}")

print("\n" + "="*62)
print("CHẠY bytecode trên MÁY GVM (trit/γ, nền NAND)")
print("="*62)
GVM([int(w) for w in ma], world={}).run()
print("\n   → Trình biên dịch GIAO→GVM nay VIẾT BẰNG GIAO. Python chỉ host & làm CPU.")

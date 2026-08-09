# -*- coding: utf-8 -*-
"""
BENCHMARK tính toán nặng — cùng một chương trình GIAO chạy trên 3 tầng:
  1) THÔNG DỊCH tree-walking (giao.py)   — đường chính, chậm
  2) GVM PYTHON (gvm_may.py)             — bytecode nhưng dispatch bằng Python
  3) WASM GVM (gvm.wasm, qua Node)       — bytecode biên dịch, NHANH
Trả lời "có VM nhanh để test tính toán nặng không": CÓ — WASM GVM (cho phần con số học).
"""
import sys, os, json, time
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)
from giao import tokenize, Parser, Runtime, nạp_chuẩn
from giaoc import compile_source_bit
from gvm_may import GVM

N = int(sys.argv[1]) if len(sys.argv) > 1 else 2_000_000
PROG = f"đặt s = 0\nlặp {N} {{ đặt s = s + 1 }}\nrọi s"
print(f"Chương trình: vòng lặp {N:,} lần, mỗi lần s = s + 1\n")

# 1) THÔNG DỊCH
rt = Runtime(); nạp_chuẩn(rt); rt.MAX_STEPS = 10**12
t0 = time.perf_counter()
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    rt.exec_block(Parser(tokenize(PROG)).parse())
t_interp = time.perf_counter() - t0

# 2) BIÊN DỊCH + GVM PYTHON
words, bit = compile_source_bit(PROG)
g = GVM(words, world={}, bit=bit)
t0 = time.perf_counter()
with contextlib.redirect_stdout(io.StringIO()):
    g.run(max_steps=10**12)
t_gvm = time.perf_counter() - t0
máy_val = g.xuất[-1][2] if g.xuất else None      # giá trị máy in (16-bit có thể GÓI)

json.dump({"words": words, "bit": bit, "N": N},
          open(os.path.join(P, "wasm", "bench.json"), "w"), ensure_ascii=False)

print(f"  {len(words)} từ-lệnh GVM · {bit}-bit")
print(f"  1) THÔNG DỊCH (tree-walk) : {t_interp:8.3f}s")
print(f"  2) GVM PYTHON (bytecode)  : {t_gvm:8.3f}s   ({t_interp/t_gvm:.1f}× nhanh hơn thông dịch)")
print(f"  → chạy `node wasm/bench.mjs` để đo tầng 3 (WASM).")
print(f"  (lưu ý: máy 16-bit GÓI giá trị → s in ra = {máy_val}; thông dịch = {N}. So TỐC ĐỘ, không phải trị.)")

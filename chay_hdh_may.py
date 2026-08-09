# -*- coding: utf-8 -*-
"""
HĐH-GIAO CHẠY NHƯ MÃ MÁY — nhân hệ điều hành viết bằng GIAO, biên dịch xuống bytecode GVM.
================================================================================
Trước mốc 3a–3e + biến-cục-bộ-theo-khung, nhân `examples/hdh.giao` (closure giữ
state riêng + bản + lặp + mãi) CHỈ chạy được trên THÔNG DỊCH. Nay nó BIÊN DỊCH trọn
xuống bytecode GVM và chạy NHƯ MÃ MÁY — Python chỉ còn là CPU (mô phỏng transistor).

  Tầng 1  giaoc biên dịch examples/hdh.giao → bytecode GVM (nhân HĐH thành mã máy).
  Tầng 2  Chạy bytecode trên GVM → đa nhiệm hợp tác THẬT (tiến trình interleave).
  Tầng 3  Cùng bytecode chạy trên WASM (memory-safe, ~430×) — ghi wasm/hdh.json.

Ngữ nghĩa HĐH (bảng tiến trình, lập lịch, syscall, cổng an toàn) NẰM TRONG bytecode.
"""
import sys, os, io, time, json, contextlib
from giaoc import compile_source_bit
from gvm_may import GVM
from giao import tokenize, Parser, Runtime

SRC = open(os.path.join("examples", "hdh.giao"), encoding="utf-8").read()

print("=" * 70)
print("TẦNG 1 — giaoc biên dịch NHÂN HĐH-GIAO (viết bằng GIAO) → bytecode GVM")
print("=" * 70)
words, bit = compile_source_bit(SRC)
print(f"   nhân HĐH-GIAO  →  {len(words)} từ-lệnh GVM ({bit}-bit · THẺ)")

print("\n" + "=" * 70)
print("TẦNG 2 — chạy NHÂN ấy NHƯ MÃ MÁY trên GVM (Python = CPU mô phỏng transistor)")
print("=" * 70)
GVM(words, world={}, bit=bit).run(max_steps=50_000_000)

# — Tầng 3: ghi artifact cho WASM —
out = os.path.join("wasm", "hdh.json")
json.dump({"words": words, "bit": bit, "nguồn": "examples/hdh.giao (nhân HĐH-GIAO)"},
          open(out, "w", encoding="utf-8"), ensure_ascii=False)
print("\n" + "=" * 70)
print(f"TẦNG 3 — đã ghi {out} ({len(words)} từ) → chạy trên WASM: node wasm/chay_hdh.mjs")
print("=" * 70)

# — ĐO trung thực: GVM-Python là CPU MÔ PHỎNG (chậm); ý nghĩa là PORTABILITY —
print("\n" + "=" * 70)
print("Ý NGHĨA — không phải 'nhanh hơn' mà là CHẠY ĐƯỢC TRÊN MÁY (đa-substrate)")
print("=" * 70)
g = GVM(words, world={}, bit=bit)
t = time.perf_counter()
with contextlib.redirect_stdout(io.StringIO()):
    g.run(max_steps=50_000_000)
dt_máy = time.perf_counter() - t

rt = Runtime(); rt.MAX_STEPS = 50_000_000
t = time.perf_counter()
with contextlib.redirect_stdout(io.StringIO()):
    rt.exec_block(Parser(tokenize(SRC)).parse())
dt_td = time.perf_counter() - t

print(f"   GVM-Python (MÔ PHỎNG transistor) : {dt_máy*1000:7.1f} ms   ({g.steps_run} bước GVM)")
print(f"   Thông dịch (tree-walk, tham chiếu): {dt_td*1000:7.1f} ms   ({rt.steps} bước cây)")
print("   • GVM-Python CHẬM hơn vì nó MÔ PHỎNG một CPU bằng Python (mỗi bước = 1 dispatch).")
print("     Đây KHÔNG phải đường triển khai — nó là 'máy tham chiếu' để khớp đa-substrate.")
print("   • Đường triển khai là WASM: CÙNG bytecode chạy NATIVE (xem node wasm/chay_hdh.mjs).")
print("   • Cái ĐẠT ĐƯỢC: nhân HĐH-GIAO (closure-giữ-state + bản + lặp + mãi) trước CHỈ chạy")
print("     thông dịch, NAY biên dịch trọn → chạy trên GVM/WASM/(Verilog lõi số). Ngữ nghĩa")
print("     hệ điều hành NẰM TRONG bytecode, memory-safe (WASM sandbox), KHÔNG qua C.")

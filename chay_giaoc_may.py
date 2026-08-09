# -*- coding: utf-8 -*-
"""
HAI TẦNG TRÊN MÁY — trình biên dịch GIAO→GVM (viết bằng GIAO) NAY ĐÃ LÀ MÃ MÁY.
================================================================================
Khác `chay_giaoc.py` (chạy trình biên dịch GIAO trên THÔNG DỊCH giao.py), ở đây:

  Tầng 1  giaoc.py BIÊN DỊCH `examples/giaoc.giao` (chính trình biên dịch, viết bằng
          GIAO) → bytecode GVM.  Logic biên dịch giờ KHÔNG còn nhờ Python diễn giải.
  Tầng 2  Chạy bytecode đó trên GVM (32-bit, có THẺ danh sách) → MÁY tự sinh ra
          bytecode của chương trình nguồn `prog` (vòng hội tụ CDFL).
  Tầng 3  Lấy bytecode máy-vừa-sinh, chạy trên một GVM mới → vòng hội tụ thật chạy.

Python chỉ còn: (a) mồi biên dịch một lần (giaoc.py), (b) CPU chạy bit (GVM).
Mọi NGỮ NGHĨA — cả của trình biên dịch LẪN của chương trình — nằm trong bytecode.
"""
import sys
from giaoc import compile_source, WORD_BIT
from gvm_may import GVM, disasm_word

THAM_CHIEU = [293,1536,256,1280,263,6400,6144,7184,1792,2048,3584,6144,257,2816,6400,3846,0]

src = open("examples/giaoc.giao", encoding="utf-8").read()

print("="*64)
print("TẦNG 1 — giaoc.py biên dịch CHÍNH trình-biên-dịch-viết-bằng-GIAO → bytecode")
print("="*64)
words = compile_source(src)
print(f"   trình biên dịch (GIAO) → {len(words)} từ-lệnh GVM")

print("\n" + "="*64)
print("TẦNG 2 — chạy trình biên dịch ấy NHƯ MÃ MÁY → máy tự sinh bytecode của 'prog'")
print("="*64)
gvm = GVM(words, world={}, bit=WORD_BIT)
gvm.run()
sinh = gvm.last_list
if sinh is None:
    print("Không bắt được bytecode (RỌI_DS)", file=sys.stderr); sys.exit(1)

print("\n   Kiểm chứng: bytecode MÁY-sinh khớp tham chiếu (thông dịch giao.py)?")
print(f"   {'KHỚP TỪNG TỪ ✓' if sinh == THAM_CHIEU else 'LỆCH ✗'}  ({len(sinh)} từ)")
if sinh != THAM_CHIEU:
    print(f"   máy : {sinh}\n   tham: {THAM_CHIEU}", file=sys.stderr); sys.exit(1)

print("\n" + "="*64)
print("TẦNG 3 — chạy bytecode MÁY-VỪA-SINH trên một GVM mới → vòng hội tụ CDFL")
print("="*64)
for i, w in enumerate(sinh): print(f"  {i:02d}:  {disasm_word(int(w))}")
print("-"*64)
GVM([int(w) for w in sinh], world={}).run()
print("\n   → Trình biên dịch GIAO→GVM (viết bằng GIAO) đã chạy TRỌN như mã máy;")
print("     bytecode nó sinh ra cũng chạy như mã máy. Python = mồi + CPU, hết.")

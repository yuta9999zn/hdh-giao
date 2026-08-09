# -*- coding: utf-8 -*-
"""
SINH bộ ca đối chiếu → wasm/cases.json
Với mỗi chương trình GIAO: biên dịch (giaoc) → bytecode, chạy trên GVM PYTHON (tham chiếu),
ghi lại OUTPUT có cấu trúc (gvm.xuất). Harness node sẽ chạy CÙNG bytecode trên wasm và so khớp.
"""
import sys, os, json, io, contextlib
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)
from giaoc import compile_source_bit
from gvm_may import GVM
from giao import tokenize, Parser, Runtime, nạp_chuẩn

# (a) các ví dụ biên dịch trực tiếp bằng giaoc.py
FILES = ["7_danh_sach_gvm","8_tong_ds_gvm","9_chuoi_gvm","10_nhieu_thamso_gvm",
         "11_chiso_sosanh_gvm","12_eval_may","13_the_kieu_gvm","giai_thua","hoi_tu_biendich",
         "closure_gvm","ban_gvm","lap_trong_gvm","so_thuc_gvm","thu_bat_mai_gvm","hdh","hdh_ben",
         "heap32_gvm","heap32_chuoi"]

cases = []
for f in FILES:
    src = open(os.path.join(P,"examples",f+".giao"), encoding="utf-8").read()
    words, bit = compile_source_bit(src)
    g = GVM(words, world={}, bit=bit)
    with contextlib.redirect_stdout(io.StringIO()): g.run()
    cases.append({"tên": f, "words": words, "bit": bit, "expect": g.xuất})

# (b) ca ĐỈNH: trình-biên-dịch-viết-bằng-GIAO (giaoc.giao) — chạy trên thông dịch lấy 'mã',
#     đó chính là bytecode 17 từ; rồi chạy bytecode ấy trên GVM để lấy golong hội tụ.
rt = Runtime(); nạp_chuẩn(rt)
with contextlib.redirect_stdout(io.StringIO()):
    rt.exec_block(Parser(tokenize(open(os.path.join(P,"examples","giaoc.giao"),encoding="utf-8").read())).parse())
ma = [int(w) for w in rt.glob["mã"]]
g = GVM(ma, world={}, bit=16)
with contextlib.redirect_stdout(io.StringIO()): g.run()
cases.append({"tên":"giaoc.giao→mã (hội tụ)", "words": ma, "bit":16, "expect": g.xuất})

# (c) ★ VIÊN NGỌC: biên dịch CHÍNH giaoc.giao (compiler viết bằng GIAO) → 8357 từ-lệnh
#     32-bit, rồi chạy trên GVM → máy tự sinh bytecode 17 từ. Đây là test nặng nhất cho wasm.
src = open(os.path.join(P,"examples","giaoc.giao"), encoding="utf-8").read()
words, bit = compile_source_bit(src)
g = GVM(words, world={}, bit=bit)
with contextlib.redirect_stdout(io.StringIO()): g.run()
cases.append({"tên":"★ giaoc.giao BIÊN DỊCH→máy", "words": words, "bit": bit, "expect": g.xuất})

json.dump(cases, open(os.path.join(P,"wasm","cases.json"),"w",encoding="utf-8"), ensure_ascii=False)
print(f"sinh {len(cases)} ca → wasm/cases.json")
for c in cases: print(f"   {c['tên']:<26} {len(c['words'])} từ-lệnh · {c['bit']}-bit · {len(c['expect'])} output")

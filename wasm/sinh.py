# -*- coding: utf-8 -*-
"""
SINH bytecode GVM → wasm/program.json (cho substrate WASM nạp).
Chạy trình-biên-dịch-viết-bằng-GIAO (examples/giaoc.giao) trên thông dịch, lấy biến
toàn cục `mã` = 17 từ-lệnh của vòng hội tụ CDFL (nhảy TRỰC TIẾP, không heap/helper).
Đây là CÙNG bytecode đã khớp 4 tầng (thông dịch/GVM mềm/model/Verilog).
"""
import sys, os, json, io, contextlib
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)
from giao import tokenize, Parser, Runtime, nạp_chuẩn

src = open(os.path.join(P, "examples", "giaoc.giao"), encoding="utf-8").read()
rt = Runtime(); nạp_chuẩn(rt)
with contextlib.redirect_stdout(io.StringIO()):          # nuốt output rọi của giaoc.giao
    rt.exec_block(Parser(tokenize(src)).parse())
ma = [int(w) for w in rt.glob["mã"]]

out = os.path.join(P, "wasm", "program.json")
json.dump({"words": ma, "bit": 16, "nguồn": "examples/giaoc.giao → biến 'mã'"},
          open(out, "w", encoding="utf-8"))
print(f"sinh {len(ma)} từ-lệnh → wasm/program.json")
print(f"   {ma}")

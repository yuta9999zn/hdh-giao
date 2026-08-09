# -*- coding: utf-8 -*-
"""chay_tac_tu.py — biên dịch LÕI QUYẾT ĐỊNH tác tử → bytecode → chạy trên
MÔ HÌNH PHẦN CỨNG (gvm_model = đúng FSM của gvm.v). Đếm chu kỳ để đặt timeout Verilog."""
import sys, os
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GỐC); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from giaoc import compile_source
from gvm_model import chạy

src = open(os.path.join(GỐC, "examples", "tac_tu_may.giao"), encoding="utf-8").read()
words = compile_source(src)
print(f"bytecode: {len(words)} từ-lệnh GVM")
outs, chu_kỳ, halt = chạy(words, mem=4096)
print(f"chu kỳ clock: {chu_kỳ}, dừng={halt}")
print(f"RỌI: {outs}")

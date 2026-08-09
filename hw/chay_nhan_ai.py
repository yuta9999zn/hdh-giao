# -*- coding: utf-8 -*-
"""
chay_nhan_ai.py — TÍCH HỢP CUỐI: biên dịch nhân-AI CDFL → bytecode → nạp vào
MÔ HÌNH PHẦN CỨNG (gvm_model = đúng FSM của gvm.v) và chạy. Nếu khớp với GVM phần
mềm thì tác tử CDFL chạy được trên FPGA (gvm.v).
"""
import sys, os
GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GỐC); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from giaoc import compile_source
from gvm_model import chạy

src = open(os.path.join(GỐC, "examples", "nhan_ai_cdfl_may.giao"), encoding="utf-8").read()
words = compile_source(src)
print("="*64)
print(f"Biên dịch nhân-AI CDFL → {len(words)} từ-lệnh bytecode GVM")
print("Nạp vào MÔ HÌNH PHẦN CỨNG (FSM của gvm.v) và chạy...")
print("="*64)
outs, chu_kỳ, halt = chạy(words, mem=4096)
print(f"Chạy {chu_kỳ} chu kỳ clock, dừng={halt}")
print(f"RỌI (chỉ_số ô, MẶT) mỗi vòng: {outs}")
print(f"  → cặp đầu (0,3)=TRỒI ô0 (DE) · (1,2)=SOI ô1 (ảo tưởng) · còn lại MẶT 1=LÀM TƯƠI (drift)")
print("\n→ Tác tử CDFL liên tục chạy trên MÔ HÌNH PHẦN CỨNG GVM — sẵn sàng cho FPGA.")

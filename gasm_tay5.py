# -*- coding: utf-8 -*-
"""
MỨC 4 — TỰ THÂN HOÁ (SELF-HOSTING): ĐIỂM BẤT ĐỘNG CỦA ASSEMBLER
================================================================
Phép thử tự thân hoá thật sự: cho assembler đọc CHÍNH MÃ NGUỒN của nó (viết bằng
ngôn ngữ đầu vào của chính nó) → nó phải sinh lại ĐÚNG MÃ MÁY của chính nó (fixed point).
Đây là cái mọi trình biên dịch tự thân (C, Go, Rust...) phải vượt qua.

Ta dùng assembler Mức 1 (gasm_tay2.ASM_BANG_TAY — 26 lệnh GÕ TAY). Ngôn ngữ đầu vào của
nó là dãy cặp (opcode, operand). Mã nguồn của chính nó, viết bằng ngôn ngữ đó, chính là
phân rã mã máy của nó: word → (word>>8, word&0xFF). (Phân rã = chỉ ĐỌC lại bit đã gõ tay,
không phải hợp dịch.)

   bước 1: A = assembler gõ tay (26 từ-lệnh)
   bước 2: nguồn = mã nguồn của A bằng ngôn ngữ của A  (các cặp op,arg)
   bước 3: chạy A trên nguồn → A' (bản A tự sinh)
   bước 4: KIỂM CHỨNG  A' == A  (điểm bất động → tự thân)
   bước 5: dùng A' (bản tự sinh) hợp dịch chương trình khác → chứng minh A' CHẠY được

Python chỉ là CPU. Không hàm Python nào hợp dịch.
"""
from gasm_tay2 import ASM_BANG_TAY
from gvm_may import GVM, disasm_word

A = list(ASM_BANG_TAY)            # 26 từ-lệnh mã máy gõ tay = bản thân assembler

# --- bước 2: mã nguồn của A, bằng ngôn ngữ đầu vào của A (cặp op,arg) ---
nguon = []
for word in A:
    nguon.append((word >> 8) & 0xFF)   # opcode
    nguon.append(word & 0xFF)          # operand
nguon.append(255)                      # sentinel kết thúc

ram = [0]*256
for i, v in enumerate(nguon): ram[i] = v
ram[250] = 0      # ip
ram[253] = 100    # out

if __name__ == "__main__":
    print("="*66)
    print("BƯỚC 1 — assembler gõ tay A (mã nguồn của chính nó ở dạng cặp op,arg)")
    print("="*66)
    print(f"  A gồm {len(A)} từ-lệnh. Mã nguồn (op,arg) dài {len(nguon)-1} số + sentinel.")
    print(f"  Vài cặp đầu: {nguon[:8]} ...")

    print("\n" + "="*66)
    print("BƯỚC 3 — chạy A trên CHÍNH mã nguồn của A  →  A' (bản tự sinh)")
    print("="*66)
    m = GVM(A, world={}, ram=ram)
    m.run()
    A_phay = m.ram[100:100+len(A)]

    print("\n" + "="*66)
    print("BƯỚC 4 — KIỂM CHỨNG ĐIỂM BẤT ĐỘNG:  A' == A  ?")
    print("="*66)
    ok = (A_phay == A)
    for i in range(len(A)):
        dau = "✓" if A_phay[i] == A[i] else "✗"
        if i < 6 or i >= len(A)-2:
            print(f"  {dau}  A[{i:2d}]={A[i]:5d}   A'[{i:2d}]={A_phay[i]:5d}   {disasm_word(A_phay[i])}")
        elif i == 6:
            print("  ...")
    print(f"\n  → A' KHỚP A từng byte? {ok}   "
          f"{'★ ASSEMBLER ĐÃ TỰ TÁI TẠO CHÍNH NÓ (tự thân) ★' if ok else 'LỆCH!'}")

    print("\n" + "="*66)
    print("BƯỚC 5 — dùng A' (bản TỰ SINH) hợp dịch chương trình khác")
    print("="*66)
    ram2 = [0]*256
    for i, v in enumerate([7,0, 8,0, 14,0, 255]): ram2[i] = v   # HỌC/GIAO/RỌI
    ram2[250] = 0; ram2[253] = 100
    m2 = GVM(A_phay, world={}, ram=ram2)        # CHẠY trên bản tự sinh A'
    m2.run()
    prog = m2.ram[100:103]
    print(f"  A' hợp dịch [7,0,8,0,14,0] → {prog}")
    for k, word in enumerate(prog):
        print(f"     {disasm_word(word)}")
    print("  Chạy chương trình đó (world vật0=37):")
    GVM(prog, world={0:37}).run()
    print("\n   → A' không chỉ giống A: nó CHẠY THẬT. Tự thân hoá hoàn tất ở tầng mã máy.")

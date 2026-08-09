# -*- coding: utf-8 -*-
"""
MỨC 1 — ASSEMBLER VIẾT BẰNG HỢP NGỮ GVM, GÕ TAY THÀNH MÃ MÁY
=============================================================
Đây là một assembler THẬT (tối giản): đọc các cặp (opcode, operand) từ RAM,
đóng gói thành từ-lệnh 16 bit  word = (op << 8) | arg,  ghi vào vùng RAM ra.

Điều cốt yếu: TOÀN BỘ assembler này là MÃ MÁY GÕ TAY (26 từ-lệnh dưới đây, mỗi từ
gõ từng bit từ bảng opcode). KHÔNG hàm Python nào dịch nó. Python chỉ là CPU chạy bit.
Như vậy 'hành vi hợp dịch' đã được MỒI bằng chính máy, không mượn ngôn ngữ lập trình.

Thuật toán (hợp ngữ GVM) — biến RAM ip=ram[250], out=ram[253]:
   LẶP: op = ram[ip]
        nếu op == 255 (sentinel) → XONG
        word = (op << 8) + ram[ip+1]
        ram[out] = word ;  out += 1 ;  ip += 2 ;  quay lại LẶP
   XONG: dừng
"""
from gvm_may import GVM, disasm_word, OP_NAME

def w(bits16): return int(bits16, 2)   # ghi lại đúng các bit đã gõ tay

# ---- MÃ MÁY GÕ TAY: [opcode 8 bit][operand 8 bit] ----
# addr                 opcode    operand     ; lệnh hợp ngữ tương ứng
ASM_BANG_TAY = [
    w("00011000" "11111010"),  # 0  TẢI_Ô 250        ; đẩy ip
    w("00011101" "00000000"),  # 1  TẢI_GIÁN          ; op = ram[ip]
    w("00010100" "00000000"),  # 2  NHÂN_BẢN          ; nhân bản op
    w("00000001" "11111111"),  # 3  NẠP 255           ; sentinel
    w("00001011" "00000000"),  # 4  TRỪ               ; op - 255
    w("00011100" "00011000"),  # 5  NHẢY_NẾU_0 24     ; ==0 → XONG(24)
    w("00011010" "00001000"),  # 6  DỊCH_TRÁI 8       ; op << 8
    w("00011000" "11111010"),  # 7  TẢI_Ô 250         ; ip
    w("00000001" "00000001"),  # 8  NẠP 1
    w("00001010" "00000000"),  # 9  CỘNG              ; ip+1
    w("00011101" "00000000"),  # 10 TẢI_GIÁN          ; arg = ram[ip+1]
    w("00001010" "00000000"),  # 11 CỘNG              ; word = (op<<8)+arg
    w("00011000" "11111101"),  # 12 TẢI_Ô 253         ; out
    w("00010110" "00000000"),  # 13 ĐỔI               ; [out, word]
    w("00011110" "00000000"),  # 14 LƯU_GIÁN          ; ram[out] = word
    w("00011000" "11111101"),  # 15 TẢI_Ô 253
    w("00000001" "00000001"),  # 16 NẠP 1
    w("00001010" "00000000"),  # 17 CỘNG
    w("00011001" "11111101"),  # 18 LƯU_Ô 253         ; out += 1
    w("00011000" "11111010"),  # 19 TẢI_Ô 250
    w("00000001" "00000010"),  # 20 NẠP 2
    w("00001010" "00000000"),  # 21 CỘNG
    w("00011001" "11111010"),  # 22 LƯU_Ô 250         ; ip += 2
    w("00001111" "00000000"),  # 23 NHẢY 0            ; lặp
    w("00010101" "00000000"),  # 24 BỎ                ; XONG: bỏ op thừa
    w("00000000" "00000000"),  # 25 DỪNG
]

# ---- RAM vào: các cặp (op,arg) cần hợp dịch, kết bằng sentinel 255 ----
# Mã nguồn 'hợp ngữ ở dạng số':  HỌC 0 ; GIAO 0 ; RỌI 0
NGUON = [7,0,  8,0,  14,0,  255]
ram = [0]*256
for i,v in enumerate(NGUON): ram[i] = v
ram[250] = 0     # ip  → đầu vùng nguồn
ram[253] = 100   # out → đầu vùng ra

if __name__ == "__main__":
    print("="*64)
    print("ASSEMBLER (mã máy gõ tay) — xác minh bằng disasm (chỉ GIẢI mã)")
    print("="*64)
    for i,word in enumerate(ASM_BANG_TAY):
        print(f"  {i:02d}:  {disasm_word(word)}")

    print("\n" + "="*64)
    print("CHẠY assembler trên CPU GVM — nó đọc NGUON và đóng gói thành mã máy")
    print("="*64)
    print(f"  Nguồn (op,arg): {NGUON}")
    m = GVM(ASM_BANG_TAY, world={}, ram=ram)
    m.run()
    n = len(NGUON)//2
    ket_qua = m.ram[100:100+n]
    print(f"  RAM ra [100..]: {ket_qua}")
    print("  Giải mã các từ-lệnh assembler vừa tạo:")
    for k,word in enumerate(ket_qua):
        print(f"     {100+k}:  {word:5d}  →  {disasm_word(word)}")

    print("\n" + "="*64)
    print("ĐÓNG VÒNG: chạy chương trình mà assembler vừa sinh ra (world vật0=37)")
    print("="*64)
    GVM(ket_qua, world={0:37}).run()
    print("\n   → Assembler (mã máy gõ tay) đã tự đóng gói lệnh. Python chỉ chạy bit.")

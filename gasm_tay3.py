# -*- coding: utf-8 -*-
"""
MỨC 2 — ASSEMBLER ĐỌC VĂN BẢN, VIẾT BẰNG HỢP NGỮ GVM, GÕ TAY THÀNH MÃ MÁY
=========================================================================
Khác Mức 1 (chỉ nhận cặp SỐ): Mức 2 đọc CHUỖI KÝ TỰ ASCII là 'hợp ngữ thật':
mỗi lệnh = một chữ mnemonic + một chữ số toán hạng, vd  "H0G0R0D0."  nghĩa là
    HỌC 0 ; GIAO 0 ; RỌI 0 ; DỪNG 0      ('.' = kết thúc)

Assembler (viết bằng hợp ngữ GVM, 65 lệnh, GÕ TAY thành mã máy dưới đây) làm:
    - đọc ký tự mnemonic, SO KHỚP với bảng (H→7, G→8, R→14, D→0) → opcode
    - đọc chữ số, đổi ASCII→trị  (mã '0'=48 ⇒ trị = mã - 48)
    - đóng gói word=(op<<8)|trị, ghi vào vùng RAM ra
KHÔNG hàm Python nào hợp dịch. Python chỉ là CPU. (disasm = chỉ GIẢI mã, để kiểm chứng.)

Bố cục RAM:  nguồn ở [0..]; ip=ram[250]; op-tạm=ram[251]; out=ram[253] (đầu=100).
"""
from gvm_may import GVM, disasm_word

def w(b): return int(b, 2)   # đọc lại đúng các bit đã gõ tay (không hợp dịch)

# ===== ASSEMBLER MỨC 2 — MÃ MÁY GÕ TAY: [opcode 8b][operand 8b] =====
# addr                 opcode    operand      ; hợp ngữ GVM  (LOOP=0)
ASM2 = [
    w("00011000" "11111010"),  # 0  TẢI_Ô 250      ; LOOP: đẩy ip
    w("00011101" "00000000"),  # 1  TẢI_GIÁN       ; ch = ram[ip]
    w("00010100" "00000000"),  # 2  NHÂN_BẢN       ; [ch,ch]   — test '.'(46)
    w("00000001" "00101110"),  # 3  NẠP 46
    w("00001011" "00000000"),  # 4  TRỪ            ; ch-46
    w("00011100" "00111111"),  # 5  NHẢY_NẾU_0 63  ; ==0 → DONE(63)
    w("00010100" "00000000"),  # 6  NHÂN_BẢN       ; test 'H'(72)
    w("00000001" "01001000"),  # 7  NẠP 72
    w("00001011" "00000000"),  # 8  TRỪ
    w("00011100" "00011010"),  # 9  NHẢY_NẾU_0 26  ; → SET_H(26)
    w("00010100" "00000000"),  # 10 NHÂN_BẢN       ; test 'G'(71)
    w("00000001" "01000111"),  # 11 NẠP 71
    w("00001011" "00000000"),  # 12 TRỪ
    w("00011100" "00011110"),  # 13 NHẢY_NẾU_0 30  ; → SET_G(30)
    w("00010100" "00000000"),  # 14 NHÂN_BẢN       ; test 'R'(82)
    w("00000001" "01010010"),  # 15 NẠP 82
    w("00001011" "00000000"),  # 16 TRỪ
    w("00011100" "00100010"),  # 17 NHẢY_NẾU_0 34  ; → SET_R(34)
    w("00010100" "00000000"),  # 18 NHÂN_BẢN       ; test 'D'(68)
    w("00000001" "01000100"),  # 19 NẠP 68
    w("00001011" "00000000"),  # 20 TRỪ
    w("00011100" "00100110"),  # 21 NHẢY_NẾU_0 38  ; → SET_D(38)
    w("00010101" "00000000"),  # 22 BỎ             ; (lạ) bỏ ch
    w("00000001" "00000000"),  # 23 NẠP 0
    w("00011001" "11111011"),  # 24 LƯU_Ô 251      ; op = 0
    w("00001111" "00101010"),  # 25 NHẢY 42        ; → EMIT(42)
    w("00010101" "00000000"),  # 26 BỎ             ; SET_H
    w("00000001" "00000111"),  # 27 NẠP 7
    w("00011001" "11111011"),  # 28 LƯU_Ô 251
    w("00001111" "00101010"),  # 29 NHẢY 42
    w("00010101" "00000000"),  # 30 BỎ             ; SET_G
    w("00000001" "00001000"),  # 31 NẠP 8
    w("00011001" "11111011"),  # 32 LƯU_Ô 251
    w("00001111" "00101010"),  # 33 NHẢY 42
    w("00010101" "00000000"),  # 34 BỎ             ; SET_R
    w("00000001" "00001110"),  # 35 NẠP 14
    w("00011001" "11111011"),  # 36 LƯU_Ô 251
    w("00001111" "00101010"),  # 37 NHẢY 42
    w("00010101" "00000000"),  # 38 BỎ             ; SET_D
    w("00000001" "00000000"),  # 39 NẠP 0
    w("00011001" "11111011"),  # 40 LƯU_Ô 251
    w("00001111" "00101010"),  # 41 NHẢY 42
    w("00011000" "11111011"),  # 42 TẢI_Ô 251      ; EMIT: op
    w("00011010" "00001000"),  # 43 DỊCH_TRÁI 8    ; op<<8
    w("00011000" "11111010"),  # 44 TẢI_Ô 250      ; ip
    w("00000001" "00000001"),  # 45 NẠP 1
    w("00001010" "00000000"),  # 46 CỘNG           ; ip+1
    w("00011101" "00000000"),  # 47 TẢI_GIÁN       ; ram[ip+1] = chữ số
    w("00000001" "00110000"),  # 48 NẠP 48
    w("00001011" "00000000"),  # 49 TRỪ            ; trị = mã - 48
    w("00001010" "00000000"),  # 50 CỘNG           ; word = (op<<8)+trị
    w("00011000" "11111101"),  # 51 TẢI_Ô 253      ; out
    w("00010110" "00000000"),  # 52 ĐỔI            ; [out, word]
    w("00011110" "00000000"),  # 53 LƯU_GIÁN       ; ram[out] = word
    w("00011000" "11111101"),  # 54 TẢI_Ô 253
    w("00000001" "00000001"),  # 55 NẠP 1
    w("00001010" "00000000"),  # 56 CỘNG
    w("00011001" "11111101"),  # 57 LƯU_Ô 253      ; out += 1
    w("00011000" "11111010"),  # 58 TẢI_Ô 250
    w("00000001" "00000010"),  # 59 NẠP 2
    w("00001010" "00000000"),  # 60 CỘNG
    w("00011001" "11111010"),  # 61 LƯU_Ô 250      ; ip += 2
    w("00001111" "00000000"),  # 62 NHẢY 0         ; → LOOP
    w("00010101" "00000000"),  # 63 BỎ             ; DONE: bỏ ch
    w("00000000" "00000000"),  # 64 DỪNG
]

# ===== Nguồn 'hợp ngữ văn bản' =====
SRC_TEXT = "H0G0R0D0."
ram = [0]*256
for i, ch in enumerate(SRC_TEXT): ram[i] = ord(ch)   # nạp văn bản dưới dạng mã ASCII
ram[250] = 0       # ip
ram[253] = 100     # out

if __name__ == "__main__":
    print("="*66)
    print("ASSEMBLER MỨC 2 (mã máy gõ tay) — xác minh bằng disasm (chỉ GIẢI mã)")
    print("="*66)
    for i, word in enumerate(ASM2):
        print(f"  {i:02d}:  {disasm_word(word)}")

    print("\n" + "="*66)
    print(f"CHẠY: hợp dịch văn bản  {SRC_TEXT!r}  (mã ASCII: {[ord(c) for c in SRC_TEXT]})")
    print("="*66)
    m = GVM(ASM2, world={}, ram=ram)
    m.run()
    n = SRC_TEXT.index(".") // 2
    out = m.ram[100:100+n]
    print(f"  RAM ra [100..]: {out}")
    print("  Giải mã các lệnh assembler vừa sinh từ VĂN BẢN:")
    for k, word in enumerate(out):
        print(f"     {100+k}:  {word:5d}  →  {disasm_word(word)}")

    print("\n" + "="*66)
    print("ĐÓNG VÒNG: chạy chương trình vừa hợp dịch (world vật0=37)")
    print("="*66)
    GVM(out, world={0: 37}).run()
    print("\n   → Assembler ĐỌC VĂN BẢN, gõ tay, chạy bằng máy. Python không hợp dịch.")

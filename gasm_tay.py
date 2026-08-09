# -*- coding: utf-8 -*-
"""
HẠT MỒI MỨC 0 — HỢP DỊCH BẰNG TAY
==================================
Đây KHÔNG dùng trình hợp dịch viết bằng Python. Mỗi từ-lệnh 16 bit dưới đây do
CON NGƯỜI gõ ra bằng tay từ bảng opcode — đúng cách assembler ĐẦU TIÊN của lịch sử
được gieo mầm. Python ở đây CHỈ đóng vai CPU (lớp GVM nạp–giải mã–thực thi từng từ);
nó KHÔNG dịch hợp ngữ. int("...",2) chỉ là cách ghi lại chính những bit đã gõ tay.

Bảng opcode (xem gvm_may.OPS):
    DỪNG=0  HỌC=7  GIAO=8  RỌI=14  NHẢY_ĐỘNG=19  TÁC_TỬ=23
Khuôn lệnh:  [opcode : 8 bit][operand : 8 bit]

Chương trình hợp ngữ muốn mã hoá:
        TÁC_TỬ 0
   LẶP: HỌC 0
        GIAO 0
        RỌI
        NHẢY_ĐỘNG LẶP     ; LẶP = địa chỉ 1
        DỪNG
"""
from gvm_may import GVM, disasm_word

# ---- HỢP DỊCH BẰNG TAY: gõ từng bit, kèm cách suy ra ----
# addr | opcode(8b) | operand(8b) | ý nghĩa
MA_MAY_BANG_TAY = [
    int("00010111" "00000000", 2),  # 0: TÁC_TỬ(23=00010111) 0   → chọn tác tử 0
    int("00000111" "00000000", 2),  # 1: HỌC(7=00000111)    0   ← nhãn LẶP
    int("00001000" "00000000", 2),  # 2: GIAO(8=00001000)   0
    int("00001110" "00000000", 2),  # 3: RỌI(14=00001110)
    int("00010011" "00000001", 2),  # 4: NHẢY_ĐỘNG(19=00010011) 1  → quay về addr 1
    int("00000000" "00000000", 2),  # 5: DỪNG(0)
]

# Thế giới (dữ liệu, không phải hợp ngữ): vật0 = 37
THE_GIOI = {0: 37}

if __name__ == "__main__":
    print("="*64)
    print("MÃ MÁY GÕ TAY (không qua assembler Python) — kiểm chứng bằng disasm")
    print("="*64)
    for i, w in enumerate(MA_MAY_BANG_TAY):
        print(f"  {i:02d}:  {disasm_word(w)}")

    print("\n" + "="*64)
    print("THỰC THI trên CPU GVM (Python chỉ nạp–giải mã–thực thi)")
    print("="*64)
    GVM(MA_MAY_BANG_TAY, THE_GIOI).run()
    print("\n   → Mã máy này do TAY tạo. Python không hề hợp dịch — chỉ chạy bit.")
    print("   Bước kế: viết assembler BẰNG hợp ngữ GVM rồi gõ-tay-một-lần thành mã máy.")

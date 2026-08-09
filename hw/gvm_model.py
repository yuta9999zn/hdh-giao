# -*- coding: utf-8 -*-
"""
gvm_model.py — Mô hình CHU-KỲ-CHÍNH-XÁC mô phỏng FSM của gvm.v (vì không có trình
mô phỏng Verilog tại đây). Đọc thẳng boot ROM TỪ gvm.v và chạy ĐÚNG ngữ nghĩa FSM
(kể cả GỌI HÀM theo khung + HEAP gián tiếp) để xác minh thiết kế.
Boot ROM hiện tại: nhân_đôi(21)=42, rồi heap ram[50]=99 → xuất [42, 99].
"""
import re, os

OP = dict(DUNG=0, NAP=1, CONG=10, TRU=11, NHAN=12, ROI=14, NHAY=15, NHAN_BAN=20, BO=21,
          TAI_O=24, LUU_O=25, NHAY_0=28, TAI_GIAN=29, LUU_GIAN=30,
          GOI_N=38, THAM_I=39, TRA_VE_N=40, CHIA=47,
          BANG=41, KHAC=42, BE_HON=43, LON_HON=44, BE_BANG=45, LON_BANG=46,
          DICH_TRAI=26, NHAY_X=35, NHAY_0_X=36)

def sgn(x):                               # diễn giải 16-bit có dấu
    return x - 0x10000 if x >= 0x8000 else x

def đọc_rom():
    src = open(os.path.join(os.path.dirname(__file__), "gvm.v"), encoding="utf-8").read()
    rom = {int(i): int(h, 16) for i, h in
           re.findall(r"rom\[(\d+)\]\s*=\s*16'h([0-9A-Fa-f]+)", src)}
    return [rom.get(i, 0) for i in range(max(rom) + 1)]

def chạy(rom, mem=4096):
    ram = [0]*mem; stack = [0]*mem
    rstk_ip = [0]*mem; rstk_fp = [0]*mem
    ip = sp = fp = rsp = 0
    state = "FETCH"; instr = 0; halt = False; outs = []; chu_kỳ = 0
    M16 = 0xFFFF; B8 = 0xFF; A = 0xFFF
    while not halt and chu_kỳ < 200000:
        chu_kỳ += 1
        if state == "FETCH":
            instr = rom[ip] if ip < len(rom) else 0
            ip = (ip + 1) & M16; state = "EXEC"
        else:
            op = (instr >> 8) & 0xFF; arg = instr & 0xFF
            state = "FETCH"
            if   op == OP["NAP"]:      stack[sp] = arg; sp += 1
            elif op == OP["TAI_O"]:    stack[sp] = ram[arg]; sp += 1
            elif op == OP["LUU_O"]:    ram[arg] = stack[sp-1]; sp -= 1
            elif op == OP["CONG"]:     stack[sp-2] = (stack[sp-2] + stack[sp-1]) & M16; sp -= 1
            elif op == OP["TRU"]:      stack[sp-2] = (stack[sp-2] - stack[sp-1]) & M16; sp -= 1
            elif op == OP["NHAN"]:     stack[sp-2] = (sgn(stack[sp-2]) * sgn(stack[sp-1])) & M16; sp -= 1
            elif op == OP["CHIA"]:
                b = sgn(stack[sp-1])
                stack[sp-2] = (0 if b == 0 else int(sgn(stack[sp-2]) / b)) & M16; sp -= 1
            elif op == OP["BANG"]:    stack[sp-2] = 1 if stack[sp-2]==stack[sp-1] else 0; sp -= 1
            elif op == OP["KHAC"]:    stack[sp-2] = 1 if stack[sp-2]!=stack[sp-1] else 0; sp -= 1
            elif op == OP["BE_HON"]:  stack[sp-2] = 1 if sgn(stack[sp-2]) <  sgn(stack[sp-1]) else 0; sp -= 1
            elif op == OP["LON_HON"]: stack[sp-2] = 1 if sgn(stack[sp-2]) >  sgn(stack[sp-1]) else 0; sp -= 1
            elif op == OP["BE_BANG"]: stack[sp-2] = 1 if sgn(stack[sp-2]) <= sgn(stack[sp-1]) else 0; sp -= 1
            elif op == OP["LON_BANG"]:stack[sp-2] = 1 if sgn(stack[sp-2]) >= sgn(stack[sp-1]) else 0; sp -= 1
            elif op == OP["NHAN_BAN"]: stack[sp] = stack[sp-1]; sp += 1
            elif op == OP["BO"]:       sp -= 1
            elif op == OP["ROI"]:      outs.append(stack[sp-1]); sp -= 1
            elif op == OP["NHAY"]:     ip = arg
            elif op == OP["NHAY_0"]:
                if stack[sp-1] == 0: ip = arg
                sp -= 1
            elif op == OP["DICH_TRAI"]: stack[sp-1] = (stack[sp-1] << arg) & M16
            elif op == OP["NHAY_X"]:   ip = stack[sp-1]; sp -= 1
            elif op == OP["NHAY_0_X"]:
                if stack[sp-1] == 0: ip = stack[sp-2]
                sp -= 2
            # --- HEAP ---
            elif op == OP["TAI_GIAN"]: stack[sp-1] = ram[stack[sp-1] & A]
            elif op == OP["LUU_GIAN"]: ram[stack[sp-2] & A] = stack[sp-1]; sp -= 2
            # --- GỌI HÀM theo KHUNG (đọc giá trị CŨ trước khi cập nhật, như non-blocking) ---
            elif op == OP["GOI_N"]:
                target = stack[sp-1]; ofp = fp; orsp = rsp
                rstk_ip[orsp] = ip; rstk_fp[orsp] = ofp
                fp = (sp - 1 - arg) & B8; rsp = (orsp + 1) & B8
                ip = target; sp -= 1
            elif op == OP["THAM_I"]:   stack[sp] = stack[fp + arg]; sp += 1
            elif op == OP["TRA_VE_N"]:
                result = stack[sp-1]; ofp = fp; orsp = rsp
                stack[ofp] = result; sp = (ofp + 1) & B8
                ip = rstk_ip[orsp-1]; fp = rstk_fp[orsp-1]; rsp = (orsp - 1) & B8
            elif op == OP["DUNG"]:     halt = True
            else:                      halt = True
            sp &= B8
    return outs, chu_kỳ, halt

if __name__ == "__main__":
    rom = đọc_rom()
    print(f"Boot ROM: {len(rom)} từ-lệnh đọc từ gvm.v")
    outs, chu_kỳ, halt = chạy(rom)
    print(f"Chạy {chu_kỳ} chu kỳ clock, dừng={halt}")
    print(f"RỌI = {outs}   (mong đợi [42,99,3,1,54,7] = gọi hàm/heap/÷/so sánh/×/nhảy gián tiếp)")
    print("KIỂM CHỨNG:", "✓ THIẾT KẾ ĐÚNG" if outs == [42, 99, 3, 1, 54, 7] else "✗ SAI")

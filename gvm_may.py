# -*- coding: utf-8 -*-
"""
GVM-MÁY — CPU CỦA GIAO  (B+ : ISA đầy đủ + assembler .gasm + đa tác tử)
======================================================================
Xây THẲNG trên ALU của gvm.py (mọi số học bắt nguồn từ DUY NHẤT cổng NAND).

Khác mọi CPU hiện có:
  • Ô nhớ = Ô TRIT–CỘNG HƯỞNG: [trạng thái 2 bit][giá trị 16 bit][γ 8 bit].
  • 'ẩn' (DE) LAN TRUYỀN ở tầng máy: cộng/trừ/đối chiếu chạm ẩn → ẩn.
  • RẼ NHÁNH theo CỘNG HƯỞNG: NHẢY_SÁNG/TỐI/ẨN/ĐỘNG thay cho cờ ZF/CF/SF.
  • ĐA TÁC TỬ: nhiều ngân hàng niềm tin (tâm) chung một thế giới (vật) → OR TẬP THỂ.

Dùng:
  python gvm_may.py                 # chạy demo nhúng (qua assembler)
  python gvm_may.py prog.gasm       # hợp dịch & chạy một tệp .gasm
"""
import sys
from gvm import int_to_bits, bits_to_int, bits_str, ripple_add, sub, ashr1, is_zero

def _s16(x):                      # diễn giải 16-bit CÓ DẤU (two's complement)
    x &= 0xFFFF
    return x - 0x10000 if x >= 0x8000 else x

# ============================================================
# Ô NHỚ GIAO — đơn vị máy mang cộng hưởng
# ============================================================
ST_AN, ST_SANG, ST_TOI = 0b00, 0b01, 0b10
ST_NAME = {ST_AN:"ẩn", ST_SANG:"sáng", ST_TOI:"tối"}

def cell(state, val=0, gam=0.0, note=None):
    return {"st": state, "val": val, "gam": gam, "note": note}
ANCELL = lambda: cell(ST_AN, 0, 0.0)
KNOWN  = lambda n: cell(ST_SANG, n, 1.0)

def word_bits(c):
    "[state:2].[val:16].[γ:8] — để NHÌN THẤY 0/1."
    st  = format(c["st"], "02b")
    val = bits_str(int_to_bits(c["val"] if c["val"] is not None else 0))
    g   = int(max(-1.0, min(1.0, c["gam"] if c["gam"] is not None else 0.0)) * 100)
    return f"{st}.{val}.{format(g & 0xFF, '08b')}"

def show_cell(c):
    note = f"   {{{c['note']}}}" if c.get("note") else ""
    if c["st"] == ST_AN: return f"ẩn        | {word_bits(c)}{note}"
    return f"{ST_NAME[c['st']]:>4}={c['val']:<4} γ={c['gam']:+.2f} | {word_bits(c)}{note}"

def fmt_fixed(v):
    "Số ĐIỂM-CỐ-ĐỊNH ×10000 → chuỗi thập phân: ≤4 chữ số lẻ, bỏ '0' đuôi. (Trùng khít wasm.)"
    neg = v < 0; a = -v if neg else v
    s = ("-" if neg else "") + str(a // 10000)
    fr = ("%04d" % (a % 10000)).rstrip("0")
    return s + ("." + fr if fr else "")

def resonance(belief, truth):
    if belief["st"] == ST_AN or truth["st"] == ST_AN: return ANCELL()
    d = abs(truth["val"] - belief["val"]); scale = max(abs(truth["val"]), 1)
    gam = max(-1.0, min(1.0, 1.0 - 2.0*d/scale))
    st = ST_SANG if gam > 0 else (ST_TOI if gam < 0 else ST_AN)
    return cell(st, belief["val"], gam)

# ============================================================
# BỘ LỆNH (ISA) — mỗi opcode là số nhị phân; lệnh = [opcode:8][operand:8]
# ============================================================
OPS = {
    "DỪNG":0, "NẠP":1, "ẨN":2,
    "TẢI_VẬT":3, "TẢI_TÂM":4, "LƯU_TÂM":5, "LƯU_VẬT":6,
    "HỌC":7, "GIAO":8, "GIAO_CHUNG":9,
    "CỘNG":10, "TRỪ":11, "NHÂN":12, "SO_SÁNH":13, "RỌI":14,
    "NHẢY":15, "NHẢY_SÁNG":16, "NHẢY_TỐI":17, "NHẢY_ẨN":18, "NHẢY_ĐỘNG":19,
    "NHÂN_BẢN":20, "BỎ":21, "ĐỔI":22, "TÁC_TỬ":23,
    # — máy đa dụng (nền để chạy assembler viết bằng hợp ngữ) —
    "TẢI_Ô":24, "LƯU_Ô":25, "DỊCH_TRÁI":26, "DỊCH_PHẢI":27, "NHẢY_NẾU_0":28,
    "TẢI_GIÁN":29, "LƯU_GIÁN":30,
    # — gọi hàm/đệ quy (1 tham số): ngăn xếp tham số + địa chỉ trả về —
    "GỌI":31, "TRẢ_VỀ":32, "THAM":33,
    "RỌI_CHUỖI":34,   # in chuỗi = duyệt danh-sách mã-ký-tự trên heap
    # — nhảy/gọi GIÁN TIẾP: địa chỉ 16-bit lấy từ ngăn xếp (cho chương trình >256 lệnh) —
    "NHẢY_X":35, "NHẢY_NẾU_0_X":36, "GỌI_X":37,
    # — gọi hàm NHIỀU THAM SỐ theo KHUNG (frame) —
    "GỌI_N":38, "THAM_I":39, "TRẢ_VỀ_N":40,
    # — so sánh: đẩy 1 (đúng) / 0 (sai) —
    "BẰNG":41, "KHÁC":42, "BÉ_HƠN":43, "LỚN_HƠN":44, "BÉ_BẰNG":45, "LỚN_BẰNG":46,
    "CHIA":47,   # chia số nguyên (b=0 → 0)
    "RỌI_DS":48, # in DANH SÁCH số (duyệt heap, gỡ thẻ) — PEEK, không pop
    "XUẤT":49,   # MMIO console: pop → in số (kèm nhãn tiến trình) — cho HĐH đa nhiệm
    # — NGẮT TIMER phần cứng (preemption ở silicon — xem hw/gvm.v) —
    "BẬT_NGẮT":50,  # pop địa chỉ handler → bật ngắt timer
    "TẮT_NGẮT":51,  # tắt ngắt
    "HẸN_GIỜ":52,   # đặt chu kỳ timer (operand = số chu kỳ clock)
    "NGẮT_VỀ":53,   # IRET — quay về điểm bị ngắt
    "TÁC_VỤ":54,    # pop entry_ip → đăng ký một tiến trình (ngân hàng thanh ghi)
    "LẬP_LỊCH":55,  # khởi động ĐA NHIỆM TIỀN-ĐỊNH (round-robin)
    "LỊCH_HỌC":56,  # khởi động LẬP LỊCH CDFL BIẾT-HỌC ở phần cứng (lập lịch theo cộng hưởng γ)
    "BẬT_SIP":57,   # bật CÔ LẬP tiến trình (base+bound relocation, không MMU)
    "GỌI_CLOSURE":58,  # gọi CLOSURE (giá trị hàm hạng nhất): khung = [bắt…, đối…] → nhảy mã
    # — SỐ THỰC dạng ĐIỂM-CỐ-ĐỊNH thập phân (×10000); số nguyên DSP, KHÔNG FPU (hợp silicon) —
    "FNHÂN":59,    # nhân điểm-cố-định: (a*b)/10000, trung gian 64-bit, cắt-về-0
    "FCHIA":60,    # chia điểm-cố-định: (a*10000)/b, 64-bit, cắt-về-0; b=0 → ẩn
    "RỌI_THỰC":61, # in số ×10000 dạng thập phân (≤4 chữ số lẻ, bỏ số 0 đuôi)
    # — NGOẠI LỆ (thử/bắt): ngăn xếp HANDLER + ném/gỡ-cuộn (unwind) —
    "BẮT_ĐẦU_THỬ":62,  # pop địa chỉ handler → đẩy bản ghi handler (lưu sâu các ngăn xếp)
    "HẾT_THỬ":63,      # thử xong êm → gỡ handler trên cùng
    "NÉM":64,          # pop trị-lỗi → gỡ-cuộn về handler gần nhất (đẩy trị-lỗi, nhảy); rỗng → DỪNG
    "RỌI_AUTO":65,     # IN tự-suy-kiểu lúc CHẠY: con trỏ chuỗi (bit30) → chuỗi; ngược lại → số
    # — BIẾN CỤC BỘ theo KHUNG (đặt trong hàm = ô-khung per-call, KHÔNG còn ô-toàn-cục) —
    "DÀNH_CB":66,      # dành 'arg' ô cục bộ ở cuối khung (khởi 0) — prologue hàm/closure
    "LƯU_THAM_I":67,   # pop → ghi vào ô THAM_I thứ 'arg' của khung (gán biến cục bộ/tham số)
    # — ★ SIÊU-LỆNH (Pha 3 / Track M co-design ISA): gộp idiom thường-gặp thành 1 opcode, giảm BƯỚC thật —
    "CỘNG_HẰNG":68,    # add-immediate: pop → push (top + arg) — gộp `NẠP k; CỘNG`. Ba-trị: ẩn→ẩn (y hệt CỘNG).
    "NHÂN_CỘNG_HẰNG":69,  # dup+add-imm: [x] → [x, x+arg] (heap-cons: hp, hp+k) — gộp `NHÂN_BẢN; CỘNG_HẰNG k`. Stack-only.
    "GHI_TRƯỜNG":70,   # store-field: ram[top] = ram[arg], GIỮ top — gộp `NHÂN_BẢN; TẢI_Ô arg; LƯU_GIÁN`. RAM-to-RAM.
    "DỊCH_CỘNG_BYTE":71,  # dựng-hằng: top ← (top<<8)+arg — gộp `DỊCH_TRÁI 8; CỘNG_HẰNG k`. Stack-only, ẩn→ẩn. (đánh con voi NẠP+DỊCH 38.6%)
    # — ★ GỌI-HỆ: TRAP về NHÂN (như `syscall`/`int 0x80`): pop `arg` đối + pop số hiệu → TẠM DỪNG,
    #   nhân phục vụ xong đẩy kết quả vào ngăn xếp rồi cho chạy tiếp. Máy KHÔNG tự làm I/O.
    "GỌI_HỆ":72,
}
FSCALE = 10000     # thang điểm-cố-định: x_thực ≈ round(x*10000)
HAS_ARG = {"NẠP","TẢI_VẬT","TẢI_TÂM","LƯU_TÂM","LƯU_VẬT","HỌC","GIAO","GIAO_CHUNG",
           "NHẢY","NHẢY_SÁNG","NHẢY_TỐI","NHẢY_ẨN","NHẢY_ĐỘNG","TÁC_TỬ",
           "TẢI_Ô","LƯU_Ô","DỊCH_TRÁI","DỊCH_PHẢI","NHẢY_NẾU_0","GỌI","GỌI_N","THAM_I","HẸN_GIỜ","GỌI_CLOSURE",
           "DÀNH_CB","LƯU_THAM_I","CỘNG_HẰNG","NHÂN_CỘNG_HẰNG","DỊCH_CỘNG_BYTE","GỌI_HỆ"}
OP_NAME = {v:k for k,v in OPS.items()}

# ============================================================
# ASSEMBLER (PYTHON) — CHỈ LÀ GIÀN GIÁO SOẠN THẢO, *KHÔNG* thuộc chuỗi mồi.
# Dùng để thử nghiệm/đối chiếu khi đang phát triển. Chuỗi mồi THẬT đi qua
# hợp-dịch-bằng-tay (gasm_tay.py) rồi assembler-viết-bằng-hợp-ngữ. Khi assembler
# tự thân chạy được, hàm Python này bị loại bỏ.
# ============================================================
def assemble_text(src):
    "Trả (code:[int], world:{addr:val}). Hai lượt: thu nhãn rồi phát mã."
    raw = []          # (mnemonic, arg_token|None, line_no)
    world = {}
    for ln, line in enumerate(src.splitlines(), 1):
        for sep in (";", "#"):                      # bỏ chú thích
            if sep in line: line = line[:line.index(sep)]
        line = line.strip()
        if not line: continue
        if line.startswith("."):                    # chỉ thị
            parts = line.replace("="," ").split()
            if parts[0].upper() == ".VẬT" or parts[0] == ".VẬT":
                world[int(parts[1])] = int(parts[2])
            else:
                raise SyntaxError(f"Dòng {ln}: chỉ thị lạ {parts[0]}")
            continue
        if line.endswith(":"):                       # nhãn đứng riêng
            raw.append(("@LABEL", line[:-1].strip(), ln)); continue
        toks = line.split()
        # nhãn dính đầu dòng:  LẶP: HỌC 0
        if toks[0].endswith(":"):
            raw.append(("@LABEL", toks[0][:-1], ln)); toks = toks[1:]
            if not toks: continue
        mn = toks[0]; arg = toks[1] if len(toks) > 1 else None
        raw.append((mn, arg, ln))

    # lượt 1: gán địa chỉ cho nhãn (đếm theo lệnh thực, bỏ qua @LABEL)
    labels, idx = {}, 0
    for mn, arg, ln in raw:
        if mn == "@LABEL": labels[arg] = idx
        else: idx += 1
    # lượt 2: phát mã
    code = []
    for mn, arg, ln in raw:
        if mn == "@LABEL": continue
        if mn not in OPS: raise SyntaxError(f"Dòng {ln}: lệnh lạ '{mn}'")
        a = 0
        if mn in HAS_ARG:
            if arg is None: raise SyntaxError(f"Dòng {ln}: '{mn}' cần toán hạng")
            a = labels[arg] if arg in labels else int(arg)
        code.append((OPS[mn] << 8) | (a & 0xFF))
    return code, world

def disasm_word(w):
    op = (w >> 8) & 0xFF; a = w & 0xFF; name = OP_NAME[op]
    arg = f" {a}" if name in HAS_ARG else ""
    return f"{format(w,'016b')}   {name}{arg}"

# ============================================================
# MÁY ẢO
# ============================================================
class GVM:
    def __init__(self, code, world, ram=None, bit=16):
        self.code = code
        self.vat = {a: KNOWN(v) for a, v in world.items()}
        self.banks = {}          # đa tác tử: {agent: {addr: cell}}
        self.agent = 0
        self.stack = []
        self.ip = 0
        self.moved = True
        self.cur_task = ""       # nhãn tiến trình hiện hành (HĐH đa nhiệm tiền-định)
        self.out_count = 0       # số lần XUẤT (đo 'công việc hữu ích' cho lập lịch CDFL)
        self.last_list = None    # danh sách số do RỌI_DS in gần nhất (để harness lấy ra chạy tiếp)
        self.xuất = []           # OUTPUT có cấu trúc (đối chiếu đa-substrate): ["ô",st,val]|["chuỗi",s]|["ds",[..]]
        self.ram = list(ram) if ram is not None else [0]*65536  # RAM 64K ô (đủ heap cho danh sách)
        self.pstack = []     # ngăn xếp tham số hàm (phẳng, nhiều khung)
        self.rstack = []     # ngăn xếp địa chỉ trả về
        self.fp_stack = []   # ngăn xếp khung: (đáy_khung, số_tham_số)
        self.handlers = []   # ngăn xếp handler thử/bắt: (ip, sâu_stack, sâu_fp, sâu_pstack, sâu_rstack)
        self.tasks = []      # entry-ip các tiến trình đăng ký (TÁC_VỤ) cho γ-scheduler
        self.timer_period = 4  # lượng tử (HẸN_GIỜ) — số lệnh trước khi BỊ CƯỚP CPU
        self.did_out = False   # tiến trình hiện hành có XUẤT/RỌI trong lượng tử? (ρ cho γ-scheduler)
        self.trap = None       # ★ GỌI_HỆ đang chờ nhân phục vụ: (số_hiệu, [đối thô])
        self.trap_pending = False
        self.fault_code = None # NÉM chưa bắt → mã lỗi để SUPERVISOR (scheduler) CÔ LẬP tiến trình
        # — ĐỘ RỘNG TỪ là tham số: 16/32/64/128/256-bit —
        self.bit  = bit
        self.MASK = (1 << bit) - 1
        self.HALF = 1 << (bit - 1)
        self.MOD  = 1 << bit

    def s(self, x):                          # diễn giải CÓ DẤU theo độ rộng từ
        x &= self.MASK
        return x - self.MOD if x >= self.HALF else x

    def bank(self):  return self.banks.setdefault(self.agent, {})
    def tam_cell(self, a): return self.bank().get(a, ANCELL())
    def vat_cell(self, a): return self.vat.get(a, ANCELL())

    def step(self):
        w = self.code[self.ip]; op = (w >> 8) & 0xFF; arg = w & 0xFF; self.ip += 1
        name = OP_NAME[op]
        if   name == "DỪNG": return False
        elif name == "NẠP":  self.stack.append(KNOWN(arg))
        elif name == "ẨN":   self.stack.append(ANCELL())
        elif name == "TẢI_VẬT": self.stack.append(dict(self.vat_cell(arg)))
        elif name == "TẢI_TÂM": self.stack.append(dict(self.tam_cell(arg)))
        elif name == "LƯU_TÂM": self.bank()[arg] = self.stack.pop()
        elif name == "LƯU_VẬT": self.vat[arg] = self.stack.pop()
        elif name == "TÁC_TỬ":  self.agent = arg
        elif name == "HỌC":     self.hoc(arg)
        elif name == "GIAO":    self.stack.append(resonance(self.tam_cell(arg), self.vat_cell(arg)))
        elif name == "GIAO_CHUNG": self.stack.append(self.giao_chung(arg))
        elif name == "CỘNG":    self.binop(lambda a,b: a+b)
        elif name == "CỘNG_HẰNG":                 # ★ siêu-lệnh add-immediate: top + arg (ba-trị: ẩn→ẩn)
            c = self.stack.pop()
            self.stack.append(ANCELL() if c["st"] == ST_AN else KNOWN((c["val"] + arg) & self.MASK))
        elif name == "NHÂN_CỘNG_HẰNG":            # ★ siêu-lệnh #2 dup+add-imm: [x] → [x, x+arg] (GIỮ x, đẩy x+arg)
            c = self.stack[-1]                     # PEEK (x ở dưới giữ nguyên)
            self.stack.append(ANCELL() if c["st"] == ST_AN else KNOWN((c["val"] + arg) & self.MASK))
        elif name == "GHI_TRƯỜNG":                # ★ siêu-lệnh #3 store-field: ram[top] = ram[arg], GIỮ top
            self.ram[self.stack[-1]["val"]] = self.ram[arg]   # ≡ NHÂN_BẢN; TẢI_Ô arg; LƯU_GIÁN (ram[idx=top]=val=ram[arg])
        elif name == "DỊCH_CỘNG_BYTE":            # ★ siêu-lệnh #4 dựng-hằng: top ← (top<<8)+arg ≡ DỊCH_TRÁI 8; CỘNG_HẰNG arg (ba-trị: ẩn→ẩn)
            c = self.stack.pop()
            self.stack.append(ANCELL() if c["st"] == ST_AN else KNOWN((((c["val"] << 8) & self.MASK) + arg) & self.MASK))
        elif name == "TRỪ":     self.binop(lambda a,b: a-b)
        elif name == "NHÂN":    self.binop(lambda a,b: a*b)
        elif name == "CHIA":    self.binop(lambda a,b: int(self.s(a)/self.s(b)) if b!=0 else 0)  # chia CÓ DẤU, cắt-về-0
        elif name == "FNHÂN":   self.fbin("*")    # số thực: (a*b)/10000
        elif name == "FCHIA":   self.fbin("/")    # số thực: (a*10000)/b
        elif name == "RỌI_THỰC":
            c = self.stack.pop()
            if c["st"] == ST_AN:
                print("   " + show_cell(c)); self.xuất.append(["ô", c["st"], c["val"]])
            else:
                s = fmt_fixed(self.s(c["val"])); print("   " + s); self.xuất.append(["chuỗi", s])
        elif name == "BẮT_ĐẦU_THỬ":               # mở vùng thử: lưu địa chỉ handler + sâu các ngăn xếp
            h = self.stack.pop()["val"]
            self.handlers.append((h, len(self.stack), len(self.fp_stack),
                                  len(self.pstack), len(self.rstack)))
        elif name == "HẾT_THỬ":                    # thử xong êm
            self.handlers.pop()
        elif name == "NÉM":                        # ném lỗi → gỡ-cuộn về handler gần nhất
            err = self.stack.pop()["val"]
            if not self.handlers:
                self.fault_code = self.s(err)   # chưa bắt → LỖI; supervisor/scheduler sẽ CÔ LẬP
                return False                     # DỪNG sạch (xuất giữ nguyên: trùng wasm `break`)
            hip, ss, sf, sp_, sr = self.handlers.pop()
            del self.stack[ss:]; del self.fp_stack[sf:]                   # gỡ-cuộn mọi khung lồng
            del self.pstack[sp_:]; del self.rstack[sr:]
            self.stack.append(KNOWN(err)); self.ip = hip                  # trao trị-lỗi cho nhánh bắt
        elif name == "RỌI_AUTO":                   # IN tự-suy-kiểu lúc chạy (cho rọi giá trị chưa rõ kiểu)
            c = self.stack.pop()
            if c["st"] != ST_AN and (c["val"] & 0xC0000000) == 0x40000000:   # con trỏ chuỗi (bit30=1, bit31=0)
                a = c["val"] & 0x3FFFFFFF; out = []
                while a != 0 and len(out) < 100000:
                    out.append(chr(self.ram[a] & 0x1FFFFF)); a = self.ram[a + 1] & 0x3FFFFFFF
                s = "".join(out); print(s); self.xuất.append(["chuỗi", s])
            else:                                                            # ẩn / số → in như RỌI
                print("   " + show_cell(c)); self.xuất.append(["ô", c["st"], c["val"]])
        elif name == "SO_SÁNH":
            b = self.stack.pop(); a = self.stack.pop(); self.stack.append(resonance(a, b))
        elif name == "RỌI":
            c = self.stack.pop(); print("   " + show_cell(c)); self.xuất.append(["ô", c["st"], c["val"]])
            self.did_out = True                   # ρ=1 (như silicon OP_ROI): có làm việc hữu ích
        elif name == "NHẢY":      self.ip = arg
        elif name == "NHẢY_SÁNG": self.branch_state(arg, ST_SANG)
        elif name == "NHẢY_TỐI":  self.branch_state(arg, ST_TOI)
        elif name == "NHẢY_ẨN":   self.branch_state(arg, ST_AN)
        elif name == "NHẢY_ĐỘNG":
            if self.moved: self.ip = arg
        elif name == "NHÂN_BẢN":  self.stack.append(dict(self.stack[-1]))
        elif name == "BỎ":        self.stack.pop()
        elif name == "ĐỔI":       self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]
        # — máy đa dụng —
        elif name == "TẢI_Ô":     self.stack.append(KNOWN(self.ram[arg]))
        elif name == "LƯU_Ô":     self.ram[arg] = self.stack.pop()["val"]
        elif name == "DỊCH_TRÁI": self.shift(lambda v: v << arg)
        elif name == "DỊCH_PHẢI": self.shift(lambda v: v >> arg)
        elif name == "TẢI_GIÁN":  self.stack.append(KNOWN(self.ram[self.stack.pop()["val"]]))
        elif name == "LƯU_GIÁN":
            val = self.stack.pop(); idx = self.stack.pop(); self.ram[idx["val"]] = val["val"]
        elif name == "NHẢY_NẾU_0":
            c = self.stack.pop()
            if c["st"] != ST_AN and c["val"] == 0: self.ip = arg
        # — gọi hàm —
        elif name == "GỌI":                       # đối ở đỉnh ngăn xếp → tham số; lưu ip về
            self.pstack.append(self.stack.pop()["val"])
            self.rstack.append(self.ip); self.ip = arg
        elif name == "TRẢ_VỀ":                    # trị trả về NẰM LẠI trên ngăn xếp
            self.ip = self.rstack.pop(); self.pstack.pop()
        elif name == "THAM":                      # đẩy tham số hiện hành
            self.stack.append(KNOWN(self.pstack[-1]))
        elif name == "XUẤT":                      # MMIO console (HĐH): in số kèm nhãn tiến trình
            print(f"   ⟨{self.cur_task}⟩ {self.s(self.stack.pop()['val'])}")
            self.out_count += 1; self.did_out = True          # ρ=1: tiến trình LÀM VIỆC HỮU ÍCH (cho γ)
        elif name == "HẸN_GIỜ":                   # đặt LƯỢNG TỬ (chu kỳ timer) cho γ-scheduler
            self.timer_period = arg if arg > 0 else 1
        elif name == "TÁC_VỤ":                    # pop entry-ip → ĐĂNG KÝ một tiến trình
            self.tasks.append(self.stack.pop()["val"])
        elif name == "LỊCH_HỌC":                  # khởi động γ-SCHEDULER CDFL (preemptive, biết-học)
            self.lập_lịch_học(); return False     # chạy bộ lập lịch rồi DỪNG (demo có biên)
        elif name == "RỌI_DS":                    # in danh-sách SỐ (mỗi phần tử một dòng) — PEEK
            a = self.stack[-1]["val"] & 0x3FFFFFFF; i = 0; self.last_list = []
            while a != 0 and i < 100000:
                v = self.s(self.ram[a]); print("   " + str(v)); self.last_list.append(v)
                a = self.ram[a + 1] & 0x3FFFFFFF; i += 1
            self.xuất.append(["ds", list(self.last_list)])
        elif name == "GỌI_HỆ":                    # ★ TRAP: máy dừng, nhường quyền cho NHÂN
            n = arg
            đối = []
            for _ in range(n): đối.append(self.stack.pop()["val"])
            đối.reverse()
            số = self.stack.pop()["val"]
            self.trap = (self.s(số), đối)         # nhân sẽ đọc, phục vụ, rồi `máy_trả` kết quả
            self.trap_pending = True              # run() thấy cờ này thì TẠM DỪNG (chưa halt)
        elif name == "RỌI_CHUỖI":                 # duyệt danh-sách mã-ký-tự → in chuỗi
            a = self.stack.pop()["val"] & 0x3FFFFFFF; out = []   # gỡ THẺ danh-sách (bit 30)
            while a != 0 and len(out) < 100000:
                out.append(chr(self.ram[a] & 0x1FFFFF)); a = self.ram[a + 1] & 0x3FFFFFFF
            print("".join(out)); self.xuất.append(["chuỗi", "".join(out)])
        # — nhảy/gọi gián tiếp (địa chỉ từ ngăn xếp) —
        elif name == "NHẢY_X":
            self.ip = self.stack.pop()["val"]
        elif name == "NHẢY_NẾU_0_X":
            c = self.stack.pop(); t = self.stack.pop()
            if c["st"] != ST_AN and c["val"] == 0: self.ip = t["val"]
        elif name == "GỌI_X":
            t = self.stack.pop(); a = self.stack.pop()
            self.pstack.append(a["val"]); self.rstack.append(self.ip); self.ip = t["val"]
        # — gọi nhiều tham số theo khung —
        elif name == "GỌI_N":                     # đỉnh = địa chỉ; dưới là 'arg' đối số
            target = self.stack.pop()["val"]
            args = [self.stack.pop()["val"] for _ in range(arg)]; args.reverse()
            base = len(self.pstack); self.pstack.extend(args)
            self.fp_stack.append((base, arg))
            self.rstack.append(self.ip); self.ip = target
        elif name == "GỌI_CLOSURE":               # đỉnh = con trỏ closure; dưới là 'arg' đối
            cp = self.stack.pop()["val"] & 0x3FFFFFFF          # gỡ thẻ nếu có
            code_addr = self.ram[cp]; ncap = self.ram[cp + 1]
            caps = [self.ram[cp + 2 + i] for i in range(ncap)]
            args = [self.stack.pop()["val"] for _ in range(arg)]; args.reverse()
            base = len(self.pstack); self.pstack.extend(caps + args)   # KHUNG = [bắt…, đối…]
            self.fp_stack.append((base, ncap + arg))
            self.rstack.append(self.ip); self.ip = code_addr
        elif name == "THAM_I":                    # đẩy ô THAM_I thứ 'arg' của khung hiện hành
            self.stack.append(KNOWN(self.pstack[self.fp_stack[-1][0] + arg]))
        elif name == "DÀNH_CB":                   # dành 'arg' ô cục bộ ở cuối khung (khởi 0)
            self.pstack.extend([0] * arg)
        elif name == "LƯU_THAM_I":                # ghi vào ô THAM_I thứ 'arg' của khung
            self.pstack[self.fp_stack[-1][0] + arg] = self.stack.pop()["val"]
        elif name == "TRẢ_VỀ_N":                  # trị trả về nằm lại ngăn xếp; bỏ khung
            self.ip = self.rstack.pop()
            base, _ = self.fp_stack.pop(); del self.pstack[base:]
        # — so sánh (pop b, a; đẩy 1/0). Thứ tự dùng CÓ DẤU 16-bit; ==/≠ dùng bit thuần —
        elif name in ("BẰNG","KHÁC","BÉ_HƠN","LỚN_HƠN","BÉ_BẰNG","LỚN_BẰNG"):
            b = self.stack.pop()["val"]; a = self.stack.pop()["val"]
            sa, sb = self.s(a), self.s(b)
            r = ({"BẰNG":a==b,"KHÁC":a!=b,"BÉ_HƠN":sa<sb,"LỚN_HƠN":sa>sb,
                  "BÉ_BẰNG":sa<=sb,"LỚN_BẰNG":sa>=sb}[name])
            self.stack.append(KNOWN(1 if r else 0))
        return True

    def shift(self, f):
        c = self.stack.pop()
        self.stack.append(ANCELL() if c["st"] == ST_AN else KNOWN(f(c["val"]) & self.MASK))

    def branch_state(self, target, st):
        if self.stack.pop()["st"] == st: self.ip = target

    def hoc(self, a):
        "σ ← σ + ((ρ−σ) >> 1) — số học chạy bằng ALU dựng từ NAND (gvm.py)."
        truth = self.vat_cell(a)
        if truth["st"] == ST_AN: self.moved = False; return
        belief = self.tam_cell(a)
        b_val = 0 if belief["st"] == ST_AN else belief["val"]
        d    = sub(int_to_bits(truth["val"]), int_to_bits(b_val))
        step = ashr1(d)
        self.moved = (is_zero(step) == 0)
        new_val = bits_to_int(ripple_add(int_to_bits(b_val), step))
        self.bank()[a] = cell(ST_SANG, new_val, 0.0)

    def giao_chung(self, a):
        "OR TẬP THỂ (tiên đề 11): hợp niềm tin các tác tử về ô a; bảo tồn đa dạng."
        vals = [bk[a]["val"] for bk in self.banks.values()
                if a in bk and bk[a]["st"] != ST_AN]
        if not vals: return ANCELL()
        mean = round(sum(vals) / len(vals))
        c = resonance(cell(ST_SANG, mean, 1.0), self.vat_cell(a))
        c["note"] = f"OR_chung của {len(vals)} tác tử, niềm tin={vals}, đa dạng={max(vals)-min(vals)}"
        return c

    def binop(self, f):
        b = self.stack.pop(); a = self.stack.pop()
        if a["st"] == ST_AN or b["st"] == ST_AN: self.stack.append(ANCELL()); return
        self.stack.append(KNOWN(f(a["val"], b["val"]) & self.MASK))   # GÓI theo độ rộng từ

    def fbin(self, op):
        "Số học ĐIỂM-CỐ-ĐỊNH ×10000 (trung gian 64-bit, cắt-về-0). Trùng khít wasm i64."
        b = self.stack.pop(); a = self.stack.pop()
        if a["st"] == ST_AN or b["st"] == ST_AN: self.stack.append(ANCELL()); return
        av, bv = self.s(a["val"]), self.s(b["val"])
        if op == "*":
            p = av * bv; d = FSCALE
        else:
            if bv == 0: self.stack.append(ANCELL()); return   # chia 0 → ẩn (như thông dịch)
            p = av * FSCALE; d = bv
        q = abs(p) // abs(d)                                  # cắt-về-0 (trunc toward zero)
        if (p < 0) != (d < 0): q = -q
        self.stack.append(KNOWN(q & self.MASK))

    def run(self, trace=False, max_steps=1000000):
        "Chạy từ self.ip. RESUMABLE: hết max_steps → TẠM DỪNG (self.halted=False) để chụp ảnh & chạy tiếp."
        n = 0; self.halted = False
        while 0 <= self.ip < len(self.code):
            if trace:
                w = self.code[self.ip]; nm = OP_NAME[(w >> 8) & 0xFF]
                print(f"      [ip={self.ip:3d} {nm:<12} sp={len(self.stack)}]")
            if not self.step(): self.halted = True; break       # DỪNG / NÉM-chưa-bắt
            n += 1
            if self.trap_pending: break                          # ★ GỌI-HỆ: nhường quyền cho nhân
            if n >= max_steps: break                             # hết ngân sách → TẠM DỪNG (chưa halt)
        else:
            self.halted = True                                   # ip ra ngoài mã → kết thúc
        self.steps_run = n
        return n

    # ============================================================
    # HĐH-GIAO Pha 1: BỘ LẬP LỊCH TIỀN-ĐỊNH (preemptive round-robin)
    # "Lượng tử thời gian" = ngắt timer phần cứng: sau mỗi 'lượng_tử' lệnh, NHÂN
    # CƯỚP CPU, lưu ngữ cảnh tiến trình hiện hành, chuyển sang tiến trình kế.
    # ⇒ một tiến trình CHẠY LOẠN (vòng vô tận, không nhường) KHÔNG treo được hệ.
    # ============================================================
    # ============================================================
    # HĐH-GIAO Pha 2: PERSISTENCE TRỰC GIAO — ảnh GIAO (RAM) bền qua reboot
    # (kiểu Smalltalk/EUMEL: lưu TOÀN BỘ trạng thái, không phải tệp rời)
    # ============================================================
    def lưu_ảnh(self, path):
        "Lưu ảnh RAM (thưa: chỉ ô khác 0) → tệp. Đây là 'đĩa' của HĐH-GIAO."
        import json
        json.dump({"ram": {str(i): int(v) for i, v in enumerate(self.ram) if v}},
                  open(path, "w"), ensure_ascii=False)
    def nạp_ảnh(self, path):
        "Khôi phục ảnh RAM khi 'boot' — trạng thái tiếp tục như chưa hề tắt máy."
        import json, os as _os
        if _os.path.exists(path):
            for k, v in json.load(open(path)).get("ram", {}).items(): self.ram[int(k)] = v
            return True
        return False

    def lưu_máy(self, path):
        "Ảnh MÁY ĐẦY ĐỦ (orthogonal persistence kiểu Smalltalk): RAM + ip + MỌI ngăn xếp + handler +"
        "vật/tâm. Cho phép chụp GIỮA CHỪNG rồi RESUME y nguyên trên một GVM khác (reboot)."
        import json
        json.dump({
            "ram": {str(i): int(v) for i, v in enumerate(self.ram) if v},
            "ip": self.ip, "bit": self.bit, "agent": self.agent, "out_count": self.out_count,
            "stack": self.stack, "pstack": list(self.pstack), "rstack": list(self.rstack),
            "fp": [list(x) for x in self.fp_stack], "handlers": [list(h) for h in self.handlers],
            "vat": {str(a): c for a, c in self.vat.items()},
            "banks": {str(ag): {str(a): c for a, c in bk.items()} for ag, bk in self.banks.items()},
        }, open(path, "w", encoding="utf-8"), ensure_ascii=False)

    def nạp_máy(self, path):
        "Khôi phục ảnh MÁY đầy đủ → RESUME từ đúng ip + ngăn xếp đã lưu (như chưa hề tắt)."
        import json, os as _os
        if not _os.path.exists(path): return False
        d = json.load(open(path, encoding="utf-8"))
        self.ram = [0] * 65536
        for k, v in d["ram"].items(): self.ram[int(k)] = v
        self.ip = d["ip"]; self.bit = d["bit"]; self.agent = d["agent"]; self.out_count = d.get("out_count", 0)
        self.MASK = (1 << self.bit) - 1; self.HALF = 1 << (self.bit - 1); self.MOD = 1 << self.bit
        self.stack = d["stack"]; self.pstack = d["pstack"]; self.rstack = d["rstack"]
        self.fp_stack = [tuple(x) for x in d["fp"]]; self.handlers = [tuple(h) for h in d["handlers"]]
        self.vat = {int(a): c for a, c in d.get("vat", {}).items()}
        self.banks = {int(ag): {int(a): c for a, c in bk.items()} for ag, bk in d.get("banks", {}).items()}
        return True

    def tiến_trình(self, nhiệm_vụ):
        "Tạo bảng ngữ cảnh tiến trình (mỗi cái có NGĂN XẾP riêng)."
        return [{"tên": nv[0], "ip": nv[1], "stack": [], "pstack": [], "rstack": [],
                 "fp": [], "sống": True, "lệnh": 0, "preempt": 0} for nv in nhiệm_vụ]

    def chạy_lát(self, c, lượng_tử):
        "CƠ CHẾ: nạp ngữ cảnh c, chạy ≤ lượng_tử lệnh rồi BỊ CƯỚP CPU, lưu ngữ cảnh. Trả số lệnh đã chạy."
        self.ip = c["ip"]; self.stack = c["stack"]; self.pstack = c["pstack"]
        self.rstack = c["rstack"]; self.fp_stack = c["fp"]; self.cur_task = c["tên"]
        k = 0; thăm = set()                                           # IP phân biệt = đo TIẾN TRIỂN (spinner=1)
        while k < lượng_tử:
            if not (0 <= self.ip < len(self.code)): c["sống"] = False; break
            thăm.add(self.ip)
            if self.step() is False: c["sống"] = False; break          # DỪNG
            k += 1
        if c["sống"] and k == lượng_tử: c["preempt"] += 1              # hết lượng tử → bị cướp
        c["ip"] = self.ip; c["lệnh"] += k; c["thăm"] = len(thăm)       # LƯU NGỮ CẢNH + tiến triển
        return k

    def chạy_đa_nhiệm(self, nhiệm_vụ, lượng_tử=4, tối_đa_lượt=64):
        "CHÍNH SÁCH: round-robin tiền-định (cơ chế = chạy_lát)."
        ctx = self.tiến_trình(nhiệm_vụ); lượt = 0
        while any(c["sống"] for c in ctx) and lượt < tối_đa_lượt:
            for c in ctx:
                if c["sống"]: self.chạy_lát(c, lượng_tử)
            lượt += 1
        return {"lượt": lượt, "ctx": ctx}

    # ── chính sách γ-scheduler DÙNG CHUNG với silicon (để phần mềm KHỚP hw/gvm.v) ──
    @staticmethod
    def γ_cập_nhật(σ, cred, cur, did_out, n, COST=128):
        """MỘT bước học+chọn của γ-scheduler — TRÙNG TỪNG WIRE với hw/gvm.v:
           σ←σ+((ρ−σ)>>2) clamp[0,255] · cred←max(0, cred+σ>>2 − (cur trả COST)) · gsel=argmax.
           Trả (σ_mới, cred_mới, gsel). Số học SỐ NGUYÊN thuần ⇒ phần mềm = phần cứng."""
        ρ = 255 if did_out else 0
        sn = σ[cur] + ((ρ - σ[cur]) >> 2)                 # >> CÓ DẤU (Verilog >>>): khớp với 2's-comp
        σ = list(σ); σ[cur] = 0 if sn < 0 else (255 if sn > 255 else sn)
        a = [cred[i] + (σ[i] >> 2) for i in range(n)]     # tích luỹ credit ∝ σ
        a[cur] = max(0, a[cur] - COST)                    # OUTGOING trả COST (bão hoà 0)
        cred = [max(0, a[i]) for i in range(n)]
        gsel = max(range(n), key=lambda i: a[i])          # argmax (ties → chỉ số NHỎ, như silicon)
        return σ, cred, gsel

    def lập_lịch_học(self, vòng_tối_đa=24, COST=128, in_trace=True):
        "γ-SCHEDULER CDFL PREEMPTIVE — chính sách TRÙNG silicon hw/gvm.v (σ-EMA >>2, argmax credit)."
        entries = self.tasks; n = len(entries)
        if n == 0: return None
        ctx = [{"ip": e, "stack": [], "pstack": [], "rstack": [len(self.code)], "fp": [(0, 0)],
                "handlers": [], "sống": True, "lỗi": None, "lệnh": 0} for e in entries]
        σ = [128] * n; cred = [0] * n; cur = 0
        if in_trace:
            print("=" * 72)
            print("γ-SCHEDULER CDFL (preemptive, BIẾT-HỌC) — chính sách TRÙNG silicon hw/gvm.v")
            print(f"  σ₀=128/255 · σ←σ+((ρ−σ)>>2) · credit←σ>>2 · COST={COST} · chọn argmax(credit)")
            print(f"  ρ=255 nếu tiến trình XUẤT trong lượng tử ({self.timer_period} lệnh), ngược lại 0")
            print("=" * 72)
        for vòng in range(vòng_tối_đa):
            if not any(c["sống"] for c in ctx): break
            if not ctx[cur]["sống"]:                       # task chết → chọn task sống credit cao nhất
                sống = [i for i in range(n) if ctx[i]["sống"]]
                cur = max(sống, key=lambda i: cred[i])
            c = ctx[cur]
            self.cur_task = f"tt#{cur}"; self.did_out = False; self.fault_code = None
            self.ip = c["ip"]; self.stack = c["stack"]; self.pstack = c["pstack"]
            self.rstack = c["rstack"]; self.fp_stack = c["fp"]; self.handlers = c["handlers"]  # NGĂN XẾP HANDLER RIÊNG
            k = 0
            while k < self.timer_period:                   # CHẠY ≤ lượng tử lệnh rồi BỊ CƯỚP CPU
                if not (0 <= self.ip < len(self.code)): c["sống"] = False; break
                if self.step() is False:                   # DỪNG êm HOẶC NÉM-chưa-bắt (lỗi)
                    c["sống"] = False
                    if self.fault_code is not None: c["lỗi"] = self.fault_code   # ★ FAULT → CÔ LẬP
                    break
                k += 1
            c["ip"] = self.ip; c["lệnh"] += k; c["handlers"] = self.handlers
            if c["lỗi"] is not None and in_trace:          # SUPERVISOR: cô lập tiến trình lỗi, hệ chạy tiếp
                print(f"   [nhân] ⚠ tt#{cur} NÉM lỗi={c['lỗi']} CHƯA BẮT → CÔ LẬP (cách ly, hệ vẫn chạy)")
            σ, cred, gsel = self.γ_cập_nhật(σ, cred, cur, self.did_out, n, COST)  # ★ chung với silicon
            if in_trace:
                γ = (2 * σ[cur] - 255) / 255.0
                print(f"  [lượt {vòng+1:2}] chạy tt#{cur}  ρ={255 if self.did_out else 0:3} "
                      f"σ={σ[cur]:3} γ={γ:+.2f}  credit={cred}  →kế: tt#{gsel}")
            cur = gsel
        if in_trace:
            print("-" * 72)
            for i in range(n):
                γ = (2 * σ[i] - 255) / 255.0
                if ctx[i]["lỗi"] is not None:
                    tt = f"CÔ LẬP (lỗi={ctx[i]['lỗi']})"
                elif not ctx[i]["sống"]:
                    tt = "kết thúc êm"
                else:
                    tt = "đốm tối → đói CPU" if γ < 0 else "hữu ích → ưu tiên"
                print(f"  · tt#{i}  σ={σ[i]:3}  γ={γ:+.2f}  ·  {ctx[i]['lệnh']:3} lệnh CPU   [{tt}]")
            cô_lập = [i for i in range(n) if ctx[i]["lỗi"] is not None]
            if cô_lập:
                print(f"  ⇒ CÔ LẬP FAULT: tt#{cô_lập} lỗi-chưa-bắt → bị cách ly; các tiến trình KHÁC chạy tiếp.")
            else:
                print("  ⇒ Nhân HỌC ra tiến trình spin (γ<0=đốm tối) → đói CPU; hữu ích được ưu tiên.")
        self.sched_σ = σ; self.sched_cred = cred; self.sched_lệnh = [c["lệnh"] for c in ctx]
        self.sched_lỗi = [c["lỗi"] for c in ctx]
        return {"σ": σ, "cred": cred, "lệnh": self.sched_lệnh, "lỗi": self.sched_lỗi}

# ============================================================
# DRIVER
# ============================================================
DEMO = """
; demo nhúng — hội tụ một tác tử bằng nhãn/nhảy tổng quát
.VẬT 0 = 37
        TÁC_TỬ 0
LẶP:    HỌC 0
        GIAO 0
        RỌI
        NHẢY_ĐỘNG LẶP      ; còn dịch → lặp; chạm sàn tối → rơi xuống DỪNG
        DỪNG
"""

def run_source(src, title):
    code, world = assemble_text(src)
    print("="*64)
    print(f"MÃ MÁY GVM (16-bit/lệnh = [opcode:8][operand:8]) — {title}")
    print("="*64)
    for i, w in enumerate(code): print(f"  {i:02d}:  {disasm_word(w)}")
    print("\n" + "="*64); print("THỰC THI"); print("="*64)
    GVM(code, world).run()

def main():
    if len(sys.argv) >= 2:
        with open(sys.argv[1], encoding="utf-8") as f: src = f.read()
        run_source(src, sys.argv[1])
    else:
        run_source(DEMO, "demo nhúng")
        print("\n   → DỪNG: chạm sàn tối (Δ=0) = viên mãn cục bộ (tiên đề 12).")

if __name__ == "__main__":
    main()

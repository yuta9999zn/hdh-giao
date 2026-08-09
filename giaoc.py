# -*- coding: utf-8 -*-
"""
GIAOC — TRÌNH BIÊN DỊCH GIAO → BYTECODE GVM   (hợp lưu mạch A + mạch B)
======================================================================
Điểm hội tụ cuối của dự án: ngôn ngữ GIAO (mạch A) được HẠ XUỐNG mã máy GVM (mạch B),
rồi chạy trên máy trit/γ dựng từ cổng NAND. Sau biên dịch, Python KHÔNG diễn giải ngữ
nghĩa GIAO nữa — nó chỉ còn mô phỏng transistor (chạy bit). Ngữ nghĩa GIAO giờ NẰM TRONG
bytecode, do CPU GVM thực thi.

Cái đẹp: các lệnh CDFL của GIAO ánh xạ THẲNG sang opcode máy —
    vật <ô> = v   →  NẠP v ; LƯU_VẬT a
    tâm <ô> = ẩn  →  ẨN ; LƯU_TÂM a
    học <ô>       →  HỌC a
    giao k = <ô>  →  GIAO a        (đẩy tri/γ lên ngăn xếp)
    rọi k         →  RỌI
    lặp N { }     →  vòng đếm bằng TẢI_Ô/TRỪ/NHẢY_NẾU_0
    +  -  *       →  CỘNG TRỪ NHÂN

Trình biên dịch viết bằng Python là 'mồi' (như trình biên dịch C đầu tiên viết bằng asm);
RUNTIME thì thuần GVM. Bước sau có thể tự thân hoá chính trình biên dịch này bằng GIAO.
"""
import sys, copy
from giao import (tokenize, Parser, Node, Num, Str, AnLit, VarRef, Bin, Decl, Dat, Hoc, Giao, Roi,
                  Lap, ExprStmt, HamDef, Tra, Goi, Neu, ListLit, Index, Lam, LapTrong, Dung,
                  Mai, ThuBat, TruthLit, SANG)
from gvm_may import GVM, OPS, disasm_word

# Bố cục bộ nhớ cho HEAP (danh sách cons-cell):
HEAP_PTR_CELL = 250   # ram[250] = đỉnh heap hiện hành
SCRATCH_H     = 251   # ô tạm cho 'đầu' khi tạo cons
SCRATCH_T     = 252   # ô tạm cho 'đuôi' khi tạo cons
HEAP_BASE     = 300   # heap bắt đầu từ ram[300]
# Ô tạm cho hàm trợ giúp BẢN (map) — không trùng cons(251/252)/helpers(253-255)/closure(230-246):
MAP_CUR  = 210        # con trỏ duyệt alist
MAP_NODE = 211        # địa chỉ node mới cấp phát
MAP_HDR  = 212        # địa chỉ ô đầu (header) của bản
MAP_T    = 213        # tạm (next / acc / count)
MAP_PREV = 214        # node trước (cho xoá_khoá unlink)

# ── THẺ KIỂU trên máy (ABI 32-bit) ─────────────────────────────────────────
# Mọi giá trị GIAO ở tầng máy là một từ 32-bit. Để `là_số`/`là_ds` phân biệt
# được SỐ với CON-TRỎ-DANH-SÁCH (cả hai đều là số nguyên thuần), ta GẮN THẺ:
#   • con trỏ danh sách (kể cả rỗng) mang bit 30:  ptr = TAG | địa_chỉ_heap
#   • NIL (danh sách rỗng) = TAG  (địa chỉ 0)
#   • số thường < 2^30 (hoặc âm) → KHÔNG mang thẻ
# Nhờ bit 30 < bit dấu (31), so sánh CÓ DẤU vẫn đúng: list ∈ [2^30, 2^31).
#   là_ds(v)  ⟺  signed(v) ≥ 2^30      (LỚN_BẰNG TAG)
#   là_số(v)  ⟺  signed(v) <  2^30      (BÉ_HƠN  TAG)
# Chạy trên GVM 32-bit (giaoc neo ABI này; chuỗi mồi assembler vẫn 16-bit, không đụng).
WORD_BIT = 32
TAG      = 1 << 30
NIL      = 0            # danh sách rỗng = 0 (KHÔNG thẻ): giữ idiom `l == 0`, `dài==0`.
FSCALE   = 10000       # SỐ THỰC = điểm-cố-định thập phân: x_thực ≈ round(x*FSCALE) (số nguyên DSP)
ERR_OOB  = 1           # mã NGOẠI LỆ: chỉ mục danh sách ngoài phạm vi (NÉM cho thử/bắt)
#  ⇒ chỉ cons-cell KHÔNG rỗng mới mang thẻ. là_ds([]) báo 'số' (giaoc.giao không hề
#    kiểm kiểu trên danh sách rỗng), nhưng so cấu trúc/độ dài vẫn đúng vì đáy đệ quy
#    (NIL=0) được so như số 0==0.

class GiaoC:
    def __init__(self, tagged=False):
        # tagged=True: bật ABI THẺ 32-bit (cho `là_số`/`là_ds` + ==/+ đa hình).
        # tagged=False (mặc định): hành vi CŨ y hệt — NIL=0, con trỏ KHÔNG thẻ,
        #   CỘNG/BẰNG/KHÁC trực tiếp, vừa 16-bit (Verilog/FPGA & mọi ví dụ cũ không đổi).
        self.tagged = tagged
        self.code = []          # [(tên_lệnh, toán_hạng|nhãn) | ("NHÃN", tên)]
        self.field_addr = {}    # ô CDFL (vật/tâm chung địa chỉ) → addr trong vat[]/bank[]
        self.var_addr = {}      # biến đặt + biến đếm → addr trong ram[]
        self.lc = 0
        self.fn_labels = {}     # tên hàm → nhãn mã
        self.frame_names = []   # tên các ô THAM_I của KHUNG đang biên dịch = [bắt…, tham số…]
        self.lam_seq = 0        # đếm closure vô danh (sinh nhãn @lam_N)
        self.loop_end = []      # ngăn xếp nhãn-kết-thúc vòng lặp (cho 'dừng')
        self.str_cell = {}      # chuỗi-hằng dùng ≥2 lần → ô NHỚ con trỏ (INTERN: dựng 1 lần)
        self.var_type = {}      # tên biến → 'str'|'num'|'list'|'?'  (để chọn RỌI vs RỌI_CHUỖI)

    # --- tiện ích phát mã ---
    def emit(self, name, operand=0): self.code.append((name, operand))
    def mark(self, label): self.code.append(("NHÃN", label))
    def new_label(self): self.lc += 1; return f"@{self.lc}"
    def emit_const(self, n):                         # nạp hằng tới 32-bit (toán hạng NẠP chỉ 8-bit)
        n = int(n) & 0xFFFFFFFF
        if 0 <= n <= 255: self.emit("NẠP", n); return
        by = [(n >> 24) & 0xFF, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF]
        k = 0
        while k < 3 and by[k] == 0: k += 1            # bỏ byte 0 dẫn đầu
        self.emit("NẠP", by[k])
        for b in by[k+1:]:                            # val = (val<<8) + b
            self.emit("DỊCH_TRÁI", 8)
            if b != 0: self.emit("NẠP", b); self.emit("CỘNG")   # byte 0 → BỎ `NẠP 0;CỘNG` (sau dịch byte-thấp đã 0; acc là hằng SÁNG ⇒ +0 ≡ identity, provably-safe)
    def emit_untag(self):                            # [ptr] → [địa_chỉ_heap]  (ptr - TAG)
        if self.tagged: self.emit_const(TAG); self.emit("TRỪ")    # chế độ cũ: con trỏ = địa chỉ, không cần gỡ
    def emit_cons(self):                             # ngăn xếp [h, t] → [con_trỏ]; cấp 2 ô heap
        self.emit("LƯU_Ô", SCRATCH_T); self.emit("LƯU_Ô", SCRATCH_H)
        self.emit("TẢI_Ô", HEAP_PTR_CELL)           # [hp]
        self.emit("NHÂN_BẢN"); self.emit("TẢI_Ô", SCRATCH_H); self.emit("LƯU_GIÁN")   # ram[hp]=h
        self.emit("NHÂN_BẢN"); self.emit("NẠP", 1); self.emit("CỘNG")
        self.emit("TẢI_Ô", SCRATCH_T); self.emit("LƯU_GIÁN")                          # ram[hp+1]=t
        self.emit("NHÂN_BẢN"); self.emit("NẠP", 2); self.emit("CỘNG")
        self.emit("LƯU_Ô", HEAP_PTR_CELL)           # hp += 2 ; [hp] = địa chỉ cons
        if self.tagged: self.emit_const(TAG); self.emit("CỘNG")   # GẮN THẺ: con trỏ = TAG | địa_chỉ
    def emit_list(self, elems):                      # [e0,..,en] → cons(e0, cons(.., NIL))
        def build(i):
            if i >= len(elems): self.emit_const(NIL); return   # NIL (có thẻ)
            self.expr(elems[i]); build(i + 1); self.emit_cons()
        build(0)

    # === CLOSURE (hàm hạng nhất) → khối heap [code_addr, ncap, cap0..] ===
    CAP_BASE = 230                                   # ô tạm 230..245 (≤16 biến bắt) + 246 = code_addr
    CODE_TMP = 246
    def free_names(self, node, acc):                 # gom MỌI tên VarRef trong cây (kể cả lam lồng)
        if node is None: return
        if type(node) is VarRef: acc.add(node.name); return
        for v in getattr(node, "__dict__", {}).values():
            if isinstance(v, list):
                for x in v:
                    if hasattr(x, "__dict__"): self.free_names(x, acc)
            elif hasattr(v, "__dict__"): self.free_names(v, acc)
    def compile_lam(self, lam):                      # đẩy 1 con trỏ closure lên ngăn xếp
        outer = self.frame_names
        free = set()
        for s in lam.body: self.free_names(s, free)
        lam_locs = [n for n in self.collect_locals(lam.body) if n not in lam.params]
        # BẮT: tên ô-khung NGOÀI mà thân dùng, KHÔNG phải tham số/biến-cục-bộ của chính lam
        caps = [n for n in outer if n in free and n not in lam.params and n not in lam_locs]
        if len(caps) > 16: raise ValueError("closure bắt quá 16 biến (giới hạn ô tạm máy)")
        self.lam_seq += 1
        code_label = f"@lam_{self.lam_seq}"; skip = self.new_label()
        # 1) phát THÂN lam (nhảy vượt qua khi chạy thẳng)
        self.emit_jump(skip)
        self.mark(code_label)
        self.frame_names = caps + list(lam.params) + lam_locs   # KHUNG = [bắt…, tham số…, cục bộ…]
        if lam_locs: self.emit("DÀNH_CB", len(lam_locs))         # prologue: dành ô cục bộ per-call
        self.block(lam.body)
        self.emit("ẨN"); self.emit("TRẢ_VỀ_N")        # chốt cuối thân: rơi khỏi thân → trả ẩn
        self.frame_names = outer                      # khôi phục khung ngoài
        self.mark(skip)
        # 2) DỰNG giá trị closure: [code_addr, cap0..] → con trỏ
        self.emit_addr(code_label)                    # đẩy ĐỊA CHỈ mã lam
        for c in caps: self.expr(VarRef(c))           # đọc biến bắt TỪ KHUNG NGOÀI (THAM_I/TẢI_Ô)
        self.emit_closure(len(caps))
    def emit_closure(self, ncap):                    # [code_addr, cap0..cap_{n-1}] → [con_trỏ closure]
        for i in range(ncap - 1, -1, -1):
            self.emit("LƯU_Ô", self.CAP_BASE + i)     # nhặt cap_i vào ô tạm
        self.emit("LƯU_Ô", self.CODE_TMP)             # nhặt code_addr
        self.emit("TẢI_Ô", HEAP_PTR_CELL)             # [hp]
        self.emit("NHÂN_BẢN"); self.emit("TẢI_Ô", self.CODE_TMP); self.emit("LƯU_GIÁN")   # ram[hp]=code
        self.emit("NHÂN_BẢN"); self.emit("NẠP", 1); self.emit("CỘNG")
        self.emit_const(ncap); self.emit("LƯU_GIÁN")                                        # ram[hp+1]=ncap
        for i in range(ncap):
            self.emit("NHÂN_BẢN"); self.emit_const(2 + i); self.emit("CỘNG")
            self.emit("TẢI_Ô", self.CAP_BASE + i); self.emit("LƯU_GIÁN")                    # ram[hp+2+i]=cap_i
        self.emit("NHÂN_BẢN"); self.emit_const(2 + ncap); self.emit("CỘNG")
        self.emit("LƯU_Ô", HEAP_PTR_CELL)             # hp += 2+ncap ; [hp]
        if self.tagged: self.emit_const(TAG); self.emit("CỘNG")   # GẮN THẺ con trỏ closure
    # --- tiện ích THẺ-AWARE cho hàm trợ giúp duyệt heap ---
    def _empty_to(self, reg, label):                 # nhảy tới label nếu ô reg là NIL (==0)
        self.emit_addr(label); self.emit("TẢI_Ô", reg); self.emit("NHẢY_NẾU_0_X")
    def _car(self, reg):                             # đẩy car(reg) = ram[addr(reg)]
        self.emit("TẢI_Ô", reg); self.emit_untag(); self.emit("TẢI_GIÁN")
    def _cdr_into(self, reg):                        # reg ← cdr(reg) = ram[addr(reg)+1] (đã có thẻ)
        self.emit("TẢI_Ô", reg); self.emit_untag(); self.emit("NẠP", 1); self.emit("CỘNG")
        self.emit("TẢI_GIÁN"); self.emit("LƯU_Ô", reg)
    # === HÀM TRỢ GIÚP phát MỘT LẦN (gọi qua GỌI_N) → mã gọn, biên dịch nhanh ===
    def emit_helpers(self):
        SA, SB, SC = 253, 254, 255                   # ô tạm vòng lặp (cons dùng 251/252)
        # --- __dài(l) → độ dài ---
        L, E = self.new_label(), self.new_label()
        self.mark("@__dài")
        self.emit("THAM_I", 0); self.emit("LƯU_Ô", SA); self.emit("NẠP", 0); self.emit("LƯU_Ô", SB)
        self.mark(L); self._empty_to(SA, E)
        self.emit("TẢI_Ô", SB); self.emit("NẠP", 1); self.emit("CỘNG"); self.emit("LƯU_Ô", SB)
        self._cdr_into(SA)
        self.emit_jump(L); self.mark(E); self.emit("TẢI_Ô", SB); self.emit("TRẢ_VỀ_N")
        # --- __lấy(l, i) → l[i]  (NÉM mã lỗi ERR_OOB nếu chỉ mục NGOÀI PHẠM VI) ---
        L2, E2 = self.new_label(), self.new_label()
        self.mark("@__lấy")
        self.emit("THAM_I", 0); self.emit("LƯU_Ô", SA); self.emit("THAM_I", 1); self.emit("LƯU_Ô", SB)
        self.mark(L2)
        self.emit_addr("@__oob"); self.emit("TẢI_Ô", SA); self.emit("NHẢY_NẾU_0_X")   # SA==NIL → ngoài phạm vi
        self.emit_addr(E2); self.emit("TẢI_Ô", SB); self.emit("NHẢY_NẾU_0_X")          # i==0 → lấy car
        self._cdr_into(SA)
        self.emit("TẢI_Ô", SB); self.emit("NẠP", 1); self.emit("TRỪ"); self.emit("LƯU_Ô", SB)
        self.emit_jump(L2); self.mark(E2); self._car(SA); self.emit("TRẢ_VỀ_N")
        # điểm NÉM dùng chung: chỉ mục ngoài phạm vi (thử/bắt sẽ gỡ-cuộn về handler)
        self.mark("@__oob"); self.emit_const(ERR_OOB); self.emit("NÉM")
        # --- __ghép(a, b) → a ++ b  (đảo a rồi chèn lên b) ---
        RL, RE, PL, PE = (self.new_label(), self.new_label(), self.new_label(), self.new_label())
        self.mark("@__ghép")
        self.emit("THAM_I", 0); self.emit("LƯU_Ô", SA); self.emit_const(NIL); self.emit("LƯU_Ô", SC)
        self.mark(RL); self._empty_to(SA, RE)
        self._car(SA); self.emit("TẢI_Ô", SC); self.emit_cons(); self.emit("LƯU_Ô", SC)
        self._cdr_into(SA)
        self.emit_jump(RL); self.mark(RE)
        self.emit("THAM_I", 1); self.emit("LƯU_Ô", SB); self.emit("TẢI_Ô", SC); self.emit("LƯU_Ô", SA)
        self.mark(PL); self._empty_to(SA, PE)
        self._car(SA); self.emit("TẢI_Ô", SB); self.emit_cons(); self.emit("LƯU_Ô", SB)
        self._cdr_into(SA)
        self.emit_jump(PL); self.mark(PE); self.emit("TẢI_Ô", SB); self.emit("TRẢ_VỀ_N")

    # === HÀM TRỢ GIÚP TẦNG-THẺ: ==/!= cấu trúc, + đa hình, số→chuỗi ===
    def emit_helpers2(self):
        # ---- __num2str(n) → danh-sách mã-ký-tự thập phân ----
        Z, LOOP, DONE = self.new_label(), self.new_label(), self.new_label()
        SA, SC = 253, 255
        self.mark("@__num2str")
        self.emit("THAM_I", 0); self.emit("LƯU_Ô", SA)
        self.emit_const(NIL); self.emit("LƯU_Ô", SC)
        self.emit_addr(Z); self.emit("TẢI_Ô", SA); self.emit("NHẢY_NẾU_0_X")      # n==0 → "0"
        self.mark(LOOP)
        self.emit_addr(DONE); self.emit("TẢI_Ô", SA); self.emit("NHẢY_NẾU_0_X")   # n==0 → xong
        # d = n - (n/10)*10 ; ch = d + 48
        self.emit("TẢI_Ô", SA)
        self.emit("TẢI_Ô", SA); self.emit("NẠP", 10); self.emit("CHIA"); self.emit("NẠP", 10); self.emit("NHÂN")
        self.emit("TRỪ"); self.emit("NẠP", 48); self.emit("CỘNG")
        self.emit("TẢI_Ô", SC); self.emit_cons(); self.emit("LƯU_Ô", SC)          # acc = cons(ch, acc)
        self.emit("TẢI_Ô", SA); self.emit("NẠP", 10); self.emit("CHIA"); self.emit("LƯU_Ô", SA)  # n /= 10
        self.emit_jump(LOOP)
        self.mark(Z)
        self.emit("NẠP", 48); self.emit_const(NIL); self.emit_cons(); self.emit("LƯU_Ô", SC)      # "0"
        self.mark(DONE)
        self.emit("TẢI_Ô", SC); self.emit("TRẢ_VỀ_N")
        # ---- __chuỗi_hoá(x): list→chính nó, số→num2str ----
        NUMP = self.new_label()
        self.mark("@__chuỗi_hoá")
        self.emit_addr(NUMP); self.emit("THAM_I", 0); self.emit_const(TAG); self.emit("LỚN_BẰNG"); self.emit("NHẢY_NẾU_0_X")
        self.emit("THAM_I", 0); self.emit("TRẢ_VỀ_N")           # đã là danh sách/chuỗi
        self.mark(NUMP)
        self.emit("THAM_I", 0); self.emit_addr("@__num2str"); self.emit("GỌI_N", 1); self.emit("TRẢ_VỀ_N")
        # ---- __cộng(a,b): số+số → cộng; ngược lại → ghép(chuỗi_hoá a, chuỗi_hoá b) ----
        CC = self.new_label()
        self.mark("@__cộng")
        self.emit("THAM_I", 0); self.emit_const(TAG); self.emit("BÉ_HƠN")        # a là số?
        self.emit("THAM_I", 1); self.emit_const(TAG); self.emit("BÉ_HƠN")        # b là số?
        self.emit("NHÂN")                                                         # cả hai là số?
        self.emit_addr(CC); self.emit("ĐỔI"); self.emit("NHẢY_NẾU_0_X")           # !=1 → nối chuỗi
        # (ĐỔI để đưa cond lên dưới target cho NHẢY_NẾU_0_X: stack [target, cond])
        self.emit("THAM_I", 0); self.emit("THAM_I", 1); self.emit("CỘNG"); self.emit("TRẢ_VỀ_N")
        self.mark(CC)
        self.emit("THAM_I", 0); self.emit_addr("@__chuỗi_hoá"); self.emit("GỌI_N", 1)
        self.emit("THAM_I", 1); self.emit_addr("@__chuỗi_hoá"); self.emit("GỌI_N", 1)
        self.emit_addr("@__ghép"); self.emit("GỌI_N", 2); self.emit("TRẢ_VỀ_N")
        # ---- __bằng(a,b) → 1/0 (đệ quy cấu trúc; số so trực tiếp, danh sách so từng phần) ----
        AL, ANBL, BOTH, AE, BEAN = (self.new_label(), self.new_label(), self.new_label(),
                                    self.new_label(), self.new_label())
        self.mark("@__bằng")
        # a là số? (a < TAG) → nếu không, a là danh sách → AL
        self.emit_addr(AL); self.emit("THAM_I", 0); self.emit_const(TAG); self.emit("BÉ_HƠN"); self.emit("NHẢY_NẾU_0_X")
        # a là số: b là số? nếu không → 0
        self.emit_addr(ANBL); self.emit("THAM_I", 1); self.emit_const(TAG); self.emit("BÉ_HƠN"); self.emit("NHẢY_NẾU_0_X")
        self.emit("THAM_I", 0); self.emit("THAM_I", 1); self.emit("BẰNG"); self.emit("TRẢ_VỀ_N")   # số==số
        self.mark(ANBL); self.emit("NẠP", 0); self.emit("TRẢ_VỀ_N")
        self.mark(AL)   # a là danh sách: b là số? → 0; ngược lại cả hai danh sách
        self.emit_addr(BOTH); self.emit("THAM_I", 1); self.emit_const(TAG); self.emit("BÉ_HƠN"); self.emit("NHẢY_NẾU_0_X")
        self.emit("NẠP", 0); self.emit("TRẢ_VỀ_N")
        self.mark(BOTH)
        self.emit_addr(AE); self.emit("THAM_I", 0); self.emit_untag(); self.emit("NHẢY_NẾU_0_X")    # a rỗng → AE
        self.emit_addr(BEAN); self.emit("THAM_I", 1); self.emit_untag(); self.emit("NHẢY_NẾU_0_X")  # b rỗng, a không → 0
        # cả hai không rỗng: __bằng(car a, car b) * __bằng(cdr a, cdr b)
        self.emit("THAM_I", 0); self.emit_untag(); self.emit("TẢI_GIÁN")
        self.emit("THAM_I", 1); self.emit_untag(); self.emit("TẢI_GIÁN")
        self.emit_addr("@__bằng"); self.emit("GỌI_N", 2)
        self.emit("THAM_I", 0); self.emit_untag(); self.emit("NẠP", 1); self.emit("CỘNG"); self.emit("TẢI_GIÁN")
        self.emit("THAM_I", 1); self.emit_untag(); self.emit("NẠP", 1); self.emit("CỘNG"); self.emit("TẢI_GIÁN")
        self.emit_addr("@__bằng"); self.emit("GỌI_N", 2)
        self.emit("NHÂN"); self.emit("TRẢ_VỀ_N")
        self.mark(AE)   # a rỗng: bằng ⟺ b cũng rỗng (addr(b)==0)
        self.emit("THAM_I", 1); self.emit_untag(); self.emit("NẠP", 0); self.emit("BẰNG"); self.emit("TRẢ_VỀ_N")
        self.mark(BEAN); self.emit("NẠP", 0); self.emit("TRẢ_VỀ_N")

    # === BẢN (map/record) — kiểu THAM CHIẾU mutable trên heap ===
    #   giá trị bản = con trỏ (có thẻ) tới Ô ĐẦU: ram[base] = head (đầu alist; 0 = rỗng).
    #   node = khối 3 ô [key, val, next]; đặt_khoá CHÈN ĐẦU (O(1)); sửa khoá cũ ⇒ vá tại chỗ.
    #   Tham chiếu: mọi nơi giữ con trỏ thấy cùng cập nhật (vì ô đầu/node bị MUTATE qua LƯU_GIÁN).
    def emit_map_new(self):                          # bản() → con trỏ bản rỗng
        self.emit("TẢI_Ô", HEAP_PTR_CELL)                                        # [hp]
        self.emit("NHÂN_BẢN"); self.emit("NẠP", 0); self.emit("LƯU_GIÁN")        # ram[hp]=0 (rỗng) → [hp]
        self.emit("NHÂN_BẢN"); self.emit("NẠP", 1); self.emit("CỘNG")
        self.emit("LƯU_Ô", HEAP_PTR_CELL)                                        # hp += 1 → [hp]
        if self.tagged: self.emit_const(TAG); self.emit("CỘNG")                  # GẮN THẺ con trỏ bản
    def emit_helpers3(self):
        # --- @__map_tìm(m, k) → địa chỉ node có khoá==k, hoặc 0 (khoá so CẤU TRÚC qua __bằng) ---
        L, ADV, E, SLOW, FOUND = (self.new_label(), self.new_label(), self.new_label(),
                                  self.new_label(), self.new_label())
        self.mark("@__map_tìm")
        self.emit("THAM_I", 0); self.emit_untag(); self.emit("TẢI_GIÁN"); self.emit("LƯU_Ô", MAP_CUR)  # cur=head
        self.mark(L)
        self.emit_addr(E); self.emit("TẢI_Ô", MAP_CUR); self.emit("NHẢY_NẾU_0_X")    # cur==0 → không thấy
        # ── NHANH: so BẰNG thô (số ↔ số, hoặc CHUỖI-INTERN cùng con trỏ) — 1 lệnh thay vì __bằng đệ quy ──
        self.emit("TẢI_Ô", MAP_CUR); self.emit("TẢI_GIÁN"); self.emit("THAM_I", 1); self.emit("BẰNG")
        self.emit_addr(SLOW); self.emit("ĐỔI"); self.emit("NHẢY_NẾU_0_X")             # !=  → thử cấu trúc
        self.emit_jump(FOUND)                                                          # == thô → TRÙNG ngay
        self.mark(SLOW)                                                                # ── CHẬM: __bằng CẤU TRÚC (chuỗi tính-toán) ──
        self.emit("TẢI_Ô", MAP_CUR); self.emit("TẢI_GIÁN")
        self.emit("THAM_I", 1); self.emit_addr("@__bằng"); self.emit("GỌI_N", 2)      # __bằng(khoá_node, k) → 1/0
        self.emit_addr(ADV); self.emit("ĐỔI"); self.emit("NHẢY_NẾU_0_X")              # bằng==0 (KHÁC) → đi tiếp
        self.mark(FOUND); self.emit("TẢI_Ô", MAP_CUR); self.emit("TRẢ_VỀ_N")          # TRÙNG → trả cur
        self.mark(ADV)                                                                # cur = ram[cur+2]
        self.emit("TẢI_Ô", MAP_CUR); self.emit("NẠP", 2); self.emit("CỘNG")
        self.emit("TẢI_GIÁN"); self.emit("LƯU_Ô", MAP_CUR)
        self.emit_jump(L)
        self.mark(E); self.emit("NẠP", 0); self.emit("TRẢ_VỀ_N")
        # --- @__map_lấy(m, k) → val hoặc ẨN (thiếu khoá) ---
        AN_L = self.new_label()
        self.mark("@__map_lấy")
        self.emit("THAM_I", 0); self.emit("THAM_I", 1); self.emit_addr("@__map_tìm"); self.emit("GỌI_N", 2)
        self.emit("NHÂN_BẢN"); self.emit_addr(AN_L); self.emit("ĐỔI"); self.emit("NHẢY_NẾU_0_X")   # nd==0 → ẩn
        self.emit("NẠP", 1); self.emit("CỘNG"); self.emit("TẢI_GIÁN"); self.emit("TRẢ_VỀ_N")        # ram[nd+1]
        self.mark(AN_L); self.emit("BỎ"); self.emit("ẨN"); self.emit("TRẢ_VỀ_N")
        # --- @__map_có(m, k) → 1/0 ---
        self.mark("@__map_có")
        self.emit("THAM_I", 0); self.emit("THAM_I", 1); self.emit_addr("@__map_tìm"); self.emit("GỌI_N", 2)
        self.emit("NẠP", 0); self.emit("KHÁC"); self.emit("TRẢ_VỀ_N")                                # nd != 0
        # --- @__map_đặt(m, k, v) → m  (sửa nếu có; chèn-đầu nếu chưa) ---
        NEW = self.new_label()
        self.mark("@__map_đặt")
        self.emit("THAM_I", 0); self.emit("THAM_I", 1); self.emit_addr("@__map_tìm"); self.emit("GỌI_N", 2)
        self.emit("NHÂN_BẢN"); self.emit_addr(NEW); self.emit("ĐỔI"); self.emit("NHẢY_NẾU_0_X")      # nd==0 → chèn
        self.emit("NẠP", 1); self.emit("CỘNG"); self.emit("THAM_I", 2); self.emit("LƯU_GIÁN")        # ram[nd+1]=v
        self.emit("THAM_I", 0); self.emit("TRẢ_VỀ_N")
        self.mark(NEW); self.emit("BỎ")                                                              # bỏ nd(=0)
        self.emit("TẢI_Ô", HEAP_PTR_CELL); self.emit("LƯU_Ô", MAP_NODE)                              # node = hp
        self.emit("TẢI_Ô", MAP_NODE); self.emit("THAM_I", 1); self.emit("LƯU_GIÁN")                  # ram[node]=k
        self.emit("TẢI_Ô", MAP_NODE); self.emit("NẠP", 1); self.emit("CỘNG"); self.emit("THAM_I", 2); self.emit("LƯU_GIÁN")  # ram[node+1]=v
        self.emit("THAM_I", 0); self.emit_untag(); self.emit("LƯU_Ô", MAP_HDR)                       # header addr
        self.emit("TẢI_Ô", MAP_NODE); self.emit("NẠP", 2); self.emit("CỘNG")
        self.emit("TẢI_Ô", MAP_HDR); self.emit("TẢI_GIÁN"); self.emit("LƯU_GIÁN")                    # ram[node+2]=head cũ
        self.emit("TẢI_Ô", MAP_HDR); self.emit("TẢI_Ô", MAP_NODE); self.emit("LƯU_GIÁN")            # ram[header]=node
        self.emit("TẢI_Ô", HEAP_PTR_CELL); self.emit("NẠP", 3); self.emit("CỘNG"); self.emit("LƯU_Ô", HEAP_PTR_CELL)  # hp+=3
        self.emit("THAM_I", 0); self.emit("TRẢ_VỀ_N")
        # --- @__map_xoá(m, k) → m  (gỡ liên kết node; prev=0 ⇒ vá header) ---
        XL, XNEXT, XDONE, XHEAD = (self.new_label(), self.new_label(), self.new_label(), self.new_label())
        self.mark("@__map_xoá")
        self.emit("THAM_I", 0); self.emit_untag(); self.emit("LƯU_Ô", MAP_HDR)                       # header addr
        self.emit("TẢI_Ô", MAP_HDR); self.emit("TẢI_GIÁN"); self.emit("LƯU_Ô", MAP_CUR)             # cur=head
        self.emit("NẠP", 0); self.emit("LƯU_Ô", MAP_PREV)                                            # prev=0
        self.mark(XL)
        self.emit_addr(XDONE); self.emit("TẢI_Ô", MAP_CUR); self.emit("NHẢY_NẾU_0_X")               # cur==0 → xong
        self.emit("TẢI_Ô", MAP_CUR); self.emit("TẢI_GIÁN"); self.emit("THAM_I", 1)
        self.emit_addr("@__bằng"); self.emit("GỌI_N", 2)                                             # khoá==k?
        self.emit_addr(XNEXT); self.emit("ĐỔI"); self.emit("NHẢY_NẾU_0_X")                           # ==0 (khác) → next
        # trùng khoá: next = ram[cur+2]
        self.emit("TẢI_Ô", MAP_CUR); self.emit("NẠP", 2); self.emit("CỘNG"); self.emit("TẢI_GIÁN"); self.emit("LƯU_Ô", MAP_T)
        self.emit_addr(XHEAD); self.emit("TẢI_Ô", MAP_PREV); self.emit("NHẢY_NẾU_0_X")               # prev==0 → vá header
        self.emit("TẢI_Ô", MAP_PREV); self.emit("NẠP", 2); self.emit("CỘNG"); self.emit("TẢI_Ô", MAP_T); self.emit("LƯU_GIÁN")  # ram[prev+2]=next
        self.emit("THAM_I", 0); self.emit("TRẢ_VỀ_N")
        self.mark(XHEAD)
        self.emit("TẢI_Ô", MAP_HDR); self.emit("TẢI_Ô", MAP_T); self.emit("LƯU_GIÁN")               # ram[header]=next
        self.emit("THAM_I", 0); self.emit("TRẢ_VỀ_N")
        self.mark(XNEXT)
        self.emit("TẢI_Ô", MAP_CUR); self.emit("LƯU_Ô", MAP_PREV)                                    # prev=cur
        self.emit("TẢI_Ô", MAP_CUR); self.emit("NẠP", 2); self.emit("CỘNG"); self.emit("TẢI_GIÁN"); self.emit("LƯU_Ô", MAP_CUR)  # cur=next
        self.emit_jump(XL)
        self.mark(XDONE); self.emit("THAM_I", 0); self.emit("TRẢ_VỀ_N")
        # --- @__map_dài(m) → số node ---
        DL, DE = self.new_label(), self.new_label()
        self.mark("@__map_dài")
        self.emit("THAM_I", 0); self.emit_untag(); self.emit("TẢI_GIÁN"); self.emit("LƯU_Ô", MAP_CUR)  # cur=head
        self.emit("NẠP", 0); self.emit("LƯU_Ô", MAP_T)                                                  # đếm=0
        self.mark(DL)
        self.emit_addr(DE); self.emit("TẢI_Ô", MAP_CUR); self.emit("NHẢY_NẾU_0_X")
        self.emit("TẢI_Ô", MAP_T); self.emit("NẠP", 1); self.emit("CỘNG"); self.emit("LƯU_Ô", MAP_T)
        self.emit("TẢI_Ô", MAP_CUR); self.emit("NẠP", 2); self.emit("CỘNG"); self.emit("TẢI_GIÁN"); self.emit("LƯU_Ô", MAP_CUR)
        self.emit_jump(DL)
        self.mark(DE); self.emit("TẢI_Ô", MAP_T); self.emit("TRẢ_VỀ_N")
        # --- @__map_khoá(m) / @__map_giá(m) → danh sách (thứ tự CHÈN: cũ→mới) ---
        # head=mới nhất; cons khi duyệt head→tail ⇒ kết quả đảo lại = thứ tự chèn. (off=0:khoá, 1:giá)
        for tên, off in (("@__map_khoá", 0), ("@__map_giá", 1)):
            KL, KE = self.new_label(), self.new_label()
            self.mark(tên)
            self.emit("THAM_I", 0); self.emit_untag(); self.emit("TẢI_GIÁN"); self.emit("LƯU_Ô", MAP_CUR)  # cur=head
            self.emit_const(NIL); self.emit("LƯU_Ô", MAP_T)                                                 # acc=NIL
            self.mark(KL)
            self.emit_addr(KE); self.emit("TẢI_Ô", MAP_CUR); self.emit("NHẢY_NẾU_0_X")
            self.emit("TẢI_Ô", MAP_CUR)
            if off: self.emit("NẠP", off); self.emit("CỘNG")
            self.emit("TẢI_GIÁN")                                                                            # phần tử
            self.emit("TẢI_Ô", MAP_T); self.emit_cons(); self.emit("LƯU_Ô", MAP_T)                          # acc=cons(x,acc)
            self.emit("TẢI_Ô", MAP_CUR); self.emit("NẠP", 2); self.emit("CỘNG"); self.emit("TẢI_GIÁN"); self.emit("LƯU_Ô", MAP_CUR)
            self.emit_jump(KL)
            self.mark(KE); self.emit("TẢI_Ô", MAP_T); self.emit("TRẢ_VỀ_N")

    def type_of(self, n):                            # suy kiểu tối giản (để in chuỗi/thực đúng)
        t = type(n)
        if t is Str: return 'str'
        if t is TruthLit: return 'num'               # sáng/tối → 1/0
        if t is Num: return 'float' if isinstance(n.v, float) else 'num'
        if t is ListLit: return 'list'
        if t is Bin:
            lt, rt = self.type_of(n.l), self.type_of(n.r)
            if n.op in ("+","-","*","/") and 'float' in (lt, rt): return 'float'
            if n.op == '+' and 'str' in (lt, rt): return 'str'
            return 'num'
        if t is VarRef: return self.var_type.get(n.name, '?')
        if t is Goi and type(n.callee) is VarRef:
            nm = n.callee.name
            if nm in ('bản','ban','đặt_khoá','dat_khoa','xoá_khoá','xoa_khoa'): return 'bản'  # trả lại chính bản
            if nm in ('khoá','khoa','giá_trị','gia_tri'): return 'list'
            if nm in ('ghép','ghep','đuôi','duoi'): return self.type_of(n.args[0]) if n.args else '?'
            if nm in ('dài','dai','đầu','dau'): return 'num'
            if nm in ('là_số','la_so','là_ds','la_ds','có_khoá','co_khoa'): return 'num'  # 0/1 → in bằng RỌI
        return '?'
    def fcell(self, name):
        if name not in self.field_addr: self.field_addr[name] = len(self.field_addr)
        return self.field_addr[name]
    def vcell(self, name):
        if name not in self.var_addr: self.var_addr[name] = len(self.var_addr)
        return self.var_addr[name]

    # --- biểu thức → để lại 1 ô trên ngăn xếp ---
    def _cấm_thực_đối(self, args, tên):
        "Chặn SỐ THỰC truyền qua đối hàm người dùng (tham số không mang kiểu ⇒ tránh sai-ngầm)."
        for a in args:
            if self.type_of(a) == 'float':
                raise ValueError(f"số thực truyền vào đối của '{tên}' CHƯA biên dịch xuống máy "
                                 f"(tham số máy không mang kiểu — số thực chỉ ở biểu thức/biến 'đặt' trực tiếp)")

    def intern_strings(self, ast):
        "Dựng SẴN mọi chuỗi-hằng dùng ≥2 lần (1 lần lúc khởi động) → mọi lần dùng sau chỉ TẢI_Ô."
        from collections import Counter
        đếm = Counter()
        def walk(n):
            if n is None: return
            if type(n) is Str: đếm[n.v] += 1
            for v in getattr(n, "__dict__", {}).values():
                if isinstance(v, list):
                    for x in v:
                        if hasattr(x, "__dict__"): walk(x)
                elif hasattr(v, "__dict__"): walk(v)
        for s in ast: walk(s)
        for nội, c in đếm.items():               # giữ THỨ TỰ xuất hiện ⇒ bytecode tất định
            if c >= 2:                            # chỉ intern chuỗi LẶP (chuỗi 1-lần giữ nguyên — bytecode cũ)
                ô = self.vcell(("__str__", nội))
                self.str_cell[nội] = ô
                self.emit_list([Num(ord(ch)) for ch in nội]); self.emit("LƯU_Ô", ô)

    def collect_locals(self, stmts):
        "Tên biến CỤC BỘ ở MỨC hàm này (đặt / biến-lặp / tên-bắt) — KHÔNG chui vào lam/hàm lồng."
        names = []
        def add(n):
            if n not in names: names.append(n)
        def walk(ss):
            for s in ss:
                t = type(s)
                if t is Dat: add(s.name)
                elif t is LapTrong: add(s.var); walk(s.body)
                elif t is Lap: walk(s.body)
                elif t is Mai: walk(s.body)
                elif t is Neu:
                    walk(s.then)
                    if s.khac: walk(s.khac)
                elif t is ThuBat:
                    walk(s.thu)
                    if s.tên: add(s.tên)
                    walk(s.bat)
                # Decl/Hoc/Giao/Roi/Tra/ExprStmt/Dung: không sinh biến cục bộ;
                # HamDef/Lam lồng: có KHUNG riêng → KHÔNG gom
        walk(stmts)
        return names
    def emit_store(self, name):
        "GHI biến: ô-KHUNG (LƯU_THAM_I) nếu cục bộ/tham số, ngược lại ô-TOÀN-CỤC (LƯU_Ô)."
        if name in self.frame_names:
            self.emit("LƯU_THAM_I", self.frame_names.index(name))
        else:
            self.emit("LƯU_Ô", self.vcell(name))

    def expr_as_float(self, n):
        "Phát n rồi đảm bảo ở thang điểm-cố-định ×FSCALE (số nguyên → nhân thang để đồng thang)."
        self.expr(n)
        if self.type_of(n) != 'float':
            self.emit_const(FSCALE); self.emit("NHÂN")   # int → fixed-point (×FSCALE)

    def expr(self, n):
        t = type(n)
        if t is Num:
            if isinstance(n.v, float):                            # SỐ THỰC (nguồn có '.') → điểm-cố-định ×FSCALE
                q = int(round(n.v * FSCALE))
                if not (-(1 << 31) <= q < (1 << 31)):
                    raise ValueError(f"số thực {n.v} ngoài phạm vi điểm-cố-định 32-bit (|x| < {(1<<31)//FSCALE})")
                self.emit_const(q & 0xFFFFFFFF); return
            v = int(n.v)
            if v < 0 or v > 0xFFFFFFFF: raise ValueError(f"hằng {v} ngoài phạm vi 32-bit")
            self.emit_const(v)
        elif t is ListLit:
            self.emit_list(n.elems)                  # danh sách → cons-cell trên heap
        elif t is Str:
            if n.v in self.str_cell:                        # chuỗi INTERN (dùng nhiều): nạp con trỏ đã dựng
                self.emit("TẢI_Ô", self.str_cell[n.v])
            else:
                self.emit_list([Num(ord(ch)) for ch in n.v])   # chuỗi dùng 1 lần → dựng tại chỗ (heap)
        elif t is Lam:
            self.compile_lam(n)                      # hàm vô danh/closure → con trỏ heap
        elif t is TruthLit:                          # sáng → 1, tối → 0 (trị-chân-lý máy; γ chỉ ở thông dịch)
            self.emit("NẠP", 1 if n.t == SANG else 0)
        elif t is AnLit:
            self.emit("ẨN")
        elif t is VarRef:
            if n.name in self.frame_names:
                self.emit("THAM_I", self.frame_names.index(n.name))   # ô THAM_I thứ i của khung (bắt/tham số)
            else:
                self.emit("TẢI_Ô", self.vcell(n.name))
        elif t is Bin and n.op == "+":
            if self.type_of(n) == 'float':                                     # SỐ THỰC: cộng cùng thang
                self.expr_as_float(n.l); self.expr_as_float(n.r); self.emit("CỘNG")
            elif self.tagged:
                self.expr(n.l); self.expr(n.r); self.emit_addr("@__cộng"); self.emit("GỌI_N", 2)  # số+số | nối chuỗi
            else:
                self.expr(n.l); self.expr(n.r); self.emit("CỘNG")             # cũ: cộng số 16-bit
        elif t is Bin and n.op in ("-","*","/"):
            if self.type_of(n) == 'float':                                     # SỐ THỰC điểm-cố-định
                self.expr_as_float(n.l); self.expr_as_float(n.r)
                self.emit({"-":"TRỪ","*":"FNHÂN","/":"FCHIA"}[n.op])
            else:
                self.expr(n.l); self.expr(n.r)
                self.emit({"-":"TRỪ","*":"NHÂN","/":"CHIA"}[n.op])            # chia SỐ NGUYÊN (máy)
        elif t is Bin and n.op in ("==", "!="):
            if 'float' in (self.type_of(n.l), self.type_of(n.r)):             # so SỐ THỰC: đưa cùng thang
                self.expr_as_float(n.l); self.expr_as_float(n.r)
                self.emit("BẰNG" if n.op == "==" else "KHÁC")
            elif self.tagged:                                                 # CẤU TRÚC (chuỗi/ds đệ quy)
                self.expr(n.l); self.expr(n.r); self.emit_addr("@__bằng"); self.emit("GỌI_N", 2)
                if n.op == "!=": self.emit("NẠP", 1); self.emit("ĐỔI"); self.emit("TRỪ")   # 1 − bằng
            else:
                self.expr(n.l); self.expr(n.r); self.emit("BẰNG" if n.op == "==" else "KHÁC")
        elif t is Bin and n.op in ("<",">","<=",">="):
            if 'float' in (self.type_of(n.l), self.type_of(n.r)):            # so SỐ THỰC cùng thang
                self.expr_as_float(n.l); self.expr_as_float(n.r)
            else:
                self.expr(n.l); self.expr(n.r)
            self.emit({"<":"BÉ_HƠN",">":"LỚN_HƠN","<=":"BÉ_BẰNG",">=":"LỚN_BẰNG"}[n.op])
        elif t is Index:
            self.expr(n.coll); self.expr(n.idx)
            if self.type_of(n.coll) == 'bản':       # m[khoá] = tra cứu bản (thiếu → ẩn)
                self.emit_addr("@__map_lấy"); self.emit("GỌI_N", 2)
            else:                                    # l[i] = đi i bước cdr rồi car
                self.emit_addr("@__lấy"); self.emit("GỌI_N", 2)
        elif t is Goi:
            nm = n.callee.name if type(n.callee) is VarRef else None
            if nm in ("gọi_hệ", "goi_he"):         # ★ TRAP xuống NHÂN: gọi_hệ(số, đối…)
                for a in n.args: self.expr(a)      # đẩy số hiệu rồi tới các đối
                self.emit("GỌI_HỆ", len(n.args) - 1)
            elif nm in ("đầu", "dau"):             # car = ram[addr(con_trỏ)]
                self.expr(n.args[0]); self.emit_untag(); self.emit("TẢI_GIÁN")
            elif nm in ("đuôi", "duoi"):           # cdr = ram[addr(con_trỏ) + 1]
                self.expr(n.args[0]); self.emit_untag(); self.emit("NẠP", 1); self.emit("CỘNG"); self.emit("TẢI_GIÁN")
            elif nm in ("dài", "dai"):             # độ dài: bản → số node; danh sách → độ dài cons
                self.expr(n.args[0])
                self.emit_addr("@__map_dài" if self.type_of(n.args[0]) == 'bản' else "@__dài")
                self.emit("GỌI_N", 1)
            elif nm in ("ghép", "ghep"):           # nối (hàm trợ giúp phát 1 lần)
                self.expr(n.args[0]); self.expr(n.args[1]); self.emit_addr("@__ghép"); self.emit("GỌI_N", 2)
            elif nm in ("bản", "ban"):             # BẢN rỗng (map/record — tham chiếu mutable)
                self.emit_map_new()
            elif nm in ("đặt_khoá", "dat_khoa"):   # m[k]=v (mutate, trả lại m)
                for a in n.args: self.expr(a)
                self.emit_addr("@__map_đặt"); self.emit("GỌI_N", 3)
            elif nm in ("lấy_khoá", "lay_khoa"):   # m[k] hoặc ẩn
                self.expr(n.args[0]); self.expr(n.args[1]); self.emit_addr("@__map_lấy"); self.emit("GỌI_N", 2)
            elif nm in ("có_khoá", "co_khoa"):     # 1/0
                self.expr(n.args[0]); self.expr(n.args[1]); self.emit_addr("@__map_có"); self.emit("GỌI_N", 2)
            elif nm in ("xoá_khoá", "xoa_khoa"):   # gỡ khoá (mutate, trả lại m)
                self.expr(n.args[0]); self.expr(n.args[1]); self.emit_addr("@__map_xoá"); self.emit("GỌI_N", 2)
            elif nm in ("khoá", "khoa"):           # danh sách khoá (thứ tự chèn)
                self.expr(n.args[0]); self.emit_addr("@__map_khoá"); self.emit("GỌI_N", 1)
            elif nm in ("giá_trị", "gia_tri"):     # danh sách giá trị (thứ tự chèn)
                self.expr(n.args[0]); self.emit_addr("@__map_giá"); self.emit("GỌI_N", 1)
            elif nm in ("là_số", "la_so"):         # THẺ: số ⟺ giá trị < TAG
                self.expr(n.args[0]); self.emit_const(TAG); self.emit("BÉ_HƠN")
            elif nm in ("là_ds", "la_ds"):         # THẺ: danh sách ⟺ giá trị ≥ TAG (mang bit 30)
                self.expr(n.args[0]); self.emit_const(TAG); self.emit("LỚN_BẰNG")
            elif nm in ("rọi_ds", "roi_ds"):       # in danh sách số (PEEK; ExprStmt 'BỎ' dọn sau)
                self.expr(n.args[0]); self.emit("RỌI_DS")
            elif nm in ("xuất", "xuat"):           # XUẤT (MMIO console + ρ cho γ-scheduler)
                self.expr(n.args[0]); self.emit("XUẤT"); self.emit("ẨN")
            elif nm in ("tác_vụ", "tac_vu"):       # đăng ký tiến trình (đối = TÊN HÀM không-tham-số)
                cal = n.args[0]
                if not (type(cal) is VarRef and cal.name in self.fn_labels):
                    raise ValueError("tác_vụ cần TÊN HÀM (tiến trình không tham số) đã định nghĩa")
                self.emit_addr(self.fn_labels[cal.name]); self.emit("TÁC_VỤ"); self.emit("ẨN")
            elif nm in ("lịch_học", "lich_hoc"):   # khởi động γ-scheduler (đối = lượng tử hằng ≤255)
                q = n.args[0]
                if not (type(q) is Num and 1 <= int(q.v) <= 255):
                    raise ValueError("lịch_học cần lượng tử HẰNG trong 1..255")
                self.emit("HẸN_GIỜ", int(q.v)); self.emit("LỊCH_HỌC"); self.emit("ẨN")
            elif nm in self.fn_labels:
                self._cấm_thực_đối(n.args, nm)
                for a in n.args: self.expr(a)                  # đẩy các đối số theo thứ tự
                self.emit_addr(self.fn_labels[nm]); self.emit("GỌI_N", len(n.args))
            elif (type(n.callee) is Lam or type(n.callee) is Goi
                  or (type(n.callee) is VarRef
                      and (n.callee.name in self.frame_names or n.callee.name in self.var_addr))):
                # GỌI CLOSURE: callee là GIÁ TRỊ hàm (tham số, kết quả gọi, lam, hoặc biến giữ closure)
                self._cấm_thực_đối(n.args, nm or "closure")
                for a in n.args: self.expr(a)                  # đẩy đối số
                self.expr(n.callee)                            # đẩy con trỏ closure (đỉnh)
                self.emit("GỌI_CLOSURE", len(n.args))
            else:
                raise ValueError(f"lời gọi '{nm}' KHÔNG biên dịch xuống máy "
                                 f"(builtin/hàm này chỉ có ở thông dịch — vd cộng_hưởng/tim/đọc_tệp…)")
        else:
            tên = {"Lam":"hàm vô danh/closure"}.get(t.__name__, t.__name__)
            raise ValueError(f"biểu thức '{tên}' KHÔNG biên dịch xuống máy (chỉ chạy ở thông dịch giao.py)")

    # --- khối lệnh (có peephole: giao k=X ; rọi k → GIAO a ; RỌI) ---
    def block(self, stmts):
        i = 0
        while i < len(stmts):
            s = stmts[i]
            if (type(s) is Giao and i+1 < len(stmts)
                    and type(stmts[i+1]) is Roi and type(stmts[i+1].expr) is VarRef
                    and stmts[i+1].expr.name == s.target):
                self.emit("GIAO", self.fcell(s.ifname))   # đẩy tri/γ
                self.emit("RỌI")                           # in ngay (giữ nguyên γ)
                i += 2; continue
            self.stmt(s); i += 1

    def stmt(self, s):
        t = type(s)
        if t is Decl and s.field == "vật":
            self.expr(s.expr); self.emit("LƯU_VẬT", self.fcell(s.name))
        elif t is Decl and s.field == "tâm":
            self.expr(s.expr); self.emit("LƯU_TÂM", self.fcell(s.name))
        elif t is Hoc:
            self.emit("HỌC", self.fcell(s.name))
        elif t is Giao:
            self.emit("GIAO", self.fcell(s.ifname))
            self.emit("LƯU_Ô", self.vcell(s.target))   # (mất γ — chỉ giữ giá trị)
        elif t is Roi:
            tk = self.type_of(s.expr)
            if tk == 'str':                          # in chuỗi = duyệt heap
                self.expr(s.expr); self.emit("RỌI_CHUỖI")
            elif tk == 'float':                      # in số thực điểm-cố-định
                self.expr(s.expr); self.emit("RỌI_THỰC")
            elif tk == '?':                          # CHƯA RÕ KIỂU (vd tham số hàm) → suy lúc CHẠY
                self.expr(s.expr); self.emit("RỌI_AUTO")
            else:
                self.expr(s.expr); self.emit("RỌI")
        elif t is Dat:
            self.expr(s.expr); self.emit_store(s.name)           # ô-khung nếu cục bộ, ngược lại toàn-cục
            self.var_type[s.name] = self.type_of(s.expr)
        elif t is Lap:
            self.compile_lap(s)
        elif t is LapTrong:
            self.compile_lap_trong(s)
        elif t is Mai:
            self.compile_mai(s)
        elif t is ThuBat:
            self.compile_thu_bat(s)
        elif t is Dung:                              # thoát vòng lặp gần nhất
            if not self.loop_end:
                raise ValueError("'dừng' nằm NGOÀI vòng lặp (không có vòng để thoát)")
            self.emit_jump(self.loop_end[-1])
        elif t is Tra:
            self.expr(s.expr); self.emit("TRẢ_VỀ_N")  # trị trả về ở đỉnh ngăn xếp; bỏ khung
        elif t is Neu:
            self.compile_neu(s)
        elif t is ExprStmt:
            self.expr(s.expr); self.emit("BỎ")
        else:
            tên = {"KhiVienMan":"khi viên_mãn",
                   "TroiReg":"trôi","TroiTick":"trôi","Nhap":"nhập"}.get(
                   t.__name__, t.__name__)
            raise ValueError(f"câu lệnh '{tên}' KHÔNG biên dịch xuống máy (chỉ chạy ở thông dịch giao.py)")

    def compile_mai(self, s):
        "mãi { } — vòng LIÊN TỤC (không điều kiện); chạy tới khi 'dừng'."
        L0, L1 = self.new_label(), self.new_label()
        self.loop_end.append(L1)
        self.mark(L0)
        self.block(s.body)
        self.emit_jump(L0)
        self.mark(L1)
        self.loop_end.pop()

    def compile_thu_bat(self, s):
        "thử { thu } bắt (tên) { bắt } — đặt handler; lỗi (NÉM) trong thu gỡ-cuộn tới nhánh bắt."
        L_h, L_end = self.new_label(), self.new_label()
        self.emit_addr(L_h); self.emit("BẮT_ĐẦU_THỬ")     # mở vùng thử (lưu sâu các ngăn xếp)
        self.block(s.thu)
        self.emit("HẾT_THỬ")                               # thử êm → gỡ handler
        self.emit_jump(L_end)
        self.mark(L_h)                                     # handler: trị-lỗi ở đỉnh ngăn xếp
        if s.tên is not None:
            self.emit_store(s.tên); self.var_type[s.tên] = '?'   # tên ← mã lỗi (ô-khung/toàn-cục)
        else:
            self.emit("BỎ")
        self.block(s.bat)
        self.mark(L_end)

    def compile_neu(self, s):
        "nếu cond { then } khác { else }. cond ra 0/1 (so sánh) → NHẢY_NẾU_0_X tới nhánh else."
        if s.ngo is not None:
            raise ValueError("rẽ BA NGẢ 'ngờ' (nhánh ẩn) KHÔNG biên dịch xuống máy — "
                             "máy chỉ có nếu/khác hai ngả (chỉ chạy ở thông dịch)")
        L_else, L_end = self.new_label(), self.new_label()
        self.emit_addr(L_else); self.expr(s.cond); self.emit("NHẢY_NẾU_0_X")   # cond==0 → else
        self.block(s.then); self.emit_jump(L_end)
        self.mark(L_else)
        if s.khac: self.block(s.khac)
        self.mark(L_end)

    def compile_lap(self, s):
        if type(s.count) is not Num: raise ValueError("lặp cần số đếm hằng (chỉ thông dịch nếu là biểu thức)")
        if isinstance(s.count.v, float) and s.count.v != int(s.count.v):
            raise ValueError("lặp cần số đếm NGUYÊN")
        cnt = self.vcell(self.new_label())          # ô đếm riêng
        L0, L1 = self.new_label(), self.new_label()
        self.emit_const(int(s.count.v)); self.emit("LƯU_Ô", cnt)   # hằng tới 32-bit (vòng lớn)
        self.loop_end.append(L1)
        self.mark(L0)
        self.emit_addr(L1); self.emit("TẢI_Ô", cnt); self.emit("NHẢY_NẾU_0_X")
        self.block(s.body)
        self.emit("TẢI_Ô", cnt); self.emit("NẠP", 1); self.emit("TRỪ"); self.emit("LƯU_Ô", cnt)
        self.emit_jump(L0)
        self.mark(L1)
        self.loop_end.pop()

    def compile_lap_trong(self, s):
        "lặp x trong <ds/chuỗi/bản> { } — DUYỆT (không đệ quy). Bản → duyệt KHOÁ (qua @__map_khoá)."
        it_kind = self.type_of(s.iterable)
        self.expr(s.iterable)
        if it_kind == 'bản':                            # bản → danh sách khoá rồi duyệt
            self.emit_addr("@__map_khoá"); self.emit("GỌI_N", 1)
        cur = self.vcell(self.new_label())              # ô con trỏ duyệt (temp toàn-cục)
        self.emit("LƯU_Ô", cur)                         # cur = head
        # CHUỖI: mỗi phần tử là MÃ ký tự; ở chế độ THẺ bọc thành chuỗi-1-ký-tự để khớp thông dịch
        # (thông dịch duyệt chuỗi cho ra chuỗi-độ-dài-1). Chế độ 16-bit: cho ra MÃ số (tài liệu hoá).
        is_str = (it_kind == 'str') and self.tagged
        self.var_type[s.var] = 'str' if is_str else '?'
        L0, L1 = self.new_label(), self.new_label()
        self.loop_end.append(L1)
        self.mark(L0)
        self.emit_addr(L1); self.emit("TẢI_Ô", cur); self.emit("NHẢY_NẾU_0_X")   # cur==NIL(0) → hết
        self.emit("TẢI_Ô", cur); self.emit_untag(); self.emit("TẢI_GIÁN")        # mã/phần tử = car(cur)
        if is_str: self.emit_const(NIL); self.emit_cons()                        # → cons(mã, NIL) = chuỗi 1 ký tự
        self.emit_store(s.var)                                                   # x = phần tử vòng (ô-khung/toàn-cục)
        self.emit("TẢI_Ô", cur); self.emit_untag(); self.emit("NẠP", 1); self.emit("CỘNG")
        self.emit("TẢI_GIÁN"); self.emit("LƯU_Ô", cur)                            # cur = cdr(cur)
        self.block(s.body)
        self.emit_jump(L0)
        self.mark(L1)
        self.loop_end.pop()

    def emit_addr(self, label):                      # đẩy ĐỊA CHỈ 16-bit của nhãn (4 lệnh cố định)
        self.code.append(("ĐỊACHỈ", label))
    def emit_jump(self, label):                      # nhảy không điều kiện tới nhãn (gián tiếp)
        self.emit_addr(label); self.emit("NHẢY_X")

    # --- chốt chương trình & rải nhãn (hỗ trợ nhảy gián tiếp 16-bit) ---
    def assemble(self):
        self.mark("@END"); self.emit("DỪNG")
        if getattr(GiaoC, "BẬT_TỐI_ƯU", True):       # ★ PHA 3 — tầng tối-ưu bytecode (peephole, conformance-safe)
            self.code = tối_ưu_mã(self.code)
        addr, labels = 0, {}
        for name, op in self.code:                   # lượt 1: gán địa chỉ (ĐỊACHỈ = 4 lệnh)
            if name == "NHÃN": labels[op] = addr
            elif name == "ĐỊACHỈ": addr += 4
            else: addr += 1
        words = []
        for name, op in self.code:                   # lượt 2: phát mã
            if name == "NHÃN": continue
            if name == "ĐỊACHỈ":
                a = labels[op]                       # nạp địa chỉ 16-bit: NẠP hi;DỊCH_TRÁI 8;NẠP lo;CỘNG
                words.append((OPS["NẠP"] << 8) | ((a >> 8) & 0xFF))
                words.append((OPS["DỊCH_TRÁI"] << 8) | 8)
                words.append((OPS["NẠP"] << 8) | (a & 0xFF))
                words.append((OPS["CỘNG"] << 8) | 0)
                continue
            operand = labels[op] if isinstance(op, str) else op
            words.append((OPS[name] << 8) | (operand & 0xFF))
        return words

def uses_tag(ast):
    """Chương trình có CẦN ABI thẻ 32-bit không? ⟺ cần phân biệt số/con-trỏ lúc chạy:
       • gọi là_số/là_ds, HOẶC
       • +/==/!= ĐA HÌNH trên chuỗi/danh sách (toán hạng là Str/ListLit) — cần __cộng/__bằng, HOẶC
       • duyệt CHUỖI literal (lặp x trong "…") — phần tử thành chuỗi-1-ký-tự, cần thẻ để nối/so."""
    found = [False]
    def walk(n):
        if found[0] or n is None: return
        if type(n) is Goi and type(n.callee) is VarRef and n.callee.name in ("là_số","la_so","là_ds","la_ds"):
            found[0] = True; return
        if type(n) is Bin and n.op in ("+","==","!=") and (
                type(n.l) in (Str, ListLit) or type(n.r) in (Str, ListLit)):
            found[0] = True; return                  # nối/so chuỗi-hoặc-danh-sách ⇒ cần đa hình
        if type(n) is LapTrong and type(n.iterable) is Str:
            found[0] = True; return                  # duyệt chuỗi literal ⇒ phần tử là chuỗi-1-ký-tự
        for v in getattr(n, "__dict__", {}).values():
            if isinstance(v, list):
                for x in v:
                    if hasattr(x, "__dict__"): walk(x)
            elif hasattr(v, "__dict__"): walk(v)
    for s in ast: walk(s)
    return found[0]

MAP_BUILTINS = ("bản","ban","đặt_khoá","dat_khoa","lấy_khoá","lay_khoa","có_khoá","co_khoa",
                "xoá_khoá","xoa_khoa","khoá","khoa","giá_trị","gia_tri")
def uses_map(ast):
    "Chương trình có dùng BẢN (map/record) không? ⟺ có gọi một builtin bản nào."
    found = [False]
    def walk(n):
        if found[0] or n is None: return
        if type(n) is Goi and type(n.callee) is VarRef and n.callee.name in MAP_BUILTINS:
            found[0] = True; return
        for v in getattr(n, "__dict__", {}).values():
            if isinstance(v, list):
                for x in v:
                    if hasattr(x, "__dict__"): walk(x)
            elif hasattr(v, "__dict__"): walk(v)
    for s in ast: walk(s)
    return found[0]

# ============================================================
# ★ PHA 3 (Track C — Compiler/Tốc độ) — TẦNG TỐI-ƯU BYTECODE #1
# ------------------------------------------------------------
# Peephole conformance-safe trên list (tên, toán-hạng). Mọi luật PROVABLY giữ ngữ-nghĩa
# (giá-trị + ba-trị sáng/ẩn/tối) trên MỌI độ-rộng-từ; chạy tới điểm-bất-động.
# RÀO an-toàn: luật chỉ khớp các lệnh LIỀN KỀ cùng tên → KHÔNG bao giờ khớp xuyên 'NHÃN'/'ĐỊACHỉ'
#   (nhảy chỉ đáp vào NHÃN; nếu NHÃN nằm giữa cửa-sổ thì code[i+k][0]≠tên-mong-đợi ⇒ luật không fire).
# Gấp-hằng nhị-phân: cả hai toán-hạng là NẠP immediate (0-255, KNOWN-sáng) ⇒ kết-quả KNOWN-sáng y hệt.
#   số-học: CỘNG/TRỪ/NHÂN/CHIA (CHIA = trunc-về-0; với 0-255 dương = a//b).  so-sánh → 1/0.
def _b_chia(a, b): return (a // b) if b != 0 else 0       # khớp GVM: int(a/b) cho a,b≥0
_FOLD = {"CỘNG": lambda a, b: a + b, "TRỪ": lambda a, b: a - b, "NHÂN": lambda a, b: a * b,
         "CHIA": _b_chia,
         "BẰNG": lambda a, b: 1 if a == b else 0, "KHÁC": lambda a, b: 1 if a != b else 0,
         "BÉ_HƠN": lambda a, b: 1 if a < b else 0, "LỚN_HƠN": lambda a, b: 1 if a > b else 0,
         "BÉ_BẰNG": lambda a, b: 1 if a <= b else 0, "LỚN_BẰNG": lambda a, b: 1 if a >= b else 0}
_TERM = {"DỪNG", "NHẢY", "NHẢY_X", "NHẢY_ĐỘNG", "TRẢ_VỀ", "TRẢ_VỀ_N", "NÉM", "NGẮT_VỀ"}  # lệnh dứt luồng (sau nó tới NHÃN = chết)
# ★ PHA A (IR-lite) — phân-loại lệnh cho abstract-interp block-local:
_CTRL_A   = _TERM | {"NHÃN", "NHẢY_NẾU_0", "NHẢY_NẾU_0_X", "NHẢY_SÁNG", "NHẢY_TỐI", "NHẢY_ẨN"}  # nhánh/join/dứt → trạng-thái vào KHÔNG-RÕ ⇒ flush ALL
_CLOBBER_A = {"LƯU_GIÁN", "GHI_TRƯỜNG", "GỌI", "GỌI_N", "GỌI_X", "GỌI_CLOSURE", "TÁC_TỬ",       # ghi ô RAM (gián-tiếp/qua callee) → ô-hằng có thể đổi ⇒ xoá kc + stk
                "HẸN_GIỜ", "LƯU_THAM_I", "DÀNH_CB"}
def _là_2mũ(x): return isinstance(x, int) and x > 1 and (x & (x - 1)) == 0

def _peephole(code):
    đổi = True
    while đổi:
        đổi = False
        ra = []
        i, n = 0, len(code)
        while i < n:
            nm, op = code[i]
            nx = code[i+1] if i+1 < n else (None, None)
            nx2 = code[i+2] if i+2 < n else (None, None)
            # L1 — GỘP DỊCH: DỊCH_TRÁI a; DỊCH_TRÁI b → DỊCH_TRÁI(a+b)  [(x<<a)<<b ≡ x<<(a+b) mod 2^W ∀W]
            if (nm == "DỊCH_TRÁI" and isinstance(op, int) and nx[0] == "DỊCH_TRÁI"
                    and isinstance(nx[1], int) and op + nx[1] <= 255):
                ra.append(("DỊCH_TRÁI", op + nx[1])); i += 2; đổi = True; continue
            # L2 — GẤP HẰNG: NẠP a; NẠP b; {+,−,×,//,so-sánh} → NẠP r  (0≤r≤255; cả 2 immediate-sáng)
            if (nm == "NẠP" and isinstance(op, int) and nx[0] == "NẠP"
                    and isinstance(nx[1], int) and nx2[0] in _FOLD):
                r = _FOLD[nx2[0]](op, nx[1])
                if 0 <= r <= 255:
                    ra.append(("NẠP", r)); i += 3; đổi = True; continue
            # L3 — GẤP DỊCH IMMEDIATE: NẠP a; {DỊCH_TRÁI|DỊCH_PHẢI} b → NẠP(a<<b | a>>b)  khi 0≤r≤255
            if (nm == "NẠP" and isinstance(op, int) and nx[0] in ("DỊCH_TRÁI", "DỊCH_PHẢI")
                    and isinstance(nx[1], int)):
                r = (op << nx[1]) if nx[0] == "DỊCH_TRÁI" else (op >> nx[1])
                if 0 <= r <= 255:
                    ra.append(("NẠP", r)); i += 2; đổi = True; continue
            # L4 — STRENGTH-REDUCTION: NẠP 2^k; NHÂN → DỊCH_TRÁI k  (x·2^k ≡ x<<k; ba-trị y hệt) — 1 lệnh thay 2
            if nm == "NẠP" and _là_2mũ(op) and nx[0] == "NHÂN":
                ra.append(("DỊCH_TRÁI", op.bit_length() - 1)); i += 2; đổi = True; continue
            # L5 — KHỬ DUP-POP: NHÂN_BẢN; BỎ → ∅  (nhân-bản rồi bỏ = không gì)
            if nm == "NHÂN_BẢN" and nx[0] == "BỎ":
                i += 2; đổi = True; continue
            # L6 — KHỬ SWAP-ĐÔI: ĐỔI; ĐỔI → ∅
            if nm == "ĐỔI" and nx[0] == "ĐỔI":
                i += 2; đổi = True; continue
            ra.append(code[i]); i += 1
        code = ra
    return code

def _dce(code):                                  # DEAD-CODE: bỏ lệnh sau lệnh-dứt-luồng tới NHÃN kế (không-tới-được)
    ra = []
    i, n = 0, len(code)
    while i < n:
        ra.append(code[i])
        if code[i][0] in _TERM:                  # sau đây tới NHÃN là chết
            j = i + 1
            while j < n and code[j][0] != "NHÃN":
                j += 1
            i = j                                # nhảy qua vùng chết (giữ NHÃN)
            continue
        i += 1
    return ra

def _siêu_lệnh(code):                             # ★ SIÊU-LỆNH (co-design ISA): gộp idiom → 1 opcode, giảm BƯỚC
    # Lượt 1: NẠP k; CỘNG → CỘNG_HẰNG k  (add-immediate; pop→push top+k. Ba-trị y hệt CỘNG: ẩn→ẩn, else sáng.)
    ra = []
    i, n = 0, len(code)
    while i < n:
        nm, op = code[i]
        nx = code[i+1] if i+1 < n else (None, None)
        if nm == "NẠP" and isinstance(op, int) and nx[0] == "CỘNG":
            ra.append(("CỘNG_HẰNG", op)); i += 2; continue
        ra.append(code[i]); i += 1
    # Lượt 2: NHÂN_BẢN; CỘNG_HẰNG k → NHÂN_CỘNG_HẰNG k  (dup+add-imm: [x]→[x,x+k], heap-cons hp/hp+k. Stack-only, ba-trị y hệt.)
    code, ra = ra, []
    i, n = 0, len(code)
    while i < n:
        nm, op = code[i]
        nx = code[i+1] if i+1 < n else (None, None)
        if nm == "NHÂN_BẢN" and nx[0] == "CỘNG_HẰNG":
            ra.append(("NHÂN_CỘNG_HẰNG", nx[1])); i += 2; continue
        ra.append(code[i]); i += 1
    # Lượt 3: NHÂN_BẢN; TẢI_Ô r; LƯU_GIÁN → GHI_TRƯỜNG r  (store-field: ram[top]=ram[r], giữ top. RAM-to-RAM.)
    code, ra = ra, []
    i, n = 0, len(code)
    while i < n:
        nm, op = code[i]
        nx = code[i+1] if i+1 < n else (None, None)
        nx2 = code[i+2] if i+2 < n else (None, None)
        if nm == "NHÂN_BẢN" and nx[0] == "TẢI_Ô" and isinstance(nx[1], int) and nx2[0] == "LƯU_GIÁN":
            ra.append(("GHI_TRƯỜNG", nx[1])); i += 3; continue
        ra.append(code[i]); i += 1
    # Lượt 4: DỊCH_TRÁI 8; CỘNG_HẰNG k → DỊCH_CỘNG_BYTE k  (dựng-hằng nhiều-byte: (acc<<8)+k. Lượt-1 đã biến NẠP k;CỘNG→CỘNG_HẰNG k.)
    #   Chặn shift==8 (chỉ idiom byte); k≤255 (luôn, vì sinh từ NẠP byte). Stack-only, ba-trị y hệt chuỗi: ẩn→ẩn.
    code, ra = ra, []
    i, n = 0, len(code)
    while i < n:
        nm, op = code[i]
        nx = code[i+1] if i+1 < n else (None, None)
        if nm == "DỊCH_TRÁI" and op == 8 and nx[0] == "CỘNG_HẰNG" and isinstance(nx[1], int) and 0 <= nx[1] <= 255:
            ra.append(("DỊCH_CỘNG_BYTE", nx[1])); i += 2; continue
        ra.append(code[i]); i += 1
    return ra

def _abs_interp(code):
    """★ PHA A — IR-lite: const/copy-propagation XUYÊN-LỆNH block-local (cái peephole-cửa-sổ-kề KHÔNG thấy).
    SOUND nhờ 2 bất-biến:
      (1) model-stack `stk` LUÔN là HẬU-TỐ đã-biết của stack THẬT (mỗi ô: ('K',c) | ('U',)) — pop/push/ĐỔI an-toàn.
      (2) CHỈ theo-dõi hằng 0≤c≤255 ⇒ MỌI fold mask-độc-lập (đúng cả 16-bit lẫn 32-bit), và c phát được bằng 1 `NẠP`.
    `kc`: ô-RAM-trực-tiếp → hằng (đặt bởi `LƯU_Ô` hằng; XOÁ khi clobber/nhánh/join). Viết lại `TẢI_Ô r`→`NẠP c` ⇒ nuôi peephole/siêu-lệnh gập tiếp.
    Lệnh chưa-mô-hình ⇒ flush_all (mặc-định an-toàn)."""
    U = ('U', 0)
    ra, stk, kc = [], [], {}
    def flush_all(): stk.clear(); kc.clear()
    def pop(): return stk.pop() if stk else U
    for nm, op in code:
        if nm in _CTRL_A:                                          # nhánh/join/dứt → vào không-rõ
            flush_all(); ra.append((nm, op)); continue
        if nm == "NẠP" and isinstance(op, int) and 0 <= op <= 255:
            stk.append(('K', op)); ra.append((nm, op)); continue
        if nm == "TẢI_Ô" and isinstance(op, int):
            if op in kc:
                c = kc[op]; stk.append(('K', c)); ra.append(("NẠP", c)); continue   # ★ propagation: TẢI_Ô ô-hằng → NẠP c
            stk.append(U); ra.append((nm, op)); continue
        if nm == "LƯU_Ô" and isinstance(op, int):
            v = pop()
            if v[0] == 'K': kc[op] = v[1]
            else: kc.pop(op, None)
            ra.append((nm, op)); continue
        if nm in _FOLD:                                            # nhị-phân `a OP b`: runtime b=pop, a=pop. Fold nếu cả 2 hằng & kết ∈[0,255].
            b = pop(); a = pop()                                   # b = đỉnh, a = dưới
            if a[0] == 'K' and b[0] == 'K':
                try: r = _FOLD[nm](a[1], b[1])
                except Exception: r = None
                stk.append(('K', r) if (isinstance(r, int) and 0 <= r <= 255) else U)
            else: stk.append(U)
            ra.append((nm, op)); continue
        if nm == "CỘNG_HẰNG" and isinstance(op, int):
            v = pop(); r = v[1] + op
            stk.append(('K', r) if (v[0] == 'K' and 0 <= r <= 255) else U); ra.append((nm, op)); continue
        if nm == "NHÂN_CỘNG_HẰNG" and isinstance(op, int):         # PEEK x (giữ), đẩy x+op
            top = stk[-1] if stk else U; r = top[1] + op
            stk.append(('K', r) if (top[0] == 'K' and 0 <= r <= 255) else U); ra.append((nm, op)); continue
        if nm in ("DỊCH_TRÁI", "DỊCH_PHẢI") and isinstance(op, int):
            v = pop()
            if v[0] == 'K':
                r = (v[1] << op) if nm == "DỊCH_TRÁI" else (v[1] >> op)
                stk.append(('K', r) if 0 <= r <= 255 else U)
            else: stk.append(U)
            ra.append((nm, op)); continue
        if nm == "DỊCH_CỘNG_BYTE":
            pop(); stk.append(U); ra.append((nm, op)); continue   # (x<<8)+k hầu như >255 → U
        if nm == "NHÂN_BẢN":
            stk.append(stk[-1] if stk else U); ra.append((nm, op)); continue
        if nm == "BỎ":
            pop(); ra.append((nm, op)); continue
        if nm == "ĐỔI":
            if len(stk) >= 2: stk[-1], stk[-2] = stk[-2], stk[-1]
            else: stk.clear()                                     # toán-hạng-2 dưới hậu-tố → mất dấu
            ra.append((nm, op)); continue
        if nm in ("ẨN", "TẢI_VẬT", "TẢI_TÂM", "TÁC_TỬ", "GIAO", "GIAO_CHUNG"):
            stk.append(U); ra.append((nm, op)); continue          # đẩy 1 trị KHÔNG-rõ (không ghi ram)
        if nm == "TẢI_GIÁN":
            pop(); stk.append(U); ra.append((nm, op)); continue   # ram[pop] → unknown; KHÔNG clobber
        if nm == "THAM_I":
            stk.append(U); ra.append((nm, op)); continue          # đọc ô-khung (chỉ-đọc, không ghi ram) → push U, GIỮ kc
        # mặc-định: LƯU_GIÁN/GHI_TRƯỜNG/GỌI*/HẸN_GIỜ/LƯU_THAM_I/DÀNH_CB + mọi lệnh lạ → clobber ram ⇒ flush ALL
        flush_all(); ra.append((nm, op))
    return ra

def tối_ưu_mã(code):
    # ★ PHA A — IR-lite abstract-interp (const-prop xuyên-lệnh). TẮT mặc-định: ĐO cho thấy NET-ÂM trên codebase này
    #   — propagation `TẢI_Ô r→NẠP c` cạnh-tranh & THUA siêu-lệnh #3 (phá 53 GHI_TRƯỜNG, +106 bytecode); cross-block const ≈0.
    #   Giữ pass (sound + 6 unit-test) làm HẠ-TẦNG: Pha B (inline) có thể PHƠI cơ-hội const-prop mới xuyên ranh-giới gọi ⇒ bật lại đo.
    ir = getattr(GiaoC, "BẬT_IR", False)
    trước = None
    while trước != code:                         # tới điểm-bất-động qua cả abstract-interp + peephole + DCE
        trước = code
        if ir: code = _abs_interp(code)          # propagation TRƯỚC ⇒ NẠP mới cho peephole/siêu-lệnh gập
        code = _dce(_peephole(code))
    if getattr(GiaoC, "BẬT_SIÊU_LỆNH", True):    # ★ siêu-lệnh CỘNG_HẰNG BẬT MẶC-ĐỊNH (−15.2% bước) — đúng 4-substrate
        code = _siêu_lệnh(code)                    #   (GVM-mềm/wasm/Verilog) sau 2 vá gvm.v: hazard context-switch + hợp-nhất preempt-granularity (timer theo LỆNH khớp software)
    return code

# ============================================================
# ★ PHA B — INLINE hàm-nhỏ tầng-AST (xoá overhead GỌI_N/TRẢ_VỀ_N; phơi const-prop)
#   SOUND nhờ 4 điều-kiện: (1) thân ĐÚNG `trả_về <expr>` 1-biểu-thức · (2) KHÔNG đệ-quy ·
#   (3) đối toàn ATOM (thuần, không side-effect, re-eval cùng-trị, sao-chép rẻ — an-toàn dù param dùng 0/n lần) ·
#   (4) mọi VarRef ĐỌC-GIÁ-TRỊ trong thân ∈ params (callee-gọi được phép) ⇒ KHÔNG name-capture khi nhúng vào khung khác.
# ============================================================
def _con_node(n):
    for v in vars(n).values():
        if isinstance(v, Node): yield v
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, Node): yield x

def _atom_thuần(n): return type(n) in (Num, Str, AnLit, TruthLit, VarRef)   # đối inline cho phép

def _kích_thước(n): return 1 + sum(_kích_thước(c) for c in _con_node(n))

def _đếm_gọi(n, tên):
    c = 1 if (type(n) is Goi and type(n.callee) is VarRef and n.callee.name == tên) else 0
    return c + sum(_đếm_gọi(c2, tên) for c2 in _con_node(n))

def _val_names_ok(n, params):
    "MỌI VarRef đọc-giá-trị (KHÔNG phải callee của Goi) phải ∈ params ⇒ chống name-capture."
    if type(n) is Goi:
        ok = True if type(n.callee) is VarRef else _val_names_ok(n.callee, params)
        return ok and all(_val_names_ok(a, params) for a in n.args)
    if type(n) is VarRef: return n.name in params
    return all(_val_names_ok(c, params) for c in _con_node(n))

def _copy_subst(n, env):
    "Bản-sao SÂU của n, thay VarRef(param) → bản-sao ĐỐI tương-ứng."
    if type(n) is VarRef and n.name in env: return copy.deepcopy(env[n.name])
    m = copy.copy(n)
    for k, v in list(vars(m).items()):
        if isinstance(v, Node): setattr(m, k, _copy_subst(v, env))
        elif isinstance(v, list):
            setattr(m, k, [_copy_subst(x, env) if isinstance(x, Node) else x for x in v])
    return m

def _hàm_inline_được(hams, ngưỡng=14):
    inl = {}
    for h in hams:
        if len(h.body) != 1 or type(h.body[0]) is not Tra: continue       # đúng 1 lệnh `trả_về <expr>`
        expr = h.body[0].expr
        if expr is None: continue
        if _đếm_gọi(expr, h.name) > 0: continue                            # đệ-quy → BỎ
        if not _val_names_ok(expr, set(h.params)): continue                # đọc biến NGOÀI params → BỎ (capture)
        if _kích_thước(expr) > ngưỡng: continue                            # ngưỡng nhỏ → tránh phình ROM
        inl[h.name] = (list(h.params), copy.deepcopy(expr))                # đông-cứng: miễn-nhiễm mutate khi inline
    return inl

def _inline_1(n, inl):
    "Inline đệ-quy mọi lời gọi inlinable trong cây n (con trước). Trả (node-mới, số-thay)."
    đếm = 0
    for k, v in list(vars(n).items()):
        if isinstance(v, Node):
            nv, d = _inline_1(v, inl); setattr(n, k, nv); đếm += d
        elif isinstance(v, list):
            for i, x in enumerate(v):
                if isinstance(x, Node):
                    nx, d = _inline_1(x, inl); v[i] = nx; đếm += d
    if type(n) is Goi and type(n.callee) is VarRef and n.callee.name in inl:
        params, expr = inl[n.callee.name]
        if len(n.args) == len(params) and all(_atom_thuần(a) for a in n.args):
            return _copy_subst(expr, dict(zip(params, n.args))), đếm + 1
    return n, đếm

def inline_ast(ast, inl, vòng=6):
    "Áp inline tới điểm-bất-động (≤ vòng lượt — bắt cả lồng-nhau qua đối-atom). Trả tổng số-thay."
    tổng = 0
    for _ in range(vòng):
        đếm = 0
        for i, s in enumerate(ast):
            ast[i], d = _inline_1(s, inl); đếm += d
        tổng += đếm
        if đếm == 0: break
    return tổng

def compile_program(ast, tagged=None):
    # ★ PHA B — inline hàm-nhỏ. TẮT mặc-định: ĐO cho thấy NET-ÂM trên codebase này — chỉ 5 hàm/11 call-site đủ-tư-cách
    #   (1-biểu-thức + đối-atom), bước −0.18% nhưng bytecode +3.09% (phình ROM). 814 gọi-động là hàm đa-lệnh/có-vòng KHÔNG
    #   đủ-tư-cách inline-an-toàn. Synergy inline+A cũng ÂM (−0.02%/+4.17%). Giữ pass (sound + byte-exact 14/14/55/55/63/63) làm hạ-tầng.
    if getattr(GiaoC, "BẬT_INLINE", False):
        inline_ast(ast, _hàm_inline_được([s for s in ast if type(s) is HamDef]))
    has_map = uses_map(ast)
    if tagged is None: tagged = uses_tag(ast) or has_map   # bản cần __bằng (so khoá cấu trúc) ⇒ bật thẻ
    c = GiaoC(tagged=tagged)
    c.emit_const(HEAP_BASE); c.emit("LƯU_Ô", HEAP_PTR_CELL)   # khởi tạo đỉnh heap
    c.intern_strings(ast)                                     # dựng sẵn chuỗi-hằng lặp (tối ưu map khoá-chuỗi)
    hams = [s for s in ast if type(s) is HamDef]
    rest = [s for s in ast if type(s) is not HamDef]
    for h in hams: c.fn_labels[h.name] = "@fn_" + h.name      # khai báo trước → đệ quy/đệ quy chéo
    c.emit_jump("@main")                                     # nhảy qua hàm trợ giúp + hàm người dùng
    c.emit_helpers()                                         # __dài, __lấy, __ghép (phát 1 lần)
    if c.tagged: c.emit_helpers2()                           # __bằng, __cộng, __chuỗi_hoá, __num2str (chỉ chế độ thẻ)
    if has_map: c.emit_helpers3()                            # __map_* (bản — cần __bằng nên sau helpers2)
    for h in hams:
        c.mark("@fn_" + h.name)
        params = list(h.params)
        locs = [n for n in c.collect_locals(h.body) if n not in params]
        c.frame_names = params + locs                        # KHUNG = [tham số…, biến cục bộ…]
        if locs: c.emit("DÀNH_CB", len(locs))                # prologue: dành ô cục bộ per-call
        c.block(h.body)
        c.emit("ẨN"); c.emit("TRẢ_VỀ_N")                     # chốt cuối: rơi khỏi thân → trả ẩn
        c.frame_names = []
    c.mark("@main")
    c.block(rest)
    return c.assemble()

def compile_source(src):
    return compile_program(Parser(tokenize(src)).parse())

def uses_float(ast):
    "Chương trình có SỐ THỰC không? ⟺ có hằng Num là float (≠ nguyên). Buộc GVM 32-bit."
    found = [False]
    def walk(n):
        if found[0] or n is None: return
        if type(n) is Num and isinstance(n.v, float):
            found[0] = True; return
        for v in getattr(n, "__dict__", {}).values():
            if isinstance(v, list):
                for x in v:
                    if hasattr(x, "__dict__"): walk(x)
            elif hasattr(v, "__dict__"): walk(v)
    for s in ast: walk(s)
    return found[0]

def compile_source_bit(src):
    "Trả (words, bit): bit=32 nếu dùng thẻ (là_số/là_ds/bản) HOẶC số thực (điểm-cố-định ×10000)."
    ast = Parser(tokenize(src)).parse()
    tagged = uses_tag(ast) or uses_map(ast)
    bit = WORD_BIT if (tagged or uses_float(ast)) else 16     # số thực cần 32-bit (×10000)
    return compile_program(ast, tagged), bit

def main():
    if len(sys.argv) < 2:
        print("Dùng: python giaoc.py <tệp.giao>"); sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f: src = f.read()
    try:
        words, bit = compile_source_bit(src)                  # 32-bit chỉ khi cần thẻ; còn lại 16-bit (như cũ)
    except ValueError as e:
        print(f"[GIAOC — RANH GIỚI] {e}", file=sys.stderr)
        print("   (đây là LÕI MÁY của GIAO; tính năng đầy đủ chạy bằng: python giao.py <tệp>)", file=sys.stderr)
        sys.exit(2)
    print("="*62); print(f"BIÊN DỊCH {sys.argv[1]} → BYTECODE GVM  ({bit}-bit{' · THẺ' if bit==WORD_BIT else ''})"); print("="*62)
    for i, w in enumerate(words): print(f"  {i:02d}:  {disasm_word(w)}")
    print("\n" + "="*62)
    print("CHẠY bytecode trên MÁY GVM (trit/γ, nền NAND) — Python chỉ là CPU")
    print("="*62)
    GVM(words, world={}, bit=bit).run()
    print("\n   → GIAO đã chạy KHÔNG qua trình thông dịch Python. Ngữ nghĩa nằm trong bytecode.")

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
GIAOC64 — BIÊN DỊCH GIAO → BYTECODE GVM-64 (máy tính toán của GIAO, chạy trên WASM/WASI)
==========================================================================================
    python giaoc64.py tệp.giao [-o tệp.g64]
    wasmtime run wasm/gvm64.wasm -- [--bước N] [--trần-ds N] [--cho-giờ] < tệp.g64
    (dự phòng) node --permission … --allow-wasi wasm/giao64.mjs tệp.g64 [cờ…]

Trình biên dịch chạy LÚC DỰNG (build); CHƯƠNG TRÌNH thì chạy trên gvm64.wasm — không Python.
Ngữ nghĩa BÁM trình thông dịch giao.py (chuẩn đối chiếu: kiem_gvm64.py so đầu ra từng ký tự):
  · thư viện chuẩn chuẩn.giao được biên dịch trước (như nạp_chuẩn);
  · `nhập` gộp mô-đun lúc biên dịch (một lần, trong cây thư mục của tệp chính, như giao.py);
  · tên: cục bộ → hàm bao ngoài (từ vựng) → toàn cục, BỎ QUA ô chưa gán (như tra cứu động);
  · `đặt` trong hàm luôn tạo biến cục bộ (như cur_define).
Chưa hỗ trợ (báo lỗi rõ khi biên dịch): tầng CDFL vật/tâm/học/giao/trôi/khi viên_mãn/de.
"""
import os, sys, struct
from giao import (tokenize, Parser, Num, Str, AnLit, TruthLit, ListLit, FieldRef, VarRef, DeQuery, Bin,
                  Unary, Index, Goi, Decl, Dat, DatIndex, Hoc, Giao, Roi, Lap, LapTrong, Mai, Dung,
                  TroiReg, TroiTick, Neu, KhiVienMan, HamDef, Lam, Tra, ThuBat, ExprStmt, Nhap, SANG)

P = os.path.dirname(os.path.abspath(__file__))

OP = {"DỪNG": 0, "HẰNG_NGUYÊN": 1, "SỐ_NHỎ": 2, "HẰNG_THỰC": 3, "HẰNG_CHUỖI": 4, "ẨN": 5, "TẢI": 6,
      "GHI_CB": 7, "GHI_TC": 8, "BỎ": 9, "NHÂN_BẢN": 10,
      "+": 11, "-": 12, "*": 13, "/": 14, "//": 15, "==": 16, "!=": 17, "<": 18, ">": 19, "<=": 20, ">=": 21,
      "ĐỐI": 22, "CHỈ_MỤC": 23, "GÁN_CHỈ_MỤC": 24, "NHẢY": 25, "RẼ_BA": 26, "GỌI": 27, "TRẢ_VỀ": 28,
      "TRẢ_ẨN": 29, "BAO_ĐÓNG": 30, "RỌI": 31, "DANH_SÁCH": 32, "DUYỆT_ĐẦU": 33, "DUYỆT_TIẾP": 34,
      "ĐẾM_ĐẦU": 35, "ĐẾM_TIẾP": 36, "THỬ": 37, "HẾT_THỬ": 38, "NÉM": 39, "HẰNG_LỚN": 40}

# Builtin của GVM-64 (mã phải KHỚP switch trong wasm/gvm64.ts). Tên không dấu là bí danh như giao.py.
BUILTIN = {}
for id_, names in [
    (0, "dài dai"), (1, "đầu dau"), (2, "đuôi duoi"), (3, "thêm them"), (4, "ghép ghep"), (5, "gom"),
    (6, "đảo dao"), (7, "nối noi"), (8, "tách tach"), (9, "là_ds la_ds"), (10, "là_số la_so"),
    (11, "rọi_ds roi_ds"), (12, "loại loai"), (13, "nguyên nguyen"), (14, "mã ma"), (15, "ký_tự ky_tu"),
    (16, "xor"), (17, "và_bit va_bit"), (18, "hoặc_bit hoac_bit"), (19, "đảo_bit dao_bit"),
    (20, "dịch_trái dich_trai"), (21, "dịch_phải dich_phai"), (22, "log"), (23, "mũ mu"), (24, "căn can"),
    (25, "bản ban"), (26, "đặt_khoá dat_khoa"), (27, "lấy_khoá lay_khoa"), (28, "có_khoá co_khoa"),
    (29, "xoá_khoá xoa_khoa"), (30, "khoá khoa"), (31, "giá_trị gia_tri"), (32, "tạo_tri tao_tri"),
    (33, "γ_của gamma_cua"), (34, "giờ_hệ"),
    (35, "cộng_hưởng cong_huong"), (36, "cộng_hưởng_thô cong_huong_tho"), (37, "γ_kỹ_năng gamma_ky_nang"),
    (38, "cam_kết cam_ket"), (39, "bỏ_dấu bo_dau"), (60, "tim"), (61, "nhúng nhung"), (62, "nhịp_tim nhip_tim"),
    (40, "mảng_sẵn mang_san"), (41, "mảng_không mang_khong"), (42, "mảng_từ mang_tu"), (43, "m_dài"),
    (44, "m_lấy"), (45, "m_gán"), (46, "m_sao"), (47, "m_sang_ds"), (48, "m_chọn"), (49, "m_đặt_chọn"),
    (50, "m_tổ_hợp"), (51, "m_nhân_số"), (52, "m_biến_đổi_cặp"), (53, "m_nhân_chọn"), (54, "m_đổi_chọn"),
    (55, "m_tổng_mô2_chọn"), (56, "m_tổng_mô2"), (57, "m_mô2_ds"), (58, "m_tích_trong"), (59, "m_rút"),
    (63, "m_biến_đổi_bốn"), (64, "ngẫu_hệ ngau_he")]:
    for nm in names.split(): BUILTIN[nm] = id_

class LỗiBiênDịch(Exception): pass

class Phạm_vi:
    "Phạm vi một HÀM: tên → ô trong khung (tham số trước, rồi biến cục bộ, rồi ô ẩn cho vòng lặp)."
    def __init__(self, cha, tham_số, cục_bộ):
        self.cha = cha; self.tên = {}
        for n in list(tham_số) + [x for x in cục_bộ if x not in tham_số]: self.tên[n] = len(self.tên)
        self.số_ô = len(self.tên)
    def ô_ẩn(self, k=1):
        s = self.số_ô; self.số_ô += k; return s

def gom_cục_bộ(stmts):
    "Tên được TẠO trong thân hàm (đặt / biến lặp / tên bắt / hàm lồng) — không chui vào hàm/lam lồng."
    tên = []
    def add(n):
        if n not in tên: tên.append(n)
    def walk(ss):
        for s in ss:
            t = type(s)
            if t is Dat: add(s.name)
            elif t is HamDef: add(s.name)
            elif t is LapTrong: add(s.var); walk(s.body)
            elif t in (Lap, Mai): walk(s.body)
            elif t is Neu:
                walk(s.then)
                if s.ngo: walk(s.ngo)
                if s.khac: walk(s.khac)
            elif t is ThuBat:
                walk(s.thu)
                if s.tên: add(s.tên)
                walk(s.bat)
    walk(stmts); return tên

class GiaoC64:
    def __init__(self, base_dir):
        self.base_dir = os.path.realpath(base_dir)
        self.mã = []                         # int | ("J", op, nhãn) | ("W", nhãn) | ("L", nhãn)
        self.ints, self.ints_i = [], {}
        self.floats, self.floats_i = [], {}
        self.strs, self.strs_i = [], {}
        self.hàm = []                        # [vào(nhãn), số_tham, số_ô, tên_i, repr_i]
        self.chờ = []                        # hàm chờ biên dịch: (chỉ_số, nút, phạm_vi_cha)
        self.tc = {}                         # tên toàn cục → ô
        self.chuỗi_tên, self.chuỗi_tên_i, self.mục = [], {}, []
        self.pv = None                       # phạm vi hàm hiện hành (None = toàn cục)
        self.lc = 0
        self.vòng = []                       # [(nhãn_thoát, độ_sâu_thử)]
        self.thử = 0                         # số vùng 'thử' đang mở trong HÀM hiện hành
        self.đã_nhập = set(); self.đang_nhập = []; self.thư_mục = [self.base_dir]
        self.tên_người_dùng = set()          # để quyết bẫy 'thêm bị vứt'
        for nm, id_ in BUILTIN.items(): self.ô_tc(nm)

    # ---------------- tiện ích ----------------
    def nhãn(self): self.lc += 1; return f"L{self.lc}"
    def e(self, op, arg=0):
        if not (-(1 << 23) <= arg < (1 << 24)): raise LỗiBiênDịch(f"toán hạng {arg} vượt 24 bit")
        self.mã.append(((arg & 0xFFFFFF) << 8) | OP[op])
    def ej(self, op, lbl): self.mã.append(("J", OP[op], lbl))
    def ew(self, lbl): self.mã.append(("W", lbl))
    def đặt_nhãn(self, lbl): self.mã.append(("L", lbl))
    def ô_tc(self, tên):
        if tên not in self.tc: self.tc[tên] = len(self.tc)
        return self.tc[tên]
    def chuỗi(self, s):
        if s not in self.strs_i: self.strs_i[s] = len(self.strs); self.strs.append(s)
        return self.strs_i[s]
    def hằng_int(self, v):
        if -(1 << 23) <= v < (1 << 23): self.e("SỐ_NHỎ", v); return
        if not (-(1 << 63) <= v < (1 << 63)):              # SỐ LỚN tuỳ ý: gửi dạng thập phân
            self.e("HẰNG_LỚN", self.chuỗi(str(v))); return
        if v not in self.ints_i: self.ints_i[v] = len(self.ints); self.ints.append(v)
        self.e("HẰNG_NGUYÊN", self.ints_i[v])
    def hằng_thực(self, x):
        k = struct.pack("<d", x)
        if k not in self.floats_i: self.floats_i[k] = len(self.floats); self.floats.append(x)
        self.e("HẰNG_THỰC", self.floats_i[k])
    def ô_ẩn(self, k=1):
        "Ô ẩn cho trạng thái vòng lặp: trong hàm = ô khung; ở toàn cục = ô toàn cục (bit 23)."
        if self.pv is not None: return self.pv.ô_ẩn(k)
        self.lc += 1; s = self.ô_tc(f"__ẩn{self.lc}")
        for i in range(1, k): self.ô_tc(f"__ẩn{self.lc}_{i}")
        return s | 0x800000

    # ---------------- tên ----------------
    def tải(self, tên):
        chuỗi = []; pv = self.pv; sâu = 0
        while pv is not None:
            if tên in pv.tên: chuỗi.append((0, sâu, pv.tên[tên]))
            pv = pv.cha; sâu += 1
        chuỗi.append((1, 0, self.ô_tc(tên)))
        khoá = (tên, tuple(chuỗi))
        if khoá not in self.chuỗi_tên_i:
            self.chuỗi_tên_i[khoá] = len(self.chuỗi_tên)
            self.chuỗi_tên.append((len(self.mục), len(chuỗi), self.chuỗi(tên)))
            for x in chuỗi: self.mục.extend(x)
        self.e("TẢI", self.chuỗi_tên_i[khoá])
    def ghi(self, tên):                                   # cur_define: cục bộ trong hàm, toàn cục ở ngoài
        if self.pv is not None:
            if tên not in self.pv.tên: self.pv.tên[tên] = self.pv.ô_ẩn()
            self.e("GHI_CB", self.pv.tên[tên])
        else:
            self.e("GHI_TC", self.ô_tc(tên))

    # ---------------- biểu thức ----------------
    def expr(self, n):
        t = type(n)
        if t is Num:
            if isinstance(n.v, float): self.hằng_thực(n.v)
            else: self.hằng_int(int(n.v))
        elif t is Str: self.e("HẰNG_CHUỖI", self.chuỗi(n.v))
        elif t is AnLit: self.e("ẨN")
        elif t is TruthLit: self.e("HẰNG_CHUỖI", self.chuỗi("sáng" if n.t == SANG else "tối"))
        elif t is ListLit:
            for x in n.elems: self.expr(x)
            self.e("DANH_SÁCH", len(n.elems))
        elif t is VarRef: self.tải(n.name)
        elif t is Bin:
            self.expr(n.l); self.expr(n.r)
            if n.op not in OP: raise LỗiBiênDịch(f"phép '{n.op}' chưa hỗ trợ")
            self.e(n.op)
        elif t is Unary: self.expr(n.e); self.e("ĐỐI")
        elif t is Index: self.expr(n.coll); self.expr(n.idx); self.e("CHỈ_MỤC")
        elif t is Goi:
            self.expr(n.callee)
            for a in n.args: self.expr(a)
            self.e("GỌI", len(n.args))
        elif t is Lam: self.e("BAO_ĐÓNG", self.hàm_mới("λ", n.params, n.body))
        elif t in (FieldRef, DeQuery):
            raise LỗiBiênDịch("tầng CDFL (tâm/vật/de) chưa có trên GVM-64 — chạy bằng giao.py")
        else: raise LỗiBiênDịch(f"biểu thức {t.__name__} chưa hỗ trợ")

    def hàm_mới(self, tên, params, body):
        chỉ = len(self.hàm)
        repr_ = f"<hàm {tên}({', '.join(params)})>"
        self.hàm.append([None, len(params), 0, self.chuỗi(tên), self.chuỗi(repr_)])
        self.chờ.append((chỉ, tên, list(params), body, self.pv))
        return chỉ

    # ---------------- câu lệnh ----------------
    def block(self, ss):
        for s in ss: self.stmt(s)
    def stmt(self, s):
        t = type(s)
        if t is Dat: self.expr(s.expr); self.ghi(s.name)
        elif t is DatIndex:
            self.tải(s.name)
            for k in s.idxs[:-1]: self.expr(k); self.e("CHỈ_MỤC")
            self.expr(s.idxs[-1]); self.expr(s.expr); self.e("GÁN_CHỈ_MỤC")
        elif t is ExprStmt:
            e_ = s.expr
            if (type(e_) is Goi and type(e_.callee) is VarRef and e_.callee.name in ("thêm", "them")
                    and e_.callee.name not in self.tên_người_dùng):
                self.e("NÉM", self.chuỗi("kết quả của 'thêm' bị VỨT — 'thêm' KHÔNG sửa danh sách tại chỗ, câu lệnh "
                                        "này không đổi gì cả. Chèn tại chỗ: gom(ds, x) · giữ bản mới: đặt ds = thêm(ds, x)"))
                return
            self.expr(e_); self.e("BỎ")
        elif t is Roi: self.expr(s.expr); self.e("RỌI")
        elif t is Neu:
            L_ngờ, L_khác, L_hết = self.nhãn(), self.nhãn(), self.nhãn()
            self.expr(s.cond)
            self.mã.append(("J", OP["RẼ_BA"], L_ngờ if s.ngo is not None else L_khác)); self.ew(L_khác)
            self.block(s.then); self.ej("NHẢY", L_hết)
            if s.ngo is not None: self.đặt_nhãn(L_ngờ); self.block(s.ngo); self.ej("NHẢY", L_hết)
            self.đặt_nhãn(L_khác)
            if s.khac is not None: self.block(s.khac)
            self.đặt_nhãn(L_hết)
        elif t is Lap:
            ô = self.ô_ẩn(); L0, L1 = self.nhãn(), self.nhãn()
            self.expr(s.count); self.e("ĐẾM_ĐẦU", ô)
            self.đặt_nhãn(L0); self.e("ĐẾM_TIẾP", ô); self.ew(L1)
            self.vòng.append((L1, self.thử)); self.block(s.body); self.vòng.pop()
            self.ej("NHẢY", L0); self.đặt_nhãn(L1)
        elif t is LapTrong:
            ô = self.ô_ẩn(2); L0, L1 = self.nhãn(), self.nhãn()
            self.expr(s.iterable); self.e("DUYỆT_ĐẦU", ô)
            self.đặt_nhãn(L0); self.e("DUYỆT_TIẾP", ô); self.ew(L1)
            self.ghi(s.var)
            self.vòng.append((L1, self.thử)); self.block(s.body); self.vòng.pop()
            self.ej("NHẢY", L0); self.đặt_nhãn(L1)
        elif t is Mai:
            L0, L1 = self.nhãn(), self.nhãn()
            self.đặt_nhãn(L0)
            self.vòng.append((L1, self.thử)); self.block(s.body); self.vòng.pop()
            self.ej("NHẢY", L0); self.đặt_nhãn(L1)
        elif t is Dung:
            if not self.vòng: raise LỗiBiênDịch("'dừng' nằm ngoài vòng lặp")
            L1, sâu = self.vòng[-1]
            for _ in range(self.thử - sâu): self.e("HẾT_THỬ")      # rời vùng 'thử' đang mở
            self.ej("NHẢY", L1)
        elif t is Tra:
            if self.pv is None: raise LỗiBiênDịch("'trả' nằm ngoài hàm")
            self.expr(s.expr)
            for _ in range(self.thử): self.e("HẾT_THỬ")
            self.e("TRẢ_VỀ")
        elif t is HamDef:
            self.e("BAO_ĐÓNG", self.hàm_mới(s.name, s.params, s.body)); self.ghi(s.name)
        elif t is ThuBat:
            L_bắt, L_hết = self.nhãn(), self.nhãn()
            self.ej("THỬ", L_bắt); self.thử += 1
            self.block(s.thu)
            self.thử -= 1; self.e("HẾT_THỬ"); self.ej("NHẢY", L_hết)
            self.đặt_nhãn(L_bắt)
            if s.tên is not None: self.ghi(s.tên)
            else: self.e("BỎ")
            self.block(s.bat)
            self.đặt_nhãn(L_hết)
        elif t is Nhap: self.nhập(s.path)
        elif t in (Decl, Hoc, Giao, TroiReg, TroiTick, KhiVienMan):
            raise LỗiBiênDịch("tầng CDFL (vật/tâm/học/giao/trôi/khi viên_mãn) chưa có trên GVM-64 — chạy bằng giao.py")
        else: raise LỗiBiênDịch(f"câu lệnh {t.__name__} chưa hỗ trợ")

    def nhập(self, path):
        real = os.path.realpath(os.path.join(self.thư_mục[-1], path))
        if not real.endswith(".giao"): raise LỗiBiênDịch(f"nhập chỉ nạp tệp .giao: '{path}'")
        if not (real == self.base_dir or real.startswith(self.base_dir + os.sep)):
            raise LỗiBiênDịch(f"nhập '{path}' NGOÀI cây thư mục dự án")
        if real in self.đã_nhập: return
        if real in self.đang_nhập: raise LỗiBiênDịch(f"nhập VÒNG (circular): '{path}'")
        with open(real, encoding="utf-8") as f: ast = Parser(tokenize(f.read())).parse()
        self.đã_nhập.add(real); self.đang_nhập.append(real); self.thư_mục.append(os.path.dirname(real))
        pv, vòng, thử = self.pv, self.vòng, self.thử
        self.pv, self.vòng, self.thử = None, [], 0            # mô-đun chạy ở phạm vi TOÀN CỤC
        try:
            self.đánh_dấu_tên(ast); self.block(ast)
        finally:
            self.pv, self.vòng, self.thử = pv, vòng, thử
            self.đang_nhập.pop(); self.thư_mục.pop()

    def đánh_dấu_tên(self, ast):
        for s in ast:
            if type(s) is HamDef: self.tên_người_dùng.add(s.name)

    # ---------------- chương trình ----------------
    def biên_dịch(self, ast_chuẩn, ast):
        self.đánh_dấu_tên(ast_chuẩn); self.đánh_dấu_tên(ast)
        for d in (ast_chuẩn, ast):
            for s in d:
                if type(s) is Nhap: pass
        self.block(ast_chuẩn); self.block(ast)
        self.e("DỪNG")
        while self.chờ:                                       # biên dịch thân hàm (kể cả lồng nhau)
            chỉ, tên, params, body, pv_cha = self.chờ.pop(0)
            L = f"F{chỉ}"; self.hàm[chỉ][0] = L
            self.đặt_nhãn(L)
            pv0, vòng0, thử0 = self.pv, self.vòng, self.thử
            self.pv = Phạm_vi(pv_cha, params, gom_cục_bộ(body)); self.vòng = []; self.thử = 0
            self.block(body)
            self.e("TRẢ_ẨN")
            self.hàm[chỉ][2] = self.pv.số_ô
            self.pv, self.vòng, self.thử = pv0, vòng0, thử0
        return self.lắp()

    def lắp(self):
        địa_chỉ, nhãn = 0, {}
        for x in self.mã:
            if isinstance(x, tuple) and x[0] == "L": nhãn[x[1]] = địa_chỉ
            else: địa_chỉ += 1
        từ = []
        for x in self.mã:
            if isinstance(x, int): w = x
            elif x[0] == "L": continue
            elif x[0] == "J": w = ((nhãn[x[2]] & 0xFFFFFF) << 8) | x[1]
            else: w = nhãn[x[1]]
            từ.append(w - (1 << 32) if w >= (1 << 31) else w)
        for h in self.hàm: h[0] = nhãn[h[0]]
        return từ

    def nhị_phân(self, từ):
        b = bytearray(b"G64\x01")
        u = lambda x: b.extend(struct.pack("<I", x & 0xFFFFFFFF))
        u(len(từ)); [u(w) for w in từ]
        u(len(self.ints)); [b.extend(struct.pack("<q", v)) for v in self.ints]
        u(len(self.floats)); [b.extend(struct.pack("<d", v)) for v in self.floats]
        u(len(self.strs))
        for s in self.strs: u(len(s)); [u(ord(ch)) for ch in s]
        u(len(self.hàm)); [[u(x) for x in h] for h in self.hàm]
        u(len(self.chuỗi_tên)); [[u(x) for x in c] for c in self.chuỗi_tên]
        u(len(self.mục)); [u(x) for x in self.mục]
        u(len(self.tc))
        dựng = [(self.tc[nm], id_) for nm, id_ in BUILTIN.items()]
        u(len(dựng)); [(u(g), u(i)) for g, i in dựng]
        return bytes(b)

def biên_dịch_tệp(đường_dẫn):
    "Trả (bytes .g64). Thư viện chuẩn chuẩn.giao luôn được biên dịch trước, như giao.py."
    with open(đường_dẫn, encoding="utf-8") as f: ast = Parser(tokenize(f.read())).parse()
    with open(os.path.join(P, "chuẩn.giao"), encoding="utf-8") as f: ast_chuẩn = Parser(tokenize(f.read())).parse()
    c = GiaoC64(os.path.dirname(os.path.abspath(đường_dẫn)))
    return c.nhị_phân(c.biên_dịch(ast_chuẩn, ast))

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(2)
    vào = a[0]; ra = a[a.index("-o") + 1] if "-o" in a else os.path.splitext(vào)[0] + ".g64"
    try:
        dữ_liệu = biên_dịch_tệp(vào)
    except LỗiBiênDịch as e:
        print(f"[GIAOC64] {e}", file=sys.stderr); sys.exit(1)
    with open(ra, "wb") as f: f.write(dữ_liệu)
    try: print(f"{vào} → {ra} ({len(dữ_liệu):,} byte)")
    except UnicodeEncodeError: print(f"{vào!a} -> {ra!a} ({len(dữ_liệu)} byte)")   # bàn điều khiển cp1252

if __name__ == "__main__":
    main()

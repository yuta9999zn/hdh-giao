# -*- coding: utf-8 -*-
"""
GIAO — Ngôn ngữ lập trình của Vùng Giao Thoa   (bản v0.2 — chuẩn bị tự thân hoá)
================================================================================
Tác giả học thuyết nền: Nguyễn Trường An (DFCT / NNL-NTHT / CDFL)

v0.2 thêm những gì TỰ THÂN HOÁ cần: hàm, đệ quy, biến (đặt), danh sách [...],
lập chỉ mục, và builtins thao tác danh sách/chuỗi. Nhờ đó có thể viết một trình
diễn giải GIAO BẰNG CHÍNH GIAO (xem giao_core.giao).

Đơn vị nền vẫn là BỘ BA CÓ CỘNG HƯỞNG (sáng/tối/ẩn), không phải bit nhị phân.
Trình thông dịch này là 'mồi' bằng Python; mục tiêu cuối là cắt bỏ nó qua tự thân hoá.
"""
import sys, os, difflib, io, contextlib, math as _math   # `subprocess` nạp LƯỜI trong builtin `chạy` (để giao.py chạy được cả trong Pyodide/trình duyệt)

# ============================================================
# 0. GIÁ TRỊ NỀN — bộ ba cộng hưởng thay cho bit nhị phân
# ============================================================
class An:
    _inst = None
    def __new__(cls):
        if cls._inst is None: cls._inst = super().__new__(cls)
        return cls._inst
    def __repr__(self): return "ẩn"
AN = An()

SANG = "sáng"   # γ > 0
TOI  = "tối"    # γ < 0

class Tri:
    "Tri thức OR: nội dung + γ + trạng thái."
    def __init__(self, value, gamma, state):
        self.value, self.gamma, self.state = value, gamma, state
    def __repr__(self):
        if self.state == "ẩn": return "tri(ẩn — chưa giao thoa, γ=∅)"
        v = self.value
        vs = f"{v:.4g}" if isinstance(v, float) else repr(v)
        return f"tri({vs}, γ={self.gamma:+.2f}, {self.state})"

def truthy3(v):
    if v is AN: return AN
    if isinstance(v, str) and v in (SANG, TOI): return v
    if isinstance(v, Tri): return AN if v.state == "ẩn" else (SANG if v.gamma > 0 else TOI)
    if isinstance(v, bool): return SANG if v else TOI
    if isinstance(v, (int, float)): return SANG if v != 0 else TOI
    if isinstance(v, list): return SANG if len(v) > 0 else TOI
    if isinstance(v, Ban): return SANG if len(v.d) > 0 else TOI
    return SANG if v else TOI

class Env:
    "Môi trường TỪ VỰNG (lexical): biến cục bộ + con trỏ tới scope CHA (nơi định nghĩa)."
    __slots__ = ("vars", "parent")
    def __init__(self, parent): self.vars = {}; self.parent = parent

class Closure:
    "Giá trị hàm — công dân hạng nhất. Bắt MÔI TRƯỜNG định nghĩa (lexical closure)."
    def __init__(self, name, params, body, env=None):
        self.name, self.params, self.body, self.env = name, params, body, env
    def __repr__(self): return f"<hàm {self.name}({', '.join(self.params)})>"

class Ban:
    "BẢN (map/record) — kiểu THAM CHIẾU, mutable; tra cứu O(1). Khoá: số/chuỗi/trị/ẩn."
    def __init__(self): self.d = {}
    def __repr__(self): return "{" + ", ".join(f"{k!r}: {v!r}" for k,v in self.d.items()) + "}"

class ReturnSignal(Exception):
    def __init__(self, value): self.value = value
class DungSignal(Exception):
    "Thoát vòng lặp (mãi/lặp) — 'dừng'. Không vượt qua biên hàm."

class GiaoError(Exception):
    "Lỗi runtime GIAO — CÓ THỂ bắt bằng thử/bắt. Mang số DÒNG + CỘT."
    def __init__(self, msg, line=None, col=None): self.msg = msg; self.line = line; self.col = col
class GiaoLimit(Exception):
    "Vượt giới hạn tài nguyên (bước/đệ quy/bộ nhớ) — KHÔNG bắt được, để chống treo/DoS."
    def __init__(self, msg): self.msg = msg
class GiaoSyntax(SyntaxError):
    "Lỗi cú pháp GIAO — mang dòng+cột (kế thừa SyntaxError để mã cũ vẫn bắt được)."
    def __init__(self, msg, line=None, col=None):
        super().__init__(msg); self.msg = msg; self.line = line; self.col = col

# ============================================================
# 1. TOKENIZER
# ============================================================
KEYWORDS = {
    "vật":"vật","vat":"vật", "tâm":"tâm","tam":"tâm", "giao":"giao",
    "học":"học","hoc":"học", "rọi":"rọi","roi":"rọi", "lặp":"lặp","lap":"lặp",
    "nếu":"nếu","neu":"nếu", "ngờ":"ngờ","ngo":"ngờ", "khác":"khác","khac":"khác",
    "khi":"khi", "viên_mãn":"viên_mãn","vien_man":"viên_mãn",
    "ẩn":"ẩn","an":"ẩn", "sáng":"sáng","sang":"sáng", "tối":"tối","toi":"tối", "de":"de",
    # v0.2
    "hàm":"hàm","ham":"hàm", "trả":"trả","tra":"trả", "đặt":"đặt","dat":"đặt",
    "thử":"thử","thu":"thử", "bắt":"bắt","bat":"bắt",
    # v0.3 — vòng liên tục thật + thế giới tự trôi
    "mãi":"mãi","mai":"mãi", "dừng":"dừng","dung":"dừng", "trôi":"trôi","troi":"trôi",
    "nhập":"nhập","nhap":"nhập",
}
PUNCT = ["==", ">=", "<=", "!=", "⋈", "~", "=", "+", "-", "*", "//", "/", ">", "<",
         "(", ")", "{", "}", "[", "]", ","]

class Tok:
    def __init__(self, kind, val, line, col=0): self.kind, self.val, self.line, self.col = kind, val, line, col
    def __repr__(self): return f"<{self.kind}:{self.val!r}>"

def is_ident_start(c): return c.isalpha() or c == "_"
def is_ident_part(c):  return c.isalnum() or c == "_"

def tokenize(src):
    toks, i, line, n = [], 0, 1, len(src)
    line_start = 0                                  # chỉ số bắt đầu dòng hiện tại → tính CỘT
    col = lambda k: k - line_start + 1
    while i < n:
        c = src[i]
        if c == "\n": toks.append(Tok("NL","\\n",line,col(i))); line += 1; i += 1; line_start = i; continue
        if c in " \t\r": i += 1; continue
        if c == "#":
            while i < n and src[i] != "\n": i += 1
            continue
        if c == '"':
            cc = col(i); j = i+1; buf = []
            while j < n and src[j] != '"':
                if src[j] == "\\" and j+1 < n:
                    nxt = src[j+1]; buf.append({"n":"\n","t":"\t",'"':'"',"\\":"\\"}.get(nxt,nxt)); j += 2
                else: buf.append(src[j]); j += 1
            if j >= n: raise GiaoSyntax("chuỗi không đóng (thiếu \")", line, cc)   # KHÔNG nuốt im-lặng tới EOF
            toks.append(Tok("STR","".join(buf),line,cc)); i = j+1; continue
        if c.isdigit() or (c == "." and i+1 < n and src[i+1].isdigit()):
            cc = col(i); j = i
            while j < n and (src[j].isdigit() or src[j] == "."): j += 1
            num = src[i:j]
            if num.count(".") > 1: raise GiaoSyntax(f"số sai (nhiều dấu chấm) {num!r}", line, cc)   # 1.2.3 → lỗi sạch, KHÔNG crash float()
            try:
                giá = float(num) if "." in num else int(num)
            except ValueError:                          # literal nguyên quá dài (>int_max_str_digits Py3.11) → lỗi sạch, KHÔNG traceback trần
                raise GiaoSyntax(f"số quá dài ({len(num)} chữ số)", line, cc)
            toks.append(Tok("NUM", giá, line, cc)); i = j; continue
        if is_ident_start(c):
            cc = col(i); j = i
            while j < n and is_ident_part(src[j]): j += 1
            word = src[i:j]
            toks.append(Tok("KW", KEYWORDS[word], line, cc) if word in KEYWORDS else Tok("ID", word, line, cc))
            i = j; continue
        matched = False
        for p in PUNCT:
            if src.startswith(p, i):
                toks.append(Tok("OP", p, line, col(i))); i += len(p); matched = True; break
        if matched: continue
        raise GiaoSyntax(f"ký tự lạ {c!r}", line, col(i))
    toks.append(Tok("NL","\\n",line,col(i))); toks.append(Tok("EOF",None,line,col(i)))
    return toks

# ============================================================
# 2. AST
# ============================================================
class Node: line=None; col=None   # mặc định lớp → đọc node.line trực tiếp (không getattr, nhanh hơn)
class Num(Node):
    def __init__(s,v): s.v=v
class Str(Node):
    def __init__(s,v): s.v=v
class AnLit(Node): pass
class TruthLit(Node):
    def __init__(s,t): s.t=t
class ListLit(Node):
    def __init__(s,elems): s.elems=elems
class FieldRef(Node):
    def __init__(s,field,name): s.field,s.name=field,name
class VarRef(Node):
    def __init__(s,name): s.name=name
class DeQuery(Node): pass
class Bin(Node):
    def __init__(s,op,l,r): s.op,s.l,s.r=op,l,r
class Unary(Node):
    def __init__(s,op,e): s.op,s.e=op,e
class Index(Node):
    def __init__(s,coll,idx): s.coll,s.idx=coll,idx
class Goi(Node):
    def __init__(s,callee,args): s.callee,s.args=callee,args
# statements
class Decl(Node):
    def __init__(s,field,name,expr): s.field,s.name,s.expr=field,name,expr
class Dat(Node):
    def __init__(s,name,expr): s.name,s.expr=name,expr
class DatIndex(Node):                  # đặt ds[i]…[k] = x — GÁN THEO CHỈ MỤC (A2), sửa TẠI CHỖ
    def __init__(s,name,idxs,expr): s.name,s.idxs,s.expr=name,idxs,expr
class Hoc(Node):
    def __init__(s,name): s.name=name
class Giao(Node):
    def __init__(s,target,ifname,mfname): s.target,s.ifname,s.mfname=target,ifname,mfname
class Roi(Node):
    def __init__(s,expr): s.expr=expr
class Lap(Node):
    def __init__(s,count,body): s.count,s.body=count,body
class LapTrong(Node):                  # lặp x trong <ds> { } — DUYỆT dữ liệu (KHÔNG đệ quy, gỡ trần sâu)
    def __init__(s,var,iterable,body): s.var,s.iterable,s.body=var,iterable,body
class Mai(Node):                       # vòng LIÊN TỤC thật (continual) — chạy tới khi 'dừng'
    def __init__(s,body): s.body=body
class Dung(Node): pass                  # thoát vòng lặp
class TroiReg(Node):                    # đăng ký LUẬT TRÔI cho một ô vật (thế giới có động học riêng)
    def __init__(s,name,expr): s.name,s.expr=name,expr
class TroiTick(Node): pass              # một NHỊP thời gian: áp mọi luật trôi → ρ_MF dịch → DE_T mọc lại
class Neu(Node):
    def __init__(s,cond,then,ngo,khac): s.cond,s.then,s.ngo,s.khac=cond,then,ngo,khac
class KhiVienMan(Node):
    def __init__(s,expr,body): s.expr,s.body=expr,body
class HamDef(Node):
    def __init__(s,name,params,body): s.name,s.params,s.body=name,params,body
class Lam(Node):                       # hàm vô danh (biểu thức) → Closure
    def __init__(s,params,body): s.params,s.body=params,body
class Tra(Node):
    def __init__(s,expr): s.expr=expr
class ThuBat(Node):
    def __init__(s,thu,tên,bat): s.thu,s.tên,s.bat=thu,tên,bat
class ExprStmt(Node):
    def __init__(s,expr): s.expr=expr
class Nhap(Node):                      # nhập "tệp.giao" — nạp module (include, an toàn trong cây dự án)
    def __init__(s,path): s.path=path

# ============================================================
# 3. PARSER
# ============================================================
class Parser:
    def __init__(self, toks): self.toks=list(toks); self.pos=0
    def peek(self,k=0): return self.toks[self.pos+k]
    def next(self): t=self.toks[self.pos]; self.pos+=1; return t
    def at(self,kind,val=None):
        t=self.peek(); return t.kind==kind and (val is None or t.val==val)
    def eat(self,kind,val=None):
        t=self.peek()
        if t.kind!=kind or (val is not None and t.val!=val):
            raise GiaoSyntax(f"chờ {kind} {val or ''}, gặp {t.kind} {t.val!r}", t.line, t.col)
        return self.next()
    def skip_nl(self):
        while self.at("NL"): self.next()

    def parse(self):
        stmts=[]; self.skip_nl()
        while not self.at("EOF"):
            stmts.append(self.statement()); self.skip_nl()
        return stmts

    def block(self):
        self.eat("OP","{"); self.skip_nl(); stmts=[]
        while not self.at("OP","}"):
            stmts.append(self.statement()); self.skip_nl()
        self.eat("OP","}"); return stmts

    def params(self):
        self.eat("OP","("); ps=[]
        if not self.at("OP",")"):
            ps.append(self.eat("ID").val)
            while self.at("OP",","): self.next(); ps.append(self.eat("ID").val)
        self.eat("OP",")"); return ps

    def statement(self):
        ln=self.peek().line; cl=self.peek().col
        node=self._statement()
        if getattr(node,"line",None) is None: node.line=ln
        if getattr(node,"col",None) is None: node.col=cl
        return node
    def _statement(self):
        t=self.peek()
        if t.kind=="KW" and t.val in ("vật","tâm"):
            self.next(); name=self.eat("ID").val; self.eat("OP","="); return Decl(t.val,name,self.expr())
        if t.kind=="KW" and t.val=="đặt":
            self.next(); name=self.eat("ID").val
            if self.at("OP","["):                  # đặt ds[i] = x · đặt b["k"] = x · lồng ds[i][j] (A2)
                idxs=[]
                while self.at("OP","["):
                    self.next(); self.skip_nl(); idxs.append(self.expr()); self.skip_nl(); self.eat("OP","]")
                self.eat("OP","="); return DatIndex(name,idxs,self.expr())
            self.eat("OP","="); return Dat(name,self.expr())
        if t.kind=="KW" and t.val=="hàm":
            self.next(); name=self.eat("ID").val; ps=self.params(); body=self.block(); return HamDef(name,ps,body)
        if t.kind=="KW" and t.val=="trả":
            self.next(); return Tra(self.expr())
        if t.kind=="KW" and t.val=="nhập":
            self.next(); return Nhap(self.eat("STR").val)
        if t.kind=="KW" and t.val=="học":
            self.next(); return Hoc(self.eat("ID").val)
        if t.kind=="KW" and t.val=="giao":
            self.next(); target=self.eat("ID").val; self.eat("OP","=")
            if self.at("KW","tâm"):
                self.next(); ifn=self.eat("ID").val
                if self.at("OP","⋈") or self.at("OP","~"): self.next()
                else: self.eat("OP","⋈")
                self.eat("KW","vật"); mfn=self.eat("ID").val; return Giao(target,ifn,mfn)
            nm=self.eat("ID").val; return Giao(target,nm,nm)
        if t.kind=="KW" and t.val=="rọi":
            self.next(); return Roi(self.expr())
        if t.kind=="KW" and t.val=="lặp":
            self.next()
            # dạng DUYỆT:  lặp <ident> trong <ds> { }   ('trong' là từ khoá NGỮ CẢNH)
            if self.at("ID") and self.peek(1).kind=="ID" and self.peek(1).val=="trong":
                name=self.eat("ID").val; self.next()      # ăn 'trong'
                it=self.expr(); return LapTrong(name,it,self.block())
            cnt=self.expr(); return Lap(cnt,self.block())
        if t.kind=="KW" and t.val=="mãi":
            self.next(); return Mai(self.block())
        if t.kind=="KW" and t.val=="dừng":
            self.next(); return Dung()
        if t.kind=="KW" and t.val=="trôi":
            self.next()
            if self.at("ID"):
                name=self.eat("ID").val; self.eat("OP","="); return TroiReg(name,self.expr())
            return TroiTick()
        if t.kind=="KW" and t.val=="nếu":
            self.next(); cond=self.expr(); then=self.block(); ngo=khac=None; self.skip_nl()
            if self.at("KW","ngờ"): self.next(); ngo=self.block(); self.skip_nl()
            if self.at("KW","khác"): self.next(); khac=self.block()
            return Neu(cond,then,ngo,khac)
        if t.kind=="KW" and t.val=="khi":
            self.next(); self.eat("KW","viên_mãn"); expr=self.expr(); return KhiVienMan(expr,self.block())
        if t.kind=="KW" and t.val=="thử":
            self.next(); thu=self.block(); self.skip_nl()
            self.eat("KW","bắt"); tên=None
            if self.at("OP","("): self.next(); tên=self.eat("ID").val; self.eat("OP",")")
            return ThuBat(thu,tên,self.block())
        return ExprStmt(self.expr())

    # biểu thức: so sánh < cộng < nhân < hậu tố < nguyên tử
    def expr(self): return self.comparison()
    def comparison(self):
        left=self.addition()
        while self.at("OP") and self.peek().val in ("==","!=",">","<",">=","<="):
            op=self.next().val; left=Bin(op,left,self.addition())
        return left
    def addition(self):
        left=self.term()
        while self.at("OP") and self.peek().val in ("+","-"):
            op=self.next().val; left=Bin(op,left,self.term())
        return left
    def term(self):
        left=self.postfix()
        while self.at("OP") and self.peek().val in ("*","/","//"):
            op=self.next().val; left=Bin(op,left,self.postfix())
        return left
    def postfix(self):
        e=self.atom()
        while True:
            if self.at("OP","("):
                self.next(); self.skip_nl(); args=[]
                if not self.at("OP",")"):
                    args.append(self.expr()); self.skip_nl()
                    while self.at("OP",","): self.next(); self.skip_nl(); args.append(self.expr()); self.skip_nl()
                self.eat("OP",")"); e=Goi(e,args)
            elif self.at("OP","["):
                self.next(); self.skip_nl(); idx=self.expr(); self.skip_nl(); self.eat("OP","]"); e=Index(e,idx)
            else: break
        return e
    def atom(self):
        ln=self.peek().line; cl=self.peek().col
        node=self._atom()
        if getattr(node,"line",None) is None: node.line=ln
        if getattr(node,"col",None) is None: node.col=cl
        return node
    def _atom(self):
        t=self.peek()
        if t.kind=="NUM": self.next(); return Num(t.val)
        if t.kind=="STR": self.next(); return Str(t.val)
        if t.kind=="OP" and t.val=="-": self.next(); return Unary("-",self.postfix())
        if t.kind=="OP" and t.val=="(":
            self.next(); self.skip_nl(); e=self.expr(); self.skip_nl(); self.eat("OP",")"); return e
        if t.kind=="OP" and t.val=="[":
            self.next(); self.skip_nl(); elems=[]
            if not self.at("OP","]"):
                elems.append(self.expr()); self.skip_nl()
                while self.at("OP",","): self.next(); self.skip_nl(); elems.append(self.expr()); self.skip_nl()
            self.skip_nl(); self.eat("OP","]"); return ListLit(elems)
        if t.kind=="KW":
            if t.val=="hàm":                       # hàm vô danh: hàm(x){ ... }
                self.next(); ps=self.params(); body=self.block(); return Lam(ps,body)
            if t.val=="ẩn": self.next(); return AnLit()
            if t.val=="sáng": self.next(); return TruthLit(SANG)
            if t.val=="tối": self.next(); return TruthLit(TOI)
            if t.val=="de": self.next(); return DeQuery()
            if t.val in ("tâm","vật"): self.next(); return FieldRef(t.val, self.eat("ID").val)
        if t.kind=="ID": self.next(); return VarRef(t.val)
        raise GiaoSyntax(f"không hiểu biểu thức tại {t.kind} {t.val!r}", t.line, t.col)

# ============================================================
# 4. INTERPRETER — bộ máy CDFL + scoping cho hàm
# ============================================================
ALPHA = 0.5
TAU_VIENMAN = 0.99

# ============================================================
# CDFL MỚI — γ SKILL-SCORE (Phụ lục F.4) + e CAM KẾT (F.11)
# Thay γ proxy cũ (1−2d/scale) bằng ĐIỂM KỸ NĂNG so với NỀN VÔ-TRI:
#   γ>0 = niềm tin THẮNG nền (kỹ năng thật) · γ<0 = TỆ HƠN không biết gì (ảo tưởng = đốm tối)
# Chống Goodhart: γ đo trên độ-khớp-thực-tại có hiệu chỉnh nền, KHÔNG là đích tối ưu trực tiếp.
# ============================================================
GAMMA_BASELINE = _math.exp(-1.0)   # R nền vô-tri (một đơn-vị lệch) — khớp core.py gamma_from_R
STD0 = 1.0                          # độ tán nền cho cam kết e

def _R_scalar(belief, truth):
    """Cộng hưởng THÔ R∈(0,1] = exp(−(d/scale)²): likelihood niềm tin khớp thực tại."""
    d = abs(truth - belief); scale = max(abs(truth), 1.0)
    return _math.exp(-((d / scale) ** 2))

def skill_gamma(R_belief, R_baseline=GAMMA_BASELINE):
    """γ kỹ-năng (F.4) = [S(ρ‖u) − S(ρ‖σ)]/[S(ρ‖u)+S(ρ‖σ)], S = −ln R.
    d=scale (niềm tin ngang nền) → γ=0; gần hơn → γ>0; xa hơn nền → γ<0 (đốm tối)."""
    a = -_math.log(max(float(R_baseline), 1e-12))   # S(ρ‖u): độ tối so NỀN vô-tri
    b = -_math.log(max(float(R_belief), 1e-12))     # S(ρ‖σ): độ tối so NIỀM TIN
    if a + b <= 1e-12: return 0.0
    return max(-1.0, min(1.0, (a - b) / (a + b)))

def commitment_e(stds, std0=STD0):
    """e cam kết (F.11) = S/(1+S), S = Σ ln(std0/std_i) ≥ 0. Niềm tin càng SẮC → càng cam kết."""
    S = 0.0
    for s in stds: S += _math.log(std0 / max(float(s), 1e-9))
    S = max(S, 0.0)
    return S / (1.0 + S)

class Runtime:
    def __init__(self):
        self.tam = {}            # IF (global)
        self.vat = {}            # MF (global)
        self.glob = {}           # biến/hàm toàn cục, kết quả OR ở mức ngoài
        self.env = None          # MÔI TRƯỜNG cục bộ hiện hành (None = scope toàn cục); chuỗi lexical
        self.observed = set()
        # --- theo dõi cho DE BỐN MẶT (tiên đề: DE_X, DE_T, DE_IF, DE_MF) ---
        self.vat_version = {}    # vật đổi mấy lần (ρ_MF trôi) → nền DE_T
        self.tam_learned = {}    # phiên bản vật lúc 'học' gần nhất
        self.tam_gamma = {}      # γ gần nhất của mỗi ô tâm → nền DE_IF (γ<0 = ảo tưởng)
        self.drifts = {}         # luật trôi: tên ô vật → biểu thức động học (thế giới TỰ trôi)
        # --- giới hạn tài nguyên (sandbox an toàn) ---
        self.cur_line = None; self.cur_col = None
        self.steps = 0;   self.MAX_STEPS = 5_000_000      # chống vòng lặp vô tận / DoS
        self.depth = 0;   self.MAX_DEPTH = 900            # chống đệ quy vô tận
        self.MAX_LIST = 1_000_000                         # chống phình danh sách
        self.MAX_STR  = 2_000_000                         # chống phình chuỗi
        # --- I/O THEO NĂNG LỰC (object-capability) ---
        # Mặc định RỖNG ⇒ KHÔNG builtin I/O nào tồn tại ⇒ sandbox tuyệt đối (như trước).
        # Host cấp quyền tường minh qua cấp_quyền(); chương trình GIAO KHÔNG tự nới được.
        self.caps = {}            # tên_quyền → cấu hình phạm vi (gốc thư mục / allowlist lệnh)
        # --- module `nhập` (cấu trúc nguồn lúc nạp; chỉ .giao trong cây dự án) ---
        self.base_dir = os.getcwd()  # gốc cây cho phép nhập (main() đặt = thư mục tệp chính)
        self.đã_nhập = set()         # realpath đã nạp → idempotent
        self.nhập_stack = []         # phát hiện vòng nhập (circular)
        self.nhập_dir = []           # thư mục module đang nạp (giải đường tương đối)
        # --- phát-hiện VA-TÊN module (namespace phẳng → bản nạp-sau che bản-trước IM-LẶNG) ---
        self.ham_origin = {}         # tên hàm toàn-cục → tệp đã định-nghĩa (nhãn)
        self.tệp_hiện = "<chính>"    # nhãn tệp cấp-cao đang chạy (ngoài `nhập`)
        self.cảnh_va_tên = True      # bật cảnh-báo va-tên (module↔module; bỏ-qua ghi-đè prelude chủ-ý)
        self._install_builtins()

    # ---- an toàn: lỗi sạch + đo bước ----
    def err(self, msg): raise GiaoError(msg, self.cur_line, self.cur_col)
    def tick(self):
        self.steps += 1
        if self.steps > self.MAX_STEPS:
            raise GiaoLimit(f"vượt {self.MAX_STEPS} bước (nghi vòng lặp vô tận)")
    def _loai(self, v):
        if v is AN: return "ẩn"
        if isinstance(v,bool): return "trị"
        if isinstance(v,(int,float)): return "số"
        if isinstance(v,str): return "chuỗi"
        if isinstance(v,list): return "danh_sách"
        if isinstance(v,Ban): return "bản"
        if isinstance(v,Closure): return "hàm"
        if isinstance(v,Tri): return "tri"
        return "?"

    # ---- scoping (TỪ VỰNG / lexical) ----
    def cur_define(self, name, val):
        if self.env is None: self.glob[name] = val
        else: self.env.vars[name] = val
    def lookup(self, name):
        e = self.env
        while e is not None:                       # đi LÊN chuỗi môi trường ĐỊNH NGHĨA
            if name in e.vars: return e.vars[name]
            e = e.parent
        if name in self.glob: return self.glob[name]
        cands = set(self.glob.keys()); e = self.env   # GỢI Ý 'có phải…?' (sửa lỗi gõ)
        while e is not None: cands |= set(e.vars.keys()); e = e.parent
        gần = difflib.get_close_matches(name, cands, n=1, cutoff=0.7)
        self.err(f"tên '{name}' chưa định nghĩa" + (f" — có phải '{gần[0]}'?" if gần else ""))

    # ---- cộng hưởng ----
    def resonance(self, belief, truth):
        if belief is AN: return Tri(AN, None, "ẩn")
        if truth is AN:  return Tri(AN, None, "ẩn")
        if isinstance(belief,(int,float)) and isinstance(truth,(int,float)):
            gamma=skill_gamma(_R_scalar(belief,truth))     # γ kỹ-năng so NỀN vô-tri (F.4, thay proxy 1−2d/scale)
        else:
            gamma=1.0 if belief==truth else -1.0
        state=SANG if gamma>0 else (TOI if gamma<0 else "ẩn")
        return Tri(belief,gamma,state)

    # ---- eval ----
    def eval(self, node):
        ln=node.line
        if ln is not None: self.cur_line=ln; self.cur_col=node.col
        self.steps+=1                                  # tick() nội tuyến (hot path)
        if self.steps>self.MAX_STEPS: raise GiaoLimit(f"vượt {self.MAX_STEPS} bước (nghi vòng lặp vô tận)")
        T=type(node)
        # — NHÁNH NÓNG trước (theo profile: VarRef/Bin/Goi/Num chiếm đa số) —
        if T is VarRef: return self.lookup(node.name)
        if T is Bin: return self.eval_bin(node)
        if T is Goi: return self.call(node)
        if T is Num: return node.v
        if T is Str: return node.v
        # — phần còn lại —
        if T is AnLit: return AN
        if T is TruthLit: return node.t
        if T is DeQuery: return self.dark_existence()
        if T is ListLit:
            xs=[self.eval(e) for e in node.elems]
            if len(xs)>self.MAX_LIST: raise GiaoLimit("danh sách quá lớn")
            return xs
        if T is FieldRef:
            store=self.tam if node.field=="tâm" else self.vat
            if node.name not in store: self.err(f"{node.field} '{node.name}' chưa khai báo")
            return store[node.name]
        if T is Lam: return Closure("λ", node.params, node.body, self.env)   # bắt môi trường định nghĩa
        if T is Unary:
            v=self.eval(node.e)
            if v is AN: return AN
            if not isinstance(v,(int,float)) or isinstance(v,bool): self.err(f"không thể lấy số đối của {self._loai(v)}")
            return -v
        if T is Index:
            coll=self.eval(node.coll); idx=self.eval(node.idx)
            return self._chỉ_mục_đọc(coll, idx)
        self.err("biểu thức không hiểu được")

    def _chỉ_mục_đọc(self, coll, idx):
        "Đọc coll[idx] — MỘT nguồn sự thật cho cả biểu thức Index lẫn gán theo chỉ mục (A2)."
        if coll is AN or idx is AN: return AN
        if isinstance(coll,Ban):                 # m[khoá] → giá trị hoặc ẩn (thiếu khoá)
            if not (isinstance(idx,(int,float,str))): self.err(f"khoá bản phải là số/chuỗi, gặp {self._loai(idx)}")
            return coll.d.get(idx, AN)
        if not isinstance(coll,(list,str)): self.err(f"không thể lập chỉ mục trên {self._loai(coll)}")
        if not isinstance(idx,(int,float)) or isinstance(idx,bool): self.err(f"chỉ mục phải là số, gặp {self._loai(idx)}")
        i=int(idx)
        if i<0 or i>=len(coll): self.err(f"chỉ mục {i} ngoài phạm vi 0..{len(coll)-1}")
        return coll[i]

    def call(self, node):
        fn=self.eval(node.callee); args=[self.eval(a) for a in node.args]
        if callable(fn) and not isinstance(fn,Closure):
            return fn(args)                       # builtin Python (tự kiểm tra số đối)
        if isinstance(fn,Closure):
            if len(args)!=len(fn.params):
                self.err(f"hàm '{fn.name}' cần {len(fn.params)} đối, nhận {len(args)}")
            self.depth+=1
            if self.depth>self.MAX_DEPTH:
                self.depth-=1
                raise GiaoLimit(f"đệ quy quá sâu (>{self.MAX_DEPTH})")
            new_env=Env(fn.env)                   # CHA = môi trường nơi hàm được ĐỊNH NGHĨA (lexical)
            for p,a in zip(fn.params,args): new_env.vars[p]=a
            saved=self.env; self.env=new_env
            try:
                for s in fn.body: self.exec(s)
                ret=AN
            except ReturnSignal as r:
                ret=r.value
            finally:
                self.env=saved; self.depth-=1
            return ret
        self.err(f"không gọi được giá trị kiểu {self._loai(fn)}")

    def eval_bin(self, node):
        l=self.eval(node.l); r=self.eval(node.r); op=node.op
        tl=type(l); tr=type(r)
        if (tl is int or tl is float) and (tr is int or tr is float):   # ★ FAST PATH số↔số
            if op=="+": return l+r
            if op=="-": return l-r
            if op=="*": return l*r
            if op=="<": return SANG if l<r else TOI
            if op==">": return SANG if l>r else TOI
            if op=="==": return SANG if l==r else TOI
            if op=="!=": return SANG if l!=r else TOI
            if op=="<=": return SANG if l<=r else TOI
            if op==">=": return SANG if l>=r else TOI
            if op=="//": return AN if r==0 else l//r
            if op=="/": return AN if r==0 else l/r
        if l is AN or r is AN: return AN
        if isinstance(l,Tri): l=l.value if l.state!="ẩn" else AN
        if isinstance(r,Tri): r=r.value if r.state!="ẩn" else AN
        if l is AN or r is AN: return AN
        num = lambda x: isinstance(x,(int,float)) and not isinstance(x,bool)
        if op=="==": return SANG if l==r else TOI
        if op=="!=": return SANG if l!=r else TOI
        if op=="+":
            if isinstance(l,str) or isinstance(r,str):
                s=f"{self._s(l)}{self._s(r)}"
                if len(s)>self.MAX_STR: raise GiaoLimit("chuỗi quá lớn")
                return s
            if isinstance(l,list) and isinstance(r,list):
                if len(l)+len(r)>self.MAX_LIST: raise GiaoLimit("danh sách quá lớn")
                return l+r
            if num(l) and num(r): return l+r
            self.err(f"không thể '+' giữa {self._loai(l)} và {self._loai(r)}")
        if op in ("-","*","/","//"):
            if not (num(l) and num(r)): self.err(f"không thể '{op}' giữa {self._loai(l)} và {self._loai(r)}")
            if op=="-": return l-r
            if op=="*": return l*r
            if op=="//": return AN if r==0 else l//r       # chia LẤY NGUYÊN chính xác (số lớn)
            return AN if r==0 else l/r            # chia 0 → ẩn (không nổ)
        # so sánh thứ tự: số↔số hoặc chuỗi↔chuỗi
        if (num(l) and num(r)) or (isinstance(l,str) and isinstance(r,str)):
            if op==">":  return SANG if l>r  else TOI
            if op=="<":  return SANG if l<r  else TOI
            if op==">=": return SANG if l>=r else TOI
            if op=="<=": return SANG if l<=r else TOI
        self.err(f"không thể so sánh '{op}' giữa {self._loai(l)} và {self._loai(r)}")

    def _s(self,v): return self.render(v)   # NGUỒN SỰ THẬT duy nhất = render (tránh hai bản format lệch nhau)

    def de_cau_truc(self):
        "DE bốn mặt dạng CẤU TRÚC (để cầu nối/host đọc) — một nguồn sự thật cho cả bản chữ."
        de_x  = [k for k in self.vat if k not in self.tam]                  # vật có, tâm chưa từng → chưa tới
        de_t  = [k for k in self.tam_learned if self.vat_version.get(k,0) > self.tam_learned[k]]  # ρ trôi sau khi học
        de_if = [k for k,v in self.tam.items() if v is AN or self.tam_gamma.get(k,0.0) < 0]       # ẩn / ảo tưởng γ<0
        de_mf = [k for k in self.vat if k not in self.observed]             # thế giới chưa phơi
        return {"DE_X":de_x, "DE_T":de_t, "DE_IF":de_if, "DE_MF":de_mf,
                "hợp": sorted(set(de_x)|set(de_t)|set(de_if)|set(de_mf))}

    def dark_existence(self):
        d = self.de_cau_truc(); de_x,de_t,de_if,de_mf = d["DE_X"],d["DE_T"],d["DE_IF"],d["DE_MF"]
        def s(xs): return ", ".join(xs) if xs else "∅"
        tổng = len(d["hợp"])
        return ("DE — Vùng Tối BỐN MẶT (Dark Existence) — chồng nhau, DE ≠ tổng rời:\n"
                f"   • DE_X  (không gian chưa tới): {s(de_x)}\n"
                f"   • DE_T  (tri thức cũ trôi)   : {s(de_t)}\n"
                f"   • DE_IF (tâm chưa hình dung) : {s(de_if)}\n"
                f"   • DE_MF (thế giới chưa phơi) : {s(de_mf)}\n"
                f"   • |DE hợp|={tổng}  →  {'còn sàn tối D>0' if tổng else 'viên mãn cục bộ ở đây'}")

    # ---- exec ----
    def exec_block(self, stmts):
        for s in stmts: self.exec(s)
    def exec(self, node):
        ln=node.line
        if ln is not None: self.cur_line=ln; self.cur_col=node.col
        self.steps+=1                                  # tick() nội tuyến (hot path)
        if self.steps>self.MAX_STEPS: raise GiaoLimit(f"vượt {self.MAX_STEPS} bước (nghi vòng lặp vô tận)")
        T=type(node)
        # — NHÁNH NÓNG trước —
        if T is Tra: raise ReturnSignal(self.eval(node.expr))
        if T is Neu:
            t3=truthy3(self.eval(node.cond))
            if t3==SANG: self.exec_block(node.then)
            elif t3 is AN:
                if node.ngo is not None: self.exec_block(node.ngo)
                elif node.khac is not None: self.exec_block(node.khac)
            else:
                if node.khac is not None: self.exec_block(node.khac)
            return
        if T is ExprStmt:
            e=node.expr
            # BẪY A3: `thêm(ds, x)` đứng MỘT MÌNH = kết quả bị vứt = danh sách KHÔNG đổi gì —
            # bug im lặng đã cắn thật (lib_người_dùng). Chỉ bắt khi 'thêm' vẫn là builtin gốc
            # (người dùng tự định nghĩa hàm 'thêm' riêng thì không đụng tới).
            if (type(e) is Goi and type(e.callee) is VarRef and e.callee.name in ("thêm","them")
                    and self.lookup(e.callee.name) is self._b_them):
                self.err("kết quả của 'thêm' bị VỨT — 'thêm' KHÔNG sửa danh sách tại chỗ, câu lệnh "
                         "này không đổi gì cả. Chèn tại chỗ: gom(ds, x) · giữ bản mới: đặt ds = thêm(ds, x)")
            self.eval(e); return
        if T is Dat:
            self.cur_define(node.name, self.eval(node.expr)); return
        if T is DatIndex:                          # đặt ds[i]…[k] = x — sửa TẠI CHỖ (A2)
            coll=self.lookup(node.name)
            for k in node.idxs[:-1]:               # các tầng GIỮA: đọc như biểu thức chỉ mục
                coll=self._chỉ_mục_đọc(coll, self.eval(k))
            idx=self.eval(node.idxs[-1]); val=self.eval(node.expr)
            if coll is AN or idx is AN: return     # thùng/chỉ-mục ẩn → KHÔNG ghi (no-op, như đặt_khoá)
            if isinstance(coll,Ban):               # đặt b[khoá] = x ≡ đặt_khoá (mutate)
                if not isinstance(idx,(int,float,str)): self.err(f"khoá bản phải là số/chuỗi, gặp {self._loai(idx)}")
                if idx not in coll.d and len(coll.d)+1>self.MAX_LIST: raise GiaoLimit("bản quá lớn")
                coll.d[idx]=val; return
            if isinstance(coll,str): self.err("chuỗi BẤT BIẾN — không gán theo chỉ mục được (dùng tách/nối)")
            if not isinstance(coll,list): self.err(f"không thể gán chỉ mục trên {self._loai(coll)}")
            if not isinstance(idx,(int,float)) or isinstance(idx,bool): self.err(f"chỉ mục phải là số, gặp {self._loai(idx)}")
            i=int(idx)
            if i<0 or i>=len(coll): self.err(f"chỉ mục {i} ngoài phạm vi 0..{len(coll)-1} (nới danh sách thì dùng gom)")
            coll[i]=val; return
        if T is ThuBat:
            try:
                self.exec_block(node.thu)
            except GiaoError as e:                 # CHỈ bắt lỗi runtime; GiaoLimit lọt qua
                if node.tên is not None: self.cur_define(node.tên, e.msg)
                self.exec_block(node.bat)
            return
        if T is Decl:
            val=self.eval(node.expr)
            if node.field=="tâm": self.tam[node.name]=val
            else:                                   # vật đổi = ρ_MF trôi (nhân quả/continual)
                self.vat[node.name]=val
                self.vat_version[node.name]=self.vat_version.get(node.name,0)+1
            return
        if T is HamDef:
            if self.env is None:                       # hàm ở scope TOÀN-CỤC → soi va-tên
                cur = self.nhập_stack[-1] if self.nhập_stack else self.tệp_hiện
                prev = self.ham_origin.get(node.name)
                # CHỈ kêu khi hai NGUỒN KHÁC nhau VÀ bản trước KHÔNG phải prelude
                # (lib ghi-đè prelude như mũ_e/ln decimal là CHỦ-Ý, không cảnh-báo).
                if (self.cảnh_va_tên and prev is not None and prev != cur
                        and prev != "chuẩn.giao"):
                    sys.stderr.write(
                        f"⚠ va-tên: hàm '{node.name}' ở {os.path.basename(cur)} "
                        f"che bản trước ({os.path.basename(prev)}) — namespace phẳng\n")
                self.ham_origin[node.name] = cur
            self.cur_define(node.name, Closure(node.name,node.params,node.body,self.env)); return
        if T is Hoc: self.learn(node.name); return
        if T is Giao:
            belief=self.tam.get(node.ifname,AN); truth=self.vat.get(node.mfname,AN)
            if node.mfname in self.vat: self.observed.add(node.mfname)
            tri=self.resonance(belief,truth)
            if tri.gamma is not None: self.tam_gamma[node.ifname]=tri.gamma
            self.cur_define(node.target, tri); return
        if T is Roi: print(self.render(self.eval(node.expr))); return
        if T is Lap:
            cnt=self.eval(node.count)
            if cnt is AN: cnt=0
            elif not isinstance(cnt,(int,float)) or isinstance(cnt,bool): self.err(f"lặp cần số lần là số, gặp {self._loai(cnt)}")
            for _ in range(int(cnt)):
                self.tick()
                try: self.exec_block(node.body)
                except DungSignal: break
            return
        if T is LapTrong:                              # DUYỆT danh sách/chuỗi — KHÔNG đệ quy (gỡ trần sâu)
            it=self.eval(node.iterable)
            if it is AN: return
            if isinstance(it,str): items=list(it)      # chuỗi → từng ký tự (length-1)
            elif isinstance(it,list): items=it
            elif isinstance(it,Ban): items=list(it.d.keys())   # bản → duyệt KHOÁ
            else: self.err(f"lặp ... trong cần danh_sách/chuỗi/bản, gặp {self._loai(it)}")
            for x in items:
                self.tick(); self.cur_define(node.var,x)
                try: self.exec_block(node.body)
                except DungSignal: break
            return
        if T is Mai:                                   # vòng LIÊN TỤC: học mãi, không viên mãn toàn cục
            while True:
                self.tick()
                try: self.exec_block(node.body)
                except DungSignal: break
            return
        if T is Dung: raise DungSignal()
        if T is TroiReg:                               # đăng ký động học riêng của thế giới
            if node.name not in self.vat: self.err(f"trôi '{node.name}': vật chưa khai báo")
            self.drifts[node.name]=node.expr; return
        if T is TroiTick:                              # một nhịp thời gian: thế giới tự dịch
            if not self.drifts: self.err("trôi: chưa có luật trôi nào được đăng ký")
            for name,expr in self.drifts.items():
                self.vat[name]=self.eval(expr)
                self.vat_version[name]=self.vat_version.get(name,0)+1
            return
        if T is KhiVienMan:
            v=self.eval(node.expr); g=v.gamma if isinstance(v,Tri) and v.gamma is not None else None
            if g is not None and g>=TAU_VIENMAN: self.exec_block(node.body)
            return
        if T is Nhap:
            importer = self.nhập_dir[-1] if self.nhập_dir else self.base_dir
            real = os.path.realpath(os.path.join(importer, node.path))
            base = os.path.realpath(self.base_dir)
            if not real.endswith(".giao"): self.err(f"nhập chỉ nạp tệp .giao: '{node.path}'")
            if not (real == base or real.startswith(base + os.sep)):
                self.err(f"nhập '{node.path}' NGOÀI cây thư mục dự án")
            if real in self.đã_nhập: return                 # đã nạp → bỏ qua (idempotent)
            if real in self.nhập_stack: self.err(f"nhập VÒNG (circular): '{node.path}'")
            try:
                with open(real, encoding="utf-8") as f: src=f.read()
            except OSError: self.err(f"không nhập được '{node.path}'")
            self.đã_nhập.add(real); self.nhập_stack.append(real); self.nhập_dir.append(os.path.dirname(real))
            saved=self.env; self.env=None                   # module chạy ở scope TOÀN CỤC
            try: self.exec_block(Parser(tokenize(src)).parse())
            finally: self.env=saved; self.nhập_stack.pop(); self.nhập_dir.pop()
            return
        self.err("câu lệnh không hiểu được")

    def learn(self, name):
        if name not in self.vat: self.err(f"không thể học '{name}': vật chưa khai báo")
        truth=self.vat[name]; self.observed.add(name)
        belief=self.tam.get(name,AN)
        if belief is AN: belief=0.0
        if isinstance(truth,(int,float)) and isinstance(belief,(int,float)):
            belief=belief+ALPHA*(truth-belief)
        else: belief=truth
        self.tam[name]=belief
        self.tam_learned[name]=self.vat_version.get(name,0)   # ghi mốc thời gian học

    def render(self, v):
        if v is AN: return "ẩn"
        if isinstance(v,Tri): return repr(v)
        if isinstance(v,float): return f"{v:.4g}"
        if isinstance(v,bool): return SANG if v else TOI
        if isinstance(v,list): return "["+", ".join(self.render(x) for x in v)+"]"
        if isinstance(v,Ban): return "{"+", ".join(f"{self.render(k)}: {self.render(x)}" for k,x in v.d.items())+"}"
        return str(v)

    # ---- builtins (đóng vai 'thư viện gốc', sẽ tự viết bằng GIAO sau) ----
    def _install_builtins(self):
        def need(args,n,who):
            if len(args)!=n: self.err(f"{who} cần {n} đối, nhận {len(args)}")
        def seq(v,who):
            if not isinstance(v,(list,str)): self.err(f"{who} cần danh_sách/chuỗi, gặp {self._loai(v)}")
            return v
        def b_dai(a):
            need(a,1,"dài")
            if isinstance(a[0],Ban): return len(a[0].d)
            return len(seq(a[0],"dài"))
        # ---- BẢN (map/record) — kiểu tham chiếu, mutable, tra cứu O(1) ----
        def _khoá(k):
            if not isinstance(k,(int,float,str)): self.err(f"khoá bản phải là số/chuỗi/trị, gặp {self._loai(k)}")
            return k
        def b_ban(a):    need(a,0,"bản"); return Ban()
        def b_dat_khoa(a):
            need(a,3,"đặt_khoá")
            if a[0] is AN: return AN                           # bản ẩn → ẩn (ba-trị, không crash)
            if not isinstance(a[0],Ban): self.err(f"đặt_khoá cần bản, gặp {self._loai(a[0])}")
            if a[1] is AN: return a[0]                         # khoá ẩn = khoá-không-biết → KHÔNG ghi (no-op), trả bản
            if len(a[0].d)+1>self.MAX_LIST: raise GiaoLimit("bản quá lớn")
            a[0].d[_khoá(a[1])]=a[2]; return a[0]              # MUTATE, trả lại bản (để nối chuỗi)
        def b_lay_khoa(a):
            need(a,2,"lấy_khoá")
            if a[0] is AN: return AN                           # bản ẩn → ẩn
            if not isinstance(a[0],Ban): self.err(f"lấy_khoá cần bản, gặp {self._loai(a[0])}")
            if a[1] is AN: return AN                           # khoá ẩn → ẩn (không-biết khoá ⇒ không-biết trị)
            return a[0].d.get(_khoá(a[1]), AN)                 # thiếu khoá → ẩn (ba-trị)
        def b_co_khoa(a):
            need(a,2,"có_khoá")
            if a[0] is AN: return AN                           # bản ẩn → ẩn
            if not isinstance(a[0],Ban): self.err(f"có_khoá cần bản, gặp {self._loai(a[0])}")
            if a[1] is AN: return TOI                          # khoá ẩn không phải khoá hiện-diện → tối
            return SANG if _khoá(a[1]) in a[0].d else TOI
        def b_xoa_khoa(a):
            need(a,2,"xoá_khoá")
            if a[0] is AN: return AN                           # bản ẩn → ẩn (đối-xứng lấy/có/đặt_khoá)
            if not isinstance(a[0],Ban): self.err(f"xoá_khoá cần bản, gặp {self._loai(a[0])}")
            if a[1] is AN: return a[0]                         # khoá ẩn → no-op (không có khoá ẩn để xoá)
            a[0].d.pop(_khoá(a[1]), None); return a[0]
        def b_khoa(a):
            need(a,1,"khoá")
            if not isinstance(a[0],Ban): self.err(f"khoá cần bản, gặp {self._loai(a[0])}")
            return list(a[0].d.keys())
        def b_gia_tri(a):
            need(a,1,"giá_trị")
            if not isinstance(a[0],Ban): self.err(f"giá_trị cần bản, gặp {self._loai(a[0])}")
            return list(a[0].d.values())
        def b_dau(a):
            need(a,1,"đầu"); s=seq(a[0],"đầu")
            if len(s)==0: self.err("đầu của danh_sách rỗng")
            return s[0]
        def b_duoi(a): need(a,1,"đuôi"); return list(seq(a[0],"đuôi")[1:])
        def b_them(a):
            need(a,2,"thêm"); seq(a[0],"thêm")
            if len(a[0])+1>self.MAX_LIST: raise GiaoLimit("danh sách quá lớn")
            return list(a[0])+[a[1]]
        self._b_them=b_them                               # để exec soi bẫy 'thêm bị vứt' (CÒN_THIẾU A3)
        def b_gom(a):                                     # CHÈN TẠI CHỖ O(1) (xây danh sách O(n))
            need(a,2,"gom")
            if not isinstance(a[0],list): self.err(f"gom cần danh_sách, gặp {self._loai(a[0])}")
            if len(a[0])+1>self.MAX_LIST: raise GiaoLimit("danh sách quá lớn")
            a[0].append(a[1]); return a[0]                # trả lại chính nó (để nối chuỗi)
        def b_dao(a):  need(a,1,"đảo"); return list(reversed(seq(a[0],"đảo")))   # O(n)
        def b_noi(a):                                     # join O(n) (thay vì O(n²) nối chuỗi)
            need(a,2,"nối"); ds=a[0]
            if not isinstance(ds,list): self.err(f"nối cần danh_sách, gặp {self._loai(ds)}")
            s=self._s(a[1]).join(self._s(x) for x in ds)
            if len(s)>self.MAX_STR: raise GiaoLimit("chuỗi quá lớn")
            return s
        def b_tach(a):                                    # split O(n)
            need(a,2,"tách")
            if not isinstance(a[0],str) or not isinstance(a[1],str): self.err("tách cần (chuỗi, chuỗi ngăn)")
            if len(a[1])==0: self.err("tách: ký tự ngăn rỗng")
            return a[0].split(a[1])   # GIỮ token rỗng — đúng Python str.split(sep): "a,b,"→[a,b,""], ",x"→["",x]
        def b_ghep(a):
            need(a,2,"ghép"); x,y=a
            if isinstance(x,list) and isinstance(y,list):
                if len(x)+len(y)>self.MAX_LIST: raise GiaoLimit("danh sách quá lớn")
                return x+y
            s=f"{self._s(x)}{self._s(y)}"
            if len(s)>self.MAX_STR: raise GiaoLimit("chuỗi quá lớn")
            return s
        def b_roi_ds(a):                                  # in danh sách số (mỗi phần tử một dòng)
            need(a,1,"rọi_ds")
            if not isinstance(a[0],list): self.err(f"rọi_ds cần danh_sách, gặp {self._loai(a[0])}")
            for x in a[0]: print("   "+self.render(x))
            return AN
        def b_la_ds(a):  need(a,1,"là_ds"); return SANG if isinstance(a[0],list) else TOI
        def b_la_so(a):  need(a,1,"là_số"); return SANG if isinstance(a[0],(int,float)) and not isinstance(a[0],bool) else TOI
        def b_loai(a):
            need(a,1,"loại"); return self._loai(a[0])   # NGUỒN SỰ THẬT duy nhất = _loai (gồm cả 'tri')
        def b_nguyen(a):                                  # phần nguyên (floor) → số nguyên
            need(a,1,"nguyên"); v=a[0]
            if not isinstance(v,(int,float)) or isinstance(v,bool): self.err(f"nguyên cần số, gặp {self._loai(v)}")
            return int(v // 1)
        def b_ma(a):                                      # mã: ký-tự → mã unicode (ord)
            need(a,1,"mã"); v=a[0]
            if not isinstance(v,str) or len(v)<1: self.err("mã cần CHUỖI ≥1 ký-tự")
            return ord(v[0])
        def b_kytu(a):                                    # ký_tự: mã → ký-tự (chr)
            need(a,1,"ký_tự"); v=a[0]
            if not isinstance(v,int) or isinstance(v,bool): self.err("ký_tự cần SỐ NGUYÊN")
            return chr(max(0,min(v,0x10FFFF)))
        # ---- PHÉP TOÁN BIT (CÒN_THIẾU A1) — mở khoá SHA-256/CRC/mã hoá ----
        # Số NGUYÊN chính xác mọi cỡ (như //): số âm theo bù-hai vô hạn kiểu Python.
        # Ba-trị: đối nào ẩn → kết quả ẩn (không nổ). Muốn gói 32-bit: và_bit(x, 4294967295).
        def _bit_nguyên(v, who):
            if not isinstance(v,int) or isinstance(v,bool):
                self.err(f"{who} cần SỐ NGUYÊN, gặp {self._loai(v)}")
            return v
        def _bit2(a, who, op):
            need(a,2,who)
            if a[0] is AN or a[1] is AN: return AN
            return op(_bit_nguyên(a[0],who), _bit_nguyên(a[1],who))
        def b_xor(a):     return _bit2(a,"xor",      lambda x,y: x^y)
        def b_va_bit(a):  return _bit2(a,"và_bit",   lambda x,y: x&y)
        def b_hoac_bit(a):return _bit2(a,"hoặc_bit", lambda x,y: x|y)
        def b_dao_bit(a):                             # ~x (bù-hai); đảo trong khung n bit: xor(x, 2^n−1)
            need(a,1,"đảo_bit")
            if a[0] is AN: return AN
            return ~_bit_nguyên(a[0],"đảo_bit")
        def b_dich_trai(a):
            need(a,2,"dịch_trái")
            if a[0] is AN or a[1] is AN: return AN
            x=_bit_nguyên(a[0],"dịch_trái"); n=_bit_nguyên(a[1],"dịch_trái")
            if n<0: self.err("dịch_trái: số bit dịch phải ≥ 0")
            if x.bit_length()+n > 8_000_000: raise GiaoLimit("dịch_trái: số quá lớn")
            return x<<n
        def b_dich_phai(a):
            need(a,2,"dịch_phải")
            if a[0] is AN or a[1] is AN: return AN
            x=_bit_nguyên(a[0],"dịch_phải"); n=_bit_nguyên(a[1],"dịch_phải")
            if n<0: self.err("dịch_phải: số bit dịch phải ≥ 0")
            return x>>n
        def b_conghuong(a):                               # γ = cộng_hưởng(σ, ρ) ∈ [-1,1] — NAY là SKILL-SCORE (F.4)
            need(a,2,"cộng_hưởng"); σ,ρ=a[0],a[1]
            if σ is AN or ρ is AN: return AN
            isnum=lambda x: isinstance(x,(int,float)) and not isinstance(x,bool)
            if isnum(σ) and isnum(ρ):
                return skill_gamma(_R_scalar(σ,ρ))         # R(niềm tin) so NỀN vô-tri → đốm tối khi tệ hơn nền
            if isinstance(σ,list) and isinstance(ρ,list):  # σ/Φ là VECTOR (nhúng từ tim) → cosine → R → skill
                if len(σ)!=len(ρ) or len(σ)==0: return -1.0
                if not all(isnum(x) for x in σ) or not all(isnum(x) for x in ρ): self.err("cộng_hưởng vector cần số")
                dot=sum(x*y for x,y in zip(σ,ρ))
                na=_math.sqrt(sum(x*x for x in σ)); nb=_math.sqrt(sum(y*y for y in ρ))
                if na==0 or nb==0: return -1.0
                c=max(-1.0,min(1.0,dot/(na*nb)))
                return skill_gamma(_math.exp(c-1.0))       # cos=1→γ=1 · cos=0→γ=0 (=nền) · cos<0→γ<0
            return 1.0 if σ==ρ else -1.0
        def b_log(a):    need(a,1,"log");  x=a[0]; return AN if x is AN else _math.log(max(float(x),1e-12))
        def b_mu(a):     need(a,1,"mũ");   x=a[0]; return AN if x is AN else _math.exp(float(x))
        def b_can(a):    need(a,1,"căn");  x=a[0]; return AN if x is AN else _math.sqrt(max(float(x),0.0))
        def b_gamma_kn(a):                                # γ_kỹ_năng(R_tin, R_nền) — skill-score tường minh
            need(a,2,"γ_kỹ_năng")
            return AN if (a[0] is AN or a[1] is AN) else skill_gamma(float(a[0]), float(a[1]))
        def b_ch_tho(a):                                  # cộng_hưởng_thô(σ,ρ) = R∈(0,1] (likelihood, chưa hiệu chỉnh nền)
            need(a,2,"cộng_hưởng_thô"); σ,ρ=a[0],a[1]
            return AN if (σ is AN or ρ is AN) else _R_scalar(σ,ρ)
        def b_cam_ket(a):                                 # cam_kết(ds_độ_tán[, std0]) = e∈[0,1) (F.11)
            if not a or not isinstance(a[0],list): self.err("cam_kết cần danh sách độ-tán")
            std0 = float(a[1]) if len(a)>1 and isinstance(a[1],(int,float)) else STD0
            return commitment_e([float(s) for s in a[0]], std0)
        def b_tim(a):                                     # TRÁI TIM: LLM local sinh văn bản từ prompt
            need(a,1,"tim")
            if not isinstance(a[0],str): self.err(f"tim cần chuỗi, gặp {self._loai(a[0])}")
            import tim_llm; return tim_llm.generate(a[0])
        def b_nhung(a):                                   # σ/Φ: nhúng văn bản → vector (để tính γ)
            need(a,1,"nhúng")
            if not isinstance(a[0],str): self.err(f"nhúng cần chuỗi, gặp {self._loai(a[0])}")
            import tim_llm; return tim_llm.embed(a[0])
        def b_nhiptim(a):                                 # backend tim vừa dùng (soi minh bạch)
            need(a,0,"nhịp_tim")
            import tim_llm; return [tim_llm.backend["sinh"], tim_llm.backend["nhúng"]]
        reg={"dài":b_dai,"dai":b_dai, "đầu":b_dau,"dau":b_dau, "đuôi":b_duoi,"duoi":b_duoi,
             "thêm":b_them,"them":b_them, "ghép":b_ghep,"ghep":b_ghep,
             "gom":b_gom, "đảo":b_dao,"dao":b_dao, "nối":b_noi,"noi":b_noi, "tách":b_tach,"tach":b_tach,
             "là_ds":b_la_ds,"la_ds":b_la_ds, "là_số":b_la_so,"la_so":b_la_so,
             "rọi_ds":b_roi_ds,"roi_ds":b_roi_ds,
             "bản":b_ban,"ban":b_ban, "đặt_khoá":b_dat_khoa,"dat_khoa":b_dat_khoa,
             "lấy_khoá":b_lay_khoa,"lay_khoa":b_lay_khoa, "có_khoá":b_co_khoa,"co_khoa":b_co_khoa,
             "xoá_khoá":b_xoa_khoa,"xoa_khoa":b_xoa_khoa, "khoá":b_khoa,"khoa":b_khoa,
             "giá_trị":b_gia_tri,"gia_tri":b_gia_tri,
             "loại":b_loai,"loai":b_loai, "nguyên":b_nguyen,"nguyen":b_nguyen,
             "mã":b_ma,"ma":b_ma, "ký_tự":b_kytu,"ky_tu":b_kytu,
             "xor":b_xor, "và_bit":b_va_bit,"va_bit":b_va_bit,
             "hoặc_bit":b_hoac_bit,"hoac_bit":b_hoac_bit, "đảo_bit":b_dao_bit,"dao_bit":b_dao_bit,
             "dịch_trái":b_dich_trai,"dich_trai":b_dich_trai,
             "dịch_phải":b_dich_phai,"dich_phai":b_dich_phai,
             "cộng_hưởng":b_conghuong,"cong_huong":b_conghuong,
             "log":b_log, "mũ":b_mu,"mu":b_mu, "căn":b_can,"can":b_can,
             "γ_kỹ_năng":b_gamma_kn,"gamma_ky_nang":b_gamma_kn,
             "cộng_hưởng_thô":b_ch_tho,"cong_huong_tho":b_ch_tho,
             "cam_kết":b_cam_ket,"cam_ket":b_cam_ket,
             "tim":b_tim, "nhúng":b_nhung,"nhung":b_nhung, "nhịp_tim":b_nhiptim,"nhip_tim":b_nhiptim}
        self.glob.update(reg)

    # ============================================================
    # I/O THEO NĂNG LỰC — object-capability (host cấp; chương trình không tự nới)
    # ============================================================
    def cấp_quyền(self, tên, **phạm_vi):
        "Host trao một năng lực I/O kèm PHẠM VI. Sau đó builtin tương ứng mới TỒN TẠI."
        hợp_lệ = {"đọc_tệp","liệt_kê","chạy","ghi_tệp","giờ","phần_cứng","mmio","máy","mạng_host",
                  "ngẫu_nhiên"}
        if tên not in hợp_lệ: raise ValueError(f"quyền lạ: {tên} (chỉ: {hợp_lệ})")
        self.caps[tên] = phạm_vi
        self._cài_quyền()

    def _trong_phạm_vi(self, path, gốc):
        "True nếu path (sau realpath) nằm TRONG một thư mục gốc được cấp — chặn thoát '..'."
        rp = os.path.realpath(path)
        for g in gốc:
            rg = os.path.realpath(g)
            if rp == rg or rp.startswith(rg + os.sep): return True
        return False

    def _cài_quyền(self):
        "Cài builtin I/O — CHỈ cho năng lực đã cấp (chưa cấp ⇒ tên không tồn tại = ocap)."
        reg = {}
        if "đọc_tệp" in self.caps:
            gốc = self.caps["đọc_tệp"].get("gốc", [])
            def b_doc(a):
                if len(a)!=1 or not isinstance(a[0],str): self.err("đọc_tệp cần 1 đường dẫn chuỗi")
                if not self._trong_phạm_vi(a[0], gốc): self.err(f"đọc_tệp '{a[0]}' NGOÀI phạm vi cho phép")
                try:
                    with open(os.path.realpath(a[0]), encoding="utf-8", errors="replace") as f:
                        s = f.read(self.MAX_STR + 1)
                    if len(s) > self.MAX_STR: raise GiaoLimit("tệp quá lớn")
                    return s
                except GiaoLimit: raise
                except OSError: return AN          # đọc hỏng → ẩn (thực tại chưa phơi)
            reg.update({"đọc_tệp":b_doc, "doc_tep":b_doc})
        if "liệt_kê" in self.caps:
            gốc = self.caps["liệt_kê"].get("gốc", [])
            def b_ls(a):
                if len(a)!=1 or not isinstance(a[0],str): self.err("liệt_kê cần 1 đường dẫn chuỗi")
                if not self._trong_phạm_vi(a[0], gốc): self.err(f"liệt_kê '{a[0]}' NGOÀI phạm vi cho phép")
                try: return sorted(os.listdir(os.path.realpath(a[0])))
                except OSError: return AN
            reg.update({"liệt_kê":b_ls, "liet_ke":b_ls})
        if "chạy" in self.caps:
            cho = self.caps["chạy"].get("lệnh", []); hạn = self.caps["chạy"].get("hạn_giờ", 10)
            def b_run(a):
                import subprocess                          # nạp lười (chỉ khi quyền 'chạy' được dùng)
                if len(a) not in (1,2) or not isinstance(a[0],str): self.err("chạy cần (lệnh[, đối])")
                đối = a[1] if len(a)==2 else []
                if not isinstance(đối,list): self.err("đối của chạy phải là danh sách")
                full = " ".join([a[0]] + [self._s(x) for x in đối]).strip()
                # Khớp KHỚP-HẲN hoặc TIỀN-TỐ-tại-biên-từ (c+" "). An toàn: KHÔNG qua shell
                # (subprocess.run dạng LIST, không injection metachar) + có timeout. ⚠ Độ-hạt:
                # cấp "git" ⇒ cho MỌI `git ...` (vd `git push --force`). Host NÊN cấp chuỗi ĐẦY-ĐỦ
                # (vd "git status") để hẹp nhất; chỉ cấp tên-lệnh-trần khi thật sự muốn mở rộng.
                if not any(full==c or full.startswith(c+" ") for c in cho):
                    self.err(f"chạy '{full}' KHÔNG trong danh sách cho phép")
                try:
                    r = subprocess.run([a[0]] + [self._s(x) for x in đối],
                                       capture_output=True, text=True, timeout=hạn)
                    return r.stdout
                except (OSError, subprocess.SubprocessError): return AN   # lỗi/quá giờ → ẩn
            reg.update({"chạy":b_run, "chay":b_run})
        if "ghi_tệp" in self.caps:
            gốc = self.caps["ghi_tệp"].get("gốc", [])
            def b_ghi(a):
                if len(a)!=2 or not isinstance(a[0],str): self.err("ghi_tệp cần (đường_dẫn, nội_dung)")
                if not self._trong_phạm_vi(a[0], gốc): self.err(f"ghi_tệp '{a[0]}' NGOÀI phạm vi cho phép")
                try:
                    with open(os.path.realpath(a[0]), "w", encoding="utf-8") as f: f.write(self._s(a[1]))
                    return SANG
                except OSError: return AN
            reg.update({"ghi_tệp":b_ghi, "ghi_tep":b_ghi})
        if "giờ" in self.caps:
            import time as _t
            def b_gio(a):                                  # giờ_hệ() → epoch giây (input BẤT-ĐỊNH, chỉ qua host)
                return int(_t.time())
            reg.update({"giờ_hệ":b_gio, "gio_he":b_gio})
        if "phần_cứng" in self.caps:
            def b_phan_cung(a):                            # phần_cứng() → bản đặc-tả chip THẬT (host dò; chỉ khi cấp)
                import platform, struct                    # BA-TRỊ: khoá KHÔNG dò được → BỎ → lấy_khoá trả 'ẩn'
                m = Ban()
                try:                                           # tên chip
                    t = platform.processor() or platform.machine()
                    if t: m.d["tên"] = t
                except Exception: pass
                try: m.d["rộng_data"] = struct.calcsize("P") * 8   # bus con-trỏ (32/64)
                except Exception: pass
                try:                                           # luồng logic
                    n = os.cpu_count()
                    if n: m.d["luồng"] = n
                except Exception: pass
                ram = None                                     # RAM tổng (byte) — đa nền
                try: ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")  # Linux/macOS
                except Exception:
                    try:                                       # Windows: GlobalMemoryStatusEx
                        import ctypes
                        class _MS(ctypes.Structure):
                            _fields_ = [("dwLength",ctypes.c_ulong),("dwMemoryLoad",ctypes.c_ulong),
                                        ("ullTotalPhys",ctypes.c_ulonglong),("ullAvailPhys",ctypes.c_ulonglong),
                                        ("ullTotalPageFile",ctypes.c_ulonglong),("ullAvailPageFile",ctypes.c_ulonglong),
                                        ("ullTotalVirtual",ctypes.c_ulonglong),("ullAvailVirtual",ctypes.c_ulonglong),
                                        ("ullAvailExtendedVirtual",ctypes.c_ulonglong)]
                        s = _MS(); s.dwLength = ctypes.sizeof(_MS)
                        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)); ram = s.ullTotalPhys
                    except Exception: ram = None
                if ram: m.d["ram_gb"] = int(ram // (1024**3))
                mhz = None                                     # xung MHz — best-effort
                try:
                    with open("/proc/cpuinfo", encoding="utf-8") as f:
                        for ln in f:
                            if ln.lower().startswith("cpu mhz"): mhz = int(float(ln.split(":")[1])); break
                except Exception: pass
                if mhz is None:
                    try:
                        import winreg
                        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                        mhz = int(winreg.QueryValueEx(k, "~MHz")[0]); winreg.CloseKey(k)
                    except Exception: pass
                if mhz: m.d["xung_mhz"] = mhz
                m.d["fpga"] = TOI                              # host thường KHÔNG có đích FPGA (không đoán 'có')
                return m                                       # l2_mb: stdlib không dò được → BỎ (ẩn)
            reg.update({"phần_cứng":b_phan_cung, "phan_cung":b_phan_cung})
        if "ngẫu_nhiên" in self.caps:
            # ============================================================
            # NĂNG LỰC "NGẪU_NHIÊN" — entropy THẬT của máy chủ.
            # Vì sao là NĂNG LỰC chứ không phải hàm sẵn: ngẫu-nhiên-thật là một THIẾT BỊ (phần
            # cứng/hệ điều hành cấp), không phải phép toán. `ngẫu(seed)` của thư viện chuẩn là LCG
            # TẤT ĐỊNH — tốt cho mô phỏng, tuyệt đối KHÔNG dùng cho khoá. Tách hai thứ ra để không
            # ai lỡ tay dùng nhầm: muốn khoá thì phải XIN, và host thấy rõ mình đang cấp gì.
            # ============================================================
            import secrets as _sc
            def b_ngau_manh(a):
                "ngẫu_mạnh(n) → n byte ngẫu nhiên THẬT (dùng cho khoá; KHÔNG tất định)"
                if len(a) != 1 or not isinstance(a[0], int) or isinstance(a[0], bool):
                    self.err("ngẫu_mạnh cần SỐ byte")
                if a[0] < 1 or a[0] > 4096: self.err("ngẫu_mạnh: số byte phải trong 1..4096")
                return list(_sc.token_bytes(a[0]))
            reg.update({"ngẫu_mạnh": b_ngau_manh, "ngau_manh": b_ngau_manh})
        if "mạng_host" in self.caps:
            # ============================================================
            # NĂNG LỰC "MẠNG_HOST" — ổ cắm TCP THẬT ra ngoài máy chủ (CÒN_THIẾU B1').
            # Sandbox bẩm sinh: chưa cấp thì mấy cái tên dưới đây KHÔNG TỒN TẠI. Cấp rồi thì vẫn
            # bị kẹp trong PHẠM VI: mặc định chỉ 127.0.0.1 và chỉ những CỔNG được liệt kê.
            # Mọi ổ đều KHÔNG CHẶN (non-blocking): nhân GIAO là vòng lặp hợp tác, một lời gọi
            # đứng chờ là cả hệ điều hành đứng theo. Chưa có gì → ẩn ("chưa biết"), không phải lỗi.
            # ============================================================
            import socket as _sk
            _cổng_cho = self.caps["mạng_host"].get("cổng", [])
            _máy_cho = self.caps["mạng_host"].get("máy", ["127.0.0.1"])
            if not hasattr(self, "_ổ_host"): self._ổ_host = {}
            _ổ = self._ổ_host
            def _tay_mới(s):
                h = len(_ổ) + 1
                while h in _ổ: h += 1
                _ổ[h] = s
                return h
            def _lấy_ổ(h, ai):
                if not isinstance(h, int) or h not in _ổ: self.err(f"{ai}: tay cầm ổ lạ")
                return _ổ[h]
            def b_o_nghe(a):
                "ổ_nghe(cổng) → tay cầm · ẩn nếu cổng đang bận"
                if len(a) != 1 or not isinstance(a[0], int): self.err("ổ_nghe cần SỐ cổng")
                if _cổng_cho and a[0] not in _cổng_cho:
                    self.err(f"ổ_nghe: cổng {a[0]} NGOÀI phạm vi được cấp {_cổng_cho}")
                try:
                    s = _sk.socket(_sk.AF_INET, _sk.SOCK_STREAM)
                    s.setsockopt(_sk.SOL_SOCKET, _sk.SO_REUSEADDR, 1)
                    s.bind((_máy_cho[0], a[0])); s.listen(8); s.setblocking(False)
                    return _tay_mới(s)
                except OSError: return AN
            def b_o_nhan(a):
                "ổ_nhận(tay_nghe) → tay cầm khách mới · ẩn nếu chưa ai tới"
                if len(a) != 1: self.err("ổ_nhận cần 1 tay cầm")
                s = _lấy_ổ(a[0], "ổ_nhận")
                try:
                    kh, _ = s.accept(); kh.setblocking(False)
                    return _tay_mới(kh)
                except (BlockingIOError, OSError): return AN
            def b_o_noi(a):
                "ổ_nối(máy, cổng) → tay cầm · ẩn nếu không nối được"
                if len(a) != 2 or not isinstance(a[0], str): self.err("ổ_nối cần (máy, cổng)")
                if a[0] not in _máy_cho: self.err(f"ổ_nối: máy '{a[0]}' NGOÀI phạm vi {_máy_cho}")
                if _cổng_cho and a[1] not in _cổng_cho:
                    self.err(f"ổ_nối: cổng {a[1]} NGOÀI phạm vi {_cổng_cho}")
                try:
                    s = _sk.create_connection((a[0], a[1]), timeout=3); s.setblocking(False)
                    return _tay_mới(s)
                except OSError: return AN
            def b_o_gui(a):
                if len(a) != 2 or not isinstance(a[1], str): self.err("ổ_gửi cần (tay cầm, chuỗi)")
                s = _lấy_ổ(a[0], "ổ_gửi")
                try: s.sendall(a[1].encode("utf-8")); return SANG
                except OSError: return TOI
            def b_o_doc(a):
                """ổ_đọc(tay cầm) → [sáng, chuỗi] khi CÓ dữ liệu · ẩn khi chưa có gì · tối khi đầu kia đóng.

                Trả DANH SÁCH cho dữ liệu là cố ý: trong GIAO `sáng`/`tối` CHÍNH LÀ CHUỖI, nên nếu
                trả thẳng chuỗi thì không tài nào phân biệt được "khách gửi chữ 'tối'" với "đầu kia
                đã đóng". Bọc vào danh sách là hết nhập nhằng."""
                if len(a) != 1: self.err("ổ_đọc cần 1 tay cầm")
                s = _lấy_ổ(a[0], "ổ_đọc")
                try:
                    d = s.recv(65536)
                    if not d: return TOI
                    return [SANG, d.decode("utf-8", errors="replace")]
                except (BlockingIOError, OSError): return AN
            def b_o_dong(a):
                if len(a) != 1: self.err("ổ_đóng cần 1 tay cầm")
                s = _ổ.pop(a[0], None)
                if s is None: return AN
                try: s.close()
                except OSError: pass
                return SANG
            reg.update({"ổ_nghe":b_o_nghe, "o_nghe":b_o_nghe, "ổ_nhận":b_o_nhan, "o_nhan":b_o_nhan,
                        "ổ_nối":b_o_noi, "o_noi":b_o_noi, "ổ_gửi":b_o_gui, "o_gui":b_o_gui,
                        "ổ_đọc":b_o_doc, "o_doc":b_o_doc, "ổ_đóng":b_o_dong, "o_dong":b_o_dong})
        if "máy" in self.caps:
            # ============================================================
            # NĂNG LỰC "MÁY" — nạp BYTECODE lên GVM rồi chạy TỪNG LƯỢNG TỬ (cướp được CPU).
            # Đây KHÔNG phải cửa hậu ngôn ngữ mà là CỬA XUỐNG PHẦN CỨNG: GVM là cái máy (NAND→CPU),
            # còn GIAO chỉ xin nó "chạy hộ N lệnh rồi trả quyền về". Nhờ vậy HĐH viết bằng GIAO mới
            # TIỀN ĐỊNH được: tiến trình biên dịch xuống máy KHÔNG cần hợp tác, hết lượng tử là bị cắt.
            # Ba-trị: nguồn vượt RANH GIỚI biên dịch (closure/bản/thử-bắt…) → ẩn, không nổ.
            # ============================================================
            if not hasattr(self, "_lõi_máy"): self._lõi_máy = []
            lõi = self._lõi_máy
            def b_bien_dich(a):
                "biên_dịch(nguồn[, bit]) — bit=32 ⇒ ép chế-độ CÓ THẺ (chuỗi/danh-sách phân biệt được lúc chạy)"
                if not a or not isinstance(a[0],str): self.err("biên_dịch cần 1 chuỗi mã nguồn GIAO")
                ép = int(a[1]) if len(a)>1 and isinstance(a[1],(int,float)) and not isinstance(a[1],bool) else 0
                try:
                    import giaoc
                    if ép == 32:
                        ast = giaoc.Parser(giaoc.tokenize(a[0])).parse()
                        words, bit = giaoc.compile_program(ast, True), 32
                    else:
                        words, bit = giaoc.compile_source_bit(a[0])
                    return [int(w) for w in words] + [-bit]      # phần tử cuối = −độ_rộng_bit (16/32)
                except Exception: return AN                       # vượt ranh giới máy → ẩn (ba-trị)
            def b_may_nap(a):
                if len(a)!=1 or not isinstance(a[0],list): self.err("máy_nạp cần danh sách từ-lệnh")
                if not a[0]: self.err("máy_nạp: mã rỗng")
                import gvm_may
                mã = [int(x) for x in a[0]]; bit = 16
                if mã and mã[-1] < 0: bit = -mã[-1]; mã = mã[:-1]  # đuôi mang độ rộng bit
                g = gvm_may.GVM(mã, world={}, bit=bit)
                lõi.append({"g": g, "lệnh": 0, "xuất_đã": 0})
                return len(lõi) - 1
            def _lấy_lõi(h):
                if not isinstance(h,(int,float)) or isinstance(h,bool): self.err("tay-cầm lõi máy phải là số")
                h = int(h)
                if h < 0 or h >= len(lõi): return None
                return lõi[h]
            def b_may_lat(a):
                "máy_lát(tay_cầm, lượng_tử) → [còn_sống, số_lệnh_vừa_chạy, có_xuất]  ← CƯỚP CPU thật"
                if len(a)!=2: self.err("máy_lát cần (tay_cầm, lượng_tử)")
                c = _lấy_lõi(a[0])
                if c is None: return AN
                n = int(a[1]) if isinstance(a[1],(int,float)) and not isinstance(a[1],bool) else 0
                if n <= 0: n = 1
                g = c["g"]; g.did_out = False
                xuất_trước = len(g.xuất)          # ρ đo bằng SỐ DÒNG XUẤT tăng thêm — đúng ý "did_out"
                buf = io.StringIO()               # của silicon mà không phải sửa cái máy đã kiểm-chứng
                                                  # (opcode RỌI đặt did_out, nhưng RỌI_AUTO/CHUỖI thì không)
                try:
                    with contextlib.redirect_stdout(buf):        # RỌI của máy: gom lại, không chen màn hình
                        đã = g.run(max_steps=n)                  # ★ chạy ≤ n lệnh RỒI DỪNG (tạm dừng được)
                except Exception:
                    g.halted = True; đã = 0
                c["lệnh"] += đã
                sống = TOI if getattr(g, "halted", True) else SANG
                có_xuất = g.did_out or len(g.xuất) > xuất_trước
                bẫy = AN                                   # ★ máy có TRAP gọi-hệ đang chờ nhân?
                if getattr(g, "trap_pending", False) and g.trap is not None:
                    bẫy = [g.trap[0], list(g.trap[1])]     # [số hiệu, [đối THÔ — số hoặc con trỏ heap]]
                return [sống, đã, SANG if có_xuất else TOI, bẫy]
            def b_may_chuoi(a):
                "máy_chuỗi(lõi, con_trỏ) → chuỗi đọc từ HEAP của máy (đối kiểu chuỗi của gọi-hệ)"
                if len(a)!=2: self.err("máy_chuỗi cần (tay_cầm, con_trỏ)")
                c = _lấy_lõi(a[0])
                if c is None: return AN
                g = c["g"]; addr = int(a[1]) & 0x3FFFFFFF; out = []
                while addr != 0 and len(out) < self.MAX_STR:
                    out.append(chr(g.ram[addr] & 0x1FFFFF)); addr = g.ram[addr + 1] & 0x3FFFFFFF
                return "".join(out)
            def b_may_tra(a):
                """máy_trả(lõi, giá_trị) — NHÂN phục vụ xong: đẩy kết quả vào ngăn xếp máy rồi cho chạy tiếp.
                   số → chính nó · sáng→1 · tối→0 · ẩn→−1 · chuỗi → CẤP TRÊN HEAP của máy, đẩy con trỏ."""
                if len(a)!=2: self.err("máy_trả cần (tay_cầm, giá_trị)")
                c = _lấy_lõi(a[0])
                if c is None: return AN
                g = c["g"]; v = a[1]
                if v is AN: giá = -1
                elif isinstance(v, str) and v == SANG: giá = 1
                elif isinstance(v, str) and v == TOI: giá = 0
                elif isinstance(v, bool): giá = 1 if v else 0
                elif isinstance(v, (int, float)): giá = int(v)
                elif isinstance(v, list):
                    # DANH SÁCH (liệt/soi/ai trả về) → ghép thành MỘT CHUỖI ngăn bằng khoảng trắng.
                    # Máy chưa có kiểu "danh sách chuỗi" để in, nên nhân dọn sẵn cho gọn — trung thực
                    # về giới hạn: tiến trình máy nhận VĂN BẢN, muốn tách từ thì hỏi tiếp gọi-hệ.
                    v = " ".join(self._s(x) for x in v)
                    return b_may_tra([a[0], v])
                elif isinstance(v, str):                     # chuỗi → cấp phát cons-cell trên heap máy
                    # Quy ước giaoc: HEAP_PTR = ram[250], mỗi ô cons = [mã_ký_tự, con_trỏ_đuôi], NIL = 0.
                    # ★ Ở chế độ CÓ THẺ (32-bit), MỌI con trỏ — kể cả con trỏ ĐUÔI nằm trong ô — đều
                    #   phải mang THẺ. Thiếu thẻ ở đuôi thì chuỗi 1 ký tự vẫn đúng mà chuỗi dài thì
                    #   so sánh/duyệt sai (đã gặp: `c == "tôi"` trượt trong khi `c == "ở"` trúng).
                    THẺ = 0x40000000 if g.MASK > 0xFFFF else 0
                    hp = g.ram[250] or 300
                    con = 0
                    for ch in reversed(v[:self.MAX_STR]):
                        g.ram[hp] = ord(ch) & g.MASK; g.ram[hp + 1] = con
                        con = (hp | THẺ) & g.MASK; hp += 2
                    g.ram[250] = hp
                    giá = con
                else: giá = 0
                import gvm_may
                g.stack.append(gvm_may.KNOWN(giá & g.MASK))
                g.trap = None; g.trap_pending = False
                return SANG
            def b_may_xuat(a):
                "máy_xuất(tay_cầm) → danh sách dòng RỌI MỚI kể từ lần hỏi trước (rút cạn)"
                if len(a)!=1: self.err("máy_xuất cần (tay_cầm)")
                c = _lấy_lõi(a[0])
                if c is None: return AN
                ra = []
                for mục in c["g"].xuất[c["xuất_đã"]:]:
                    if isinstance(mục, list) and mục and mục[0] == "ô":   ra.append(str(mục[2]))
                    elif isinstance(mục, list) and mục and mục[0] == "chuỗi": ra.append(str(mục[1]))
                    elif isinstance(mục, list) and mục and mục[0] == "ds": ra.append(" ".join(str(x) for x in mục[1]))
                    else: ra.append(str(mục))
                c["xuất_đã"] = len(c["g"].xuất)
                return ra
            def b_may_anh(a):
                """máy_ảnh(lõi) → ẢNH trạng thái lõi (JSON hoá được) để CHỤP CẢ TIẾN TRÌNH MÁY.
                   Không chụp bytecode (biên dịch lại từ nguồn là ra đúng thế), chỉ chụp NGỮ CẢNH:
                   ip · các ngăn xếp · vùng RAM đã dùng (ô biến 0..299 + heap 300..HEAP_PTR)."""
                if len(a)!=1: self.err("máy_ảnh cần (tay_cầm)")
                c = _lấy_lõi(a[0])
                if c is None: return AN
                g = c["g"]
                def gói(ds): return [[x["st"], x["val"]] for x in ds]   # ngăn xếp TOÁN HẠNG = ô
                hp = max(int(g.ram[250] or 0), 300)
                # pstack là SỐ THUẦN (giá trị tham số), không phải ô — đừng gói như ngăn xếp toán hạng.
                return [g.ip, gói(g.stack), [int(x) for x in g.pstack], list(g.rstack),
                        [list(x) for x in g.fp_stack], [list(x) for x in g.handlers],
                        1 if getattr(g, "halted", False) else 0,
                        [int(x) for x in g.ram[:hp]], c["lệnh"], c["xuất_đã"],
                        1 if getattr(g, "trap_pending", False) else 0]
            def b_may_nap_anh(a):
                "máy_nạp_ảnh(mã, ảnh) → tay-cầm lõi MỚI đã khôi phục đúng ngữ cảnh (chạy tiếp được)"
                if len(a)!=2 or not isinstance(a[0],list) or not isinstance(a[1],list):
                    self.err("máy_nạp_ảnh cần (mã, ảnh)")
                h = b_may_nap([a[0]])
                c = lõi[h]; g = c["g"]; ả = a[1]
                import gvm_may
                def mở(ds): return [gvm_may.cell(int(x[0]), int(x[1]), 1.0) for x in ds]
                g.ip = int(ả[0]); g.stack = mở(ả[1]); g.pstack = [int(x) for x in ả[2]]
                g.rstack = [int(x) for x in ả[3]]
                g.fp_stack = [tuple(int(y) for y in x) for x in ả[4]]
                g.handlers = [tuple(int(y) for y in x) for x in ả[5]]
                g.halted = bool(int(ả[6]))
                for i, v in enumerate(ả[7]): g.ram[i] = int(v)
                c["lệnh"] = int(ả[8]); c["xuất_đã"] = int(ả[9])
                g.trap_pending = False; g.trap = None      # trap dở dang đã được phục vụ trước khi chụp
                return h
            def b_may_lenh(a):
                if len(a)!=1: self.err("máy_lệnh cần (tay_cầm)")
                c = _lấy_lõi(a[0])
                return AN if c is None else c["lệnh"]
            reg.update({"biên_dịch":b_bien_dich, "bien_dich":b_bien_dich,
                        "máy_nạp":b_may_nap, "may_nap":b_may_nap,
                        "máy_lát":b_may_lat, "may_lat":b_may_lat,
                        "máy_xuất":b_may_xuat, "may_xuat":b_may_xuat,
                        "máy_lệnh":b_may_lenh, "may_lenh":b_may_lenh,
                        "máy_chuỗi":b_may_chuoi, "may_chuoi":b_may_chuoi,
                        "máy_trả":b_may_tra, "may_tra":b_may_tra,
                        "máy_ảnh":b_may_anh, "may_anh":b_may_anh,
                        "máy_nạp_ảnh":b_may_nap_anh, "may_nap_anh":b_may_nap_anh})
        if "mmio" in self.caps:
            # ============================================================
            # MMIO — ĐỌC/GHI THANH GHI THIẾT BỊ (đường "xuống chip": phần mềm điều khiển phần cứng)
            # Bản đồ thiết bị = mô hình NỀN THAM CHIẾU. Trên FPGA (Pha 1) ánh xạ sang chân UART/GPIO
            # THẬT của hw/gvm.v. Ba-trị: thanh ghi lạ/chỉ-đọc-mà-ghi → ẩn (không crash). Cần cấp --cho-mmio.
            # ============================================================
            UART_TX, UART_ST, TIMER, LED = 0x00, 0x04, 0x08, 0x0C
            if not hasattr(self, "_mmio_dev"): self._mmio_dev = {"led": 0, "uart": []}
            dev = self._mmio_dev
            def b_mmio(a):
                if len(a) not in (1,2): self.err("mmio cần (địa_chỉ) để ĐỌC hoặc (địa_chỉ, giá_trị) để GHI")
                addr = a[0]
                if not isinstance(addr,(int,float)) or isinstance(addr,bool): self.err("mmio địa_chỉ cần số")
                addr = int(addr)
                if len(a) == 2:                                # ── GHI thanh ghi thiết bị ──
                    val = a[1]
                    if not isinstance(val,(int,float)) or isinstance(val,bool): return AN
                    val = int(val)
                    if addr == UART_TX:                        # cổng nối tiếp: ghi 1 byte
                        if (val & 0xFF) == 10:                 # '\n' → xả dòng UART
                            print("   UART│ " + "".join(dev["uart"])); dev["uart"] = []
                        else:
                            b = val & 0xFF; dev["uart"].append(chr(b) if 32 <= b < 127 else "·")
                        return SANG
                    if addr == LED:                            # GPIO LED: đặt trạng thái 8 bit
                        dev["led"] = val & 0xFF
                        bóng = "".join("●" if (dev["led"]>>i)&1 else "○" for i in range(7,-1,-1))
                        print(f"   LED │ {bóng}  (0x{dev['led']:02X})")
                        return SANG
                    return AN                                  # thanh ghi chỉ-đọc / lạ → bỏ (ba-trị)
                if addr == UART_ST: return 1                   # ── ĐỌC ── TX luôn sẵn sàng (mô hình)
                if addr == TIMER:   return self.steps & 0xFFFFFFFF   # bộ đếm chu-kỳ tự chạy (timer thật)
                if addr == LED:     return dev["led"]
                return AN
            reg.update({"mmio":b_mmio})
        self.glob.update(reg)

# ============================================================
# 5. ĐIỂM VÀO
# ============================================================
def run(src):
    rt=Runtime(); rt.exec_block(Parser(tokenize(src)).parse()); return rt

def chạy_chuỗi(src, chuẩn=True):
    "Chạy nguồn GIAO → trả TOÀN BỘ đầu ra (kèm lỗi đã gói) dạng text. Cho playground/nhúng."
    import io, contextlib
    sys.setrecursionlimit(40000)
    rt = Runtime()
    try: rt.base_dir = os.getcwd()
    except Exception: pass
    if chuẩn: nạp_chuẩn(rt)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rt.exec_block(Parser(tokenize(src)).parse())
    except GiaoSyntax as e:
        buf.write(f"\n[cú pháp] (dòng {e.line}, cột {e.col}) {e.msg}{khung_lỗi(src,e.line,e.col)}\n")
    except SyntaxError as e:
        buf.write(f"\n[cú pháp] {e}\n")
    except GiaoError as e:
        buf.write(f"\n[lỗi] (dòng {e.line}, cột {e.col}) {e.msg}{khung_lỗi(src,e.line,e.col)}\n")
    except GiaoLimit as e:
        buf.write(f"\n[chặn — an toàn] {e.msg}\n")
    except RecursionError:
        buf.write("\n[chặn — an toàn] đệ quy quá sâu\n")
    except (ReturnSignal, DungSignal):
        buf.write("\n[lỗi] 'trả'/'dừng' nằm ngoài ngữ cảnh\n")
    return buf.getvalue()

def nạp_chuẩn(rt):
    "Nạp thư viện chuẩn (prelude) viết bằng GIAO, nếu có."
    lib=os.path.join(os.path.dirname(os.path.abspath(__file__)), "chuẩn.giao")
    if os.path.exists(lib):
        saved=rt.tệp_hiện; rt.tệp_hiện="chuẩn.giao"   # nhãn prelude (ghi-đè sau = chủ-ý, không cảnh-báo)
        try:
            with open(lib, encoding="utf-8") as f:
                rt.exec_block(Parser(tokenize(f.read())).parse())
        finally: rt.tệp_hiện=saved

def _phân_tích_cờ(argv):
    "Tách tệp nguồn + các cờ CẤP QUYỀN I/O. Không cờ ⇒ không quyền ⇒ sandbox tuyệt đối."
    tệp=None; đọc=[]; chạy=[]; ghi=[]; giờ=[False]; pc=[False]; mmio=[False]; máy_cờ=[False]; bước=[None]
    mạng=[]; i=0
    while i < len(argv):
        a=argv[i]
        # --cho-mạng <cổng>: cấp năng lực ổ cắm TCP THẬT, CHỈ trên 127.0.0.1 và CHỈ cổng ấy
        if a in ("--cho-ngẫu","--cho-ngau"): mạng.append(-1); i+=1; continue   # cờ riêng, xử dưới
        if a in ("--cho-mạng","--cho-mang") and i+1<len(argv):
            try: mạng.append(int(argv[i+1]))
            except ValueError: pass
            i+=2; continue
        if a in ("--cho-đọc","--cho-doc") and i+1<len(argv): đọc.append(argv[i+1]); i+=2
        elif a in ("--cho-chạy","--cho-chay") and i+1<len(argv): chạy.append(argv[i+1]); i+=2
        elif a in ("--cho-ghi",) and i+1<len(argv): ghi.append(argv[i+1]); i+=2
        elif a in ("--cho-giờ","--cho-gio"): giờ[0]=True; i+=1
        elif a in ("--cho-phần-cứng","--cho-phan-cung"): pc[0]=True; i+=1
        elif a in ("--cho-mmio",): mmio[0]=True; i+=1
        elif a in ("--cho-máy","--cho-may"): máy_cờ[0]=True; i+=1
        # --bước N: NỚI trần số bước (mặc định 5 triệu). Chương trình lớn thật (vd HĐH-GIAO) chạm
        # trần một cách CHÍNH ĐÁNG; host phải nới TƯỜNG MINH, chứ mặc định vẫn chặn (chống DoS).
        elif a in ("--bước","--buoc") and i+1<len(argv):
            try: bước[0]=int(argv[i+1])
            except ValueError: pass
            i+=2
        elif a.startswith("--bước=") or a.startswith("--buoc="):
            try: bước[0]=int(a.split("=",1)[1])
            except ValueError: pass
            i+=1
        elif tệp is None and not a.startswith("--"): tệp=a; i+=1
        else: i+=1
    return tệp, đọc, chạy, ghi, giờ[0], pc[0], mmio[0], máy_cờ[0], bước[0], mạng

def khung_lỗi(src, line, col):
    "Dòng nguồn + dấu ^ tại cột (như compiler hiện đại). '' nếu thiếu thông tin."
    if not src or not line: return ""
    dòng = src.splitlines()
    if line < 1 or line > len(dòng): return ""
    return f"\n   {dòng[line-1]}\n   {' ' * ((col or 1) - 1)}^"

def repl(đọc=(), chạy=(), ghi=()):
    "Vòng ĐỌC–TÍNH–IN (REPL). Trạng thái bền qua các dòng; biểu thức cuối → in giá trị."
    sys.setrecursionlimit(40000)
    rt=Runtime(); rt.base_dir=os.getcwd(); nạp_chuẩn(rt)
    if đọc: rt.cấp_quyền("đọc_tệp", gốc=list(đọc)); rt.cấp_quyền("liệt_kê", gốc=list(đọc))
    if chạy: rt.cấp_quyền("chạy", lệnh=list(chạy))
    if ghi: rt.cấp_quyền("ghi_tệp", gốc=list(ghi))
    print("GIAO — vòng tương tác (REPL). Gõ `.trợ_giúp`, thoát bằng `.thoát` hoặc Ctrl-Z↵.")
    buf=""
    while True:
        try: line=input("  ... " if buf else "giao> ")
        except EOFError: print(); break
        except KeyboardInterrupt: print("^C"); buf=""; continue
        if not buf:
            cmd=line.strip()
            if cmd in (".thoát",".thoat",".q"): break
            if cmd in (".trợ_giúp",".tro_giup",".help","?"):
                print("  • Gõ biểu thức → in giá trị (vd  1+2 ,  bản_đồ(hàm(x){trả x*2},[1,2,3]) )")
                print("  • Câu lệnh chạy bình thường (đặt/hàm/vật/tâm/học/giao/rọi/lặp/nếu…)")
                print("  • Khối nhiều dòng: mở `{` → tự xuống dòng `...` tới khi cân ngoặc")
                print("  • Trạng thái GIỮ qua các dòng. Thoát: .thoát / Ctrl-Z↵"); continue
        buf += line+"\n"
        try: toks=tokenize(buf)
        except GiaoSyntax as e: print(f"[cú pháp] (cột {e.col}) {e.msg}{khung_lỗi(buf,e.line,e.col)}"); buf=""; continue
        except SyntaxError as e: print(f"[cú pháp] {e}"); buf=""; continue
        depth=sum(1 for t in toks if t.kind=="OP" and t.val in "{([") \
             - sum(1 for t in toks if t.kind=="OP" and t.val in "})]")
        if depth>0: continue                       # ngoặc chưa cân → đọc tiếp (đa dòng)
        src=buf; buf=""
        try:
            stmts=Parser(toks).parse()
            if stmts and type(stmts[-1]) is ExprStmt:
                for s in stmts[:-1]: rt.exec(s)
                val=rt.eval(stmts[-1].expr)
                if val is not AN: print(rt.render(val))
            else:
                rt.exec_block(stmts)
        except GiaoSyntax as e:
            print(f"[cú pháp] (cột {e.col}) {e.msg}{khung_lỗi(src,e.line,e.col)}")
        except SyntaxError as e: print(f"[cú pháp] {e}")
        except GiaoError as e:
            print(f"[lỗi]{f' (dòng {e.line}, cột {e.col})' if e.line else ''} {e.msg}{khung_lỗi(src,e.line,e.col)}")
        except GiaoLimit as e: print(f"[chặn — an toàn] {e.msg}")
        except ReturnSignal: print("[lỗi] 'trả' nằm ngoài hàm")
        except DungSignal: print("[lỗi] 'dừng' nằm ngoài vòng lặp")
        except RecursionError: print("[chặn — an toàn] đệ quy quá sâu")

def main():
    sys.setrecursionlimit(40000)             # để giới hạn đệ quy của GIAO bắt trước
    tệp, đọc, chạy, ghi, giờ, pc, mmio, máy_cờ, bước, mạng = _phân_tích_cờ(sys.argv[1:])
    if tệp is None:
        repl(đọc, chạy, ghi); return         # KHÔNG tham số tệp → vào REPL
    with open(tệp, encoding="utf-8") as f: src=f.read()
    try:
        rt=Runtime(); rt.base_dir=os.path.dirname(os.path.abspath(tệp))   # gốc cho `nhập`
        if bước: rt.MAX_STEPS = bước                     # host nới trần bước (tường minh)
        nạp_chuẩn(rt)                        # thư viện chuẩn sẵn dùng cho mọi chương trình
        if đọc: rt.cấp_quyền("đọc_tệp", gốc=đọc); rt.cấp_quyền("liệt_kê", gốc=đọc)
        if chạy: rt.cấp_quyền("chạy", lệnh=chạy)
        if ghi: rt.cấp_quyền("ghi_tệp", gốc=ghi)
        if giờ: rt.cấp_quyền("giờ")          # đồng-hồ host (input bất-định, chỉ khi cấp)
        if pc: rt.cấp_quyền("phần_cứng")     # dò chip THẬT (capability — sandbox bẩm sinh: chưa cấp ⇒ không tồn tại)
        if mmio: rt.cấp_quyền("mmio")
        if -1 in mạng: rt.cấp_quyền("ngẫu_nhiên")          # entropy THẬT (cho khoá phiên)
        _cổng = [c for c in mạng if c != -1]
        if _cổng: rt.cấp_quyền("mạng_host", cổng=_cổng, máy=["127.0.0.1"])   # ổ TCP thật, kẹp cổng
        if máy_cờ: rt.cấp_quyền("máy")   # nạp bytecode lên GVM + cướp CPU theo lượng tử        # MMIO thanh-ghi thiết bị (đường xuống chip; chưa cấp ⇒ không tồn tại)
        rt.tệp_hiện=os.path.basename(tệp)    # nhãn tệp chính (cho cảnh-báo va-tên)
        rt.exec_block(Parser(tokenize(src)).parse())
    except GiaoSyntax as e:
        loc=f" (dòng {e.line}, cột {e.col})" if e.line else ""
        print(f"[GIAO cú pháp]{loc} {e.msg}{khung_lỗi(src,e.line,e.col)}", file=sys.stderr); sys.exit(1)
    except SyntaxError as e:
        print(f"[GIAO cú pháp] {e}", file=sys.stderr); sys.exit(1)
    except GiaoError as e:
        loc=f" (dòng {e.line}, cột {e.col})" if e.line else ""
        print(f"[GIAO lỗi]{loc} {e.msg}{khung_lỗi(src,e.line,e.col)}", file=sys.stderr); sys.exit(1)
    except GiaoLimit as e:
        print(f"[GIAO chặn — an toàn] {e.msg}", file=sys.stderr); sys.exit(1)
    except RecursionError:
        print("[GIAO chặn — an toàn] đệ quy quá sâu", file=sys.stderr); sys.exit(1)
    except ReturnSignal:
        print("[GIAO lỗi] 'trả' nằm ngoài hàm", file=sys.stderr); sys.exit(1)
    except DungSignal:
        print("[GIAO lỗi] 'dừng' nằm ngoài vòng lặp", file=sys.stderr); sys.exit(1)

if __name__=="__main__": main()

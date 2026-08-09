# -*- coding: utf-8 -*-
"""
GIAO CẦU NỐI — sidecar suy luận CDFL nói JSON qua stdio (JSON Lines).
================================================================================
Mục tiêu: CẮM GIAO VÀO DỰ ÁN BẤT KỲ NGÔN NGỮ NÀO, KHÔNG conflict.
  • Mọi ngôn ngữ đều sinh/đọc được JSON ⇒ không cần link, không dependency chung.
  • GIAO chạy như TIẾN TRÌNH RIÊNG (sandbox: không I/O, không global của host) ⇒
    không thể tranh tài nguyên với host. Nó chỉ QUAN SÁT và CỐ VẤN.
  • LOGIC suy luận (cộng hưởng γ, vùng tối DE, cổng phê duyệt) nằm trong GIAO/runtime;
    Python ở đây CHỈ là vỏ: đọc JSON → gọi runtime GIAO → trả JSON.

GIAO THỨC (mỗi dòng stdin = 1 yêu cầu JSON; mỗi dòng stdout = 1 đáp JSON):
  {"id":1,"op":"vật","tên":"đĩa","giá_trị":80}        # host phơi thực tại  (ρ_MF)
  {"id":2,"op":"tâm","tên":"đĩa","giá_trị":50}        # ta tin (σ); "ẩn" = chưa biết
  {"id":3,"op":"học","tên":"đĩa"}                     # kéo niềm tin về thực tại
  {"id":4,"op":"giao","tên":"đĩa"}                    # → {giá_trị, gamma, trạng_thái}
  {"id":5,"op":"de"}                                  # → DE bốn mặt (cấu trúc)
  {"id":6,"op":"chọn","hành_động":[["A",40,100],["B",90,100]]}   # → hành động OR lớn nhất
  {"id":7,"op":"phê_duyệt","gamma":0.4,"bất_khả_hồi":true,"ngưỡng":0.7}  # cổng an toàn
  {"id":8,"op":"trạng_thái"}                          # → dump tâm/vật hiện thời
  {"id":9,"op":"trôi","tên":"đĩa","luật":"(vật đĩa)+5"}  # đăng ký+chạy một nhịp trôi
Đáp: {"id":N,"ok":true, ...}  hoặc  {"id":N,"ok":false,"lỗi":"..."}

Chạy thử nhanh (pipe JSONL vào — gọi được từ shell/Go/JS/Rust... y hệt):
  printf '%s\n' '{"op":"vật","tên":"đĩa","giá_trị":100}' '{"op":"tâm","tên":"đĩa","giá_trị":100}' '{"op":"giao","tên":"đĩa"}' | python giao_cau_noi.py
"""
import sys, os, json, re
from giao import (tokenize, Parser, Runtime, Tri, AN, SANG, TOI,
                  GiaoError, GiaoLimit, nạp_chuẩn)

_IDENT = re.compile(r"^[^\W\d]\w*$", re.UNICODE)   # định danh GIAO hợp lệ (chống chèn mã)

class CầuNối:
    def __init__(self):
        self.rt = Runtime()
        nạp_chuẩn(self.rt)                          # thư viện chuẩn (chọn, cộng_hưởng...)
        lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cau_noi.giao")
        with open(lib, encoding="utf-8") as f:      # lõi suy luận viết bằng GIAO
            self.rt.exec_block(Parser(tokenize(f.read())).parse())
        self._cấp_từ_env()                          # QUYỀN I/O do HOST cấu hình (mặc định: KHÔNG)

    def _cấp_từ_env(self):
        "Cấp năng lực I/O theo biến môi trường — HOST quyết GIAO được chạm gì (mặc định rỗng)."
        đọc = [p for p in os.environ.get("GIAO_CHO_DOC", "").split(os.pathsep) if p]
        chạy = [c for c in os.environ.get("GIAO_CHO_CHAY", "").split("|") if c.strip()]
        ghi  = [p for p in os.environ.get("GIAO_CHO_GHI", "").split(os.pathsep) if p]
        if đọc: self.rt.cấp_quyền("đọc_tệp", gốc=đọc); self.rt.cấp_quyền("liệt_kê", gốc=đọc)
        if chạy: self.rt.cấp_quyền("chạy", lệnh=[c.strip() for c in chạy])
        if ghi: self.rt.cấp_quyền("ghi_tệp", gốc=ghi)

    # ---- tiện ích ----
    def _ident(self, s):
        if not isinstance(s, str) or not _IDENT.match(s):
            raise ValueError(f"tên không hợp lệ: {s!r}")
        return s
    def _lit(self, v):                              # giá trị JSON → literal GIAO an toàn
        if v is None or v == "ẩn": return "ẩn"
        if isinstance(v, bool): return SANG if v else TOI
        if isinstance(v, (int, float)): return repr(v)
        if isinstance(v, str): return '"' + v.replace("\\","\\\\").replace('"','\\"') + '"'
        if isinstance(v, list): return "[" + ", ".join(self._lit(x) for x in v) + "]"
        raise ValueError(f"giá trị không hỗ trợ: {v!r}")
    def _py(self, v):                               # giá trị GIAO → JSON
        if v is AN: return None
        if isinstance(v, Tri):
            return {"giá_trị": self._py(v.value), "gamma": v.gamma, "trạng_thái": v.state}
        if isinstance(v, list): return [self._py(x) for x in v]
        return v
    def _exec(self, src): self.rt.exec_block(Parser(tokenize(src)).parse())
    def _eval(self, expr):                          # tính một biểu thức GIAO, lấy trị Python
        self._exec(f"đặt __kq = ({expr})")
        return self._py(self.rt.glob.get("__kq"))

    # ---- xử lý một yêu cầu ----
    def xử_lý(self, req):
        op = req.get("op")
        if op == "vật":
            self._exec(f"vật {self._ident(req['tên'])} = {self._lit(req['giá_trị'])}")
            return {"ghi": "vật", "tên": req["tên"]}
        if op == "tâm":
            self._exec(f"tâm {self._ident(req['tên'])} = {self._lit(req['giá_trị'])}")
            return {"ghi": "tâm", "tên": req["tên"]}
        if op == "học":
            self._exec(f"học {self._ident(req['tên'])}")
            return {"học": req["tên"], "tâm": self._py(self.rt.tam.get(req["tên"], AN))}
        if op == "giao":
            t = self._ident(req["tên"]); self._exec(f"giao __t = {t}")
            return self._py(self.rt.glob["__t"])
        if op == "de":
            return self.rt.de_cau_truc()
        if op == "chọn":
            hd = req["hành_động"]                     # [[tên,σ_dự_đoán,ρ_kỳ_vọng],...]
            chosen = self._eval(f"chọn({self._lit(hd)})")    # argmax γ (chuẩn.giao)
            γ = None
            if isinstance(chosen, list) and len(chosen) >= 3:
                γ = self._eval(f"cộng_hưởng({self._lit(chosen[1])}, {self._lit(chosen[2])})")
            return {"chọn": chosen, "gamma": γ}
        if op == "phê_duyệt":
            γ = req.get("gamma", 0.0); bkh = bool(req.get("bất_khả_hồi", False))
            ng = req.get("ngưỡng", 0.5)
            kq = self._eval(f"phê_duyệt({repr(float(γ))}, {SANG if bkh else TOI}, {repr(float(ng))})")
            phán = {"sáng": "cho_phép", "tối": "chặn", None: "cân_nhắc"}[kq]
            return {"phán": phán, "ba_trị": kq if kq else "ẩn", "γ": γ, "ngưỡng": ng, "bất_khả_hồi": bkh}
        if op == "trạng_thái":
            return {"tâm": {k: self._py(v) for k, v in self.rt.tam.items()},
                    "vật": {k: self._py(v) for k, v in self.rt.vat.items()}}
        if op == "trôi":
            t = self._ident(req["tên"])
            self._exec(f"trôi {t} = {req['luật']}\ntrôi")   # đăng ký luật + một nhịp
            return {"trôi": t, "vật": self._py(self.rt.vat.get(t, AN))}
        # --- I/O THEO NĂNG LỰC (chỉ chạy nếu HOST đã cấp qua env; chưa cấp → lỗi sạch) ---
        if op == "đọc_tệp":
            return {"nội_dung": self._eval(f"đọc_tệp({self._lit(req['đường_dẫn'])})")}
        if op == "liệt_kê":
            return {"mục": self._eval(f"liệt_kê({self._lit(req['đường_dẫn'])})")}
        if op == "chạy":
            return {"ra": self._eval(f"chạy({self._lit(req['lệnh'])}, {self._lit(req.get('đối', []))})")}
        raise ValueError(f"op lạ: {op!r}")

def main():
    cn = CầuNối()
    # báo sẵn sàng (host có thể chờ dòng này)
    print(json.dumps({"sẵn_sàng": True, "giao_thức": "giao-cau-noi/1",
                      "op": ["vật","tâm","học","giao","de","chọn","phê_duyệt","trạng_thái","trôi"]},
                     ensure_ascii=False), flush=True)
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        rid = None
        try:
            req = json.loads(line); rid = req.get("id")
            kết = cn.xử_lý(req); out = {"id": rid, "ok": True}; out.update(kết)
        except (GiaoError,) as e:
            out = {"id": rid, "ok": False, "lỗi": f"GIAO: {e.msg}"}
        except (GiaoLimit,) as e:
            out = {"id": rid, "ok": False, "lỗi": f"GIAO chặn (an toàn): {e.msg}"}
        except Exception as e:
            out = {"id": rid, "ok": False, "lỗi": f"{type(e).__name__}: {e}"}
        print(json.dumps(out, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()

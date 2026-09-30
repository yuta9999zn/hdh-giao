# -*- coding: utf-8 -*-
"""
SỔ NIÊM PHONG DỰ ĐOÁN — mọi đề xuất của AI/LLM phải kèm một DỰ ĐOÁN, được NIÊM PHONG (băm) TRƯỚC khi
làm, rồi CHẤM sau khi biết kết quả. (Học từ D:\\KIAI\\con-thuyen: "dự đoán niêm phong, chấm sau, so
với đường nền" — thay cho việc tin γ như một cổng.)

  · Sổ là JSONL chỉ-ghi-thêm, mỗi mục mang `băm_trước` = băm mục ngay trước ⇒ CHUỖI BĂM: sửa, xoá
    hay chèn lén bất kỳ mục nào cũng làm `kiểm_chuỗi()` báo đứt.
  · Dự đoán niêm phong TRƯỚC ⇒ không thể "đoán sau khi đã biết". Chấm trỏ tới băm niêm phong.
  · Thống kê so với ĐƯỜNG NỀN (đoán theo tỉ lệ nền của chính kết quả) — "trúng 90%" vô nghĩa nếu
    90% việc vốn thành công sẵn.
  · γ ở đây chỉ là thước HIỆU CHỈNH SAU SỰ VIỆC, KHÔNG dùng để cho phép việc bất khả hồi.

Dùng (Python):  sổ = SổNiêmPhong(đường_dẫn)
                b = sổ.niêm_phong("llm:claude", "vá lib_x.giao", {"đích_sáng": True, "hồi_quy": 0})
                … làm việc …
                sổ.chấm(b, {"đích_sáng": True, "hồi_quy": 0})
                sổ.kiểm_chuỗi(); sổ.thống_kê()
Dòng lệnh:      python niem_phong.py [sổ.jsonl]   → kiểm chuỗi + thống kê
Mặc định sổ ở __pycache__/so_niem_phong.jsonl (đổi bằng biến môi trường GIAO_SO_NIEM_PHONG).
"""
import os, sys, json, hashlib, time

P = os.path.dirname(os.path.abspath(__file__))
MẶC_ĐỊNH = os.environ.get("GIAO_SO_NIEM_PHONG") or os.path.join(P, "__pycache__", "so_niem_phong.jsonl")
GỐC = "0" * 64

def _băm(mục):
    "SHA-256 của mục (không kể 'băm' và 'ký'), JSON chuẩn tắc (khoá sắp xếp, không khoảng trắng thừa)."
    d = {k: v for k, v in mục.items() if k not in ("băm", "ký")}
    return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

# ---------------- KÝ KÉP ML-DSA-65 + Ed25519 (v0.40, lộ trình GĐ2) ----------------
# Chuỗi băm phát hiện SỬA nhưng không chứng minh AI VIẾT: ai có quyền ghi tệp đều dựng lại được cả chuỗi.
# Nay mỗi mục mới được KÝ KÉP trên `băm` của nó (băm đã nối cả chuỗi phía trước): ML-DSA-65 (mldsa-native, FIPS
# 204) và Ed25519 (Monocypher, RFC 8032), mã vendor nguyên văn → WASM (ky_kep.py). Mục chỉ HỢP LỆ khi CẢ
# HAI chữ ký đúng. Khoá sinh từ os.urandom lần đầu dùng, nằm ở .khoa/niem_phong/ (không commit).
KHOÁ_MẶC_ĐỊNH = os.environ.get("GIAO_KHOA_NIEM_PHONG") or os.path.join(P, ".khoa", "niem_phong")
TIỀN_TỐ_KÝ = b"GIAO-NIEM-PHONG-v1\x00"

def _thông_điệp_ký(băm): return TIỀN_TỐ_KÝ + bytes.fromhex(băm)
def vân_tay_đủ(pk_ed, pk_ml): return hashlib.sha256(b"GIAO-KHOA-v1" + pk_ed + pk_ml).hexdigest()
def vân_tay(pk_ed, pk_ml): return vân_tay_đủ(pk_ed, pk_ml)[:32]

# GHIM KHOÁ (v0.41): khoá công khai tin cậy KHÔNG được chỉ nằm cạnh khoá (.khoa/) — kẻ ghi được thư mục ấy
# thay được cả khoá. Vân tay ĐỦ 256 bit được COMMIT vào kho (khoa_niem_phong.ghim): lịch sử git là nhân chứng
# độc lập. Có ghim ⇒ khoá nạp lên phải khớp; mất thư mục khoá thì KHÔNG tự tạo khoá mới (máy mới / khôi
# phục: chạy `python niem_phong.py --ghim-khoa` rồi commit — một thay đổi AI CŨNG THẤY trong git).
GHIM_KHOÁ = os.environ.get("GIAO_GHIM_KHOA_NIEM_PHONG") or os.path.join(P, "khoa_niem_phong.ghim")
class KhoáLệchGhim(RuntimeError): pass
def đọc_ghim_khoá(tệp=None):
    tệp = tệp or GHIM_KHOÁ
    if not os.path.exists(tệp): return None
    return json.load(open(tệp, encoding="utf-8"))["vân_tay_đủ"]

class KhoáSổ:
    "Cặp khoá ký kép của sổ. bi_mat.json = (ξ ML-DSA, hạt Ed25519); cong_khai.json = khoá công khai + vân tay."
    def __init__(self, thư_mục=KHOÁ_MẶC_ĐỊNH, tạo=True, ghim="mặc_định"):
        "ghim: 'mặc_định' ⇒ GHIM_KHOÁ nếu tệp ấy có · None ⇒ không kiểm ghim · đường dẫn ⇒ tệp ghim ấy."
        import ky_kep as K
        self.K = K; self.thư_mục = thư_mục
        vt_ghim = đọc_ghim_khoá(None if ghim == "mặc_định" else ghim) if ghim is not None else None
        bí, công = os.path.join(thư_mục, "bi_mat.json"), os.path.join(thư_mục, "cong_khai.json")
        if not os.path.exists(bí):
            if vt_ghim is not None:
                raise KhoáLệchGhim(f"có ghim khoá ({vt_ghim[:16]}…) nhưng KHÔNG có khoá ở {thư_mục} — không tự tạo khoá mới. "
                                   "Khôi phục thư mục khoá, hoặc (máy mới) chạy: python niem_phong.py --ghim-khoa rồi commit.")
            if not tạo: raise FileNotFoundError(bí)
            os.makedirs(thư_mục, exist_ok=True)
            ξ, hạt = os.urandom(32), os.urandom(32)
            pk_ml, _ = K.mldsa_khoá(ξ); pk_ed = K.ed_khoá(hạt)
            fd = os.open(bí, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f: json.dump({"mldsa_xi": ξ.hex(), "ed_hat": hạt.hex()}, f)
            with open(công, "w", encoding="utf-8") as f:
                json.dump({"ed25519": pk_ed.hex(), "mldsa65": pk_ml.hex(), "vân_tay": vân_tay(pk_ed, pk_ml)}, f)
        d = json.load(open(bí, encoding="utf-8")); c = json.load(open(công, encoding="utf-8"))
        self._ξ, self._hạt = bytes.fromhex(d["mldsa_xi"]), bytes.fromhex(d["ed_hat"])
        # dựng LẠI khoá công khai từ khoá bí mật: cong_khai.json bị tráo (hoặc lệch bi_mat) là lộ ngay
        pk_ml, _ = K.mldsa_khoá(self._ξ); pk_ed = K.ed_khoá(self._hạt)
        if (pk_ed.hex(), pk_ml.hex()) != (c["ed25519"], c["mldsa65"]):
            raise KhoáLệchGhim(f"{công} KHÔNG khớp khoá bí mật trong {bí} (bị tráo?)")
        self.vân_tay_đủ = vân_tay_đủ(pk_ed, pk_ml)
        if vt_ghim is not None and self.vân_tay_đủ != vt_ghim:
            raise KhoáLệchGhim(f"khoá ở {thư_mục} (vân tay {self.vân_tay_đủ[:16]}…) KHÁC ghim {vt_ghim[:16]}… — từ chối ký/kiểm")
        self.công = {"ed25519": c["ed25519"], "mldsa65": c["mldsa65"], "vân_tay": vân_tay(pk_ed, pk_ml)}
    def ký(self, băm):
        ed, ml = self.K.ký_kép(self._ξ, self._hạt, _thông_điệp_ký(băm))
        return {"vân_tay": self.công["vân_tay"], "ed25519": ed.hex(), "mldsa65": ml.hex()}

def _có_thể_ký():
    if os.environ.get("GIAO_NIEM_PHONG_KY", "1") == "0": return False
    try:
        from vo_gvm64 import WASMTIME
        return os.path.exists(os.path.join(P, "wasm", "ky_lenh.wasm")) and bool(WASMTIME) and os.path.exists(WASMTIME)
    except Exception: return False

class SổNiêmPhong:
    def __init__(self, đường_dẫn=MẶC_ĐỊNH, ký=None, khoá=None):
        "ký=None ⇒ tự ký nếu có ky_lenh.wasm + wasmtime (tắt: GIAO_NIEM_PHONG_KY=0). khoá = KhoáSổ hoặc thư mục."
        self.đường_dẫn = đường_dẫn
        os.makedirs(os.path.dirname(os.path.abspath(đường_dẫn)), exist_ok=True)
        if ký is None: ký = _có_thể_ký()
        self.khoá = (khoá if isinstance(khoá, KhoáSổ) else KhoáSổ(khoá or KHOÁ_MẶC_ĐỊNH)) if ký else None

    def đọc(self):
        if not os.path.exists(self.đường_dẫn): return []
        with open(self.đường_dẫn, encoding="utf-8") as f:
            return [json.loads(d) for d in f if d.strip()]

    def _ghi(self, mục):
        ds = self.đọc()
        mục["số"] = len(ds); mục["băm_trước"] = ds[-1]["băm"] if ds else GỐC
        mục["lúc"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        mục["băm"] = _băm(mục)
        if self.khoá is not None: mục["ký"] = self.khoá.ký(mục["băm"])
        with open(self.đường_dẫn, "a", encoding="utf-8") as f:
            f.write(json.dumps(mục, ensure_ascii=False, sort_keys=True) + "\n")
        return mục["băm"]

    def niêm_phong(self, ai, việc, dự_đoán):
        "Ghi dự đoán TRƯỚC khi làm. Trả băm niêm phong (dùng để chấm sau)."
        if not isinstance(dự_đoán, dict) or not dự_đoán: raise ValueError("dự đoán phải là bản {khoá: giá_trị} không rỗng")
        return self._ghi({"loại": "niêm_phong", "ai": str(ai), "việc": str(việc), "dự_đoán": dự_đoán})

    def chấm(self, băm_niêm, kết_quả):
        "Ghi kết quả thật cho một niêm phong. trúng = MỌI khoá đã dự đoán đều khớp kết quả."
        ds = self.đọc()
        niêm = next((m for m in ds if m.get("loại") == "niêm_phong" and m["băm"] == băm_niêm), None)
        if niêm is None: raise ValueError(f"không có niêm phong {băm_niêm[:12]}… trong sổ")
        if any(m.get("loại") == "chấm" and m.get("niêm") == băm_niêm for m in ds):
            raise ValueError("niêm phong này ĐÃ được chấm — không chấm lại (chống sửa điểm)")
        lệch = {k: {"đoán": v, "thật": kết_quả.get(k, None)} for k, v in niêm["dự_đoán"].items() if kết_quả.get(k, None) != v}
        trúng = not lệch
        self._ghi({"loại": "chấm", "niêm": băm_niêm, "kết_quả": kết_quả, "trúng": trúng, "lệch": lệch})
        return {"trúng": trúng, "lệch": lệch}

    def kiểm_chuỗi(self, khoá_công=None, bắt_buộc_ký=False):
        """Kiểm toàn vẹn: mỗi mục băm đúng + nối đúng mục trước + chấm trỏ tới niêm phong CÓ TRƯỚC; và KÝ KÉP:
        mục có chữ ký phải đúng CẢ Ed25519 LẪN ML-DSA-65 theo khoá công khai (mặc định: khoá của sổ này);
        từ mục ký đầu tiên trở đi, mục nào THIẾU chữ ký là lỗi (chống gỡ chữ ký). bắt_buộc_ký=True: MỌI mục
        phải có chữ ký (sổ mới — chống gỡ SẠCH mọi chữ ký, trường hợp mà quy tắc trên không bắt được)."""
        khoá_công = khoá_công or (self.khoá.công if self.khoá is not None else None)
        trước = GỐC; đã_niêm = set(); đã_ký = False; K = None
        for i, m in enumerate(self.đọc()):
            if m.get("số") != i: return False, f"mục {i}: số thứ tự sai ({m.get('số')}) — có mục bị xoá/chèn"
            if m.get("băm_trước") != trước: return False, f"mục {i}: đứt chuỗi (băm_trước không khớp)"
            if _băm(m) != m.get("băm"): return False, f"mục {i}: nội dung bị SỬA (băm không khớp)"
            if "ký" in m:
                if khoá_công is None: return False, f"mục {i}: có chữ ký nhưng không có khoá công khai để kiểm"
                k = m["ký"]
                if k.get("vân_tay") != khoá_công["vân_tay"]: return False, f"mục {i}: ký bằng KHOÁ LẠ (vân tay {str(k.get('vân_tay'))[:12]}…)"
                if K is None: import ky_kep as K
                try:
                    ok_ed, ok_ml = K.kiểm_kép(bytes.fromhex(khoá_công["ed25519"]), bytes.fromhex(khoá_công["mldsa65"]),
                                              _thông_điệp_ký(m["băm"]), bytes.fromhex(k["ed25519"]), bytes.fromhex(k["mldsa65"]))
                except (ValueError, K.LỗiKý): ok_ed = ok_ml = False
                if not ok_ed: return False, f"mục {i}: chữ ký Ed25519 SAI"
                if not ok_ml: return False, f"mục {i}: chữ ký ML-DSA-65 SAI"
                đã_ký = True
            elif đã_ký: return False, f"mục {i}: THIẾU chữ ký sau mục đã ký (chữ ký bị gỡ?)"
            elif bắt_buộc_ký: return False, f"mục {i}: THIẾU chữ ký (sổ bắt buộc ký)"
            if m.get("loại") == "niêm_phong": đã_niêm.add(m["băm"])
            elif m.get("loại") == "chấm" and m.get("niêm") not in đã_niêm:
                return False, f"mục {i}: chấm một niêm phong không có TRƯỚC nó"
            trước = m["băm"]
        return True, "chuỗi nguyên vẹn" + (" · mọi chữ ký kép đúng" if đã_ký else "")

    def thống_kê(self):
        "Theo từng 'ai': số niêm phong, số đã chấm, tỉ lệ trúng, và ĐƯỜNG NỀN (đoán theo tỉ lệ nền)."
        ds = self.đọc(); niêm = {m["băm"]: m for m in ds if m.get("loại") == "niêm_phong"}
        theo_ai = {}
        for m in ds:
            if m.get("loại") != "chấm": continue
            n = niêm[m["niêm"]]; a = theo_ai.setdefault(n["ai"], {"chấm": 0, "trúng": 0, "kết_quả": []})
            a["chấm"] += 1; a["trúng"] += bool(m["trúng"]); a["kết_quả"].append(json.dumps(m["kết_quả"], sort_keys=True))
        ra = {}
        for ai, a in theo_ai.items():
            # đường nền = luôn đoán kết quả PHỔ BIẾN NHẤT của chính ai đó (không cần biết gì về việc)
            phổ = max(a["kết_quả"].count(k) for k in set(a["kết_quả"]))
            ra[ai] = {"niêm_phong": sum(1 for m in niêm.values() if m["ai"] == ai), "đã_chấm": a["chấm"],
                      "trúng": a["trúng"], "tỉ_lệ": round(a["trúng"] / a["chấm"], 3),
                      "đường_nền": round(phổ / a["chấm"], 3),
                      "hơn_nền": round((a["trúng"] - phổ) / a["chấm"], 3)}
        for ai in {m["ai"] for m in niêm.values()} - set(ra):
            ra[ai] = {"niêm_phong": sum(1 for m in niêm.values() if m["ai"] == ai), "đã_chấm": 0}
        return ra

def ghim_khoá(thư_mục=KHOÁ_MẶC_ĐỊNH, tệp=None):
    "Ghi vân tay ĐỦ của khoá hiện tại vào tệp ghim (tạo khoá nếu chưa có). Việc của NGƯỜI — rồi commit."
    tệp = tệp or GHIM_KHOÁ
    k = KhoáSổ(thư_mục, ghim=None)
    with open(tệp, "w", encoding="utf-8") as f:
        json.dump({"vân_tay_đủ": k.vân_tay_đủ, "thuật_toán": "SHA-256('GIAO-KHOA-v1' ‖ pk_Ed25519 ‖ pk_ML-DSA-65)",
                   "ed25519": k.công["ed25519"]}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return k.vân_tay_đủ

if __name__ == "__main__":
    if "--ghim-khoa" in sys.argv:
        vt = ghim_khoá(); print(f"đã GHIM khoá sổ niêm phong: {vt}\n→ {GHIM_KHOÁ} — hãy COMMIT tệp này."); sys.exit(0)
    sổ = SổNiêmPhong(sys.argv[1] if len(sys.argv) > 1 else MẶC_ĐỊNH)
    ok, lý = sổ.kiểm_chuỗi()
    ds = sổ.đọc(); n_ký = sum(1 for m in ds if "ký" in m)
    print(f"sổ: {sổ.đường_dẫn}")
    print(f"toàn vẹn: {'✓' if ok else '✗'} {lý}")
    print(f"ký kép (ML-DSA-65 + Ed25519): {n_ký}/{len(ds)} mục" + (f" · khoá {sổ.khoá.công['vân_tay'][:16]}…" if sổ.khoá else ""))
    print(json.dumps(sổ.thống_kê(), ensure_ascii=False, indent=1))
    sys.exit(0 if ok else 1)

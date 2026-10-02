# -*- coding: utf-8 -*-
"""
SỔ NIÊM PHONG DỰ ĐOÁN — lớp CẦU Python mỏng. LOGIC SỔ nay viết bằng GIAO (niem_phong.giao, chạy trên GVM-64
qua `sh niem.sh`, v0.45); tệp này chỉ giữ NGUYÊN API cũ cho các cầu host (giao_mcp.py, moi_gioi_luong_tu.py,
vong_tu_sua.py) và bài kiểm. (Học từ D:\\KIAI\\con-thuyen: "dự đoán niêm phong, chấm sau, so với đường nền".)

  · Sổ JSONL chỉ-ghi-thêm, định dạng 2: mỗi mục mang `băm_trước` ⇒ CHUỖI BĂM; mục mới KÝ KÉP ML-DSA-65 +
    Ed25519 trên "GIAO-NIEM-PHONG-v2|<băm>". BĂM = SHA-256 của chính văn bản dòng trước `,"băm":"` + "}".
  · Dự đoán niêm phong TRƯỚC ⇒ không thể "đoán sau khi đã biết". Chấm trỏ tới băm niêm phong, không chấm lại.
  · Thống kê so với ĐƯỜNG NỀN. γ chỉ là thước HIỆU CHỈNH SAU SỰ VIỆC.

Dùng (Python):  sổ = SổNiêmPhong(đường_dẫn)
                b = sổ.niêm_phong("llm:claude", "vá lib_x.giao", {"đích_sáng": True, "hồi_quy": 0})
                sổ.chấm(b, {"đích_sáng": True, "hồi_quy": 0});  sổ.kiểm_chuỗi(); sổ.thống_kê()
Dòng lệnh:      sh niem.sh kiem <sổ> · sh niem.sh thong_ke <sổ> · sh niem.sh ghim_khoa   (KHÔNG cần Python)
                python niem_phong.py [sổ.jsonl] | --ghim-khoa   (giữ cho quen tay — gọi niem.sh)
Biến môi trường: GIAO_SO_NIEM_PHONG · GIAO_KHOA_NIEM_PHONG · GIAO_GHIM_KHOA_NIEM_PHONG · GIAO_NIEM_PHONG_KY=0.
"""
import os, sys, json, hashlib, subprocess, tempfile, shutil

P = os.path.dirname(os.path.abspath(__file__))
MẶC_ĐỊNH = os.environ.get("GIAO_SO_NIEM_PHONG") or os.path.join(P, "__pycache__", "so_niem_phong.jsonl")
KHOÁ_MẶC_ĐỊNH = os.environ.get("GIAO_KHOA_NIEM_PHONG") or os.path.join(P, ".khoa", "niem_phong")
GHIM_KHOÁ = os.environ.get("GIAO_GHIM_KHOA_NIEM_PHONG") or os.path.join(P, "khoa_niem_phong.ghim")
GỐC = "0" * 64
_KHÔNG_GHIM = os.path.join(P, "__pycache__", "_khong_co_ghim")   # đường không tồn tại ⇒ không kiểm ghim

class KhoáLệchGhim(RuntimeError): pass

def dòng_sổ(mục):
    "Mục (dict, đúng thứ tự trường) → một dòng sổ gọn — cách niem_phong.giao viết."
    return json.dumps(mục, ensure_ascii=False, separators=(",", ":"))

def _băm(mục):
    "SHA-256 của dòng sổ bỏ 'băm' và 'ký' (giữ thứ tự trường) — y như niem_phong.giao tính trên văn bản."
    return hashlib.sha256(dòng_sổ({k: v for k, v in mục.items() if k not in ("băm", "ký")}).encode("utf-8")).hexdigest()

def vân_tay_đủ(pk_ed, pk_ml): return hashlib.sha256(b"GIAO-KHOA-v1" + pk_ed + pk_ml).hexdigest()
def vân_tay(pk_ed, pk_ml): return vân_tay_đủ(pk_ed, pk_ml)[:32]

def đọc_ghim_khoá(tệp=None):
    tệp = tệp or GHIM_KHOÁ
    if not os.path.exists(tệp): return None
    return json.load(open(tệp, encoding="utf-8"))["vân_tay_đủ"]

def _niem(việc, *đối, khoá_dir=None, ghim=None, sổ=None, cờ=()):
    "Chạy `sh niem.sh` → (mã, stdout, stderr). ghim=None ⇒ KHÔNG kiểm ghim."
    env = dict(os.environ)
    env["GIAO_KHOA_NIEM_PHONG"] = os.path.abspath(khoá_dir or KHOÁ_MẶC_ĐỊNH)
    env["GIAO_GHIM_KHOA_NIEM_PHONG"] = os.path.abspath(ghim) if ghim else _KHÔNG_GHIM
    env.pop("GIAO_NIEM_PHONG_KY", None)                 # quyết ký/không do lớp này (cờ --khong-ky)
    lệnh = ["sh", os.path.join(P, "niem.sh"), việc] + ([os.path.abspath(sổ)] if sổ else []) + [str(x) for x in đối] + list(cờ)
    r = subprocess.run(lệnh, capture_output=True, env=env, cwd=P)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")

def _lỗi(err):
    "Lấy thông điệp `__ném` của GIAO; LỆCH GHIM ⇒ KhoáLệchGhim, còn lại ValueError."
    dòng = [d for d in err.splitlines() if "[GIAO lỗi]" in d or "[niem]" in d]
    lý = (dòng[0].split("]", 1)[1].strip() if dòng else err.strip()) or "niem.sh thất bại"
    return KhoáLệchGhim(lý) if "LỆCH GHIM" in lý else ValueError(lý)

def _ghim_của(ghim):
    if ghim is None: return None
    tệp = GHIM_KHOÁ if ghim == "mặc_định" else ghim
    return tệp if os.path.exists(tệp) else None

class KhoáSổ:
    "Cặp khoá ký kép của sổ (bi_mat.json + cong_khai.json trong thư_mục). Sinh/kiểm/ký đều trong niem_phong.giao."
    def __init__(self, thư_mục=KHOÁ_MẶC_ĐỊNH, tạo=True, ghim="mặc_định"):
        "ghim: 'mặc_định' ⇒ GHIM_KHOÁ nếu tệp ấy có · None ⇒ không kiểm ghim · đường dẫn ⇒ tệp ghim ấy."
        self.thư_mục = thư_mục; self.ghim = _ghim_của(ghim)
        if not tạo and not os.path.exists(os.path.join(thư_mục, "bi_mat.json")) and self.ghim is None:
            raise FileNotFoundError(os.path.join(thư_mục, "bi_mat.json"))
        if tạo and not os.path.exists(os.path.join(thư_mục, "bi_mat.json")):
            mã, _, err = _niem("khoa", khoá_dir=thư_mục, ghim=self.ghim)
            if mã: raise _lỗi(err)
        mã, out, err = _niem("cong", khoá_dir=thư_mục, ghim=self.ghim)
        if mã: raise _lỗi(err)
        c = json.loads(out.strip().splitlines()[-1])
        self.vân_tay_đủ = c["vân_tay_đủ"]
        self.công = {"ed25519": c["ed25519"], "mldsa65": c["mldsa65"], "vân_tay": c["vân_tay"]}
    def ký(self, băm):
        mã, out, err = _niem("ky", băm, khoá_dir=self.thư_mục, ghim=self.ghim)
        if mã: raise _lỗi(err)
        return json.loads(out.strip().splitlines()[-1])

def _có_thể_ký():
    if os.environ.get("GIAO_NIEM_PHONG_KY", "1") == "0": return False
    try:
        from vo_gvm64 import WASMTIME
        return os.path.exists(os.path.join(P, "wasm", "ky.wasm")) and bool(WASMTIME) and os.path.exists(WASMTIME)
    except Exception: return False

class SổNiêmPhong:
    def __init__(self, đường_dẫn=MẶC_ĐỊNH, ký=None, khoá=None):
        "ký=None ⇒ tự ký nếu có ky.wasm + wasmtime (tắt: GIAO_NIEM_PHONG_KY=0). khoá = KhoáSổ hoặc thư mục."
        self.đường_dẫn = đường_dẫn
        os.makedirs(os.path.dirname(os.path.abspath(đường_dẫn)), exist_ok=True)
        if ký is None: ký = _có_thể_ký()
        self.khoá = (khoá if isinstance(khoá, KhoáSổ) else KhoáSổ(khoá or KHOÁ_MẶC_ĐỊNH)) if ký else None

    def _chạy(self, việc, *đối, cờ=()):
        if self.khoá is None: return _niem(việc, *đối, sổ=self.đường_dẫn, cờ=tuple(cờ) + ("--khong-ky",))
        return _niem(việc, *đối, sổ=self.đường_dẫn, khoá_dir=self.khoá.thư_mục, ghim=self.khoá.ghim, cờ=cờ)

    def đọc(self):
        if not os.path.exists(self.đường_dẫn): return []
        with open(self.đường_dẫn, encoding="utf-8") as f:
            return [json.loads(d) for d in f if d.strip()]

    def niêm_phong(self, ai, việc, dự_đoán):
        "Ghi dự đoán TRƯỚC khi làm. Trả băm niêm phong (dùng để chấm sau)."
        if not isinstance(dự_đoán, dict) or not dự_đoán: raise ValueError("dự đoán phải là bản {khoá: giá_trị} không rỗng")
        mã, out, err = self._chạy("niem", str(ai), str(việc), json.dumps(dự_đoán, ensure_ascii=False))
        if mã: raise _lỗi(err)
        return next(d[4:].strip() for d in out.splitlines() if d.startswith("BĂM "))

    def chấm(self, băm_niêm, kết_quả):
        "Ghi kết quả thật cho một niêm phong. trúng = MỌI khoá đã dự đoán đều khớp kết quả."
        mã, out, err = self._chạy("cham", băm_niêm, json.dumps(kết_quả, ensure_ascii=False))
        if mã: raise _lỗi(err)
        return json.loads(out.strip().splitlines()[-1])

    def kiểm_chuỗi(self, khoá_công=None, bắt_buộc_ký=False):
        """Kiểm toàn vẹn (chuỗi băm + chấm trỏ tới niêm phong CÓ TRƯỚC) và KÝ KÉP theo khoá công khai (mặc định
        khoá của sổ này). Từ mục ký đầu tiên trở đi, mục THIẾU chữ ký là lỗi; bắt_buộc_ký=True: MỌI mục phải ký."""
        cờ = ("--bat-buoc-ky",) if bắt_buộc_ký else ()
        if khoá_công is not None:
            tm = tempfile.mkdtemp()
            try:
                with open(os.path.join(tm, "cong_khai.json"), "w", encoding="utf-8") as f:
                    json.dump({"ed25519": khoá_công["ed25519"], "mldsa65": khoá_công["mldsa65"]}, f)
                mã, out, err = _niem("kiem", sổ=self.đường_dẫn, khoá_dir=tm, cờ=cờ)
            finally: shutil.rmtree(tm, ignore_errors=True)
        else:
            mã, out, err = self._chạy("kiem", cờ=cờ)
        for d in out.splitlines():
            if d.startswith("✓ "): return True, d[2:]
            if d.startswith("✗ "): return False, d[2:]
        if not os.path.exists(self.đường_dẫn) and not mã: return True, "chuỗi nguyên vẹn"
        raise _lỗi(err)

    def thống_kê(self):
        "Theo từng 'ai': số niêm phong, số đã chấm, tỉ lệ trúng, ĐƯỜNG NỀN (luôn đoán kết quả phổ biến nhất)."
        mã, out, err = _niem("thong_ke", sổ=self.đường_dẫn, cờ=("--khong-ky",))
        if mã: raise _lỗi(err)
        return json.loads(out.strip().splitlines()[-1])

def ghim_khoá(thư_mục=KHOÁ_MẶC_ĐỊNH, tệp=None):
    "Ghi vân tay ĐỦ của khoá hiện tại vào tệp ghim (tạo khoá nếu chưa có). Việc của NGƯỜI — rồi commit."
    tệp = tệp or GHIM_KHOÁ
    k = KhoáSổ(thư_mục, ghim=None)                    # ghim lại: KHÔNG so với ghim cũ (đổi ghim là việc có chủ ý)
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

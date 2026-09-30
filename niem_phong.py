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
    "SHA-256 của mục (không kể trường 'băm'), JSON chuẩn tắc (khoá sắp xếp, không khoảng trắng thừa)."
    d = {k: v for k, v in mục.items() if k != "băm"}
    return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

class SổNiêmPhong:
    def __init__(self, đường_dẫn=MẶC_ĐỊNH):
        self.đường_dẫn = đường_dẫn
        os.makedirs(os.path.dirname(os.path.abspath(đường_dẫn)), exist_ok=True)

    def đọc(self):
        if not os.path.exists(self.đường_dẫn): return []
        with open(self.đường_dẫn, encoding="utf-8") as f:
            return [json.loads(d) for d in f if d.strip()]

    def _ghi(self, mục):
        ds = self.đọc()
        mục["số"] = len(ds); mục["băm_trước"] = ds[-1]["băm"] if ds else GỐC
        mục["lúc"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        mục["băm"] = _băm(mục)
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

    def kiểm_chuỗi(self):
        "Kiểm toàn vẹn: mỗi mục băm đúng + nối đúng mục trước + chấm trỏ tới niêm phong CÓ TRƯỚC."
        trước = GỐC; đã_niêm = set()
        for i, m in enumerate(self.đọc()):
            if m.get("số") != i: return False, f"mục {i}: số thứ tự sai ({m.get('số')}) — có mục bị xoá/chèn"
            if m.get("băm_trước") != trước: return False, f"mục {i}: đứt chuỗi (băm_trước không khớp)"
            if _băm(m) != m.get("băm"): return False, f"mục {i}: nội dung bị SỬA (băm không khớp)"
            if m.get("loại") == "niêm_phong": đã_niêm.add(m["băm"])
            elif m.get("loại") == "chấm" and m.get("niêm") not in đã_niêm:
                return False, f"mục {i}: chấm một niêm phong không có TRƯỚC nó"
            trước = m["băm"]
        return True, "chuỗi nguyên vẹn"

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

if __name__ == "__main__":
    sổ = SổNiêmPhong(sys.argv[1] if len(sys.argv) > 1 else MẶC_ĐỊNH)
    ok, lý = sổ.kiểm_chuỗi()
    print(f"sổ: {sổ.đường_dẫn}\ntoàn vẹn: {'✓' if ok else '✗'} {lý}")
    print(json.dumps(sổ.thống_kê(), ensure_ascii=False, indent=1))
    sys.exit(0 if ok else 1)

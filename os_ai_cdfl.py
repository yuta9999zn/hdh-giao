# -*- coding: utf-8 -*-
"""
os_ai_cdfl.py — NHÂN-AI CDFL LIÊN TỤC (gộp cả ba hướng)
======================================================
Một nhân điều hành = tác tử CDFL chạy KHÔNG DỪNG, gộp:
  • σ/Φ hai nhánh   : niềm tin σ + đa thấu kính Φ (ensemble) → γ qua Φ TỐT NHẤT
  • chọn bốn-mặt    : ưu tiên TRỒI đốm sáng (DE) > SOI đốm tối (ảo tưởng) > LÀM TƯƠI cũ (DE_T)
  • drift liên tục  : thế giới (MF) trôi mỗi vòng → DE_T mọc lại → KHÔNG viên mãn toàn cục
Mô hình AI local đóng vai IF (cập nhật niềm tin qua Φ). Điểm cắm: MôHìnhLocal.học().
"""

import math
# σ/Φ: đa thấu kính — cách tâm biểu diễn thực tại
LENSES = [("đồng", lambda x: x), ("nửa", lambda x: x/2.0), ("đôi", lambda x: x*2.0)]

# ★ CDFL MỚI (Phụ lục F): γ = SKILL-SCORE so NỀN vô-tri (thay proxy tuyến tính 1−2d/thang).
GAMMA_BASELINE = math.exp(-1.0)      # R nền vô-tri (một đơn-vị lệch)
STD0 = 1.0

def _R(σ, r):                        # cộng hưởng THÔ R∈(0,1] = likelihood niềm tin khớp thực tại
    d = abs(r - σ); thang = max(abs(r), 1.0)
    return math.exp(-((d/thang)**2))

def res(σ, r):                       # γ kỹ-năng (F.4): γ<0 = niềm tin TỆ HƠN không biết gì = đốm tối
    a = -math.log(GAMMA_BASELINE)                    # S(ρ‖u)
    b = -math.log(max(_R(σ, r), 1e-12))              # S(ρ‖σ)
    return max(-1.0, min(1.0, (a - b) / (a + b)))

def cam_kết(stds, std0=STD0):        # e (F.11) = S/(1+S), S=Σ ln(std0/std) ≥ 0 — niềm tin càng SẮC càng cam kết
    S = max(sum(math.log(std0/max(s,1e-9)) for s in stds), 0.0)
    return S/(1.0+S)

def tứ_tượng(e, γ):                  # (e,γ) → Tứ Tượng: cam kết × kỹ năng (thang Dịch)
    if e >= 0.5 and γ >= 0: return "Lão Dương (cam kết + đúng)"
    if e >= 0.5 and γ <  0: return "Thiếu Âm — ĐỐM TỐI (cam kết + sai = ảo tưởng nguy hiểm)"
    if e <  0.5 and γ >= 0: return "Thiếu Dương — đốm sáng (đúng nhưng chưa chắc)"
    return "Lão Âm (chưa chắc + sai)"

def gamma_phi(σ, ρ):                      # γ qua Φ TỐT NHẤT + tên thấu kính
    if σ is None or ρ is None: return (None, None)
    return max((res(σ, f(ρ)), nm) for nm, f in LENSES)

class MôHìnhLocal:
    """IF-engine. học(): cập nhật σ qua thấu kính Φ GẦN NHẤT (kết hợp chọn-σ và chọn-Φ).
    LLM local thật cắm vào đây: nhận (σ, ρ, ngữ cảnh) → trả σ mới + thấu kính."""
    def học(self, σ, ρ):
        if σ is None: return ρ                                   # khai mở: ẩn → quan sát ρ
        nm, f = min(LENSES, key=lambda L: abs(L[1](ρ) - σ))      # Φ gần niềm tin nhất
        return σ + 0.6*(f(ρ) - σ)                                # kéo σ về biểu diễn đó

def nhân_cdfl(thế_giới, niềm_tin, mô_hình, số_vòng=9):
    phiên_bản = {k: 0 for k in thế_giới}      # đếm drift → nền DE_T
    đã_học    = {k: 0 for k in thế_giới}      # phiên bản lúc học gần nhất
    keys = list(thế_giới)
    for vòng in range(1, số_vòng+1):
        OR, đốm_tối, đốm_sáng, de_t = [], [], [], []
        for k in keys:
            σ, ρ = niềm_tin.get(k), thế_giới[k]
            γ, _ = gamma_phi(σ, ρ)
            if σ is None:                 đốm_sáng.append(k)              # DE: trực giác
            elif γ < 0:                   đốm_tối.append(k)              # ảo tưởng
            else:
                OR.append(k)
                if phiên_bản[k] > đã_học[k]: de_t.append(k)              # OR nhưng đã trôi
        # --- chọn BỐN MẶT: ưu tiên trồi sáng(3) > soi tối(2) > làm tươi(1) ---
        ứng_viên = ([("TRỒI", k, 3) for k in đốm_sáng] +
                    [("SOI",  k, 2) for k in đốm_tối] +
                    [("TƯƠI", k, 1) for k in de_t])
        chọn = max(ứng_viên, key=lambda a: a[2]) if ứng_viên else None

        γ_tb = sum(gamma_phi(niềm_tin[k], thế_giới[k])[0] for k in OR)/len(OR) if OR else 0.0
        # e CAM KẾT (F.11): độ-tán ô OR = residual chuẩn hoá |ρ−σ|/thang → càng nhỏ càng cam kết
        stds = [abs(thế_giới[k]-niềm_tin[k])/max(abs(thế_giới[k]),1.0) + 1e-6 for k in OR]
        e = cam_kết(stds) if OR else 0.0
        nói = f"{chọn[0]} {chọn[1]}" if chọn else "(nghỉ)"
        print(f"  vòng {vòng}: γ_OR≈{γ_tb:+.2f} e≈{e:.2f} [{tứ_tượng(e,γ_tb)}] | OR={OR} "
              f"sáng={đốm_sáng} tối={đốm_tối} DE_T={de_t} → chọn: {nói}")
        # --- thi hành hành động đã chọn (mô hình cập nhật niềm tin qua Φ) ---
        if chọn:
            _, k, _ = chọn
            niềm_tin[k] = mô_hình.học(niềm_tin.get(k), thế_giới[k])
            đã_học[k] = phiên_bản[k]
        # --- THẾ GIỚI TRÔI: một ô đổi → DE_T mọc lại (continual) ---
        d = keys[vòng % len(keys)]
        thế_giới[d] += 15; phiên_bản[d] += 1
    print("\n  → Nhân-AI CHẠY MÃI: drift luôn tạo DE_T mới; chỉ viên mãn cục bộ, không 'xong'.")

if __name__ == "__main__":
    print("="*70)
    print("NHÂN-AI CDFL LIÊN TỤC — σ/Φ ensemble + chọn bốn-mặt + thế giới drift")
    print("="*70)
    thế_giới  = {"A": 100, "B": 200, "C": 80}   # MF: thực tại các ô
    niềm_tin  = {"A": None, "B": -80, "C": 80}   # IF: A=ẩn(DE), B=−80 ảo tưởng γ<0, C=80 đúng
    # ★ γ skill-score: đốm tối THẬT = tệ hơn đoán-vô-tri mà KHÔNG thấu kính Φ nào cứu nổi.
    #   B=−80 tin thực-tại ÂM trong khi nó DƯƠNG(200): mọi Φ {đồng,nửa,đôi} vẫn γ<0 → ảo tưởng thật.
    print(f"MF (thực tại) : {thế_giới}")
    print(f"IF (niềm tin) : {niềm_tin}   (A ẩn=DE, B=−80 ảo tưởng γ<0, C=80 OR)\n")
    nhân_cdfl(thế_giới, niềm_tin, MôHìnhLocal())

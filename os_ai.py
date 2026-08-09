# -*- coding: utf-8 -*-
"""
os_ai.py — AI LÀ DỊCH VỤ NHÂN (kernel) CỦA HỆ ĐIỀU HÀNH GIAO
============================================================
Khác biệt với HĐH/ngôn ngữ hiện nay: ở đây MÔ HÌNH AI LOCAL đóng vai IF (tâm trường)
TRONG vòng CDFL — vòng đó CHÍNH LÀ nhân điều hành. Bạn GIAO VIỆC (một mục tiêu);
nhân-tác-tử dùng mô hình để CHỌN hành động tác động lên THẾ GIỚI (MF = tài nguyên/
thiết bị, nhân quả ngược IF→MF), đo CỘNG HƯỞNG γ (OR = điều đã kiểm chứng với thực tại),
và theo dõi DE (điều chưa biết). Bạn TƯƠNG TÁC bằng cách hỏi OR/DE và hiệu chỉnh.

An toàn theo thiết kế: OS coi đầu ra mô hình là NIỀM TIN (IF) phải đối chiếu THỰC TẠI
(MF) qua γ — γ<0 = ảo tưởng (không thi hành); ẩn = chưa biết (hỏi lại). Mô hình local
chạy trong hộp cát tài nguyên (như giới hạn của runtime GIAO).
"""

AN = "ẩn"

# ============================================================
# ĐIỂM CẮM MÔ HÌNH LOCAL  (thay nghĩ() bằng lời gọi LLM local: llama.cpp / ollama / ...)
# ============================================================
class MôHìnhLocal:
    """IF-engine. Nhận (quan sát thế giới, mục tiêu, hành động khả dĩ) → đề xuất hành động
    kèm DỰ ĐOÁN tác động. LLM thật: dựng prompt từ 3 thứ đó, đọc lại tên hành động."""
    def nghĩ(self, quan_sát, mục_tiêu, hành_động):
        tốt, điểm_tốt = AN, -1
        for tên, hiệu_ứng in hành_động.items():
            dự = self._mô_phỏng(quan_sát, hiệu_ứng)        # niềm tin σ về kết quả nếu làm
            lợi = self._độ_gần(dự, mục_tiêu) - self._độ_gần(quan_sát, mục_tiêu)
            if lợi > điểm_tốt: tốt, điểm_tốt = tên, lợi
        # nếu không hành động nào tiến gần mục tiêu → trả 'ẩn' (chưa biết cách → DE)
        return tốt if điểm_tốt > 0 else AN
    def _mô_phỏng(self, tt, hiệu_ứng):
        m = dict(tt)
        for k, d in hiệu_ứng.items(): m[k] = max(0, m.get(k, 0) + d)
        return m
    def _độ_gần(self, tt, mt):                              # âm = càng xa mục tiêu
        return -sum(max(0, tt.get(k, 0) - v) for k, v in mt.items())

# ============================================================
# NHÂN ĐIỀU HÀNH = VÒNG CDFL  (giao việc cho AI)
# ============================================================
def γ_cộng_hưởng(thế_giới, mục_tiêu):
    """OR/γ: 1 = đã đạt mục tiêu (cộng hưởng), giảm dần khi còn lệch."""
    lệch = sum(max(0, thế_giới.get(k, 0) - v) for k, v in mục_tiêu.items())
    thang = sum(mục_tiêu.values()) or 1
    return max(-1.0, 1.0 - lệch / thang)

def giao_việc(thế_giới, mục_tiêu, hành_động, mô_hình, tối_đa=8):
    "Giao một MỤC TIÊU cho nhân-AI. Trả nhật ký + báo cáo OR/DE."
    nhật_ký, de = [], []
    for bước in range(tối_đa):
        γ = γ_cộng_hưởng(thế_giới, mục_tiêu)
        if γ >= 0.999:
            nhật_ký.append(f"  ✓ viên mãn: mục tiêu đạt (γ={γ:+.2f})"); break
        chọn = mô_hình.nghĩ(thế_giới, mục_tiêu, hành_động)        # IF: model chọn hành động
        if chọn is AN:                                            # DE: chưa biết cách
            de.append("không tìm được hành động mở rộng OR")
            nhật_ký.append(f"  · γ={γ:+.2f} → mô hình ‘ẩn’: cần con người/biết thêm (DE)"); break
        # đối chiếu trước khi thi hành (an toàn): hành động có thật sự tăng γ?
        thử = dict(thế_giới)
        for k, d in hành_động[chọn].items(): thử[k] = max(0, thử.get(k, 0) + d)
        if γ_cộng_hưởng(thử, mục_tiêu) <= γ:                     # γ không tăng = ảo tưởng → bỏ
            de.append(f"‘{chọn}’ tưởng có lợi mà không (γ không tăng)")
            nhật_ký.append(f"  · γ={γ:+.2f} → loại ‘{chọn}’ (đốm tối, không thi hành)"); break
        thế_giới = thử                                           # NHÂN QUẢ IF→MF: thi hành
        nhật_ký.append(f"  · γ={γ:+.2f} → CHỌN ‘{chọn}’ → {thế_giới}")
    return thế_giới, nhật_ký, de, γ_cộng_hưởng(thế_giới, mục_tiêu)

# ============================================================
# DEMO: giao việc cho HĐH-AI rồi tương tác
# ============================================================
if __name__ == "__main__":
    mô_hình = MôHìnhLocal()                 # ← thay bằng LLM local thật ở đây
    # THẾ GIỚI (MF) = trạng thái tài nguyên hệ thống
    thế_giới = {"cpu": 85, "mem": 70}
    # HÀNH ĐỘNG khả dĩ và tác động (LLM thật suy ra từ mô tả thiết bị)
    hành_động = {
        "đóng_tiến_trình_nặng": {"cpu": -30},
        "giải_phóng_cache":      {"mem": -40},
        "chờ":                   {},
    }
    print("="*64); print("HĐH-AI — GIAO VIỆC cho nhân-tác-tử (mô hình local đóng vai IF)")
    print("="*64)
    print(f"Thế giới (MF) ban đầu: {thế_giới}")

    mục_tiêu = {"cpu": 30, "mem": 40}       # ← việc bạn GIAO: hạ cpu≤30, mem≤40
    print(f"MỤC TIÊU giao: cpu≤30, mem≤40\n")
    thế_giới, nhật_ký, de, γ = giao_việc(thế_giới, mục_tiêu, hành_động, mô_hình)
    for d in nhật_ký: print(d)

    print("\n--- TƯƠNG TÁC: hỏi nhân-AI nó biết/chưa biết gì ---")
    print(f"  OR (đã kiểm chứng): trạng thái {thế_giới}, γ={γ:+.2f}")
    print(f"  DE (chưa chắc/chưa biết): {de or '∅'}")
    print("\n  → AI là DỊCH VỤ NHÂN: bạn giao mục tiêu, nó chọn-hành-động-đối-chiếu-γ,")
    print("    chỉ thi hành điều LÀM TĂNG OR THẬT, và báo lại điều còn trong vùng tối.")

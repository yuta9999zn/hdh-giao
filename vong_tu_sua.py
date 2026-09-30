# -*- coding: utf-8 -*-
"""
vong_tu_sua.py — VÒNG TỰ-SỬA (self-repair agent loop) cho GIAO, có CỔNG CDFL.
================================================================================
Quy trình THẬT, tự-động: chạy-test → đọc-lỗi → SINH bản-vá → ÁP → KIỂM → cổng-CDFL.
  • Cổng CDFL: chỉ NHẬN bản vá nếu test đích tối(fail)→sáng(pass) VÀ không phá test khác (REGRESSION-SAFE:
    chạy lại TOÀN BỘ test liên-quan, vá gây hồi-quy → HOÀN-TÁC). Vá không-giúp/gây-hồi-quy (đốm-tối) → HOÀN-TÁC.
  • Sinh-vá v1 = SỬA-THEO-ORACLE (rule-based, THẬT cho lớp lỗi "trả sai hằng/giá-trị"): đọc
    'expected E got G' từ test → thử thay literal G→E trong câu `trả` của tệp đích.
  • TỔNG-QUÁT: thay hàm sinh-vá bằng LLM (hook `sinh_va`) — sandbox này chưa có API nên dùng rule-based.
  • CỔNG ĐỦ-MẠNH (học từ vườn ươm z: "chứng minh phép kiểm CÓ THỂ rớt" trước khi tin nó): test đích
    chuyển sang sáng CHƯA đủ — một test yếu (vd chỉ kiểm `> 100`) cũng "sáng" với 127, 128, 129. Trước
    khi NHẬN, vòng (a) chạy lại test đích lần 2 phải cùng kết quả (ỔN ĐỊNH), (b) ĐỘT BIẾN chính bản vá
    (đổi toán tử, hằng ±1) và đòi test RỚT trên ≥ 1 đột biến. Không chứng minh được ⇒ kết quả là ẨN
    (không phải sáng) và bản vá bị HOÀN-TÁC (trừ khi --nhận-ẩn). Đây là logic BA TRỊ của GIAO:
    "đạt mà chưa chứng minh được là có thể trượt" = CHƯA BIẾT, không bịa là sáng.
TRUNG THỰC: đây KHÔNG phải AI tổng-quát; là vòng program-repair hẹp + chỗ-cắm-LLM rõ ràng.
  python vong_tu_sua.py <đích.giao> <test.giao> [--llm] [--nhận-ẩn]   (test in 'PASS' / 'FAIL expected E got G')
  Mã thoát: 0 = SÁNG (vá + đã chứng minh) · 2 = ẨN (test chưa đủ mạnh) · 1 = không vá được.
"""
import subprocess, sys, os, re, shutil
from niem_phong import SổNiêmPhong

PY = sys.executable
def chạy_test(test):
    r = subprocess.run([PY, "giao.py", test], capture_output=True, text=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1"), encoding="utf-8")
    return (r.stdout or "") + (r.stderr or "")

def đọc_lỗi(out):
    "Đọc oracle 'FAIL expected E got G' → (E, G); PASS → None."
    if "PASS" in out: return None
    m = re.search(r"expected\s+(-?\d+)\s+got\s+(-?\d+)", out)
    return (m.group(1), m.group(2)) if m else ("?", "?")

# ── HOOK sinh-vá. THAY bằng LLM (Stage 5) cho lỗi tổng-quát; hiện: rule-based (Stage 1+2) ──
_NHÓM_TOÁN = [" + ", " - ", " * ", " // "]
_NHÓM_SO   = [" == ", " != ", " < ", " > ", " <= ", " >= "]
def sinh_va(src, expected, got):
    "Sinh BẢN VÁ ứng-viên: (1) hằng G→E trong `trả`; (2) mutation TOÁN-TỬ/SO-SÁNH (Stage 2)."
    ứng_viên = []
    # Stage 1 — oracle-repair HẰNG: thay literal got→expected trong câu `trả`
    for m in re.finditer(r"(trả[^\n]*?)(?<![\d-])(" + re.escape(got) + r")(?![\d])", src):
        i, j = m.start(2), m.end(2)
        ứng_viên.append(src[:i] + expected + src[j:])
    ứng_viên += đột_biến(src)
    return ứng_viên

def đột_biến(src):
    "Đột biến MỘT điểm: Stage 2 (toán-tử/so-sánh cùng nhóm) + Stage 3 (hằng nguyên ±1). Dùng chung cho sinh-vá và cổng đủ-mạnh."
    ứng_viên = []
    # Stage 2 — mutation TOÁN-TỬ & SO-SÁNH (thử thay từng vị-trí bằng phép cùng nhóm)
    for nhóm in (_NHÓM_TOÁN, _NHÓM_SO):
        for op in nhóm:
            start = 0
            while True:
                k = src.find(op, start)
                if k < 0: break
                for op2 in nhóm:
                    if op2 != op:
                        ứng_viên.append(src[:k] + op2 + src[k+len(op):])
                start = k + 1
    # Stage 3 — OFF-BY-ONE: ±1 trên từng hằng-số nguyên (lỗi sai-biên Stage 1/2 không bắt)
    for m in re.finditer(r"(?<![\w.])(\d+)(?![\w.])", src):
        n = int(m.group(1)); i, j = m.start(1), m.end(1)
        for n2 in (n+1, n-1):
            ứng_viên.append(src[:i] + str(n2) + src[j:])
    return ứng_viên

def cộng_hưởng(σ, ρ):
    "γ = 1 − 2|ρ−σ|/max(|ρ|,1) (cùng công thức MCP giao). γ>0 sáng · <0 tối."
    d = abs(ρ - σ); scale = max(abs(ρ), 1)
    return max(-1.0, min(1.0, 1 - 2.0*d/scale))

def _test_hồi_quy(tests, trừ):
    "Chạy mọi test trong `tests` (trừ `trừ`), trả DANH SÁCH test bị TỐI (regression). Rỗng = sạch."
    return [t for t in tests if t != trừ and đọc_lỗi(chạy_test(t)) is not None]

SỐ_ĐỘT_BIẾN = 12
def độ_đủ_mạnh(đích, test, vá, gốc, K=SỐ_ĐỘT_BIẾN):
    """CỔNG ĐỦ-MẠNH: (ổn_định, bắt, tổng). Test đích đã SÁNG trên `vá`; giờ đòi:
       · ỔN ĐỊNH — chạy lần 2 vẫn sáng (test chập chờn thì kết quả 'sáng' vô nghĩa);
       · ĐỘT BIẾN bản vá (tối đa K, chọn đều, tất định): test phải RỚT trên ≥ 1 đột biến.
       Đột biến TƯƠNG ĐƯƠNG (không đổi hành vi) vẫn 'sống' ⇒ bắt/tổng là CẬN DƯỚI của độ đủ mạnh."""
    ổn = đọc_lỗi(chạy_test(test)) is None
    ds = []
    for m in đột_biến(vá):
        if m != vá and m != gốc and m not in ds: ds.append(m)
    chọn = ds[::max(1, len(ds) // K)][:K] if ds else []
    bắt = 0
    try:
        for m in chọn:
            open(đích, "w", encoding="utf-8").write(m)
            if đọc_lỗi(chạy_test(test)) is not None: bắt += 1
    finally:
        open(đích, "w", encoding="utf-8").write(vá)
    return ổn, bắt, len(chọn)

NHẬN_ẨN = False           # --nhận-ẩn: giữ bản vá dù cổng đủ-mạnh trả ẨN (người dùng tự chịu)
KẾT_QUẢ = {"trạng_thái": "tối"}

def _chạy_ứng_viên(đích, test, kèm, gốc, ứng_viên, nhãn, max_thử, ai=None):
    """ÁP từng bản-vá → KIỂM đích + hồi-quy → CỔNG CDFL (regression-safe) → CỔNG ĐỦ-MẠNH. True nếu NHẬN (sáng).
    ai ≠ None (đề xuất của LLM): NIÊM PHONG dự đoán TRƯỚC khi áp, CHẤM bằng kết quả thật SAU cổng
    (sổ niem_phong.py, chuỗi băm) — để biết LLM có thật sự đoán giỏi hơn đường nền."""
    for k, vá in enumerate(ứng_viên[:max_thử]):
        niêm = None
        if ai is not None:
            niêm = SổNiêmPhong().niêm_phong(ai, f"vá {os.path.basename(đích)} cho {os.path.basename(test)}",
                                            {"đích_sáng": True, "hồi_quy": 0, "đủ_mạnh": True})
            print(f"    [niêm phong] dự đoán của {ai}: đích sáng · 0 hồi quy · test đủ mạnh — băm {niêm[:12]}…")
        thật = {"đích_sáng": False, "hồi_quy": 0, "đủ_mạnh": False}
        kq = _một_ứng_viên(đích, test, kèm, gốc, vá, k, nhãn, thật)
        if niêm is not None:
            c = SổNiêmPhong().chấm(niêm, thật)
            print(f"    [chấm] {'TRÚNG' if c['trúng'] else 'TRƯỢT'}" + ("" if c["trúng"] else f" — lệch: {c['lệch']}"))
        if kq is not None: return kq
    return False

def _một_ứng_viên(đích, test, kèm, gốc, vá, k, nhãn, thật):
    "Một bản vá qua mọi cổng. Trả True (nhận) / False (dừng, ẩn) / None (thử bản kế). Ghi kết quả thật vào `thật`."
    if True:
        open(đích, "w", encoding="utf-8").write(vá)                 # ÁP
        ok = đọc_lỗi(chạy_test(test)) is None                       # KIỂM test đích
        hồi_quy = _test_hồi_quy(kèm, test) if ok else []           # KIỂM hồi-quy (chỉ khi đích đã sáng)
        thật["đích_sáng"] = ok; thật["hồi_quy"] = len(hồi_quy)
        ρ = 100 if (ok and not hồi_quy) else 0; γ = cộng_hưởng(95, ρ)
        lý_do = "SÁNG" if ok else "tối"
        if ok and hồi_quy: lý_do = f"đích-SÁNG nhưng PHÁ {len(hồi_quy)} test ({', '.join(hồi_quy)})"
        print(f"    [{nhãn}] vá#{k+1}: {lý_do} · γ(σ=95,ρ={ρ}) = {γ:+.2f} → {'NHẬN' if γ>0 else 'HOÀN-TÁC (đốm-tối)'}")
        if γ > 0:                                                    # CỔNG CDFL: đích sáng + không hồi-quy
            ổn, bắt, tổng = độ_đủ_mạnh(đích, test, vá, gốc)
            thật["đủ_mạnh"] = bool(ổn and bắt > 0)
            if ổn and bắt > 0:
                print(f"    [đủ-mạnh] ổn định ✓ · test RỚT trên {bắt}/{tổng} đột biến của bản vá "
                      f"(cận dưới — đột biến tương đương vẫn sống) → test CÓ THỂ trượt ⇒ SÁNG")
                print(f"  ✅ TỰ-SỬA THÀNH CÔNG [{nhãn}]: bản vá #{k+1} làm test SÁNG (regression-safe, đủ-mạnh {bắt}/{tổng}), đã giữ lại.")
                KẾT_QUẢ["trạng_thái"] = "sáng"; return True
            lý = "test CHẬP CHỜN (lần 2 cho kết quả khác)" if not ổn else (
                 f"test KHÔNG rớt trên đột biến nào ({bắt}/{tổng}) — nó không phân biệt được bản vá với các biến thể"
                 if tổng else "không sinh được đột biến nào để thử test")
            print(f"    [đủ-mạnh] {lý} ⇒ ẨN (chưa chứng minh được, KHÔNG phải sáng)")
            KẾT_QUẢ["trạng_thái"] = "ẩn"
            if NHẬN_ẨN:
                print(f"  ◐ TỰ-SỬA ẨN [{nhãn}]: giữ bản vá #{k+1} theo --nhận-ẩn — cần test mạnh hơn để xác nhận.")
                return False
            print(f"  ◐ TỰ-SỬA ẨN [{nhãn}]: bản vá #{k+1} làm test đạt nhưng test chưa đủ mạnh → HOÀN-TÁC (thêm test phân biệt rồi chạy lại).")
            open(đích, "w", encoding="utf-8").write(gốc)
            return False
        open(đích, "w", encoding="utf-8").write(gốc)                 # hoàn-tác vá hỏng/gây-hồi-quy
        return None

# ── STAGE 5: sinh-vá bằng LLM (host API qua tim_llm) — cho lỗi TỔNG-QUÁT (rule-based bó tay) ──
def _gỡ_rào_mã(s):
    "Bóc khối ```...``` nếu LLM bọc nó; ngược lại trả nguyên (đã cắt khoảng-trắng đầu/cuối)."
    m = re.search(r"```(?:[A-Za-z]*\n)?(.*?)```", s, re.S)
    return (m.group(1) if m else s).strip("\n").strip()

def sinh_va_llm(gốc, expected, got, lỗi_text):
    "Hỏi host-LLM (tim_llm.generate) sửa lỗi → danh-sách nguồn ứng-viên. Không-có-LLM-thật → [] (êm)."
    try:
        import tim_llm
    except Exception:
        return [], "không nạp được tim_llm"
    prompt = (
        "Bạn là bộ VÁ-LỖI cho ngôn ngữ lập trình GIAO (cú pháp tiếng Việt: "
        "`hàm tên(a,b){...}` · `trả` · `đặt` · `nếu/khác` · `lặp x trong` · toán-tử + - * // == < >). "
        f"Một test tự-động báo lỗi: KỲ VỌNG {expected}, NHẬN {got}.\n"
        "Dưới đây là TOÀN BỘ tệp nguồn GIAO. Hãy sửa ĐÚNG chỗ gây sai, GIỮ NGUYÊN phần còn lại. "
        "CHỈ trả về nội dung tệp ĐÃ SỬA, đặt trong một khối ```...```, KHÔNG giải thích.\n\n"
        + gốc
    )
    try:
        out = tim_llm.generate(prompt)
    except Exception as e:
        return [], "gọi LLM lỗi: " + str(e)[:80]
    be = tim_llm.backend.get("sinh", "")
    if be.startswith("dự-phòng"):                                   # rơi xuống stub = KHÔNG có LLM thật
        return [], "host API/Ollama tắt (dự-phòng) — " + (tim_llm.backend.get("api_lý_do", "") or "không cấu hình")
    mã = _gỡ_rào_mã(out)
    if not mã or mã == gốc:
        return [], f"LLM ({be}) không đề-xuất thay-đổi hợp-lệ"
    return [mã], be

def vòng(đích, test, max_thử=40, tests_kèm=None, dùng_llm=False):
    # REGRESSION-SAFE: `tests_kèm` = TOÀN BỘ test liên-quan phải GIỮ-SÁNG sau vá.
    #   Mặc định None → chỉ test đích (tương thích lối gọi cũ). Cổng CDFL chỉ NHẬN khi
    #   test đích sáng VÀ không test kèm nào chuyển sang tối (không phá test khác).
    #   dùng_llm=True → khi rule-based (Stage 1-4) bó tay, hỏi host-LLM (Stage 5), VẪN qua cổng CDFL.
    kèm = tests_kèm if tests_kèm is not None else [test]
    print("="*74); print(f"VÒNG TỰ-SỬA: đích={đích} · test={test}" + (f" · giữ-sáng {len(kèm)} test" if len(kèm) > 1 else "")); print("="*74)
    gốc = open(đích, encoding="utf-8").read()
    out = chạy_test(test); lỗi = đọc_lỗi(out)
    if lỗi is None:
        print("  test ĐÃ sáng — không cần sửa."); return True
    print(f"  [đọc-lỗi] test TỐI (fail): expected {lỗi[0]} got {lỗi[1]}")
    # σ = niềm-tin 'sẽ-vá-được' (95) ; ρ_trước = thực-tại (0 = fail)
    print(f"  [CDFL] trước vá: γ(σ=95, ρ=0) = {cộng_hưởng(95,0):+.2f} (tối = ảo-tưởng-đang-hỏng)")
    # ── Stage 1-4: rule-based (oracle/mutation/off-by-one) ──
    ứng_viên = sinh_va(gốc, lỗi[0], lỗi[1])
    print(f"  [sinh-vá rule-based] {len(ứng_viên)} bản-vá ứng-viên ({lỗi[1]}→{lỗi[0]})")
    if _chạy_ứng_viên(đích, test, kèm, gốc, ứng_viên, "rule", max_thử):
        return True
    # ── Stage 5: LLM (host API) — chỉ khi bật & rule-based bó tay ──
    if dùng_llm:
        llm, nguồn = sinh_va_llm(gốc, lỗi[0], lỗi[1], out)
        if llm:
            print(f"  [Stage 5/LLM] {len(llm)} bản-vá từ {nguồn} (vẫn qua cổng CDFL regression-safe)")
            if _chạy_ứng_viên(đích, test, kèm, gốc, llm, "LLM", max_thử, ai=f"llm:{nguồn}"):
                return True
        else:
            print(f"  [Stage 5/LLM] bỏ qua: {nguồn}")
    print("  ✗ Không bản-vá nào vừa làm đích sáng vừa giữ test khác" + ("" if dùng_llm else " (rule-based bất-lực → bật --llm cho lỗi tổng-quát)") + ".")
    return False

# ── STAGE 4: ĐỊNH-VỊ lỗi (spectrum) — TỰ tìm tệp lỗi từ test-suite, KHÔNG cần chỉ đích ──
def _imports(test_path):
    return set(re.findall(r'nhập\s+"([^"]+)"', open(test_path, encoding="utf-8").read()))

def định_vị(tests):
    "Chạy suite → tệp xuất-hiện ở test-FAIL nhưng KHÔNG ở test-PASS = NGHI cao nhất (spectrum)."
    imp_fail, imp_pass, failing = set(), set(), []
    for t in tests:
        out = chạy_test(t); imp = _imports(t)
        if đọc_lỗi(out) is None: imp_pass |= imp
        else: imp_fail |= imp; failing.append(t)
    nghi = sorted(imp_fail - imp_pass) or sorted(imp_fail)   # ưu tiên CHỈ-trong-fail
    return nghi, failing

def vòng_suite(targets, tests, dùng_llm=False):
    "Stage 4: ĐỊNH-VỊ tệp lỗi rồi REPAIR (Stage 1-3, +5 nếu --llm). targets = tệp ĐƯỢC PHÉP sửa."
    print("="*74); print(f"STAGE 4 — ĐỊNH-VỊ + TỰ-SỬA (suite {len(tests)} test, {len(targets)} đích" + (", +LLM" if dùng_llm else "") + ")"); print("="*74)
    nghi, failing = định_vị(tests)
    print(f"  [định-vị] nghi (spectrum, chỉ-ở-test-fail): {nghi}")
    for target in nghi:
        if target not in targets: continue
        for t in failing:
            if target in _imports(t):
                print(f"  [chọn] sửa '{target}' (test fail: {t})")
                if vòng(target, t, tests_kèm=tests, dùng_llm=dùng_llm): return True   # regression-safe: giữ-sáng TOÀN suite
    print("  ✗ không định-vị/sửa được trong tầm Stage 1-5."); return False

if __name__ == "__main__":
    # cờ --llm: bật Stage 5 (host-LLM) khi rule-based bó tay (cần ANTHROPIC_API_KEY hoặc Ollama).
    dùng_llm = "--llm" in sys.argv
    NHẬN_ẨN = "--nhận-ẩn" in sys.argv or "--nhan-an" in sys.argv
    av = [a for a in sys.argv if a not in ("--llm", "--nhận-ẩn", "--nhan-an")]
    def _mã(ok): return 0 if ok else (2 if KẾT_QUẢ["trạng_thái"] == "ẩn" else 1)
    if av[1] == "--suite":
        sep = av.index("--")
        sys.exit(_mã(vòng_suite(av[2:sep], av[sep+1:], dùng_llm=dùng_llm)))
    đích, test = av[1], av[2]
    sys.exit(_mã(vòng(đích, test, dùng_llm=dùng_llm)))

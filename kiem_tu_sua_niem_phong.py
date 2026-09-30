# -*- coding: utf-8 -*-
"""kiem_tu_sua_niem_phong.py — kiểm NIÊM PHONG dự đoán cho bản vá do LLM đề xuất (vòng tự-sửa Stage 5).
Máy kiểm không có API LLM thật ⇒ thay sinh_va_llm bằng hàm GIẢ (một lần đề xuất ĐÚNG, một lần SAI).
Đòi: mỗi đề xuất được niêm phong TRƯỚC khi áp, chấm SAU cổng; đề xuất sai bị chấm TRƯỢT; sổ toàn vẹn."""
import os, sys, tempfile, shutil
P = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, P)
thư = tempfile.mkdtemp(); os.environ["GIAO_SO_NIEM_PHONG"] = os.path.join(thư, "so.jsonl")
os.chdir(P)
import io, contextlib, vong_tu_sua
from niem_phong import SổNiêmPhong

đích = "_tnp_dich.giao"; test = "_tnp_test.giao"
LỖI = "hàm hiệu(a, b) { trả b - a }\n"               # luật (hằng/toán tử/±1) KHÔNG sửa được: phải đảo toán hạng
TEST = 'nhập "_tnp_dich.giao"\nđặt g = hiệu(5, 3)\nnếu g == 2 { rọi "PASS" } khác { rọi "FAIL expected 2 got " + g }\n'
T = R = 0
def kiểm(tên, đk, ct=""):
    global T, R; T += 1; R += 0 if đk else 1
    print(f"  {'✓' if đk else '✗'} {tên}" + ("" if đk else f"   {ct}"))
def chạy(đề_xuất):
    open(đích, "w", encoding="utf-8").write(LỖI); open(test, "w", encoding="utf-8").write(TEST)
    vong_tu_sua.sinh_va_llm = lambda gốc, e, g, t: ([đề_xuất], "giả")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): ok = vong_tu_sua.vòng(đích, test, dùng_llm=True)
    return ok, buf.getvalue(), open(đích, encoding="utf-8").read()
try:
    ok, out, sau = chạy("hàm hiệu(a, b) { trả a - b }\n")
    kiểm("LLM đề xuất ĐÚNG → vá được nhận (sáng)", ok and "trả a - b" in sau, out[-400:])
    kiểm("… dự đoán được NIÊM PHONG trước khi áp, chấm TRÚNG sau", "[niêm phong]" in out and "[chấm] TRÚNG" in out, out[-400:])
    ok, out, sau = chạy("hàm hiệu(a, b) { trả a * b }\n")
    kiểm("LLM đề xuất SAI → không nhận, file giữ nguyên", not ok and sau == LỖI, out[-400:])
    kiểm("… vẫn niêm phong trước, chấm TRƯỢT (lệch đích_sáng)", "[chấm] TRƯỢT" in out and "đích_sáng" in out, out[-400:])
    sổ = SổNiêmPhong(); toàn, lý = sổ.kiểm_chuỗi(); tk = sổ.thống_kê().get("llm:giả", {})
    kiểm("sổ toàn vẹn + thống kê: 2 chấm, 1 trúng", toàn and tk.get("đã_chấm") == 2 and tk.get("trúng") == 1, (lý, tk))
finally:
    for f in (đích, test):
        if os.path.exists(f): os.remove(f)
    shutil.rmtree(thư, ignore_errors=True)
print(f"NIÊM PHONG TỰ-SỬA: {T - R}/{T} đạt")
sys.exit(1 if R else 0)

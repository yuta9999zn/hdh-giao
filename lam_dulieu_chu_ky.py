# -*- coding: utf-8 -*-
"""
lam_dulieu_chu_ky.py — sinh DỮ LIỆU CỐ ĐỊNH cho `kiem_chu_ky.giao`
================================================================================
Sinh hai cặp khoá: **kho thật** và **kho giả mạo**. Kho giả mạo có mục lục hợp lệ, băm gói đúng
y như thật — chỉ khác chỗ nó ký bằng khoá của CHÍNH NÓ. Đó đúng là ca mà chỉ có băm thì không
cứu nổi, và là lý do phải có chữ ký.

    python lam_dulieu_chu_ky.py      # ghi đè kiem_chu_ky_dulieu.giao

Chạy lại chỉ khi muốn đổi khoá; dữ liệu sinh ra là CỐ ĐỊNH nên bài kiểm tất định.
"""
import os, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lam_khoa

THÂN = '# nền\nnói "nền"'
THÂN_SAU = '# cửa_sau — gói của kho GIẢ MẠO\nnói "cửa sau"'


def _khoá(bit=2048):
    "Sinh một cặp khoá và trả (d, e, n) — không đụng tệp khoá của dự án."
    p = lam_khoa._nguyên_tố(bit // 2)
    q = lam_khoa._nguyên_tố(bit // 2)
    while q == p: q = lam_khoa._nguyên_tố(bit // 2)
    n = p * q
    d = pow(lam_khoa.E, -1, (p - 1) * (q - 1) // lam_khoa._ước_chung(p - 1, q - 1))
    return d, lam_khoa.E, n


def _ký(nội, d, n):
    k = (n.bit_length() + 7) // 8
    return f"{pow(int(lam_khoa._khuôn(nội, k), 16), d, n):0{k * 2}x}"


def main():
    d1, e1, n1 = _khoá()          # kho THẬT
    d2, e2, n2 = _khoá()          # kho GIẢ MẠO
    b = hashlib.sha256(THÂN.encode("utf-8")).hexdigest()
    b2 = hashlib.sha256(THÂN_SAU.encode("utf-8")).hexdigest()

    mục = f"nền|1.0|Nền|||{b}|gói nền"
    mục_sửa = f"nền|9.9|Nền|||{b}|gói nền ĐÃ BỊ SỬA"
    # kho giả mạo: mục lục HỢP LỆ, băm ĐÚNG — chỉ khác ở chỗ ký bằng khoá của nó
    mục_giả = f"nền|1.0|Nền|||{b}|gói nền\ncửa_sau|1.0|Nền|||{b2}|gói của kho giả mạo"

    def th(s):        # thoát cho chuỗi GIAO: dấu nháy và xuống dòng
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    d = [
        "# kiem_chu_ky_dulieu.giao — SINH TỰ ĐỘNG bởi lam_dulieu_chu_ky.py, ĐỪNG sửa tay.",
        "# Kho THẬT và kho GIẢ MẠO: mục lục kho giả cũng hợp lệ, băm cũng đúng — khác mỗi chữ ký.",
        f'đặt CK_THÂN = "{th(THÂN)}"',
        f'đặt CK_MỤC = "{th(mục)}"',
        f'đặt CK_MỤC_SỬA = "{th(mục_sửa)}"',
        f'đặt CK_MỤC_GIẢ = "{th(mục_giả)}"',
        f'đặt CK_N = "{n1:x}"',
        f'đặt CK_KHOÁ = "rsa|{e1}|{n1:x}"',
        f'đặt CK_KÝ = "{_ký(mục, d1, n1)}"',
        f'đặt CK_N_GIẢ = "{n2:x}"',
        f'đặt CK_KHOÁ_GIẢ = "rsa|{e2}|{n2:x}"',
        f'đặt CK_KÝ_GIẢ = "{_ký(mục_giả, d2, n2)}"',
    ]
    ra = os.path.join(HERE, "kiem_chu_ky_dulieu.giao")
    with open(ra, "w", encoding="utf-8") as f:
        f.write("\n".join(d) + "\n")
    print(f"  ✓ {ra}")
    print(f"  vân tay kho THẬT: {hashlib.sha256(f'{n1:x}'.encode()).hexdigest()[:16]}")
    print(f"  vân tay kho GIẢ : {hashlib.sha256(f'{n2:x}'.encode()).hexdigest()[:16]}")


if __name__ == "__main__":
    main()

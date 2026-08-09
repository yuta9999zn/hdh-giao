# -*- coding: utf-8 -*-
"""
lam_kho.py — DỰNG MỤC LỤC KHO cho HĐH-GIAO (băm SHA-256 thật của từng thân gói)
================================================================================
Học apt/Kali: mục lục mang BĂM của mọi thứ ⇒ tin mục lục là tin cả kho. Khác apt: mỗi gói còn
TỰ KHAI NĂNG LỰC nó cần, và gói chỉ là DỮ LIỆU (thân lệnh) — không có script chạy quyền gốc lúc cài.

    python lam_kho.py            # in ra đoạn GIAO để dán vào hdh_nền.giao
    python lam_kho.py --kiểm     # đối chiếu băm trong hdh_nền.giao với thân gói
"""
import sys, hashlib

# tên | nhóm | phụ thuộc | năng lực | mô tả | THÂN LỆNH (kịch bản vỏ GIAO)
GÓI = [
    ("đo_đĩa", "1.0", "Hệ thống", "", "",
     "xem tình trạng chỗ trống",
     '# đo_đĩa — xem nhanh chỗ trống\nnói "── đĩa ──"\nliệt /tạm | đếm\nnói "tệp trong /tạm"'),

    ("soi_người", "1.0", "An toàn", "", "",
     "liệt kê người dùng và nhóm",
     '# soi_người — ai đang có trên máy\nnói "── người ──"\nngười\nnói "── nhóm ──"\nnhóm'),

    ("gác_cổng", "1.2", "An toàn", "soi_người", "",
     "soi quyền: ai đọc được gì",
     '# gác_cổng — soi quyền trên một đường dẫn\nsoi_người\nnói "── vì sao ──"\nvì_sao /hệ/mật_khẩu'),

    ("nhật_ký_gọn", "1.0", "Hệ thống", "", "",
     "xem 20 dòng audit gần nhất",
     '# nhật_ký_gọn\nnhật_ký 20'),

    ("dọn_nhà", "2.0", "Tệp", "đo_đĩa", "xoá",
     "dọn thư mục tạm (đòi năng lực xoá)",
     '# dọn_nhà — dọn /tạm\nđo_đĩa\nnói "(bản demo: chỉ liệt kê, không xoá gì)"\nliệt /tạm'),

    ("bộ_hệ_thống", "1.0", "Siêu-gói", "đo_đĩa,nhật_ký_gọn,soi_người", "",
     "SIÊU-GÓI: gom bộ công cụ soi hệ thống (học kali-linux-headless)",
     '# bộ_hệ_thống — siêu-gói: chạy cả bộ\nđo_đĩa\nnhật_ký_gọn\nsoi_người'),
]


def _thoát(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def dựng():
    import lam_khoa
    dòng_mục = []
    dòng_thân = []
    for tên, phiên, nhóm, pt, nl, mô, thân in GÓI:
        băm = hashlib.sha256(thân.encode("utf-8")).hexdigest()
        dòng_mục.append(f"{tên}|{phiên}|{nhóm}|{pt}|{nl}|{băm}|{mô}")
        dòng_thân.append(f'    gọi(M, khởi, GH_TẠO, ["/hệ/kho/gói/{tên}", 644, "{_thoát(thân)}"])')
    mục_thật = "\n".join(dòng_mục)               # chuỗi THẬT (xuống dòng thật) — đây là thứ được KÝ
    mục = "\\n".join(dòng_mục)                   # bản escape để nhét vào mã nguồn GIAO
    with open(lam_khoa.TỆP_CÔNG, encoding="utf-8") as f:
        khoá_công = f.read().strip()
    chữ_ký = lam_khoa.ký(mục_thật)               # ký BÊN NGOÀI — khoá riêng không vào máy
    ra = []
    ra.append('    gọi(M, khởi, GH_TẠO_THƯ, ["/hệ/kho", 755])')
    ra.append('    gọi(M, khởi, GH_TẠO_THƯ, ["/hệ/kho/gói", 755])')
    ra.extend(dòng_thân)
    ra.append(f'    gọi(M, khởi, GH_TẠO, ["/hệ/kho/mục_lục", 644, "{mục}"])')
    ra.append('    # ★ I1: NEO TIN CẬY — mỗi nguồn khai đúng một khoá công của riêng nó (học `Signed-By:`)')
    ra.append(f'    gọi(M, khởi, GH_TẠO, ["/hệ/kho/khoá_công", 644, "{khoá_công}"])')
    ra.append(f'    gọi(M, khởi, GH_TẠO, ["/hệ/kho/mục_lục.ký", 644, "{chữ_ký}"])')
    ra.append('    gọi(M, khởi, GH_TẠO, ["/hệ/kho/nguồn", 644,'
              ' "kho-nhà|/hệ/kho/mục_lục|/hệ/kho/mục_lục.ký|/hệ/kho/khoá_công"])')
    ra.append('    gọi(M, khởi, GH_TẠO, ["/hệ/gói_đã_cài", 644, ""])')
    return "\n".join(ra)


if __name__ == "__main__":
    if "--kiểm" in sys.argv or "--kiem" in sys.argv:
        import os
        nền = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hdh_nền.giao")
        with open(nền, encoding="utf-8") as f:
            src = f.read()
        import lam_khoa
        rớt = 0
        dòng_mục = []
        for tên, phiên, nhóm, pt, nl, mô, thân in GÓI:
            băm = hashlib.sha256(thân.encode("utf-8")).hexdigest()
            dòng_mục.append(f"{tên}|{phiên}|{nhóm}|{pt}|{nl}|{băm}|{mô}")
            if băm not in src:
                print(f"  ✗ băm của '{tên}' không có trong hdh_nền.giao"); rớt += 1
            if f'/hệ/kho/gói/{tên}' not in src:
                print(f"  ✗ thân gói '{tên}' chưa được dựng lúc boot"); rớt += 1
        # ★ I1: chữ ký trong hdh_nền.giao phải ĐÚNG với mục lục ấy và khoá công hiện có
        mục_thật = "\n".join(dòng_mục)
        import re
        m = re.search(r'/hệ/kho/mục_lục\.ký", 644, "([0-9a-f]+)"', src)
        if not m:
            print("  ✗ hdh_nền.giao chưa mang chữ ký mục lục"); rớt += 1
        elif not lam_khoa.kiểm(mục_thật, m.group(1)):
            print("  ✗ CHỮ KÝ trong hdh_nền.giao KHÔNG khớp mục lục (chạy lại `python lam_kho.py`)"); rớt += 1
        print("  ✓ mục lục kho khớp thân gói VÀ đúng chữ ký" if not rớt else f"  {rớt} chỗ lệch")
        sys.exit(1 if rớt else 0)
    print(dựng())

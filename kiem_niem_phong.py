# -*- coding: utf-8 -*-
"""kiem_niem_phong.py — kiểm SỔ NIÊM PHONG: chuỗi băm phát hiện SỬA / XOÁ / CHÈN / ĐỔI THỨ TỰ;
không chấm niêm phong không tồn tại; không chấm lại; thống kê so với ĐƯỜNG NỀN."""
import os, sys, json, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from niem_phong import SổNiêmPhong, dòng_sổ

T = R = 0
def kiểm(tên, đk, ct=""):
    global T, R; T += 1; R += 0 if đk else 1
    print(f"  {'✓' if đk else '✗'} {tên}" + ("" if đk else f"   {ct}"))

thư = tempfile.mkdtemp()
try:
    sổ = SổNiêmPhong(os.path.join(thư, "so.jsonl"))
    b = [sổ.niêm_phong("llm", f"việc {i}", {"thành_công": True}) for i in range(6)]
    for i, x in enumerate(b): sổ.chấm(x, {"thành_công": i != 3})          # 5 trúng, 1 trượt
    ok, lý = sổ.kiểm_chuỗi(); kiểm("sổ gốc: chuỗi nguyên vẹn", ok, lý)
    tk = sổ.thống_kê()["llm"]
    kiểm("thống kê: 6 chấm · 5 trúng · đường nền 5/6 · hơn nền 0 (đoán 'luôn thành công' cũng ngang)",
         tk["đã_chấm"] == 6 and tk["trúng"] == 5 and tk["đường_nền"] == round(5/6, 3) and tk["hơn_nền"] == 0.0, tk)

    dòng = open(sổ.đường_dẫn, encoding="utf-8").read().splitlines()
    def thử_sửa(tên, dòng_mới):
        f = os.path.join(thư, "hong.jsonl"); open(f, "w", encoding="utf-8").write("\n".join(dòng_mới) + "\n")
        ok, lý = SổNiêmPhong(f).kiểm_chuỗi(); kiểm(tên, not ok, lý); return lý
    m = json.loads(dòng[9]); m["trúng"] = True                                  # sửa điểm lần chấm TRƯỢT (i=3) thành trúng
    thử_sửa("SỬA kết quả một lần chấm → phát hiện", dòng[:9] + [dòng_sổ(m)] + dòng[10:])
    thử_sửa("XOÁ một mục → phát hiện", dòng[:4] + dòng[5:])
    thử_sửa("ĐỔI THỨ TỰ hai mục → phát hiện", dòng[:2] + [dòng[3], dòng[2]] + dòng[4:])
    m = json.loads(dòng[1]); m["dự_đoán"] = {"thành_công": False}; m["băm"] = __import__("niem_phong")._băm(m)
    thử_sửa("SỬA dự đoán rồi TÍNH LẠI băm của mục đó → vẫn đứt chuỗi ở mục sau", dòng[:1] + [dòng_sổ(m)] + dòng[2:])

    try: sổ.chấm("f" * 64, {"thành_công": True}); kiểm("chấm niêm phong không tồn tại → từ chối", False)
    except ValueError: kiểm("chấm niêm phong không tồn tại → từ chối", True)
    try: sổ.chấm(b[0], {"thành_công": False}); kiểm("chấm LẠI → từ chối", False)
    except ValueError: kiểm("chấm LẠI → từ chối", True)
finally:
    shutil.rmtree(thư, ignore_errors=True)
print(f"SỔ NIÊM PHONG: {T - R}/{T} đạt")
sys.exit(1 if R else 0)

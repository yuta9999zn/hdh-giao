# -*- coding: utf-8 -*-
"""
KIỂM TỰ THÂN HOÁ — giaoc64.giao (trình biên dịch viết bằng GIAO, chạy trên GVM-64) phải cho ra .g64
TRÙNG TỪNG BYTE với giaoc64.py, trên MỌI chương trình GIAO của dự án.
    python kiem_tu_bien_dich.py [tệp.giao …]
Ngoài ra kiểm ĐIỂM BẤT ĐỘNG: giaoc64.giao tự biên dịch chính nó → phải trùng bản mồi do giaoc64.py dịch.
Python ở đây CHỈ là bộ kiểm (so byte); việc biên dịch được kiểm là của GVM-64.
"""
import os, sys, glob, subprocess, shutil
P = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, P)
from giaoc64 import biên_dịch_tệp
TU = os.path.join(P, "wasm", "giaoc64_tu.g64")
SH = shutil.which("sh") or r"C:\Program Files\Git\usr\bin\sh.exe"

def tự_dịch(tệp, tu=TU):
    env = dict(os.environ, GIAOC64_TU=tu)
    r = subprocess.run([SH, os.path.join(P, "tu_bien_dich.sh"), tệp], capture_output=True, env=env, timeout=600)
    return r.returncode, r.stdout, r.stderr.decode("utf-8", "replace")

def main():
    # bản mồi luôn dựng lại từ nguồn hiện hành (để kiểm đúng giaoc64.giao đang có)
    with open(TU, "wb") as f: f.write(biên_dịch_tệp(os.path.join(P, "giaoc64.giao")))
    ds = sys.argv[1:] or sorted(set(glob.glob(os.path.join(P, "*.giao")) + glob.glob(os.path.join(P, "examples", "*.giao"))))
    khớp = lệch = cả_hai_lỗi = 0
    for tệp in ds:
        tên = os.path.relpath(tệp, P)
        try: kỳ = biên_dịch_tệp(tệp); lỗi_py = None
        except Exception as e: kỳ = None; lỗi_py = f"{type(e).__name__}"
        mã, ra, lỗi = tự_dịch(tệp)
        if kỳ is None:
            if mã != 0: cả_hai_lỗi += 1; print(f"  · {tên:<44} cả hai cùng từ chối ({lỗi_py})")
            else: lệch += 1; print(f"  ✗ {tên:<44} Python từ chối ({lỗi_py}) mà GIAO lại dịch được")
        elif mã == 0 and ra == kỳ: khớp += 1
        else:
            lệch += 1
            chỗ = next((i for i in range(min(len(ra), len(kỳ))) if ra[i] != kỳ[i]), min(len(ra), len(kỳ)))
            print(f"  ✗ {tên:<44} LỆCH (mã {mã}, {len(ra)} vs {len(kỳ)} byte, khác từ byte {chỗ}) {lỗi.strip()[-200:]}")
    # điểm bất động: trình biên dịch GIAO tự dịch chính nó
    mã, ra, lỗi = tự_dịch(os.path.join(P, "giaoc64.giao"))
    mồi = open(TU, "rb").read()
    bất_động = mã == 0 and ra == mồi
    if bất_động:
        tu2 = os.path.join(P, "__pycache__", "giaoc64_tu2.g64"); os.makedirs(os.path.dirname(tu2), exist_ok=True)
        open(tu2, "wb").write(ra)
        m2, r2, _ = tự_dịch(os.path.join(P, "giaoc64.giao"), tu=tu2)       # thế hệ 2 dịch lại → vẫn trùng
        bất_động = m2 == 0 and r2 == mồi
    print(f"  {'✓' if bất_động else '✗'} điểm bất động: giaoc64.giao tự biên dịch chính nó (2 thế hệ) "
          f"{'TRÙNG từng byte bản mồi' if bất_động else 'LỆCH: ' + lỗi.strip()[-200:]}")
    print(f"\nKẾT QUẢ TỰ BIÊN DỊCH: {khớp} trùng từng byte · {lệch} lệch · {cả_hai_lỗi} cả hai cùng từ chối · "
          f"điểm bất động {'đạt' if bất_động else 'RỚT'}")
    sys.exit(0 if lệch == 0 and bất_động else 1)

if __name__ == "__main__":
    main()

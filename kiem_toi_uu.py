# -*- coding: utf-8 -*-
"""
kiem_toi_uu.py — CONFORMANCE tầng TỐI-ƯU BYTECODE (★ Pha 3 — Track C).
Cho MỖI ví-dụ máy: biên-dịch KHÔNG tối-ưu vs CÓ tối-ưu, chạy GVM, KHẲNG ĐỊNH:
  (1) output (self.xuất) KHỚP BYTE  — tối-ưu KHÔNG đổi ngữ-nghĩa.
  (2) số-bước CÓ-tối-ưu ≤ KHÔNG-tối-ưu — thật-sự giảm việc.
In tổng % giảm bytecode + bước.
   PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python kiem_toi_uu.py
"""
import glob, os, io, contextlib, sys
import giaoc
from giaoc import compile_source_bit
from gvm_may import GVM

def _chạy(src, opt):
    giaoc.GiaoC.BẬT_TỐI_ƯU = opt
    words, bit = compile_source_bit(src)
    g = GVM(words, world={}, bit=bit)
    with contextlib.redirect_stdout(io.StringIO()):
        g.run(max_steps=5_000_000)
    return words, g.xuất, g.steps_run

def kiểm_luật():
    "Unit-test TỪNG TẦNG optimizer (peephole/DCE/siêu-lệnh) + rào NHÃN — provably-safe, độc-lập corpus."
    from giaoc import _peephole as P, _dce as D, _siêu_lệnh as S, _abs_interp as A
    ca = [
        (P, [("DỊCH_TRÁI",8),("DỊCH_TRÁI",16)], [("DỊCH_TRÁI",24)]),               # L1 gộp-dịch
        (P, [("NẠP",2),("NẠP",3),("CỘNG",0)], [("NẠP",5)]),                        # L2 +
        (P, [("NẠP",6),("NẠP",7),("NHÂN",0)], [("NẠP",42)]),                       # L2 ×
        (P, [("NẠP",5),("NẠP",5),("BẰNG",0)], [("NẠP",1)]),                        # L2 so-sánh
        (P, [("NẠP",20),("NẠP",4),("CHIA",0)], [("NẠP",5)]),                       # L2 //
        (P, [("NẠP",200),("NẠP",100),("CỘNG",0)], [("NẠP",200),("NẠP",100),("CỘNG",0)]),  # >255 KHÔNG fold
        (P, [("NẠP",1),("DỊCH_TRÁI",4)], [("NẠP",16)]),                            # L3
        (P, [("NẠP",8),("NHÂN",0)], [("DỊCH_TRÁI",3)]),                            # L4 strength
        (P, [("NHÂN_BẢN",0),("BỎ",0)], []),                                        # L5
        (P, [("ĐỔI",0),("ĐỔI",0)], []),                                            # L6
        (P, [("NẠP",2),("NHÃN","@l"),("NẠP",3),("CỘNG",0)], [("NẠP",2),("NHÃN","@l"),("NẠP",3),("CỘNG",0)]),  # RÀO NHÃN (peephole)
        (P, [("NẠP",2),("NẠP",3),("NHÂN",0),("NẠP",4),("CỘNG",0)], [("NẠP",10)]),  # chuỗi fold lồng
        (D, [("DỪNG",0),("NẠP",9),("NHÃN","@x"),("NẠP",1)], [("DỪNG",0),("NHÃN","@x"),("NẠP",1)]),  # DCE
        (S, [("NẠP",7),("CỘNG",0)], [("CỘNG_HẰNG",7)]),                            # ★ SIÊU-LỆNH #1 add-immediate
        (S, [("NẠP",5),("NHÃN","@l"),("CỘNG",0)], [("NẠP",5),("NHÃN","@l"),("CỘNG",0)]),  # siêu-lệnh KHÔNG xuyên NHÃN
        (S, [("NHÂN_BẢN",0),("NẠP",2),("CỘNG",0)], [("NHÂN_CỘNG_HẰNG",2)]),         # ★ SIÊU-LỆNH #2 dup+add-imm (2 lượt)
        (S, [("NHÂN_BẢN",0),("NHÃN","@l"),("NẠP",2),("CỘNG",0)], [("NHÂN_BẢN",0),("NHÃN","@l"),("CỘNG_HẰNG",2)]),  # #2 KHÔNG xuyên NHÃN
        (S, [("NHÂN_BẢN",0),("TẢI_Ô",5),("LƯU_GIÁN",0)], [("GHI_TRƯỜNG",5)]),        # ★ SIÊU-LỆNH #3 store-field
        (S, [("NHÂN_BẢN",0),("TẢI_Ô",5),("NHÃN","@l"),("LƯU_GIÁN",0)], [("NHÂN_BẢN",0),("TẢI_Ô",5),("NHÃN","@l"),("LƯU_GIÁN",0)]),  # #3 KHÔNG xuyên NHÃN
        (S, [("DỊCH_TRÁI",8),("NẠP",5),("CỘNG",0)], [("DỊCH_CỘNG_BYTE",5)]),       # ★ SIÊU-LỆNH #4 dựng-hằng end-to-end (lượt1 NẠP;CỘNG→CỘNG_HẰNG, lượt4 gộp)
        (S, [("NẠP",3),("DỊCH_TRÁI",8),("NẠP",232),("CỘNG",0)], [("NẠP",3),("DỊCH_CỘNG_BYTE",232)]),  # #4 hằng 1000 = 3·256+232 → 2 lệnh thay 4
        (S, [("DỊCH_TRÁI",16),("CỘNG_HẰNG",5)], [("DỊCH_TRÁI",16),("CỘNG_HẰNG",5)]),  # #4 shift≠8 KHÔNG gộp (giữ ngữ-nghĩa dịch khác)
        (S, [("DỊCH_TRÁI",8),("NHÃN","@l"),("CỘNG_HẰNG",5)], [("DỊCH_TRÁI",8),("NHÃN","@l"),("CỘNG_HẰNG",5)]),  # #4 KHÔNG xuyên NHÃN
        # ★ PHA A — abstract-interp const/copy-prop XUYÊN-LỆNH (sound):
        (A, [("NẠP",5),("LƯU_Ô",3),("TẢI_Ô",3)], [("NẠP",5),("LƯU_Ô",3),("NẠP",5)]),                          # propagation: TẢI_Ô ô-hằng → NẠP 5
        (A, [("NẠP",5),("LƯU_Ô",3),("NHÃN","@l"),("TẢI_Ô",3)], [("NẠP",5),("LƯU_Ô",3),("NHÃN","@l"),("TẢI_Ô",3)]),  # rào NHÃN (join không-rõ) → GIỮ
        (A, [("NẠP",5),("LƯU_Ô",3),("LƯU_GIÁN",0),("TẢI_Ô",3)], [("NẠP",5),("LƯU_Ô",3),("LƯU_GIÁN",0),("TẢI_Ô",3)]),  # clobber gián-tiếp → GIỮ
        (A, [("NẠP",5),("LƯU_Ô",3),("GỌI_N",1),("TẢI_Ô",3)], [("NẠP",5),("LƯU_Ô",3),("GỌI_N",1),("TẢI_Ô",3)]),  # callee có thể ghi ô → GIỮ
        (A, [("NẠP",9),("LƯU_Ô",3),("NẠP",7),("LƯU_Ô",3),("TẢI_Ô",3)], [("NẠP",9),("LƯU_Ô",3),("NẠP",7),("LƯU_Ô",3),("NẠP",7)]),  # ghi-đè: lấy hằng MỚI nhất
        (A, [("ẨN",0),("LƯU_Ô",3),("TẢI_Ô",3)], [("ẨN",0),("LƯU_Ô",3),("TẢI_Ô",3)]),                          # lưu trị KHÔNG-rõ → KHÔNG prop
    ]
    return sum(1 for fn, vào, ra in ca if fn(list(vào)) == list(ra)), len(ca)

def chạy_kiểm():
    P = os.path.dirname(os.path.abspath(__file__))
    exs = sorted(glob.glob(os.path.join(P, "examples", "*_gvm.giao")))
    exs += [os.path.join(P, "examples", x) for x in ("giai_thua.giao", "giaoc.giao")]
    tot0 = tot1 = lw0 = lw1 = ok = 0
    rớt = []
    for f in exs:
        src = open(f, encoding="utf-8").read()
        try:
            w0, x0, s0 = _chạy(src, False)
            w1, x1, s1 = _chạy(src, True)
        except Exception as e:
            rớt.append((os.path.basename(f), "EXC " + str(e)[:50])); continue
        if x0 != x1:
            rớt.append((os.path.basename(f), "OUTPUT KHÁC")); continue
        if s1 > s0:
            rớt.append((os.path.basename(f), f"bước TĂNG {s0}->{s1}")); continue
        ok += 1; tot0 += s0; tot1 += s1; lw0 += len(w0); lw1 += len(w1)
    giaoc.GiaoC.BẬT_TỐI_ƯU = True
    gb = 100 * (lw0 - lw1) / max(1, lw0)
    gs = 100 * (tot0 - tot1) / max(1, tot0)
    return ok, len(exs), rớt, gb, gs

if __name__ == "__main__":
    lo, ln = kiểm_luật()
    print(f"Unit-test luật optimizer: {lo}/{ln} (provably-safe + rào NHÃN)")
    ok, n, rớt, gb, gs = chạy_kiểm()
    print(f"TỐI-ƯU conformance: {ok}/{n} ví-dụ — output KHỚP BYTE + bước giảm")
    print(f"  bytecode −{gb:.1f}% · bước GVM −{gs:.1f}%")
    if rớt:
        print("  RỚT:", rớt); sys.exit(1)
    đạt = (lo == ln and ok == n)
    print("  ✓ ĐẠT" if đạt else "  ✗")
    sys.exit(0 if đạt else 1)

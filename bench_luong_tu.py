# -*- coding: utf-8 -*-
"""
ĐO SỨC THẬT lib_lượng_tử.giao — thời gian + RAM đỉnh, mạch QFT và mạch ngẫu nhiên.

   python bench_luong_tu.py                      # QFT + ngẫu nhiên ở 20 24 26 qubit, lõi mảng
   python bench_luong_tu.py --cỡ 10 14 --lõi thuần
   python bench_luong_tu.py --qiskit <python_có_qiskit>   # chạy CÙNG mạch trên Qiskit Aer để so

Mỗi ca chạy trong MỘT TIẾN TRÌNH RIÊNG → RAM đỉnh (peak working set, psutil) không lẫn giữa các ca.
GIAO dựng mạch rồi xuất OpenQASM 2.0 → Qiskit đọc ĐÚNG mạch đó (không phải mạch "tương tự").
Ở ≤ 20 qubit, trạng thái cuối của GIAO được lưu để bench_qiskit.py đo độ trung thực với Aer.
Kết quả: bench_luong_tu.json (+ in bảng). numpy chỉ dùng để ghi .npy — không nằm trong đường đo.
"""
import os, sys, json, time, subprocess, io, contextlib
P = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(P, "__pycache__", "bench_lt")
ĐỘ_SÂU = 5                                     # mạch ngẫu nhiên: 5 lớp (RY+RZ mọi qubit + CZ xen kẽ)

def mã_mạch(loại, n):
    return f"mạch_qft({n})" if loại == "qft" else f"mạch_ngẫu_nhiên({n}, {ĐỘ_SÂU}, 2026)"

def một_ca(loại, n, lõi):
    "Chạy trong tiến trình con: dựng mạch, áp cổng (đo giờ), trả dict."
    t0 = time.perf_counter()
    sys.setrecursionlimit(40000); sys.path.insert(0, P)
    from giao import tokenize, Parser, Runtime, nạp_chuẩn
    import psutil
    rt = Runtime(); rt.base_dir = P; rt.MAX_STEPS = 10 ** 13; rt.MAX_LIST = 1 << 31
    with contextlib.redirect_stdout(io.StringIO()):
        nạp_chuẩn(rt)
        rt.exec_block(Parser(tokenize('nhập "lib_lượng_tử.giao"\n' + ("dùng_lõi_mảng(tối)\n" if lõi == "thuần" else "") +
                                      f"đặt m = {mã_mạch(loại, n)}\nđặt qasm = sang_qasm(m)\nđặt ψ = trạng_thái({n})")).parse())
        t1 = time.perf_counter()
        rt.exec_block(Parser(tokenize('lặp l trong m["lệnh"] { _áp_lệnh(ψ, l) }')).parse())
        t2 = time.perf_counter()
        rt.exec_block(Parser(tokenize("đặt chuẩn = chuẩn_bình_phương(ψ)")).parse())
    os.makedirs(TMP, exist_ok=True)
    tên = f"{loại}_{n}"
    with open(os.path.join(TMP, tên + ".qasm"), "w", encoding="utf-8") as f: f.write(rt.glob["qasm"])
    if n <= 20:                                                  # lưu trạng thái để đo độ trung thực với Aer
        import numpy as np
        ψ = rt.glob["ψ"].d
        v = (np.array(ψ["v"].re) + 1j * np.array(ψ["v"].im)) if "v" in ψ else np.array(ψ["re"]) + 1j * np.array(ψ["im"])
        np.save(os.path.join(TMP, tên + f"_{lõi}.npy"), v)
    return {"bộ": f"GIAO ({lõi})", "mạch": loại, "n": n, "số_cổng": len(rt.glob["m"].d["lệnh"]),
            "giây_mô_phỏng": round(t2 - t1, 3), "giây_dựng": round(t1 - t0, 3),
            "ram_đỉnh_MB": round(psutil.Process().memory_info().peak_wset / 2 ** 20),
            "chuẩn": rt.glob["chuẩn"]}

def chạy_tiến_trình(args, py=sys.executable):
    r = subprocess.run([py] + args, capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"), cwd=P)
    for d in reversed((r.stdout or "").splitlines()):
        if d.startswith("{"): return json.loads(d)
    return {"lỗi": (r.stderr or r.stdout or "?").strip().splitlines()[-1:]}

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--một":                                     # tiến trình con
        print(json.dumps(một_ca(a[1], int(a[2]), a[3]), ensure_ascii=False)); sys.exit(0)
    cỡ = [20, 24, 26]; lõi = "mảng"; py_qiskit = None; loại_ds = ["qft", "ngẫu"]
    i = 0
    while i < len(a):
        if a[i] == "--cỡ":
            cỡ = []; i += 1
            while i < len(a) and not a[i].startswith("--"): cỡ.append(int(a[i])); i += 1
            continue
        if a[i] == "--lõi": lõi = a[i + 1]; i += 2; continue
        if a[i] == "--qiskit": py_qiskit = a[i + 1]; i += 2; continue
        if a[i] == "--mạch": loại_ds = [a[i + 1]]; i += 2; continue
        i += 1
    kq = []
    print(f"{'bộ':<26} {'mạch':<5} {'n':>3} {'cổng':>5} {'giây':>9} {'RAM đỉnh':>10}   ghi chú", flush=True)
    def in_dòng(d):
        if "lỗi" in d: print(f"  LỖI: {d['lỗi']}", flush=True); return
        ghi = f"⟨ψ|ψ⟩={d['chuẩn']:.10f}" if "chuẩn" in d else d.get("ghi_chú", "")
        print(f"{d['bộ']:<26} {d['mạch']:<5} {d['n']:>3} {d['số_cổng']:>5} {d['giây_mô_phỏng']:>9.2f} "
              f"{d['ram_đỉnh_MB']:>7} MB   {ghi}", flush=True)
    for n in cỡ:
        for loại in loại_ds:
            d = chạy_tiến_trình([os.path.join(P, "bench_luong_tu.py"), "--một", loại, str(n), lõi]); in_dòng(d); kq.append(d)
            if py_qiskit:
                for chế_độ in ("aer1", "aer", "numpy"):
                    d = chạy_tiến_trình([os.path.join(P, "bench_qiskit.py"), loại, str(n), chế_độ], py=py_qiskit)
                    in_dòng(d); kq.append(d)
    with open(os.path.join(P, "bench_luong_tu.json"), "w", encoding="utf-8") as f:
        json.dump(kq, f, ensure_ascii=False, indent=1)

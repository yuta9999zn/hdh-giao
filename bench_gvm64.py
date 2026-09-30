# -*- coding: utf-8 -*-
"""
ĐO SỨC lib_lượng_tử.giao trên GVM-64 (wasmtime) — thời gian + RAM đỉnh, QFT và mạch ngẫu nhiên.
    python bench_gvm64.py [--cỡ 20 24 26] [--qiskit <python_có_qiskit>] [--không-simd] [--ra tệp.json]
Chương trình GIAO do chính lib_lượng_tử.giao dựng mạch (mạch_qft / mạch_ngẫu_nhiên, như bench_luong_tu.py),
biên dịch bằng giaoc64, chạy trên gvm64.wasm dưới wasmtime — KHÔNG có Python lúc chạy.
Thời gian mô phỏng đo BÊN TRONG máy bằng giờ_hệ() (năng lực --cho-giờ) — không tính dựng mạch/khởi động.
Máy in vài biên độ với ĐỦ chữ số (số_chính_xác) → đối chiếu với Qiskit Aer trên CÙNG QASM do GIAO xuất.
"""
import os, sys, time, json, subprocess, shutil
P = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, P)
from giaoc64 import biên_dịch_tệp
import psutil

WASMTIME = shutil.which("wasmtime") or r"D:\wasmtime\wasmtime.exe"
TMP = os.path.join(P, "__pycache__", "bench_lt"); os.makedirs(TMP, exist_ok=True)
CỜ_MÁY = []                             # vd --không-simd (đo A/B trên cùng tệp máy)
CHỈ_SỐ = [0, 1, 12345, 777777]           # biên độ đem đối chiếu (lọc < 2^n)

def nguồn(loại, n):
    mạch = f"mạch_qft({n})" if loại == "qft" else f"mạch_ngẫu_nhiên({n}, 5, 2026)"
    ks = [k for k in CHỈ_SỐ if k < (1 << n)] + [(1 << n) - 1]
    return (f'nhập "lib_lượng_tử.giao"\nđặt m = {mạch}\nđặt ψ = trạng_thái({n})\n'
            f'rọi "cổng=" + dài(m["lệnh"])\nđặt t0 = giờ_hệ()\n'
            f'lặp l trong lệnh_để_chạy(m) {{ _áp_lệnh(ψ, l) }}\n'   # GỘP CỔNG (thời gian gộp tính vào)
            f'rọi "giây=" + số_chính_xác(giờ_hệ() - t0)\nrọi "chuẩn=" + số_chính_xác(chuẩn_bình_phương(ψ))\n'
            + "".join(f'đặt z = biên_độ(ψ, {k})\nrọi "a{k}=" + số_chính_xác(z[0]) + " " + số_chính_xác(z[1])\n' for k in ks)
            + 'rọi "qasm-bắt-đầu"\nrọi sang_qasm(m)\n')

def chạy(loại, n):
    tệp = os.path.join(P, f"_bench64_{loại}_{n}.giao")
    with open(tệp, "w", encoding="utf-8") as f: f.write(nguồn(loại, n))
    try: dữ = biên_dịch_tệp(tệp)
    finally: os.remove(tệp)
    g = os.path.join(TMP, f"{loại}_{n}.g64")
    with open(g, "wb") as f: f.write(dữ)
    với = open(g, "rb"); t0 = time.perf_counter()
    fo, fe = open(g + ".out", "wb"), open(g + ".err", "wb")          # tệp, KHÔNG pipe (pipe Windows nhỏ → nghẽn)
    pr = psutil.Popen([WASMTIME, "run", os.path.join(P, "wasm", "gvm64.wasm"), "--", "--cho-giờ"] + CỜ_MÁY,
                      stdin=với, stdout=fo, stderr=fe)
    đỉnh = 0
    while pr.poll() is None:
        try: đỉnh = max(đỉnh, pr.memory_info().peak_wset)
        except psutil.Error: pass
        time.sleep(0.05)
    pr.wait(); với.close(); fo.close(); fe.close(); tổng = time.perf_counter() - t0
    out = open(g + ".out", encoding="utf-8").read(); err = open(g + ".err", "rb").read()
    if pr.returncode != 0: return {"lỗi": err.decode("utf-8", "replace")[-300:]}
    trước, qasm = out.split("qasm-bắt-đầu\n", 1)
    kv = dict(d.split("=", 1) for d in trước.splitlines() if "=" in d)
    with open(os.path.join(TMP, f"{loại}_{n}.qasm"), "w", encoding="utf-8") as f: f.write(qasm)
    biên = {int(k[1:]): complex(*map(float, v.split())) for k, v in kv.items() if k.startswith("a")}
    return {"mạch": loại, "n": n, "số_cổng": int(kv["cổng"]), "giây_mô_phỏng": float(kv["giây"]),
            "giây_tiến_trình": round(tổng, 2), "ram_đỉnh_MB": round(đỉnh / 2**20), "chuẩn": float(kv["chuẩn"]),
            "biên_độ": {str(k): [v.real, v.imag] for k, v in biên.items()}}

KIỂM_AER = r'''
import sys, json, numpy as np
from qiskit import qasm2, transpile
from qiskit_aer import AerSimulator
qc = qasm2.load(sys.argv[1], custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS); qc.remove_final_measurements()
sim = AerSimulator(method="statevector", precision="double"); qc.save_statevector()
psi = np.asarray(sim.run(transpile(qc, sim, optimization_level=0), shots=1).result().get_statevector())
print(json.dumps({str(k): [psi[k].real, psi[k].imag] for k in map(int, sys.argv[2].split(","))}))
'''

if __name__ == "__main__":
    a = sys.argv[1:]; cỡ = [20, 24, 26]; py_q = None
    if "--cỡ" in a:
        i = a.index("--cỡ") + 1; cỡ = []
        while i < len(a) and not a[i].startswith("--"): cỡ.append(int(a[i])); i += 1
    if "--qiskit" in a: py_q = a[a.index("--qiskit") + 1]
    if "--không-simd" in a: CỜ_MÁY.append("--không-simd")
    ra = a[a.index("--ra") + 1] if "--ra" in a else "bench_gvm64.json"
    kq = []
    print(f"{'mạch':<5} {'n':>3} {'cổng':>5} {'giây mô phỏng':>14} {'RAM đỉnh':>10}   ⟨ψ|ψ⟩ · đối chiếu Aer")
    for n in cỡ:
        for loại in ("qft", "ngẫu"):
            d = chạy(loại, n)
            if "lỗi" in d: print(f"{loại:<5} {n:>3}  LỖI: {d['lỗi']}", flush=True); continue
            ghi = f"{d['chuẩn']:.12f}"
            if py_q:
                ks = ",".join(d["biên_độ"])
                r = subprocess.run([py_q, "-c", KIỂM_AER, os.path.join(TMP, f"{loại}_{n}.qasm"), ks], capture_output=True, text=True)
                if r.returncode == 0:
                    aer = json.loads(r.stdout); lệch = max(abs(complex(*d["biên_độ"][k]) - complex(*aer[k])) for k in aer)
                    d["lệch_aer"] = lệch; ghi += f" · lệch biên độ so Aer = {lệch:.1e}"
                else: ghi += " · (Aer lỗi: " + r.stderr.strip()[-120:] + ")"
            print(f"{loại:<5} {n:>3} {d['số_cổng']:>5} {d['giây_mô_phỏng']:>14.2f} {d['ram_đỉnh_MB']:>7} MB   {ghi}", flush=True)
            kq.append(d)
    with open(os.path.join(P, ra), "w", encoding="utf-8") as f: json.dump(kq, f, ensure_ascii=False, indent=1)

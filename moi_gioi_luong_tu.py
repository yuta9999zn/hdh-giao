# -*- coding: utf-8 -*-
"""
MÔI GIỚI LƯỢNG TỬ — tiến trình DUY NHẤT được gọi máy lượng tử thật (IBM Quantum), chạy NGOÀI hộp cát.
=====================================================================================================
GVM-64 không có mạng (đúng thiết kế) — không phá điều đó. Môi giới này làm phần mạng, còn mọi phần
tính toán vẫn ở GIAO trên GVM-64:
  1. Dịch mạch: `mạch.giao` phải đặt biến `m` (mạch của lib_lượng_tử.giao, đã ĐO_HẾT). Môi giới biên
     dịch nó bằng tu_bien_dich.sh (trình biên dịch GIAO tự thân) và chạy trên GVM-64 → OpenQASM 2.0.
  2. NIÊM PHONG dự đoán (niem_phong.py) TRƯỚC khi gửi: dấu γ và khoảng XEB mình tin sẽ đo được.
  3. Cổng NGƯỜI DUYỆT: gửi mạch lên máy thật tốn hạn mức và KHÔNG hoàn tác được ⇒ mặc định chỉ in
     "cần_người_duyệt" rồi thoát (mã 2). Chỉ gửi khi người gõ --duyệt. γ không bao giờ tự cho phép.
  4. Gửi (SamplerV2 của qiskit-ibm-runtime), nhận số đếm, lưu __pycache__/luong_tu_that/<băm>.json.
  5. CHẤM trên GVM-64: chấm_mẫu(đếm, ψ_lý_tưởng, ε) của lib_lượng_tử.giao → XEB tuyến tính + γ (F.4),
     rồi chấm niêm phong. Đo được nhiễu máy thật so với bộ mô phỏng của chính GIAO.

    python moi_gioi_luong_tu.py mạch.giao [--shots 1000] [--máy ibm_xxx] [--đoán-γ sáng|tối]
                                [--đoán-xeb cao|vừa|thấp] [--ε 0.01] [--duyệt]
    python moi_gioi_luong_tu.py mạch.giao --giả-lập 0.02 [--duyệt]   # thử CẢ QUY TRÌNH không cần token:
                                                                      # Aer + nhiễu khử cực mỗi cổng
Token: CHỈ đọc từ biến môi trường QISKIT_IBM_TOKEN (không ghi ra đĩa, không in). Cần gói
qiskit-ibm-runtime (pip install qiskit-ibm-runtime) trong Python chạy môi giới — chỉ khi gửi máy thật.
Khoảng XEB: cao ≥ 0.5 · vừa 0.2–0.5 · thấp < 0.2.
"""
import os, sys, json, time, hashlib, shutil, subprocess, tempfile
P = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, P)
from niem_phong import SổNiêmPhong

WT = shutil.which("wasmtime") or r"D:\wasmtime\wasmtime.exe"
SH = shutil.which("sh") or r"C:\Program Files\Git\usr\bin\sh.exe"
KHO = os.path.join(P, "__pycache__", "luong_tu_that")

def chạy_giao(mã_nguồn, thư_mục):
    "Biên dịch BẰNG GIAO (tu_bien_dich.sh) rồi chạy trên GVM-64. Trả stdout (chuỗi)."
    fd, tệp = tempfile.mkstemp(suffix=".giao", prefix="_moi_gioi_", dir=thư_mục)
    with os.fdopen(fd, "w", encoding="utf-8") as f: f.write(mã_nguồn)
    try:
        g = subprocess.run([SH, os.path.join(P, "tu_bien_dich.sh"), tệp], capture_output=True, timeout=900)
        if g.returncode != 0: raise RuntimeError("biên dịch GIAO lỗi: " + g.stderr.decode("utf-8", "replace")[-400:])
        r = subprocess.run([WT, "run", "--preload", "argon2=" + os.path.join(P, "wasm", "argon2.wasm"), os.path.join(P, "wasm", "gvm64.wasm"), "--", "--bước", "4000000000",
                            "--trần-ds", "200000000"], input=g.stdout, capture_output=True, timeout=3600)
        if r.returncode != 0: raise RuntimeError("GVM-64 lỗi: " + r.stderr.decode("utf-8", "replace")[-400:])
        return r.stdout.decode("utf-8")
    finally:
        os.remove(tệp)

def khoảng_xeb(x):
    return "cao" if x >= 0.5 else ("vừa" if x >= 0.2 else "thấp")

def gửi_ibm(qasm, máy, shots):
    token = os.environ.get("QISKIT_IBM_TOKEN")
    if not token: sys.exit("thiếu biến môi trường QISKIT_IBM_TOKEN (token IBM Quantum của BẠN) — không gửi.")
    try:
        from qiskit import qasm2, transpile
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    except ImportError as e:
        sys.exit(f"thiếu gói ({e.name}) — cài: pip install qiskit qiskit-ibm-runtime")
    svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    be = svc.backend(máy) if máy else svc.least_busy(operational=True, simulator=False)
    qc = qasm2.loads(qasm, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    job = SamplerV2(mode=be).run([transpile(qc, be, optimization_level=1)], shots=shots)
    print(f"[môi giới] đã gửi lên {be.name} · job {job.job_id()} · chờ kết quả…", flush=True)
    return be.name, job.job_id(), job.result()[0].data.c.get_counts()

def giả_lập(qasm, p, shots, seed=2026):
    "Máy GIẢ để thử cả quy trình không cần token: Aer + nhiễu khử cực p mỗi cổng 1 và 2 qubit."
    from qiskit import qasm2, transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(p, 1), ["u", "u1", "u2", "u3", "rx", "ry", "rz", "h", "x", "y", "z", "s", "sdg", "t", "tdg", "p", "sx"])
    nm.add_all_qubit_quantum_error(depolarizing_error(min(1.0, 2 * p), 2), ["cx", "cz", "swap", "cp", "cu1", "crz"])
    sim = AerSimulator(noise_model=nm, seed_simulator=seed)
    qc = qasm2.loads(qasm, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    return f"aer-giả-lập(p={p})", "cục-bộ", sim.run(transpile(qc, sim, optimization_level=0), shots=shots).result().get_counts()

def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("--"): print(__doc__); sys.exit(2)
    def cờ(tên, mặc=None): return a[a.index(tên) + 1] if tên in a else mặc
    mạch_tệp = os.path.abspath(a[0]); thư_mục = os.path.dirname(mạch_tệp); tên = os.path.basename(mạch_tệp)
    shots = int(cờ("--shots", "1000")); máy = cờ("--máy"); ε = float(cờ("--ε", "0.01"))
    đoán = {"γ_dấu": cờ("--đoán-γ", "sáng"), "xeb": cờ("--đoán-xeb", "vừa")}
    p_giả = cờ("--giả-lập"); duyệt = "--duyệt" in a

    # 1. mạch → QASM, trên GVM-64
    qasm = chạy_giao(f'nhập "{tên}"\nrọi sang_qasm(m)\n', thư_mục)
    băm_mạch = hashlib.sha256(qasm.encode("utf-8")).hexdigest()
    nơi = f"giả lập (p={p_giả})" if p_giả else (máy or "máy IBM rảnh nhất")
    print(f"[môi giới] mạch {tên} · QASM {len(qasm.splitlines())} dòng · sha256 {băm_mạch[:16]}… · {shots} shots · nơi chạy: {nơi}")

    # 2. cổng người duyệt (chạy khô: không niêm phong, không gửi)
    if not duyệt:
        print("[môi giới] cần_người_duyệt: gửi mạch là việc BẤT KHẢ HỒI (tốn hạn mức, không rút lại được).\n"
              "           Xem QASM dưới đây rồi chạy lại với --duyệt nếu đồng ý. Chưa gửi, chưa niêm phong gì.")
        print(qasm); sys.exit(2)

    if not p_giả and not os.environ.get("QISKIT_IBM_TOKEN"):      # thiếu điều kiện thì dừng TRƯỚC khi niêm phong
        sys.exit("thiếu biến môi trường QISKIT_IBM_TOKEN (token IBM Quantum của BẠN) — không gửi, không niêm phong.")

    # 3. niêm phong dự đoán — SAU khi người duyệt, TRƯỚC khi gửi
    sổ = SổNiêmPhong()
    niêm = sổ.niêm_phong("người:môi_giới_lượng_tử", f"{nơi} · {tên} · {băm_mạch[:16]} · {shots} shots", đoán)
    print(f"[môi giới] đã NIÊM PHONG dự đoán {đoán} → {niêm[:16]}…")

    # 4. chạy
    tên_máy, job, đếm = giả_lập(qasm, float(p_giả), shots) if p_giả else gửi_ibm(qasm, máy, shots)
    os.makedirs(KHO, exist_ok=True)
    lưu = os.path.join(KHO, f"{băm_mạch[:16]}_{job.replace('/', '_')}_{time.strftime('%Y%m%d-%H%M%S')}.json")
    with open(lưu, "w", encoding="utf-8") as f:
        json.dump({"mạch": tên, "qasm_sha256": băm_mạch, "máy": tên_máy, "job": job, "shots": shots, "đếm": đếm}, f, ensure_ascii=False, indent=1)

    # 5. chấm trên GVM-64
    gán = "".join(f'đặt đếm["{k}"] = {int(v)}\n' for k, v in sorted(đếm.items()))
    ra = chạy_giao(f'nhập "{tên}"\nđặt ψ = trạng_thái_cuối(m)\nđặt đếm = bản()\n{gán}'
                   f'đặt kq = chấm_mẫu(đếm, ψ, {ε})\nrọi "xeb=" + số_chính_xác(kq["xeb"])\n'
                   f'rọi "γ=" + số_chính_xác(kq["γ"])\nrọi "n=" + kq["số_mẫu"]\n', thư_mục)
    kv = dict(d.split("=", 1) for d in ra.splitlines() if "=" in d)
    xeb, γ = float(kv["xeb"]), float(kv["γ"])
    thật = {"γ_dấu": "sáng" if γ > 0 else ("tối" if γ < 0 else "ẩn"), "xeb": khoảng_xeb(xeb)}
    kq = sổ.chấm(niêm, thật)
    print(f"[môi giới] {tên_máy} · job {job} · {kv['n']} mẫu → XEB tuyến tính = {xeb:.4f} · γ(ε={ε}) = {γ:+.4f}")
    print(f"[môi giới] chấm niêm phong: {'TRÚNG' if kq['trúng'] else 'TRƯỢT'} {kq['lệch'] or ''} · số đếm lưu ở {lưu}")

if __name__ == "__main__":
    main()

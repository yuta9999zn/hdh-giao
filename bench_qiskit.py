# -*- coding: utf-8 -*-
"""
Nửa QISKIT của bench_luong_tu.py — chạy bằng một Python CÓ qiskit + qiskit-aer + psutil:
   <python_qiskit> bench_qiskit.py <qft|ngẫu> <n> <aer1|aer|numpy>
Đọc ĐÚNG tệp QASM mà GIAO đã xuất (bench_luong_tu.py tạo trong __pycache__/bench_lt/).
  aer1  = Qiskit Aer, statevector, 1 luồng        (so công bằng với GIAO: CPython đơn luồng)
  aer   = Qiskit Aer, statevector, mọi luồng       (cấu hình mặc định người dùng Qiskit sẽ gặp)
  numpy = qiskit.quantum_info.Statevector           (thuần numpy — "nếu GIAO dùng numpy")
Ở ≤ 20 qubit: đo thêm độ trung thực |⟨ψ_GIAO|ψ_Qiskit⟩|² — kiểm GIAO ĐÚNG ở cỡ lớn, không chỉ nhanh.
"""
import os, sys, json, time
P = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(P, "__pycache__", "bench_lt")

def main(loại, n, chế_độ):
    import psutil, numpy as np
    from qiskit import qasm2, transpile
    tên = f"{loại}_{n}"
    qc = qasm2.load(os.path.join(TMP, tên + ".qasm"), custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    qc.remove_final_measurements()
    t0 = time.perf_counter()
    if chế_độ == "numpy":
        from qiskit.quantum_info import Statevector
        ψ = Statevector.from_instruction(qc).data
        dt = time.perf_counter() - t0; ghi = "quantum_info.Statevector"
    else:
        from qiskit_aer import AerSimulator
        sim = AerSimulator(method="statevector", precision="double",
                           **({"max_parallel_threads": 1} if chế_độ == "aer1" else {}))
        qc2 = qc.copy(); qc2.save_statevector()
        tq = transpile(qc2, sim, optimization_level=0)
        t0 = time.perf_counter()
        r = sim.run(tq, shots=1).result()
        dt = time.perf_counter() - t0
        ψ = np.asarray(r.get_statevector())
        md = r.results[0].metadata; ghi = f"luồng={md.get('parallel_state_update', '?')}, fusion={md.get('fusion', {}).get('applied', '?')}"
    tt = ""
    tệp = os.path.join(TMP, tên + "_mảng.npy")
    if n <= 20 and os.path.exists(tệp):
        g = np.load(tệp); tt = f" · độ trung thực với GIAO = {abs(np.vdot(g, ψ)) ** 2:.12f}"
    return {"bộ": f"Qiskit {chế_độ}", "mạch": loại, "n": n, "số_cổng": qc.size(),
            "giây_mô_phỏng": round(dt, 3), "ram_đỉnh_MB": round(psutil.Process().memory_info().peak_wset / 2 ** 20),
            "ghi_chú": ghi + tt}

if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1], int(sys.argv[2]), sys.argv[3]), ensure_ascii=False))

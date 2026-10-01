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
qiskit-ibm-runtime + pyopenssl + cryptography (OpenSSL ≥ 3.5) trong Python chạy môi giới — chỉ khi gửi máy thật.
TLS: mọi kết nối tới IBM phải thoả thuận nhóm LAI HẬU LƯỢNG TỬ (X25519MLKEM768…), kiểm bắt tay trước khi
gửi và chốt ở từng kết nối; không thì từ chối (chấp nhận cổ điển: --cho-tls-cổ-điển).
Khoảng XEB: cao ≥ 0.5 · vừa 0.2–0.5 · thấp < 0.2.
"""
import os, sys, json, time, hashlib, shutil, subprocess, tempfile
P = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, P)
from niem_phong import SổNiêmPhong
from vo_gvm64 import lệnh_gvm64

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
        r = subprocess.run(lệnh_gvm64(["--bước", "4000000000",
                            "--trần-ds", "200000000"]), input=g.stdout, capture_output=True, timeout=3600)
        if r.returncode != 0: raise RuntimeError("GVM-64 lỗi: " + r.stderr.decode("utf-8", "replace")[-400:])
        return r.stdout.decode("utf-8")
    finally:
        os.remove(tệp)

def khoảng_xeb(x):
    return "cao" if x >= 0.5 else ("vừa" if x >= 0.2 else "thấp")

# ---------------- TLS HẬU LƯỢNG TỬ (v0.42, lộ trình GĐ2): X25519 + ML-KEM-768 ----------------
# ssl của Python trên máy này (OpenSSL 1.1.1 / 3.0) KHÔNG có ML-KEM. pyOpenSSL dùng OpenSSL đi kèm gói
# `cryptography` (≥ 3.5: có ML-KEM, đề nghị X25519MLKEM768 trước tiên). Môi giới ép requests/urllib3 (thứ
# qiskit-ibm-runtime dùng) đi qua pyOpenSSL và CHỐT ở MỌI kết nối: nhóm trao đổi khoá phải là nhóm lai
# hậu lượng tử, không thì đóng kết nối — token không bao giờ đi trên kênh chỉ cổ điển (trừ --cho-tls-cổ-điển).
# Đo 2026-10-01: quantum.cloud.ibm.com và iam.cloud.ibm.com đều thoả thuận X25519MLKEM768 / TLS 1.3.
MÁY_CHỦ_IBM = ["quantum.cloud.ibm.com", "iam.cloud.ibm.com"]
NHÓM_HẬU_LƯỢNG_TỬ = {"X25519MLKEM768", "SecP256r1MLKEM768", "SecP384r1MLKEM1024", "MLKEM768", "MLKEM1024"}

class TLSCổĐiển(RuntimeError): pass

def _bối_cảnh_pq(xác_minh=True):
    from OpenSSL import SSL
    ctx = SSL.Context(SSL.TLS_CLIENT_METHOD)
    ctx.set_min_proto_version(SSL.TLS1_3_VERSION)
    if xác_minh:
        import certifi
        ctx.set_verify(SSL.VERIFY_PEER); ctx.load_verify_locations(certifi.where())
    return ctx

def bắt_tay_nhóm(host, cổng=443, xác_minh=True):
    "Bắt tay TLS 1.3 bằng pyOpenSSL → (nhóm trao đổi khoá, phiên bản). Không gửi dữ liệu nào."
    import socket
    from OpenSSL import SSL
    s = socket.create_connection((host, cổng), timeout=15); s.settimeout(None)
    try:
        c = SSL.Connection(_bối_cảnh_pq(xác_minh), s)
        c.set_tlsext_host_name(host.encode()); c.set_connect_state(); c.do_handshake()
        nhóm, bản = c.get_group_name(), c.get_protocol_version_name()
        c.shutdown(); return nhóm, bản
    finally:
        s.close()

def bật_tls_hậu_lượng_tử(cho_cổ_điển=False):
    """Ép urllib3 (requests, qiskit-ibm-runtime) đi qua pyOpenSSL và chốt nhóm lai ở MỌI kết nối.
    → chuỗi phiên bản OpenSSL đang dùng. Thiếu pyOpenSSL/OpenSSL đủ mới ⇒ TLSCổĐiển (trừ cho_cổ_điển)."""
    import warnings
    try:
        warnings.simplefilter("ignore", DeprecationWarning)
        import urllib3.contrib.pyopenssl as po
        from cryptography.hazmat.backends.openssl.backend import backend
    except ImportError as e:
        if cho_cổ_điển: return "ssl chuẩn (CỔ ĐIỂN — người dùng cho phép)"
        raise TLSCổĐiển(f"thiếu {e.name} — cài: pip install pyopenssl cryptography urllib3 (cần OpenSSL ≥ 3.5)")
    po.inject_into_urllib3()
    gốc = po.PyOpenSSLContext.wrap_socket
    if not getattr(gốc, "_giao_chốt_pq", False):
        def bọc(self, *a, **k):
            ws = gốc(self, *a, **k)
            nhóm = ws.connection.get_group_name()
            if nhóm not in NHÓM_HẬU_LƯỢNG_TỬ and not cho_cổ_điển:
                ws.close(); raise TLSCổĐiển(f"kết nối TLS dùng nhóm {nhóm} — KHÔNG phải lai hậu lượng tử, đã đóng")
            return ws
        bọc._giao_chốt_pq = True
        po.PyOpenSSLContext.wrap_socket = bọc
    return backend.openssl_version_text()

def kiểm_tls_máy_chủ(hosts=MÁY_CHỦ_IBM, cho_cổ_điển=False):
    "Bắt tay thử TRƯỚC khi gửi token. → [(host, nhóm, bản)]; máy chủ nào không lai ⇒ TLSCổĐiển."
    ra = []
    for h in hosts:
        nhóm, bản = bắt_tay_nhóm(h)
        ra.append((h, nhóm, bản))
        if nhóm not in NHÓM_HẬU_LƯỢNG_TỬ and not cho_cổ_điển:
            raise TLSCổĐiển(f"{h} chỉ thoả thuận {nhóm} ({bản}) — không gửi token qua kênh cổ điển")
    return ra

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
    if not p_giả:                                                  # TLS lai hậu lượng tử, kiểm TRƯỚC khi niêm phong/gửi
        cổ_điển = "--cho-tls-cổ-điển" in a
        try:
            bản = bật_tls_hậu_lượng_tử(cổ_điển)
            for h, nhóm, v in kiểm_tls_máy_chủ(cho_cổ_điển=cổ_điển):
                print(f"[môi giới] TLS {h}: {nhóm} · {v}")
            print(f"[môi giới] mọi kết nối tới IBM đi qua {bản}, chốt nhóm lai hậu lượng tử")
        except TLSCổĐiển as e:
            sys.exit(f"[môi giới] TỪ CHỐI: {e} — không gửi, không niêm phong. (Chấp nhận TLS cổ điển: --cho-tls-cổ-điển)")

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

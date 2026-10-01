# -*- coding: utf-8 -*-
"""KIỂM MÔI GIỚI LƯỢNG TỬ — cổng người duyệt + niêm phong đúng thứ tự (không cần token, không cần Qiskit).
    python kiem_moi_gioi.py
  ① không --duyệt  ⇒ mã thoát 2, in "cần_người_duyệt" + QASM (dịch bằng GIAO trên GVM-64), KHÔNG ghi sổ;
  ② --duyệt mà thiếu token ⇒ từ chối, KHÔNG ghi sổ (không để lại niêm phong treo);
  ③ (nếu có qiskit_aer) --giả-lập ⇒ niêm phong TRƯỚC, chấm SAU, chuỗi băm nguyên vẹn, XEB/γ tính trên GVM-64.
"""
import os, sys, subprocess, tempfile, json
P = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, P)
from niem_phong import SổNiêmPhong

đạt = rớt = 0
def ca(tên, ok, ct=""):
    global đạt, rớt
    if ok: đạt += 1; print(f"  ✓ {tên}")
    else: rớt += 1; print(f"  ✗ {tên}  {ct}")

def chạy(args, py=sys.executable, token=None):
    sổ = os.path.join(tempfile.mkdtemp(), "so.jsonl")
    env = dict(os.environ, GIAO_SO_NIEM_PHONG=sổ, PYTHONIOENCODING="utf-8"); env.pop("QISKIT_IBM_TOKEN", None)
    if token: env["QISKIT_IBM_TOKEN"] = token
    r = subprocess.run([py, os.path.join(P, "moi_gioi_luong_tu.py"), "mạch_mẫu_ibm.giao"] + args, cwd=P, env=env,
                       capture_output=True, text=True, encoding="utf-8", timeout=1800)
    return r.returncode, r.stdout + r.stderr, sổ

print("[môi giới lượng tử]")
mã, o, sổ = chạy([])
ca("không --duyệt ⇒ cần_người_duyệt, mã 2, in QASM dịch bằng GIAO", mã == 2 and "cần_người_duyệt" in o and "OPENQASM 2.0;" in o and "measure q[3] -> c[3];" in o, o[-300:])
ca("chạy khô KHÔNG ghi sổ niêm phong", not os.path.exists(sổ))
mã, o, sổ = chạy(["--duyệt"])
ca("--duyệt mà thiếu token ⇒ từ chối, không gửi", mã != 0 and "QISKIT_IBM_TOKEN" in o, o[-300:])
ca("thiếu token KHÔNG để lại niêm phong treo", not os.path.exists(sổ))
try:
    import OpenSSL  # noqa: F401
    có_pyopenssl = True
except ImportError:
    có_pyopenssl = False
if not có_pyopenssl:
    mã, o, sổ = chạy(["--duyệt"], token="token-giả-chỉ-để-kiểm")
    ca("có token nhưng Python thiếu pyOpenSSL (không TLS hậu lượng tử) ⇒ TỪ CHỐI, không gửi",
       mã != 0 and "TỪ CHỐI" in o and "--cho-tls-cổ-điển" in o, o[-300:])
    ca("từ chối vì TLS cổ điển KHÔNG để lại niêm phong treo", not os.path.exists(sổ))
try:
    import qiskit_aer  # noqa: F401
    có_aer = True
except ImportError:
    có_aer = False
if có_aer:
    mã, o, sổ = chạy(["--giả-lập", "0.02", "--shots", "4000", "--đoán-xeb", "cao", "--duyệt"])
    s = SổNiêmPhong(sổ); ds = s.đọc(); ok_chuỗi, _ = s.kiểm_chuỗi()
    ca("giả lập: niêm phong TRƯỚC, chấm SAU, chuỗi băm nguyên vẹn",
       mã == 0 and [m["loại"] for m in ds] == ["niêm_phong", "chấm"] and ok_chuỗi, o[-300:])
    ca("giả lập p=0.02: XEB tính trên GVM-64 ở khoảng 'cao', γ > 0, dự đoán TRÚNG",
       "chấm niêm phong: TRÚNG" in o and "γ(ε=0.01) = +" in o, o[-300:])
else:
    print("  · (bỏ qua giả lập — Python này không có qiskit_aer)")
print(f"\nMÔI GIỚI LƯỢNG TỬ: {đạt}/{đạt + rớt}")
sys.exit(0 if rớt == 0 else 1)

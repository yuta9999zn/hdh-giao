# -*- coding: utf-8 -*-
"""KIỂM TLS HẬU LƯỢNG TỬ của môi giới (moi_gioi_luong_tu.py) — không cần mạng.
    <python có pyopenssl + cryptography (OpenSSL ≥ 3.5)> kiem_tls_pq.py      (GIAO_KIEM_MANG=1: thêm IBM thật)
  ① máy chủ cục bộ CHỈ CỔ ĐIỂN (ssl chuẩn của Python, OpenSSL cũ ⇒ X25519) ⇒ bắt tay thấy nhóm cổ điển, và
     kết nối qua urllib3/requests (đã chốt) bị ĐÓNG — token không đi được;
  ② máy chủ cục bộ CÓ ML-KEM (pyOpenSSL) ⇒ X25519MLKEM768, kết nối đi qua;
  ③ --cho-tls-cổ-điển ⇒ kết nối cổ điển được phép (người dùng tự chịu, nói rõ);
  ④ (GIAO_KIEM_MANG=1) quantum.cloud.ibm.com + iam.cloud.ibm.com thoả thuận nhóm lai.
Python không có pyOpenSSL ⇒ in BỎ QUA và thoát 0 (môi giới khi ấy cũng TỪ CHỐI gửi — đã kiểm ở ⑤).
"""
import os, sys, ssl, socket, threading, tempfile, datetime
P = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, P)
đạt = rớt = 0
def ca(tên, ok, ct=""):
    global đạt, rớt
    if ok: đạt += 1; print(f"  ✓ {tên}")
    else: rớt += 1; print(f"  ✗ {tên}  {ct}")
try:
    import OpenSSL, urllib3, requests  # noqa: F401
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
except ImportError as e:
    print(f"[TLS hậu lượng tử] BỎ QUA — Python này thiếu {e.name} (chạy bằng Python có pyopenssl + cryptography)")
    print("\nTLS HẬU LƯỢNG TỬ: bỏ qua"); sys.exit(0)
import moi_gioi_luong_tu as MG

# chứng chỉ tự ký cho 127.0.0.1 (chỉ cho bài kiểm)
tm = tempfile.mkdtemp()
k = ec.generate_private_key(ec.SECP256R1())
tên = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
bây = datetime.datetime.now(datetime.timezone.utc)
cert = (x509.CertificateBuilder().subject_name(tên).issuer_name(tên).public_key(k.public_key())
        .serial_number(1).not_valid_before(bây - datetime.timedelta(days=1)).not_valid_after(bây + datetime.timedelta(days=1))
        .sign(k, hashes.SHA256()))
CERT, KEY = os.path.join(tm, "c.pem"), os.path.join(tm, "k.pem")
open(CERT, "wb").write(cert.public_bytes(serialization.Encoding.PEM))
open(KEY, "wb").write(k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))

def máy_chủ_cổ_điển():
    "ssl CHUẨN của Python (OpenSSL không có ML-KEM) — chỉ thoả thuận nhóm cổ điển."
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(CERT, KEY)
    s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(8)
    def chạy():
        while True:
            try: c, _ = s.accept()
            except OSError: return
            try:
                t = ctx.wrap_socket(c, server_side=True)
                t.recv(4096); t.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok"); t.close()
            except Exception: c.close()
    threading.Thread(target=chạy, daemon=True).start(); return s, s.getsockname()[1], ssl.OPENSSL_VERSION

def máy_chủ_pq():
    "pyOpenSSL (OpenSSL của cryptography, có ML-KEM)."
    from OpenSSL import SSL
    ctx = SSL.Context(SSL.TLS_SERVER_METHOD); ctx.use_certificate_file(CERT); ctx.use_privatekey_file(KEY)
    s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(8)
    def chạy():
        while True:
            try: c, _ = s.accept()
            except OSError: return
            try:
                t = SSL.Connection(ctx, c); t.set_accept_state(); t.do_handshake()
                try: t.recv(4096)
                except SSL.Error: pass
                t.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok"); t.shutdown(); c.close()
            except Exception: c.close()
    threading.Thread(target=chạy, daemon=True).start(); return s, s.getsockname()[1]

print("[TLS hậu lượng tử — môi giới]")
bản = MG.bật_tls_hậu_lượng_tử()
from cryptography.hazmat.backends.openssl.backend import backend
ca(f"urllib3/requests đi qua pyOpenSSL: {bản}", "OpenSSL" in bản)
import urllib3.contrib.pyopenssl as po

s1, cổng1, bản1 = máy_chủ_cổ_điển()
nhóm, v = MG.bắt_tay_nhóm("127.0.0.1", cổng1, xác_minh=False)
ca(f"① máy chủ CỔ ĐIỂN ({bản1}) chỉ thoả thuận {nhóm} {v}", nhóm not in MG.NHÓM_HẬU_LƯỢNG_TỬ)
try:
    requests.get(f"https://127.0.0.1:{cổng1}/", verify=False, timeout=10); ok, lý = False, "không bị chặn"
except Exception as e:
    lý = repr(e); ok = "KHÔNG phải lai hậu lượng tử" in lý
ca("① requests tới máy chủ cổ điển bị ĐÓNG ở bước bắt tay (token không đi được)", ok, lý[:200])

s2, cổng2 = máy_chủ_pq()
nhóm2, v2 = MG.bắt_tay_nhóm("127.0.0.1", cổng2, xác_minh=False)
ca(f"② máy chủ có ML-KEM ⇒ {nhóm2} {v2}", nhóm2 in MG.NHÓM_HẬU_LƯỢNG_TỬ)
try:
    r = requests.get(f"https://127.0.0.1:{cổng2}/", verify=False, timeout=10); ok, lý = r.text == "ok", r.text
except Exception as e:
    ok, lý = False, repr(e)
ca("② requests tới máy chủ lai đi qua bình thường", ok, lý[:200])

# ③ cho phép cổ điển: tạo lại lớp chốt với cho_cổ_điển=True
po.PyOpenSSLContext.wrap_socket = po.PyOpenSSLContext.wrap_socket.__wrapped__ if hasattr(po.PyOpenSSLContext.wrap_socket, "__wrapped__") else po.PyOpenSSLContext.wrap_socket
import importlib
po.extract_from_urllib3(); importlib.reload(po)
MG.bật_tls_hậu_lượng_tử(cho_cổ_điển=True)
try:
    r = requests.get(f"https://127.0.0.1:{cổng1}/", verify=False, timeout=10); ok = r.text == "ok"
except Exception as e:
    ok = False; print("   ", repr(e)[:200])
ca("③ --cho-tls-cổ-điển ⇒ kết nối cổ điển được phép (người dùng tự quyết)", ok)

if os.environ.get("GIAO_KIEM_MANG") == "1":
    try:
        ds = MG.kiểm_tls_máy_chủ()
        ca("④ IBM thật: " + " · ".join(f"{h} {g}" for h, g, _ in ds), all(g in MG.NHÓM_HẬU_LƯỢNG_TỬ for _, g, _ in ds))
    except Exception as e:
        ca("④ IBM thật", False, repr(e)[:200])
else:
    print("  · ④ IBM thật: bỏ qua (đặt GIAO_KIEM_MANG=1)")
s1.close(); s2.close()
print(f"\nTLS HẬU LƯỢNG TỬ: {đạt}/{đạt + rớt}")
sys.exit(0 if rớt == 0 else 1)

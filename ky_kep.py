# -*- coding: utf-8 -*-
"""KÝ KÉP ML-DSA-65 + Ed25519 — lớp gọi (host) cho wasm/ky_lenh.wasm.

Mã mật mã KHÔNG ở đây: ML-DSA-65 là mldsa-native v2.0.0 (FIPS 204), Ed25519 là Monocypher (RFC 8032), vendor nguyên
văn trong ben_ngoai/, dựng bằng wasi-sdk (sh wasm/dung_ky.sh), chạy dưới wasmtime KHÔNG cấp thư mục. Tệp
này chỉ đóng gói tham số, kiểm GHIM SHA-256 của module (wasm/ky.sha256) rồi gọi.

KÝ KÉP ("lai"): một chữ ký chỉ HỢP LỆ khi CẢ HAI hợp lệ — phá được Ed25519 (máy lượng tử đủ lớn) vẫn
chưa giả được ML-DSA; nếu ML-DSA (mới, ít năm thẩm định) có lỗ thì Ed25519 vẫn đỡ.

Ngẫu nhiên: ξ (khoá ML-DSA), hạt Ed25519 và rnd khi ký đều lấy từ HĐH (os.urandom) ở đây rồi TRUYỀN vào
module — module không tự lấy ngẫu nhiên. `rnd = 0³²` ⇒ biến thể tất định của FIPS 204 (dùng cho vector kiểm).
"""
import os, struct, subprocess
from vo_gvm64 import WASMTIME, kiểm_ghim

P = os.path.dirname(os.path.abspath(__file__))
MODULE = os.environ.get("GIAO_KY_WASM") or os.path.join(P, "wasm", "ky_lenh.wasm")
GHIM_KY = os.path.join(P, "wasm", "ky.sha256")
MLDSA_PK, MLDSA_SK, MLDSA_SIG = 1952, 4032, 3309
_đã_ghim = False

class LỗiKý(RuntimeError): pass

def _gọi(lệnh, *trường):
    global _đã_ghim
    if not _đã_ghim: kiểm_ghim(MODULE, "ky_lenh.wasm", GHIM_KY); _đã_ghim = True
    vào = bytes([lệnh]) + b"".join(struct.pack("<I", len(t)) + bytes(t) for t in trường)
    r = subprocess.run([WASMTIME, "run", MODULE], input=vào, capture_output=True, timeout=120)
    ra = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0 or ra.startswith("LOI"): raise LỗiKý(ra or r.stderr.decode("utf-8", "replace")[-200:])
    return ra

def mldsa_khoá(ξ):
    h = bytes.fromhex(_gọi(1, ξ)); return h[:MLDSA_PK], h[MLDSA_PK:]
def mldsa_ký(sk, thông_điệp, ngữ_cảnh=b"", rnd=None):
    return bytes.fromhex(_gọi(2, sk, thông_điệp, ngữ_cảnh, rnd if rnd is not None else os.urandom(32)))
def mldsa_kiểm(pk, thông_điệp, ngữ_cảnh, chữ_ký):
    return _gọi(3, pk, thông_điệp, ngữ_cảnh, chữ_ký) == "1"
def ed_khoá(hạt):
    return bytes.fromhex(_gọi(4, hạt))
def ed_ký(hạt, thông_điệp):
    return bytes.fromhex(_gọi(5, hạt, thông_điệp))
def ed_kiểm(pk, thông_điệp, chữ_ký):
    return _gọi(6, pk, thông_điệp, chữ_ký) == "1"

NGỮ_CẢNH_SỔ = b"giao-niem-phong-v1"
def ký_kép(ξ, hạt_ed, thông_điệp, ngữ_cảnh=NGỮ_CẢNH_SỔ):
    "→ (ký_ed25519 64 byte, ký_mldsa65 3309 byte). rnd của ML-DSA lấy từ HĐH (biến thể 'hedged')."
    h = bytes.fromhex(_gọi(8, ξ, hạt_ed, thông_điệp, ngữ_cảnh, os.urandom(32)))
    return h[:64], h[64:]
def kiểm_kép(pk_ed, pk_ml, thông_điệp, ký_ed, ký_ml, ngữ_cảnh=NGỮ_CẢNH_SỔ):
    "→ (Ed25519 hợp lệ?, ML-DSA-65 hợp lệ?). Ký kép chỉ HỢP LỆ khi CẢ HAI đúng."
    r = _gọi(7, pk_ed, pk_ml, thông_điệp, ngữ_cảnh, ký_ed, ký_ml)
    return r[0] == "1", r[1] == "1"

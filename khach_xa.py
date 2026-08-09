# -*- coding: utf-8 -*-
"""
khach_xa.py — KHÁCH nối vào HĐH-GIAO từ xa, KÊNH ĐÃ MÃ HOÁ
================================================================================
    python khach_xa.py [--cổng 2222]
    python khach_xa.py --kịch "an" "an" "tôi" "liệt /" "thoát"      # chế độ kịch bản (nghiệm thu)
    python khach_xa.py --trần                                        # KHÔNG mã hoá (chỉ để soi)

Bắt tay (đúng phần GIAO ở đầu kia làm ngược lại):
  ① máy chủ chào TRẦN một dòng: "GIAO-KÍN <vân tay khoá máy>" — khách đối chiếu vân tay ấy với
     `khoa_may_cong.txt` (tin-lần-đầu, như `known_hosts` của SSH). Sai vân tay ⇒ DỪNG.
  ② khách sinh 96 byte ngẫu nhiên, bọc PKCS#1 v1.5 rồi mã bằng KHOÁ CÔNG của máy → chỉ máy giải nổi.
  ③ từ đó mọi dòng đi trong KHUNG: ChaCha20 (mỗi chiều một khoá) + HMAC-SHA256 phủ cả số đếm.

Đây chỉ là cái MÁY ĐẦU CUỐI; đăng nhập/quyền/lệnh đều do HĐH-GIAO ở đầu kia quyết.
"""
import socket, sys, os, time, hmac, hashlib, struct, secrets

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------- ChaCha20 (RFC 8439) ----------------
def _qr(s, a, b, c, d):
    M = 0xffffffff
    s[a] = (s[a] + s[b]) & M; s[d] ^= s[a]; s[d] = ((s[d] << 16) | (s[d] >> 16)) & M
    s[c] = (s[c] + s[d]) & M; s[b] ^= s[c]; s[b] = ((s[b] << 12) | (s[b] >> 20)) & M
    s[a] = (s[a] + s[b]) & M; s[d] ^= s[a]; s[d] = ((s[d] << 8) | (s[d] >> 24)) & M
    s[c] = (s[c] + s[d]) & M; s[b] ^= s[c]; s[b] = ((s[b] << 7) | (s[b] >> 25)) & M


def _khối(khoá, nonce, đếm):
    s = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574] + list(struct.unpack("<8I", khoá)) \
        + [đếm & 0xffffffff] + list(struct.unpack("<3I", nonce))
    t = s[:]
    for _ in range(10):
        _qr(t, 0, 4, 8, 12); _qr(t, 1, 5, 9, 13); _qr(t, 2, 6, 10, 14); _qr(t, 3, 7, 11, 15)
        _qr(t, 0, 5, 10, 15); _qr(t, 1, 6, 11, 12); _qr(t, 2, 7, 8, 13); _qr(t, 3, 4, 9, 14)
    return b"".join(struct.pack("<I", (t[i] + s[i]) & 0xffffffff) for i in range(16))


def chacha20(khoá, nonce, đếm_đầu, dữ):
    ra = bytearray()
    for i in range(0, len(dữ), 64):
        kd = _khối(khoá, nonce, đếm_đầu + i // 64)
        ra += bytes(x ^ y for x, y in zip(dữ[i:i + 64], kd))
    return bytes(ra)


def _nonce(đếm):
    return b"\x00" * 8 + struct.pack(">I", đếm)


REKEY_MỖI = 32          # đổi khoá sau chừng này khung gửi đi — phiên dài không dùng mãi một khoá


class Kênh:
    "Đúng khuôn khung của lib_kenh.giao: '<đếm>:<hex ct>:<hex thẻ>'"
    def __init__(self, kp):
        self.lên = kp[0:32]; self.xuống = kp[32:64]; self.mac = kp[64:96]
        self.đếm_lên = 0; self.đếm_xuống = 0

    def thay_khoá(self, kp):
        "Rekey: thay trọn bộ khoá, số đếm về 0 — hai bên cùng làm sau khi trao DH mới."
        self.lên = kp[0:32]; self.xuống = kp[32:64]; self.mac = kp[64:96]
        self.đếm_lên = 0; self.đếm_xuống = 0

    def đóng(self, chữ):
        ct = chacha20(self.lên, _nonce(self.đếm_lên), 1, chữ.encode("utf-8"))
        hct = ct.hex()
        thẻ = hmac.new(self.mac, f"{self.đếm_lên}:{hct}".encode(), hashlib.sha256).hexdigest()
        k = f"{self.đếm_lên}:{hct}:{thẻ}"
        self.đếm_lên += 1
        return k

    def mở(self, khung):
        p = khung.strip().split(":")
        if len(p) != 3: return None
        mong = hmac.new(self.mac, f"{p[0]}:{p[1]}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(mong, p[2]): return None
        return chacha20(self.xuống, _nonce(int(p[0])), 1, bytes.fromhex(p[1])).decode("utf-8", "replace")


def _cờ(tên, mặc_định):
    for i, a in enumerate(sys.argv):
        if a == tên and i + 1 < len(sys.argv):
            try: return int(sys.argv[i + 1])
            except ValueError: return mặc_định
    return mặc_định


def _hút_dòng(s, chờ=6.0):
    "Đọc tới hết MỘT dòng (khung kết bằng \\n)."
    s.settimeout(chờ); đệm = b""
    while b"\n" not in đệm:
        try:
            d = s.recv(65536)
            if not d: break
            đệm += d
        except (socket.timeout, OSError):
            break
    return đệm.decode("utf-8", "replace")


# RFC 3526 §3 — MODP Group 14 (2048 bit), g = 2 — phải ĐÚNG nhóm mà lib_dh.giao dùng
DH_P = int(("ffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020bbea63b139b22"
            "514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe1356d6d51c245e485b576625e7ec6"
            "f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5a899fa5ae9f24117c4b1fe649286651ece45b3d"
            "c2007cb8a163bf0598da48361c55d39a69163fa8fd24cf5f83655d23dca3ad961c62f356208552bb"
            "9ed529077096966d670c354e4abc9804f1746c08ca18217c32905e462e36ce3be39e772c180e8603"
            "9b2783a2ec07a28fb5c55df06f4c52c9de2bcbf6955817183995497cea956ae515d2261898fa0510"
            "15728e5a8aacaa68ffffffffffffffff"), 16)


def _kdf_kênh(chung: int) -> bytes:
    "Bí mật chung DH (số) → 96 byte khoá phiên — đúng công thức dh_khoá_phiên của lib_dh.giao."
    gốc = chung.to_bytes(256, "big")
    kp = b""; i = 1
    while len(kp) < 96:
        kp += hashlib.sha256(gốc + f"GIAO-kênh-{i}".encode()).digest(); i += 1
    return kp[:96]


def đổi_khoá(s, kênh):
    """Rekey GIỮA PHIÊN: trao DH mới NGAY TRONG kênh cũ (kênh cũ đã xác thực bằng HMAC nên
    không cần ký lại), rồi hai bên cùng thay khoá và đưa số đếm về 0. → True nếu xong."""
    b2 = int.from_bytes(secrets.token_bytes(32), "big") + 2
    B2 = pow(2, b2, DH_P)
    s.sendall((kênh.đóng(f"ĐỔI_KHOÁ {B2:0512x}") + "\n").encode())
    trả_lời = kênh.mở(_hút_dòng(s))
    del B2
    if trả_lời is None: return False
    phần = trả_lời.strip().split()
    if len(phần) != 2 or phần[0] != "ĐỔI_KHOÁ_OK": return False
    try:
        chung = pow(int(phần[1], 16), b2, DH_P)
    except ValueError:
        return False
    finally:
        del b2                                   # khoá tạm biến mất ngay — như lúc bắt tay đầu
    kênh.thay_khoá(_kdf_kênh(chung))
    return True


def _bọc_pkcs1(m: bytes, k: int) -> int:
    "PKCS#1 v1.5 kiểu 2: 00 02 <đệm ngẫu nhiên khác 0> 00 <m>"
    đệm = bytearray()
    while len(đệm) < k - 3 - len(m):
        b = secrets.randbits(8)
        if b: đệm.append(b)
    return int.from_bytes(b"\x00\x02" + bytes(đệm) + b"\x00" + m, "big")


def main():
    cổng = _cờ("--cổng", _cờ("--cong", 2222))
    trần = "--trần" in sys.argv or "--tran" in sys.argv
    kịch = None
    for c in ("--kịch", "--kich"):
        if c in sys.argv:
            kịch = sys.argv[sys.argv.index(c) + 1:]

    try:
        s = socket.create_connection(("127.0.0.1", cổng), timeout=5)
    except OSError as e:
        print(f"[không nối được 127.0.0.1:{cổng}] {e}"); sys.exit(1)

    chào = _hút_dòng(s).strip().split()
    if not chào or chào[0] != "GIAO-DH" or len(chào) < 4:
        print(f"[máy chủ lạ] {' '.join(chào)!r}"); s.close(); sys.exit(1)
    vân_tay_nhận, A_hex, ký_hex = chào[1], chào[2], chào[3]

    # ① đối chiếu vân tay với khoá công đã biết (tin-lần-đầu, như known_hosts)
    tệp_công = os.path.join(HERE, "khoa_may_cong.txt")
    if not os.path.exists(tệp_công):
        print(f"[không có {tệp_công}] — chưa biết máy này, không dám nối."); s.close(); sys.exit(1)
    with open(tệp_công, encoding="utf-8") as f:
        p = f.read().strip().split("|")
    e, n = int(p[1]), int(p[2], 16)
    vân_tay_thật = hashlib.sha256(f"{n:x}".encode()).hexdigest()[:16]
    if vân_tay_nhận != vân_tay_thật:
        print(f"⚠ VÂN TAY KHÔNG KHỚP! máy chủ nói {vân_tay_nhận}, khoá ta có là {vân_tay_thật}")
        print("  → có thể có kẻ đứng giữa. DỪNG.")
        s.close(); sys.exit(1)

    # ② KIỂM CHỮ KÝ trên giá trị DH của máy — không có bước này thì DH vô nghĩa trước kẻ đứng giữa
    k_ = (n.bit_length() + 7) // 8
    em = f"{pow(int(ký_hex, 16), e, n):0{k_ * 2}x}"
    mong = ("0001" + "ff" * (k_ - 54) + "00"
            + "3031300d060960864801650304020105000420" + hashlib.sha256(A_hex.encode()).hexdigest())
    if em != mong:
        print("⚠ CHỮ KÝ TRÊN GIÁ TRỊ DH SAI — kẻ đứng giữa? DỪNG."); s.close(); sys.exit(1)

    # ③ Diffie-Hellman: sinh khoá TẠM, gửi B, cùng tính bí mật chung rồi VỨT khoá tạm
    b = int.from_bytes(secrets.token_bytes(32), "big") + 2
    B = pow(2, b, DH_P)
    chung = pow(int(A_hex, 16), b, DH_P)
    s.sendall((f"{B:0512x}" + "\n").encode())
    del b                                        # khoá tạm biến mất ngay — bí mật chuyển tiếp
    kp = _kdf_kênh(chung)
    print(f"[kênh kín] máy chủ đúng vân tay {vân_tay_thật} · chữ ký DH hợp lệ")
    print(f"           ChaCha20 + HMAC-SHA256 · Diffie-Hellman 2048-bit (có bí mật chuyển tiếp)")
    print(f"           tự ĐỔI KHOÁ sau mỗi {REKEY_MỖI} khung (rekey — phiên dài không dùng mãi một khoá)")
    kênh = Kênh(kp)

    def nhận():
        khung = _hút_dòng(s)
        if not khung.strip(): return ""
        ra = kênh.mở(khung)
        return ra if ra is not None else "[gói hỏng hoặc thẻ sai]"

    def _rekey_nếu_đến_hạn(ép=False):
        if ép or kênh.đếm_lên >= REKEY_MỖI:
            if đổi_khoá(s, kênh):
                print("[kênh kín] ĐÃ ĐỔI KHOÁ giữa phiên — khoá cũ vứt, số đếm về 0", flush=True)
            else:
                print("[kênh kín] ⚠ đổi khoá KHÔNG thành — giữ khoá cũ", flush=True)

    print(nhận(), end="", flush=True)
    if kịch is not None:
        for dòng in kịch:
            if dòng in ("@đổi_khoá", "@doi_khoa"):       # cho nghiệm thu ép rekey giữa kịch bản
                _rekey_nếu_đến_hạn(ép=True); continue
            _rekey_nếu_đến_hạn()
            s.sendall((kênh.đóng(dòng) + "\n").encode())
            print(dòng)
            print(nhận(), end="", flush=True)
        s.close(); return

    try:
        while True:
            try: dòng = input()
            except (EOFError, KeyboardInterrupt): break
            _rekey_nếu_đến_hạn()
            s.sendall((kênh.đóng(dòng) + "\n").encode())
            ra = nhận()
            print(ra, end="", flush=True)
            if not ra: break
    finally:
        s.close()
        print("\n[khách] đã ngắt.")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
kiem_tu_xa.py — nghiệm thu MẠNG RA HOST (B1') + ĐĂNG NHẬP TỪ XA (C4)
================================================================================
Điều phải chứng minh KHÔNG phải "nối được", mà là:
  • ổ cắm TCP chỉ tồn tại khi host CẤP năng lực (chưa cấp ⇒ tên không tồn tại = sandbox bẩm sinh);
  • năng lực bị KẸP phạm vi: cổng ngoài danh sách → từ chối thẳng;
  • phiên từ xa xác thực bằng ĐÚNG sổ /hệ/mật_khẩu, KHÔNG có cửa riêng;
  • phiên từ xa chạy dưới ĐÚNG uid ⇒ quyền, cổng bất-khả-hồi, audit vẫn nguyên;
  • KHÔNG nói rõ sai tên hay sai mật khẩu.

    python kiem_tu_xa.py
"""
import os, sys, time, socket, subprocess

P = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
PY = sys.executable
CỔNG = 2223

tổng = rớt = 0
def ca(tên, điều_kiện, ct=""):
    global tổng, rớt; tổng += 1
    print(f"  {'✓' if điều_kiện else '✗'} {tên}" + ("" if điều_kiện else f"   ← {ct}"))
    if not điều_kiện: rớt += 1

def chạy_giao(mã, *cờ):
    "Chạy một đoạn GIAO rời, trả stdout+stderr."
    t = os.path.join(P, "_kiem_tu_xa_tam.giao")
    with open(t, "w", encoding="utf-8") as f: f.write(mã)
    try:
        r = subprocess.run([PY, "giao.py", t, *cờ], capture_output=True, text=True,
                           env=ENV, cwd=P, encoding="utf-8", timeout=120)
        return (r.stdout or "") + (r.stderr or "")
    finally:
        try: os.remove(t)
        except OSError: pass

print("=" * 68); print("NGHIỆM THU MẠNG RA HOST (B1') + ĐĂNG NHẬP TỪ XA (C4)"); print("=" * 68)

print("\n[1] Năng lực `mạng_host`: sandbox bẩm sinh + kẹp phạm vi")
o = chạy_giao('thử { rọi ổ_nghe(9998) } bắt (l) { rọi "CHẶN: " + l }')
ca("★★ CHƯA CẤP thì tên ổ_nghe KHÔNG TỒN TẠI (không phải 'bị từ chối' — là không có)",
   "CHẶN:" in o and "chưa định nghĩa" in o)
o = chạy_giao('thử { rọi ổ_nghe(9998) } bắt (l) { rọi "CHẶN: " + l }', "--cho-mạng", "9997")
ca("★★ CẤP RỒI vẫn bị KẸP: cổng ngoài danh sách → từ chối thẳng",
   "NGOÀI phạm vi được cấp" in o)
o = chạy_giao('đặt S = ổ_nghe(9997)\nrọi loại(S)\nrọi ổ_nhận(S)\nrọi ổ_đóng(S)', "--cho-mạng", "9997")
ca("cổng ĐƯỢC cấp thì mở được, chưa ai tới → ẩn (không chặn cả hệ)",
   "số" in o and "ẩn" in o and "sáng" in o)
o = chạy_giao('thử { rọi ổ_nối("8.8.8.8", 9997) } bắt (l) { rọi "CHẶN: " + l }', "--cho-mạng", "9997")
ca("★ nối ra máy NGOÀI 127.0.0.1 → từ chối (mặc định chỉ localhost)",
   "NGOÀI phạm vi" in o)

print("\n[2] Máy chủ từ xa lên, khách nối vào")
mc = subprocess.Popen([PY, "-u", "chay_hdh_xa.py", "--cổng", str(CỔNG)],
                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                      env=ENV, cwd=P, encoding="utf-8", text=True)
try:
    sẵn = False
    t0 = time.time()
    while time.time() - t0 < 90:
        try:
            s = socket.create_connection(("127.0.0.1", CỔNG), timeout=1); s.close()
            sẵn = True; break
        except OSError:
            time.sleep(0.5)
    ca("máy chủ mở được cổng và nghe được", sẵn)

    def phiên(*dòng):
        r = subprocess.run([PY, "khach_xa.py", "--cổng", str(CỔNG), "--kịch", *dòng],
                           capture_output=True, text=True, env=ENV, cwd=P,
                           encoding="utf-8", timeout=180)
        return (r.stdout or "") + (r.stderr or "")

    o = phiên("an", "sai-bét", "an", "an", "tôi", "xem /hệ/mật_khẩu", "xoá /tạm/rác1", "thoát")
    ca("★ có màn ĐĂNG NHẬP từ xa, TRÊN KÊNH MÃ HOÁ CÓ BÍ MẬT CHUYỂN TIẾP",
       "kênh MÃ HOÁ, có bí mật chuyển tiếp" in o and "Tên đăng nhập:" in o and "Mật khẩu:" in o
       and "chữ ký DH hợp lệ" in o and "Diffie-Hellman 2048-bit" in o)
    ca("★★ sai mật khẩu bị TỪ CHỐI", "Sai tên đăng nhập hoặc mật khẩu." in o)
    ca("★ KHÔNG chỉ điểm sai TÊN hay sai MẬT KHẨU", "không có người" not in o.lower())
    ca("★★★ xác thực bằng ĐÚNG sổ /hệ/mật_khẩu ⇒ vào được, có phiên vỏ thật",
       "Xin chào an." in o and "Phiên vỏ là tiến-trình" in o)
    ca("★★★ phiên từ xa chạy dưới ĐÚNG uid", "an (uid 1000)" in o)
    ca("★★★ QUYỀN vẫn chặn y hệt ngồi tại máy", "xem: cấm đọc /hệ/mật_khẩu" in o)
    ca("★★★ CỔNG BẤT-KHẢ-HỒI vẫn giữ việc lại", "CẦN PHÊ DUYỆT — xoá(/tạm/rác1)" in o)
    ca("`thoát` đóng phiên sạch", "tạm biệt" in o)

    o = phiên("gốc", "gốc", "tôi", "xem /hệ/mật_khẩu", "thoát")
    ca("★★ gốc-quyền từ xa thì ĐỌC ĐƯỢC sổ bóng — và thấy BĂM, không thấy mật khẩu",
       "gốc (uid 0)" in o and "$g3$" in o and "gốc:gốc" not in o)

    o = phiên("an", "an", "nhật_ký 40", "thoát")
    ca("★★ audit ghi cả việc làm TỪ XA (không có đường tắt nào không bị ghi)",
       "tt" in o and "đọc" in o and "ai" in o)

    # ---------------- KÊNH KÍN: soi thẳng trên DÂY ----------------
    print("\n[3] ★★★ Kênh MÃ HOÁ — soi thẳng byte trên dây")
    sys.path.insert(0, P)
    import hashlib, secrets, importlib
    kx = importlib.import_module("khach_xa")

    with open(os.path.join(P, "khoa_may_cong.txt"), encoding="utf-8") as f:
        pk = f.read().strip().split("|")
    e_, n_ = int(pk[1]), int(pk[2], 16)
    k_ = (n_.bit_length() + 7) // 8
    vân_thật = hashlib.sha256(f"{n_:x}".encode()).hexdigest()[:16]

    P_ = int("".join("""
        ffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020bbea63b139b22
        514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe1356d6d51c245e485b576625e7ec6
        f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5a899fa5ae9f24117c4b1fe649286651ece45b3d
        c2007cb8a163bf0598da48361c55d39a69163fa8fd24cf5f83655d23dca3ad961c62f356208552bb
        9ed529077096966d670c354e4abc9804f1746c08ca18217c32905e462e36ce3be39e772c180e8603
        9b2783a2ec07a28fb5c55df06f4c52c9de2bcbf6955817183995497cea956ae515d2261898fa0510
        15728e5a8aacaa68ffffffffffffffff""".split()), 16)

    def bắt_tay():
        "Làm đúng phần khách: đối chiếu vân tay · kiểm chữ ký DH · trao B · dựng khoá phiên."
        s = socket.create_connection(("127.0.0.1", CỔNG), timeout=5)
        chào = kx._hút_dòng(s).strip().split()
        A_hex, ký_hex = chào[2], chào[3]
        em = f"{pow(int(ký_hex, 16), e_, n_):0{k_ * 2}x}"
        mong = ("0001" + "ff" * (k_ - 54) + "00" + "3031300d060960864801650304020105000420"
                + hashlib.sha256(A_hex.encode()).hexdigest())
        b = int.from_bytes(secrets.token_bytes(32), "big") + 2
        s.sendall((f"{pow(2, b, P_):0512x}" + "\n").encode())
        gốc = pow(int(A_hex, 16), b, P_).to_bytes(256, "big")
        kp = b""; i = 1
        while len(kp) < 96:
            kp += hashlib.sha256(gốc + f"GIAO-kênh-{i}".encode()).digest(); i += 1
        return s, chào, kx.Kênh(kp[:96]), (em == mong), A_hex

    s, chào, kênh, ký_ok, A1 = bắt_tay()
    ca("★★ máy chủ chào bằng VÂN TAY khoá máy (khách đối chiếu như known_hosts)",
       chào[0] == "GIAO-DH" and chào[1] == vân_thật, " ".join(chào)[:60])
    ca("★★★ giá trị DH của máy có CHỮ KÝ hợp lệ bằng khoá máy — không có nó thì DH vô nghĩa "
       "trước kẻ đứng giữa", ký_ok)
    _ = kênh.mở(kx._hút_dòng(s))                       # "Tên đăng nhập: "
    s.sendall((kênh.đóng("an") + "\n").encode()); kx._hút_dòng(s)
    s.sendall((kênh.đóng("an") + "\n").encode()); kx._hút_dòng(s)
    BÍ_MẬT = "SEN-VANG-BI-MAT-9137"
    s.sendall((kênh.đóng(f'nói "{BÍ_MẬT}"') + "\n").encode())
    dây = kx._hút_dòng(s)
    rõ = kênh.mở(dây)
    ca("★★★ CHỮ TRÊN DÂY KHÔNG ĐỌC ĐƯỢC: bí mật KHÔNG hiện trong byte truyền đi",
       BÍ_MẬT not in dây, dây[:80])
    ca("★★★ nhưng GIẢI RA thì đúng nguyên văn", rõ is not None and BÍ_MẬT in rõ, str(rõ)[:80])

    # sửa MỘT ký tự bản mã → thẻ HMAC gãy, máy chủ từ chối chứ không giải bừa
    kh = kênh.đóng("tôi")
    p3 = kh.split(":")
    hỏng = f"{p3[0]}:{'f' if p3[1][0] != 'f' else '0'}{p3[1][1:]}:{p3[2]}"
    s.sendall((hỏng + "\n").encode())
    o2 = kênh.mở(kx._hút_dòng(s)) or ""
    ca("★★★ sửa MỘT ký tự trên dây → THẺ XÁC THỰC SAI, máy chủ KHÔNG giải bừa",
       "THẺ XÁC THỰC SAI" in o2, o2[:90])

    # phát lại một khung cũ → số đếm không tiến → bỏ
    s.sendall((kh + "\n").encode()); kênh.mở(kx._hút_dòng(s))
    s.sendall((kh + "\n").encode())
    o3 = kênh.mở(kx._hút_dòng(s)) or ""
    ca("★★ PHÁT LẠI khung cũ bị bỏ (số đếm phải tiến)", "LẶP LẠI" in o3, o3[:90])
    s.close()

    # ★★★ BÍ MẬT CHUYỂN TIẾP: mỗi phiên một khoá TẠM mới ⇒ giá trị DH của máy phải KHÁC nhau
    s2, chào2, kênh2, ký_ok2, A2 = bắt_tay()
    ca("★★★ MỖI PHIÊN một khoá TẠM mới (giá trị DH khác hẳn) — nền của bí mật chuyển tiếp",
       A1 != A2 and ký_ok2, f"A1[:16]={A1[:16]} A2[:16]={A2[:16]}")
    ca("★★★ khoá phiên hai lần KHÁC nhau ⇒ lộ khoá máy về sau KHÔNG giải nổi phiên cũ",
       kênh.lên != kênh2.lên and kênh.mac != kênh2.mac)
    s2.close()

    o = phiên("gốc", "gốc", "xem /hệ/khoá_máy", "thoát")
    ca("★ khoá RIÊNG của máy để 600 — nhưng gốc-quyền vẫn đọc được (đúng vai)", "rsa|" in o)
    o = phiên("an", "an", "xem /hệ/khoá_máy", "thoát")
    ca("★★ người thường KHÔNG đọc nổi khoá riêng của máy", "cấm đọc /hệ/khoá_máy" in o)

    # ---------------- ĐỔI KHOÁ GIỮA PHIÊN (rekey) ----------------
    print("\n[4] ★★★ ĐỔI KHOÁ GIỮA PHIÊN (rekey) — phiên dài không dùng mãi một khoá")
    o = phiên("an", "an", "tôi", "@đổi_khoá", "tôi", "thoát")
    ca("★★ khách ép đổi khoá giữa phiên — phiên vỏ vẫn chạy tiếp như không",
       "ĐÃ ĐỔI KHOÁ giữa phiên" in o and o.count("an (uid 1000)") >= 2 and "tạm biệt" in o)

    s3, _, kênh3, _, _ = bắt_tay()
    _ = kênh3.mở(kx._hút_dòng(s3))                     # "Tên đăng nhập: "
    s3.sendall((kênh3.đóng("an") + "\n").encode()); kx._hút_dòng(s3)
    s3.sendall((kênh3.đóng("an") + "\n").encode()); kx._hút_dòng(s3)
    khoá_cũ = kx.Kênh(kênh3.lên + kênh3.xuống + kênh3.mac)   # bản sao GIỮ KHOÁ CŨ để soi
    ok_rk = kx.đổi_khoá(s3, kênh3)
    ca("★★★ trao DH mới NGAY TRONG kênh cũ (đã xác thực HMAC nên không cần ký lại), "
       "số đếm về 0", ok_rk and kênh3.đếm_lên == 0 and kênh3.đếm_xuống == 0)
    ca("★★★ khoá đổi THẬT: cả ba khoá (lên · xuống · MAC) đều khác trước",
       kênh3.lên != khoá_cũ.lên and kênh3.xuống != khoá_cũ.xuống and kênh3.mac != khoá_cũ.mac)
    s3.sendall((kênh3.đóng("tôi") + "\n").encode())
    dây3 = kx._hút_dòng(s3)
    ca("★★★ khung SAU rekey: khoá MỚI mở được — khoá CŨ thì KHÔNG (lộ khoá cũ không đọc "
       "được khúc sau)", "an (uid 1000)" in (kênh3.mở(dây3) or "") and khoá_cũ.mở(dây3) is None)
    s3.close()

    # ---------------- MÁY CHỦ ÉP ĐỔI KHOÁ (học RekeyLimit của sshd) ----------------
    print("\n[4b] ★★★ MÁY CHỦ ÉP đổi khoá — an toàn KHÔNG treo vào thiện chí của khách")
    s4, _, kênh4, _, _ = bắt_tay()
    _ = kênh4.mở(kx._hút_dòng(s4))
    s4.sendall((kênh4.đóng("an") + "\n").encode()); kx._hút_dòng(s4)
    s4.sendall((kênh4.đóng("an") + "\n").encode()); kx._hút_dòng(s4)

    # KHÁCH BƯỚNG: cứ gõ mãi trên MỘT khoá, không thèm đổi. Máy chủ phải tự cắt.
    bị_ép = ""
    for i in range(90):
        s4.sendall((kênh4.đóng("tôi") + "\n").encode())
        ra = kênh4.mở(kx._hút_dòng(s4)) or ""
        if "CẦN ĐỔI KHOÁ" in ra:
            bị_ép = ra; break
    ca("★★★ khách BƯỚNG không đổi khoá → máy chủ NGỪNG PHỤC VỤ (sshd chỉ tự đổi phía mình; "
       "ở đây hạn được ÉP)", "CẦN ĐỔI KHOÁ" in bị_ép, bị_ép[:110] or "(không hề bị chặn)")
    ca("★ lời từ chối nói rõ hạn và cách đi tiếp", "ĐỔI_KHOÁ" in bị_ép and "hạn 64" in bị_ép)

    đổi_xong = kx.đổi_khoá(s4, kênh4)
    s4.sendall((kênh4.đóng("tôi") + "\n").encode())
    sau = kênh4.mở(kx._hút_dòng(s4)) or ""
    ca("★★ đường thoát DUY NHẤT là đổi khoá — đổi xong thì gõ tiếp được ngay",
       đổi_xong and "an (uid 1000)" in sau, sau[:90])
    s4.close()

    o = phiên("an", "an", *["tôi"] * 70, "thoát")
    ca("★★ khách TỬ TẾ (tự đổi mỗi 32 khung) chạy 70 lệnh không hề vướng hạn",
       "CẦN ĐỔI KHOÁ" not in o and o.count("ĐÃ ĐỔI KHOÁ giữa phiên") >= 2
       and o.count("an (uid 1000)") >= 70)

    s5, _, kênh5, _, _ = bắt_tay()
    _ = kênh5.mở(kx._hút_dòng(s5))
    s5.sendall((kênh5.đóng("an") + "\n").encode()); kx._hút_dòng(s5)
    s5.sendall((kênh5.đóng("an") + "\n").encode()); kx._hút_dòng(s5)
    s5.sendall((kênh5.đóng("nói " + "x" * 9000) + "\n").encode())
    o5 = kênh5.mở(kx._hút_dòng(s5)) or ""
    ca("★★ khung QUÁ DÀI bị bỏ TRƯỚC khi giải (chặn bộ nhớ, và giữ cận trên dữ liệu/khoá)",
       "khung quá dài" in o5, o5[:90])
    s5.close()

    # ---------------- CHỐNG DÒ MẬT KHẨU từ xa ----------------
    print("\n[5] ★★ CHỐNG DÒ MẬT KHẨU từ xa — chậm dần + ngắt kết nối")
    o1 = phiên("dò-xa", "x", "dò-xa", "x", "dò-xa", "x")
    ca("★★ 3 lần sai trong MỘT kết nối → máy chủ NGẮT (kẻ dò phải tốn công bắt tay DH lại)",
       "Sai quá nhiều lần — ngắt." in o1)
    o2 = phiên("dò-xa", "x", "dò-xa", "x", "dò-xa", "x")
    ca("★★★ sổ chậm dần theo TÊN sống qua kết nối mới: nối lại vẫn bị bắt chờ",
       "chậm dần: thử lại sau" in o2)
    ca("★ thông điệp chậm dần KHÔNG chỉ điểm sai tên hay sai mật khẩu",
       "không có người" not in (o1 + o2).lower())
finally:
    mc.terminate()
    try: mc.wait(timeout=10)
    except subprocess.TimeoutExpired: mc.kill()

print("\n" + "=" * 68)
print(f"TỪ XA: {tổng - rớt}/{tổng} hạng mục đạt" + ("" if rớt == 0 else f"  — {rớt} RỚT"))
print("=" * 68)
sys.exit(1 if rớt else 0)

# -*- coding: utf-8 -*-
"""
chay_hdh_xa.py — HĐH-GIAO MỞ CỔNG ĐĂNG NHẬP TỪ XA (C4, trên nền B1')
================================================================================
    python chay_hdh_xa.py [--cổng 2222] [--nhịp 400]

Rồi từ cửa sổ khác:  python khach_xa.py           (hoặc bất kỳ telnet-client nào)

Python ở đây CHỈ làm hai việc: cấp năng lực `mạng_host` (ổ cắm TCP) và quay bánh xe nhân.
Toàn bộ phần XÉT — đón khách, hỏi tên, xác thực bằng /hệ/mật_khẩu, sinh phiên vỏ dưới đúng uid,
chạy lệnh qua đúng tầng gọi-hệ — đều nằm trong GIAO (`lib_tu_xa.giao`).

Kênh MÃ HOÁ (ChaCha20+HMAC, DH bí mật chuyển tiếp, rekey giữa phiên) — vẫn chỉ nghe 127.0.0.1.
Xem ghi chú đầu `lib_tu_xa.giao`.
"""
import os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from giao import tokenize, Parser, Runtime, nạp_chuẩn, GiaoError, GiaoLimit


def _cờ(tên, mặc_định):
    for i, a in enumerate(sys.argv):
        if a == tên and i + 1 < len(sys.argv):
            try: return int(sys.argv[i + 1])
            except ValueError: return mặc_định
    return mặc_định


def main():
    cổng = _cờ("--cổng", _cờ("--cong", 2222))
    nhịp = _cờ("--nhịp", _cờ("--nhip", 0))          # 0 = chạy mãi

    rt = Runtime(); rt.base_dir = HERE
    rt.MAX_STEPS = 2_000_000_000
    rt.cấp_quyền("máy")
    rt.cấp_quyền("mạng_host", cổng=[cổng], máy=["127.0.0.1"])   # ★ B1': chỉ cổng này, chỉ localhost
    rt.cấp_quyền("ngẫu_nhiên")                                  # ★ entropy THẬT — cho khoá tạm DH
    rt.cấp_quyền("giờ")                                         # ★ đồng hồ — cho CHẬM DẦN chống dò mật khẩu
    nạp_chuẩn(rt)

    def G(mã): rt.exec_block(Parser(tokenize(mã)).parse())

    with open(os.path.join(HERE, "hdh_nền.giao"), encoding="utf-8") as f:
        G(f.read())
    G('nhập "lib_tu_xa.giao"')

    # ---- KHOÁ MÁY: sinh MỘT LẦN trên đĩa host, rồi nạp vào hệ-tệp GIAO ----
    # Khoá riêng vào /hệ/khoá_máy (600, chỉ gốc-quyền đọc) — máy chủ PHẢI giữ khoá riêng của
    # chính nó, khác với kho phần mềm (khoá riêng của kho không bao giờ vào máy).
    import lam_khoa
    tệp_riêng = os.path.join(HERE, "khoa_may.txt")
    if not os.path.exists(tệp_riêng):
        print("  [khoá máy] chưa có — đang sinh RSA-2048 (một lần)…", flush=True)
        cũ_r, cũ_c = lam_khoa.TỆP_RIÊNG, lam_khoa.TỆP_CÔNG
        lam_khoa.TỆP_RIÊNG = tệp_riêng
        lam_khoa.TỆP_CÔNG = os.path.join(HERE, "khoa_may_cong.txt")
        lam_khoa.sinh()
        lam_khoa.TỆP_RIÊNG, lam_khoa.TỆP_CÔNG = cũ_r, cũ_c
    with open(tệp_riêng, encoding="utf-8") as f: kr = f.read().strip()
    with open(os.path.join(HERE, "khoa_may_cong.txt"), encoding="utf-8") as f: kc = f.read().strip()
    rt.glob["__kr"] = kr; rt.glob["__kc"] = kc
    G('gọi(M, TT_KHỞI, GH_TẠO, [TX_KHOÁ_MÁY, 600, __kr])\n'
      'gọi(M, TT_KHỞI, GH_TẠO, [TX_KHOÁ_CÔNG, 644, __kc])\n'
      'đặt __vt = vân_tay_máy(M, TT_KHỞI)')
    G('nếu trạng(lấy_khoá(M, "nhân"), V) != "chết" { gọi(M, V, GH_THOÁT, []) }')   # chưa ai đăng nhập
    rt.glob["__cổng"] = cổng
    G('đặt PHIÊN = bản()\nđặt __mở = mở_cổng_xa(M, TT_KHỞI, __cổng)')
    if rt.glob["__mở"] != "sáng":
        print(f"[lỗi] không mở nổi cổng {cổng} (đang bận?)"); sys.exit(1)

    print("┌────────────────────────────────────────────────────────────┐")
    print("│  HĐH-GIAO · ĐĂNG NHẬP TỪ XA                                │")
    print("└────────────────────────────────────────────────────────────┘")
    print(f"  đang nghe 127.0.0.1:{cổng}  ·  đăng nhập bằng sổ THẬT (an/an · gốc/gốc)")
    print(f"  kênh MÃ HOÁ: ChaCha20 + HMAC-SHA256 · Diffie-Hellman 2048-bit (bí mật chuyển tiếp)")
    print(f"  khoá máy chỉ dùng để KÝ giá trị DH — không tham gia tạo bí mật")
    print(f"  ĐỔI KHOÁ giữa phiên (rekey trong kênh cũ) · CHỐNG DÒ mật khẩu (chậm dần, khoá sau 10 lần)")
    print(f"  vân tay khoá máy: {rt.glob['__vt']}   ← khách phải thấy ĐÚNG chuỗi này")
    print(f"  nối vào:  python khach_xa.py --cổng {cổng}")
    print("  ⚠ chưa qua thẩm định mật mã — xem ghi chú đầu lib_kenh.giao / lib_dh.giao")
    print("  Ctrl-C để tắt\n", flush=True)

    đã = 0
    try:
        while True:
            try:
                G('đặt _ = phục_vụ_xa(M, TT_KHỞI, __cổng, PHIÊN, 1)\n'
                  'đặt _ = vòng_nhân(M, 2)')
            except (GiaoError, GiaoLimit) as e:
                print(f"[lỗi hệ] {getattr(e, 'msg', e)}", flush=True)
            đã += 1
            if nhịp and đã >= nhịp: break
            time.sleep(0.02)                        # nhường CPU cho host, khỏi quay tít
    except KeyboardInterrupt:
        print("\n[HĐH-GIAO] tắt cổng từ xa.")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
chay_kho_xa.py — MỘT KHO PHẦN MỀM Ở NGOÀI (đóng vai máy chủ kho trên mạng)
================================================================================
    python chay_kho_xa.py --dựng            # dựng kho mẫu + sinh khoá riêng CỦA KHO
    python chay_kho_xa.py [--cổng 2280]     # chạy máy chủ kho

Đây KHÔNG phải một phần của HĐH-GIAO — nó là "máy của người giữ kho" nằm đâu đó ngoài kia.
Nên nó viết bằng Python cho gọn: phần đáng nói (tải · KIỂM CHỮ KÝ · kiểm băm · cài) nằm ở phía
HĐH, trong `lib_kho.giao`.

Giao thức trần trụi, đúng một dòng:  `LẤY <thứ>\\n`  →  máy chủ trả nội dung rồi ĐÓNG.
`<thứ>` ∈ { mục_lục · chữ_ký · khoá_công · gói/<tên> }

Vì sao KHÔNG mã hoá: mục lục và gói vốn công khai. Cái cần là TOÀN VẸN + XÁC THỰC, mà chữ ký đã
lo — sửa một byte trên đường là chữ ký gãy, HĐH bỏ hết, không ghi gì. (SSH phải mã hoá vì nó chở
mật khẩu; kho thì không chở bí mật nào.)
"""
import os, sys, socket, hashlib, threading

HERE = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(HERE, "kho_xa")
sys.path.insert(0, HERE)
import lam_khoa

# tên | phiên | nhóm | phụ thuộc | năng lực | mô tả | THÂN
GÓI_XA = [
    ("chào_xa", "1.0", "Mạng", "", "",
     "gói tải VỀ TỪ MẠNG — chào một tiếng",
     '# chào_xa — gói này tải về từ kho ở ngoài\nnói "chào từ kho xa!"\ntôi'),
    ("soi_mạng", "1.1", "Mạng", "chào_xa", "",
     "soi thiết bị mạng (cần chào_xa)",
     '# soi_mạng\nchào_xa\nnói "── mạng ──"\nxem /tb/mạng'),
    ("dao_xa", "1.0", "Tệp", "", "xoá",
     "gói xa ĐÒI năng lực xoá — phải đồng ý mới cài",
     '# dao_xa\nnói "(bản demo, không xoá gì)"'),
]


def dựng():
    os.makedirs(os.path.join(KHO, "gói"), exist_ok=True)
    # khoá RIÊNG của kho xa — khác hẳn khoá của kho cục bộ, để chứng minh neo tin cậy có tác dụng
    r, c = lam_khoa.TỆP_RIÊNG, lam_khoa.TỆP_CÔNG
    lam_khoa.TỆP_RIÊNG = os.path.join(KHO, "khoa_rieng.txt")
    lam_khoa.TỆP_CÔNG = os.path.join(KHO, "khoa_cong.txt")
    if not os.path.exists(lam_khoa.TỆP_RIÊNG):
        print("  [kho xa] sinh khoá riêng của KHO (một lần)…"); lam_khoa.sinh()
    dòng = []
    for tên, phiên, nhóm, pt, nl, mô, thân in GÓI_XA:
        with open(os.path.join(KHO, "gói", tên), "w", encoding="utf-8") as f: f.write(thân)
        băm = hashlib.sha256(thân.encode("utf-8")).hexdigest()
        dòng.append(f"{tên}|{phiên}|{nhóm}|{pt}|{nl}|{băm}|{mô}")
    mục = "\n".join(dòng)
    with open(os.path.join(KHO, "mục_lục"), "w", encoding="utf-8") as f: f.write(mục)
    with open(os.path.join(KHO, "chữ_ký"), "w", encoding="utf-8") as f: f.write(lam_khoa.ký(mục))
    lam_khoa.TỆP_RIÊNG, lam_khoa.TỆP_CÔNG = r, c
    with open(os.path.join(KHO, "khoa_cong.txt"), encoding="utf-8") as f:
        n = f.read().strip().split("|")[2]
    print(f"  ✓ kho xa dựng ở {KHO} · {len(GÓI_XA)} gói")
    print(f"  vân tay khoá KHO XA: {hashlib.sha256(n.encode()).hexdigest()[:16]}")


def _đọc_thứ(thứ):
    thứ = thứ.strip()
    if thứ in ("mục_lục", "chữ_ký", "khoá_công"):
        tệp = {"khoá_công": "khoa_cong.txt"}.get(thứ, thứ)
        đường = os.path.join(KHO, tệp)
    elif thứ.startswith("gói/") and "/" not in thứ[4:] and ".." not in thứ:
        đường = os.path.join(KHO, "gói", thứ[4:])
    else:
        return None
    if not os.path.exists(đường): return None
    with open(đường, encoding="utf-8") as f: return f.read()


def phục_vụ(kh, addr, kể):
    try:
        kh.settimeout(5)
        yc = b""
        while b"\n" not in yc:
            d = kh.recv(4096)
            if not d: return
            yc += d
        dòng = yc.decode("utf-8", "replace").strip()
        if not dòng.startswith("LẤY "):
            kh.sendall(b"KHONG-HIEU\n"); return
        thứ = dòng[4:]
        nội = _đọc_thứ(thứ)
        if kể: print(f"  → {addr[0]} xin '{thứ}' … {'gửi' if nội else 'KHÔNG CÓ'}", flush=True)
        kh.sendall((nội if nội is not None else "KHÔNG-CÓ").encode("utf-8"))
    except OSError:
        pass
    finally:
        try: kh.close()
        except OSError: pass


def main():
    if "--dựng" in sys.argv or "--dung" in sys.argv:
        dựng(); return
    cổng = 2280
    for i, a in enumerate(sys.argv):
        if a in ("--cổng", "--cong") and i + 1 < len(sys.argv):
            try: cổng = int(sys.argv[i + 1])
            except ValueError: pass
    if not os.path.exists(os.path.join(KHO, "mục_lục")):
        print("  [kho xa] chưa dựng — đang dựng…"); dựng()
    kể = "--im" not in sys.argv
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", cổng)); s.listen(8)
    print(f"[kho xa] đang phục vụ {KHO} trên 127.0.0.1:{cổng}", flush=True)
    try:
        while True:
            kh, addr = s.accept()
            threading.Thread(target=phục_vụ, args=(kh, addr, kể), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[kho xa] tắt.")
    finally:
        s.close()


if __name__ == "__main__":
    main()

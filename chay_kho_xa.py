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
import shutil, subprocess

# v0.44: kho xa KHÔNG còn dựng/ký bằng Python (lam_khoa.py đã bỏ). Gói nguồn ở goi_xa/, dựng + ký kép bằng
# BỘ CÔNG CỤ GIAO (goi.giao trên GVM-64) với khoá RIÊNG của kho xa (.khoa/kho_xa — khác khoá kho gói).
NGUỒN_XA = os.path.join(HERE, "goi_xa")
KHOÁ_XA = os.path.join(HERE, ".khoa", "kho_xa")


def dựng():
    sh = shutil.which("sh") or r"C:\Program Files\Git\usr\bin\sh.exe"
    env = dict(os.environ, GOI_NGUON=NGUỒN_XA, GOI_RA=KHO, GOI_KHOA=KHOÁ_XA)
    if not os.path.exists(os.path.join(KHOÁ_XA, "rieng.txt")):
        print("  [kho xa] sinh khoá KÉP của KHO XA (một lần, bằng goi.giao)…", flush=True)
        subprocess.run([sh, os.path.join(HERE, "goi.sh"), "khoa"], env=env, cwd=HERE, check=True,
                       stdout=subprocess.DEVNULL)
    r = subprocess.run([sh, os.path.join(HERE, "goi.sh"), "dung"], env=env, cwd=HERE,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0: raise SystemExit("[kho xa] dựng hỏng:\n" + r.stdout[-800:] + r.stderr[-800:])
    print("  " + r.stdout.strip().splitlines()[-1])


def _đọc_thứ(thứ):
    thứ = thứ.strip()
    if thứ in ("mục_lục", "chữ_ký", "khoá_công"):
        đường = os.path.join(KHO, thứ)
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
    if not os.path.exists(os.path.join(KHO, "khoá_công")):
        print("  [kho xa] chưa dựng — đang dựng…"); dựng()
    kể = "--im" not in sys.argv
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):                # Windows: KHÔNG cho tiến-trình khác chiếm chung cổng
        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    else:
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

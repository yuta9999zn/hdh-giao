# -*- coding: utf-8 -*-
"""
kiem_thoat_host.py — NGHIỆM THU: KHÔNG CÓ ĐƯỜNG THOÁT RA HOST (Bước 1)
================================================================================
Chứng minh bất-biến an-toàn: từ TRONG vỏ GIAO, lệnh host NGOÀI danh sách
cho-phép KHÔNG chạy được. Cụ thể:

  • Mặc định (không --kali): mọi lệnh host ngoài allowlist tĩnh → TỪ CHỐI,
    KHÔNG cả hỏi (hỏi_chạy = None ⇒ cổng kín).
  • Chế độ --kali: KHÔNG còn cấp quyền theo TÊN-LỆNH-TRẦN. Lệnh ngoài
    allowlist phải được người dùng DUYỆT TAY TỪNG LẦN (hook hỏi_chạy), và
    hook nhận đúng CHUỖI LỆNH ĐẦY ĐỦ. Từ chối ⇒ không chạy; đồng ý ⇒ chạy.
  • allowlist tĩnh chỉ gồm 3 lệnh wsl soi-mạng, và đã trỏ /mnt/e (GIAO ở ổ E).

    python kiem_thoat_host.py
"""
import os, sys, io, contextlib

P = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, P)
os.environ.setdefault("PYTHONUTF8", "1")

from giao import Runtime, nạp_chuẩn, GiaoError, AN
import chay_hdh_giao

tổng = rớt = 0
def ca(tên, điều_kiện, ct=""):
    global tổng, rớt; tổng += 1
    print(f"  {'✓' if điều_kiện else '✗'} {tên}" + ("" if điều_kiện else f"   ← {ct}"))
    if not điều_kiện: rớt += 1

def gọi_chạy(rt, cmd, đối):
    "Gọi builtin `chạy` của GIAO như vỏ gọi; trả giá trị (chuỗi out | AN khi bị chặn)."
    return rt.glob["chạy"]([cmd, đối])

print("=" * 68); print("NGHIỆM THU: KHÔNG CÓ ĐƯỜNG THOÁT RA HOST (Bước 1)"); print("=" * 68)

# ---------------- 1. builtin `chạy`: cổng kín mặc định ----------------
print("\n[1] builtin `chạy`: mặc định KÍN (không hook ⇒ không hỏi, chặn thẳng)")
rt = Runtime(); nạp_chuẩn(rt)
PY = sys.executable
rt.cấp_quyền("chạy", lệnh=[f'{PY} -c print(42)'])  # chỉ cho ĐÚNG một lệnh đầy đủ

out = gọi_chạy(rt, PY, ['-c', 'print(42)'])
ca("lệnh ĐÚNG trong allowlist chạy được", out is not AN and "42" in str(out), f"{out!r}")

out = gọi_chạy(rt, PY, ['-c', 'print(99)'])
ca("lệnh KHÁC (ngoài allowlist) bị TỪ CHỐI (→ ẩn)", out is AN, f"{out!r}")
ca("không có hook ⇒ không hỏi (hỏi_chạy=None)", rt.hỏi_chạy is None)

# tên-lệnh-trần KHÔNG đủ: cấp 'nmap' kiểu cũ đã bị bỏ — ở đây allowlist không có nmap
out = gọi_chạy(rt, "nmap", ['-sn', '10.0.0.0/24'])
ca("tên lệnh host tuỳ ý bị chặn (→ ẩn)", out is AN, f"{out!r}")

# ---------------- 2. hook DUYỆT-TỪNG-LẦN: thấy nguyên lệnh, từ chối/đồng ý ----------------
print("\n[2] hook duyệt-từng-lần: nhận đúng chuỗi đầy đủ; từ chối ⇒ chặn, đồng ý ⇒ chạy")
rt2 = Runtime(); nạp_chuẩn(rt2)
rt2.cấp_quyền("chạy", lệnh=[])  # allowlist RỖNG ⇒ mọi lệnh phải qua hook

thấy = []
rt2.hỏi_chạy = lambda full: (thấy.append(full), False)[1]   # luôn TỪ CHỐI
out = gọi_chạy(rt2, PY, ['-c', 'print(7)'])
ca("hook bị hỏi với CHUỖI ĐẦY ĐỦ", len(thấy) == 1 and thấy[0] == f'{PY} -c print(7)', f"{thấy}")
ca("hook từ chối ⇒ lệnh KHÔNG chạy (→ ẩn)", out is AN, f"{out!r}")

rt2.hỏi_chạy = lambda full: True   # giờ ĐỒNG Ý
out = gọi_chạy(rt2, PY, ['-c', 'print(7)'])
ca("hook đồng ý ⇒ lệnh chạy", out is not AN and "7" in str(out), f"{out!r}")

# ---------------- 3. Máy thật: allowlist chỉ có 3 wsl, trỏ /mnt/e ----------------
print("\n[3] Máy HĐH thật: allowlist tĩnh gọn, đường dẫn đã sang /mnt/e")
m_k = chay_hdh_giao.Máy(kali=True)
cho = m_k.rt.caps["chạy"]["lệnh"]
ca("đúng 3 lệnh wsl trong allowlist tĩnh", len(cho) == 3, f"{cho}")
ca("toàn bộ trỏ /mnt/e (không còn /mnt/d)", all("/mnt/e/" in c for c in cho) and not any("/mnt/d/" in c for c in cho), f"{cho}")
for xấu in ("nmap", "cat", "git", "bash", "sh", "python3", "curl"):
    ca(f"KHÔNG còn tên-lệnh-trần '{xấu}' trong allowlist", xấu not in cho)
ca("--kali gắn hook duyệt-từng-lần", callable(m_k.rt.hỏi_chạy))

m_thường = chay_hdh_giao.Máy(kali=False)
ca("không --kali ⇒ cổng kín (hỏi_chạy=None)", m_thường.rt.hỏi_chạy is None)

# ---------------- 4. TỪ TRONG VỎ: chạy_thật lệnh ngoài list → chặn ----------------
print("\n[4] Từ trong vỏ GIAO: `chạy_thật <lệnh ngoài list>` bị chặn end-to-end")

def gõ_bắt(máy, dòng):
    "Gõ một dòng vào vỏ; trả (mã_thoát, text_in_ra)."
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mã = máy.gõ(dòng, lát_nền=0)
    return mã, buf.getvalue()

# 4a. kali + hook từ chối
m_k.rt.hỏi_chạy = lambda full: False
mã, o = gõ_bắt(m_k, "chạy_thật nmap -sn 192.168.1.0/24")
ca("vỏ (kali, từ chối): nmap KHÔNG chạy", mã != 0 and "KHÔNG chạy được" in o, f"{mã}:{o[-200:]!r}")

# 4b. không kali: cổng kín
mã, o = gõ_bắt(m_thường, "chạy_thật hostname")
ca("vỏ (mặc định): host 'hostname' bị chặn", mã != 0 and "KHÔNG chạy được" in o, f"{mã}:{o[-200:]!r}")

# 4c. kali + hook đồng ý: lệnh host vô hại chạy thật (chứng minh cổng hoạt động 2 chiều)
thấy2 = []
m_k.rt.hỏi_chạy = lambda full: (thấy2.append(full), True)[1]
mã, o = gõ_bắt(m_k, "chạy_thật hostname")
ca("vỏ (kali, đồng ý): 'hostname' chạy, hook thấy đúng lệnh",
   mã == 0 and thấy2 == ["hostname"], f"{mã}:{thấy2}:{o[-120:]!r}")

print("\n" + "=" * 68)
print(f"KẾT QUẢ: {tổng - rớt}/{tổng} đạt" + ("" if rớt == 0 else f"  — {rớt} RỚT"))
print("=" * 68)
sys.exit(1 if rớt else 0)

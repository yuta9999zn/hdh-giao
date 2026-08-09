# -*- coding: utf-8 -*-
"""
GHI SỔ CỔNG — mỗi commit một dòng kết cục, để về sau còn học được từ chính mình
================================================================================
Tác giả: Nguyễn Trường An. SỞ HỮU TRÍ TUỆ thuộc về tác giả.

VÌ SAO CÓ TỆP NÀY. GIAO có bộ kiểm thật (`kiem_toan_bo.py` — 72/72 hạng mục) nhưng **không hề
ghi lại** kết quả ấy gắn với thay đổi nào. Nghĩa là mỗi lần chạy xong, con số bay đi mất. Không
có sợi dây nối "thay đổi này" với "kết cục của nó" thì:

  · không ai biết thay đổi nào hay làm hỏng cái gì;
  · không dựng được bộ dữ liệu để đo, để dự báo, hay để nuôi một trợ thủ nào;
  · và mỉa mai nhất: GIAO xây trên chính lý thuyết γ đo-được, mà bản thân nó chưa đo được mình.

Sổ cổng chữa đúng chỗ đó. Mỗi commit một dòng JSON trong `so_cong.jsonl`:

    {commit, thời điểm, tác giả, lời nhắn, đạt, tổng, tỉ lệ, giây, các mục rớt}

CÁCH DÙNG
    python ghi_cong.py            # chấm HEAD bằng bộ kiểm ĐẦY ĐỦ (kiem_toan_bo.py)
    python ghi_cong.py --nhanh    # chấm nhanh bằng kiem_thu.py (63 ca) khi cần vòng ngắn
    python ghi_cong.py --xem      # xem lại sổ

Tự động: móc `post-commit` gọi tệp này ở **nền**, nên commit vẫn trả về ngay; kết quả rơi vào sổ
vài phút sau. Hàm ghi là **bất biến theo commit** — chạy lại cùng một hash thì không ghi trùng.

HẠN CHẾ, khai thẳng: chỉ chấm được TRẠNG THÁI HIỆN TẠI. Các commit trước khi có tệp này thì
không có kết cục, và sổ chỉ dày lên từ nay về sau. Muốn đủ dữ liệu để một trợ thủ học được thì
cần cỡ **150–200 commit có kết cục** — theo đúng ngưỡng đã đo ở các dự án khác.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

GOC = os.path.dirname(os.path.abspath(__file__))
SO = os.path.join(GOC, "so_cong.jsonl")
# Mỗi bộ kiểm in một kiểu khác nhau — thử lần lượt, KHÔNG đoán một kiểu rồi thôi.
# (Lỗi đã mắc: mẫu đầu chỉ bắt "TOÀN BỘ: 72/72", trong khi kiem_thu.py in "KẾT QUẢ: 74/74 đạt"
#  nên bộ kiểm nhanh sẽ ghi dat=None mà không ai biết.)
MAU = [re.compile(r"TOÀN BỘ:\s*(\d+)\s*/\s*(\d+)"),
       re.compile(r"KẾT QUẢ:\s*(\d+)\s*/\s*(\d+)"),
       re.compile(r"(\d+)\s*/\s*(\d+)\s*(?:ca|hạng mục)?\s*(?:đạt|pass)", re.I)]


def doc_so(ra):
    """Đọc 'đạt/tổng' từ đầu ra. Lấy lần khớp CUỐI CÙNG — dòng tổng kết luôn ở cuối."""
    for m in MAU:
        k = m.findall(ra)
        if k:
            return int(k[-1][0]), int(k[-1][1])
    return None, None


def _git(*a):
    r = subprocess.run(["git", "-C", GOC] + list(a), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return (r.stdout or "").strip()


def da_ghi(h):
    if not os.path.exists(SO):
        return False
    for ln in io.open(SO, encoding="utf-8"):
        try:
            if json.loads(ln).get("commit") == h:
                return True
        except Exception:
            pass
    return False


def cham(nhanh=False):
    kich_ban = "kiem_thu.py" if nhanh else "kiem_toan_bo.py"
    t0 = time.time()
    r = subprocess.run([sys.executable, kich_ban], cwd=GOC, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1"))
    ra = (r.stdout or "") + (r.stderr or "")
    giay = round(time.time() - t0, 1)
    dat, tong = doc_so(ra)
    rot = [ln.strip()[2:].strip() for ln in ra.splitlines() if ln.strip().startswith("✗")]
    return {"kich_ban": kich_ban, "ma_thoat": r.returncode, "dat": dat, "tong": tong,
            "ti_le": (dat / tong) if (dat is not None and tong) else None,
            "giay": giay, "so_muc_rot": len(rot), "muc_rot": rot[:20]}


KHOA = os.path.join(GOC, ".git", "ghi_cong.khoa")


def ghi(nhanh=False):
    # CHỐNG CHẠY CHỒNG: bộ kiểm đầy đủ mất ~434s; commit dày sẽ làm nhiều lượt đè lên nhau.
    if os.path.exists(KHOA) and time.time() - os.path.getmtime(KHOA) < 3600:
        print("đang có lượt chấm khác chạy — bỏ qua lượt này"); return
    io.open(KHOA, "w").write(str(os.getpid()))
    try:
        _ghi(nhanh)
    finally:
        try:
            os.remove(KHOA)
        except OSError:
            pass


def _ghi(nhanh=False):
    h = _git("rev-parse", "HEAD")
    if not h:
        print("chưa có commit nào — bỏ qua"); return
    if da_ghi(h):
        print(f"đã có trong sổ: {h[:10]} — không ghi trùng"); return
    d = {"commit": h, "commit_ngan": h[:10],
         "thoi_diem": _git("log", "-1", "--pretty=%at"),
         "tac_gia": _git("log", "-1", "--pretty=%an"),
         "loi_nhan": _git("log", "-1", "--pretty=%s"),
         "so_file_cham": len([x for x in _git("show", "--name-only", "--pretty=", "HEAD").splitlines() if x.strip()]),
         "ghi_luc": int(time.time())}
    d.update(cham(nhanh))
    with io.open(SO, "a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")
    tl = f"{d['dat']}/{d['tong']}" if d["dat"] is not None else "KHÔNG ĐỌC ĐƯỢC SỐ"
    print(f"đã ghi cổng: {h[:10]} · {tl} · {d['giay']}s · {d['loi_nhan'][:50]}")


def xem():
    if not os.path.exists(SO):
        print("sổ còn trống"); return
    ds = [json.loads(x) for x in io.open(SO, encoding="utf-8") if x.strip()]
    print(f"{len(ds)} commit đã có kết cục\n")
    print(f"{'commit':<12s}{'kết quả':>10s}{'giây':>7s}  lời nhắn")
    for d in ds[-25:]:
        kq = f"{d['dat']}/{d['tong']}" if d.get("dat") is not None else "?"
        print(f"{d['commit_ngan']:<12s}{kq:>10s}{d['giay']:>7.0f}  {d['loi_nhan'][:46]}")
    co = [d for d in ds if d.get("ti_le") is not None]
    if co:
        xanh = sum(1 for d in co if d["ti_le"] >= 1.0)
        print(f"\nđạt trọn vẹn: {xanh}/{len(co)} commit ({xanh/len(co)*100:.0f}%)")
        print(f"-> cần ~{max(0, 150 - len(co))} commit có kết cục nữa mới đủ để một trợ thủ học được")


if __name__ == "__main__":
    if "--xem" in sys.argv:
        xem()
    else:
        ghi(nhanh="--nhanh" in sys.argv)

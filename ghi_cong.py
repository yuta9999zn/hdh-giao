# -*- coding: utf-8 -*-
"""
GHI SỔ CỔNG — mỗi commit một dòng: ĐẶC TRƯNG trước cổng + KẾT CỤC TỪNG HẠNG MỤC
================================================================================
Tác giả: Nguyễn Trường An. SỞ HỮU TRÍ TUỆ thuộc về tác giả.

VÌ SAO SỬA LẠI (2026-08-09). Bản đầu chỉ ghi con số tổng ("72/72"). Đem chính sổ ấy chấm bằng
skill `project_readiness` của D:\\CDFL harness thì nó phán **not_ready**, và dòng đầu tiên mới là
điều đáng giá:

    [blocking] gate: every recorded outcome is the same (1.0)

Bộ kiểm của GIAO luôn đạt trọn vẹn. Một quyển sổ toàn điểm mười thì **dù có 150 commit cũng không
học được gì** — không có thất bại nào để học. Và nó còn thiếu một thứ nữa, nặng hơn: sổ ghi KẾT
CỤC nhưng gần như không ghi ĐẶC TRƯNG nào. Không có thứ quan sát được TRƯỚC khi cổng phán thì
không có gì để nối vào kết cục cả.

HAI CHỖ SỬA:

  1. KẾT CỤC TỪNG HẠNG MỤC. Thay vì một số tổng, ghi cả danh sách ~72 hạng mục với đạt/rớt riêng
     từng cái. Nó không tạo ra thất bại — nó làm cho thất bại, khi xảy ra, **có địa chỉ**: hỏng ở
     hạng mục nào, thuộc mục lớn nào. Một commit làm rớt 1/72 sẽ hiện ra thay vì biến mất.

  2. ĐẶC TRƯNG QUAN SÁT ĐƯỢC TRƯỚC CỔNG. Mười ba đại lượng lấy từ chính git tại thời điểm commit,
     tất cả đều biết được TRƯỚC khi chạy bộ kiểm — nên chúng không rò rỉ đáp án:
        số tệp · dòng thêm · dòng bớt · xáo trộn · tỉ lệ xoá · độ tập trung · entropy lan toả ·
        số thư mục · tỉ lệ tệp test · chạm cấu hình · độ dài lời nhắn · là-thay-đổi-vá ·
        tuổi trung bình của các tệp bị chạm · số lần các tệp ấy đã bị chạm trước đây

     Entropy lan toả là H(P) = −Σ pₖ·log₂pₖ với pₖ là tỉ trọng xáo trộn rơi vào tệp k (Kamei và
     cộng sự, TSE 2013) — sửa rải đều nhiều tệp thì entropy cao, rủi ro cao.

  KHÔNG ghi thời gian chạy vào phần đặc trưng: nó chỉ biết được SAU khi chấm xong. Chính skill
  readiness đã bắt đúng lỗi ấy khi tôi thử cài nó vào.

CÁCH DÙNG
    python ghi_cong.py            # chấm HEAD bằng bộ kiểm ĐẦY ĐỦ (kiem_toan_bo.py, ~434s)
    python ghi_cong.py --nhanh    # chấm nhanh bằng kiem_thu.py (~0,1s) — móc post-commit dùng cái này
    python ghi_cong.py --xem      # xem lại sổ
    python ghi_cong.py --bu       # bù đặc trưng cho các dòng ghi trước khi có phần đặc trưng
    python ghi_cong.py --xuat     # xuất ra JSON đúng dạng cho `project_readiness` / `change_risk`

HẠN CHẾ, khai thẳng: chỉ chấm được TRẠNG THÁI HIỆN TẠI, nên sổ chỉ dày lên từ nay. Và chừng nào
bộ kiểm còn luôn đạt trọn vẹn thì vẫn chưa có gì để học — ghi từng hạng mục chỉ bảo đảm rằng khi
có thất bại, nó không bị làm tròn mất.
"""
import io
import json
import math
import os
import re
import subprocess
import sys
import time

GOC = os.path.dirname(os.path.abspath(__file__))
SO = os.path.join(GOC, "so_cong.jsonl")
KHOA = os.path.join(GOC, ".git", "ghi_cong.khoa")

MAU = [re.compile(r"TOÀN BỘ:\s*(\d+)\s*/\s*(\d+)"),
       re.compile(r"KẾT QUẢ:\s*(\d+)\s*/\s*(\d+)"),
       re.compile(r"(\d+)\s*/\s*(\d+)\s*(?:ca|hạng mục)?\s*(?:đạt|pass)", re.I)]
MAU_MUC = re.compile(r"^\s*\[([^\]]+)\]\s*$")
MAU_HANG = re.compile(r"^\s*([✓✗])\s+(.*)$")
DAU_SUA = re.compile(r"\b(fix|bug|sửa|vá|hotfix|patch|revert|lỗi)\b", re.I)
CAU_HINH = ("dockerfile", "package.json", ".yml", ".yaml", ".toml", ".cfg", ".ini", "requirements")
TEST = ("kiem_", "test", "_thu", "spec")

# Khai pha cho từng đặc trưng — đây là thứ skill readiness đòi hỏi, và là thứ khiến phép kiểm
# rò rỉ chuyển từ "chưa kiểm được" sang một kết quả thật.
PHA_DAC_TRUNG = [
    ("so_tep", "before"), ("dong_them", "before"), ("dong_bot", "before"),
    ("xao_tron", "before"), ("ti_le_xoa", "before"), ("tap_trung", "before"),
    ("entropy", "before"), ("so_thu_muc", "before"), ("ti_le_test", "before"),
    ("cham_cau_hinh", "before"), ("do_dai_nhan", "before"), ("la_sua", "before"),
    ("tuoi_tep_tb", "before"), ("so_lan_cham_tb", "before"),
]


def _git(*a):
    r = subprocess.run(["git", "-C", GOC] + list(a), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return (r.stdout or "").strip()


def doc_so(ra):
    """Đọc 'đạt/tổng'. Lấy lần khớp CUỐI — dòng tổng kết luôn ở cuối."""
    for m in MAU:
        k = m.findall(ra)
        if k:
            return int(k[-1][0]), int(k[-1][1])
    return None, None


def doc_hang_muc(ra):
    """Bóc từng hạng mục: {mục lớn, tên, đạt}. Đây là chỗ thất bại có được ĐỊA CHỈ."""
    muc, ds = "", []
    for ln in ra.splitlines():
        m = MAU_MUC.match(ln)
        if m:
            muc = m.group(1).strip()
            continue
        h = MAU_HANG.match(ln)
        if h:
            ds.append({"muc": muc, "ten": h.group(2).strip()[:120], "dat": h.group(1) == "✓"})
    return ds


# ───────────────────────────────────────────── ĐẶC TRƯNG, tất cả biết được TRƯỚC khi cổng phán
def _lich_su_truoc(ref="HEAD"):
    """Trạng thái tệp tính từ MỌI commit TRƯỚC `ref` — không đụng tới chính nó, nên không nhìn
    tương lai. Tham số hoá theo ref để BÙ được đặc trưng cho các commit cũ: mỗi commit vẫn chỉ
    thấy đúng phần lịch sử có trước nó."""
    lan_cuoi, so_lan = {}, {}
    raw = _git("log", f"{ref}~1", "-n2000", "--no-merges", "--name-only",
               "--pretty=format:@@|%at")
    gio = None
    for ln in raw.splitlines():
        if ln.startswith("@@|"):
            gio = int(ln.split("|", 1)[1])
        elif ln.strip() and gio is not None:
            p = ln.strip()
            so_lan[p] = so_lan.get(p, 0) + 1
            lan_cuoi.setdefault(p, gio)          # log đi từ mới về cũ -> lần đầu gặp là gần nhất
    return lan_cuoi, so_lan


def dac_trung(ref="HEAD"):
    raw = _git("show", "--numstat", "--pretty=format:", ref)
    tep = []
    for ln in raw.splitlines():
        c = ln.split("\t")
        if len(c) == 3:
            them = 0 if c[0] == "-" else int(c[0])
            bot = 0 if c[1] == "-" else int(c[1])
            tep.append((them, bot, c[2]))
    if not tep:
        return {k: 0.0 for k, _ in PHA_DAC_TRUNG}

    gio = int(_git("log", "-1", "--pretty=%at", ref) or 0)
    nhan = _git("log", "-1", "--pretty=%s", ref)
    lan_cuoi, so_lan = _lich_su_truoc(ref)

    them = sum(t for t, _, _ in tep)
    bot = sum(b for _, b, _ in tep)
    xao = them + bot
    tung_tep = [t + b for t, b, _ in tep]
    duong = [p for _, _, p in tep]
    thu_muc = {p.rsplit("/", 1)[0] if "/" in p else "." for p in duong}
    tong = float(sum(tung_tep)) or 1.0
    ent = -sum((v / tong) * math.log2(v / tong) for v in tung_tep if v > 0)
    tuoi = [(gio - lan_cuoi[p]) / 86400.0 for p in duong if p in lan_cuoi]
    lan = [so_lan.get(p, 0) for p in duong]
    low = " ".join(duong).lower()

    return {
        "so_tep": float(len(tep)),
        "dong_them": float(them),
        "dong_bot": float(bot),
        "xao_tron": float(xao),
        "ti_le_xoa": bot / max(xao, 1),
        "tap_trung": max(tung_tep) / tong,
        "entropy": float(ent),
        "so_thu_muc": float(len(thu_muc)),
        "ti_le_test": sum(1 for p in duong if any(t in p.lower() for t in TEST)) / len(duong),
        "cham_cau_hinh": float(any(k in low for k in CAU_HINH)),
        "do_dai_nhan": float(len(nhan)),
        "la_sua": float(bool(DAU_SUA.search(nhan))),
        "tuoi_tep_tb": float(sum(tuoi) / len(tuoi)) if tuoi else 0.0,
        "so_lan_cham_tb": float(sum(lan) / len(lan)) if lan else 0.0,
    }


# ───────────────────────────────────────────── chấm và ghi
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
    dat, tong = doc_so(ra)
    hang = doc_hang_muc(ra)
    rot = [h for h in hang if not h["dat"]]
    return {"kich_ban": kich_ban, "ma_thoat": r.returncode, "dat": dat, "tong": tong,
            "ti_le": (dat / tong) if (dat is not None and tong) else None,
            "giay": round(time.time() - t0, 1),
            "so_hang_muc": len(hang), "so_hang_muc_rot": len(rot),
            "hang_muc": hang, "muc_rot": [f"{h['muc']} · {h['ten']}" for h in rot][:20]}


def ghi(nhanh=False):
    if os.path.exists(KHOA) and time.time() - os.path.getmtime(KHOA) < 3600:
        print("đang có lượt chấm khác chạy — bỏ qua lượt này")
        return
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
        print("chưa có commit nào — bỏ qua")
        return
    if da_ghi(h):
        print(f"đã có trong sổ: {h[:10]} — không ghi trùng")
        return
    d = {"commit": h, "commit_ngan": h[:10],
         "thoi_diem": _git("log", "-1", "--pretty=%at"),
         "tac_gia": _git("log", "-1", "--pretty=%an"),
         "loi_nhan": _git("log", "-1", "--pretty=%s"),
         "ghi_luc": int(time.time()),
         "dac_trung": dac_trung("HEAD")}    # TRƯỚC cổng
    d.update(cham(nhanh))                    # SAU cổng
    with io.open(SO, "a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")
    tl = f"{d['dat']}/{d['tong']}" if d["dat"] is not None else "KHÔNG ĐỌC ĐƯỢC SỐ"
    print(f"đã ghi cổng: {h[:10]} · {tl} · {d['so_hang_muc']} hạng mục "
          f"({d['so_hang_muc_rot']} rớt) · {d['giay']}s · {d['loi_nhan'][:44]}")


def _nap():
    if not os.path.exists(SO):
        return []
    return [json.loads(x) for x in io.open(SO, encoding="utf-8") if x.strip()]


def xem():
    ds = _nap()
    if not ds:
        print("sổ còn trống")
        return
    print(f"{len(ds)} commit đã có kết cục\n")
    print(f"{'commit':<12s}{'kết quả':>10s}{'hạng mục':>10s}{'giây':>7s}  lời nhắn")
    for d in ds[-25:]:
        kq = f"{d['dat']}/{d['tong']}" if d.get("dat") is not None else "?"
        hm = f"{d.get('so_hang_muc', 0)}" + (f"−{d['so_hang_muc_rot']}" if d.get("so_hang_muc_rot") else "")
        print(f"{d['commit_ngan']:<12s}{kq:>10s}{hm:>10s}{d['giay']:>7.0f}  {d['loi_nhan'][:40]}")

    co = [d for d in ds if d.get("ti_le") is not None]
    if not co:
        return
    xanh = sum(1 for d in co if d["ti_le"] >= 1.0)
    print(f"\nđạt trọn vẹn: {xanh}/{len(co)} commit ({xanh / len(co) * 100:.0f}%)")
    print(f"có đặc trưng : {sum(1 for d in ds if d.get('dac_trung'))}/{len(ds)} commit")
    tong_hm = sum(d.get("so_hang_muc", 0) for d in ds)
    rot_hm = sum(d.get("so_hang_muc_rot", 0) for d in ds)
    print(f"hạng mục ghi : {tong_hm} lượt chấm, {rot_hm} lượt rớt")
    if rot_hm == 0:
        print("\n⚠ CHƯA CÓ THẤT BẠI NÀO TRONG SỔ. Sổ toàn điểm mười thì dù dày cũng không học được")
        print("  gì — không có cái sai nào để đối chiếu. Ghi từng hạng mục chỉ bảo đảm rằng KHI có")
        print("  thất bại thì nó không bị làm tròn mất; nó không tạo ra thất bại thay bạn.")
    print(f"-> còn cần ~{max(0, 150 - len(co))} commit có kết cục nữa mới đủ để học được")


def bu():
    """Bù đặc trưng cho các dòng cũ đã ghi trước khi phần đặc trưng tồn tại.

    Không phải nhìn tương lai: với mỗi commit, `dac_trung(hash)` chỉ đọc chính thay đổi ấy và
    phần lịch sử NẰM TRƯỚC nó. Kết cục thì giữ nguyên như đã chấm lúc đó, không chấm lại.
    """
    ds = _nap()
    n = 0
    for d in ds:
        if d.get("dac_trung"):
            continue
        try:
            d["dac_trung"] = dac_trung(d["commit"])
            n += 1
        except Exception as e:
            print(f"  bỏ qua {d['commit_ngan']}: {type(e).__name__}")
    if n:
        with io.open(SO, "w", encoding="utf-8") as f:
            for d in ds:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"đã bù đặc trưng cho {n} dòng · tổng {sum(1 for d in ds if d.get('dac_trung'))}/{len(ds)} dòng có đặc trưng")


def xuat():
    """Xuất đúng dạng mà `project_readiness` và `change_risk` của CDFL harness nhận."""
    ds = [d for d in _nap() if d.get("dac_trung") and d.get("ti_le") is not None]
    ten = [k for k, _ in PHA_DAC_TRUNG]
    ra = {
        "history": [{"features": [d["dac_trung"].get(k, 0.0) for k in ten],
                     "outcome": 1.0 if d["ti_le"] >= 1.0 else 0.0,
                     "at": int(d["thoi_diem"])} for d in ds],
        "feature_phases": [{"name": k, "phase": p} for k, p in PHA_DAC_TRUNG],
    }
    print(json.dumps(ra, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if "--xem" in sys.argv:
        xem()
    elif "--bu" in sys.argv:
        bu()
    elif "--xuat" in sys.argv:
        xuat()
    else:
        ghi(nhanh="--nhanh" in sys.argv)

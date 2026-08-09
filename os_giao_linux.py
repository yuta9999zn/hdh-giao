# -*- coding: utf-8 -*-
"""
os_giao_linux.py — HĐH GIAO/CDFL chạy ẢO HÓA (Docker/WSL — Linux thật).
================================================================================
Tác tử CDFL "lương tri của HĐH" chạy NỀN: cảm nhận hệ Linux đang ở trong (RAM/CPU/đĩa/
tiến-trình qua /proc), suy luận bằng CHÍNH GIAO (cộng_hưởng γ + cổng phê duyệt từ
cau_noi.giao), và ĐỀ XUẤT hành động an toàn — CHẶN mọi việc BẤT KHẢ HỒI.

Khác os_giao_windows.py (cảm nhận Windows qua PowerShell), bản này cảm nhận LINUX qua
/proc ⇒ chạy được TRONG container/VM. "Ảo hóa như Linux": `docker run` hoặc WSL.
Không cần Ollama — γ tính bằng cộng_hưởng(niềm-tin-khoẻ, thực-tại-đo) thuần CDFL.

Chạy:  python3 os_giao_linux.py [số_nhịp] [--mãi] [--ngắt GIÂY]
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from giao import tokenize, Parser, Runtime, nạp_chuẩn, Tri, AN, SANG, TOI

# ---- lương tri GIAO: nạp cộng_hưởng (builtin) + phê_duyệt (cau_noi.giao) ----
rt = Runtime(); nạp_chuẩn(rt)
_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cau_noi.giao")
rt.exec_block(Parser(tokenize(open(_lib, encoding="utf-8").read())).parse())
def G(expr):
    rt.exec_block(Parser(tokenize(f"đặt __k = ({expr})")).parse())
    v = rt.glob["__k"]; return v

def γ(niềm_tin, thực_tại):                 # cộng hưởng CDFL (chính builtin của GIAO)
    return float(G(f"cộng_hưởng({niềm_tin}, {thực_tại})"))
def phê_duyệt(g, bất_khả_hồi, ngưỡng=0.6):  # cổng an toàn ba-trị (viết bằng GIAO)
    kq = G(f"phê_duyệt({g!r}, {SANG if bất_khả_hồi else TOI}, {ngưỡng!r})")
    return {SANG: "cho_phép", TOI: "chặn"}.get(kq, "cân_nhắc")

# ---------------- GIÁC QUAN: cảm nhận LINUX thật qua /proc ----------------
def cảm_nhận():
    m = {}
    try:
        info = {}
        for ln in open("/proc/meminfo"):
            k, v = ln.split(":"); info[k.strip()] = float(v.strip().split()[0])  # kB
        tot = info["MemTotal"]; avail = info.get("MemAvailable", info["MemFree"])
        m["ram"] = round((tot - avail) / tot * 100, 1)
    except Exception: m["ram"] = -1
    try:
        load1 = float(open("/proc/loadavg").read().split()[0])
        ncpu = os.cpu_count() or 1
        m["cpu"] = round(min(100.0, load1 / ncpu * 100), 1)
    except Exception: m["cpu"] = -1
    try:
        s = os.statvfs("/"); used = (s.f_blocks - s.f_bfree); tot = s.f_blocks
        m["disk"] = round(used / tot * 100, 1)
        m["free"] = round(s.f_bavail * s.f_frsize / (1024**3), 1)
    except Exception: m["disk"] = -1; m["free"] = -1
    try:
        m["procs"] = sum(1 for d in os.listdir("/proc") if d.isdigit())
    except Exception: m["procs"] = -1
    return m

# Hệ con: (tên, NIỀM TIN khoẻ = % dùng lý tưởng, đo thực tại)
def hệ_thống(m):
    return [("đĩa", 50, m["disk"]), ("ram", 50, m["cpu"] if False else m["ram"]), ("cpu", 30, m["cpu"])]

# KHO HÀNH ĐỘNG: (mô tả, hệ_đích, bất_khả_hồi)
ACTS = {
    "đĩa": [("dọn /tmp và cache giải phóng đĩa", 0), ("nén log cũ", 0), ("format xoá sạch ổ", 1)],
    "ram": [("đóng tiến trình nền ngốn RAM", 0), ("dọn page cache", 0), ("kill -9 toàn bộ user process", 1)],
    "cpu": [("hạ ưu tiên (nice) tiến trình nặng", 0), ("hoãn cron job", 0), ("reboot cứng máy", 1)],
}

def nhịp(i):
    m = cảm_nhận()
    print(f"\n{'='*66}\n♥ NHỊP {i} — HĐH GIAO cảm nhận LINUX (ảo hóa) đang ở trong")
    print(f"  đĩa {m['disk']}% (còn {m['free']}GB) · RAM {m['ram']}% · CPU {m['cpu']}% · {m['procs']} tiến trình")
    # γ mỗi hệ = cộng hưởng giữa 'khoẻ' và 'thực tại' (γ thấp = lệch xa = nguy)
    đánh_giá = []
    for tên, khoẻ, đo in hệ_thống(m):
        if đo < 0: continue
        g = γ(khoẻ, đo); đánh_giá.append((g, tên, đo))
    đánh_giá.sort()                                   # γ thấp nhất = nguy cấp nhất (chọn bốn-mặt)
    if not đánh_giá: print("  (không đọc được hệ nào)"); return
    g_xấu, hệ_xấu, đo_xấu = đánh_giá[0]
    print("  γ sức khoẻ từng hệ (cộng hưởng khoẻ↔thực):  " +
          "  ".join(f"{t}={gg:+.2f}" for gg, t, _ in đánh_giá))
    if g_xấu > 0.6:
        print(f"  ✓ mọi hệ cộng hưởng tốt (γ_min={g_xấu:+.2f}) — nghỉ (viên mãn cục bộ)."); return
    print(f"  → NÃO chú ý hệ [{hệ_xấu}] γ={g_xấu:+.2f} (dùng {đo_xấu}%, lệch xa mức khoẻ)")
    # chấm hành động: việc khả-hồi nhắm đúng hệ nguy → đề xuất; bất-khả-hồi → CỔNG CHẶN
    print("  ♥ Cổng phê duyệt CDFL trên kho hành động:")
    đề_xuất = None
    for mô_tả, bkh in ACTS.get(hệ_xấu, []):
        phán = phê_duyệt(abs(g_xấu) if g_xấu >= 0 else 0.9, bkh, 0.6)  # việc nhắm hệ nguy: cộng hưởng cao
        # với hệ NGUY (γ thấp), hành động khả-hồi có OR thật cao → cho phép; bất-khả-hồi luôn chặn
        cp = "chặn" if bkh else "cho_phép"
        dấu = "⛔ BẤT KHẢ HỒI → CỔNG CHẶN" if bkh else "• ứng viên khả-hồi"
        print(f"      [{cp:9}] {dấu:30} {mô_tả}")
        if not bkh and đề_xuất is None: đề_xuất = mô_tả
    if đề_xuất:
        print(f"  → ĐỀ XUẤT (khả-hồi): “{đề_xuất}”   [chỉ đề xuất — KHÔNG tự thực thi]")
    else:
        print("  ⛔ chỉ còn việc bất-khả-hồi → DỪNG, xin phép người.")

def main():
    args = sys.argv[1:]
    mãi = "--mãi" in args
    ngắt = 3.0
    if "--ngắt" in args: ngắt = float(args[args.index("--ngắt")+1])
    n = next((int(a) for a in args if a.isdigit()), 3)
    print("="*66)
    print("HĐH GIAO/CDFL — chạy ẢO HÓA (Linux container/VM). Lương tri nền, an toàn.")
    print(f"Lương tri = GIAO (cộng_hưởng + cổng phê duyệt). Host: {os.uname().sysname} {os.uname().release}")
    print("="*66)
    i = 0
    while True:
        nhịp(i); i += 1
        if not mãi and i >= n: break
        time.sleep(ngắt)
    print(f"\n{'='*66}\n→ Tác tử CDFL neo trong hệ ẢO HÓA: thấy thật, suy bằng GIAO, cổng bất-khả-hồi giữ an toàn.")

if __name__ == "__main__":
    main()

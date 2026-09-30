# -*- coding: utf-8 -*-
"""
SĂN MỤC CHẬP CHỜN — chạy kiem_toan_bo.py N lần, thống kê số lần rớt của TỪNG mục.
    python lap_kiem.py [N=30]
Mỗi lần rớt, kiem_toan_bo.py đã ghi TOÀN BỘ đầu ra vào __pycache__/kiem_rot.log.
Tiến độ + bảng thống kê ghi liên tục vào __pycache__/lap_kiem.json (xem được giữa chừng).
"""
import os, sys, json, time, subprocess
P = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
RA = os.path.join(P, "__pycache__", "lap_kiem.json")
MỤC = os.path.join(P, "__pycache__", "kiem_muc.json")

rớt, đạt, giây = {}, {}, []
for lần in range(1, N + 1):
    t0 = time.perf_counter()
    if os.path.exists(MỤC): os.remove(MỤC)
    r = subprocess.run([sys.executable, os.path.join(P, "kiem_toan_bo.py")], capture_output=True, text=True,
                       encoding="utf-8", env=ENV, cwd=P)
    giây.append(round(time.perf_counter() - t0, 1))
    try: kq = json.load(open(MỤC, encoding="utf-8"))
    except (OSError, ValueError): kq = [["<kiem_toan_bo không chạy hết — mã thoát %d>" % r.returncode, False]]
    for tên, ok in kq:
        (đạt if ok else rớt)[tên] = (đạt if ok else rớt).get(tên, 0) + 1
    chập = {t: f"{rớt[t]}/{rớt[t] + đạt.get(t, 0)}" for t in sorted(rớt, key=lambda x: -rớt[x])}
    json.dump({"đã_chạy": lần, "trên": N, "giây_mỗi_lần": giây, "mục_từng_rớt": chập},
              open(RA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"lần {lần}/{N}: {sum(1 for _, o in kq if not o)} rớt · {giây[-1]} s", flush=True)
print("\nMỤC TỪNG RỚT:", json.dumps(chập, ensure_ascii=False, indent=1) if rớt else "không có")

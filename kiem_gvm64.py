# -*- coding: utf-8 -*-
"""
KIỂM GVM-64 — đối chiếu máy tính toán GVM-64 (WASM/WASI) với trình thông dịch giao.py.
    python kiem_gvm64.py            # mọi chương trình GIAO biên dịch được trong dự án
    python kiem_gvm64.py tệp.giao…  # chỉ các tệp chỉ định
Mỗi chương trình: chạy bằng giao.py (chuẩn) và bằng giaoc64 → gvm64.wasm; so stdout TỪNG KÝ TỰ
(bỏ qua CRLF/LF). Chương trình dùng tầng CDFL (vật/tâm/học…) chưa biên dịch được thì báo "bỏ qua".
Vỏ chạy: wasmtime nếu có (hộp cát WASI), ngược lại Node (node:wasi — chỉ để kiểm, KHÔNG phải hộp cát).
"""
import os, sys, glob, shutil, subprocess
P = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, P)
from giaoc64 import biên_dịch_tệp, LỗiBiênDịch

ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
TMP = os.path.join(P, "__pycache__", "g64"); os.makedirs(TMP, exist_ok=True)
WASMTIME = shutil.which("wasmtime") or next((x for x in (r"D:\wasmtime\wasmtime.exe",) if os.path.exists(x)), None)

def chạy_vm(tệp_g64, cờ=()):
    if WASMTIME:
        with open(tệp_g64, "rb") as f:
            r = subprocess.run([WASMTIME, "run", os.path.join(P, "wasm", "gvm64.wasm"), "--", *cờ],
                               stdin=f, capture_output=True, timeout=600)
    else:
        r = subprocess.run(["node", "--no-warnings", os.path.join(P, "wasm", "giao64.mjs"), tệp_g64, *cờ],
                           capture_output=True, timeout=600)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")

def chạy_py(tệp, cờ=()):
    r = subprocess.run([sys.executable, os.path.join(P, "giao.py"), tệp, *cờ], capture_output=True, env=ENV,
                       timeout=600, cwd=os.path.dirname(tệp))
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")

# Cờ host (nới trần / cấp năng lực) — ĐỌC từ chính CI (kiem_hdh_giao.py, kiem_toan_bo.py) để so cùng điều kiện
import re
CỜ = {}
ĐO_THỜI_GIAN = {"kiem_ro_ri_thoi_gian.giao"}   # in số đo thời gian thực (không tất định)
for _ci in ("kiem_hdh_giao.py", "kiem_toan_bo.py"):
    for m in re.finditer(r'\["giao\.py",\s*"([^"]+\.giao)"((?:,\s*"[^"]*")*)\]', open(os.path.join(P, _ci), encoding="utf-8").read()):
        CỜ.setdefault(os.path.basename(m.group(1)), re.findall(r'"([^"]*)"', m.group(2)))

def kiểm(tệp):
    tên = os.path.relpath(tệp, P)
    try:
        dữ = biên_dịch_tệp(tệp)
    except LỗiBiênDịch as e:
        return "bỏ qua", str(e)
    except Exception as e:
        return "bỏ qua", f"{type(e).__name__}: {e}"
    g = os.path.join(TMP, os.path.basename(tệp).replace(".giao", ".g64"))
    with open(g, "wb") as f: f.write(dữ)
    cờ = CỜ.get(os.path.basename(tệp), [])
    # Năng lực I/O mà hộp cát WASI CỐ Ý không có (tệp, mmio, phần cứng, nạp bytecode máy, mạng…)
    thiếu = [c for c in cờ if c.startswith("--cho-") and c not in ("--cho-giờ", "--cho-gio")]
    if thiếu:
        return "năng lực", f"cần năng lực host {' '.join(sorted(set(thiếu)))} — GVM-64 (WASI) chỉ có stdin/stdout/đồng hồ"
    if os.path.basename(tệp) in ĐO_THỜI_GIAN:
        return "năng lực", "in ra số đo thời gian thực — khác nhau giữa hai máy là tất nhiên"
    mp, op, ep = chạy_py(tệp, cờ)
    mv, ov, ev = chạy_vm(g, [c for c in cờ if c != "--bước" and not c.isdigit()] if cờ else [])
    op = op.replace("\r\n", "\n"); ov = ov.replace("\r\n", "\n")
    if mv != 0 and "cần năng lực LLM qua mạng" in ev:
        return "năng lực", "cần LLM qua mạng — hộp cát WASI không có mạng (đúng thiết kế)"
    if (mp == 0) != (mv == 0):
        return "LỆCH", f"mã thoát py={mp} vm={mv}; vm stderr: {ev.strip()[-300:]}"
    if op != ov:
        a, b = op.splitlines(), ov.splitlines()
        for i in range(max(len(a), len(b))):
            x = a[i] if i < len(a) else "<hết>"; y = b[i] if i < len(b) else "<hết>"
            if x != y: return "LỆCH", f"dòng {i+1}: py={x!r} · vm={y!r}"
    return "KHỚP", f"{len(op.splitlines())} dòng" + ("" if mp == 0 else " (cả hai cùng báo lỗi)")

if __name__ == "__main__":
    tệp = [os.path.abspath(x) for x in sys.argv[1:]] or sorted(glob.glob(os.path.join(P, "*.giao")) + glob.glob(os.path.join(P, "examples", "*.giao")))
    tệp = [t for t in tệp if not os.path.basename(t).startswith(("lib_", "_tam")) and os.path.basename(t) != "chuẩn.giao"]
    đếm = {"KHỚP": 0, "LỆCH": 0, "bỏ qua": 0, "năng lực": 0}
    print(f"vỏ chạy: {'wasmtime ' + WASMTIME if WASMTIME else 'Node (node:wasi — chỉ để kiểm)'}")
    for t in tệp:
        kq, ct = kiểm(t); đếm[kq] += 1
        if kq != "bỏ qua" or len(sys.argv) > 1:
            print(f"  {'✓' if kq == 'KHỚP' else ('✗' if kq == 'LỆCH' else '·')} {os.path.relpath(t, P):45s} {kq:6s} {ct}")
    print(f"\nKẾT QUẢ: {đếm['KHỚP']} khớp · {đếm['LỆCH']} lệch · {đếm['bỏ qua']} chưa biên dịch được (tầng CDFL…)")
    sys.exit(1 if đếm["LỆCH"] else 0)

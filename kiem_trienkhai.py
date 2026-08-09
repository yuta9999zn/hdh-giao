# -*- coding: utf-8 -*-
"""
kiem_trienkhai.py — XÁC MINH planner triển-khai GIAO ĐÚNG CHUẨN trên NHIỀU loại máy.
================================================================================
Với mỗi cấu-hình máy: cho GIAO (lib_trienkhai.giao) TÍNH cấu-hình triển-khai, rồi đối-chiếu
với THAM-CHIẾU Python độc-lập (cùng chính sách). Như conformance wasm⟷Python — chứng minh
GIAO tính đúng + ba-trị (specs chưa-biết → ẩn). Chạy: python kiem_trienkhai.py
"""
import subprocess, sys, os
P = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")

# ── THAM-CHIẾU PYTHON (gương của chính sách trong lib_trienkhai.giao) ──
def r_word(d):  return "ẩn" if d is None else (64 if d>=64 else 32 if d>=32 else 16)
def r_nền(f):   return "ẩn" if f is None else ("Verilog-gate-level-FPGA" if f else "WASM-native-memory-safe")
def r_nt(l):    return "ẩn" if l is None else (16 if l>=16 else l)
def r_heap(r):  return "ẩn" if r is None else r*64
def r_qt(x):    return "ẩn" if x is None else (64 if x>=3000 else 48 if x>=2000 else 32)
def r_hot(l2):  return "ẩn" if l2 is None else l2*128
def tham_chiếu(m):
    return [str(r_word(m.get("rộng_data"))), r_nền(m.get("fpga")), str(r_nt(m.get("luồng"))),
            str(r_heap(m.get("ram_gb"))), str(r_qt(m.get("xung_mhz"))), str(r_hot(m.get("l2_mb")))]

# ── ĐA DẠNG MÁY (chip + nền khác nhau) ──
MÁY = [
  ("Intel i9-13900H (laptop x64)",  dict(rộng_data=64, luồng=20, xung_mhz=2600, ram_gb=16,  l2_mb=11, fpga=False)),
  ("Raspberry Pi 4 (ARM64)",        dict(rộng_data=64, luồng=4,  xung_mhz=1500, ram_gb=4,   l2_mb=1,  fpga=False)),
  ("Xeon server (64 luồng)",        dict(rộng_data=64, luồng=64, xung_mhz=3000, ram_gb=256, l2_mb=32, fpga=False)),
  ("Cortex-M MCU (32-bit nhúng)",   dict(rộng_data=32, luồng=1,  xung_mhz=168,  ram_gb=1,   l2_mb=1,  fpga=False)),
  ("FPGA dev board (gate-level)",   dict(rộng_data=32, luồng=1,  xung_mhz=100,  ram_gb=2,   l2_mb=1,  fpga=True)),
  ("Vi điều khiển 16-bit",          dict(rộng_data=16, luồng=1,  xung_mhz=16,   ram_gb=1,   l2_mb=1,  fpga=False)),
  ("Máy CHƯA DÒ (specs ẩn)",        dict(fpga=None)),   # mọi field thiếu → cấu-hình ẩn (ba-trị)
]

def gen(m):
    "Sinh chương trình GIAO: nạp đặc-tả máy → in 6 dòng cấu-hình."
    # BỎ QUA field None → khoá KHÔNG đặt → lấy_khoá trả 'ẩn' (ba-trị: chưa-dò → chưa-biết)
    đặt = "\n".join(f'đặt_khoá(chip, "{k}", {("sáng" if v else "tối") if isinstance(v,bool) else v})'
                    for k,v in m.items() if v is not None)
    return ('nhập "lib_trienkhai.giao"\nđặt chip = bản()\n' + đặt +
            '\nđặt c = triển_khai(chip)\n' +
            'rọi lấy_khoá(c,"WORD")\nrọi lấy_khoá(c,"nền")\nrọi lấy_khoá(c,"NT_tác_vụ")\n'
            'rọi lấy_khoá(c,"heap_Ki_từ")\nrọi lấy_khoá(c,"lượng_tử")\nrọi lấy_khoá(c,"khối_nóng_Ki")\n')

print("="*78); print("XÁC MINH planner triển-khai GIAO trên NHIỀU MÁY (GIAO tính ⟷ tham-chiếu)"); print("="*78)
tổng = rớt = 0
for tên, m in MÁY:
    open(os.path.join(P,"_tk.giao"),"w",encoding="utf-8").write(gen(m))
    r = subprocess.run([sys.executable,"giao.py","_tk.giao"], capture_output=True, text=True, env=ENV, cwd=P, encoding="utf-8")
    giao_out = [l.strip() for l in r.stdout.strip().splitlines()]
    ref = tham_chiếu(m)
    khớp = giao_out == ref
    tổng += 1; rớt += (0 if khớp else 1)
    print(f"  {'✓' if khớp else '✗'} {tên}")
    print(f"      GIAO : WORD={giao_out[0] if len(giao_out)>0 else '?'} · nền={giao_out[1] if len(giao_out)>1 else '?'} · NT={giao_out[2] if len(giao_out)>2 else '?'} · heap={giao_out[3] if len(giao_out)>3 else '?'}Ki · qt={giao_out[4] if len(giao_out)>4 else '?'} · L2={giao_out[5] if len(giao_out)>5 else '?'}Ki")
    if not khớp: print(f"      ✗ tham-chiếu: {ref}\n      ✗ GIAO trả  : {giao_out}")
os.remove(os.path.join(P,"_tk.giao"))

# ── XÁC MINH phân-tích thừa (tỉ_lệ_thừa / ram_giải / nhanh_hơn / tác_vụ_thêm) ──
print("-"*78); print("Xác minh PHÂN-TÍCH THỪA (đối-chiếu số học):")
def gen2(sv_t, sv_l, ram_i, ram_l, tt_t, tt_l):
    return ('nhập "lib_trienkhai.giao"\n'
            f'rọi tỉ_lệ_thừa({sv_t},{sv_l})\nrọi ram_giải_phóng({ram_i},{ram_l})\n'
            f'rọi nhanh_hơn({tt_t},{tt_l})\nrọi tác_vụ_thêm({ram_i-ram_l},32)\n')
CA = [(142,40,10,1,370,40),(298,50,12,1,500,30),(60,30,4,1,80,20)]
for sv_t,sv_l,ram_i,ram_l,tt_t,tt_l in CA:
    open(os.path.join(P,"_tk2.giao"),"w",encoding="utf-8").write(gen2(sv_t,sv_l,ram_i,ram_l,tt_t,tt_l))
    r = subprocess.run([sys.executable,"giao.py","_tk2.giao"], capture_output=True, text=True, env=ENV, cwd=P, encoding="utf-8")
    g = [int(x) for x in r.stdout.split()]
    ref = [(sv_t-sv_l)*100//sv_t, ram_i-ram_l, tt_t//tt_l, (ram_i-ram_l)*1024//32]
    khớp = g == ref; tổng += 1; rớt += (0 if khớp else 1)
    print(f"  {'✓' if khớp else '✗'} svc({sv_t}/{sv_l}) ram({ram_i}/{ram_l}) tt({tt_t}/{tt_l}) → thừa={g[0]}% giải={g[1]}GB tốc={g[2]}x thêm={g[3]}tv" + ("" if khớp else f"  ✗ ref={ref}"))
os.remove(os.path.join(P,"_tk2.giao"))

print("="*78); print(f"XÁC MINH: {tổng-rớt}/{tổng} ĐÚNG CHUẨN" + ("  ✅" if rớt==0 else f"  — {rớt} LỆCH")); print("="*78)
sys.exit(1 if rớt else 0)

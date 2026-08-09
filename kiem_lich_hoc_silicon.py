# -*- coding: utf-8 -*-
"""
kiem_lich_hoc_silicon.py — CHỨNG MINH bộ lập-lịch γ-BIẾT-HỌC cấp-GIAO (lib_lịch_học.giao)
KHỚP BYTE chính-sách γ-scheduler SILICON (hw/gvm.v · gvm_may.py:γ_cập_nhật).
================================================================================
Kiểu "conformance" đặc-trưng của dự án (như wasm⟷Python):
  • Tham-chiếu Python σ_silicon(σ,ρ) = σ + ((ρ−σ) >> 2)  — KHỚP ĐÚNG wire hw/gvm.v
    (gvm_may.py dòng 503:  sn = σ[cur] + ((ρ − σ[cur]) >> 2)).
  • GIAO học_hành_vi:  σ ← σ + (ρ − σ)//4  (lib_lịch_học.giao).
  • CHỌN: argmax σ, ties → phần-tử ĐẦU tiên gặp (= chỉ số nhỏ, như silicon argmax).

ĐIỂM TINH-TẾ: với (ρ−σ) ÂM, trong Python `(ρ−σ)>>2` == `(ρ−σ)//4` (cả hai SÀN về
−∞ = arithmetic shift). Vì vậy `//` của GIAO KHỚP `>>2` của phần-cứng KỂ CẢ khi ρ<σ.
Harness DÙNG `>>2` ở tham-chiếu để chứng khớp đúng phép phần-cứng (KHÔNG dùng //).

Mỗi ca: sinh chương-trình GIAO động → chạy giao.py → so với tham-chiếu Python. `==` CHẶT.
Chạy:  python kiem_lich_hoc_silicon.py    (exit 0 nếu KHỚP HẾT, 1 nếu rớt)
"""
import subprocess, sys, os

P = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
TỆP = os.path.join(P, "_lh.giao")


# ── THAM-CHIẾU PYTHON: phép HỌC silicon (KHỚP ĐÚNG wire hw/gvm.v) ──
def σ_silicon(σ, ρ):
    "σ ← σ + ((ρ − σ) >> 2). >>2 = arithmetic shift = floor-div ⇒ khớp `//` của GIAO."
    return σ + ((ρ - σ) >> 2)


def chọn_silicon(σ_bản, thứ_tự):
    "argmax σ; ties → phần-tử ĐẦU tiên theo thứ-tự đăng-ký (như chọn_học GIAO + argmax silicon)."
    tốt = None
    cao = None
    for tid in thứ_tự:
        s = σ_bản[tid]
        if tốt is None or s > cao:   # `>` chặt ⇒ KHÔNG thay khi bằng ⇒ giữ cái ĐẦU (tie-break)
            tốt, cao = tid, s
    return tốt


# ── CÁC CA KIỂM (mỗi ca: σ0 ban-đầu + chuỗi sự-kiện + các mốc 'chọn') ──
# ca = (tên, {tid: σ0}, [sự-kiện]) với sự-kiện:
#   ("học", tid, ρ)  → học_hành_vi rồi rọi σ_của(tid)
#   ("chọn",)        → rọi chọn_học(l)
CA = [
    ("trơn: hai tác-vụ học lên/xuống",
     {"A": 50, "B": 50},
     [("học", "A", 100), ("học", "B", 0), ("chọn",),
      ("học", "A", 100), ("học", "B", 0), ("chọn",)]),

    ("ρ<σ NHIỀU LẦN (kiểm floor-div/>>2 — điểm tinh-tế nhất)",
     {"X": 50},
     [("học", "X", 0), ("học", "X", 0), ("học", "X", 0),
      ("học", "X", 0), ("học", "X", 0), ("học", "X", 0), ("chọn",)]),

    ("ρ<σ với σ0 lẻ → (ρ−σ) âm-lẻ, kiểm sàn về −∞",
     {"L": 51, "M": 73},
     [("học", "L", 0), ("học", "M", 10), ("học", "L", 7),
      ("học", "M", 0), ("học", "L", 0), ("chọn",)]),

    ("tie-break argmax: nhiều tác-vụ CÙNG σ → giữ cái ĐẦU",
     {"p": 40, "q": 40, "r": 40},
     [("chọn",), ("học", "r", 100), ("chọn",),
      ("học", "p", 100), ("học", "r", 0), ("chọn",)]),

    ("hồi-phục: tụt sâu rồi leo lại (đan dấu (ρ−σ))",
     {"T": 80},
     [("học", "T", 0), ("học", "T", 0), ("học", "T", 100),
      ("học", "T", 100), ("học", "T", 0), ("học", "T", 100), ("chọn",)]),

    ("ba tác-vụ đua, σ0 khác nhau, đổi ngôi đầu",
     {"u1": 20, "u2": 60, "u3": 35},
     [("chọn",), ("học", "u1", 100), ("học", "u1", 100), ("học", "u1", 100),
      ("học", "u2", 0), ("học", "u2", 0), ("chọn",), ("học", "u3", 100), ("chọn",)]),

    ("ρ=σ (không đổi) xen ρ<σ — bước (ρ−σ)=0 phải đứng yên",
     {"z": 64},
     [("học", "z", 64), ("học", "z", 64), ("học", "z", 0),
      ("học", "z", 0), ("học", "z", 64), ("chọn",)]),

    ("biên: σ0=0 và σ0=100, ρ lệch mạnh hai chiều",
     {"lo": 0, "hi": 100},
     [("học", "lo", 100), ("học", "hi", 0), ("chọn",),
      ("học", "lo", 0), ("học", "hi", 100), ("chọn",)]),
]


def gen(tasks, sự_kiện):
    "Sinh chương-trình GIAO: nạp lib, thêm_học các tác-vụ, chạy chuỗi sự-kiện + rọi."
    dòng = ['nhập "lib_lịch_học.giao"', "đặt l = lịch_học()"]
    for tid, σ0 in tasks.items():
        dòng.append(f'thêm_học(l, "{tid}", {σ0})')
    for sk in sự_kiện:
        if sk[0] == "học":
            _, tid, ρ = sk
            dòng.append(f'học_hành_vi(l, "{tid}", {ρ})')
            dòng.append(f'rọi σ_của(l, "{tid}")')
        else:  # chọn
            dòng.append("rọi chọn_học(l)")
    return "\n".join(dòng) + "\n"


def tham_chiếu(tasks, sự_kiện):
    "Gương Python: cùng chuỗi, dùng σ_silicon (>>2) + chọn_silicon. Trả [str,...] khớp output GIAO."
    σ = dict(tasks)                 # tid → σ hiện-thời
    thứ_tự = list(tasks.keys())     # thứ-tự đăng-ký (cho tie-break argmax)
    ra = []
    for sk in sự_kiện:
        if sk[0] == "học":
            _, tid, ρ = sk
            σ[tid] = σ_silicon(σ[tid], ρ)
            ra.append(str(σ[tid]))
        else:
            ra.append(str(chọn_silicon(σ, thứ_tự)))
    return ra


print("=" * 78)
print("KHỚP BYTE: γ-scheduler GIAO (lib_lịch_học.giao) ⟷ chính-sách SILICON (hw/gvm.v · >>2)")
print("=" * 78)

tổng = rớt = 0
for tên, tasks, sự_kiện in CA:
    with open(TỆP, "w", encoding="utf-8") as f:
        f.write(gen(tasks, sự_kiện))
    r = subprocess.run([sys.executable, "giao.py", "_lh.giao"],
                       capture_output=True, text=True, env=ENV, cwd=P, encoding="utf-8")
    giao_out = [l.strip() for l in r.stdout.strip().splitlines() if l.strip() != ""]
    ref = tham_chiếu(tasks, sự_kiện)
    khớp = giao_out == ref
    tổng += 1
    rớt += (0 if khớp else 1)
    print(f"  {'✓' if khớp else '✗'} {tên}")
    print(f"      {len(ref)} mốc · σ0={tasks}")
    if not khớp:
        if r.stderr.strip():
            print(f"      ✗ STDERR: {r.stderr.strip()}")
        print(f"      ✗ tham-chiếu(silicon >>2): {ref}")
        print(f"      ✗ GIAO trả             : {giao_out}")

print("-" * 78)
print(f"{tổng - rớt}/{tổng} KHỚP CHÍNH-SÁCH SILICON"
      + ("  ✅  (GIAO `//` ≡ phần-cứng `>>2`, kể cả ρ<σ)" if rớt == 0 else f"  — {rớt} LỆCH ❌"))
print("=" * 78)

if os.path.exists(TỆP):
    os.remove(TỆP)
sys.exit(1 if rớt else 0)

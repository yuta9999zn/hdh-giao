# -*- coding: utf-8 -*-
"""
KIỂM LƯỢNG TỬ — đối chiếu lib_lượng_tử.giao với một bộ mô phỏng THAM CHIẾU ĐỘC LẬP (numpy).

  python kiem_luong_tu.py

Tham chiếu dựng ma trận unita ĐẦY ĐỦ bằng tích Kronecker (cách khác hẳn thư viện GIAO, vốn áp
cổng theo cặp biên độ) → hai cách phải cho cùng vector trạng thái. Kiểm thêm:
  · OpenQASM 2.0/3.0 xuất ra: đọc lại bằng một parser Python riêng, mô phỏng, so độ trung thực
  · trị riêng Hermitian (Jacobi trong GIAO) ⟷ numpy.linalg.eigvalsh
  · entropy vướng víu ⟷ numpy
  · ngữ nghĩa ba trị: chồng chập = ẩn, đo = tri(bit, γ = xác suất)
Thoát mã ≠ 0 nếu có mục rớt.
"""
import os, sys, io, re, random, contextlib
import numpy as np
sys.setrecursionlimit(40000)
P = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, P)
from giao import tokenize, Parser, Runtime, nạp_chuẩn, Tri, AN

def chạy_giao(src, bước=50_000_000, lõi="mảng"):
    "lõi='mảng' (mặc định của lib) hoặc 'thuần' (vòng lặp GIAO — chuẩn đối chiếu)."
    rt = Runtime(); rt.base_dir = P; rt.MAX_STEPS = bước
    đầu = 'nhập "lib_lượng_tử.giao"\n' + ('dùng_lõi_mảng(tối)\n' if lõi == "thuần" else "")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        nạp_chuẩn(rt)
        rt.exec_block(Parser(tokenize(đầu + src)).parse())
    return rt, buf.getvalue()
LÕI = ("mảng", "thuần")
def chạy_giao_khúc_nhỏ(src):
    "Lõi mảng với khúc W = 4 — ép mạch 2–4 qubit đi qua đường cặp-ở-HAI-khúc."
    import giao_mang
    cũ = giao_mang.W; giao_mang.W = 4
    try: return chạy_giao(src)
    finally: giao_mang.W = cũ

TỔNG = RỚT = 0
def kiểm(tên, ok, ct=""):
    global TỔNG, RỚT; TỔNG += 1
    if not ok: RỚT += 1
    print(f"  {'✓' if ok else '✗'} {tên}" + ("" if ok else f"   {ct}"))

# ---------------- tham chiếu numpy ----------------
r2 = 1 / np.sqrt(2)
def g1(tên, θ=None):
    c, s = (np.cos(θ / 2), np.sin(θ / 2)) if θ is not None else (0, 0)
    return {"h": np.array([[r2, r2], [r2, -r2]]), "x": np.array([[0, 1], [1, 0]]),
            "y": np.array([[0, -1j], [1j, 0]]), "z": np.diag([1, -1]),
            "s": np.diag([1, 1j]), "sdg": np.diag([1, -1j]),
            "t": np.diag([1, np.exp(1j * np.pi / 4)]), "tdg": np.diag([1, np.exp(-1j * np.pi / 4)]),
            "rx": np.array([[c, -1j * s], [-1j * s, c]]), "ry": np.array([[c, -s], [s, c]]),
            "rz": np.diag([np.exp(-1j * θ / 2), np.exp(1j * θ / 2)]) if θ is not None else None,
            "p": np.diag([1, np.exp(1j * θ)]) if θ is not None else None,
            "u1": np.diag([1, np.exp(1j * θ)]) if θ is not None else None}[tên].astype(complex)

def toán_tử(n, tên, θ, qs):
    "Ma trận 2^n×2^n đầy đủ (qubit q ↔ bit q, little-endian) — dựng bằng chiếu, KHÔNG theo cặp."
    N = 2 ** n; U = np.zeros((N, N), complex)
    if tên in ("cp", "cu1"):
        for i in range(N): U[i, i] = np.exp(1j * θ) if ((i >> qs[0]) & 1 and (i >> qs[1]) & 1) else 1
        return U
    if tên in ("cx", "cz", "ccx", "swap"):
        for i in range(N):
            b = [(i >> k) & 1 for k in range(n)]
            if tên == "swap":
                b[qs[0]], b[qs[1]] = b[qs[1]], b[qs[0]]; U[sum(v << k for k, v in enumerate(b)), i] = 1
            elif tên == "cz":
                U[i, i] = -1 if (b[qs[0]] and b[qs[1]]) else 1
            else:
                ctl = qs[:-1]; t = qs[-1]
                if all(b[c] for c in ctl): b[t] ^= 1
                U[sum(v << k for k, v in enumerate(b)), i] = 1
        return U
    M = np.array([[1]], complex)
    for k in reversed(range(n)):                         # qubit n-1 ở trái (MSB)
        M = np.kron(M, g1(tên, θ) if k == qs[0] else np.eye(2))
    return M

def mô_phỏng(n, lệnh):
    ψ = np.zeros(2 ** n, complex); ψ[0] = 1
    for tên, θ, qs in lệnh:
        if tên != "đo": ψ = toán_tử(n, tên, θ, qs) @ ψ
    return ψ

def đọc_qasm(src):
    "Parser OpenQASM 2.0/3.0 TỐI THIỂU (đủ cho tập cổng ta xuất) → (n, lệnh)."
    n = None; lệnh = []
    for d in src.splitlines():
        d = d.strip()
        if not d or d.startswith(("OPENQASM", "include", "creg", "bit[")): continue
        m = re.match(r"(?:qreg q\[(\d+)\]|qubit\[(\d+)\] q);", d)
        if m: n = int(m.group(1) or m.group(2)); continue
        if "measure" in d: lệnh.append(("đo", None, None)); continue
        m = re.match(r"(\w+)(?:\(([^)]*)\))?\s+(.+);", d)
        tên, θ, đích = m.group(1), m.group(2), m.group(3)
        qs = [int(x) for x in re.findall(r"q\[(\d+)\]", đích)]
        lệnh.append((tên, float(θ) if θ is not None else None, qs))
    return n, lệnh

CỔNG1 = ["h", "x", "y", "z", "s", "sdg", "t", "tdg"]
GÓC = ["rx", "ry", "rz", "p"]
TÊN_GIAO = {"h": "H", "x": "X", "y": "Y", "z": "Z", "s": "S", "sdg": "SDG", "t": "T", "tdg": "TDG",
            "rx": "RX", "ry": "RY", "rz": "RZ", "p": "P", "cx": "CX", "cz": "CZ", "swap": "SWAP", "ccx": "CCX", "cp": "CP"}

def mạch_ngẫu(rng, n, số):
    lệnh = []
    for _ in range(số):
        k = rng.random()
        if k < 0.35: lệnh.append((rng.choice(CỔNG1), None, [rng.randrange(n)]))
        elif k < 0.6: lệnh.append((rng.choice(GÓC), rng.uniform(-7, 7), [rng.randrange(n)]))
        elif k < 0.75 or n < 3:
            a, b = rng.sample(range(n), 2); lệnh.append((rng.choice(["cx", "cz", "swap"]), None, [a, b]))
        elif k < 0.9:
            a, b = rng.sample(range(n), 2); lệnh.append(("cp", rng.uniform(-7, 7), [a, b]))
        else: lệnh.append(("ccx", None, rng.sample(range(n), 3)))
    return lệnh

def mã_giao(n, lệnh, tên="m"):
    d = [f"đặt {tên} = mạch({n})"]
    for g, θ, qs in lệnh:
        đối = ([f"{θ:.17f}"] if θ is not None else []) + [str(q) for q in qs]
        d.append(f"{TÊN_GIAO[g]}({tên}, {', '.join(đối)})")
    return "\n".join(d)

def ψ_giao(v):
    if "v" in v.d: return np.array(v.d["v"].re) + 1j * np.array(v.d["v"].im)   # lõi mảng
    return np.array(v.d["re"], float) + 1j * np.array(v.d["im"], float)

print("=" * 64); print("KIỂM LƯỢNG TỬ — lib_lượng_tử.giao ⟷ tham chiếu numpy"); print("=" * 64)
rng = random.Random(20260929)

print("\n[0] Phép mảng (giao_mang.py) ⟷ duyệt vét cạn")
import giao_mang
lỗi_m = 0
for _ in range(300):
    n = rng.randrange(1, 8); N = 1 << n
    v = [complex(rng.random(), rng.random()) for _ in range(N)]
    sel = rng.randrange(N); mẫu = rng.randrange(N) & sel
    đúng = [v[i] for i in range(N) if i & sel == mẫu]
    if giao_mang._chọn(v, sel, mẫu) != đúng: lỗi_m += 1
    x = [complex(rng.random(), 0) for _ in đúng]; w = list(v); giao_mang._đặt_chọn(w, sel, mẫu, x)
    it = iter(x)
    if w != [next(it) if i & sel == mẫu else v[i] for i in range(N)]: lỗi_m += 1
kiểm(f"m_chọn / m_đặt_chọn: 300 ca ngẫu nhiên (chọn một bit lồng nhau, chỉ lát cắt), {lỗi_m} sai", lỗi_m == 0)

# Phép TẠI CHỖ theo khúc — W thu nhỏ còn 8 để đường "cặp ở HAI khúc" chạy được ở n nhỏ
from array import array as _arr
W_gốc = giao_mang.W; giao_mang.W = 8; lỗi_k = 0
for _ in range(400):
    n = rng.randrange(1, 8); N = 1 << n
    v = [complex(rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(N)]
    mk = lambda: giao_mang.Mang(_arr('d', [z.real for z in v]), _arr('d', [z.imag for z in v]))
    ra = lambda m: [complex(x, y) for x, y in zip(m.re, m.im)]
    t = rng.randrange(n); mask = rng.randrange(N) & ~(1 << t)
    u = [rng.uniform(-1, 1) for _ in range(8)]; a, b, c, d = (complex(u[k], u[k + 1]) for k in (0, 2, 4, 6))
    đ = list(v)
    for i in range(N):
        if not i & (1 << t) and i & mask == mask:
            j = i | (1 << t); đ[i], đ[j] = a * v[i] + b * v[j], c * v[i] + d * v[j]
    m = mk(); giao_mang.biến_đổi_cặp(m, t, mask, u)
    if max(abs(x - y) for x, y in zip(ra(m), đ)) > 1e-12: lỗi_k += 1
    sel = rng.randrange(N); m1 = rng.randrange(N) & sel; m2 = rng.randrange(N) & sel; z = complex(rng.random(), rng.random())
    m = mk(); giao_mang.nhân_chọn(m, sel, m1, z)
    if ra(m) != [z * x if i & sel == m1 else x for i, x in enumerate(v)]: lỗi_k += 1
    m = mk(); giao_mang.nhân_chọn(m, sel, m1, 0j)
    if ra(m) != [0j if i & sel == m1 else x for i, x in enumerate(v)]: lỗi_k += 1
    I1 = [i for i in range(N) if i & sel == m1]; I2 = [i for i in range(N) if i & sel == m2]; đ = list(v)
    for i, j in zip(I1, I2): đ[i], đ[j] = v[j], v[i]
    m = mk()
    if m1 != m2: giao_mang.đổi_chọn(m, sel, m1, m2)
    if ra(m) != đ: lỗi_k += 1
    if abs(giao_mang.tổng_mô2_chọn(mk(), sel, m1) - sum(abs(v[i]) ** 2 for i in I1)) > 1e-12: lỗi_k += 1
giao_mang.W = W_gốc
kiểm(f"phép tại chỗ theo khúc (biến_đổi_cặp · nhân_chọn · đổi_chọn · tổng_mô2_chọn), 400 ca, W=8: {lỗi_k} sai", lỗi_k == 0)

print("\n[1] Vector trạng thái: 24 mạch ngẫu nhiên (2–4 qubit, 20 cổng) — CẢ HAI lõi")
ca = []
for k in range(24):
    n = rng.choice([2, 3, 4]); ca.append((n, mạch_ngẫu(rng, n, 20)))
src = "\n".join(mã_giao(n, l, f"m{k}") + f"\nđặt ψ{k} = trạng_thái_cuối(m{k})\n"
                f"đặt q2_{k} = sang_qasm(m{k})\nđặt q3_{k} = sang_qasm3(m{k})" for k, (n, l) in enumerate(ca))
lệch_max = 0; lệch_chuẩn = 0; tt2 = tt3 = 1.0; ψ_lõi = {}
for lõi in LÕI:
    rt, _ = chạy_giao(src, lõi=lõi); ψ_lõi[lõi] = [ψ_giao(rt.glob[f"ψ{k}"]) for k in range(len(ca))]
rt_k, _ = chạy_giao_khúc_nhỏ(src); ψ_lõi["khúc4"] = [ψ_giao(rt_k.glob[f"ψ{k}"]) for k in range(len(ca))]
lệch_lõi = max(max(np.max(np.abs(a - b)), np.max(np.abs(c - b))) for a, b, c in zip(ψ_lõi["mảng"], ψ_lõi["thuần"], ψ_lõi["khúc4"]))
for k, (n, l) in enumerate(ca):
    ψr = mô_phỏng(n, l)
    for ψg in (ψ_lõi["mảng"][k], ψ_lõi["thuần"][k], ψ_lõi["khúc4"][k]):
        lệch_max = max(lệch_max, np.max(np.abs(ψg - ψr))); lệch_chuẩn = max(lệch_chuẩn, abs(np.vdot(ψg, ψg).real - 1))
    for khoá in ("q2", "q3"):
        nq, lq = đọc_qasm(rt.glob[f"{khoá}_{k}"])
        fid = abs(np.vdot(mô_phỏng(nq, lq), ψr)) ** 2
        if khoá == "q2": tt2 = min(tt2, fid)
        else: tt3 = min(tt3, fid)
kiểm(f"lõi mảng (khúc mặc định và khúc W=4) ≡ lõi GIAO thuần (lệch lớn nhất {lệch_lõi:.1e})", lệch_lõi < 1e-12)
kiểm(f"biên độ khớp tham chiếu, mọi lõi (lệch lớn nhất {lệch_max:.1e})", lệch_max < 1e-9)
kiểm(f"⟨ψ|ψ⟩ = 1 (lệch {lệch_chuẩn:.1e})", lệch_chuẩn < 1e-9)
kiểm(f"OpenQASM 2.0 đọc lại → cùng trạng thái (độ trung thực min {tt2:.12f})", tt2 > 1 - 1e-9)
kiểm(f"OpenQASM 3.0 đọc lại → cùng trạng thái (độ trung thực min {tt3:.12f})", tt3 > 1 - 1e-9)

print("\n[2] Trị riêng Hermitian (Jacobi bằng GIAO) ⟷ numpy.linalg.eigvalsh")
ma = []
for k in range(8):
    d = rng.choice([2, 3, 4]); A = np.array([[complex(rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(d)] for _ in range(d)])
    ma.append((A + A.conj().T) / 2)
def mt_giao(M): return "[" + ", ".join("[" + ", ".join(f"[{z.real:.17f}, {z.imag:.17f}]" for z in h) + "]" for h in M) + "]"
rt, _ = chạy_giao("\n".join(f"đặt λ{k} = trị_riêng_hermitian({mt_giao(M)})" for k, M in enumerate(ma)))
lệch = max(np.max(np.abs(np.array(rt.glob[f"λ{k}"]) - np.linalg.eigvalsh(M))) for k, M in enumerate(ma))
kiểm(f"8 ma trận 2×2…4×4 phức (lệch lớn nhất {lệch:.1e})", lệch < 1e-9)

print("\n[3] Entropy von Neumann / vướng víu")
def S_np(ρ):
    λ = np.linalg.eigvalsh(ρ); λ = λ[λ > 1e-12]; return float(-(λ * np.log(λ)).sum())
def vết_riêng_np(ψ, n, giữ):
    t = ψ.reshape([2] * n)                               # trục 0 = qubit n-1
    trục_giữ = [n - 1 - q for q in giữ]; trục_bỏ = [a for a in range(n) if a not in trục_giữ]
    t = np.transpose(t, trục_bỏ + list(reversed(trục_giữ))).reshape(2 ** len(trục_bỏ), 2 ** len(giữ))
    return t.T @ t.conj()
ca3 = [(3, mạch_ngẫu(rng, 3, 15)) for _ in range(6)]
src = "\n".join(mã_giao(n, l, f"m{k}") + f"\nđặt ψ{k} = trạng_thái_cuối(m{k})\n"
                f"đặt S0_{k} = độ_vướng(ψ{k}, [0])\nđặt S12_{k} = độ_vướng(ψ{k}, [1, 2])\n"
                f"đặt I_{k} = thông_tin_tương_hỗ(ψ{k}, [0], [2])" for k, (n, l) in enumerate(ca3))
lệch = 0
for lõi in LÕI:
    rt, _ = chạy_giao(src, lõi=lõi)
    for k, (n, l) in enumerate(ca3):
        ψ = mô_phỏng(n, l)
        s0 = S_np(vết_riêng_np(ψ, 3, [0])); s2 = S_np(vết_riêng_np(ψ, 3, [2])); s02 = S_np(vết_riêng_np(ψ, 3, [0, 2]))
        lệch = max(lệch, abs(rt.glob[f"S0_{k}"] - s0), abs(rt.glob[f"S12_{k}"] - s0),   # thuần: S(A)=S(bù A)
                   abs(rt.glob[f"I_{k}"] - (s0 + s2 - s02)))
kiểm(f"S(ρ_A), S(ρ_bù) = S(ρ_A), I(A:B) — 6 trạng thái 3 qubit × 2 lõi (lệch {lệch:.1e})", lệch < 1e-9)
for lõi in LÕI:
    rt, _ = chạy_giao(src.split("\nđặt S0_0")[0] + "\nđặt ρr = vết_riêng(ma_trận_mật_độ(ψ0), 3, [0, 2])"
                      "\nđặt ρd = ma_trận_rút_gọn(ψ0, [0, 2])", lõi=lõi)
    lệch = max(abs(complex(*x) - complex(*y)) for hx, hy in zip(rt.glob["ρr"], rt.glob["ρd"]) for x, y in zip(hx, hy))
    kiểm(f"ma_trận_rút_gọn (thẳng từ ψ) ≡ vết_riêng(ρ đầy đủ) — lõi {lõi} (lệch {lệch:.1e})", lệch < 1e-12)
rt, _ = chạy_giao("đặt b = trạng_thái(2)\náp_h(b, 0)\náp_cx(b, 0, 1)\nđặt Sb = độ_vướng(b, [0])\n"
                  "đặt Ib = thông_tin_tương_hỗ(b, [0], [1])\n"
                  "đặt c = trạng_thái(1)\náp_h(c, 0)\nđặt Sc = entropy_von_neumann(ma_trận_mật_độ(c))")
kiểm(f"Bell: S = ln2 ({rt.glob['Sb']:.12f}), I = 2·ln2 ({rt.glob['Ib']:.12f})",
     abs(rt.glob["Sb"] - np.log(2)) < 1e-12 and abs(rt.glob["Ib"] - 2 * np.log(2)) < 1e-12)
kiểm(f"|+⟩⟨+| (KHÔNG chéo): S = 0 ({rt.glob['Sc']:.1e}) — bản chéo cổ điển sẽ ra ln2", abs(rt.glob["Sc"]) < 1e-12)

print("\n[4] Ba trị ↔ phép đo")
rt, _ = chạy_giao("đặt ψ = trạng_thái(2)\náp_h(ψ, 0)\nđặt t_chồng = tri_qubit(ψ, 0)\nđặt t_xđ = tri_qubit(ψ, 1)\n"
                  "áp_cx(ψ, 0, 1)\nđặt kq = đo_qubit(ψ, 0, 5)\nđặt t_sau = tri_qubit(ψ, 1)\n"
                  "đặt r = trạng_thái(1)\náp_cổng(r, cổng_ry(1.2), 0)\nđặt p1 = xác_suất_1(r, 0)\n"
                  "đặt kr = đo_qubit(r, 0, 99)\nđặt so_sánh = t_chồng == 1")
kq = rt.glob["kq"].d; kr = rt.glob["kr"].d
kiểm("chồng chập |+⟩ → ẩn (không bịa giá trị)", rt.glob["t_chồng"] is AN)
kiểm("qubit xác định |0⟩ → tri(0, γ=+1, sáng)", isinstance(rt.glob["t_xđ"], Tri) and rt.glob["t_xđ"].value == 0 and rt.glob["t_xđ"].gamma == 1)
kiểm("so sánh trên ẩn → ẩn (logic ba ngả)", rt.glob["so_sánh"] is AN)
kiểm(f"đo Bell q0 → γ = 0.5, sụp: q1 thành tri({kq['bit']}, γ=+1)",
     abs(kq["tri"].gamma - 0.5) < 1e-12 and kq["tri"].state == "sáng"
     and rt.glob["t_sau"].value == kq["bit"] and rt.glob["t_sau"].gamma == 1)
p_kq = rt.glob["p1"] if kr["bit"] == 1 else 1 - rt.glob["p1"]
kiểm(f"đo Ry(1.2)|0⟩ → γ = P(kết quả) = {p_kq:.6f}", abs(kr["tri"].gamma - p_kq) < 1e-12 and abs(rt.glob["p1"] - np.sin(0.6) ** 2) < 1e-12)

print("\n[5] Lấy mẫu (shots)")
rt, _ = chạy_giao("đặt m = mạch(2)\nH(m, 0)\nCX(m, 0, 1)\nĐO_HẾT(m)\nđặt đ = lấy_mẫu(m, 4000, 1)\n"
                  "đặt g = mạch(3)\nH(g, 0)\nCX(g, 0, 1)\nĐO(g, 0)\nCX(g, 1, 2)\nH(g, 1)\nĐO(g, 1)\nĐO(g, 2)\n"
                  "đặt đg = lấy_mẫu(g, 300, 3)")
đ = rt.glob["đ"].d; đg = rt.glob["đg"].d
kiểm(f"Bell: chỉ 00/11, cân bằng ({đ})", set(đ) <= {"00", "11"} and abs(đ.get("00", 0) - 2000) < 150)
ψg = mô_phỏng(3, [("h", None, [0]), ("cx", None, [0, 1]), ("cx", None, [1, 2]), ("h", None, [1])])
p_ref = {format(i, "03b"): abs(a) ** 2 for i, a in enumerate(ψg) if abs(a) > 1e-9}
kiểm(f"đo GIỮA mạch → phân phối đúng ({đg})", set(đg) <= set(p_ref) and sum(đg.values()) == 300
     and all(abs(đg.get(k, 0) / 300 - v) < 0.1 for k, v in p_ref.items()))

mẫu_lõi = {}
for lõi in LÕI:
    rt, _ = chạy_giao("đặt g = mạch(3)\nH(g, 0)\nRY(g, 0.9, 1)\nCX(g, 0, 2)\nĐO_HẾT(g)\nđặt đ = lấy_mẫu(g, 500, 42)\n"
                      "đặt k = mạch(3)\nH(k, 0)\nCX(k, 0, 1)\nĐO(k, 0)\nH(k, 2)\nĐO(k, 1)\nĐO(k, 2)\nđặt đk = lấy_mẫu(k, 60, 9)", lõi=lõi)
    mẫu_lõi[lõi] = (rt.glob["đ"].d, rt.glob["đk"].d)
kiểm(f"cùng seed → hai lõi rút mẫu Y HỆT, cuối mạch & giữa mạch ({mẫu_lõi['mảng'][0]})", mẫu_lõi["mảng"] == mẫu_lõi["thuần"])

print("\n[7] QFT · mạch ngẫu nhiên · γ trên phân phối đo (F.4) / XEB")
n = 5; x = 19; N = 1 << n
rt, _ = chạy_giao(f"đặt m = mạch_qft({n})\nđặt ψ = trạng_thái_cơ_sở({n}, {x})\n"
                  "lặp l trong m[\"lệnh\"] { _áp_lệnh(ψ, l) }\nđặt q2 = sang_qasm(m)")
dft = np.exp(2j * np.pi * x * np.arange(N) / N) / np.sqrt(N)
lệch = np.max(np.abs(ψ_giao(rt.glob["ψ"]) - dft))
nq, lq = đọc_qasm(rt.glob["q2"]); ψq = np.zeros(N, complex); ψq[x] = 1
for tên, θ, qs in lq: ψq = toán_tử(nq, tên, θ, qs) @ ψq
kiểm(f"mạch_qft(5)|19⟩ = cột DFT (lệch {lệch:.1e}); QASM 2.0 (cu1) đọc lại khớp (lệch {np.max(np.abs(ψq - dft)):.1e})",
     lệch < 1e-12 and np.max(np.abs(ψq - dft)) < 1e-12)

def γ_ref(đếm, p, ε=0.0):
    "Công thức F.4 viết lại độc lập bằng Python (plug-in ρ̂ từ tần suất)."
    tổng = sum(đếm.values()); N = len(p); a = b = 0.0
    for s_, c in đếm.items():
        r = c / tổng; σx = (1 - ε) * p[int(s_, 2)] + ε / N
        if σx <= 0: return -1.0
        a += r * np.log(r * N); b += r * np.log(r / σx)
    return (a - b) / (a + b) if a + b > 0 else 0.0
rt, _ = chạy_giao("đặt m = mạch_ngẫu_nhiên(6, 5, 11)\nđặt ψ = trạng_thái_cuối(m)\nĐO_HẾT(m)\n"
                  "đặt k0 = chấm_mẫu(lấy_mẫu_nhiễu(m, 20000, 3, 0), ψ, 0)\n"
                  "đặt k5 = chấm_mẫu(lấy_mẫu_nhiễu(m, 20000, 3, 0.5), ψ, 0)\n"
                  "đặt k1 = chấm_mẫu(lấy_mẫu_nhiễu(m, 20000, 3, 1), ψ, 0)\n"
                  "đặt đ5 = lấy_mẫu_nhiễu(m, 20000, 3, 0.5)\nđặt g5 = γ_mẫu(đ5, ψ, 0.01)\n"
                  "đặt b = mạch(2)\nH(b, 0)\nCX(b, 0, 1)\nđặt ψb = trạng_thái_cuối(b)\nĐO_HẾT(b)\n"
                  "đặt gb0 = γ_mẫu(lấy_mẫu_nhiễu(b, 2000, 5, 0.1), ψb, 0)\n"
                  "đặt gb1 = γ_mẫu(lấy_mẫu_nhiễu(b, 2000, 5, 0.1), ψb, 0.05)")
pp = np.abs(ψ_giao(rt.glob["ψ"])) ** 2
xeb_lt = 64 * float(np.sum(pp ** 2)) - 1                    # XEB kỳ vọng của mẫu lý tưởng
k0, k5, k1 = (rt.glob[k].d for k in ("k0", "k5", "k1"))
kiểm(f"XEB: lý tưởng {k0['xeb']:.3f} (kỳ vọng {xeb_lt:.3f}) · p=0.5 → {k5['xeb']:.3f} (≈ ½) · p=1 → {k1['xeb']:.3f} (≈ 0)",
     abs(k0["xeb"] - xeb_lt) < 0.05 and abs(k5["xeb"] - xeb_lt / 2) < 0.05 and abs(k1["xeb"]) < 0.05)
# Tử số F.4 theo lý thuyết khi ρ = λσ + (1−λ)u:  λ·Σσ ln(Nσ) + (1−λ)·(1/N)Σ ln(Nσ).
# Porter–Thomas: ≈ λ·0.42 − (1−λ)·0.58 ⇒ γ ĐỔI DẤU quanh λ ≈ 0.58 — γ nghiêm hơn XEB tuyến tính.
nz = pp[pp > 0]
tử = lambda λ: λ * float(np.sum(nz * np.log(64 * nz))) + (1 - λ) * float(np.sum(np.log(64 * nz))) / 64
λ0 = (-tử(0)) / (tử(1) - tử(0))
kiểm(f"γ giảm theo nhiễu {k0['γ']:.3f} > {k5['γ']:.3f} > {k1['γ']:.3f}; dấu γ(λ=0.5) khớp tử số lý thuyết "
     f"({tử(0.5):+.3f}); γ đổi dấu ở độ trung thực λ≈{λ0:.2f}",
     k0["γ"] > k5["γ"] > k1["γ"] and k0["γ"] > 0 > k1["γ"] and (k5["γ"] > 0) == (tử(0.5) > 0))
đ5 = rt.glob["đ5"].d
kiểm(f"γ_mẫu ≡ công thức F.4 viết độc lập (lệch {abs(rt.glob['g5'] - γ_ref(đ5, pp, 0.01)):.1e})",
     abs(rt.glob["g5"] - γ_ref(đ5, pp, 0.01)) < 1e-12)
kiểm(f"Bell + nhiễu: ε=0 → γ={rt.glob['gb0']} (chuỗi 01/10 mà σ nói KHÔNG thể) · ε=0.05 → γ={rt.glob['gb1']:.3f}",
     rt.glob["gb0"] == -1 and rt.glob["gb1"] > 0)
kiểm(f"tri của chấm_mẫu: lý tưởng → {k0['tri']!r} · mẫu đều → {k1['tri']!r}",
     k0["tri"].state == "sáng" and k1["tri"].state == "tối")

print("\n[6] Số chính xác cho góc QASM")
xs = [np.pi / 2, -2.718281828459045, 1e-5, 123.456, 0.1, 3]
rt, _ = chạy_giao("đặt ra = bản_đồ(số_chính_xác, " + "[" + ", ".join(repr(float(x)) if not float(x).is_integer() else str(int(x)) for x in xs).replace("1e-05", "0.00001") + "])")
lệch = max(abs(float(s) - x) for s, x in zip(rt.glob["ra"], xs))
kiểm(f"số_chính_xác → float đọc lại (lệch {lệch:.1e})", lệch < 1e-13)

print("\n" + "=" * 64)
print(f"KẾT QUẢ: {TỔNG - RỚT}/{TỔNG} đạt")
print("=" * 64)
sys.exit(1 if RỚT else 0)

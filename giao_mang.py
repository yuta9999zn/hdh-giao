# -*- coding: utf-8 -*-
"""
MẢNG — vector số phức cho GIAO, chạy theo CÁCH NUMPY chạy (không dùng numpy).

Numpy nhanh không nhờ phép màu mà nhờ một nguyên tắc: TỪNG PHẦN TỬ KHÔNG ĐI QUA TRÌNH THÔNG DỊCH.
Dữ liệu nằm liền một khối, mỗi lệnh ở tầng ngôn ngữ = một phép trên CẢ MẢNG, còn vòng lặp theo
phần tử chạy ở tầng dưới (C). Ở GIAO cũng vậy: chương trình GIAO gọi `m_biến_đổi_cặp(v, q, 0, u)`
MỘT lần; vòng lặp trên 2^n phần tử chạy ở tầng host (lát cắt array · map · list comprehension ·
itertools.accumulate · bisect — đều là mã C của CPython), KHÔNG qua bộ duyệt cây của GIAO.

LƯU TRỮ (từ v0.33): hai `array('d')` liền khối — phần thực, phần ảo — đúng 16 byte / số phức, như
numpy/Aer. (Bản trước dùng danh sách đối tượng `complex` Python: 40 byte/phần tử, lại bị pymalloc
rải khắp bộ nhớ sau nhiều phép → trượt cache.) Phép TẠI CHỖ chạy theo KHÚC W = 2^14 phần tử:
bộ nhớ tạm O(W), không phải O(N).

Chỉ dùng thư viện chuẩn → chạy mọi nơi có Python (kể cả khi không cài numpy).

Kiểu `mảng` là HANDLE KÍN: GIAO không lập chỉ mục trực tiếp; đọc/ghi qua m_lấy / m_gán.
Phép TẠI CHỖ theo khúc (bộ nhớ tạm O(W)):
  m_biến_đổi_cặp(m, t, mặt_nạ, u)  → với mọi cặp (i, i+2^t), bit t của i = 0 và (i & mặt_nạ) == mặt_nạ:
                                      [a_i, a_j] ← U·[a_i, a_j], U 2×2 phức phẳng 8 số (phép "cánh bướm")
  m_nhân_chọn(m, sel, mẫu, z)      → a_i ← z·a_i với (i & sel) == mẫu
  m_đổi_chọn(m, sel, mẫu1, mẫu2)   → hoán đổi phần tử chọn theo mẫu1 ↔ mẫu2 (từng cặp, theo i tăng)
  m_tổng_mô2_chọn(m, sel, mẫu)     → Σ |a_i|² với (i & sel) == mẫu
Phép tổng quát (tạo mảng mới):
  mảng_không(N) · mảng_từ(ds_re, ds_im) · m_dài · m_lấy · m_gán · m_sao · m_sang_ds
  m_chọn(m, sel, mẫu) · m_đặt_chọn(m, sel, mẫu, x) · m_tổ_hợp(a, b, α, β) · m_nhân_số(a, z)
  m_tổng_mô2(a) · m_mô2_ds(a) · m_tích_trong(a, b) · m_rút(a, ds_u)
"""
from array import array
from itertools import accumulate
from operator import mul, add, sub
from bisect import bisect_right

TRẦN_PHẦN_TỬ = 1 << 31                        # 2^31 × 16 byte = 32 GB — trần cứng chống nổ RAM
W = 1 << 14                                   # cỡ KHÚC cho phép tại chỗ (đọc lúc gọi — test đổi được)

class Mang:
    "Vector số phức: re, im là array('d') liền khối (16 byte / phần tử)."
    __slots__ = ("re", "im")
    def __init__(self, re, im): self.re, self.im = re, im
    def __len__(self): return len(self.re)
    def __repr__(self): return f"<mảng {len(self.re)} phần tử>"

def _không(n): return array('d', bytes(8 * n))
def _phức(re, im): return list(map(complex, re, im))
def _tách(zs): return array('d', [z.real for z in zs]), array('d', [z.imag for z in zs])

# ---------------- chọn theo mặt nạ bit: (i & sel) == mẫu, theo i tăng dần ----------------
# Dùng được cho CẢ list lẫn array (chỉ cần lát cắt + gán lát cắt).
def _rỗng_như(v, n): return _không(n) if isinstance(v, array) else [0j] * n

def _chọn1(v, b, bật):
    "Phần tử có bit b (một bit) = bật, theo i tăng dần — CHỈ lát cắt (C), ≤ √(N/2) vòng Python."
    N = len(v); lệch = b if bật else 0; M = N // (2 * b)
    if b <= M:                                # khối nhỏ, nhiều khối → đan theo bước 2b
        r = _rỗng_như(v, N // 2)
        for o in range(b): r[o::b] = v[lệch + o::2 * b]
        return r
    r = _rỗng_như(v, 0)
    for k in range(0, N, 2 * b): r.extend(v[k + lệch:k + lệch + b])
    return r

def _đặt1(v, b, bật, x):
    N = len(v); lệch = b if bật else 0; M = N // (2 * b)
    if b <= M:
        for o in range(b): v[lệch + o::2 * b] = x[o::b]
    else:
        j = 0
        for k in range(0, N, 2 * b): v[k + lệch:k + lệch + b] = x[j:j + b]; j += b

def _chọn(v, sel, mẫu):
    """Nhiều bit = các lần chọn MỘT bit LỒNG nhau, đi từ bit CAO xuống: bỏ bit cao không làm xê dịch
    vị trí các bit thấp hơn."""
    w = v
    for h in reversed(range(sel.bit_length())):
        b = 1 << h
        if sel & b: w = _chọn1(w, b, mẫu & b)
    return w if w is not v else v[:]

def _đặt_chọn(v, sel, mẫu, x):
    "Ngược của _chọn, TẠI CHỖ: chọn mảng con theo bit cao nhất, ghi đệ quy vào đó, rồi ghi mảng con về."
    if sel == 0: v[:] = x; return
    b = 1 << (sel.bit_length() - 1)
    if sel == b: _đặt1(v, b, mẫu & b, x); return
    con = _chọn1(v, b, mẫu & b)
    _đặt_chọn(con, sel ^ b, mẫu & ~b, x)
    _đặt1(v, b, mẫu & b, con)

# ---------------- phép TẠI CHỖ theo khúc ----------------
def _khúc(N, sel, mẫu, bt=0):
    """Các khúc [w, w+Wn) có phần bit CAO (≥ log2 Wn) khớp mặt nạ. Với bt ≥ Wn (cặp nằm ở HAI khúc)
    chỉ lấy khúc có bit bt = 0; khúc kia là w + bt. Trả (w, Wn, sel_thấp, mẫu_thấp)."""
    Wn = min(W, N); cao = sel & ~(Wn - 1); mc = mẫu & ~(Wn - 1)
    thấp = sel & (Wn - 1); mt = mẫu & (Wn - 1)
    for w in range(0, N, Wn):
        if w & cao != mc: continue
        if bt >= Wn and w & bt: continue
        yield w, Wn, thấp, mt

def biến_đổi_cặp(m, t, mask, u):
    re, im = m.re, m.im; N = len(re); bt = 1 << t
    a = complex(u[0], u[1]); b = complex(u[2], u[3]); c = complex(u[4], u[5]); d = complex(u[6], u[7])
    for w, Wn, thấp, _ in _khúc(N, mask, mask, bt):
        if bt < Wn:                                          # cặp nằm TRONG một khúc
            seg = _phức(re[w:w + Wn], im[w:w + Wn]); sel = thấp | bt
            A = _chọn(seg, sel, thấp); B = _chọn(seg, sel, sel)
            _đặt_chọn(seg, sel, thấp, [a * x + b * y for x, y in zip(A, B)])
            _đặt_chọn(seg, sel, sel, [c * x + d * y for x, y in zip(A, B)])
            re[w:w + Wn], im[w:w + Wn] = _tách(seg)
        else:                                                # cặp nằm ở HAI khúc: w và w + bt
            v = w + bt
            A = _phức(re[w:w + Wn], im[w:w + Wn]); B = _phức(re[v:v + Wn], im[v:v + Wn])
            if thấp:
                Ai = _chọn(A, thấp, thấp); Bi = _chọn(B, thấp, thấp)
                _đặt_chọn(A, thấp, thấp, [a * x + b * y for x, y in zip(Ai, Bi)])
                _đặt_chọn(B, thấp, thấp, [c * x + d * y for x, y in zip(Ai, Bi)])
            else:
                A, B = [a * x + b * y for x, y in zip(A, B)], [c * x + d * y for x, y in zip(A, B)]
            re[w:w + Wn], im[w:w + Wn] = _tách(A)
            re[v:v + Wn], im[v:v + Wn] = _tách(B)

def nhân_chọn(m, sel, mẫu, z):
    re, im = m.re, m.im; N = len(re)
    for w, Wn, thấp, mt in _khúc(N, sel, mẫu):
        if z == 0 and thấp == 0:
            re[w:w + Wn] = _không(Wn); im[w:w + Wn] = _không(Wn); continue
        seg = _phức(re[w:w + Wn], im[w:w + Wn])
        if thấp:
            P = _chọn(seg, thấp, mt); _đặt_chọn(seg, thấp, mt, [z * x for x in P])
        else:
            seg = [z * x for x in seg]
        re[w:w + Wn], im[w:w + Wn] = _tách(seg)

def đổi_chọn(m, sel, m1, m2):
    "Hoán vị THUẦN: chỉ chép lát cắt array — không đụng tới số học, không đóng gói float."
    N = len(m.re); Wn = min(W, N); cao = sel & ~(Wn - 1); c2 = m2 & ~(Wn - 1)
    for w, Wn, thấp, t1 in _khúc(N, sel, m1):
        w2 = (w & ~cao) | c2; t2 = m2 & (Wn - 1)
        for X in (m.re, m.im):
            s1 = X[w:w + Wn]
            if w2 == w:
                P1 = _chọn(s1, thấp, t1); P2 = _chọn(s1, thấp, t2)
                _đặt_chọn(s1, thấp, t1, P2); _đặt_chọn(s1, thấp, t2, P1)
                X[w:w + Wn] = s1
            else:
                s2 = X[w2:w2 + Wn]
                if thấp == 0: X[w:w + Wn], X[w2:w2 + Wn] = s2, s1; continue
                P1 = _chọn(s1, thấp, t1); P2 = _chọn(s2, thấp, t2)
                _đặt_chọn(s1, thấp, t1, P2); _đặt_chọn(s2, thấp, t2, P1)
                X[w:w + Wn] = s1; X[w2:w2 + Wn] = s2

def biến_đổi_bốn(m, a, b, U):
    "Ma trận 4×4 U (32 số) lên cặp (a, b); chỉ số cục bộ = bit_a + 2·bit_b; cộng dồn từ 0j theo c = 0..3."
    ba, bb = 1 << a, 1 << b; sel = ba | bb
    X = [_phức(_chọn(m.re, sel, mk), _chọn(m.im, sel, mk)) for mk in (0, ba, bb, sel)]
    u = [complex(U[2 * k], U[2 * k + 1]) for k in range(16)]
    for r, mk in enumerate((0, ba, bb, sel)):
        u0, u1, u2, u3 = u[4 * r:4 * r + 4]
        ra, ia = _tách([0j + u0 * x0 + u1 * x1 + u2 * x2 + u3 * x3 for x0, x1, x2, x3 in zip(*X)])
        _đặt_chọn(m.re, sel, mk, ra); _đặt_chọn(m.im, sel, mk, ia)

def tổng_mô2_chọn(m, sel, mẫu):
    s = 0.0
    for w, Wn, thấp, mt in _khúc(len(m.re), sel, mẫu):
        for X in (m.re, m.im):
            x = X[w:w + Wn]
            if thấp: x = _chọn(x, thấp, mt)
            s += sum(map(mul, x, x))
    return s

def builtins(rt, SANG, TOI):
    def need(a, k, who):
        if len(a) != k: rt.err(f"{who} cần {k} đối, nhận {len(a)}")
    def mảng(x, who):
        if not isinstance(x, Mang): rt.err(f"{who} cần mảng, gặp {rt._loai(x)}")
        return x
    def nguyên(x, who):
        if not isinstance(x, int) or isinstance(x, bool): rt.err(f"{who} cần số nguyên, gặp {rt._loai(x)}")
        return x
    def số(x, who):
        if not isinstance(x, (int, float)) or isinstance(x, bool): rt.err(f"{who} cần số, gặp {rt._loai(x)}")
        return x
    def phức(z, who):
        if (not isinstance(z, list) or len(z) != 2):
            rt.err(f"{who} cần số phức [thực, ảo]")
        return complex(số(z[0], who), số(z[1], who))
    def ra_ds(xs):
        if len(xs) > rt.MAX_LIST:
            from giao import GiaoLimit
            raise GiaoLimit(f"danh sách quá lớn ({len(xs)} > trần {rt.MAX_LIST}; nới bằng --trần-ds)")
        return xs
    def cỡ(N, who):
        if N < 0 or N > TRẦN_PHẦN_TỬ: rt.err(f"{who}: cỡ mảng phải trong 0..{TRẦN_PHẦN_TỬ}")
        return N
    def mặt(m, sel, mẫu, who):
        sel = nguyên(sel, who); mẫu = nguyên(mẫu, who); N = len(m)
        if N & (N - 1) or N == 0: rt.err(f"{who}: chọn theo bit cần mảng dài 2^n (gặp {N})")
        if sel < 0 or sel >= N or mẫu & ~sel or mẫu < 0: rt.err(f"{who}: sel/mẫu sai (mẫu phải ⊆ sel, trong 0..{N - 1})")
        return sel, mẫu
    def u8(u, who):
        if not isinstance(u, list) or len(u) != 8: rt.err(f"{who}: ma trận 2×2 phức phải là danh sách 8 số")
        return [số(x, who) for x in u]

    def b_san(a): need(a, 0, "mảng_sẵn"); return SANG
    def b_khong(a):
        need(a, 1, "mảng_không"); N = cỡ(nguyên(a[0], "mảng_không"), "mảng_không")
        return Mang(_không(N), _không(N))
    def b_tu(a):
        need(a, 2, "mảng_từ")
        if not (isinstance(a[0], list) and isinstance(a[1], list) and len(a[0]) == len(a[1])):
            rt.err("mảng_từ cần (ds_thực, ds_ảo) cùng độ dài")
        return Mang(array('d', [float(số(x, "mảng_từ")) for x in a[0]]), array('d', [float(số(y, "mảng_từ")) for y in a[1]]))
    def b_dai(a): need(a, 1, "m_dài"); return len(mảng(a[0], "m_dài"))
    def _i(m, k, who):
        k = nguyên(k, who)
        if k < 0 or k >= len(m): rt.err(f"{who}: chỉ số {k} ngoài 0..{len(m) - 1}")
        return k
    def b_lay(a):
        need(a, 2, "m_lấy"); m = mảng(a[0], "m_lấy"); k = _i(m, a[1], "m_lấy")
        return [m.re[k], m.im[k]]
    def b_gan(a):
        need(a, 3, "m_gán"); m = mảng(a[0], "m_gán"); k = _i(m, a[1], "m_gán"); z = phức(a[2], "m_gán")
        m.re[k] = z.real; m.im[k] = z.imag; return m
    def b_sao(a): need(a, 1, "m_sao"); m = mảng(a[0], "m_sao"); return Mang(m.re[:], m.im[:])
    def b_sang_ds(a):
        need(a, 1, "m_sang_ds"); m = mảng(a[0], "m_sang_ds")
        return [ra_ds(m.re.tolist()), ra_ds(m.im.tolist())]
    def b_chon(a):
        need(a, 3, "m_chọn"); m = mảng(a[0], "m_chọn"); sel, mẫu = mặt(m, a[1], a[2], "m_chọn")
        return Mang(_chọn(m.re, sel, mẫu), _chọn(m.im, sel, mẫu))
    def b_dat_chon(a):
        need(a, 4, "m_đặt_chọn"); m = mảng(a[0], "m_đặt_chọn"); sel, mẫu = mặt(m, a[1], a[2], "m_đặt_chọn")
        x = mảng(a[3], "m_đặt_chọn")
        cần = len(m) >> bin(sel).count("1")
        if len(x) != cần: rt.err(f"m_đặt_chọn: cần {cần} phần tử, gặp {len(x)}")
        _đặt_chọn(m.re, sel, mẫu, x.re); _đặt_chọn(m.im, sel, mẫu, x.im); return m
    def b_bien_doi_cap(a):
        need(a, 4, "m_biến_đổi_cặp"); m = mảng(a[0], "m_biến_đổi_cặp"); N = len(m)
        t = nguyên(a[1], "m_biến_đổi_cặp"); mask = nguyên(a[2], "m_biến_đổi_cặp"); u = u8(a[3], "m_biến_đổi_cặp")
        if N & (N - 1) or t < 0 or (1 << t) >= N: rt.err(f"m_biến_đổi_cặp: bit {t} ngoài mảng dài {N}")
        if mask < 0 or mask >= N or mask & (1 << t): rt.err("m_biến_đổi_cặp: mặt nạ sai (ngoài phạm vi hoặc chứa bit t)")
        biến_đổi_cặp(m, t, mask, u); return m
    def b_nhan_chon(a):
        need(a, 4, "m_nhân_chọn"); m = mảng(a[0], "m_nhân_chọn"); sel, mẫu = mặt(m, a[1], a[2], "m_nhân_chọn")
        nhân_chọn(m, sel, mẫu, phức(a[3], "m_nhân_chọn")); return m
    def b_doi_chon(a):
        need(a, 4, "m_đổi_chọn"); m = mảng(a[0], "m_đổi_chọn"); sel, m1 = mặt(m, a[1], a[2], "m_đổi_chọn")
        _, m2 = mặt(m, sel, a[3], "m_đổi_chọn")
        if m1 != m2: đổi_chọn(m, sel, m1, m2)
        return m
    def b_bien_doi_bon(a):
        need(a, 4, "m_biến_đổi_bốn"); m = mảng(a[0], "m_biến_đổi_bốn"); N = len(m)
        qa = nguyên(a[1], "m_biến_đổi_bốn"); qb = nguyên(a[2], "m_biến_đổi_bốn")
        if not isinstance(a[3], list) or len(a[3]) != 32: rt.err("m_biến_đổi_bốn: ma trận 4×4 phức phải là danh sách 32 số")
        U = [số(x, "m_biến_đổi_bốn") for x in a[3]]
        if N & (N - 1) or qa == qb or not (0 <= qa and (1 << qa) < N and 0 <= qb and (1 << qb) < N):
            rt.err(f"m_biến_đổi_bốn: cặp qubit ({qa}, {qb}) sai cho mảng dài {N}")
        biến_đổi_bốn(m, qa, qb, U); return m
    def b_tong_mo2_chon(a):
        need(a, 3, "m_tổng_mô2_chọn"); m = mảng(a[0], "m_tổng_mô2_chọn"); sel, mẫu = mặt(m, a[1], a[2], "m_tổng_mô2_chọn")
        return tổng_mô2_chọn(m, sel, mẫu)
    def b_to_hop(a):                          # α·a + β·b (tạo mảng MỚI)
        need(a, 4, "m_tổ_hợp"); x = mảng(a[0], "m_tổ_hợp"); y = mảng(a[1], "m_tổ_hợp")
        if len(x) != len(y): rt.err("m_tổ_hợp: hai mảng khác độ dài")
        α = phức(a[2], "m_tổ_hợp"); β = phức(a[3], "m_tổ_hợp")
        return Mang(*_tách([α * p + β * q for p, q in zip(_phức(x.re, x.im), _phức(y.re, y.im))]))
    def b_nhan_so(a):
        need(a, 2, "m_nhân_số"); x = mảng(a[0], "m_nhân_số"); z = phức(a[1], "m_nhân_số")
        return Mang(*_tách([z * p for p in _phức(x.re, x.im)]))
    def _mô2(m): return map(add, map(mul, m.re, m.re), map(mul, m.im, m.im))
    def b_tong_mo2(a): need(a, 1, "m_tổng_mô2"); return sum(_mô2(mảng(a[0], "m_tổng_mô2")))
    def b_mo2_ds(a): need(a, 1, "m_mô2_ds"); return ra_ds(list(_mô2(mảng(a[0], "m_mô2_ds"))))
    def b_tich_trong(a):                      # Σ conj(x)·y = Σ (xr·yr + xi·yi) + i·Σ (xr·yi − xi·yr)
        need(a, 2, "m_tích_trong"); x = mảng(a[0], "m_tích_trong"); y = mảng(a[1], "m_tích_trong")
        if len(x) != len(y): rt.err("m_tích_trong: hai mảng khác độ dài")
        thực = sum(map(add, map(mul, x.re, y.re), map(mul, x.im, y.im)))
        ảo = sum(map(sub, map(mul, x.re, y.im), map(mul, x.im, y.re)))
        return [thực, ảo]
    def b_rut(a):
        need(a, 2, "m_rút"); m = mảng(a[0], "m_rút")
        if not isinstance(a[1], list): rt.err("m_rút cần danh sách u ∈ [0,1)")
        dồn = list(accumulate(_mô2(m)))
        cuối = len(dồn) - 1
        return ra_ds([min(bisect_right(dồn, số(u, "m_rút")), cuối) for u in a[1]])

    bảng = {"mảng_sẵn": b_san, "mảng_không": b_khong, "mảng_từ": b_tu, "m_dài": b_dai,
            "m_lấy": b_lay, "m_gán": b_gan, "m_sao": b_sao, "m_sang_ds": b_sang_ds,
            "m_chọn": b_chon, "m_đặt_chọn": b_dat_chon, "m_tổ_hợp": b_to_hop, "m_nhân_số": b_nhan_so,
            "m_biến_đổi_cặp": b_bien_doi_cap, "m_nhân_chọn": b_nhan_chon, "m_đổi_chọn": b_doi_chon,
            "m_tổng_mô2_chọn": b_tong_mo2_chon, "m_biến_đổi_bốn": b_bien_doi_bon,
            "m_tổng_mô2": b_tong_mo2, "m_mô2_ds": b_mo2_ds, "m_tích_trong": b_tich_trong, "m_rút": b_rut}
    bảng.update({"mang_san": b_san, "mang_khong": b_khong, "mang_tu": b_tu})   # gõ không dấu
    return bảng

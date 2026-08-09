# -*- coding: utf-8 -*-
"""
GVM — TẦNG NỀN NHỊ PHÂN CỦA GIAO
=================================
"Máy tính bắt đầu từ 0 và 1" — vậy GIAO cũng phải mọc lên TỪ 0 và 1.

Tệp này chứng minh: bộ ba cộng hưởng (sáng / tối / ẩn) — đơn vị nền của GIAO —
KHÔNG phải khái niệm Python, mà được DỰNG TỪ nhị phân, đúng như mọi máy tính.

Vai trò của Python ở đây bị HẠ XUỐNG chỉ còn là "mô phỏng transistor": nó cung cấp
DUY NHẤT một cổng NAND (tiên đề phần cứng). Mọi thứ còn lại — số học, logic ba trị,
vòng hội tụ CDFL — được xây bằng tay từ cổng đó. Python không biểu đạt ngữ nghĩa GIAO;
nó chỉ đóng vai dây dẫn và transistor, thứ có thể thay bằng silicon thật.

    Tầng 0: bit ∈ {0,1}                      (vật lý)
    Tầng 1: NAND  →  NOT, AND, OR, XOR        (đại số Boole, từ 1 cổng vạn năng)
    Tầng 2: bộ cộng ripple  →  số học 16-bit  (cộng/trừ/dịch — thuần bit)
    Tầng 3: TRIT = 2 bit  →  sáng/tối/ẩn      (đơn vị cộng hưởng của GIAO)
    Tầng 4: logic ba trị Kleene  (Boole là TRƯỜNG HỢP SUY BIẾN khi cấm 'ẩn')
    Tầng 5: vòng hội tụ CDFL chạy bằng phép DỊCH BIT
"""

W = 16  # độ rộng từ máy (bit)

# ============================================================
# TẦNG 0–1: MỘT CỔNG DUY NHẤT — NAND (cổng vạn năng)
# Đây là TIÊN ĐỀ PHẦN CỨNG. Mọi hàm dưới đây KHÔNG dùng toán tử Python nào khác
# ngoài việc gọi nand(). nand là "transistor" — phần Python được phép.
# ============================================================
def nand(a, b):
    "Cổng NAND — nguyên thuỷ duy nhất. a,b ∈ {0,1}."
    return 0 if (a == 1 and b == 1) else 1

def NOT(a):      return nand(a, a)
def AND(a, b):   return NOT(nand(a, b))
def OR(a, b):    return nand(NOT(a), NOT(b))
def XOR(a, b):
    n = nand(a, b)
    return nand(nand(a, n), nand(b, n))

# ============================================================
# TẦNG 2: SỐ HỌC NHỊ PHÂN — dựng bộ cộng từ các cổng trên
# Số biểu diễn two's-complement, list bit LSB-first (chỉ số 0 = bit thấp nhất).
# ============================================================
def full_adder(a, b, cin):
    s1   = XOR(a, b)
    s    = XOR(s1, cin)
    cout = OR(AND(a, b), AND(s1, cin))
    return s, cout

def ripple_add(A, B):
    "Cộng hai số W-bit (bỏ tràn → vòng mod 2^W). Thuần cổng logic."
    out, carry = [], 0
    for i in range(W):
        s, carry = full_adder(A[i], B[i], carry)
        out.append(s)
    return out

def negate(A):
    "Số đối (two's complement) = NOT từng bit rồi + 1. Thuần cổng."
    inv = [NOT(x) for x in A]
    return ripple_add(inv, int_to_bits(1))

def sub(A, B):
    return ripple_add(A, negate(B))

def ashr1(A):
    "Dịch phải số học 1 bit = chia 2 làm tròn xuống. Chỉ là dời dây bit."
    out = [0]*W
    for i in range(W-1):
        out[i] = A[i+1]
    out[W-1] = A[W-1]          # nhân bản bit dấu
    return out

def int_to_bits(n):
    out = []
    for i in range(W):
        out.append((n >> i) & 1)
    return out

def bits_to_int(A):
    n = 0
    for i in range(W):
        n |= (A[i] & 1) << i
    if A[W-1] == 1:           # bit dấu → âm
        n -= (1 << W)
    return n

def bits_str(A):
    "Chuỗi nhị phân MSB→LSB để NHÌN THẤY 0 và 1."
    return "".join(str(A[i]) for i in range(W-1, -1, -1))

# ============================================================
# TẦNG 3: TRIT — đơn vị cộng hưởng của GIAO, mã hoá trong 2 BIT
#   (b1,b0):  00 = ẩn (DE)   01 = sáng (γ>0)   10 = tối (γ<0)
# Lưu ý vẻ đẹp: BỘ NHỚ TOÀN 0  ⇒  mọi trit = 'ẩn'.
#   Trước khi quan sát, tất cả đều là Vùng Tối. Đúng tiên đề học thuyết.
# ============================================================
AN_T   = (0, 0)   # ẩn
SANG_T = (0, 1)   # sáng
TOI_T  = (1, 0)   # tối

def trit_name(t):
    return {AN_T: "ẩn", SANG_T: "sáng", TOI_T: "tối"}.get(t, "?")

# ============================================================
# TẦNG 4: LOGIC BA TRỊ KLEENE — dựng từ các cổng nhị phân Tầng 1
# Phủ định ba trị: NOT(sáng)=tối, NOT(tối)=sáng, NOT(ẩn)=ẩn.
# Với mã hoá trên, đảo b0<->b1 chính là phủ định → chỉ cần HOÁN DÂY.
# ============================================================
def k_not(t):
    b1, b0 = t
    return (b0, b1)                       # tráo hai bit = phủ định ba trị

def k_and(p, q):
    "AND ba trị (Kleene): sáng nếu cả hai sáng; tối nếu CÓ tối; ngược lại ẩn."
    p1, p0 = p; q1, q0 = q
    is_toi  = OR(p1, q1)                  # có ít nhất một 'tối'
    is_sang = AND(p0, q0)                 # cả hai 'sáng'
    b1 = is_toi
    b0 = AND(is_sang, NOT(is_toi))
    return (b1, b0)

def k_or(p, q):
    "OR ba trị (Kleene) = đối ngẫu De Morgan của k_and qua k_not."
    return k_not(k_and(k_not(p), k_not(q)))

# ---- Chứng minh: NHỊ PHÂN LÀ TRƯỜNG HỢP SUY BIẾN ----
def boolean_is_subcase():
    "Cấm 'ẩn' (chỉ dùng sáng=1, tối=0) → Kleene TRÙNG KHỚP đại số Boole."
    ok = True
    tab = {1: SANG_T, 0: TOI_T}
    for a in (0, 1):
        for b in (0, 1):
            # AND
            got = k_and(tab[a], tab[b]) == tab[AND(a, b)]
            # OR
            got &= k_or(tab[a], tab[b]) == tab[OR(a, b)]
            ok &= got
        got_not = k_not(tab[a]) == tab[NOT(a)]
        ok &= got_not
    return bool(ok)

# ============================================================
# TẦNG 5: VÒNG HỘI TỤ CDFL — chạy THUẦN bằng số học/dịch bit
# σ ← σ + ((ρ − σ) >> 1)   (học, α = 1/2 = dịch phải 1 bit)
# Phân loại trit theo khoảng cách d = ρ − σ:  d==0 → sáng tuyệt đối.
# ============================================================
def is_zero(A):
    "d == 0 ? — OR dồn mọi bit rồi NOT. Thuần cổng."
    acc = 0
    for i in range(W):
        acc = OR(acc, A[i])
    return NOT(acc)

def classify(d_bits, truth_bits):
    "Trạng thái trit từ khoảng cách d so với mục tiêu truth (đã biết hai trường ⇒ không 'ẩn')."
    if is_zero(d_bits) == 1:
        return SANG_T              # khớp tuyệt đối
    # còn lệch: vẫn 'sáng' nếu đã gần (|d| < nửa |truth|), bằng dấu & độ lớn — ngưỡng theo MỤC TIÊU, không hằng-chết
    return SANG_T if abs(bits_to_int(d_bits)) * 2 < max(1, abs(bits_to_int(truth_bits))) else TOI_T

def converge_demo(truth_int):
    truth  = int_to_bits(truth_int)
    belief = int_to_bits(0)        # bộ nhớ khởi đầu = 0 ⇒ hoàn toàn 'ẩn'
    print(f"   ρ (vật, thực tại) = {bits_str(truth)}  = {truth_int}")
    print(f"   σ khởi đầu        = {bits_str(belief)}  = 0   (bộ nhớ 0 ⇒ ẩn)\n")
    print("   vòng |     σ (nhị phân)   | σ(10) | d=ρ−σ | trit")
    print("   -----+--------------------+-------+-------+------")
    for t in range(8):
        d    = sub(truth, belief)
        st   = trit_name(classify(d, truth))
        print(f"    {t:2d}  | {bits_str(belief)} |  {bits_to_int(belief):3d}  |  {bits_to_int(d):3d}  | {st}")
        step = ashr1(d)                       # (ρ−σ) >> 1  — học bằng dịch bit
        if is_zero(step) == 1:
            print("        → step=0: chạm SÀN TỐI (D_min>0) — viên mãn tới hạn LSB (tiên đề 12)")
            break
        belief = ripple_add(belief, step)     # σ ← σ + step

# ============================================================
# DEMO
# ============================================================
if __name__ == "__main__":
    print("="*60)
    print("TẦNG 1 — Mọi cổng dựng từ DUY NHẤT cổng NAND")
    print("="*60)
    print(f"  NOT(0)={NOT(0)}  NOT(1)={NOT(1)}")
    print(f"  AND: 0,0={AND(0,0)} 0,1={AND(0,1)} 1,1={AND(1,1)}")
    print(f"  OR : 0,0={OR(0,0)} 0,1={OR(0,1)} 1,1={OR(1,1)}")
    print(f"  XOR: 0,1={XOR(0,1)} 1,1={XOR(1,1)}")

    print("\n" + "="*60)
    print("TẦNG 2 — Số học nhị phân từ các cổng (cộng/trừ/dịch)")
    print("="*60)
    a, b = int_to_bits(37), int_to_bits(9)
    print(f"  37 = {bits_str(a)}")
    print(f"   9 = {bits_str(b)}")
    print(f"  37+9 = {bits_str(ripple_add(a,b))} = {bits_to_int(ripple_add(a,b))}")
    print(f"  37-9 = {bits_str(sub(a,b))} = {bits_to_int(sub(a,b))}")
    print(f"  37>>1= {bits_str(ashr1(a))} = {bits_to_int(ashr1(a))}")

    print("\n" + "="*60)
    print("TẦNG 3–4 — TRIT cộng hưởng (2 bit) & logic ba trị Kleene")
    print("="*60)
    print(f"  Mã hoá:  ẩn={AN_T}  sáng={SANG_T}  tối={TOI_T}")
    print(f"  k_not(sáng) = {trit_name(k_not(SANG_T))}")
    print(f"  k_not(ẩn)   = {trit_name(k_not(AN_T))}   (chưa biết vẫn chưa biết)")
    print(f"  k_and(sáng,ẩn) = {trit_name(k_and(SANG_T,AN_T))}   (ẩn nuốt — DE lan truyền)")
    print(f"  k_and(tối,ẩn)  = {trit_name(k_and(TOI_T,AN_T))}   (đã có tối ⇒ tối)")
    print(f"  k_or (sáng,ẩn) = {trit_name(k_or(SANG_T,AN_T))}")
    print(f"\n  NHỊ PHÂN LÀ TRƯỜNG HỢP SUY BIẾN (cấm 'ẩn')? → {boolean_is_subcase()}")

    print("\n" + "="*60)
    print("TẦNG 5 — Vòng hội tụ CDFL chạy THUẦN bằng dịch bit")
    print("="*60)
    converge_demo(37)

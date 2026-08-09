# -*- coding: utf-8 -*-
"""
KIỂM TRA TOÀN BỘ — một lệnh xác minh cả dự án (như CI).
Gồm: bộ test ngôn ngữ · MCP · wasm conformance · mọi ví dụ thông dịch · mọi ví dụ máy.
   python kiem_toan_bo.py
"""
import os, sys, subprocess, glob
P = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
PY = sys.executable

# Ví dụ chỉ chạy ở MÁY (idiom `l==0`/cần cờ) — KHÔNG kỳ vọng chạy trên thông dịch trần:
CHỈ_MÁY = {"8_tong_ds_gvm", "11_chiso_sosanh_gvm", "io_quyen", "hdh_preempt", "hdh_fault", "driver_mmio"}

def chạy(mô_tả, args, kỳ_vọng=None, cwd=P):
    r = subprocess.run([PY]+args if args[0].endswith(".py") else args, capture_output=True,
                       text=True, env=ENV, cwd=cwd, encoding="utf-8")
    out = (r.stdout or "") + (r.stderr or "")
    ok = r.returncode == 0 and (kỳ_vọng is None or kỳ_vọng in out)
    return ok, out

tổng = rớt = 0
def mục(tên, ok, ct=""):
    global tổng, rớt; tổng += 1
    print(f"  {'✓' if ok else '✗'} {tên}" + ("" if ok else f"   {ct}"))
    if not ok: rớt += 1

print("="*64); print("KIỂM TRA TOÀN BỘ GIAO"); print("="*64)

print("\n[Bộ test]")
ok,o = chạy("kiem_thu", ["kiem_thu.py"], "KẾT QUẢ"); mục(f"ngôn ngữ — {o.strip().splitlines()[-2] if o else ''}".replace('='*64,'').strip(), ok and "đạt" in o)
ok,o = chạy("kiem_mcp", ["kiem_mcp.py"], "đạt"); mục("MCP server", ok)

print("\n[WASM conformance]")
ok,_ = chạy("sinh", ["wasm/sinh_tat_ca.py"]);
import shutil
node = shutil.which("node")
if node:
    r = subprocess.run([node, "wasm/kiem.mjs"], capture_output=True, text=True, env=ENV, cwd=P, encoding="utf-8")
    mục("wasm ⟷ Python (20 ca)", r.returncode==0 and "KHỚP" in (r.stdout or ""))
else:
    mục("wasm (bỏ qua — không có node)", True)

print("\n[Ví dụ thông dịch]")
ti = tr = 0
for f in sorted(glob.glob(os.path.join(P,"examples","*.giao"))):
    tên = os.path.splitext(os.path.basename(f))[0]
    if tên in CHỈ_MÁY: continue
    ok,o = chạy(tên, ["giao.py", f]); ti += 1
    if not ok: tr += 1; print(f"    ✗ {tên}: {o.strip().splitlines()[-1] if o.strip() else 'rỗng'}")
mục(f"{ti} ví dụ thông dịch chạy sạch", tr==0, f"{tr} rớt")

print("\n[Thư viện chuẩn]")
ok,o = chạy("lib_duyet", ["giao.py","kiem_lib_duyet.giao"])
kỳ = ["[1, 2, 5, 5, 6, 9]", "[1, 2, 3, 4]", "ẩn", "[1, 2, 3]", "[2, 4]",
      "[[0, 10], [1, 20], [2, 30]]", "[0, 1, 3, 6]", "[[1, 2], [3, 4], [5]]", "[1, 0, 2, 0, 3]", "[1, 9]",   # đợt1: liệt_kê/cuộn/theo_khối/xen_kẽ/min_max
      "[[1, 2, 3], [10, 20, 30]]", "[3, 4, 5, 1, 2]", "[[1, 1], [2], [3, 3], [1]]",   # đợt2: giải_nén/xoay_ds/gom_kề
      "[[1, 10, 100], [2, 20, 200]]", "[3, 5, 7]", "[5, 4, 3, 1, 1]",   # đợt3: khoá_kéo_nhiều/khác_biệt/sắp_giảm
      "[1, a, 2, b, 3, c]", "[9, 5, 4]", "[2, 3, 1, 4, 5]"]   # đợt4: đan/đỉnh_k/xáo(tất-định)
mục("lib_duyet (Enumerable đợt1-4: +đan/bản_đồ_chỉ_số/mỗi_với_chỉ_số/đỉnh_k/xáo)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_chuoi", ["giao.py","kiem_lib_chuoi.giao"])
kỳ = ["HELLO WORLD", "a-b-c-d", "ẩn", "xin chào", "ababab",
      "Xin Chào Thế Giới", "happy", "runn", "[a, b, ]", "[a, =, b=c]",   # đợt1: tiêu_đề/bỏ_tiền_tố/bỏ_hậu_tố/tách_giữ/phân_vùng
      "bb",   # regression: thay("aa","a","b")="bb" (sửa builtin tách bỏ-rỗng)
      "hippo", "hELLO", "[the quick, brown fox]", "[1, 3, 5]",   # đợt2: dịch/swapcase/bọc_dòng/chỉ_mục_tất_cả
      "[a, b, c,d]", "fox quick the", "hello w…",   # đợt3: tách_n/đảo_từ/viết_tắt
      "[a, b, c, d]"]   # đợt4: chia_ký (split nhiều dấu)
mục("lib_chuoi (String, ba-trị: +là_chữ_số/cắt_biến-thể/tách_giữ/phân_vùng/bỏ_tiền-hậu_tố/tiêu_đề)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_hàm", ["giao.py","kiem_lib_hàm.giao"])
kỳ = ["7", "15", "8", "tối", "sáng", "ẩn", "[6, 10]", "16", "99", "-4"]   # …đợt4: áp_đôi/điểm_bất_động/đầu_rõ→-4
mục("lib_hàm (combinators đợt1-4: +áp_đôi/điểm_bất_động/đầu_rõ — bao-đóng giữ-state + ba-trị)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_định_dạng", ["giao.py","kiem_lib_định_dạng.giao"])
kỳ = ["[   ab]", "[ab   ]", "007", "-07", "1,234,567", "ID=00042", "{x}=9", "thiếu a ẩn"]   # căn-lề/đệm-0/nhóm-phẩy/printf/escape/ba-trị
mục("lib_định_dạng (string-format: căn-lề/đệm-0/nhóm-phẩy/mini-printf {:spec}, ba-trị)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_toan", ["giao.py","kiem_lib_toan.giao"])
kỳ = ["1.414", "ẩn", "12", "sáng", "tối"]
mục("lib_toan (Math, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("dh_nhóm", ["kiem_dh_nhom.py"])
mục("nhóm Diffie-Hellman đúng RFC 3526 nhóm 14 (kiểm bằng CÔNG THỨC + nguyên tố an toàn)",
    ok and o.count("✓") >= 5, o.strip()[-120:])
ok,o = chạy("chacha20", ["giao.py","kiem_chacha20.giao","--bước","900000000"])
kỳ = ["10f1e7e4d13b5915500fdd1fa32071c4",          # RFC 8439 §2.3.2 khối
      "6e2e359a2568f98041ba0728dd0d6981",          # RFC 8439 §2.4.2 mã câu
      "b1023d4b4f71e65241a5c9905ded8aa60428a0db49adc95d93e2fbd5f5345d16",   # HMAC chuẩn
      'nói "sen vàng nở sớm"']
mục("ChaCha20 + HMAC-SHA256 THUẦN GIAO (khớp VECTOR RFC 8439 · khung kín mở lại nguyên văn)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("khoá_kho", ["lam_kho.py","--kiểm"])
mục("mục lục kho khớp thân gói VÀ đúng chữ ký (băm + RSA — chạy `python lam_kho.py` nếu lệch)",
    ok and "✓" in o, o.strip()[-120:])
ok,o = chạy("lib_sha256", ["giao.py","kiem_lib_sha256.giao"])
kỳ = ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
      "d9defc99671f93c3d55304e3cb1be019081a0624b8bf1dca421351258e4521ff",
      "2816597888e4a0d3a36b82b83316ab32680eb8f00f8cd3b904d681246d285a0e",
      "[97, 196, 131]"]
mục("SHA-256 THUẦN GIAO (FIPS 180-4 + UTF-8 tự dựng — khớp hashlib TỪNG KÝ TỰ)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_bit", ["giao.py","kiem_lib_bit.giao"])
kỳ = ["6", "8", "14", "1024", "-6", "3989547399", "2014458966",
      "1267650600228229401496703205376", "ẩn"]
mục("phép toán BIT (builtin A1: xor/và/hoặc/đảo/dịch — rotr32 dựng được, số lớn, ba-trị)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_thống_kê", ["giao.py","kiem_lib_thống_kê.giao"])
kỳ = ["2.5", "ẩn", "2.667", "1.633", "1.714", "[2, 3, 4]"]
mục("lib_thống_kê (Statistics, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_tổ_hợp", ["giao.py","kiem_lib_tổ_hợp.giao"])
kỳ = ["120", "ẩn", "[[1, 2], [1, 3], [2, 3]]", "[[1, 2], [2, 1]]", "[[], [1], [2], [1, 2]]"]
mục("lib_tổ_hợp (itertools/combinatorics, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_tập", ["giao.py","kiem_lib_tập.giao"])
kỳ = ["[1, 2, 3]", "[2, 3]", "[1, 2, 4]", "sáng", "tối"]
mục("lib_tập (Set, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_phân_số", ["giao.py","kiem_lib_phân_số.giao"])
kỳ = ["[1, 2]", "[-1, 2]", "ẩn", "5/6", "2/3", "4/3", "sáng", "tối"]
mục("lib_phân_số (Fraction, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_thập_phân", ["giao.py","kiem_lib_thập_phân.giao"])
kỳ = ["0.3", "0.01", "0.3333", "3.15", "0.14285714285714285714", "12345678901234567891.0",
      "1.331", "1.414213562373095048801688724210",
      "2.7182818285", "7.389056", "2.718281828459045235360287471353",   # mũ_e: e, e², e@30
      "0.6931471806", "2.302585093", "0.693147180559945309417232121458", "5.00000000",   # ln: ln2,ln10,ln2@30,exp∘ln
      "3.141592653589793238462643383280", "0.8414709848", "-0.54402111", "-1.00000000",   # pi@30, sin1, sin10(thu-gọn), cosπ
      "2.00000000", "10.000000",   # a^b: 8^⅓=2 · lô_ga: log₂1024=10
      "0.7853981634", "1.3734007669", "0.5235987756", "1.57079633",   # arctan π/4, arctan5, arcsin½ π/6, arcsin1 π/2
      "1.1752011936", "1.5430806348", "0.7615941560",   # sinh/cosh/tanh(1)
      "1125899906842624.00000000000000000000",   # 2^50 exact — guard-độ-lớn (review-vá)
      "1.2599210499",   # căn_bậc: ∛2 (Newton tổng-quát, n lẻ/chẵn + d<0 ba-trị)
      "ẩn", "sáng", "tối"]
mục("lib_thập_phân (Decimal độ-tuỳ-ý: số-học + siêu-việt đầy-đủ exp/ln/a^b/log/lượng-giác±/hyperbolic, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_đống", ["giao.py","kiem_lib_đống.giao"])
kỳ = ["[1, 2, 3, 5, 7, 8, 9]", "ẩn", "[9, 8]", "[1, 3, 4, 5, 7]", "sáng", "tối"]
mục("lib_đống (heapq priority-queue + bisect, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_hàng", ["giao.py","kiem_lib_hàng.giao"])
kỳ = ["[1, 2, 3]", "[0, 1, 2]", "ẩn", "[4, 1, 2, 3]", "[[3, 3], [1, 2]]", "sáng", "tối"]
mục("lib_hàng (deque hai-đầu + phổ_biến_nhất/most_common, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_lịch", ["giao.py","kiem_lib_lịch.giao"])
kỳ = ["khẩn", "web", "nền", "trang1", "trang2", "khởi động", "ẩn"]   # lập-lịch ưu-tiên + IPC FIFO
mục("lib_lịch (lập-lịch ưu-tiên + IPC hộp-thư, Nhánh II 2.B, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_tiến_trình", ["giao.py","kiem_lib_tiến_trình.giao"])
kỳ = ["cơ-sở-dữ-liệu", "chặn", "[web, log]", "[db]", "chết", "ẩn", "tối", "sáng"]   # bảng tiến-trình: tên/trạng/liệt/giết/tid-lạ→ẩn
mục("lib_tiến_trình (bảng tiến-trình có-tên + vòng-đời trạng-thái, ba-trị)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("va-tên module", ["giao.py","kiem_va_ten.giao"])   # namespace phẳng: nhập 2 tệp đụng tên → cảnh-báo + bản-sau-che
mục("phát-hiện va-tên (nhập 2 module đụng tên → cảnh-báo stderr, bản-sau-che, KHÔNG vỡ)",
    ok and ("va-tên" in o) and ("va_thử" in o) and ("12" in o), "thiếu cảnh-báo va-tên hoặc che sai")

ok,o = chạy("hdh_hệ", ["giao.py","hdh_hệ.giao"])
kỳ = ["điều_phối → lưu", "chặn", "yêu-cầu", "chết", "số_sống = 2", "checkpoint/restore Y NGUYÊN",
      "p-chặn KHÔNG dispatch (ẩn) ĐÚNG", "gửi_tin = chết", "a / ẩn ĐÚNG", "nhường-trùng→điều_phối = y / ẩn ĐÚNG"]   # chốt-regression đồng-bộ IPC-chặn + nhường (review-vá)
mục("hdh_hệ (NHÂN HĐH-GIAO HỢP-NHẤT: bảng+lập-lịch+IPC-blocking+persistence, đồng-bộ-an-toàn)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("hdh_lịch_học", ["giao.py","hdh_lịch_học.giao"])
kỳ = ["90", "8", "57", "tốt", "ẩn", "spin bị bóp"]   # γ-học: tốt σ→90 ưu-tiên · spin σ→8 bóp · tid-lạ→ẩn
mục("hdh_lịch_học (γ-SCHEDULER biết-học tầng GIAO: σ←σ+(ρ−σ)//4, khớp silicon)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("hdh_thích_nghi", ["giao.py","hdh_thích_nghi.giao"])
kỳ = ["daemon", "chạy", "2", "ẩn", "merit học-được"]   # nhân thích-nghi: γ-học chọn CPU + loại_bỏ bỏ-qua-chết
mục("hdh_thích_nghi (NHÂN THÍCH-NGHI: γ-scheduler-học ⊗ bảng-tiến-trình, CPU theo merit)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("hdh_lịch", ["giao.py","hdh_lịch.giao"])
kỳ = ["khẩn bước #1", "thường bước #3", "nền bước #1", "máy-in nhận: trang-A", "trang-C", "NHÂN dừng"]
mục("hdh_lịch (NHÂN hợp-tác lái bằng lib_lịch: strict-priority + IPC)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("hdh_bền_lịch", ["giao.py","hdh_bền_lịch.giao"])
kỳ = ["chạy: lưu", "chạy: tính", "chạy: dọn", "log: khởi-động", "log: nạp-xong", "KHÔI PHỤC ĐẦY ĐỦ"]
mục("hdh_bền_lịch (PERSISTENCE: snapshot JSON → sập → khôi phục, ready-queue + IPC sống sót)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("hdh_chặn", ["giao.py","hdh_chặn.giao"])
kỳ = ["thợ: CHẶN chờ việc", "gửi việc-1 cho thợ", "việc-1"]   # IPC blocking: chặn → đánh-thức → nhận
mục("hdh_chặn (IPC CHẶN + ĐÁNH-THỨC: chờ_tin rỗng→chặn, gửi→wake, ba-trị)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_bản", ["giao.py","kiem_lib_bản.giao"])
kỳ = ["[y, z]", "ẩn", "22", "sáng", "tối", "[[x, 1], [z, 3]]", "[1, ẩn, 3]",   # đợt2: chọn/bỏ_khoá · lấy_nhiều
      "[[a, 3], [b, 1], [c, 2]]",   # đợt3: cặp_sắp (sắp theo khoá)
      "[x, y]", "[[b, 1], [c, 2], [a, 3]]"]   # đợt4: đảo_nhóm/cặp_sắp_giá
mục("lib_bản (Hash đợt1-4: +từ_khoá_giá/đảo_nhóm/cặp_sắp_giá)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_json", ["giao.py","kiem_lib_json.giao"])
kỳ = ['{"a":1,"b":[2,3]}', '{"k":[1,2],"c":true,"n":null}', "ẩn", "3.5"]   # null↔ẩn, round-trip
mục("lib_json (JSON parse/serialize, null↔ẩn)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_regex", ["giao.py","kiem_lib_regex.giao"])
sl = o.strip().splitlines()
mục("lib_regex (backtracking: .*+? ^$ [a-z] [^..])",
    ok and sl == ["sáng","sáng","sáng","tối","sáng","tối","sáng","sáng","tối","sáng","sáng","sáng","sáng","sáng","tối"])
ok,o = chạy("lib_regex_nc", ["giao.py","kiem_lib_regex_nc.giao"])
kỳ = ["[42, 7]", "x#y#z", "[an@gmail, an, gmail]", "[10-25, 10, 25]", "ẩn"]   # findall · sub · capture · không-khớp→ẩn
mục("lib_regex nâng-cao (\\d\\w\\s · alt | · nhóm () capture · findall/sub)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("ca_bien_an", ["giao.py","kiem_ca_bien_an.giao"])   # chốt-regression review 2026-06-19
# marker cuối CHỈ in nếu KHÔNG abort (mọi guard ẩn + chống-DoS regex còn nguyên); + đường-thường vẫn đúng
mục("ca-biên ẩn/DoS (guard ẩn lib số/đếm/parser/base64/định-dạng + regex chống lặp-mũ & đệ-quy-sâu & lát O(n) → ẩn, không crash/treo)",
    ok and "CA-BIÊN ẨN/DoS: HẾT" in o and "20" in o and "sáng" in o and "tối" in o and "600" in o,
    "abort/thiếu-guard" if "CA-BIÊN ẨN/DoS: HẾT" not in o else "")
ok,o = chạy("ca_bien_an_td", ["giao.py","kiem_ca_bien_an_td.giao"])   # chốt-regression decimal (tách: làm_tròn/căn va-tên)
mục("ca-biên ẩn decimal (thập_phân/_mười_mũ/luỹ_thừa + thang=ẩn ở 17 hàm siêu-việt → ẩn, không crash/lặp/malformed)",
    ok and "CA-BIÊN ẨN decimal: HẾT" in o and "1024" in o and "1.4142135624" in o,
    "abort/thiếu-guard" if "CA-BIÊN ẨN decimal: HẾT" not in o else "")
ok,o = chạy("ca_bien_an_lib", ["giao.py","kiem_ca_bien_an_lib.giao"])   # chốt-regression sweep: collection/stat/OS-layer + builtin khoá-ẩn
mục("ca-biên ẩn sweep (collection/stat/đống/hàng/tiến-trình/khonggian + builtin khoá-bản(ẩn) → ẩn, không crash)",
    ok and "CA-BIÊN ẨN lib (collection/OS): HẾT" in o and "[1, 2, 3]" in o,
    "abort/thiếu-guard" if "CA-BIÊN ẨN lib (collection/OS): HẾT" not in o else "")
ok,o = chạy("phuc_tap", ["giao.py","kiem_phuc_tap.giao"])   # PERF-GUARD: O(n²)→O(n) (duy_nhất/lib_tập/mốt/heapsort) — revert O(n²) → chạm-trần 5M → rớt
mục("perf O(n) (duy_nhất/hợp_tập/con_của/mốt/heapsort ở n=1500 → KHÔNG chạm-trần 5M; revert O(n²) sẽ rớt)",
    ok and "PERF-GUARD O(n): HẾT" in o and "1500" in o,
    "chạm-trần/O(n²)-regression" if "PERF-GUARD O(n): HẾT" not in o else "")
ok,o = chạy("lib_csv", ["giao.py","kiem_lib_csv.giao"])
kỳ = ["Bình, Jr", 'a,"b,c"', 'd,"e""f"', "Số 1, Lê Lợi"]
mục("lib_csv (parse/serialize, ô-có-nháy)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_url", ["giao.py","kiem_lib_url.giao"])
kỳ = ["example.com", "8080", "ẩn", "a=1&b=2&c=3"]
mục("lib_url (parse URL/query, thiếu→ẩn)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_base64", ["giao.py","kiem_lib_base64.giao"])
kỳ = ["TWFu", "TQ==", "Hello", "WGluIGNow6BvIEdJQU8="]   # khớp Python, UTF-8 Việt
mục("lib_base64 (base64+UTF-8, khớp Python)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_bam_mau", ["giao.py","kiem_lib_bam_mau.giao"])
kỳ = ["261238937", "Chào An, 25 tuổi!", "{thiếu}"]   # djb2 khớp Python + template
mục("lib_băm/lib_mẫu (djb2 hash + template)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("app_baocao", ["giao.py","app_baocao.giao"])
kỳ = ['{"tên":"Dung","tuổi":"19","điểm":"95"}', "Đủ tuổi: 3 người", "điểm TB: 86", "đầu bảng: Dung"]
mục("app_baocao (PHẦN-MỀM thật ghép 6 lib: csv+duyệt+toán+json+mẫu)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
o1 = chạy("ng_host0", ["giao.py","kiem_lib_ngày_host.giao"])[1]        # KHÔNG cấp → ẩn
ok,o2 = chạy("ng_host1", ["giao.py","kiem_lib_ngày_host.giao","--cho-giờ"])  # CÓ cấp → ngày thật
mục("lib_ngày_host (giờ thật qua capability; chưa-cấp→ẩn)",
    ok and "CHUA-CAP" in o1 and "OK-NGAY-HOP-LE" in o2)
ok,o = chạy("lib_ngày", ["giao.py","kiem_lib_ngày.giao"])
kỳ = ["Thứ Bảy", "[2024, 2, 29]", "2024-03-05", "ẩn"]
mục("lib_ngày (Date math, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_thời_gian", ["giao.py","kiem_lib_thời_gian.giao"])
kỳ = ["2026-06-17T14:30:00+07:00", "2026-06-18T00:30:00+07:00", "2026-06-17T07:30:00+00:00", "7200", "ẩn", "sáng", "tối"]
mục("lib_thời_gian (datetime + múi-giờ ISO8601, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_io", ["giao.py","kiem_lib_io.giao","--cho-đọc","."])
kỳ = ["danh_sách", "tối", "ẩn", "sáng"]   # đọc/liệt được cấp · ghi/chạy chưa-cấp → tối/ẩn (sandbox)
mục("lib_io (capability, ba-trị + sandbox)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("driver_mmio", ["giao.py","examples/driver_mmio.giao","--cho-mmio"])   # CÓ cấp → MMIO tồn tại
kỳ = ["UART", "GIAO xuong chip", "LED", "●", "phục vụ"]   # UART serial + GPIO LED + γ-scheduler mới
mục("driver MMIO bare-metal (UART+GPIO+timer, lịch γ mới; --cho-mmio; chưa-cấp→ocap)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_baomat", ["giao.py","kiem_lib_baomat.giao"])
kỳ = ["khởi động", "tối", "ẩn", "50"]   # write-up CHẶN, fail-safe ẩn, σ HỌC tụt → mất quyền
mục("lib_baomat (γ-gated, no-write-up + σ học-được)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_khonggian", ["giao.py","kiem_lib_khonggian.giao"])
kỳ = ["thư_mục", "[đĩa0]", "ẩn", "sáng"]   # object namespace, thiếu→ẩn
mục("lib_khonggian (object namespace, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_dichvu", ["giao.py","kiem_lib_dichvu.giao"])
kỳ = ["lỗi", "3", "tối", "ẩn"]   # vòng-đời + phụ-thuộc + hồi-phục→cô-lập
mục("lib_dichvu (service: phụ-thuộc + hồi-phục/cô-lập)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_nhóm", ["giao.py","kiem_lib_nhóm.giao"])
kỳ = ["700", "300", "1200", "1000", "501", "sáng", "tối", "ẩn"]   # Job Object: kế-toán/hạn-mức + γ-động (σ thấp bị bóp) + ba-trị
mục("lib_nhóm (Job Object/cgroup: hạn-mức + kế-toán + γ-động — học Win, vượt bằng CDFL)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("lib_đồng_bộ", ["giao.py","kiem_lib_đồng_bộ.giao"])
kỳ = ["sáng", "ẩn", "tối", "2", "9", "3", "1"]   # lock(FIFO→2) · γ-fair(→9 σ-cao) · sem(wake 3) · condvar(wake 1) · ba-trị
mục("lib_đồng_bộ (lock/semaphore/condvar — ba-trị + đánh-thức γ-công-bằng, học Win vượt CDFL)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("hdh_full", ["giao.py","hdh_full.giao"])
kỳ = ["CHẶN", "tước quyền", "CÔ-LẬP", "sự-kiện-2", "QUOTA CHẶN", "cấp OK"]   # 4 hệ-con: ns + bảo-mật-γ + dịch-vụ + QUOTA-γ-động
mục("hdh_full (NHÂN HĐH tích-hợp: ns + bảo-mật-γ + dịch-vụ + quota-γ-động)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("trien_khai", ["giao.py","trien_khai.giao"])
kỳ = ["64-bit", "WASM", "ẩn"]   # planner theo chip; chip chưa-dò → cấu-hình ẩn
mục("trien_khai (planner silicon-aware theo chip, ba-trị)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok1,o1 = chạy("tk_auto", ["giao.py","trien_khai_tu_dong.giao","--cho-phan-cung"])  # CÓ cấp → tự-dò chip thật
_,o0 = chạy("tk_auto_sb", ["giao.py","trien_khai_tu_dong.giao"])                   # CHƯA cấp → sandbox chặn
kỳ = ["WASM-native-memory-safe", "ẩn"]   # tự-dò: nền (fpga=tối) + L2-chưa-dò→ẩn (ba-trị)
mục("trien_khai_tu_dong (TỰ-DÒ chip qua capability `phần_cứng` + sandbox bẩm sinh)",
    ok1 and all(k in o1 for k in kỳ) and ("chưa định nghĩa" in o0),
    "tự-dò hỏng hoặc sandbox hở")
ok,o = chạy("tinh_gon", ["giao.py","tinh_gon.giao"])
kỳ = ["71%", "WASM", "9x"]   # phân-tích thừa Windows → triển-khai GIAO tinh-gọn
mục("tinh_gon (phân-tích thừa HĐH → triển-khai GIAO tối-ưu)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("kiem_trienkhai", ["kiem_trienkhai.py"], "ĐÚNG CHUẨN")
mục("xác minh planner ĐÚNG CHUẨN trên 7 loại máy (GIAO ⟷ tham-chiếu)", ok and "10/10" in o)
ok,o = chạy("kiem_lich_hoc_silicon", ["kiem_lich_hoc_silicon.py"], "KHỚP CHÍNH-SÁCH SILICON")
mục("γ-scheduler-học cấp-GIAO ⟷ chính-sách SILICON (conformance σ←σ+(ρ−σ)>>2)", ok and "8/8" in o)
ok,o = chạy("hdh_full_may", ["giao.py","hdh_full_may.giao"])
kỳ = ["CHAN", "tuoc quyen", "CO-LAP", "2000", "QUOTA CHAN", "cap OK"]   # 4 hệ-con TẬP-CON-MÁY (biên-dịch GVM/silicon): +quota γ-động
mục("hdh_full_may (nhân tích-hợp tập-con-máy +quota-γ → silicon)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("hdh_sync_may", ["giao.py","hdh_sync_may.giao"])
kỳ = ["GIU", "trao cho t2", "trao cho t9", "wake t3", "dem=1"]   # sync TẬP-CON-MÁY (biên-dịch GVM/silicon): lock FIFO + γ-fair(t9) + semaphore
mục("hdh_sync_may (lock/semaphore + γ-fair tập-con-máy → silicon)", ok and all(k in o for k in kỳ),
    "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("hdh_qs_may", ["giao.py","hdh_qs_may.giao"])
kỳ = ["GIU vung-toi-han", "trao lock cho t2", "QUOTA CHAN", "bi bop CA HAI", "wake t3"]   # HỢP-NHẤT quota+sync: 1 σ điều-phối CẢ HAI
mục("hdh_qs_may (HỢP-NHẤT quota+sync: 1 σ → wake-lock + trần-quota, tập-con-máy → silicon)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o))
ok,o = chạy("tu_sua", ["kiem_tu_sua.py"], "TỰ-SỬA THÀNH CÔNG")
mục("vòng TỰ-SỬA Stage1-3 (gieo lỗi→tự vá→sáng, cổng CDFL)", ok)
ok,o = chạy("tu_sua_loc", ["kiem_tu_sua_localize.py"], "ĐỊNH-VỊ đúng")
mục("vòng TỰ-SỬA Stage4 (định-vị tệp lỗi qua suite→vá)", ok)

print("\n[Ví dụ máy (giaoc)]")
MÁY = ["7_danh_sach_gvm","8_tong_ds_gvm","9_chuoi_gvm","10_nhieu_thamso_gvm","11_chiso_sosanh_gvm",
       "12_eval_may","13_the_kieu_gvm","giai_thua","hoi_tu_biendich","closure_gvm","ban_gvm",
       "lap_trong_gvm","so_thuc_gvm","thu_bat_mai_gvm","hdh","hdh_preempt","hdh_fault","hdh_ben",
       "heap32_gvm","heap32_chuoi","heap32_io","heap32_an","heap32_concat","giaoc"]
tm = trм = 0
for tên in MÁY:
    ok,o = chạy(tên, ["giaoc.py", os.path.join("examples",tên+".giao")]); tm += 1
    if not ok: trм += 1; print(f"    ✗ {tên}")
mục(f"{tm} ví dụ máy biên dịch+chạy", trм==0, f"{trм} rớt")

print("\n[★ HĐH-GIAO lối Linux + trợ lý AI]")
ok,o = chạy("hdh_giao", ["kiem_hdh_giao.py"], "hạng mục đạt")
_dòng = [l for l in o.splitlines() if "HĐH-GIAO:" in l]
mục(f"hệ-tệp · quyền · gọi-hệ · vỏ · trợ lý ({_dòng[-1].split(':')[-1].strip() if _dòng else '?'})",
    ok and "RỚT" not in o)

ok,o = chạy("lich_gamma", ["kiem_lich_gamma.py"], "TRÙNG KHÍT")
mục("lịch γ của HĐH ≡ lịch γ của máy/silicon (2000 ca ngẫu nhiên)", ok)

ok,o = chạy("kho_phiên", ["giao.py","kiem_kho_phien.giao","--bước","900000000"])
kỳ = ["kho chỉ có 'nền' bản 1.0 — không thoả nền >= 2.0",     # I3: ràng buộc phiên bản
      "✓ nền 2.0 (cần vì 'trên' cần nền>=2.0)",
      "✓ nền_khác 3.0 (cần vì 'hai_ngả' cần nền>=9.9/nền_khác)",   # I3: gói thay thế
      "không gỡ được: trên, hai_ngả đang cần 'nền'",
      "↩ nền → 3.0", "↩ nền → 2.0", "còn lùi được 0 bước"]        # I4: lùi nhiều bước
mục("kho: phụ thuộc CÓ PHIÊN BẢN + gói thay thế + LÙI NHIỀU BƯỚC (I3·I4)",
    ok and all(k in o for k in kỳ), "thiếu: "+", ".join(k for k in kỳ if k not in o)[:150])
ok,o = chạy("kho_xa", ["kiem_kho_xa.py"], "hạng mục đạt")
_dòng = [l for l in o.splitlines() if "KHO QUA MẠNG:" in l]
mục(f"kho phần mềm QUA MẠNG (tải về ≠ tin: chữ ký sai/khoá khác → KHÔNG ghi byte nào) "
    f"({_dòng[-1].split(':')[-1].strip() if _dòng else '?'})", ok and "RỚT" not in o)

ok,o = chạy("tu_xa", ["kiem_tu_xa.py"], "hạng mục đạt")
_dòng = [l for l in o.splitlines() if "TỪ XA:" in l]
mục(f"mạng ra host + ĐĂNG NHẬP TỪ XA (ocap kẹp cổng · quyền/cổng-duyệt/audit vẫn nguyên) "
    f"({_dòng[-1].split(':')[-1].strip() if _dòng else '?'})", ok and "RỚT" not in o)

ok,o = chạy("ban_lam_viec", ["kiem_de.py"], "hạng mục đạt")
_dòng = [l for l in o.splitlines() if "BÀN LÀM VIỆC:" in l]
mục(f"bàn làm việc (desktop trên nhân THẬT: quyền chặn · cổng duyệt · khoá phiên) "
    f"({_dòng[-1].split(':')[-1].strip() if _dòng else '?'})", ok and "RỚT" not in o)

print("\n[★ Pha 3 — Tối-ưu bytecode (Track C)]")
try:
    import kiem_toi_uu
    _lo, _ln = kiem_toi_uu.kiểm_luật()
    _ok, _n, _rớt, _gb, _gs = kiem_toi_uu.chạy_kiểm()
    mục(f"tối-ưu bytecode (luật {_lo}/{_ln} provably-safe + conformance {_ok}/{_n} KHỚP BYTE; bước −{_gs:.1f}% / bytecode −{_gb:.1f}%)",
        _lo == _ln and _ok == _n and not _rớt, str(_rớt) if _rớt else f"luật {_lo}/{_ln}")
except Exception as e:
    mục("tối-ưu bytecode conformance", False, f"EXC {e}")

print("\n" + "="*64)
print(f"TOÀN BỘ: {tổng-rớt}/{tổng} hạng mục đạt" + ("" if rớt==0 else f"  — {rớt} RỚT"))
print("="*64)
sys.exit(1 if rớt else 0)

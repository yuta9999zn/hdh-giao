# -*- coding: utf-8 -*-
"""
KIỂM THỬ GIAO — bộ test cho tính ỔN ĐỊNH + BẢO MẬT của runtime.
Kiểm: hành vi đúng, lỗi sạch (KHÔNG traceback Python) kèm số dòng, giới hạn tài
nguyên (chống vòng lặp/đệ quy vô tận), và thử/bắt. Thoát mã ≠ 0 nếu có test rớt.
"""
import sys, io, contextlib
sys.setrecursionlimit(40000)
from giao import tokenize, Parser, Runtime, GiaoError, GiaoLimit, nạp_chuẩn

def chạy(src, max_steps=None, max_depth=None, chuẩn=False, cấp=None):
    "Chạy nguồn GIAO; trả (đầu_ra, lỗi). chuẩn=True nạp thư viện chuẩn. cấp(rt) để trao quyền I/O."
    rt = Runtime()
    if max_steps is not None: rt.MAX_STEPS = max_steps
    if max_depth is not None: rt.MAX_DEPTH = max_depth
    buf = io.StringIO(); err = None
    try:
        with contextlib.redirect_stdout(buf):
            if chuẩn: nạp_chuẩn(rt)
            if cấp: cấp(rt)
            rt.exec_block(Parser(tokenize(src)).parse())
    except (GiaoError, GiaoLimit, SyntaxError) as e:
        err = e
    return buf.getvalue(), err

TỔNG = 0; RỚT = 0
def kiểm(tên, điều_kiện, chi_tiết=""):
    global TỔNG, RỚT; TỔNG += 1
    if điều_kiện: print(f"  ✓ {tên}")
    else: RỚT += 1; print(f"  ✗ {tên}   {chi_tiết}")

print("="*64); print("KIỂM THỬ GIAO — ổn định & bảo mật"); print("="*64)

# ---------- 1. HÀNH VI ĐÚNG ----------
print("\n[1] Hành vi đúng")
out, e = chạy('hàm cd(n) { nếu n == 0 { trả 0 } trả n + cd(n - 1) } rọi cd(5)')
kiểm("đệ quy: cd(5)=15", e is None and out.strip() == "15", f"out={out!r} e={e}")

out, e = chạy('đặt a = 10\nrọi (a) + (ẩn)')        # ẩn lan truyền
kiểm("ẩn lan truyền: 10+ẩn=ẩn", e is None and out.strip() == "ẩn", f"out={out!r}")

out, e = chạy('rọi (8) / (0)')                      # chia 0 → ẩn, KHÔNG nổ
kiểm("chia 0 → ẩn (không lỗi)", e is None and out.strip() == "ẩn", f"out={out!r} e={e}")

# ---------- 2. LỖI SẠCH + SỐ DÒNG (KHÔNG traceback Python) ----------
print("\n[2] Lỗi sạch + số dòng")
out, e = chạy('đặt a = 1\nrọi không_có')
kiểm("tên chưa định nghĩa → GiaoError", isinstance(e, GiaoError), f"e={type(e).__name__}")
kiểm("...đúng số dòng (2)", isinstance(e, GiaoError) and e.line == 2, f"line={getattr(e,'line',None)}")
kiểm("...thông điệp rõ", isinstance(e, GiaoError) and "chưa định nghĩa" in e.msg, f"msg={getattr(e,'msg','')}")

out, e = chạy('rọi (5) - ("x")')          # '-' đòi số thật (khác '+' là nối chuỗi)
kiểm("số − chuỗi: lỗi kiểu sạch", isinstance(e, GiaoError) and "không thể" in e.msg, f"e={e}")

out, e = chạy('đặt l = [1, 2]\nrọi l[9]')
kiểm("chỉ mục ngoài phạm vi → lỗi", isinstance(e, GiaoError) and "ngoài phạm vi" in e.msg, f"e={e}")

out, e = chạy('rọi đầu([])')
kiểm("đầu([]) → lỗi sạch (không IndexError)", isinstance(e, GiaoError) and "rỗng" in e.msg, f"e={e}")

out, e = chạy('hàm f(a) { trả a } rọi f(1, 2)')
kiểm("sai số đối → lỗi hợp đồng", isinstance(e, GiaoError) and "đối" in e.msg, f"e={e}")

out, e = chạy('học chưa_có')
kiểm("học vật chưa khai báo → lỗi sạch", isinstance(e, GiaoError) and "học" in e.msg, f"e={e}")

# ---------- 3. GIỚI HẠN TÀI NGUYÊN (bảo mật) ----------
print("\n[3] Giới hạn tài nguyên (sandbox)")
out, e = chạy('hàm f(n) { trả f(n) } rọi f(1)', max_depth=200)
kiểm("đệ quy vô tận → GiaoLimit (không treo)", isinstance(e, GiaoLimit) and "đệ quy" in e.msg, f"e={type(e).__name__}:{e}")

out, e = chạy('lặp 100000 { đặt x = 1 }', max_steps=5000)
kiểm("vòng lặp lớn → GiaoLimit số bước", isinstance(e, GiaoLimit) and "bước" in e.msg, f"e={e}")

# ---------- 4. THỬ / BẮT ----------
print("\n[4] thử/bắt (xử lý lỗi trong ngôn ngữ)")
out, e = chạy('thử {\n  đặt y = không_có\n} bắt (loi) {\n  rọi "bắt: " + loi\n}\nrọi "tiếp tục"')
kiểm("thử/bắt bắt lỗi & phục hồi", e is None and "bắt: " in out and "tiếp tục" in out, f"out={out!r} e={e}")

out, e = chạy('thử {\n  rọi "ổn"\n} bắt (x) {\n  rọi "không nên thấy"\n}')
kiểm("không lỗi → bắt KHÔNG chạy", e is None and "ổn" in out and "không nên" not in out, f"out={out!r}")

out, e = chạy('hàm f(n) { trả f(n) }\nthử {\n  rọi f(1)\n} bắt (x) {\n  rọi "nuốt được DoS?!"\n}', max_depth=200)
kiểm("thử/bắt KHÔNG nuốt GiaoLimit (an toàn)", isinstance(e, GiaoLimit) and "nuốt" not in out, f"out={out!r} e={type(e).__name__}")

# ---------- 5. KHÔNG RÒ RỈ TRACEBACK ----------
print("\n[5] Không rò rỉ nội tạng Python")
ok = True
for bẫy in ['rọi x[0]', 'rọi 1 + [2]', 'rọi (sai)(1)', 'lặp ẩn { }']:
    o, er = chạy(bẫy)
    if er is not None and not isinstance(er, (GiaoError, GiaoLimit, SyntaxError)): ok = False
kiểm("mọi lỗi đều là lỗi GIAO (không Python)", ok)

# ---------- 6. THƯ VIỆN CHUẨN ----------
print("\n[6] Thư viện chuẩn (bản_đồ/lọc/gấp/số học/chuỗi)")
out, e = chạy('hàm đôi(x){trả x*2}\nrọi bản_đồ(đôi,[1,2,3])', chuẩn=True)
kiểm("bản_đồ", e is None and "[2, 4, 6]" in out, f"out={out!r} e={e}")
out, e = chạy('rọi lọc(chẵn, dải(6))', chuẩn=True)
kiểm("lọc + chẵn + dải", e is None and "[0, 2, 4]" in out, f"out={out!r} e={e}")
out, e = chạy('rọi gộp(dải_từ(1,6))', chuẩn=True)
kiểm("gấp/gộp tổng 1..5=15", e is None and out.strip() == "15", f"out={out!r} e={e}")
out, e = chạy('rọi dư(17,5)', chuẩn=True)
kiểm("dư 17 mod 5 = 2", e is None and out.strip() == "2", f"out={out!r} e={e}")
out, e = chạy('rọi nối(["a","b","c"],"-")', chuẩn=True)
kiểm("nối chuỗi a-b-c", e is None and out.strip() == "a-b-c", f"out={out!r} e={e}")
out, e = chạy('rọi gộp(bản_đồ(giai_thừa, [1,2,3,4]))', chuẩn=True)
kiểm("kết hợp bản_đồ∘gộp", e is None and out.strip() == "33", f"out={out!r} e={e}")  # 1+2+6+24

# ---------- 7. TẦNG HỌC THUYẾT CDFL ----------
print("\n[7] Tầng học thuyết CDFL")
# ★ CDFL MỚI: γ nay là SKILL-SCORE (F.4) thay proxy 1−2d/scale. cộng_hưởng(90,100):
#   d=10,scale=100 → R=exp(−0.01)=0.990 → γ=(1−0.01005)/(1+0.01005)=0.9802 (cùng dấu dương, "sáng").
out, e = chạy('rọi cộng_hưởng(90, 100)')
kiểm("cộng_hưởng(90,100)=0.9802 (skill-score)", e is None and out.strip() == "0.9802", f"out={out!r} e={e}")
out, e = chạy('rọi đầu(chọn([["A",40,100],["B",90,100],["C",20,100]]))', chuẩn=True)
kiểm("chọn hành động OR lớn nhất = B", e is None and out.strip() == "B", f"out={out!r} e={e}")
out, e = chạy('rọi or_tập_thể([["a",90],["b",70]], 100)', chuẩn=True)
kiểm("or_tập_thể [γ_tốt, đa_dạng]", e is None and "0.9802" in out and "20" in out, f"out={out!r} e={e}")
out, e = chạy('vật A = 50\ntâm A = ẩn\nhọc A\nvật A = 90\nrọi de')
dt = [ln for ln in out.splitlines() if "DE_T" in ln]
kiểm("DE bốn mặt: DE_T bắt thế giới trôi", e is None and dt and "A" in dt[0], f"out={out!r} e={e}")

# ---------- 8. v0.3 — VÒNG LIÊN TỤC + THẾ GIỚI TỰ TRÔI + σ/Φ ENSEMBLE ----------
print("\n[8] v0.3 — mãi/dừng, trôi (tự trôi), σ/Φ ensemble")
out, e = chạy('đặt i = 0\nmãi {\n  đặt i = i + 1\n  rọi i\n  nếu i >= 3 { dừng }\n}')
kiểm("mãi + dừng: chạy tới điều kiện rồi thoát", e is None and out.split()==["1","2","3"], f"out={out!r} e={e}")

out, e = chạy('đặt s = 0\nlặp 9 {\n  đặt s = s + 1\n  nếu s == 4 { dừng }\n}\nrọi s')
kiểm("dừng thoát được cả lặp N", e is None and out.strip()=="4", f"out={out!r} e={e}")

# trôi: thế giới TỰ dịch một nhịp → vật đổi mà KHÔNG tự tay gán
out, e = chạy('vật w = 10\ntrôi w = (vật w) + 5\ntrôi\nrọi (vật w)')
kiểm("trôi: thế giới tự dịch 10→15", e is None and out.strip()=="15", f"out={out!r} e={e}")

# trôi sau khi học → DE_T bật (tự thân, không sửa tay vật)
out, e = chạy('vật d = 50\ntâm d = ẩn\ntrôi d = (vật d) + 20\nhọc d\ntrôi\nrọi de')
dt = [ln for ln in out.splitlines() if "DE_T" in ln]
kiểm("trôi tự thân → DE_T mọc lại", e is None and dt and "d" in dt[0], f"out={out!r} e={e}")

out, e = chạy('hàm Φ1(x){trả x}\nhàm Φ2(x){trả x/2}\nrọi ensemble_γ(50,[Φ1,Φ2],100)', chuẩn=True)
kiểm("σ/Φ ensemble: γ tốt nhất=1 (Φ nửa khớp)", e is None and out.strip()=="1", f"out={out!r} e={e}")

out, e = chạy('hàm Φ1(x){trả x}\nrọi de_if_Φ(50,[Φ1],999999,0.5)', chuẩn=True)
kiểm("de_if_Φ sáng khi không Φ nào khớp", e is None and out.strip()=="sáng", f"out={out!r} e={e}")

# ---------- 9. I/O THEO NĂNG LỰC (object-capability) ----------
print("\n[9] I/O theo năng lực (ocap: không cấp ⇒ không tồn tại)")
out, e = chạy('rọi đọc_tệp("chuẩn.giao")')                       # KHÔNG cấp quyền
kiểm("chưa cấp → đọc_tệp không tồn tại", isinstance(e, GiaoError) and "chưa định nghĩa" in e.msg, f"e={e}")

cấp_đọc = lambda rt: rt.cấp_quyền("đọc_tệp", gốc=["."])
out, e = chạy('rọi dài(đọc_tệp("chuẩn.giao")) > 0', cấp=cấp_đọc)
kiểm("cấp đọc → đọc được tệp trong phạm vi", e is None and out.strip() == "sáng", f"out={out!r} e={e}")

cấp_hẹp = lambda rt: rt.cấp_quyền("đọc_tệp", gốc=["examples"])
out, e = chạy('rọi đọc_tệp("chuẩn.giao")', cấp=cấp_hẹp)          # tệp ngoài 'examples'
kiểm("ngoài phạm vi → chặn sạch", isinstance(e, GiaoError) and "NGOÀI phạm vi" in e.msg, f"e={e}")

cấp_chạy = lambda rt: rt.cấp_quyền("chạy", lệnh=["python --version"])
out, e = chạy('rọi chạy("git", ["push"])', cấp=cấp_chạy)         # lệnh ngoài allowlist
kiểm("chạy ngoài allowlist → chặn", isinstance(e, GiaoError) and "trong danh sách" in e.msg, f"e={e}")

out, e = chạy('ghi_tệp("x.txt","hi")', cấp=cấp_đọc)              # chỉ cấp đọc, không cấp ghi
kiểm("chỉ cấp đọc → ghi_tệp vẫn không tồn tại", isinstance(e, GiaoError) and "chưa định nghĩa" in e.msg, f"e={e}")

out, e = chạy('rọi đọc_tệp("chuẩn.giao")')                       # mặc định vẫn sandbox
kiểm("mặc định KHÔNG quyền (sandbox nguyên vẹn)", isinstance(e, GiaoError) and "chưa định nghĩa" in e.msg, f"e={e}")

# ---------- 10. VÒNG DUYỆT `lặp ... trong` (gỡ trần đệ quy) ----------
print("\n[10] lặp ... trong — duyệt dữ liệu KHÔNG đệ quy")
out, e = chạy('đặt t=0\nlặp x trong [10,20,30] { đặt t = t + x }\nrọi t')
kiểm("for-each cộng dồn = 60", e is None and out.strip()=="60", f"out={out!r} e={e}")

out, e = chạy('đặt n=0\nlặp c trong "giao" { đặt n = n + 1 }\nrọi n')
kiểm("duyệt chuỗi đếm ký tự = 4", e is None and out.strip()=="4", f"out={out!r} e={e}")

out, e = chạy('đặt s=0\nlặp x trong [1,2,3,4,5] { đặt s=s+x  nếu x==3 {dừng} }\nrọi s')
kiểm("dừng trong for-each", e is None and out.strip()=="6", f"out={out!r} e={e}")

# gỡ TRẦN: tách chuỗi DÀI (1200 ký tự) — bản đệ quy cũ sẽ vượt MAX_DEPTH; bản iterative thì không
src_dài = ('đặt s=""\nlặp i trong dải(1200) { đặt s = s + "a" }\n'
           'đặt phần = tách(s + "b" + s, "b")\nrọi dài(phần)\nrọi dài(đầu(phần))')
out, e = chạy(src_dài, chuẩn=True, max_depth=900)
kiểm("tách chuỗi 1200+ ký tự KHÔNG tràn ngăn xếp", e is None and out.split()==["2","1200"], f"out={out!r} e={e}")

out, e = chạy('rọi bản_đồ(hàm(x){trả x+1}, dải(500))', chuẩn=True, max_depth=900)
kiểm("bản_đồ trên 500 phần tử (iterative, không tràn)", e is None and out.strip().startswith("[1, 2, 3"), f"e={e}")

# ---------- 11. BẢN (map/record) — tra cứu O(1) ----------
print("\n[11] bản (map/record)")
out, e = chạy('đặt m=bản()\nđặt_khoá(m,"a",1)\nđặt_khoá(m,"b",2)\nrọi lấy_khoá(m,"a")')
kiểm("đặt_khoá/lấy_khoá", e is None and out.strip()=="1", f"out={out!r} e={e}")

out, e = chạy('đặt m=bản()\nđặt_khoá(m,"x",9)\nrọi m["x"]')
kiểm("index m[khoá]", e is None and out.strip()=="9", f"out={out!r} e={e}")

out, e = chạy('đặt m=bản()\nrọi lấy_khoá(m,"vắng")')
kiểm("thiếu khoá → ẩn (ba-trị)", e is None and out.strip()=="ẩn", f"out={out!r} e={e}")

out, e = chạy('đặt m=bản()\nđặt_khoá(m,"a",1)\nrọi có_khoá(m,"a")\nrọi có_khoá(m,"z")')
kiểm("có_khoá → sáng/tối", e is None and out.split()==["sáng","tối"], f"out={out!r} e={e}")

out, e = chạy('đặt m=bản()\nđặt_khoá(m,"a",1)\nđặt_khoá(m,"b",2)\nđặt t=0\nlặp k trong m { đặt t = t + lấy_khoá(m,k) }\nrọi t')
kiểm("lặp trong bản (duyệt khoá) + tra giá trị", e is None and out.strip()=="3", f"out={out!r} e={e}")

out, e = chạy('đặt m=bản()\nđặt_khoá(m,"a",1)\nđặt_khoá(m,"a",5)\nrọi m["a"]\nrọi dài(m)')
kiểm("mutate tại chỗ + dài", e is None and out.split()==["5","1"], f"out={out!r} e={e}")

out, e = chạy('đặt m=bản()\nrọi đặt_khoá(m,[1],9)')        # khoá danh sách → lỗi sạch
kiểm("khoá không hợp lệ → lỗi sạch", isinstance(e, GiaoError) and "khoá" in e.msg, f"e={e}")

# ---------- 12. MODULE `nhập` ----------
print("\n[12] nhập (module)")
out, e = chạy('nhập "examples/lib_hinh.giao"\nrọi vuông(6)')
kiểm("nhập module → hàm sẵn dùng", e is None and out.strip()=="36", f"out={out!r} e={e}")
out, e = chạy('nhập "examples/lib_hinh.giao"\nnhập "examples/lib_hinh.giao"\nrọi PI100')
kiểm("nhập lần 2 idempotent (không lỗi)", e is None and out.strip()=="314", f"out={out!r} e={e}")
out, e = chạy('nhập "../../etc/passwd.giao"')
kiểm("chặn thoát cây dự án (..)", isinstance(e, GiaoError) and "NGOÀI" in e.msg, f"e={e}")
out, e = chạy('nhập "khong_co_that.giao"')
kiểm("nhập tệp không tồn tại → lỗi sạch", isinstance(e, GiaoError) and "nhập" in e.msg, f"e={e}")

# ---------- 13. CLOSURE TỪ VỰNG (lexical scope) ----------
print("\n[13] closure lexical (bắt môi trường ĐỊNH NGHĨA)")
out, e = chạy('hàm thêm(n){ trả hàm(x){ trả x+n } }\nđặt a=thêm(5)\nđặt b=thêm(10)\nrọi a(100)\nrọi b(100)')
kiểm("closure curry giữ biến riêng (105/110)", e is None and out.split()==["105","110"], f"out={out!r} e={e}")

out, e = chạy('đặt x="ngoài"\nhàm tạo(){ trả hàm(){ trả x } }\nhàm gọi(f){ đặt x="trong"  trả f() }\nrọi gọi(tạo())')
kiểm("KHÔNG bị dynamic-scope (ra 'ngoài')", e is None and out.strip()=="ngoài", f"out={out!r} e={e}")

out, e = chạy('hàm đếm(){ trả 0 }\nhàm gt(n){ nếu n==0 {trả 1} trả n*gt(n-1) }\nrọi gt(5)')
kiểm("đệ quy vẫn đúng (giai thừa 5=120)", e is None and out.strip()=="120", f"out={out!r} e={e}")

out, e = chạy('hàm a(x){ trả hàm(y){ trả hàm(z){ trả x+y+z } } }\nrọi a(1)(20)(300)')
kiểm("closure LỒNG 3 tầng (lexical) = 321", e is None and out.strip()=="321", f"out={out!r} e={e}")

out, e = chạy('đặt m=bản()\nđặt_khoá(m,1,"một")\nđặt_khoá(m,2,"hai")\nrọi m[1]\nrọi dài(m)')
kiểm("map khoá SỐ + index", e is None and out.split()==["một","2"], f"out={out!r} e={e}")

# ---------- 13b. PHÉP BIT (A1) + GÁN THEO CHỈ MỤC (A2) ----------
print("\n[13b] phép bit (A1) + gán theo chỉ mục (A2)")
out, e = chạy('rọi xor(12,10)\nrọi và_bit(12,10)\nrọi hoặc_bit(12,10)\nrọi dịch_trái(1,10)\nrọi dịch_phải(1024,3)\nrọi đảo_bit(5)')
kiểm("bit: xor/và/hoặc/dịch/đảo", e is None and out.split()==["6","8","14","1024","128","-6"], f"out={out!r} e={e}")
out, e = chạy('rọi xor(5, ẩn)\nrọi dịch_trái(ẩn, 3)')
kiểm("bit ba-trị: đối ẩn → ẩn", e is None and out.split()==["ẩn","ẩn"], f"out={out!r} e={e}")
out, e = chạy('rọi dịch_trái(1, 0-2)')
kiểm("dịch số bit âm → lỗi sạch", isinstance(e, GiaoError) and "≥ 0" in e.msg, f"e={e}")
out, e = chạy('đặt ds=[1,2,3]\nđặt ds[1]=99\nrọi ds\nđặt l=[[1,2],[3,4]]\nđặt l[0][1]=7\nrọi l[0]')
kiểm("đặt ds[i]=x sửa TẠI CHỖ (cả lồng)", e is None and "[1, 99, 3]" in out and "[1, 7]" in out, f"out={out!r} e={e}")
out, e = chạy('đặt m=bản()\nđặt m["k"]=5\nrọi m["k"]')
kiểm("đặt bản[khoá]=x ≡ đặt_khoá", e is None and out.strip()=="5", f"out={out!r} e={e}")
out, e = chạy('đặt ds=[1]\nđặt i=ẩn\nđặt ds[i]=9\nrọi ds')
kiểm("chỉ mục ẩn → KHÔNG ghi (no-op)", e is None and out.strip()=="[1]", f"out={out!r} e={e}")
out, e = chạy('đặt ds=[1]\nđặt ds[7]=9')
kiểm("ngoài phạm vi → lỗi sạch", isinstance(e, GiaoError) and "ngoài phạm vi" in e.msg, f"e={e}")
out, e = chạy('đặt c="abc"\nđặt c[0]="z"')
kiểm("chuỗi bất biến → lỗi sạch", isinstance(e, GiaoError) and "BẤT BIẾN" in e.msg, f"e={e}")

# ---------- 13c. BẪY thêm/gom (A3) ----------
print("\n[13c] bẫy thêm/gom (A3): vứt kết quả 'thêm' → lỗi sạch")
out, e = chạy('đặt ds=[1]\nthêm(ds, 2)\nrọi ds')
kiểm("thêm(ds,x) đứng một mình → lỗi sạch có gợi ý gom", isinstance(e, GiaoError) and "gom" in e.msg, f"e={e}")
out, e = chạy('đặt ds=[1]\nđặt ds=thêm(ds, 2)\nrọi ds')
kiểm("đặt ds=thêm(...) vẫn hợp lệ", e is None and out.strip()=="[1, 2]", f"out={out!r} e={e}")
out, e = chạy('hàm thêm(a,b){ trả 7 }\nthêm(1,2)\nrọi "ok"')
kiểm("người dùng TỰ định nghĩa 'thêm' → không đụng tới", e is None and out.strip()=="ok", f"out={out!r} e={e}")

# ---------- 14. THÔNG ĐIỆP LỖI: cột + gợi ý ----------
print("\n[14] lỗi: vị trí cột + gợi ý 'có phải…?'")
out, e = chạy('đặt số_lượng=1\nrọi số_luong')
kiểm("lỗi mang CỘT", isinstance(e, GiaoError) and e.col == 5, f"col={getattr(e,'col',None)}")
kiểm("gợi ý tên gần đúng", isinstance(e, GiaoError) and "có phải 'số_lượng'" in e.msg, f"msg={getattr(e,'msg','')}")
from giao import GiaoSyntax
out, e = chạy('rọi 1 @ 2')
kiểm("cú pháp mang dòng+cột", isinstance(e, GiaoSyntax) and e.line==1 and e.col==7, f"e={getattr(e,'line',None)}:{getattr(e,'col',None)}")

print("\n" + "="*64)
print(f"KẾT QUẢ: {TỔNG - RỚT}/{TỔNG} đạt" + ("" if RỚT == 0 else f"  — {RỚT} RỚT"))
print("="*64)
sys.exit(1 if RỚT else 0)

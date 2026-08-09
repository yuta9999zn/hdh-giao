# -*- coding: utf-8 -*-
"""
kiem_kho_xa.py — nghiệm thu KHO PHẦN MỀM QUA MẠNG (CÒN_THIẾU I2)
================================================================================
Điều phải chứng minh KHÔNG phải "tải về được", mà là **tải về thì chưa tin**:
  • mục lục tải qua mạng chỉ được ghi xuống khi ĐÚNG CHỮ KÝ của khoá ĐÃ NEO trên máy;
  • sửa MỘT ký tự trên đường ⇒ chữ ký gãy ⇒ KHÔNG ghi byte nào;
  • kho ký bằng KHOÁ KHÁC (kho giả mạo) ⇒ từ chối, dù mục lục hợp lệ và băm gói đúng;
  • thân gói tải về phải khớp BĂM trong mục lục đã ký thì mới được ghi;
  • gói xa đòi năng lực nhạy cảm vẫn phải ĐỒNG Ý tường minh.

    python kiem_kho_xa.py
"""
import os, sys, time, socket, shutil, subprocess, hashlib

P = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
PY = sys.executable
CỔNG = 2281
KHO = os.path.join(P, "kho_xa")

tổng = rớt = 0
def ca(tên, điều_kiện, ct=""):
    global tổng, rớt; tổng += 1
    print(f"  {'✓' if điều_kiện else '✗'} {tên}" + ("" if điều_kiện else f"   ← {ct}"))
    if not điều_kiện: rớt += 1


def chạy_giao(mã, *cờ):
    t = os.path.join(P, "_kiem_kho_xa_tam.giao")
    with open(t, "w", encoding="utf-8") as f: f.write(mã)
    try:
        r = subprocess.run([PY, "giao.py", t, "--bước", "900000000", *cờ], capture_output=True,
                           text=True, env=ENV, cwd=P, encoding="utf-8", timeout=300)
        return (r.stdout or "") + (r.stderr or "")
    finally:
        try: os.remove(t)
        except OSError: pass


def _nền(neo_khoá):
    """Mã GIAO dựng một máy sạch, neo `neo_khoá` làm khoá tin cậy, khai kho xa."""
    return f'''
nhập "lib_vỏ.giao"
đặt M = khởi_máy()
thêm_người(M, 0, "gốc")  thêm_người(M, 1000, "an")
đặt K = sinh_tt(M, "khởi", 0, 0, "/")
gọi(M, K, GH_TẠO_THƯ, ["/hệ", 755])       gọi(M, K, GH_TẠO_THƯ, ["/nhà", 755])
gọi(M, K, GH_TẠO_THƯ, ["/lệnh", 755])     gọi(M, K, GH_TẠO_THƯ, ["/thùng_rác", 777])
gọi(M, K, GH_TẠO_THƯ, ["/hệ/kho", 755])   gọi(M, K, GH_TẠO_THƯ, ["/hệ/kho/gói", 755])
gọi(M, K, GH_TẠO_THƯ, ["/nhà/an", 755])   gọi(M, K, GH_TẠO_THƯ, ["/nhà/an/lệnh", 755])
gọi(M, K, GH_ĐỔI_CHỦ, ["/nhà/an", 1000])  duyệt(M)
gọi(M, K, GH_ĐỔI_CHỦ, ["/nhà/an/lệnh", 1000])  duyệt(M)
cài_lệnh(M, K)                            # ~ /bin: có sẵn `nói`, `tôi`… để kịch bản gói chạy được
gọi(M, K, GH_TẠO, ["/hệ/đường_lệnh", 644, "/lệnh:/nhà/an/lệnh"])
gọi(M, K, GH_TẠO, ["/hệ/gói_đã_cài", 644, ""])
gọi(M, K, GH_TẠO, ["/hệ/kho/khoá_công", 644, "{neo_khoá}"])
gọi(M, K, GH_TẠO, ["/hệ/kho/nguồn", 644, "kho-xa|/hệ/kho/mục_lục|/hệ/kho/mục_lục.ký|/hệ/kho/khoá_công"])
gọi(M, K, GH_TẠO, ["/hệ/kho/nguồn_xa", 644, "kho-xa|127.0.0.1|{CỔNG}"])
đặt V = gọi(M, K, GH_SINH, ["vỏ", 5])
đặt_khoá(lấy_khoá(lấy_khoá(M, "cred"), V), "uid", 1000)
đặt_khoá(lấy_khoá(lấy_khoá(M, "cred"), V), "thư", "/nhà/an")
'''


print("=" * 68); print("NGHIỆM THU KHO PHẦN MỀM QUA MẠNG (I2)"); print("=" * 68)

with open(os.path.join(KHO, "khoa_cong.txt"), encoding="utf-8") as f:
    khoá_thật = f.read().strip()
n_thật = khoá_thật.split("|")[2]
vân_thật = hashlib.sha256(n_thật.encode()).hexdigest()[:16]

mc = subprocess.Popen([PY, "-u", "chay_kho_xa.py", "--cổng", str(CỔNG), "--im"],
                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                      env=ENV, cwd=P, encoding="utf-8", text=True)
try:
    sẵn = False
    t0 = time.time()
    while time.time() - t0 < 40:
        try:
            s = socket.create_connection(("127.0.0.1", CỔNG), timeout=1); s.close(); sẵn = True; break
        except OSError:
            time.sleep(0.4)
    print("\n[1] Kho ở ngoài lên, HĐH tải mục lục về")
    ca("máy chủ kho nghe được", sẵn)

    o = chạy_giao(_nền(khoá_thật) + '''
rọi "-- người thường KHÔNG tự đổi được mục lục CHUNG (như `apt update` cần root) --"
rọi kho_tải_mục_lục(M, V)[1]
rọi "-- gốc-quyền tải mục lục về cho cả máy --"
đặt r = kho_tải_mục_lục(M, K)
rọi r[0]
rọi r[1]
rọi "gói thấy được: " + dài(kho_mục_lục(M, V))
rọi "-- cài gói TẢI VỀ TỪ MẠNG (thân gói cũng tải, kiểm băm rồi mới ghi) --"
đặt c = kho_cài(M, V, "soi_mạng", tối)
rọi c[0]
lặp d trong c[1] { rọi d }
rọi "-- chạy thử lệnh vừa tải về --"
rọi chạy_dòng_im(M, V, "chào_xa")[1]
rọi "-- gói xa ĐÒI năng lực nhạy cảm vẫn phải ĐỒNG Ý --"
rọi kho_cài(M, V, "dao_xa", tối)[1]
''', "--cho-mạng", str(CỔNG))
    ca("★★ người thường không tự đổi mục lục CHUNG — nói rõ phải dùng gốc-quyền",
       "cập nhật mục lục chung cần gốc-quyền" in o, o[:400])
    ca("★★ tải mục lục về và KIỂM CHỮ KÝ xong", "đã tải và KIỂM CHỮ KÝ xong: 3 gói" in o, o[-200:])
    ca("★ vân tay khoá đúng khoá đã neo", vân_thật in o, o[-200:])
    ca("★★★ cài được gói TẢI TỪ MẠNG: phụ thuộc kéo theo, thân gói tải + kiểm băm rồi mới ghi",
       "✓ chào_xa 1.0 (cần vì 'soi_mạng' cần chào_xa)" in o and "✓ soi_mạng 1.1" in o, o[-300:])
    ca("★★ lệnh tải từ mạng CHẠY được thật", "chào từ kho xa!" in o and "an (uid 1000)" in o)
    ca("★ gói xa đòi năng lực nhạy cảm vẫn phải đồng ý tường minh",
       "NĂNG LỰC NHẠY CẢM: dao_xa→xoá" in o)

    print("\n[2] ★★★ Tải về thì CHƯA TIN — hai phép thử phủ định")
    # ① sửa MỘT ký tự trong mục lục trên máy chủ kho
    ml = os.path.join(KHO, "mục_lục")
    with open(ml, encoding="utf-8") as f: gốc = f.read()
    with open(ml, "w", encoding="utf-8") as f: f.write(gốc.replace("chào một tiếng", "chào một tiếnh"))
    o = chạy_giao(_nền(khoá_thật) + '''
đặt r = kho_tải_mục_lục(M, V)
rọi r[0]
rọi r[1]
rọi "mục lục ghi xuống máy chưa? " + loại(gọi(M, V, GH_ĐỌC, ["/hệ/kho/mục_lục"]))
''', "--cho-mạng", str(CỔNG))
    ca("★★★ SỬA MỘT KÝ TỰ trên đường → chữ ký gãy, TỪ CHỐI",
       "CHỮ KÝ KHÔNG KHỚP" in o and "KHÔNG ghi gì cả" in o, o[-200:])
    ca("★★★ và thật sự KHÔNG ghi byte nào xuống máy", "mục lục ghi xuống máy chưa? ẩn" in o, o[-200:])
    with open(ml, "w", encoding="utf-8") as f: f.write(gốc)

    # ② kho GIẢ MẠO: mục lục hợp lệ, băm đúng, nhưng máy neo khoá KHÁC
    with open(os.path.join(P, "khoa_cong.txt"), encoding="utf-8") as f:
        khoá_khác = f.read().strip()
    o = chạy_giao(_nền(khoá_khác) + '''
đặt r = kho_tải_mục_lục(M, V)
rọi r[0]
rọi r[1]
rọi "mục lục ghi xuống máy chưa? " + loại(gọi(M, V, GH_ĐỌC, ["/hệ/kho/mục_lục"]))
''', "--cho-mạng", str(CỔNG))
    ca("★★★ kho ký bằng KHOÁ KHÁC → từ chối, dù mục lục hợp lệ và băm gói đúng",
       "CHỮ KÝ KHÔNG KHỚP" in o and "không phải kho bạn neo" in o, o[-200:])
    ca("★★★ cũng KHÔNG ghi gì (an toàn nằm ở NEO TIN CẬY)",
       "mục lục ghi xuống máy chưa? ẩn" in o, o[-200:])

    print("\n[3] Sandbox: chưa cấp năng lực mạng thì không ra ngoài được")
    o = chạy_giao(_nền(khoá_thật) + '''
đặt r = kho_tải_mục_lục(M, V)
rọi r[0]
rọi r[1]
''')
    ca("★★ chưa cấp `mạng_host` → nói rõ, không lặng lẽ hỏng",
       "chưa được cấp năng lực" in o and "mạng_host" in o, o[-200:])
finally:
    mc.terminate()
    try: mc.wait(timeout=10)
    except subprocess.TimeoutExpired: mc.kill()

print("\n" + "=" * 68)
print(f"KHO QUA MẠNG: {tổng - rớt}/{tổng} hạng mục đạt" + ("" if rớt == 0 else f"  — {rớt} RỚT"))
print("=" * 68)
sys.exit(1 if rớt else 0)

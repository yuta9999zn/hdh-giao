# -*- coding: utf-8 -*-
"""
kiem_de.py — nghiệm thu BÀN LÀM VIỆC (desktop) của HĐH-GIAO
================================================================================
Điều phải chứng minh KHÔNG phải "giao diện hiện ra đẹp", mà là:
  • bàn làm việc chạy trên NHÂN THẬT (lệnh gõ trên giao diện = lệnh gõ ở vỏ);
  • giao diện KHÔNG có cửa hậu — quyền rwx/uid/nhóm chặn y hệt;
  • cổng BẤT-KHẢ-HỒI vẫn giữ việc lại → giao diện phải hiện hộp phê duyệt;
  • KHOÁ PHIÊN chặn lời gọi từ nơi khác (không có khoá ⇒ 403).

    python kiem_de.py
"""
import os, sys, json, threading, urllib.request, urllib.error

P = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, P)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import giao_de
from http.server import ThreadingHTTPServer

tổng = rớt = 0
def ca(tên, điều_kiện, ct=""):
    global tổng, rớt; tổng += 1
    print(f"  {'✓' if điều_kiện else '✗'} {tên}" + ("" if điều_kiện else f"   ← {ct}"))
    if not điều_kiện: rớt += 1

print("=" * 68); print("NGHIỆM THU BÀN LÀM VIỆC HĐH-GIAO"); print("=" * 68)

máy_chủ = ThreadingHTTPServer(("127.0.0.1", 0), giao_de.Tay)
CỔNG = máy_chủ.server_address[1]
threading.Thread(target=máy_chủ.serve_forever, daemon=True).start()
GỐC = f"http://127.0.0.1:{CỔNG}"

def api(việc, khoá=None, **thêm):
    thân = json.dumps({"việc": việc, **thêm}).encode("utf-8")
    yc = urllib.request.Request(GỐC + "/api", data=thân,
                                headers={"Content-Type": "application/json",
                                         "X-Giao-Khoa": giao_de.KHOÁ if khoá is None else khoá})
    try:
        with urllib.request.urlopen(yc, timeout=120) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, {}

print("\n[1] Máy chủ khung hình: tệp tĩnh + KHOÁ PHIÊN")
with urllib.request.urlopen(GỐC + "/", timeout=30) as r:
    trang = r.read().decode("utf-8")
ca("phục vụ được trang bàn làm việc", "HĐH-GIAO · Bàn làm việc" in trang)
ca("trang KHÔNG nạp gì từ mạng ngoài (tự chứa)",
   "http://" not in trang.replace("http://www.w3.org", "") and "cdn" not in trang.lower())
mã, _ = api("trạng", khoá="sai-khoá")
ca("★ sai KHOÁ PHIÊN → 403 (trang web lạ không gọi lén được)", mã == 403)
mã, _ = api("trạng", khoá="")
ca("thiếu khoá → 403", mã == 403)

print("\n[2] Chưa đăng nhập thì chưa có gì")
_, t = api("trạng")
ca("trạng thái nói rõ CHƯA vào", t.get("đã_vào") is False)
_, r = api("lệnh", dòng="tôi")
ca("★ gõ lệnh khi chưa đăng nhập → từ chối", r.get("lỗi") == "chưa đăng nhập")
_, r = api("vào", tên="an", mk="sai-bét")
ca("★ sai mật khẩu → không vào được", r.get("ok") is False)
ca("★ KHÔNG chỉ điểm sai TÊN hay sai MẬT KHẨU",
   "Sai tên đăng nhập hoặc mật khẩu." == r.get("lý_do"))

print("\n[3] Đăng nhập thật — cùng sổ người dùng với vỏ dòng lệnh")
_, r = api("vào", tên="an", mk="an")
ca("vào được bằng an/an", r.get("ok") is True, str(r))
_, t = api("trạng")
ca("phiên chạy dưới đúng uid 1000", t.get("uid") == 1000 and t.get("tên") == "an")
ca("dấu nhắc do chính HĐH sinh", str(t.get("nhắc", "")).startswith("an:/nhà/an$"))

print("\n[4] ★★ Giao diện chạy trên NHÂN THẬT (không mô phỏng)")
_, r = api("lệnh", dòng="tôi")
ca("lệnh `tôi` trả đúng danh tính", "an (uid 1000)" in r.get("ra", ""))
_, r = api("lệnh", dòng="xem /hệ/nhật_ký")
ca("đọc được tệp thật của hệ", "đĩa: /tạm đầy 91%" in r.get("ra", ""))
_, r = api("lệnh", dòng="người | đếm")
ca("ống lệnh vẫn chạy qua giao diện", r.get("ra", "").strip().isdigit())
_, r = api("lệnh", dòng='nói "chào từ bàn làm việc" > /nhà/an/ghi_chú')
_, r = api("lệnh", dòng="xem /nhà/an/ghi_chú")
ca("tạo tệp từ giao diện → tệp có thật trong hệ", "chào từ bàn làm việc" in r.get("ra", ""))

print("\n[5] ★★★ KHÔNG CÓ CỬA HẬU — quyền chặn giao diện y hệt dòng lệnh")
_, r = api("lệnh", dòng="xem /hệ/mật_khẩu")
ca("★ 'an' vẫn KHÔNG đọc nổi /hệ/mật_khẩu (600)", "cấm đọc /hệ/mật_khẩu" in r.get("ra", ""))
_, r = api("thư_mục", đường="/nhà/an")
ca("ứng dụng Tệp liệt kê được nhà mình", any(m["tên"] == "ghi_chú" for m in r.get("mục", [])))
ca("ứng dụng Tệp mang đủ quyền/chủ/cỡ (đi qua GH_SOI)",
   all(k in (r.get("mục") or [{}])[0] for k in ("quyền", "chủ", "cỡ")))
_, r = api("thư_mục", đường="/không-có-thư-mục-này")
ca("đường không có → báo thiếu, không bịa", "không có" in str(r.get("lỗi", "")))

print("\n[6] ★★★ CỔNG BẤT-KHẢ-HỒI hiện ra trên giao diện")
_, r = api("lệnh", dòng="xoá /tạm/rác1")
ca("★ xoá bị GIỮ LẠI, không làm ngay", "CẦN PHÊ DUYỆT" in r.get("ra", ""))
ca("★★ trạng thái mang việc-đang-chờ để bàn làm việc bật hộp phê duyệt",
   "xoá(/tạm/rác1)" in str(r.get("chờ_duyệt")))
_, r = api("lệnh", dòng="duyệt")
ca("phê duyệt xong thì việc mới chạy", "đã phê duyệt và thực hiện" in r.get("ra", ""))
_, r = api("lệnh", dòng="liệt /tạm")
ca("xoá có hiệu lực thật (rác1 mất, rác2 còn)",
   "rác2" in r.get("ra", "") and "rác1" not in r.get("ra", ""))
_, t = api("trạng")
ca("hết việc chờ → hộp phê duyệt tắt", t.get("chờ_duyệt") is None)

print("\n[7] Nhóm · sudo · mạng · audit đều soi được từ giao diện")
_, r = api("lệnh", dòng="nhóm")
ca("ứng dụng Người & Nhóm đọc được sổ nhóm (C2)", "văn" in r.get("ra", ""))
_, r = api("lệnh", dòng="xem /tb/mạng")
ca("ứng dụng Mạng đọc được /tb/mạng (B1)", "nghe cổng:" in r.get("ra", ""))
_, r = api("lệnh", dòng="nhật_ký 60")
ca("ứng dụng Nhật ký thấy audit ghi ĐÚNG việc vừa làm (xoá + đọc /tb/mạng, dưới tt của phiên)",
   "xoá  /tạm/rác1" in r.get("ra", "") and "đọc  /tb/mạng" in r.get("ra", ""))
_, r = api("lệnh", dòng="nhờ xem nhật ký hệ thống có gì bất thường không")
ca("★ trợ lý chạy trong giao diện, có nêu γ", "cộng hưởng:" in r.get("ra", ""))

print("\n[8] ★★ Trình SOẠN THẢO: đọc/ghi qua đúng gọi-hệ (nhóm G)")
_, r = api("ghi", đường="/nhà/an/bài_thơ", nội="sen vàng nở sớm\nmùa thu Hà Nội")
ca("ghi tệp mới từ trình soạn thảo", r.get("ok") is True, str(r)[:120])
_, r = api("đọc", đường="/nhà/an/bài_thơ")
ca("đọc lại đúng nguyên văn (kể cả xuống dòng)", r.get("nội") == "sen vàng nở sớm\nmùa thu Hà Nội")
_, r = api("ghi", đường="/nhà/an/bài_thơ", nội="đã sửa")
_, r = api("đọc", đường="/nhà/an/bài_thơ")
ca("ghi đè tệp đã có", r.get("nội") == "đã sửa")
_, r = api("đọc", đường="/hệ/mật_khẩu")
ca("★★★ QUYỀN vẫn chặn trình soạn thảo: 'an' KHÔNG đọc nổi /hệ/mật_khẩu",
   "cấm đọc" in str(r.get("lỗi", "")), str(r)[:120])
_, r = api("ghi", đường="/hệ/cửa_sau", nội="hack")
ca("★★★ và KHÔNG ghi nổi vào /hệ", r.get("ok") is not True and "lỗi" in r, str(r)[:120])
_, r = api("đọc", đường="/nhà/an/không-hề-có")
ca("tệp không có → báo thiếu, không bịa", "lỗi" in r)

print("\n[9] ★★ Ứng dụng Tệp: TẠO tệp/thư mục & CHÉP ngay trong cửa sổ (đuôi nhóm G)")
# Giao diện gọi đúng các lệnh vỏ `tạothư`/`sờ`/`chép` — nghiệm ở đây bằng chính đường ấy.
_, r = api("lệnh", dòng="tạothư /nhà/an/góc")
_, r = api("lệnh", dòng="sờ /nhà/an/góc/nháp")
_, r = api("thư_mục", đường="/nhà/an/góc")
ca("★ tạo thư mục + tạo tệp mới từ cửa sổ Tệp → có thật trong hệ",
   any(m["tên"] == "nháp" for m in r.get("mục", [])), str(r)[:120])
_, r = api("lệnh", dòng="chép /nhà/an/bài_thơ /nhà/an/góc/bài_thơ_sao")
_, r = api("lệnh", dòng="xem /nhà/an/góc/bài_thơ_sao")
ca("★★ `chép` (GH_CHÉP) ra bản sao đúng nội dung", "đã sửa" in r.get("ra", ""), str(r)[:120])
_, r = api("lệnh", dòng="xem /nhà/an/bài_thơ")
ca("tệp gốc không suy suyển", "đã sửa" in r.get("ra", ""))
_, r = api("lệnh", dòng="chép /nhà/an/bài_thơ /nhà/an/góc/bài_thơ_sao")
ca("★★ chép KHÔNG đè lên thứ đã có", "KHÔNG đè" in r.get("ra", ""))
_, r = api("lệnh", dòng="chép /hệ/mật_khẩu /nhà/an/trộm")
ca("★★★ QUYỀN vẫn chặn: 'an' không chép nổi /hệ/mật_khẩu ra ngoài",
   "không chép được /hệ/mật_khẩu" in r.get("ra", ""))

print("\n[10] Đăng xuất")
_, r = api("ra")
_, t = api("trạng")
ca("đăng xuất → phiên đóng", t.get("đã_vào") is False)
_, r = api("lệnh", dòng="tôi")
ca("sau đăng xuất KHÔNG gõ được nữa", r.get("lỗi") == "chưa đăng nhập")

máy_chủ.shutdown()
print("\n" + "=" * 68)
print(f"BÀN LÀM VIỆC: {tổng - rớt}/{tổng} hạng mục đạt" + ("" if rớt == 0 else f"  — {rớt} RỚT"))
print("=" * 68)
sys.exit(1 if rớt else 0)

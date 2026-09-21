# -*- coding: utf-8 -*-
"""
kiem_hdh_giao.py — NGHIỆM THU HĐH-GIAO LỐI LINUX (hệ-tệp · quyền · gọi-hệ · vỏ · trợ lý AI)
================================================================================
Kiểm ĐÚNG những bất-biến của một HĐH, không chỉ "chạy không lỗi":
  • cây "/" + mọi thứ là tệp (procfs /tt, devfs /tb)      • quyền rwx + uid có hiệu lực thật
  • ba-trị errno: sáng = xong · tối = cấm · ẩn = không có • cổng BẤT-KHẢ-HỒI chặn tới khi `duyệt`
  • vỏ: ống | · chuyển hướng > · nối &&                   • trợ lý AI: γ-cổng, từ chối khi chưa hiểu,
                                                            KHÔNG có cửa hậu (bị quyền chặn y hệt người)
    python kiem_hdh_giao.py
"""
import os, re, sys, subprocess

P = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
PY = sys.executable

def chạy(args):
    r = subprocess.run([PY] + args, capture_output=True, text=True, env=ENV, cwd=P, encoding="utf-8")
    return r.returncode, (r.stdout or "") + (r.stderr or "")

tổng = rớt = 0
def ca(tên, điều_kiện, ct=""):
    global tổng, rớt; tổng += 1
    print(f"  {'✓' if điều_kiện else '✗'} {tên}" + ("" if điều_kiện else f"   ← {ct}"))
    if not điều_kiện: rớt += 1

print("=" * 68); print("NGHIỆM THU HĐH-GIAO (lối Linux + trợ lý AI)"); print("=" * 68)

# ---------------- 1. hệ-tệp ----------------
print("\n[1] Hệ-tệp: cây, quyền Unix, ba-trị errno")
mã, o = chạy(["giao.py", "kiem_lib_tệp_hệ.giao"])
ca("chạy sạch", mã == 0, o[-300:])
ca("chủ đọc được tệp 600 của mình", "an:x:1000" in o)
ca("người khác bị TỪ CHỐI (tối)", o.count("tối") >= 5)
ca("đường-dẫn không có → ẩn (không bịa)", "ẩn" in o)
ca("thư-mục 700 chặn người ngoài liệt kê", "[ghi_chú]" in o)
ca("xoá cần quyền GHI trên thư-mục CHA", "-- xoá cần quyền GHI trên THƯ-MỤC CHA --" in o)
ca("chuỗi quyền kiểu ls -l", "rw-rw-rw-" in o and "rw-r--r--" in o)
ca("mknod chỉ dành cho gốc-quyền", "màn_hình" in o)

# ---------------- 2. gọi-hệ ----------------
print("\n[2] Tầng gọi-hệ: danh tính, cổng bất-khả-hồi, procfs, audit")
mã, o = chạy(["giao.py", "kiem_lib_gọi_hệ.giao"])
ca("chạy sạch", mã == 0, o[-300:])
ca("người thường KHÔNG đọc được /hệ/mật_khẩu", "cấm đọc /hệ/mật_khẩu" in o)
ca("người thường KHÔNG tự lên gốc-quyền", "chỉ gốc-quyền mới đổi được danh tính" in o)
ca("đổi_chủ bị giữ lại chờ phê duyệt", "CẦN PHÊ DUYỆT — đổi_chủ" in o)
ca("ghi ổ đĩa (định dạng) bị giữ lại", "CẦN PHÊ DUYỆT — ghi(/tb/đĩa0)" in o)
ca("KHÔNG giết được tiến-trình 1", "KHÔNG giết được tiến-trình 1" in o)
ca("procfs /tt phơi tiến-trình dưới dạng tệp", "sẵn-sàng" in o and "[1, 2]" in o)
ca("giết sau khi duyệt → trạng 'chết'", "chết" in o)
ca("nhật ký audit ghi mọi lời gọi", "sinh, việc_phụ" in o and "đọc, /tt/" in o)

# ---------------- 3. toàn hệ + trợ lý ----------------
print("\n[3] HĐH đầy đủ: boot → đăng nhập → vỏ → trợ lý AI")
mã, o = chạy(["giao.py", "hdh_giao.giao"])
ca("boot + chạy sạch", mã == 0, o[-300:])
ca("dấu nhắc kiểu bash (người:thư$)", "an:/nhà/an$" in o)
ca("cây hệ-tệp có /hệ /nhà /tb /tt /tạm", all(x in o for x in ["hệ/", "nhà/", "tb/", "tt/", "tạm/"]))
ca("thiết bị hiện trong cây (⌁)", "đĩa0 ⌁" in o)
ca("ống | + tìm + đếm", "\n2\n" in o)
ca("chuyển hướng > tạo tệp thật", "việc hôm nay: xem lại nhật ký" in o)
ca("ranh giới quyền: cấm đọc mật khẩu", "xem: cấm đọc /hệ/mật_khẩu" in o)
ca("ranh giới quyền: cấm ghi vào /hệ", "cấm tạo /hệ/cửa_sau" in o)
ca("cổng bất-khả-hồi giữ lệnh xoá", "CẦN PHÊ DUYỆT — xoá(/tạm/rác1)" in o)
ca("duyệt xong thì việc mới chạy", "✔ đã phê duyệt và thực hiện" in o)
ca("★ trợ lý hiểu lời → tự gõ lệnh đúng", "$ xem /hệ/nhật_ký" in o and "đĩa: /tạm đầy 91%" in o)
ca("★ trợ lý nêu γ minh bạch cho mọi lựa chọn", "cộng hưởng:" in o and "%" in o)
ca("★ trợ lý TỪ CHỐI việc bất-khả-hồi", "BẤT KHẢ HỒI — tôi KHÔNG tự làm" in o)
ca("★ trợ lý KHÔNG bịa khi chưa hiểu", "KHÔNG soạn nổi lệnh nào" in o and "thà nói không biết" in o)
ca("★ trợ lý KHÔNG có cửa hậu — bị quyền chặn y hệt người",
   "✗ xem: cấm đọc /hệ/mật_khẩu" in o and "tôi không lách quyền của bạn" in o)
ca("nhật ký audit ghi cả lời nhờ trợ lý", "nhờ  kiểm tra giúp tôi tệp mật khẩu" in o)

# ---------------- 4. vỏ tương tác (chế độ kịch bản) ----------------
print("\n[4] Vỏ tương tác: python chay_hdh_giao.py <kịch bản>")
mã, o = chạy(["chay_hdh_giao.py", "kich_ban_thu.txt"])
ca("chạy sạch", mã == 0, o[-300:])
ca("nối lệnh &&", "ghi chú thử" in o)
ca("trợ lý làm việc trong phiên tương tác", "tôi TỰ SOẠN" in o or "✓ chọn" in o)
ca("phiên đóng bằng `thoát`", "tạm biệt" in o)

# ---------------- 5. tiến trình THẬT dưới bộ lập lịch ----------------
print("\n[5] ★ `sinh` chạy CHƯƠNG TRÌNH THẬT: đa nhiệm, chặn/đánh-thức, vòng đời")
mã, o = chạy(["giao.py", "hdh_tiến_trình.giao"])
ca("chạy sạch", mã == 0, o[-300:])
ca("dịch vụ nền tự vào trạng 'chặn' (ngủ, không đốt CPU)", "tt2 nhật_ký_hệ=chặn" in o)
ca("hai tiến trình chạy XEN KẼ (không phải tuần tự)",
   "tt5 đếm → tiếp" in o and "tt4 đếm → tiếp" in o and o.index("tt5 đếm") < o.rindex("tt4 đếm"))
ca("mỗi tiến trình có vùng nhớ riêng (đếm độc lập)", "tệp A: [1 2 3 4 ]" in o and "tệp B: [1 2 3 ]" in o)
ca("IPC `gửi` ĐÁNH THỨC tiến trình đang chặn", "đĩa /tạm sắp đầy" in o and "mạng chập chờn" in o)
ca("dịch vụ ghi xong lại ngủ tiếp", o.count("nhật_ký_hệ → chặn") >= 2)
ca("tiến trình ghi được ra thiết bị", "[màn] xin chào từ tiến trình (2)" in o)
ca("tiến trình đi hỏi hệ-tệp qua gọi-hệ", "rác trong /tạm: 2 mục" in o)
ca("★ tiến trình KẾ THỪA uid — không tạo được cửa hậu", "KHÔNG tồn tại (ẩn)" in o)
ca("★ tiến trình con bị chặn đọc mật khẩu", "cấm đọc /hệ/mật_khẩu" in o)
ca("★ bộ lập lịch KHÔNG giết `khởi` và `vỏ` (tiến trình không có thân)",
   "tt1 khởi=chặn" in o and "tt3 vỏ=chặn" in o)
ca("vòng đời đầy đủ: có tiến trình 'chết' sau khi xong", "đếm=chết" in o and "báo=chết" in o)

print("\n[6] Chạy chương trình TỪ VỎ (chạy · nhịp · việc · kể)")
mã, o = chạy(["chay_hdh_giao.py", "kich_ban_tt.txt"])
ca("chạy sạch", mã == 0, o[-300:])
ca("`việc` liệt kê chương trình cài sẵn", "đếm · nhật_ký_hệ · báo · chào · soi_rác" in o)
ca("`chạy` sinh tiến trình thật", "đã sinh tt5 · đếm" in o)
ca("việc nền tự tiến khi người dùng gõ tiếp", "1 2 3" in o)
ca("`kể` in vết lập lịch", "⟨lịch⟩" in o)
ca("vỏ có vòng đời thật (đang xử lý = 'chạy')", "vỏ  \tchạy" in o)

# ---------------- 7. /lệnh là thư mục lệnh thật ----------------
print("\n[7] ★ /lệnh — lệnh cũng chỉ là TỆP (tra $PATH · bit x · kịch bản · bệ phóng tiến trình)")
mã, o = chạy(["giao.py", "hdh_giao.giao"])
ca("mỗi lệnh vỏ là một tệp trong /lệnh", "liệt /lệnh | đếm" in o and "\n69\n" in o)
ca("tệp lệnh KỊCH BẢN đọc được như văn bản", "# soi_hệ — xem nhanh tình trạng máy" in o)
ca("kịch bản chạy được (nhiều dòng)", "── máy ──" in o and "giao-01" in o)
ca("kịch bản nhận đối số $1", "lỗi đĩa" in o and "đĩa: /tạm đầy 91%" in o)
ca("tệp lệnh làm bệ phóng TIẾN TRÌNH (tiền cảnh: vỏ chờ xong)",
   "tt5 · đếm xong (" in o and "1 2 3" in o)
ca("★ người dùng TỰ VIẾT lệnh mới lúc máy đang chạy", "nhà_tôi" in o)
ca("★ bit x có hiệu lực: khoá lệnh lại là chạy không được",
   "vỏ: cấm chạy /lệnh/xoá — thiếu quyền x" in o)
ca("★ xoá tệp lệnh = mất lệnh", "vỏ: không có lệnh 'cây'" in o)
ca("xoá tệp lệnh vẫn phải qua cổng bất-khả-hồi", "CẦN PHÊ DUYỆT — xoá(/lệnh/cây)" in o)

mã, o = chạy(["chay_hdh_giao.py", "kich_ban_lenh.txt"])
ca("vỏ tương tác: viết lệnh mới rồi chạy ngay", mã == 0 and "xin chào An" in o, o[-300:])

# ---------------- 8. ống liên-tiến-trình thật ----------------
print("\n[8] ★ ỐNG liên-tiến-trình (chặn · đánh thức · phản áp · EOF · quyền)")
mã, o = chạy(["giao.py", "hdh_ống.giao"])
ca("chạy sạch", mã == 0, o[-300:])
ca("ống là TỆP: soi thấy số gói đọng + quyền", "gói đọng (rw-rw-rw-)" in o)
ca("★ PHẢN ÁP: ống đầy thì bên GHI bị chặn", "bơm → chặn" in o)
ca("bên đọc rút bớt thì bên ghi được đánh thức", o.count("bơm → tiếp") >= 3)
ca("★ EOF: đóng đầu ghi ⇒ bên đọc rút hết rồi tự kết thúc",
   "bơm=chết" in o and "hút=chết" in o and "gói 5 lẻ" in o)
ca("ba chặng bơm→lọc→hút qua HAI ống", "gói 2 chẵn" in o and "gói 8 chẵn" in o and "gói 1 lẻ" not in o.split("BA CHẶNG")[1])
ca("ống có QUYỀN: người thường không ghi vào ống 600 của gốc", "cấm ghi ống /ống/kín" in o)
ca("★ đọc ống không ai ghi ⇒ ngủ mãi, nhân KHÔNG quay tít",
   "trạng = chặn" in o and "còn việc sẵn-sàng? tối" in o)
ca("đóng ống là lối thoát khỏi bế tắc", "thấy EOF, kết thúc sạch sẽ" in o)

print("\n[9] Đường ống TỪ VỎ: `bơm | lọc | hút` = 3 tiến trình + `&` chạy nền")
mã, o = chạy(["chay_hdh_giao.py", "kich_ban_ong.txt"])
ca("chạy sạch", mã == 0, o[-300:])
ca("vỏ dựng ĐƯỜNG ỐNG thật (không phải chuyền văn bản)", "đường ống bơm | lọc | hút → tt5 tt6 tt7" in o)
ca("kết quả qua hai ống đúng", "gói 2 chẵn" in o and "gói 6 chẵn" in o)
ca("`&` trả dấu nhắc ngay, tiến trình chạy nền", "[nền]" in o and "bơm  \tsẵn-sàng" in o)
ca("`ống`/`soi` dùng được từ vỏ", "đã tạo ống /ống/thử (sức chứa 2 gói)" in o and "ống  chủ=an" in o)

# ---------------- 10. bền hoá: chụp cả hệ ra JSON ----------------
print("\n[10] ★ BỀN HOÁ: chụp cả hệ điều hành ra JSON → dựng lại → chạy tiếp")
mã, o = chạy(["giao.py", "hdh_bền.giao"])
ca("chạy sạch", mã == 0, o[-300:])
ca("chụp được cả hệ ra MỘT chuỗi JSON", "ảnh chụp dài" in o and '{"phiên_bản":1' in o)
ca("máy cũ bị vứt, chỉ còn chuỗi", "máy cũ: ẩn" in o)
ca("dựng lại được thân tiến trình từ ảnh", "dựng lại 2 thân tiến-trình" in o)
ca("sổ người dùng + hệ-tệp sống lại nguyên vẹn",
   "uid 1000 = an" in o and "giao-01" in o and "lệnh do người dùng viết" in o)
ca("★ tiến trình dở dang CHẠY TIẾP, không làm lại từ đầu",
   "trước khi chạy tiếp: [1 2 3 ]" in o and "sau khi chạy tiếp:  [1 2 3 4 5 6 ]" in o)
ca("ống giữ nguyên gói đang đọng qua lần chụp", "gói còn kẹt trong ống" in o)
ca("việc CHỜ PHÊ DUYỆT vẫn treo sau phục hồi", "việc chờ phê duyệt vẫn treo: xoá(/nhà/an/sổ_tay)" in o)
ca("dịch vụ nền vẫn ngủ, gửi tin là dậy ghi nhật ký", "tin sau khi phục hồi" in o)
ca("nhật ký audit của ĐỜI TRƯỚC còn nguyên", "lời gọi từ ĐỜI TRƯỚC" in o)
ca("round-trip ỔN ĐỊNH: chụp→dựng→chụp ra đúng một ảnh", "ảnh(M2) == ảnh(M3)? sáng" in o)

print("\n[11] Bền hoá QUA HAI LẦN CHẠY (ảnh nằm trên đĩa thật)")
ảnh_kiểm = os.path.join(P, "anh_kiem.json")
if os.path.exists(ảnh_kiểm): os.remove(ảnh_kiểm)
mã1, o1 = chạy(["chay_hdh_giao.py", "kich_ban_ben1.txt", "--lưu", ảnh_kiểm])
ca("phiên 1 chạy sạch + ghi ảnh ra đĩa", mã1 == 0 and os.path.exists(ảnh_kiểm), o1[-200:])
ca("phiên 1 để lại việc đang dở (đếm chưa xong)", "đếm  \tsẵn-sàng" in o1)
mã2, o2 = chạy(["chay_hdh_giao.py", "kich_ban_ben2.txt", "--nạp", ảnh_kiểm])
ca("phiên 2 nạp được ảnh từ đĩa", mã2 == 0 and "nạp ảnh hệ điều hành" in o2, o2[-200:])
ca("tệp của đời trước còn nguyên", "ghi chú đời thứ nhất" in o2)
ca("★ lệnh do người dùng viết ở ĐỜI TRƯỚC vẫn chạy được", "xin chào từ đời trước" in o2)
ca("★ tiến trình đếm dở CHẠY TIẾP ở đời sau (không reset về 1)",
   "1 2 3 4 5 6 7" in o2 and "40" in o2)
if os.path.exists(ảnh_kiểm): os.remove(ảnh_kiểm)

# ---------------- 12. trợ lý TỰ SINH LỆNH ----------------
print("\n[12] ★ TRỢ LÝ TỰ SINH LỆNH (soạn mới · thẩm định · cổng phá huỷ · không bịa)")
mã, o = chạy(["chay_hdh_giao.py", "kich_ban_sinh.txt"])
ca("chạy sạch", mã == 0, o[-300:])
ca("★ soạn được lệnh MỚI ngoài kho kỹ năng", "tôi TỰ SOẠN (mẫu + dò hệ-tệp): $ xem /nhà/an/sổ_tay" in o)
ca("đối tượng lấy từ hệ-tệp THẬT (dò bằng gọi-hệ)", "việc cần làm hôm nay" in o)
ca("chọn ĐÚNG động từ dù câu có nhiều từ khoá", "$ soi /nhà/an/sổ_tay" in o and "cỡ=20" in o)
ca("chọn đối tượng CỤ THỂ NHẤT (mật_khẩu chứ không phải /hệ)", "$ xem /hệ/mật_khẩu" in o)
ca("★ lệnh tự soạn vẫn bị QUYỀN chặn (không cửa hậu)",
   "✗ xem: cấm đọc /hệ/mật_khẩu" in o and "nhân chặn" in o)
ca("★ có PHÁ HUỶ trên bàn ⇒ HỎI LẠI, không tự chọn",
   "$ xoá /tạm/rác1   [BẤT KHẢ HỒI" in o and "KHÔNG đoán bừa" in o)
ca("lệnh có căn cứ THẮNG kỹ năng khớp mơ hồ", "chỉ khớp lửng lơ" in o and "$ liệt /tạm" in o)
ca("★ không soạn được thì NÓI KHÔNG BIẾT, không bịa",
   "KHÔNG soạn nổi lệnh nào" in o and "thà nói không biết" in o)
ca("mọi lệnh tự soạn đều được IN RA trước khi chạy", o.count("tôi TỰ SOẠN") >= 4)
ca("HỢP KIỂU: `xem` một THƯ MỤC tự chỉnh thành `liệt` (không báo 'cấm đọc' lừa người)",
   o.count("$ liệt /tạm") >= 2 and "cấm đọc /tạm" not in o)
ca("đối tượng CÓ THẬT thắng động từ chung chung (nhật ký hệ → tệp /hệ/nhật_ký)",
   "$ xem /hệ/nhật_ký" in o and "khởi: nhân lên" in o)

print("\n[14] ★ LẬP LỊCH γ (CDFL): nhân đo rồi quyết — kẻ tham lam bị bóp")
mã, o = chạy(["giao.py", "hdh_tiền_định.giao"])
ca("chạy sạch", mã == 0, o[-300:])
ca("lịch cổ điển: kẻ tham lam chiếm ~nửa CPU", "tham = 15 lát (50%)" in o)
ca("lịch cổ điển còn BỎ ĐÓI một tiến trình thật", "A = 0" in o)
ca("★ lịch γ bóp kẻ tham lam xuống ~1/6", "tham = 5 lát (16%)" in o)
ca("★ lịch γ KHÔNG bỏ đói ai", "A = 13" in o and "B = 12" in o)
ca("σ học được: tham tụt, việc-thật leo", "tham = 30" in o and "A = 250" in o)
ca("γ của kẻ tham lam là ÂM (đốm tối)", "tham = -0.7" in o)
ca("nhân in được vết học từng lát", "⟨γ⟩ lát 1 · tt2 tham → tiếp  (ρ=tối" in o)

mã, o = chạy(["kiem_lich_gamma.py"])
ca("★ chính sách γ của HĐH ≡ chính sách của MÁY/SILICON (2000 ca)",
   mã == 0 and "2000/2000" in o and "TRÙNG KHÍT" in o, o[-200:])

print("\n[15] ★★ TIỀN ĐỊNH THẬT: thân tiến trình BIÊN DỊCH XUỐNG GVM, nhân CƯỚP CPU")
mã, o = chạy(["giao.py", "hdh_máy.giao", "--cho-máy"])
ca("chạy sạch", mã == 0, o[-300:])
ca("biên dịch được thân tiến trình xuống bytecode + sinh tiến trình MÁY", "tt2 việc_thật" in o)
ca("★ vòng lặp 1.000.000 bước KHÔNG nhường vẫn bị CẮT NGANG (hệ không treo)",
   "tt4 tham_lam → tiếp" in o and o.count("tt4 tham_lam") >= 3)
ca("★ tiến trình có việc thật vẫn TIẾN ĐỀU dù kẻ tham lam đang chạy",
   o.count("việc_thật → tiếp") >= 6)
ca("γ đo đúng: việc-thật ρ=sáng, tham-lam ρ=tối", "việc_thật → tiếp  (ρ=sáng" in o and "tham_lam → tiếp  (ρ=tối" in o)
ca("★ kẻ tham lam bị BÓP: ít lát hơn hẳn hai tiến trình thật",
   "tham_lam  (tt4): 480 lệnh · 4 lát" in o and "· 7 lát" in o)
ca("σ/γ: tham lam thành đốm tối", "tham_lam = 40" in o and "tham_lam = -0.68" in o)
ca("đếm được CPU thật bằng SỐ LỆNH MÁY", "lệnh · 7 lát" in o)

mã, o = chạy(["giao.py", "hdh_máy.giao"])          # KHÔNG cấp năng lực
ca("★ chưa cấp `--cho-máy` thì `biên_dịch` KHÔNG TỒN TẠI (ocap) — HĐH vẫn chạy êm",
   mã == 0 and "Chưa cấp năng lực `máy`" in o, o[-200:])

print("\n[16] ★★ OPCODE GỌI-HỆ: tiến trình MÁY xin việc của nhân (trap như CPU thật)")
mã, o = chạy(["giao.py", "hdh_máy_gọi_hệ.giao", "--cho-máy"])
ca("chạy sạch", mã == 0, o[-300:])
ca("★ máy ĐỌC được chuỗi qua nhân (nhân cấp lên heap của máy)", "gọi_hệ đọc → dữ liệu do NGƯỜI tạo" in o)
ca("★ máy GHI được tệp qua nhân — chép tệp trọn vẹn", "/tạm/bản_sao = [dữ liệu do NGƯỜI tạo]" in o)
ca("★ QUYỀN vẫn chặn mã đã biên dịch", "gọi_hệ đọc → tối" in o and "cấm đọc /hệ/mật_khẩu" in o)
ca("★ CỔNG BẤT-KHẢ-HỒI giữ được cả tiến trình máy", "gọi_hệ xoá → tối" in o and "vẫn còn nguyên" in o)
ca("kẻ tham lam vẫn bị cắt CPU dù có/không gọi-hệ", "tham_máy (tt6)" in o and "σ=12" in o)
ca("tiến trình máy CHĂM CHỈ có σ CAO HƠN hẳn kẻ tham lam", "chăm_máy (tt7)" in o and "σ=142" in o)
ca("nhật ký audit ghi cả lời xin của tiến trình máy", "tt7  thêm  /tạm/bản_sao" in o)

print("\n[17] ★★★ VỎ LỆNH CHẠY BẰNG BYTECODE (vỏ_máy.giao → GVM)")
mã, o = chạy(["chay_vo_may.py"])
ca("chạy sạch", mã == 0, o[-300:])
ca("★ nhân chỉ đưa NGUYÊN DÒNG, vỏ máy tự lo phần còn lại",
   "gọi_hệ lệnh → xem /hệ/tên_máy" in o)
ca("★★ VỎ MÁY TỰ TÁCH TỪ bằng bytecode của chính nó (đếm_từ ra 4)",
   "gọi_hệ lệnh → đếm_từ một hai ba" in o and "[tt3] 4" in o)
ca("★ so sánh CHUỖI trên máy chạy đúng (token tự dựng khớp hằng)", "[tt3] giao-01" in o)
ca("vỏ máy đọc được tệp qua nhân", "[tt3] giao-01" in o)
ca("vỏ máy liệt kê được thư mục", "[tt3] rác ghi_chú" in o)
ca("vỏ máy soi được tệp", "[tt3] tệp rw-r--r--" in o)
ca("vỏ máy GHI được rồi ĐỌC LẠI", "[tt3] xong-rồi" in o and "/tạm/vm_ghi = xong-rồi" in o)
ca("★ QUYỀN vẫn chặn vỏ máy (uid 1000 đọc mật khẩu)", "gọi_hệ đọc → tối" in o)
ca("★ CỔNG BẤT-KHẢ-HỒI vẫn chặn vỏ máy (xoá)", "gọi_hệ xoá → tối" in o)
ca("tệp bị nhắm xoá VẪN CÒN", "/tạm/rác còn không? danh_sách" in o)
ca("lệnh lạ → báo không hiểu, không bịa", "vỏ-máy: không hiểu lệnh" in o)
ca("hết hàng lệnh → vỏ máy tự kết thúc", "vỏ_máy → xong" in o)

print("\n[18] ★★★ DỊCH VỤ NỀN chạy bằng BYTECODE — biết NGỦ như daemon thật")
mã, o = chạy(["chay_dv_may.py"])
ca("chạy sạch", mã == 0, o[-300:])
ca("★ dịch vụ máy TỰ NGỦ khi hộp thư rỗng (trạng 'chặn')",
   "nhật_ký_máy → chặn" in o and "trạng = chặn" in o)
ca("★ ngủ thì KHÔNG tốn lát CPU nào (quay nhân 10 lát vẫn nguyên)",
   "lát CPU vẫn là: 1 (không tăng)" in o)
ca("★ `gửi` tin ĐÁNH THỨC dịch vụ máy", "gọi_hệ nhận → đĩa /tạm sắp đầy" in o)
ca("dịch vụ máy GHI nhật ký qua đúng cổng gọi-hệ", "gọi_hệ thêm → sáng" in o)
ca("ghi xong lại NGỦ TIẾP (không quay vòng bận)", o.count("nhật_ký_máy → chặn") >= 3)
ca("nội dung nhật ký do BYTECODE viết", "[máy] đĩa /tạm sắp đầy" in o and "[máy] mạng chập chờn" in o)
ca("tổng kết đo được bằng lệnh máy + lát CPU", "lệnh máy trong" in o and "trạng cuối = chặn" in o)

print("\n[19] ★ BỀN HOÁ CHO TIẾN TRÌNH MÁY (vá lỗ hổng: ảnh cũ làm nó thành XÁC)")
mã, o = chạy(["chay_ben_may.py"])
ca("chạy sạch", mã == 0, o[-300:])
ca("ảnh nay mang theo NGỮ CẢNH lõi GVM", "dựng lại 2 thân tiến-trình" in o)
ca("★ lõi máy sống lại (có tay-cầm, không phải ẩn)", "lõi máy của tt2 có còn? số" in o)
ca("số lệnh máy đời trước được giữ nguyên", "giữ nguyên từ đời trước): 120" in o)
ca("★ đếm TIẾP chứ không đếm lại từ đầu",
   "[tt2] 30" in o and "[tt2] 26" in o and o.count("[tt2] 30") == 1)
ca("★ tiến trình máy đang dở GỌI-HỆ cũng sống lại đúng",
   "gọi_hệ đọc → nhịp 0" in o and "/tạm/chép = [nhịp 0  khởi: nhân lên]" in o)
ca("cả hai tiến trình máy chạy tới khi CHẾT bình thường", o.count("trạng chết") >= 2)

print("\n[20] ★★ GỌI-HỆ TRÊN CỔNG LOGIC THẬT (opcode 72 trong hw/gvm.v, chạy bằng iverilog)")
import shutil as _sh
_iv = _sh.which("iverilog") or (r"D:\iverilog\bin\iverilog.exe" if os.path.exists(r"D:\iverilog\bin\iverilog.exe") else None)
if not _iv:
    print("   (bỏ qua — máy này chưa có iverilog; cài: winget install Icarus.Verilog --location D:\\iverilog)")
else:
    _env = dict(ENV, PATH=os.path.dirname(_iv) + os.pathsep + ENV.get("PATH", ""))
    _r = subprocess.run([PY, os.path.join(P, "hw", "lam_trap.py")], capture_output=True,
                        text=True, env=_env, cwd=P, encoding="utf-8")
    o = (_r.stdout or "") + (_r.stderr or "")
    ca("chạy sạch", _r.returncode == 0, o[-300:])
    ca("★ CPU phần cứng phát TRAP xin nhân (bắt tay trap_valid)", "[nhan]" in o and "TRAP so=11" in o)
    ca("★ nhân (testbench) phục vụ xong, CPU nhận kết quả rồi CHẠY TIẾP", "ROI = 700" in o)
    ca("★ tính toán TRÊN giá trị nhân trả về (700+42=742)", "ROI = 742" in o)
    ca("trap có ĐỐI SỐ chạy đúng (nhân đôi 21→42, 42→84)", "doi=21" in o and "ROI = 84" in o)
    ca("★ trap HAI ĐỐI (5+9=14) — phần cứng đọc thêm một tầng ngăn xếp",
       "nargs=2 doi=5,9" in o and "ROI = 14" in o)
    ca("★ trap BA ĐỐI ĐÚNG THỨ TỰ (1,2,3 → 1+20+300=321)",
       "nargs=3 doi=1,2,3" in o and "ROI = 321" in o)
    ca("★ trap LỒNG NHAU: đối tự nó là một lời xin khác (700,14,8 → 1640)",
       "nargs=3 doi=700,14,8" in o and "ROI = 1640" in o)
    ca("CPU dừng sạch sau khi xong", "CPU DUNG sau" in o and "7 lan trap" in o)
    ca("★★ phần mềm ⟷ phần cứng TRÙNG KHÍT từng giá trị", "TRÙNG KHÍT" in o)

print("\n[21] ★★★ TIM LÀ THIẾT BỊ — lõi QUYẾT ĐỊNH của trợ lý chạy bằng bytecode")
mã, o = chạy(["chay_tro_ly_may.py"])
ca("chạy sạch", mã == 0, o[-300:])
ca("★ máy xin NHÚNG qua gọi-hệ, chỉ nhận SỐ HIỆU (không thấy vector)",
   "gọi_hệ nhúng → 0" in o and "gọi_hệ nhúng → 1" in o)
ca("★ máy xin γ qua gọi-hệ (cộng_hưởng ×1000)", "gọi_hệ cộng_hưởng →" in o)
ca("★ máy TỰ CHỌN đúng kỹ năng cho lời nhờ (γ cao nhất)",
   "gọi_hệ đọc → nhịp 2" in o and "gọi_hệ liệt → [rác1, rác2]" in o)
# Tim thật (Ollama bge-m3): γ ngữ-nghĩa sắc → kỹ năng 'tôi là ai' vượt ngưỡng, máy TRẢ LỜI.
# Tim đã gỡ (CÒN_THIẾU E1) → nhúng dự-phòng băm-từ: γ thô, dưới ngưỡng. Bất-biến còn giữ được
# là XẾP HẠNG (kỹ năng đúng vẫn cao nhất) + TỪ CHỐI an toàn (không đoán bừa) — đúng học thuyết.
_tim_dp = "dự-phòng" in o.split("/tb/tim): ", 1)[-1].split("\n", 1)[0]
if not _tim_dp:
    ca("máy tự chọn được cả kỹ năng 'tôi là ai' (tim thật)", "[tt3] 1000 an" in o)
else:
    _tt3 = re.findall(r"\[tt3\] (.+)", o)
    _n3 = _tt3[8:12] if len(_tt3) >= 12 else ["", "", "", ""]
    ca("máy xếp 'tôi là ai' CAO NHẤT + TỪ CHỐI an toàn dưới ngưỡng (tim dự-phòng)",
       all(x.strip().isdigit() for x in _n3[:3])
       and int(_n3[2]) > int(_n3[0]) and int(_n3[2]) > int(_n3[1])
       and _n3[3].strip() == "4294967295", " · ".join(_tt3[8:12]))
ca("★ dưới ngưỡng thì máy TỪ CHỐI, không đoán bừa (−1 = 4294967295)", "[tt3] 4294967295" in o)
ca("thiết bị /tb/tim soi được tim đang đập bằng gì", "/tb/tim): " in o)
ca("nhân giữ kho vector, máy không đụng tới", "số vector tim đã cấp cho máy:" in o)

print("\n[22] ★★★★★ ĐỒNG MÔ PHỎNG — cổng logic xin việc của NHÂN HĐH-GIAO THẬT")
if not _iv:
    print("   (bỏ qua — chưa có iverilog)")
else:
    _env = dict(ENV, PATH=os.path.dirname(_iv) + os.pathsep + ENV.get("PATH", ""))
    _r = subprocess.run([PY, os.path.join(P, "hw", "lam_cosim.py")], capture_output=True,
                        text=True, env=_env, cwd=P, encoding="utf-8", timeout=600)
    o = (_r.stdout or "") + (_r.stderr or "")
    ca("chạy sạch", _r.returncode == 0, o[-300:])
    ca("★ CPU gate-level xin việc, NHÂN GIAO THẬT phục vụ", "[NHÂN GIAO ] #1 gọi-hệ 0" in o)
    ca("★ chuỗi đi từ nhân → HEAP của CPU silicon → CPU tự in",
       "[CPU-silicon] giao-01" in o)
    ca("★★ QUYỀN THẬT chặn tiến trình silicon (uid 1000 đọc mật khẩu)",
       "cấm đọc /hệ/mật_khẩu" in o)
    ca("★★ CỔNG BẤT-KHẢ-HỒI THẬT chặn tiến trình silicon (xoá)",
       "CẦN PHÊ DUYỆT — xoá(/tạm/rác)" in o)
    ca("tệp bị nhắm xoá VẪN CÒN sau khi silicon chạy xong",
       "/tạm/rác còn không? danh_sách" in o)
    ca("gọi-hệ không đối cũng chạy (ai → 1000 an)", "[CPU-silicon] 1000 an" in o)
    ca("★★ silicon TẠO TỆP qua nhân bằng gọi-hệ BA ĐỐI (đường, quyền, nội dung)",
       "gọi-hệ 2 đối=['/tạm/từ_silicon', 644, 'dòng này do CỔNG LOGIC viết']" in o)
    ca("★★ silicon NỐI THÊM bằng gọi-hệ HAI ĐỐI, rồi đọc lại thấy đủ",
       "gọi-hệ 3 đối=['/tạm/từ_silicon', ' + thêm nữa']" in o
       and "/tạm/từ_silicon = [dòng này do CỔNG LOGIC viết + thêm nữa]" in o)
    ca("★ NHẬT KÝ AUDIT ghi đủ việc tiến trình silicon đã xin",
       "tt2  đọc  /hệ/tên_máy" in o and "tt2  xoá  /tạm/rác" in o
       and "tt2  tạo  /tạm/từ_silicon" in o and "tt2  ai" in o)
    ca("CPU dừng sạch sau đúng 8 lần xin nhân", "8 lan xin nhan" in o)

print("\n[23] ★★ ĐIỂM HẸN **VPI** — nhân GIAO thành hàm hệ thống trong chính bộ mô phỏng")
_gcc = _sh.which("gcc") or (r"D:\mingw64\mingw64\bin\gcc.exe"
                            if os.path.exists(r"D:\mingw64\mingw64\bin\gcc.exe") else None)
if not _iv or not _gcc:
    print("   (bỏ qua — cần iverilog + gcc; cài: winget install BrechtSanders.WinLibs.POSIX.MSVCRT"
          " --location D:\\mingw64)")
else:
    _env = dict(ENV, PATH=os.path.dirname(_gcc) + os.pathsep
                          + os.path.dirname(_iv) + os.pathsep + ENV.get("PATH", ""))
    _r = subprocess.run([PY, os.path.join(P, "hw", "lam_cosim_vpi.py")], capture_output=True,
                        text=True, env=_env, cwd=P, encoding="utf-8", timeout=600)
    o = (_r.stdout or "") + (_r.stderr or "")
    ca("chạy sạch", _r.returncode == 0, o[-400:])
    ca("★ module VPI dựng được và bộ mô phỏng NẠP ĐƯỢC", "giao_vpi.vpi" in o
       and "failed to open" not in o and "not defined by any module" not in o)
    ca("★ điểm hẹn là SOCKET, không phải tệp", "điểm hẹn = SOCKET" in o)
    ca("★★ nhân GIAO THẬT phục vụ qua $giao_trap", "[NHÂN GIAO ] #1 gọi-hệ 0" in o)
    ca("★ C duyệt thẳng dut.ram[] lấy chuỗi đối (gọi-hệ ba đối)",
       "gọi-hệ 2 đối=['/tạm/từ_silicon', 644, 'dòng này do CỔNG LOGIC viết']" in o)
    ca("★ C cấp chuỗi trả về vào HEAP của CPU — CPU tự in được",
       "[CPU-silicon] giao-01" in o
       and "[CPU-silicon] dòng này do CỔNG LOGIC viết + thêm nữa" in o)
    ca("★★ QUYỀN + CỔNG BẤT-KHẢ-HỒI vẫn nguyên qua đường VPI",
       "cấm đọc /hệ/mật_khẩu" in o and "CẦN PHÊ DUYỆT — xoá(/tạm/rác)" in o
       and "/tạm/rác còn không? danh_sách" in o)
    ca("tệp do silicon tạo còn thật sau khi chạy xong",
       "/tạm/từ_silicon = [dòng này do CỔNG LOGIC viết + thêm nữa]" in o)
    ca("mọi lời xin đều đi qua VPI (8/8)", "8 lan xin nhan (8 lan qua VPI)" in o)
    import re as _re
    _m = _re.search(r"CPU DUNG sau (\d+) chu ky", o)
    _ck = int(_m.group(1)) if _m else 10 ** 9
    ca(f"★★ KHÔNG đốt chu kỳ để ĐỢI: {_ck} chu kỳ (bản tệp: 16k–2,3tr, thay đổi từng lần)",
       _ck < 8000, f"chu kỳ = {_ck}")

print("\n[24] ★★★ ĐỈNH CHO BO FPGA — GVM + cầu UART, mô phỏng tới TỪNG BIT trên dây")
if not _iv or not _gcc:
    print("   (bỏ qua — cần iverilog + gcc)")
else:
    _env = dict(ENV, PATH=os.path.dirname(_gcc) + os.pathsep
                          + os.path.dirname(_iv) + os.pathsep + ENV.get("PATH", ""))
    _r = subprocess.run([PY, os.path.join(P, "hw", "lam_bo_mo_phong.py")], capture_output=True,
                        text=True, env=_env, cwd=P, encoding="utf-8", timeout=900)
    o = (_r.stdout or "") + (_r.stderr or "")
    ca("chạy sạch", _r.returncode == 0, o[-400:])
    ca("★ CHÍNH cái đỉnh sẽ nạp lên bo (gvm_bo.v) chạy được", "BO DUNG sau" in o)
    ca("★★ cầu UART 8N1 chở được cả hai chiều (byte lên + byte xuống)",
       bool(re.search(r"(\d+) byte len · (\d+) byte xuong", o))
       and all(int(x) > 500 for x in re.search(r"(\d+) byte len · (\d+) byte xuong", o).groups()))
    ca("★ nhân GIAO THẬT phục vụ CPU qua dây, không qua chân trap",
       "[NHÂN GIAO] #1 gọi-hệ 0" in o)
    ca("★ chuỗi đối đi LÊN: máy chủ duyệt heap của CPU qua lệnh ĐỌC-ô-nhớ",
       "gọi-hệ 2 đối=['/tạm/từ_bo', 644, 'dòng này do BO FPGA viết']" in o)
    ca("★ chuỗi kết quả đi XUỐNG: máy chủ CẤP vào heap của CPU qua lệnh GHI-ô-nhớ",
       "[CPU-bo] dòng này do BO FPGA viết" in o and "[CPU-bo] giao-01" in o)
    ca("★★ QUYỀN + CỔNG BẤT-KHẢ-HỒI vẫn nguyên trên đường dây",
       "cấm đọc /hệ/mật_khẩu" in o and "CẦN PHÊ DUYỆT — xoá(/tạm/rác)" in o
       and "/tạm/rác còn không? danh_sách" in o)
    ca("tệp do CPU trên bo tạo còn thật", "/tạm/từ_bo = [dòng này do BO FPGA viết]" in o)
    ca("NHẬT KÝ AUDIT ghi đủ việc tiến trình TRÊN BO đã xin",
       "tt2  tạo  /tạm/từ_bo" in o and "tt2  xoá  /tạm/rác" in o and "tt2  ai" in o)

print("\n[25] ★★★ ĐĂNG NHẬP THẬT — sổ người dùng, mật khẩu BĂM CÓ MUỐI, đổi người, đổi mật khẩu")
mã, o = chạy(["giao.py", "kiem_lib_mật_khẩu.giao", "--bước", "200000000", "--cho-giờ"])
ca("chạy sạch (thư viện băm mật khẩu)", mã == 0, o[-300:])
ca("★ cùng mật khẩu + KHÁC MUỐI ⇒ khác bản băm (bảng cầu vồng vô dụng)", "muối khác → băm khác" in o)
ca("★ đúng mật khẩu → sáng · sai một ký tự → tối", "đúng → sáng" in o and "sai → tối" in o)
ca("bản băm KHÔNG chứa mật khẩu gốc", "không lộ mật khẩu" in o)
ca("định dạng $g3$<N>$<muối>$<băm64> (memory-hard) đọc lại được", "đọc lại bản ghi: sáng" in o)
ca("★ bản ghi $g1$ CŨ vẫn khớp được (hai định dạng song song — C1)",
   "bản ghi g1 cũ: vẫn sáng" in o and "bản ghi g1 cũ: sai → tối" in o)
ca("★ $g2$ có hiệu ứng thác đổ của SHA-256", "g2 thác đổ: khác hẳn" in o)
ca("★ bản ghi $g2$ CŨ vẫn khớp được (ba định dạng song song, không ai phải đổi mật khẩu)",
   "bản ghi g2 cũ: vẫn sáng" in o and "bản ghi g2 cũ: sai → tối" in o)
ca("★★★ $g3$ KHÓ VỀ BỘ NHỚ (học yescrypt của Kali): ổn định + thác đổ",
   "g3 ổn định: cùng vào → cùng ra" in o and "g3 thác đổ: khác hẳn" in o)
ca("★★ đổi N là đổi CẢ ĐƯỜNG ĐI trong bảng — không phải xích tuần tự chạy thêm vòng",
   "g3 đổi N → đổi hẳn kết quả" in o)
ca("★★★ chỉ số truy cập bảng TẢN THẬT (phụ thuộc trạng thái) — có thế mới BẮT PHẢI GIỮ bảng, "
   "tức mới khó về bộ nhớ", "g3 chỉ số TẢN thật" in o)
ca("★★★ TRẦN CÔNG: bản ghi khai N/vòng vô lý bị chặn TỨC THÌ — một dòng '$g3$999999999$…' trong "
   "sổ là treo máy ngay tại màn đăng nhập, không cần biết mật khẩu",
   "★ ba bản ghi vô lý bị chặn TỨC THÌ" in o and "trần không chặn nhầm bản ghi thật" in o)

def _phiên(gõ):
    "Chạy một phiên TƯƠNG TÁC qua đường ống (kể cả các dòng mật khẩu)."
    r = subprocess.run([PY, os.path.join(P, "chay_hdh_giao.py")], input="\n".join(gõ) + "\n",
                       capture_output=True, text=True, env=ENV, cwd=P, encoding="utf-8", timeout=900)
    return r.returncode, (r.stdout or "") + (r.stderr or "")

mã, o = _phiên(["an", "sai-bét", "an", "an", "tôi", "người", "xem /hệ/mật_khẩu", "thoát", "tắt"])
ca("chạy sạch (phiên tương tác)", mã == 0, o[-300:])
ca("★ có MÀN HÌNH ĐĂNG NHẬP thật", "giao-01 đăng nhập:" in o and "mật khẩu:" in o)
ca("★ sai mật khẩu bị TỪ CHỐI", "Sai tên đăng nhập hoặc mật khẩu." in o)
ca("★ KHÔNG chỉ điểm sai TÊN hay sai MẬT KHẨU", "không có người" not in o.lower())
ca("★ đúng mật khẩu → có phiên vỏ dưới đúng uid", "Xin chào an." in o and "an (uid 1000)" in o)
ca("`người` liệt kê sổ người dùng", "NGƯỜI" in o and "an\t1000\t/nhà/an" in o)
ca("★★ 'an' VẪN không đọc nổi /hệ/mật_khẩu (600)", "cấm đọc /hệ/mật_khẩu" in o)
ca("★ `thoát` là ĐĂNG XUẤT, quay lại màn đăng nhập chứ không tắt máy",
   "đã đăng xuất." in o and o.count("giao-01 đăng nhập:") >= 2)
ca("`tắt` mới thật sự tắt máy", "tắt máy." in o)

mã, o = _phiên(["an", "an", "thành gốc", "gốc", "tôi", "xem /hệ/mật_khẩu",
                "đổi_mk", "gốc", "sen-vàng-2026", "sen-vàng-2026", "thoát",
                "gốc", "sen-vàng-2026", "tôi", "tắt"])
ca("chạy sạch (đổi người + đổi mật khẩu)", mã == 0, o[-300:])
ca("★ `thành` (su) đổi người NGAY TRONG phiên, có hỏi mật khẩu",
   "mật khẩu của gốc:" in o and "nay bạn là gốc" in o)
ca("★ dấu nhắc đổi theo quyền (an$ → gốc#)", "gốc:/#" in o)
ca("★★ GỐC-QUYỀN thì ĐỌC ĐƯỢC /hệ/mật_khẩu — và thấy BĂM, không thấy mật khẩu",
   "$g3$64$" in o and "gốc:gốc" not in o)
ca("★ `đổi_mk` (passwd) đổi được mật khẩu", "mật khẩu của gốc đã đổi." in o)
ca("★★ mật khẩu MỚI dùng đăng nhập lại được thật", o.count("Xin chào gốc.") >= 1)

mã, o = _phiên(["an", "an", "đổi_mk", "SAI-mk-cũ", "abcd", "abcd", "tắt"])
ca("★ đổi mật khẩu mà KHÔNG biết mật khẩu cũ → từ chối",
   "mật khẩu hiện tại không đúng" in o)
mã, o = _phiên(["an", "an", "đổi_mk", "an", "abcd", "abcE", "tắt"])
ca("★ hai lần gõ mật khẩu mới không khớp → không đổi gì", "không khớp" in o)

print("\n[26] ★★★ MẠNG (B1) — ổ nghe theo cổng, kết nối hai chiều, QUYỀN vẫn chặn được")
mã, o = chạy(["giao.py", "kiem_lib_mang.giao", "--bước", "200000000"])
ca("chạy sạch (tầng mạng)", mã == 0, o[-300:])
ca("★ cổng < 1024 CHỈ gốc-quyền được nghe (luật Linux)",
   "cổng 80 < 1024: chỉ gốc-quyền được nghe" in o)
ca("★★ HAI TIẾN TRÌNH nói chuyện qua mạng (hỏi – đáp trọn vòng)",
   "khách nối cổng 5000 → mã 1" in o and "[1, chào dịch vụ, mấy giờ rồi]" in o
   and "nhịp máy đang là" in o)
ca("chủ nghe biết có khách mới (['nối', mã])", "[nối, 1]" in o)
ca("★★ quyền trên Ổ NGHE có hiệu lực (600 → người khác bị CẤM nối)", "cấm nối cổng 6000" in o)
ca("★★ kẻ thứ ba KHÔNG chen được vào kết nối của người khác",
   o.count("KHÔNG phải đầu mối của kết nối 1") >= 2)
ca("ba-trị đúng chỗ: không ai nghe → ẨN · cấm → TỐI", "không ai nghe cổng 7777" in o)
ca("phản áp: hàng gói đầy thì bên gửi phải chờ (như ống)", "kết nối 1 đầy — chờ" in o)
ca("soi được qua thiết bị /tb/mạng", "nghe cổng: [80, 5000, 6000] · kết nối: 1" in o)
ca("audit ghi cả lời gọi mạng", "nhật ký có 'nối': sáng · có 'gửi_gói': sáng" in o)

print("\n[27] ★★★ NHÓM NGƯỜI DÙNG (C2) + SỔ SUDO (C3)")
mã, o = chạy(["giao.py", "kiem_nhom_sudo.giao", "--bước", "200000000"])
ca("chạy sạch (nhóm + sudo)", mã == 0, o[-300:])
ca("★★ hai người CÙNG NHÓM đọc được tệp 640 của nhau (đúng đề bài C2)",
   "bản nháp chương một" in o)
ca("★★ người NGOÀI NHÓM thì không", o.count("cấm đọc /nhà/an/bài") >= 1)
ca("bit nhóm 640 chỉ cho ĐỌC — ghi vẫn bị chặn", "cấm ghi /nhà/an/bài" in o)
ca("★ luật chgrp Linux: chủ tệp + THUỘC nhóm đích; gốc tuỳ ý",
   o.count("phải là CHỦ tệp và THUỘC nhóm đích") >= 2)
ca("★ thứ tự Unix: CHỦ thắng NHÓM (chủ 040 tự khoá mình, người cùng nhóm vẫn đọc)",
   "cấm đọc /nhà/an/lạ" in o and "chủ tự khoá mình" in o)
ca("★ sổ sudo ba-trị: được=sáng · lệnh-không-cấp=tối · không-có-trong-sổ=ẩn",
   "sáng\ntối\nsáng\nẩn" in o.replace("\r\n", "\n"))
ca("sổ sudo 440 — người thường không tự đọc được", "cấm đọc /hệ/sudo" in o)

mã, o = _phiên(["an", "an", "nhóm", "sudo xem /hệ/mật_khẩu", "an",
                "sudo tt", "an", "sudo xoá /tạm/rác1", "an", "duyệt", "liệt /tạm", "tắt"])
ca("chạy sạch (phiên sudo tương tác)", mã == 0, o[-300:])
ca("★ lệnh `nhóm` (~getent group) chạy trong vỏ", "văn\t100\tgốc,an" in o)
ca("★★ sudo hỏi mật khẩu CỦA MÌNH rồi cấp gốc-quyền cho MỘT lệnh",
   "[sudo] mật khẩu của an:" in o and "$g3$64$" in o)
ca("★★ sổ /hệ/sudo CHẶN lệnh không được cấp", "sổ /hệ/sudo không cấp cho an lệnh 'tt'" in o)
ca("★★★ sudo KHÔNG thay duyệt: lệnh bất-khả-hồi qua sudo VẪN chờ phê duyệt",
   "CẦN PHÊ DUYỆT — xoá(/tạm/rác1)" in o and "✔ đã phê duyệt và thực hiện" in o)
ca("xoá qua sudo+duyệt có hiệu lực thật (rác1 mất, rác2 còn)",
   "rác2" in o and "rác1" not in o.split("đã phê duyệt và thực hiện", 1)[1])

print("\n[28] ★★★ BỔ KHUYẾT LINUX — thùng rác/hoàn tác ở TẦNG GỌI-HỆ + `vì_sao`")
mã, o = chạy(["giao.py", "kiem_bo_khuyet_linux.giao", "--bước", "200000000"])
ca("chạy sạch", mã == 0, o[-300:])
ca("★★★ xoá mà LẤY LẠI ĐƯỢC: bỏ → hoàn tác về ĐÚNG chỗ, ĐÚNG nội dung",
   o.count("sen nở đầu mùa") >= 3 and "/nhà/an/thơ" in o)
ca("★ `bỏ` KHÔNG cần phê duyệt (hoàn tác được ⇒ cổng không đứng ở đây)",
   "CẦN PHÊ DUYỆT — bỏ" not in o)
ca("★ hoàn tác lấy đúng thứ VỪA bỏ gần nhất (kiểu Ctrl-Z)", "bản trong kho" in o)
ca("bỏ hai tệp TRÙNG TÊN không đè nhau trong thùng", "\n2\n" in o)
ca("★★ QUYỀN vẫn chặn ở tầng thùng rác", "cấm bỏ /nhà/an/thơ (cần quyền GHI trên /nhà/an)" in o)
ca("★★ không lấy lại được thứ NGƯỜI KHÁC bỏ", "thùng rác CỦA BẠN trống" in o)
ca("★★★ `dọn_rác` MỚI là việc bất-khả-hồi ⇒ cổng duyệt đứng ở ĐÓ",
   "CẦN PHÊ DUYỆT — dọn_rác()" in o)
ca("dọn xong thì hết đường lấy lại (thùng còn 0)", "\n1\n0\n" in o.replace("\r\n", "\n"))
ca("★★ vì_sao chỉ đúng THƯ MỤC giữa đường chặn (chỗ Linux hay tắc)",
   "chặn ở thư-mục '/nhà/bình' (chưa tới đích)" in o and "bit CHẠY (x)" in o)
ca("★★ vì_sao nói rõ VAI + QUYỀN + CÁCH QUA khi chính tệp chặn",
   "đứng vai khác" in o and "chủ uid 1001" in o and "Muốn qua:" in o)
ca("vì_sao cũng giải thích khi ĐƯỢC phép (nhờ vai nào)", "được ĐỌC '/nhà/an'" in o and "vai chủ" in o)
ca("★ phân biệt ẨN (không có) với TỐI (bị cấm) — Linux trộn hai cái này",
   "Đây là ẩn (không biết), KHÔNG phải tối (bị cấm)" in o)

mã, o = _phiên(["an", "an", 'nói "bài thơ" > /nhà/an/thơ', "bỏ /nhà/an/thơ", "xem /nhà/an/thơ",
                "thùng", "hoàn_tác", "xem /nhà/an/thơ", "vì_sao /hệ/mật_khẩu", "tắt"])
ca("chạy sạch (phiên thùng rác tương tác)", mã == 0, o[-300:])
ca("★★ trọn vòng trong VỎ THẬT: bỏ → mất khỏi chỗ cũ → hoàn_tác → nội dung trở lại",
   "đã bỏ vào thùng rác" in o and "xem: không có /nhà/an/thơ" in o
   and "đã lấy lại: /nhà/an/thơ" in o
   and "bài thơ" in o.split("đã lấy lại: /nhà/an/thơ", 1)[1])
ca("★ lệnh `thùng` liệt kê đường CŨ để biết thứ gì đang nằm đó", "/nhà/an/thơ" in o)
ca("★★ `vì_sao` chạy được trong vỏ và nói rõ vai + cách qua",
   "cấm ĐỌC '/hệ/mật_khẩu'" in o and "đứng vai khác" in o)

print("\n[29] ★★★ BỔ KHUYẾT LINUX — dừng ÊM có hạn (H3) + hết bộ nhớ chọn theo σ rồi HỎI (H4)")
mã, o = chạy(["giao.py", "kiem_dung_em.giao", "--bước", "200000000"])
ca("chạy sạch", mã == 0, o[-300:])
ca("★★★ tiến trình được TỰ DỌN rồi mới thoát (Linux: SIGKILL không cho dọn)",
   "dọn: ghi nốt phần dở dang" in o and "đã dọn xong — thoát ÊM" in o)
ca("★★ việc dọn chạy Ở LÁT CỦA CHÍNH NÓ — không chen ngang như signal handler",
   "sẽ dọn ở lát của mình" in o)
ca("★ dừng hẳn vẫn phải HỎI NGƯỜI (xin_thoát qua cổng duyệt)",
   "CẦN PHÊ DUYỆT — xin_thoát(2)" in o)
ca("★★ kẻ CHÂY Ì quá hạn thì nhân mới cắt — và NÓI RÕ đã cắt (không im lặng)",
   "QUÁ HẠN dọn dẹp — nhân CẮT" in o)
ca("không xin tiến-trình 1 thoát được (chặn THẲNG, không qua cổng)",
   "KHÔNG xin tiến-trình 1 (khởi) thoát được" in o)
ca("★★★ hết bộ nhớ: nhân KHÔNG tự bắn ai mà nêu LÝ DO rồi hỏi",
   "HẾT BỘ NHỚ (900/1000 ô)" in o and "Gõ `duyệt` để đồng ý" in o)
ca("★★★ nạn nhân chọn theo σ HỌC ĐƯỢC, không phải heuristic 'ai to nhất'",
   "σ=12 THẤP NHẤT — đóng góp ít nhất" in o and "nạn nhân được đề nghị: tt5" in o)
ca("★ kẻ σ CAO tuy cũng ngốn nhiều vẫn được yên", "trạng thái kẻ quan trọng: sẵn-sàng" in o)
ca("người đồng ý → dừng ÊM (qua xin_thoát), bộ nhớ trả lại, xin lại thì được",
   "trạng thái kẻ ăn hại: chết" in o and "tổng đang dùng: 400" in o)

print("\n[30] ★★★ BỔ KHUYẾT LINUX — tên tệp (H5) · cấu hình kiểm-trước (H6) · ghi có điều kiện (H7)")
mã, o = chạy(["giao.py", "kiem_h5_h6_h7.giao", "--bước", "200000000"])
ca("chạy sạch", mã == 0, o[-300:])
ca("★★ tên có KÝ TỰ ĐIỀU KHIỂN bị chặn TỪ LÚC TẠO (Linux chỉ cấm byte 0 và '/')",
   "tên chứa ký tự điều khiển (mã 10)" in o)
ca("★ tên có LỀ TRẮNG thừa bị chặn (nhìn y hệt tên thật)", "tên có lề trắng thừa" in o)
ca("'.'/'..'/rỗng bị chặn", "không phải một tên ('.', '..' hay rỗng)" in o)
ca("★★ tệp tên '-rf' TẠO ĐƯỢC và VÔ HẠI (vỏ truyền danh sách đối, không nối rồi tách)",
   "tệp có tên hiểm" in o and "/tạm/-rf" in o)
ca("tên bình thường (có dấu cách) vẫn dùng được", o.split("\n")[1].strip() == "sáng")
ca("★★★ ghi sổ mà BỎ MẤT uid 0 → TỪ CHỐI (Linux ghi bừa rồi mất root)",
   "MẤT HẲN đường lên gốc-quyền" in o)
ca("★★ tệp cũ CÒN NGUYÊN sau khi từ chối", "(Tệp cũ còn NGUYÊN" in o)
ca("★ nói rõ DÒNG nào sai và sai vì sao",
   "dòng 2: uid 'mười' không phải số" in o and "dòng 2: thư mục nhà phải là đường tuyệt đối" in o)
ca("★★ trùng uid bị chặn (chung uid là chung QUYỀN — Linux im lặng cho qua)",
   "dòng 3: trùng uid 1000" in o)
ca("★ sudo để trống phần lệnh bị chặn", "được sudo NHỮNG LỆNH NÀO?" in o)
ca("★★ mật khẩu THÔ lọt vào sổ bóng bị chặn", "ghi mật khẩu THÔ vào đây là lộ hết" in o)
ca("★★ cửa NỐI THÊM (>>) cũng qua bộ kiểm — không lách được", "dòng 3: uid 'hai' không phải số" in o)
ca("ghi ĐÚNG thì vẫn qua bình thường", "bình:1001:/nhà/bình" in o)
ca("★★★ hai người cùng sửa: kẻ ghi sau bằng bản CŨ bị TỪ CHỐI, không đè mất việc kẻ trước",
   "ĐÃ CÓ NGƯỜI SỬA /tạm/sổ_chung" in o and "dòng của A" in o)
ca("★ đọc lại rồi làm lại thì được (cả hai việc đều còn)",
   "dòng 1\ndòng của A\ndòng của B" in o.replace("\r\n", "\n"))
ca("★ ghi_nếu VẪN qua bộ kiểm cấu hình (H6 và H7 chồng đúng thứ tự)",
   o.rstrip().endswith("(Tệp cũ còn NGUYÊN. Linux sẽ ghi bừa rồi hỏng lúc dùng.)"))

print("\n[31] ★★★ KHO PHẦN MỀM — học apt/Kali (quan sát máy thật), vá 5 chỗ yếu của nó")
mã, o = chạy(["giao.py", "kiem_kho.giao", "--bước", "500000000"])
ca("chạy sạch (kho)", mã == 0, o[-300:])
ca("★ kế hoạch cài nói VÌ SAO kéo theo từng gói, kèm ĐÚNG RÀNG BUỘC (apt chỉ in bức tường tên)",
   "nền (cần vì 'trên' cần nền)" in o)
ca("★★★ gói TỰ KHAI NĂNG LỰC — nhạy cảm thì phải ĐỒNG Ý tường minh (apt: tin là được ăn cả)",
   "đòi NĂNG LỰC NHẠY CẢM: dao→xoá" in o)
ca("★★ người thường CÀI ĐƯỢC mà không cần nâng quyền (apt bắt buộc root)",
   "cài vào /nhà/an/lệnh" in o)
ca("phụ thuộc được cài TRƯỚC, đúng thứ tự", "✓ nền 1.0" in o and "✓ trên 1.0" in o)
ca("★★★ GÓI BỊ SỬA ĐỔI → từ chối TOÀN BỘ giao dịch, KHÔNG ghi gì (apt: dpkg hỏng dở dang)",
   "BỊ SỬA ĐỔI" in o and "KHÔNG cài gì cả" in o)
ca("★★ không gỡ được gói mà kẻ khác đang cần", "không gỡ được: trên đang cần 'nền'" in o)
ca("★★ gỡ → thùng rác → hoàn_tác lấy lại nguyên nội dung",
   "thân lệnh nằm trong thùng rác" in o and "# trên — cần nền" in o)
ca("★★★ nâng cấp rồi LÙI được: thân lệnh về bản cũ, phiên trong sổ cũng lùi (apt KHÔNG có)",
   "↑ nền: 1.0 → 2.0" in o and "↩ nền → 1.0" in o and "[[dao, 1.0], [nền, 1.0]]" in o)

mã, o = _phiên(["an", "an", "gói kho", "gói cài bộ_hệ_thống", "gói", "bộ_hệ_thống", "tắt"])
ca("chạy sạch (phiên kho tương tác)", mã == 0, o[-300:])
ca("★ `gói kho` liệt kê mục lục kèm NHÓM và NĂNG LỰC",
   "SIÊU-GÓI: gom bộ công cụ soi hệ thống" in o and "dọn_nhà" in o)
ca("★★ SIÊU-GÓI kéo đủ bộ (học kali-linux-headless) rồi CHẠY được thật",
   "✓ bộ_hệ_thống 1.0" in o and "── người ──" in o and "── nhóm ──" in o)

print("\n[32] ★★★★ CHỮ KÝ KHOÁ-CÔNG-KHAI cho kho (I1) — RSA-2048 kiểm THUẦN GIAO")
mã, o = chạy(["giao.py", "kiem_chu_ky.giao", "--bước", "500000000"])
ca("chạy sạch (chữ ký)", mã == 0, o[-300:])
ca("★★★ GIAO tự kiểm được chữ ký RSA-2048 (mũ-modulo số lớn thuần GIAO)",
   "vân tay khoá đã neo: " in o and len(o.split("vân tay khoá đã neo: ")[1].split("\n")[0].strip()) == 16)
ca("kho đúng chữ ký thì cài được bình thường", "-- kho đúng chữ ký thì cài được --" in o)
ca("★★ SỬA MỤC LỤC → chữ ký gãy ngay, và chặn cả CÀI lẫn NÂNG CẤP",
   "KHÔNG CÀI: CHỮ KÝ KHÔNG KHỚP" in o and "KHÔNG NÂNG CẤP: CHỮ KÝ KHÔNG KHỚP" in o)
ca("★★★★ KHO GIẢ MẠO (mục lục hợp lệ + BĂM ĐÚNG, ký bằng khoá khác) vẫn bị TỪ CHỐI "
   "— đây đúng chỗ băm không cứu nổi",
   "băm của gói giả VẪN ĐÚNG" in o and o.count("KHÔNG CÀI: CHỮ KÝ KHÔNG KHỚP") >= 2)
ca("★★ an toàn nằm ở NEO TIN CẬY: đổi khoá neo sang khoá kẻ giả thì mới qua — và VÂN TAY ĐỔI "
   "nên người soi bằng mắt là thấy",
   "vân tay khoá nay là:" in o and "(thật) ≠" in o)
ca("chữ ký hỏng định dạng / thiếu hẳn → tối, không nổ",
   "kho KHÔNG có chữ ký" in o and "KHÔNG chống được kho giả mạo" in o)
ca("★ kho CỤC BỘ (chưa neo khoá) cho qua nhưng NÓI RÕ đang tin theo quyền tệp, không phải chữ ký",
   "cục-bộ (CHƯA NEO KHOÁ — tin theo quyền tệp, không phải chữ ký)" in o)

mã, o = _phiên(["an", "an", "gói tin", "tắt"])
ca("★ lệnh `gói tin` nói rõ nguồn, neo tin cậy và vân tay khoá",
   "neo tin cậy: /hệ/kho/khoá_công" in o and "✓ mục lục ĐÚNG chữ ký · vân tay khoá" in o)

print("\n[33] ★★ CHUYỂN TỆP (~mv) — nền cho kéo-thả trên bàn làm việc")
mã, o = _phiên(["an", "an", 'nói "bản nháp" > /nhà/an/thơ', "chuyển /nhà/an/thơ /nhà/an/thơ_thu",
                "xem /nhà/an/thơ_thu", "tạothư /nhà/an/kho",
                "chuyển /nhà/an/thơ_thu /nhà/an/kho/thơ_thu", "liệt /nhà/an/kho",
                'nói "khác" > /nhà/an/thơ_thu', "chuyển /nhà/an/thơ_thu /nhà/an/kho/thơ_thu",
                "chuyển /hệ/mật_khẩu /nhà/an/trộm", "tắt"])
ca("chạy sạch (chuyển tệp)", mã == 0, o[-300:])
ca("★ đổi tên giữ nguyên nội dung", "bản nháp" in o)
ca("★ dời được sang thư mục khác", "thơ_thu" in o.split("liệt /nhà/an/kho", 1)[-1])
ca("★★ KHÔNG đè lên thứ đã có (đè là mất dữ liệu im lặng)",
   "đích đã có thì KHÔNG đè" in o)
ca("★★ quyền chặn: không lôi được tệp 600 của /hệ ra ngoài",
   "không chuyển được /hệ/mật_khẩu" in o)

mã, o = _phiên(["an", "an", 'nói "bản gốc" > /nhà/an/tho', "chép /nhà/an/tho /nhà/an/tho_sao",
                "xem /nhà/an/tho_sao", "xem /nhà/an/tho", "chép /nhà/an/tho /nhà/an/tho_sao",
                "chép /hệ/mật_khẩu /nhà/an/trộm", "soi /nhà/an/tho_sao", "tắt"])
ca("chạy sạch (chép tệp ~cp, GH_CHÉP)", mã == 0, o[-300:])
ca("★ `chép` ra BẢN SAO đúng nội dung — tệp gốc không suy suyển", o.count("bản gốc") >= 2)
ca("★★ chép KHÔNG đè lên thứ đã có", "đích đã có thì KHÔNG đè" in o)
ca("★★ khác `chuyển` đúng chỗ quyền: chép cần ĐỌC nguồn — /hệ/mật_khẩu 600 vẫn kín",
   "không chép được /hệ/mật_khẩu" in o)
ca("★ bản sao thuộc NGƯỜI CHÉP, quyền theo tệp nguồn", "rw-r--r--  tệp  chủ=an" in o)

print("\n[34] ★★★ CHỐNG DÒ MẬT KHẨU (C4-④): chậm dần + KHOÁ sau N lần sai (C5)")
mã, o = chạy(["giao.py", "kiem_chong_do.giao", "--bước", "200000000", "--cho-giờ"])
ca("chạy sạch (chống dò)", mã == 0 and "RỚT" not in o, o[-300:])
ca("★ hai lần sai đầu CHƯA bị hành (người gõ nhầm thật không vướng)",
   "chờ sau 1 lần sai: 0" in o and "chờ sau 2 lần sai: 0" in o)
ca("★★ từ lần sai thứ 3 bắt CHỜ GẤP ĐÔI — trong quãng chờ GÕ ĐÚNG cũng không xét",
   "★ sau 3 lần sai phải chờ" in o)
ca("★★ hết quãng chờ + gõ đúng → vào được, SỔ DÒ XOÁ (chỉ phạt chuỗi sai liên tiếp)",
   "đăng nhập lại được: tiến-trình" in o and "sổ dò còn ghi mồi không: tối" in o)
ca("★★★ sai liên tiếp 10 lần → tài khoản bị KHOÁ THẬT trong sổ bóng (bóng = *)",
   "ĐÃ KHOÁ (bóng = *)" in o)
ca("★★ `gốc` KHÔNG bị tự khoá — kẻ dò không thể khoá cửa của chủ máy",
   "gốc sau 12 lần sai vẫn vào được" in o)
ca("quãng chờ có TRẦN 60 giây", "trần chờ giữ đúng" in o)

print("\n[35] ★★★ RÒ RỈ THEO THỜI GIAN khi xác thực — giấu ở lời nói mà hở ở đồng hồ")
mã, o = chạy(["giao.py", "kiem_ro_ri_thoi_gian.giao", "--bước", "900000000", "--cho-giờ"])
ca("chạy sạch (rò rỉ thời gian)", mã == 0 and "RỚT" not in o, o[-300:])
ca("★★★ người KHÔNG CÓ tốn công NGANG người có thật — không đếm được tài khoản bằng đồng hồ "
   "(đo trước khi vá: 750ms vs ~0ms)", "★ không-có tốn công NGANG có-thật" in o)
ca("★★ tài khoản BỊ KHOÁ cũng ngang — không lộ 'có thật, đang bị khoá'",
   "★ bị-khoá cũng tốn công NGANG" in o)
ca("vá thời gian KHÔNG làm sai kết quả (đúng→sáng · sai→tối · không có→ẩn · khoá→tối)",
   all(k in o for k in ["vẫn đúng: mật khẩu đúng → sáng", "vẫn đúng: sai mật khẩu → tối",
                        "vẫn đúng: không có người → ẩn",
                        "vẫn đúng: tài khoản khoá → tối dù mật khẩu đúng"]))

print("\n[36] ★★★★ B2 — SỔ ĐỊNH DẠNG CHẠY ĐƯỢC (hình dạng binfmt_misc) + /lệnh mang BYTECODE")
# Chạy HAI LẦN: chưa cấp năng lực `máy` và đã cấp — cùng một tệp kiểm, hai kết quả.
mã0, o0 = chạy(["giao.py", "kiem_dinh_dang.giao", "--bước", "900000000"])
mã1, o1 = chạy(["giao.py", "kiem_dinh_dang.giao", "--bước", "900000000", "--cho-máy"])
ca("chạy sạch cả hai chế độ (chưa cấp `máy` / đã cấp)", mã0 == 0 and mã1 == 0, (o0 + o1)[-300:])
ca("sổ /hệ/định_dạng có thật, dòng cuối là NGẢ LUI '*'",
   "số dòng trong sổ: 4" in o0 and "dòng cuối là ngả lui: sáng" in o0)

ca("★★ ① sổ sai cú pháp → TỪ CHỐI từ lúc GHI, tệp cũ CÒN NGUYÊN (binfmt_misc ghi thẳng /proc, "
   "không ai kiểm)",
   "phải đúng 4 cột" in o0 and "sổ cũ còn nguyên: sáng" in o0)
ca("★★★ trùng magic bị bắt — dòng sau KHÔNG BAO GIỜ tới lượt mà Linux im lặng cho qua",
   "trùng magic '#tt ' với dòng trên — dòng này không bao giờ tới lượt" in o0)
ca("★★ ngả lui đặt GIỮA sổ thì nuốt hết dòng sau → chặn",
   "nằm SAU ngả lui '*'" in o0)
ca("★★ THIẾU ngả lui → chặn (kẻo tệp lạ không chạy nổi mà chẳng biết vì sao)",
   "thiếu NGẢ LUI" in o0)
ca("trình không có thật → chặn, kèm danh sách trình có thật", "'trình_ma' không có thật" in o0)
ca("★★★ ① XOÁ HẲN sổ đi máy VẪN chạy lệnh — ngả lui nằm TRONG MÃ, không nằm trên đĩa "
   "(binfmt_misc: phá sổ là làm câm cả máy)",
   "sổ đã bị xoá, đọc /hệ/định_dạng: ẩn" in o0 and "vẫn có ngả lui: 4" in o0
   and "máy vẫn nói được" in o0)

ca("★★★★ /lệnh mang CHÍNH BYTECODE: `dịch` sinh tệp mở đầu '#!mã-máy 32', KHÔNG còn mã nguồn",
   "tệp lệnh mở đầu bằng: #!mã-máy 32" in o1 and "tệp KHÔNG còn chứa mã nguồn: sáng" in o1
   and "377 từ-lệnh, chạy thẳng không dịch lại" in o1)
ca("★★★★ và CHẠY ĐÚNG như một tiến trình MÁY thật (7×6 = 42, có lát lập-lịch)",
   "[tt3] 42" in o1 and "nhân42 xong" in o1)
ca("★★ ③ định dạng TỰ KHAI năng lực: chưa cấp `máy` thì TỪ CHỐI và nói rõ cách bật "
   "(binfmt_misc: đăng ký là trao trọn quyền, không ai hỏi)",
   "cần năng lực 'máy' — máy CHƯA cấp" in o0 and "--cho-máy" in o0
   and "cần năng lực 'máy' — máy CÓ cấp." in o1)
ca("★★ ② nói RÕ VÌ SAO cho MỌI định dạng — thứ 'Exec format error' của Linux không nói",
   "khớp định dạng 'kịch_bản' (ngả lui" in o0 and "khớp định dạng 'nội_trú' (magic '#nội-trú')" in o0)
ca("★★ thân mã hỏng → từ chối SẠCH kèm cách dựng lại, không đoán bừa",
   "thân mã hỏng" in o1 and "Dựng lại bằng: dịch" in o1
   and o0.count("tệp_sang_mã") == 3 and o0.count(": ẩn") >= 3)
ca("★★★ QUYỀN vẫn chặn y như cũ — thêm định dạng KHÔNG mở thêm cửa nào",
   "cấm chạy /nhà/an/lệnh/không_x — thiếu quyền x" in o0
   and "cấm chạy /nhà/an/lệnh/không_x — thiếu quyền x" in o1)

mã, o = _phiên(["an", "an", "định_dạng", 'nói "rọi 6 * 7" > /nhà/an/n.giao',
                "dịch /nhà/an/n.giao /nhà/an/lệnh/bốn_hai", "định_dạng bốn_hai",
                "bốn_hai", "tắt"])
ca("chạy sạch (phiên tương tác B2)", mã == 0, o[-300:])
ca("★ lệnh `định_dạng` liệt kê sổ trong vỏ thật",
   "ĐỊNH DẠNG CHẠY ĐƯỢC" in o and "mã_máy" in o and "#!mã-máy" in o)
ca("★★★ dịch rồi chạy NGAY trong vỏ thật: bytecode trên đĩa → tiến trình máy → 42",
   "đã dịch" in o and "] 42" in o and "bốn_hai xong" in o)
ca("★ `định_dạng <lệnh>` tra được bằng TÊN lệnh, không cần đường đủ",
   "khớp định dạng 'mã_máy'" in o)

print("\n[37] ★★★★★ B3 — TẦNG KHỐI + NHẬT KÝ + GẮN ĐĨA (vá 3 chỗ ext4 THẬT còn yếu)")
mã, o = chạy(["giao.py", "kiem_dia.giao", "--bước", "900000000"])
ca("chạy sạch (tầng khối)", mã == 0 and "RỚT" not in o, o[-300:])
ca("khối · inode · tổng kiểm · gắn-phát-lại chạy được",
   "đã ghi thơ (30 byte → 1 khối)" in o and "sen vàng nở sớm mùa thu Hà Nội" in o)
ca("★ ④ nói thật CÁI GIÁ của tầng khối (ext4: tệp 1 byte tốn 4096)",
   "tệp 1 byte → 1 khối = 32 byte, phí 31 byte" in o)

ca("★★★ ② KHỐI MỤC THẦM LẶNG bị BÁO, không trả rác — `metadata_csum` của ext4 KHÔNG phủ "
   "dữ liệu người dùng nên ext4 trả nó ra như thật",
   "★ khối hỏng → TỪ CHỐI" in o and "tổng kiểm không khớp" in o)
ca("★★★★ ① MẤT ĐIỆN TRƯỚC CAM KẾT → giữ bản CŨ nguyên vẹn từng chữ",
   "vứt 8 khối ⇒ giữ bản CŨ nguyên vẹn" in o and "★★★ nội dung ĐÚNG BẢN CŨ" in o)
ca("★★★★★ ① MẤT ĐIỆN SAU CAM KẾT, GIỮA LÚC CHÉP → phát lại thành bản MỚI TRỌN VẸN "
   "(ext4 `data=ordered` chỉ ghi nhật ký siêu-dữ-liệu nên chỗ này ra nội dung RÁC)",
   "cắt điện giữa lúc chép (đã chép 4/8 khối)" in o
   and "chép tiếp 8 khối ⇒ giữ bản MỚI trọn vẹn" in o
   and "★★★ nội dung ĐÚNG BẢN MỚI, trọn vẹn" in o)
ca("★★★ ③ TÊN và NỘI DUNG cùng MỘT giao dịch — không có điệu nhảy fsync như ext4 "
   "(`fsync(tệp)` của Linux không làm bền cái tên)",
   "★★ TÊN cũng không sinh ra" in o and "★ tệp cũ vẫn còn nguyên" in o)
ca("vùng mô tả hỏng → GẮN TỪ CHỐI, không đoán bừa", "★★ gắn TỪ CHỐI" in o)
ca("hết chỗ thì nói thẳng, và tệp cũ không suy suyển",
   "★ hết chỗ trên đĩa" in o and "tệp cũ còn nguyên: sáng" in o)

ca("★★★ GẮN vào cây thư mục: ghi/đọc bằng ĐƯỜNG DẪN THƯỜNG mà byte nằm trên KHỐI",
   "byte ấy có THẬT nằm trên khối không: sáng" in o and "liệt: [thơ]" in o)
ca("★★ chỉ GỐC-QUYỀN được gắn (như `mount`)", "người thường gắn: tối" in o)
ca("★★★ QUYỀN của ĐIỂM GẮN quyết định — gắn đĩa KHÔNG mở thêm cửa nào",
   "cấm đọc /đĩa/thơ" in o and "cấm tạo /đĩa/lén" in o)
ca("★★★ khối hỏng thì GỌI-HỆ báo lỗi, chương trình không nhận được rác",
   "đọc 'thơ' hỏng: KHỐI" in o)
ca("★★★★ mất điện giữa lúc ghi rồi GẮN LẠI → đọc qua gọi-hệ ra đúng bản mới trọn vẹn",
   "★★★ đọc qua gọi-hệ ra ĐÚNG bản mới trọn vẹn" in o)
ca("tháo đĩa → đường dẫn quay về cây nút thường", "không có /đĩa3/sổ" in o)

mã, o = _phiên(["gốc", "gốc", "đĩa dựng /đĩa 64 32", "ghi /đĩa/thơ sen vàng nở sớm",
                "xem /đĩa/thơ", "liệt /đĩa", "đĩa", "tắt"])
ca("chạy sạch (phiên đĩa tương tác)", mã == 0, o[-300:])
ca("★★ dựng + gắn đĩa từ vỏ thật, rồi dùng như thư mục thường",
   "đã dựng và gắn đĩa ở /đĩa (64 khối × 32 byte)" in o and "sen vàng nở sớm" in o)
ca("★ lệnh `đĩa` báo SỐ LIỆU THẬT: mấy tệp, mấy khối, phí bao nhiêu byte",
   "1 tệp" in o and "1/64 khối×32B" in o and "phí" in o)

print("\n" + "=" * 68)
print(f"HĐH-GIAO: {tổng - rớt}/{tổng} hạng mục đạt" + ("" if rớt == 0 else f"  — {rớt} RỚT"))
print("=" * 68)
sys.exit(1 if rớt else 0)

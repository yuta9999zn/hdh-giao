# TIẾN ĐỘ & KẾ HOẠCH — GIAO / HĐH-GIAO

> Ảnh chụp tiến độ để **quay lại sau**. Chạy kiểm: `PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python kiem_toan_bo.py`

## ★ ĐIỂM TIẾP TỤC (cập nhật 2026-07-30 — đọc TRƯỚC TIÊN khi quay lại)
**Trạng thái xanh:** `kiem_toan_bo.py` = **65/65 hạng mục** · ngôn-ngữ 71/71 · HĐH 234/234 · wasm 20/20 · Verilog gate-level byte-exact. Hồ sơ tồn đọng: **`CÒN_THIẾU.md`** (nguồn sự thật việc-cần-làm).

**PHIÊN 2026-07-30/31 — v0.11.0 → v0.29.0:**
- ✅ **v0.29.0 B3 — TẦNG KHỐI + NHẬT KÝ PHỦ CẢ DỮ LIỆU + GẮN ĐĨA.** Quan sát ext4 Kali thật:
  `findmnt` ra **`data=ordered`** (nhật ký chỉ phủ SIÊU DỮ LIỆU) · `metadata_csum` **không phủ dữ
  liệu người dùng** · `man 2 fsync` tự nói **không đảm bảo cái TÊN bền** · tệp 1 byte tốn 4096.
  `lib_dia.giao`: khối · inode · **tổng kiểm từng khối** · **nhật ký chở CẢ khối dữ liệu** ·
  gắn-và-phát-lại **có báo cáo**. **Phép thử quyết định — CẮT ĐIỆN GIỮA LÚC GHI ở hai điểm:**
  trước cam kết → vứt nhật ký, đọc ra **đúng bản CŨ nguyên vẹn**; sau cam kết giữa lúc chép (4/8
  khối) → chép tiếp, đọc ra **đúng bản MỚI trọn vẹn**. Không có cửa nào cho "nửa cũ nửa mới" —
  đúng chỗ `data=ordered` của ext4 sẽ ra nội dung RÁC. Khối mục → **BÁO** qua cả gọi-hệ, không
  trả rác. Tên + nội dung **cùng một giao dịch** ⇒ không có điệu nhảy fsync. **GẮN**: `gắn_đĩa`
  treo vào thư mục có sẵn, `ghi/xem/liệt` đường dẫn thường đi xuống tầng khối qua 4 cửa gọi-hệ;
  **chỉ gốc được gắn**, **quyền ĐIỂM GẮN quyết định** ⇒ không mở thêm cửa nào. Lệnh vỏ `đĩa`
  hiện thẳng **số byte phí** thay vì giấu. *Trung thực: đĩa vẫn nằm trong bộ nhớ máy GIAO, chưa
  phải mặt đĩa vật lý — cái mới là NGỮ NGHĨA; djb2 bắt hỏng ngẫu nhiên chứ không chống kẻ cố ý;
  mới có tệp phẳng, chưa xoá/thu hồi khối, chưa gắn được `/`.* *Vấp: một ca rớt vì BỘ KIỂM SAI
  chứ không phải mã sai — "đĩa quá nhỏ" tôi đặt vẫn đủ chỗ; ca phủ định chỉ có giá trị khi đã
  tính đúng ngưỡng.* Kiểm: `kiem_dia.giao` → mục [37], +18 hạng mục. `kiem_hdh_giao` **385/385**.
- ✅ **v0.28.0 B2 XONG — SỔ ĐỊNH DẠNG (hình dạng `binfmt_misc`) + `/lệnh` mang chính BYTECODE.**
  *Phần đáng kể lại: quan sát Kali ở v0.27.0 đã ĐỔI CÁCH NGHĨ về chính mục này.* Đếm `/bin` ra
  1540 ELF **nhưng 897 kịch bản có `#!`** ⇒ B2 không phải "bỏ văn bản đi" như tên mục cũ gợi ý;
  cái đáng học là **sổ đăng ký magic → trình chạy**, `#!` chỉ là một mục. `chạy_một_lệnh` nay
  **không còn nhánh ghi cứng nào** (trước: `#nội-trú`/`#tt `/kịch bản đóng đinh trong vỏ).
  `lib_dinh_dang.giao` + `/hệ/định_dạng` (4 cột) · định dạng **`#!mã-máy`** + `đăng_ký_ct_mã` +
  nhánh `ct_mã` trong `GH_SINH` ⇒ chạy lệnh **không đụng trình biên dịch** · lệnh `dịch` và
  `định_dạng`. **Ba chỗ binfmt_misc yếu đã vá:** ① sổ qua H6 (bắt trùng magic — *"dòng này không
  bao giờ tới lượt"*, ngả lui đặt giữa, thiếu ngả lui, trình ma; kèm số dòng, tệp cũ nguyên) VÀ
  **xoá hẳn sổ máy vẫn chạy** vì ngả lui nằm TRONG MÃ ② `vì_sao_dạng` nói rõ nấc hỏng (Linux chỉ
  `ENOEXEC`) ③ định dạng **tự khai năng lực**. Quyền xét TRƯỚC khi tra sổ ⇒ không mở thêm cửa nào.
  *Trung thực: hệ-tệp GIAO chứa CHUỖI nên từ-lệnh viết dạng số thập phân — cái đổi thật là tệp
  mang MÃ chứ không mang NGUỒN, gọi "nhị phân" là nói quá.* **★ VẤP ĐÁNG KỂ NHẤT: tra sổ nằm trên
  đường đi của MỌI lệnh** — bản đầu đọc + tách dòng + tách cột mỗi lần chạy lệnh ⇒ `hdh_giao.giao`
  **chạm trần 5 triệu bước ngay lần chạy đầu**, 12 hạng mục rớt một lượt mà nhìn qua tưởng 12 lỗi
  khác nhau (đúng bẫy §5.5 đã ghi: procfs + tra $PATH, nay vấp lại chỗ mới). Vá bằng **nhớ bản đã
  phân tích, khoá theo CHÍNH nội dung thô** — sổ đổi một ký tự là tự hết hiệu lực, KHÔNG ai phải
  nhớ đi xoá đệm (nếu "xoá đệm lúc ghi" thì phải rải ra 6 chỗ GH_*, quên một chỗ là chạy sai mà
  kiểm vẫn xanh). **Đo lại: cần ~4–5M bước, chạy được ở mặc định 5M nhưng chỉ dư ~20%** ⇒ việc nào
  sau này đặt thêm chi phí lên đường đi của mọi lệnh phải ĐO TRƯỚC. *Vấp lần THỨ HAI liên tiếp: bộ
  kiểm đếm CỨNG số tệp /lệnh (59→61) — lần này đoán trước, nhưng vẫn là bẫy nằm chờ.*
  Kiểm: `kiem_dinh_dang.giao` chạy HAI LẦN (chưa cấp `máy` / đã cấp) → mục [36], +18 hạng mục.
  `kiem_hdh_giao` **367/367** · `kiem_de` **41/41** · `kiem_tu_xa` **37/37**.
- ✅ **v0.27.0 ĐỐI CHIẾU KALI 2026.2 (quan sát máy THẬT trên WSL) — tìm được 1 chỗ Kali HƠN ta + 2
  chỗ Kali HỞ.** ① **Kali hơn ta:** `ENCRYPT_METHOD YESCRYPT` (memory-hard) trong khi `$g2$` của ta
  chỉ khó về THỜI GIAN ⇒ GPU thắng. Thêm **`$g3$` = ROMix kiểu scrypt** thuần GIAO (đổ đầy bảng V
  → truy cập NGẪU NHIÊN, chỉ số lấy từ chính trạng thái nên không nạp trước được). **Điểm quyết
  định: KHÔNG phải trả thêm gì — đo thật g2 743ms vs g3 752ms, chênh 1,2%.** Ba định dạng song
  song, không ai phải đổi mật khẩu. *Kiểm bắt đúng hai chỗ dễ cài sai: đổi N phải đổi CẢ ĐƯỜNG ĐI
  (nếu là xích tuần tự thì N=8 sẽ là TIỀN TỐ của N=16), và dãy chỉ số phải TẢN thật (23/24) — j
  chạy đều thì bảng V không cần giữ và tính khó-bộ-nhớ sụp dù đầu ra trông vẫn ngẫu nhiên.*
  ② **sshd hở:** `RekeyLimit` cho thấy hạn phải ở CẢ HAI đầu, mà rekey v0.26.0 của ta treo vào
  thiện chí của KHÁCH ⇒ máy chủ nay ĐẾM và TỪ CHỐI PHỤC VỤ quá 64 khung (đường thoát duy nhất là
  đổi khoá), kèm chặn khung > 8192 ký tự ⇒ "số khung × cỡ tối đa" thành cận trên THẬT cho dữ liệu.
  ③ **`pam_faillock` CÓ mà KHÔNG BẬT** trong `/etc/pam.d`, và `pam_unix` chậm 2s bằng cách **SLEEP
  chính tiến trình** ⇒ mở 100 kết nối là giữ chân 100 tiến trình: thứ chống dò hoá đòn bẩy DoS. Ta
  ghi MỐC rồi trả lời ngay, sổ chung theo TÊN nên song song cũng cùng một quãng chờ. *Vấp: GIAO
  không cho xuống dòng rồi mới tới `+`; và đổi định dạng bóng làm 3 bộ kiểm khác rớt vì dò chuỗi
  cứng `$g2$128$` — định dạng bản ghi là GIAO DIỆN CÔNG KHAI, đổi thì phải quét cả cây kiểm.*
  ④ **★ TỰ BẮT ĐƯỢC trong lúc đối chiếu — RÒ RỈ THEO THỜI GIAN:** ta nói "sai tên HOẶC mật khẩu"
  cho kín, nhưng ĐO ra thì người có thật tốn ~750ms còn người không có / tài khoản bị khoá trả lời
  ~0ms ⇒ **kẻ dò không cần đọc câu trả lời, bấm giờ là đếm sạch tài khoản**. Vá theo lối OpenSSH
  (băm `BÓNG_GIẢ` rồi vứt; bản giả dựng TỪ `MK_N3` nên nâng N là tự theo). **Đã tháo bản vá ra để
  xem bộ kiểm có rớt không: 3s·0s·0s → rớt cả hai ca** — chốt chỉ đáng tin khi đã thấy nó bật.
  *Bài học: giấu ở LỜI NÓI mà hở ở ĐỒNG HỒ thì coi như không giấu; và lỗi nằm đúng trong thứ mình
  tưởng đã làm cẩn thận.* ⑤ **TRẦN CÔNG cho bản ghi bóng:** bản ghi TỰ KHAI số vòng/số ô mà
  `khớp_mk` chạy theo lời khai ⇒ một dòng `$g3$999999999$…` lọt vào sổ là **treo máy ngay tại màn
  đăng nhập, không cần biết mật khẩu**. Nay `MK_TRẦN_N=4096` · `MK_TRẦN_VÒNG=100000` · chặn
  `vòng < 1`. `kiem_hdh_giao` **349/349** · `kiem_tu_xa` **37/37**.
- ✅ **v0.26.0 KHÉP C4·C5·G2 — rekey + chống dò mật khẩu + `GH_CHÉP`** — ① **rekey**: khách gửi
  `ĐỔI_KHOÁ <B₂>` NGAY TRONG kênh cũ (đã xác thực HMAC ⇒ **không cần ký lại** — đúng lối SSH),
  hai bên thay trọn ba khoá + số đếm về 0, khách tự đổi mỗi 32 khung; soi dây: khoá CŨ không mở
  nổi khung sau rekey. ② **chống dò**: sổ `DÒ_SỔ` theo TÊN móc trong `đăng_nhập` (MỘT điểm chặn
  phủ tại-máy/`thành`/từ-xa) — 2 lần đầu tha, từ lần 3 chờ gấp đôi (trần 60s, cần `giờ`),
  **trong quãng chờ gõ ĐÚNG cũng không xét** (không lộ trúng/trượt), 10 lần liên tiếp → tự
  `khoá_người` (bóng `*`, **chừa `gốc`** — kẻo kẻ dò khoá được cửa chủ máy); từ xa thêm: 3 sai/kết
  nối → NGẮT (bắt tay DH lại cũng không thoát sổ tên). ③ **`GH_CHÉP`** (gọi-hệ 42, ~cp): ĐỌC
  nguồn + GHI thư-mục đích (khác `chuyển` cần GHI cả hai cha), không đè, bản sao thuộc người
  chép; Tệp có “Chép thành…” + chuột phải nền “Tạo tệp/thư mục mới”. *Vấp: bộ kiểm đếm CỨNG
  58 tệp /lệnh — thêm lệnh nội trú là lệch một.* `kiem_hdh_giao` **340/340** · `kiem_tu_xa`
  **32/32** · `kiem_de` **41/41**.
- ✅ **v0.25.0 I3+I4 — KHÉP TRỌN NHÓM I** — phụ thuộc **có phiên bản** (`cần X>=2.0`, so theo từng đốt số nên `1.10>1.9`) + **gói thay thế** `a/b` (**`/` chứ không `|`** — `|` đã là dấu ngăn cột, dùng nhầm thì cột dịch và băm rơi ô khác; bộ kiểm H6 nay đòi ĐÚNG 7 cột) + từ chối **nói rõ vì sao**; **lùi NHIỀU BƯỚC** (sổ lùi thành ngăn xếp). *Vấp: lấy bản cũ từ thùng rác mà không gỡ mục ấy ⇒ bước lùi sau vớ lại đúng nó, trả sai bản — chỉ lộ khi kiểm hai bước liên tiếp.* `kiem_toan_bo` **72/72**.
- ✅ **v0.24.0 KHO QUA MẠNG (I2)** — `nguồn_xa` + `gói tải` + tự tải thân gói khi cài. **Điểm chính không phải "tải được" mà là trình tự: tải → KIỂM CHỮ KÝ → rồi mới GHI**; khoá công KHÔNG tải về (neo sẵn). Hai phép thử phủ định: sửa 1 ký tự trên đường → từ chối & **không ghi byte nào**; kho ký khoá khác → từ chối. Mục lục cần gốc-quyền (như `apt update`), thân gói thì người thường tải vào kho riêng ⇒ **vẫn không cần nâng quyền để cài**. `chay_kho_xa.py` đóng vai kho ngoài (khoá riêng của chính nó). `kiem_kho_xa.py` **12/12** · `kiem_toan_bo` **71/71**. *Vấp: ghi mục lục thất bại IM LẶNG vì thiếu quyền — nay kiểm kết quả mọi lần ghi.*
- ✅ **v0.23.0 NHÓM G** — gọi-hệ **41 `chuyển`** (~mv: cần GHI cả hai thư-mục cha · tên đích sạch · **KHÔNG đè** · khả-hồi nên không cần cổng duyệt) · ứng dụng **Soạn thảo** (đọc/ghi qua đúng gọi-hệ ⇒ quyền chặn cả hai chiều) · **chuột phải** (hàng tệp + nền) · **kéo-thả** (vào thư mục để chuyển, vào 🗑 dock để bỏ). *Bẫy `sáng`/`tối` LÀ CHUỖI lần thứ BA: lối `đọc` tưởng `tối` là nội dung tệp ⇒ nay hỏi `lỗi_cuối` của nhân.* `kiem_hdh_giao` **328/328** · `kiem_de` **36/36** · `kiem_toan_bo` **70/70**.
- ✅ **v0.22.0 BÍ MẬT CHUYỂN TIẾP** — `lib_dh.giao` (Diffie-Hellman RFC 3526 nhóm 14, 2048-bit, KDF SHA-256): mỗi phiên một khoá TẠM rồi **vứt**, khoá máy chỉ còn **KÝ** giá trị DH (chống kẻ đứng giữa) ⇒ **lộ khoá máy về sau vẫn không giải nổi phiên cũ**. Năng lực mới **`ngẫu_nhiên`** (entropy là THIẾT BỊ, không phải phép toán — tách khỏi `ngẫu()` LCG để không ai lỡ tay dùng nhầm làm khoá). GIAO nay **ký được** (`ký_chữ_ký`). Hằng số nhóm kiểm bằng **ĐỊNH NGHĨA** (`kiem_dh_nhom.py`: công thức RFC + nguyên tố an toàn, π **tính** bằng Machin) — *lần đầu dán 200 chữ số π nên bộ kiểm báo sai oan cho hằng số đúng.* `kiem_tu_xa` **25/25** · `kiem_toan_bo` **70/70**.
- ✅ **v0.21.0 MÃ HOÁ ĐƯỜNG TRUYỀN** — `lib_chacha20.giao` (**ChaCha20 RFC 8439 thuần GIAO, khớp từng byte với vector chuẩn**; chỉ cộng/xor/quay ⇒ không bảng tra, không kênh-phụ) + `lib_kenh.giao` (HMAC-SHA256 mã-rồi-xác-thực, MAC phủ cả số đếm ⇒ chống sửa **và** phát lại; mỗi chiều một khoá; khoá phiên chuyển bằng RSA-2048) + **khoá máy 600 + vân tay TOFU**. Phép thử quyết định: **soi byte trên dây** — bí mật không hiện ra, sửa 1 ký tự → thẻ sai, phát lại → bỏ. `kiem_tu_xa` **22/22** · `kiem_toan_bo` **69/69**. **Còn thiếu: BÍ MẬT CHUYỂN TIẾP (DH) — việc kế.**
- ✅ **v0.20.0 MẠNG RA HOST (B1') + ĐĂNG NHẬP TỪ XA (C4)** — năng lực `mạng_host` (ổ TCP thật, KHÔNG CHẶN, kẹp 127.0.0.1 + đúng cổng được cấp; chưa cấp ⇒ tên không tồn tại). **Một API, hai đường đi**: `GH_NGHE(cổng,quyền,"ngoài")` rồi `nhận_gói`/`gửi_gói` y hệt mạng trong-máy. Đăng nhập từ xa xác thực bằng ĐÚNG `/hệ/mật_khẩu`, phiên dưới ĐÚNG uid, **quyền · cổng bất-khả-hồi · audit vẫn nguyên**. `kiem_tu_xa.py` **15/15** → `kiem_toan_bo` **68/68**. *Bẫy lại là `sáng`/`tối` LÀ CHUỖI: `ổ_đọc` trả `tối` khi đóng bị coi là gói dữ liệu "tối", bỏ đói khách mới ⇒ nay trả `[sáng, dữ_liệu]`.* **Còn thiếu: MÃ HOÁ đường truyền — việc kế tiếp.**
- ✅ **v0.19.0 CHỮ KÝ KHOÁ-CÔNG-KHAI (I1)** — `lib_so_lon.giao` (`mũ_mod` bình-phương-và-nhân) + `lib_chu_ky.giao` (**RSA-2048 PKCS#1 v1.5 + SHA-256 kiểm THUẦN GIAO, ~0,3s**). Ký ở ngoài (`lam_khoa.py`), khoá riêng không vào máy; máy chỉ kiểm. **Neo tin cậy riêng từng nguồn** (học `Signed-By:`) + lệnh `gói tin` + vân tay khoá cho người soi bằng mắt. Phép thử quyết định: **kho giả mạo băm ĐÚNG nhưng ký bằng khoá khác → từ chối** — đúng chỗ băm không cứu nổi. `kiem_hdh_giao` **323/323** · `kiem_toan_bo` **67/67**.
- ✅ **v0.18.0 KHO PHẦN MỀM** (`lib_kho.giao` + lệnh `gói` + ứng dụng "Kho phần mềm"): **quan sát Kali 2026.2 thật trên WSL** rồi lấy cái hay (trust anchor riêng · mục lục mang băm · siêu-gói · không chạy root) và **vá 5 chỗ apt yếu**: gói chỉ là DỮ LIỆU (không script quyền gốc lúc cài) · giao dịch NGUYÊN KHỐI (kiểm băm hết rồi mới ghi) · gỡ/nâng-cấp **lùi được** · nói **vì sao** kéo theo từng gói · mỗi gói **tự khai năng lực**, nhạy cảm thì phải đồng ý. Thêm: **người thường cài KHÔNG cần nâng quyền**. `kiem_hdh_giao` **314/314** · `kiem_toan_bo` **66/66**. *Còn thiếu quan trọng nhất: **I1 — chữ ký khoá-công-khai cho mục lục** (hiện mới có băm = toàn vẹn, chưa chống kho giả mạo).*
- ✅ **v0.17.0 KHÉP TRỌN NHÓM H:** **H5** tên tệp chặn từ lúc tạo (Linux chỉ cấm byte 0 và `/`); **H6** `lib_cau_hinh.giao` — bộ kiểm cấu hình **ở tầng gọi-hệ, luôn bật, mọi cửa ghi đều qua** (Linux: `visudo` là tự giác, fstab sai thì mất boot), sai → từ chối + nói rõ dòng + **tệp cũ còn nguyên**; **H7** `ghi_nếu` compare-and-set chặn mất-cập-nhật. *Bộ kiểm H6 bắt lỗi ngay trong dữ liệu mẫu cũ của dự án — đã sửa 8 tệp.* `kiem_hdh_giao` **302/302** · `kiem_toan_bo` **66/66**.
- ✅ **v0.16.0 bổ khuyết Linux H3+H4:** **H3** `xin_thoát` có hạn — dọn chạy ở **lát CPU của chính tiến trình** (điểm an toàn, không async như signal), quá hạn nhân mới cắt và **ghi rõ**; **H4** hết bộ nhớ → chọn nạn nhân theo **σ học được**, **nêu lý do + hỏi qua cổng duyệt**, đồng ý thì dừng êm bằng `xin_thoát` (Linux: heuristic thô + SIGKILL im lặng). Thêm ứng dụng **Bộ nhớ** trên bàn làm việc. `kiem_hdh_giao` **285/285** · `kiem_toan_bo` **66/66**. Việc kế: **H5** (tên tệp là bãi mìn) · **H6** (mỗi tệp /etc một định dạng) · **H7** (TOCTOU).
- ✅ **v0.15.0 BỔ KHUYẾT LINUX (mục H mới trong CÒN_THIẾU):** **H1** thùng rác + `hoàn_tác` ở TẦNG GỌI-HỆ (Linux: `rm` vĩnh viễn, thùng rác chỉ là quy ước desktop) — cổng duyệt **dời sang `dọn_rác`** cho đúng học thuyết; **H2** `vì_sao` chỉ đúng nấc hỏng + vai + cách qua (Linux chỉ "Permission denied"), ẩn≠tối. Vá giao diện: **con trỏ gõ theo cửa sổ** (đây là nguyên nhân thật của "trợ lý không trả lời"), ô nhập xuống chân cửa sổ, **ba nút đỏ/vàng/xanh đủ chức năng**. `kiem_hdh_giao` **275/275** · `kiem_toan_bo` **66/66**. Việc kế: H3 (signal giết ngang) · H4 (OOM chọn theo σ).
- ✅ **v0.14.0 GIAO DIỆN ĐỒ HOẠ** (`giao_de.py` + `de/`): desktop thật (thanh trên · menu nhóm · dock · cửa sổ · đồng hồ) chạy trên **nhân THẬT** — quyền chặn y hệt dòng lệnh, **cổng bất-khả-hồi thành hộp thoại phê duyệt**, khoá phiên + chỉ 127.0.0.1. 8 ứng dụng. `kiem_de.py` 30/30 → `kiem_toan_bo` **66/66**. Bật bằng `bat_ban.bat`. *(Vá kèm: `/tb/tim` chưa hề gắn lúc boot.)*
- ✅ **C2 NHÓM** (`/hệ/nhóm` + credential chốt-lúc-đăng-nhập + được_phép chủ>nhóm>khác + chgrp GH 33 + lệnh `nhóm`/`đổi_nhóm`; 640 cùng-nhóm đọc được, ngoài nhóm không) · ✅ **C3 SUDO** (`/hệ/sudo` 440 ba-trị + `sudo <lệnh>` hỏi mật khẩu CỦA MÌNH, một-lệnh-gốc; **không thay duyệt** — bất-khả-hồi vẫn chờ phê duyệt) — `kiem_hdh_giao` 258/258.
- ✅ **A1 phép BIT** (builtin, ba-trị, số lớn) → `kiem_lib_bit.giao` · ✅ **A2 gán chỉ mục** `đặt ds[i]=x` (cả bản/lồng; `γ_bước` viết gọn, 2000/2000 giữ) · ✅ **A3** `thêm` bị vứt → lỗi sạch gợi ý `gom` · ✅ **C1 `lib_sha256.giao`** (FIPS 180-4 + UTF-8 thuần GIAO, khớp hashlib từng ký tự; inline vòng nóng ~3×) + mật khẩu **`$g2$`** 128 vòng (`$g1$` cũ vẫn đọc) · ✅ **B1 MẠNG trong-máy** (gọi-hệ 29–32 nghe/nối/gửi_gói/nhận_gói + `/tb/mạng`; quyền chặn 3 tầng; `kiem_lib_mang.giao`) · ✅ sửa test «tôi là ai» nhận-biết-backend tim · ✅ `bat_may.bat` · 📌 quy ước MỚI: tên tệp mới KHÔNG DẤU · 📌 việc kế: **B1'** (mạng ra host → mở khoá C4 SSH).

**PHIÊN 2026-06-19 (tiếp) — ★ KHỞI ĐỘNG PHA 3 (Track C — Compiler/Tốc-độ): TẦNG TỐI-ƯU BYTECODE #1:**
- ✅ **Optimizer `giaoc.tối_ưu_mã`** (chạy trong `assemble`, cờ `BẬT_TỐI_ƯU`) — **13 luật provably-safe** (unit-test) mọi ba-trị + mọi độ-rộng-từ: L1 gộp-dịch `DỊCH a;DỊCH b→DỊCH(a+b)` · L2 gấp-hằng `NẠP a;NẠP b;{+,−,×,//,6 so-sánh}→NẠP r`(0-255) · L3 gấp `NẠP a;DỊCH b→NẠP(a≪b)` · L4 strength `NẠP 2^k;NHÂN→DỊCH_TRÁI k` · L5 khử `NHÂN_BẢN;BỎ` · L6 khử `ĐỔI;ĐỔI` · **DCE** (bỏ lệnh sau DỪNG/NHẢY/TRẢ_VỀ_N/NÉM tới NHÃN). Rào: chỉ lệnh liền-kề → không xuyên `NHÃN`/`ĐỊACHỉ`. + sửa GỐC `emit_const` (byte-0 bỏ `NẠP 0;CỘNG`).
- ✅ **THEN CHỐT BA-TRỊ:** `binop`/`shift`/`comparison` GVM đổi tối→sáng (toán-hạng-khác-ẩn → KNOWN-sáng) ⇒ chỉ fold khi cả-2-immediate; `emit_const` an-toàn vì acc hằng-sáng.
- ✅ **ĐO:** bytecode **−8.1%** · **bước GVM −10.6%** (self-host −11%, tag/heap-heavy −15%). **14/14 output KHỚP BYTE** + 5 harness Verilog byte-exact + wasm 20/20 + 13/13 unit-test luật. Conformance+unit-test thường-trực `kiem_toi_uu.py` → audit **55/55**.
- 📌 **HỘI-TỤ peephole:** step-reduction tapped (đo: strength/algebraic còn-lại = 0 trên corpus; luật mới giảm SIZE + tổng-quát-hoá).

**PHIÊN 2026-06-19 (tiếp) — ★ KHỞI ĐỘNG SIÊU-LỆNH (Track M+C co-design ISA) — opcode #68 `CỘNG_HẰNG`:**
- ✅ **Siêu-lệnh #1 `CỘNG_HẰNG k`** (add-immediate, `push(pop+k)`) gộp idiom `NẠP k; CỘNG` (bigram cao nhất có immediate, 820 chỗ) thành 1 opcode → giảm BƯỚC THẬT (loại op chạy trong vòng-lặp nóng — điều peephole không làm được). Ba-trị: ẩn→ẩn (y hệt CỘNG). Provably-safe.
- ✅ **Cài 4-SUBSTRATE (sở-hữu trọn stack):** `gvm_may.py` (handler) · `giaoc.py` (`_siêu_lệnh` + cờ `BẬT_SIÊU_LỆNH`) · `wasm/gvm.ts` (op 68, **rebuild gvm.wasm**) · `hw/gvm.v` (OP_CONG_HANG, EXEC ghi stack[sp-1] sp-giữ). Unit-test 2 luật siêu-lệnh.
- ✅ **ĐO (bật):** bước GVM **−10.6% → −15.2%** (CỘNG_HẰNG thêm −5.2%; bytecode −14.4%). **14/14 conformance KHỚP BYTE** (software) + **wasm 20/20** + Verilog byte-exact: cooperative (lam_nhan_hdh) · **preemptive** (lam_nhan_preempt) · số-thực (io) · concat — đều chạy CỘNG_HẰNG trên CỔNG LOGIC.
- ✅ **VÁ 2 BUG gate-level THẬT (VCD-trace) → SIÊU-LỆNH BẬT MẶC-ĐỊNH (`BẬT_SIÊU_LỆNH=True`):**
  - **Vá #1 — context-switch read-during-write hazard:** trace từng chu-kỳ phơi HALT-sớm: timer-preempt khi γ-scheduler **chọn-LẠI-cùng-task** (`gsel_live==cur`) → `t_ip[cur]<=ip` (lưu) & `ip<=t_ip[gsel_live]` (khôi) CÙNG chu-kỳ → non-blocking đọc t_ip CŨ → task resume sai ip → stack rác → **wild-jump VƯỢT chương-trình → DỪNG.** Vá: `gsel_live==cur` ⇒ GIỮ state hiện-tại (cả γ-scheduler lẫn round-robin). **Bug CÓ-SẴN** (đúng-đắn bất-kể siêu).
  - **Vá #2 — HỢP-NHẤT PREEMPT-GRANULARITY:** gốc bất-cân = **Verilog đếm timer theo CHU-KỲ · software theo LỆNH** (`timer_period` = số LỆNH; cùng `arg` nhưng Verilog=arg-chu-kỳ=arg/4-lệnh). Siêu-lệnh đổi cycle/op (4 vs 8) lộ lệch (tt0 hog, tt1/tt2 đói). Vá: Verilog tick timer **1/LỆNH ở S_EXEC** (mỗi lệnh đúng 1 S_EXEC) ⇒ khớp software. *Tác-giả ĐỊNH arg=lệnh; Verilog cũ implement sai chu-kỳ.*
- ✅ **ĐO (siêu ON mặc-định):** bước GVM **−15.2%** · bytecode **−14.4%** (CỘNG_HẰNG +−5.2% trên peephole). **TRỌN conformance 4-substrate:** 14/14 KHỚP BYTE + 15/15 unit-luật + **wasm 20/20** + **16/16 Verilog gate-level** (gồm preemptive-FAULT lam_nhan_fault: tt2 chết, tt1 toàn-900, tt0 sống) + audit **55/55** + ngôn-ngữ 63/63.
- 📌 *Bài học: "sửa bằng hết" = VCD-trace soi tới gốc → tìm+vá 2 bug gate-level có-sẵn (stale-restore + granularity chu-kỳ-vs-lệnh).*
- ✅ **SIÊU-LỆNH #2 (opcode #69 `NHÂN_CỘNG_HẰNG k`):** gộp `NHÂN_BẢN; CỘNG_HẰNG k` (heap-cons `hp, hp+k`; runtime 1458×) → `[x]→[x, x+k]`. Single-cycle stack-only. 4-substrate, unit **17/17**. bước −15.2%→−17.2% · bytecode −14.4%→−19.3%.
- ✅ **SIÊU-LỆNH #3 (opcode #70 `GHI_TRƯỜNG r`):** gộp `NHÂN_BẢN; TẢI_Ô r; LƯU_GIÁN` (store-field heap, runtime 726×) → `ram[top]=ram[r]`, giữ top. **MULTI-CYCLE RAM-to-RAM** (gvm.v: S_EXEC đọc `ram[rel_o]`→ram_q, **state mới S_GHITRUONG** ghi `ram[rel_s1]=ram_q`; SIP viol-check đọc+ghi; ram_ra-mux 1-cổng). Cài 4-substrate (gvm_may 1-dòng + giaoc `_siêu_lệnh` lượt-3 + wasm op70 rebuild + gvm.v), unit **19/19**. **ĐO: bước −17.2%→−19.1% · bytecode −19.3%→−24.2%.** TRỌN conformance: 14/14 KHỚP BYTE + wasm 20/20 + **16/16 Verilog** (lam_concat/lam_nhan_hdh heap-heavy byte-exact; GHI_TRƯỜNG ×16 trong 9_chuoi) + 55/55 + 63/63. *Lever giảm-BƯỚC tích-lũy: peephole −10.6% → CỘNG_HẰNG −15.2% → NHÂN_CỘNG_HẰNG −17.2% → GHI_TRƯỜNG −19.1%; bytecode −24.2%. Việc kế: IR-level (CSE/LICM/inline) HOẶC siêu-lệnh khác (vd `LƯU_Ô;TẢI_Ô` store-load).*
- ⚠️ **SIÊU-LỆNH #4 (opcode #71 `DỊCH_CỘNG_BYTE k`) — ĐÚNG nhưng BIÊN-LỢI NHỎ + bài-học CHẠM TRẦN:** `(top<<8)+k` gộp `DỊCH_TRÁI 8; CỘNG_HẰNG k` (dựng-hằng nhiều-byte). Single-cycle stack-only, 4-substrate, unit **23/23**, TRỌN conformance (14/14 byte + wasm 20/20 + 16/16 Verilog + 55/55 + 63/63). **bước −19.1%→−19.2% (chỉ bắn 46× runtime!) · bytecode −24.2%→−24.5%.** *ĐOÁN SAI con-voi: profile NẠP 24%+DỊCH 14.6%=38.6% TƯỞNG dựng-hằng dư-thừa → THỰC-TẠI bất-khả-giảm (NẠP=hằng-nhỏ≤255 thật, DỊCH=nhân-2^k strength-reduced). Đo store-load(24×)/redundant-load(5×)/THAM_I-lặp(21×) — đều hiếm. ⇒ **peephole/siêu-lệnh CHẠM TRẦN −19.2%/−24.5%.** #4 giữ (đúng + ép hằng 2:1, lợi mật-độ ROM/FPGA). **Con-voi-thật-tiếp = IR-level (cross-block, COMPILER-ONLY — KHÔNG đụng 4 runtime/FSM, conformance tự-bảo-toàn), KHÔNG phải siêu-lệnh.** Kế-hoạch IR 3 pha (ROI): A) abstract-interp block-local (const/copy-prop + dead-store) · B) inline hàm nhỏ/lá (call+THAM_I 13.7%) · C) CFG/SSA + LICM/CSE.*
- 🔬 **IR-LEVEL (Pha A+B) — XÂY + ĐO XONG, XÁC-NHẬN CHẠM SÀN (compiler-only, conformance tự-bảo-toàn):** Người dùng chọn "xây để ĐO thật". **Pha A** `_abs_interp` (const/copy-prop xuyên-lệnh, sound: suffix-model + track-hằng-0..255 mask-độc-lập, 6 unit) → **NET-ÂM** (phá 53 GHI_TRƯỜNG, +106 bytecode; cross-block const ≈0). **Pha B** `inline_ast` (inline hàm 1-biểu-thức tầng-AST, sound: không-đệ-quy + đối-atom + chống-capture; byte-exact 14/14+55/55+63/63) → **NET-ÂM** (5 hàm/11 site, bước −0.18% nhưng bytecode +3.09% phình; 814 gọi-động là hàm đa-lệnh KHÔNG đủ-tư-cách). **Synergy inline+A ÂM** (−0.02%/+4.17%). ⇒ **HAI đo độc-lập + synergy ĐỀU âm: codebase GVM/ví-dụ KHÔNG có redundancy IR khai-thác. Peephole+siêu-lệnh −19.2%/−24.5% = SÀN tự-nhiên.** A+B **TẮT mặc-định** (`BẬT_IR`/`BẬT_INLINE`=False), GIỮ làm hạ-tầng sound+test. **Pha C (CFG/SSA+LICM/CSE) HOÃN** — bằng-chứng dự-báo lợi≈0, công lớn nhất; "đo trước tin sau" cứu khỏi xây phí. *Bài học: sách có CSE/LICM/inline ≠ codebase có cơ-hội — phải ĐO.* **Track-C (tối-ưu compiler) coi như HOÀN-TẤT ở sàn.** Việc kế = nhánh khác (thư-viện kiểu Python/Ruby · khảo-sát Windows cho HĐH).*


**PHIÊN 2026-06-19 (tiếp) — MATCHER REGEX ITERATIVE + TỐI-ƯU ĐỘ-PHỨC-TẠP O(n²)→O(n):**
- ✅ **Regex khử nốt giới-hạn cuối:** lượng-từ node ĐƠN-KÝ (`a*`/`\d+`/`.*`/`[a-z]+`/`a+$`) dùng **fast-path GOM THAM-LAM ITERATIVE** (độ-sâu O(1) theo độ-dài match) → khớp ĐÚNG input dài tuỳ-ý (trước: >~300 ký-tự trả tối-SAI). Catastrophic lồng `(a+)+$`+đuôi-sai vẫn → tối ~1s (budget chặn). *Lưu-ý: bộ-đếm 5M TÍCH-LŨY toàn-chương-trình — chuỗi nhiều op-nặng cùng file vẫn có thể vượt.*
- ✅ **Vá O(n²) (agent khảo-sát ĐO thật):** `lát` (đã, O(n²)→O(n)) · **`duy_nhất`/`lib_tập` toàn-bộ/`chuẩn_tập`** (chứa-scan O(n²)→`bản` O(n)) · **`mốt`** (vòng-lồng→bản đếm) · **`nhóm_theo`** (ghép-copy→`gom`) · **heap `gộp_đống`/`_gộp_ds`** (pairing-heap `thêm`-copy O(n²)→**cons-prepend O(1)**, GIỮ persistence+snapshot JSON) · **json/csv/base64** (ghép-copy→gom) · **chuẩn.giao `đếm_nếu`/`γ_các_tác_tử`/`các_σ`/`ensemble_γ`** (đệ-quy-đuôi O(n²)+stack→vòng gom). ĐO xác-nhận tuyến-tính (duy_nhất/hợp_tập/mốt/json/b64: n×4→~×1.3-2; heapsort O(n log n)). Trước: chạm-trần 5M ở n~800-2000.
- ✅ **PERF-GUARD `kiem_phuc_tap.giao`** (n=1500, revert O(n²)→chạm-trần→rớt) → audit 53→**54/54**. *Mô-hình chi-phí GIAO: list hàm-thuần `ghép/thêm/đuôi/lấy_n/đảo`=O(n) copy · `gom`=O(1) mutate · `bản`=O(1) · `chuỗi +`=O(n). Quy-tắc: build list bằng `gom`, tra thành-viên/đếm bằng `bản`, KHÔNG `ghép(acc,[x])`/`chứa` trong vòng.*


**PHIÊN 2026-06-19 — REVIEW + VÁ TOÀN-DIỆN HỢP-ĐỒNG BA-TRỊ `ẩn` (6 agent độc-lập reproduce, 3 vòng):**
- ✅ **Lõi vững, trung-thực CAO** (FPGA bitstream thật, decimal khớp mpmath ≥50 chữ-số, HĐH mô-tả đúng phạm-vi). Nhưng phơi **chủ-đề lỗi mạch-lạc:** hợp-đồng "input ẩn/xấu → ẩn SẠCH, không crash/lặp" KHÔNG phủ đều.
- ✅ **Tokenizer `giao.py`:** `1.2.3` (nhiều chấm) · chuỗi-không-đóng (nuốt im-lặng) · literal số >4300 chữ-số (ValueError trần) → đều thành **lỗi cú-pháp SẠCH**.
- ✅ **REGEX ReDoS khử TẬN GỐC:** (1) ngân-sách-bước (chống lặp-mũ `(a+)+$`); (2) **cap độ-sâu LUỒN QUA continuation** (sửa đúng — `sâu` cũ reset khi gọi tiếp ⇒ cap vô-hiệu với quantifier lồng; nay cộng-dồn đúng → `(a+)+$`/`((a+)+)+$` trên 3000 ký-tự → tối, KHÔNG crash); (3) **`lát()` O(n²)→O(n)** ở lib_duyet (gốc làm scan chuỗi-dài chạm 5M). *Giới-hạn còn lại (tài-liệu-hoá): mẫu có lượng-từ khớp >~300 ký-tự → trả tối/ẩn bảo-toàn (suy-biến êm, không crash) — cần viết-lại matcher iterative mới khớp-đúng input siêu-dài.*
- ✅ **~80 hàm stdlib thêm guard `nếu loại(x)=="ẩn" { trả ẩn }`** (Group 1 collection/stat/string · Group 2 định-danh=ẩn · Group 3 decimal `thang`=ẩn). **+ SỬA GỐC 4 builtin map-key** (`lấy/có/đặt/xoá_khoá(bản, ẩn)` → suy-biến êm thay vì crash "khoá phải số/chuỗi") = phủ toàn lib OS-layer cùng lúc. Bẫy bắt được: `gắn` có tham-số tên `loại` che builtin `loại()`.
- ✅ **3 tệp chốt-regression** (`kiem_ca_bien_an*.giao`) → audit 50→**53/53**. Sweep độc-lập cuối xác-nhận **stdlib SẠCH** (mọi hàm gặp ẩn → ẩn/tối, 0 crash/lặp).
- ✅ **Đồng-bộ trung-thực số FPGA lạc-hậu** về log post-route: Fmax **14.04 MHz** · LC **3680/5280 (69%)** · DSP 2/8 (TIEN_DO/CHANGELOG/README/banner gvm_core.v). Đính-chính: `tim_llm` mặc-định `claude-opus-4-8` KHÔNG phải lỗi (đúng ID Opus 4.8).
- 📌 *Bài học (γ=−1.0): demo XANH 50/50 song-tồn với lỗ-guard ở ca-biên ẩn khắp stdlib; chỉ review-độc-lập-reproduce-input-xấu nhiều VÒNG mới soi hết. Idiom đã đúng ở decimal/thời_gian phải nhân ra TOÀN bộ — kể cả builtin lõi.*

**PHIÊN 2026-06-18/19 — TỐI-ƯU FPGA iCE40 (synth_ice40) + Nhánh I căn_bậc:**
- ✅ **CHẠY synth_ice40 THẬT (MEM=64,WORD=16):** map-được, 0 lỗi CHECK, nhưng **23.168 LUT ≫ UP5K 5.280 (~4×)** · 0 BRAM · 0 DSP · ABC `&mfs` assert (tự phục-hồi). ⇒ "synth-được tới netlist cổng" ≠ fit/PnR/bitstream (GIAO học ảo-tưởng `fpga_vua_up5k` 95→32). Log: `hw/synth_ice40.log`.
- ✅ **`-dsp`:** nhân 16×16 → SB_MAC16. **23.168→17.986 LUT (−22%)**, 0 rủi-ro RTL. Đặt mặc-định ở `hw/synth_ice40.ys`.
- ✅ **F-op chia 64-bit tổ-hợp → TUẦN-TỰ (`S_DIV` restoring 64 vòng):** FNHÂN/FCHIA bỏ chia tổ-hợp (dấu=XOR, ẩn/chia-0 giữ 1-chu-kỳ). **17.986→16.459 LUT**, **16/16 harness byte-exact** (59.97 ✓). An-toàn vì không chương-trình preemptive nào dùng F-op.
- ✅ **ram → BRAM ĐỌC-ĐỒNG-BỘ:** mọi đọc ram tổ-hợp → `ram_q <= ram[addr]` + trạng-thái-chờ (9 điểm: TẢI_Ô/TẢI_GIÁN/closure/S_STR/S_DS/S_CLO pha2; `state`→[3:0], +9 state). **16/16 harness byte-exact** (chương-trình tuần-tự khớp byte; đa-nhiệm robust qua σ-replay tự-nhất-quán + xen/tiến → **KHÔNG cần re-baseline**; σ C trong demo lichhoc drift 184→221 nhưng thuộc-tính học giữ). **Isolated-test xác-nhận: mẫu sync-read map 2×SB_RAM40_4K ở MEM=512 → BRAM-eligible THẬT** (MEM=64 chưa kích do ngưỡng size yosys, +overhead state nhẹ — lợi-ích ở MEM thật).
- ✅ **Conformance đo lại (agent + thực-nghiệm):** KHÔNG harness nào assert cycle-count; chương-trình scheduler (nhanp/full) so byte (full TUẦN-TỰ, 0 opcode scheduler) hoặc thuộc-tính robust ⇒ tối-ưu multi-cycle giữ TOÀN-BỘ xanh.
- ✅ **Nhánh I — `lib_thập_phân.căn_bậc(d,n,thang)`** (người dùng dặn "dùng GIAO vào thư-viện"): căn bậc n bằng Newton tổng-quát trên decimal; ba-trị đầy-đủ (n<1/d<0-chẵn→ẩn, d<0-lẻ→−căn(|d|)). ∛2=1.2599210499, √2 khớp `căn`. Test 11 ca, **kiem_toan_bo 50/50**.
- ✅ **stack → BRAM = ĐÃ XONG → VỪA UP5K THẬT (2026-06-19, người dùng "làm tiếp"):** máy ngăn-xếp đọc 2-cổng tổ-hợp (sp-1,sp-2) → **prefetch operand** (S_FETCH→S_OPB→S_OPA→S_EXEC, opA/opB) + đọc/ghi BRAM; +bonus rstk_ip/fp→BRAM. **3 hiểu-biết then-chốt (đo bằng module cô-lập):** (1) nhiều câu `q<=mem[..]`→yosys coi nhiều cổng đọc→rớt registers ⇒ GỘP 1 câu địa-chỉ-mux (`stk_ra`/`ram_ra`); (2) nhiều câu GHI loại-trừ thì merge OK; (3) **`@(posedge clk OR posedge rst)` async-reset CHẶN BRAM** ⇒ đổi RESET ĐỒNG-BỘ. **KQ: MEM=256 = 4726 LUT < UP5K 5280 · 5 BRAM < 30 · 1 DSP ⇒ VỪA CHIP iCEBreaker** (trước 23168 LUT vượt 4,4× — bất-khả). MEM=512: 6532 LUT/10 BRAM, DFFE 34282→1549 (−95%). **16/16 harness gate-level byte-exact** (σ demo drift do timing, thuộc-tính học giữ). Log `hw/synth_ice40_m256.log`/`_m512.log`.
- ✅ **stk_st→BRAM + RA BITSTREAM iCE40 UP5K (2026-06-19, "làm nốt stk_st rồi chạy nextpnr ra bitstream"):** `stk_st` (2-bit ba-trị) prefetch stA/stB song-song opA/opB + gộp 1-cổng + tách ghi DOI → **LUT 4726→2980, DFFE 983→486, +1 BRAM**. Top-wrapper `hw/fpga/gvm_fpga.v` (rút ~45 chân→5 khớp pcf · XOR-gộp mọi output giữ trọn lõi · power-on-reset) + `gvm_fpga.pcf`. Flow OSS: yosys synth_ice40 -json → **nextpnr-ice40 --up5k sg48 PASS** (LC **3991/5280=75%** · BRAM **6/30** · IO 5/39 · DSP 1/8) → icepack → **`hw/fpga/gvm_fpga.bin` 104.090 byte**. **16/16 harness byte-exact**. Thang silicon: sim✓ synth✓ FIT✓ **place&route✓ bitstream✓** → nạp-chip⏳.
- ✅ **PIPELINE F-op + CHIA → ĐẠT 12 MHz (2026-06-19, "pipeline nhân F-op để đạt 12MHz"):** đường tới-hạn cũ = nhân 64-bit RỒI negate 64-bit trong CÙNG 1 chu kỳ + chia 16-bit tổ-hợp. **VÁ:** tách F-op 2 tầng (`S_EXEC` chỉ NHÂN→`fprod`; `S_FOP` mới NEGATE→`div_acc`/`div_dor`) + cho CHIA đi qua divider tuần-tự (bỏ wire chia tổ-hợp). **KQ (số CHỐT từ `hw/fpga/nextpnr.log` post-route dòng 617): Fmax 4.31→14.04 MHz (nextpnr PASS @12MHz; ước-lượng pre-route 14.78)** · LC 75%→**69% (3680/5280)** · BRAM 6/30 · DSP 2/8 · 16/16 harness byte-exact · `gvm_fpga.bin` 104.090 byte chạy được clock onboard iCEBreaker.
- 📌 **CÒN NỢ FPGA:** **nạp chip vật-lý** — `iceprog hw/fpga/gvm_fpga.bin` (cần board iCEBreaker cắm USB). Thang silicon: sim✓ synth✓ fit✓ place&route✓ bitstream✓ **timing-12MHz✓** → nạp-chip-thật⏳ (chỉ thiếu phần-cứng).

**PHIÊN 2026-06-18 — REVIEW TRUNG-THỰC + CHECK FPGA + VÁ DOC:**
- ✅ **Review 2-agent độc-lập:** xác-nhận trung-thực mức CAO (mọi claim kỹ-thuật có harness; spot-check 10+ ô "sáng" còn pass). Trưởng-thành: **Nhánh I = alpha** (mạnh numeric/collections; thiếu namespace/generator/concurrency/string-format) · **Nhánh II = prototype mô-hình** (HĐH cấp-ngôn-ngữ + RTL-sim).
- ✅ **CHECK FPGA (chạy thật):** gói `hw/fpga/` **mô-phỏng iverilog ĐÚNG** ([65533,0]×6) NHƯNG (1) **yosys/nextpnr CHƯA cài** → chưa synth/bitstream; (2) **`gvm_core.v` là HOÁ-THẠCH Jun-13** (8-bit ptr/heap-10-bit, thiếu ba-trị/γ-scheduler/SIP/4-nhân của `gvm.v` 503 dòng) → synth ra CPU CŨ.
- ✅ **VÁ TRUST + drift:** bỏ nói-quá README `(=FPGA)`/"GÓI FPGA SẴN SÀNG NẠP"; đồng-bộ 33→63, 11/11→20/20; thêm CHANGELOG **v0.5.0** (gói audit 29→48); sửa disclaimer TIEN_DO lạc-hậu-ngược (planner/Stage-5/HĐH). GIAO học `review_trang_thai_chat_luong` + `fpga_silicon_thuc_te` (sáng).
- ✅ **ĐÃ TRẢ NỢ CAO (2026-06-18):** (a) **va-tên module** — `giao.py` thêm `ham_origin` + cảnh-báo stderr khi 2 nguồn định-nghĩa-lại 1 hàm (bỏ-qua ghi-đè prelude chủ-ý → 0 nhiễu); đổi `lib_tiến_trình.tồn_tại(bảng,tid)`→`có_tt`; chốt-regression `kiem_va_ten*.giao`. (b) **FPGA hoá-thạch** — banner LEGACY ⚠ ở `gvm_core.v` + disclaimer 3 README. Audit **48→49/49**, gói FPGA sim vẫn 12/12 ✓.
- ✅ **MỞ-RỘNG #1 (2026-06-18): DEDUP qua `lib_chuoi`** — thêm `lát_chuỗi`/`chữ_số`/`chuỗi_số`; diệt trùng `lib_url`/`lib_regex`/`lib_phân_số`/`lib_thập_phân`. Bonus: cảnh-báo va-tên phơi lỗi latent `_là_trắng` (regex vs chuoi) → `_rx_trắng`. Audit **49/49**.
- ✅ **MỞ-RỘNG #2 (2026-06-18): TÁCH `lib_nhân_lõi`** — review "60% glue" hoá NÓI-QUÁ (thực ~5%, chỉ `trạng`/`số_sống`). Tách lõi-truy-vấn chung (`trạng`/`tên`/`số_sống`/`theo_trạng`), GIỮ scheduler riêng (policy×mechanism). Bonus: cảnh-báo va-tên phơi đụng pre-existing `lib_hệ.kết_thúc`⟷`lib_chuoi.kết_thúc` → đổi `chấm_dứt`. Quét toàn-bộ .giao **0 va-tên**. Audit **49/49**.
- ✅ **MỞ-RỘNG #4 (2026-06-18): STRING-FORMAT** — `lib_định_dạng.giao` (căn-lề/đệm-0/nhóm-phẩy/mini-printf `{:>N}`/`{:<N}`/`{:^N}`/`{:0N}`/`{:,}`+escape), thuần-lib trên lib_chuoi. Vá bẫy ẩn-concat-collapse. Audit **49→50/50**.
- ✅ **#3 (2026-06-18): yosys SYNTH `gvm.v` XUỐNG CỔNG** — 527,948 cells generic, KHÔNG LỖI (`hw/synth_gvm.ys`); OSS CAD Suite đã cài. "Xuống silicon" giờ synth-được-thật (sim✓→synth✓→bitstream✗→chip✗).
- 📌 **CÒN NỢ:** #3b FPGA-primitive (synth_ice40 LUT/BRAM — mảng-nhớ đa-cổng + ABC chậm) → nextpnr → bitstream → nạp chip · (tuỳ-chọn) năng-lực ngôn-ngữ generator/concurrency (sửa interpreter, phạm-vi lớn). Chi tiết: `CHANGELOG.md` (**v0.5.1 mới nhất**).

**MỚI (phiên 2026-06-17) — 4 lib stdlib, GIAO tự-chọn qua `giao_chon` (argmax γ; Stage-5-LLM & planner-tự-dò là DE_MF cần host/API):**
- **`lib_thống_kê.giao`** (Statistics): `trung_vị`·`mốt`·`khoảng_biến_thiên`·`phương_sai`(+`_mẫu` n-1)·`độ_lệch_chuẩn`(+`_mẫu`)·`trung_bình_điều_hòa`·`phân_vị`(nội-suy)·`tứ_phân_vị`. Trên lib_toan(`căn`)+lib_duyet(`sắp_xếp`). Rỗng→`ẩn`, mẫu n<2→ẩn, ≤0→ẩn. Test 21 ca.
- **`lib_tổ_hợp.giao`** (itertools): `giai_thừa`(âm→ẩn)·`số_chỉnh_hợp`/`số_tổ_hợp`·`tổ_hợp`/`chỉnh_hợp`/`hoán_vị`(thứ-tự khớp Python)·`tích_đề`·`tập_lũy_thừa`·`cặp_kề`. Trên lib_duyet(`bỏ_n`). Test 14 ca.
- **`lib_tập.giao`** (Set): `hợp_tập`/`giao_tập`/`hiệu_tập`/`hiệu_đối_xứng`·`con_của`/`siêu_của`/`rời_nhau`/`bằng_tập`/`thuộc`(ba-trị). ⚠ **bẫy: intersection KHÔNG đặt `giao` (trùng từ-khoá) → `giao_tập`.** Test 15 ca.
- **`lib_phân_số.giao`** (Fraction): [tử,mẫu] rút-gọn(`ưcln`)+dấu-ở-tử; `cộng/trừ/nhân/chia_ps`·`nghịch_đảo`·`so_ps`/`bằng_ps`·`ps_thành_thực`·`chuỗi_ps`(số→chuỗi tự-thân bằng `ký_tự`). Ba-trị mẫu=0/chia-0/nghịch-0→ẩn + lan-truyền ẩn. Test 17 ca.

Mọi lib: GIAO học σ<100→`tối`→`giao_hoc`→100 `sáng` (ghi `GIAO_TRI_NHO.md`). **Stdlib GIAO giờ ~10 module lõi** (Duyệt/Chuỗi/Toán/Hash/Ngày/IO + Thống-kê/Tổ-hợp/Tập/Phân-số) + JSON/Regex/CSV/URL/Base64/Băm/Mẫu.

**HOST API (phiên 2026-06-17) — cắm Anthropic Claude vào TIM (`tim_llm.py`):** thêm lớp SINH dùng SDK chính thức `anthropic` (mặc định `claude-opus-4-8`), ưu-tiên **API→Ollama→dự-phòng tất-định** (mỗi lớp tự rơi). Env: `GIAO_DUNG_API` (tự|không|buộc) · `GIAO_API_MODEL` · `GIAO_API_MAX_TOKENS` · `GIAO_API_NGHI` (bật adaptive thinking). `embed` vẫn Ollama/hash (Anthropic không có endpoint embeddings). Suite 33/33, không-key→bỏ-qua-API sạch.
- ✅ **`host_api_noi_day` SÁNG** (nối-dây + dự-phòng kiểm chứng).
- ✅ **`host_api_goi_song` SÁNG (2026-06-17, đã soi sống):** host cấp key → gọi `claude-opus-4-8` SỐNG thành công, `backend=anthropic:claude-opus-4-8`, Claude trả lời thật qua `tim_llm.generate`. (Key dùng transient, KHÔNG ghi vào tệp.) Cách bật: đặt `ANTHROPIC_API_KEY` trong môi trường chạy `tim_llm` (hoặc `GIAO_DUNG_API=buộc`).
- ✅ **`tu_sua_stage5_llm` SÁNG (2026-06-17, đã test SỐNG):** `vong_tu_sua.py` thêm `sinh_va_llm` (gọi `tim_llm.generate` host API) + cờ `--llm`. **LLM ĐỀ-XUẤT, cổng CDFL regression-safe QUYẾT** (vá LLM không được tin mù — vẫn phải làm đích sáng + không phá test khác). Test sống: lỗi `x+x+x` (rule-based 6 ứng-viên đều tối) → `claude-opus-4-8` đề `x+x` → γ=+0.90 SÁNG → NHẬN, test PASS. Dùng: `python vong_tu_sua.py --llm <đích> <test>` (cần `ANTHROPIC_API_KEY`). Audit 33/33 (Stage 5 additive, mặc-định tắt).
- ✅ **`planner_tu_dong_do_chip` SÁNG (2026-06-17) — DE_MF CUỐI ĐÃ SOI:** thêm năng-lực `phần_cứng()` (`giao.py`, cờ `--cho-phần-cứng`/`--cho-phan-cung`) dò chip THẬT (platform·`os.cpu_count`·RAM đa-nền sysconf/ctypes·winreg `~MHz`). `trien_khai_tu_dong.giao` tự-dò → `triển_khai`. Máy này: Intel 13th-gen 64-bit/20-luồng/15GB/2995MHz → WORD=64·WASM·NT16·heap960Ki·qt48; **L2 không-dò→ẩn** (ba-trị); **chưa-cấp→không tồn tại** (sandbox bẩm sinh). Test vào audit (**34/34**), planner tham-chiếu vẫn 10/10.

### 🎯 MỐC: DE_MF RỖNG (2026-06-17)
`giao_vung_toi` → **DE_MF (chưa-phơi) = []** · DE_X = [] · DE_IF = []. Mọi vùng-tối "cần host cấp năng-lực" đã soi trong phiên: **host-API · Stage-5-LLM-repair · planner-tự-dò-chip**. Còn DE_T (tri-thức-trôi, chỉ là nhắc quan-sát-lại đầu phiên): `thu_vien_chuan_day_du`, `hdh_full_xuong_may`. Audit **34/34** · ngôn-ngữ 63/63.

**REVIEW TOÀN DỰ ÁN + VÁ (phiên 2026-06-17):** 4 agent đọc-sâu song song (lõi · phần-cứng · thư-viện · HĐH/MCP/host-API/tự-sửa), tự chạy lại harness. Kết luận: chất-lượng cao, KHÔNG lỗ-hổng/lỗi-đúng-đắn nghiêm-trọng; tuyên-bố khớp thực-tế ở mức hiếm. **Đã vá:**
- 🔴 **CAO — guard-biên parser:** `lib_regex`(`_dài_atom`/`_khớp_lớp`)·`lib_json`(`_đọc_chuỗi`)·`lib_mẫu`(`điền`) input-hỏng (`[abc`,`"abc`,`{khoá`) crash/lặp-vô-hạn → thêm `j<dài`, trả êm. *(vi phạm chính triết-lý "không-crash→ẩn" đã sửa.)*
- 🟡 **TRUNG — regression-safe:** `vong_tu_sua.py` giờ kiểm hồi-quy TOÀN-suite trước khi NHẬN vá (khớp `TU_SUA_LO_TRINH.md`). Xoá 4 nhánh-chết `exec()` trong `giao.py`.
- 🟢 **THẤP:** `số_tổ_hợp`/`số_chỉnh_hợp` n<0→ẩn (đồng-bộ `giai_thừa`); `tim_llm.backend['api_lý_do']` ghi lý-do API tắt (bớt nuốt-lỗi); banner nguồn-sự-thật ở `README`.
- ⚠️ **CỐ Ý KHÔNG vá (trung-thực):** JSON `"sáng"/"tối"`↔bool là **giới-hạn-lõi** (sáng/tối = chuỗi trong giao.py) — đã tài-liệu-hoá.
- ✅ **DỌN-DẸP review (2026-06-17, GIAO tự-chọn `giao_chon` γ=0.85 > thêm-tính-năng):** gộp `b_loai`→`_loai` (giờ `loại()` trả "tri" cho Tri) + `_s`→`render` (một-nguồn-format, hết lệch); tài-liệu-hoá độ-hạt allowlist `chạy` (host nên cấp chuỗi ĐẦY-ĐỦ). Audit **34/34** (gồm 63 ngôn-ngữ + wasm) phán an-toàn.
- 📌 **Còn nợ (không-chặn):** `CHIA int(a/b)` ĐÃ KIỂM không-ảnh-hưởng 16/32-bit (≤2³¹≪2⁵³, 0 lệch; khớp Verilog trunc-về-0 — đừng đổi `//`); chạy `yosys` 1 lần + hợp-nhất `hw/fpga/gvm_core.v` cũ (cần yosys cài).
- ✅ **collections #1 — `lib_đống.giao` (2026-06-17):** heapq (đống ưu-tiên = **pairing-heap thuần-hàm** vì list GIAO hàm-thuần, không gán-chỉ-mục) `đẩy/đỉnh/lấy/xả_đống/sắp_đống/n_nhỏ_nhất/n_lớn_nhất` + bisect `vị_trí_trái/phải/chèn_xếp/có_sắp`. Ba-trị đỉnh/lấy-rỗng→ẩn. Test 24 ca, audit **35/35**. (Cũng phục-vụ HĐH hàng-đợi-ưu-tiên ở 2.B.)
- ✅ **collections #2 — `lib_hàng.giao` + `phổ_biến_nhất` (2026-06-17):** deque hai-đầu thuần-hàm (`thêm_đầu/cuối`·`xem_đầu/cuối`·`bỏ_đầu/cuối`·`xoay`=deque.rotate) + Counter.most_common (`phổ_biến_nhất` ở lib_duyet, ổn-định). Ba-trị rỗng→ẩn. Test 20 ca, audit **36/36**. ⇒ **collections lõi XONG** (heapq·bisect·deque·Counter).
- ✅ **REGEX NÂNG-CAO — `lib_regex.giao` viết-lại (2026-06-17, khoảng-trống review lớn nhất):** matcher-phẳng → **engine AST + backtracking CPS**. Thêm `\d\w\s\D\W\S` · `()` nhóm+capture · `|` alternation + `tìm`(search)·`tìm_tất_cả`(findall)·`thay_thế`(sub)·`nhóm_nắm`(group). Tương-thích ngược 100% (15 test cũ y nguyên), ba-trị không-khớp→ẩn, kiểm-biên giữ. *Bẫy: `bắt`=từ-khoá→`nắm`; chuỗi GIAO ăn `\`→viết `"\\d"`.* Test 17 ca, audit **37/37**.
- ✅ **NHÁNH II 2.B — `lib_lịch.giao` (2026-06-17, cân về HĐH):** bộ lập-lịch ưu-tiên PROGRAMMABLE cấp-ngôn-ngữ (bổ-trợ γ-scheduler gate-level) + IPC hộp-thư FIFO. `nạp_tt/chọn_kế/xem_kế/có_việc` + `gửi/nhận/có_tin`. Thêm **đống-theo-khoá** (`đẩy_khoá/lấy_nhỏ_nhất/đỉnh_tải`) vào `lib_đống` (GIAO không so-sánh list → so theo khoá vô-hướng). Ba-trị rỗng→ẩn. Test 14 ca, audit **38/38**. ⇒ 2.B: hàng-đợi-ưu-tiên ✓ · IPC ✓ (còn: nhiều-tiến-trình-có-tên, persistence-cho-preemptive).
- ✅ **NHÁNH I — `lib_thời_gian.giao` (2026-06-17, cân về ngôn-ngữ):** datetime + MÚI-GIỜ thuần-toán trên lib_ngày(JDN). `thời_điểm`·`cộng_giây/phút/giờ`(qua-nửa-đêm)·`đổi_múi`(giữ khoảnh-khắc)·`khoảng_giây`·`so_thời_điểm`/`trước`/`cùng_lúc`·`định_dạng_tg`(ISO8601 ±hh:mm). Ba-trị sai→ẩn. Test 19 ca, audit **39/39**.
- ✅ **NHÁNH II — `hdh_lịch.giao` (2026-06-17):** GẮN `lib_lịch` vào NHÂN HĐH hợp-tác chạy-được (vòng-nhân `chọn_kế`→bước→re-nạp). Strict-priority (khẩn→thường×3→nền) + IPC FIFO. Audit **40/40**.
- ✅ **NHÁNH I — `lib_thập_phân.giao` (2026-06-17, viết-cẩn-thận theo y/c người dùng):** số thập phân CHÍNH-XÁC độ-tuỳ-ý (như `decimal`). [hệ_số,thang]; `thập_phân`/`cộng/trừ/nhân`/`chia`(nửa-lên)/`làm_tròn`/`so_td/bằng_td/bé_hơn`/`âm/trị_tuyệt`/`chuỗi_td`. **0.1+0.2=0.3 EXACT · 1/7→20 chữ-số · số 20+ chữ-số exact** (vượt xa float ×10000). Ba-trị sai/chia-0/thang<0→ẩn. Test 33 ca, audit **41/41**.
- ✅ **NHÁNH II — PERSISTENCE scheduler (2026-06-17, theo recommend):** `chụp`/`phục_hồi` ở `lib_lịch` (qua lib_json) = checkpoint/restore trực-giao. `hdh_bền_lịch.giao`: chạy→snapshot JSON bền→'sập'→khôi phục nhân MỚI→chạy tiếp; **ready-queue (ưu-tiên) + hộp-thư IPC sống sót**. Mẹo: đơn-vị-việc = mục-hàng-đợi ⇒ nhân TỰ-ĐỦ. Round-trip kiểm kỹ. Audit **42/42**.
- ✅ **NHÁNH I — `lib_thập_phân` đầy đủ (2026-06-17):** thêm `luỹ_thừa`(n≥0 exact, mũ-âm→ẩn) + `căn`(√ bằng Newton TRÊN decimal, nửa-lên, số-âm→ẩn). **√2 tới 30 chữ-số = 1.414213562373095048801688724210** (đúng toán-học). ⇒ kiểu-số decimal đầy-đủ `+ - * / căn luỹ_thừa`. Test 45 ca, audit **42/42**.
- ✅ **SONG SONG (2026-06-17, 2 agent + tự-duyệt) — cả 2 nhánh cùng tiến:**
  - *Nhánh II:* **IPC CHẶN + ĐÁNH-THỨC** ở `lib_lịch` (`chờ_tin`/`đang_chặn` + bảng "chặn" + `gửi` đánh-thức, tương-thích-ngược). Demo `hdh_chặn.giao` (block→wake). 
  - *Nhánh I:* **`mũ_e` (e^x)** Taylor trên decimal — e tới 30 chữ-số khớp mpmath tuyệt-đối. 
  - Audit **43/43**.
- ✅ **SONG SONG #2 (2026-06-17, 2 agent + tự-duyệt):**
  - *Nhánh I:* **`ln`** (logarit tự-nhiên) cho decimal = `2·atanh((x-1)/(x+1))` + **thu-gọn đối-số** `e·ln2+ln(m)` (tránh vượt MAX_STEPS khi x xa 1). ln2@30 khớp mpmath; `mũ_e(ln(5))=5`. ⇒ decimal có exp+log đầy đủ.
  - *Nhánh II:* **`lib_tiến_trình.giao`** — bảng tiến-trình có TÊN + vòng-đời trạng-thái (sẵn-sàng/chạy/chặn/chết); tự-thân, tid-lạ→ẩn.
  - Audit **44/44**.
- ✅ **SONG SONG #3 (2026-06-17, 2 agent + tự-duyệt):**
  - *Nhánh I:* **`pi`/`sin`/`cos`** cho decimal — π Machin (16·atan⅕−4·atan 1/239), sin/cos Taylor sau **thu-gọn miền mod 2π** (đúng cả x lớn: sin(10)=-0.54402111). π@30 khớp mpmath. ⇒ decimal có **đầy đủ hàm siêu-việt** (exp/ln/lượng-giác).
  - *Nhánh II:* **`lib_hệ.giao` — NHÂN HĐH-GIAO HỢP-NHẤT** (bảng-tiến-trình + scheduler + IPC-blocking + persistence, đồng-bộ trạng-bảng⟷hàng). Demo `hdh_hệ.giao`: chụp TOÀN-hệ→JSON→phục-hồi nguyên-vẹn.
  - Audit **45/45**.
- ✅ **SONG SONG #4 (2026-06-17, 2 agent + tự-duyệt):**
  - *Nhánh I:* **`luỹ_thừa_thực`(a^b=e^(b·ln a)) + `lô_ga`(log cơ-số)** cho decimal — khớp mpmath 9/9 (2^0.5=√2, 8^⅓=2, log₂1024=10). ⇒ decimal có **mũ-thực + log-cơ-số** (hoàn-tất đại-số siêu-việt).
  - *Nhánh II:* **`lib_lịch_học.giao` — γ-SCHEDULER BIẾT-HỌC tầng GIAO**, mô-phỏng ĐÚNG chính-sách silicon (σ←σ+(ρ−σ)//4 = `>>2`, argmax σ): tác-vụ-tốt được ưu-tiên-động, spin bị bóp. Demo `hdh_lịch_học.giao`.
  - Audit **46/46**.
- ✅ **SONG SONG #5 (2026-06-17, 2 agent + tự-duyệt):**
  - *Nhánh I:* **`arctan`/`arcsin`/`arccos`** cho decimal — agent PHƠI lỗi spec của tôi (atan_td(y=1) Leibniz vượt MAX_STEPS → γ=−1.0 ẢO-TƯỞNG) rồi tự sửa bằng **thu-gọn nửa-góc** `_atan_nhỏ`. Khớp mpmath (π/4, π/3, π/6, π/2). ⇒ decimal có **lượng-giác ngược đầy-đủ**.
  - *Nhánh II:* **`lib_nhân_học.giao` — NHÂN THÍCH-NGHI** (γ-scheduler-học ⊗ bảng-tiến-trình): CPU phân theo MERIT học-được (worker chiếm CPU, zombie bỏ-đói, loại_bỏ→bỏ-qua-chết). Bẫy mới: `học`=từ-khoá. Demo `hdh_thích_nghi.giao`.
  - Audit **47/47**.
- ✅ **SONG SONG #6 (2026-06-17, 2 agent + tự-duyệt):**
  - *Nhánh I:* **`sinh_hyp`/`cosh_hyp`/`tanh_hyp`** (hyperbolic = (e^x±e^−x)/2 qua `mũ_e`) — khớp mpmath 11/11; mẫu tanh>0 luôn. ⇒ decimal **đại-số+siêu-việt TRỌN VẸN**.
  - *Nhánh II:* **`kiem_lich_hoc_silicon.py` — CONFORMANCE** chứng `lib_lịch_học` (γ-scheduler cấp-GIAO) **KHỚP BYTE chính-sách silicon** `hw/gvm.v` (`//`≡`>>2` sàn-âm-vô-cực): 8/8 ca. Nối γ-scheduler cấp-ngôn-ngữ ⟷ gate-level (kiểu wasm⟷Python).
  - Audit **48/48**.
- ✅ **REVIEW loạt-song-song (2026-06-17, 2 agent độc-lập + tự-duyệt) — PHƠI & VÁ 2 LỖI THẬT:**
  - 🔴 **Đồng-bộ IPC `lib_hệ`:** heap không-xoá-tuỳ-ý → task-chặn vẫn bị `điều_phối` + nhân-đôi khi đánh-thức + `kết_thúc`+`gửi_tin` HỒI-SINH task chết. **Vá:** `điều_phối` pop-tới-"sẵn-sàng" (lazy-delete) + `gửi_tin` không-hồi-sinh-chết + `kết_thúc` gỡ-cờ-chặn. Chốt-regression vào `hdh_hệ.giao`.
  - 🔴 **Guard decimal:** `mũ_e`/`luỹ_thừa_thực` guard cố-định không đủ chữ-số-có-nghĩa khi kết-quả lớn (`2^50` ra đuôi-rác). **Vá:** nới guard theo độ-lớn (phần-nguyên-|x|/2 + độ-lớn-b·ln a). `2^50` exact. Chốt-regression vào `kiem_lib_thập_phân`.
  - 🟡🟢 **THẤP/TRUNG cũng vá hết:** TRUNG-1 `nhường`-không-idempotent → trung-hoà bởi `điều_phối` pop-tới-"sẵn-sàng" (chốt-regression 8d) · THẤP guard `pi`/lượng-giác `+8→+10` (tránh sát 0.5 ulp ở thang cao; audit khẳng không đổi giá-trị). *(MAX_STEPS là hằng-interpreter, không phải lỗi lib.)*
  - *Bài học (đúng CDFL):* demo XANH che lỗi; **review-độc-lập-có-reproduce** mới soi ảo-tưởng. Audit **48/48** (gồm chốt-regression 8a/8b/8c/8d + 2^50).
- **Hướng MỞ-RỘNG kế (cân 2 nhánh):** *Nhánh I:* √bậc-n (`x^(1/n)`) · hằng-số (e, φ, π) tới N chữ-số · hiệu-năng map-băm-O(1) ở GVM. *Nhánh II:* gộp `lib_nhân_học`+`lib_hệ` (nhân thích-nghi + IPC-blocking + persistence trong MỘT, áp pop-tới-"sẵn-sàng") · gắn γ-scheduler-học XUỐNG Verilog.

**ĐÃ LÀM (phiên dài 2026-06-16/17):**
1. **Silicon:** 4 nhân HĐH chạy gate-level (mô-phỏng iverilog): hợp-tác(`hdh.giao` 14490 từ) · preemptive(`hdh_preempt`) · cô-lập-fault(`hdh_fault`) · **tích-hợp**(`hdh_full_may.giao` 16896 từ — namespace+bảo-mật-γ+dịch-vụ). Ba-trị TRỌN (`ẩn`+`tối`). Sửa 2 lỗi silicon: cắt-địa-chỉ-12-bit (`rel_*`→16-bit) + CHIA/NHÂN số-âm (wire signed self-determined).
2. **Stdlib ~16 lib** (mỗi cái soi Python/Ruby): Duyệt·Chuỗi(+`số_chuỗi`)·Toán·Hash·Ngày·Ngày-host·IO · **JSON·Regex·CSV·URL·Base64(UTF-8)·Băm(djb2)·Mẫu** · tầng HĐH (`lib_baomat`/`lib_khonggian`/`lib_dichvu`). Builtin MỚI ở `giao.py`: `mã`/`ký_tự`(ord/chr) + capability `giờ`(cờ `--cho-giờ`, `giờ_hệ`).
3. **Phần-mềm thật:** `app_baocao.giao` ghép 6 lib (CSV→lọc→sắp→thống-kê→JSON+báo-cáo).
4. **Vòng TỰ-SỬA** `vong_tu_sua.py` (autonomous, cổng CDFL): **Stage 1-4 ✅** (hằng·toán-tử·off-by-one·**định-vị-lỗi-spectrum**). Lộ-trình `TU_SUA_LO_TRINH.md`. Stage 5=cắm-LLM (cần API host), 6=chủ-động.
5. **Planner theo chip** `lib_trienkhai.giao`+`trien_khai.giao`+`tinh_gon.giao` (chip→cấu-hình; xác minh `kiem_trienkhai.py` 10/10 máy).

**⚠ NGUYÊN TẮC TRUNG THỰC (người dùng chốt — KHÔNG nói quá; họ sẽ mở kiểm như Kali):**
"Xuống silicon" — THANG TRUNG-THỰC (2026-06-18 cập-nhật): (1) ✅ mô-phỏng iverilog gate-level (4 nhân khớp-byte); (2) ✅ **MỚI — yosys 0.66 (OSS CAD Suite) TỔNG-HỢP `gvm.v` (core CDFL: ba-trị+γ-scheduler+SIP+4-nhân) XUỐNG ~528k cổng generic (AND/OR/MUX/XOR/NOT + ~13.4k DFF + ALU NAND), MEM=256, KHÔNG LỖI** → synth-được CHỨNG-MINH (script `hw/synth_gvm.ys`); (3) ⏳ FPGA-primitive (synth_ice40 LUT/BRAM) + ABC tối-ưu — đang thử, ABC chậm vì quy-mô-CPU + mảng-nhớ đa-cổng; (4) ✗ nextpnr place&route → bitstream; (5) ✗ nạp chip FPGA thật. ⇒ "xuống silicon" = **synth-được-thật tới netlist cổng**, CHƯA tới bitstream/chip. `hw/fpga/gvm_core.v` vẫn là DI-SẢN bản-đầu (8-bit, thiếu CDFL) — KHÔNG dùng để synth nữa vì `gvm.v` chính đã synth thẳng. "Mạnh hơn Windows/9x"=tính-giấy (CHƯA đo đối-đầu). Planner=tự-dò chip QUA capability `phần_cứng()` (host phải cấp `--cho-phần-cứng`; L2 không-dò→ẩn). **"GIAO tự học" qua MCP=Claude ghi sổ CDFL, GIAO KHÔNG tự làm.** Tự-sửa=`vong_tu_sua.py` Stage 1-4 rule-based + **Stage 5 LLM-đề-xuất** (key-gated) — mọi vá QUA cổng CDFL regression-safe, KHÔNG tin mù. **Tầng HĐH-GIAO (lib_hệ/nhân_học/lịch...)=MÔ-HÌNH cấp-ngôn-ngữ + γ-scheduler khớp-byte silicon, CHƯA quản tiến-trình/RAM/phần-cứng thật.**

**VIỆC TIẾP (lần lượt):** (Nhánh I) `lib_chuoi` export số↔chuỗi+slice để diệt trùng-lặp 5 lib · namespace/cảnh-báo-va-tên khi `nhập` · 1 năng-lực ngôn-ngữ (generator/string-format/concurrency) · (Nhánh II) quyết-dứt `hw/fpga` (yosys 1 lần hoặc đánh-dấu `gvm_core.v` di-sản) · tự-sửa Stage 6 (chủ-động) · (dài hạn) FPGA thật. Chi tiết: `CHANGELOG.md` (**v0.5.0 mới nhất**), `GIAO_TRI_NHO.md`, `HOC_TU_WINDOWS.md`.
**Bẫy tên GIAO:** biến trùng alias-không-dấu của từ-khoá → tránh `tra`(=trả), `tam`(=tâm). Builtin thông-dịch-only KHÔNG biên-dịch máy: `gom/tách/loại/nối/cộng_hưởng` (máy dùng `ghép`).

---

## 0. Trạng thái hiện tại (mốc xanh — mục cũ)
| Hạng mục | Kết quả |
|---|---|

## 0. Trạng thái hiện tại (mốc xanh)
| Hạng mục | Kết quả |
|---|---|
| Bộ test ngôn ngữ | **63/63** |
| WASM ⟷ Python (đối chiếu byte) | **20/20 ca** |
| Ví dụ thông dịch | **51** chạy sạch |
| Ví dụ máy (giaoc → GVM) | **23** biên dịch+chạy |
| Verilog gate-level (iverilog) | **12/12 harness xanh**. ★ **BỐN NHÂN HĐH gate-level**: `lam_nhan_hdh` (HỢP-TÁC 14490 từ), `lam_nhan_preempt` (PREEMPTIVE γ), `lam_nhan_fault` (CÔ-LẬP-FAULT), **`lam_nhan_full` (TÍCH-HỢP ns+bảo-mật-γ+dịch-vụ, 16896 từ, 18/18)**. Ba-trị: `_an`(ẩn) + `lam_toi`(tối/SO_SÁNH). Cùng: `lam_verilog`(16b), `_32`(heap), `_chuoi`, `_io`(số thực+ds), `_thubat`(thử/bắt), `lam_concat`(heap-lớn) |

**Lưu ý môi trường:** luôn chạy với `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` (Windows cp1252). iverilog ở `C:\iverilog\bin`.

---

## 1. ĐÃ LÀM

### Lõi ngôn ngữ xuống máy (thu hẹp RANH_GIOI) — TRỌN
| Mốc | Tính năng | Ghi chú |
|---|---|---|
| 3a | closure / hàm hạng nhất | opcode `GỌI_CLOSURE` |
| 3b | `bản` (map, tham chiếu mutable) | helper `@__map_*`, khoá so cấu trúc |
| 3c | `lặp x trong` + `dừng` | duyệt list/chuỗi/bản, vòng lồng |
| 3d | số thực (điểm-cố-định ×10000) | `FNHÂN/FCHIA/RỌI_THỰC`, i64 trung gian |
| 3e | `mãi` + `thử/bắt` (ngoại lệ) | `BẮT_ĐẦU_THỬ/HẾT_THỬ/NÉM`, gỡ-cuộn |

### HĐH-GIAO
- **Nhân hợp-tác** `examples/hdh.giao` → biên dịch trọn (16968 từ), chạy GVM/WASM khớp thông dịch.
- **Biến cục bộ theo khung** (`DÀNH_CB`/`LƯU_THAM_I`) — sửa `đặt`-trong-hàm thành per-call (mở khóa closure-giữ-state = mô hình tiến trình).
- **Lập lịch PREEMPTIVE γ (biết-học)** `examples/hdh_preempt.giao` — `xuất/tác_vụ/lịch_học` → opcode `XUẤT/TÁC_VỤ/HẸN_GIỜ/LỊCH_HỌC`. Chính sách `GVM.γ_cập_nhật` **≡ wire silicon `hw/gvm.v`** (3000/3000 ca). Runner `chay_hdh_preempt.py`.
- **Cô lập fault** `examples/hdh_fault.giao` — tiến trình NÉM-chưa-bắt → nhân CÔ LẬP, hệ chạy tiếp; tự bọc `thử/bắt` → phục hồi. Handler per-task.
- **Persistence trực giao** `examples/hdh_ben.giao` — `GVM.lưu_máy/nạp_máy` (ảnh MÁY đầy đủ: RAM+ip+ngăn xếp+heap), `run()` resumable → chụp giữa chừng, RESUME trên GVM mới. Runner `chay_hdh_ben.py`.

### Tối ưu
- **Map khoá-chuỗi −62%** — intern chuỗi-hằng (`intern_strings`) + đường-nhanh `BẰNG` trước `__bằng` trong `@__map_tìm`. (gem `giaoc.giao` 8387→7276 từ.)
- Thông dịch 1.69× (mốc cũ).

### Phần cứng (Verilog `hw/gvm.v`)
- 16-bit: ngắt timer, context-switch đa-nhiệm, **γ-scheduler biết-học** (σ-EMA), SIP (base+bound), persistence.
- **Lõi 32-bit** (`WORD=32`): ABI thẻ (bit 30) → heap/list + gọi-hàm-khung + `là_số/là_ds` gate-level (`examples/heap32_gvm.giao`).
- **Opcode mới ở Verilog**: `ĐỔI · RỌI_CHUỖI · GỌI_CLOSURE · RỌI_AUTO · DÀNH_CB · LƯU_THAM_I` → **closure + chuỗi** chạy gate-level (`examples/heap32_chuoi.giao`). Cổng `out_kind` (0số/1ký-tự/2hết-chuỗi).
- **★ RÀO BA-TRỊ `ẩn` ĐÃ XUỐNG SILICON** (`examples/heap32_an.giao`, harness `lam_verilog32_an.py`):
  thêm **mảng cờ `stk_st [1:0]` song song ngăn xếp** (ẩn=00/sáng=01/tối=10). RAM/heap KHÔNG mang
  trạng-thái (`LƯU_*/TẢI_*` chỉ chuyển val → tải lại = sáng) ⇒ **chỉ ngăn xếp cần cờ** = khít GVM
  phần mềm. Opcode mới `ẨN`(2) đẩy ô ẩn; `XUẤT`(49) MMIO console (out_kind=7 + cổng `out_proc`=cur).
  Lan-truyền: số học (CỘNG/TRỪ/NHÂN/CHIA/FNHÂN/FCHIA) chạm ẩn → ẩn (val=0 ≡ ANCELL); FCHIA chia-0 → ẩn;
  `THAM_I` LUÔN sáng (≡ mô hình pstack); `TRẢ_VỀ_N` giữ trạng-thái (hàm rơi-khỏi-thân trả ẩn);
  `NHÂN_BẢN`/`ĐỔI` chuyển cờ; `NHẢY_NẾU_0(_X)` coi ẩn ≠ 0 (không nhánh); `RỌI`/`RỌI_AUTO`/`RỌI_THỰC`
  gặp ẩn → out_kind=6. Verify gate-level 4 nguồn ẩn (literal `ẩn`, hàm-rơi-thân, lan-truyền, chia-0) +
  sáng song song, **khớp byte** GVM phần mềm. Còn TODO: `SO_SÁNH`/`GIAO`/`HỌC` (tầng cộng-hưởng γ sinh `tối`).
- **SỐ THỰC + DANH SÁCH gate-level** (`examples/heap32_io.giao`, harness `lam_verilog32_io.py`): thêm `FNHÂN`(59)/`FCHIA`(60) — số thực điểm-cố-định ×10000 với trung gian **64-bit có dấu** (suy ra DSP, `/` Verilog cắt-về-0 = khít `fbin()`/i64 wasm) · `RỌI_THỰC`(61) — phát trị thô + `out_kind=3`, harness định dạng thập phân · `RỌI_DS`(48) — trạng thái `S_DS` duyệt cons-cell, in từng số (`out_kind=4`) + xung HẾT-DS (`out_kind=5`), **PEEK** không pop · `NÉM`(64) **tối thiểu** (chưa-bắt → DỪNG; nhánh chia-0 nên không chạy ở demo). `out_kind` mở rộng `[2:0]`, thêm cổng `out_proc` (nhãn tiến trình). 59.97 (vượt 16-bit) khớp byte ⇒ đường DSP 64-bit đúng.

### Polyglot / DX (mốc cũ, còn nguyên)
Cầu nối JSON-stdio · MCP server · capability I/O · REPL · lỗi-có-cột · playground trình duyệt.

---

## 2. VIỆC CẦN LÀM TIẾP (ưu tiên giảm dần)

### A. Hoàn tất lõi GVM 32-bit ở Verilog (để chạy nhân hdh ĐẦY ĐỦ gate-level)
Còn thiếu opcode trong `hw/gvm.v` (so với compiler emit):
- [x] `FNHÂN`(59)/`FCHIA`(60) — số thực điểm-cố-định (trung gian 64-bit có dấu, DSP). ✅ `lam_verilog32_io`.
- [x] `RỌI_THỰC`(61) — in số thực (out_kind=3, harness định dạng). ✅
- [x] `RỌI_DS`(48) — in danh sách số (trạng thái S_DS, PEEK). ✅
- [~] `NÉM`(64) — bản TỐI THIỂU (chưa-bắt → DỪNG). Còn thiếu `BẮT_ĐẦU_THỬ`(62)/`HẾT_THỬ`(63) + gỡ-cuộn (cần ngăn xếp handler trong Verilog) → try/catch ĐẦY ĐỦ.
- [x] `XUẤT`(49) — MMIO console (out_kind=7 + cổng `out_proc`=cur). ✅ cùng rào ẩn.
- [x] **★ RÀO LỚN NHẤT: trạng-thái `ẩn` (ba-trị) — ĐÃ XONG (2026-06-16).** Giải bằng **mảng cờ `stk_st [1:0]` SONG SONG** ngăn xếp (không nới WORD). Then chốt: RAM/heap **không** mang trạng-thái (đo từ GVM phần mềm: `LƯU_*/TẢI_*` chỉ chuyển val) ⇒ **chỉ ngăn xếp cần cờ**. `ẨN` đẩy ẩn; số học lan-truyền (val=0); FCHIA chia-0 → ẩn; `THAM_I` luôn sáng (≡ pstack); `TRẢ_VỀ_N` giữ cờ; `NHẢY_NẾU_0(_X)` ẩn≠0; `RỌI*` ẩn → out_kind=6. Verify `lam_verilog32_an`. *Còn:* `SO_SÁNH`/`GIAO`/`HỌC` (sinh `tối` qua cộng-hưởng γ) — tầng tác-tử CDFL, chưa cần cho nhân OS.
- [x] **try/catch ĐẦY ĐỦ ở Verilog (2026-06-16):** `BẮT_ĐẦU_THỬ`/`HẾT_THỬ` + `NÉM` gỡ-cuộn (ngăn-xếp-handler toàn cục: lưu sp/fp/rsp lúc vào 'thử', khôi phục + trao trị-lỗi + nhảy 'bắt'; rỗng → DỪNG). Verify `lam_verilog_thubat` (`thu_bat_mai_gvm`: chỉ-mục ngoài-phạm-vi → NÉM → bắt → phục hồi, khớp byte). *Còn:* handler PER-TASK (cho `hdh_fault` dưới scheduler) + cô-lập-fault phần cứng (uncaught-NÉM giết task, không halt CPU).
- [x] **★ NHÂN HĐH PREEMPTIVE chạy GATE-LEVEL ĐẦY ĐỦ (2026-06-16):** nạp CHÍNH bytecode `examples/hdh_preempt.giao` vào `hw/gvm.v`, γ-scheduler phần cứng cướp CPU (456 chuyển ngữ cảnh), tiến trình = HÀM (khung per-task). Đối chiếu CHẶT: phơi vết quyết-định lập-lịch (`sched_evt`/`sched_cur`/`sched_rho`) → **replay qua `γ_cập_nhật` phần mềm cho σ=[99,3,99] KHỚP BYTE**; spin (tt#1) bị throttle (σ=3 ≪ 99). Harness `lam_nhan_preempt.py`.
- [x] **★ Nhân HỢP-TÁC `hdh.giao` (32-bit, 14490 từ) chạy GATE-LEVEL ĐẦY ĐỦ — 24/24 khớp byte, dừng sau 400071 chu kỳ (2026-06-16).** Boot → sinh 4 tiến trình → interleave hợp-tác → **cổng CDFL chặn syscall 'format ổ đĩa' bất-khả-hồi** → DỪNG. Harness `lam_nhan_hdh.py`.
  - **GỐC RỄ đã sửa:** `rel_o`/`rel_s1`/`rel_s2` (relocation cho TẢI_GIÁN/LƯU_GIÁN/TẢI_Ô/LƯU_Ô) khai báo `[11:0]` (12-bit, di sản SIP vùng-128) → **địa chỉ heap ≥ 4096 bị wrap mod 4096** → nhân vỡ ở heap~4727. Nới `[15:0]`. Repro `examples/heap32_concat.giao` (nối chuỗi tích lũy, heap tới ~15000) + harness `lam_concat.py`.
- [x] **★ NHÂN CÔ-LẬP-FAULT `hdh_fault.giao` chạy GATE-LEVEL (2026-06-16).** Thêm **ngăn-xếp-handler PER-TASK** (`t_hsp[i]` = vùng [i*8,i*8+8), lưu/khôi phục khi chuyển ngữ cảnh → try/bắt cô-lập qua preemption) + **`t_dead[i]`** (uncaught-NÉM dưới scheduler → giết task, chuyển task sống qua `gsel_fault` loại cur, hệ KHÔNG halt; mọi task chết → DỪNG). `gsel_live` bỏ-qua-chết ≡ `gsel` khi không có chết (preempt không hồi quy). Verify `lam_nhan_fault.py`: tt#2(hỏng) `t_dead=1` sau 1 XUẤT; tt#0(khoẻ) đếm tiếp; tt#1(tự_chữa) XUẤT 900 lặp. ⇒ **bộ ba nhân (hợp-tác/preemptive/fault) trọn vẹn gate-level.**
- *Ghi chú:* `DÀNH_CB` ở Verilog hiện chỉ advance sp (KHÔNG zero ô). Nếu cần đọc-local-chưa-`đặt` đúng (=0) thì thêm zero (multi-cycle).

### B. Mở rộng HĐH-GIAO ở tầng GIAO (không cần Verilog)
- [ ] **Hàng đợi ưu tiên** cho scheduler (dùng `bản`/closure — giờ đã nhanh sau tối ưu map).
- [ ] **Nhiều tiến trình hơn** + đặt tên tiến trình hiển thị (hiện `tt#i` theo chỉ số; cân nhắc truyền tên qua opcode).
- [ ] **IPC / chia sẻ trạng thái** giữa tiến trình (qua `bản` toàn cục — đã có mẫu ở `hdh.giao`).
- [ ] **Persistence cho nhân preemptive** (kết hợp `lưu_máy` với scheduler — hiện scheduler chạy trong method Python, chưa snapshot giữa lập-lịch được; cân nhắc đưa vòng lập-lịch thành bytecode).

### C. Tối ưu thêm
- [ ] **Cache khoá-bản** đã tra (map khoá-chuỗi vẫn ~hàng trăm lệnh/thao tác dù đã −62%).
- [ ] `bản` dùng BĂM thay alist tuyến tính (hiện O(n) tra trên máy).
- [ ] Đưa vòng lập-lịch γ xuống bytecode (hiện ở `GVM.lập_lịch_học` Python) để chạy WASM/Verilog.

### D. Việc nhỏ / dọn dẹp
- [ ] `examples/hdh_preempt.giao`/`hdh_fault.giao` là CHỈ_MÁY (interp không có `xuất/tác_vụ/lịch_học`); cân nhắc thêm các builtin này vào thông dịch để nhất quán (hoặc giữ là máy/silicon-only — hiện tài liệu hoá ở `RANH_GIOI.md`).
- [ ] Bù `out_kind` cho các testbench Verilog cũ nếu muốn in chuỗi ở chúng.

---

## 3. BẢN ĐỒ TỆP (điều hướng nhanh)
- `giao.py` — thông dịch (ngôn ngữ đầy đủ, tham chiếu).
- `giaoc.py` — trình biên dịch GIAO → bytecode GVM.
- `gvm_may.py` — GVM phần mềm (CPU mô phỏng) + scheduler γ + persistence + opcode.
- `examples/` — `hdh*.giao` (HĐH), `heap32*.giao` (lõi 32-bit), `*_gvm.giao` (ví dụ máy).
- `hw/gvm.v` — GVM Verilog (16/32-bit, tham số WORD). `hw/lam_*.py` — harness gate-level.
- `wasm/gvm.ts` — GVM WASM (AssemblyScript). `wasm/kiem.mjs` — conformance.
- `chay_hdh*.py` — runner HĐH (máy/preempt/fault/persistence).
- `kiem_toan_bo.py` — **kiểm toàn bộ (chạy cái này trước tiên khi quay lại)**.
- Tài liệu: `CHANGELOG.md` (chi tiết từng mốc) · `RANH_GIOI.md` (ranh giới máy/thông dịch) · `KE_HOACH_PHAT_TRIEN.md` (kế hoạch gốc) · `TIEN_DO.md` (tệp này).

## 4. QUY TẮC GIỮ AN TOÀN (đã tuân thủ)
- **Additive**: mỗi thay đổi giữ suite 5/5; KHÔNG phá ví dụ cũ.
- **KHÔNG qua C** (bảo mật) — đường máy là WASM/Verilog, memory-safe.
- Đối chiếu BYTE wasm⟷Python mỗi mốc.
- Ranh giới máy/thông dịch **tự-thực-thi** (lỗi sạch, không biên-dịch-nhưng-sai).

---

## 5. HAI NHÁNH SONG SONG (định hướng tổng — bổ khuyết nhau)

> Chốt với người dùng (2026-06-16): hai nhánh tiến **song song**, không tách rời.

### Nhánh I — NGÔN NGỮ GIAO trưởng thành ngang Python/Ruby
Mục tiêu: GIAO là ngôn ngữ lập trình **khả thi + trưởng thành tương đương Python/Ruby**, không chỉ
là lõi CDFL. Cách làm: **tham khảo cách thư viện chuẩn Python/Ruby vận hành** rồi dựng bộ thư viện
tương ứng cho GIAO (giữ idiom GIAO, không bê nguyên).
- [x] **DUYỆT (Enumerable kiểu Python/Ruby) — `lib_duyet.giao` (2026-06-16):** 25 hàm —
  `sắp_xếp`/`sắp_theo` (merge sort), `duy_nhất`(uniq), `phẳng`(flatten)/`gộp_bản_đồ`(flat_map),
  `khoá_kéo`(zip), `phân_đôi`(partition), `nhóm_theo`(group_by→bản), `lấy_khi`/`bỏ_khi`(take/drop_while),
  `bỏ_n`/`lát`(slice), `bất_kỳ`/`mọi`/`không_ai`(any/all/none), `tìm_thấy`(detect), `chỉ_số`(index),
  `lớn_nhất_theo`/`nhỏ_nhất_theo`(max/min_by), `tổng_theo`(sum_by), `gọn`(compact). **GIỮ CỐT LÕI:**
  ba-trị (tìm_thấy/chỉ_số không-thấy→`ẩn` không bịa · `gọn` bỏ ẩn · predicate sáng/tối) · idiom Việt ·
  tự-thân (trên builtin+chuẩn.giao) · iterative. Test `kiem_lib_duyet.giao` (25 ca) trong `kiem_toan_bo` (6/6).
  *Lưu ý cú pháp: GIAO không có `và`/`hoặc`/`không` → lồng `nếu`.*
- [x] **CHUỖI — `lib_chuoi.giao` (2026-06-16):** 16 hàm — `hoa`/`thường` (TRA-BẢNG-chữ-cái, KHÔNG cần
  builtin mã↔ký-tự), `hoa_đầu`, `đảo_chuỗi`, `chuỗi_từ`/`ký_tự_ds`, `thay`/`số_lần` (qua `tách`+`nối`),
  `chứa_chuỗi`, `vị_trí` (không-thấy→**ẩn**), `bắt_đầu`/`kết_thúc`, `cắt_lề`, `lặp_lại`. Test 16 ca.
- [x] **TOÁN — `lib_toan.giao` (2026-06-16):** `sàn`/`trần`/`làm_tròn`, `dấu`/`kẹp`, `căn` (Newton —
  số-ÂM→**ẩn**), `ưcln`/`bcnn`, `trung_bình` (rỗng→**ẩn**), `nguyên_tố`(→sáng/tối). Test 22 ca.
- [x] **HASH/BẢN — `lib_bản.giao` (2026-06-16):** 19 hàm KHÔNG-phá-huỷ — `từ_cặp`/`cặp`, `gộp_bản`/`gộp_với`,
  `biến_đổi_giá_trị`/`biến_đổi_khoá`, `lọc_bản`, `đảo_bản`, `lấy_hoặc`(fetch+default), `có_giá_trị`,
  `khoá_của` (reverse lookup, không-thấy→**ẩn**), `đếm_giá_trị` (tally/Counter), `mỗi_cặp`. Test 19 ca.
- [x] **NGÀY-GIỜ — `lib_ngày.giao` (2026-06-16):** THUẦN TOÁN (JDN, không cần đồng-hồ): `năm_nhuận`/`hợp_lệ`(→sáng/tối),
  `ngày_trong_tháng`, `số_ngày`/`từ_số_ngày` (JDN ⟷ ngày), `khoảng_ngày`/`cộng_ngày`, `thứ`/`thứ_số`,
  `định_dạng` (ISO). Ngày SAI → **ẩn**. Test 20 ca (thứ 2000-01-01=Thứ Bảy ✓).
- [x] **IO theo NĂNG LỰC — `lib_io.giao` (2026-06-16):** `đọc`/`đọc_dòng`/`tồn_tại`/`ghi`/`liệt`/`chạy_lệnh` —
  GÓI builtin host-cấp, **TUYỆT ĐỐI không tự nới quyền**; thất-bại/chưa-cấp/ngoài-phạm-vi → **ẩn/tối** (không crash).
  Test (chạy `--cho-đọc .`): đọc/liệt được cấp, ghi/chạy chưa-cấp → tối/ẩn, **tệp KHÔNG bị tạo** (sandbox bẩm sinh).
- [x] **★ STDLIB GIAO ~100%** (6 module: Duyệt+Chuỗi+Toán+Hash+Ngày+IO) — `kiem_toan_bo` **11/11**, GIỮ trọn ba-trị + capability.
- [x] Giữ bản chất: ba-trị `ẩn`, CDFL, capability-IO, sandbox bẩm sinh — KHÔNG đánh đổi (đã tuân ở lib_duyet).

### Nhánh II — HĐH-GIAO (hướng Linux, học cái hay của Windows)
Đang phát triển trên **máy Windows 11**. HĐH-GIAO sẽ MẠNH HƠN nhiều, nhưng **học tối ưu/ý hay của
Windows** (lập lịch, quản-lý-năng-lượng, đối-tượng-kernel, bảo mật token/ACL, WSL...) — **không
đánh mất bản chất GIAO** (an-toàn-kiến-tạo, CDFL-native, ô ba-trị, KHÔNG qua C).
- [x] **KHẢO SÁT Windows 11 THẬT (2026-06-16) → `HOC_TU_WINDOWS.md`.** Đo sống: 374 procs/811k handle ·
  MIC (Medium, lưới Untrusted→System, no-write-up) · token 5 privileges · 298 services · VBS đang-chạy ·
  WSL · 674k Events (object manager) · scheduler boost=2. Map **11 cơ-chế** Win → GIAO-OS.
  **GIAO mạnh hơn:** γ-liên-tục thay MIC-rời-rạc · ba-trị `ẩn` (Win chỉ allow/deny) · memory-safe KIẾN-TẠO
  (không cần VBS/hypervisor) · γ-scheduler biết-học (đã ở silicon). **Học từ Win:** lưới-tin-cậy-có-thứ-tự,
  object-namespace thống-nhất, vòng-đời service, foreground-boost.
- [x] **Lớp BẢO-MẬT γ-gated — `lib_baomat.giao` (2026-06-16):** no-write-up LIÊN-TỤC (σ∈[0..255] thay 5 nấc
  MIC) + BA-TRỊ (`có_thể_ghi`→sáng/tối/**ẩn**; tin-cậy-chưa-soi=ẩn fail-safe) + **σ HỌC-ĐƯỢC** (`học_σ`:
  tác_vụ cư-xử-xấu σ tụt 200→50 → TỰ mất quyền ghi ô-cao — Windows MIC tĩnh KHÔNG làm được). `tạo_miền`/
  `đăng_ký`/`ghi`/`đọc`/`γ_truy_cập`. Test 14 ca → `kiem_toan_bo` **12/12**.
- [x] **Object namespace — `lib_khonggian.giao` (2026-06-16):** cây 'bản' gốc (học Object Manager); `gắn`/`tra_kg`/
  `tra_trị`/`loại_của`/`có`/`liệt_kg`/`gỡ` theo ĐƯỜNG-DẪN; thiếu→**ẩn**. (*Bẫy: `tra` = alias không-dấu của `trả`.*)
- [x] **Tầng service — `lib_dichvu.giao` (2026-06-16):** vòng-đời + PHỤ-THUỘC đệ-quy + **hồi-phục N lần → CÔ-LẬP**
  (`báo_lỗi` ≡ fault-isolation: 1 dv sập, hệ chạy tiếp); `khởi_tự_động`, phụ-thuộc-hỏng→tối, chưa-đăng-ký→ẩn.
- [x] **★ NHÁNH II KHÉP — 3/3 tính-năng GIAO-OS từ khảo sát Win** (γ-gated security + object-namespace + service-layer).
  `kiem_toan_bo` **14/14**. Học Windows, vượt bằng CDFL (liên-tục + ba-trị + memory-safe), giữ TRỌN bản chất GIAO.
- Xem mục **2.B** cho việc HĐH tầng GIAO; mục **2.A** cho đường xuống silicon.

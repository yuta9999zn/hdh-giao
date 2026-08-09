# CÒN THIẾU — hồ sơ tồn đọng của HĐH-GIAO

> **Cách dùng:** bảo *"check những chỗ còn thiếu và update"* là mở thẳng tệp này, chọn mục, làm.
> Mỗi mục đã ghi sẵn **bắt đầu ở đâu** và **kiểm bằng gì** để không phải dò lại từ đầu.
>
> Cập nhật lần cuối: **2026-07-31** · sau v0.18.0 — **nhóm H khép trọn (H1–H7)** + **KHO PHẦN MỀM**
> (học apt/Kali từ quan sát máy thật, vá 5 chỗ yếu của nó). *(Mỗi mục còn vài đuôi nhỏ, ghi ngay dưới mục ấy.)*
> Cập nhật **2026-07-31** sau v0.20.0 — **B1' (mạng ra host) + C4 (đăng nhập từ xa) XONG**.
> Cập nhật **2026-07-31** sau v0.23.0 — **nhóm G xong phần chính** (chuyển tệp · soạn thảo ·
> chuột phải · kéo-thả).
> Cập nhật **2026-07-31** sau v0.25.0 — **nhóm I khép trọn (I1–I4)**: chữ ký · kho qua mạng ·
> phụ thuộc có phiên bản · lùi nhiều bước.
> Cập nhật **2026-07-31** sau v0.26.0 — **khép C4 (rekey + chống dò) · C5 (khoá sau N lần sai) ·
> G2 (tạo/chép trong Tệp, `GH_CHÉP`)**.
> Cập nhật **2026-07-31** sau v0.27.0 — **đối chiếu Kali 2026.2 THẬT**: `$g3$` khó-về-bộ-nhớ
> (chỗ Kali hơn ta, đã vá một nấc) · máy chủ **ÉP** đổi khoá (chỗ sshd hở) · ghi rõ vì sao chống
> dò của ta khác `pam_faillock`/`pam_unix`. Hình dạng đúng cho B2 nay là **`binfmt_misc`**.
> Cập nhật **2026-07-31** sau v0.28.0 — **B2 XONG**: sổ định dạng `/hệ/định_dạng` (hình dạng
> `binfmt_misc`, vá 3 chỗ nó yếu) + `/lệnh` mang được **chính bytecode** (`#!mã-máy`, lệnh `dịch`).
> Cập nhật **2026-07-31** sau v0.29.0 — **B3 xong phần NGỮ NGHĨA**: `lib_dia.giao` (khối · inode ·
> tổng kiểm · **nhật ký phủ CẢ DỮ LIỆU** · gắn-phát-lại), vá 3 chỗ ext4 thật còn yếu.
> **Việc lớn còn lại: B4 (tiền định trọn vẹn) · B3 phần đuôi (đĩa vật lý · thư mục con · xoá tệp) ·
> B5 (cô lập bộ nhớ) · G1 phần đuôi (biểu tượng nền · nhiều bàn ảo · danh sách cửa sổ) ·
> G4 (nhiều phiên đồ hoạ) · các đuôi nhỏ ghi dưới từng mục.**
> Trạng thái mới nhất (sau v0.29.0): `kiem_hdh_giao.py` **385/385** · `kiem_toan_bo.py` **72/72** · `kiem_thu.py` 74/74 · `kiem_de.py` **41/41** · `kiem_tu_xa.py` **37/37** · `kiem_kho_xa.py` 12/12 · `kiem_lich_gamma.py` 2000/2000.
>
> **Bật máy:** `bat_may.bat` (dòng lệnh) · `bat_ban.bat` (bàn làm việc) · `bat_xa.bat` (cổng từ xa).
>
> **Bật máy:** `bat_may.bat` (dòng lệnh) · `bat_ban.bat` (bàn làm việc đồ hoạ).
> **Quy ước tên tệp (chốt 2026-07-30): tệp/đường dẫn MỚI đặt tên KHÔNG DẤU** (vd `lib_sha256.giao`);
> tệp cũ có dấu giữ nguyên; định danh trong mã vẫn tiếng Việt có dấu.
>
> **Quy ước bất di bất dịch của dự án:** mọi thứ cài vào **ổ D**, không đụng ổ C (C chỉ còn ~15 GB).
> **Dự án nằm ở `D:\HeDieuHanh\GIAO` — đường dẫn KHÔNG DẤU. Giữ nguyên như vậy:** cả `vvp`,
> `nextpnr` lẫn `iverilog` đều mở tệp bằng API ANSI, đường dẫn có dấu là hỏng ngay.
> Công cụ đã cài: `D:\iverilog` · `D:\mingw64` · `D:\oss-cad`. Kết quả tổng hợp ra `hw/ra/`.

---

## A. CHẶN NHIỀU THỨ KHÁC — làm trước thì mở khoá được nhiều việc

### ~~A1. GIAO chưa có phép toán trên BIT~~ — **XONG v0.11.0 (2026-07-30)**
- Đã thêm builtin `giao.py`: `xor` · `và_bit` · `hoặc_bit` · `đảo_bit` · `dịch_trái` · `dịch_phải`
  (ba-trị, số lớn, trần dịch chống nổ bộ nhớ). Kiểm: `kiem_lib_bit.giao` trong `kiem_toan_bo`.
- **Còn mở (nếu cần sau):** đưa phép bit xuống MÁY (`gvm_may.py` + `hw/gvm.v`, opcode mới, giữ ba
  bản khớp nhau) — hiện `giaoc` từ chối sạch theo RANH_GIOI, chưa chặn gì.

### ~~A2. GIAO chưa gán được theo chỉ mục~~ — **XONG v0.11.0 (2026-07-30)**
- `đặt ds[i] = x` · `đặt bản[khoá] = x` · lồng `đặt l[i][j] = x` — sửa tại chỗ; ẩn → no-op;
  ngoài phạm vi/chuỗi → lỗi sạch. `γ_bước` (`lib_lịch_γ.giao`) đã viết lại gọn, 2000/2000 vẫn khớp.

### ~~A3. `thêm` vs `gom` dễ nhầm chết người~~ — **XONG v0.12.0 (2026-07-30)**
- `thêm(ds, x)` đứng một mình (kết quả bị vứt) nay là **lỗi sạch** kèm gợi ý dùng `gom` /
  `đặt ds = thêm(...)`. Người dùng tự định nghĩa hàm `thêm` riêng thì không bị đụng.

---

## B. HỆ ĐIỀU HÀNH

### ~~B1. Chưa có MẠNG~~ — **XONG PHẦN TRONG-MÁY v0.12.0 (2026-07-30)**
- Đã có: gọi-hệ 29–32 (`GH_NGHE`/`GH_NỐI`/`GH_GỬI_GÓI`/`GH_NHẬN_GÓI`), thiết bị `/tb/mạng`,
  mô hình y như ống nhưng theo CỔNG; cổng <1024 chỉ gốc; quyền ổ (600 chặn người ngoài); chỉ
  đầu mối được dùng kết nối; phản áp + audit. Kiểm: `kiem_lib_mang.giao` (kiem_hdh mục [26]).

### ~~B1'. Mạng RA HOST thật (socket TCP)~~ — **XONG v0.20.0**
- Năng lực `mạng_host` (`--cho-mạng <cổng>`, kẹp 127.0.0.1) + `ổ_nghe/nhận/nối/gửi/đọc/đóng`
  KHÔNG CHẶN; `GH_NGHE(cổng, quyền, "ngoài")` dùng **cùng API** với mạng trong-máy.
- **Còn mở nhỏ:** ① **chưa mã hoá** (xem C4) · ② chỉ nghe 127.0.0.1, chưa cho nghe ra LAN
  (cố ý — mở ra thì phải có mã hoá trước) · ③ chưa có UDP · ④ chưa có DNS.

### ~~B2. `/lệnh` vẫn là VĂN BẢN, chưa phải nhị phân~~ — **XONG v0.28.0**
- **★ Quan sát Kali 2026.2 đã ĐỔI CÁCH NGHĨ về mục này:** `/bin` có **1540 tệp ELF nhưng 897 tệp
  là kịch bản có `#!`**. **Ngay Linux thật cũng pha trộn**, nên đích không phải "bỏ văn bản đi".
  Cái đáng học là **`binfmt_misc`**: nhân giữ **sổ đăng ký** ánh xạ *magic → trình chạy*, `#!`
  chỉ là một mục trong sổ. Theo hình dạng đó thì bytecode là **thêm một DÒNG**, không phải thay
  cả cơ chế — và quả nhiên `chạy_một_lệnh` nay không còn nhánh ghi cứng nào.
- **Đã làm:** `lib_dinh_dang.giao` + sổ `/hệ/định_dạng` (644, 4 cột `tên|magic|trình|năng_lực`) ·
  định dạng **`#!mã-máy`** mang CHÍNH bytecode GVM · lệnh **`dịch <nguồn> <đích>`** sinh ra nó ·
  lệnh **`định_dạng [tệp]`** soi sổ / hỏi vì sao · `đăng_ký_ct_mã` + nhánh `ct_mã` trong `GH_SINH`
  (nạp thẳng, **không đụng trình biên dịch lúc chạy**).
- **Ba chỗ `binfmt_misc` yếu, đã vá:** ① đăng ký sai **không làm câm máy** — sổ qua bộ kiểm H6
  (trùng magic · ngả lui đặt giữa · thiếu ngả lui · trình không có thật đều bị chặn kèm số dòng,
  tệp cũ còn nguyên), và **xoá hẳn sổ đi máy vẫn chạy** vì ngả lui nằm TRONG MÃ · ② **nói rõ vì
  sao** (Linux chỉ `ENOEXEC`) · ③ định dạng **tự khai năng lực**, thiếu thì từ chối kèm cách bật.
- **Kiểm:** `kiem_dinh_dang.giao` chạy **hai lần** (chưa cấp `máy` / đã cấp) — mục [36] của
  `kiem_hdh_giao.py`. `xem /lệnh/<tên>` ra bytecode, `chạy` vẫn đúng, quyền `x` vẫn chặn.
- **Còn mở nhỏ:** ① hệ-tệp GIAO chứa CHUỖI nên từ-lệnh viết ra dạng **số thập phân**, tức cái đã
  đổi thật sự là *tệp mang MÃ chứ không mang NGUỒN* — còn nói "nhị phân" thì vẫn là nói quá ·
  ② mới có bốn trình chạy dựng sẵn; muốn cắm trình NGOÀI (như `binfmt_misc` trỏ tới một
  thông dịch bất kỳ) thì phải mở thêm · ③ `dịch` chỉ nuốt được tập con mà `giaoc` biên dịch
  được (RANH_GIOI) — vượt thì báo rõ và bảo cứ để làm kịch bản vỏ.
- **⚠ NGÂN SÁCH BƯỚC — đọc trước khi thêm việc lên đường chạy lệnh:** tra sổ nằm trên đường đi của
  MỌI lệnh. Bản đầu phân tích lại sổ mỗi lần ⇒ `hdh_giao.giao` **chạm trần 5 triệu bước**, 12 hạng
  mục rớt một lượt. Đã vá bằng nhớ-theo-nội-dung-thô, nhưng **đo lại còn cần ~4–5M bước, chỉ dư
  ~20%** so với mặc định 5M. Việc sau đặt thêm chi phí lên đường ấy thì **ĐO TRƯỚC**.

### ~~B3. Chưa có hệ-tệp thật trên đĩa~~ — **XONG PHẦN NGỮ NGHĨA v0.29.0**
- **Đã có:** `lib_dia.giao` — **khối · inode · tổng kiểm từng khối · NHẬT KÝ · gắn-và-phát-lại**,
  và `gắn_đĩa` treo đĩa vào một thư mục có sẵn nên **đường dẫn thường** (`ghi /đĩa/thơ`,
  `xem /đĩa/thơ`, `liệt /đĩa`) đi xuống tầng khối. Lệnh vỏ `đĩa` (dựng · gắn · tháo · soi).
- **★ Quan sát ext4 THẬT (Kali 2026.2) rồi mới làm** — ba chỗ nó yếu, đã làm khác:
  ① `findmnt` ra **`data=ordered`** (mặc định): nhật ký chỉ phủ **siêu dữ liệu**, KHÔNG phủ dữ
  liệu ⇒ mất điện giữa lúc ghi có thể ra *"siêu dữ liệu mới + nội dung rác"* mà không ai báo.
  Ở đây nhật ký **chở cả khối dữ liệu** ⇒ hoặc thấy trọn vẹn, hoặc không thấy gì.
  ② `metadata_csum` **không phủ dữ liệu người dùng** ⇒ khối mục thầm lặng bị **trả ra như thật**.
  Ở đây mỗi khối mang tổng kiểm, đọc phải khối hỏng thì **BÁO**.
  ③ `man 2 fsync`: *"does not necessarily ensure that the entry in the directory … has also
  reached disk"* ⇒ độ bền là **kiến thức truyền miệng**. Ở đây **tên và nội dung cùng một giao
  dịch**, cùng sống hoặc cùng chết — không có điệu nhảy fsync.
  ④ *(không phải chỗ yếu, là cái giá thật)* khối 4096 B ⇒ tệp 1 byte tốn 4096. Ta cũng phải trả,
  và lệnh `đĩa` **hiện số byte phí ra** chứ không giấu.
- **Kiểm:** `kiem_dia.giao` — phép thử quyết định là **cắt điện giữa lúc ghi** ở hai điểm (trước
  cam kết → giữ bản CŨ nguyên vẹn; sau cam kết giữa lúc chép → phát lại thành bản MỚI trọn vẹn),
  cộng khối mục → từ chối, quyền điểm gắn chặn, chỉ gốc được gắn. Mục **[37]** của `kiem_hdh_giao.py`.
- **Còn mở (trung thực):** ① "đĩa" vẫn là cấu trúc trong bộ nhớ máy GIAO, **chưa phải mặt đĩa vật
  lý** — bền qua tắt máy vẫn nhờ ảnh chụp JSON như cũ; cái mới thật sự là **NGỮ NGHĨA** ·
  ② tổng kiểm dùng djb2 nên bắt hỏng **ngẫu nhiên**, không chống kẻ **cố ý** (muốn thế phải dùng
  `lib_sha256.giao`) · ③ đĩa mới có **tệp phẳng**, chưa có thư mục con · ④ chưa có xoá tệp trên
  đĩa, chưa có bản đồ khối trống (xoá xong không thu hồi khối) · ⑤ chưa gắn được `/` (mới gắn
  được vào thư mục con).

### B4. Đa nhiệm tiền định mới TỪNG PHẦN
- **Thiếu:** vỏ / trợ lý / dịch vụ vẫn là closure hợp-tác vì chúng cần `bản`/closure/`thử-bắt` —
  ngoài tập con mà `giaoc` biên dịch được. Tiến trình MÁY thì đã cắt ngang được.
- **Bắt đầu:** mở rộng `giaoc.py` cho `bản` + closure, HOẶC viết lại dịch vụ trong tập con.
- **Kiểm:** `hdh_tiền_định.giao` — kẻ tham lam bị cắt CPU kể cả khi là vỏ.

### B5. Cô lập bộ nhớ giữa các tiến trình
- **Thiếu:** cô lập hiện nhờ trình thông dịch, không phải nhờ phần cứng. Trên GVM đã có tiến trình
  máy riêng ngăn xếp, nhưng chưa có bảng trang / MMU.
- **Đáng làm sau B4.**

---

## C. ĐĂNG NHẬP & NHIỀU NGƯỜI DÙNG *(vừa làm §5.19 — đây là phần còn thiếu của nó)*

### ~~C1. Hàm băm mật khẩu chưa phải KDF được thẩm định~~ — **PHẦN LỚN XONG v0.11.0 (2026-07-30)**
- **Đã làm:** `lib_sha256.giao` (SHA-256 FIPS 180-4 thuần GIAO + UTF-8 tự dựng, khớp `hashlib`
  từng ký tự) · định dạng **`$g2$`** = SHA-256 xích theo byte, `bóng_mới` phát hành `$g2$`,
  `khớp_mk` đọc cả `$g1$` lẫn `$g2$` (bản cũ không phải đổi mật khẩu). Kiểm xanh cả hai.
- ~~**chưa chống nổi GPU**~~ — **VÁ MỘT NẤC v0.27.0**: quan sát Kali 2026.2 thấy
  `ENCRYPT_METHOD YESCRYPT` (memory-hard) ⇒ **chỗ Kali hơn ta**. Thêm **`$g3$` = ROMix kiểu
  scrypt** thuần GIAO: pha ĐỔ ĐẦY bảng `V[0..N−1]` rồi pha TRUY CẬP NGẪU NHIÊN (chỉ số `j` lấy từ
  chính trạng thái ⇒ không đoán trước, không nạp trước) — kẻ tiếc bộ nhớ phải tính lại từ đầu.
  **Đo thật: g2 743 ms/lần · g3 752 ms/lần (chênh 1,2%)** ⇒ cùng cái giá, mua thêm được tính
  khó-về-bộ-nhớ. Ba định dạng song song, bản ghi cũ không phải đổi.
- **Còn mở (trung thực):** bảng `$g3$` mới **N=64 × 32 byte = 2 KB**, còn xa scrypt (16 MB) và
  yescrypt — có ĐÚNG CẤU TRÚC nhưng LƯỢNG bộ nhớ còn nhỏ, nên mới chặn GPU được phần nào. `N`
  nằm trong bản ghi nên có đường máy nhanh (phép bit xuống GVM) thì nâng `MK_N3`, bản cũ vẫn khớp.
  Vẫn chưa qua thẩm định mật mã.

### ~~C2. Chưa có nhóm người dùng~~ — **XONG v0.13.0 (2026-07-30)**
- `/hệ/nhóm` (644) + bảng credential `TTH_NHÓM` (chốt lúc đăng nhập qua `đồng_bộ_nhóm`) +
  `được_phép` xét chủ>nhóm>khác đúng thứ tự Unix + `GH_ĐỔI_NHÓM`(33)/lệnh `đổi_nhóm` (luật chgrp
  Linux) + lệnh `nhóm`. Kiểm đúng đề bài: 640 cùng nhóm đọc được, ngoài nhóm không
  (`kiem_nhom_sudo.giao`).
- **Còn mở nhỏ:** tệp mới tạo mang gid 0 — chưa kế thừa nhóm chính của người tạo / setgid thư mục.

### ~~C3. Chưa có `sudo` với sổ quyền riêng~~ — **XONG v0.13.0 (2026-07-30)**
- `/hệ/sudo` (440) `tên: lệnh…|*` + `sudo_được` ba-trị + lệnh `sudo <lệnh>` (hỏi mật khẩu CỦA MÌNH,
  cấp gốc cho ĐÚNG MỘT lệnh). **Giữ đúng ghi nhớ:** sudo KHÔNG thay duyệt — bất-khả-hồi qua sudo
  vẫn chờ phê duyệt (test sống trong kiem_hdh mục [27]).
- **Còn mở nhỏ:** sổ chưa có vế "dưới uid nào" (hiện luôn là gốc).

### ~~C4. Chưa có đăng nhập từ xa~~ — **XONG v0.20.0 (trừ mã hoá)**
- `lib_tu_xa.giao` + `chay_hdh_xa.py` + `khach_xa.py` + `bat_xa.bat`: xác thực bằng ĐÚNG
  `/hệ/mật_khẩu`, phiên chạy dưới ĐÚNG uid, **quyền · cổng bất-khả-hồi · audit vẫn nguyên**.
  Kiểm: `kiem_tu_xa.py` 15/15.
- ~~**MÃ HOÁ ĐƯỜNG TRUYỀN**~~ — **XONG v0.21.0**: ChaCha20 + HMAC-SHA256 thuần GIAO (khớp vector
  RFC 8439), khoá phiên chuyển bằng RSA-2048, **khoá máy + vân tay TOFU**. Có test **soi byte trên
  dây**: bí mật không hiện ra, sửa một ký tự → thẻ sai, phát lại → bị bỏ.
- ~~**BÍ MẬT CHUYỂN TIẾP**~~ — **XONG v0.22.0**: Diffie-Hellman RFC 3526 nhóm 14 (`lib_dh.giao`),
  khoá tạm mỗi phiên rồi vứt, khoá máy chỉ còn dùng để **ký** giá trị DH. Năng lực `ngẫu_nhiên`
  cấp entropy thật. Hằng số nhóm kiểm bằng **công thức** (`kiem_dh_nhom.py`), không so chuỗi.
- ~~**ĐỔI KHOÁ GIỮA PHIÊN (rekey)**~~ — **XONG v0.26.0**: DH mới NGAY TRONG kênh cũ (đã xác
  thực HMAC nên không cần ký lại — đúng lối SSH), hai bên thay trọn bộ khoá + số đếm về 0;
  khách tự đổi sau mỗi 32 khung. Kiểm soi dây: khoá CŨ không mở nổi khung sau rekey.
  **v0.27.0 vá tiếp chỗ sshd hở:** hạn phải ở CẢ HAI đầu — máy chủ nay ĐẾM và **từ chối phục vụ**
  quá `TX_HẠN_KHUNG=64` khung (đường thoát duy nhất là đổi khoá), kèm chặn khung dài quá
  `TX_KHUNG_TỐI_ĐA=8192` ⇒ dữ liệu giữa hai lần đổi khoá có **cận trên thật** (512 KB).
- ~~**CHỐNG DÒ MẬT KHẨU**~~ — **XONG v0.26.0** (xem C5): chậm dần theo TÊN + ngắt sau 3 lần
  sai mỗi kết nối + khoá tài khoản sau 10 lần (trừ gốc).
- **Còn thiếu:** ① mở ra LAN (giờ vẫn kẹp 127.0.0.1 — mở phải cân nhắc lại toàn bộ) ·
  ② nhiều tty song song có tên riêng (hạ tầng đã sẵn, nhiều khách cùng lúc đã chạy được) ·
  ③ chưa qua thẩm định mật mã (nói một lần cho hết: cả ChaCha20/HMAC/RSA/DH ở đây đều là bản
  hiện thực cho dự án, đúng thuật toán và khớp vector chuẩn, nhưng chưa ai soi về mặt an toàn).
- **Ghi chú:** hạ tầng phiên đã sẵn — `đăng_nhập` trả về một tid vỏ, nên nhiều phiên song song chỉ
  là chuyện giữ nhiều `V` thay vì một.

### ~~C5. Chưa khoá tài khoản sau N lần sai~~ — **PHẦN CHÍNH XONG v0.26.0**
- Sổ `DÒ_SỔ` trong `lib_người_dùng.giao`, móc ngay trong `đăng_nhập` (một điểm chặn cho CẢ
  tại máy, `thành`, lẫn từ xa): từ lần sai thứ 3 **chậm dần gấp đôi** (2s→60s trần, cần năng
  lực `giờ`); **trong quãng chờ gõ ĐÚNG cũng không xét**; sai liên tiếp 10 lần → `khoá_người`
  tự động (bóng = `*`) — **trừ `gốc`** (khoá gốc là kẻ dò khoá được cửa của chủ máy;
  pam_faillock cũng chừa root). Đăng nhập đúng thì xoá sổ. Kiểm: `kiem_chong_do.giao`
  (kiem_hdh mục [34]) + `kiem_tu_xa.py` mục [5].
- **v0.27.0 vá thêm RÒ RỈ THEO THỜI GIAN:** ta nói "sai tên HOẶC mật khẩu" cho kín, nhưng người
  có thật tốn ~750ms còn người không có / bị khoá trả lời ~0ms ⇒ bấm giờ là đếm được tài khoản.
  Nay băm `BÓNG_GIẢ` rồi vứt (lối OpenSSH), mọi ngả tốn công ngang nhau. Kiểm:
  `kiem_ro_ri_thoi_gian.giao` — **đã thử tháo bản vá ra và thấy nó rớt** (3s vs 0s).
- **Còn mở nhỏ:** ① sổ dò sống trong BỘ NHỚ máy đang chạy — tắt máy là quên (pam_faillock
  cũng thế với tally mặc định; muốn bền thì ghi xuống /hệ) · ② chưa có **hạn tuổi mật khẩu**
  (đổi định kỳ) — phần này của C5 vẫn mở (Kali cũng đang tắt: `PASS_MAX_DAYS 99999` — nhưng đó
  không phải cái cớ) · ③ gõ tên bừa nay tốn 750ms CPU máy chủ mà sổ chậm-dần khoá theo TÊN nên
  không chặn kẻ đổi tên liên tục; hiện chỉ có hạn 3-sai-mỗi-kết-nối (bắt làm lại DH) giữ cho
  phép tính không lỗ.

---

## I. KHO PHẦN MỀM — *mới có ở v0.18.0 (học apt/Kali). Đây là phần còn thiếu của nó*

### ~~I1. Chưa có CHỮ KÝ khoá-công-khai cho mục lục~~ — **XONG v0.19.0**
- `lib_so_lon.giao` (`mũ_mod`) + `lib_chu_ky.giao` (**RSA-2048 PKCS#1 v1.5 + SHA-256, kiểm thuần
  GIAO, ~0,3s**) + neo tin cậy riêng từng nguồn (`/hệ/kho/nguồn`, học `Signed-By:`) + lệnh
  `gói tin`. Ký làm **bên ngoài** (`lam_khoa.py`) — khoá riêng không vào máy.
- Kiểm: kho giả mạo **băm đúng nhưng ký bằng khoá khác** → từ chối (`kiem_chu_ky.giao`).
- **Còn mở nhỏ:** ① `lam_khoa.py` sinh nguyên tố là bản gọn, **chưa qua thẩm định mật mã**;
  ② chưa có **hạn dùng / thu hồi khoá** (apt có `Valid-Until` trong Release); ③ chưa ký **từng
  gói** riêng, mới ký mục lục (mục lục mang băm gói nên vẫn phủ, nhưng ký riêng thì gỡ được
  từng gói ra dùng lại); ④ chưa có đường **đổi khoá** an toàn (khoá mới ký bằng khoá cũ).

### ~~I2. Kho vẫn nằm TRONG máy, chưa có nguồn từ xa~~ — **XONG v0.24.0**
- `nguồn_xa` + `gói tải` + tự tải thân gói khi cài. Trình tự: **tải → kiểm chữ ký → rồi mới ghi**;
  khoá công **không tải về** (neo sẵn trên máy). Mục lục cần gốc-quyền (như `apt update`), thân
  gói thì người thường tải vào kho riêng. Kiểm: `kiem_kho_xa.py` 12/12 với hai ca phủ định.
- **Còn mở nhỏ:** ① chưa có nhiều nguồn cùng lúc (giờ đúng một `nguồn_xa`) · ② `_xa_lấy` **quay
  vòng bận** (busy-wait) chờ dữ liệu — chạy tốt trên cùng máy, ra mạng thật thì nên có chờ-ngủ ·
  ③ chưa tải lại được khi đứt giữa chừng (tải lại từ đầu) · ④ chưa có `Valid-Until` để mục lục
  cũ tự hết hạn.

### ~~I3. Chưa có phiên bản hoá phụ thuộc~~ — **XONG v0.25.0**
- `>=` `>` `=` `<=` `<` + gói thay thế `a/b` (dùng `/` chứ KHÔNG dùng `|` như apt — vì `|` đã là
  dấu ngăn cột; bộ kiểm H6 nay đòi ĐÚNG 7 cột để bắt lỗi ấy ngay). `so_phiên` so theo từng đốt số
  nên `1.10 > 1.9`.
- **Còn mở nhỏ:** chưa có "xung khắc" (`Conflicts:`), chưa có "cung cấp" (`Provides:` — gói ảo),
  chưa có ràng buộc kép (`>=1.0` và `<2.0` cùng lúc).

### ~~I4. `gói lùi` mới lùi được MỘT bước~~ — **XONG v0.25.0**
- Sổ lùi là NGĂN XẾP có đánh số bước; `gói lùi` bóc từng bước và báo còn mấy bước.
- **Còn mở nhỏ:** `dọn_rác` xoá sạch thùng ⇒ **mất luôn đường lùi** — nên cảnh báo trước khi dọn
  nếu còn bước lùi chưa dùng.

---

## H. BỔ KHUYẾT LINUX — *mở ở v0.15.0; đây là danh sách việc tiếp*

> Nguyên tắc: chỉ chép cái hay, KHÔNG chép cái dở. Mỗi mục ghi rõ **Linux hỏng ở đâu** rồi mới bàn cách.

### ~~H1. `rm` vĩnh viễn, thùng rác chỉ là quy ước desktop~~ — **XONG v0.15.0**
- Gọi-hệ 34–36 (`bỏ`/`hoàn_tác`/`dọn_rác`) + `/thùng_rác` + lệnh `thùng`. Cổng duyệt dời sang
  `dọn_rác` (việc thật sự bất-khả-hồi). Kiểm: `kiem_bo_khuyet_linux.giao`.

### ~~H2. "Permission denied" không nói gì thêm~~ — **XONG v0.15.0**
- `vì_sao` (gọi-hệ 37): chỉ đúng nấc hỏng, vai, bit thiếu, cách qua; ẩn ≠ tối.

### ~~H3. Signal giết ngang, không dọn dẹp~~ — **XONG v0.16.0**
- `xin_thoát` (gọi-hệ 38) + `đăng_ký_dọn` + `dọn_dẹp`: dọn chạy ở **lát CPU của chính tiến trình**
  (điểm an toàn, không async), có **hạn ân hạn**, quá hạn nhân mới cắt và **ghi rõ**. Vẫn qua cổng.
- **Còn mở nhỏ:** chưa có "xin dừng cả một NHÓM/dịch vụ theo thứ tự phụ thuộc" (kiểu shutdown
  có thứ tự) — `lib_dichvu.giao` đã có đồ thị phụ thuộc, nối vào là ra.

### ~~H4. OOM-killer chọn nạn nhân bằng heuristic~~ — **XONG v0.16.0**
- `cấp_ô` (gọi-hệ 39) + `bộ_nhớ`: chọn theo **σ học được**, nêu lý do, **hỏi qua cổng duyệt**,
  đồng ý thì dừng êm bằng `xin_thoát`. Chết là tự trả bộ nhớ.
- **Còn mở nhỏ:** bộ nhớ hiện là **ô do chương trình tự xin** (kế toán tường minh), chưa đo bộ nhớ
  thật mà trình thông dịch cấp; và chưa có hạn mức theo NGƯỜI/NHÓM (`lib_nhóm.giao` đã có quota —
  nối vào là ra).

### ~~H5. Đường dẫn/tên tệp là bãi mìn~~ — **XONG v0.17.0**
- `lý_do_tên_xấu` chặn từ lúc TẠO ở tầng hệ-tệp (ký tự điều khiển · lề trắng · `.`/`..` · `/` ·
  quá dài), báo rõ lý do. `-rf` vô hại theo kiến tạo (vỏ truyền danh sách đối).
- **Còn mở nhỏ:** chưa chặn tên trông-giống-nhau bằng Unicode (chữ Kirin lẫn Latinh — homoglyph),
  và chưa có tuỳ chọn "chỉ cho tên ASCII" cho thư mục nhạy cảm như `/lệnh`.

### ~~H6. Cấu hình /etc mỗi tệp một định dạng~~ — **XONG v0.17.0**
- `lib_cau_hinh.giao`: bộ kiểm cho `/hệ/người_dùng` · `/hệ/nhóm` · `/hệ/sudo` · `/hệ/mật_khẩu`,
  gắn ở tầng gọi-hệ nên **mọi cửa ghi đều qua** (kể cả `>>`). Sai → từ chối, nói rõ dòng, tệp cũ
  còn nguyên. Lệnh `kiểm_cấu_hình`.
- **Còn mở nhỏ:** thêm bộ kiểm cho các tệp cấu hình sau này (thêm một nhánh trong
  `kiểm_cấu_hình` là xong); chưa có "sửa thử rồi hoàn tác nếu hỏng" kiểu `netplan try`.

### ~~H7. TOCTOU (kiểm rồi mới dùng)~~ — **XONG v0.17.0**
- Gọi-hệ GIAO vốn kiểm-và-làm trong MỘT lượt nên khe `access`→`open` không có. Thêm **`ghi_nếu`**
  (gọi-hệ 40) = compare-and-set trên tệp, chặn **mất-cập-nhật** khi hai tiến trình cùng sửa —
  thứ Linux không có câu trả lời.
- **Còn mở nhỏ:** chưa có giao dịch nhiều tệp (đổi 2 tệp cùng lúc, hỏng thì lùi cả hai).

---

## G. BÀN LÀM VIỆC (giao diện đồ hoạ) — *mới có ở v0.14.0, đây là phần còn thiếu của nó*

### G1. Chưa kéo-thả, chưa chuột phải, chưa biểu tượng trên nền
- **Hiện có:** cửa sổ kéo/co được, **ba nút đủ chức năng** (đỏ đóng · vàng thu nhỏ · xanh phóng
  to/co lại — v0.15.0), dock, menu ứng dụng, hộp phê duyệt.
- **Đã vá (v0.18.1):** cửa sổ **trải ra theo cột** thay vì chồng khít góc trái · nút **⊞ Xếp gọn**
  dàn lưới · đồng hồ về z-index 1 (trước nó đè lên cửa sổ, nuốt mất cú bấm).
- **Đã có (v0.23.0):** **kéo-thả** (thả vào thư mục để chuyển · thả vào 🗑 dock để bỏ) ·
  **menu chuột phải** (trên hàng tệp và trên nền).
- **Thiếu:** biểu tượng trên mặt nền · nhiều bàn làm việc ảo · **danh sách cửa sổ trên thanh
  trên** (giờ muốn tìm cửa sổ bị che thì phải bấm dock) · kéo-thả **giữa hai cửa sổ Tệp**
  (giờ chỉ trong cùng một cửa sổ) · chọn nhiều tệp một lúc.
- **Bắt đầu:** `de/de.js` (phần cửa sổ + ứng dụng Tệp).

### ~~G2. Ứng dụng Tệp~~ — **XONG v0.26.0**
- **Đã có:** 🗑 bỏ vào thùng rác · ? `vì_sao` (v0.15.0) · **đổi tên · đổi quyền · chuyển** qua
  chuột phải và kéo-thả (v0.23.0) · **tạo tệp/thư mục mới** (chuột phải trên NỀN cửa sổ) và
  **chép** (v0.26.0 — gọi-hệ 42 `GH_CHÉP` ~cp: cần ĐỌC nguồn + GHI thư-mục đích, KHÔNG đè,
  bản sao thuộc người chép; lệnh vỏ `chép`).
- **Còn mở nhỏ:** `chép` chỉ chép TỆP thường — chưa có chép cả THƯ MỤC (`cp -r`).

### ~~G3. Trình soạn thảo văn bản~~ — **XONG v0.23.0**
- Ứng dụng **Soạn thảo**: mở/sửa/lưu, đọc-ghi qua đúng `GH_ĐỌC`/`GH_GHI`/`GH_TẠO` nên quyền chặn
  y hệt dòng lệnh (có test cả hai chiều).
- **Thiếu nhỏ:** chưa hỏi "chưa lưu, thoát thật không?"; chưa `ghi_nếu` (H7) để hai người cùng
  sửa một tệp thì kẻ sau bị chặn thay vì đè — **hạ tầng đã có sẵn, nối vào là xong**.

### G4. Một máy chủ = một phiên
- **Hiện tại:** `giao_de.py` giữ MỘT máy GIAO, nên hai tab trình duyệt = **cùng một phiên**.
  Muốn nhiều phiên song song thì cần bảng phiên (hạ tầng đã sẵn: `đăng_nhập` trả tid vỏ riêng —
  xem ghi chú C4).

---

## D. PHẦN CỨNG / SILICON

### D1. CẮM BO THẬT *(việc duy nhất cần MUA ĐỒ)*
- **Trạng thái:** bitstream **đã dựng xong** — `D:\giao_bitstream\gvm.bit`, ECP5-85F, 7.067 LUT (8%),
  30 BRAM (14%), Fmax 39,66 MHz (chạy 25 MHz).
- **Chặn bởi:** máy **không có bo FPGA nào** (`openFPGALoader --scan-usb` ra bảng rỗng).
- **Khi có bo:**
  ```
  python hw/lam_bitstream.py --nạp        # nạp lên bo
  python hw/nhan_qua_uart.py COM7         # nhân GIAO phục vụ CPU trên silicon
  ```
- **Bo gợi ý:** ULX3S (ECP5-85F) — đã có sẵn `hw/ulx3s_top.v` + `hw/ulx3s.lpf`.

### D2. Bo khác ULX3S
- **Thiếu:** mỗi bo cần một vỏ như `hw/ulx3s_top.v` + tệp ràng buộc chân riêng. `hw/gvm_bo.v` giữ nguyên.
- **Với bo Xilinx** thì luồng mã nguồn mở không dùng được — phải Vivado.

### D3. Trap phần cứng mới nhận 0–3 đối
- **Đủ dùng** cho bảng gọi-hệ hiện tại (nhiều nhất là `tạo(đường, quyền, nội)`).
- **Muốn hơn:** nới vòng `trap_k` trong `hw/gvm.v` (trạng thái `S_TRAPA`) — việc cơ học.

### D4. Chưa có ràng buộc thời gian tử tế
- **Hiện tại:** chỉ khai 25 MHz trong `.lpf`; Fmax 39,66 MHz nên dư 59%, nhưng chưa phân tích đường
  tới hạn. Nếu sau này thêm logic thì phải soi lại.

---

## E. TRỢ LÝ AI

### E1. Trái tim (Ollama) đã GỠ khỏi máy
- Xem trí nhớ `ollama-heart-setup` — cách cài lại **vào ổ D** và hiệu chỉnh ngưỡng γ.
- Không có tim thì trợ lý chạy bằng **bảng mẫu**, vẫn đúng nhưng hẹp.
- **2026-07-30:** `kiem_hdh_giao.py` mục [21] nay NHẬN BIẾT backend qua `/tb/tim` — tim dự phòng
  thì kiểm *xếp hạng đúng + từ chối an toàn dưới ngưỡng* thay vì đòi trả lời (γ băm-từ chỉ ~381
  < ngưỡng 450). Cài tim thật lại thì test tự đòi mức cao hơn, không phải sửa gì.

### E2. Vốn động từ của trợ lý là bảng tay (~11 động từ), mỗi lần soạn MỘT lệnh
- **Thiếu:** chưa ghép nhiều bước, chưa hiểu câu phức.
- **Bắt đầu:** `lib_trợ_lý.giao` — `sinh_ứng_viên` và bảng động từ.
- **Ba cửa chặn (cùng-danh-tính · γ-ngưỡng · bất-khả-hồi) là CHỦ Ý, không phải thiếu sót — giữ nguyên.**

---

## F. VẶT NHƯNG HAY CẮN

- ~~**Đường dẫn tiếng Việt** phá `vvp` / `nextpnr` / `iverilog`~~ — **ĐÃ CHỮA TẬN GỐC 2026-07-29**:
  dự án chuyển từ `D:\Hệ điều hành\GIAO` sang **`D:\HeDieuHanh\GIAO`**, mọi chỗ lách đã gỡ bỏ.
  **Đừng đặt dự án vào thư mục có dấu nữa** — ổ D đã tắt tên 8.3 nên không lách bằng đường dẫn ngắn
  được, và cách chữa duy nhất khi ấy là chép tệp đi nơi khác.
- **`yosys` không nuốt định danh tiếng Việt** trong RTL (chú thích thì được) ⇒ `hw/*.v` phải đặt tên
  ASCII. `iverilog` cũng vậy.
- **RAM chỉ được 1 cổng đọc + 1 cổng ghi** nếu muốn ở lại BRAM. Thêm cổng thứ ba là cả `4096×32` rơi
  xuống 133.078 flip-flop và tổng hợp chạy hơn nửa tiếng. Nếu sau này thêm cổng cho RAM, phải làm
  cho tính loại-trừ **hiện ra trong RTL** (kiểu `if (!dbg_we)`), vì yosys không tự chứng minh được
  với tín hiệu đến từ chân ngoài.
- **Testbench để hở chân input** làm X lan khắp thiết kế và kết quả rỗng không rõ lý do — luôn nối
  đất mọi chân `dbg_*` khi thêm cổng mới vào `gvm.v`.

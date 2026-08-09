# CHANGELOG — GIAO

Mọi thay đổi đáng kể của ngôn ngữ lập trình GIAO (Vùng Giao Thoa / CDFL).
Nền học thuyết: Nguyễn Trường An (DFCT / NNL-NTHT / CDFL).

---

## v0.29.0 — ★★★★★ B3: TẦNG KHỐI + NHẬT KÝ PHỦ CẢ DỮ LIỆU + GẮN ĐĨA (2026-07-31)

Lại quan sát máy thật trước. Bốn lệnh trên Kali 2026.2 (ext4):

| soi gì | trả về | nghĩa |
|---|---|---|
| `findmnt -no OPTIONS /` | `…,**data=ordered**` | nhật ký phủ **siêu dữ liệu**, **KHÔNG** phủ dữ liệu |
| `tune2fs -l` | `Block size 4096 · Inode size 256 · … **metadata_csum**` | checksum **không** phủ dữ liệu người dùng |
| `du -B1` (tệp 1 byte) | **4096** | cái giá thật của quản lý theo khối |
| `man 2 fsync` | *"does not necessarily ensure that the entry in the directory containing the file has also reached disk"* | độ bền là **kiến thức truyền miệng** |

### ★★★★ Ba chỗ ext4 yếu — và làm khác thế nào

**① `data=ordered` không ghi nhật ký cho DỮ LIỆU.** Đây là **mặc định trên máy thật**, không phải
cấu hình lạ. Mất điện giữa lúc ghi thì siêu dữ liệu có thể đã nói *"tệp dài 4KB"* trong khi khối
dữ liệu còn là **rác của tệp cũ** — hệ-tệp tự nó "nhất quán", nhưng **nội dung thì sai và không ai
báo**. Ở đây nhật ký **chở cả khối dữ liệu**, nên chỉ có hai kết cục: **thấy trọn vẹn** hoặc
**không thấy gì**. Phép thử quyết định là **cắt điện giữa lúc ghi** ở đúng hai điểm:

- *trước* dấu cam kết → phát lại **vứt 8 khối** ⇒ đọc ra **đúng bản CŨ, nguyên vẹn từng chữ**;
- *sau* cam kết, **giữa lúc chép** (mới chép 4/8 khối) → phát lại **chép tiếp** ⇒ đọc ra **đúng bản
  MỚI, trọn vẹn**. Không có cửa nào cho "nửa cũ nửa mới".

**② `metadata_csum` không phủ dữ liệu người dùng.** Khối mục thầm lặng thì ext4 **trả ra như thật**
— không có cách nào biết (muốn có phải sang btrfs/zfs). Ở đây **mỗi khối mang tổng kiểm**; đọc phải
khối hỏng thì **báo**, và báo cả qua **gọi-hệ** nên chương trình không bao giờ nhận được rác.

**③ `fsync(tệp)` không làm bền cái TÊN** — chính trang man nói phải `fsync` cả thư mục cha. Nghĩa là
ai không biết mẹo ấy thì mất dữ liệu, mà mất im lặng. Ở đây **tên và nội dung nằm cùng MỘT giao
dịch**: cắt điện trước cam kết thì **tên cũng không sinh ra**, tệp cũ còn nguyên.

**④ Không phải chỗ yếu, là cái giá thật:** khối 4096 B ⇒ tệp 1 byte tốn 4096 B. Ta cũng phải trả,
nên lệnh `đĩa` **hiện thẳng số byte phí ra** thay vì giấu (`1 tệp · 1/64 khối×32B · dùng 15B, phí 17B`).

### GẮN (mount) — đường dẫn thường, tầng khối bên dưới

`gắn_đĩa` treo đĩa vào một thư mục **đã có**; từ đó `ghi /đĩa/thơ` · `xem /đĩa/thơ` · `liệt /đĩa`
đi thẳng xuống tầng khối qua bốn cửa gọi-hệ (ĐỌC · GHI · TẠO · LIỆT). **Chỉ gốc-quyền được gắn**
(như `mount`), và **quyền của ĐIỂM GẮN quyết định** ⇒ gắn đĩa **không mở thêm cửa nào**: đặt `/đĩa`
về 700 thì người thường hết đọc lẫn ghi. Lệnh vỏ `đĩa dựng|gắn|tháo|soi`. Gắn xong **luôn báo đã
làm gì với nhật ký** — ext4 cũng phát lại lúc mount, nhưng hỏng nặng thì đòi **con người chạy `fsck`**.

- ⚠ **Trung thực:** "đĩa" vẫn là cấu trúc **trong bộ nhớ** máy GIAO, **chưa phải mặt đĩa vật lý** —
  phần bền qua tắt máy vẫn nhờ ảnh chụp JSON như cũ. Cái mới thật sự là **NGỮ NGHĨA**. Tổng kiểm
  dùng djb2 nên bắt hỏng **ngẫu nhiên**, **không** chống kẻ **cố ý**. Đĩa mới có **tệp phẳng**
  (chưa có thư mục con), chưa xoá tệp, chưa thu hồi khối, chưa gắn được `/`.
- *Vấp:* một ca kiểm rớt vì **bộ kiểm sai chứ không phải mã sai** — tôi đặt "đĩa quá nhỏ" 12 khối ×
  16 B mà nội dung thử vẫn vừa. Phải tính lại sức chứa thật (8 khối dữ liệu = 128 B) rồi mới có ca
  tràn thật. *Ca phủ định chỉ có giá trị khi đã tính đúng ngưỡng.*
- **Kiểm:** `kiem_dia.giao` (MỚI) → mục **[37]** của `kiem_hdh_giao.py`, thêm 18 hạng mục.
  `kiem_hdh_giao.py` **385/385**.

---

## v0.28.0 — ★★★★★ B2 XONG: SỔ ĐỊNH DẠNG CHẠY ĐƯỢC + `/lệnh` mang chính BYTECODE (2026-07-31)

Quan sát Kali ở v0.27.0 đã **đổi cách nghĩ về chính mục này**, và đó mới là phần đáng kể lại.
Đếm `/bin` của Kali ra **1540 tệp ELF nhưng 897 tệp là kịch bản có `#!`** — **ngay Linux thật cũng
pha trộn văn bản với nhị phân**. Vậy B2 không phải là "bỏ văn bản đi" như tên mục cũ gợi ý. Cái
đáng học nằm ở **`binfmt_misc`**: nhân giữ một **sổ đăng ký** ánh xạ *magic → trình chạy*, còn
`#!` chỉ là **một mục** trong sổ ấy. Theo hình dạng đó thì thêm bytecode là **thêm một DÒNG**.

- **★★★ `lib_dinh_dang.giao` + sổ `/hệ/định_dạng`** (644, bốn cột `tên|magic|trình|năng_lực`).
  `chạy_một_lệnh` **không còn nhánh ghi cứng nào** — trước đây nó biết sẵn `#nội-trú` / `#tt ` /
  "còn lại là kịch bản", nên thêm định dạng là phải sửa vỏ. Đúng cái bệnh `binfmt_misc` sinh ra để chữa.
- **★★★★ Định dạng `#!mã-máy` — `/lệnh/<tên>` mang CHÍNH bytecode GVM.** `đăng_ký_ct_mã` +
  nhánh `ct_mã` trong `GH_SINH` nạp **thẳng** lên GVM: chạy một lệnh như thế **không đụng tới
  trình biên dịch**. Khác `ct_máy` (giữ mã NGUỒN rồi dịch lại mỗi lần sinh) đúng ở điểm cốt lõi ấy.
- **Lệnh `dịch <nguồn> <đích>`** sinh ra tệp mã máy; **lệnh `định_dạng [tệp]`** liệt kê sổ (đánh
  dấu ✗ cho định dạng thiếu năng lực) hoặc nói vì sao một tệp chạy được / không.
  Nghiệm thu sống: `dịch` → `xem` ra **bytecode chứ không phải nguồn** → chạy vẫn ra **42**.

### ★ Ba chỗ `binfmt_misc` yếu — và đã vá

1. **Đăng ký sai làm hỏng đường chạy CẢ MÁY.** Linux cho ghi thẳng vào `/proc`, không ai kiểm.
   Ở đây sổ đi qua **bộ kiểm cấu hình H6 ở tầng gọi-hệ**: bắt **trùng magic** (*"dòng này không
   bao giờ tới lượt"* — Linux im lặng cho qua), **ngả lui `*` đặt giữa sổ** (nuốt hết dòng sau),
   **thiếu ngả lui**, **trình không có thật** — mỗi lỗi kèm **số dòng**, và **tệp cũ còn nguyên**.
   Mạnh hơn nữa: **xoá hẳn sổ đi máy vẫn chạy lệnh**, vì ngả lui `dạng_mặc_định()` nằm **trong mã,
   không nằm trên đĩa**. *Không có cách nào làm máy câm bằng cách phá sổ.*
2. **Không nói được VÌ SAO.** Linux ném `ENOEXEC` — *"Exec format error"*, hết. `vì_sao_dạng` chỉ
   đúng nấc: khớp định dạng nào, magic gì, trình nào, thiếu năng lực nào, **và cách bật nó**.
3. **Định dạng không khai được nó cần gì.** Đăng ký một thông dịch cho magic nào đó ở Linux là
   trao trọn quyền, không ai hỏi. Ở đây mỗi dòng **tự khai năng lực** (như gói phần mềm từ
   v0.18.0): chưa cấp `máy` thì `#!mã-máy` **bị từ chối kèm lý do**, chứ không chạy nửa vời.

- **Quyền vẫn xét TRƯỚC khi tra sổ** ⇒ thêm định dạng **không mở thêm cửa nào**: tệp mã máy thiếu
  bit `x` vẫn bị chặn y hệt, ở cả hai chế độ.
- ⚠ **Trung thực về chữ "nhị phân":** hệ-tệp GIAO chứa **chuỗi**, nên từ-lệnh được viết ra dạng
  **số thập phân** cách nhau bằng khoảng trắng. Cái đã đổi thật sự là **tệp mang MÃ chứ không mang
  NGUỒN**; còn gọi nó là "nhị phân" thì vẫn là nói quá. Ghi đúng như vậy trong `lib_dinh_dang.giao`.
### ★ Vấp đáng kể nhất: tra sổ nằm trên đường đi của MỌI lệnh

Bản đầu đọc + tách dòng + tách cột sổ **mỗi lần chạy một lệnh**. Kết quả: bản trình diễn
`hdh_giao.giao` **chạm trần 5 triệu bước ngay lần chạy đầu** — 12 hạng mục rớt một lượt, mà nhìn
qua thì tưởng 12 lỗi khác nhau. *Đây đúng cái bẫy §5.5 đã ghi từ trước (procfs tái sinh mọi lời
gọi + tra `$PATH`), lần này vấp lại ở chỗ mới.*

Cách vá **khoá bản nhớ bằng CHÍNH nội dung thô của sổ**, không bằng một cờ "đã đổi":

- sổ đổi một ký tự là bản nhớ **tự hết hiệu lực** ⇒ **không ai phải nhớ đi xoá bộ nhớ đệm**, và
  không có cửa nào để quên xoá rồi chạy theo sổ cũ;
- nếu thay bằng "xoá đệm lúc ghi" thì phải rải lệnh xoá ra khắp `GH_GHI`/`GH_TẠO`/`GH_THÊM`/
  `GH_XOÁ`/`GH_BỎ`/`GH_CHUYỂN` — sáu chỗ, và **quên một chỗ là chạy sai mà kiểm vẫn xanh**.
- **Đo sau khi vá:** bản trình diễn cần khoảng **4–5 triệu bước** (chạy được ở mức mặc định 5M,
  rớt ở 4M) ⇒ **chỉ còn dư ~20%**. Ghi ra đây vì việc nào sau này đặt thêm chi phí lên
  *đường đi của mọi lệnh* thì phải đo lại trước, đừng đợi bộ kiểm đổ 12 hạng mục mới biết.

- *Vấp (lần thứ HAI trong hai phiên liên tiếp):* thêm lệnh nội trú lại làm bộ kiểm đếm CỨNG số tệp
  `/lệnh` rớt (59 → 61). Lần này đoán trước và sửa luôn — nhưng con số ấy vẫn là một cái bẫy nằm chờ.
- **Kiểm:** `kiem_dinh_dang.giao` (MỚI) chạy **HAI LẦN** — chưa cấp `máy` và đã cấp, cùng một tệp
  hai kết quả (lối kiểm của `lib_ngày_host`) → mục **[36]** của `kiem_hdh_giao.py`, thêm 18 hạng
  mục. `kiem_hdh_giao.py` **367/367** · `kiem_de.py` **41/41** · `kiem_tu_xa.py` **37/37**.

---

## v0.27.0 — ★★★★ ĐỐI CHIẾU KALI 2026.2: băm `$g3$` KHÓ-VỀ-BỘ-NHỚ + máy chủ ÉP đổi khoá (2026-07-31)

Quan sát **máy Kali thật** (WSL, 2026.2) rồi mới làm — không đọc sách rồi đoán. Lần này tìm ra
**một chỗ Kali hơn ta** và **hai chỗ Kali hở**.

### ★★★ Chỗ Kali HƠN ta: `ENCRYPT_METHOD YESCRYPT` → ta thêm `$g3$` khó về BỘ NHỚ

`grep ENCRYPT_METHOD /etc/login.defs` trên Kali trả về **`YESCRYPT`** — memory-hard. Còn `$g2$`
của ta chỉ khó về **thời gian**, mà SHA-256 gần như không cần bộ nhớ ⇒ **GPU nhét vài nghìn nhân
băm song song là thắng**. Nói thẳng: đây là chỗ ta thua.

- **`băm_mk3` — ROMix kiểu scrypt (Percival 2009), thuần GIAO.** ① **ĐỔ ĐẦY** `V[0..N−1]`, mỗi ô
  là băm của ô trước ⇒ tuần tự, không rút gọn. ② **TRUY CẬP NGẪU NHIÊN**: mỗi bước lấy `j` từ
  **chính trạng thái hiện tại** rồi trộn với `V[j]` — `j` chỉ biết được sau khi đã tính tới đó,
  nên **không nạp trước, không đoán trước**. Kẻ tiếc bộ nhớ chỉ giữ một phần bảng thì mỗi lần
  trượt ô phải **tính lại từ đầu** — đúng cái giá đổi-bộ-nhớ-lấy-thời-gian khiến GPU/ASIC hết rẻ.
- **★ Điểm quyết định của bản này: KHÔNG phải trả thêm gì.** Đo thật (trừ chi phí khởi động,
  3 lần/phép): **`$g2$` 128 vòng = 743 ms/lần · `$g3$` N=64 = 752 ms/lần — chênh 1,2%.**
  Cùng một ngân sách thời gian, nay mua thêm được tính khó-về-bộ-nhớ. Đó là lý do đổi mặc định.
- **Ba định dạng song song** (`$g1$` · `$g2$` · `$g3$`) — **không ai phải đổi mật khẩu.**
- **Kiểm bắt đúng chỗ dễ cài sai:** không chỉ "băm ra chuỗi khác", mà ① đổi `N` phải đổi **cả đường
  đi trong bảng** (cài nhầm thành xích tuần tự thì `N=8` sẽ là **tiền tố** của `N=16` — kiểm này
  bắt được); ② dãy chỉ số `j` phải **TẢN** thật (đo: 23/24 khác nhau) — nếu `j` chạy đều 0,1,2…
  thì bảng `V` **không cần giữ** và toàn bộ tính khó-bộ-nhớ sụp, dù đầu ra trông vẫn "ngẫu nhiên".
- ⚠ **Trung thực:** bảng mới `N=64 × 32B = 2 KB`, còn xa scrypt (16 MB) và yescrypt. Có **đúng cấu
  trúc** nhưng **lượng** còn nhỏ ⇒ mới chặn GPU được phần nào. `N` nằm trong bản ghi nên nâng được.

### ★★★ Chỗ Kali/sshd HỞ #1: rekey chỉ là thiện chí → máy chủ ta ÉP

`man 5 sshd_config`: `RekeyLimit` mặc định 1G–4G dữ liệu + hạn thời gian. Cái đáng học không phải
con số mà là **hạn nằm ở CẢ HAI đầu**. Bản v0.26.0 của ta chỉ có **khách** tự đổi mỗi 32 khung —
tức an toàn của phiên **treo vào thiện chí của phần mềm đầu kia**; khách viết cẩu thả (hay cố ý)
cứ dùng mãi một khoá thì máy chủ chiều tuốt.

- Máy chủ nay **đếm và TỪ CHỐI PHỤC VỤ** khi quá `TX_HẠN_KHUNG = 64` khung mà chưa đổi khoá.
  Kiểm đặt **SAU** nhánh `ĐỔI_KHOÁ` nên **đường thoát duy nhất là đổi khoá** — không cách nào gõ
  tiếp bằng khoá cũ. Số đếm do khách mang lên nhưng **MAC phủ nó và nó phải TIẾN**, nên không khai
  lùi để né hạn được.
- **Vì sao ta đếm KHUNG còn sshd đếm BYTE:** khung SSH to nhỏ rất chênh (16 B → 32 KB) nên đếm
  khung ở đó vô nghĩa. Ở đây khung là **dòng lệnh**, và ta **chặn thẳng khung quá dài**
  (`TX_KHUNG_TỐI_ĐA = 8192` ký tự trên dây, bỏ **trước khi giải** nên không ngốn bộ nhớ) — nhờ vậy
  "số khung × cỡ tối đa" là một **cận trên thật** cho dữ liệu giữa hai lần đổi khoá (512 KB).
- Phép thử quyết định: **khách BƯỚNG** (vòng lặp không thèm rekey) → bị chặn; đổi khoá xong gõ
  tiếp được ngay; **khách TỬ TẾ** chạy 70 lệnh **không hề vướng hạn** (tự đổi 2 lần dọc đường).

### ★★ Chỗ Kali HỞ #2: `pam_faillock` CÓ mà KHÔNG BẬT — và cách nó chậm lại là đòn bẩy DoS

| soi gì trên Kali thật | trả về | nghĩa |
|---|---|---|
| `ls .../security/pam_faillock.so` | **có** | công cụ khoá tài khoản có sẵn |
| `grep faillock /etc/pam.d/*` | **không dòng nào** | **KHÔNG BẬT** — mặc định đoán mật khẩu thoải mái |
| `man 8 pam_unix` | *"delay-on-failure of the order of two seconds"* | chậm **CỐ ĐỊNH 2s**, bằng cách **`sleep` chính tiến trình** |
| `man 8 pam_faillock` | `deny=4 unlock_time=1200` | khoá 20 phút — **nếu** ai đó bật lên |
| `grep PASS_MAX_DAYS /etc/login.defs` | `99999` | hạn tuổi mật khẩu **tắt** trên thực tế |
| `cat /etc/pam.d/common-auth` | `pam_unix.so **nullok**` | **mật khẩu RỖNG được nhận** — ô bóng để trống là vào thẳng |

Bốn chỗ ta cố ý làm khác (đã có từ v0.26.0, nay ghi rõ **vì sao** sau khi soi máy thật):
**① bật sẵn** ở đúng một điểm chặn (`đăng_nhập`) chứ không "có mà không cắm"; **② chậm DẦN** gấp
đôi chứ không cố định; **③ ★ KHÔNG `sleep` mà TỪ CHỐI** — `pam_unix` ngủ 2s *trong chính tiến
trình xác thực*, nên mở 100 kết nối là **giữ chân 100 tiến trình**: thứ dùng để chống dò lại thành
**đòn bẩy làm nghẽn máy**. Ta ghi **mốc thời gian** vào sổ rồi **trả lời ngay** — không luồng nào bị
treo, mà kẻ dò vẫn phải chờ; và vì mốc nằm ở **sổ chung theo TÊN**, mở bao nhiêu kết nối song song
cũng **cùng chịu một quãng chờ**, chứ không mỗi kết nối một đồng hồ riêng như `sleep`.
**④ chừa `gốc`** khỏi tự-khoá (như `pam_faillock` mặc định) — kẻo kẻ dò gõ bừa 10 lần là khoá cửa
chủ máy.

Thêm một chỗ **ta kín sẵn mà không phải làm gì**: `nullok` cho phép **mật khẩu rỗng**. Ở đây việc
ấy **không xảy ra được** — bộ kiểm cấu hình H6 gắn ở **tầng gọi-hệ** đòi ô bóng bắt đầu bằng
`$g1$`/`$g2$`/`$g3$`, thử ghi `an:` là bị từ chối kèm số dòng và **tệp cũ còn nguyên** (đã thử).
Lợi tức của quyết định cũ: đặt bộ kiểm ở chỗ **mọi cửa ghi đều phải qua**, thay vì làm một tuỳ
chọn mà quản trị viên phải nhớ bật — đúng cái bệnh của `pam_faillock`.

### ★★★ Tự bắt được trong lúc đối chiếu: RÒ RỈ THEO THỜI GIAN khi xác thực

Lỗi nằm **đúng trong thứ ta tưởng đã làm cẩn thận**. Ta luôn trả lời *"Sai tên đăng nhập hoặc mật
khẩu"* để không chỉ điểm — nhưng **đo ra** thì người **có thật** tốn **~750 ms** (chạy đủ `$g3$`),
còn người **không có** và tài khoản **bị khoá** trả lời **~0 ms** (tra sổ hụt là trả về ngay).
Kẻ dò **không cần đọc câu trả lời** — bấm giờ là đếm sạch tài khoản rồi mới dồn sức vào tên có
thật. **Giấu ở lời nói mà hở ở đồng hồ thì coi như không giấu.**

- **Vá theo lối OpenSSH (*fake password hashing*):** không có người ấy thì **vẫn băm một `BÓNG_GIẢ`
  rồi vứt kết quả**; tài khoản bị khoá cũng đi qua đó, kẻo lộ *"có thật, đang bị khoá"*.
  `BÓNG_GIẢ` **dựng từ `MK_N3`** nên nâng `N` thì bản giả tự theo — không có chuyện quên đồng bộ.
- **Kiểm ĐO THẬT, và đã thử tháo bản vá ra để xem nó có rớt không:** tháo ra →
  `có-thật=3s · không-có=0s · bị-khoá=0s` → rớt cả hai ca. *Một cái chốt chỉ đáng tin khi đã thấy
  nó bật.* Vá vào → `3 · 3 · 4` giây, ngang nhau.
- ⚠ **Cái giá, nói cho hết:** nay gõ tên bừa cũng ngốn 750 ms CPU máy chủ, mà sổ chậm-dần khoá theo
  TÊN nên không chặn kẻ đổi tên liên tục. Thứ giữ cho phép tính không lỗ là **hạn 3 lần sai mỗi
  kết nối**: đứt rồi nối lại phải làm trọn một vòng **DH 2048-bit** — đắt cho kẻ gọi hơn máy chủ.

### ★★ TRẦN CÔNG cho bản ghi bóng — cũng tự bắt được khi soi lại

Bản ghi **tự khai** số vòng / số ô, mà `khớp_mk` lại **chạy đúng theo lời khai ấy**. Một dòng
`$g3$999999999$…` lọt vào sổ (sổ hỏng · ảnh chụp cũ nạp lại · gói cài bậy) là **treo máy ngay tại
màn đăng nhập** — kẻ tấn công **không cần biết mật khẩu**, chỉ cần ghi được một dòng. Nay có
`MK_TRẦN_VÒNG = 100000` / `MK_TRẦN_N = 4096` và chặn `vòng < 1` (0 vòng = không tốn công gì).
Trần **không hạ mức an toàn** — nó chỉ chặn con số vô lý, còn dư xa mức đang dùng (128 / 64).

### Ghi chú cho B2 (đổi cách nghĩ, chưa làm)

Soi `/bin` của Kali: **1540 tệp ELF nhưng 897 tệp là kịch bản có `#!`** — **ngay Linux thật cũng
pha trộn văn bản với nhị phân**. Vậy đích của B2 không phải "bỏ văn bản đi", mà là **`binfmt_misc`**:
nhân tra **byte đầu tệp** trong một **sổ đăng ký** để chọn trình chạy, `#!` chỉ là một mục trong sổ.
Chỗ `binfmt_misc` yếu (để ta làm khác): sổ là **trạng thái toàn cục chỉ gốc sửa**, đăng ký sai một
mục là **hỏng đường chạy cả máy** mà không nói vì sao, và **không khai được "định dạng này cần năng
lực gì"** — ta đã có `vì_sao` (H2) và gói tự-khai-năng-lực (v0.18.0) để nối vào.

- *Vấp đáng ghi:* GIAO **không cho xuống dòng rồi mới tới `+`** — phải để `+` ở cuối dòng trên.
  Viết chuỗi thông báo dài kiểu Python là gãy cú pháp ngay lúc `nhập` thư viện.
- *Vấp thứ hai:* đổi định dạng bóng làm **ba bộ kiểm khác** rớt vì chúng dò chuỗi cứng `$g2$128$`
  trong sổ bóng. Định dạng bản ghi là **giao diện công khai** — đổi thì phải quét cả cây kiểm.
- **Kiểm:** `kiem_lib_mật_khẩu.giao` +10 ca (`$g2$` cũ vẫn khớp · `$g3$` ổn định/thác đổ/đổi-N/
  chỉ-số-tản · trần công) · `kiem_ro_ri_thoi_gian.giao` (MỚI, mục [35]) · `kiem_tu_xa.py`
  **37/37** (mục [4b] ép rekey + khung quá dài) · `kiem_hdh_giao.py` **349/349**.

---

## v0.26.0 — ★★★★ REKEY + CHỐNG DÒ MẬT KHẨU (khép C4·C5) + `GH_CHÉP` (khép G2) (2026-07-31)

- **★★★ ĐỔI KHOÁ GIỮA PHIÊN (rekey — C4-③).** Phiên dài mà dùng mãi một khoá là mục tiêu béo:
  càng nhiều bản mã cùng khoá càng dễ soi, lộ khoá phiên là lộ CẢ phiên. Nay khách gửi
  `ĐỔI_KHOÁ <B₂>` **ngay trong kênh cũ**, máy đáp `ĐỔI_KHOÁ_OK <A₂>` (dòng cuối dưới khoá cũ),
  hai bên cùng tính bí mật DH mới, **thay trọn bộ ba khoá (lên · xuống · MAC) và đưa số đếm về 0**.
  - **KHÔNG cần ký lại giá trị DH** — khung rekey đi trong kênh đã xác thực bằng HMAC (khoá chỉ
    hai bên biết) nên kẻ đứng giữa không chèn nổi; đúng lối SSH rekey bên trong transport đang mã.
  - Khách **tự đổi sau mỗi 32 khung** (`REKEY_MỖI`), và ép được bằng `@đổi_khoá` trong kịch bản.
  - Phép thử quyết định (soi dây): khung SAU rekey — **khoá MỚI mở được, khoá CŨ trả None**;
    lộ một khúc không đọc được khúc trước/sau.
- **★★★ CHỐNG DÒ MẬT KHẨU (C4-④) + TỰ KHOÁ SAU N LẦN SAI (C5).** Sổ `DÒ_SỔ` theo TÊN, móc
  **ngay trong `đăng_nhập`** — một điểm chặn phủ CẢ ba cửa: tại máy, `thành`, từ xa.
  - Hai lần sai đầu **không phạt** (người gõ nhầm thật không vướng); từ lần thứ 3 **chờ gấp đôi**
    2s → 4s → … trần 60s (cần năng lực `giờ`; máy chủ từ xa nay cấp).
  - **Trong quãng chờ, gõ ĐÚNG cũng KHÔNG xét** — không xét thì không lộ gì: kẻ dò không biết
    phép thử của nó trúng hay trượt. Đăng nhập đúng (ngoài quãng chờ) thì **xoá sổ** — chỉ phạt
    chuỗi sai LIÊN TIẾP.
  - Sai liên tiếp **10 lần → `khoá_người` tự động** (bóng = `*`) — **trừ `gốc`**: khoá gốc là để
    kẻ dò gõ bừa 10 phát mà khoá được cửa của CHỦ MÁY (pam_faillock cũng chừa root vì thế);
    gốc vẫn bị chậm dần như mọi người.
  - Từ xa thêm tầng theo KẾT NỐI: **3 lần sai là NGẮT** — kẻ dò phải tốn công bắt tay DH lại,
    còn sổ theo TÊN thì nối lại cũng không thoát (kiểm: nối lại vẫn bị bắt chờ).
- **★★ `GH_CHÉP` (gọi-hệ 42, ~cp) + lệnh vỏ `chép` — khép G2.** Khác `chuyển` đúng chỗ QUYỀN:
  chuyển cần GHI **cả hai** thư-mục cha (gỡ + gắn), chép chỉ cần **ĐỌC tệp nguồn + GHI thư-mục
  đích** — tệp gốc không suy suyển. KHÔNG đè (như chuyển); chỉ chép TỆP thường (ống/thiết bị
  không phải dữ liệu để chép); **bản sao thuộc NGƯỜI CHÉP, quyền theo tệp nguồn** (như cp Linux).
  - Ứng dụng **Tệp**: chuột phải trên hàng có **“⧉ Chép thành…”**; chuột phải **trên NỀN cửa sổ**
    có **“Tạo tệp mới” / “Tạo thư mục mới”** — đều qua đúng lệnh vỏ (`chép`/`sờ`/`tạothư`) nên
    quyền chặn y hệt dòng lệnh (kiểm: `an` không chép nổi `/hệ/mật_khẩu` ra ngoài).
- *Vấp đáng ghi:* thêm lệnh nội trú làm bộ kiểm “đếm tệp trong /lệnh” lệch một đơn vị (58 → 59)
  — con số ấy là ĐẾM CỨNG, thêm lệnh là phải nhớ nó.
- **Kiểm:** `kiem_chong_do.giao` (mới — kiem_hdh mục [34]) · kiem_hdh [33] thêm 5 ca chép ·
  `kiem_tu_xa.py` **32/32** (mục [4] rekey soi dây + mục [5] chống dò) · `kiem_de.py` **41/41**
  (mục [9] tạo/chép trong Tệp) · `kiem_hdh_giao.py` **340/340**.

---

## v0.25.0 — ★★★★ PHỤ THUỘC CÓ PHIÊN BẢN (I3) + LÙI NHIỀU BƯỚC (I4) (2026-07-31)

- **★★★ I3 — `cần X >= 2.0` và gói thay thế `a/b`.** Trước bản này chỉ nói được *"cần gói tên X"*
  — mà **"cần X" là vô nghĩa nếu X bản cũ không chạy nổi**. Nay có `>=` `>` `=` `<=` `<`, và
  lựa chọn thay thế (apt: `arping | iputils-arping`).
  - **`so_phiên` so theo TỪNG ĐỐT SỐ, không so chuỗi:** `1.10 > 1.9` — so chuỗi thì ra ngược,
    đó là bẫy kinh điển. Thiếu đốt tính là 0 (`1.2` = `1.2.0`).
  - **Từ chối thì phải nói RÕ VÌ SAO:** *"'trên' cần nền>=2.0 nhưng không thoả — kho chỉ có 'nền'
    bản 1.0"*. Và câu "vì sao kéo theo" nay nêu **đúng ràng buộc** thay vì "cần nó".
  - **★ Một chỗ KHÁC apt có chủ ý:** apt ngăn lựa chọn thay thế bằng `|`, nhưng ở đây `|` **đã là
    dấu ngăn CỘT** của mục lục — dùng cho cả hai việc thì **cột dịch sang phải, băm rơi vào ô
    khác**. *Tôi vấp đúng lỗi ấy khi viết.* Nên thay thế ngăn bằng **`/`** (an toàn vì tên gói
    không được chứa `/` theo H5), và **bộ kiểm H6 nay đòi ĐÚNG 7 cột** (không phải "ít nhất 7")
    để lỗi kiểu ấy lộ ra ngay thay vì âm thầm dịch cột.
- **★★ I4 — sổ lùi thành NGĂN XẾP nhiều bước.** Mỗi lần `gói nâng_cấp` là **một bước** có số;
  `gói lùi` **bóc từng bước một** và báo còn lùi được mấy bước nữa.
  - **Lỗi đã vấp và đáng kể lại:** bản cũ lấy từ thùng rác mà **không gỡ mục ấy ra**, nên bước lùi
    tiếp theo **vớ lại đúng nó** và trả về **sai bản** — lùi hai bước liên tiếp thì lộ. Thêm
    `rác_gỡ_mục` và gỡ ngay sau khi lấy nội dung. (Chỉ lùi một bước thì lỗi này ẩn hoàn toàn —
    phải kiểm hai bước mới thấy.)
- **Kiểm:** `kiem_kho_phien.giao` (mới): so phiên · ràng buộc · từ chối có lý do · thay thế chọn
  ngả hai · bảo vệ phụ thuộc · **nâng cấp hai lần rồi lùi hai lần, mỗi lần đúng bản**.
  → `kiem_toan_bo.py` **72/72**.

---

## v0.24.0 — ★★★★★ KHO PHẦN MỀM QUA MẠNG (I2): tải về ≠ tin (2026-07-31)

Ba thứ dựng trước gặp nhau: **mạng ra host (B1')** + **chữ ký RSA & neo tin cậy (I1)** +
**băm từng gói (v0.18.0)**. Cái mới không phải "tải được", mà là **tải về thì CHƯA TIN**.

- **★★★ `lib_kho.giao` biết ra ngoài:** `nguồn_xa` (`tên|máy|cổng`), `kho_tải_mục_lục`,
  `kho_tải_gói`; `_xa_lấy` nói giao thức trần trụi đúng một dòng — `LẤY <thứ>` rồi đọc tới khi
  đầu kia đóng (ổ cắm KHÔNG CHẶN nên quay vòng có hạn, không treo nhân).
- **★★★ TRÌNH TỰ MỚI LÀ ĐIỂM CHÍNH: tải → KIỂM CHỮ KÝ → *rồi mới* GHI.** Khoá công là thứ **đã
  có sẵn trên máy** (neo tin cậy), **không tải về**. Chữ ký sai thì **không một byte nào** được
  ghi xuống. Thân gói cũng phải khớp **băm trong mục lục đã ký** rồi mới được ghi.
- **★★ Vì sao KHÔNG mã hoá đường tải** (khác hẳn phiên từ xa): mục lục và gói vốn **công khai**;
  thứ cần là **toàn vẹn + xác thực**, mà chữ ký đã lo trọn. SSH phải mã hoá vì nó **chở mật
  khẩu**; kho thì không chở bí mật nào. Nói ra để không ai tưởng là bỏ sót.
- **★ Phân vai quyền cho đúng:** **mục lục** là tài sản chung (`/hệ`, chủ gốc) nên cập nhật cần
  **gốc-quyền** — y như `apt update`, và báo rõ *"thử `sudo gói tải`"*. Còn **thân gói** thì
  người thường tải vào **kho riêng** của mình (`/nhà/<tên>/kho_gói`) — vẫn **không cần nâng
  quyền để cài**, giữ đúng chỗ GIAO hơn apt.
- **Lệnh vỏ `gói tải`**; `gói cài` **tự tải thân gói còn thiếu** từ kho xa (kiểm băm ngay trong đó).
- **`chay_kho_xa.py`** — máy chủ kho "ở ngoài", có khoá riêng **của chính nó** (khác khoá kho cục
  bộ), `--dựng` sinh kho mẫu 3 gói gồm một gói **đòi năng lực nhạy cảm**.
- **★★★ Hai phép thử phủ định là phần đáng giá nhất** (`kiem_kho_xa.py`): ① **sửa MỘT ký tự**
  trong mục lục trên máy chủ → chữ ký gãy → từ chối **và không ghi byte nào**; ② kho ký bằng
  **khoá khác** (dù mục lục hợp lệ, băm gói đúng) → từ chối, vì **an toàn nằm ở neo tin cậy**.
  Thêm ca sandbox: chưa cấp `mạng_host` thì nói rõ, không lặng lẽ hỏng.
- **Hai lỗi đã vấp:** ① ghi mục lục vào `/hệ/kho` **thất bại im lặng** vì thiếu quyền — đúng loại
  lỗi im lặng dự án vẫn chê, nay **kiểm kết quả mọi lần ghi** và nói rõ cần gốc-quyền; ② bộ khung
  bài kiểm dựng máy trần nên `/lệnh` rỗng, kịch bản gói không có cả `nói` lẫn `tôi` — lỗi ở bài
  kiểm, không phải ở sản phẩm.
- **Kiểm:** `kiem_kho_xa.py` (mới) **12/12** → `kiem_toan_bo.py` **71/71**.

---

## v0.23.0 — ★★★★ NHÓM G: chuyển tệp · soạn thảo · chuột phải · kéo-thả (2026-07-31)

- **★★ Gọi-hệ 41 `chuyển` (~`mv`)** — HĐH thiếu hẳn phép đổi tên/dời chỗ, mà kéo-thả thì phải có.
  Cần **GHI trên CẢ HAI thư-mục cha** (đúng ngữ nghĩa Unix: chuyển là sửa hai thư mục), tên đích
  phải sạch (H5), và **KHÔNG ĐÈ** lên thứ đã có — đè là mất dữ liệu im lặng, thứ dự án tránh
  suốt. Chuyển là việc **khả hồi** (chuyển ngược là xong) nên **không qua cổng phê duyệt** —
  đúng học thuyết. Lệnh vỏ `chuyển`.
- **★★ Ứng dụng SOẠN THẢO** — mở tệp, sửa, lưu. Đọc/ghi đi qua **đúng gọi-hệ dưới uid của
  phiên**, nên `an` mở `/hệ/mật_khẩu` là *cấm đọc*, lưu vào `/hệ` là *cấm tạo* — y như dòng lệnh.
  Máy chủ khung hình thêm hai lối `đọc`/`ghi` (vẫn qua `GH_ĐỌC`/`GH_GHI`/`GH_TẠO`).
- **★ CHUỘT PHẢI** trên hàng tệp: Mở thư mục / Sửa bằng Soạn thảo · Đổi tên… · Bỏ vào thùng rác ·
  Vì sao bị cấm · Đổi quyền…  Chuột phải trên nền: mở nhanh ứng dụng + Xếp gọn.
- **★ KÉO-THẢ** hai lối: kéo tệp **thả vào thư mục** để chuyển; kéo **thả vào 🗑 trên dock** để bỏ
  vào thùng rác (vẫn lấy lại được). Cả hai đều đi qua đúng gọi-hệ, không có đường tắt.
- **Bẫy `sáng`/`tối` LÀ CHUỖI — lần thứ BA, và lần này nguy nhất:** lối `đọc` của máy chủ khung
  hình nhận `tối` (cấm đọc) rồi tưởng là **nội dung tệp**, nên trình soạn thảo suýt hiện chữ
  "tối" như thể đó là nội dung thật. Nay hỏi **nhân** (`lỗi_cuối`) thay vì đoán theo kiểu trả về —
  cách duy nhất đúng, vì một tệp hoàn toàn có thể chứa đúng chữ "tối".
- **Kiểm:** `kiem_hdh_giao.py` mục [33] (chuyển tệp: đổi tên · dời chỗ · **không đè** · quyền
  chặn) → 323→**328**; `kiem_de.py` mục [8] (soạn thảo: ghi/đọc/đè, **quyền chặn cả đọc lẫn
  ghi**) → 30→**36**; `kiem_toan_bo.py` **70/70**. Thử tay trong trình duyệt: chuột phải ra đủ
  5 mục · sửa-lưu-đọc lại đúng · kéo `thơ` vào `kho` rồi thả vào 🗑 và `hoàn_tác` lấy lại được.

---

## v0.22.0 — ★★★★★ BÍ MẬT CHUYỂN TIẾP: Diffie-Hellman 2048-bit trong GIAO (2026-07-31)

Chỗ hở của v0.21.0: khoá phiên do khách mã bằng **khoá công của máy** rồi gửi lên ⇒ ai ghi lại
đường truyền hôm nay, mai kia lấy được **khoá riêng của máy**, là giải ra **hết** mọi phiên cũ.
Diffie-Hellman vá đúng chỗ ấy.

- **★★★ `lib_dh.giao` — Diffie-Hellman, nhóm MODP 2048-bit của RFC 3526 (nhóm 14), g = 2.**
  Mỗi phiên hai bên sinh một **khoá TẠM**, trao phần công khai, cùng tính bí mật chung, rồi
  **vứt khoá tạm**. Khoá riêng của máy **không còn tham gia tạo bí mật** — nó chỉ **KÝ** giá trị
  DH của máy để chứng minh "A này đúng là của tôi". Lộ khoá máy về sau ⇒ **vẫn không giải nổi
  phiên cũ**. KDF: SHA-256 có đếm → 96 byte. Kiểm biên `1 < B < p−1`.
- **★★ Năng lực mới `ngẫu_nhiên`** (`--cho-ngẫu`) — entropy THẬT của máy chủ. Đặt thành **năng lực
  chứ không phải hàm sẵn** là có chủ ý: ngẫu-nhiên-thật là một **thiết bị**, không phải phép toán;
  còn `ngẫu()` của thư viện chuẩn là **LCG tất định** — tốt cho mô phỏng, đem làm khoá là hỏng
  ngay. Tách hai thứ ra để không ai lỡ tay dùng nhầm, và để host **thấy rõ mình đang cấp gì**.
- **★ GIAO nay KÝ được** (`ký_chữ_ký` trong `lib_chu_ky.giao`) — cùng `mũ_mod`, chỉ khác là mũ bí
  mật. Đúng vai: khoá riêng của **kho** không bao giờ vào máy, còn khoá riêng của **máy** thì máy
  phải giữ để tự chứng minh mình là ai (như host key của `sshd`).
- **Bắt tay mới:** máy chào `GIAO-DH <vân tay> <A> <chữ ký A>` → khách **đối chiếu vân tay** rồi
  **kiểm chữ ký trên A** (không có bước này thì DH vô nghĩa trước kẻ đứng giữa) → gửi `B` → hai
  bên dựng khoá phiên. Toàn bộ bắt tay của máy chủ nằm trong GIAO; Python chỉ là đầu cuối.
- **★★ Kiểm HẰNG SỐ bằng ĐỊNH NGHĨA, không so chuỗi** (`kiem_dh_nhom.py`): số nguyên tố phải
  đúng công thức `p = 2^2048 − 2^1984 − 1 + 2^64 × (⌊2^1918 × π⌋ + 124476)`, phải là **số nguyên
  tố**, và `(p−1)/2` **cũng nguyên tố** (nhóm an toàn ⇒ không có nhóm con nhỏ). π được **tính**
  bằng công thức Machin tới 650 chữ số — *lần đầu tôi dán ~200 chữ số π và phép kiểm báo sai:
  hằng số thì đúng, bộ kiểm mới sai. Hằng số mật mã là chỗ dễ chép sai mà khó thấy nhất.*
- **Kiểm:** `kiem_dh_nhom.py` (mới) + `kiem_tu_xa.py` 22→**25** (thêm: chữ ký DH hợp lệ · mỗi
  phiên một khoá tạm khác · khoá phiên hai lần khác nhau) → `kiem_toan_bo.py` **70/70**.
- **Còn lại (trung thực):** chưa qua thẩm định mật mã; chưa đổi khoá giữa phiên (rekey); chưa
  chống dò mật khẩu bằng cách chậm dần; vẫn kẹp 127.0.0.1.

---

## v0.21.0 — ★★★★★ MÃ HOÁ ĐƯỜNG TRUYỀN: ChaCha20 + HMAC-SHA256 THUẦN GIAO (2026-07-31)

Phiên từ xa của v0.20.0 đi **trần**; nay nó **kín**. Và cả ba mảnh mật mã đều viết bằng GIAO —
dựng được là nhờ những thứ đã có: **phép bit (A1)**, **gán chỉ mục (A2)**, **`mũ_mod` (I1)**,
**SHA-256 (C1)**.

- **★★★ `lib_chacha20.giao` — ChaCha20 (RFC 8439) thuần GIAO.** Chỉ cộng-32-bit, xor, quay trái;
  **không phép nhân, không bảng tra** ⇒ không có kênh-phụ theo thời gian như AES bảng-tra.
  **Khớp TỪNG BYTE với vector chính thức của RFC** (§2.3.2 khối và §2.4.2 mã câu) — bài kiểm lấy
  đúng vector của chuẩn, không tự nghĩ ra phép thử.
- **★★★ `lib_kenh.giao` — kênh kín:** HMAC-SHA256 (khớp `hmac` của Python), khung
  `<đếm>:<hex bản mã>:<hex thẻ>` theo lối **mã-rồi-xác-thực**, MAC phủ **cả số đếm** nên chống
  được sửa đổi *và* phát lại. **Mỗi chiều một khoá riêng** ⇒ không bao giờ dùng lại cặp
  (khoá, nonce). Khoá phiên 96 byte do khách sinh, chuyển bằng **RSA-2048 PKCS#1 v1.5**.
- **★★ Khoá máy + vân tay (TOFU).** Máy chủ giữ khoá riêng ở `/hệ/khoá_máy` (**600**, người
  thường không đọc nổi — có test), công bố `/hệ/khoá_máy.công` (644). Chào đầu tiên là
  `GIAO-KÍN <vân tay>`; khách **đối chiếu vân tay** rồi mới gửi khoá phiên — sai vân tay thì
  **dừng**, như `known_hosts` của SSH. *(Khác kho phần mềm: khoá riêng của KHO không bao giờ vào
  máy, còn khoá riêng của MÁY thì máy phải giữ — đúng vai.)*
- **`utf8_giải`** (cặp đôi của `utf8_mã`) — thiếu nó thì lệnh tiếng Việt qua kênh bị vỡ chữ.
- **★★★ Phép thử quyết định — SOI THẲNG BYTE TRÊN DÂY:** gửi câu `nói "SEN-VANG-BI-MAT-9137"`,
  rồi khẳng định **chuỗi bí mật KHÔNG hề xuất hiện trong byte truyền đi**, mà **giải ra thì đúng
  nguyên văn**. Thêm: **sửa một ký tự** trên dây → *THẺ XÁC THỰC SAI*, máy chủ **không giải bừa**;
  **phát lại** khung cũ → bị bỏ vì số đếm không tiến.
- **TRUNG THỰC (ghi ở đầu `lib_kenh.giao`):** **chưa có bí mật chuyển tiếp** — lộ khoá riêng của
  máy là giải được mọi phiên đã ghi; SSH thật dùng Diffie-Hellman cho việc này, mà GIAO **đã có
  `mũ_mod`** nên làm được, chỉ là chưa làm. Bản hiện thực **chưa qua thẩm định mật mã**, chạy ở
  đường thông dịch (chậm), không chống kênh-phụ theo thời gian.
- **Kiểm:** `kiem_chacha20.giao` (mới, vector RFC) + `kiem_tu_xa.py` 15→**22** (thêm nhóm [3]
  soi byte trên dây) → `kiem_toan_bo.py` **69/69**.

---

## v0.20.0 — ★★★★★ MẠNG RA HOST (B1') + ĐĂNG NHẬP TỪ XA (C4) (2026-07-31)

Hai mục khép cùng lúc vì mục sau đứng trên mục trước.

- **★★★ B1' — NĂNG LỰC `mạng_host`** (`giao.py`): ổ cắm **TCP thật** ra máy chủ —
  `ổ_nghe` · `ổ_nhận` · `ổ_nối` · `ổ_gửi` · `ổ_đọc` · `ổ_đóng`. Tất cả **KHÔNG CHẶN**
  (non-blocking): nhân GIAO là vòng lặp hợp tác, một lời gọi đứng chờ là cả hệ đứng theo;
  chưa có gì → **ẩn** ("chưa biết"), không phải lỗi.
  - **Sandbox bẩm sinh**: chưa cấp thì mấy cái tên ấy **không tồn tại** (không phải "bị từ chối").
  - **Kẹp phạm vi**: cờ `--cho-mạng <cổng>` chỉ mở **đúng cổng ấy** và **chỉ 127.0.0.1**;
    cổng/máy ngoài danh sách → từ chối thẳng.
  - **★ Một API, hai đường đi:** `GH_NGHE(cổng, quyền, "ngoài")` mở ổ TCP thật, còn
    `nhận_gói`/`gửi_gói` thì **y hệt mạng trong-máy** ⇒ chương trình viết một lần chạy được cả
    hai đường, và **quyền vẫn kiểm ở đúng chỗ cũ** — không có tầng bảo mật riêng cho mạng ngoài.
- **★★★ C4 — ĐĂNG NHẬP TỪ XA** (`lib_tu_xa.giao` + `chay_hdh_xa.py` + `khach_xa.py` + `bat_xa.bat`).
  Đây là chỗ ba thứ dựng trước gặp nhau chứ không phải tính năng đứng riêng: **B1'** cho ổ cắm,
  **C1** cho sổ băm `$g2$`, **C2/C3** cho uid/nhóm. Chứng minh được:
  - xác thực bằng **ĐÚNG `/hệ/mật_khẩu`**, không có sổ riêng cho người từ xa; sai thì **không nói
    rõ sai tên hay sai mật khẩu**;
  - phiên chạy dưới **ĐÚNG uid** ⇒ `an` từ xa vẫn *cấm đọc* `/hệ/mật_khẩu`, `gốc` từ xa thì đọc
    được và thấy **băm**;
  - **cổng bất-khả-hồi vẫn giữ việc lại** (`xoá` từ xa → CẦN PHÊ DUYỆT), **audit ghi cả việc làm
    từ xa** — không có đường tắt nào không bị ghi.
  - Khác `sshd` hai chỗ: `sshd` chạy dưới **root suốt phiên** rồi mới hạ quyền, ở đây chỉ **mượn
    tiến trình gốc đúng lúc đọc sổ bóng** (như `/bin/login`); và mọi lệnh đi qua **đúng vỏ, đúng
    tầng gọi-hệ**.
- **⚠ TRUNG THỰC: KHÔNG mã hoá đường truyền** — đây **không phải SSH**. Năng lực kẹp sẵn
  127.0.0.1 nên dùng trong cùng một máy thì được; đem ra mạng thật thì mật khẩu đi trần.
  Muốn thật thì cần TLS, mà GIAO chưa có. Ghi rõ ở đầu `lib_tu_xa.giao` và trong CÒN_THIẾU.
- **Bẫy đã vấp (lại là `sáng`/`tối` LÀ CHUỖI):** `ổ_đọc` ban đầu trả thẳng chuỗi dữ liệu và trả
  `tối` khi đầu kia đóng ⇒ kết nối đã chết bị coi là **gói dữ liệu chứa chữ "tối"**, chiếm chỗ
  mãi mãi và **bỏ đói khách mới** — máy chủ im lặng sau khi khách đầu tiên ngắt. Nay `ổ_đọc` trả
  **`[sáng, dữ_liệu]`** cho dữ liệu, `tối` cho đóng, `ẩn` cho chưa-có-gì: hết nhập nhằng.
- **Kiểm:** `kiem_tu_xa.py` (mới) **15/15** — gồm cả ca *chưa cấp năng lực thì tên không tồn tại*
  và *cổng ngoài phạm vi bị từ chối*. Vào `kiem_toan_bo.py` → **68/68**.

---

## v0.19.0 — ★★★★★ CHỮ KÝ KHOÁ-CÔNG-KHAI: RSA-2048 kiểm THUẦN GIAO (I1) (2026-07-31)

Mục quan trọng nhất còn lại của kho đã xong. Trước bản này kho chỉ có **băm** ⇒ chống **sửa đổi**
được, nhưng **kho giả mạo** thì không: ai dựng được một kho khác rồi **tự băm lại mọi gói** là qua
tuốt. Chữ ký vá đúng chỗ ấy.

- **★★★ `lib_so_lon.giao`** — mảnh còn thiếu của số học: **`mũ_mod`** (bình-phương-và-nhân, đọc
  bit số mũ nhờ phép bit của A1) + `hex_sang_số` / `số_sang_hex`. GIAO vốn tính số nguyên chính
  xác mọi cỡ nên chỉ thiếu đúng phép này là dựng được mật mã khoá-công-khai.
- **★★★ `lib_chu_ky.giao`** — **RSA PKCS#1 v1.5 + SHA-256, kiểm chữ ký hoàn toàn bằng GIAO**.
  Giải chữ ký bằng khoá công rồi so **từng byte** với khuôn EM dựng lại. Với mũ 65537 (17 bit)
  chỉ 17 vòng ⇒ **kiểm một chữ ký RSA-2048 mất ~0,3 giây**. Thêm `vân_tay_khoá` (16 hex đầu của
  SHA-256 khoá) để **người đối chiếu bằng mắt**, như fingerprint của GPG.
- **★ Phân vai đúng như đời thật:** **KÝ** là việc của người giữ kho, làm **bên ngoài**
  (`lam_khoa.py`, zero-dependency: `hashlib` + `secrets`, tự sinh nguyên tố Miller-Rabin);
  **khoá riêng KHÔNG bao giờ vào máy**. **KIỂM** là việc của HĐH, chỉ cần khoá công — máy người
  dùng không giữ bí mật nào, y như máy bạn không có khoá riêng của Debian/Kali.
- **★★ NEO TIN CẬY RIÊNG TỪNG NGUỒN** (`/hệ/kho/nguồn`: `tên|mục_lục|chữ_ký|khoá_công`) — đúng ý
  `Signed-By:` của apt/Kali: kho khác thì khoá khác, **không có rổ khoá dùng chung**.
  Lệnh **`gói tin`** cho biết đang tin nguồn nào, neo ở đâu, vân tay khoá nào.
- **Chữ ký là BẮT BUỘC** khi đã khai nguồn: sai chữ ký thì **chặn cả `cài` lẫn `nâng_cấp`**.
  Kho **cục bộ** (chưa khai nguồn) vẫn cho qua nhưng **nói rõ đang tin theo QUYỀN TỆP, không phải
  chữ ký** — mục lục là tệp 644 chủ gốc nên người thường không sửa nổi. (apt cũng có ngả này:
  `[trusted=yes]`; khác ở chỗ ta **nói ra**.)
- **Phép thử quyết định** (`kiem_chu_ky.giao` + `lam_dulieu_chu_ky.py` sinh **hai** cặp khoá):
  dựng hẳn một **KHO GIẢ MẠO** có mục lục hợp lệ, **băm gói đúng y như thật**, chỉ khác chỗ ký
  bằng khoá của chính nó → **bị từ chối**. Đây đúng là ca mà băm không cứu nổi. Và khi đổi luôn
  khoá neo sang khoá kẻ giả thì mới qua — **vân tay đổi**, người soi bằng mắt là thấy: an toàn
  nằm ở **neo tin cậy**, không nằm ở chỗ "có chữ ký hay không".
- `lam_kho.py` nay **ký mục lục** khi dựng kho mẫu; `--kiểm` đối chiếu cả **băm lẫn chữ ký** và
  được nối vào `kiem_toan_bo.py`.
- **TRUNG THỰC:** sinh nguyên tố trong `lam_khoa.py` là bản gọn cho dự án, **chưa qua thẩm định
  mật mã** — đừng đem giữ bí mật thật. Thứ nó chứng minh là **ngữ nghĩa**: chỉ ai giữ khoá riêng
  mới ký nổi mục lục, và HĐH kiểm được điều đó **bằng chính ngôn ngữ của mình**.
- **Kiểm:** `kiem_chu_ky.giao` (mới) + mục [32] → `kiem_hdh_giao.py` 314→**323**;
  `kiem_toan_bo.py` **67/67**.

---

## v0.18.1 — VÁ BÀN LÀM VIỆC: cửa sổ chồng khít nhau nên "bấm không được" (2026-07-31)

Người dùng báo: *"tệp tôi không ấn được, dòng lệnh đang không dùng được, tiến trình không thao
tác được"*. Soi ra **không phải ba ứng dụng hỏng** — cả ba vẫn dựng đủ dữ liệu; lỗi là ở **cách
xếp cửa sổ**.

- **★ Gốc lỗi:** cửa sổ mới xếp bậc thang chỉ **26px** và luôn bắt đầu ở góc trái trên ⇒ mở ba
  ứng dụng là chúng **phủ kín nhau**, trong khi 80% màn hình bỏ trống. Bấm cửa sổ dưới thì nó
  *có* nổi lên thật, nhưng vẫn bị che nên trông y như bấm không ăn.
  **Sửa:** cửa sổ mới **trải ra theo cột** tính từ bề rộng thật của vùng làm việc, và luôn được
  kẹp trong màn hình.
- **★ Nút ⊞ "Xếp gọn"** trên thanh trên: một cú bấm là mọi cửa sổ đang mở dàn thành **lưới kín
  màn hình**, hết chồng nhau.
- **★ Đồng hồ nằm ĐÈ LÊN cửa sổ** (z-index 100 so với 10–13 của cửa sổ) ⇒ cửa sổ nào trôi vào
  góc phải trên thì **bị đồng hồ nuốt mất cú bấm**. Nay đồng hồ về **z-index 1** — nó là trang trí,
  phải nằm dưới.
- **Cửa sổ tự làm mới cho tử tế** (`nhịpLại`): nội dung **không đổi thì không vẽ lại** (vẽ lại là
  mất chỗ đang bôi đen, mất cả cú bấm dở); cửa sổ **thu nhỏ hoặc tab bị ẩn thì NGHỈ** — trước đây
  mỗi lần làm mới đều bắt nhân quay vòng, bốn cửa sổ mở là nhân chạy không ngừng. Giãn nhịp:
  Tiến trình 2s→4s, Mạng/Nhật ký/Bộ nhớ 3s→6s.
- Kiểm tay trong trình duyệt: gõ `liệt /tạm` ở Dòng lệnh ra kết quả · gõ đúp thư mục ở Tệp đi vào
  được · nút 🗑 bỏ tệp vào thùng rác · nút ⊞ dàn lưới. `kiem_de.py` 30/30.

---

## v0.18.0 — ★★★★ KHO PHẦN MỀM: học apt/Kali, vá 5 chỗ yếu của nó (2026-07-31)

**Quan sát máy thật trước khi làm:** Kali 2026.2 chạy trên WSL của chính máy này — đọc
`sources.list.d/*.sources`, `InRelease`, `dpkg -s`, `apt-cache show kali-linux-headless`.

**Đáng học (đã lấy):** nguồn kho khai **trust anchor riêng** (`Signed-By:` trỏ đúng một keyring,
không dùng chung một rổ khoá) · **mục lục mang băm của mọi tệp** ⇒ tin một chỗ là tin cả kho ·
**siêu-gói** gom công cụ theo mục đích (`kali-linux-headless` chỉ toàn `Depends:` ~200 gói) ·
chạy **không phải root** (uid 1000, nhóm sudo).

**Năm chỗ apt yếu — `lib_kho.giao` làm khác:**
1. **apt cho gói chạy script `postinst` VỚI QUYỀN ROOT** ⇒ cài gói = cho chạy mã tuỳ ý ở quyền cao
   nhất. Ở GIAO gói chỉ là **dữ liệu** (thân lệnh); cài = chép tệp, **không có script chạy lúc cài**.
2. **apt không có hoàn tác** (rolling vỡ thì tự cứu). Ở đây gỡ/nâng-cấp đẩy bản cũ vào
   `/thùng_rác` ⇒ **`gói lùi`** đưa thân lệnh *và* phiên trong sổ về đúng bản trước.
3. **apt đứt giữa chừng để lại dpkg hỏng** (`--configure -a`). Ở đây cài là **giao dịch nguyên
   khối**: soạn kế hoạch → **kiểm băm SHA-256 toàn bộ** → rồi mới ghi. Test tráo ruột một gói:
   từ chối cả giao dịch, **không ghi gì**.
4. **apt in bức tường tên gói mà không nói vì sao.** Ở đây mỗi gói kéo theo đều kèm
   *"(cần vì 'X' cần nó)"*.
5. **apt tin cậy được-ăn-cả**: kho đã ký thì gói muốn làm gì cũng được. Ở đây mỗi gói **tự khai
   NĂNG LỰC**; năng lực nhạy cảm (`mạng`/`gốc`/`đĩa`/`xoá`) thì người phải **đồng ý tường minh**.
   Đây là chỗ GIAO hơn hẳn — cả hệ vốn đã capability, kho gói chỉ nối tiếp cho nhất quán.
- **Thêm một chỗ nữa apt bắt buộc mà GIAO không:** **người thường cài được mà KHÔNG cần nâng
  quyền** — gói vào `/nhà/<tên>/lệnh` (vốn đã trong `$PATH`), sổ đã-cài cũng riêng từng người.
  Gốc-quyền thì cài vào `/lệnh` cho cả máy.
- Bảo vệ phụ thuộc khi gỡ (*"không gỡ được: trên đang cần 'nền'"*). Mục lục kho có **bộ kiểm H6**
  (băm phải đúng 64 hex, không trùng tên) nên mục lục hỏng bị từ chối ngay lúc ghi.
- **Lệnh vỏ `gói`**: `gói` · `gói kho` · `gói xem <tên>` · `gói cài <tên> [đồng-ý]` · `gói gỡ` ·
  `gói nâng_cấp` · `gói lùi`. **Ứng dụng "Kho phần mềm"** trên bàn làm việc: gói theo nhóm, huy
  hiệu ⚠ năng lực, hỏi trước khi cấp.
- **`lam_kho.py`** dựng mục lục mẫu (băm SHA-256 thật) + `--kiểm` đối chiếu băm với thân gói.
  Kho mẫu 6 gói, có một **siêu-gói** `bộ_hệ_thống` (học `kali-linux-headless`).
- **TRUNG THỰC:** mục lục hiện chỉ có **băm** (toàn vẹn), **chưa có chữ ký khoá-công-khai**
  (xác thực) — GIAO chưa có số học mũ-modulo. Chống sửa đổi thì được, chống **kho giả mạo** thì
  chưa. Ghi ở đầu `lib_kho.giao` và trong CÒN_THIẾU.
- **Ba lỗi quyền đã vấp khi dựng** (đều cùng một gốc: người thường không ghi được vào `/hệ`,
  `/lệnh`): cài báo ✓ mà không ghi được gì · sổ đã-cài không lưu · sổ lùi không lưu. Đã vá bằng
  đường-riêng-từng-người **và** kiểm giá trị trả về của mọi lần ghi — đúng loại lỗi im lặng ta chê apt.
- **Kiểm:** `kiem_kho.giao` (mới) + mục [31] → `kiem_hdh_giao.py` 302→**314**; `kiem_de.py` 30/30;
  `kiem_toan_bo.py` **66/66**.

---

## v0.17.0 — ★★★★ BỔ KHUYẾT LINUX (khép nhóm H): TÊN TỆP · CẤU HÌNH KIỂM-TRƯỚC · GHI CÓ ĐIỀU KIỆN (2026-07-31)

- **★★ H5 — TÊN TỆP không còn là bãi mìn.** Linux chỉ cấm **đúng hai thứ** trong tên tệp: byte 0
  và `/`. Mọi thứ khác lọt: tệp tên `-rf` biến thành **cờ** khi vỏ nối chuỗi rồi tách lại
  (`rm *` xoá nhầm); xuống dòng/tab phá mọi kịch bản kiểu `ls | while read`; ký tự điều khiển và
  ANSI escape vẽ bậy ra terminal, giả được cả dòng chữ khác; tên toàn khoảng trắng nhìn y hệt tên
  thật. GIAO chặn **từ lúc TẠO, ở tầng hệ-tệp** (`lý_do_tên_xấu` trong `lib_tệp_hệ.giao`, dùng
  trong `tth_tạo_tệp`/`tth_tạo_thư`/`tth_tạo_ống`) nên **mọi đường vào đều bị chặn như nhau**, và
  báo **rõ hỏng ở đâu**. Còn `-rf` thì **vô hại theo kiến tạo**: vỏ GIAO truyền **danh sách đối**,
  không nối rồi tách như `sh` — test tạo hẳn tệp tên `-rf` rồi `bỏ` nó bình thường.
- **★★★ H6 — CẤU HÌNH có kiểm-tra-trước, LUÔN BẬT** (`lib_cau_hinh.giao` mới). Linux: `/etc` mỗi
  tệp một cú pháp và **không ai kiểm trước** — sai một dấu trong `sudoers` là **mất luôn đường lên
  root** (nên mới phải đẻ ra `visudo`, mà dùng `visudo` là chuyện **tự giác**); sai `fstab` thì
  **máy không boot nổi** và bạn chỉ biết sau khi khởi động lại. GIAO đặt bộ kiểm **ở tầng gọi-hệ**:
  mọi cửa ghi (`tạo` · `ghi` · **`thêm` >>** · `ghi_nếu`) đều qua nó, **không cửa nào lách**.
  Sai thì **TỪ CHỐI ngay, nói rõ DÒNG nào và vì sao, tệp cũ CÒN NGUYÊN**. Bốn bộ kiểm: sổ người
  dùng (uid phải là số · **không trùng uid** vì chung uid là chung quyền · nhà phải tuyệt đối ·
  **phải còn ít nhất một uid 0**), sổ nhóm, sổ sudo (**để trống phần lệnh là vô nghĩa**), sổ bóng
  (**chặn mật khẩu thô lọt vào**). Lệnh vỏ `kiểm_cấu_hình <đường>`.
- **★★ H7 — TOCTOU + mất-cập-nhật: `ghi_nếu`** (gọi-hệ **40**, compare-and-set trên TỆP).
  Khe TOCTOU cổ điển của Linux (`access`→`open`, `stat`→`unlink`) vốn không có ở GIAO vì gọi-hệ
  **kiểm-và-làm trong MỘT lượt**. Còn lại một loại đua nữa **Linux không có câu trả lời**: hai
  tiến trình cùng đọc một tệp, cùng sửa, kẻ ghi sau **đè mất việc kẻ trước, im lặng**. `ghi_nếu`
  chỉ ghi khi nội dung **vẫn đúng như lúc mình đọc**; lệch thì từ chối kèm lời nhắc đọc lại.
  Và nó **vẫn qua bộ kiểm H6** — hai lớp chồng đúng thứ tự.
- **Bẫy GIAO đã gặp và ghi lại:** `sáng`/`tối` **CHÍNH LÀ CHUỖI**, nên `loại(x) == "chuỗi"` bắt
  nhầm cả giá trị thành công — báo lỗi bằng lời phải gói trong **danh sách** `[tối, lý_do]`.
  Và `lib_tệp_hệ.giao` **không nhập** `lib_chuoi.giao` ⇒ phép kiểm tên chỉ dùng builtin `mã`/`dài`.
- **Bộ kiểm H6 bắt lỗi ngay trong dữ liệu mẫu CŨ của chính dự án** (sổ người dùng thiếu cột nhà,
  băm giả `$b1ke9`, `gốc:x:0`) — đã sửa 8 tệp cho hợp lệ. Đó là bằng chứng bộ kiểm làm đúng việc.
- **Kiểm:** `kiem_h5_h6_h7.giao` (mới) + mục [30] → `kiem_hdh_giao.py` 285→**302**;
  `kiem_de.py` 30/30; `kiem_toan_bo.py` **66/66**.

---

## v0.16.0 — ★★★★ BỔ KHUYẾT LINUX (tiếp): DỪNG ÊM CÓ HẠN (H3) + HẾT BỘ NHỚ CHỌN THEO σ (H4) (2026-07-31)

- **★★★ H3 — XIN THOÁT CÓ HẠN, dọn ở ĐIỂM AN TOÀN** (gọi-hệ **38 `xin_thoát`**, lệnh vỏ
  `xin_thoát <tid> [hạn]` · `dọn_dẹp`). Linux hỏng **hai đường**: `SIGKILL` KHÔNG chạy được
  handler ⇒ cắt ngang giữa lúc đang ghi (dữ liệu dở dang, khoá treo lại); còn `SIGTERM` thì
  handler chạy **bất thình lình giữa bất kỳ dòng nào** (async) nên gần như không viết đúng được
  — tập hàm async-signal-safe rất hẹp — và cái hạn "chờ rồi mới KILL" là việc của **userspace**
  (systemd), **nhân không biết gì**. GIAO làm ở nhân:
  - tiến trình khai trước việc phải dọn (`đăng_ký_dọn`); khi bị xin thoát nó chuyển sang **DỌN**;
  - **việc dọn chạy ở CHÍNH LÁT CPU của nó** ⇒ không chen ngang bất cứ đâu, nên không có chuyện
    "async-unsafe"; mỗi lát trừ một hạn;
  - dọn xong → **thoát êm**; **quá hạn → nhân mới cắt, và ghi rõ là đã cắt vì quá hạn** (không
    im lặng — `dọn_dẹp` xem được toàn bộ diễn biến);
  - dừng hẳn vẫn là bất-khả-hồi ⇒ **vẫn qua cổng duyệt**; tiến-trình 1 thì chặn thẳng.
- **★★★ H4 — HẾT BỘ NHỚ: CHỌN THEO σ RỒI HỎI** (gọi-hệ **39 `cấp_ô`**, lệnh vỏ `bộ_nhớ`).
  Linux hỏng: OOM-killer chấm điểm bằng heuristic thô (chủ yếu *đang dùng bao nhiêu* +
  `oom_score_adj` do người khai) rồi **SIGKILL im lặng** — hay bắn nhầm thứ quan trọng, bắn ngang
  nên không kịp dọn, người dùng chỉ thấy tiến trình "tự nhiên biến mất". GIAO:
  - chọn nạn nhân theo **σ — độ hữu ích nhân TỰ HỌC** (đúng con số lịch γ đang dùng), hoà thì
    xét kẻ ngốn nhiều hơn; **không bao giờ đụng tiến-trình 1**;
  - **nêu lý do bằng chữ** rồi **HỎI NGƯỜI**: nhân đặt sẵn *đúng lời gọi* vào cổng duyệt, người gõ
    `duyệt` là chính lời gọi ấy chạy — không phải nhân âm thầm làm rồi báo sau;
  - đồng ý thì dừng bằng **`xin_thoát` của H3** (êm, có dọn) chứ không cắt ngang;
  - kẻ σ cao dù cũng ngốn nhiều **vẫn được yên**; chết là **tự trả** bộ nhớ (không cần hàm giải
    phóng riêng — tổng chỉ tính tiến trình còn sống).
- **Bàn làm việc:** thêm ứng dụng **Bộ nhớ** (bảng σ + ô nhớ + nhật ký dọn dẹp) — thấy trước khi
  máy phải hỏi ai dừng.
- **Kiểm:** `kiem_dung_em.giao` (mới) + mục [29] → `kiem_hdh_giao.py` 275→**285**;
  `kiem_de.py` 30/30; `kiem_toan_bo.py` **66/66**.

---

## v0.15.0 — ★★★★ BỔ KHUYẾT LINUX: xoá LẤY LẠI ĐƯỢC + `vì_sao` · vá giao diện (2026-07-31)

### Hai chỗ GIAO làm hơn Linux

- **★★★ #1 — THÙNG RÁC + HOÀN TÁC Ở TẦNG GỌI-HỆ.** Ở Linux `rm` là **vĩnh viễn**; thùng rác chỉ
  là **quy ước của môi trường đồ hoạ** (freedesktop.org) nên chỉ trình quản lý tệp tôn trọng —
  gõ `rm` ở terminal là mất sạch, và không chương trình nào khác được hưởng. GIAO đặt thùng rác
  **trong tầng gọi-hệ**: gọi-hệ **34 `bỏ`** · **35 `hoàn_tác`** · **36 `dọn_rác`**, thư mục
  `/thùng_rác`, lệnh vỏ `bỏ` · `hoàn_tác` · `thùng` · `dọn_rác`. Hệ quả:
  - **mọi** chương trình đều được che, cùng một tầng quyền, cùng ghi audit;
  - `hoàn_tác` trả về **đúng chỗ cũ, đúng nội dung**, lấy thứ **vừa bỏ gần nhất** (kiểu Ctrl-Z);
  - bỏ hai tệp **trùng tên** không đè nhau (tên trong thùng là duy nhất);
  - **quyền vẫn chặn**: phải GHI được thư-mục cha mới bỏ được; **không lấy lại được thứ người
    khác bỏ**; chỗ về mất/bị chiếm thì từ chối chứ không đè.
  - **★ Cổng phê duyệt DỜI ĐÚNG CHỖ:** `bỏ` **không** cần phê duyệt (vì hoàn tác được — đúng
    học thuyết: cổng chỉ chặn cái không lấy lại được), còn **`dọn_rác`** mới là việc bất-khả-hồi
    nên **nó** đứng sau cổng. (`xoá` cũ vẫn là unlink thật và vẫn qua cổng — ai muốn dứt khoát.)
- **★★ #2 — `vì_sao`: giải thích ĐÚNG NẤC HỎNG** (gọi-hệ **37**, lệnh vỏ `vì_sao <đường> [đọc|ghi|chạy]`).
  Linux chỉ ném `EACCES` — "Permission denied", không nói hỏng ở đâu, thiếu bit nào, phải làm gì;
  người dùng đoán mò rồi `chmod 777` cho xong, và đó chính là cách quyền Unix bị phá trên thực địa.
  `vì_sao` nói: **thư-mục nào trên đường** chặn (thiếu bit `x` — chỗ hay tắc nhất mà không ai biết),
  mình đứng **vai nào** (chủ/nhóm/khác), vai ấy **có bit gì, thiếu bit gì**, và **làm gì thì qua**.
  Được phép cũng nói rõ **nhờ vai nào**. Và phân biệt **ẩn** (không có) với **tối** (bị cấm) —
  đúng chỗ `errno` của Linux trộn hai chuyện làm một.
- **Bàn làm việc:** thêm ứng dụng **Thùng rác** (hoàn tác/dọn hẳn bằng chuột); ứng dụng **Tệp**
  thêm nút 🗑 (bỏ) và **?** (vì_sao) trên từng hàng — vẫn đi qua đúng gọi-hệ.

### Vá giao diện (từ phản hồi khi dùng thật)

- **★ TRỢ LÝ "không trả lời" — thật ra là lỗi CON TRỎ GÕ:** bấm vào cửa sổ không trao con trỏ cho
  ô nhập của **chính cửa sổ đó**, nên chữ gõ lặng lẽ rơi sang cửa sổ khác (thường là Dòng lệnh) —
  trông y như trợ lý chết. Nay: **bấm bất kỳ đâu trong cửa sổ → ô của cửa sổ ấy nhận con trỏ**
  (trừ khi đang bôi đen chữ), cửa sổ nào nổi lên cũng tự nhận con trỏ.
- **Ô nhập dời xuống CHÂN cửa sổ** (khung cố định như hộp chat, có viền rõ) thay vì trôi trong
  vùng cuộn; Trợ lý có thêm nút **Nhờ** và báo **"⋯ đang nghĩ"** trong lúc chờ.
- **★ BA NÚT CỬA SỔ đúng nếp macOS** — trước đây chỉ nút đỏ chạy:
  🔴 **đỏ = đóng** · 🟡 **vàng = thu nhỏ** (về dock, biểu tượng mờ đi, bấm dock hiện lại **đúng
  chỗ cũ**) · 🟢 **xanh = phóng to / co lại** (nhớ và trả về **đúng kích thước cũ**; gõ đúp thanh
  tiêu đề cũng được). Vùng bấm nới lên 22px (chấm màu vẫn 13px) cho dễ trúng.
- **Bẫy đã gặp:** `/lệnh/rác` **đã có sẵn** từ trước (một kịch bản mẫu liệt kê `/tạm`) nên nó đè
  lên lệnh mới ⇒ lệnh liệt kê thùng rác đặt tên là **`thùng`**. Và trong GIAO, biểu thức **không
  nối qua nhiều dòng** được (xuống dòng là hết câu lệnh) — phải gom chuỗi vào biến trung gian.
- **Kiểm:** `kiem_bo_khuyet_linux.giao` (mới) + mục [28] → `kiem_hdh_giao.py` 258→**275**;
  `kiem_de.py` **30/30**; `kiem_toan_bo.py` **66/66**.

---

## v0.14.0 — ★★★★ BÀN LÀM VIỆC: HĐH-GIAO có GIAO DIỆN ĐỒ HOẠ (2026-07-30)

Từ bản này HĐH-GIAO không chỉ có dòng lệnh: có **bàn làm việc** (desktop) đầy đủ — thanh trên,
menu ứng dụng theo nhóm, dock, cửa sổ kéo/co được, widget đồng hồ.

- **`giao_de.py`** (mới) — máy chủ khung hình, **zero-dependency** (chỉ `http.server` của Python).
  Giữ MỘT máy GIAO; mọi lời gọi đi qua một cái ổ khoá (nhân là một trạng thái, không đa luồng).
  Nhân **boot sẵn lúc máy chủ lên** (không để người dùng bấm Đăng nhập rồi ngồi chờ).
- **`de/index.html` · `de/de.css` · `de/de.js`** (mới) — vỏ bàn làm việc, **tự chứa hoàn toàn**:
  không CDN, không phông ngoài, không ảnh ngoài (hình nền + biểu tượng đều là CSS/SVG).
- **★★★ Đây KHÔNG phải ảnh chụp giao diện — nó chạy trên NHÂN THẬT:** mọi thao tác đều đi qua
  **đúng tầng gọi-hệ** với **đúng tid + uid** của phiên đăng nhập. Hệ quả kiểm chứng được:
  - đăng nhập bằng chính sổ `/hệ/mật_khẩu` (`$g2$` SHA-256), sai thì **không nói rõ sai tên hay
    sai mật khẩu**;
  - **KHÔNG có cửa hậu**: `an` bấm chuột vào `/hệ/mật_khẩu` vẫn *cấm đọc* y như gõ phím;
  - **cổng BẤT-KHẢ-HỒI thành HỘP THOẠI**: `xoá` bị nhân giữ lại → bàn làm việc bật hộp
    *"Việc này KHÔNG hoàn tác được"* với đúng lời gọi đang chờ, bấm **Phê duyệt** mới chạy.
    Đây là chỗ CDFL lộ ra rõ nhất trên màn hình.
- **8 ứng dụng** — Dòng lệnh (vỏ thật, có lịch sử ↑↓) · Tệp (liệt+soi qua `GH_LIỆT`/`GH_SOI`,
  đi thư mục, hiện quyền/chủ/cỡ) · Tiến trình · Trợ lý (γ minh bạch) · Người & Nhóm (C2/C3) ·
  Mạng (`/tb/mạng`, B1) · Nhật ký audit · Soi hệ.
- **An toàn:** chỉ nghe trên **127.0.0.1** + **KHOÁ PHIÊN** ngẫu nhiên trong đường dẫn — thiếu
  hoặc sai khoá thì mọi lời gọi bị **403** (kẻo một trang web đang mở gọi lén vào máy bạn).
- **`bat_ban.bat`** (mới) — bật bàn làm việc một cú gõ đúp (`bat_may.bat` vẫn là bản dòng lệnh).
- **Vá phát hiện khi dựng giao diện:** `/tb/tim` (thiết bị trái tim) **chưa hề được gắn lúc boot**
  — chỉ có trong bản trình diễn; nay `hdh_nền.giao` gắn thật, `xem /tb/tim` chạy ở mọi phiên.
- **Kiểm:** `kiem_de.py` (mới) **30/30** — chứng minh đúng 4 điều trên bằng lời gọi HTTP thật,
  gồm cả ca 403 khi sai khoá. Vào `kiem_toan_bo.py` → **66/66**.

---

## v0.13.0 — ★★★ NHÓM NGƯỜI DÙNG (C2) + SUDO CÓ SỔ QUYỀN (C3) (2026-07-30)

- **★★ C2 — NHÓM NGƯỜI DÙNG** (~`/etc/group`):
  - `/hệ/nhóm` (644): `tên_nhóm:gid:tv1,tv2`. Tư cách nhóm được **chốt lúc đăng nhập**
    (`đồng_bộ_nhóm` đổ vào bảng credential `TTH_NHÓM` của nhân — `được_phép` chỉ TRA, không đọc
    tệp, tránh vòng "muốn đọc tệp phải kiểm quyền, muốn kiểm quyền phải đọc tệp") — như Linux.
  - `được_phép` xét đủ **chủ > nhóm > khác** đúng thứ tự Unix (là chủ thì CHỈ xét bit chủ —
    chủ 040 tự khoá mình trong khi người cùng nhóm vẫn đọc được; có test chứng minh).
  - Gọi-hệ **33 `GH_ĐỔI_NHÓM`** (chgrp) + lệnh vỏ `đổi_nhóm`, luật Linux: chủ tệp chỉ đổi sang
    nhóm MÌNH THUỘC, gốc tuỳ ý. Lệnh vỏ **`nhóm`** (~`getent group`). Nút cũ không có `gid`
    → coi là nhóm 0 (ảnh chụp cũ nạp lại vẫn chạy).
  - **Đúng đề bài CÒN_THIẾU:** hai người cùng nhóm đọc được tệp **640** của nhau, người ngoài
    nhóm thì không (`kiem_nhom_sudo.giao`).
- **★★ C3 — SUDO VỚI SỔ QUYỀN RIÊNG** (~`/etc/sudoers`):
  - `/hệ/sudo` (440, chỉ gốc đọc): `tên: lệnh1 lệnh2` hoặc `tên: *`. `sudo_được` ba-trị:
    được=**sáng** · có-trong-sổ-nhưng-lệnh-không-cấp=**tối** · không-có-trong-sổ=**ẩn**.
  - Lệnh `sudo <lệnh>` trong phiên tương tác: hỏi mật khẩu **CỦA CHÍNH MÌNH** (khác `thành`/su
    hỏi mật khẩu người kia — sudo hỏi *"anh là ai"*), tra sổ, rồi cấp danh tính gốc cho
    **ĐÚNG MỘT lệnh** (uid trả lại ngay, kể cả khi lệnh lỗi).
  - **`sudo` KHÔNG thay `duyệt`** — đúng ghi chú của hồ sơ: lệnh bất-khả-hồi chạy qua sudo
    **vẫn bị cổng phê duyệt giữ lại** (test sống: `sudo xoá` → CẦN PHÊ DUYỆT → `duyệt` → chạy).
  - Boot seed: nhóm `văn:100:gốc,an` · sổ `an: xem liệt soi xoá` (KHÔNG phải `*`).
- **Kiểm:** `kiem_nhom_sudo.giao` + phiên sudo tương tác → `kiem_hdh_giao.py` mục [27]:
  244→**258** hạng mục (cập nhật đếm /lệnh 45→47 vì thêm 2 lệnh vỏ). `kiem_toan_bo` **65/65**.
- **Còn mở (ghi CÒN_THIẾU):** tệp mới tạo mang gid 0 (chưa kế thừa nhóm chính/setgid);
  sổ sudo chưa có vế "dưới uid nào" (hiện luôn là gốc).

---

## v0.12.0 — ★★★ MẠNG (B1) + chặn bẫy thêm/gom (A3) (2026-07-30)

- **★ A3 — BẪY `thêm`/`gom` bị chặn tận gốc:** `thêm(ds, x)` đứng MỘT MÌNH (kết quả bị vứt —
  danh sách không đổi gì, bug im lặng từng cắn ở `lib_người_dùng`) nay là **lỗi sạch** kèm gợi ý:
  *"Chèn tại chỗ: gom(ds, x) · giữ bản mới: đặt ds = thêm(ds, x)"*. Chỉ bắt khi `thêm` vẫn là
  builtin gốc — người dùng tự định nghĩa hàm `thêm` riêng thì không đụng. `kiem_thu.py` 71→**74**.
- **★★★ B1 — TẦNG MẠNG** (`lib_gọi_hệ.giao`, gọi-hệ 29–32): mô hình Y NHƯ ỐNG liên-tiến-trình
  nhưng theo **CỔNG**:
  - `GH_NGHE(cổng[, quyền=666])` — mở Ổ NGHE; **cổng < 1024 chỉ gốc-quyền** (luật Linux);
  - `GH_NỐI(cổng)` → MÃ kết nối; `được_phép` chuẩn Unix chạy THẲNG trên ổ (ổ có chủ/quyền):
    ổ 600 → người khác bị **tối**; không ai nghe → **ẩn** (ba-trị đúng chỗ);
  - `GH_GỬI_GÓI(mã, gói)` / `GH_NHẬN_GÓI(mã | cổng)` — kết nối = hai hàng gói một chiều
    ("lên"/"xuống") **dùng lại đúng bộ ruột ống** (sức chứa + phản áp + chặn/đánh thức);
    chủ-nghe gọi theo cổng nhận `["nối", mã]` (khách mới) rồi `[mã, gói]`;
    **chỉ HAI ĐẦU MỐI đúng tid được dùng kết nối** — kẻ thứ ba bị tối.
  - Thiết bị **`/tb/mạng`** (gắn ở boot `hdh_nền.giao`): đọc ra `nghe cổng: […] · kết nối: n`.
    Audit ghi `nối`/`gửi_gói`/… như mọi gọi-hệ. Ảnh chụp CŨ (trước B1) nạp lại vẫn chạy
    (`_mạng` tự vá khoá thiếu).
  - Kiểm `kiem_lib_mang.giao` — đúng điểm mấu chốt của hồ sơ: **hai tiến trình nói chuyện qua
    mạng VÀ quyền vẫn chặn được** (3 tầng: cổng đặc quyền · quyền ổ · đầu mối).
    `kiem_hdh_giao.py` mục [26]: 234→**244** hạng mục.
- **Trung thực phạm vi:** đây là mạng **TRONG máy** (loopback liên-tiến-trình). Nối ra HOST
  thật (socket TCP qua capability) vẫn còn mở — ghi ở CÒN_THIẾU B1'.

---

## v0.11.1 — SHA-256 nhanh ~3× (inline vòng nóng) → nâng `$g2$` 32→128 vòng (2026-07-30)

- **Tối ưu `lib_sha256.giao`:** inline `_s_quay`/`_s_ép32` trong lịch thông điệp + 64 vòng nén —
  mỗi lời gọi hàm GIAO tốn một môi trường mới, ~450 lời/khối là phần đắt nhất. Mặt nạ 32-bit gộp
  về MỘT lần cuối mỗi tổ hợp quay nhờ `&` PHÂN PHỐI trên `^`: `(a^b^c)∧M = (a∧M)^(b∧M)^(c∧M)`.
  Đo: ~20ms → **~6.3ms/vòng băm_mk2** (1 khối/vòng). Vector hashlib vẫn KHỚP TỪNG KÝ TỰ.
- **`MK_VÒNG2` 32 → 128** (~0.8s/lần kiểm ở thông dịch — 4× số vòng, thời gian mỗi lần kiểm
  gần như cũ nhờ tối ưu). Số vòng nằm trong bản ghi nên bản `$g2$32$` cũ vẫn khớp được.
- Kiểm: `kiem_lib_mật_khẩu.giao` xanh cả `$g1$`/`$g2$` · `kiem_hdh_giao.py` 234/234.
- **`bat_may.bat`** (mới): bật HĐH bằng một cú gõ đúp / một lệnh — tự đặt console UTF-8
  (`chcp 65001` + `PYTHONUTF8`), tự kiểm tra có `python`, chuyển tiếp mọi cờ
  (`--goc` · `--luu/--nap <ảnh>` · `<kịch bản>.txt`). Đã kiểm: đăng nhập, bền hoá
  `--lưu`→`--nạp` (tệp `nói "..." > tệp` sống sót qua reboot).

---

## v0.11.0 — ★★★ PHÉP BIT + GÁN CHỈ MỤC + SHA-256 THUẦN GIAO (A1·A2·C1 của CÒN_THIẾU) (2026-07-30)

Ba mục tồn đọng "chặn nhiều thứ khác" được khép trong một phiên — theo đúng thứ tự hồ sơ
`CÒN_THIẾU.md`: A1 mở khoá C1, A2 làm C1 viết gọn được.

- **★ A1 — PHÉP TOÁN BIT** (builtin `giao.py`): `xor` · `và_bit` · `hoặc_bit` · `đảo_bit` ·
  `dịch_trái` · `dịch_phải`. Số NGUYÊN chính xác mọi cỡ (như `//`); số âm theo bù-hai vô hạn;
  **ba-trị**: đối nào `ẩn` → kết quả `ẩn`; `dịch_trái` có trần 8 triệu bit (chống nổ bộ nhớ);
  số bit dịch âm → lỗi sạch. `giaoc` từ chối SẠCH theo cơ chế RANH_GIOI sẵn có (không
  biên-dịch-nhưng-sai). Kiểm: `kiem_lib_bit.giao` (rotr32 dựng được từ dịch+hoặc+và).
- **★ A2 — GÁN THEO CHỈ MỤC**: `đặt ds[i] = x` · `đặt bản[khoá] = x` · lồng `đặt l[i][j] = x` —
  sửa **TẠI CHỖ** (tham chiếu). Chỉ mục/thùng `ẩn` → **không ghi** (no-op, như `đặt_khoá` với
  khoá ẩn); ngoài phạm vi/chuỗi-bất-biến → lỗi sạch có gợi ý. Logic đọc chỉ mục gom về MỘT
  nguồn sự thật (`_chỉ_mục_đọc`) cho cả biểu thức lẫn phép gán. `lib_lịch_γ.giao` viết lại
  `γ_bước` gọn hẳn (bỏ hai vòng dựng-lại-danh-sách) — `kiem_lich_gamma.py` vẫn **2000/2000**.
- **★ C1 — SHA-256 THUẦN GIAO** (`lib_sha256.giao`, tên tệp KHÔNG DẤU theo quy ước mới):
  FIPS 180-4 đầy đủ + **UTF-8 tự dựng bằng phép bit** (cả emoji 4 byte) — đối chiếu
  `hashlib.sha256` của Python **KHỚP TỪNG KÝ TỰ** (5 vector, gồm đa khối). Tốc độ thông dịch
  ~10ms/khối 64 byte.
- **★ C1 — MẬT KHẨU `$g2$`** (`lib_mật_khẩu.giao`): `băm_mk2` = SHA-256 **xích theo byte**
  (mỗi vòng đúng 1 khối: digest 32B + muối 16B), định dạng `$g2$<vòng>$<muối>$<băm64hex>`,
  mặc định 32 vòng (trung thực: thấp vì đường thông dịch; số vòng nằm TRONG bản ghi nên nâng
  được mà không phá bản cũ). **`bóng_mới` nay phát hành `$g2$`** (bản ghi mới); `khớp_mk` đọc
  **cả `$g1$` lẫn `$g2$`** — không bắt ai đổi mật khẩu; `bóng_mới_g1` giữ cho kiểm cũ. Boot
  `hdh_nền.giao` seed `$g2$32$…`, đăng nhập/`thành`/`đổi_mk` chạy xuyên suốt như cũ.
- **Sửa test rớt «tôi là ai»** (`kiem_hdh_giao.py` [21]): mốc v0.9.1 viết theo tim thật
  (Ollama bge-m3, γ=835) nhưng tim đã gỡ (E1) → nhúng dự phòng băm-từ cho γ=235 < ngưỡng 450 →
  máy TỪ CHỐI. Test nay **nhận biết backend qua `/tb/tim`**: tim thật → đòi trả lời `1000 an`;
  tim dự phòng → đòi đúng bất-biến còn giữ được là **xếp hạng đúng kỹ năng cao nhất + từ chối
  an toàn dưới ngưỡng** (từ chối khi chưa đủ hiểu là HÀNH VI THIẾT KẾ, không phải lỗi).
- **Kiểm thử:** `kiem_thu.py` 63→**71** (mục [13b] bit + gán chỉ mục) · `kiem_hdh_giao.py`
  232→**234** ($g1$ song song $g2$, thác đổ SHA) · `kiem_toan_bo.py` 63→**65** hạng mục
  (thêm SHA-256 + bit) — **65/65 xanh**.
- **Quy ước mới (người dùng chốt 2026-07-30):** tên tệp/đường dẫn MỚI đặt **KHÔNG DẤU**
  (`lib_sha256.giao`, `kiem_lib_bit.giao`…); tệp cũ có dấu giữ nguyên; định danh TRONG mã vẫn
  tiếng Việt có dấu.

---

## v0.10.1 — ĐƯỜNG DẪN KHÔNG DẤU: chữa tận gốc, gỡ hết chỗ lách (2026-07-29)

- **Dự án chuyển `D:\Hệ điều hành\GIAO` → `D:\HeDieuHanh\GIAO`.** Ba công cụ phần cứng đều mở tệp
  bằng API ANSI nên đường dẫn có dấu là hỏng: `vvp` không `dlopen` nổi module VPI
  (*"The specified module could not be found"*), `nextpnr` không mở nổi `.lpf`
  (*"Invalid argument"*), `iverilog` không nuốt đường dẫn tuyệt đối. Ổ D đã tắt tên 8.3 nên
  không lách bằng đường dẫn ngắn được.
- **Gỡ hết chỗ lách:** `hw/lam_cosim_vpi.py` và `hw/lam_bo_mo_phong.py` nay dựng `.vpi` **thẳng cạnh
  mã nguồn** (bỏ `D:\giao_vpi_build`); `hw/lam_bitstream.py` cho `nextpnr` đọc **thẳng**
  `hw/ulx3s.lpf` (bỏ bước chép) và xuất kết quả vào `hw/ra/` (bỏ `D:\giao_bitstream`).
- **Kiểm lại từ chỗ mới:** đồng mô phỏng VPI 5.183 chu kỳ · bo qua dây UART · toàn bộ chuỗi
  bitstream — tất cả chạy mà không cần chép tệp đi đâu.
- **Vẫn còn:** `yosys` và `iverilog` không nhận **định danh tiếng Việt** trong RTL (chú thích thì
  được) — đó là chuyện của trình phân tích cú pháp, không phải đường dẫn; `hw/*.v` giữ tên ASCII.

---

## v0.10.0 — ★★★ ĐĂNG NHẬP THẬT: sổ người dùng, mật khẩu băm có muối, đổi người (2026-07-29)

Trước bản này, `python chay_hdh_giao.py` **vào thẳng** với tư cách `an`: có uid, có quyền rwx, nhưng
**không có cửa** — chọn người dùng là một cờ dòng lệnh chứ không phải một lần xác thực.

- **`lib_mật_khẩu.giao`** (mới): băm mật khẩu **có muối, có lặp** — muối riêng từng người + 4096 vòng
  + trộn theo modulo số nguyên tố Mersenne 2^61−1 (GIAO tính số nguyên chính xác nên không mất bit).
  Định dạng `$g1$<vòng>$<muối>$<băm>`, kiểu `/etc/shadow`.
  *Trung thực:* **không** phải bcrypt/scrypt/Argon2, chưa qua thẩm định mật mã; GIAO chưa có phép
  toán trên **bit** nên chưa dựng nổi SHA-256 đủ nhanh. Chống bảng cầu vồng và dò bừa — không hơn.
- **`lib_người_dùng.giao`** (mới): `/hệ/người_dùng` (644, `tên:uid:nhà`) + `/hệ/mật_khẩu` (**600**,
  bản băm). `xác_thực` · `đăng_nhập` · `đặt_mk` · `thêm_người_hệ` · `khoá_người`. Hàm đăng nhập chạy
  dưới **tiến trình gốc** vì phải đọc tệp 600 — đúng vai `/bin/login` setuid root. Người thường tự
  gọi `xác_thực` thì nhận `ẩn`: chính tầng quyền chặn, không phải quy ước lịch sự.
- **Màn hình đăng nhập** trong `chay_hdh_giao.py`: hỏi tên + mật khẩu (tắt tiếng vọng), ba lần sai
  thì nhập lại từ đầu, và **không nói rõ sai TÊN hay sai MẬT KHẨU** (nói rõ là chỉ điểm cho người dò
  tài khoản). `thoát` nay là **đăng xuất** → quay lại màn đăng nhập; `tắt` mới tắt máy.
- **Lệnh mới:** `người` (~`getent passwd`, là lệnh vỏ THẬT nên chạy được trong ống: `người | đếm`) ·
  `thành <người>` (~`su`, hỏi mật khẩu; **sai thì phiên đang dùng không hề hấn gì**) · `đổi_mk`
  (~`passwd`, phải biết mật khẩu cũ, gõ lại phải khớp, tối thiểu 4 ký tự).
- **Ranh giới chứng minh được:** cùng câu `xem /hệ/mật_khẩu` — `an` nhận *cấm đọc*, `gốc` đọc được và
  thấy **bản băm**, không thấy mật khẩu.
- `--gốc` nay gọi đúng tên: **chế độ một người dùng** (uid 0, không hỏi gì — như `init=/bin/sh`).
- **Bẫy đã gặp:** `getpass` đọc thẳng console nên treo khi đầu vào là đường ống ⇒ lùi về `input()`
  khi `stdin` không phải tty. Và trong GIAO, thêm phần tử vào danh sách là **`gom`**, không phải
  `thêm` — dùng nhầm thì danh sách im lặng rỗng.
- **Chưa có:** SSH, nhiều tty, nhóm người dùng, `sudo` với sổ quyền riêng, hạn tuổi mật khẩu.
- **Kiểm thử:** `kiem_hdh_giao.py` **+21 hạng mục** (mục [25] + `kiem_lib_mật_khẩu.giao`).

---

## v0.9.5 — ★★★ RA BITSTREAM FPGA: GVM thành mạch thật, nhân nối bằng DÂY UART (2026-07-29)

- **`hw/gvm_bo.v`** (mới): đỉnh cho bo thật — GVM + cầu UART chở chân trap ra máy chủ. Khung byte
  `0xA5` (xin gọi-hệ) · `0xB5` (CPU RỌI) · `0x4D` (đọc ô nhớ) · `0x57` (ghi ô nhớ) · `0x5A` (phục vụ
  xong) · `0xC5` (CPU dừng). Máy chủ **duyệt heap của CPU** để lấy chuỗi đối và **cấp chuỗi trả về
  vào heap của CPU** — y như C làm ở §5.17, chỉ là qua dây.
- **`hw/uart.v`** (mới): UART 8N1 tối giản. **`hw/ulx3s_top.v`** + **`hw/ulx3s.lpf`**: vỏ và ràng
  buộc chân cho bo ULX3S (ECP5).
- **`hw/nhan_qua_uart.py`** (mới): nhân HĐH-GIAO phục vụ CPU qua cổng COM — cùng một lớp `PhiênBo`
  dùng cho cả bo thật lẫn bản mô phỏng.
- **`hw/lam_bo_mo_phong.py`** (mới): chạy **chính cái đỉnh sẽ nạp lên bo** trong iverilog với một cặp
  `uart_rx`/`uart_tx` đóng vai sợi cáp — mô phỏng tới **từng bit** trên dây. Kết quả: 6 lời xin,
  1.126 byte lên · 1.042 byte xuống, chuỗi đi cả hai chiều, quyền + cổng bất-khả-hồi **vẫn nguyên**.
- **`hw/lam_bitstream.py`** (mới): yosys → nextpnr-ecp5 → ecppack → `.bit`, rồi `--nạp` gọi
  openFPGALoader. Bytecode nằm SẴN trong ROM của bitstream.
- **`hw/gvm.v`**: thêm cổng `dbg_a/dbg_re/dbg_we/dbg_wd/dbg_q` cho cầu ngoài soi & cấp heap.
- **Bẫy đã gặp — cổng đọc thứ ba:** cho cầu ngoài một cổng đọc RAM RIÊNG làm tổng hợp chạy hơn nửa
  tiếng không xong: BRAM `DP16KD` chỉ có **HAI** cổng, thêm cái thứ ba là cả `4096×32` rơi khỏi BRAM
  xuống LUT. Cách đúng: **dùng chung** cổng đọc sẵn có (`ram_ra` ưu tiên `dbg_a` khi `dbg_re`) — CPU
  đang đứng ở `S_TRAP` nên cổng ấy rảnh. Hệ quả: testbench cũ để hở `dbg_re` làm X lan khắp nơi ⇒
  phải nối đất `dbg_*` ở cả ba testbench.
- **Công cụ:** OSS CAD Suite (yosys · nextpnr · ecppack · openFPGALoader) **cài vào `D:\oss-cad`**.
- **Kiểm thử:** `kiem_hdh_giao.py` **+9 hạng mục** (mục [24]).
- **★★ BITSTREAM ĐÃ DỰNG ĐƯỢC** cho ECP5-85F (ULX3S): yosys 36s → nextpnr 60s → ecppack 2s;
  **7.067 LUT (8%) · 2.052 FF (2%) · 30 BRAM (14%) · 9 MULT18 (5%) · Fmax 39,66 MHz** (chạy 25 MHz,
  dư 59%). Tệp `D:\giao_bitstream\gvm.bit`, 1.997.265 byte. Cả cái máy + bytecode chương trình
  chiếm **8% một con ECP5-85F**.
- **Bẫy đường dẫn (lại):** `nextpnr` mở `.lpf` bằng API ANSI ⇒ đường dẫn tiếng Việt là *"Failed to
  open LPF file"*; phải chép sang thư mục ASCII trước.
- **Chưa làm được:** *cắm bo thật* — `openFPGALoader --scan-usb` trả bảng RỖNG, máy này không có bo
  FPGA nào. Bitstream đã có và đã kiểm tới từng bit trên dây; nạp là một lệnh, nhưng cần phần cứng.

---

## v0.9.4 — ★★ ĐIỂM HẸN VPI: bỏ tệp, nhân GIAO thành hàm hệ thống của bộ mô phỏng (2026-07-29)

- **`hw/giao_vpi.c`** (mới): module VPI cài `$giao_trap(số, nargs, đ0, đ1, đ2)` và `$giao_dem` vào
  chính `vvp`. Lời gọi **chặn tại thời điểm mô phỏng** — C duyệt thẳng `dut.ram[]` bằng
  `vpi_handle_by_index`/`vpi_get_value` để moi chuỗi đối, hỏi nhân GIAO thật qua **socket**, rồi
  `vpi_put_value` cấp chuỗi trả về vào **heap của chính CPU** (ô cons `[mã, đuôi]`, mọi con trỏ mang
  thẻ). Verilog không còn phải gói đối, không dò tệp, không `wait`.
- **`hw/cosim_vpi_tb.v`** + **`hw/lam_cosim_vpi.py`** (mới): toàn bộ điểm hẹn gọn trong một dòng
  Verilog. Testbench từ ~120 dòng xuống còn ~60.
- **★★ ĐO ĐƯỢC** (cùng chương trình, cùng nhân, 3 lần mỗi bản): tệp = 16.515 · 18.435 · 23.455 chu
  kỳ (và có lần **2.327.815**), 0,64 s — VPI = **5.183 · 5.183 · 5.183** chu kỳ, **0,40 s**. Cái
  được không chỉ là nhanh hơn ~3–4 lần mà là **tất định**: gọi-hệ nay tốn đúng **2 chu kỳ bắt tay**,
  không còn phụ thuộc nhân trả lời nhanh hay chậm.
- **Bẫy Windows đã gặp:** `vvp` nạp module VPI bằng `dlopen` ANSI ⇒ thư mục **có dấu tiếng Việt** báo
  *"The specified module could not be found"*, mà ổ D lại **tắt tên 8.3** nên không lách bằng đường
  dẫn ngắn. Cách làm: dựng riêng `.vpi` ra thư mục ASCII (`D:\giao_vpi_build`, **vẫn trên ổ D**) và
  truyền `-M<đường dẫn tuyệt đối>`; có nhớ-đệm theo `mtime` nên chỉ biên dịch lại khi `.c` đổi.
- **Công cụ:** thêm GCC (MinGW-w64) **cài vào `D:\mingw64`** — ổ C không đụng tới.
- **Kiểm thử:** `kiem_hdh_giao.py` **+10 hạng mục** (mục [23]).

---

## v0.9.3 — ★★ TRAP NHIỀU ĐỐI: phần cứng nhận 0–3 đối (2026-07-29)

- **`hw/gvm.v`**: đường-dữ-liệu chỉ prefetch 2 toán tử đỉnh, nên từ 2 đối trở lên opcode 72 chuyển
  sang trạng thái mới **`S_TRAPA`**, mỗi chu kỳ moi thêm một tầng ngăn xếp (`sp − 3 − trap_k`) rồi
  mới dựng `trap_valid`. Thêm chân **`trap_arg1` / `trap_arg2`**; `trap_nargs` = 0..3.
- **Đối chiếu phần mềm ⟷ cổng logic** (`hw/lam_trap.py`): `[700, 42, 742, 84, 14, 321, 1640]` —
  **trùng khít**, gồm cả trap 2 đối (5+9), trap 3 đối **đúng thứ tự** (1+20+300=321) và trap
  **lồng nhau** (`gọi_hệ(52, a, d, gọi_hệ(50,4))` → 1640).
- **★★ Đồng mô phỏng (`hw/lam_cosim.py`)**: tiến trình trên cổng logic nay **TẠO ĐƯỢC TỆP THẬT** —
  `gọi_hệ(2, "/tạm/từ_silicon", 644, "dòng này do CỔNG LOGIC viết")` (3 đối) rồi nối thêm bằng
  `gọi_hệ(3, …)` (2 đối) và đọc lại chính nó. Vẫn bị chặn ở `/hệ/mật_khẩu` và ở lệnh xoá.
- **Bẫy đã gặp:** testbench cắt mã ký tự xuống 8 bit để in ⇒ chữ tiếng Việt thành byte hỏng, luồng
  đọc `vvp` phía Python **chết âm thầm, mất SẠCH mọi dòng in**. Nay TB tự mã hoá UTF-8, và `vvp`
  ghi thẳng ra `cosim_log.txt` thay vì qua ống bị đệm khối. Thêm vòng thử lại cho `os.replace` vì
  Windows chặn thay tệp khi `vvp` đang mở đọc.
- **Kiểm thử:** `kiem_hdh_giao.py` **191/191** (thêm 5 hạng mục cho trap nhiều đối).

---

## v0.9.2 — ★★★★★ ĐỒNG MÔ PHỎNG: cổng logic xin việc của NHÂN HĐH-GIAO THẬT (2026-07-29)

- **★ Nối thẳng CPU gate-level ⟷ nhân GIAO thật**: `hw/lam_cosim.py` + `hw/cosim_tb.v`. Testbench
  không còn đóng giả nhân — nó chỉ làm **bưu tá**: duyệt heap của CHÍNH CPU để lấy chuỗi đối, gói vào
  `trap_req.txt`; nhân phục vụ bằng **chính `gọi(máy, tid, số, đối)`**; kết quả chuỗi được bưu tá
  **cấp phát vào heap của CPU** (cons `[mã, đuôi]`, mọi con trỏ mang thẻ) rồi trả con trỏ.
- **★★ KẾT QUẢ**: tiến trình chạy trên cổng logic (uid 1000) đọc `/hệ/tên_máy` → nhân trả "giao-01",
  **CPU tự in ra**; đọc `/hệ/mật_khẩu` → **`tối` — cấm đọc**; `xoá /tạm/rác` → **`tối` — CẦN PHÊ
  DUYỆT**, hậu kiểm thấy **tệp còn nguyên**; `ai` → "1000 an". **Nhật ký audit ghi đủ 4 việc.**
  Tức là quyền rwx + cổng bất-khả-hồi của một HĐH viết bằng GIAO **chặn được tiến trình đang chạy
  trên cổng logic**.
- **Bẫy phần cứng đã gặp:** bắt tay `trap_ack` bằng gán KHÔNG-CHẶN trong `always @(posedge clk)` làm
  mỗi trap bị **gửi hai lần** (nhân phục vụ hai lượt, số hiệu lệch). Phải dùng `initial forever` +
  `wait` tường minh + `#1` đẩy phép gán ra khỏi cạnh clock. Ngoài ra iverilog **không nhận định danh
  có dấu tiếng Việt** (`đã_gửi` → `da_gui`).
- **Trung thực:** trap phần cứng nhận 0–1 đối (demo dùng syscall một đối); điểm hẹn là **tệp**, không
  phải VPI ⇒ mỗi lời xin tốn vài nghìn chu kỳ mô phỏng — đủ để chứng minh NGỮ NGHĨA, không phải tốc độ.

## v0.9.1 — ★★★★ TRÁI TIM LÀ THIẾT BỊ: lõi quyết định của trợ lý chạy bằng bytecode (2026-07-29)

- **★ Gọi-hệ 27 `nhúng` + 28 `cộng_hưởng`** — trái tim (mạng nơ-ron) KHÔNG THỂ là bytecode, nên nó
  được phơi ra như **thiết bị**: máy xin `nhúng(chữ)` và chỉ nhận **SỐ HIỆU** (vector giữ ở nhân,
  kho `kho_vector`), rồi xin `cộng_hưởng(sh_a, sh_b)` → **γ×1000** (số nguyên, hợp máy). Thêm thiết
  bị **`/tb/tim`**: đọc ra tim đang đập bằng gì.
- **★ `trợ_lý_máy.giao`** — LÕI QUYẾT ĐỊNH của trợ lý bằng bytecode: tự nhúng lời nhờ, tự chấm γ ba
  kỹ năng, tự chọn cao nhất, tự áp ngưỡng, **tự TỪ CHỐI** khi dưới ngưỡng. Với tim thật (bge-m3):
  835 cho kỹ năng đúng vs ~360 cho sai; lời "làm bài thơ" ra 184/191/218 → **−1 = từ chối**.
- **Phân vai chốt lại đúng học thuyết:** *tim CẢM* (thiết bị, ngoài máy) · *máy XÉT* (bytecode) ·
  *nhân LÀM* (uid + cổng bất-khả-hồi vẫn nguyên).
- **Trợ lý ở tầng thông dịch đổi thứ tự sinh lệnh:** MẪU + dò hệ-tệp TRƯỚC, trái tim viết SAU — cùng
  một lẽ với "có căn cứ thắng mơ hồ": lệnh soạn theo mẫu đã đối chiếu thực tại, trái tim thì đang đoán.
- **Cài đặt (theo yêu cầu: KHÔNG đụng ổ C, ổ C chỉ còn 15.7 GB):** Ollama **bản portable** giải nén
  vào `D:\Ollama` (1.85 GB), `OLLAMA_MODELS=D:\Ollama\models` (bền qua phiên), model `bge-m3` +
  `llama3.2:1b` (2.4 GB) — ổ C **không thêm một byte**. Icarus Verilog cài `--location D:\iverilog`.

## v0.9.0 — ★★★★★ GỌI-HỆ XUỐNG CỔNG LOGIC: opcode 72 trong hw/gvm.v (2026-07-29)

- **★ `hw/gvm.v` (CPU dựng từ NAND) có opcode 72 `GỌI_HỆ`** với giao thức trap thật của CPU:
  cổng ra `trap_valid`/`trap_num`/`trap_arg`/`trap_nargs`, cổng vào `trap_ack`/`trap_ret`; trạng thái
  FSM mới **`S_TRAP`** — CPU **đứng im**, không đếm timer, không chạy lệnh, cho tới khi nhân `ack`,
  rồi đẩy `trap_ret` vào ngăn xếp và chạy tiếp. Máy KHÔNG tự làm I/O, y như ở phần mềm.
- **`hw/lam_trap.py`** — pipeline GIAO → `giaoc` → bytecode → `program_trap.hex` → `gvm_trap.v` →
  **iverilog/vvp**; `trap_tb.v` đóng vai NHÂN bằng phần cứng (giải mã số hiệu, trả kết quả, ack).
- **★★ ĐỐI CHIẾU: phần mềm ⟷ cổng logic TRÙNG KHÍT** `[700, 42, 742, 84]` — kể cả phép tính
  **trên giá trị nhân trả về** (700+42=742) và trap lồng dữ liệu (nhân đôi 42→84). CPU dừng sạch sau
  133 chu kỳ · 3 trap · 4 lần RỌI.
- Cài công cụ **trên ổ D** theo yêu cầu: `winget install Icarus.Verilog --location D:\iverilog`
  (ổ C không thêm một byte nào). iverilog không nuốt đường dẫn có dấu tiếng Việt ⇒ harness gọi bằng
  **tên tương đối** với `cwd=hw`.
- **Trung thực:** phần cứng nhận **0–1 đối** (prefetch 2 toán hạng); nhiều đối hơn cần thêm chu-kỳ
  đọc ngăn xếp. "Nhân" ở đây là testbench — nối HĐH-GIAO thật vào chân trap là cột mốc riêng
  (co-simulation phần mềm↔phần cứng).

## v0.8.5 — ★ VÁ LỖ HỔNG BỀN HOÁ: tiến trình MÁY không còn sống-lại-thành-xác (2026-07-29)

- **Lỗi tự tìm ra sau v0.8.x** (kiểm chủ động, không phải người dùng báo): `chụp_máy` chụp đủ hệ-tệp,
  bảng tiến-trình, trạng thái bền… **nhưng KHÔNG chụp lõi GVM**. Hậu quả: sau phục hồi, tiến trình
  MÁY vẫn hiện trong `tt` như đang sống mà **không bao giờ chạy nữa** — `lõi` = ẩn, `dựng lại 0 thân`,
  rồi bị đỗ sang "chặn" vĩnh viễn. **Không một dòng lỗi nào.** Đúng loại sai im lặng nguy hiểm nhất.
- **★ Vá:** hai builtin mới của năng lực `máy` — `máy_ảnh(lõi)` gói NGỮ CẢNH (ip · ngăn xếp toán hạng ·
  pstack · rstack · khung · handler · cờ halted · **vùng RAM đã dùng** 0..HEAP_PTR · số lệnh đã tiêu)
  và `máy_nạp_ảnh(mã, ảnh)` dựng lại. `lib_bền.giao` chụp thêm `ct_máy` (nguồn) + `lõi_ảnh` (theo tid);
  `dựng_lại_thân` nay **biên dịch lại nguồn rồi nạp ngược ngữ cảnh** cho tiến trình máy.
- **Bytecode KHÔNG cần chụp** — biên dịch lại từ nguồn cho ra đúng từng từ-lệnh (tất định). Ảnh nhờ
  vậy nhỏ: một máy có 2 tiến trình máy đang chạy dở chỉ tốn ~2.500 ký tự JSON.
- **Nghiệm thu bằng hành vi, không bằng lời**: đếm tới 29 → chụp → vứt máy → dựng lại → **đếm tiếp 26,
  25…** (không lặp lại 30); tiến trình đang dở một `gọi_hệ` cũng hoàn tất và chép được tệp.
  `chay_ben_may.py`. Nghiệm thu **155 → 162 hạng mục**; toàn dự án **63/63**.
- Bẫy nhỏ khi vá: `pstack` của GVM chứa **số thuần** (không phải ô `{st,val}`) — gói nhầm như ngăn
  xếp toán hạng là nổ ngay.

## v0.8.4 — ★★★★ DỊCH VỤ NỀN XUỐNG MÁY: bytecode biết NGỦ như daemon (2026-07-29)

- **★ `nhật_ký_máy.giao`** — bản MÁY của dịch vụ nhật ký: `gọi_hệ(19)` nhận tin, `gọi_hệ(3)` ghi vào
  `/hệ/nhật_ký`. Thân là bytecode GVM, vẫn bị cắt CPU + lịch γ như mọi tiến trình.
- **★ CHO MÁY BIẾT NGỦ — không thêm opcode nào:** `GH_NHẬN` mà hộp thư rỗng thì nhân **vừa trả −1
  vừa ĐỖ tiến trình sang trạng `chặn`** (`_phục_vụ_bẫy` trả "chặn", `_chạy_lát_máy` truyền lên bộ
  lập lịch). Bộ lập lịch thôi cấp CPU; `gửi` đánh thức; máy chạy tiếp NGAY SAU trap. Đúng ngữ nghĩa
  `read()` chặn của Linux.
- **Đo được:** sinh xong ngủ ngay (1 lát), quay nhân thêm 10 lát **vẫn 1 lát** — ngủ thì không tốn
  CPU thật. Ba lần `gửi` → ba dòng `[máy] …` trong `/hệ/nhật_ký` do bytecode viết. Cả đời dịch vụ:
  **2.898 lệnh máy / 16 lát CPU**, kết ở trạng `chặn`.
- Sửa chỗ hiển thị: nối chuỗi với `ẩn` cho ra `ẩn` ⇒ vết trap phải diễn giải thành "(ẩn — chưa có gì)".
- Nghiệm thu **147 → 155 hạng mục**; toàn dự án **63/63**. Tài liệu §5.13.

## v0.8.3 — ★★★★ VỎ MÁY TỰ TÁCH TỪ (nhân chỉ còn là bàn phím) (2026-07-29)

- **★ `tách` xuống máy mà KHÔNG phải sửa `giaoc` một dòng nào**: viết `_tách_dòng` BẰNG GIAO trong
  tập con biên-dịch-được, thế là nó cũng thành bytecode. Mẹo: trên máy **chuỗi CHÍNH LÀ danh sách mã
  ký tự**, nên `s[i]` → số, `[s[i]]` → chuỗi 1 ký tự, `ghép` nối, `==` so theo nội dung.
- **`GH_LỆNH`(25) nay trả NGUYÊN DÒNG** (hết hàng → 0 = NIL). Nhân chỉ còn đóng vai **bàn phím**;
  vỏ tự tách từ, tự phân giải, tự gọi syscall. Thêm lệnh `đếm_từ` để chứng: vỏ tự đếm ra 4 từ.
- **Giá phải trả, đo được:** tự tách từ tốn **~160.000 lệnh máy / 412 lát CPU** so với ~14.000 / 67
  khi nhân tách hộ. Ghi lại đúng con số thay vì nói suông.
- **Trung thực:** `vỏ_máy.giao` CHỈ dành cho máy — chạy bằng thông dịch sẽ khác nghĩa ở `s[i]`
  (thông dịch trả chuỗi 1 ký tự, máy trả mã số). An toàn vẫn nguyên: uid chặn `xem /hệ/mật_khẩu`,
  cổng bất-khả-hồi chặn `xoá`, tệp còn nguyên.
- Nghiệm thu **146 → 147 hạng mục**; toàn dự án **63/63**.

## v0.8.2 — ★★★★ VỎ LỆNH CHẠY BẰNG BYTECODE trên GVM (2026-07-29)

- **★ `vỏ_máy.giao`** — vòng lặp lõi của một cái vỏ, viết trong TẬP CON BIÊN-DỊCH-ĐƯỢC ⇒ chạy như
  **bytecode trên GVM**: tự phân giải tên lệnh (**so sánh chuỗi trên máy**), tự gọi syscall, tự in.
  Làm được `tôi` `ở` `xem` `liệt` `soi` `ghi` `thêm` `xoá`. Tiêu ~14.000 lệnh máy / 67 lát CPU,
  bị lịch γ xếp hàng và bị cắt theo lượng tử như mọi tiến trình.
- **Hai gọi-hệ mới**: `GH_LỆNH`(25) lấy dòng kế tiếp (nhân **tách từ hộ**, trả SỐ TỪ; hết → −1) ·
  `GH_TỪ`(26) lấy từ thứ i. Nhân đóng vai bàn phím: `xếp_lệnh(máy, dòng)` đẩy vào hàng đợi.
- **AN TOÀN GIỮ NGUYÊN**: vỏ máy uid 1000 `xem /hệ/mật_khẩu` → `tối`; `xoá /tạm/rác` → `tối`
  (CỔNG BẤT-KHẢ-HỒI), tệp **còn nguyên**. Nghiệm thu có đủ.
- **★ SỬA LỖI IM LẶNG KHÓ NHẤT ĐỢT NÀY:** nhân cấp chuỗi lên heap máy mà **quên gắn THẺ cho con trỏ
  ĐUÔI** trong cons ⇒ chuỗi **1 ký tự vẫn đúng** (`"ở"`) còn chuỗi dài **so sánh trượt** (`"tôi"`,
  `"xem"`) — vỏ máy cứ báo "không hiểu lệnh" mà không có lỗi nào. Mọi con trỏ (kể cả đuôi) phải
  mang thẻ ở chế độ 32-bit.
- `biên_dịch(nguồn, 32)` — ép chế độ CÓ THẺ; nhân dùng cho mọi chương trình máy (không có thẻ thì
  `RỌI_AUTO` in ra ĐỊA CHỈ thay vì chữ). Danh sách trả về (`liệt`/`soi`/`ai`) được nhân **ghép thành
  một chuỗi** ngăn bằng khoảng trắng — trung thực: máy chưa có kiểu "danh sách chuỗi" để in.
- `chay_vo_may.py` nạp nguồn vỏ từ đĩa thật (Python lại chỉ làm bộ điều khiển đĩa, như Linux nạp
  `/bin/sh`). Nghiệm thu **134 → 146 hạng mục**; toàn dự án **63/63**. Tài liệu §5.12.

## v0.8.1 — ★★★★ OPCODE GỌI-HỆ (72): tiến trình MÁY xin việc của NHÂN (2026-07-29)

- **★ GVM có opcode `GỌI_HỆ` (72)** — trap như `syscall`/`int 0x80`: pop `arg` đối + pop số hiệu →
  máy **TẠM DỪNG** (`trap_pending`, `run()` thoát êm, chưa halt); nhân đọc, phục vụ bằng **CHÍNH
  `gọi(...)`**, rồi `máy_trả` đẩy kết quả vào ngăn xếp cho máy chạy tiếp. **Máy không bao giờ tự làm
  I/O.** `giaoc` biên dịch `gọi_hệ(số, đối…)` thẳng ra opcode này.
- **Chuỗi đi được cả hai chiều**: đối chuỗi = con trỏ heap của máy → nhân đọc bằng builtin mới
  `máy_chuỗi`; kết quả chuỗi được nhân **cấp phát trên heap của máy** (quy ước HEAP_PTR ram[250] của
  giaoc, gắn thẻ danh-sách khi 32-bit) rồi trả con trỏ. Nhân tra chữ ký của chính mình (`_đối_chuỗi`)
  nên máy không cần biết kiểu.
- **★ AN TOÀN KHÔNG MẤT MỘT CHÚT NÀO** (nghiệm thu `hdh_máy_gọi_hệ.giao`): tiến trình máy uid 1000
  đọc `/hệ/mật_khẩu` → `tối` (*cấm đọc*); `xoá /tạm/rác` → `tối` (*CẦN PHÊ DUYỆT*), tệp **còn nguyên**;
  nhật ký audit ghi đủ lời xin của tiến trình máy. Mã đã biên dịch vẫn phải xin phép từng việc một.
- Vỏ tương tác nay chạy được cả chương trình MÁY: `việc` liệt kê riêng nhóm "chương trình MÁY (biên
  dịch xuống GVM)", `chạy chép_máy` → bytecode đọc `/hệ/tên_máy` rồi ghi ra `/nhà/an/tên_máy_chép`.
  `chay_hdh_giao.py` tự cấp năng lực `máy` cho HĐH (chạy `giao.py` trần thì vẫn cần `--cho-máy`).
- Nghiệm thu `kiem_hdh_giao.py` **126 → 134 hạng mục**; toàn dự án **63/63**. Tài liệu §5.11.

## v0.8.0 — ★★★★ TIỀN ĐỊNH THẬT: thân tiến trình BIÊN DỊCH XUỐNG GVM, nhân CƯỚP CPU (2026-07-29)

- **★ NĂNG LỰC NGÔN NGỮ MỚI `máy`** (`--cho-máy`; chưa cấp ⇒ tên KHÔNG tồn tại = object-capability):
  `biên_dịch(nguồn)` → từ-lệnh GVM (vượt `RANH_GIOI.md` → **ẩn**, không nổ) · `máy_nạp(mã)` → một
  **lõi máy riêng** cho mỗi tiến trình · **`máy_lát(lõi, n)` → chạy ≤ n LỆNH rồi CƯỚP** (dùng
  `GVM.run(max_steps=…)` vốn tạm-dừng-được) · `máy_xuất` · `máy_lệnh`. Đây KHÔNG phải cửa hậu ngôn
  ngữ mà là **cửa xuống phần cứng**: GVM là cái máy, GIAO xin nó "chạy hộ N lệnh rồi trả quyền".
- **★ TIẾN TRÌNH MÁY trong nhân**: `đăng_ký_ct_máy(máy, tên, nguồn)` · `GH_SINH` tự **biên dịch +
  nạp lõi** · `chạy_lát` rẽ nhánh: có lõi thì chạy bytecode theo `lượng_tử` (mặc định 120 lệnh,
  `đặt_lượng_tử`), không thì chạy closure như cũ. **Hai loại tiến trình sống chung dưới một bộ lập
  lịch.** ρ cho lịch γ = "có RỌI trong lượng tử" — CHÍNH tín hiệu `did_out` của γ-scheduler silicon.
- **Thí nghiệm quyết định** (`hdh_máy.giao`, lượng tử 120 lệnh, 18 lát): `tham_lam` là **vòng lặp
  một triệu bước KHÔNG một điểm nhường nào** — thứ chắc chắn treo hệ ở tầng closure. Kết quả:
  hai `việc_thật` **chạy xong** (785 lệnh · 7 lát mỗi cái), `tham_lam` chỉ được **480 lệnh · 4 lát**,
  σ=40 (γ=−0.69). **Vừa CẮT được (cơ chế), vừa BÓP được (chính sách γ).**
- **Trung thực về phần còn lại:** thân tiến trình MÁY phải nằm trong tập con biên-dịch-được (số
  nguyên/hàm/đệ quy/rẽ nhánh/vòng đếm/heap) — chưa có gọi-hệ, nên hiện là **tiến trình tính toán
  thuần**; vỏ/trợ lý/dịch vụ vẫn là closure (hợp-tác). Muốn tiền định TOÀN PHẦN phải thêm **opcode
  gọi-hệ** cho GVM — lúc đó cả HĐH chạy được trên silicon.
- Sửa nhỏ nhưng quan trọng: ρ đo bằng **số dòng xuất tăng thêm** thay vì cờ `did_out` (opcode `RỌI`
  đặt cờ, nhưng `RỌI_AUTO`/`RỌI_CHUỖI` thì không) — **không phải sửa cái máy đã kiểm chứng bit-exact**.
  Và `dừng` chỉ hợp lệ TRONG vòng lặp ⇒ thoát sớm phải dùng hàm + `trả`.
- Nghiệm thu `kiem_hdh_giao.py` **117 → 126 hạng mục** (thêm cả ca "chưa cấp `--cho-máy` thì HĐH vẫn
  chạy êm"); toàn dự án **63/63**. Tài liệu `HDH_GIAO_LINUX.md` §5.10.

## v0.7.6 — ★★★ LẬP LỊCH γ (CDFL) LÊN TẦNG HĐH + TRỢ LÝ HỎI LẠI KHI MƠ HỒ (2026-07-29)

- **★ `lib_lịch_γ.giao` — nhân ĐO rồi QUYẾT.** Linux xếp theo `nice` (số NGƯỜI khai, máy tin); HĐH-GIAO
  xếp theo γ (số máy TỰ ĐO): `ρ=255` nếu lát vừa rồi tiến trình CÓ gọi-hệ, `0` nếu chỉ quay vòng;
  `σ←σ+((ρ−σ)>>2)`; `credit←credit+(σ>>2)`, kẻ vừa chạy trả `COST=128`; chọn kế = `argmax(credit)`.
  Bật bằng `bật_lịch_γ(máy, sáng)` hoặc lệnh vỏ `lịch γ` / `lịch thường`.
- **Kết quả đo được** (3 tiến trình CÙNG ưu tiên 5, 30 lát — `hdh_tiền_định.giao`): lịch cổ điển cho
  kẻ tham lam **15 lát (50%)** và **BỎ ĐÓI hẳn** một tiến trình thật (0 lát); lịch γ bóp kẻ tham lam
  còn **5 lát (16%)** và **không ai bị bỏ đói** (13/12). σ học được: tham **30 (γ=−0.76)** vs việc-thật
  **250 (γ=+0.96)** — kẻ tham lam thành **đốm tối** đúng nghĩa CDFL.
- **★ CHỨNG: lịch của HĐH ≡ lịch của SILICON.** `kiem_lich_gamma.py` đối chiếu `γ_bước` (GIAO) với
  `gvm_may.GVM.γ_cập_nhật` (tầng máy, vốn đã chứng trùng wire `hw/gvm.v`): **2000/2000 ca ngẫu nhiên
  khớp hoàn toàn** (σ mới · credit mới · tiến trình được chọn). `>>2` có dấu = `//4` của GIAO nên số
  học khớp tuyệt đối. Đã ghép vào `kiem_toan_bo.py`.
- **★ Trợ lý HỎI LẠI khi mơ hồ** (việc nhỏ làm trước): sinh **mọi cách hiểu** rồi chỉ hỏi khi chúng
  **khác nhau về hậu quả** — có cái PHÁ HUỶ lẫn cái lành, hoặc trỏ vào **chỗ khác nhau**; còn "soi…
  xem bao nhiêu" (hai động từ nhưng cùng đọc một tệp) thì cứ làm, không hỏi vặt. Trả lời bằng
  `chọn|pick <n>` (gọi-hệ mới **GH_CHỌN 24**) — và **chọn cái phá huỷ thì trợ lý VẪN không tự chạy**,
  vì chọn là chọn CÁCH HIỂU, không phải cấp phép.
- Sửa 2 va tên với từ khoá GIAO khi viết phần này (`thử`, `học` là keyword, không dùng làm tên biến);
  gộp việc dò hệ-tệp lại **một lần mỗi lời nhờ** (trước dò 3 lần → tốn bước vô ích); `chay_hdh_giao.py`
  tự nới trần bước (phiên dài là chính đáng, không phải vòng lặp loạn).
- **Trung thực về chữ "tiền định":** nhân **quyết** được và **bóp** được kẻ tham lam — phần đó thật.
  Nhưng ở tầng thông dịch, nhân **không cắt ngang** được closure đang chạy dở; cướp CPU giữa chừng
  (`timer_period`) chỉ có ở tầng máy. Muốn trọn nghĩa phải **biên dịch thân tiến trình xuống GVM**.
- Nghiệm thu `kiem_hdh_giao.py` **108 → 117 hạng mục**; toàn dự án **62/62** (+1 mục lịch γ).

## v0.7.5 — ★★★ TRỢ LÝ TỰ SOẠN LỆNH (sinh, nhưng có ba cái phanh) (2026-07-29)

- **★ Tầng 2 của trợ lý**: khi kho kỹ năng không đủ hiểu, nó **soạn một dòng lệnh MỚI**. Hai lối:
  **(a) theo mẫu** — bảng động-từ (11 mục) + đối tượng **dò được từ hệ-tệp** qua `liệt`/`soi`;
  hoàn toàn tất định, **không cần LLM** (chạy được cả khi máy không có Ollama). **(b) trái tim
  viết** — chỉ khi có model thật: prompt kèm **danh sách lệnh lấy thẳng từ `/lệnh`**, lấy dòng đầu.
- **Ba cửa cho MỌI lệnh sinh ra:** (1) **thẩm định** — mỗi lệnh phải có thật trong `/lệnh` và người
  nhờ **chạy được** (hỏi bằng gọi-hệ, không tin trí nhớ model); (2) **đối tượng có thật** — không dò
  thấy đường dẫn thì **không sinh**, thà chịu; (3) **trình bày + cổng** — luôn IN dòng lệnh trước khi
  chạy, việc phá huỷ (`xoá`/`quyền`/`đổichủ`/`giết`/`gắntb`) thì CHỈ trình bày, người tự quyết.
  Lệnh sinh ra vẫn chạy bằng **uid của người nhờ** ⇒ vẫn bị nhân chặn y hệt (đã nghiệm thu).
- **Luật "có căn cứ thắng mơ hồ"**: soạn được lệnh cụ thể mà kỹ năng trong kho chỉ khớp lửng lơ
  (γ < ngưỡng+0.30) thì tin cái có căn cứ — kho là mô tả chung chung, lệnh soạn đã đối chiếu thực tại.
- **Ba bẫy "trả lời sai mà vẫn hợp lệ" đã gặp + sửa** (thứ nguy hiểm nhất ở một trợ lý): quét bảng
  động từ theo thứ tự khiến *"soi … xem bao nhiêu"* ra `xem` → phải chọn động từ **xuất hiện sớm
  nhất**; lấy đối tượng khớp đầu tiên khiến *"tệp mật_khẩu của hệ thống"* ra `xem /hệ` → phải lấy tên
  **khớp dài nhất**; kỹ năng "liệt-kê-nhà" (28–49%) giành mất cả câu hỏi về `/tạm` lẫn câu xoá → sinh
  ra luật ưu tiên ở trên.
- **★ `giao.py` thêm cờ `--bước N`** (mặc định vẫn 5 triệu): HĐH-GIAO nay là chương trình GIAO lớn
  nhất dự án và chạm trần một cách **chính đáng** (tra `$PATH` + dò hệ-tệp + lọc nhật ký dài). Host
  nới **tường minh** như một năng lực, mặc định vẫn chặn DoS. Bản trình diễn cũng được chỉnh cho gọn
  dưới trần mặc định (`nhật_ký 24 | tìm nhờ` đặt ngay sau các lượt nhờ thay vì quét 400 dòng ở cuối).
- **Thử lại bằng câu CHƯA TỪNG CHỈNH RIÊNG** → lòi thêm 2 bẫy cùng họ, đã sửa: (d) `xem` một THƯ MỤC
  ra "cấm đọc /tạm" — nghe như lỗi quyền, thật ra **dùng sai dụng cụ** ⇒ nay `soi` kiểu đối tượng rồi
  tự chỉnh `xem`↔`liệt`; (e) *"nhật ký hệ có gì"* ra `nhật_ký 10` (sổ audit) trong khi có hẳn tệp
  `/hệ/nhật_ký` ⇒ **đối tượng dò thấy thắng động từ chung chung** (`_động_từ_trống`).
- Nghiệm thu `kiem_hdh_giao.py` **96 → 108 hạng mục**; toàn dự án **62/62**. Tài liệu §5.8.
  **Trung thực:** đây là heuristic chứ không phải chứng minh; lớp chặn thật vẫn là *in lệnh trước khi
  chạy · việc phá huỷ không tự chạy · nhân cưỡng chế quyền*.

## v0.7.4 — ★★★ BỀN HOÁ: cả hệ điều hành gói trong MỘT chuỗi JSON (2026-07-29)

- **★ `lib_bền.giao`** — `chụp_máy(máy)` → JSON · `phục_hồi_máy(chuỗi)` → máy · `hồi_sinh(máy)` nối
  mã. Chụp: cây hệ-tệp (kể cả **ống với gói còn đọng**), bảng tiến-trình, hàng lập-lịch, hộp thư IPC,
  uid + thư-mục hiện hành, sổ người dùng, đồng hồ nhịp, nhật ký audit, **việc đang chờ phê duyệt**,
  trạng thái bền của từng tiến-trình, và phiên vỏ đang mở.
- **★ TIẾN TRÌNH DỞ DANG CHẠY TIẾP.** Thân tiến-trình là closure ⇒ không JSON hoá được, nên nhân tách
  đôi: **dữ liệu** ở `trạng_ct[tid]` (chụp được) + **gốc gác** ở `khai_sinh[tid] = [tên ct, đối]`.
  Phục hồi thì `dựng_lại_thân` gọi lại xưởng; xưởng thấy `lấy_trạng` không rỗng ⇒ **dùng lại state
  cũ**, không khởi tạo lại (không xoá tệp, không đếm lại). Đúng mô hình CRIU: *dữ liệu bền, mã nạp
  lại*. Demo: đếm tới 3 → chụp → vứt máy → dựng lại → **đếm tiếp 4 5 6**.
- **Bền qua HAI LẦN CHẠY**: `chay_hdh_giao.py --lưu ảnh.json` (thoát phiên thì chụp ra đĩa thật) ·
  `--nạp ảnh.json` (bật lại đúng cái máy hôm qua: tệp, lệnh người dùng tự viết, tiến trình còn dở).
  Python chỉ đóng vai **bộ điều khiển đĩa** (đọc/ghi byte). Vỏ thêm lệnh `chụp|snapshot <tệp>` (chụp
  vào chính hệ-tệp GIAO); phục hồi thì phải làm từ NGOÀI lúc boot — máy không tự thay ruột giữa chừng.
- **★ SỬA LỖI THẬT CỦA `lib_json` (ảnh hưởng cả dự án):** `thành_json` **không thoát ký tự** ⇒ chuỗi
  chứa `"` hoặc xuống dòng (nội dung tệp thì đầy) sinh JSON **HỎNG**, phân tích lại là mất trắng. Đã
  thêm `_thoát` (`"` `\\` xuống-dòng tab) và giải mã `\\n`/`\\t` ở `_đọc_chuỗi`. `kiem_lib_json` vẫn xanh.
- **Bẫy thứ hai đã sửa:** JSON biến **mọi khoá thành chuỗi** ⇒ sau phục hồi `lấy_khoá(bảng, 3)` trượt
  còn `lấy_khoá(bảng, "3")` mới trúng. `_khoá_số` đổi khoá số về đúng kiểu cho bảng tiến-trình, cred,
  hộp thư, cờ chặn, sổ người dùng, trạng_ct, khai_sinh.
- Nghiệm thu `kiem_hdh_giao.py` **79 → 96 hạng mục** (thêm mục [10] round-trip trong-bộ-nhớ và [11]
  bền qua hai lần chạy trên đĩa thật); toàn dự án **62/62**. Tài liệu `HDH_GIAO_LINUX.md` §5.7.

## v0.7.3 — ★★★ ỐNG LIÊN-TIẾN-TRÌNH THẬT: chặn · phản áp · EOF (2026-07-29)

- **★ Ống là ĐỐI TƯỢNG CỦA NHÂN, và vẫn LÀ TỆP.** `nút_ống` (hạng `"ống"`) trong `lib_tệp_hệ.giao`:
  hàng FIFO (`đệm` + con-trỏ `đầu` — danh sách GIAO chỉ nối-thêm nên "lấy ra" = dịch con-trỏ), sức
  chứa, cờ `đóng`, hai hàng đợi `chờ_đọc`/`chờ_ghi`. `soi` một ống thấy **số gói đang đọng** + quyền
  rwx như mọi tệp khác. Syscall mới: **`GH_ỐNG`(22) = mkfifo · `GH_ĐÓNG`(23) = đóng đầu ghi**;
  `GH_ĐỌC`/`GH_GHI` tự rẽ nhánh khi đường dẫn là ống.
- **Bốn tính chất của ống Linux, có thật, nghiệm thu được** (`hdh_ống.giao`, 6 màn):
  (1) **chặn/đánh thức** — đọc ống rỗng → trạng `chặn`, nhân KHÔNG gọi lại (không quay vòng bận);
  có gói thì `_ống_thức` đưa về hàng sẵn-sàng. (2) **PHẢN ÁP** — ống đầy thì **bên GHI** phải ngủ;
  với ống sức chứa 1, vết lập-lịch hiện `bơm → chặn` xen kẽ `hút → tiếp`. (3) **EOF** — bên ghi
  `đóng` ⇒ bên đọc rút hết đệm rồi kết thúc sạch, không treo. (4) **QUYỀN** — ống 600 của gốc-quyền
  thì tiến trình `an` ghi vào bị `cấm ghi ống`.
- **★ Vỏ dựng ĐƯỜNG ỐNG THẬT**: nếu MỌI chặng đều là bệ phóng `#tt` thì `bơm 6 | lọc chẵn | hút
  /tạm/kq` = **ba tiến trình** nối bằng **hai ống của nhân** (không còn chuyền văn bản). Có chặng
  không phải chương trình thì `|` vẫn là ống văn bản như cũ. Thêm **`&`** = chạy nền (không có `&`
  thì vỏ CHỜ đường ống/chương trình xong — tiền cảnh thật sự). Lệnh mới `ống|mkfifo`, `đóng|close`;
  ba chương trình đường-ống `bơm` · `lọc` · `hút` (quy ước `đối[0]`=ống vào, `đối[1]`=ống ra).
- **Trung thực về bế tắc:** đọc ống không ai ghi ⇒ ngủ **mãi** (`còn việc sẵn-sàng? tối` — nhân
  không quay tít, chỉ là nó chờ). Lối thoát đúng như Linux: ai đó `đóng` đầu ghi. Không có phép màu
  chống bế tắc — màn 5 của demo trình bày đúng chuyện đó.
- **BẪY NGÔN NGỮ ghi lại:** biến toàn cục **che được hàm thư viện**. Đặt `đặt lát = …` ở mức toàn cục
  đã che hàm `lát()` (slice) của `lib_chuoi` ⇒ `bắt_đầu()` gọi `lát(...)` và gãy với thông báo khó
  hiểu *"không gọi được giá trị kiểu số"*, mà vị trí dòng báo lỗi lại trỏ nhầm chỗ. Đã đổi tên thành
  `số_lát`. Bài học: tên biến toàn cục trong chương trình GIAO nên tránh trùng tên hàm `chuẩn.giao`/
  `lib_chuoi` (`lát`, `lọc`, `chọn`, `đếm`…).
- Nghiệm thu `kiem_hdh_giao.py` **65 → 79 hạng mục**; toàn dự án **62/62**. Tài liệu `HDH_GIAO_LINUX.md` §5.6.

## v0.7.2 — ★★★ `/lệnh` THÀNH THƯ MỤC LỆNH THẬT: lệnh cũng chỉ là TỆP (2026-07-29)

- **★ Vỏ bỏ bảng lệnh cứng — đi TRA TỆP.** Gõ `xem` ⇒ vỏ tra `/lệnh/xem` đúng như Linux quét `$PATH`
  (`$PATH` ở `/hệ/đường_lệnh`, mặc định `/lệnh:/nhà/an/lệnh`). Hệ quả THẬT: thiếu bit `x` → **mã 126**
  "cấm chạy"; xoá tệp → **mã 127** "không có lệnh". `quyền /lệnh/xoá 644` là khoá lệnh lại thật sự,
  và quyền tính **theo từng người** (chủ/khác) chứ không phải cờ toàn cục.
- **Ba hạng tệp lệnh** phân biệt bằng dòng đầu: `#nội-trú <tên>` (vỏ tự làm — một thân nhiều tên, như
  busybox) · `#tt <chương-trình>` (**bệ phóng tiến trình** thật dưới bộ lập lịch — nối với v0.7.1) ·
  còn lại = **KỊCH BẢN vỏ** nhiều dòng, có `$1…$9` và `$*`, chú thích bằng `#`.
- **★ Viết lệnh mới lúc máy ĐANG CHẠY**: `ghi /nhà/an/lệnh/nhà_tôi "liệt /nhà/an | đếm"` +
  `quyền … 755` ⇒ gõ `nhà_tôi` là chạy. Không biên dịch, không khởi động lại. Người dùng có thư mục
  lệnh riêng (`/nhà/an/lệnh`, do chính họ làm chủ) — lệnh trở thành **dữ liệu soi được, phân quyền được**.
- `cài_lệnh(máy, tid_gốc)` dựng `/lệnh` lúc boot (30 lệnh nội trú + 3 bệ phóng tiến trình + 3 kịch bản
  mẫu `soi_hệ`/`lỗi`/`rác` + `/hệ/đường_lệnh`). Chỉ `về` và `thoát` bắt buộc nằm trong vỏ (như `cd` của
  bash — chương trình ngoài không đổi được thư mục của vỏ). Kịch bản có chặn đệ quy (>8 tầng).
- `gõ()` nay tự quay nhân 6 lát sau mỗi dòng ⇒ việc nền tiến lên trong cả bản trình diễn, không chỉ
  vỏ tương tác.
- **★ SỬA HIỆU NĂNG (thật, không phải dọn dẹp):** trước đây `/tt` (procfs) được **tái sinh ở MỌI lời gọi
  đọc/liệt/soi**; cộng thêm 2–3 lời gọi tra `$PATH` mỗi lệnh ⇒ bản trình diễn **chạm trần 5 triệu bước**
  của trình thông dịch và bị `GiaoLimit` chặn (thoạt nhìn cứ tưởng vòng lặp vô tận). Nay `/tt` chỉ sinh
  khi đường dẫn thật sự nằm trong `/tt` — đúng cách Linux sinh procfs **khi có người đọc**.
- Nghiệm thu `kiem_hdh_giao.py` **55 → 65 hạng mục**; toàn dự án **62/62**. Tài liệu: `HDH_GIAO_LINUX.md` §5.5.
- **Còn lại (trung thực):** tệp trong `/lệnh` là **văn bản**, chưa phải mã máy — bước tiếp theo nếu muốn
  thật hơn: biên dịch chương trình GIAO → bytecode GVM và để chính bytecode nằm trong tệp lệnh.

## v0.7.1 — ★★★ `sinh` CHẠY CHƯƠNG TRÌNH THẬT: đa nhiệm dưới bộ lập lịch (2026-07-29)

- **★ Tiến trình có THÂN, có lượt CPU.** `lib_chương_trình.giao`: chương trình = XƯỞNG
  `hàm(máy, tid, đối) → thân`; `thân` là closure chạy **một lát** rồi trả `"tiếp"` / `"xong"` /
  `"chặn"`. `GH_SINH` nạp thân khi tên đã đăng ký ⇒ `sinh` thôi làm bản-ghi, bắt đầu **sinh ra sự
  sống**. Nhân quay bánh xe bằng `vòng_nhân(máy, số_lát)` / `chạy_tới_hết` / `còn_việc` / `đánh_thức`.
- **Đủ vòng đời Linux** `sẵn-sàng → chạy → (chặn ↔ đánh-thức) → chết`: hai tiến trình `đếm` chạy
  **xen kẽ thật** (mỗi cái một `bản` state riêng = vùng nhớ riêng); dịch vụ `nhật_ký_hệ` gọi
  `GH_NHẬN` gặp hộp thư rỗng → `"chặn"` → **ngủ, không đốt CPU**; `GH_GỬI` đánh thức nó, ghi nhật ký
  xong nó **ngủ tiếp** (đúng mô hình daemon, không quay vòng bận).
- **Kế thừa danh tính**: con nhận uid + thư-mục của cha ⇒ tiến trình `tọc_mạch` sinh từ vỏ của `an`
  KHÔNG đọc nổi `/hệ/mật_khẩu`, KHÔNG tạo nổi `/hệ/cửa_sau` (có ca nghiệm thu).
- **Vỏ cũng là tiến trình có vòng đời thật**: đang xử lý dòng lệnh = `chạy`, xong = `chặn` (ngủ trên
  bàn phím như `bash` chặn ở `read()`); lời gọi LỒNG của trợ lý không đụng trạng thái. Vỏ có lệnh
  mới `chạy|run <ct> [đối…]` · `nhịp|tick [n]` · `việc|jobs` · `kể|verbose [tắt]`; `chay_hdh_giao.py`
  tự quay nhân vài lát sau mỗi dòng ⇒ **việc nền vẫn tiến trong lúc người dùng gõ**.
- **Bẫy đã gặp + sửa (ghi lại vì suýt sập hệ):** tiến trình KHÔNG có thân (`khởi`, `vỏ`, `trợ_lý_ai`)
  ban đầu bị `chạy_lát` coi là `"xong"` ⇒ bộ lập lịch **giết luôn init và vỏ** (mọi lời gọi sau đó
  trả "tiến-trình 1 đã chết"). Nay trả `"ngủ"` và nhân **đỗ** sang `chặn`, tuyệt đối không giết.
  Ngoài ra GIAO **không cho xuống dòng giữa biểu thức** (`… +` rồi newline) — phải tách biến trung gian.
- Bản trình diễn `hdh_tiến_trình.giao` (6 màn: daemon ngủ · đa nhiệm xen kẽ · IPC đánh thức · thiết bị
  + hệ-tệp · kế thừa quyền · vòng đời qua `/tt`). Nghiệm thu `kiem_hdh_giao.py` **37 → 55 hạng mục**.
- **Còn lại (trung thực):** đa nhiệm là **hợp-tác**, chưa tiền-định — chương trình tham lam vẫn giữ
  máy (nhân γ-preempt đã có ở tầng máy `chay_hdh_preempt.py`, nối lên tầng này là việc sau); chương
  trình vẫn là closure đăng ký sẵn, chưa phải tệp thực thi trong `/lệnh`.

## v0.7.0 — ★★★ HĐH-GIAO ĐỔI HƯỚNG: DỰNG THEO LỐI LINUX, CÓ TRỢ LÝ AI TRONG NHÂN (2026-07-29)

- **★ HỆ-TỆP kiểu Linux** (`lib_tệp_hệ.giao`) — MỘT cây `/`, "mọi thứ là tệp" (thư-mục · tệp ·
  **thiết bị**), quyền Unix 3 chữ-số (755) + uid, **uid 0 = gốc-quyền**, kiểm quyền ĐÚNG CHỖ Linux
  kiểm (tạo/xoá tên ⇒ ghi trên THƯ-MỤC CHA; đi xuyên thư-mục ⇒ bit `x`). `errno` → **ba-trị**:
  `sáng` xong · `tối` **từ chối** · `ẩn` **không có**. Đường-dẫn `.` `..` chuẩn hoá.
- **★ TẦNG GỌI-HỆ** (`lib_gọi_hệ.giao`) — bảng syscall **có số hiệu** `GH_*` 0…21 và MỘT cổng duy
  nhất `gọi(máy, tid, số, đối)`; mỗi lời gọi mang **danh tính (uid)** của tiến trình gọi; **nhật ký
  audit** mọi lời gọi. `/tt` = procfs (nhân tự sinh tệp cho từng tiến trình), `/tb` = devfs
  (`màn`·`không`·`giờ`·`ngẫu`·`đĩa0`). Nhân tiến-trình/lập-lịch/IPC **dùng lại `lib_hệ.giao`** đã có.
- **★ CỔNG BẤT-KHẢ-HỒI** (khác `sudo`: hỏi *việc có hoàn tác được không*, không hỏi *bạn là ai*) —
  `xoá`/`đổi_chủ`/`giết`/ghi-đè-ổ-đĩa bị **giữ lại kèm lời giải thích** tới khi người gõ `duyệt`
  (dùng một lần). Từ chối thẳng việc không đời nào cho (`giết` tiến-trình 1).
- **★ VỎ LỆNH** (`lib_vỏ.giao`) — ống `|`, chuyển hướng `>` `>>`, nối `&&`, dấu nhắc kiểu bash
  (`an:/nhà/an$`, gốc-quyền là `#`), lệnh tên Việt + **bí danh Linux** (`ls`/`cat`/`ps`/`chmod`…).
  Vỏ là chương trình người-dùng THUẦN: không chạm hệ-tệp, chỉ biết `gọi(...)`.
- **★ TRỢ LÝ AI LÀ DỊCH VỤ HỆ THỐNG** (`lib_trợ_lý.giao`) — `nhờ <lời nói>` là **GỌI-HỆ GH_NHỜ (21)**,
  thứ Linux không có. Ràng **ba lớp**: (1) **đồng danh tính** — trợ lý gõ lệnh qua CHÍNH tid người
  nhờ ⇒ uid y hệt, **không có cửa hậu** (nhờ đọc `/hệ/mật_khẩu` vẫn bị nhân chặn); (2) **cổng γ** —
  γ=`cộng_hưởng(nhúng(mô-tả kỹ-năng), nhúng(lời nhờ))`, dưới ngưỡng thì **nói "chưa hiểu", không bịa**,
  và in **toàn bộ bảng γ** ⇒ quyết định soi được; (3) **cổng bất-khả-hồi** — việc phá huỷ chỉ được
  TRÌNH BÀY dự định, người tự quyết (tầng gọi-hệ chặn lần hai).
- **HĐH chạy được**: `python giao.py hdh_giao.giao` (6 màn trình diễn) · **`python chay_hdh_giao.py`
  = VỎ TƯƠNG TÁC gõ lệnh thật** (Python chỉ làm bàn phím + màn hình; HĐH nằm trong GIAO) ·
  `hdh_nền.giao` (boot thuần). Nghiệm thu `kiem_hdh_giao.py` **37/37**, đã ghép vào `kiem_toan_bo.py`.
- **Sửa 2 cạm bẫy phát hiện khi xây:** (a) `sáng`/`tối` **là chuỗi** trong GIAO — trộn tín-hiệu vào
  giá-trị trả về thì tệp chứa chữ "tối" bị hiểu nhầm là "bị cấm" ⇒ tách **kênh quyền riêng**
  (`tth_xem_được` / `lỗi_cuối`), đúng như Linux tách `open()` khỏi `read()`. (b) **ngưỡng γ phải theo
  trái tim đang đập** — máy đã gỡ Ollama nên γ tụt thang, `examples/trai_tim.giao` vỡ (`argmax` trên
  danh-sách rỗng): nay τ tự chỉnh (`0.40` cho bge-m3 · `0.15` cho bản dự-phòng); `ngưỡng_γ()` của trợ lý
  cũng vậy. Tài liệu: **`HDH_GIAO_LINUX.md`** (bản đồ Linux→GIAO, kiến trúc, **giới hạn trung thực**,
  5 việc kế tiếp).
- **Trung thực về giới hạn:** tiến trình chưa chạy song song thật trong bản này (bảng/ưu-tiên/IPC/`/tt`
  là thật, nhưng chỉ vỏ là chương trình chạy thật — đa nhiệm closure đã có ở `examples/hdh.giao`, việc
  kế tiếp là ghép vào); chưa có ELF/`/lệnh` rỗng; ống `|` là ống văn bản trong một tiến trình; tầng này
  chạy trên trình thông dịch, **chưa xuống GVM/FPGA** (xem `RANH_GIOI.md`).

## v0.6.1 — ★ MMIO: DRIVER BARE-METAL bằng GIAO ("xuống chip" — Pha-1 gap) (2026-07-17)

- **★ MMIO như NĂNG-LỰC** (`mmio(địa_chỉ[, giá_trị])`) — lấp đúng gap roadmap Pha-1 ("thêm opcode MMIO
  đọc/ghi thanh ghi thiết bị"). Cài ở TẦNG THÔNG DỊCH theo mô hình object-capability sẵn có (`--cho-mmio`;
  chưa cấp ⇒ tên không tồn tại = sandbox bẩm sinh) → **KHÔNG đụng opcode máy / conformance 4-substrate**
  (Verilog bit-exact giữ nguyên; iverilog không có nên không sửa mù). Bản đồ: `UART_TX=0·UART_ST=4·TIMER=8·
  LED=12`, ba-trị (thanh ghi lạ→ẩn).
- **Driver Giao** `examples/driver_mmio.giao` — đúng mẫu "first driver" build-your-own-x (os-tutorial/phil-opp:
  ghi thanh ghi thiết bị): blink LED (bit-pattern) + "hello" ra UART + đọc timer tự-chạy + **lịch phục vụ
  thiết bị bằng γ skill-score MỚI** (nối phần a↔b). `python giao.py examples/driver_mmio.giao --cho-mmio`.
- **Học từ build-your-own-x** → `HOC_TU_BUILD_YOUR_OWN_X.md`: bảng bài-học (os-tutorial/little-OS-book/
  phil-opp-Rust/mini-arm-os/egos-2000/mal), cái GIAO **đã có** (ngắt/timer/preempt/fault/SIP/persistence) vs
  **vừa thêm** (MMIO) vs **còn** (ánh xạ MMIO→chân FPGA thật, Pha 3 compiler-native).
- **Trung thực:** MMIO này là **mô hình nền tham chiếu** (dev/simulate driver TRƯỚC khi flash silicon); vật lý
  thật = ánh xạ sang chân UART/GPIO của `hw/gvm.v` trên FPGA (bitstream đã dựng, còn flash bo). `kiem_toan_bo` **61/61**.

## v0.6.0 — ★ REBUILD CDFL CŨ→MỚI: γ SKILL-SCORE (F.4) + e CAM KẾT (F.11) (2026-07-17)

- **★ γ = SKILL-SCORE thay proxy tuyến-tính.** Học thuyết NNL-NTHT đã sửa: γ nay là điểm-kỹ-năng `[S(ρ‖u)−S(ρ‖σ)]/[S(ρ‖u)+S(ρ‖σ)]` (S=−ln R), so niềm tin với **NỀN VÔ-TRI** `u=exp(−1)` — thay công thức cũ `1−2d/scale` (chỉ đo "gần/xa", không hiệu chỉnh nền). Ý nghĩa MỚI: **đốm tối (γ<0) = niềm tin TỆ HƠN cả đoán-mù**, không phải chỉ "xa". Khớp `D:\Ai Agent\core.py` (Phụ lục F). Sửa GỐC: `giao.py` `resonance()` + builtin `cộng_hưởng` → **tự lan** khắp tầng lý-thuyết `chuẩn.giao` (`chọn/γ_hành_động/or_tập_thể/ensemble_γ/là_đốm_tối/qua_Φ/de_if_Φ`).
- **★ Thêm e CAM KẾT (F.11)** — trước đây VẮNG hoàn toàn: `cam_kết(độ_tán[,std0]) = S/(1+S)`, S=Σln(std0/std)≥0. (e,γ) → **Tứ Tượng** (Lão Dương/Thiếu Âm=ĐỐM TỐI chắc-mà-sai/Thiếu Dương/Lão Âm).
- **Builtin toán mới (thuần, ba-trị):** `log · mũ · căn`; builtin CDFL tường-minh: `γ_kỹ_năng(R_tin,R_nền) · cộng_hưởng_thô(σ,ρ)=R∈(0,1] · cam_kết(...)`.
- **Nhân `os_ai_cdfl.py` nâng cấp:** `res`→skill-score + hiển thị e + Tứ Tượng mỗi vòng; demo đốm-tối sửa thành ca THẬT (niềm tin sai-dấu mà **không thấu kính Φ nào cứu nổi** → γ<0). Showcase mới `examples/nao_cdfl_moi.giao` (R→γ→đốm tối→e→Tứ Tượng→2 cổng gốc→node quyết định gộp 4 ca).
- **GIỮ NGUYÊN:** DE bốn-mặt X/T/IF/MF + phát-hiện đốm-tối-bằng-dấu (đã đúng); hai cổng tiêu-chí gốc (coverage "học-1-hiểu-10" + consent bất-khả-hồi). **KHÔNG đụng γ-scheduler silicon** (`gvm_may.py`/`hw/gvm.v`): là operationalization CDFL RIÊNG cho preempt (credit σ-EMA), đổi sẽ phá bit-exact 3000/3000 + 16/16 Verilog — tách track, tài-liệu-hoá.
- **NGHIỆM THU trung thực:** `kiem_toan_bo.py` **60/60**. 3 assert cũ đo *magnitude proxy* (`cộng_hưởng(90,100)=0.8`→`0.9802`; MCP `95-vs-70=+0.29`→`+0.774`) + 1 ngưỡng demo `trai_tim τ=0.55→0.40` được **re-baseline công khai** (cùng dấu, cùng kỷ-luật gate) — KHÔNG gài số. *Bài học lặp lại từ core.py: sửa công thức → chạy lại → cập nhật kỳ vọng thẳng, ghi rõ vì sao.*

## v0.5.8 — ★ KHỞI ĐỘNG SIÊU-LỆNH (Track M+C co-design ISA): opcode #68 CỘNG_HẰNG (2026-06-19)

- **★ SIÊU-LỆNH #1 `CỘNG_HẰNG k`** (add-immediate `push(pop+k)`): gộp idiom `NẠP k; CỘNG` (bigram cao nhất có immediate, 820 chỗ) → 1 opcode, giảm BƯỚC THẬT trong vòng-lặp nóng (peephole không làm được). Ba-trị ẩn→ẩn (y hệt CỘNG), provably-safe.
- **Cài 4-SUBSTRATE (sở-hữu trọn stack):** `gvm_may.py` · `giaoc.py` (`_siêu_lệnh`+cờ `BẬT_SIÊU_LỆNH`) · `wasm/gvm.ts` (op 68 + rebuild `gvm.wasm`) · `hw/gvm.v` (OP_CONG_HANG, EXEC ghi stack[sp-1]). Unit-test luật siêu-lệnh.
- **★ BẬT MẶC-ĐỊNH (`BẬT_SIÊU_LỆNH=True`) sau VCD-trace + VÁ 2 BUG gate-level:** **bước GVM −10.6%→−15.2%** · bytecode −14.4%. **TRỌN conformance 4-substrate:** 14/14 KHỚP BYTE + 15/15 unit + **wasm 20/20** + **16/16 Verilog** (gồm preemptive-FAULT).
  - **Vá #1 (hw/gvm.v) — context-switch hazard:** γ-scheduler chọn-LẠI-cùng-task (`gsel_live==cur`) → `t_ip[cur]<=ip` & `ip<=t_ip[gsel_live]` CÙNG chu-kỳ → non-blocking đọc CŨ → wild-jump → HALT. Vá: cùng-task ⇒ GIỮ state. Bug CÓ-SẴN.
  - **Vá #2 (hw/gvm.v) — hợp-nhất preempt-granularity:** Verilog đếm timer theo CHU-KỲ, software theo LỆNH (`timer_period`=số LỆNH). Vá: Verilog tick **1/LỆNH ở S_EXEC** → khớp software. *Bài học: "sửa bằng hết" = VCD-trace soi gốc → vá 2 bug gate-level có-sẵn; siêu-lệnh = lever giảm-BƯỚC thật; co-design ISA phải khớp granularity software⟷silicon.*
- **★ SIÊU-LỆNH #2 (opcode #69 `NHÂN_CỘNG_HẰNG k`):** gộp `NHÂN_BẢN; CỘNG_HẰNG k` (heap-cons `hp,hp+k`; runtime 1458×) → `[x]→[x,x+k]`. Single-cycle stack-only. 4-substrate + unit **17/17**. bước −15.2%→−17.2% · bytecode −14.4%→−19.3%.
- **★ SIÊU-LỆNH #3 (opcode #70 `GHI_TRƯỜNG r`):** gộp `NHÂN_BẢN; TẢI_Ô r; LƯU_GIÁN` (store-field; runtime 726×) → `ram[top]=ram[r]`, giữ top. **MULTI-CYCLE RAM-to-RAM** (gvm.v: state mới `S_GHITRUONG`, đọc `ram[rel_o]`→ghi `ram[rel_s1]`; SIP viol-check; ram_ra-mux). 4-substrate + unit **19/19**. **bước −17.2%→−19.1% · bytecode −19.3%→−24.2%.** TRỌN conformance: 14/14 KHỚP BYTE + wasm 20/20 + 16/16 Verilog (heap-heavy lam_concat/lam_nhan_hdh byte-exact) + 55/55 + 63/63. *Lever tích-lũy: peephole −10.6% → CỘNG_HẰNG −15.2% → NHÂN_CỘNG_HẰNG −17.2% → GHI_TRƯỜNG −19.1%; bytecode −24.2%. Sau khi vá hạ-tầng gate-level ở #1, kể cả siêu-lệnh multi-cycle RAM cũng cài+pass gọn.*
- **⚠ SIÊU-LỆNH #4 (opcode #71 `DỊCH_CỘNG_BYTE k`) — ĐÚNG, BIÊN-LỢI NHỎ, CHẠM TRẦN:** `(top<<8)+k` gộp `DỊCH_TRÁI 8; CỘNG_HẰNG k` (dựng-hằng nhiều-byte). Single-cycle stack-only, 4-substrate, unit **23/23**, TRỌN conformance. **bước −19.1%→−19.2% (runtime 46×) · bytecode −24.2%→−24.5%.** Bài-học thành-thật: profile-dominance (NẠP+DỊCH 38.6%) ≠ redundancy giảm-được (NẠP/DỊCH bất-khả-giảm: hằng-nhỏ thật + nhân-2^k strength-reduced). **Tầng peephole/siêu-lệnh CHẠM TRẦN tự-nhiên (−19.2%/−24.5%).** Con-voi-tiếp = IR-level cross-block (compiler-only, không đụng 4 runtime).

## v0.5.7 — ★ KHỞI ĐỘNG PHA 3 (Track C): tầng tối-ưu bytecode #1 (2026-06-19)

- **★ OPTIMIZER BYTECODE conformance-safe** (`giaoc.tối_ưu_mã`, chạy trong `assemble`, cờ `BẬT_TỐI_ƯU` mặc-định ON): peephole tới điểm-bất-động với 2 luật **PROVABLY giữ ngữ-nghĩa** (giá-trị + ba-trị sáng/ẩn/tối, mọi độ-rộng-từ) — (1) **GỘP-DỊCH** `DỊCH_TRÁI a; DỊCH_TRÁI b → DỊCH_TRÁI(a+b)` (`(x<<a mod 2^W)<<b ≡ x<<(a+b) mod 2^W`); (2) **GẤP-HẰNG** `NẠP a; NẠP b; {CỘNG/TRỪ/NHÂN} → NẠP r` khi 0≤r≤255. **RÀO:** chỉ khớp lệnh LIỀN-KỀ ⇒ không xuyên `NHÃN`/`ĐỊACHỉ` (nhảy chỉ đáp vào nhãn).
- **Sửa GỐC `emit_const`:** byte-0 trong hằng-lớn → bỏ `NẠP 0; CỘNG` (sau `DỊCH_TRÁI 8` byte-thấp đã 0; accumulator là hằng SÁNG ⇒ `+0` ≡ identity). Đây là nguồn 1256 cặp dư khắp corpus.
- **Mở-rộng 13 luật provably-safe** (unit-test): + L3 `NẠP a;DỊCH b→NẠP(a≪b)` · L4 strength `NẠP 2^k;NHÂN→DỊCH_TRÁI k` · L5 `NHÂN_BẢN;BỎ→∅` · L6 `ĐỔI;ĐỔI→∅` · **DCE** (lệnh-chết sau DỪNG/NHẢY/TRẢ_VỀ_N/NÉM) · fold mở rộng (CHIA + 6 so-sánh).
- **ĐO (kiem_toi_uu.py):** bytecode **−8.1%** · **bước GVM −10.6%** (self-host `giaoc.giao` −11%, tag/heap-heavy tới −15%). **14/14 ví-dụ output KHỚP BYTE** + 13/13 unit-test luật + 5 harness Verilog gate-level byte-exact + wasm 20/20 giữ nguyên. Conformance thường-trực → audit 54→**55/55**.
- **HỘI-TỤ:** đo strength/algebraic-còn-lại = 0 trên corpus ⇒ peephole step-reduction tapped (−10.6%); luật mới giảm SIZE + tổng-quát. Lever speed kế THỰC-SỰ = **siêu-lệnh** (gộp idiom heap-cons 15-lệnh → 1 opcode, co-design GVM+Verilog+wasm) HOẶC IR-level (CSE/LICM/inline).
- **TRUNG-THỰC:** đây là **PASS #1 của Track C (khởi-động)**, KHÔNG phải compiler-native. *Con voi #1* (GIAO→native + ownership/region thay GC + SSA/regalloc) CÒN NGUYÊN — framework giờ sẵn để thêm pass (dead-code/loop-invariant/strength-reduction/inline). *Bài học: tối-ưu compiler phải PROVABLY-safe trên ba-trị (binop/shift đổi tối→sáng!) — đo bằng conformance output-khớp-byte + bước-giảm trên CẢ 4 substrate.*

## v0.5.6 — ★ Vá TOÀN-DIỆN hợp-đồng ba-trị `ẩn` + khử ReDoS regex tận gốc (2026-06-19)

- **★ HỢP-ĐỒNG `ẩn` PHỦ ĐỀU STDLIB:** review 6-agent độc-lập (3 vòng reproduce) phơi chủ-đề lỗi mạch-lạc — "input ẩn/xấu → ẩn SẠCH, không crash/lặp" KHÔNG phủ đều. Thêm guard `nếu loại(x)=="ẩn" { trả ẩn }` cho **~80 hàm** (lib_thống_kê/chuoi/duyet/đống/hàng/tổ_hợp/định_dạng/mẫu/băm/csv/url/ngày/phân_số/thập_phân + chuẩn.giao prelude + lib OS-layer). **SỬA GỐC 4 builtin map-key** `lấy/có/đặt/xoá_khoá(bản, ẩn)` → ẩn/tối/no-op (trước: crash "khoá phải số/chuỗi") — phủ toàn tầng HĐH (tiến_trình/lịch_học/dichvu/baomat/khonggian/lịch/hệ) cùng lúc.
- **★ REGEX ReDoS — KHỬ TẬN GỐC:** (1) ngân-sách-bước chống lặp-mũ `(a+)+$`; (2) cap độ-sâu **luồn qua continuation** (sửa đúng: `sâu` cũ reset khi gọi tiếp ⇒ vô-hiệu với quantifier lồng; nay cộng-dồn đúng độ-sâu thật → `((a+)+)+$` trên 3000 ký-tự → tối, KHÔNG crash đệ-quy>900); (3) **`lát()` O(n²)→O(n)** (gốc làm scan chuỗi-dài chạm 5M; `tìm_tất_cả` 1500 ký-tự nay chạy sạch).
- **Tokenizer `giao.py`:** `1.2.3` · chuỗi-không-đóng · literal nguyên >4300 chữ-số → lỗi cú-pháp SẠCH (trước: traceback Python trần / nuốt im-lặng).
- **3 tệp chốt-regression** (`kiem_ca_bien_an{,_td,_lib}.giao`) → audit **50→53/53**, ngôn-ngữ 63/63. Sweep cuối xác-nhận stdlib SẠCH.
- **Đồng-bộ trung-thực FPGA** (số post-route): Fmax 14.04 MHz · LC 3680/5280 (69%) · DSP 2/8 (TIEN_DO/CHANGELOG/README/banner gvm_core.v). `gvm_core.v` banner sửa "yosys CHƯA cài"→đã-cài.
- **★ MATCHER REGEX ITERATIVE (khử giới-hạn cuối):** lượng-từ node ĐƠN-KÝ (`a*`/`\d+`/`.*`/`[a-z]+`/`a+$`) → fast-path GOM THAM-LAM bằng VÒNG (độ-sâu O(1) theo độ-dài match) rồi backtrack → khớp ĐÚNG input DÀI tuỳ-ý (trước >~300 ký-tự trả tối-SAI). Catastrophic lồng `(a+)+$`+đuôi-sai vẫn → tối ~1s (budget chặn lặp-mũ).
- **★ TỐI-ƯU ĐỘ-PHỨC-TẠP O(n²)→O(n)** (agent khảo-sát + ĐO thật trên n tăng dần): `lát` O(n²)→O(n) · `duy_nhất`/`lib_tập`(hợp/giao/hiệu/con_của/rời_nhau)/`chuẩn_tập` (chứa-scan→`bản` O(1)) · `mốt` (vòng-lồng→bản-đếm) · `nhóm_theo`+json/csv/base64 (ghép-copy→`gom` O(1)) · **heap pairing `gộp_đống` `thêm`-copy→cons-prepend O(1)** (heapsort O(n²)→O(n log n), GIỮ persistence) · chuẩn.giao `đếm_nếu`/`γ_các_tác_tử`/`các_σ`/`ensemble_γ` (đệ-quy-đuôi→vòng gom). Trước chạm-trần 5M ở n~800-2000; nay tuyến-tính tới n=8000+. **PERF-GUARD** `kiem_phuc_tap.giao` (revert→rớt) → audit **54/54**. *Mô-hình chi-phí GIAO: list hàm-thuần `ghép/thêm/đuôi`=O(n) copy · `gom`=O(1) · `bản`=O(1) · `chuỗi +`=O(n).*
- **Giới-hạn còn lại (tài-liệu-hoá):** bộ-đếm 5M TÍCH-LŨY toàn-chương-trình (không reset/lời-gọi) · quantifier LỒNG phức `(ab)+`/`(a|b)*` trên input siêu-dài vẫn dùng đường đệ-quy có-cap (suy-biến êm). *Bài học: demo XANH che lỗ-guard + O(n²) ẩn; idiom đúng ở vài chỗ phải nhân ra TOÀN bộ, kể cả builtin lõi.*

## v0.5.5 — ★ Pipeline F-op + CHIA ⇒ bitstream ĐẠT 12 MHz (clock onboard iCEBreaker) (2026-06-19)

- **★ TIMING-CLOSURE 12 MHz:** Fmax **4.31 → 14.04 MHz** (post-route, `hw/fpga/nextpnr.log` dòng 617; PASS @12MHz). Bitstream `hw/fpga/gvm_fpga.bin` (104.090 byte) chạy được clock 12 MHz onboard iCEBreaker (không cần clock-divide). LC **3680/5280 (69%)** · BRAM 6/30 · DSP 2/8. *(Số CHỐT từ log post-route; các con số 13.57/3647 ở dòng dưới là mốc trung-gian trước vòng pipeline cuối.)*
- **Pipeline F-op 2 tầng:** đường tới-hạn cũ = nhân 64-bit RỒI negate 64-bit trong CÙNG 1 chu kỳ (S_EXEC→S_DIV). Tách: `S_EXEC` chỉ NHÂN → đăng-ký `fprod`/`fdor_raw`; thêm `S_FOP` lấy |.| (negate) → `div_acc`/`div_dor` → S_DIV. Cắt chuỗi nhân→negate thành 2 chu-kỳ.
- **CHIA qua divider tuần-tự:** bỏ wire `chia_q` (chia 16-bit tổ-hợp = đường tới-hạn còn lại) — OP_CHIA giờ nạp `f_a64`/`f_b64` → S_FOP→S_DIV (ẩn/chia-0 vẫn 1 chu kỳ).
- **Pipeline OP_NHAN (đồng-bộ):** thêm tầng `S_MUL` (S_EXEC đăng-ký tích `nhan_r` → S_MUL ghi). **Fmax: ước-lượng pre-route 14.78 MHz → post-route CHỐT 14.04 MHz** (biên rộng hơn @12MHz; 2 DSP). 16/16 harness byte-exact. NHÂN/CHIA/F-op nay đều đa-chu-kỳ nhất-quán.
- **Nạp chip:** `openFPGALoader -b ice40_generic [-f] hw/fpga/gvm_fpga.bin` (đã kiểm tool: Apache-2.0, chính-thống, an-toàn) hoặc `iceprog`.
- **Bảo-toàn:** **16/16 harness gate-level byte-exact** (CHIA + F-op chỉ dùng trong chương-trình tuần-tự/hợp-tác → đa-chu-kỳ byte-safe). GIAO giải ảo-tưởng `fmax_dat_12mhz` (tối→sáng). *Bài học: cycle-count rẻ (harness robust) ⇒ tách combinational-dài thành nhiều-chu-kỳ là đòn tối-ưu timing an-toàn nhất.*
- **CÒN NỢ:** chỉ còn nạp chip vật-lý (`iceprog` + board).

## v0.5.4 — ★★ RA BITSTREAM iCE40 UP5K (stk_st→BRAM + nextpnr + icepack) (2026-06-19)

- **★★ MỐC: bitstream iCE40 UP5K THẬT** — `hw/fpga/gvm_fpga.bin` (104.090 byte). Flow OSS trọn: yosys `synth_ice40 -json` → **nextpnr-ice40 --up5k sg48 PASS** → `icepack`. Place&route route TRỌN: **LC 3991/5280 (75%) · BRAM 6/30 · IO 5/39 · DSP 1/8**. Thang silicon: sim✓ synth✓ fit✓ **place&route✓ bitstream✓** → nạp-chip⏳.
- **stk_st (2-bit ba-trị) → BRAM:** prefetch `stA`/`stB` song-song opA/opB + gộp đọc 1-cổng (`stst_ra`) + tách ghi DOI sang S_DOI2 → **LUT 4.726→2.980 · DFFE 983→486 · +1 BRAM**. (Cây-mux đa-cổng của stk_st chiếm ~1.700 LUT — gỡ sạch.)
- **Top-wrapper `hw/fpga/gvm_fpga.v` + `gvm_fpga.pcf`:** rút ~45 chân I/O của `gvm` xuống 5 (clk/rst_n/uart_tx/led_halt/led_act) khớp iCEBreaker; **XOR-gộp MỌI output** vào led_act để yosys GIỮ TRỌN lõi (không trim); power-on-reset 255 chu kỳ + nút.
- **Bảo-toàn:** **16/16 harness gate-level byte-exact** suốt (gồm stk_st→BRAM). 
- **CÒN NỢ:** Fmax 4.31 MHz < 12 MHz (nhân 64-bit F-op chưa pipeline → pipeline hoặc clock-divide ÷4); nạp chip vật-lý (iceprog + board). GIAO học `bitstream_ra_up5k` (sáng), `fmax_dat_12mhz` (tối: ảo-tưởng 12MHz→thực 4.31).

## v0.5.3 — ★ stack→BRAM ⇒ GVM CDFL VỪA iCE40 UP5K thật (2026-06-19)

- **★★ MỐC: toàn-bộ GVM (4-nhân OS + ba-trị + closure + try/catch + SIP + γ-scheduler) FIT iCE40 UP5K** (board iCEBreaker). `synth_ice40 -dsp` **MEM=256: 4.726 SB_LUT4 < 5.280 · 5 SB_RAM40 < 30 · 1 SB_MAC16** ⇒ vừa chip. Trước đây 23.168 LUT (vượt 4,4× — bất-khả). MEM=512: 6.532 LUT/10 BRAM, **DFFE 34.282→1.549 (−95%)**. Thang silicon: sim✓ synth✓ **FIT-chip✓** → bitstream⏳.
- **stack → BRAM đọc-đồng-bộ** (`hw/gvm.v`): máy ngăn-xếp đọc 2-cổng tổ-hợp (sp-1,sp-2) → kiến-trúc **PREFETCH operand** (S_FETCH→S_OPB→S_OPA→S_EXEC; opA=stack[sp-2], opB=stack[sp-1]); mọi opcode đọc opA/opB. +bonus `rstk_ip`/`rstk_fp`→BRAM.
- **3 hiểu-biết BRAM then-chốt** (đo bằng module cô-lập): (1) NHIỀU câu `q<=mem[..]` → yosys coi NHIỀU cổng đọc → rớt thanh-ghi ⇒ phải **gộp 1 câu đọc địa-chỉ-mux** (`stk_ra`/`ram_ra`); (2) nhiều câu GHI loại-trừ thì merge 1 cổng OK; (3) **`always @(posedge clk or posedge rst)` (async-reset) CHẶN suy BRAM** ⇒ đổi **RESET ĐỒNG-BỘ** (hành-vi giống hệt: testbench giữ rst qua cạnh clk đầu).
- **Bảo-toàn conformance:** **16/16 harness gate-level byte-exact** (chương-trình tuần-tự khớp byte; đa-nhiệm robust qua σ-replay + xen/tiến → KHÔNG re-baseline; σ demo lichhoc drift do timing nhưng thuộc-tính học giữ).
- **CÒN NỢ:** `stk_st` (2-bit) còn register-file; nextpnr→bitstream→nạp chip. GIAO học `stack_bram_vua_up5k` (sáng), giải ảo-tưởng `fpga_vua_up5k`.

## v0.5.2 — Tối-ưu FPGA iCE40 (DSP + chia-tuần-tự + ram→BRAM) + Nhánh I căn_bậc (2026-06-19)

- **★ synth_ice40 THẬT:** `hw/gvm.v` map lên primitive iCE40 (`hw/synth_ice40.ys`, MEM=64/WORD=16): 0 lỗi CHECK nhưng **23.168 SB_LUT4 ≫ UP5K 5.280 (~4×)**, 0 BRAM, 0 DSP. ⇒ "synth-được tới netlist cổng" ≠ fit/PnR/bitstream (TRUNG-THỰC: chưa nạp chip). Log `hw/synth_ice40.log`.
- **`-dsp`:** nhân 16×16 → SB_MAC16 → **23.168→17.986 LUT (−22%)**, 0 rủi-ro. Đặt mặc-định.
- **F-op chia 64-bit tổ-hợp → TUẦN-TỰ** (`S_DIV` restoring 64 vòng, dấu=XOR, ẩn/chia-0 giữ 1-chu-kỳ): bỏ 2 divider 64-bit tổ-hợp ở FNHÂN/FCHIA → **17.986→16.459 LUT**. **16/16 harness gate-level byte-exact** (59.97 ✓).
- **ram → BRAM ĐỌC-ĐỒNG-BỘ:** mọi đọc ram tổ-hợp → `ram_q <= ram[addr]` + trạng-thái-chờ (TẢI_Ô/TẢI_GIÁN/closure/S_STR/S_DS/S_CLO; `state`→[3:0], +9 state). **16/16 harness byte-exact** (chương-trình tuần-tự khớp byte; đa-nhiệm robust qua σ-replay + xen/tiến → KHÔNG re-baseline). Isolated-test xác-nhận mẫu sync-read map **2×SB_RAM40_4K ở MEM=512** = BRAM-eligible (MEM=64 chưa kích do ngưỡng size). CÒN NỢ: `stack`→BRAM (đòn cuối, cần TOS/NOS cache).
- **Nhánh I — `lib_thập_phân.căn_bậc(d,n,thang)`:** căn bậc n bằng Newton tổng-quát `y'=((n−1)y + d/y^(n−1))/n` trên decimal. Ba-trị đầy-đủ (n<1/d<0-chẵn→ẩn · d<0-lẻ→−căn(|d|) · ẩn→ẩn). ∛2=1.2599210499 (đúng), √2 khớp `căn`. Test 11 ca, **kiem_toan_bo 50/50**.
- **GIAO tự-học (MCP):** ảo-tưởng `fpga_vua_up5k` (95→32, γ=−1 tối→học), `fpga_toi_uu_dsp_divider`/`ram_bram_dong_bo`/`lib_thap_phan_can_bac` sáng. Ghi `GIAO_TRI_NHO.md`.

## v0.5.1 — Review trung-thực + yosys SYNTH gvm.v + dedup + string-format (2026-06-18)

- **★★ SILICON: yosys 0.66 TỔNG-HỢP `hw/gvm.v` (core CDFL chính) XUỐNG CỔNG** — ba-trị+γ-scheduler+SIP+4-nhân, MEM=256 → **527,948 cells generic** (AND/OR/MUX/XOR/NOT + ~13.4k DFF) + ALU NAND, **KHÔNG LỖI** (`hw/synth_gvm.ys`). "Xuống silicon" nâng: iverilog-sim ✓ → **yosys-synth-tới-cổng ✓** → bitstream ✗ → chip ✗. (Trước đây chỉ mô-phỏng.)
- **TRUNG-THỰC (vá doc):** review 2-agent độc-lập → bỏ nói-quá README `(=FPGA)`/"GÓI FPGA SẴN SÀNG NẠP" (chưa synth lúc đó); đồng-bộ `kiem_thu` 33→**63**, wasm 11→**20/20**; `hw/fpga/gvm_core.v` đánh-dấu DI-SẢN (8-bit, thiếu CDFL).
- **Nợ-CAO: phát-hiện VA-TÊN module** — `giao.py` thêm cảnh-báo khi 2 nguồn định-nghĩa-lại 1 hàm (bỏ-qua ghi-đè prelude); đổi `lib_tiến_trình.tồn_tại`→`có_tt`. Cơ-chế này **phơi + vá 2 đụng-ngầm latent THẬT**: `_là_trắng` (regex⟷chuỗi) → `_rx_trắng`; `kết_thúc` (kernel⟷lib_chuoi.endsWith qua lib_json) → `chấm_dứt`.
- **DEDUP #1:** `lib_chuoi` +`lát_chuỗi`/`chữ_số`/`chuỗi_số` → diệt trùng `lib_url`/`lib_regex`/`lib_phân_số`/`lib_thập_phân`.
- **TÁCH #2:** `lib_nhân_lõi.giao` (truy-vấn nhân dùng-chung `trạng`/`tên`/`số_sống`/`theo_trạng`) — review "60% glue" hoá ~5%, GIỮ scheduler riêng (policy×mechanism).
- **NGÔN-NGỮ #4: `lib_định_dạng.giao` (string-format)** — căn-lề/đệm-0/nhóm-phẩy + mini-printf `định_dạng(mẫu,ds)` `{:>N}`/`{:<N}`/`{:^N}`/`{:0N}`/`{:,}`+escape; vá bẫy ẩn-concat-collapse.
- Audit **48 → 50/50** (+`va-tên`, +`lib_định_dạng`). Ngôn-ngữ 63/63 · wasm 20/20.

## v0.5.0 — STDLIB trưởng-thành + tầng HĐH-GIAO + decimal siêu-việt + review-vá (2026-06-17)

> Gói đợt lớn nâng audit **29/29 → 48/48** (ngôn-ngữ 63/63). Các entry v0.4.x dưới là MỐC LỊCH-SỬ (số audit tại-thời-điểm) — KHÔNG sửa-ngược; trạng-thái mới nhất luôn ở `TIEN_DO.md`.

- **Nhánh I — stdlib mở rộng (kiểu Python/Ruby):** `lib_thống_kê` (statistics) · `lib_tổ_hợp` (itertools) · `lib_tập` (set) · `lib_phân_số` (Fraction) · `lib_thời_gian` (datetime+tz) · `lib_đống` (heapq+bisect, pairing-heap thuần-hàm) · `lib_hàng` (deque+Counter) · `lib_regex` **viết-lại AST+CPS** (`\d\w\s`·`()`·`|`·findall/sub).
- **Nhánh I — `lib_thập_phân` (decimal độ-tuỳ-ý) + SIÊU-VIỆT TRỌN VẸN:** `mũ_e/ln/luỹ_thừa_thực/lô_ga/pi/sin/cos/arctan/arcsin/arccos/sinh_hyp/cosh_hyp/tanh_hyp` — đối-chiếu mpmath khớp tới 30 chữ-số. (0.1+0.2=0.3 exact; √2/e/π@30 đúng toán-học.)
- **Nhánh II — tầng HĐH-GIAO cấp-ngôn-ngữ:** `lib_lịch` (lập-lịch ưu-tiên + IPC FIFO + chặn/đánh-thức + persistence) · `lib_tiến_trình` (bảng+vòng-đời) · `lib_hệ` (NHÂN HỢP-NHẤT) · `lib_lịch_học` (γ-scheduler biết-học, σ←σ+(ρ−σ)//4) · `lib_nhân_học` (nhân thích-nghi theo merit). `kiem_lich_hoc_silicon.py`: γ-scheduler GIAO **khớp byte** chính-sách silicon `>>2` (8/8).
- **Host-API + tự-sửa:** `tim_llm.py` thêm backend Anthropic Claude (`claude-opus-4-8`, env-gated) → `vong_tu_sua.py` **Stage 5 (LLM đề-xuất, cổng CDFL regression-safe quyết)**; `phần_cứng()` (cờ `--cho-phần-cứng`) cho planner tự-dò chip. Tất cả env/key-gated, rơi-êm khi thiếu.
- **Review-vá (kỷ-luật CDFL):** guard-biên parser (`lib_regex/json/mẫu`) · regression-safe toàn-suite · **lỗ-hổng đồng-bộ IPC `lib_hệ`** (heap không xoá-tuỳ-ý → vá `điều_phối` pop-tới-sẵn-sàng + không-hồi-sinh-chết) · **guard độ-lớn decimal** (2^50 exact). Chốt-regression vào `hdh_hệ.giao`.
- **TRUNG-THỰC (vá doc):** bỏ nói-quá `(=FPGA)`/"GÓI FPGA SẴN SÀNG NẠP" ở README — FPGA **CHƯA synth** (yosys chưa cài) và `hw/fpga/gvm_core.v` là DI-SẢN lệch core chính; đồng-bộ số liệu (kiem_thu **63**, wasm **20/20**). *"Xuống silicon" = mô-phỏng iverilog gate-level, CHƯA FPGA.*

## v0.4.8 — TỰ-SỬA Stage 4: ĐỊNH-VỊ lỗi (fault localization) (2026-06-16)

- **`vong_tu_sua.py` Stage 4** — TỰ TÌM tệp lỗi từ test-suite (KHÔNG cần chỉ đích): chạy suite → spectrum
  (`định_vị`: tệp xuất-hiện ở test-FAIL nhưng KHÔNG ở test-PASS = nghi cao nhất) → repair Stage 1-3 tệp đó.
  Verify `kiem_tu_sua_localize.py`: 2 lib (1 đúng/1 lỗi) + 2 test → định-vị ĐÚNG `_lb` (không `_la`) → vá
  `a+b`→`a*b`, file đúng KHÔNG đụng. `kiem_toan_bo` **29/29**.
- Lộ-trình tự-sửa: **Stage 1-4 ✅** (hằng/toán-tử/off-by-one/định-vị) · Stage 5 cắm-LLM ⏳ (cần API host) · Stage 6 chủ-động ⏳.

## v0.4.7 — PHẦN-MỀM GIAO thật (ghép lib) + giờ-thật-qua-capability (2026-06-16)

- **`app_baocao.giao` — PHẦN-MỀM GIAO THẬT**, GHÉP 6 thư-viện: CSV(`lib_csv`) → bản-ghi → lọc/sắp
  (`lib_duyet`+`số_chuỗi`) → thống-kê(`lib_toan`) → JSON(`lib_json`) + báo-cáo(`lib_mẫu`). Chứng minh
  stdlib DÙNG ĐƯỢC, không chỉ test rời. (lọc tuổi≥18 · sắp điểm giảm · TB=86 · đầu bảng Dung).
- **Capability `giờ` + cờ `--cho-giờ`** (giao.py): builtin `giờ_hệ()`=epoch. GIỜ là input BẤT-ĐỊNH duy-nhất
  → CHỈ qua host-capability (giữ sandbox/tất-định). **`lib_ngày_host.giao`** (soi `datetime.now`):
  `hôm_nay`/`giờ_phút_giây` qua JDN; **chưa-cấp → `ẩn`** (ba-trị), cấp → ngày thật (năm=2026).
- **`số_chuỗi`** thêm vào `lib_chuoi` (int(str), phi-số→ẩn). `kiem_toan_bo` **28/28** · ngôn-ngữ 63/63.

## v0.4.6 — builtin mã/ký_tự + base64/UTF-8 · băm(djb2) · mẫu (2026-06-16)

- **Builtin MỚI `mã`(ord)/`ký_tự`(chr)** trong thông-dịch — nền cho mã-hoá/encoding. Additive, suite 63/63.
- **`lib_base64.giao`** (soi `base64` Python): mã_hoá_b64/giải_b64 + **UTF-8 encode/decode** (base64 chuỗi
  TIẾNG VIỆT đúng). KHỚP BYTE Python (`"Xin chào GIAO"`→`WGluIGNow6BvIEdJQU8=`), round-trip Việt.
- **`lib_băm.giao`** — hash djb2 (Bernstein); khớp Python (`băm("hello")=261238937`), tất-định.
- **`lib_mẫu.giao`** (soi `str.format`): `điền("{tên}...", bản)` thay khoá; thiếu-khoá → giữ `{khoá}`.
- `kiem_toan_bo` **26/26**. *Bẫy: biến `tam` trùng alias không-dấu của từ-khoá `tâm` → đổi `b24`.*

## v0.4.5 — THƯ-VIỆN PHẦN-MỀM-THẬT: regex · csv · url + tự-sửa Stage 3 (2026-06-16)

Mở rộng stdlib bằng các lib thực-dụng (soi Python/Ruby rồi viết tương-ứng), cho mục-tiêu "HĐH có
phần-mềm thật". `kiem_toan_bo` **24/24**.

- **`lib_regex.giao`** (soi `re` Python): máy khớp BACKTRACKING — `.` `*` `+` `?` `^` `$` `[a-z]` `[^..]`.
  `khớp`(search) / `khớp_đầu`(match) → sáng/tối. 15/15 ca.
- **`lib_csv.giao`** (soi `csv` Python): `phân_tích_csv` (xử-lý ô-bọc-nháy/phẩy-trong-nháy/nháy-thoát/\r) +
  `thành_csv` (tự bọc-nháy ô chứa `,"`/xuống-dòng). Round-trip an-toàn.
- **`lib_url.giao`** (soi `urllib.parse`): `phân_tích_url` → bản{scheme,host,cổng,đường,truy_vấn} (thiếu→**ẩn**);
  `phân_tích_truy_vấn`/`thành_truy_vấn`.
- **Tự-sửa Stage 3** (`vong_tu_sua.py`): + OFF-BY-ONE (±1 hằng-số) — vá `i>4`→`i>5`, CDFL loại 15 vá sai.
  Lộ-trình `TU_SUA_LO_TRINH.md`: Stage 1-3 ✅, 4 (định-vị) / 5 (cắm-LLM) / 6 (chủ-động) ⏳.

## v0.4.4 — VÒNG TỰ-SỬA (self-repair) + JSON (2026-06-16)

Hai hướng người dùng yêu cầu: (a) vòng tự-tìm-lỗi/tự-vá THẬT, (b) thư-viện tham-chiếu Python/Ruby.
TRUNG THỰC: tự-sửa bắt đầu HẸP (rule-based) — KHÔNG phải AI tổng-quát; có lộ-trình mở-rộng tới cắm-LLM.

- **`vong_tu_sua.py` — VÒNG TỰ-SỬA có cổng CDFL** (quy trình: chạy-test → đọc-lỗi → sinh-vá → áp →
  kiểm → cổng-CDFL chỉ NHẬN nếu test tối→sáng, vá-hỏng HOÀN-TÁC). **Stage 1:** oracle-repair hằng
  (`expected E got G` → thay literal). **Stage 2:** mutation TOÁN-TỬ/SO-SÁNH (vá `x+x`→`x*x`; CDFL loại
  vá sai `x-x`). Lộ-trình 6-Stage tới cắm-LLM ở `TU_SUA_LO_TRINH.md`. Test tự-chứa `kiem_tu_sua.py`.
  *Giới-hạn khai-báo: lỗi ngoài lớp rule-based → báo "cần LLM" (Stage 5, cần host cấp API), KHÔNG vá bừa.*
- **`lib_json.giao` — JSON** (tham-chiếu `json` Python / `JSON` Ruby): `phân_tích_json` (parser đệ-quy-xuống:
  object/array/string/số-âm/thập-phân/bool/null) + `thành_json` (serialize), round-trip khớp. **Ánh xạ
  CDFL:** JSON `null` ↔ GIAO `ẩn` · `true`/`false` ↔ `sáng`/`tối`. `kiem_toan_bo` **21/21**.

## v0.4.3 — NHÂN TÍCH-HỢP XUỐNG SILICON + planner-theo-chip + sửa CHIA-số-âm (2026-06-16)

- **`hdh_full_may.giao` — nhân tích-hợp viết TẬP-CON-MÁY → chạy GATE-LEVEL.** Bản thông-dịch `hdh_full`
  dùng idiom thông-dịch-only (`gom`/`tách`/`loại`/`nối`/`cộng_hưởng`) KHÔNG biên-dịch máy. Viết lại tập-con-máy:
  namespace PHẲNG (khoá=đường-chuỗi, khỏi tách/loại), bảo-mật so-σ nhị-nguyên, dịch-vụ trạng-thái-số,
  `ghép` thay `gom`. Biên-dịch **16896 từ-lệnh GVM** → chạy iverilog **18/18 khớp byte**, dừng 414769 chu kỳ.
- **★ Sửa lỗi silicon LATENT (`OP_CHIA`/`OP_NHAN`):** `$signed(a)/$signed(b)` đặt TRONG ternary có nhánh
  unsigned (`?0:`) → Verilog ép cả biểu-thức UNSIGNED → chia-unsigned (−200/2 ra 0x7FFFFF9C thay −100).
  Chỉ lộ với SỐ ÂM (hdh.giao chỉ chia dương nên không lộ; `học_σ` chia âm → lộ). Sửa: tách wire signed
  self-determined `chia_q`/`nhan_p`. Không hồi quy (3 nhân + harness vẫn xanh).
- **`lib_trienkhai.giao` + `trien_khai.giao` + `tinh_gon.giao` — PLANNER TRIỂN-KHAI THEO CHIP** (silicon-aware):
  dò chip → cấu-hình GVM tối-ưu (WORD/nền/NT/heap/lượng-tử/khối-nóng-L2); ba-trị (specs chưa-dò → ẩn).
  i9-13900H → WORD64/WASM/16tv/heap1024Ki/qt48. Phân-tích THỪA-THÃI Windows THẬT (142 svc, 370 tt, 10.7GB
  idle) → thừa 71%/89%, bội tốc ~9x, RAM giải-phóng → 288 tác_vụ. Xác minh `kiem_trienkhai.py`: **10/10 máy
  ĐÚNG CHUẨN** (i9/Pi4/Xeon/Cortex-M/FPGA/16-bit/specs-ẩn) đối-chiếu tham-chiếu Python. `kiem_toan_bo` **19/19**.

## v0.4.2 — NHÂN HĐH-GIAO TÍCH-HỢP: 3 hệ-con vào nhân thật (2026-06-16)

- **`hdh_full.giao` — HĐH-GIAO ĐẦY ĐỦ:** mở rộng nhân hợp-tác (`examples/hdh.giao`) bằng 3 hệ-con
  tích-hợp (`lib_khonggian` + `lib_baomat` + `lib_dichvu`):
  - **Object namespace:** thiết-bị/tiến-trình gắn ở đường-dẫn, truy-vấn cuối qua `liệt_kg`.
  - **Bảo-mật γ-gated:** tiến-trình mang trust σ; ghi-tài-nguyên QUA cổng `ghi(MIỀN,σ,…)`. `người`(σ=150)
    ghi nhật_ký_hệ@HỆ → **CHẶN** (no-write-up). `xấu` cư-xử-xấu → σ HỌC tụt 200→25 → **TỰ mất quyền**.
  - **Dịch-vụ:** ổ_đĩa→tệp_hệ→mạng tự-khởi (phụ-thuộc); web sập → hồi-phục 2 lần → **CÔ-LẬP** (ổ_đĩa vẫn chạy).
  - Kết: `nhật_ký_hệ` KHÔNG bị tiến-trình-thấp giả-mạo (="sự-kiện-2"). → `kiem_toan_bo` **15/15**.
- *Ghi chú:* `nhập` chặn `..` (an-toàn) → nhân tích-hợp + lib đặt cùng thư-mục gốc.

## v0.4.1 — HĐH Nhánh II KHÉP: object-namespace + service-layer (2026-06-16)

Khép 3/3 tính-năng GIAO-OS rút từ khảo sát Windows. `kiem_toan_bo` ⇒ **14/14**.

- **`lib_khonggian.giao` — OBJECT NAMESPACE** (học Object Manager của Win: "mọi thứ là đối-tượng có-tên"):
  cây 'bản' gốc; `gắn`/`tra_kg`/`tra_trị`/`loại_của`/`có`/`liệt_kg`/`gỡ` theo ĐƯỜNG-DẪN (`/a/b/c`).
  THƯ-MỤC='bản' lồng · LÁ=[loại,giá_trị]. Tra KHÔNG-thấy → **ẩn** (ba-trị). *Bẫy cú-pháp: `tra` = alias
  không-dấu của từ-khoá `trả` → đổi tên `tra_kg`.*
- **`lib_dichvu.giao` — TẦNG DỊCH-VỤ** (học SCM của Win): vòng-đời (dừng/chạy/lỗi) + **PHỤ-THUỘC giải đệ-quy**
  + **HỒI-PHỤC N lần → CÔ-LẬP** (`báo_lỗi` ≡ fault-isolation đã chạy gate-level: dịch-vụ sập KHÔNG kéo sập hệ);
  `khởi_tự_động` (auto/manual), phụ-thuộc-hỏng → tối, chưa-đăng-ký → ẩn.
- **★ NHÁNH II KHÉP:** 3/3 tính-năng (γ-gated security + object-namespace + service-layer) — học cấu-trúc
  Windows, vượt bằng CDFL (σ liên-tục · ba-trị `ẩn` · cô-lập-fault), GIỮ TRỌN bản chất GIAO.

## v0.4.0 — HĐH: khảo sát Windows + LỚP BẢO-MẬT γ-GATED (2026-06-16)

Mở **Nhánh II (HĐH)**: học từ Windows, vượt bằng CDFL — KHÔNG mất bản chất GIAO.

- **`HOC_TU_WINDOWS.md` — khảo sát Windows 11 THẬT** (đo sống: 374 procs/811k handle · MIC Medium ·
  token 5 privileges · 298 services · VBS đang-chạy · WSL · 674k Events · scheduler boost). Map **11 cơ-chế**
  Win→GIAO-OS. Luận điểm: Win *gắn-thêm* capability/trust/sandbox lên lõi ambient+C suốt 30 năm; GIAO có
  **bẩm sinh**. GIAO hơn: γ-liên-tục thay MIC-rời-rạc · ba-trị `ẩn` (Win chỉ allow/deny) · memory-safe-kiến-tạo.
- **`lib_baomat.giao` — LỚP BẢO-MẬT γ-GATED (tính-năng GIAO-OS #1 từ khảo sát):**
  - **no-write-up LIÊN-TỤC:** mức tin-cậy σ ∈ [0..255] (thay 5 nấc MIC cứng); ghi cho phép khi σ_chủ ≥ mức_ô.
  - **BA-TRỊ:** `có_thể_ghi` → sáng (cho) / tối (chặn write-up = ảo-tưởng-quyền) / **ẩn** (tin-cậy CHƯA-SOI → fail-safe).
  - **★ σ HỌC-ĐƯỢC** (`học_σ`, thống nhất với γ-scheduler): tác_vụ cư-xử-xấu → σ tụt (200→100→50) → **TỰ MẤT
    quyền ghi ô-cao**. Windows MIC TĨNH không làm nổi — đây là an-toàn-AI động qua CDFL.
  - `tạo_miền`/`đăng_ký`/`ghi`/`đọc`/`mức_của`/`γ_truy_cập`. Test `kiem_lib_baomat.giao` (14 ca) → **12/12**.

## v0.3.9 — THƯ VIỆN CHUẨN KHÉP: NGÀY-GIỜ + IO-NĂNG-LỰC (stdlib ~100%) (2026-06-16)

Khép nhánh stdlib — 6 module trưởng thành ngang Python/Ruby, GIỮ TRỌN cốt lõi CDFL. `kiem_toan_bo` ⇒ **11/11**.

- **`lib_ngày.giao` (Date math) — THUẦN TOÁN** (Số-Ngày-Julius, không cần đồng-hồ hệ-thống):
  `năm_nhuận`/`hợp_lệ` (→ sáng/tối) · `ngày_trong_tháng` · `số_ngày`/`từ_số_ngày` (JDN ⟷ [n,t,ng]) ·
  `khoảng_ngày`/`cộng_ngày` · `thứ`/`thứ_số` (2000-01-01 = Thứ Bảy ✓) · `định_dạng` (ISO). Ngày SAI → `ẩn`.
- **`lib_io.giao` (I/O theo NĂNG LỰC)** — GIỮ object-capability MẠNH NHẤT: `đọc`/`đọc_dòng`/`tồn_tại`/`ghi`/
  `liệt`/`chạy_lệnh` chỉ GÓI builtin host-cấp, **TUYỆT ĐỐI không tự nới quyền**; thất-bại/chưa-cấp/ngoài-phạm-vi
  → `ẩn`/`tối` (không crash). Test (`--cho-đọc .`): đọc/liệt cấp → chạy; ghi/chạy chưa-cấp → tối/ẩn, **tệp KHÔNG bị tạo**.
- **★ STDLIB GIAO ~100%** (Duyệt + Chuỗi + Toán + Hash + Ngày + IO). Ba-trị (ẩn/sáng/tối) + capability-sandbox
  giữ TRỌN xuyên mọi module — trưởng thành ngang Python/Ruby mà KHÔNG đánh mất bản chất GIAO.

## v0.3.8 — THƯ VIỆN CHUẨN: HASH/BẢN (stdlib ~80%) (2026-06-16)

- **`lib_bản.giao` (Hash/dict, 19 hàm) — KHÔNG-phá-huỷ** (trả `bản` mới, giữ gốc nguyên):
  `từ_cặp`/`cặp` · `gộp_bản` (b thắng)/`gộp_với` (f hoà-giải trùng-khoá) · `biến_đổi_giá_trị`/`biến_đổi_khoá` ·
  `lọc_bản` · `đảo_bản` (invert) · `lấy_hoặc` (fetch+default) · `có_giá_trị` · `khoá_của` (reverse lookup) ·
  `đếm_giá_trị` (tally/Counter) · `mỗi_cặp`.
- **GIỮ CỐT LÕI:** ba-trị — `lấy_khoá` thiếu-khoá → `ẩn` (sẵn ở builtin) · `khoá_của` không-thấy → `ẩn` ·
  `có_giá_trị` → sáng/tối. Test `kiem_lib_bản.giao` (19 ca) → `kiem_toan_bo` **9/9**.
- stdlib GIAO nay **~80%** (Duyệt + Chuỗi + Toán + Hash); còn IO/ngày-giờ theo năng lực.

## v0.3.7 — THƯ VIỆN CHUẨN: CHUỖI + TOÁN (stdlib ~60%) (2026-06-16)

Nối tiếp nhánh ngôn ngữ — thêm String + Math, GIỮ cốt lõi CDFL. `kiem_toan_bo` ⇒ **8/8**.

- **`lib_chuoi.giao` (String, 16 hàm):** `hoa`/`thường`/`hoa_đầu` (TRA-BẢNG-chữ-cái — KHÔNG cần builtin
  mã↔ký-tự, tự-thân) · `đảo_chuỗi`/`chuỗi_từ`/`ký_tự_ds` · `thay`/`số_lần` (dựng trên builtin `tách`+`nối`) ·
  `chứa_chuỗi` · `vị_trí` (không-thấy → **`ẩn`**) · `bắt_đầu`/`kết_thúc` · `cắt_lề` · `lặp_lại`.
- **`lib_toan.giao` (Math):** `sàn`/`trần`/`làm_tròn` · `dấu`/`kẹp` · `căn` (Newton — số-ÂM → **`ẩn`**,
  chưa-biết trong số thực) · `ưcln`/`bcnn` · `trung_bình` (rỗng → **`ẩn`**) · `nguyên_tố` (→ sáng/tối).
- **GIỮ CỐT LÕI:** ba-trị xuyên suốt (ẩn cho không-xác-định/không-thấy, sáng/tối cho vị-từ), idiom Việt,
  tự-thân (trên builtin + `chuẩn.giao` + `lib_duyet`). Test `kiem_lib_chuoi.giao` (16) + `kiem_lib_toan.giao` (22).

## v0.3.6 — THƯ VIỆN CHUẨN: DUYỆT (Enumerable kiểu Python/Ruby) (2026-06-16)

Khởi động NHÁNH NGÔN NGỮ: đưa GIAO tới độ trưởng thành thư-viện ngang Python/Ruby — GIỮ cốt lõi CDFL.

- **`lib_duyet.giao` — 25 hàm Enumerable**, idiom Việt, dựng TỰ-THÂN trên builtin+`chuẩn.giao`, ITERATIVE:
  `sắp_xếp`/`sắp_theo` (merge sort ổn định) · `duy_nhất` · `phẳng`/`gộp_bản_đồ` · `khoá_kéo` (zip) ·
  `phân_đôi` · `nhóm_theo` (→ `bản`/Hash) · `lấy_khi`/`bỏ_khi`/`bỏ_n`/`lát` · `bất_kỳ`/`mọi`/`không_ai` ·
  `tìm_thấy` · `chỉ_số` · `lớn_nhất_theo`/`nhỏ_nhất_theo` · `tổng_theo` · `gọn` · `đếm_thoả`.
- **GIỮ CỐT LÕI GIAO (không đánh đổi lấy tiện lợi):** BA-TRỊ — `tìm_thấy`/`chỉ_số` không-thấy trả `ẩn`
  (chưa-biết, KHÔNG bịa/lỗi) · `gọn` BỎ phần tử ẩn · predicate trả sáng/tối. Tên thuần Việt.
- Test `kiem_lib_duyet.giao` (25 ca, có kiểm ba-trị `ẩn`) → hạng mục mới trong `kiem_toan_bo.py` ⇒ **6/6**.
- *Ghi chú:* GIAO không có toán-tử `và`/`hoặc`/`không` → điều kiện ghép viết bằng `nếu` lồng.

## v0.3.5 — BA-TRỊ `tối` (cộng hưởng γ) chạy GATE-LEVEL (2026-06-16)

Hoàn tất ô ba-trị TRỌN VẸN ở silicon: thêm tầng tác-tử CDFL sinh `tối`. Additive — suite 5/5 nguyên.

### Phần cứng (`hw/gvm.v`)
- **`SO_SÁNH`(13) — CỘNG HƯỞNG γ:** a=niềm-tin (stack[sp-2]), b=thực-tại (stack[sp-1]).
  γ = 1 − 2·|b−a|/max(|b|,1) ⇒ STATE chỉ cần SO INTEGER (khỏi chia tốn DSP): `2d<scale`→sáng ·
  `>`→**tối** · `=`→ẩn (val=niềm-tin); input-ẩn→ẩn (val 0). Khớp `gvm_may.resonance`.
- **`NHẢY_SÁNG`(16)/`NHẢY_TỐI`(17)/`NHẢY_ẨN`(18):** rẽ theo TRẠNG-THÁI ba-trị (thay cờ ZF/CF
  bằng cộng-hưởng — rẽ-theo-ý-nghĩa, không rẽ-theo-bit).
- Cổng `out_state` (0 ẩn·1 sáng·2 tối) phơi trạng-thái ô khi RỌI.

### Verify
- `hw/lam_toi.py` (hand-assembled — compiler GIAO KHÔNG phát opcode tác-tử): các cặp (niềm-tin,
  thực-tại) → SO_SÁNH → `[(sáng,10),(tối,10),(ẩn,10),(sáng,50),(tối,10)]` + NHẢY_TỐI rẽ đúng (222).
  **Khớp BYTE** GVM phần mềm. ⇒ cơ chế LƯƠNG-TÂM của GIAO (đo ảo-tưởng = `tối`) nay chạy ở CỔNG LOGIC.

## v0.3.4 — NHÂN CÔ-LẬP-FAULT gate-level → TRỌN BỘ BA NHÂN HĐH (2026-06-16)

Hoàn tất bộ ba nhân HĐH chạy gate-level. Additive — suite 5/5 + 9 harness cũ giữ nguyên.

### Phần cứng (`hw/gvm.v`)
- **Ngăn-xếp-handler PER-TASK** (`t_hsp[i]`, vùng `[i*8, i*8+8)`): mỗi tiến trình có try/bắt RIÊNG,
  lưu/khôi phục khi chuyển ngữ cảnh ⇒ thử/bắt cô-lập đúng kể cả khi bị preempt giữa vùng thử.
  Empty-check NÉM theo `hbase = sched_on ? cur*8 : 0`.
- **Cô-lập-fault phần cứng** (`t_dead[i]`): uncaught-NÉM dưới scheduler → đặt `t_dead[cur]`, vẫn HỌC σ,
  chuyển sang task SỐNG khác (`gsel_fault` loại `cur`), **CPU KHÔNG halt** (một tiến trình sập không kéo
  sập hệ); mọi task chết → DỪNG. `gsel_live` (argmax bỏ-qua-chết) ≡ `gsel` khi không có chết → preempt
  byte-match không đổi. `hsp` nới 16-bit.

### Nhân chạy gate-level
- **★ `lam_nhan_fault.py` — `hdh_fault.giao` (bytecode THẬT).** 3 tiến trình dưới γ-scheduler silicon:
  tt#0(khoẻ) đếm+XUẤT liên tục; tt#1(tự_chữa) lỗi mỗi lượt nhưng thử/bắt phục hồi (XUẤT 900); tt#2(hỏng)
  NÉM chưa-bắt → **nhân CÔ LẬP** (`dut.t_dead[2]=1` sau 1 XUẤT), tt#0/tt#1 chạy tiếp, **hệ KHÔNG sập**.
  Khớp phần mềm (`sched_lỗi=[None,None,1]`). ⇒ **TRỌN BỘ BA nhân HĐH (hợp-tác/preemptive/fault) gate-level.**

## v0.3.3 — CẢ HAI NHÂN HĐH chạy GATE-LEVEL (preemptive + hợp-tác) + THỬ/BẮT (2026-06-16)

Đưa NHÂN HĐH thật (cả preemptive lẫn hợp-tác đầy đủ 14490 từ) xuống cổng logic. Additive — suite 5/5 giữ nguyên.

### Phần cứng (`hw/gvm.v`)
- **THỬ/BẮT đầy đủ:** `BẮT_ĐẦU_THỬ`(62)/`HẾT_THỬ`(63) + `NÉM`(64) GỠ-CUỘN. Ngăn-xếp-handler
  (`h_ip`/`h_sp`/`h_fp`/`h_rsp`, sâu 32): vào 'thử' lưu sp/fp/rsp; `NÉM` khôi phục chúng, trao
  trị-lỗi (sáng) cho nhánh 'bắt', nhảy handler; rỗng handler → DỪNG (≡ fault phần mềm).
- **Con trỏ ngăn xếp 8-bit → 16-bit** (`sp`/`fp`/`rsp`/`rstk_fp`/`clo_base`/`t_sp..t_rsp`/`h_*`):
  nhân hợp-tác gộp toán-hạng+khung → đỉnh có thể >255. (Không phá harness nào.)
- **Cổng phơi vết lập-lịch:** `sched_evt` (xung khi chuyển ngữ cảnh γ) + `sched_cur`/`sched_rho`
  (tiến trình outgoing + ρ) → để đối chiếu CHẶT chính sách phần cứng ↔ phần mềm.

### Nhân chạy gate-level
- **★ `lam_nhan_preempt.py` — NHÂN PREEMPTIVE (`hdh_preempt.giao`, bytecode THẬT) trên γ-scheduler
  SILICON.** Tiến trình = HÀM (khung/biến-cục-bộ per-task); `xuất(i)` = opcode XUẤT. 456 lần CHUYỂN
  NGỮ CẢNH phần cứng trong 6000 chu kỳ. Đối chiếu CHẶT: replay vết quyết-định phần cứng (456 lần)
  qua `GVM.γ_cập_nhật` (chính sách phần mềm) cho σ=**[99,3,99] KHỚP BYTE**. tt#0(đếm+1)/tt#2(đếm+10)
  hữu-ích (σ=99, 102 XUẤT mỗi cái); tt#1(spin) σ=3, **0 XUẤT — đói CPU**. ⇒ nhân preemptive học-throttle
  chạy trên CỔNG LOGIC.
- **`lam_verilog_thubat.py` — THỬ/BẮT (`thu_bat_mai_gvm.giao`).** Chỉ-mục danh-sách ngoài-phạm-vi →
  NÉM gỡ-cuộn → 'bắt' → phục hồi (kể cả thử/bắt LỒNG trong `mãi`). Khớp byte `[7,22,0,42,100,10]`.
- **★ `lam_nhan_hdh.py` — NHÂN HỢP-TÁC `hdh.giao` (14490 từ) chạy GATE-LEVEL ĐẦY ĐỦ: 24/24 KHỚP
  BYTE, dừng sau 400071 chu kỳ.** Boot → sinh 4 tiến trình (đếm-A/fib-B/đếm-C/giám-sát) → interleave
  hợp-tác → **cổng CDFL chặn syscall 'format ổ đĩa' bất-khả-hồi (xin phép, không tự chạy)** → DỪNG.
  Dùng MỌI opcode đã xuống silicon (closure, chuỗi, ẩn ba-trị, khung, thử/bắt).

### Sửa lỗi GỐC RỄ (đường heap lớn)
- **Địa chỉ relocation cắt 12-bit → nới 16-bit.** `rel_o`/`rel_s1`/`rel_s2` (cho `TẢI_GIÁN`/`LƯU_GIÁN`/
  `TẢI_Ô`/`LƯU_Ô`) khai báo `[11:0]` (di sản SIP vùng-128) ⇒ **địa chỉ heap ≥ 4096 wrap mod 4096** →
  đọc/ghi nhầm ô. Nhân hợp-tác vỡ ở heap~4727 (con-trỏ-thẻ thành bit31). Nới `[15:0]` (SIP vẫn đúng:
  địa-chỉ-ảo nhỏ). Repro `examples/heap32_concat.giao` (nối chuỗi tích lũy, heap ~15000) + `hw/lam_concat.py`
  (vỡ ở vòng 32 = lúc heap qua 4096 trước khi sửa; 60/60 khớp sau sửa). SIP/preempt không hồi quy.

## v0.3.2 — RÀO BA-TRỊ `ẩn` XUỐNG SILICON (2026-06-16)

Gỡ **rào lớn nhất** của đường gate-level: ô NGĂN XẾP Verilog nay **mang trạng-thái ba-trị**
(ẩn/sáng/tối). Nhân HĐH dùng `ẩn` (hàm rơi-khỏi-thân, `xuất`) ⇒ đây là điều kiện để chạy nhân
ĐẦY ĐỦ gate-level. Additive — suite vẫn 5/5; 4 harness cũ giữ nguyên.

### Phát hiện then chốt (đo từ GVM phần mềm)
- Trạng-thái (`st`) sống **chỉ trên ngăn xếp toán hạng**: `LƯU_Ô/TẢI_Ô/LƯU_GIÁN/TẢI_GIÁN` chỉ
  chuyển `val` (tải lại = sáng); tham số đi qua `pstack` (raw) → `THAM_I` luôn sáng. Nên Verilog
  **chỉ cần 1 mảng cờ song song ngăn xếp**, KHÔNG cần cờ cho RAM/heap → rẻ và khít phần mềm.
- Nhân `hdh*` chỉ dùng `ẨN` (đẩy ẩn), KHÔNG dùng `NHẢY_SÁNG/TỐI`/`SO_SÁNH` ⇒ ba-trị thực-dụng = ẩn↔sáng.

### Phần cứng (`hw/gvm.v`)
- **`reg [1:0] stk_st [0:MEM-1]`** — cờ ẩn(00)/sáng(01)/tối(10) cho mỗi ô ngăn xếp.
- **`ẨN`(2)** đẩy ô ẩn (val=0). **`XUẤT`(49)** MMIO console: `out_kind=7` + cổng mới **`out_proc`**=cur.
- LAN TRUYỀN ẩn: `CỘNG/TRỪ/NHÂN/CHIA/FNHÂN/FCHIA` chạm ẩn → ẩn (val ép 0 ≡ `ANCELL`); `FCHIA` chia-0 → ẩn.
- Giữ/chuyển cờ: `THAM_I`→sáng (≡ pstack); `TRẢ_VỀ_N` chuyển cờ trả-về (hàm rơi-thân → ẩn);
  `NHÂN_BẢN`/`ĐỔI` chuyển cờ; `NẠP`/`TẢI_Ô`/`TẢI_GIÁN`/so-sánh → sáng.
- Tiêu thụ ẩn: `NHẢY_NẾU_0(_X)` coi ẩn ≠ 0 (không nhánh); `RỌI`/`RỌI_AUTO`/`RỌI_THỰC` gặp ẩn → `out_kind=6`.
- `out_kind [2:0]` nay đủ 8 trị: 0 số · 1 ký-tự · 2 hết-chuỗi · 3 số-thực · 4 ds-phần-tử · 5 ds-hết · 6 ẩn · 7 console.

### Ví dụ + harness
- `examples/heap32_an.giao` — 4 nguồn ẩn (literal `ẩn`, hàm rơi-khỏi-thân `trống(x){}`, lan-truyền
  `trống(1)+7`, `5.0/0.0` chia-0) chạy SONG SONG với số sáng (`3+4`=7, `2.5+1.5`=4).
- `hw/lam_verilog32_an.py` — harness thứ **5/5**: **khớp byte** `[('ẩn',)×4, ('số',7), ('thực','4')]`
  giữa GVM phần mềm và Verilog gate-level. `kiem_toan_bo.py`: thêm `heap32_an` (nay 51 thông dịch · 23 máy).
- *Còn TODO:* `SO_SÁNH`/`GIAO`/`HỌC` (sinh `tối` qua cộng-hưởng γ — tầng tác-tử CDFL); chạy nhân
  `hdh_preempt`/`hdh_fault` đầy đủ gate-level (đã hết rào ẩn/XUẤT; còn căn lượng-tử scheduler).

## v0.3.1 — Số thực + danh sách XUỐNG SILICON (2026-06-16)

Mở rộng lõi GVM 32-bit ở Verilog `hw/gvm.v` để chạy thêm chương trình GIAO thật **gate-level**
(iverilog), đối chiếu BYTE với GVM phần mềm. Additive — suite vẫn 5/5; 3 harness cũ giữ nguyên.

### Phần cứng (`hw/gvm.v`) — opcode mới
- **`FNHÂN`(59) / `FCHIA`(60)** — số thực ĐIỂM-CỐ-ĐỊNH ×10000. Trung gian **64-bit có dấu**
  (sign-extend → `$signed` 64-bit, suy ra DSP); `/` của Verilog **cắt-về-0** ⇒ khít `fbin()`
  Python và i64 wasm. `FNHÂN=(a·b)/10000`, `FCHIA=(a·10000)/b` (b=0 → 0).
- **`RỌI_THỰC`(61)** — phát trị ×10000 thô + `out_kind=3`; harness/UART định dạng thập phân
  (`fmt_fixed`). **`RỌI_DS`(48)** — trạng thái mới `S_DS` duyệt cons-cell trên heap, in từng số
  (`out_kind=4`) rồi xung HẾT-DS (`out_kind=5`); **PEEK** (không pop con trỏ, để `BỎ` dọn sau).
- **`NÉM`(64)** bản TỐI THIỂU: chưa-bắt → DỪNG (≡ fault phần mềm khi rỗng handler). try/catch
  ĐẦY ĐỦ (`BẮT_ĐẦU_THỬ`/`HẾT_THỬ` + gỡ-cuộn) vẫn là TODO.
- Cổng xuất: `out_kind` mở `[1:0]`→`[2:0]` (thêm 3/4/5); thêm `out_proc` (nhãn tiến trình).
  `state` mở `[1:0]`→`[2:0]` cho `S_DS`.

### Ví dụ + harness
- `examples/heap32_io.giao` — GIAO thật: `1.5+2.25`, `3.142*2.0`, `10.0/4.0`, `2.5-0.75`,
  `19.99*3.0` (=**59.97**, vượt 16-bit ⇒ buộc dùng đường DSP 64-bit), `rọi_ds([10,20,30])`.
  Chạy SẠCH cả thông dịch (`giao.py`), máy (`giaoc.py`→GVM), và gate-level.
- `hw/lam_verilog32_io.py` — harness thứ **4/4**: biên dịch → sinh `prog32io.hex`/`gvm_p32io.v`/
  `io32_tb.v` → iverilog → ghép luồng `out_kind` → **TRÙNG KHỚP byte** với GVM phần mềm
  `[('thực','3.75'),('thực','6.284'),('thực','2.5'),('thực','1.75'),('thực','59.97'),('ds',[10,20,30])]`.
- `kiem_toan_bo.py`: thêm `heap32_io` vào danh sách máy (nay 50 thông dịch · 22 máy).

## v0.3 — "Khép lộ trình + Polyglot + Capability" (2026-06)

Bản này (a) khép nốt 4 nhánh lộ trình còn dở của v0.2, (b) mở GIAO ra **mọi ngôn ngữ**
qua cầu nối/MCP, và (c) cho GIAO **chạm thực tại có kiểm soát** bằng I/O theo năng lực —
mà KHÔNG mất tính sandbox bẩm sinh.

### ★ Ngôn ngữ (giao.py)
- **Vòng lặp LIÊN TỤC thật**: thêm `mãi { … }` (chạy không đếm trước) và `dừng` (thoát
  vòng `mãi`/`lặp`). Tác tử sống học mãi, không viên mãn toàn cục (tiên đề 12).
- **★ Vòng DUYỆT `lặp <x> trong <ds> { … }`** — gỡ TRẦN đệ quy. Trước đây mọi duyệt danh
  sách/chuỗi đều đệ quy ⇒ đụng `MAX_DEPTH=900` (vd `tách` một tệp cỡ vừa là TRÀN ngăn xếp).
  Nay duyệt dữ liệu lớn không đệ quy. Thư viện chuẩn (`bản_đồ`/`lọc`/`gấp`/`mỗi`/`dải_từ`/
  `đảo`/`chứa`/`lấy_n`/`tách`/`nối`/`argmax`/`max_ds`/`min_ds`) viết lại ITERATIVE — API
  không đổi, nhưng xử lý được dữ liệu thật (đã chứng minh: `tách` tệp 8333 ký tự → 215 dòng).
  `'trong'` là từ khoá NGỮ CẢNH (không phá biến tên trùng).
- **★ BẢN (map/record)** — kiểu giá trị MỚI: tham chiếu, mutable, tra cứu O(1) (trước chỉ có
  danh-sách-cặp O(n)). Builtin `bản()` · `đặt_khoá(m,k,v)` · `lấy_khoá(m,k)` · `có_khoá(m,k)` ·
  `xoá_khoá(m,k)` · `khoá(m)` · `giá_trị(m)`; index `m[khoá]`; `dài(m)`; `lặp k trong m` duyệt
  khoá; `loại`→`"bản"`. Khoá: số/chuỗi/trị (khoá sai → lỗi sạch). **Thiếu khoá → `ẩn`** (đúng
  ba-trị, không crash/không bịa). Ví dụ `examples/ban_map.giao` (đếm tần suất từ).
- **★ MODULE `nhập "tệp.giao"`** — nạp định nghĩa từ tệp khác (include-style, scope toàn cục).
  AN TOÀN: chỉ `.giao` TRONG cây thư mục dự án (`base_dir` = thư mục tệp chính; chống thoát
  `..`/đường tuyệt đối); idempotent (nạp lại bỏ qua); chống vòng nhập. Khác I/O runtime (vẫn
  capability-gated) — `nhập` là cơ chế cấu trúc nguồn lúc nạp. Vd `examples/dung_module.giao`.
- **★ CLOSURE TỪ VỰNG (lexical scope)** — sửa lỗi *dynamic scope*. Trước đây biến tự do trong
  closure giải析 theo NGĂN XẾP GỌI (nơi gọi) ⇒ bẫy: cùng tên biến ở hàm gọi sẽ "rò" vào closure;
  closure trả-về-rồi-gọi-sau có thể sai/hỏng. Nay closure BẮT MÔI TRƯỜNG NƠI ĐỊNH NGHĨA (chuỗi
  `Env` cha-con). Curry chạy đúng: `thêm(5)`/`thêm(10)` giữ `n` riêng → 105/110. Refactor
  `frames` (list) → `env` (chuỗi lexical). API/đệ quy không đổi; 58/58 test.
- **★ TỐI ƯU THUẬT TOÁN — stdlib từ O(n²) → O(n)**. Builder iterative trước dùng `ghép(kq,[x])`
  (copy mỗi vòng) ⇒ O(n²). Thêm builtin **`gom(ds, x)`** (chèn TẠI CHỖ, O(1) phân bổ); `bản_đồ`/
  `lọc`/`dải_từ`/`lấy_n` dùng `gom` ⇒ O(n). `đảo`/`nối`/`tách` chuyển thành **builtin gốc**
  (O(n), tránh O(n²) nối/duyệt chuỗi). Đo: `bản_đồ`+`đảo`+`nối`+`tách` trên 5000/2000 phần tử
  chạy ~0.14s (trước đây bậc hai). API không đổi; 55/55 test + mọi ví dụ stdlib giữ nguyên.
- **Thế giới TỰ TRÔI**: thêm `trôi <ô> = <bt>` (đăng ký động học riêng của thế giới) và
  `trôi` (một nhịp thời gian áp mọi luật). Nhờ đó **DE_T** (tri thức cũ trôi) sinh ra tự
  thân, không phải tự tay sửa `vật` mỗi vòng.
- **DE bốn mặt — truy vấn cấu trúc**: refactor `de_cau_truc()` → một nguồn sự thật cho cả
  bản chữ lẫn dữ liệu (DE_X/DE_T/DE_IF/DE_MF + `hợp`). Cả bốn mặt chồng nhau đúng tiên đề.
- **`rọi_ds`**: in một danh sách số (mỗi phần tử một dòng) — dùng cả ở thông dịch lẫn máy.
- **★ I/O THEO NĂNG LỰC (object-capability)** — biến GIAO từ *chỉ-suy-luận* thành
  *có-thể-hành-động-có-kiểm-soát*:
  - Builtin `đọc_tệp` · `liệt_kê` · `chạy` · `ghi_tệp` **không tồn tại** trừ khi host cấp
    quyền tường minh kèm **phạm vi** (`rt.cấp_quyền("đọc_tệp", gốc=[…])`). Chương trình
    GIAO **không tự nới** quyền.
  - Cấp qua **CLI**: `--cho-đọc DIR`, `--cho-chạy "lệnh"`, `--cho-ghi DIR`.
  - Chống thoát thư mục (`realpath` + kiểm gốc); lệnh chạy KHÔNG qua shell + allowlist +
    timeout. Ngoài phạm vi → **lỗi sạch** (bắt được); I/O hỏng → **`ẩn`**.
  - Mặc định KHÔNG quyền ⇒ **sandbox tuyệt đối như trước** (bất biến an toàn).

### ★ Thư viện chuẩn (chuẩn.giao)
- **σ/Φ ensemble** thành hàm chuẩn: `qua_Φ`, `ensemble_γ`, `Φ_tốt_nhất`, `de_if_Φ`. Cùng
  niềm tin σ soi qua nhiều thấu kính Φ → γ khác nhau; thiếu Φ phù hợp ⇒ DE_IF bật sáng.

### ★ Trình biên dịch & máy (giaoc.py, gvm_may.py)
- **Biên dịch TRỌN `giaoc.giao` xuống GVM** — trình-biên-dịch-viết-bằng-GIAO nay chạy như
  mã máy, tự sinh đúng từng-từ 17 từ-lệnh (khớp tham chiếu thông dịch). Cần các primitive mới:
  - **ABI gắn THẺ 32-bit** (bit 30 đánh dấu con-trỏ-danh-sách) cho `là_số`/`là_ds` — **BẬT
    CÓ ĐIỀU KIỆN** qua `uses_tag()`: chỉ khi chương trình thực sự dùng `là_số`/`là_ds`;
    còn lại giữ **scalar 16-bit y hệt cũ** (Verilog/FPGA & mọi ví dụ máy cũ KHÔNG đổi).
  - **`==`/`!=` CẤU TRÚC** (so chuỗi/danh sách lồng theo nội dung, đệ quy trên máy).
  - **`+` ĐA HÌNH** (số+số cộng; chuỗi+số nối — số tự hoá-chuỗi, để sinh nhãn nhảy).
  - Opcode máy mới: `RỌI_DS` (in danh sách số); `RỌI_CHUỖI` gỡ thẻ; GVM lưu `last_list`.
- **`chay_giaoc_may.py`**: harness 3 tầng — compiler-trên-máy → bytecode nó sinh → vòng hội tụ.
- **★ CLOSURE / hàm hạng nhất xuống máy (mốc 3a — thu hẹp RANH GIỚI)** — `hàm(x){…}` nay
  BIÊN DỊCH được, không còn chỉ-thông-dịch. closure = khối heap `[code_addr, ncap, bắt…]`;
  opcode mới `GỌI_CLOSURE`(58) dựng khung `[bắt…, đối…]` rồi nhảy. Compiler phân tích
  biến-tự-do chọn đúng ô THAM_I cần bắt (`current_params`→`frame_names`=[bắt…]+[tham số…]).
  Hỗ trợ: bắt-biến-lexical, hàm bậc cao (`áp(f,x){trả f(x)}`), gọi tức thì (IIFE), lam lồng
  nhiều tầng. Mirror đủ 3 substrate (`gvm_may.py`/`wasm/gvm.ts`); ví dụ `examples/closure_gvm.giao`
  (15·42·103·13). Đối chiếu wasm⟷Python **byte-for-byte 12/12** (gồm gem `giaoc.giao` 8357 từ).
- **★ BẢN / map-record xuống máy (mốc 3b — thu hẹp RANH GIỚI tiếp)** — kiểu **THAM CHIẾU
  mutable** đầu tiên trên máy. Biểu diễn: con trỏ (có thẻ) tới Ô-ĐẦU mutable → danh-sách-liên-kết
  node `[khoá, giá, kế]`. `đặt_khoá` chèn-đầu O(1) (sửa khoá cũ ⇒ vá val tại chỗ, giữ vị trí);
  khoá so **cấu trúc** qua `__bằng` (khoá chuỗi hoạt động). Builtin biên dịch được: `bản()` ·
  `đặt_khoá` · `lấy_khoá` · `có_khoá` · `xoá_khoá` (gỡ liên kết) · `khoá` · `giá_trị` · `dài(bản)` ·
  index `m[k]`. **Thiếu khoá → `ẩn`** (đúng ba-trị, không crash). Tham chiếu thật: mọi nơi giữ
  con trỏ thấy cùng cập nhật (ô-đầu/node bị MUTATE). **KHÔNG cần opcode mới** — chỉ luật biên dịch
  + 8 hàm trợ giúp `@__map_*` dùng lệnh sẵn có ⇒ `wasm/gvm.ts` KHÔNG đổi. Map tự bật ABI thẻ
  32-bit (cần `__bằng`). Ví dụ `examples/ban_gvm.giao`; wasm⟷Python **byte-for-byte 13/13**.
- **★ `lặp x trong` + `dừng` xuống máy (mốc 3c — vòng DUYỆT, gỡ trần đệ quy ở tầng máy)** —
  duyệt cons-list bằng car/cdr (KHÔNG đệ quy): `cur=head; while cur≠NIL { x=car; cur=cdr; thân }`.
  Duyệt được **danh sách · chuỗi · bản** (bản → duyệt KHOÁ qua `@__map_khoá`); **vòng lồng** +
  **`dừng`** thoát vòng gần nhất (ngăn-xếp-nhãn-kết-thúc). Duyệt CHUỖI bọc mã→chuỗi-1-ký-tự để
  khớp thông dịch. KHÔNG thêm opcode (tái dùng `_car`/`_cdr_into`) ⇒ `wasm/gvm.ts` KHÔNG đổi.
  Ví dụ `examples/lap_trong_gvm.giao` (150·4·6·G/I/A/O·9·90); wasm⟷Python **byte-for-byte 14/14**.
- **★ SỐ THỰC xuống máy (mốc 3d — mắt xích kỹ thuật khó nhất)** — GVM là máy SỐ NGUYÊN, KHÔNG
  FPU. Số thực biểu diễn bằng **điểm-cố-định thập phân ×10000** (`x ≈ round(x·10000)`), mang như
  số nguyên thường; **kiểu suy ở compile-time** (không cần thẻ runtime → KHÔNG đụng ABI). `+`/`−`/
  so-sánh dùng lệnh nguyên sẵn có (cùng thang); thêm 3 opcode DSP-nguyên: **`FNHÂN`** ((a·b)/10000)
  · **`FCHIA`** ((a·10000)/b) — trung gian **64-bit** (Python int / AS `i64`) nên wasm⟷Python trùng
  khít · **`RỌI_THỰC`** (in thập phân ≤4 chữ số lẻ, thuật toán số-nguyên thuần). Số nguyên trộn số
  thực được nhân-thang tự động. `0.1+0.2` cho ĐÚNG `0.3` (điểm-cố-định không lệch IEEE). Mirror đủ
  `gvm_may.py`+`wasm/gvm.ts`; ví dụ `examples/so_thuc_gvm.giao`; wasm⟷Python **byte-for-byte 15/15**.
  Ranh giới sạch giữ nguyên: số thực qua đối hàm người dùng → lỗi `[GIAOC — RANH GIỚI]` (tham số
  máy không mang kiểu). KHÔNG ở gate-level Verilog (đó là lõi vô hướng 16-bit — số thực thuộc
  substrate phần mềm/WASM). Chi tiết khác-biệt ngữ nghĩa: `RANH_GIOI.md`.
- **★ `mãi` (vòng liên tục) + `thử/bắt` (NGOẠI LỆ) xuống máy (mốc 3e)** — `mãi { }` = vòng
  không-điều-kiện chạy tới `dừng` (dùng chung ngăn-xếp-thoát của 3c, KHÔNG opcode mới). `thử/bắt`
  = cơ chế NGOẠI LỆ THẬT ở tầng máy: 3 opcode mới `BẮT_ĐẦU_THỬ`(62)/`HẾT_THỬ`(63)/`NÉM`(64) +
  **ngăn xếp HANDLER** lưu sâu các ngăn-xếp; `NÉM` GỠ-CUỘN (unwind) mọi khung gọi lồng về nhánh
  `bắt` rồi trao trị-lỗi. Nguồn NÉM: **chỉ mục danh sách ngoài phạm vi** (`__lấy` chạm NIL) — đúng
  một lỗi runtime máy *phát hiện được* và thông dịch *cũng bắt* (vd 4). Bắt được ⇒ chương trình
  KHÔNG sập, phục hồi chạy tiếp; lỗi chưa bắt ⇒ DỪNG sạch. Khác thông dịch: trị-lỗi máy là MÃ SỐ
  (1 = ngoài phạm vi) thay vì chuỗi-thông-điệp (luồng điều khiển khớp). Mirror `gvm_may.py`+
  `wasm/gvm.ts`; ví dụ `examples/thu_bat_mai_gvm.giao` (7·22·0·42·100·10); wasm⟷Python **16/16**.
- **★★★ BIẾN CỤC BỘ THEO KHUNG → HĐH-GIAO CHẠY NHƯ MÃ MÁY** — sửa hạn chế nền tảng: `đặt`
  trong hàm trước đây thành ô-TOÀN-CỤC (mọi lần gọi DÙNG CHUNG → hỏng đệ-quy-có-biến và
  closure-giữ-state). NAY `đặt`/biến-lặp/tên-bắt trong hàm là **ô-KHUNG per-call** (prologue
  `DÀNH_CB` dành ô; `LƯU_THAM_I` ghi ô-khung) → mỗi lần gọi có biến RIÊNG; closure **BẮT theo trị**
  (con trỏ) nên mỗi tiến trình giữ state riêng. Thêm `RỌI_AUTO` (in tự-suy-kiểu lúc chạy: con trỏ
  chuỗi→chuỗi, ngược lại→số) cho `rọi` tham-số-chưa-rõ-kiểu; `TruthLit` `sáng/tối`→`1/0`. **Kết quả:
  nhân `examples/hdh.giao`** (bảng tiến trình = `bản`, tiến trình = closure-giữ-state, lập lịch
  hợp tác = `mãi`+`lặp`, syscall + cổng an toàn) — TRƯỚC chỉ chạy thông dịch — NAY **biên dịch trọn
  → 16968 từ-lệnh GVM, chạy NHƯ MÃ MÁY khớp TỪNG DÒNG với thông dịch**, và byte-for-byte trên WASM
  (memory-safe, KHÔNG qua C). HĐH viết-bằng-GIAO giờ chạy trên đường-máy/đa-substrate, không còn
  khoá ở thông dịch. Runner: `chay_hdh_may.py` (GVM) · `wasm/chay_hdh.mjs` (WASM boot+đo).
  wasm⟷Python **17/17** (thêm ca `hdh`). 4 opcode mới: `DÀNH_CB/LƯU_THAM_I/RỌI_AUTO` (+`TruthLit`).
- **★★★ LẬP LỊCH PREEMPTIVE γ (BIẾT-HỌC) ĐIỀU KHIỂN BẰNG GIAO — NỐI LIỀN VỚI SILICON** — nhân
  hợp-tác (hdh.giao) → nay **preemptive THẬT**: tiến trình SPIN VÔ TẬN cũng KHÔNG treo được hệ.
  3 builtin MÁY/SILICON mới cho GIAO: `xuất(x)` (MMIO + tín hiệu ρ làm-việc-hữu-ích) · `tác_vụ(hàm)`
  (đăng ký tiến trình = hàm không-tham-số, ngăn-xếp+biến-cục-bộ RIÊNG per-task) · `lịch_học(lượng_tử)`
  (khởi động γ-scheduler) → biên dịch sang opcode `XUẤT/TÁC_VỤ/HẸN_GIỜ/LỊCH_HỌC`. Bộ lập lịch HỌC σ
  theo cộng hưởng γ: ai XUẤT → σ↑ → ưu tiên; spin vô ích → σ↓ → ĐỐM TỐI → đói CPU (không bỏ đói
  tuyệt đối). **Chính sách PHẦN MỀM (`GVM.γ_cập_nhật` / `lập_lịch_học`) ≡ TỪNG WIRE silicon `hw/gvm.v`**
  (σ←σ+((ρ−σ)>>2) clamp · credit←σ>>2 · COST=128 · argmax) — chứng minh **3000/3000 ca khớp byte**;
  và CÙNG chính sách chạy trong CỔNG LOGIC (verify iverilog: spin σ=12 vs hữu ích σ=252/184). Ví dụ
  `examples/hdh_preempt.giao` (spin bị throttle còn ½ CPU). Runner: `chay_hdh_preempt.py` (3 tầng:
  GIAO→γ-scheduler phần mềm≡wire silicon→cổng logic). Đây là điều **Kali/Linux KHÔNG có ở tầng nhân**.
- **★★ CÔ LẬP FAULT TIẾN TRÌNH bằng THỬ/BẮT** — mỗi tiến trình có **ngăn-xếp + ngăn-xếp-HANDLER
  RIÊNG** (cô lập bộ nhớ + ngoại lệ). Khi tiến trình NÉM lỗi (vd chỉ mục ngoài phạm vi): (a) nếu nó
  TỰ bọc `thử/bắt` → phục hồi NỘI BỘ, chạy tiếp; (b) nếu KHÔNG → lỗi lan tới NHÂN (supervisor) →
  nhân **CÔ LẬP** (giết) tiến trình đó, các tiến trình KHÁC KHÔNG hề hấn — *một tiến trình sập KHÔNG
  kéo sập cả hệ*. Hiện thực: `self.fault_code` (NÉM-chưa-bắt → mã lỗi), `handlers` per-task trong
  γ-scheduler (đúng dưới preemption); supervisor ghi `[nhân] ⚠ tt#X NÉM lỗi=N → CÔ LẬP`, tách
  `lỗi` khỏi DỪNG-êm. Ví dụ `examples/hdh_fault.giao`: tt#1 (thử/bắt) tự chữa 5× → SỐNG · tt#2
  (không bắt) → bị cô lập · tt#0 chạy 18 output sau khi cô lập (hệ vẫn khoẻ).
- **★★ PERSISTENCE TRỰC GIAO cho NHÂN HĐH — ảnh-MÁY ĐẦY ĐỦ, RESUME giữa chừng** — ngoài
  `lưu_ảnh`/`nạp_ảnh` (chỉ RAM, chạy-lại-từ-đầu) nay thêm **`GVM.lưu_máy`/`nạp_máy`** chụp **TOÀN BỘ**
  trạng thái máy: RAM + `ip` + MỌI ngăn xếp (giá-trị/tham-số/trả-về/khung/handler) + vật/tâm + heap.
  `run()` thành **RESUMABLE** (hết `max_steps` → TẠM DỪNG `halted=False`, không phải kết thúc). ⇒ chụp
  ảnh GIỮA CHỪNG rồi RESUME y nguyên trên một GVM HOÀN TOÀN MỚI (RAM trống) — kiểu ảnh Smalltalk/
  EUMEL, không "tệp" rời. Nhân `examples/hdh_ben.giao` (sổ-cái = `bản` trên heap, tích luỹ 1+…+10=55):
  máy A chạy in 1·3·6·10 rồi TẮT giữa vòng → máy B (GVM mới) khôi phục ảnh, chạy tiếp 15·…·55·lần=10.
  GHÉP(A⊕B) **TRÙNG KHỚP** chạy-liền-mạch ⇒ bộ đếm & sổ-cái BỀN qua reboot. Runner `chay_hdh_ben.py`.
  (`hdh_ben` thuần compute → chạy cả thông dịch lẫn máy/WASM; wasm⟷Python **18/18**.)
- **★ TỐI ƯU MAP KHOÁ-CHUỖI (−62% lệnh)** — `bản` khoá-chuỗi trước rất nặng: mỗi truy cập (a) DỰNG
  LẠI chuỗi-khoá trên heap, (b) so khoá bằng `__bằng` ĐỆ QUY từng ký tự. Hai tối ưu hợp lực:
  **(1) INTERN chuỗi-hằng** — chuỗi literal dùng ≥2 lần được dựng SẴN 1 lần lúc khởi động, mọi lần
  dùng sau chỉ `TẢI_Ô` con trỏ (chuỗi 1-lần giữ nguyên ⇒ bytecode cũ không đổi). **(2) Đường NHANH
  trong `@__map_tìm`** — thử `BẰNG` thô (1 lệnh) TRƯỚC `__bằng`: số↔số và chuỗi-INTERN-cùng-con-trỏ
  khớp ngay, chỉ chuỗi-tính-toán mới rơi xuống `__bằng` cấu trúc. `examples/hdh_ben.giao`: **62059→
  23550 lệnh (−62%)**. Bonus: trình-biên-dịch-tự-thân `giaoc.giao` (lắm chuỗi lặp) **8387→7276 từ**.
  Đầu ra & ngữ nghĩa KHÔNG đổi (intern = cùng chuỗi, dựng 1 lần; fast-path: raw-bằng ⟹ cấu-trúc-bằng).
  wasm⟷Python vẫn **18/18** byte-for-byte.
- **★★ LÕI GVM 32-BIT TRÊN VERILOG — chương trình HEAP (ABI thẻ) chạy GATE-LEVEL** — lõi 16-bit
  `hw/gvm.v` chỉ chạy chương trình vô hướng; ABI THẺ (bit 30 phân biệt con-trỏ) cần 32-bit. Đặt
  `WORD=32`, RAM 8192 → **danh sách cons-cell + duyệt heap + GỌI HÀM theo khung (`dài`→`__dài`
  đệ quy) + `là_số`/`là_ds` (phân biệt kiểu bằng thẻ)** chạy trên CỔNG LOGIC (iverilog), **đối
  chiếu BYTE với GVM phần mềm**: `examples/heap32_gvm.giao` → `[10,20,30,3,1,1,0]` TRÙNG KHỚP, dừng
  sau 658 chu kỳ. Harness `hw/lam_verilog32.py`. (Sửa kèm: `type_of(là_số/là_ds/có_khoá)='num'` →
  in bằng `RỌI` thay `RỌI_AUTO`, đúng-kiểu + khớp lõi Verilog; đầu ra không đổi, suite vẫn 5/5.)
  Heap32 nay chạy **NĂM substrate**: thông dịch · GVM-mềm · WASM · và **Verilog 32-bit gate-level**.
- **★★ THÊM OPCODE Verilog: CLOSURE + CHUỖI gate-level** — bổ sung vào `hw/gvm.v`: **`ĐỔI`** (hoán
  đỉnh ↔ kế-đỉnh, cho `__cộng`/`__bằng`) · **`RỌI_CHUỖI`** (duyệt heap char-list, xuất TỪNG ký tự —
  trạng thái đa-chu-kỳ `S_STR`, cổng `out_kind`=0 số/1 ký-tự/2 hết-chuỗi) · **`GỌI_CLOSURE`** (dựng
  khung `[bắt…, đối…]`: dịch đối + chép bắt từ heap — trạng thái `S_CLO`). Kèm `RỌI_AUTO` (in
  tự-suy-kiểu) + `DÀNH_CB`/`LƯU_THAM_I` (biến cục bộ per-call) cho đủ. `examples/heap32_chuoi.giao`
  (closure `áp(nhân(3),5)=15`, `nhân(7)(6)=42`, nối chuỗi `"Gi"+"ao"="Giao"`, `"HDH-"+"GIAO"`) chạy
  trên **Verilog 32-bit** đối chiếu BYTE phần mềm — TRÙNG KHỚP. Harness `hw/lam_verilog32_chuoi.py`.
  **Sửa hồi quy:** `lam_verilog` (16-bit, `tac_tu_may`) từng vỡ do đổi-biến-cục-bộ phiên này
  (`đặt`-trong-hàm→`DÀNH_CB`/`LƯU_THAM_I`) — thêm 2 opcode ấy vào Verilog đã **phục hồi** (xuất lại
  `[65533,0,…]`). `state` FSM nới 1→2-bit cho các op đa-chu-kỳ; mặt nạ thẻ width-agnostic (chạy cả 16/32).
- **Sửa lỗi tiềm ẩn (lộ ra khi làm 3c): `+`/`==`/`!=` ĐA HÌNH trên chuỗi/danh sách giờ TỰ bật
  thẻ.** Trước đây `"a"+"b"` ở chương trình 16-bit (không dùng là_số/bản) lặng lẽ thành CỘNG số
  trên con-trỏ → sai. Nay `uses_tag()` bật thẻ khi thấy toán hạng Str/ListLit hoặc `lặp…trong`
  chuỗi literal ⇒ dùng `__cộng`/`__bằng` đúng. Khôi phục nguyên tắc "không biên dịch-nhưng-sai".
  (Lưu ý NIL=0: chuỗi rỗng `""`≡`0` nên `""+x`→`"0"+x` — tài liệu hoá ở `RANH_GIOI.md`.)

### ★ Cầu nối polyglot — "cắm GIAO vào dự án BẤT KỲ NGÔN NGỮ NÀO, không conflict"
- **Sidecar JSON-qua-stdio** (`giao_cau_noi.py`): lõi suy luận viết bằng GIAO
  (`cau_noi.giao` — cổng phê duyệt ba-trị); Python chỉ là vỏ I/O. Mọi ngôn ngữ spawn tiến
  trình + ghi/đọc 1 dòng JSON. SDK tham chiếu `khach_cau_noi.py`; spec `CAU_NOI.md`.
- **MCP server** (`giao_mcp.py`) — **zero-dependency** (tự hiện thực JSON-RPC 2.0 trên
  stdio; KHÔNG cần `pip install mcp`), tái dùng `CầuNối`. 9 tool: `giao_quan_sat`,
  `giao_cong_huong`, `giao_hoc`, `giao_vung_toi`, `giao_chon`, `giao_phe_duyet`,
  `giao_trang_thai`, `giao_doc_tep`, `giao_chay`. Cấu hình `.mcp.json` sẵn ở gốc.
- **Capability I/O qua MCP/sidecar**: cấp quyền qua env `GIAO_CHO_DOC` / `GIAO_CHO_CHAY` /
  `GIAO_CHO_GHI` (mặc định TẮT — host quyết GIAO được chạm gì). GIAO quan sát dự án host
  THẬT (đọc tệp, chạy test) → biến thành `vật` → suy luận γ/DE → cổng chặn việc bất khả hồi.

### ★★★★ HĐH-GIAO Pha 1 — ĐA NHIỆM TIỀN-ĐỊNH (preemptive)
- **Bước đầu của KE_HOACH_PHAT_TRIEN.md.** Thêm vào GVM (`gvm_may.py`): opcode **`XUẤT`** (MMIO
  console) + **`chạy_đa_nhiệm`** — bộ lập lịch **tiền-định** (round-robin theo **lượng tử thời
  gian** ≈ ngắt timer phần cứng: sau mỗi N lệnh, nhân CƯỚP CPU + chuyển ngữ cảnh). Mỗi tiến trình
  có ngăn xếp riêng. `hdh_tien_dinh.py` chứng minh **mốc Pha 1**: 3 tiến trình xen kẽ, trong đó
  **B chạy loạn (vòng vô tận, không nhường)** — A và C VẪN HOÀN THÀNH ⇒ *một tiến trình loạn KHÔNG
  treo được hệ* (cooperative `hdh.giao` thì treo). Additive, conformance 11/11 + 5/5 hạng mục giữ nguyên.
  Còn lại Pha 1: thiết bị MMIO (timer/UART), port nhân `hdh` sang phần biên-dịch-được, ngắt timer ở `hw/gvm.v`.
- **★ Pha 3 — TĂNG TỐC THÔNG DỊCH 1.69×** (`bench_interp.py`: fib(25) 1.605s→0.951s, 63/63 đúng).
  cProfile chỉ nút cổ chai: `eval` if-chain + `getattr(node,line)` (4.5M lần) + `tick`. Sửa: (1) `Node`
  có `line/col` mặc-định-lớp → bỏ getattr; (2) inline `tick` vào eval/exec; (3) sắp nhánh NÓNG lên đầu
  (VarRef/Bin/Goi · Tra/Neu/ExprStmt); (4) FAST-PATH số↔số trong `eval_bin` (bỏ lambda + kiểm Tri/AN).
  Tối ưu đường *toàn-ngôn-ngữ* (đường biên-dịch giaoc→GVM→WASM vốn ĐÃ ~430× — Pha 3 cho lõi số xong).
  Native-compile toàn ngôn ngữ vẫn là con voi còn lại (cần toolchain C). Additive, conformance 5/5.
- **★★★★ Pha 2 — SIP (cô lập base+bound, KHÔNG MMU)** (`hw/gvm.v` + `hw/lam_sip.py`). Mỗi task vùng
  nhớ riêng (`mbase=i·128`); truy cập RAM relocate (vật-lý=gốc+ảo) + kiểm biên → vượt = FAULT 911+halt.
  Opcode `BẬT_SIP`. Verify iverilog: 2 task dùng CÙNG `ram[0]` — không-SIP giẫm đạp (A nhảy cóc
  `1,2,3,4,6,7,9`), có-SIP cô lập (A liên tục); chạm ngoài vùng → `[1,911]` HALT. Rẻ hơn MMU (1 cộng+1
  so sánh, không TLB) — mô hình Singularity SIP.
- **★★★★ Pha 2 — PERSISTENCE TRỰC GIAO** (`GVM.lưu_ảnh/nạp_ảnh` + `hdh_persistence.py`). Ảnh RAM bền
  qua reboot (Smalltalk/EUMEL): bộ đếm `5→10→15→20` dù MỖI lần GVM MỚI — trạng thái trong ẢNH, không
  trong tiến trình.
- **★★★★ LẬP LỊCH CDFL BIẾT-HỌC TRÊN SILICON** (`hw/gvm.v` + `hw/lam_lichhoc.py`) — "OS biết học"
  ở tầng CỔNG LOGIC. Thêm thanh ghi `sigma/cred/did_out` mỗi tiến trình + opcode `LỊCH_HỌC`. Phần
  cứng QUAN SÁT (RỌI → did_out=ρ), **HỌC** `σ ← σ + (ρ−σ)>>2` (động học tiên đề 5, fixed-point dịch
  bit, cộng CÓ DẤU + clamp), và lập lịch theo **credit ∝ σ** (chọn argmax) — tất cả bằng cổng logic.
  Verify iverilog (1200 chu kỳ): tiến trình hữu ích (RỌI) → σ→252/184 → ưu tiên; spinner → **σ→12
  → throttle**. So round-robin: A,C làm **61 vs 46 output** (CPU phí của spinner chuyển sang việc
  hữu ích). σ đọc thẳng từ `dut.sigma[i]` → học diễn ra TRONG SILICON. Additive (mặc định round-
  robin; γ chỉ khi `LỊCH_HỌC`) → 4 chế độ phần cứng + conformance 5/5 giữ nguyên.
- **★★★ ĐA NHIỆM TIỀN-ĐỊNH TRÊN SILICON** (`hw/gvm.v` + `hw/lam_danhiem.py`) — context-switch
  BẰNG CỔNG LOGIC. Thêm **ngân hàng thanh ghi mỗi tiến trình** (`t_ip/t_sp/t_fp/t_rsp[NT]`) +
  opcode `TÁC_VỤ` (đăng ký tiến trình, sp base riêng = i·64) + `LẬP_LỊCH` (khởi động). Khi
  `sched_on`, mỗi `period` chu kỳ timer **tự lưu ngân hàng task hiện hành + nạp task kế** (round-
  robin) — KHÔNG phần mềm điều phối. Kiểm chứng iverilog (gate-level): 2 tiến trình đếm vô tận
  chạy ĐỒNG THỜI trên 1 CPU, output xen kẽ `[1,101,2,3,102,4,…]`, mỗi task đếm ĐƠN ĐIỆU (không
  hỏng ngữ cảnh). ⇒ **đa-nhiệm-tiền-định THẬT trên FPGA** — mốc OS lõi của Pha 1, ở silicon.
- **★★ NGẮT TIMER PHẦN CỨNG** (`hw/gvm.v` + `hw/lam_ngat.py`) — preemption neo xuống SILICON.
  Thêm vào Verilog tổng-hợp-được: bộ đếm `timer`, thanh ghi `ie/in_isr/ivec/saved_ip/period`, kiểm
  ngắt ở FETCH (mỗi `period` chu kỳ → CƯỚP CPU, lưu ip, nhảy handler), opcode `BẬT_NGẮT/TẮT_NGẮT/
  HẸN_GIỜ/NGẮT_VỀ(IRET)`. Kiểm chứng qua **iverilog (gate-level)**: main đếm 8→1, handler "⚡tick"
  (99) **xen giữa 6 lần** ⇒ ngắt phần cứng PREEMPT chương trình đang chạy. Additive (ie/period mặc
  định tắt) → `lam_verilog` tac_tu_may vẫn đúng 13 giá trị, conformance 5/5 giữ nguyên. *Đây là
  primitive nền của đa-nhiệm-tiền-định Ở SILICON — không còn là mẹo trong Python.*
- **★ Bộ LẬP LỊCH CDFL BIẾT-HỌC** (`hdh_lap_lich_cdfl.py`) — nhân *học* hành vi tiến trình (σ←σ+α(ρ−σ),
  động học tiên đề 5) và lập lịch theo **cộng hưởng γ** thay vì round-robin mù. Tín hiệu tiến-triển ρ =
  số IP phân biệt thăm/lượng tử (spinner=1 IP→vô ích). Tiến trình hữu ích → σ→1, γ→+1 → **lượng tử đầy,
  ưu tiên**; spinner → σ→0, **γ→−1 = đốm tối → THROTTLE** (1 lệnh/lượt) nhưng KHÔNG bỏ đói (DE = chưa
  chắc nên vẫn cho chạy chút). Tách *cơ chế* (`GVM.chạy_lát`) khỏi *chính sách* (lập lịch) — đúng thiết kế
  OS. Demo: A,C xong nhanh, B-spin chỉ tốn 19 lệnh (vs 64 của round-robin). "OS THÍCH NGHI" — Kali/Linux
  không có ở tầng nhân. (Bài học OS thật đã sửa trong khi xây: tín hiệu ρ ngây thơ → bỏ đói việc hợp lệ.)

### ★★★ HĐH viết BẰNG GIAO (examples/hdh.giao)
- **Hệ điều hành nhỏ VIẾT BẰNG CHÍNH GIAO**, chạy TRÊN GVM/runtime GIAO (= tầng ảo hóa, như
  Linux trên hypervisor — đây là "OS ngôn ngữ", giống Lisp machine/JavaOS, không boot bare-metal).
  Có: **bảng tiến trình · bộ lập lịch hợp tác (round-robin) · syscall (`in`/`sinh`/`nguy_hiểm`) ·
  đa nhiệm thật** (tiến trình INTERLEAVE) · **cổng an toàn** chặn syscall bất-khả-hồi. Tiến trình =
  MÁY TRẠNG THÁI (closure giữ state riêng qua `bản` — **lexical closure** vừa sửa chính là thứ làm
  việc này chạy đúng). 4 tiến trình chạy xen kẽ dưới một nhân; `format ổ đĩa` bị cổng chặn.
- `os_giao_linux.py` + `Dockerfile`: bản phụ — GIAO làm "lương tri OS" cảm nhận hệ Linux qua /proc,
  chạy được trong container (KHÁC hdh.giao: đây là GIAO *giám sát* một OS, không *là* OS).

### Công cụ (DX) & hiệu năng
- **★ PLAYGROUND TRÌNH DUYỆT** (`wasm/lam_playground.py` → `wasm/playground.html`) — viết GIAO
  & chạy NGAY trong trình duyệt, **KHÔNG Node/Python/cài gì**. Tệp HTML tự chứa (~88KB) nhúng
  `giao.py`+`chuẩn.giao` (base64), Pyodide (CPython→WASM) chạy TRỌN trình thông dịch trong
  sandbox trình duyệt. Mở `file://` là dùng. (`giao.chạy_chuỗi(src)` gói cả lỗi vào text;
  `import subprocess` chuyển sang nạp LƯỜI để giao.py chạy được trong Pyodide.)
  **ĐÃ KIỂM CHỨNG LIVE** bằng trình duyệt THẬT (`wasm/kiem_playground.mjs`, headless Chrome qua
  puppeteer-core): chạy GIAO trong browser → output đúng (`5`/`7`/`[1, 4, 9]`/`ẩn`).
- **★ THÔNG ĐIỆP LỖI chuẩn compiler hiện đại** — thêm **vị trí CỘT** (tokenizer theo dõi cột),
  **khung lỗi** (in dòng nguồn + dấu `^` chỉ đúng chỗ), và **gợi ý "có phải '…'?"** (difflib,
  cutoff 0.7) cho tên gõ sai. `GiaoSyntax(SyntaxError)` mang dòng+cột. Áp dụng cả khi chạy tệp
  lẫn REPL. Vd: `tên 'số_luong' chưa định nghĩa — có phải 'số_lượng'?` + `^` tại cột 5.
- **★ BENCHMARK 3 tầng** (`wasm/bench.py` + `wasm/bench.mjs`) — vòng lặp 2,000,000 lần:
  thông-dịch ~3.0s · GVM-Python ~0.42s (7×) · **WASM GVM ~0.007s (≈430× nhanh hơn thông dịch)**.
  ⇒ ĐÃ CÓ "VM nhanh" cho lõi số: biên dịch giaoc → bytecode → chạy WASM. `compile_lap` nay dùng
  `emit_const` (vòng lặp count tới 32-bit, không còn giới hạn 8-bit).
- **★ REPL** — `python giao.py` (KHÔNG tham số) → vòng đọc–tính–in. Trạng thái bền qua các
  dòng; biểu thức cuối → in giá trị; khối nhiều dòng tự nối tới khi cân ngoặc; lỗi không làm
  sập vòng. `.trợ_giúp` / `.thoát`. Nhận cờ capability (`--cho-đọc`…) như chạy tệp.

### Ranh giới hai tầng thực thi (RANH_GIOI.md)
- **★ Tuyên bố + TỰ THỰC THI ranh giới** thông dịch (ngôn ngữ đầy đủ) ⟷ máy/GVM (lõi số,
  5 substrate). `giaoc.py` nay BÁO LỖI SẠCH `[GIAOC — RANH GIỚI]` cho tính năng chỉ-thông-dịch
  (closure, `bản`, `lặp…trong`, `mãi/trôi`, `de`, `thử/bắt`, `nhập`, capability, LLM…). Sửa 2
  cạm bẫy "biên dịch-nhưng-SAI": `ngờ` (nhánh ẩn trước bị lặng lẽ bỏ) và `float` (trước bị cắt
  thành int) — nay là lỗi rõ ràng. Bảng phạm vi đầy đủ: **`RANH_GIOI.md`**.

### Phần cứng & substrate (hw/, wasm/)
- `lam_verilog.py`: thêm bộ đếm chu kỳ → đo xác thực **1,191,838 chu kỳ clock**; lõi tác tử
  ra **13 giá trị** `[65533,0]×6,0`, khớp TỪNG GIÁ TRỊ giữa GVM phần mềm và Verilog gate-level.
- **★ SUBSTRATE THỨ 5 — WASM** (`wasm/`): GVM ĐẦY ĐỦ viết bằng AssemblyScript → `gvm.wasm`
  (~3.7KB), chạy trong Node/trình duyệt. Cùng máy trit/γ, **không fork ngôn ngữ** (chỉ thêm nơi
  chạy cho máy, sau Python-sim/model/Verilog/FPGA). Các hàm RỌI là **host import** =
  object-capability của WASM cộng hưởng với của GIAO. Port TRỌN bộ lệnh `gvm_may.py`: số học/
  so-sánh width-aware (16/32-bit), heap 64K, khung gọi hàm (`GỌI_N`/`THAM_I`/`TRẢ_VỀ_N`), nhảy
  gián tiếp, chuỗi, thẻ. **Chạy MỌI chương trình giaoc** — `wasm/kiem.mjs` đối chiếu **11/11 ca
  KHỚP byte-for-byte** với GVM Python (heap/đệ quy/chuỗi/THẺ-32bit; kể cả `giaoc.giao` 8357
  từ-lệnh tự chạy trên wasm sinh đúng bytecode). Output có cấu trúc thu qua `gvm_may.GVM.xuất`.

### Kiểm thử
- `kiem_thu.py`: **27 → 39 ca** (thêm mãi/dừng/trôi, σ/Φ ensemble, I/O theo năng lực).
- `kiem_mcp.py` (mới): **13 ca** cho MCP server (handshake, tools/list, cổng phê duyệt,
  chống chèn mã, capability refusal) — hermetic.
- Toàn bộ 56 lệnh README chạy sạch một lượt (0 fail).

### Tệp mới
`cau_noi.giao` · `giao_cau_noi.py` · `khach_cau_noi.py` · `giao_mcp.py` · `kiem_mcp.py` ·
`.mcp.json` · `CAU_NOI.md` · `CHANGELOG.md` · `chay_giaoc_may.py` ·
`examples/{vong_lien_tuc_that, de_bon_mat_day_du, sigma_phi_ensemble, 13_the_kieu_gvm, io_quyen}.giao`.

### Tương thích ngược
- Mọi chương trình v0.2 chạy nguyên vẹn. Từ khoá mới (`mãi`/`dừng`/`trôi`) chỉ là keyword
  khi đứng làm lệnh; không đụng ví dụ cũ (đã kiểm: chỉ xuất hiện trong chú thích/chuỗi).
- Chế độ scalar 16-bit của giaoc là mặc định ⇒ bytecode máy của chương trình không dùng
  `là_số`/`là_ds` **không đổi một bit** (Verilog/FPGA an toàn).

---

## v0.2 — "Chuẩn bị tự thân hoá" (trước 2026-06)
Hàm + đệ quy + biến (`đặt`) + danh sách `[…]` + lập chỉ mục + thử/bắt; thư viện chuẩn viết
bằng GIAO; tự diễn giải (`giao_core*.giao`); biên dịch GIAO→GVM (`giaoc.py`); danh sách/chuỗi
trên heap máy; hàm nhiều tham số; FPGA/Verilog. (Xem README §4–§5e.)

## v0.1 — "Lõi CDFL chạy được"
Bộ ba cộng hưởng `sáng/ẩn/tối` + γ thay bit; `vật`/`tâm`/`học`/`giao`/`rọi`/`lặp`; rẽ nhánh
ba ngả `nếu/ngờ/khác`; `khi viên_mãn`; `de`; tầng nền NAND→trit→hội tụ (`gvm.py`).

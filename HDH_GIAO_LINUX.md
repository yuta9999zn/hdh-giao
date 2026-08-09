# HĐH-GIAO theo lối LINUX — có TRỢ LÝ AI trong nhân

> Đổi hướng (2026-07-29): trước đây HĐH-GIAO học **Object Manager / SCM / Job Object của Windows**
> (`hdh_full.giao`, `lib_khonggian`, `lib_dichvu`, `lib_nhóm`). Từ nay xây theo **lối Linux**:
> một cây `/` duy nhất · mọi thứ là tệp · quyền rwx + uid · **bảng gọi-hệ có số hiệu** · vỏ có
> ống/chuyển-hướng · `/proc` · `/dev`. Nhưng khác Linux ở một điểm cốt tử: **trợ lý AI là DỊCH VỤ
> HỆ THỐNG, và "nói bằng lời" là một GỌI-HỆ hạng nhất** — máy nghe được tiếng người.

## 1. Chạy thử

```bash
python giao.py hdh_giao.giao        # bản trình diễn có kịch bản (boot → 6 màn)
python giao.py hdh_tiến_trình.giao  # ★ đa nhiệm thật: tiến trình chạy xen kẽ, ngủ, dậy, chết
python giao.py hdh_ống.giao         # ★ ống liên-tiến-trình: phản áp, EOF, quyền, bế tắc
python giao.py hdh_bền.giao         # ★ chụp cả hệ ra JSON → tắt máy → dựng lại → chạy tiếp
python giao.py hdh_tiền_định.giao   # ★ lập lịch γ: kẻ tham lam bị bóp, không ai bị bỏ đói
python kiem_lich_gamma.py           # ★ chứng: lịch γ của HĐH ≡ lịch γ của silicon (2000 ca)
python giao.py hdh_máy.giao --cho-máy         # ★★ TIỀN ĐỊNH THẬT: thân tiến trình là bytecode GVM
python giao.py hdh_máy_gọi_hệ.giao --cho-máy  # ★★ opcode GỌI-HỆ: máy xin việc của nhân (trap)
python chay_vo_may.py                         # ★★★ VỎ LỆNH chạy bằng BYTECODE trên GVM
python chay_dv_may.py                         # ★★★ DỊCH VỤ NỀN bằng BYTECODE, biết NGỦ như daemon
python chay_ben_may.py                        # ★ chụp–dựng CẢ tiến trình máy (ngữ cảnh lõi GVM)
python hw/lam_trap.py                         # ★★ GỌI-HỆ chạy trên CỔNG LOGIC THẬT (iverilog)
python chay_tro_ly_may.py                     # ★★★ TIM LÀ THIẾT BỊ: lõi quyết định trợ lý = bytecode
python hw/lam_cosim.py                        # ★★★★★ ĐỒNG MÔ PHỎNG: cổng logic xin việc NHÂN THẬT
python hw/lam_cosim_vpi.py                    # ★★ như trên nhưng điểm hẹn là VPI — tất định, 2 chu kỳ/lời xin
python hw/lam_bo_mo_phong.py                  # ★★★ CHÍNH cái đỉnh sẽ nạp lên bo, qua dây UART từng bit
python hw/lam_bitstream.py                    # ★★★ tổng hợp ra BITSTREAM FPGA (yosys → nextpnr → ecppack)
python hw/nhan_qua_uart.py COM7               # nhân GIAO phục vụ CPU đang chạy trên SILICON THẬT
python chay_hdh_giao.py --lưu ảnh.json      # thoát phiên thì chụp cả hệ ra đĩa thật
python chay_hdh_giao.py --nạp ảnh.json      # bật lại đúng cái máy hôm qua
python chay_hdh_giao.py             # ★ ĐĂNG NHẬP rồi gõ lệnh thật (mặc định an/an · gốc/gốc)
python chay_hdh_giao.py --gốc       # chế độ MỘT NGƯỜI DÙNG (uid 0, không hỏi mật khẩu)
python kiem_hdh_giao.py             # nghiệm thu 232 hạng mục
```

Trong vỏ: `giúp` · `nhờ <việc nói bằng lời>` · `chờ` / `duyệt` / `huỷ` · `thoát`.

## 2. Bản đồ Linux → GIAO

| Linux | HĐH-GIAO | Nằm ở |
|---|---|---|
| VFS, "everything is a file" | cây `/` một gốc, nút = thư/tệp/thiết_bị | `lib_tệp_hệ.giao` |
| quyền `rwx`, uid/gid, root | quyền 3 chữ số (755), uid, **uid 0 = gốc-quyền** | `lib_tệp_hệ.giao` |
| `errno` (ENOENT/EACCES) | **ba-trị**: `sáng` xong · `tối` từ chối · `ẩn` không có | toàn tầng |
| bảng syscall (`unistd.h`) | `GH_*` 0…21, cổng duy nhất `gọi(máy, tid, số, đối)` | `lib_gọi_hệ.giao` |
| `/proc` | `/tt` — nhân tự sinh tệp cho mỗi tiến trình | `đồng_bộ_tt` |
| `/dev` + driver | `/tb` + trình điều khiển (`màn`, `không`, `giờ`, `ngẫu`, `đĩa0`) | `_tb_đọc/_tb_ghi` |
| `/etc` · `/home` · `/tmp` | `/hệ` · `/nhà` · `/tạm` | `hdh_nền.giao` |
| `/bin` + `$PATH` + `chmod +x` | `/lệnh` — **mọi lệnh là một tệp**, `$PATH` ở `/hệ/đường_lệnh` | `cài_lệnh` (`lib_vỏ`) |
| init (PID 1) | `khởi` — tiến trình 1, dựng cây, sinh dịch vụ | `hdh_nền.giao` |
| bash: `\|` `>` `>>` `&&` `.` `..` | y hệt, lệnh có tên Việt + bí danh Linux (`ls`,`cat`,`ps`…) | `lib_vỏ.giao` |
| `auditd` | nhật ký mọi lời gọi hệ (`nhật_ký` / `dmesg`) | `lib_gọi_hệ.giao` |
| lập lịch + IPC | bảng tiến trình, hàng ưu tiên, hộp thư | `lib_hệ.giao` |
| `nice` (ưu tiên NGƯỜI khai) | **γ — độ hữu ích máy TỰ ĐO**, `lịch γ` để bật | `lib_lịch_γ.giao` |
| ngắt timer cướp CPU | **tiến trình MÁY**: thân là bytecode GVM, chạy ≤ `lượng_tử` lệnh rồi bị cắt | `--cho-máy` |
| `fork`+`exec`, tiến trình chạy thật | `GH_SINH` nạp **thân** chương trình, `vòng_nhân` quay bánh xe | `lib_chương_trình.giao` |
| pipe / FIFO | `/ống` — ống của nhân, `soi` thấy số gói đọng | `nút_ống` (`lib_tệp_hệ`) |
| hibernate / CRIU checkpoint | `chụp_máy` → JSON · `phục_hồi_máy` + `hồi_sinh` | `lib_bền.giao` |
| `sudo` | `duyệt` — nhưng chỉ cho **việc bất-khả-hồi**, không phải "lên quyền" | `lib_gọi_hệ.giao` |
| — (không có) | **`nhờ <lời nói>` = GH_NHỜ, trợ lý AI trong nhân** | `lib_trợ_lý.giao` |

## 3. Kiến trúc — bốn tầng, một cổng

```
   người gõ / nói ─────────────────────────────────────────────┐
        │                                                      │
   ┌────▼───────────────┐        ┌──────────────────────────┐  │
   │ VỎ  (lib_vỏ)       │        │ TRỢ LÝ AI (lib_trợ_lý)   │  │
   │ ống · > · &&       │        │ γ-cổng · từ chối · dự định│ │
   └────┬───────────────┘        └────────────┬─────────────┘  │
        │  MỌI THỨ đi qua một cổng duy nhất   │ (cùng tid!)     │
   ┌────▼─────────────────────────────────────▼──────────────┐  │
   │ GỌI-HỆ (lib_gọi_hệ) — số hiệu · uid · audit · cổng      │  │
   │ BẤT-KHẢ-HỒI                                             │  │
   └────┬───────────────────────────┬────────────────────────┘  │
        │                           │                           │
   ┌────▼──────────────┐   ┌────────▼──────────┐   ┌───────────▼──┐
   │ HỆ-TỆP (lib_tệp_hệ)│   │ NHÂN (lib_hệ)     │   │ TRÁI TIM     │
   │ cây / · quyền rwx  │   │ tiến trình · lịch │   │ (tim_llm)    │
   └────────────────────┘   │ · IPC             │   │ nhúng → γ    │
                            └───────────────────┘   └──────────────┘
```

Kỷ luật Linux được giữ nghiêm: **vỏ và trợ lý không chạm hệ-tệp hay bảng tiến-trình**. Chúng chỉ
biết `gọi(...)`. Muốn kiểm chứng: `nhật_ký` in ra đúng dãy lời gọi mà chúng đã thực hiện.

## 4. Bảng gọi-hệ

| # | tên | ~ Linux | ghi chú |
|---|---|---|---|
| 0–3 | `đọc` `ghi` `tạo` `thêm` | read/write/creat | thiết bị đi qua trình điều khiển |
| 4–7 | `liệt` `tạo_thư` `xoá` `soi` | getdents/mkdir/unlink/stat | `xoá` ★ bất-khả-hồi |
| 8–9 | `đổi_quyền` `đổi_chủ` | chmod/chown | `đổi_chủ` ★ bất-khả-hồi, chỉ gốc |
| 10–13 | `về` `ở` `ai` `thành` | chdir/getcwd/getuid/setuid | `thành` chỉ gốc-quyền |
| 14–17 | `sinh` `thoát` `giết` `tt` | fork+exec/exit/kill/ps | `giết` ★; **không giết được tiến trình 1** |
| 18–19 | `gửi` `nhận` | IPC | dùng hộp thư của `lib_hệ` |
| **22–23** | **`ống` `đóng`** | **mkfifo / close** | **ống liên-tiến-trình: chặn · phản áp · EOF** |
| — | (opcode máy **72** `GỌI_HỆ`) | `syscall` / `int 0x80` | **tiến trình MÁY trap về nhân** |
| **25–26** | `lệnh` `từ` | `readline` / `argv` | **vỏ máy lấy NGUYÊN DÒNG (nó tự tách từ)** |
| **27–28** | `nhúng` `cộng_hưởng` | — (không có ở Linux) | **TIM như THIẾT BỊ: máy cầm SỐ HIỆU vector, xin γ** |
| 20 | `gắn_tb` | mknod | chỉ gốc-quyền |
| **21** | **`nhờ`** | **(Linux không có)** | **giao việc bằng lời cho trợ lý AI** |

## 5. Ba điều HĐH-GIAO làm khác Linux

### 5.1 `errno` là ba-trị, không phải mã số
`sáng` = xong · `tối` = **biết mà không cho** (EACCES) · `ẩn` = **không biết** (ENOENT).
Đây không phải trang trí: `ẩn` là DE của học thuyết — máy phân biệt "cấm bạn" với "tôi không có
cái đó", và không bao giờ bịa ra cái nó không biết.

> Bài học kỹ thuật rút ra khi xây: `sáng`/`tối` trong GIAO **là chuỗi**, mà nội dung tệp cũng là
> chuỗi ⇒ nếu trộn tín hiệu vào giá trị trả về thì một tệp chứa đúng chữ "tối" sẽ bị hiểu là
> "bị cấm". Nên quyền được hỏi ở **kênh riêng** (`tth_xem_được`, `lỗi_cuối`) đúng như Linux tách
> `open()` (kiểm quyền) khỏi `read()` (trả byte).

### 5.2 Cổng BẤT-KHẢ-HỒI (không phải cổng "quyền")
`sudo` của Linux hỏi *bạn là ai*. Cổng này hỏi *việc này có hoàn tác được không*. Xoá tệp, đổi chủ,
giết tiến trình, ghi đè ổ đĩa đều bị **giữ lại** cùng lời giải thích, tới khi người gõ `duyệt`
(dùng một lần). Nền tảng CDFL: hành động thu hẹp không gian lựa chọn của con người phải do **con
người** quyết, không phải máy — đây là empowerment, chứ không phải phân quyền.

### 5.3 Trợ lý AI là dịch vụ hệ thống, bị ràng ba lớp
```
$ nhờ hãy định dạng xoá sạch toàn bộ ổ đĩa giúp tôi
🤖 trợ lý nghe: "hãy định dạng xoá sạch toàn bộ ổ đĩa giúp tôi"
   cộng hưởng: định-dạng-ổ 50% · dọn-rác 8% · liệt-kê-nhà 4%   (ngưỡng 20%)
   ⛔ việc "định-dạng-ổ" là BẤT KHẢ HỒI — tôi KHÔNG tự làm.
```

1. **Đồng danh tính** — trợ lý gõ lệnh **qua chính tid của người nhờ**, nên uid y hệt. Không có cửa
   hậu: nhờ nó đọc `/hệ/mật_khẩu` thì nó bị nhân chặn đúng như bạn (nghiệm thu có ca này).
2. **Cổng cộng hưởng γ** — mỗi kỹ năng có mô tả; γ = `cộng_hưởng(nhúng(mô-tả), nhúng(lời nhờ))`.
   Dưới ngưỡng ⇒ **nói "chưa hiểu"**, không đoán bừa (cổng phủ "học-1-hiểu-10"). Toàn bộ bảng γ
   được in ra ⇒ quyết định của AI **soi được**, không phải hộp đen.
3. **Cổng bất-khả-hồi** — kỹ năng phá huỷ chỉ được **trình bày dự định**, người tự quyết. Tầng
   gọi-hệ chặn lần hai (phòng thủ kép: kể cả kỹ năng bị cài sai `khả_hồi` cũng không lọt).

**Trái tim**: `tim_llm.py` (Ollama nếu có → `nhúng` ngữ nghĩa thật; không có → bản dự-phòng băm-dấu
tất định). Ngưỡng γ **tự chỉnh theo trái tim đang đập** (`ngưỡng_γ`): 0.5 cho bge-m3, 0.2 cho bản
dự-phòng — vì mỗi bộ nhúng có thang γ riêng.

*(Máy này hiện **không còn Ollama** — trước có, nay đã gỡ ⇒ trợ lý đang chạy bằng bản dự-phòng.
Muốn trái tim thật thì cài lại **trên ổ D**, đừng đụng ổ C:*

```powershell
winget install Ollama.Ollama --location D:\Ollama
setx OLLAMA_MODELS "D:\Ollama\models"        # model tải về nằm ở D, không phải C:\Users\…
D:\Ollama\ollama.exe pull bge-m3             # nhúng đa ngữ — γ tiếng Việt sắc
D:\Ollama\ollama.exe pull llama3.2:1b        # sinh câu (tuỳ chọn)
```
*Cài xong, `nhịp_tim()` tự đổi sang `ollama:bge-m3` và `ngưỡng_γ()` tự nâng lên 0.5 — không phải
sửa một dòng GIAO nào. Bản thân HĐH-GIAO **không ghi gì ra ngoài `D:\HeDieuHanh\GIAO\`**: hệ-tệp
của nó nằm trong bộ nhớ, không đụng đĩa thật.)*

## 5.4 `sinh` chạy CHƯƠNG TRÌNH THẬT (đa nhiệm dưới bộ lập lịch)

`sinh` không còn chỉ ghi một dòng vào bảng tiến trình. Chương trình đăng ký trong
`lib_chương_trình.giao` là một **xưởng** `hàm(máy, tid, đối) → thân`; `thân` là closure chạy **một
lát** rồi trả `"tiếp"` / `"xong"` / `"chặn"`. Nhân quay bánh xe bằng `vòng_nhân(máy, số_lát)`:

```
$ chạy đếm 3 /nhà/an/tiến_độ
đã sinh tt5 · đếm — chạy nền (gõ `nhịp` để cấp thêm lượt CPU)
   ⟨lịch⟩ lát 2 · tt5 đếm → tiếp        ← hai tiến trình THAY PHIÊN nhau
   ⟨lịch⟩ lát 3 · tt4 đếm → tiếp
```

Đủ vòng đời Linux: **sẵn-sàng → chạy → (chặn ↔ đánh-thức) → chết**.
- **Ngủ/đánh thức thật**: dịch vụ `nhật_ký_hệ` gọi `GH_NHẬN`, hộp thư rỗng ⇒ trả `"chặn"` ⇒ nhân
  KHÔNG gọi nó nữa (không quay vòng bận). Ai `gửi` tin thì `lib_hệ` đưa nó lại hàng sẵn-sàng, nó
  ghi nhật ký rồi **ngủ tiếp** — đúng mô hình daemon.
- **Vùng nhớ riêng**: state của mỗi tiến trình nằm trong `bản` mà closure ôm; hai tiến trình `đếm`
  chạy xen kẽ vẫn đếm độc lập.
- **Kế thừa danh tính**: `GH_SINH` cho con **uid + thư mục của cha**. Tiến trình `tọc_mạch` sinh từ
  vỏ của `an` không đọc nổi `/hệ/mật_khẩu`, không tạo nổi `/hệ/cửa_sau` — nghiệm thu có ca này.
- **Vỏ cũng là tiến trình có vòng đời thật**: đang xử lý dòng lệnh = `chạy`, xong = `chặn` (ngủ trên
  bàn phím, như `bash` chặn ở `read()`). Sau mỗi dòng lệnh, `chay_hdh_giao.py` quay nhân vài lát nên
  **việc nền vẫn tiến trong lúc ta gõ**.

> Bẫy đã gặp và đã sửa: tiến trình **không có thân** (`khởi`, `vỏ`, `trợ_lý_ai`) mà bị coi là "xong"
> thì bộ lập lịch **giết luôn init và vỏ** → sập phiên. Nay `chạy_lát` trả `"ngủ"` cho chúng và nhân
> **đỗ** sang `chặn` chứ không giết.

Lệnh vỏ liên quan: `chạy|run <ct> [đối…]` · `nhịp|tick [n]` · `việc|jobs` · `kể|verbose [tắt]`.
Chương trình có sẵn: `đếm` · `nhật_ký_hệ` · `báo` · `chào` · `soi_rác` · `tọc_mạch`.
Bản trình diễn đầy đủ: `python giao.py hdh_tiến_trình.giao`.

## 5.5 `/lệnh` — thư mục lệnh THẬT (mọi lệnh cũng chỉ là tệp)

Vỏ không còn bảng lệnh cứng. Gõ `xem` ⇒ vỏ **đi tra tệp** `/lệnh/xem` y như Linux tra `$PATH`
(`$PATH` nằm ở `/hệ/đường_lệnh`, mặc định `/lệnh:/nhà/an/lệnh`). Hệ quả **thật**, không phải mô phỏng:

```
gốc:/# quyền /lệnh/xoá 644          ← gỡ bit x
an:/nhà/an$ xoá /tạm/rác2
vỏ: cấm chạy /lệnh/xoá — thiếu quyền x (rw-r--r--, chủ gốc)      (mã 126)

gốc:/# xoá /lệnh/cây  →  duyệt      ← xoá TỆP lệnh
an:/nhà/an$ cây /nhà
vỏ: không có lệnh 'cây' (xem `liệt /lệnh`)                        (mã 127)
```

Các hạng tệp lệnh phân biệt bằng **dòng đầu** — và từ v0.28.0 danh sách này **không nằm trong vỏ
nữa** mà nằm trong sổ `/hệ/định_dạng` (xem §5.20):

| dòng đầu (magic) | nghĩa | ví dụ |
|---|---|---|
| `#nội-trú <tên>` | vỏ tự làm — một thân, nhiều tên (như busybox) | `/lệnh/xem`, `/lệnh/tt` |
| `#tt <chương-trình>` | **sinh tiến trình thật** dưới bộ lập lịch (nối §5.4) | `/lệnh/đếm_số` → `đếm` |
| `#!mã-máy <16\|32>` | **chính BYTECODE GVM**, nạp thẳng — không dịch lại (§5.20) | tệp do `dịch` sinh ra |
| còn lại (`*`) | **kịch bản vỏ**: các dòng lệnh, có `$1…$9`, `$*` | `/lệnh/soi_hệ`, `/lệnh/lỗi` |

Nên **viết lệnh mới lúc máy đang chạy** chỉ là ghi một tệp — không biên dịch, không khởi động lại:

```
an:/nhà/an$ ghi /nhà/an/lệnh/nhà_tôi "liệt /nhà/an | đếm"
an:/nhà/an$ quyền /nhà/an/lệnh/nhà_tôi 755
an:/nhà/an$ nhà_tôi
3
```

Chỉ `về` (đổi thư mục của **chính tiến trình vỏ**) và `thoát` bắt buộc nằm trong vỏ — như `cd`
của bash, không thể là chương trình ngoài.

> Chi phí phải trả (đã đo): mỗi lệnh nay tốn thêm 2–3 lời gọi hệ để tra `$PATH` — thấy rõ trong
> `nhật_ký`. Đúng như `execve` của Linux phải quét `$PATH`. Đổi lại: lệnh trở thành **dữ liệu**,
> soi được, phân quyền được, thêm bớt được lúc đang chạy.
>
> Cũng vì thế phải sửa một chỗ **procfs**: trước đây `/tt` được tái sinh ở MỌI lời gọi đọc/liệt/soi;
> cộng với tra `$PATH` thì cả bản trình diễn chạm trần **5 triệu bước** của GIAO. Nay `/tt` chỉ sinh
> khi đường dẫn thật sự nằm trong `/tt` — đúng cách Linux sinh procfs **khi có người đọc**.

## 5.6 Ống liên-tiến-trình THẬT (`GH_ỐNG` / `GH_ĐÓNG`)

`|` của vỏ trước nay chỉ chuyền **văn bản trong một tiến trình**. Ống ở đây là **đối tượng của
nhân** nối hai tiến trình khác nhau, mỗi bên một đầu — và nó vẫn **là tệp** (nút trong cây, có
quyền rwx, `soi` thấy số gói đang đọng):

```
an:/nhà/an$ bơm 6 | lọc chẵn | hút /tạm/kq
đường ống bơm | lọc | hút → tt5 tt6 tt7  (xong sau 19 lát lập-lịch)
an:/nhà/an$ xem /tạm/kq
gói 2 chẵn / gói 4 chẵn / gói 6 chẵn
```

Vỏ nhận ra **mọi chặng đều là bệ phóng `#tt`** ⇒ nó tạo ống của nhân giữa từng cặp rồi sinh **ba
tiến trình thật**. Thêm `&` để chạy nền. Nếu có chặng không phải chương trình, `|` vẫn là ống văn
bản như cũ (tiện cho `xem … | tìm …`).

Bốn tính chất, đều nghiệm thu được (`hdh_ống.giao`):

| tính chất | biểu hiện |
|---|---|
| **chặn/đánh thức** | đọc ống rỗng → trạng `chặn`, không quay vòng bận; có gói → nhân đánh thức |
| **phản áp** | ống đầy → **bên GHI** phải ngủ. Ống sức chứa 1: trace hiện `bơm → chặn` xen kẽ |
| **EOF** | bên ghi `đóng` ⇒ bên đọc rút hết rồi kết thúc sạch — không treo |
| **quyền** | ống 600 của gốc-quyền: tiến trình `an` ghi vào bị `cấm ghi ống /ống/kín` |

**Bế tắc thì nói thẳng**: đọc một ống không ai ghi ⇒ tiến trình ngủ **mãi** (`trạng = chặn`,
`còn việc sẵn-sàng? tối` — nhân không quay tít, chỉ là nó chờ). Lối thoát đúng như Linux: ai đó
`đóng` đầu ghi thì bên đọc thấy EOF và kết thúc. Không có phép màu chống bế tắc, y như hệ thật.

## 5.7 Bền hoá: cả hệ điều hành gói trong MỘT chuỗi JSON

> **Đọc kèm §5.21 (tầng khối, B3).** Ảnh chụp JSON trả lời câu *"tắt máy rồi bật lại có còn dữ liệu
> không"*, nhưng **không** trả lời được *"mất điện GIỮA LÚC GHI thì sao"* — nó là ảnh chụp một
> khoảnh khắc, không phải giao dịch. §5.21 vá đúng chỗ ấy bằng khối + nhật ký. Hai thứ bổ nhau:
> ảnh chụp lo **cả máy**, tầng khối lo **từng lần ghi**.

`chụp_máy(máy)` xuất **toàn bộ phần dữ liệu** của một hệ đang sống ra JSON; `phục_hồi_máy(chuỗi)`
dựng lại; `hồi_sinh(máy)` nối mã vào. Chụp được: cây hệ-tệp (kể cả **ống với gói còn đọng**), bảng
tiến trình, hàng lập-lịch, hộp thư IPC, uid + thư mục hiện hành, sổ người dùng, đồng hồ nhịp, nhật ký
audit, **việc đang chờ phê duyệt**, và trạng thái bền của từng tiến trình.

```
tiến trình đếm (tt4) mới chạy 3 lát: tệp = [1 2 3 ]
ảnh chụp dài 6653 ký tự
máy cũ: ẩn                       ← vứt cả máy, chỉ giữ chuỗi JSON
dựng lại 2 thân tiến-trình · nhịp = 93
trước khi chạy tiếp: [1 2 3 ]
sau khi chạy tiếp:  [1 2 3 4 5 6 ]    ← ĐẾM TIẾP, không làm lại từ đầu
```

**Vì sao tiến trình sống lại được** — thân tiến trình là *closure*, không JSON hoá được. Nên nhân
tách đôi: **dữ liệu** của tiến trình nằm trong `trạng_ct[tid]` (một `bản`, chụp được), **gốc gác**
nằm trong `khai_sinh[tid] = [tên chương trình, đối]`. Khi phục hồi, `dựng_lại_thân` gọi lại xưởng
của chương trình; xưởng thấy `lấy_trạng` **không rỗng** nên **dùng lại state cũ** thay vì khởi tạo
lại (không xoá tệp, không đếm lại). Đây đúng là cách CRIU/checkpoint của hệ thật làm: *dữ liệu thì
bền, mã thì nạp lại*.

**Qua hai lần chạy** (ảnh nằm trên đĩa thật, Python đóng vai bộ điều khiển đĩa):

```bash
python chay_hdh_giao.py --lưu ảnh.json     # đời thứ nhất: làm việc rồi thoát
python chay_hdh_giao.py --nạp ảnh.json     # đời thứ hai: tệp, lệnh tự viết, tiến trình dở — còn cả
```

Trong vỏ còn có `chụp|snapshot <tệp>` để chụp ảnh **vào chính hệ-tệp GIAO**. Phục hồi thì phải làm
từ **ngoài** (lúc boot) — một cái máy không thể tự thay ruột mình giữa chừng.

> Hai chỗ suýt sai, đã sửa: (a) `thành_json` **không thoát ký tự** — chuỗi có `"` hoặc xuống dòng
> (mà nội dung tệp thì đầy) sinh ra JSON **hỏng**; đã thêm `_thoát` + giải mã `
`/`	` khi đọc.
> Đây là lỗi thật của `lib_json`, ảnh hưởng cả dự án chứ không riêng bền hoá. (b) JSON biến **mọi
> khoá thành chuỗi** ⇒ sau khi phục hồi, `lấy_khoá(bảng, 3)` trượt còn `"3"` mới trúng; phải đổi
> khoá số về lại kiểu số (`_khoá_số`) cho bảng tiến trình, cred, hộp thư, sổ người dùng.

## 5.8 Trợ lý TỰ SOẠN lệnh (không còn chỉ chọn trong kho)

Kho kỹ năng là hữu hạn — hỏi cái ngoài kho thì trợ lý đành chịu. Nay nó **soạn một dòng lệnh mới**,
nhưng "sinh" mà không phanh thì thành bịa, nên mọi lệnh sinh ra đi qua **ba cửa**:

| cửa | nội dung |
|---|---|
| **1. Thẩm định** | mỗi lệnh trong dòng phải **thật sự có trong `/lệnh`** và người nhờ **chạy được** nó — hỏi bằng gọi-hệ, không tin trí nhớ. Bịa `khởi_động_lại_máy` là chặn ngay |
| **2. Đối tượng có thật** | đường dẫn phải do trợ lý **dò thấy** bằng `liệt`/`soi`; không dò thấy ⇒ **không sinh** |
| **3. Trình bày + cổng** | luôn **in dòng lệnh trước khi chạy**; việc phá huỷ (`xoá` `quyền` `đổichủ` `giết` `gắntb`) thì **chỉ trình bày**, người tự quyết. Nhân chặn lần hai |

Hai lối soạn: **(a) theo mẫu** — động từ trong lời + đối tượng dò được trong hệ-tệp; hoàn toàn
tất định, **không cần LLM** (nên vẫn chạy khi máy không có Ollama). **(b) trái tim viết** — chỉ
dùng khi có model thật (`nhịp_tim()` ≠ dự-phòng): trái tim nhận danh sách lệnh **lấy từ `/lệnh`**
rồi viết một dòng, và vẫn phải qua đúng ba cửa trên.

```
an:/nhà/an$ nhờ cho tôi xem tệp sổ tay
   ⟡ kho kỹ năng chỉ khớp 19% < ngưỡng ⇒ không có việc sẵn nào đúng.
   ✎ tôi TỰ SOẠN (mẫu + dò hệ-tệp): $ xem /nhà/an/sổ_tay
   thẩm định: hợp lệ · cộng hưởng lệnh↔lời = 37%
        việc cần làm hôm nay

an:/nhà/an$ nhờ xoá giúp tôi tệp rác1 trong thư mục tạm
   ✎ tôi TỰ SOẠN (mẫu + dò hệ-tệp): $ xoá /tạm/rác1
   ⛔ đây là việc BẤT KHẢ HỒI / đổi quyền — tôi KHÔNG tự làm.

an:/nhà/an$ nhờ làm cho tôi một bài thơ về mùa thu Hà Nội
   ⟡ tôi KHÔNG soạn nổi lệnh nào cho việc này (không thấy động từ/đối tượng có thật).
   Tôi thà nói không biết còn hơn bịa ra một câu lệnh.
```

**Có căn cứ thắng mơ hồ**: nếu soạn được lệnh cụ thể (động từ + đối tượng dò thấy) mà kỹ năng trong
kho chỉ khớp lửng lơ (γ < ngưỡng + 0.30) thì **tin cái có căn cứ** — vì kho chỉ là mô tả chung
chung, còn lệnh soạn ra đã được đối chiếu với thực tại.

> **Năm** bẫy đã gặp và sửa khi làm phần này (ba cái đầu lộ ra lúc xây, hai cái sau lộ ra khi
> **thử lại bằng câu chưa từng chỉnh riêng** — đúng thứ cần làm sau mỗi lần vá heuristic): (a) quét bảng động từ theo thứ tự khiến *"soi … xem bao
> nhiêu"* ra `xem` — phải chọn động từ **xuất hiện sớm nhất** trong câu; (b) lấy đối tượng khớp đầu
> tiên khiến *"tệp mật_khẩu của hệ thống"* ra `xem /hệ` — phải lấy tên **khớp dài nhất** (cụ thể
> nhất); (c) kỹ năng "liệt-kê-nhà" khớp 28–49% giành mất cả câu hỏi về `/tạm` lẫn câu xoá — nên mới
> có luật "có căn cứ thắng mơ hồ" ở trên; (d) `xem` một **thư mục** ra `cấm đọc /tạm` — nghe như
> lỗi quyền, thật ra là **dùng sai dụng cụ** ⇒ nay hỏi `soi` kiểu đối tượng rồi tự chỉnh `xem`↔`liệt`;
> (e) *"nhật ký hệ có gì"* ra `nhật_ký 10` (sổ audit) trong khi máy có hẳn tệp `/hệ/nhật_ký` ⇒ đối
> tượng **dò thấy** thắng động từ chung chung. Cả năm đều là **trả lời sai mà vẫn "hợp lệ"** — thứ
> nguy hiểm nhất ở một trợ lý, vì không có gì báo động cả.
>
> **Trung thực:** năm cái này đã vá và có ca nghiệm thu, nhưng đây là **heuristic**, không phải chứng
> minh — câu chữ tiếng Việt còn muôn hình vạn trạng. Cái CHẶN THẬT không nằm ở độ khôn của bộ sinh mà
> ở ba lớp không đổi: **luôn in lệnh trước khi chạy** (người soi được), **việc phá huỷ không tự chạy**,
> và **nhân cưỡng chế quyền** bất kể trợ lý nghĩ gì.

## 5.9 Lập lịch γ — nhân ĐO rồi quyết, không nghe khai báo

Linux xếp hàng theo `nice`: một con số **người khai, máy tin**. Kẻ tham lam chỉ cần khai ưu tiên
cao. HĐH-GIAO xếp theo **γ**: con số **máy tự đo** — lát vừa rồi tiến trình có làm việc thật không
(có gọi-hệ nào không).

```
ρ = 255 nếu lát vừa rồi CÓ gọi-hệ, 0 nếu chỉ quay vòng
σ ← σ + ((ρ − σ) >> 2)                  ← học độ hữu ích, kẹp [0,255]
credit ← credit + (σ >> 2);  kẻ vừa chạy TRẢ COST = 128
chọn kế = argmax(credit)
```

Ba tiến trình **cùng ưu tiên 5** — một kẻ `tham` (quay vòng, không gọi-hệ) và hai `đếm` (ghi tệp
mỗi lát), chạy 30 lát:

| | kẻ tham lam | việc thật A | việc thật B |
|---|---|---|---|
| **lịch cổ điển** (ưu tiên tĩnh) | **15 lát (50%)** | **0 — bị bỏ đói!** | 15 |
| **lịch γ** | **5 lát (16%)** | 13 | 12 |
| σ học được (lịch γ) | 30 → γ = **−0.76** | 250 → γ = +0.96 | 249 |

Kẻ tham lam bị bóp xuống 1/6, **và không ai bị bỏ đói** — thứ mà đống ưu-tiên tĩnh làm hỏng ngay
trong cùng thí nghiệm. Nó không xin được, không khai man được: nhân **không hỏi nó câu nào cả**.

**★ Cùng một chính sách từ vỏ lệnh xuống cổng logic.** `γ_bước` (viết bằng GIAO) trùng **từng phép**
với `gvm_may.GVM.γ_cập_nhật` ở tầng máy — vốn đã được chứng là trùng **wire `hw/gvm.v`** trên
silicon. `python kiem_lich_gamma.py` đối chiếu **2000/2000 ca ngẫu nhiên** (σ mới · credit mới ·
tiến trình được chọn). Dịch phải có dấu `>>2` = `//4` của GIAO nên số học khớp tuyệt đối.

Trong vỏ: `lịch` (xem đang dùng gì) · `lịch γ` · `lịch thường`.

> **Trung thực về chữ "tiền định":** nhân **quyết** ai chạy tiếp và **bóp được** kẻ tham lam — phần
> đó thật, chạy được, đo được. Nhưng ở tầng thông dịch, nhân **không cắt ngang được** một closure
> đang chạy dở; tiến trình vẫn phải trả CPU sau mỗi lát. Cắt ngang thật sự (đếm đủ N lệnh là cướp)
> chỉ có ở **tầng máy** — `gvm_may.lập_lịch_học` với `timer_period`, đã chạy bit-exact trên Verilog.
> Muốn tiền định trọn vẹn ở tầng này thì phải **biên dịch thân tiến trình xuống GVM**.

## 5.10 Tiền định THẬT — thân tiến trình biên dịch xuống GVM

Ở §5.9 nhân đã **quyết** được nhưng chưa **cắt ngang** được: closure GIAO phải tự trả CPU. Nay có
loại tiến trình thứ hai — **tiến trình MÁY** — thân là **bytecode GVM**, và nhân cho nó chạy đúng
`lượng_tử` **lệnh máy** rồi **dừng nó lại giữa chừng** (`GVM.run(max_steps=…)` vốn tạm-dừng-được).
Nó không cần hợp tác, và cũng không có cách nào từ chối.

**Năng lực mới của ngôn ngữ** (object-capability, cấp bằng `--cho-máy`; chưa cấp thì các tên này
**không tồn tại**):

| builtin | việc |
|---|---|
| `biên_dịch(nguồn)` | mã nguồn GIAO → danh sách từ-lệnh GVM; vượt `RANH_GIOI.md` → **ẩn** |
| `máy_nạp(mã)` | nạp bytecode thành một **lõi máy** riêng (mỗi tiến trình một cõi) |
| `máy_lát(lõi, n)` | **chạy ≤ n lệnh rồi CƯỚP** → `[còn_sống, số_lệnh, có_xuất]` |
| `máy_xuất(lõi)` · `máy_lệnh(lõi)` | rút output mới · tổng số lệnh đã tiêu |

Đây không phải cửa hậu ngôn ngữ mà là **cửa xuống phần cứng**: GVM chính là cái máy (NAND→CPU),
GIAO chỉ xin nó *"chạy hộ N lệnh rồi trả quyền về"*.

Thí nghiệm (`hdh_máy.giao`): hai tiến trình có việc thật + **một `tham_lam` là vòng lặp một triệu
bước, không một điểm nhường nào**, lượng tử 120 lệnh, 18 lát:

```
⟨γ⟩ lát 1 · tt2 việc_thật → tiếp  (ρ=sáng σ=159)
⟨γ⟩ lát 3 · tt4 tham_lam → tiếp  (ρ=tối  σ=96)     ← bị cắt giữa vòng lặp, hệ vẫn thở
…
việc_thật (tt2): 785 lệnh · 7 lát · chết        ← chạy XONG dù kẻ tham lam đang chạy
việc_thật (tt3): 785 lệnh · 7 lát · chết
tham_lam  (tt4): 480 lệnh · 4 lát · sẵn-sàng    ← vừa BỊ CẮT, vừa BỊ BÓP (σ=40, γ=−0.69)
```

**Hai thứ khác nhau, có đủ cả hai:** *cắt ngang* (không ai treo được hệ) là cơ chế; *bóp* (kẻ vô ích
được ít lượt hơn) là chính sách γ. ρ ở đây = "có RỌI trong lượng tử" — **chính** tín hiệu `did_out`
mà γ-scheduler silicon dùng.

> **Còn giới hạn gì:** thân tiến trình MÁY phải nằm trong tập con biên-dịch-được (`RANH_GIOI.md`:
> số nguyên, hàm, đệ quy, rẽ nhánh, vòng đếm, danh sách/chuỗi trên heap) — **không** closure, `bản`,
> `thử/bắt`, không gọi-hệ. Nên tiến trình MÁY hiện là **tiến trình tính toán thuần**; muốn nó xin
> việc của nhân thì phải thêm opcode gọi-hệ vào GVM (đường đã rõ: thêm một opcode `GỌI_HỆ` rồi bắc
> cầu về `gọi(...)`). Vỏ, trợ lý, dịch vụ vẫn là tiến trình closure như cũ — hai loại sống chung
> dưới cùng một bộ lập lịch.

## 5.11 Opcode GỌI-HỆ — máy xin việc, nhân xét rồi phục vụ

§5.10 cho tiến trình MÁY bị cắt CPU, nhưng nó chỉ tính toán được. Nay GVM có **opcode 72
`GỌI_HỆ`**: máy đẩy số hiệu + đối lên ngăn xếp rồi **tạm dừng**; nhân đọc, phục vụ bằng **chính
`gọi(...)`**, đẩy kết quả vào ngăn xếp, máy chạy tiếp. Đúng mô hình `syscall`/`int 0x80` của CPU thật:
**máy không bao giờ tự làm I/O, nó chỉ biết xin.**

```
GIAO nguồn:   đặt nội = gọi_hệ(0, "/tạm/nguồn")        ← 0 = GH_ĐỌC
              gọi_hệ(2, "/tạm/bản_sao", 644, nội)      ← 2 = GH_TẠO
chạy:         ⟨trap⟩ tt3 gọi_hệ đọc → dữ liệu do NGƯỜI tạo
              ⟨trap⟩ tt3 gọi_hệ tạo → sáng
kết quả:      /tạm/bản_sao = [dữ liệu do NGƯỜI tạo]
```

**Chuỗi chạy được cả hai chiều**: đối kiểu chuỗi là **con trỏ heap của máy** → nhân đọc bằng
`máy_chuỗi`; kết quả chuỗi được nhân **cấp phát trên heap của máy** rồi trả con trỏ. Nhân biết chữ
ký của chính mình (`_đối_chuỗi`) nên máy không cần biết gì về kiểu.

**Điều quan trọng nhất — an toàn không mất một chút nào**, vì trap đi qua đúng cái cổng cũ:

| thử | kết quả |
|---|---|
| tiến trình máy uid 1000 đọc `/hệ/mật_khẩu` | `gọi_hệ đọc → tối` · *cấm đọc /hệ/mật_khẩu* |
| tiến trình máy `xoá /tạm/rác` | `gọi_hệ xoá → tối` · *CẦN PHÊ DUYỆT* — tệp **còn nguyên** |
| nhật ký audit | ghi đủ `tt7 thêm /tạm/bản_sao` như mọi tiến trình khác |

Trong vỏ tương tác, `việc` liệt kê cả **chương trình MÁY** và `chạy <tên>` khởi động được chúng:

```
an:/nhà/an$ chạy chép_máy
đã sinh tt6 · chép_máy — chạy nền
    [tt6] 1
an:/nhà/an$ xem /nhà/an/tên_máy_chép
giao-01                       ← do BYTECODE đọc /hệ/tên_máy rồi ghi ra, qua nhân
```

> **Còn lại:** vỏ/trợ lý/dịch vụ vẫn là closure (hợp-tác) vì chúng cần `bản`, closure, `thử/bắt` —
> ngoài tập con biên-dịch-được. Muốn cả HĐH xuống máy thì phải mở rộng `giaoc` cho những thứ đó,
> hoặc viết lại các dịch vụ trong tập con. Đường đã thông; phần còn lại là công.

## 5.12 Vỏ lệnh chạy bằng bytecode (`vỏ_máy.giao`)

Câu hỏi cuối: **vỏ có xuống máy được không?** Trả lời trung thực: `lib_vỏ.giao` (vỏ đầy đủ) thì
không — nó dùng `bản`, closure, `thử/bắt`. Nhưng **vòng lặp lõi của một cái vỏ** thì được, và đó
mới là thứ đáng nói: `vỏ_máy.giao` viết trong tập con biên-dịch-được, chạy như **bytecode trên GVM**.

Gọi-hệ **`GH_LỆNH` (25)** đưa **nguyên một dòng** (hết hàng → 0 = NIL). Nhân chỉ đóng vai **bàn
phím**, không hơn: **vỏ tự tách từ, tự phân giải, tự gọi syscall** — tất cả bằng bytecode của chính nó.

Tách từ viết bằng GIAO trong tập con, nên nó cũng là bytecode. Mẹo then chốt: **trên máy, một CHUỖI
chính là DANH SÁCH mã ký tự** (cons trên heap), nên `s[i]` ra **số**, `[s[i]]` là chuỗi một ký tự,
`ghép` nối chuỗi, và `từ == "xem"` so **theo nội dung** (đã kiểm: token dựng lúc chạy khớp hằng chuỗi).
Chính vì thế tệp `vỏ_máy.giao` **chỉ dành cho máy** — chạy bằng thông dịch sẽ khác nghĩa ở `s[i]`.

```
⟨trap⟩ tt3 gọi_hệ lệnh → 2          ← vỏ MÁY xin dòng lệnh
⟨trap⟩ tt3 gọi_hệ từ  → xem
⟨trap⟩ tt3 gọi_hệ từ  → /hệ/tên_máy
⟨trap⟩ tt3 gọi_hệ đọc → giao-01
   [tt3] giao-01                    ← bytecode tự in kết quả
…
⟨trap⟩ tt3 gọi_hệ đọc → tối         ← `xem /hệ/mật_khẩu` (uid 1000) BỊ CHẶN
⟨trap⟩ tt3 gọi_hệ xoá → tối         ← `xoá /tạm/rác` vướng CỔNG BẤT-KHẢ-HỒI, tệp còn nguyên
```

Vỏ máy làm được: `tôi` `ở` `xem` `liệt` `soi` `ghi` `thêm` `xoá` `đếm_từ` — mỗi lệnh là một trap.
Tự tách từ nên tốn hơn hẳn: **~160.000 lệnh máy trong 412 lát CPU** (trước, khi nhân tách hộ:
~14.000 lệnh / 67 lát). Đó là cái giá thật của việc tự làm lấy — và đo được bằng chính `lệnh_đã_chạy`.

**Ba thứ phải sửa mới chạy được** (đều là bài học thật):
1. **Con trỏ đuôi trong cons phải MANG THẺ.** Nhân cấp chuỗi lên heap máy mà quên gắn thẻ cho con
   trỏ `đuôi` ⇒ chuỗi **1 ký tự vẫn đúng** (`ở`) còn chuỗi dài thì so sánh trượt (`"tôi"`, `"xem"`)
   — đúng kiểu lỗi im lặng khó nhất.
2. **Ép biên dịch 32-bit CÓ THẺ** cho chương trình máy (`biên_dịch(nguồn, 32)`) — không có thẻ thì
   `RỌI_AUTO` không phân biệt được con trỏ chuỗi với số, in ra địa chỉ thay vì chữ.
3. **Danh sách trả về** (`liệt`/`soi`/`ai`) được nhân ghép thành **một chuỗi** ngăn bằng khoảng
   trắng — máy chưa có kiểu "danh sách chuỗi" để in.

> Còn lại: vỏ đầy đủ (`lib_vỏ.giao`) vẫn ở thông dịch vì cần `bản`/closure/`thử-bắt` cho ống, kịch
> bản, trợ lý. Nhưng ranh giới đã dịch chuyển thật: **tách từ + phân giải lệnh + so sánh chuỗi + gọi
> syscall đều đã là bytecode** chạy trên chính cái máy dựng từ NAND. Và hoá ra **không phải mở rộng
> `giaoc` một dòng nào**: `tách` được viết BẰNG GIAO trong tập con, thế là đủ.

## 5.13 Dịch vụ nền chạy bằng bytecode — và biết NGỦ

Vỏ đã xuống máy (§5.12). Còn dịch vụ nền thì vướng một chỗ khác hẳn: **daemon phải biết ngủ**. Một
tiến trình máy quay vòng hỏi "có tin chưa?" là đúng thứ dịch vụ nền không được phép làm.

Cách giải: **`gọi_hệ(19)` (nhận) mà hộp thư rỗng thì nhân vừa trả −1 vừa ĐỖ tiến trình sang trạng
`chặn`** — bộ lập lịch thôi cấp CPU. Ai `gửi` tin thì nhân đánh thức, và máy chạy tiếp **ngay sau
trap** với giá trị vừa được đẩy vào ngăn xếp. Không thêm opcode nào; chỉ là ngữ nghĩa chặn của
syscall, đúng như `read()` chặn trong Linux.

```
⟨γ⟩ lát 1 · tt2 nhật_ký_máy → chặn        ← sinh xong là ngủ ngay
   sau 6 lát:  trạng = chặn · lát CPU = 1
   quay nhân THÊM 10 lát:  lát CPU vẫn là 1 (không tăng)   ← ngủ thì KHÔNG tốn CPU

⟨trap⟩ tt2 gọi_hệ nhận → đĩa /tạm sắp đầy  ← `gửi` đánh thức
⟨trap⟩ tt2 gọi_hệ thêm → sáng              ← ghi nhật ký qua đúng cổng
⟨γ⟩ lát 6 · tt2 nhật_ký_máy → chặn        ← ghi xong NGỦ LẠI
```

Nhật ký hệ sau ba lần gửi — do **bytecode** viết ra:

```
nhịp 0  khởi: nhân lên
[máy] đĩa /tạm sắp đầy
[máy] mạng chập chờn
[máy] có người đăng nhập
```

Cả đời dịch vụ tiêu **2.898 lệnh máy trong 16 lát CPU**, kết thúc ở trạng `chặn`. Đúng mô hình
daemon của Linux — chờ trên hàng đợi, dậy đúng lúc có việc — nhưng thân là bytecode chạy trên chính
cái máy dựng từ NAND.

## 5.14 Gọi-hệ trên CỔNG LOGIC THẬT — opcode 72 trong `hw/gvm.v`

Cả mạch đã thông từ GIAO xuống bytecode. Bước cuối là xuống **cổng logic**: `hw/gvm.v` — CPU dựng
từ NAND — nay có **opcode 72 `GỌI_HỆ`** với đúng giao thức trap của CPU thật:

```verilog
output reg trap_valid;      // 1 = đang xin nhân phục vụ (giữ tới khi có ack)
output reg [7:0] trap_num;  // số hiệu gọi-hệ
output reg [WORD-1:0] trap_arg, trap_arg1, trap_arg2;   // tới BA đối
output reg [7:0] trap_nargs;                            // 0..3
input  trap_ack;            // nhân báo: xong
input  [WORD-1:0] trap_ret; // giá trị nhân trả về → đẩy vào ngăn xếp
```

Đường-dữ-liệu chỉ prefetch **2 toán tử đỉnh** (`opA`, `opB`), nên từ 2 đối trở lên phải **đọc thêm
tầng ngăn xếp**: opcode chuyển sang trạng thái `S_TRAPA`, mỗi chu kỳ moi thêm một ô sâu hơn
(`sp − 3 − k`) rồi mới dựng `trap_valid`. Cái giá là **1–2 chu kỳ** cho mỗi đối vượt quá hai —
CPU vẫn đứng im, không lệnh nào chen vào giữa.

CPU **đứng im ở trạng thái `S_TRAP`** (không đếm timer, không chạy lệnh nào) cho tới khi có
`trap_ack` — rồi đẩy `trap_ret` vào ngăn xếp và chạy tiếp. Nó **không tự làm I/O**, đúng như trên
phần mềm. Testbench `trap_tb.v` đóng vai **nhân bằng phần cứng**.

Chạy thật bằng iverilog (`python hw/lam_trap.py`):

```
[nhan] chu ky  41: TRAP so=11 nargs=0 doi=0
[CPU ] chu ky  55: ROI = 700          ← nhận kết quả rồi in
[nhan] chu ky  67: TRAP so=50 nargs=1 doi=21
[CPU ] chu ky  83: ROI = 42
[CPU ] chu ky 101: ROI = 742          ← 700+42: TÍNH TRÊN giá trị nhân trả về
[nhan] chu ky 113: TRAP so=50 nargs=1 doi=42,…
[CPU ] chu ky 129: ROI = 84
[nhan] chu ky 161: TRAP so=51 nargs=2 doi=5,9,0        ← ★ HAI đối
[CPU ] chu ky 175: ROI = 14
[nhan] chu ky 185: TRAP so=52 nargs=3 doi=1,2,3        ← ★ BA đối, ĐÚNG THỨ TỰ (1+20+300)
[CPU ] chu ky 199: ROI = 321
[nhan] chu ky 225: TRAP so=50 nargs=1 doi=4,…          ← đối tự nó là một lời xin khác
[nhan] chu ky 235: TRAP so=52 nargs=3 doi=700,14,8
[CPU ] chu ky 241: ROI = 1640
CPU DUNG sau 245 chu ky · 7 lan trap · 7 lan roi

phần mềm (gvm_may): [700, 42, 742, 84, 14, 321, 1640]
phần cứng (gvm.v) : [700, 42, 742, 84, 14, 321, 1640]
✓ TRÙNG KHÍT
```

Nghĩa là **ngữ nghĩa gọi-hệ giống hệt nhau từ mã GIAO xuống tới cổng logic** — không phải "lấy cảm
hứng", mà trùng từng giá trị.

Đối **lồng nhau** cũng chạy: `gọi_hệ(52, a, d, gọi_hệ(50, 4))` — lời xin bên trong được phục vụ
trước, kết quả của nó thành đối thứ ba của lời xin bên ngoài (700 + 10×14 + 100×8 = 1640).

> **Trung thực về phạm vi:** phần cứng nhận **0–3 đối**. Ba là đủ cho toàn bộ bảng gọi-hệ hiện có
> (nhiều nhất là `tạo(đường, quyền, nội)`); muốn hơn thì chỉ là nới `trap_k` — cùng một vòng lặp.
> Và "nhân" trong thí nghiệm này là testbench, không phải HĐH-GIAO thật — xem §5.16 cho bản nối
> nhân thật.

## 5.15 Trái tim là THIẾT BỊ — nên lõi quyết định của trợ lý cũng xuống được máy

Trái tim là **mạng nơ-ron**: nó **không bao giờ** là bytecode GVM được — đây là giới hạn bản chất,
không phải thiếu công. Lối ra đúng đắn là phơi nó ra như **thiết bị**, y như `/tb/màn` hay `/tb/đĩa0`:

```
gọi_hệ(27, "chữ")        → SỐ HIỆU vector   (vector nằm ở NHÂN, máy không hề thấy)
gọi_hệ(28, sh_a, sh_b)   → γ × 1000         (số nguyên — hợp với máy)
đọc /tb/tim              → tim đang đập bằng gì  ("ollama:bge-m3")
```

Nhờ vậy **phần quyết định** xuống được máy: `trợ_lý_máy.giao` tự nhúng lời nhờ, tự chấm γ từng kỹ
năng, tự chọn cái cao nhất, tự áp ngưỡng và **tự từ chối** — tất cả bằng bytecode:

```
⟨trap⟩ gọi_hệ lệnh → xem nhật ký hệ thống có gì bất thường không
   [máy] 835   359   361          ← γ×1000 ba kỹ năng, máy tự chấm
⟨trap⟩ gọi_hệ đọc  → nhịp 2  đĩa: /tạm đầy 91%

⟨trap⟩ gọi_hệ lệnh → làm giúp tôi một bài thơ về mùa thu Hà Nội
   [máy] 184   191   218          ← đều dưới ngưỡng 450
   [máy] 4294967295               ← −1 (bù-hai): TỪ CHỐI, không đoán bừa
```

Phân vai giờ rạch ròi và **đúng như học thuyết**: **tim CẢM** (thiết bị, ngoài máy) · **máy XÉT**
(bytecode: chấm, chọn, ngưỡng, từ chối) · **nhân LÀM** (và vẫn chặn bằng uid + cổng bất-khả-hồi).

> Con số γ ở trên là **tim thật** (`ollama:bge-m3` chạy từ `D:\Ollama`): 835 cho kỹ năng đúng so với
> ~360 cho kỹ năng sai — phổ rộng, xếp hạng chắc. Bản dự-phòng băm-dấu cho phổ hẹp hơn nhiều.

## 5.16 Đồng mô phỏng — cổng logic xin việc của NHÂN THẬT

§5.14 cho gọi-hệ chạy trên cổng logic, nhưng "nhân" khi ấy là **testbench đóng giả**. Nay nối thẳng:

```
CPU gate-level (iverilog chạy hw/gvm.v, dựng từ NAND)
      ⟷  điểm hẹn tệp trap_req.txt / trap_res.txt  ⟷
NHÂN HĐH-GIAO THẬT (lib_gọi_hệ.giao trên trình thông dịch)
```

`cosim_tb.v` chỉ còn làm **bưu tá**: thấy `trap_valid` thì **duyệt heap của chính CPU** để lấy chuỗi
đối, gói vào tệp; nhân phục vụ bằng **chính `gọi(máy, tid, số, đối)`**; nếu kết quả là chuỗi thì bưu
tá **cấp phát vào heap của CPU** (cons `[mã, đuôi]`, mọi con trỏ mang thẻ) rồi trả con trỏ.

Tiến trình silicon chạy dưới **uid 1000** — và chịu đủ mọi thứ:

```
[NHÂN GIAO] #1 gọi-hệ 0  đối=['/hệ/tên_máy']                        → giao-01
   [CPU-silicon] giao-01                       ← chuỗi do NHÂN cấp, CPU tự in

[NHÂN GIAO] #2 gọi-hệ 2  đối=['/tạm/từ_silicon', 644, 'dòng này…']  → sáng   ★ BA đối: TẠO TỆP
[NHÂN GIAO] #3 gọi-hệ 0  đối=['/tạm/từ_silicon']                    → dòng này do CỔNG LOGIC viết
[NHÂN GIAO] #4 gọi-hệ 3  đối=['/tạm/từ_silicon', ' + thêm nữa']     → sáng   ★ HAI đối: NỐI THÊM
[NHÂN GIAO] #5 gọi-hệ 0  đối=['/tạm/từ_silicon']                    → dòng này do CỔNG LOGIC viết + thêm nữa
   [CPU-silicon] dòng này do CỔNG LOGIC viết + thêm nữa

[NHÂN GIAO] #6 gọi-hệ 0  đối=['/hệ/mật_khẩu'] → tối   (cấm đọc /hệ/mật_khẩu)
[NHÂN GIAO] #7 gọi-hệ 6  đối=['/tạm/rác']     → tối   (CẦN PHÊ DUYỆT — BẤT KHẢ HỒI)
[NHÂN GIAO] #8 gọi-hệ 12 đối=[]               → 1000 an
CPU DUNG sau 2.327.815 chu ky · 8 lan xin nhan

HẬU KIỂM (hỏi lại nhân):
   /tạm/từ_silicon = [dòng này do CỔNG LOGIC viết + thêm nữa]   ← TỆP DO SILICON TẠO RA, còn thật
   /tạm/rác còn không? danh_sách        ← CÒN NGUYÊN, cổng đã chặn
   nhật ký audit: tt2 đọc /hệ/tên_máy · tt2 tạo /tạm/từ_silicon · tt2 thêm /tạm/từ_silicon ·
                  tt2 đọc /hệ/mật_khẩu · tt2 xoá /tạm/rác · tt2 ai
```

Tiến trình trên cổng logic **tạo ra một tệp thật trong hệ-tệp của HĐH** bằng gọi-hệ ba đối, nối
thêm bằng gọi-hệ hai đối, rồi đọc lại chính nó — chuỗi đi **cả hai chiều** qua heap của CPU.

**Quyền rwx và cổng bất-khả-hồi của một HĐH viết bằng GIAO đã chặn được một tiến trình đang chạy
trên cổng logic** — và ghi vào nhật ký audit y như mọi tiến trình khác.

> **Bẫy đã gặp (đáng ghi):** bắt tay `trap_ack` bằng gán KHÔNG-CHẶN trong `always @(posedge clk)`
> làm mỗi trap bị gửi **hai lần** — nhân phục vụ hai lượt cho cùng một lời xin, số hiệu lệch hẳn đi.
> Phải dùng `initial forever` + `wait` tường minh, và đẩy phép gán ra khỏi cạnh clock bằng `#1` để
> không tranh chấp với chính CPU đang lấy mẫu.
>
> **Trung thực về phạm vi:** điểm hẹn là
> **tệp** (không phải VPI/DPI) nên mỗi lời xin tốn vài nghìn chu kỳ mô phỏng — đúng cho việc chứng
> minh ngữ nghĩa, không phải cho tốc độ.

## 5.17 Điểm hẹn **VPI** — nhân GIAO thành hàm hệ thống của chính bộ mô phỏng

§5.16 dùng **tệp** làm điểm hẹn, và cái giá lộ ra rõ: testbench phải `#200` rồi mở tệp dò lại, nên
**mỗi lời xin đốt chu kỳ mô phỏng chỉ để ĐỢI** — mà đốt bao nhiêu thì tuỳ nhân trả lời nhanh hay
chậm, không lần nào giống lần nào (đo được từ 16.515 tới 2.327.815 chu kỳ cho cùng một chương trình).
Thời gian mô phỏng bị lẫn với thời gian thực: sai về nguyên tắc.

**VPI** cắt đúng chỗ ấy. `hw/giao_vpi.c` cài vào bộ mô phỏng một hàm hệ thống:

```verilog
trap_ret <= $giao_trap(trap_num, trap_nargs, trap_arg, trap_arg1, trap_arg2);
```

Lời gọi ấy **chặn ngay tại thời điểm mô phỏng đó** — thời gian mô phỏng đứng yên trong lúc C làm việc:

1. đối nào mang **thẻ** (bit 30) thì C **duyệt thẳng `dut.ram[]` qua VPI** (`vpi_handle_by_index` +
   `vpi_get_value`) để moi từng mã ký tự — Verilog không phải gói hộ nữa;
2. gửi qua **socket** tới tiến trình đang chạy **nhân GIAO thật**, chờ trả lời;
3. kết quả là chuỗi thì C **cấp phát vào heap của chính CPU** (`vpi_put_value` ghi ô cons
   `[mã, đuôi]`, `ram[250]` là con trỏ heap, mọi con trỏ mang thẻ) rồi trả con trỏ.

Cùng một chương trình, cùng một nhân, ba lần chạy mỗi bản:

| điểm hẹn | chu kỳ mô phỏng | thời gian thực |
|---|---|---|
| **tệp** (`lam_cosim.py`) | 16.515 · 18.435 · 23.455 — *và có lần 2.327.815* | 0,64 s |
| **VPI** (`lam_cosim_vpi.py`) | **5.183 · 5.183 · 5.183** | **0,40 s** |

Điều đáng giá không phải con số nhanh hơn ~3–4 lần, mà là **5.183 lặp lại y hệt**: chi phí gọi-hệ
nay đúng bằng **2 chu kỳ bắt tay** `trap_valid`/`trap_ack`, không phụ thuộc nhân trả lời nhanh chậm.
Mô phỏng trở lại **tất định**.

> **Bẫy đã gặp (Windows):** `vvp` nạp module VPI bằng `dlopen` đường-dẫn-**ANSI**, nên thư mục có
> dấu tiếng Việt làm nó báo *"The specified module could not be found"* — mà ổ D lại tắt tên 8.3 nên
> không lách bằng đường dẫn ngắn được. **Đã chữa tận gốc (v0.10.1):** dự án chuyển sang
> `D:\HeDieuHanh\GIAO`, và mọi chỗ lách đã gỡ — `.vpi` nay dựng thẳng cạnh mã nguồn.
> Cần thêm trình biên dịch C: `winget install BrechtSanders.WinLibs.POSIX.MSVCRT --location D:\mingw64`.

## 5.18 Ra **BITSTREAM FPGA** — GVM thành mạch thật trên chip

Chuỗi khép lại ở đây:

```
GIAO → giaoc → bytecode GVM → gvm.v (RTL) → yosys    (tổng hợp: RTL → cổng logic)
                                           → nextpnr  (đặt & nối trên CHIP THẬT)
                                           → ecppack  (đóng gói → .bit)
                                           → openFPGALoader (nạp vào FPGA)
```

Bytecode **nằm sẵn trong ROM của bitstream** — bo cấp điện là chương trình chạy, không phải nạp gì.

### Trên bo thì nhân ở đâu?

Bo không chạy Python được. Nên nhân HĐH-GIAO **vẫn ở máy chủ**, nối bằng **UART** — đúng cái kiến
trúc đã dựng từ đầu: *CPU không tự làm I/O, nó chìa lời xin ra rồi chờ nhân*. Chỉ khác: dây bây giờ
là dây đồng.

`hw/gvm_bo.v` là cầu ấy — GVM + UART + một máy trạng thái đóng/mở khung byte:

| bo → chủ | | chủ → bo | |
|---|---|---|---|
| `0xA5 số nargs đ0[4] đ1[4] đ2[4]` | xin gọi-hệ | `0x4D đc[2]` | đọc ô nhớ |
| `0xB5 kind dl[4]` | CPU RỌI | `0x57 đc[2] dl[4]` | ghi ô nhớ |
| `0x4D dl[4]` | trả lời lệnh đọc | `0x5A kq[4]` | phục vụ xong |
| `0xC5` | CPU đã dừng | | |

Máy chủ làm đúng việc mà C đã làm ở §5.17, chỉ là qua dây: **duyệt heap của CPU** bằng lệnh đọc-ô-nhớ
để lấy chuỗi đối, và **cấp chuỗi trả về vào heap của CPU** bằng lệnh ghi-ô-nhớ. An toàn vì CPU đang
đứng im ở `S_TRAP` suốt lúc ấy.

> **Bẫy đã gặp — cổng đọc thứ ba:** thoạt đầu tôi cho cầu ngoài một cổng đọc RAM **riêng**. Tổng hợp
> chạy hơn nửa tiếng không xong: BRAM `DP16KD` chỉ có **HAI** cổng, thêm cái thứ ba là cả
> `4096×32` rơi khỏi BRAM xuống LUT. Cách đúng: **dùng chung** cổng đọc sẵn có (`ram_ra` ưu tiên
> `dbg_a` khi `dbg_re`) — CPU đang đứng ở `S_TRAP` nên cổng ấy rảnh.

### Kiểm trước khi cắm bo

`hw/lam_bo_mo_phong.py` chạy **chính cái đỉnh sẽ nạp lên bo** trong iverilog, với một cặp
`uart_rx`/`uart_tx` đóng vai sợi cáp — mô phỏng tới **từng bit** trên dây:

```
[NHÂN GIAO] #1 gọi-hệ 0  đối=['/hệ/tên_máy']                     → giao-01
   [CPU-bo] giao-01
[NHÂN GIAO] #2 gọi-hệ 2  đối=['/tạm/từ_bo', 644, 'dòng này…']    → sáng
[NHÂN GIAO] #3 gọi-hệ 0  đối=['/tạm/từ_bo']                      → dòng này do BO FPGA viết
   [CPU-bo] dòng này do BO FPGA viết
[NHÂN GIAO] #4 gọi-hệ 0  đối=['/hệ/mật_khẩu'] → tối   (cấm đọc)
[NHÂN GIAO] #5 gọi-hệ 6  đối=['/tạm/rác']     → tối   (CẦN PHÊ DUYỆT)
BO DUNG sau 113.110 chu ky · 1.126 byte len · 1.042 byte xuong
```

Quyền rwx và cổng bất-khả-hồi **vẫn nguyên trên đường dây**.

### Bitstream đã dựng được

Đích: **Lattice ECP5-85F** (bo ULX3S), 25 MHz.

```
1) yosys   — tổng hợp RTL → cổng logic   ✓  36s
2) nextpnr — đặt & nối trên chip thật    ✓  60s
3) ecppack — đóng gói thành bitstream    ✓   2s

TRELLIS_COMB    7.067 / 83.640    8%      ← LUT
TRELLIS_FF      2.052 / 83.640    2%
DP16KD             30 /    208   14%      ← BRAM (ram · rom · stack · rstk)
MULT18X18D          9 /    156    5%
tần số tối đa: 39,66 MHz   (thiết kế chạy ở 25 MHz — dư 59%)

D:\giao_bitstream\gvm.bit   1.997.265 byte
```

Cả cái máy — GVM dựng từ NAND, γ-scheduler, opcode gọi-hệ, cầu UART, và **bytecode chương trình nằm
sẵn trong ROM** — chiếm **8% một con ECP5-85F**.

### Cắm bo

```bash
python hw/lam_bitstream.py              # tổng hợp → đặt-nối → đóng gói (.bit)
python hw/lam_bitstream.py --nạp        # nạp lên bo đang cắm
python hw/nhan_qua_uart.py COM7         # nhân GIAO phục vụ CPU đang chạy trên SILICON
```

Bo mẫu là **ULX3S** (Lattice ECP5, luồng mã nguồn mở). Bo khác chỉ cần viết một vỏ như
`hw/ulx3s_top.v` + tệp ràng buộc chân của bo ấy; `gvm_bo.v` giữ nguyên.

> **Chưa làm được — nói thẳng:** *cắm bo thật*. Máy đang dùng **không có bo FPGA nào**
> (`openFPGALoader --scan-usb` trả về bảng rỗng; soi USB/COM cũng không thấy FTDI/JTAG nào).
> Bitstream đã có và đã kiểm tới từng bit trên dây; nạp chỉ là một lệnh — nhưng phải có phần cứng
> trong tay. Đây là giới hạn vật lý, không phải giới hạn của chuỗi công cụ.

> **Bẫy đường dẫn (lại):** `nextpnr` cũng mở tệp ràng buộc bằng API ANSI ⇒ hồi dự án còn ở thư mục
> có dấu thì báo *"Failed to open LPF file: Invalid argument"*. **Đã chữa tận gốc (v0.10.1)** cùng
> lúc với bẫy VPI: đường dẫn dự án nay không dấu, `nextpnr` đọc thẳng `hw/ulx3s.lpf`.

## 5.19 ĐĂNG NHẬP — sổ người dùng, mật khẩu băm, đổi người

Trước đây `python chay_hdh_giao.py` là **vào thẳng** với tư cách `an`: có hệ-tệp, có quyền, có uid —
nhưng **không có cửa**. Chọn người dùng là một cờ dòng lệnh, không phải một lần xác thực. Nay có cửa
thật.

```
giao-01 · HĐH-GIAO — đăng nhập  (gõ `tắt` để tắt máy)
giao-01 đăng nhập: an
mật khẩu:
Xin chào an. Phiên vỏ là tiến-trình 5.

an:/nhà/an$ tôi
an (uid 1000) · tiến-trình 5 · /nhà/an
an:/nhà/an$ xem /hệ/mật_khẩu
xem: cấm đọc /hệ/mật_khẩu
an:/nhà/an$ thành gốc
mật khẩu của gốc:
[thành] nay bạn là gốc · tiến-trình 6
gốc:/# xem /hệ/mật_khẩu
gốc:$g2$128$efc5ab81674d2309$bfcec02303f2b43c2a79b1e6261cc4fccb932e774657e715c4e4f8905f5ecfff
an:$g2$128$1674d2309efc5ab8$f91f4789c926582e26a4ad85421b8a2fa05f3b04e28b142e7cc098172151e8bb
```

Cùng một tệp, cùng một câu lệnh: `an` bị chặn, `gốc` đọc được — và cái đọc được là **bản băm**, không
phải mật khẩu. Đây không phải quy ước lịch sự mà là chính tầng quyền rwx của HĐH.

| tệp | quyền | nội dung | vai |
|---|---|---|---|
| `/hệ/người_dùng` | 644 | `tên:uid:nhà` | ~ `/etc/passwd` — ai đọc cũng được |
| `/hệ/mật_khẩu` | **600** | `tên:$g3$N$muối$băm` | ~ `/etc/shadow` — **chỉ gốc-quyền** |

### Băm mật khẩu (`lib_mật_khẩu.giao`)

Không dùng `băm()` (djb2) của `lib_băm.giao`: đó là hash cho **bảng băm** — không muối, không lặp,
một phép nhân là xong; đem giữ mật khẩu thì bảng cầu vồng phá trong tích tắc. Ở đây là cấu trúc của
một hàm dẫn-xuất-khoá: **muối riêng cho từng người** + **lặp nhiều vòng** + lõi băm thật.

**Ba định dạng song song** — bản ghi cũ không bao giờ bị bắt đổi:
- `$g3$N$muối$băm64hex` — ★ **KHÓ VỀ BỘ NHỚ** (ROMix kiểu scrypt). **Bản ghi mới dùng cái này.**
- `$g2$vòng$muối$băm64hex` — **SHA-256 THẬT** (`lib_sha256.giao`, thuần GIAO, đối chiếu `hashlib`
  từng ký tự) xích `vòng` lần theo byte.
- `$g1$vòng$muối$băm16hex` — bộ trộn Mersenne 2^61−1 đời đầu, giữ để bản ghi cũ vẫn khớp được.

#### Vì sao thêm `$g3$` — quan sát Kali 2026.2 rồi mới làm

`grep ENCRYPT_METHOD /etc/login.defs` trên máy Kali thật trả về **`YESCRYPT`**. Đây là chỗ **Kali
hơn ta**, nói thẳng: `$g2$` chỉ khó về **thời gian**, mà SHA-256 gần như không cần bộ nhớ — nhét
vài nghìn nhân băm song song lên một con GPU là xong, mỗi nhân chỉ tốn dăm chục byte.

Cách chữa đúng (Percival, scrypt 2009) là bắt hàm băm **giữ một bảng lớn** và **truy cập vào bảng
ấy theo thứ tự không đoán trước được**. `băm_mk3` làm hai pha:

1. **Đổ đầy** `V[0..N−1]`, mỗi ô là băm của ô trước ⇒ tuần tự, không rút gọn được.
2. **Truy cập ngẫu nhiên**: mỗi bước lấy `j` từ **chính trạng thái hiện tại** rồi trộn với `V[j]`.
   `j` chỉ biết được sau khi đã tính tới đó ⇒ không nạp trước, không đoán trước.

Ai tiếc bộ nhớ mà chỉ giữ một phần bảng thì mỗi lần trượt ô phải **tính lại từ đầu** — đó chính là
cái giá đổi-bộ-nhớ-lấy-thời-gian khiến GPU/ASIC hết rẻ.

> **Trung thực — đừng đọc "memory-hard" thành "bằng yescrypt":** bảng ở đây là `N × 32` byte, mặc
> định `N = 64` ⇒ **2 KB**. scrypt thật chạy `N = 16384` (16 MB), yescrypt còn hơn. Ta có **đúng
> cấu trúc** nhưng **lượng** bộ nhớ còn nhỏ, nên phần chặn GPU mới là phần nào chứ chưa dứt điểm.
> `N` nhỏ vì ngân sách thời gian: **đo thật `$g2$` 743 ms/lần · `$g3$` 752 ms/lần — chênh 1,2%.**
> Nói cách khác: **cùng một cái giá, nay mua thêm được tính khó-về-bộ-nhớ** — đó là lý do đổi.
> `N` nằm trong bản ghi nên có đường máy nhanh thì nâng `MK_N3`, bản ghi cũ vẫn khớp.
> Cả ba định dạng đều **chưa qua thẩm định mật mã**.

### Ai làm việc gì

| việc | ở đâu | vì sao |
|---|---|---|
| đọc bàn phím, **tắt tiếng vọng** khi gõ mật khẩu | host (`chay_hdh_giao.py`) | đó là việc của **terminal**, như `tcsetattr` |
| đọc `/hệ/mật_khẩu`, băm, so, sinh phiên dưới đúng uid | **GIAO** (`lib_người_dùng.giao`) | đó là việc của **`/bin/login`** |

Hàm `đăng_nhập` chạy dưới **tiến trình gốc** (tid 1) vì phải đọc tệp 600 — đúng vai `/bin/login`
setuid root. Người dùng thường không tự chạy nó được: thử `xác_thực` bằng phiên của `an` thì trả
`ẩn`, vì `an` không đọc nổi sổ bóng.

### Lệnh

| lệnh | ~ Linux | ghi chú |
|---|---|---|
| `người` | `getent passwd` | lệnh vỏ THẬT — chạy được trong ống: `người \| đếm` |
| `thành <người>` | `su` | hỏi mật khẩu; sai thì **phiên đang dùng không hề hấn gì** |
| `đổi_mk` | `passwd` | phải biết mật khẩu cũ; gõ lại phải khớp; tối thiểu 4 ký tự |
| `thoát` | `logout` | **đăng xuất**, quay lại màn đăng nhập — không tắt máy |
| `tắt` | `poweroff` | tắt máy |

Sai mật khẩu ba lần thì phải nhập lại từ đầu, và **thông báo lỗi không nói rõ sai TÊN hay sai MẬT
KHẨU** — nói rõ là chỉ điểm cho người đang dò xem tài khoản nào có thật.

`--gốc` vẫn còn, nhưng nay được gọi đúng tên: **chế độ một người dùng**, vào thẳng uid 0 không hỏi gì
— như `init=/bin/sh` của Linux, chỉ dùng khi ngồi trước máy.

### Chống dò mật khẩu — đối chiếu với Kali 2026.2 THẬT

Quan sát trước, kết luận sau. Ba lệnh trên máy Kali thật:

| soi gì | Kali 2026.2 trả về | nghĩa là |
|---|---|---|
| `ls /usr/lib/*/security/pam_faillock.so` | **có** module | công cụ khoá tài khoản **có sẵn** |
| `grep faillock /etc/pam.d/*` | **không dòng nào** | …nhưng **KHÔNG BẬT** — mặc định đoán mật khẩu **thoải mái** |
| `grep PASS_MAX_DAYS /etc/login.defs` | `99999` | hạn tuổi mật khẩu **tắt** trên thực tế |
| `man 8 pam_unix` | *"delay-on-failure of the order of two seconds"* | chậm **CỐ ĐỊNH 2 giây**, và bằng cách **`sleep` chính tiến trình** |
| `man 8 pam_faillock` | `deny=4  unlock_time=1200` | khoá 20 phút sau 4 lần sai — **nếu** ai đó bật nó lên |
| `cat /etc/pam.d/common-auth` | `pam_unix.so **nullok**` | **mật khẩu RỖNG được chấp nhận** — sổ bóng để trống là vào thẳng |

Bốn chỗ HĐH-GIAO cố ý làm khác:

1. **Bật sẵn, không phải "có mà không cắm".** Sổ dò nằm ngay trong `đăng_nhập`, tức **một điểm chặn
   cho cả ba cửa** (ngồi tại máy · `thành` · từ xa). Không có kiểu "module có sẵn, quản trị viên tự
   nhớ mà bật" — thứ mặc định-tắt thì đa số máy sẽ chạy đời không có nó.
2. **Chậm DẦN chứ không chậm CỐ ĐỊNH.** 2s → 4s → 8s… trần 60s. Chậm cố định 2 giây chỉ cắt tốc độ
   đi một hằng số; chậm gấp đôi thì mỗi lần đoán hụt lại **đắt gấp đôi lần trước**.
3. **★ Không `sleep`, mà từ chối.** Đây là chỗ đáng nói nhất. `pam_unix` ngủ 2 giây **trong chính
   tiến trình đang xác thực** ⇒ kẻ tấn công mở 100 kết nối là **giữ chân 100 tiến trình** — cái
   dùng để chống dò lại thành **đòn bẩy làm nghẽn máy**. Ở đây ta ghi một **mốc thời gian** vào sổ
   rồi **trả lời ngay**: không luồng nào bị treo, mà kẻ dò vẫn phải chờ. Và vì mốc ấy nằm ở **sổ
   chung theo TÊN**, mở bao nhiêu kết nối song song cũng **cùng chịu một quãng chờ** — chứ không
   phải mỗi kết nối một đồng hồ riêng như `sleep` của PAM.
4. **Chừa `gốc` khỏi việc tự khoá** — giống `pam_faillock` (mặc định không `even_deny_root`), và vì
   đúng lý do: khoá được `gốc` thì kẻ dò chỉ cần gõ bừa 10 lần là **khoá cửa của chủ máy**. `gốc`
   vẫn bị chậm dần như mọi người.

Và một chỗ **ta đã kín sẵn mà không phải làm gì thêm**: `nullok` của Kali cho phép **mật khẩu
rỗng** — ai để trống ô bóng trong `/etc/shadow` là vào thẳng không cần gõ gì. Ở HĐH-GIAO việc ấy
**không xảy ra được**, vì bộ kiểm cấu hình H6 gắn ở **tầng gọi-hệ** đòi ô bóng phải bắt đầu bằng
`$g1$`/`$g2$`/`$g3$`; thử ghi `an:` vào sổ thì bị từ chối kèm số dòng, và **tệp cũ còn nguyên**.
Đây là lợi tức của một quyết định cũ: đặt bộ kiểm ở chỗ **mọi cửa ghi đều phải qua**, thay vì để
nó thành một tuỳ chọn mà quản trị viên phải nhớ bật.

> **Còn thiếu thật:** sổ dò sống trong **bộ nhớ** máy đang chạy — tắt máy là quên (`pam_faillock`
> với tally mặc định cũng vậy). Và **hạn tuổi mật khẩu** thì chưa có — tuy Kali cũng đang tắt
> (`PASS_MAX_DAYS 99999`), đó không phải cái cớ để ta không làm.

### Giấu ở lời nói mà hở ở đồng hồ — rò rỉ THEO THỜI GIAN

Chỗ này tự bắt được trong lúc đối chiếu, và nó đáng kể lại vì **lỗi nằm đúng trong thứ ta tưởng đã
làm cẩn thận**. Ta luôn trả lời *"Sai tên đăng nhập hoặc mật khẩu"* để không chỉ điểm tài khoản nào
có thật. Nhưng đo ra thì:

| gõ tên nào | công phải trả (trước khi vá) |
|---|---|
| người **CÓ THẬT**, sai mật khẩu | **~750 ms** (chạy đủ `$g3$`) |
| người **KHÔNG CÓ** | **~0 ms** (tra sổ hụt là trả về ngay) |
| tài khoản **BỊ KHOÁ** (`*`) | **~0 ms** |

Tức là kẻ dò **không cần đọc câu trả lời** — chỉ bấm giờ là đếm sạch danh sách tài khoản, rồi mới
dồn sức vào những tên có thật. **Giấu ở lời nói mà hở ở đồng hồ thì coi như không giấu.**

Cách chữa là cách OpenSSH đã dùng (họ gọi là *fake password hashing*): không có người ấy thì **vẫn
băm một bản ghi GIẢ rồi vứt kết quả**, để mọi ngả tốn đúng ngần ấy công. Tài khoản bị khoá cũng
phải đi qua đó, kẻo lại lộ *"tài khoản này có thật, đang bị khoá"*. `BÓNG_GIẢ` dựng từ `MK_N3` nên
nâng `N` thì bản giả tự theo — không có chuyện quên đồng bộ rồi hở lại.

Bộ kiểm `kiem_ro_ri_thoi_gian.giao` **đo thật chứ không tin lời hứa**, và đã thử **tháo bản vá ra
để xem nó có rớt không**: tháo ra thì `có-thật=3s · không-có=0s · bị-khoá=0s` → rớt cả hai ca.
Một cái chốt chỉ đáng tin khi đã thấy nó bật.

> **Cái giá phải trả, nói cho hết:** nay mỗi lần gõ tên bừa cũng ngốn 750 ms CPU của máy chủ. Sổ
> chậm-dần khoá theo TÊN nên không chặn được kẻ đổi tên liên tục. Thứ giữ cho phép tính này không
> lỗ là **hạn 3 lần sai mỗi kết nối**: quá thì đứt, mà nối lại phải làm **trọn một vòng
> Diffie-Hellman 2048-bit** — đắt cho kẻ gọi hơn là cho máy chủ.

### Trần công: đừng chạy theo lời khai của chính bản ghi

Cùng mạch soi lại, thấy thêm chỗ này. Bản ghi bóng **tự khai** số vòng (`$g2$**128**$…`) hay số ô
bảng (`$g3$**64**$…`), và `khớp_mk` **chạy đúng theo lời khai ấy** — đó là chủ ý, để nâng mức khó
mà không phá bản ghi cũ. Nhưng nó cũng có nghĩa: một dòng `$g3$999999999$…` lọt vào sổ (sổ hỏng ·
ảnh chụp cũ nạp lại · gói cài bậy) là **treo máy ngay tại màn đăng nhập** — kẻ tấn công **không
cần biết mật khẩu**, chỉ cần ghi được một dòng.

`MK_TRẦN_VÒNG = 100000` · `MK_TRẦN_N = 4096` · và `vòng < 1` cũng bị từ chối (0 vòng nghĩa là
không tốn công gì). Trần **không hạ mức an toàn**: nó chỉ chặn con số vô lý, còn dư xa mức đang
dùng. Bài học chung với mục trên: **thứ do bên ngoài khai thì phải kẹp phạm vi trước khi dùng** —
kể cả khi "bên ngoài" là tệp cấu hình của chính máy mình.

## 5.20 Sổ định dạng chạy được — và `/lệnh` mang chính BYTECODE (B2)

### Quan sát trước đã đổi cả cách đặt vấn đề

Mục B2 trong `CÒN_THIẾU.md` vốn tên là *"`/lệnh` vẫn là VĂN BẢN, chưa phải nhị phân"* — nghe như
việc phải làm là bỏ văn bản đi. Rồi đếm `/bin` trên Kali 2026.2 thật:

```
ELF/nhị phân: 1540      kịch bản có shebang: 897
```

**Ngay Linux thật cũng pha trộn.** Nên cái đáng học không phải "phải là nhị phân", mà là
**`binfmt_misc`**: nhân giữ một **sổ đăng ký** ánh xạ *byte đầu tệp (magic) → trình chạy*, còn
`#!` chỉ là **một mục** trong sổ ấy. Theo hình dạng đó thì thêm bytecode là **thêm một dòng**.

Trước v0.28.0, `chạy_một_lệnh` **ghi cứng** ba nhánh — muốn thêm định dạng là phải sửa vỏ, đúng
cái bệnh mà `binfmt_misc` sinh ra để chữa. Nay vỏ **không biết trước** có những định dạng nào; nó
hỏi sổ:

```
an:/nhà/an$ định_dạng
ĐỊNH DẠNG CHẠY ĐƯỢC (sổ /hệ/định_dạng)
TÊN         MAGIC       TRÌNH        NĂNG LỰC
  nội_trú     #nội-trú    nội_trú      -
  tiến_trình  #tt         tiến_trình   -
  mã_máy      #!mã-máy    mã_máy       máy
  kịch_bản    *           kịch_bản     -
```

### `/lệnh` mang chính bytecode

```
an:/nhà/an$ nói "rọi 6 * 7" > /nhà/an/n.giao
an:/nhà/an$ dịch /nhà/an/n.giao /nhà/an/lệnh/bốn_hai
đã dịch /nhà/an/n.giao → /nhà/an/lệnh/bốn_hai (377 từ-lệnh, chạy thẳng không dịch lại)

an:/nhà/an$ xem /nhà/an/lệnh/bốn_hai
#!mã-máy 32
257 18220 6650 257 6664 374 2560 8960 9984 6653 …          ← MÃ, không phải NGUỒN

an:/nhà/an$ bốn_hai
    [tt6] 42
tt6 · bốn_hai xong (1 lát lập-lịch)                        ← tiến trình MÁY thật, cắt ngang được
```

Chạy nó **không đụng tới trình biên dịch**: `đăng_ký_ct_mã` đưa thẳng từ-lệnh cho `máy_nạp`.
Khác `ct_máy` (giữ mã **nguồn** rồi dịch lại mỗi lần sinh) đúng ở điểm cốt lõi ấy.

> **Trung thực về chữ "nhị phân":** hệ-tệp GIAO chứa **chuỗi**, nên từ-lệnh được viết ra dạng
> **số thập phân** cách nhau bằng khoảng trắng. Cái đã đổi thật sự là **tệp mang MÃ chứ không
> mang NGUỒN**. Còn gọi nó là "nhị phân" thì vẫn là nói quá, nên trong mã ghi đúng như vậy.

### Ba chỗ `binfmt_misc` yếu — và làm khác thế nào

**① Đăng ký sai làm hỏng đường chạy cả máy.** Linux cho ghi thẳng vào `/proc/sys/fs/binfmt_misc`,
không ai kiểm; sai một mục là mọi tệp khớp magic ấy hết chạy, mà chỉ báo `Exec format error`.
Ở đây sổ đi qua **bộ kiểm cấu hình H6 ở tầng gọi-hệ** (§5.19 · H6), bắt được:

| ghi vào sổ | bị chặn vì |
|---|---|
| `b\|#tt \|kịch_bản\|-` sau một dòng cũng `#tt ` | **trùng magic** — *"dòng này không bao giờ tới lượt"* (Linux im lặng cho qua) |
| ngả lui `*` đặt ở **giữa** sổ | nó **nuốt hết** các dòng sau |
| sổ **không có** dòng `*` | tệp lạ sẽ không chạy nổi mà chẳng biết vì sao |
| `trình` không có thật | kèm luôn danh sách trình có thật |

Mỗi lỗi kèm **số dòng**, và **tệp cũ còn nguyên**. Mạnh hơn nữa: **xoá hẳn sổ đi máy vẫn chạy
lệnh**, vì ngả lui `dạng_mặc_định()` nằm **trong mã, không nằm trên đĩa**. *Không có cách nào làm
máy câm bằng cách phá sổ* — đúng chỗ `binfmt_misc` mong manh nhất.

**② Không nói được vì sao.** Linux ném `ENOEXEC`, hết. Ở đây:

```
an:/nhà/an$ định_dạng bốn_hai
/nhà/an/lệnh/bốn_hai: khớp định dạng 'mã_máy' (magic '#!mã-máy'),
chạy bằng trình 'mã_máy', cần năng lực 'máy' — máy CÓ cấp.
```

**③ Định dạng không khai được nó cần gì.** Đăng ký một thông dịch cho magic nào đó ở Linux là
trao trọn quyền, không ai hỏi. Ở đây mỗi dòng **tự khai năng lực** — cùng một lối với gói phần
mềm tự khai năng lực (kho, v0.18.0). Chưa cấp `máy` thì:

```
vỏ: /nhà/an/lệnh/giả_mã: khớp định dạng 'mã_máy' (magic '#!mã-máy'), chạy bằng trình
'mã_máy', cần năng lực 'máy' — máy CHƯA cấp, nên KHÔNG chạy được.
Bật bằng cờ --cho-máy lúc khởi động.
```

**Quyền vẫn xét TRƯỚC khi tra sổ**, nên thêm định dạng **không mở thêm cửa nào**: tệp mã máy
thiếu bit `x` vẫn bị chặn y hệt, ở cả hai chế độ. Kiểm: `kiem_dinh_dang.giao` chạy **hai lần**
(chưa cấp `máy` / đã cấp) — cùng một tệp, hai kết quả.

### Chi phí phải trả — và cái bẫy đã vấp

Tra sổ nằm trên **đường đi của mọi lệnh**. Bản đầu đọc rồi tách dòng, tách cột **mỗi lần chạy một
lệnh**; hậu quả là bản trình diễn `hdh_giao.giao` **chạm trần 5 triệu bước ngay lần chạy đầu** —
12 hạng mục nghiệm thu rớt một lượt, mà nhìn qua thì tưởng 12 lỗi khác nhau. Đúng cái bẫy §5.5 đã
ghi từ trước (procfs tái sinh mọi lời gọi + tra `$PATH`), chỉ là vấp lại ở chỗ mới.

Cách vá: **nhớ bản đã phân tích, khoá bằng CHÍNH nội dung thô của sổ** — không phải bằng một cờ
"đã đổi". Khác biệt quan trọng:

- sổ đổi một ký tự là bản nhớ **tự hết hiệu lực**, nên **không ai phải nhớ đi xoá bộ nhớ đệm**;
- cách kia ("xoá đệm mỗi khi ghi") phải rải lệnh xoá ra `GH_GHI` · `GH_TẠO` · `GH_THÊM` ·
  `GH_XOÁ` · `GH_BỎ` · `GH_CHUYỂN` — sáu chỗ, và **quên một chỗ là chạy sai mà bộ kiểm vẫn xanh**.

> **Đo sau khi vá:** bản trình diễn cần khoảng **4–5 triệu bước** (chạy được ở mức mặc định 5M,
> rớt ở 4M) — **chỉ còn dư chừng 20%**. Ghi ra đây để việc nào sau này đặt thêm chi phí lên đường
> đi của mọi lệnh thì **đo trước**, đừng đợi bộ kiểm đổ 12 hạng mục mới biết.

## 5.21 Tầng KHỐI + nhật ký — và ba chỗ ext4 thật còn yếu (B3)

Bền hoá trước đây là **chụp cả hệ ra JSON** (§5.7): đúng ở mức "ảnh", nhưng không có khối, không
có inode, không có nhật ký — nghĩa là không có câu trả lời cho câu hỏi *"mất điện giữa lúc ghi thì
sao?"*. B3 vá chỗ ấy. Và như thường lệ, **soi máy thật trước**:

| soi gì trên Kali 2026.2 (ext4) | trả về |
|---|---|
| `findmnt -no OPTIONS /` | `rw,relatime,discard,errors=remount-ro,`**`data=ordered`** |
| `tune2fs -l` | `Block size 4096` · `Inode size 256` · features … **`metadata_csum`** |
| `du -B1` trên tệp 1 byte | **4096** |
| `man 2 fsync` | *"does not necessarily ensure that the entry in the directory containing the file has also reached disk"* |

### ① `data=ordered`: nhật ký KHÔNG phủ dữ liệu

Đây là **mặc định trên máy thật**, không phải cấu hình lạ. Nó ghi nhật ký cho **siêu dữ liệu**
thôi. Hậu quả: mất điện giữa lúc ghi thì siêu dữ liệu có thể đã nói *"tệp dài 4 KB"* trong khi khối
dữ liệu còn là **rác của tệp cũ**. Hệ-tệp **tự nó nhất quán** — `fsck` không kêu gì — nhưng **nội
dung thì sai, và không ai báo**.

Ở đây nhật ký **chở cả khối dữ liệu**. Trình tự: gom mọi khối sắp đổi vào nhật ký → đặt **dấu cam
kết** (điểm nguyên tử) → chép ra khối thật → xoá nhật ký. Phép thử quyết định là **cắt điện đúng
hai điểm**:

```
cắt TRƯỚC cam kết   → PHÁT LẠI: giao dịch CHƯA cam kết → vứt 8 khối ⇒ giữ bản CŨ nguyên vẹn
                      đọc ra: "BẢN CŨ — phải còn nguyên sau khi mất điện"     ← đúng từng chữ

cắt SAU cam kết,    → PHÁT LẠI: giao dịch ĐÃ cam kết → chép tiếp 8 khối ⇒ giữ bản MỚI trọn vẹn
giữa lúc chép (4/8)   đọc ra: "BẢN MỚI dài hơn hẳn, trải ra nhiều khối…"      ← trọn vẹn
```

**Không có cửa nào cho "nửa cũ nửa mới"** — đúng chỗ `data=ordered` sẽ ra nội dung rác.

### ② `metadata_csum` không phủ dữ liệu người dùng

Khối dữ liệu mục thầm lặng thì ext4 **trả nó ra như thật**; muốn có checksum trên dữ liệu phải
sang btrfs/zfs. Ở đây **mỗi khối mang tổng kiểm**, và đọc phải khối hỏng thì **báo** — báo cả qua
**gọi-hệ**, nên chương trình không bao giờ nhận được rác:

```
gốc:/# xem /đĩa/thơ
xem: đọc 'thơ' hỏng: KHỐI 7 HỎNG — tổng kiểm không khớp
```

### ③ `fsync(tệp)` không làm bền cái TÊN

Chính trang man nói phải `fsync` **cả thư mục cha**. Nghĩa là độ bền của dữ liệu là **kiến thức
truyền miệng** mà ứng dụng phải tự biết; ai không biết thì mất dữ liệu, và mất im lặng. Ở đây
**tên và nội dung nằm cùng một giao dịch** — cắt điện trước cam kết thì **tên cũng không sinh ra**,
tệp cũ còn nguyên. Không có điệu nhảy fsync nào phải nhớ.

### ④ Không phải chỗ yếu — là cái giá thật

Khối 4096 B nghĩa là tệp 1 byte tốn 4096 byte. Tầng khối **không miễn phí**, và ta cũng phải trả.
Nên lệnh `đĩa` **hiện thẳng phần phí** thay vì giấu:

```
gốc:/# đĩa
ĐIỂM GẮN   TỆP     KHỐI              CHỖ
/đĩa       1 tệp   1/64 khối×32B     dùng 15B, phí 17B
```

### GẮN (mount): đường dẫn thường, tầng khối bên dưới

```
gốc:/# đĩa dựng /đĩa 64 32
đã dựng và gắn đĩa ở /đĩa (64 khối × 32 byte) — sạch — không có giao dịch dở
gốc:/# ghi /đĩa/thơ sen vàng nở sớm
gốc:/# xem /đĩa/thơ
sen vàng nở sớm
```

`ghi` · `xem` · `liệt` đi xuống tầng khối qua bốn cửa gọi-hệ. **Chỉ gốc-quyền được gắn** (như
`mount`), và **quyền của ĐIỂM GẮN quyết định** — đặt `/đĩa` về 700 thì người thường hết cả đọc lẫn
ghi. Tức **gắn đĩa không mở thêm cửa nào**. Gắn xong máy **luôn nói đã làm gì với nhật ký**; ext4
cũng phát lại lúc mount, nhưng hỏng nặng thì đòi **con người chạy `fsck`**.

> **Trung thực:** "đĩa" ở đây vẫn là cấu trúc **trong bộ nhớ** máy GIAO, **chưa phải mặt đĩa vật
> lý** — phần bền qua tắt máy vẫn nhờ ảnh chụp JSON (§5.7). Cái mới và thật sự có giá trị là
> **ngữ nghĩa**: khối · inode · tổng kiểm · nhật ký · gắn-và-phát-lại. Tổng kiểm dùng djb2 nên bắt
> hỏng **ngẫu nhiên**, **không** chống được kẻ **cố ý** sửa (muốn thế phải dùng `lib_sha256.giao`).
> Đĩa mới có **tệp phẳng** — chưa có thư mục con, chưa xoá tệp, chưa thu hồi khối, chưa gắn được `/`.

## 6. Trung thực về giới hạn hiện tại

> **Hồ sơ đầy đủ, thi hành được ngay: [`CÒN_THIẾU.md`](CÒN_THIẾU.md)** — mỗi mục ghi rõ bắt đầu ở
> tệp nào, kiểm bằng gì, và mục nào đang bị mục nào chặn.

Bốn chỗ đáng nêu ngay ở đây *(hai mục cũ — "chưa có phép bit" và "chưa có mạng" — đã XONG:
phép bit từ v0.11.0, mạng trong-máy v0.12.0, mạng ra host + đăng nhập từ xa v0.20.0)*:

- **Mật mã chưa qua thẩm định.** ChaCha20 · HMAC-SHA256 · RSA-2048 · Diffie-Hellman · KDF `$g3$`
  đều **đúng thuật toán và khớp vector chuẩn**, nhưng chưa ai soi về mặt an toàn. Riêng `$g3$`:
  có đúng **cấu trúc** khó-về-bộ-nhớ nhưng bảng mới 2 KB, còn xa scrypt/yescrypt (§5.19).
- **Phiên từ xa vẫn kẹp `127.0.0.1`.** Mở ra LAN là một quyết định khác hẳn, phải cân lại toàn bộ.
- **Đa nhiệm tiền định mới TỪNG PHẦN.** Tiến trình MÁY cắt ngang được (§5.10–5.11); vỏ/trợ lý/dịch vụ
  vẫn hợp-tác vì chúng cần `bản`/closure/`thử-bắt` — ngoài tập con `giaoc` biên dịch được.
- **Chưa cắm bo FPGA thật.** Bitstream đã dựng xong (§5.18) và đã kiểm tới từng bit trên dây UART;
  chỉ thiếu phần cứng trong tay.

`/lệnh` **đã mang được chính bytecode** từ v0.28.0 (§5.20) — nhưng vì hệ-tệp GIAO chứa chuỗi nên
từ-lệnh viết ra dạng **số thập phân**: cái đã đổi thật sự là *tệp mang MÃ chứ không mang NGUỒN*,
còn gọi là "nhị phân" thì vẫn là nói quá. Sổ định dạng cũng mới có **bốn trình chạy dựng sẵn**;
muốn cắm một trình NGOÀI (như `binfmt_misc` trỏ tới thông dịch bất kỳ) thì phải mở thêm.

## 7. Việc kế tiếp (đề xuất, theo thứ tự)

1. ~~Cho `sinh` chạy chương trình thật~~ — **XONG** (xem §5.4): `lib_chương_trình.giao` +
   `vòng_nhân` + `chạy`/`nhịp`/`việc`/`kể` trong vỏ; 55/55 nghiệm thu.
2. ~~`/lệnh` thành thư mục lệnh thật~~ — **XONG** (xem §5.5): tra `$PATH`, bit `x` có hiệu lực,
   kịch bản có đối số, tệp lệnh làm bệ phóng tiến trình, người dùng tự viết lệnh lúc đang chạy.
3. ~~Ống liên-tiến-trình thật (`GH_ỐNG`), rồi `&` chạy nền~~ — **XONG** (xem §5.6): chặn/đánh thức,
   phản áp, EOF, quyền trên ống, `bơm | lọc | hút` = 3 tiến trình thật, `&` chạy nền.
4. ~~Bền hoá: snapshot cả hệ-tệp + nhân ra JSON~~ — **XONG** (xem §5.7): `lib_bền.giao`,
   `--lưu`/`--nạp`, tiến trình dở dang chạy tiếp đúng chỗ.
5. ~~Trợ lý sinh lệnh (không chỉ chọn)~~ — **XONG** (xem §5.8): soạn theo mẫu + dò hệ-tệp (không cần
   LLM) hoặc để trái tim viết, rồi bắt buộc qua thẩm định + cổng phá huỷ + trình bày.

6. ~~Đa nhiệm tiền định: nối nhân γ-preempt lên tầng này~~ — **XONG một nửa, đúng nửa quan trọng**
   (xem §5.9): chính sách γ đã lên tầng HĐH và **trùng bit với silicon**; kẻ tham lam bị bóp. Nửa
   còn lại (cắt ngang giữa chừng) đòi biên dịch thân tiến trình xuống GVM.

7. ~~Biên dịch thân tiến trình xuống GVM để cướp được CPU~~ — **XONG** (xem §5.10): năng lực `máy`
   (`biên_dịch`/`máy_nạp`/`máy_lát`), tiến trình MÁY bị cắt đúng lượng tử, γ vẫn bóp kẻ vô ích.

8. ~~Thêm opcode gọi-hệ cho GVM~~ — **XONG** (xem §5.11): opcode 72 `GỌI_HỆ`, trap về nhân, chuỗi
   chạy hai chiều, quyền/cổng/audit giữ nguyên.

9. ~~Mở rộng để vỏ cũng xuống máy~~ — **XONG phần lõi** (xem §5.12): `vỏ_máy.giao` phân giải lệnh
   + so sánh chuỗi + gọi syscall, tất cả bằng bytecode; hai gọi-hệ `lệnh`/`từ` làm bàn phím.

10. ~~Đưa dịch vụ nền xuống máy~~ — **XONG** (xem §5.13): `nhật_ký_máy.giao` ngủ trên hàng đợi,
    dậy khi có tin, ghi qua gọi-hệ, ngủ lại — không quay vòng bận.

11. ~~Trái tim thành thiết bị để trợ lý xuống máy~~ — **XONG** (xem §5.15): gọi-hệ 27/28 + `/tb/tim`;
    `trợ_lý_máy.giao` chấm γ, chọn, từ chối — bằng bytecode.
12. ~~Gọi-hệ trên cổng logic~~ — **XONG** (xem §5.14): opcode 72 trong `hw/gvm.v`, iverilog, trùng khít.

13. ~~Đồng mô phỏng: nối nhân GIAO thật vào chân trap~~ — **XONG** (xem §5.16).

14. ~~Trap phần cứng ≥2 đối~~ — **XONG** (xem §5.14): trạng thái `S_TRAPA` moi thêm tầng ngăn xếp,
    nhận 0–3 đối; silicon **tạo được tệp thật** bằng `gọi_hệ(2, đường, quyền, nội)`.

15. ~~Thay điểm hẹn tệp bằng VPI~~ — **XONG** (xem §5.17): `$giao_trap` là hàm hệ thống trong chính
    bộ mô phỏng; gọi-hệ tốn đúng 2 chu kỳ, mô phỏng trở lại tất định.

16. ~~Tổng hợp `gvm.v` ra bitstream FPGA~~ — **XONG** (xem §5.18): yosys → nextpnr-ecp5 → ecppack,
    bytecode nằm sẵn trong ROM; đỉnh `gvm_bo.v` nối nhân qua UART, đã kiểm tới từng bit trên dây.

17. ~~Đăng nhập nhiều người · nhóm · sudo · **đăng nhập từ xa có mã hoá**~~ — **XONG** (xem §5.19 và
    `CÒN_THIẾU.md` mục C): kênh ChaCha20 + HMAC + Diffie-Hellman có bí mật chuyển tiếp, **đổi khoá
    giữa phiên do máy chủ ÉP**, chống dò mật khẩu, băm `$g3$` khó về bộ nhớ.

18. ~~B2: `/lệnh` mang chính bytecode~~ — **XONG** (xem §5.20): sổ `/hệ/định_dạng` theo hình dạng
    `binfmt_misc` (vá 3 chỗ nó yếu) + định dạng `#!mã-máy` + lệnh `dịch` / `định_dạng`.
19. ~~B3: khối / inode / mount~~ — **XONG phần NGỮ NGHĨA** (xem §5.21): `lib_dia.giao` với nhật ký
    **phủ cả dữ liệu** (vá `data=ordered`), tổng kiểm từng khối (vá `metadata_csum`), tên+nội dung
    cùng giao dịch (vá bẫy `fsync`), và `gắn_đĩa` treo vào cây thư mục.

**Việc lớn còn lại (theo `CÒN_THIẾU.md`, nguồn sự thật):**
- **cắm bo FPGA thật** — bitstream đã có, nạp chỉ là một lệnh (`python hw/lam_bitstream.py --nạp`),
  nhưng phải có phần cứng trong tay. Đây là việc duy nhất cần **mua đồ**.
- **B3 phần còn lại:** đĩa xuống **mặt đĩa vật lý** thật · thư mục con · xoá tệp + thu hồi khối.
- **B4** tiền định trọn vẹn cho cả vỏ/dịch vụ.
- **G1/G4** đuôi bàn làm việc: biểu tượng trên nền · nhiều bàn ảo · danh sách cửa sổ · nhiều phiên
  đồ hoạ song song.

---
*Nền học thuyết: DFCT / NNL-NTHT / CDFL — Nguyễn Trường An. Tệp liên quan:
`lib_tệp_hệ.giao` · `lib_gọi_hệ.giao` · `lib_vỏ.giao` · `lib_trợ_lý.giao` · `hdh_nền.giao` ·
`lib_chương_trình.giao` · `hdh_giao.giao` · `hdh_tiến_trình.giao` · `hdh_ống.giao` · `lib_bền.giao` · `hdh_bền.giao` · `lib_lịch_γ.giao` · `hdh_tiền_định.giao` · `hdh_máy.giao` · `hdh_máy_gọi_hệ.giao` · `vỏ_máy.giao` · `chay_vo_may.py` · `nhật_ký_máy.giao` · `chay_dv_may.py` · `lib_trợ_lý.giao` ·
`chay_hdh_giao.py` · `lib_dinh_dang.giao` · `kiem_dinh_dang.giao` · `lib_dia.giao` · `kiem_dia.giao` ·
`lib_mật_khẩu.giao` · `lib_người_dùng.giao` · `lib_tu_xa.giao` · `lib_kenh.giao` ·
`lib_dh.giao` · `chay_hdh_xa.py` · `khach_xa.py` · `kiem_ro_ri_thoi_gian.giao` · `kiem_chong_do.giao` ·
`hw/gvm.v` · `hw/giao_vpi.c` · `hw/cosim_vpi_tb.v` · `hw/lam_cosim_vpi.py` ·
`hw/gvm_bo.v` · `hw/uart.v` · `hw/ulx3s_top.v` · `hw/ulx3s.lpf` · `hw/nhan_qua_uart.py` · `hw/lam_bitstream.py` ·
`kiem_hdh_giao.py`.*

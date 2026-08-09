# GIAO — Ngôn ngữ lập trình của Vùng Giao Thoa

> Ngôn ngữ lập trình cho AI, xây trực tiếp trên học thuyết **Lưỡng Trường Hội Tụ
> (DFCT / NNL-NTHT / CDFL)** của Nguyễn Trường An.
> Không vay mượn mô hình tính toán của bất kỳ ngôn ngữ nào hiện có.

> **📌 Trạng thái hiện tại (nguồn-sự-thật: `TIEN_DO.md`):** `python kiem_toan_bo.py` = **72/72 hạng mục** ·
> ngôn-ngữ **74/74** · HĐH **385/385** · bàn làm việc **41/41** · đăng nhập từ xa **37/37** ·
> wasm 20/20 · gate-level Verilog chạy thật bằng `iverilog` (gọi-hệ trên cổng logic · đồng mô phỏng
> nhân GIAO). Các con số rải rác trong tài liệu này / `CHANGELOG.md` là ảnh-chụp theo mốc lịch-sử —
> khi cần trạng-thái mới nhất hãy đọc `TIEN_DO.md` (đã cập-nhật mỗi phiên).
>
> **Hồ sơ việc-cần-làm:** `CÒN_THIẾU.md` · **HĐH:** `HDH_GIAO_LINUX.md`.

---

## 1. Tại sao phải thay bit nhị phân?

Mọi máy tính ngày nay đứng trên **bit {0, 1}**. Đó là một thế giới quan ngầm:
mọi mệnh đề **hoặc đúng (1) hoặc sai (0)**, luôn xác định, không có chỗ cho
*cái chưa biết*, và **không có chủ thể quan sát**. Từ khuyết điểm gốc rễ này sinh ra:

| Khuyết điểm của thế giới nhị phân | Hệ quả thực tế |
|---|---|
| Không phân biệt "sai" với "chưa biết" | `null` / `undefined` → "lỗi tỉ đô" (Tony Hoare) |
| Không có chủ thể / niềm tin | Chương trình không biết nó *đang tin gì*, không tự hiệu chỉnh |
| Không đo được độ tin (chỉ True/False) | Không phân biệt **tri thức thật** với **ảo tưởng tự tin** (vấn đề an toàn AI) |
| Giá trị là chết, gán cứng | Không có khái niệm *học*, *hội tụ* — AI phải bắc giàn giáo bên ngoài |

GIAO thay nền tảng đó bằng **bộ ba có cộng hưởng**, lấy thẳng từ học thuyết:

```
        sáng              ẩn               tối
     (γ > 0)           (γ = ∅)          (γ < 0)
  biết-ĐÚNG        CHƯA biết         ẢO TƯỞNG
  ∈ vùng OR        ∈ vùng DE      đốm tối trong OR
```

Nhị phân là trường hợp suy biến của GIAO khi **cấm vùng tối** (ép mọi thứ về sáng/tối,
xoá `ẩn`) và **bỏ γ** (chỉ giữ dấu). GIAO tổng quát hơn, không nghèo hơn.

---

## 2. Ánh xạ học thuyết → ngôn ngữ

| Khái niệm CDFL/DFCT | Hiện thân trong GIAO |
|---|---|
| **RF** — trường gốc | Giới hạn lý tưởng, không mô hình trực tiếp (chân trời) |
| **IF** — tâm trường (niềm tin σ) | không gian tên `tâm` |
| **MF** — vật trường (thực tại ρ) | không gian tên `vật` |
| **OR** — vùng giao thoa = tri thức | toán tử `giao ... = tâm A ⋈ vật B` → giá trị `tri` |
| **DE** — vùng tối bốn mặt | giá trị `ẩn` (hạng nhất) + truy vấn `de` |
| **γ** — độ cộng hưởng | trường `γ` trong mỗi `tri`; quyết định sáng/tối |
| **Động học IF** (tiên đề 5) | lệnh `học X`: σ ← σ + α·(ρ − σ) |
| **Viên mãn cục bộ "Aha!"** | `khi viên_mãn <tri> { ... }` (kích hoạt khi γ ≥ 0.99) |
| **Đốm tối** (ảo tưởng, γ<0) | `tri` có `state = tối` → bài toán hiệu chỉnh/an toàn |
| **Nhận thức ba trị** | rẽ nhánh ba ngả `nếu / ngờ / khác` |

**"Ngôn ngữ cho AI"** ở đây mang nghĩa mạnh nhất: AI **không phải thư viện** gọi kèm,
mà là **chính ngữ nghĩa thực thi** — một chương trình GIAO *bản chất là một tác tử*
quan sát thực tại, nuôi niềm tin, và hội tụ.

---

## 3. Cú pháp (bản v0.1)

Mọi từ khoá có cả bản **có dấu** và **ASCII không dấu** (vd `tâm`=`tam`, `học`=`hoc`).

```
vật  <tên> = <bt>          # khai báo ô thực tại  (MF)
tâm  <tên> = <bt>          # khai báo ô niềm tin   (IF);  có thể = ẩn
học  <tên>                 # 1 bước động học: kéo tâm.<tên> về vật.<tên>
giao <kq> = tâm A ⋈ vật B  # tạo tri thức OR (γ);  dạng tắt:  giao <kq> = X
giao <kq> = X              #   ⇔  giao <kq> = tâm X ⋈ vật X     ( ~ thay được ⋈ )

rọi  <bt>                  # "rọi sáng" / in ra (kèm γ nếu là tri)
lặp  <n> { ... }           # vòng lặp đếm trước (mô phỏng vòng học hữu hạn)
lặp  <x> trong <ds> { ... } # DUYỆT danh sách/chuỗi — KHÔNG đệ quy (xử lý dữ liệu lớn không tràn ngăn xếp)

mãi  { ... }               # vòng LIÊN TỤC thật (continual) — chạy tới khi `dừng`
dừng                       # thoát vòng (mãi/lặp)
trôi <ô> = <bt>            # đăng ký ĐỘNG HỌC riêng của thế giới cho ô vật (một lần)
trôi                       # một NHỊP thời gian: áp mọi luật trôi → ρ_MF tự dịch → DE_T mọc lại

nhập "tệp.giao"            # MODULE: nạp định nghĩa từ tệp khác (chỉ .giao trong cây dự án; idempotent)

nếu <bt> { ... }           # rẽ nhánh BA NGẢ theo logic ba trị:
ngờ      { ... }           #   sáng → nếu | ẩn → ngờ | tối → khác
khác     { ... }

khi viên_mãn <tri> { ... } # kích hoạt khi γ ≥ 0.99  (khoảnh khắc "Aha!")
de                         # biểu thức: báo cáo Vùng Tối (DE_IF, DE_MF)
```

**Giá trị nền:** số, chuỗi `"..."`, danh sách `[...]`, **bản** (map/record — kiểu tham chiếu,
tra cứu O(1): `bản()`/`đặt_khoá`/`lấy_khoá`/`có_khoá`/`m[khoá]`, thiếu khoá → `ẩn`), hàm
(hạng nhất), và ba hằng cộng hưởng `sáng` / `tối` / `ẩn`.

**An toàn `ẩn`:** mọi phép toán chạm `ẩn` đều trả `ẩn` (không crash). Chia cho 0
cũng ra `ẩn` (vùng tối), không nổ chương trình. Đây là cách GIAO diệt `null`.

---

## 4. Tầng nền nhị phân — GIAO mọc TỪ 0 và 1 (`gvm.py`)

"Máy tính bắt đầu từ 0 và 1" — nên GIAO cũng phải mọc lên **từ** 0 và 1, chứ không
phải từ Python. Tệp `gvm.py` chứng minh điều đó bằng cách dựng cả ngăn xếp từ đáy:

```
Tầng 0: bit ∈ {0,1}                         (vật lý)
Tầng 1: NAND → NOT, AND, OR, XOR            (đại số Boole từ 1 cổng vạn năng)
Tầng 2: bộ cộng ripple → số học 16-bit      (cộng/trừ/dịch — thuần bit)
Tầng 3: TRIT = 2 bit → sáng/tối/ẩn          (đơn vị cộng hưởng của GIAO)
Tầng 4: logic ba trị Kleene                 (Boole = trường hợp SUY BIẾN khi cấm 'ẩn')
Tầng 5: vòng hội tụ CDFL chạy bằng DỊCH BIT
```

Hai kết quả cốt lõi `gvm.py` in ra:
- **"nhị phân là trường hợp suy biến → True"**: cấm trạng thái `ẩn` thì logic ba trị
  Kleene **trùng khít** đại số Boole. GIAO *bao trùm* nhị phân, không mâu thuẫn.
- Vòng hội tụ dừng ở 36 (thiếu 1 so với 37) → **chạm "sàn tối" D_min>0**: minh hoạ
  bằng máy tiên đề 12 (luôn còn vùng tối, không viên mãn toàn cục).

**Vai trò của Python bị HẠ XUỐNG.** Trong `gvm.py`, Python chỉ cung cấp **một cổng
NAND** (đóng vai transistor) — thứ có thể thay bằng silicon thật. Mọi ngữ nghĩa GIAO
(trit, cộng hưởng, hội tụ) nằm ở tầng bit do ta tự dựng, **không** do Python biểu đạt.
Đây là khác biệt then chốt với `giao.py`: ở đó Python còn là "ngôn ngữ mồi"; ở đây
Python chỉ còn là "phần cứng mô phỏng".

### 4b. CPU của GIAO — máy bytecode trit/γ (`gvm_may.py`)

Đặt thẳng trên ALU của `gvm.py` (số học bắt nguồn từ cổng NAND), `gvm_may.py` dựng
**một CPU mà ô nhớ không phải từ-nhị-phân-thuần** mà là **ô trit–cộng hưởng**:
`[trạng thái 2 bit][giá trị 16 bit][γ 8 bit]`. Ba điểm khác mọi CPU hiện có:

- **`ẩn` (DE) lan truyền ở tầng máy**: `CỘNG`/`TRỪ` chạm ô ẩn → ô ẩn (không sinh rác).
- **Rẽ nhánh theo CỘNG HƯỞNG, không theo cờ-zero**: lệnh `NHẢY_NẾU_ĐỘNG` nhìn vào việc
  niềm tin *còn dịch* hay đã *chạm sàn tối* (viên mãn cục bộ) — thay cho ZF/CF/SF.
- **Bộ lệnh mang ngữ nghĩa học thuyết**: `HỌC`, `GIAO`, `VẬT`/`TÂM` là opcode gốc, không
  phải lời gọi thư viện.

`python gvm_may.py` in ra mã máy 16-bit/lệnh rồi chạy vòng hội tụ CDFL bằng chính bytecode đó.

### 4c. Chuỗi mồi của ASSEMBLER — không mượn ngôn ngữ lập trình

Trình hợp dịch **không** được phép viết bằng Python (đó lại là mượn ngôn ngữ khác).
Như mọi assembler trong lịch sử, nó phải được **gieo mầm bằng tay** đúng một lần:

```
Mức 0  gasm_tay.py   — mã máy GÕ TAY từng bit (con người dịch từ bảng opcode).
                       Python CHỈ là CPU nạp–giải mã–thực thi. KHÔNG dịch gì.
Mức 1  gasm_tay2.py  — một ASSEMBLER tối giản VIẾT BẰNG HỢP NGỮ GVM (26 lệnh),
                       rồi GÕ TAY thành mã máy. Nó đọc cặp (opcode, operand) từ RAM,
                       đóng gói word=(op<<8)|arg, ghi ra. 'Hành vi hợp dịch' giờ chạy
                       bằng chính máy — đã mồi xong, không qua hàm Python nào.
Mức 2  gasm_tay3.py  — assembler ĐỌC VĂN BẢN (65 lệnh gõ tay): nhận chuỗi ASCII
                       "H0G0R0D0.", SO KHỚP ký tự mnemonic (H→7,G→8,R→14,D→0) bằng
                       chuỗi so sánh nội tuyến, đổi chữ số ASCII→trị, đóng gói & ghi ra.
                       Đây là 'hợp ngữ văn bản' thật, dịch hoàn toàn bằng máy gõ tay.
Mức 3  gasm_tay4.py  — assembler có NHÃN + toán hạng NHIỀU CHỮ SỐ (136 lệnh gõ tay):
                       bảng nhãn ở RAM, tham chiếu "@L" giải thành địa chỉ. Nhờ đó hợp
                       dịch được CHƯƠNG TRÌNH CÓ VÒNG LẶP — hợp dịch trọn VÒNG HỘI TỤ CDFL.
Mức 4  gasm_tay5.py  — TỰ THÂN HOÁ (self-hosting): assembler đọc CHÍNH mã nguồn của nó
                       (viết bằng ngôn ngữ đầu vào của nó) và sinh lại ĐÚNG mã máy của
                       chính nó (ĐIỂM BẤT ĐỘNG A'==A từng byte). Rồi bản tự sinh A' CHẠY
                       THẬT — tự hợp dịch chương trình khác. Python đã ra hẳn khỏi đường mồi.
```

`python gasm_tay{2,3,4,5}.py` chứng minh end-to-end. Mức 3 hợp dịch `"T00:LH00G00R00J@LD00$"`
(có nhãn) → `TÁC_TỬ 0 / HỌC 0 / GIAO 0 / RỌI / NHẢY_ĐỘNG 1 / DỪNG`, chạy ra TRỌN vòng hội tụ.
Mức 4 đạt **điểm bất động**: A'==A — phép thử tự thân mà mọi trình tự-biên-dịch (C, Go, Rust)
đều phải vượt. `assemble_text()` trong `gvm_may.py` chỉ là **giàn giáo soạn thảo**, KHÔNG mồi.

> **Trung thực về Mức 4:** tự thân hoá đạt ở **tầng mã máy** — ngôn ngữ nguồn của A là dãy
> cặp (op, operand) = đúng cái máy thực thi, nên A tái tạo A trọn vẹn. Bản tự thân ở tầng
> *mnemonic văn bản* (assembler chữ tự hợp dịch nguồn-chữ của nó) là MỞ RỘNG CƠ HỌC cùng ý
> tưởng: cần mnemonic cho cả ~31 opcode + toán hạng 3 chữ số + nhãn tiến hai lượt — lớn hơn
> nhưng không khó hơn về nguyên lý. Điểm bất động A'==A đã chứng minh nguyên lý đó đứng vững.

## 4d. Tự thân hoá TẦNG NGÔN NGỮ — GIAO diễn giải GIAO (`examples/giao_core.giao`)

Song song với chuỗi mồi assembler (tầng máy), GIAO cũng tự thân ở **tầng ngôn ngữ**: một
**trình diễn giải GIAO viết bằng chính GIAO** (metacircular, kiểu `eval` của Lisp). Chương
trình GIAO-Core được biểu diễn bằng **danh sách GIAO** (đồng hình):

```
số → chính nó | ["biến","x"] | ["+",a,b] | ["nếu",c,t,e] | ["để",tên,v,thân] | ["giao",IF,MF]
```

`eval(nút, môi_trường)` (viết bằng hàm + đệ quy của GIAO v0.2) duyệt cây, tra cứu biến,
ràng buộc `để` (let), và tính **giao thoa** (sáng nếu IF khớp MF, tối nếu lệch). Khi GIAO
mô tả được chính ngữ nghĩa của nó ⇒ ngôn ngữ đủ mạnh để tự thân. `python giao.py
examples/giao_core.giao` chạy 5 ca (số học, giao thoa, let lồng nhau...) đều đúng.

**Bản đầy đủ `examples/giao_core2.giao`** mở rộng trình diễn giải lên *toàn bộ* GIAO:
**hàm + đệ quy + gọi**, **lặp**, và **trường tâm/vật + học + giao thoa**. Trạng thái thay
đổi (tâm/vật/đặt/học) được mô hình bằng **store kiểu danh sách kết hợp** — cập nhật = thêm
binding mới che binding cũ (thuần danh sách, threading store qua từng câu lệnh). Chạy đúng
cả `cộng_dồn(5)=15` (đệ quy) lẫn vòng hội tụ CDFL `σ: 0→36.71` (tâm/vật/học/lặp).

### 4e. ★ HỢP LƯU A+B — biên dịch GIAO → bytecode GVM (`giaoc.py`)

Điểm hội tụ cuối: `giaoc.py` **biên dịch** mã nguồn GIAO (mạch A) **xuống bytecode GVM**
(mạch B), rồi chạy trên máy trit/γ nền NAND. Sau biên dịch, **Python KHÔNG diễn giải ngữ
nghĩa GIAO nữa** — nó chỉ mô phỏng transistor; ngữ nghĩa GIAO nằm trong bytecode, do CPU
GVM thực thi. Các lệnh CDFL ánh xạ THẲNG sang opcode máy:

```
vật ô=v → NẠP v;LƯU_VẬT a   tâm ô=ẩn → ẨN;LƯU_TÂM a   học ô → HỌC a
giao k=ô → GIAO a            rọi k → RỌI               lặp N{} → vòng đếm bằng NHẢY_NẾU_0
```

`python giaoc.py examples/hoi_tu_biendich.giao` biên dịch vòng hội tụ CDFL thành 17 từ-lệnh
GVM rồi chạy: niềm tin học `0→18→27→…→36`, γ tăng `−0.03 → +0.95`.

**Tự thân hoá trình biên dịch — `examples/giaoc.giao` + `chay_giaoc.py`:** trình biên dịch
GIAO→bytecode GVM nay được **viết lại bằng CHÍNH GIAO** (cấp phát ô nhớ, rải nhãn nhảy cho
vòng lặp — tất cả bằng danh sách GIAO thuần, threading trạng thái). `python chay_giaoc.py`
chạy trình biên dịch-GIAO đó (trên `giao.py`), lấy bytecode nó sinh, rồi nạp vào GVM — ra
ĐÚNG 17 từ-lệnh và trọn vòng hội tụ. Logic biên dịch giờ là GIAO; Python chỉ host trình
thông dịch + làm CPU.

### 4f. ★ HÀM + ĐỆ QUY chạy trên máy NAND (tinh khiết tận cùng)

GVM được thêm **cơ chế gọi hàm**: opcode `GỌI`/`TRẢ_VỀ`/`THAM` + ngăn xếp tham số &
địa chỉ trả về (quy ước 1 tham số). `giaoc` mở rộng biên dịch **hàm, đệ quy, `nếu`, `trả`**.
`python giaoc.py examples/giai_thua.giao` biên dịch hàm ĐỆ QUY `giai_thừa(5)` thành 20
từ-lệnh GVM rồi chạy trên máy trit/γ → `sáng=120`. Đệ quy thực thi thật sự bằng `GỌI`/
`TRẢ_VỀ` trên ngăn xếp máy — **mô hình tính toán đầy đủ (Turing-complete) chạy KHÔNG qua
Python**; Python chỉ là CPU.

### 4g. DANH SÁCH trên HEAP của máy (dời GIAO sang neo vào MÁY)

RAM của GVM được nới **256 → 65536 ô** (vốn chỉ là tham số mặc định). Trình biên dịch nay
hiểu **danh sách = cons-cell trên heap**: `[a,b,c]` → cấp ô heap `cons(a,cons(b,cons(c,NIL)))`,
`đầu` = đọc ô đầu, `đuôi` = đọc con trỏ kế (NIL=0). Hằng 16-bit nạp bằng `NẠP cao;DỊCH_TRÁI 8;
NẠP thấp;CỘNG`. `python giaoc.py examples/8_tong_ds_gvm.giao` biên dịch **hàm đệ quy cộng
danh sách** `tổng([10,20,30,40])` → chạy trên máy → `sáng=100` — **danh sách + đệ quy +
điều kiện đồng thời trên máy NAND**, Python chỉ là CPU.

**CHUỖI + `dài`/`ghép` trên máy** (`9_chuoi_gvm.giao`): chuỗi = danh-sách mã-ký-tự trên heap;
`dài`/`ghép` biên dịch thành vòng lặp + cấp heap; opcode `RỌI_CHUỖI` in chuỗi bằng duyệt heap.
`ghép("Giao"," thoa")` → `Giao thoa`, `dài`=9. Khi chương trình vượt **256 lệnh** (string/list
sinh nhiều mã), toán hạng nhảy 8-bit không đủ → đã thêm **nhảy/gọi GIÁN TIẾP** (`NHẢY_X`/
`NHẢY_NẾU_0_X`/`GỌI_X`, địa chỉ 16-bit lấy từ ngăn xếp). Chuỗi assembler gõ tay (A'=A) **không
đổi** vì vẫn dùng lệnh 8-bit cũ.

**HÀM NHIỀU THAM SỐ** (`10_nhieu_thamso_gvm.giao`): GVM thêm quy ước gọi theo **KHUNG** —
`GỌI_N` (đẩy N đối vào khung trên ngăn xếp tham số), `THAM_I i` (đọc tham số thứ i),
`TRẢ_VỀ_N` (bỏ khung). `luỹ(2,10)=1024` (đệ quy 2 tham số), `cộng(luỹ(2,5),100)=132` (gọi
lồng). Đây là mảnh then chốt để tiến tới **biên dịch chính `giaoc.giao` xuống máy**.

**LẬP CHỈ MỤC + SO SÁNH + COMPILE GỌN** (`11_chiso_sosanh_gvm.giao`): `l[i]` = đi i bước
`cdr` rồi `car`; so sánh `< > <= >= == !=` thêm 6 opcode GVM (đẩy 1/0), nhánh `nếu` dùng
chung một đường. **Tối ưu tốc độ biên dịch:** `dài`/`ghép`/`l[i]` nay là **hàm trợ giúp phát
MỘT LẦN** (`__dài`/`__ghép`/`__lấy`) gọi qua `GỌI_N` — mỗi chỗ dùng chỉ vài lệnh thay vì
nội tuyến hàng chục lệnh ⇒ mã ngắn, biên dịch nhanh. `phân_loại`(</>), `đếm_từ(l,20)=2`
(đệ quy 2 tham số + `>=` + `đầu`/`đuôi`) chạy đúng trên máy. Còn lại để biên dịch trọn
`giaoc.giao`: vài builtin (`là_ds`/`là_số`) — mở rộng cơ học.

> **Tinh khiết tận cùng — đúng hướng "máy làm hạt mồi":** tầng assembler (`gasm_tay5`, A'=A)
> ĐÃ neo vào MÁY (NAND), không vào Python-như-ngôn-ngữ. Việc đang làm là **dời GIAO xuống
> cùng tầng đó** bằng cách biên dịch dần ngôn ngữ (đã có: số học, hàm, đệ quy, điều kiện, vòng
> lặp, **danh sách/heap**) xuống GVM. Mắt xích ngôn ngữ Python duy nhất còn lại là `giao.py`;
> khi biên dịch đủ nhiều GIAO xuống máy, hạt mồi thật chỉ còn **một cổng NAND (vật lý)** —
> Python ở `gvm.py` chỉ mô phỏng cổng đó, vai trò mà silicon/FPGA sẽ thay.

> **Toàn cảnh:** một cổng NAND → ALU → CPU trit/γ → chuỗi mồi assembler tự thân
> (`gasm_tay5.py`, A'=A) → ngôn ngữ GIAO (`giao.py`) → tự diễn giải (`giao_core.giao`) →
> **biên dịch xuống máy** (`giaoc.py`). Cả ngăn xếp đứng trên chính nó, mọc từ 0 và 1.

## 5. Chạy thử

```bash
python giao.py                            # ★ REPL — vòng đọc–tính–in (không tham số tệp); .trợ_giúp / .thoát
python wasm/lam_playground.py             # ★ sinh wasm/playground.html — viết & chạy GIAO TRONG TRÌNH DUYỆT (Pyodide, KHÔNG Node/cài gì)
python gvm.py                             # TẦNG NỀN: từ NAND → trit → hội tụ bằng bit
python gvm_may.py                         # CPU GIAO: bytecode trit/γ chạy vòng hội tụ
python gasm_tay.py                        # MỒI Mức 0: mã máy gõ tay (không assembler Python)
python gasm_tay2.py                       # MỒI Mức 1: assembler (cặp số) viết bằng hợp ngữ
python gasm_tay3.py                       # MỒI Mức 2: assembler ĐỌC VĂN BẢN, gõ tay
python gasm_tay4.py                       # MỒI Mức 3: assembler có NHÃN, hợp dịch vòng lặp
python gasm_tay5.py                       # MỒI Mức 4: TỰ THÂN HOÁ — điểm bất động A'==A
python giao.py examples/1_hoi_tu.giao     # vòng hội tụ CDFL → "Aha!"
python giao.py examples/2_an_toan.giao    # ẩn lan truyền an toàn, rẽ nhánh 3 ngả
python giao.py examples/3_ao_tuong.giao   # đốm tối (γ<0) → hiệu chỉnh → tri thức thật
python giao.py examples/4_thu_bat.giao     # ổn định & an toàn: thử/bắt + lỗi sạch + sandbox
python giao.py examples/5_thu_vien.giao    # thư viện chuẩn: bản_đồ/lọc/gấp + số học + chuỗi
python giao.py examples/6_cdfl.giao        # TẦNG HỌC THUYẾT: chọn + DE bốn mặt + OR tập thể
python giao.py examples/cdfl_sau.giao      # CDFL SÂU: đốm tối/đốm sáng + empowerment
python giao.py examples/if_sigma_phi.giao  # σ/Φ hai nhánh (đa-Φ ensemble)
python giao.py examples/vong_lien_tuc.giao # vòng liên tục drift (không viên mãn toàn cục)
python giao.py examples/chon_bon_mat.giao  # chọn bốn-mặt (ưu tiên trồi sáng>soi tối>làm tươi)
python giao.py examples/giao_viec.giao     # GIAO VIỆC cho AI (N tài nguyên) — viết bằng GIAO
python giao.py examples/nao_cdfl.giao      # ★ BỘ NÃO CDFL (port từ Ruby): lookahead + coverage + consent gate
python giao.py examples/transition_model.giao  # Ψ học được (port Ruby TransitionModel): quan sát→dự đoán
python giao.py examples/boltzmann.giao     # chọn Boltzmann (port Ruby): explore/exploit theo nhiệt độ
python giao.py examples/hilbert.giao       # độ đo Hilbert I(I:M) (port Ruby): thông tin tương hỗ tâm–vật
python giao.py examples/cung_dien.giao     # cung điện ký ức (port Ruby): 4 tầng × 5 loại, tin-cậy phân rã, truy xuất
python giao.py examples/tich_hop.giao      # ★ TÍCH HỢP Ψ→lookahead: lookahead lái trên mô hình TỰ HỌC (tránh ngõ cụt, không bịa)
python giao.py examples/trai_tim.giao      # ★♥ TRÁI TIM: LLM local bơm σ/Φ → não CDFL kiểm γ + đốm tối + cổng phê duyệt
python giao.py examples/tim_vong.giao      # ★♥ TIM ⟂ VÒNG LIÊN TỤC: nhúng σ/Φ vào nhân-AI bốn-mặt, thế giới trôi → đập mãi
python giao.py examples/tim_tich_hop.giao  # ★♥ TIM SINH ỨNG VIÊN → planner: tim tỉa 6→3 hành động, não lookahead Ψ kiểm & chọn
python giao.py examples/tac_tu.giao         # ★★♥ TÁC TỬ HOÀN CHỈNH: gộp cả 3 (sinh+kiểm+lookahead) + ký ức + thế giới trôi → đập mãi
#   TIM THẬT: cài Ollama (winget install Ollama.Ollama), pull llama3.2:1b + bge-m3 → tự dùng, KHÔNG sửa GIAO.
#   Mặc định tim_llm.py: sinh=llama3.2:1b, nhúng=bge-m3 (đa ngữ, γ tiếng Việt SẮC: đúng~0.71 > ảo~0.52 > lạc~0.34).
#   Đổi model qua GIAO_LLM_MODEL / GIAO_EMB_MODEL. Tiền tố nhúng tự bật cho nomic, tắt cho bge-m3 (theo tên model).
#   τ trong các demo tim đã hiệu chỉnh cho thang bge-m3 (trai_tim/tim_vong 0.55, tac_tu 0.45).
python giaoc.py examples/tac_tu_may.giao    # ★★ LÕI QUYẾT ĐỊNH tác tử BIÊN DỊCH XUỐNG GVM: Ψ+lookahead+cổng phê duyệt chạy như mã máy
#   (trái tim LLM ở NGOÀI — là cơ quan I/O; lõi số nguyên neo vào silicon. Khớp thông dịch: −3≡65533 16-bit.)
python hw/lam_verilog.py                     # ★★★ NEO XUỐNG VERILOG THẬT: GIAO→bytecode→gvm.v (iverilog/vvp), lõi tác tử chạy gate-level
#   cần Icarus Verilog (winget install Icarus.Verilog). CPU DỪNG sau 1,191,838 chu kỳ clock (đo từ testbench),
#   RỌI khớp 4 tầng (thông dịch/GVM mềm/model/Verilog): 13 giá trị — [65533, 0] lặp 6 lần rồi 0
#   (65533 ≡ −3 ở 16-bit). GVM phần mềm & Verilog gate-level trùng TỪNG GIÁ TRỊ.
# hw/fpga/  — ★★★ GÓI FPGA: gvm_fpga.v (wrapper instantiate gvm.v THẬT, rút ~45 chân→5 khớp iCEBreaker) + gvm_fpga.pcf + gvm_core (DI-SẢN, KHÔNG synth) + gvm_top (LED+UART)
#   ★★ RA BITSTREAM iCE40 UP5K THẬT (2026-06-19): yosys synth_ice40 -json → nextpnr-ice40 --up5k sg48 PASS → icepack → gvm_fpga.bin (104.090 byte).
#   Số CHỐT (hw/fpga/nextpnr.log post-route): Fmax 14.04 MHz (PASS @12MHz) · LC 3680/5280 (69%) · BRAM 6/30 · DSP 2/8. 16/16 harness gate-level byte-exact.
yosys -s hw/synth_gvm.ys           # YOSYS TỔNG-HỢP core CHÍNH gvm.v XUỐNG CỔNG (ba-trị+γ-scheduler+SIP+4-nhân)
#   → 527,948 cells generic (AND/OR/MUX/XOR/NOT + ~13.4k DFF) + ALU adderN(NAND), MEM=256, KHÔNG LỖI. (cần OSS CAD Suite: PATH có bin+lib)
#   ⇒ "xuống silicon" THANG: (1) iverilog-sim ✓ · (2) yosys-synth ✓ · (3) FPGA-fit UP5K ✓ · (4) nextpnr place&route + bitstream ✓ · (5) timing-12MHz ✓ · (6) nạp chip vật-lý ⏳ (chỉ thiếu board iCEBreaker).
#   ⚠ TRUNG-THỰC: ĐÃ có bitstream THẬT (place&route PASS), CHƯA nạp chip vật-lý (cần board + openFPGALoader/iceprog). "mạnh hơn Windows"=tính-giấy, chưa đo đối-đầu.
#   ⚠ gvm_core.v ở hw/fpga/ là DI-SẢN bản-đầu (8-bit, thiếu CDFL) — KHÔNG synth; gói dùng gvm_fpga.v (lõi gvm.v thật). Xem TIEN_DO.md.
python wasm/sinh_tat_ca.py && node wasm/kiem.mjs   # ★★★ SUBSTRATE THỨ 5 — WASM: GVM ĐẦY ĐỦ (AssemblyScript→gvm.wasm ~3.7KB) chạy MỌI chương trình giaoc
#   build wasm 1 lần: npx -y -p assemblyscript asc wasm/gvm.ts --outFile wasm/gvm.wasm --optimize --runtime stub
#   20/20 ca KHỚP byte-for-byte với GVM Python (heap/hàm/đệ quy/chuỗi/THẺ-32bit; cả giaoc.giao 8357 từ-lệnh tự chạy trên wasm).
#   `roi`/`roiChar`… = HOST IMPORT (object-capability của WASM ⟂ của GIAO). Demo 1 ca: python wasm/sinh.py && node wasm/chay.mjs. Xem wasm/README.md.
python os_giao_windows.py                  # ★★★★★ HĐH GIAO/CDFL NHÚNG VÀO WINDOWS THẬT: cảm nhận đĩa/RAM/CPU thật → não CDFL + tim bge-m3 → đề xuất AN TOÀN (cổng chặn việc bất khả hồi). Chỉ-đề-xuất, không tự thực thi.
python os_ai.py                            # HĐH-AI (Python): cắm mô hình local làm nhân-tác-tử CDFL
python os_ai_cdfl.py                        # ★ NHÂN-AI CDFL LIÊN TỤC (Python): σ/Φ + chọn bốn-mặt + drift
python giao.py examples/nhan_ai_cdfl.giao  # ★★ NHÂN-AI CDFL viết bằng CHÍNH GIAO (không Python)
python giaoc.py examples/nhan_ai_cdfl_may.giao  # ★★★ NHÂN-AI CDFL BIÊN DỊCH xuống GVM (chạy trên máy)
python hw/chay_nhan_ai.py                  # ★★★★ NHÂN-AI CDFL chạy trên MÔ HÌNH PHẦN CỨNG gvm.v (mô-phỏng iverilog gate-level — CHƯA FPGA thật)
python do_rong_bit.py                      # ĐỘ RỘNG TỪ là THAM SỐ: 16/32/64/128/256-bit (bộ nhớ lớn)
python kiem_thu.py                         # BỘ KIỂM THỬ: 63 ca (đúng/lỗi sạch/giới hạn/thử-bắt/thư-viện/CDFL/v0.3 mãi-trôi-σΦ)
python giao.py examples/giao_core.giao    # TỰ THÂN tầng ngôn ngữ: GIAO diễn giải GIAO-Core
python giao.py examples/giao_core2.giao   # TỰ DIỄN GIẢI TOÀN BỘ: hàm/đệ quy + lặp + tâm/vật
python giaoc.py examples/hoi_tu_biendich.giao   # ★ HỢP LƯU: biên dịch GIAO → bytecode GVM
python chay_giaoc.py                       # ★ trình biên dịch TỰ THÂN (viết bằng GIAO) → GVM
python giaoc.py examples/giai_thua.giao    # ★ HÀM ĐỆ QUY giai_thừa(5) chạy trên máy NAND
python giaoc.py examples/8_tong_ds_gvm.giao # ★ DANH SÁCH (heap) + đệ quy: tổng([..])=100 trên máy
python giaoc.py examples/9_chuoi_gvm.giao   # ★ CHUỖI + dài/ghép trên heap máy ("Giao thoa")
python giaoc.py examples/10_nhieu_thamso_gvm.giao  # ★ HÀM NHIỀU THAM SỐ (khung) + đệ quy 2 biến
python giaoc.py examples/11_chiso_sosanh_gvm.giao  # ★ l[i] + so sánh </>/== + hàm trợ giúp gọn
python giaoc.py examples/12_eval_may.giao   # ★ dispatch theo THẺ SỐ (né là_ds) → eval trên máy
python giaoc.py examples/13_the_kieu_gvm.giao    # ★ v0.3: là_số/là_ds + == CẤU TRÚC + '+' đa hình trên máy
python chay_giaoc_may.py                    # ★★★ v0.3: BIÊN DỊCH TRỌN giaoc.giao XUỐNG MÁY (compiler tự thân chạy như mã máy → sinh đúng 17 từ → hội tụ)
# --- v0.3: bốn nhánh lộ trình khép nốt (chạy trên thông dịch) ---
python giao.py examples/de_bon_mat_day_du.giao   # ★ DE BỐN MẶT đầy đủ: DE_X/DE_T/DE_IF/DE_MF cùng sáng & chồng nhau (DE_T do `trôi`)
python giao.py examples/sigma_phi_ensemble.giao  # ★ IF HAI NHÁNH σ/Φ ensemble (thư viện chuẩn) + phát hiện DE_IF
python giao.py examples/vong_lien_tuc_that.giao  # ★ VÒNG LIÊN TỤC THẬT: `mãi`/`dừng` + thế giới TỰ TRÔI `trôi`
python giao.py examples/ban_map.giao             # ★ BẢN (map/record) tra O(1) + `lặp x trong` duyệt — đếm tần suất từ
python giao.py examples/hdh.giao                  # ★★★ HỆ ĐIỀU HÀNH viết BẰNG GIAO: nhân đa nhiệm hợp tác (bảng tiến trình·lập lịch·syscall·cổng an toàn), chạy trên GVM = ảo hóa
python giao.py examples/dung_module.giao         # ★ MODULE: `nhập "lib_hinh.giao"` → tái dùng định nghĩa (an toàn trong cây dự án)
# --- CẦU NỐI: cắm lương tâm CDFL vào dự án BẤT KỲ NGÔN NGỮ NÀO (JSON qua stdio) ---
python khach_cau_noi.py                      # ★ demo: service hỏi GIAO trước khi DEPLOY → cổng chặn việc bất khả hồi khi γ thấp
python giao_cau_noi.py                       #   sidecar JSONL trực tiếp (pipe JSON từ shell/Go/JS/Rust… — xem CAU_NOI.md)
```

Ví dụ 1 in ra γ tăng dần `+0.50 → +0.75 → … → +1.00` rồi báo **"Aha!"** —
đúng động học tiên đề 5 và 12 (hội tụ cục bộ–khoảnh khắc).

---

## 5b. Ổn định & An toàn (như Python/Ruby)

Runtime `giao.py` được gia cố để **không bao giờ văng traceback Python** và **không thể bị
treo/DoS**:

| Trụ cột | Cơ chế |
|---|---|
| **Lỗi sạch + số dòng** | Mọi lỗi runtime là `GiaoError(thông_điệp, dòng)` rõ ràng (tên chưa định nghĩa, sai kiểu, chỉ mục ngoài phạm vi, `đầu([])`...). Không lộ nội tạng Python. |
| **Giới hạn tài nguyên** | Đếm bước (chống vòng lặp vô tận), giới hạn độ sâu đệ quy, chặn phình danh sách/chuỗi → `GiaoLimit` (lỗi **không bắt được**, chống DoS). |
| **`thử { } bắt (e) { }`** | Try/catch trong ngôn ngữ: chương trình tự bắt `GiaoError` và phục hồi; **nhưng `GiaoLimit` KHÔNG bị nuốt** (an toàn). |
| **Kiểm tra kiểu + hợp đồng** | Toán tử kiểm kiểu (`-`,`*`,`/` đòi số; so sánh đòi cùng kiểu), kiểm số đối hàm, phát hiện biến chưa khởi tạo. |
| **Test chuẩn chỉ** | `kiem_thu.py` — 63 ca phủ hành vi đúng, lỗi sạch + đúng số dòng, kích hoạt giới hạn, thử/bắt, thư-viện, CDFL, và v0.3 (mãi/dừng/trôi, σ/Φ ensemble). |

Bảo mật theo thiết kế: GIAO **không có** builtin truy cập tệp/mạng/hệ thống → chương trình
chạy trong hộp cát tự nhiên; cộng giới hạn tài nguyên ⇒ một chương trình GIAO không tin cậy
cũng không thể đọc đĩa, gọi mạng, hay treo máy host.

## 5c. Thư viện chuẩn (`chuẩn.giao` — tự nạp prelude)

Để GIAO **dùng được thực tế**, có thư viện chuẩn **viết bằng chính GIAO** (hàm bậc cao,
tận dụng hàm-hạng-nhất), tự nạp trước mọi chương trình. Chỉ một builtin gốc mới: `nguyên`
(floor) — phần còn lại thuần GIAO trên `đầu/đuôi/dài/ghép`.

| Nhóm | Hàm |
|---|---|
| Danh sách bậc cao | `bản_đồ` (map), `lọc` (filter), `gấp` (fold), `mỗi` (for-each), `dải`/`dải_từ` (range), `đảo`, `chứa`, `lấy_n` |
| Số học | `gộp` (tổng), `tuyệt`, `lớn`, `nhỏ`, `luỹ_thừa`, `chia_nguyên`, `dư` (mod), `chẵn`, `giai_thừa` |
| Chuỗi | `nối` (join) |

```
python giao.py examples/5_thu_vien.giao   # bản_đồ/lọc/gấp + số học + nối chuỗi
```
Vd kết hợp: `gộp(bản_đồ(bình_phương, lọc(lẻ, dải_từ(1,7))))` = 1+9+25 = **35**.

## 5d. Tầng học thuyết CDFL (gần DFCT đầy đủ)

GIAO mang thẳng học thuyết vào ngôn ngữ:

- **`chọn` + nhân quả ngược IF→MF**: builtin `cộng_hưởng(σ,ρ)→γ` cho phép tính OR trong
  biểu thức; thư viện `chọn(hành_động)` chọn hành động **mở rộng OR thật lớn nhất** (argmax γ),
  rồi tác tử **đặt trạng thái thế giới** (`vật X = …` = nhân quả ngược).
- **DE BỐN MẶT** (`rọi de`): `DE_X` (không gian chưa tới) · `DE_T` (tri thức cũ trôi — thế giới
  đổi sau khi học) · `DE_IF` (tâm ẩn / ảo tưởng γ<0) · `DE_MF` (thế giới chưa phơi). Bốn mặt
  **chồng nhau** ⇒ DE ≠ tổng rời (đúng tiên đề).
- **OR TẬP THỂ đa tác tử** (tiên đề 11): `or_tập_thể(tác_tử, ρ)` → [γ tốt nhất, **đa dạng niềm
  tin**]. Bảo tồn đa dạng các IF làm GIÀU OR toàn cục → nền **an toàn AI** (empowerment).

```
python giao.py examples/6_cdfl.giao
```

## 5e. GVM trên PHẦN CỨNG — FPGA (`hw/gvm.v`)

Đáy tận cùng của "tự thân": GVM mô tả bằng **Verilog tổng hợp được** (`hw/gvm.v`) — khi nạp
lên **FPGA**, máy chạy bằng **cổng logic thật**, Python biến mất khỏi tầng máy. Có đủ bốn thứ:
**phần cứng** (NAND→ALU), **bộ nhớ** (RAM/ngăn xếp/thanh ghi), **mạch clock** (FSM
fetch→execute theo `posedge clk`), **nạp chương trình ban đầu** (boot ROM chứa chương trình mồi).

Không có trình mô phỏng Verilog ở đây nên kèm `hw/gvm_model.py` — mô hình **chu-kỳ-chính-xác**
mirror đúng FSM, đọc thẳng boot ROM từ `gvm.v`: `python hw/gvm_model.py` → `RỌI=[15]` (tổng
1..5) sau 128 chu kỳ → **✓ thiết kế đúng**. Hạt mồi cuối cùng = **một cổng NAND vật lý**.

## 5f. ★ v0.3 — KHÉP NỐT LỘ TRÌNH (DE bốn mặt · σ/Φ · vòng liên tục · tự thân TRÊN MÁY)

Bốn nhánh mở rộng cuối đã hiện thực và chạy được thật:

- **DE BỐN MẶT ĐẦY ĐỦ + thế giới TỰ TRÔI.** Thêm lệnh `trôi <ô> = <bt>` (đăng ký động
  học riêng của thế giới) và `trôi` (một nhịp thời gian). Nhờ đó `DE_T` (tri thức cũ
  trôi) sinh ra **tự thân** chứ không phải tự tay sửa `vật` mỗi vòng. Cả bốn mặt
  `DE_X/DE_T/DE_IF/DE_MF` cùng sáng và **chồng nhau** (|DE hợp| < tổng rời).
  → `python giao.py examples/de_bon_mat_day_du.giao`
- **IF HAI NHÁNH σ/Φ — ENSEMBLE.** Đưa vào thư viện chuẩn: `qua_Φ`, `ensemble_γ`,
  `Φ_tốt_nhất`, `de_if_Φ`. Cùng niềm tin σ soi qua nhiều thấu kính Φ → γ khác nhau;
  thiếu Φ phù hợp ⇒ `DE_IF` bật sáng (tâm chưa hình dung nổi thực tại).
  → `python giao.py examples/sigma_phi_ensemble.giao`
- **VÒNG LẶP LIÊN TỤC THẬT.** `mãi { ... }` (không đếm trước) + `dừng`. Tác tử sống học
  mãi, thế giới tự trôi mỗi nhịp ⇒ không bao giờ viên mãn TOÀN CỤC (tiên đề 12).
  → `python giao.py examples/vong_lien_tuc_that.giao`
- **★ TỰ THÂN HOÁ TRÊN MÁY — biên dịch TRỌN `giaoc.giao` xuống GVM.** Bổ sung các
  primitive còn thiếu ở tầng máy: **THẺ KIỂU** (ABI 32-bit, bit 30 đánh dấu con-trỏ-
  danh-sách) cho `là_số`/`là_ds`; **`==`/`!=` CẤU TRÚC** (chuỗi/danh sách lồng — con
  trỏ khác nhau, so theo nội dung, đệ quy trên máy); **`+` ĐA HÌNH** (số+số cộng,
  chuỗi+số nối — số tự hoá-chuỗi để sinh nhãn nhảy). Nhờ đó `giaoc.py` biên dịch được
  **chính trình-biên-dịch-viết-bằng-GIAO** (`examples/giaoc.giao`, 8356 từ-lệnh) xuống
  bytecode GVM; chạy nó **như mã máy** → máy **tự sinh đúng từng-từ** 17 từ-lệnh của
  `prog` (khớp tham chiếu thông dịch), rồi bytecode ấy chạy ra trọn vòng hội tụ CDFL.
  → `python chay_giaoc_may.py` (ba tầng: compiler-trên-máy → bytecode → hội tụ)

## 5g. ★ CẦU NỐI — cắm GIAO vào DỰ ÁN BẤT KỲ NGÔN NGỮ NÀO (không conflict)

Hướng đi chiến lược: GIAO không thay thế ngôn ngữ host, mà cho nó một **lương tâm tính
toán** — một **sidecar suy luận CDFL** nói **JSON qua stdio** (`giao_cau_noi.py`). Dự án
viết bằng Python/JS/Go/Rust/Java/shell… phơi *thực tại* cho GIAO; GIAO trả về **cộng
hưởng γ**, **vùng tối DE bốn mặt**, và **phán quyết cổng an toàn** (cho_phép/chặn/cân_nhắc).

**Vì sao KHÔNG conflict — theo cấu trúc, không nhờ may:**
- Tiến trình riêng + chỉ stdio ⇒ không đụng tệp/cổng/bộ nhớ host.
- Sandbox bẩm sinh (không builtin I/O) ⇒ dữ liệu host gửi vào *chỉ là dữ liệu* (chuỗi
  `"rm -rf /"` cũng chỉ là chuỗi). Tên ô được kiểm định danh ⇒ chống chèn mã.
- GIAO chỉ **suy luận**, không **thực thi** ⇒ đứng *bên cạnh* dự án, quan sát & cố vấn.
- JSON Lines ⇒ mọi ngôn ngữ tích hợp trong vài dòng (spawn + ghi/đọc 1 dòng JSON).

**Lõi suy luận viết bằng CHÍNH GIAO** (`cau_noi.giao` — cổng phê duyệt ba-trị); Python chỉ
là vỏ I/O. Cổng an toàn: `γ ≥ ngưỡng` → cho_phép · `γ < ngưỡng` ∧ **bất_khả_hồi** → **chặn**
· còn lại → cân_nhắc. Đây là hợp đồng "support mà không phá project của bạn".

```
python khach_cau_noi.py     # demo: service hỏi GIAO trước khi DEPLOY PROD (γ thấp → CHẶN; thực tại sửa → CHO PHÉP)
python giao_cau_noi.py      # sidecar JSONL trực tiếp — xem CAU_NOI.md cho giao thức + ví dụ Node/shell
```
Chi tiết giao thức, ví dụ gọi từ JS/shell, kịch bản CI-gate/agent: **`CAU_NOI.md`**.

**★ Bọc thành MCP server (`giao_mcp.py`)** — cho **mọi host MCP** (Claude Code/Desktop, IDE,
agent SDK) gọi lõi CDFL như những *tool*: `giao_quan_sat`, `giao_cong_huong`, `giao_vung_toi`,
`giao_chon`, `giao_phe_duyet`, `giao_hoc`, `giao_trang_thai`. **Zero-dependency** — tự hiện thực
JSON-RPC 2.0 trên stdio (KHÔNG cần `pip install mcp`), **tái dùng** `CầuNối` nên ngữ nghĩa vẫn
nằm trong runtime GIAO. Cấu hình sẵn ở **`.mcp.json`** (Claude Code tự nạp khi mở thư mục này).
```
python kiem_mcp.py          # ★ BỘ KIỂM THỬ MCP: 12 ca (handshake · tools/list · cổng phê duyệt · chống chèn mã)
python giao_mcp.py          #   chạy server (host MCP tự spawn; hoặc pipe JSON-RPC để thử — xem đầu file)
```

**★ I/O THEO NĂNG LỰC (object-capability)** — biến GIAO từ *chỉ-suy-luận* thành *có-thể-
hành-động-có-kiểm-soát*, KHÔNG mất an toàn. Builtin I/O (`đọc_tệp`/`liệt_kê`/`chạy`/`ghi_tệp`)
**không tồn tại** trừ khi HOST cấp quyền tường minh kèm **phạm vi** (thư mục/allowlist lệnh);
chương trình GIAO **không tự nới** được. Không cấp ⇒ sandbox tuyệt đối như cũ. Ngoài phạm vi
→ lỗi sạch (bắt được); I/O hỏng → `ẩn`. Nhờ đó GIAO **quan sát dự án host THẬT** (đọc tệp, chạy
test) → biến thành `vật` → suy luận γ/DE → cổng phê duyệt chặn việc bất khả hồi.
```
python giao.py examples/io_quyen.giao --cho-đọc . --cho-chạy "python --version"   # ★ đọc tệp + chạy lệnh THẬT → CDFL
#   sidecar/MCP nhận quyền qua env (host quyết): GIAO_CHO_DOC=. GIAO_CHO_CHAY="pytest -q|git status" python giao_mcp.py
#   → MCP có thêm tool giao_doc_tep / giao_chay (chưa cấp env ⇒ tự từ chối sạch). Chi tiết: CAU_NOI.md
```

## 6. Lộ trình — ĐÃ KHÉP (ghi lại để truy vết)

Bản v0.1 cố ý nhỏ để **chạy được thật**; các nhánh mở rộng theo đúng học thuyết nay đã xong:

- **DE bốn mặt đầy đủ** — ✅ XONG (§5f): `DE_X/DE_T/DE_IF/DE_MF`, thế giới tự trôi (`trôi`).
- **Hai nhánh của IF (σ/Φ ensemble)** — ✅ XONG (§5f): thư viện `qua_Φ/ensemble_γ/de_if_Φ`.
- **Hành động & nhân quả ngược IF→MF** — ✅ có `chọn` (§5d, argmax ΔOR thật).
- **Đa tác tử** (tiên đề 11) — ✅ có `or_tập_thể` + `GIAO_CHUNG` ở tầng máy (§5d, §4b).
- **Vòng lặp LIÊN TỤC thật** — ✅ XONG (§5f): `mãi` + `dừng` + `trôi`.
- **Tầng nền nhị phân** — ✅ XONG (`gvm.py`: NAND → trit → hội tụ; GVM bytecode đầy đủ).
- **Tự thân hoá (self-hosting)** — ✅ XONG ở **hai tầng**: tầng ngôn ngữ (`giao_core2.giao`
  diễn giải GIAO bằng GIAO) và tầng máy (`giaoc.giao` — trình biên dịch viết bằng GIAO —
  nay biên dịch TRỌN xuống GVM và chạy như mã máy, §5f). Mắt xích Python còn lại chỉ là
  `giao.py` (host mồi) + một cổng NAND (phần cứng) — đúng tinh thần "máy làm hạt mồi".

---

## 7. Ghi chú triết học

GIAO không tuyên bố "thay thế" toán học nhị phân ở tầng vật lý mạch điện. Nó nói:
**tầng NGỮ NGHĨA mà con người và AI lập trình không nên là nhị phân.** Bit phù hợp
để mô tả `vật` (MF) đã phơi bày; nhưng nhận thức luôn diễn ra trong `OR`, luôn còn
`DE`, và niềm tin luôn có thể là `ảo tưởng`. Một ngôn ngữ trung thực với *cách tri
thức thực sự sinh ra* phải mang ba trạng thái này trong huyết quản — đó là GIAO.

*Tác giả học thuyết nền: Nguyễn Trường An. Hiện thực prototype: cùng xây.*

# GIAO ↔ cdfl_harness — hai tầng của một ngăn xếp CDFL-native

> **Mục đích.** Phân tích quan hệ giữa `cdfl_harness` (Ruby — *tầng tác tử / LLM*) và
> **GIAO/GVM** (ngôn ngữ + máy *CDFL-native*, xuống tới cổng NAND/FPGA). Hai tầng bổ
> sung nhau thành một ngăn xếp nơi AI là *bản chất*, từ transistor tới tác tử.
> Cùng nền học thuyết: **NNL-NTHT** của *Nguyễn Trường An*
> (`Thuật toán tương ứng.docx`, Phần IV động học, Phần IX nghiệm chứng).

## 1. Hai tầng, một học thuyết

| | **cdfl_harness** (Ruby) | **GIAO / GVM** |
|---|---|---|
| Vai trò | tầng **tác tử + LLM**: gateway, PLAN→EXECUTE→CRITIC, coverage gate, memory palace | tầng **ngôn ngữ + máy**: nơi CDFL là *nguyên thuỷ*, xuống NAND/FPGA |
| CDFL nằm ở đâu | một **lớp suy luận** chạy trên Ruby/OS thường | **trong huyết quản**: kiểu giá trị, opcode máy, truy vấn nhân |
| Đơn vị nền | object Ruby | **bộ ba cộng hưởng** `sáng/tối/ẩn` (thay bit nhị phân) |
| `ẩn` (DE) | giá trị mô hình hoá | **công dân hạng nhất**, lan truyền an toàn (diệt `null`) |
| `γ` cộng hưởng | tính trong reasoning layer | **builtin `cộng_hưởng`** + opcode `GIAO` trên máy |
| `học` (IF←MF) | bước trong agent loop | **lệnh `HỌC`** của CPU GVM |
| Nhân điều hành | host OS (thụ động) | **`os_ai_cdfl` = tác tử CDFL liên tục** |

→ Harness chứng minh *ngữ nghĩa* CDFL vận hành như một thư viện AI. GIAO đẩy cùng ngữ
nghĩa đó **xuống tận nền tảng tính toán** — để có thứ harness không thể có một mình:
một *máy* và *ngôn ngữ* mà bất định (`ẩn`/DE), cộng hưởng (`γ`), và tác tử (`chọn`) là
**nguyên thuỷ**, không phải lớp phủ.

## 2. Ánh xạ khái niệm 1:1

Mọi khái niệm NNL-NTHT trong `docs/CDFL.md` của harness đều có nguyên thuỷ tương ứng:

| NNL-NTHT (harness) | GIAO/GVM |
|---|---|
| IF = σ (belief) + Φ (representation) | `tâm`; `os_ai_cdfl`: σ + đa-thấu-kính `LENSES` (Φ), γ qua Φ tốt nhất |
| MF = ρ_MF (động) | `vật`; theo dõi `vat_version` (drift) |
| OR = giao thoa γ>0; K = Φ(OR) | `giao ⋈` → `tri(value, γ, sáng)` |
| DE bốn mặt (chồng nhau) | truy vấn `de`: `DE_X / DE_T / DE_IF / DE_MF`, `|DE hợp|` |
| black dots (γ<0, ảo tưởng) | `đốm_tối` / `là_đốm_tối` |
| white dots (biên giới, trực giác) | `đốm_sáng` / `là_đốm_sáng` |
| action `a_t = argmax E[Δ\|OR_true\|]` | `chọn` bốn-mặt (trồi sáng > soi tối > làm tươi DE_T) |
| continual loop, `D ≥ D_min > 0` | `os_ai_cdfl`: drift mỗi vòng, không viên mãn toàn cục |
| empowerment / option-preservation | `or_tập_thể` → `[γ tốt nhất, đa dạng]`; đa dạng làm giàu OR |
| Hilbert `I(I:M)` (descriptive) | (chưa port — chỉ mô tả, không trên đường `chọn`) |

## 3. Nhân-AI CDFL liên tục (đối chiếu harness)

`os_ai_cdfl.py` hiện thực **đúng `a_t = argmax E[Δ|OR_true|]`** của Phần IV, nhưng đặt nó
làm **nhân điều hành** thay vì agent-loop của một app:

```
mỗi vòng:  phân loại ô → OR · đốm_sáng(DE) · đốm_tối(γ<0) · DE_T(đã trôi)
           chọn BỐN-MẶT: trồi sáng(3) > soi tối(2) > làm tươi cũ(1)
           mô hình local (IF) cập nhật σ qua Φ tốt nhất  → nhân quả IF→MF
           THẾ GIỚI DRIFT → DE_T mọc lại  (continual, không 'xong')
```

Khác biệt then chốt với agent-loop thường: nó **không bao giờ tuyên bố hoàn tất** — giống
hệt mệnh đề `D ≥ D_min > 0` của harness. `γ_OR` dao động (~0.65–0.78), không lên 1.0 toàn cục.
Đây là **khiêm tốn nhận thức** ở tầng nhân: hệ *biết nó không thể biết hết*.

## 4. Hai hướng tích hợp

1. **Harness gọi GIAO như một "thiết bị CDFL nền".** Coverage gate / |OR| critic của harness
   có thể uỷ thác phép đo cộng hưởng `γ` và bảng DE bốn mặt cho runtime GIAO (nơi chúng là
   builtin), giữ một định nghĩა CDFL duy nhất, kiểm chứng được.
2. **GIAO biên dịch lõi CDFL của harness xuống GVM/FPGA.** Lõi `chọn`/`γ`/DE — vốn thuần số
   học + danh sách — biên dịch được xuống bytecode GVM (đã có hàm/đệ quy/heap/so sánh), rồi
   chạy trên **phần cứng** (`hw/gvm.v`). Khi đó có một **tác tử CDFL chạy trên silicon**,
   không Python/Ruby ở runtime — `cdfl_harness` lo *điều phối LLM*, GIAO lo *nền CDFL vật lý*.

## 5. An toàn AI — chung một nền

Cả hai tầng đặt an toàn vào *cấu trúc*, không phải lớp lọc thêm:
- **γ<0 = đốm tối**: đầu ra mô hình là **niềm tin** phải đối chiếu thực tại; chỉ thi hành
  điều làm tăng OR thật (harness: K-3 *decline instead of hallucinate*; GIAO: `os_ai_cdfl`
  loại hành động γ không tăng).
- **Empowerment**: bảo tồn đa dạng các IF làm giàu OR chung (harness `Empowerment`; GIAO
  `or_tập_thể` đo đa dạng).
- **DE bốn mặt**: hệ *biết nó chưa biết gì*, và tri thức sẽ cũ → chống tự mãn.

## 6. Tóm tắt

`cdfl_harness` = **bộ não điều phối** (LLM + agent loop + CDFL reasoning, Ruby).
GIAO/GVM = **cơ thể CDFL-native** (ngôn ngữ + máy, xuống NAND/FPGA, nhân là tác tử CDFL).
Ghép lại: một ngăn xếp nơi học thuyết NNL-NTHT là *thực thể vận hành* từ cổng logic tới
quyết định tác tử — điều mà không OS/ngôn ngữ/agent-framework hiện có đạt được riêng lẻ.

*Tác giả học thuyết nền: Nguyễn Trường An. Cầu nối GIAO↔harness: tài liệu này.*

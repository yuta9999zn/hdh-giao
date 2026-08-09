# GVM trên PHẦN CỨNG (FPGA) — `gvm.v`

Đáy tận cùng của "tự thân": khi GVM chạy bằng **cổng logic thật trên FPGA**, Python
biến mất khỏi tầng máy. Hạt mồi cuối cùng = **một cổng NAND vật lý (transistor)**.

## Tệp
| Tệp | Vai trò |
|---|---|
| `gvm.v` | CPU GVM mô tả phần cứng (Verilog tổng hợp được): NAND→ALU→ngăn xếp+RAM+boot ROM, theo clock |
| `gvm_tb.v` | Testbench mô phỏng (cho iverilog/Vivado) |
| `gvm_model.py` | Mô hình chu-kỳ-chính-xác (Python) mirror đúng FSM của `gvm.v` để kiểm chứng tại đây |

## Bốn thứ bạn cần — đã có trong `gvm.v`
| Bạn cần | Trong `gvm.v` |
|---|---|
| **Phần cứng vật lý** | `nand2` → `inv1/and2/or2/xor2` → `full_adder` → `adder16` (ALU) — mọi thứ từ NAND |
| **Bộ nhớ** | `ram[]` (RAM dữ liệu), `stack[]` (ngăn xếp), thanh ghi `ip`/`sp` |
| **Mạch clock** | FSM `FETCH→EXEC` chạy theo `posedge clk` |
| **Nạp chương trình ban đầu** | `rom[]` = **boot ROM** chứa chương trình mồi (tổng 1..5 = 15) |

## Kiểm chứng (không cần trình mô phỏng Verilog)
```
python hw/gvm_model.py     # → RỌI = [15], dừng sau 128 chu kỳ → ✓ THIẾT KẾ ĐÚNG
```
`gvm_model.py` đọc THẲNG boot ROM từ `gvm.v` và chạy đúng ngữ nghĩa FSM, nên xác minh
logic thiết kế là đúng.

## Khi có công cụ — mô phỏng & nạp FPGA
```
# Mô phỏng (Icarus Verilog):
iverilog -o gvm hw/gvm.v hw/gvm_tb.v && vvp gvm      # in "RỌI = 15", "CPU DỪNG."

# Tổng hợp lên FPGA (Yosys mã nguồn mở, hoặc Vivado/Quartus):
#   - nạp gvm.v, gán out_data → LED/UART, clk → dao động bo mạch
#   - boot ROM nạp sẵn chương trình → bật nguồn là CPU chạy
```

## Đường tới SILICON đầy đủ
- **FPGA** (đích khả thi): `gvm.v` tổng hợp thành cổng logic thật → CPU vật lý chạy thật.
  Python chỉ từng là kẻ đóng thế cho FPGA. Boot ROM = hạt mồi gõ tay (Mức 0) → tự bootstrap.
- **ASIC** (chip đúc): cùng `gvm.v` đưa qua nhà máy đúc → silicon tùy biến. Đây là chế tạo
  vật lý, ngoài phạm vi repo.

## Độ rộng từ là THAM SỐ
`gvm #(.MEM(4096), .WORD(16))` — đổi `WORD` thành 16/32/64/128/256 là có CPU rộng tương ứng.
**Dữ liệu** (ram/stack/thanh ghi/ALU `adderN #(WORD)`) rộng `WORD`-bit; **lệnh** luôn 16-bit
([opcode:8][operand:8]); con trỏ sp/fp 8-bit. Nới `WORD=64` ⇒ địa chỉ 2⁶⁴ = 16 EB ≫ 1TB —
dùng được bộ nhớ máy thật. (Song song với tham số `bit` của `gvm_may.py` phần mềm.)

### LÕI 32-BIT — chương trình HEAP (ABI thẻ) gate-level
`WORD=32` mở khoá **ABI THẺ** (bit 30 phân biệt con-trỏ với số) → danh-sách/heap +
`là_số`/`là_ds` + gọi-hàm-theo-khung chạy trên cổng logic. Chạy: `python hw/lam_verilog32.py`
(biên dịch `examples/heap32_gvm.giao` 32-bit → iverilog → đối chiếu BYTE phần mềm:
`[10,20,30,3,1,1,0]`). **CLOSURE + CHUỖI gate-level:** `python hw/lam_verilog32_chuoi.py`
(`áp(nhân(3),5)=15`, `"Gi"+"ao"="Giao"`) — dùng opcode mới `ĐỔI · RỌI_CHUỖI · GỌI_CLOSURE ·
RỌI_AUTO · DÀNH_CB · LƯU_THAM_I`; cổng `out_kind` (0=số/1=ký-tự/2=hết-chuỗi) để host ghép chuỗi.
*Còn thiếu để chạy nhân ĐẦY ĐỦ:* `BẮT_ĐẦU_THỬ/HẾT_THỬ/NÉM · FNHÂN/FCHIA · XUẤT · RỌI_THỰC/RỌI_DS`
+ xử-lý-trạng-thái-`ẩn` (máy-trị Verilog chưa có ô ba-trị).

## Opcode đã có
Lõi (NẠP/TẢI_Ô/LƯU_Ô/CỘNG/TRỪ/NHÂN_BẢN/BỎ/NHẢY/NHẢY_NẾU_0/RỌI/DỪNG) + **khung hàm**
(`GỌI_N/THAM_I/TRẢ_VỀ_N`) + **heap** (`TẢI_GIÁN/LƯU_GIÁN`) + **`CHIA`** (chia số nguyên có dấu).
Boot ROM kiểm chứng: `[42, 99, 3]` = gọi hàm nhân_đôi(21), heap ram[50], 17/5.

## Còn mở rộng (để chạy TRỌN bytecode GIAO biên dịch trên FPGA)
Thêm dần các opcode trình biên dịch còn dùng: **so sánh** (BẰNG/KHÁC/BÉ_HƠN/LỚN_HƠN/
BÉ_BẰNG/LỚN_BẰNG), **NHÂN** (nhân), **nhảy gián tiếp** (NHẢY_X/NHẢY_NẾU_0_X). Đủ chừng đó
là nạp được bytecode của `nhan_ai_cdfl_may.giao` vào boot ROM → nhân-AI CDFL chạy trên silicon.

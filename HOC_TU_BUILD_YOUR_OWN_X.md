# Học từ build-your-own-x — GIAO học được gì để "xuống chip"

> Tham khảo https://github.com/codecrafters-io/build-your-own-x (mục *Operating System*).
> Câu hỏi: cách người ta xây HĐH bare-metal — GIAO **đã có gì · vừa thêm gì · còn gì**.

## 1. Các bài mẫu và bài học rút được

| Bài (build-your-own-x) | Ngôn ngữ | Bài học lõi | GIAO tương ứng |
|---|---|---|---|
| **os-tutorial** (cfenollosa) | C + Asm | boot-sector → 32-bit → kernel C → **driver màn hình qua địa chỉ 0xB8000**, bàn phím, ngắt | boot = **bitstream FPGA** (`hw/gvm.v`), không cần GRUB vì GVM *là* CPU. Driver = **MMIO** (vừa thêm) |
| **The little OS book** | C + Asm | GDT · **IDT/PIC ngắt** · **timer** · phân trang · user-mode · syscall | ngắt+timer **đã có** (`BẬT_NGẮT/HẸN_GIỜ/NGẮT_VỀ`, `γ-scheduler`); cô lập **không cần phân trang** nhờ **SIP** |
| **Writing an OS in Rust** (phil-opp) | Rust `no_std` | **VGA buffer qua MMIO** · CPU exceptions · ngắt · heap alloc | MMIO (vừa thêm) · fault-isolation **đã có** (`hdh_fault`, mỗi tiến trình 1 stack+handler) · heap32 **đã có** |
| **mini-arm-os** | C + Asm (QEMU) | **context-switch** · **lập lịch tiền-định** · mutex · syscall trên Cortex-M | preempt γ-scheduler **đã có** (`hdh_preempt`, bit-exact silicon); lock/semaphore **đã có** (`lib_đồng_bộ`) |
| **egos-2000** | C (RISC-V, ~2000 dòng) | HĐH **tí hon, kiểm-chứng-được**, tách 3 lớp | trùng triết lý GIAO: ~10KB, TCB nhỏ, đường tới **verify hình thức** (seL4-class) |
| **mal / Jonesforth** | bất kỳ / Forth | **OS-nền-ngôn-ngữ**: ngôn ngữ tự nở thành hệ | chính là GIAO — ngôn ngữ + máy + HĐH một mạch, CDFL là *nguyên thuỷ* |

## 2. Điều KHÁC then chốt (vì sao GIAO không sao chép C/Asm)

Mọi bài "xuống chip" cổ điển dùng **Asm/C/Rust + bootloader trên CPU x86/ARM có sẵn**. GIAO đi đường
khác **có chủ đích** (README): *"máy tính bắt đầu từ 0 và 1 → GIAO phải mọc lên TỪ 0 và 1, không phải
từ Python"*. Nên "bare-metal" của GIAO = **GVM synthesized ra silicon** (`hw/gvm.v` → yosys → iCE40
UP5K bitstream, 16/16 Verilog bit-exact) — Python chỉ đóng vai **một cổng NAND** (mồi). Không mượn
CPU x86; **tự làm CPU**. Đây là cái đa số bài build-your-own-x KHÔNG có (chúng chạy trên CPU người khác).

Hệ quả ràng buộc: chỉ **Giao + Python (mồi)** — nên KHÔNG viết kernel C/Rust. "Kiểm soát chip" đạt qua
**hai đường hợp lệ**: (a) **MMIO** — phần mềm Giao ghi/đọc thanh ghi thiết bị; (b) **FPGA** — GVM chạy
trên silicon thật.

## 3. GIAO VỪA THÊM (đợt này) — lấp đúng gap Pha-1 mà roadmap tự nêu

Roadmap (`KE_HOACH_PHAT_TRIEN.md` Pha 1) liệt "thêm **opcode MMIO** (đọc/ghi thanh ghi thiết bị)" là
việc còn thiếu. Đã thêm — **đúng mẫu "first driver" của os-tutorial/phil-opp (ghi thanh ghi thiết bị)**:

- **MMIO như một NĂNG-LỰC** (`mmio(địa_chỉ[, giá_trị])` trong `giao.py`) — khớp mô hình object-capability
  sẵn có (`đọc_tệp`/`phần_cứng`): chưa cấp `--cho-mmio` ⇒ tên `mmio` **không tồn tại** (sandbox bẩm sinh).
  KHÔNG thêm opcode máy ⇒ **không đụng conformance 4-substrate** (Verilog bit-exact giữ nguyên).
- **Bản đồ thiết bị**: `UART_TX=0` (cổng nối tiếp) · `UART_ST=4` (sẵn sàng) · `TIMER=8` (bộ đếm chu-kỳ
  tự chạy) · `LED=12` (GPIO 8-bit). Ba-trị: thanh ghi lạ → `ẩn`, không crash.
- **Driver Giao** `examples/driver_mmio.giao`: blink LED (bit-pattern) + "hello" ra UART + đọc timer +
  **lịch phục vụ thiết bị bằng γ skill-score MỚI (F.4)** — nối phần (a: CDFL mới) ↔ (b: xuống chip).
- Chạy: `python giao.py examples/driver_mmio.giao --cho-mmio`. Nghiệm thu trong `kiem_toan_bo.py` (61/61).

**Trung thực về tầng:** MMIO này là **mô hình nền THAM CHIẾU** chạy trên GVM-Python (dev/simulate — đúng
quy trình: mô phỏng driver TRƯỚC khi flash silicon). Vật lý thật = **ánh xạ các thanh ghi này sang chân
UART/GPIO của `hw/gvm.v`** trên FPGA (Pha 1, phần cứng — bitstream đã dựng, chỉ còn flash bo `iceprog`).

## 4. Còn gì (theo roadmap 5 pha, không né)

- **Pha 1 nốt:** ánh xạ MMIO→chân FPGA thật (Verilog, cần `iverilog`/bo iCE40); driver khối-lưu-trữ; lập
  lịch **ưu tiên** (đã có nền γ-preempt).
- **Pha 2:** IPC capability-passing; filesystem/persistence (đã có `hdh_ben` persistence trực giao).
- **Pha 3 🐘 (gate lớn nhất):** compiler GIAO→native tối ưu + bộ nhớ ownership/region — mở khoá tốc độ.
- **Pha 4–5:** SMP đa-lõi (lập lịch **theo γ/OR CDFL-native**), stack mạng (virtio), driver GPU + compositor.

*Kết luận: build-your-own-x xác nhận GIAO KHÔNG thiếu rào nguyên lý nào — chỉ là "xây thêm". Cái GIAO
hơn-theo-kiến-tạo (tự-làm-CPU, an-toàn-bộ-nhớ, SIP không-MMU, ocap, CDFL-native, kiểm-chứng-được) là
thứ các bài kia — chạy trên CPU + OS người khác — không có. Nền học thuyết: Nguyễn Trường An.*

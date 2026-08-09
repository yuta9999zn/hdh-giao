# KẾ HOẠCH PHÁT TRIỂN GIAO → CẤP NĂNG LỰC OS TƯƠNG ĐƯƠNG (iOS/Windows/Linux)

> Thuần KỸ THUẬT. Gác chuyện người dùng/hệ sinh thái/học thuyết. Câu hỏi duy nhất:
> *cần xây gì, theo thứ tự nào, để GIAO đạt năng-lực-lõi của một OS đa dụng hiện đại?*

---

## 0. ĐIỂM MẠNH KỸ THUẬT — vì sao đây là vị thế xuất phát MẠNH

1. **Sở hữu TRỌN ngăn xếp dọc, đã chạy thật:** NAND → ALU → ISA (GVM) → assembler tự thân
   (A'=A) → ngôn ngữ → trình biên dịch → FPGA + WASM. Đa số dự án OS *không* có máy riêng đã
   kiểm chứng. GIAO có một ISA sạch, nhỏ, **mình toàn quyền sửa** (co-design ISA theo nhu cầu OS).
2. **An toàn bộ nhớ THEO KIẾN TẠO** → loại bỏ ~70% lớp lỗi cỡ-nhân (overflow/UAF) ngay từ gốc.
3. **Capability/ocap từ nền** → cô lập mịn, không quyền ambient — primitive bảo mật *hơn* Unix.
4. **Cô lập tiến trình KHÔNG cần MMU** (SIP — Software Isolated Process): nhờ memory-safety,
   nhiều tiến trình chạy chung một không-gian-địa-chỉ *an toàn* → context-switch RẺ hơn, phần
   cứng đơn giản hơn (Singularity đã chứng minh nhanh hơn Linux ở vài ca).
5. **Bất biến substrate + conformance byte-for-byte** (11/11) → test trên thông dịch nhanh,
   triển khai trên silicon; TCB nhỏ → đường tới **kiểm chứng hình thức** (seL4-class) rộng mở.
6. **Tí hon + tất định**: ~10 KB cả CPU+OS → lặp nhanh, fit mọi nơi.

→ Tổng: **làm chủ từ cổng-logic tới ngôn ngữ, an-toàn-bộ-nhớ + capability theo kiến tạo, nhỏ
& kiểm-chứng-được.** Thiếu sót còn lại thuần là *xây thêm* (preemption, driver, VM, compiler
nhanh, FS, mạng) — **không có rào nguyên lý nào.**

---

## 1. "Cấp tương đương" = bộ NĂNG LỰC-LÕI (đo được, paradigm-trung-lập)

Boot tự chủ · lập lịch **tiền-định + ưu tiên + ĐA LÕI (SMP)** · **bộ nhớ ảo/cô lập** · **stack
driver** (lưu trữ/mạng/đồ hoạ/nhập/USB/âm thanh) · **filesystem** (VFS+journaling) · **stack
mạng** (TCP/IP) · **quản lý bộ nhớ động không-GC-trong-nhân** · **mô hình bảo mật/sandbox** ·
**đồ hoạ/UI** (compositor) · ABI syscall + runtime userspace · toolchain (compiler/debug/profile)
· quản lý nguồn. Đạt đủ bộ này = "cấp Linux/Windows" về *năng lực kỹ thuật*.

---

## 2. SÁU TRACK chạy SONG SONG (OS thật là chương trình đa-track)

| Track | Nội dung | Khó nhất ở |
|---|---|---|
| **M — Máy/ISA** | mở rộng GVM: ngắt, MMIO, atomic (CAS), đa lõi, đặc quyền (hoặc dựa SIP) | đa lõi + nhất quán bộ nhớ |
| **K — Nhân** | lập lịch, quản-lý-bộ-nhớ, IPC, driver, FS, mạng — viết bằng GIAO | driver (đuôi dài) |
| **C — Compiler/Tốc độ** | GIAO→native tối ưu (hoặc GVM-ASIC); bộ nhớ ownership/region thay GC | **con voi #1** |
| **V — Kiểm chứng** | conformance + verify lõi (seL4-style) | công sức verify |
| **U — Userspace** | mô hình tiến trình, ABI syscall, dịch vụ, runtime | mô hình SIP↔ABI |
| **G — Đồ hoạ/UI** | driver display + compositor + nhập (cho Windows/iOS-class) | driver GPU |

---

## 3. NĂM PHA — mỗi pha CHỐT một mốc năng-lực OS

### Pha 1 — RTOS BARE-METAL TIỀN-ĐỊNH  *(tự chủ + đa nhiệm cướp được CPU)*
- **M:** thêm vào GVM: **ngắt + vector timer**, **opcode MMIO** (đọc/ghi thanh ghi thiết bị),
  lưu/khôi phục ngữ cảnh. *(Hạ tầng FPGA + UART đã có.)*
- **K:** lập lịch **tiền-định + ưu tiên**; driver tối thiểu (timer/UART/khối-lưu-trữ); port
  nhân `hdh.giao` sang **phần biên-dịch-được** (chạy trên GVM-silicon, không thông dịch).
- **Chốt:** OS tự boot trên FPGA, nhiều tiến trình, *một tiến trình lỗi KHÔNG treo hệ*.
- **Cỡ:** TRUNG BÌNH — đòn bẩy cao nhất, hạ tầng sẵn.

### Pha 2 — OS BẢO VỆ + BỀN  *(cô lập tiến trình + lưu trữ + IPC)*
- **M/K:** **SIP** (cô lập capability + memory-safety, **không MMU**); cấp-phát-bộ-nhớ-nhân;
  **IPC** (kênh/thông điệp, capability-passing); **persistence trực giao** (ảnh GIAO bền) +/hoặc
  **filesystem capability** (kho-đối-tượng, có journaling).
- **Chốt:** đa nhiệm CÔ LẬP, dữ liệu BỀN qua reboot, tiến trình giao tiếp an toàn. ≈ Minix/early-Unix-class.
- **Cỡ:** TRUNG BÌNH–LỚN.

### Pha 3 — HIỆU NĂNG  *(chạy workload thật)*  ← **GATE LỚN NHẤT**
- **C:** **trình biên dịch tối ưu** GIAO → mã native (x86/ARM/RISC-V) HOẶC GVM-ASIC pipeline
  GHz; **mô hình bộ nhớ ownership/region** (không GC pause trong nhân); inline/SSA/regalloc.
- *Mấu chốt:* memory-safety của GIAO có thể **gần-zero-cost** nếu biên dịch tốt (Rust đã chứng minh)
  → an toàn KHÔNG phải trả bằng tốc độ ở quy mô.
- **Chốt:** hiệu năng hữu dụng cho workload thật → mở cửa "đa dụng".
- **Cỡ:** **LỚN (nhiều person-year)** — không né được, paradigm nào cũng phải trả.

### Pha 4 — KẾT NỐI + ĐA LÕI  *(server-class)*
- **M:** **đa lõi (SMP)** + atomic/CAS + ngắt liên-lõi.
- **K:** lập lịch SMP cân tải (có thể **lập lịch theo γ/OR** — CDFL-native); **stack mạng**
  (TCP/IP capability) HOẶC **virtio** trên hypervisor (né đuôi-driver); mở rộng driver (NVMe/NIC).
- **Chốt:** nhiều lõi, dịch vụ mạng, lưu trữ nhanh. ≈ lõi OS server hiện đại.
- **Cỡ:** LỚN.

### Pha 5 — TƯƠNG TÁC GIÀU  *(desktop/mobile — Windows/iOS-class)*
- **G:** driver display/GPU + **compositor** + nhập (chuột/cảm ứng); âm thanh; quản lý nguồn.
- **U:** runtime app GIAO-native + ABI ổn định + công cụ dev.
- **Chốt:** OS tương tác đầy đủ. ≈ năng-lực Windows/iOS (trừ bề rộng hệ sinh thái — đã gác).
- **Cỡ:** LỚN (driver GPU là đuôi khó).

### Xuyên suốt — Track V (Kiểm chứng)
Mỗi pha: conformance đa-substrate + **verify hình thức lõi nhân** (đường mà C *không* có) →
một OS đa dụng mà **lõi được CHỨNG MINH đúng** — thứ Linux/Windows chưa từng đạt.

---

## 4. HAI CON VOI thật (và GIAO giảm nhẹ chúng ra sao)

1. 🐘 **Trình biên dịch tối ưu (Pha 3).** Bắt buộc cho tốc độ. *Giảm nhẹ:* ISA do GIAO sở hữu
   → co-design dễ; memory-safety gần-zero-cost nếu làm đúng. Vẫn là nhiều person-year.
2. 🐘 **Đuôi dài driver (Pha 4–5).** *Giảm nhẹ:* dùng **virtio + unikernel-trên-hypervisor**
   (chục driver paravirtual thay hàng nghìn) cho 80% giá trị; driver GIAO **không-gây-sập**
   (memory-safe) nên ổn định hơn. GPU vẫn là đuôi khó nhất.

*(Hai voi này paradigm-trung-lập: Linux/Windows cũng đã cưỡi chúng suốt 30 năm.)*

---

## 5. THỨ TỰ KHÔN NGOAN + bước đầu cụ thể

- **Đừng làm Pha 3 (compiler) trước** — phí công nếu chưa có OS chạy. Làm **1 → 2** trước để
  có một OS *thật, tự chủ, cô lập, bền* (đã là một OS hoàn chỉnh trong niche), RỒI mới Pha 3
  mở khoá tốc độ, rồi 4–5 mở rộng.
- **Bước đầu (Pha 1, đòn bẩy cao nhất, hạ tầng đã có):** thêm **ngắt timer + opcode MMIO** vào
  GVM (`gvm_may.py` mô phỏng trước → `hw/gvm.v` phần cứng), viết **bộ lập lịch tiền-định** +
  **driver UART**, port nhân `hdh` sang phần biên-dịch-được.

## 6. Đánh giá điểm cuối (thuần kỹ thuật)

Khả thi về NGUYÊN LÝ (Singularity/Lisp-machine/Redox/seL4/MirageOS đã chứng minh từng mảnh).
GIAO **hơn-theo-kiến-tạo** ở: an-toàn-bộ-nhớ · cô-lập (SIP) · bảo-mật (ocap) · kiểm-chứng-được ·
sở-hữu-trọn-stack. **Ngang** ở: năng-lực-lõi sau khi xây đủ 5 pha. **Tốn ngang mọi OS** ở: hai
con voi. → Một OS đa dụng **an-toàn-và-kiểm-chứng-được hơn Windows/Linux theo kiến tạo**, đạt
được bằng *ít cơ chế phần cứng hơn* (không cần MMU nhờ SIP) — một thiết kế *gọn và đúng hơn*,
không phải *to hơn*.

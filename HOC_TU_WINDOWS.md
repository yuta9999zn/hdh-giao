# HỌC TỪ WINDOWS — khảo sát cho HĐH-GIAO (giữ TRỌN bản chất GIAO)

> Khảo sát THỰC-TẠI máy đang chạy (CDFL: phơi ρ thật, không suy diễn). Mục tiêu: học CẤU-TRÚC & ĐỘ-CHÍN
> của Windows, map sang HĐH-GIAO — chỉ rõ chỗ GIAO **mạnh hơn** nhờ CDFL, **KHÔNG đánh mất bản chất**.
> Đo ngày 2026-06-16 trên Windows 11 Home build 26200.

## 0. Số liệu THẬT đo được (ρ)
| Hạng mục | Thực tại đo | Ý nghĩa |
|---|---|---|
| Tiến trình | **374** · **811,770 handle** mở | handle = tham-chiếu đối-tượng-kernel (≈ capability) |
| Kernel objects | **674,911 Events** · 14,039 Sections · 1,912 Mutexes · 6,721 threads | "mọi thứ là ĐỐI-TƯỢNG CÓ-TÊN" (Object Manager) |
| Integrity (MIC) | tiến trình ta = **Medium (S-1-16-8192)** | lưới Untrusted0·Low4096·Medium8192·High12288·System16384 — TOÀN PHẦN, no-write-up |
| Token | **5 privileges** | mỗi privilege = 1 năng-lực bật/tắt (capability) |
| Services (SCM) | 144 chạy / 154 dừng / **298** | tiến-trình-nền có vòng-đời quản-lý |
| Scheduler | Win32PrioritySeparation=**2** | quantum + BOOST foreground (heuristic) |
| Cô-lập | **VBS đang chạy (status=2)** + WSL (docker-desktop) | kernel cô-lập bằng HYPERVISOR; Linux thật cạnh Win |
| Config | **6 registry hive** | cây khoá→giá-trị phân-cấp |
| Sống động | đọc PriorityClass tiến-trình-cao → **"Access denied"** | MIC chặn Medium soi High — cô-lập THẬT, ngay lúc khảo sát |

## 1. LUẬN ĐIỂM CỐT LÕI
Windows mất ~30 năm **GẮN THÊM** capability/trust/sandbox lên một lõi *ambient-authority* (mặc-định-toàn-quyền).
GIAO có những thứ đó là **BẨM SINH**: object-capability native · tin-cậy CDFL native · memory-safe kiến-tạo (WASM/Verilog, KHÔNG qua C).
→ **Học Windows = lấy CẤU-TRÚC/độ-chín. Vượt Windows = thay RỜI-RẠC bằng γ LIÊN-TỤC + ba-trị `ẩn`.**

## 2. BẢN ĐỒ CƠ-CHẾ: Windows → GIAO-OS
| Cơ-chế Windows | Bản chất | GIAO-OS tương ứng (giữ CDFL) | GIAO mạnh hơn ở đâu |
|---|---|---|---|
| **Handle** (đối-tượng + access-mask) | object-capability | 'ô'/handle GIAO (đã có ocap I/O) | handle mang **γ** (cộng-hưởng) thay access-mask nhị-phân; quyền "ẩn"=chưa-soi |
| **MIC** (5 mức cố-định, no-write-up) | lưới tin-cậy RỜI-RẠC | **σ mỗi tác_vụ** (đã có ở γ-scheduler!) làm mức tin-cậy | σ ∈ liên-tục thay 5 nấc; "no-write-up" = chặn-ghi khi γ(người-ghi) < γ(ô); **`ẩn` cho tin-cậy CHƯA-BIẾT** (Win KHÔNG có) |
| **Token + Privileges** | năng-lực nhị-phân | capability có phạm-vi (đã có: host cấp `--cho-đọc`…) | privilege ba-trị: bật/tắt/**ẩn** (chưa-cấp ≠ từ-chối) |
| **Object Manager** (\ namespace) | namespace đối-tượng thống-nhất | mọi tài-nguyên = 'ô' trong **'bản' phân-cấp** (đã có bản lồng) | tra-cứu trả `ẩn` khi chưa-phơi (không lỗi) |
| **Scheduler** (ưu-tiên + boost, heuristic) | ưu-tiên TĨNH | **γ-scheduler BIẾT-HỌC** (đã có, chạy **gate-level**!) | HỌC độ-hữu-ích (σ←ρ) thay heuristic cứng; spin tự bị throttle |
| **Registry** (6 hive, khoá→giá-trị) | kho config phân-cấp | 'bản' lồng + **persistence trực-giao** (đã có lưu_máy/nạp_máy) | ảnh-máy đầy-đủ resumable, không chỉ config |
| **Services/SCM** (vòng-đời nền) | daemon quản-lý | tác_vụ + **nhân giám-sát** (đã có ở hdh.giao) | + cô-lập-fault (đã có: tt hỏng bị cách-ly, hệ không sập) |
| **VBS** (hypervisor cô-lập kernel) | cô-lập bằng ảo-hoá | cô-lập bằng **WASM/Verilog memory-safe** (đã có) | an-toàn KIẾN-TẠO, KHÔNG cần hypervisor vá lên C |
| **SEH** (structured exception) | xử-lý ngoại-lệ | **thử/bắt** (đã có, chạy **gate-level**) | gỡ-cuộn + ba-trị |
| **AppContainer** (sandbox + cap SID) | sandbox năng-lực | sandbox **BẨM SINH** (mọi I/O cần host cấp) | không cần "container" thêm — mặc-định KHÔNG quyền |
| **Job Objects** (nhóm + hạn-mức) | nhóm tiến-trình | **`lib_nhóm` ✅** (hạn-mức+kế-toán theo tid) | **hạn-mức γ-ĐỘNG** (σ thấp→quota co; Job tĩnh không làm nổi) + ba-trị chưa-đặt-hạn→`ẩn` |
| **Memory mgmt** (commit-charge, working-set, RAM-compression) | overcommit ảo > RAM vật-lý | kế-toán `lib_nhóm` (commit/handle theo nhóm) | trần γ-động + chưa-đo→`ẩn` (Win: commit-limit cứng) |

## 3. ĐIỀU GIAO ĐÃ HƠN (giữ vững khi học Win)
- **Ba-trị `ẩn`:** Windows chỉ allow/deny (nhị-phân). GIAO phân biệt *từ-chối* (tối) với *CHƯA-BIẾT/chưa-cấp* (ẩn) — lương-tâm thật.
- **γ liên-tục thay mức cố-định:** MIC 5 nấc cứng → GIAO σ/γ đo cộng-hưởng → tin-cậy MỀM, biết-học.
- **Memory-safe kiến-tạo:** Win cần VBS (hypervisor) vá lên lõi C. GIAO memory-safe từ NAND→WASM/Verilog, không "qua C".
- **Scheduler biết-học ở SILICON:** Win boost bằng heuristic. GIAO γ-scheduler học độ-hữu-ích, đã chạy gate-level.

## 4. ĐIỀU ĐÁNG HỌC TỪ WINDOWS (chuyển-hoá, không bê nguyên)
1. **Lưới tin-cậy có THỨ TỰ + "no-write-up":** chuẩn-hoá σ-mỗi-tác_vụ thành CHÍNH SÁCH truy-cập (γ-gated write). → việc-cần-làm: gắn σ-scheduler (đã có) vào cổng ghi tài-nguyên.
2. **Namespace đối-tượng THỐNG NHẤT:** mọi tài-nguyên (tệp/tiến-trình/sự-kiện) tra qua MỘT 'bản' gốc → đơn-giản-hoá ocap.
3. **Vòng-đời SERVICE + phụ-thuộc:** tầng quản-lý daemon (khởi-động/dừng/phụ-thuộc/tự-hồi-phục) trên nhân giám-sát.
4. **Boost foreground theo tương-tác:** thêm tín-hiệu ρ "đang-phục-vụ-người-dùng" vào γ-scheduler (đã có did_out; mở rộng).
5. **WSL = interop:** GIAO chạy CẠNH HĐH chủ (sidecar) — đúng tầm-nhìn polyglot; học cơ-chế interop của WSL.

## 5. VIỆC-CẦN-LÀM (đề xuất, ưu-tiên giữ-bản-chất)
- [ ] **Lớp BẢO MẬT γ-gated** ở tầng GIAO: dùng σ-mỗi-tác_vụ (đã có ở scheduler) làm integrity-level LIÊN-TỤC; cổng ghi tài-nguyên chặn khi γ(ghi) < γ(ô); quyền chưa-soi = `ẩn`. (map MIC → CDFL)
- [ ] **'bản' tài-nguyên gốc** (object namespace) — tra-cứu thống-nhất tệp/tác_vụ/sự-kiện, thiếu→`ẩn`.
- [ ] **Tầng SERVICE**: vòng-đời + phụ-thuộc trên nhân giám-sát + cô-lập-fault (đã có nền).
- *Ranh giới:* mọi thứ trên dựng tầng-GIAO (không cần Verilog mới); ghi `RANH_GIOI.md` cái gì máy/thông-dịch.

## 6. KHẢO-SÁT BỔ-SUNG (2026-06-19) — QUẢN-LÝ-BỘ-NHỚ + JOB OBJECTS (đo Win11 build 26200 thật, ρ)
| Hạng mục | Thực tại đo | Ý nghĩa cho GIAO-OS |
|---|---|---|
| RAM vật-lý | **15.6 GB** (free 2.43 GB → **84% dùng**) | áp-lực bộ-nhớ thật → cần kế-toán/hạn-mức |
| **Commit limit** | **36.7 GB** = RAM + pagefile | Windows **OVERCOMMIT** bộ-nhớ-ảo > vật-lý (hứa nhiều hơn có) |
| Pagefile | dùng **4993 MB** / peak 5691 / alloc 21553 MB | trang lạnh đẩy xuống đĩa khi RAM cạn |
| **Memory Compression** | **540 MB** (tiến-trình riêng) | NÉN trang RAM lạnh thay vì paging — tiết-kiệm I/O |
| Per-process | vmmemWSL 7593 MB private · claude 1112 MB | working-set/private-bytes = kế-toán mỗi tiến-trình |
| Đếm | 363 proc · 5530 thread · **1.1M handle** | quy-mô đối-tượng-kernel (handle ≈ capability) |
| CPU/Power | i9-13900H 14C/20T · scheme **Balanced** | DVFS/power-state (việc-cần-làm: γ-scheduler power-aware) |

**MAP → `lib_nhóm.giao` (tính-năng GIAO-OS #4):** Job Objects + commit-charge → nhóm tài-nguyên có **hạn-mức + kế-toán theo tid** (`đặt_hạn`/`ghi_dùng`/`tổng_dùng`/`còn`/`quá_hạn`/`xin_cấp`). **VƯỢT Windows bằng CDFL:** (1) `hạn_hiệu_dụng`/`xin_cấp_γ` — **trần CO theo tin-cậy σ** (tác_vụ xấu σ↓ ⇒ quota↓ động; Job Objects + commit-limit của Win là TĨNH); (2) **ba-trị** — chưa-đặt-hạn → `ẩn` (chính-sách phải RÕ trước khi cấp; Win mặc-định "vô-hạn tới khi sập"). Test `kiem_lib_nhóm.giao`, audit **57/57**.
**TÍNH-NĂNG GIAO-OS #5 — `lib_đồng_bộ.giao` ✅ (đồng-bộ-hoá):** map Windows critical-section/mutex · semaphore · condition-variable → `khoá_*` (lock) + `sem_*` (semaphore) + `cv_*` (condvar), hàng-chờ list. **VƯỢT bằng CDFL:** (1) ba-trị — khoá RẢNH → chủ=`ẩn` (KHÔNG sentinel "none" giả; thao-tác trên ẩn → ẩn); (2) **`khoá_mở_γ` đánh-thức γ-CÔNG-BẰNG** — trao khoá cho waiter TIN-CẬY σ CAO nhất (test: hàng [5,9,7] σ=[100,250,180] → wake t9, KHÔNG phải FIFO t5; Windows wake FIFO / priority TĨNH). Test `kiem_lib_đồng_bộ.giao`, audit **58/58**.
**★ PHÁT-HIỆN (2026-06-20) — NHÂN PREEMPTIVE CÔ-LẬP BỘ-NHỚ BẨM-SINH:** thử gắn sync-shared-memory (khoá Peterson) vào nhân preemptive gate-level → BẤT-KHẢ vì γ-scheduler cấp **vùng-nhớ RIÊNG mỗi tác_vụ** (gvm.v:551 `mbase[ntask]=ntask<<7`, [i·128,i·128+128)). Tác_vụ KHÔNG chia-sẻ ô-toàn-cục ⇒ Peterson/khoá vô-nghĩa. **Đây là ƯU-THẾ CDFL, không phải hạn-chế:** Windows = shared-memory mặc-định + data-race + vá khoá (CAS/SRW); GIAO preemptive = **cô-lập mặc-định → cả LỚP data-race KHÔNG thể xảy ra by-construction**; phối-hợp qua message-passing HOẶC qua γ-scheduler (σ-governance = quota tài-nguyên ĐÃ nằm Ở scheduler: spin-throttle). Sync+quota shared-memory chạy gate-level ở nhân HỢP-TÁC (`hdh_qs_may`, 1 context). 
*Còn (việc-cần-làm): power-aware γ-scheduler (tín-hiệu Balanced/DVFS) · IPC message-passing cho phối-hợp liên-tác_vụ trên nhân preemptive cô-lập.*

> KẾT: HĐH-GIAO không "bắt chước" Windows — nó **hấp thụ cấu-trúc đã-chín** rồi thay lõi *ambient + rời-rạc + vá-C*
> bằng lõi **capability + γ-liên-tục + ba-trị + memory-safe-kiến-tạo**. Mạnh hơn, mà KHÔNG mất bản chất GIAO.

# Đóng góp cho GIAO / HĐH-GIAO

Cảm ơn bạn đã quan tâm. Dự án này xây một **ngăn xếp tính toán từ đáy lên** — ngôn ngữ,
máy ảo bytecode, và một hệ điều hành lối Linux — trên nền logic ba trị (`sáng`/`ẩn`/`tối`)
thay cho nhị phân. Tài liệu này giúp bạn bắt tay được ngay.

## 1. Chạy thử & kiểm

Yêu cầu: **Python 3.10+**. Một số phần phần cứng cần thêm `iverilog` (đồng mô phỏng Verilog)
và `oss-cad-suite` (tổng hợp FPGA) — không bắt buộc để chạy bộ kiểm phần mềm.

```bash
# Bộ kiểm tổng — nguồn-sự-thật về trạng thái dự án
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python kiem_toan_bo.py

# Các bộ kiểm lẻ
python kiem_hdh_giao.py     # hệ điều hành (hệ tệp · quyền · gọi-hệ · vỏ · trợ lý)
python kiem_de.py           # bàn làm việc đồ hoạ
python kiem_tu_xa.py        # đăng nhập từ xa (mã hoá · rekey · chống dò)
python kiem_kho_xa.py       # kho phần mềm qua mạng

# Chạy HĐH
python chay_hdh_giao.py     # đăng nhập rồi gõ lệnh (mặc định an/an · gốc/gốc)
bat_ban.bat                 # bàn làm việc đồ hoạ (Windows)
```

**Trước khi gửi PR: bộ kiểm phải XANH.** Sổ cổng `so_cong.jsonl` ghi kết cục bộ kiểm cho
mỗi commit — đây là dữ liệu quý, đừng xoá.

## 2. Quy ước của dự án (bất di bất dịch)

- **Tên tệp/đường dẫn MỚI đặt KHÔNG DẤU** (vd `lib_sha256.giao`). Tệp cũ có dấu giữ nguyên.
  Định danh *trong mã* vẫn dùng tiếng Việt có dấu (`tâm`, `học`, `giao`…).
- **Đường dẫn dự án không được có dấu** — `iverilog`/`vvp`/`nextpnr` mở tệp bằng API ANSI,
  đường dẫn có dấu là hỏng ngay.
- Ba lớp phải giữ **khớp nhau** khi thêm opcode: `gvm_may.py` (handler) · `giaoc.py` (sinh mã) ·
  `wasm/gvm.ts` (rebuild `gvm.wasm`) · `hw/gvm.v` (cổng logic). Đổi một lớp mà quên lớp khác
  thì conformance rớt.
- Nguyên tắc gốc: **"đo trước tin sau"** — mọi tối ưu/tính năng đặt chi phí lên đường đi
  của mọi lệnh phải ĐO trước khi tin.

## 3. Bản đồ mã nguồn

| Vùng | Tệp chính |
|---|---|
| Ngôn ngữ (thông dịch) | `giao.py` |
| Trình biên dịch → bytecode | `giaoc.py` |
| Máy ảo GVM (bytecode) | `gvm_may.py`, `gvm.py` (dựng từ NAND) |
| Nhân HĐH · gọi-hệ | `lib_gọi_hệ.giao`, `lib_hệ.giao`, `hdh_nền.giao` |
| Vỏ lệnh | `lib_vỏ.giao` |
| Hệ tệp | `lib_tệp_hệ.giao`, `lib_dia.giao` |
| Bàn làm việc | `giao_de.py`, `de/` |
| Bảo mật | `lib_sha256.giao`, `lib_chacha20.giao`, `lib_chu_ky.giao`, `lib_dh.giao` |
| Phần cứng | `hw/gvm.v`, `hw/lam_cosim.py` |
| Hồ sơ tồn đọng | `CÒN_THIẾU.md` (nguồn sự thật việc-cần-làm) |
| Ảnh chụp tiến độ | `TIEN_DO.md` |

## 4. Việc còn mở (bắt đầu từ đây)

Xem `CÒN_THIẾU.md` — mỗi mục đã ghi sẵn **bắt đầu ở đâu** và **kiểm bằng gì**. Việc lớn còn lại:
B4 (tiền định trọn vẹn) · B3 đuôi (đĩa vật lý · thư mục con · xoá tệp) · B5 (cô lập bộ nhớ) ·
G1/G4 (biểu tượng nền · nhiều bàn ảo · nhiều phiên đồ hoạ) · thư viện chuẩn kiểu Python/Ruby.

## 5. Khoá mật mã trong repo là KHOÁ DEMO

Các tệp khoá riêng (`khoa_rieng.txt`, `khoa_may.txt`, `kho_xa/khoa_rieng.txt`) **không được
commit** — chúng nằm trong `.gitignore` và được **sinh tự động** khi chạy lần đầu
(`python chay_kho_xa.py --dựng`, hoặc `bat_xa.bat` sinh khoá máy). Bản sinh ra là **khoá đồ chơi
để dạy/chạy dự án**, KHÔNG dùng cho bí mật thật (xem chú thích trong `lam_khoa.py`). Đừng đưa
khoá riêng thật vào repo.

## 6. Gửi đóng góp

Mở issue để bàn trước với thay đổi lớn. Mỗi PR: mô tả *vì sao*, kèm bộ kiểm xanh, và một dòng
cho `TIEN_DO.md` nếu chạm tính năng. Đóng góp của bạn được nhận theo giấy phép **Apache-2.0**
(xem `LICENSE`).

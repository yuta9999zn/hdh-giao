# Dạy GIAO tự theo dõi máy đang truy cập wifi

GIAO (hệ điều hành của bạn) tự khởi động bắt gói và tự xem — Claude chỉ viết mã, **bạn chạy**.
Cơ chế: GIAO dùng năng lực `chạy` (host command) bắc qua `wsl` vào Kali chạy bộ bắt gói Rust.
Kết quả `so_soi.jsonl` được GIAO đọc lại bằng `--cho-đọc`.

## Chuẩn bị một lần — build bộ bắt gói (chạy trong terminal)
```
wsl -d kali-linux -- bash /mnt/d/HeDieuHanh/GIAO/soi_mang/build_kali.sh
```

## 3 lệnh GIAO

### 1) BẬT theo dõi (mặc định máy 192.168.1.46 — sửa IP trong bat_theo_doi.giao)
```
python giao.py bat_theo_doi.giao --cho-chạy "wsl -d kali-linux -- bash /mnt/d/HeDieuHanh/GIAO/soi_mang/start_soi.sh"
```
→ GIAO tự chạy bắt gói NỀN. Trả về ngay (không treo).

### 2) XEM họ đang vào gì (đọc live, chạy lại để làm mới)
```
python giao.py theo_doi_mang.giao --cho-đọc .
```
→ Hiện tên miền máy .46 / .32 đã truy cập (dns/sni), gom không trùng.

### 3) TẮT (và tự vá ARP trả mạng)
```
python giao.py tat_theo_doi.giao --cho-chạy "wsl -d kali-linux -- bash /mnt/d/HeDieuHanh/GIAO/soi_mang/tat_soi.sh"
```

## Quan trọng
- Chuỗi sau `--cho-chạy` phải **khớp y hệt** đầu lệnh trong tệp `.giao` (allowlist theo tiền tố tại biên từ). Đã đặt sẵn khớp.
- Chỉ thấy **TÊN MIỀN** (youtube.com…), **không thấy nội dung** — HTTPS mã hoá. Giới hạn thật.
- Máy .46 đang ngồi im thì bắt được ít; theo dõi lúc nó đang lướt.
- `--cho-chạy` là năng lực MẠNH (cho GIAO chạy lệnh host). Chỉ cấp đúng chuỗi này, đừng cấp trần "wsl".

## Luồng tổng
```
GIAO (Windows, giao.py)
  └─ chạy(wsl → Kali) ─► start_soi.sh ─► sudo soi_mang chen eth0 <ip>  (raw ARP, nền)
                                              └─► ghi live so_thiet_bi/so_soi.jsonl (ổ D:)
GIAO  ◄── đọc so_soi.jsonl (--cho-đọc .) ── theo_doi_mang.giao  (hiện tên miền, ba-trị)
```

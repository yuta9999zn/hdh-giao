# soi_mang — soi mạng nhà của GIAO

Lớp **gốc (Rust)** bắt/gửi khung Ethernet thật để GIAO nhìn được mạng wifi thật.
Không bê nguyên `arp-scan`/`bettercap` — học nguyên lý ARP rồi gói lại theo **ba-trị
`sáng/tối/ẩn`** của GIAO, và trả kết quả ra JSONL cho app `.giao` đọc qua cầu nối.

## Vì sao Rust, vì sao chạy dưới WSL/Kali

- Lớp mạng cũ trong `lib_gọi_hệ.giao` (`GH_NGHE/GH_NỐI/GH_GỬI_GÓI`) là **mạng mô phỏng
  trong VM** — không đụng phần cứng, nên không thấy wifi thật.
- Bắt gói thật cần **raw socket** → cần Linux (`AF_PACKET`). Máy bạn là Windows nên phần
  này chạy dưới **WSL/Kali**, nơi bạn đã có quyền raw. GIAO chỉ việc đọc file kết quả.

## Ba-trị áp cho mạng

| Thế | Ý nghĩa mạng |
|---|---|
| `sáng` | có ARP reply → **chắc chắn đang online** |
| `tối` | bị chặn / từ chối (vd ta chủ động chặn, hoặc có filter) |
| `ẩn` | **im lặng, chưa rõ** — KHÔNG kết luận là đã tắt |

Điểm cốt: máy im lặng là `ẩn`, không phải `tối`. Khiêm tốn nhận thức ở tầng công cụ.

## Kiến trúc (mỗi tầng 1 module)

```
main.rs      CLI: lệnh `quet` và `chen`
nic.rs       LỚP GỐC — trait Nic (gửi/nhận khung thô). Đổi HDH chỉ cần viết lại đây.
             Hiện có NicLinux (AF_PACKET).
mac.rs       kiểu MAC, tách OUI, nhận biết MAC ngẫu nhiên (máy giấu danh tính)
arp.rs       đóng/đọc gói ARP; bộ QUÉT Tầng 1
oui.rs       tra hãng theo MAC (nạp thêm oui.txt của IEEE nếu có)
soi.rs       bóc TÊN MIỀN từ DNS query + TLS SNI
chen.rs      ARP spoof/MITM + KHÔI PHỤC sạch khi thoát
bat_tri.rs   ba-trị sáng/tối/ẩn
```

## Build & chạy (trong Kali WSL)

```bash
# cần cargo: sudo apt install -y cargo   (hoặc rustup)
cd /mnt/d/HeDieuHanh/GIAO/soi_mang
cargo build --release

# TẦNG 1 — ai đang nối wifi:
sudo ./target/release/soi_mang quet wlan0
#   → bảng IP/MAC/hãng + ghi so_thiet_bi.jsonl

# CHEN (MITM) — soi tên miền một máy (CHỈ mạng bạn sở hữu):
sudo ./target/release/soi_mang chen wlan0 192.168.1.23
#   → in [dns]/[sni] tên miền máy đó vào; ghi so_soi.jsonl; Ctrl-C để dừng & vá ARP
```

> Tên giao diện: chạy `ip link` để biết (thường `wlan0` cho wifi, `eth0` cho dây).

## Ranh giới thành thật

- **HTTPS chỉ lộ TÊN MIỀN** (qua DNS/SNI), **không lộ nội dung**. Đây là giới hạn thật
  của mật mã, không phải thiếu code. Muốn thấy nội dung phải cài chứng chỉ giả lên máy
  nạn nhân — không làm ở đây.
- `chen` là **kỹ thuật tấn công**: chỉ dùng trên mạng bạn sở hữu/được phép. Nó làm mạng
  chậm; luôn để nó **khôi phục ARP** khi thoát (đã cài sẵn, kể cả khi Ctrl-C).
- MAC chỉ cho biết **hãng thiết bị**, không phải **tên người**. MAC ngẫu nhiên (điện
  thoại đời mới) sẽ được đánh dấu "nghi giấu danh tính".

## Việc tiếp theo (gợi ý)

1. **Tầng 3 — canh & chặn**: whitelist MAC, quét định kỳ, báo động khi có MAC lạ.
2. Cầu nối `.giao`: một lệnh gọi-hệ `GH_SOI_MANG` đọc `so_thiet_bi.jsonl` → app GIAO
   hiện danh sách máy như một tài nguyên ba-trị.
3. Nạp `oui.txt` đầy đủ của IEEE để tra hãng chính xác hơn.

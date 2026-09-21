#!/bin/bash
# start_soi.sh — GIAO gọi để BẬT bắt gói CHẠY NỀN, sống sót sau khi wsl.exe trở về.
# Mấu chốt: setsid (tách phiên riêng) + nohup — nếu không, WSL giết tiến trình ngay
# khi lệnh gọi từ Windows kết thúc.
IP="${1:-192.168.1.46}"
GIAY="${2:-600}"
cd /mnt/d/HeDieuHanh/GIAO/soi_mang || exit 9

if [ ! -x target/release/soi_mang ]; then
  echo "LOI: chua build binary. Chay: bash soi_mang/build_kali.sh"
  exit 3
fi

# dừng phiên cũ nếu còn (tránh chèn chồng)
sudo pkill -TERM -f 'target/release/soi_mang chen' 2>/dev/null
sleep 1

# setsid + nohup: tiến trình thoát khỏi phiên của wsl.exe → không bị giết theo.
setsid nohup sudo ./target/release/soi_mang chen eth0 "$IP" "$GIAY" >soi_chen.log 2>&1 </dev/null &
disown 2>/dev/null

# kiểm chứng nó thật sự sống
sleep 2
if pgrep -f 'target/release/soi_mang chen' >/dev/null; then
  echo "OK: dang theo doi $IP (toi da ${GIAY}s) — so_soi.jsonl cap nhat live"
else
  echo "LOI: tien trinh chet ngay. Log:"
  tail -6 soi_chen.log
fi

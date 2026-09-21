#!/bin/bash
# start_ngat.sh — GIAO gọi để BẬT "đá theo nhịp": cho máy dùng N phút rồi cắt, lặp mãi.
# setsid + nohup để sống sót sau khi wsl.exe trở về.
IP="${1:-192.168.1.32}"
PHUT="${2:-5}"       # cho dùng bao nhiêu phút
CAT="${3:-20}"      # rồi cắt bao nhiêu giây
cd /mnt/d/HeDieuHanh/GIAO/soi_mang || exit 9

if [ ! -x target/release/soi_mang ]; then
  echo "LOI: chua build binary. Chay: bash soi_mang/build_kali.sh"
  exit 3
fi

# dừng phiên đá cũ nếu còn
sudo pkill -TERM -f 'target/release/soi_mang ngat' 2>/dev/null
sleep 1

setsid nohup sudo ./target/release/soi_mang ngat eth0 "$IP" "$PHUT" "$CAT" >soi_ngat.log 2>&1 </dev/null &
disown 2>/dev/null

sleep 2
if pgrep -f 'target/release/soi_mang ngat' >/dev/null; then
  echo "OK: dang da $IP — cho dung ${PHUT} phut roi cat ${CAT}s, lap mai. Go 'thoi-da' de dung."
else
  echo "LOI: tien trinh chet ngay. Log:"; tail -6 soi_ngat.log
fi

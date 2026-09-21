#!/bin/bash
# TANG 3 — canh gac: quet moi 30s, bao dong may LA (MAC ngoai danh_biet.txt).
# Lan dau tao danh_biet.txt lam baseline — HAY MO FILE, xoa dong nao khong phai may ban.
# Them --chan de tu cat mang may la. Ctrl-C de dung.
cd /mnt/d/HeDieuHanh/GIAO/soi_mang || exit 9
CHUKY="${1:-30}"
echo "== canh gac moi ${CHUKY}s (them 'chan' o cuoi de cat mang may la) =="
if [ "$2" = "chan" ]; then
  sudo ./target/release/soi_mang canh eth0 "$CHUKY" --chan
else
  sudo ./target/release/soi_mang canh eth0 "$CHUKY"
fi

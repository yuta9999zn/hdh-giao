#!/bin/bash
# NGAT NHIP: cho may .166 dung mang 5 phut roi CAT 20 giay, lap mai.
# Ctrl-C de dung va tra lai mang. Doi IP/thoi gian bang tham so: bash ngat_kali.sh <ip> <phut> <giay_cat>
IP="${1:-192.168.1.166}"
PHUT="${2:-5}"
CAT="${3:-20}"
cd /mnt/d/HeDieuHanh/GIAO/soi_mang || exit 9
echo "== ngat nhip $IP: dung ${PHUT} phut / cat ${CAT}s, lap lai (Ctrl-C de dung) =="
sudo ./target/release/soi_mang ngat eth0 "$IP" "$PHUT" "$CAT"

#!/bin/bash
# MITM soi ten mien 1 may (mac dinh .166 Intel). Tu dung sau 45s, tu va ARP.
# Doi IP o dong duoi neu muon may khac.
IP="${1:-192.168.1.166}"
GIAY="${2:-45}"
cd /mnt/d/HeDieuHanh/GIAO/soi_mang || exit 9
echo "== chen (MITM) $IP trong ${GIAY}s =="
sudo ./target/release/soi_mang chen eth0 "$IP" "$GIAY"
echo "== ket qua ten mien (so_soi.jsonl) =="
cat so_soi.jsonl 2>/dev/null || echo "(chua boc duoc ten mien nao — may co the dang im)"

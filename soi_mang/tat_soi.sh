#!/bin/bash
# tat_soi.sh — GIAO gọi để DỪNG mọi hoạt động chủ động (theo-dõi + đá).
# SIGTERM → tool tự vá ARP trả mạng.
n=0
if sudo pkill -TERM -f 'target/release/soi_mang chen' 2>/dev/null; then n=1; fi
if sudo pkill -TERM -f 'target/release/soi_mang ngat' 2>/dev/null; then n=1; fi
if [ "$n" = "1" ]; then
  echo "da dung (theo-doi/da) — ARP se tu va, mang tra lai binh thuong"
else
  echo "khong co phien theo-doi/da nao dang chay"
fi

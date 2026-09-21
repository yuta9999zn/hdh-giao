#!/bin/bash
# lam_lai.sh — LAM LAI TU DAU: build + don dep + quet. Chay 1 lenh trong Kali:
#   bash /mnt/d/HeDieuHanh/GIAO/soi_mang/lam_lai.sh
cd /mnt/d/HeDieuHanh/GIAO/soi_mang || { echo "khong vao duoc thu muc"; exit 9; }

echo "===== [1/4] DUNG PHIEN CU + DON KET QUA CU ====="
sudo pkill -TERM -f 'soi_mang chen' 2>/dev/null
sleep 1
rm -f so_soi.jsonl soi_chen.log
echo "ok"

echo "===== [2/4] BUILD (cho ~20-30s) ====="
export CARGO_HOME=$PWD/.cargo_home
cargo build --release 2>&1 | tail -6
if [ ! -x target/release/soi_mang ]; then
  echo "!!! BUILD LOI — dung lai, dan output tren cho tro ly"
  exit 1
fi
echo "binary moi: $(ls -la --time-style=+%H:%M:%S target/release/soi_mang | awk '{print $6}')"

echo "===== [3/4] QUET WIFI (ai dang noi) ====="
sudo ./target/release/soi_mang quet eth0

echo
echo "===== [4/4] XONG ====="
echo "Gio MO HDH-GIAO (nhay dup bat_may.bat, dang nhap goc/goc) roi go:"
echo "   soi-mang               # ai dang noi wifi"
echo "   theo-doi 192.168.1.46  # bat theo doi may .46"
echo "   xem-vao                # ho vao ten mien gi (go lai de lam moi)"
echo "   tat-doi                # dung + tra mang"

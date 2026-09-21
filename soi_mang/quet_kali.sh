#!/bin/bash
cd /mnt/d/HeDieuHanh/GIAO/soi_mang || exit 9
export CARGO_HOME=/mnt/d/HeDieuHanh/GIAO/soi_mang/.cargo_home
echo "== build =="
cargo build --release 2>&1 | tail -3
echo "== quet eth0 (mang that 192.168.1.0/24) =="
sudo ./target/release/soi_mang quet eth0

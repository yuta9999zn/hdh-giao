#!/bin/bash
cd /mnt/d/HeDieuHanh/GIAO/soi_mang || exit 9
export CARGO_HOME=/mnt/d/HeDieuHanh/GIAO/soi_mang/.cargo_home
cargo build --release 2>&1
echo "---build rc=$?---"
ls -la target/release/soi_mang 2>&1

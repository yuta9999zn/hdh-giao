#!/bin/sh
# Dựng Argon2 THAM CHIẾU (ben_ngoai/argon2, không sửa) thành WASM bằng wasi-sdk:
#   wasm/argon2.wasm       — module reactor cho GVM-64 (nạp: wasmtime run --preload argon2=wasm/argon2.wasm …)
#   wasm/argon2_lenh.wasm  — lệnh WASI cho trình thông dịch giao.py (đọc stdin, in hex)
# Cần wasi-sdk (https://github.com/WebAssembly/wasi-sdk). WASI_SDK mặc định D:/wasi-sdk/wasi-sdk-34.0-x86_64-windows.
set -e
cd "$(dirname "$0")/.."
SDK="${WASI_SDK:-/d/wasi-sdk/wasi-sdk-34.0-x86_64-windows}"
CC="$SDK/bin/clang"
A=ben_ngoai/argon2
NGUON="$A/src/argon2.c $A/src/core.c $A/src/ref.c $A/src/encoding.c $A/src/blake2/blake2b.c"
CO="--target=wasm32-wasip1 --sysroot=$SDK/share/wasi-sysroot -O3 -DARGON2_NO_THREADS -I$A/include -I$A/src"
"$CC" $CO -mexec-model=reactor $NGUON wasm/argon2_gvm.c -o wasm/argon2.wasm
"$CC" $CO $NGUON wasm/argon2_gvm.c wasm/argon2_lenh.c -o wasm/argon2_lenh.wasm
ls -la wasm/argon2.wasm wasm/argon2_lenh.wasm

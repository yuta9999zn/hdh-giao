#!/bin/sh
# Dựng gvm64.wasm (AssemblyScript → WASM). Kết quả CHỈ import WASI (fd_read/fd_write/args/clock/proc_exit).
# Node chỉ cần để CHẠY trình biên dịch asc lúc dựng; máy chạy trên runtime WASI bất kỳ (wasmtime…).
cd "$(dirname "$0")/.." && npx -y -p assemblyscript@0.28.20 asc wasm/gvm64.ts   --outFile wasm/gvm64.wasm --optimize --runtime incremental --use abort=

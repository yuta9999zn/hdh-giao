#!/bin/sh
# Dựng wasm/bam_lenh.wasm — SHA-256 (FIPS 180-4, wasm/bam_lenh.c) thành lệnh WASI cho giao.py (builtin `băm_sha256`).
# GHIM SHA-256 ở wasm/bam.sha256 (bản dựng tái lập được): khác ghim ⇒ thất bại; cố ý đổi mã/trình dịch: --ghim.
# Cần wasi-sdk. WASI_SDK mặc định D:/wasi-sdk/wasi-sdk-34.0-x86_64-windows.
set -e
cd "$(dirname "$0")/.."
SDK="${WASI_SDK:-/d/wasi-sdk/wasi-sdk-34.0-x86_64-windows}"
"$SDK/bin/clang" --target=wasm32-wasip1 --sysroot="$SDK/share/wasi-sysroot" -O2 wasm/bam_lenh.c -o wasm/bam_lenh.wasm
if [ "$1" = "--ghim" ]; then
  sha256sum wasm/bam_lenh.wasm | sed 's/ \*/  /' > wasm/bam.sha256; echo "đã GHIM:"; cat wasm/bam.sha256
else
  sha256sum -c wasm/bam.sha256 || { echo "hash KHÁC ghim — nếu cố ý đổi: sh wasm/dung_bam.sh --ghim" >&2; exit 1; }
fi

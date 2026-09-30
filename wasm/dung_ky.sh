#!/bin/sh
# Dựng wasm/ky_lenh.wasm — KÝ KÉP ML-DSA-65 (PQClean @ 0586a82, vendor nguyên văn) + Ed25519 (Monocypher
# 4.0.3, vendor nguyên văn) bằng wasi-sdk. Keo nối duy nhất: wasm/ky_lenh.c.
# Ngăn xếp 1 MiB: ký ML-DSA-65 đặt mảng lớn trên ngăn xếp, mặc định 64 KiB của wasm-ld TRÀN (bẫy bộ nhớ).
# GHIM SHA-256 ở wasm/ky.sha256 (bản dựng tái lập được): khác ghim ⇒ thất bại; cố ý đổi: --ghim.
set -e
cd "$(dirname "$0")/.."
SDK="${WASI_SDK:-/d/wasi-sdk/wasi-sdk-34.0-x86_64-windows}"
Q=ben_ngoai/pqclean; M=ben_ngoai/monocypher
NGUON="$Q/mldsa65/ntt.c $Q/mldsa65/packing.c $Q/mldsa65/poly.c $Q/mldsa65/polyvec.c $Q/mldsa65/reduce.c
       $Q/mldsa65/rounding.c $Q/mldsa65/sign.c $Q/mldsa65/symmetric-shake.c $Q/common/fips202.c
       $M/monocypher.c $M/monocypher-ed25519.c wasm/ky_lenh.c"
"$SDK/bin/clang" --target=wasm32-wasip1 --sysroot="$SDK/share/wasi-sysroot" -O2 \
  -Wl,-z,stack-size=1048576 -I$Q/mldsa65 -I$Q/common -I$M $NGUON -o wasm/ky_lenh.wasm
if [ "$1" = "--ghim" ]; then
  sha256sum wasm/ky_lenh.wasm | sed 's/ \*/  /' > wasm/ky.sha256; echo "đã GHIM:"; cat wasm/ky.sha256
else
  sha256sum -c wasm/ky.sha256 || { echo "hash KHÁC ghim — nếu cố ý đổi: sh wasm/dung_ky.sh --ghim" >&2; exit 1; }
fi

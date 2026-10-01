#!/bin/sh
# Dựng wasm/ky_lenh.wasm — KÝ KÉP ML-DSA-65 (mldsa-native v2.0.0 @ 834a90d, vendor nguyên văn, bản dựng một
# khối mldsa_native.c) + Ed25519 (Monocypher 4.0.3, vendor nguyên văn) bằng wasi-sdk. Keo nối: wasm/ky_lenh.c.
# MLD_CONFIG_NO_RANDOMIZED_API: thư viện không có đường lấy ngẫu nhiên nào — hạt/rnd do bên gọi đưa.
# Ngăn xếp 1 MiB: ký ML-DSA-65 đặt mảng lớn trên ngăn xếp, mặc định 64 KiB của wasm-ld TRÀN (bẫy bộ nhớ).
# GHIM SHA-256 ở wasm/ky.sha256 (bản dựng tái lập được): khác ghim ⇒ thất bại; cố ý đổi: --ghim.
set -e
cd "$(dirname "$0")/.."
SDK="${WASI_SDK:-/d/wasi-sdk/wasi-sdk-34.0-x86_64-windows}"
N=ben_ngoai/mldsa-native; M=ben_ngoai/monocypher
"$SDK/bin/clang" --target=wasm32-wasip1 --sysroot="$SDK/share/wasi-sysroot" -O2 \
  -DMLD_CONFIG_PARAMETER_SET=65 -DMLD_CONFIG_NO_RANDOMIZED_API \
  -Wl,-z,stack-size=1048576 -I$N -I$M \
  $N/mldsa_native.c $M/monocypher.c $M/monocypher-ed25519.c wasm/ky_lenh.c -o wasm/ky_lenh.wasm
# ky.wasm: module reactor CHỈ KIỂM cho GVM-64 (--preload ky=wasm/ky.wasm), 0 import
"$SDK/bin/clang" --target=wasm32-wasip1 --sysroot="$SDK/share/wasi-sysroot" -O2 -mexec-model=reactor   -DMLD_CONFIG_PARAMETER_SET=65 -DMLD_CONFIG_NO_RANDOMIZED_API -DMLD_CONFIG_NO_KEYPAIR_API -DMLD_CONFIG_NO_SIGN_API   -Wl,-z,stack-size=1048576 -I$N -I$M   $N/mldsa_native.c $M/monocypher.c $M/monocypher-ed25519.c wasm/ky_gvm.c -o wasm/ky.wasm
if [ "$1" = "--ghim" ]; then
  sha256sum wasm/ky_lenh.wasm wasm/ky.wasm | sed 's/ \*/  /' > wasm/ky.sha256; echo "đã GHIM:"; cat wasm/ky.sha256
else
  sha256sum -c wasm/ky.sha256 || { echo "hash KHÁC ghim — nếu cố ý đổi: sh wasm/dung_ky.sh --ghim" >&2; exit 1; }
fi

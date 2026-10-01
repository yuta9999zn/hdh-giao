/* ky_gvm.c — KIỂM KÝ KÉP (ML-DSA-65 mldsa-native + Ed25519 Monocypher) cho GVM-64, dạng module reactor.
 *
 * Dựng thành wasm/ky.wasm (sh wasm/dung_ky.sh). GVM-64 nạp: wasmtime run --preload ky=wasm/ky.wasm …
 * Module CHỈ KIỂM (không có hàm ký, không giữ khoá riêng): máy người dùng chỉ cần khoá công — như apt.
 * Hai module có bộ nhớ riêng: GVM-64 chép đầu vào vào đây từng byte (k_dat) rồi gọi k_kiem_kep.
 * Bố cục VAO: pk_ed (32) | pk_ml (1952) | thông_điệp | ngữ_cảnh | ký_ed (64) | ký_ml.
 * Không import gì (không tệp, không mạng, không ngẫu nhiên).
 */
#include <stdint.h>
#include <string.h>
#include "mldsa_native.h"
#include "monocypher-ed25519.h"

#define ML(sym) PQCP_MLDSA_NATIVE_MLDSA65_##sym
#define TRAN 1048576
static uint8_t VAO[TRAN];

__attribute__((export_name("k_dat"))) int k_dat(int i, int b) {
    if (i < 0 || i >= TRAN || b < 0 || b > 255) return -1;
    VAO[i] = (uint8_t)b; return 0;
}

/* → bit 1 = Ed25519 hợp lệ · bit 2 = ML-DSA-65 hợp lệ (3 = cả hai) · -1 = độ dài sai */
__attribute__((export_name("k_kiem_kep"))) int k_kiem_kep(int lm, int lctx, int lml) {
    if (lm < 0 || lctx < 0 || lctx > 255 || lml < 0) return -1;
    long long can = 32LL + MLDSA65_PUBLICKEYBYTES + lm + lctx + 64 + lml;
    if (can > TRAN) return -1;
    const uint8_t *pk_ed = VAO, *pk_ml = VAO + 32, *m = pk_ml + MLDSA65_PUBLICKEYBYTES;
    const uint8_t *ctx = m + lm, *s_ed = ctx + lctx, *s_ml = s_ed + 64;
    int ok_ed = crypto_ed25519_check(s_ed, pk_ed, m, (size_t)lm) == 0;
    int ok_ml = lml == MLDSA65_BYTES && ML(verify)(s_ml, m, (size_t)lm, ctx, (size_t)lctx, pk_ml) == 0;
    return ok_ed | (ok_ml << 1);
}

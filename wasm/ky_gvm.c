/* ky_gvm.c — KIỂM KÝ KÉP (ML-DSA-65 mldsa-native + Ed25519 Monocypher) cho GVM-64, dạng module reactor.
 *
 * Dựng thành wasm/ky.wasm (sh wasm/dung_ky.sh). GVM-64 nạp: wasmtime run --preload ky=wasm/ky.wasm …
 * Kiểm chữ ký (HĐH dùng). Từ v0.43 có thêm sinh khoá/ký cho công cụ làm gói — khoá riêng KHÔNG nằm trong module:
 * bên gọi đưa vào mỗi lần, module xoá ngay sau khi dùng.
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

/* ---- v0.43: SINH KHOÁ + KÝ (cho công cụ làm gói viết bằng GIAO — goi.giao). Khoá riêng KHÔNG nằm trong
 * HĐH: công cụ đọc nó từ stdin rồi đưa vào đây; hạt và rnd do bên gọi lấy từ random_get rồi truyền vào. ---- */
static uint8_t RA[64 + MLDSA65_BYTES];
static uint8_t pk[MLDSA65_PUBLICKEYBYTES], sk[MLDSA65_SECRETKEYBYTES];
__attribute__((export_name("k_lay"))) int k_lay(int i) {
    if (i < 0 || i >= (int)sizeof RA) return -1;
    return RA[i];
}
/* VAO: ξ (32) | hạt_ed (32) → RA: pk_ed (32) | pk_ml (1952). Trả 0 hoặc -1. */
__attribute__((export_name("k_khoa"))) int k_khoa(void) {
    uint8_t hat[32], skd[64];
    if (ML(keypair_internal)(pk, sk, VAO) != 0) return -1;
    memcpy(hat, VAO + 32, 32); crypto_ed25519_key_pair(skd, RA, hat); crypto_wipe(skd, 64);
    memcpy(RA + 32, pk, MLDSA65_PUBLICKEYBYTES); crypto_wipe(sk, sizeof sk); crypto_wipe(VAO, 64);
    return 0;
}
/* VAO: ξ (32) | hạt_ed (32) | rnd (32) | thông_điệp (lm) | ngữ_cảnh (lctx) → RA: ký_ed (64) | ký_ml (3309). */
__attribute__((export_name("k_ky_kep"))) int k_ky_kep(int lm, int lctx) {
    if (lm < 0 || lctx < 0 || lctx > 255 || 96LL + lm + lctx > TRAN) return -1;
    const uint8_t *m = VAO + 96, *ctx = m + lm;
    uint8_t hat[32], skd[64], pkd[32], pre[MLD_DOMAIN_SEPARATION_MAX_BYTES];
    if (ML(keypair_internal)(pk, sk, VAO) != 0) return -1;
    size_t npre = ML(prepare_domain_separation_prefix)(pre, NULL, 0, ctx, (size_t)lctx, MLD_PREHASH_NONE);
    if (npre == 0) return -1;
    int r = ML(signature_internal)(RA + 64, m, (size_t)lm, pre, npre, VAO + 64, sk, 0);
    crypto_wipe(sk, sizeof sk);
    if (r != 0) return -1;
    memcpy(hat, VAO + 32, 32); crypto_ed25519_key_pair(skd, pkd, hat);
    crypto_ed25519_sign(RA, skd, m, (size_t)lm); crypto_wipe(skd, 64); crypto_wipe(VAO, 96);
    return 0;
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

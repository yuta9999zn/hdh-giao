/* ky_lenh.c — KÝ KÉP ML-DSA-65 (mldsa-native, FIPS 204) + Ed25519 (Monocypher, RFC 8032), bọc thành lệnh WASI.
 *
 * Mã mật mã là mã VENDOR NGUYÊN VĂN (ben_ngoai/mldsa-native v2.0.0, ben_ngoai/monocypher 4.0.3) — tệp này chỉ
 * là keo nối: đọc yêu cầu từ stdin, gọi hàm, in kết quả hex. Dựng: sh wasm/dung_ky.sh → wasm/ky_lenh.wasm.
 * Chạy: wasmtime run wasm/ky_lenh.wasm  (không cấp thư mục, không mạng).
 * (v0.40 dùng PQClean — đã lưu trữ 2026-08; v0.41 chuyển sang mldsa-native, cùng chuẩn, cùng giao thức.)
 *
 * mldsa-native dựng với MLD_CONFIG_NO_RANDOMIZED_API: thư viện KHÔNG có đường lấy ngẫu nhiên nào. Chỉ
 * dùng các hàm "internal" nhận hạt từ bên gọi: keypair_internal(ξ), signature_internal(…, rnd, …).
 *
 * stdin : 1 byte MÃ LỆNH, rồi các TRƯỜNG, mỗi trường = u32 little-endian độ dài + bấy nhiêu byte.
 * stdout: kết quả hex (một dòng) · lỗi: "LOI <mô tả>" và mã thoát 1.
 *   1 mldsa_khoa (ξ 32)                      → pk ‖ sk      (ML-DSA.KeyGen_internal với ξ — FIPS 204 Alg. 6)
 *   2 mldsa_ky   (sk, thông_điệp, ngữ_cảnh, rnd 32) → chữ ký (ML-DSA.Sign: M' = 0 ‖ |ctx| ‖ ctx ‖ M; rnd = 0³²
 *                                             ⇒ biến thể TẤT ĐỊNH)
 *   3 mldsa_kiem (pk, thông_điệp, ngữ_cảnh, chữ_ký) → "1" hợp lệ / "0" không
 *   4 ed_khoa    (hạt 32)                    → pk (32)
 *   5 ed_ky      (hạt 32, thông_điệp)        → chữ ký (64)
 *   6 ed_kiem    (pk, thông_điệp, chữ_ký)    → "1" / "0"
 *   7 kiem_kep   (pk_ed, pk_ml, thông_điệp, ngữ_cảnh, ký_ed, ký_ml) → "11"/"10"/"01"/"00" (Ed25519, ML-DSA)
 *   8 ky_kep     (ξ, hạt_ed, thông_điệp, ngữ_cảnh, rnd 32) → ký_ed (64) ‖ ký_ml (3309)
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "mldsa_native.h"
#include "monocypher-ed25519.h"

#define ML(sym) PQCP_MLDSA_NATIVE_MLDSA65_##sym
enum { PK = MLDSA65_PUBLICKEYBYTES, SK = MLDSA65_SECRETKEYBYTES, SIG = MLDSA65_BYTES };

#define TRAN 1048576
static uint8_t VAO[TRAN + 64];
static size_t NVAO, VT;

static int truong(const uint8_t **p, size_t *n) {
    if (VT + 4 > NVAO) return -1;
    uint32_t L = (uint32_t)VAO[VT] | ((uint32_t)VAO[VT + 1] << 8) | ((uint32_t)VAO[VT + 2] << 16) | ((uint32_t)VAO[VT + 3] << 24);
    VT += 4;
    if (L > NVAO - VT) return -1;
    *p = VAO + VT; *n = L; VT += L; return 0;
}
static void hex(const uint8_t *p, size_t n) { for (size_t i = 0; i < n; i++) printf("%02x", p[i]); printf("\n"); }
static int loi(const char *m) { printf("LOI %s\n", m); return 1; }

static uint8_t pk[PK], sk[SK], sig[SIG];

/* ML-DSA.Sign thuần (external/pure) có ngữ cảnh, với rnd do bên gọi đưa */
static int ky_ml(const uint8_t *m, size_t nm, const uint8_t *ctx, size_t nctx, const uint8_t rnd[32], const uint8_t *khoa) {
    uint8_t pre[MLD_DOMAIN_SEPARATION_MAX_BYTES];
    size_t npre = ML(prepare_domain_separation_prefix)(pre, NULL, 0, ctx, nctx, MLD_PREHASH_NONE);
    if (npre == 0) return -1;
    return ML(signature_internal)(sig, m, nm, pre, npre, rnd, khoa, 0);
}

int main(void) {
    NVAO = fread(VAO, 1, TRAN + 1, stdin);
    if (NVAO < 1 || NVAO > TRAN) return loi("đầu vào rỗng hoặc quá lớn");
    uint8_t lenh = VAO[0]; VT = 1;
    const uint8_t *a, *b, *c, *d; size_t na, nb, nc, nd;
    switch (lenh) {
    case 1:
        if (truong(&a, &na) || na != 32) return loi("mldsa_khoa cần ξ 32 byte");
        if (ML(keypair_internal)(pk, sk, a) != 0) return loi("keypair thất bại");
        for (int i = 0; i < PK; i++) printf("%02x", pk[i]);
        hex(sk, SK); return 0;
    case 2:
        if (truong(&a, &na) || truong(&b, &nb) || truong(&c, &nc) || truong(&d, &nd)) return loi("mldsa_ky thiếu trường");
        if (na != SK || nc > 255 || nd != 32) return loi("mldsa_ky: sk/ngữ cảnh/rnd sai độ dài");
        if (ky_ml(b, nb, c, nc, d, a) != 0) return loi("ký thất bại");
        hex(sig, SIG); return 0;
    case 3:
        if (truong(&a, &na) || truong(&b, &nb) || truong(&c, &nc) || truong(&d, &nd)) return loi("mldsa_kiem thiếu trường");
        if (na != PK || nc > 255) return loi("mldsa_kiem: pk/ngữ cảnh sai độ dài");
        if (nd != SIG) { printf("0\n"); return 0; }
        printf("%s\n", ML(verify)(d, b, nb, c, nc, a) == 0 ? "1" : "0"); return 0;
    case 4: case 5: {
        uint8_t hat[32], skd[64], pkd[32], s[64];
        if (truong(&a, &na) || na != 32) return loi("ed25519 cần hạt 32 byte");
        memcpy(hat, a, 32); crypto_ed25519_key_pair(skd, pkd, hat);
        if (lenh == 4) { hex(pkd, 32); return 0; }
        if (truong(&b, &nb)) return loi("ed_ky thiếu thông điệp");
        crypto_ed25519_sign(s, skd, b, nb); crypto_wipe(skd, 64); hex(s, 64); return 0; }
    case 6:
        if (truong(&a, &na) || truong(&b, &nb) || truong(&c, &nc)) return loi("ed_kiem thiếu trường");
        if (na != 32 || nc != 64) return loi("ed_kiem: pk/chữ ký sai độ dài");
        printf("%s\n", crypto_ed25519_check(c, a, b, nb) == 0 ? "1" : "0"); return 0;
    case 7: {
        const uint8_t *e, *f; size_t ne, nf;
        if (truong(&a, &na) || truong(&b, &nb) || truong(&c, &nc) || truong(&d, &nd) || truong(&e, &ne) || truong(&f, &nf))
            return loi("kiem_kep thiếu trường");
        if (na != 32 || nb != PK || nd > 255 || ne != 64) return loi("kiem_kep: độ dài sai");
        int ok_ed = crypto_ed25519_check(e, a, c, nc) == 0;
        int ok_ml = nf == SIG && ML(verify)(f, c, nc, d, nd, b) == 0;
        printf("%d%d\n", ok_ed, ok_ml); return 0; }
    case 8: {
        const uint8_t *e; size_t ne; uint8_t hat[32], skd[64], pkd[32], s[64];
        if (truong(&a, &na) || truong(&b, &nb) || truong(&c, &nc) || truong(&d, &nd) || truong(&e, &ne))
            return loi("ky_kep thiếu trường");
        if (na != 32 || nb != 32 || nd > 255 || ne != 32) return loi("ky_kep: độ dài sai");
        if (ML(keypair_internal)(pk, sk, a) != 0) return loi("keypair thất bại");
        if (ky_ml(c, nc, d, nd, e, sk) != 0) return loi("ký ML-DSA thất bại");
        memcpy(hat, b, 32); crypto_ed25519_key_pair(skd, pkd, hat);
        crypto_ed25519_sign(s, skd, c, nc); crypto_wipe(skd, 64); crypto_wipe(sk, sizeof sk);
        for (int i = 0; i < 64; i++) printf("%02x", s[i]);
        hex(sig, SIG); return 0; }
    }
    return loi("mã lệnh lạ");
}

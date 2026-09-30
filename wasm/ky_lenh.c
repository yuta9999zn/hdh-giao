/* ky_lenh.c — KÝ KÉP ML-DSA-65 (PQClean, FIPS 204) + Ed25519 (Monocypher, RFC 8032), bọc thành lệnh WASI.
 *
 * Mã mật mã là mã VENDOR NGUYÊN VĂN (ben_ngoai/pqclean, ben_ngoai/monocypher) — tệp này chỉ là keo nối:
 * đọc yêu cầu từ stdin, gọi hàm, in kết quả hex. Dựng: sh wasm/dung_ky.sh → wasm/ky_lenh.wasm.
 * Chạy: wasmtime run wasm/ky_lenh.wasm  (không cấp thư mục, không mạng).
 *
 * stdin : 1 byte MÃ LỆNH, rồi các TRƯỜNG, mỗi trường = u32 little-endian độ dài + bấy nhiêu byte.
 * stdout: kết quả hex (một dòng) · lỗi: "LOI <mô tả>" và mã thoát 1.
 *   1 mldsa_khoa (ξ 32)                      → pk ‖ sk      (ML-DSA.KeyGen với ξ — FIPS 204 Alg. 1/6)
 *   2 mldsa_ky   (sk, thông_điệp, ngữ_cảnh, rnd 32) → chữ ký (rnd = 0³² ⇒ biến thể TẤT ĐỊNH của FIPS 204)
 *   3 mldsa_kiem (pk, thông_điệp, ngữ_cảnh, chữ_ký) → "1" hợp lệ / "0" không
 *   4 ed_khoa    (hạt 32)                    → pk (32)
 *   5 ed_ky      (hạt 32, thông_điệp)        → chữ ký (64)
 *   6 ed_kiem    (pk, thông_điệp, chữ_ký)    → "1" / "0"
 *   7 kiem_kep   (pk_ed, pk_ml, thông_điệp, ngữ_cảnh, ký_ed, ký_ml) → "11"/"10"/"01"/"00" (Ed25519, ML-DSA)
 *   8 ky_kep     (ξ, hạt_ed, thông_điệp, ngữ_cảnh, rnd 32) → ký_ed (64) ‖ ký_ml (3309)
 * NGẪU NHIÊN: module KHÔNG tự lấy ngẫu nhiên. ξ và rnd do bên gọi đưa vào (bên gọi lấy từ HĐH); PQClean
 * đòi randombytes() ⇒ trả đúng các byte đã nạp; đòi nhiều hơn số đã nạp ⇒ dừng máy (hỏng thì đóng).
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "api.h"
#include "monocypher-ed25519.h"

#define TRAN 1048576
static uint8_t VAO[TRAN + 64];
static size_t NVAO, VT;

static const uint8_t *NGAU; static size_t NNGAU;
int PQCLEAN_randombytes(uint8_t *out, size_t n) {
    if (n > NNGAU) { printf("LOI randombytes đòi %zu byte, chỉ nạp %zu\n", n, NNGAU); exit(1); }
    memcpy(out, NGAU, n); NGAU += n; NNGAU -= n; return 0;
}

static int truong(const uint8_t **p, size_t *n) {
    if (VT + 4 > NVAO) return -1;
    uint32_t L = (uint32_t)VAO[VT] | ((uint32_t)VAO[VT + 1] << 8) | ((uint32_t)VAO[VT + 2] << 16) | ((uint32_t)VAO[VT + 3] << 24);
    VT += 4;
    if (L > NVAO - VT) return -1;
    *p = VAO + VT; *n = L; VT += L; return 0;
}
static void hex(const uint8_t *p, size_t n) { for (size_t i = 0; i < n; i++) printf("%02x", p[i]); printf("\n"); }
static int loi(const char *m) { printf("LOI %s\n", m); return 1; }

int main(void) {
    NVAO = fread(VAO, 1, TRAN + 1, stdin);
    if (NVAO < 1 || NVAO > TRAN) return loi("đầu vào rỗng hoặc quá lớn");
    uint8_t lenh = VAO[0]; VT = 1;
    const uint8_t *a, *b, *c, *d; size_t na, nb, nc, nd;
    enum { PK = PQCLEAN_MLDSA65_CLEAN_CRYPTO_PUBLICKEYBYTES, SK = PQCLEAN_MLDSA65_CLEAN_CRYPTO_SECRETKEYBYTES,
           SIG = PQCLEAN_MLDSA65_CLEAN_CRYPTO_BYTES };
    static uint8_t pk[PK], sk[SK], sig[SIG];
    switch (lenh) {
    case 1:
        if (truong(&a, &na) || na != 32) return loi("mldsa_khoa cần ξ 32 byte");
        NGAU = a; NNGAU = 32;
        if (PQCLEAN_MLDSA65_CLEAN_crypto_sign_keypair(pk, sk) != 0) return loi("keypair thất bại");
        if (NNGAU != 0) return loi("keypair không dùng hết ξ");
        for (int i = 0; i < PK; i++) printf("%02x", pk[i]);
        hex(sk, SK); return 0;
    case 2: {
        if (truong(&a, &na) || truong(&b, &nb) || truong(&c, &nc) || truong(&d, &nd)) return loi("mldsa_ky thiếu trường");
        if (na != SK || nc > 255 || nd != 32) return loi("mldsa_ky: sk/ngữ cảnh/rnd sai độ dài");
        NGAU = d; NNGAU = 32; size_t sl = 0;
        if (PQCLEAN_MLDSA65_CLEAN_crypto_sign_signature_ctx(sig, &sl, b, nb, c, nc, a) != 0) return loi("ký thất bại");
        hex(sig, sl); return 0; }
    case 3:
        if (truong(&a, &na) || truong(&b, &nb) || truong(&c, &nc) || truong(&d, &nd)) return loi("mldsa_kiem thiếu trường");
        if (na != PK || nc > 255) return loi("mldsa_kiem: pk/ngữ cảnh sai độ dài");
        NGAU = NULL; NNGAU = 0;
        printf("%s\n", PQCLEAN_MLDSA65_CLEAN_crypto_sign_verify_ctx(d, nd, b, nb, c, nc, a) == 0 ? "1" : "0"); return 0;
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
    case 7: {   /* kiem_kep (pk_ed, pk_ml, thông_điệp, ngữ_cảnh, ký_ed, ký_ml) → hai chữ số: Ed25519, ML-DSA */
        const uint8_t *e, *f; size_t ne, nf;
        if (truong(&a, &na) || truong(&b, &nb) || truong(&c, &nc) || truong(&d, &nd) || truong(&e, &ne) || truong(&f, &nf))
            return loi("kiem_kep thiếu trường");
        if (na != 32 || nb != PK || nd > 255 || ne != 64) return loi("kiem_kep: độ dài sai");
        NGAU = NULL; NNGAU = 0;
        int ok_ed = crypto_ed25519_check(e, a, c, nc) == 0;
        int ok_ml = PQCLEAN_MLDSA65_CLEAN_crypto_sign_verify_ctx(f, nf, c, nc, d, nd, b) == 0;
        printf("%d%d\n", ok_ed, ok_ml); return 0; }
    case 8: {   /* ky_kep (ξ, hạt_ed, thông_điệp, ngữ_cảnh, rnd) → ký_ed(64) ‖ ký_ml — dựng lại khoá từ ξ/hạt */
        const uint8_t *e; size_t ne; uint8_t hat[32], skd[64], pkd[32], s[64]; size_t sl = 0;
        if (truong(&a, &na) || truong(&b, &nb) || truong(&c, &nc) || truong(&d, &nd) || truong(&e, &ne))
            return loi("ky_kep thiếu trường");
        if (na != 32 || nb != 32 || nd > 255 || ne != 32) return loi("ky_kep: độ dài sai");
        NGAU = a; NNGAU = 32;
        if (PQCLEAN_MLDSA65_CLEAN_crypto_sign_keypair(pk, sk) != 0 || NNGAU != 0) return loi("keypair thất bại");
        NGAU = e; NNGAU = 32;
        if (PQCLEAN_MLDSA65_CLEAN_crypto_sign_signature_ctx(sig, &sl, c, nc, d, nd, sk) != 0) return loi("ký ML-DSA thất bại");
        memcpy(hat, b, 32); crypto_ed25519_key_pair(skd, pkd, hat);
        crypto_ed25519_sign(s, skd, c, nc); crypto_wipe(skd, 64); memset(sk, 0, sizeof sk);
        for (int i = 0; i < 64; i++) printf("%02x", s[i]);
        hex(sig, sl); return 0; }
    }
    return loi("mã lệnh lạ");
}

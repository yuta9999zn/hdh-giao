/* bam_lenh.c — SHA-256 (FIPS 180-4) thành lệnh WASI cho trình thông dịch giao.py.
 *
 * Vì sao: SHA-256 viết bằng GIAO (lib_sha256.giao) chạy trên đường THÔNG DỊCH ~16 KB/giây, nên đường ống
 * nhận tệp chỉ băm được tệp ≤ 64 KB. Mã này chạy trên máy WASM (cùng lối argon2_lenh / ky_lenh) — không có
 * SHA-256 nào viết bằng Python ở đường chạy.
 *
 * Dựng: sh wasm/dung_bam.sh → wasm/bam_lenh.wasm (ghim ở wasm/bam.sha256).
 * Chạy: wasmtime run wasm/bam_lenh.wasm  (không cấp thư mục, không mạng)
 *   stdin : các byte cần băm (đọc theo khúc — cỡ không giới hạn bởi bộ đệm)
 *   stdout: 64 ký tự hex + "\n"   · lỗi đọc: "LOI <mô tả>" và mã thoát 1
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};

#define ROTR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

static uint32_t H[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};

static void khoi(const uint8_t *p) {
    uint32_t w[64], a, b, c, d, e, f, g, h, t1, t2;
    for (int i = 0; i < 16; i++)
        w[i] = ((uint32_t)p[4 * i] << 24) | ((uint32_t)p[4 * i + 1] << 16) | ((uint32_t)p[4 * i + 2] << 8) | p[4 * i + 3];
    for (int i = 16; i < 64; i++) {
        uint32_t s0 = ROTR(w[i - 15], 7) ^ ROTR(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = ROTR(w[i - 2], 17) ^ ROTR(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    a = H[0]; b = H[1]; c = H[2]; d = H[3]; e = H[4]; f = H[5]; g = H[6]; h = H[7];
    for (int i = 0; i < 64; i++) {
        t1 = h + (ROTR(e, 6) ^ ROTR(e, 11) ^ ROTR(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i];
        t2 = (ROTR(a, 2) ^ ROTR(a, 13) ^ ROTR(a, 22)) + ((a & b) ^ (a & c) ^ (b & c));
        h = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
    }
    H[0] += a; H[1] += b; H[2] += c; H[3] += d; H[4] += e; H[5] += f; H[6] += g; H[7] += h;
}

static uint8_t BUF[1 << 16];

int main(void) {
    uint8_t du[64];                /* phần chưa đủ một khối 64 byte */
    size_t ndu = 0, n;
    uint64_t tong = 0;             /* tổng số byte (độ dài gốc) */
    while ((n = fread(BUF, 1, sizeof BUF, stdin)) > 0) {
        size_t i = 0;
        tong += n;
        if (ndu) {                 /* lấp nốt khối dở từ lần đọc trước */
            while (ndu < 64 && i < n) du[ndu++] = BUF[i++];
            if (ndu == 64) { khoi(du); ndu = 0; }
        }
        for (; i + 64 <= n; i += 64) khoi(BUF + i);
        while (i < n) du[ndu++] = BUF[i++];
    }
    if (ferror(stdin)) { printf("LOI đọc stdin hỏng\n"); return 1; }
    /* đệm: 0x80, các 0, rồi độ dài bit big-endian 8 byte */
    du[ndu++] = 0x80;
    if (ndu > 56) { while (ndu < 64) du[ndu++] = 0; khoi(du); ndu = 0; }
    while (ndu < 56) du[ndu++] = 0;
    uint64_t bit = tong * 8;
    for (int i = 0; i < 8; i++) du[56 + i] = (uint8_t)(bit >> (56 - 8 * i));
    khoi(du);
    for (int i = 0; i < 8; i++) printf("%08x", H[i]);
    printf("\n");
    return 0;
}

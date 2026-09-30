/* argon2_lenh.c — CÙNG keo nối argon2_gvm.c, bọc thành lệnh WASI cho TRÌNH THÔNG DỊCH giao.py.
 *
 * Dựng thành wasm/argon2_lenh.wasm. giao.py gọi:  wasmtime run wasm/argon2_lenh.wasm  (không cấp thư mục)
 *   stdin : 9 số u32 little-endian (kieu, lpwd, lsalt, lsec, lad, t, m, p, ltag) + các byte đầu vào
 *   stdout: thẻ băm dạng hex (một dòng)       · lỗi: "LOI <mã> <thông điệp>" và mã thoát 1
 * Nhờ vậy trình thông dịch và GVM-64 chạy ĐÚNG MỘT mã Argon2 (tham chiếu C), không có bản Python nào.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "argon2.h"

int a2_dat(int i, int b);
int a2_lay(int i);
int a2_chay(int kieu, int lpwd, int lsalt, int lsec, int lad, int t, int m, int p, int ltag);

static uint8_t BUF[65536 + 64];

int main(void) {
    size_t n = fread(BUF, 1, sizeof BUF, stdin);
    if (n < 36) { printf("LOI -1001 thiếu đầu đề\n"); return 1; }
    int h[9];
    for (int k = 0; k < 9; k++)
        h[k] = (int)((uint32_t)BUF[4 * k] | ((uint32_t)BUF[4 * k + 1] << 8) | ((uint32_t)BUF[4 * k + 2] << 16) | ((uint32_t)BUF[4 * k + 3] << 24));
    long long can = (long long)h[1] + h[2] + h[3] + h[4];
    if (h[1] < 0 || h[2] < 0 || h[3] < 0 || h[4] < 0 || can > 65536 || (long long)n != 36 + can) {
        printf("LOI -1002 độ dài đầu vào không khớp đầu đề\n"); return 1;
    }
    for (long long i = 0; i < can; i++) a2_dat((int)i, BUF[36 + i]);
    int r = a2_chay(h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7], h[8]);
    memset(BUF, 0, sizeof BUF);
    if (r != 0) { printf("LOI %d %s\n", r, r == -1000 ? "vượt trần tham số" : argon2_error_message(r)); return 1; }
    for (int i = 0; i < h[8]; i++) printf("%02x", a2_lay(i));
    printf("\n");
    return 0;
}

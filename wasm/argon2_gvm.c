/* argon2_gvm.c — keo nối Argon2 THAM CHIẾU (ben_ngoai/argon2, không sửa) cho GVM-64.
 *
 * Dựng thành wasm/argon2.wasm (wasi-sdk, -mexec-model=reactor). GVM-64 nạp bằng
 *     wasmtime run --preload argon2=wasm/argon2.wasm wasm/gvm64.wasm
 * Hai module có bộ nhớ RIÊNG: GVM-64 chép đầu vào vào đây TỪNG BYTE (a2_dat), gọi a2_chay, rồi đọc
 * thẻ băm ra (a2_lay). Module này không cần hàm WASI nào (không tệp, không mạng, không đồng hồ).
 *
 * Bố cục VAO: mật khẩu | muối | khoá bí mật | dữ liệu kèm (liền nhau, theo độ dài truyền cho a2_chay).
 * Trần (chống bản ghi khai tham số vô lý làm treo máy): m ≤ 1 GiB, t ≤ 64, p ≤ 16, thẻ 4..1024 byte.
 */
#include <stdint.h>
#include <string.h>
#include "argon2.h"

#define TRAN_VAO 65536
#define TRAN_THE 1024
static uint8_t VAO[TRAN_VAO];
static uint8_t THE[TRAN_THE];

__attribute__((export_name("a2_dat"))) int a2_dat(int i, int b) {
    if (i < 0 || i >= TRAN_VAO || b < 0 || b > 255) return -1;
    VAO[i] = (uint8_t)b; return 0;
}

__attribute__((export_name("a2_lay"))) int a2_lay(int i) {
    if (i < 0 || i >= TRAN_THE) return -1;
    return THE[i];
}

/* kieu: 0 = Argon2d · 1 = Argon2i · 2 = Argon2id. Trả 0 (ARGON2_OK) hoặc mã lỗi âm của argon2.h;
 * -1000 = vượt trần của keo nối. */
__attribute__((export_name("a2_chay"))) int a2_chay(int kieu, int lpwd, int lsalt, int lsec, int lad,
                                                    int t, int m, int p, int ltag) {
    if (lpwd < 0 || lsalt < 0 || lsec < 0 || lad < 0) return -1000;
    if ((long long)lpwd + lsalt + lsec + lad > TRAN_VAO) return -1000;
    if (ltag < 4 || ltag > TRAN_THE || t < 1 || t > 64 || p < 1 || p > 16 || m < 8 || m > (1 << 20)) return -1000;
    if (kieu < 0 || kieu > 2) return -1000;
    argon2_context ctx;
    memset(&ctx, 0, sizeof ctx);
    uint8_t *q = VAO;
    ctx.out = THE; ctx.outlen = (uint32_t)ltag;
    ctx.pwd = q; ctx.pwdlen = (uint32_t)lpwd; q += lpwd;
    ctx.salt = q; ctx.saltlen = (uint32_t)lsalt; q += lsalt;
    ctx.secret = lsec ? q : NULL; ctx.secretlen = (uint32_t)lsec; q += lsec;
    ctx.ad = lad ? q : NULL; ctx.adlen = (uint32_t)lad;
    ctx.t_cost = (uint32_t)t; ctx.m_cost = (uint32_t)m;
    ctx.lanes = (uint32_t)p; ctx.threads = (uint32_t)p;
    ctx.version = ARGON2_VERSION_13;
    ctx.allocate_cbk = NULL; ctx.free_cbk = NULL;
    ctx.flags = ARGON2_DEFAULT_FLAGS;
    argon2_type ty = kieu == 0 ? Argon2_d : (kieu == 1 ? Argon2_i : Argon2_id);
    int r = argon2_ctx(&ctx, ty);
    memset(VAO, 0, sizeof VAO);            /* không để mật khẩu nằm lại trong bộ nhớ module */
    return r;
}

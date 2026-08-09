/* ============================================================
 * giao_vpi.c — ĐIỂM HẸN VPI: nhân HĐH-GIAO thành HÀM HỆ THỐNG trong chính bộ mô phỏng.
 * ------------------------------------------------------------
 * Trước đây cổng logic và nhân hẹn nhau qua TỆP (trap_req.txt / trap_res.txt): testbench phải
 * `#200` rồi mở tệp dò lại — mỗi lời xin ngốn hàng nghìn chu kỳ mô phỏng chỉ để ĐỢI.
 * Nay dùng VPI: `$giao_trap(...)` là một lời gọi C **chặn ngay tại thời điểm mô phỏng ấy**.
 *   1. đọc đối từ chân trap; đối nào mang THẺ (bit30) thì DUYỆT THẲNG `dut.ram[]` qua VPI
 *      để lấy từng mã ký tự — không cần Verilog gói hộ nữa
 *   2. gửi qua socket tới tiến trình Python đang chạy nhân GIAO thật, chờ trả lời
 *   3. kết quả là chuỗi thì CẤP PHÁT vào heap của chính CPU (ram[250] = con trỏ heap,
 *      ô cons [mã, đuôi], MỌI con trỏ mang thẻ) rồi trả con trỏ; là số thì trả thẳng
 * Không một chu kỳ mô phỏng nào bị đốt để đợi.
 *
 * Dựng:  gcc -shared -o giao_vpi.vpi giao_vpi.c -I<iverilog>/include/iverilog \
 *              -L<iverilog>/lib -lvpi -lws2_32
 * Chạy:  vvp -M. -mgiao_vpi gvm_vpi.vvp        (cổng lấy từ biến môi trường GIAO_CONG)
 * ============================================================ */
#include <vpi_user.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#define TỐI_ĐA_KÝ_TỰ 4096
#define ĐỆM          (1 << 20)

static SOCKET sk = INVALID_SOCKET;
static char   đệm[ĐỆM];
static int    đệm_dài = 0, đệm_vị = 0;
static vpiHandle ram = NULL;
static long   số_lời_xin = 0;

/* ── điểm hẹn: socket tới nhân GIAO ── */
static int nối(void) {
    if (sk != INVALID_SOCKET) return 1;
    WSADATA w;
    static int đã_khởi = 0;
    if (!đã_khởi) { if (WSAStartup(MAKEWORD(2, 2), &w) != 0) return 0; đã_khởi = 1; }

    const char *c = getenv("GIAO_CONG");
    if (!c) { vpi_printf("[giao_vpi] thiếu biến môi trường GIAO_CONG\n"); return 0; }

    struct sockaddr_in đ;
    memset(&đ, 0, sizeof đ);
    đ.sin_family = AF_INET;
    đ.sin_port   = htons((unsigned short)atoi(c));
    đ.sin_addr.s_addr = inet_addr("127.0.0.1");

    sk = socket(AF_INET, SOCK_STREAM, 0);
    if (sk == INVALID_SOCKET) return 0;
    int một = 1;
    setsockopt(sk, IPPROTO_TCP, TCP_NODELAY, (const char *)&một, sizeof một);
    if (connect(sk, (struct sockaddr *)&đ, sizeof đ) != 0) {
        vpi_printf("[giao_vpi] không nối được tới nhân ở cổng %s\n", c);
        closesocket(sk); sk = INVALID_SOCKET; return 0;
    }
    return 1;
}

static void gửi(const char *s, int n) {
    int i = 0;
    while (i < n) { int k = send(sk, s + i, n - i, 0); if (k <= 0) return; i += k; }
}

/* đọc một DÒNG (tới '\n') từ socket */
static int đọc_dòng(char *ra, int max) {
    int n = 0;
    for (;;) {
        if (đệm_vị >= đệm_dài) {
            đệm_dài = recv(sk, đệm, ĐỆM, 0); đệm_vị = 0;
            if (đệm_dài <= 0) return -1;
        }
        char c = đệm[đệm_vị++];
        if (c == '\n') { ra[n] = 0; return n; }
        if (n < max - 1) ra[n++] = c;
    }
}

/* ── đọc/ghi RAM của CPU qua VPI ── */
static int bảo_đảm_ram(void) {
    if (ram) return 1;
    ram = vpi_handle_by_name("cosim_vpi_tb.dut.ram", NULL);
    if (!ram) vpi_printf("[giao_vpi] không thấy cosim_vpi_tb.dut.ram\n");
    return ram != NULL;
}
static unsigned ô_đọc(unsigned i) {
    s_vpi_value v; v.format = vpiIntVal;
    vpiHandle w = vpi_handle_by_index(ram, (PLI_INT32)i);
    if (!w) return 0;
    vpi_get_value(w, &v);
    return (unsigned)v.value.integer;
}
static void ô_ghi(unsigned i, unsigned x) {
    s_vpi_value v; v.format = vpiIntVal; v.value.integer = (PLI_INT32)x;
    vpiHandle w = vpi_handle_by_index(ram, (PLI_INT32)i);
    if (w) vpi_put_value(w, &v, NULL, vpiNoDelay);
}

/* con trỏ chuỗi (danh sách cons) → mảng mã ký tự */
static int chuỗi_ra(unsigned p, unsigned *mã, int max) {
    int k = 0; unsigned a = p & 0x3FFFFFFFu;
    while (a && k < max) { mã[k++] = ô_đọc(a) & 0x1FFFFFu; a = ô_đọc(a + 1) & 0x3FFFFFFFu; }
    return k;
}
/* mảng mã ký tự → cấp phát danh sách cons vào HEAP CỦA CPU, trả con trỏ CÓ THẺ */
static unsigned chuỗi_vào(unsigned *mã, int n) {
    unsigned hp = ô_đọc(250); if (hp < 300) hp = 300;
    unsigned con = 0;
    for (int i = n - 1; i >= 0; i--) {
        ô_ghi(hp, mã[i]); ô_ghi(hp + 1, con);
        con = hp | 0x40000000u;              /* MỌI con trỏ mang THẺ — kể cả đuôi */
        hp += 2;
    }
    ô_ghi(250, hp);
    return con;
}

/* ── $giao_trap(số, nargs, đ0, đ1, đ2) → kết quả ── */
static PLI_INT32 trap_cỡ(PLI_BYTE8 *u) { (void)u; return 32; }

static PLI_INT32 trap_gọi(PLI_BYTE8 *u) {
    (void)u;
    vpiHandle tf = vpi_handle(vpiSysTfCall, NULL);
    vpiHandle it = vpi_iterate(vpiArgument, tf), h;
    PLI_INT32 đ[5] = {0, 0, 0, 0, 0};
    int n = 0;
    while ((h = vpi_scan(it)) != NULL) {
        if (n < 5) { s_vpi_value v; v.format = vpiIntVal; vpi_get_value(h, &v); đ[n] = v.value.integer; }
        n++;
    }

    s_vpi_value kq; kq.format = vpiIntVal; kq.value.integer = -1;
    if (!nối() || !bảo_đảm_ram()) { vpi_put_value(tf, &kq, NULL, vpiNoDelay); return 0; }

    unsigned số = (unsigned)đ[0] & 0xFFu, nargs = (unsigned)đ[1];
    if (nargs > 3) nargs = 3;

    /* gói lời xin: "số nargs [là_chuỗi dài mã…]×nargs" */
    static char gói[TỐI_ĐA_KÝ_TỰ * 8 + 256];
    static unsigned mã[TỐI_ĐA_KÝ_TỰ];
    int p = snprintf(gói, sizeof gói, "%u %u", số, nargs);
    for (unsigned j = 0; j < nargs; j++) {
        unsigned v = (unsigned)đ[2 + j];
        int k = (v & 0x40000000u) ? chuỗi_ra(v, mã, TỐI_ĐA_KÝ_TỰ) : 0;
        if (k > 0) {
            p += snprintf(gói + p, sizeof gói - p, " 1 %d", k);
            for (int i = 0; i < k; i++) p += snprintf(gói + p, sizeof gói - p, " %u", mã[i]);
        } else {
            p += snprintf(gói + p, sizeof gói - p, " 0 1 %u", v);   /* SỐ */
        }
    }
    p += snprintf(gói + p, sizeof gói - p, "\n");
    gửi(gói, p);
    số_lời_xin++;

    /* chờ nhân — CHẶN NGAY TẠI THỜI ĐIỂM MÔ PHỎNG NÀY, không đốt chu kỳ nào */
    static char trả[TỐI_ĐA_KÝ_TỰ * 8 + 64];
    if (đọc_dòng(trả, sizeof trả) < 0) { vpi_put_value(tf, &kq, NULL, vpiNoDelay); return 0; }

    char *t = trả;
    long loại = strtol(t, &t, 10), dài = strtol(t, &t, 10);
    if (loại == 1) {                                  /* CHUỖI → cấp vào heap của CPU */
        if (dài > TỐI_ĐA_KÝ_TỰ) dài = TỐI_ĐA_KÝ_TỰ;
        for (long i = 0; i < dài; i++) mã[i] = (unsigned)strtoul(t, &t, 10);
        kq.value.integer = (PLI_INT32)chuỗi_vào(mã, (int)dài);
    } else {
        kq.value.integer = (PLI_INT32)strtoul(t, &t, 10);
    }
    vpi_put_value(tf, &kq, NULL, vpiNoDelay);
    return 0;
}

/* ── $giao_đếm() → số lời xin đã phục vụ (để hậu kiểm) ── */
static PLI_INT32 đếm_cỡ(PLI_BYTE8 *u) { (void)u; return 32; }
static PLI_INT32 đếm_gọi(PLI_BYTE8 *u) {
    (void)u;
    vpiHandle tf = vpi_handle(vpiSysTfCall, NULL);
    s_vpi_value v; v.format = vpiIntVal; v.value.integer = (PLI_INT32)số_lời_xin;
    vpi_put_value(tf, &v, NULL, vpiNoDelay);
    return 0;
}

/* ── $giao_byte_ra(b): đẩy MỘT byte tới máy chủ (dùng cho cầu UART của bo) ── */
static PLI_INT32 byte_ra_gọi(PLI_BYTE8 *u) {
    (void)u;
    vpiHandle tf = vpi_handle(vpiSysTfCall, NULL);
    vpiHandle it = vpi_iterate(vpiArgument, tf), h;
    PLI_INT32 b = 0;
    if ((h = vpi_scan(it)) != NULL) {
        s_vpi_value v; v.format = vpiIntVal; vpi_get_value(h, &v); b = v.value.integer;
        vpi_free_object(it);
    }
    if (nối()) { char c = (char)(b & 0xFF); gửi(&c, 1); }
    return 0;
}

/* ── $giao_byte_vao(): lấy MỘT byte máy chủ gửi xuống, hoặc −1 nếu chưa có (KHÔNG chặn) ── */
static PLI_INT32 byte_vào_cỡ(PLI_BYTE8 *u) { (void)u; return 32; }
static PLI_INT32 byte_vào_gọi(PLI_BYTE8 *u) {
    (void)u;
    vpiHandle tf = vpi_handle(vpiSysTfCall, NULL);
    s_vpi_value v; v.format = vpiIntVal; v.value.integer = -1;
    if (nối()) {
        if (đệm_vị >= đệm_dài) {
            unsigned long sẵn = 0;
            if (ioctlsocket(sk, FIONREAD, &sẵn) == 0 && sẵn > 0) {
                đệm_dài = recv(sk, đệm, ĐỆM, 0); đệm_vị = 0;
                if (đệm_dài <= 0) đệm_dài = 0;
            }
        }
        if (đệm_vị < đệm_dài) v.value.integer = (unsigned char)đệm[đệm_vị++];
    }
    vpi_put_value(tf, &v, NULL, vpiNoDelay);
    return 0;
}

static void đăng_ký(void) {
    s_vpi_systf_data d;
    memset(&d, 0, sizeof d);
    d.type = vpiSysFunc; d.sysfunctype = vpiSysFuncSized;
    d.tfname = "$giao_trap"; d.calltf = trap_gọi; d.sizetf = trap_cỡ;
    vpi_register_systf(&d);

    memset(&d, 0, sizeof d);
    d.type = vpiSysFunc; d.sysfunctype = vpiSysFuncSized;
    d.tfname = "$giao_dem"; d.calltf = đếm_gọi; d.sizetf = đếm_cỡ;
    vpi_register_systf(&d);

    memset(&d, 0, sizeof d);
    d.type = vpiSysTask; d.tfname = "$giao_byte_ra"; d.calltf = byte_ra_gọi;
    vpi_register_systf(&d);

    memset(&d, 0, sizeof d);
    d.type = vpiSysFunc; d.sysfunctype = vpiSysFuncSized;
    d.tfname = "$giao_byte_vao"; d.calltf = byte_vào_gọi; d.sizetf = byte_vào_cỡ;
    vpi_register_systf(&d);
}

void (*vlog_startup_routines[])(void) = { đăng_ký, 0 };

# ben_ngoai — mã bên ngoài, VENDOR NGUYÊN VĂN (không sửa)

GIAO không tự viết mật mã. Mọi thuật toán mật mã đến từ các nguồn dưới đây, chép nguyên văn, dựng thành
WASM bằng wasi-sdk và GHIM SHA-256 (bản dựng tái lập được).

| thư mục | nguồn | phiên bản | giấy phép | dùng cho |
|---|---|---|---|---|
| `argon2/` | https://github.com/P-H-C/phc-winner-argon2 | `f57e61e` | CC0 / Apache-2.0 | băm mật khẩu `$argon2id$` (`wasm/argon2.wasm`) |
| `pqclean/mldsa65`, `pqclean/common` (fips202, randombytes.h) | https://github.com/PQClean/PQClean | `0586a82` (bản cuối, repo **đã lưu trữ** 2026-08-04) | CC0 / public domain | ML-DSA-65 (FIPS 204) — ký kép sổ niêm phong |
| `monocypher/` (monocypher + optional/monocypher-ed25519) | https://github.com/LoupVaillant/Monocypher | `4.0.3` | BSD-2 / CC0 | Ed25519 (RFC 8032) — ký kép |
| `vector/` | NIST ACVP-Server `975de31` (ML-DSA keyGen/sigGen/sigVer, EDDSA sigVer); RFC 8032 §7.1 | — | công bố công khai | vector kiểm chính thức (`kiem_ky_kep.py`) |

Keo nối DUY NHẤT do dự án viết: `wasm/argon2_gvm.c`, `wasm/argon2_lenh.c`, `wasm/ky_lenh.c` (đọc/ghi byte,
gọi hàm thư viện). PQClean khuyên chuyển sang **mldsa-native** (PQ Code Package) — việc nên làm tiếp.

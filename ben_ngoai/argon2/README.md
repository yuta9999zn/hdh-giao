# Argon2 — mã tham chiếu (ĐƯỢC VENDOR NGUYÊN VĂN, không sửa)

Nguồn: https://github.com/P-H-C/phc-winner-argon2 @ `f57e61e19229e23c4445b85494dbf7c07de721cb`
Giấy phép: CC0 1.0 hoặc Apache 2.0 (tuỳ chọn) — xem `LICENSE`.

Chỉ chép các tệp cần cho bản tham chiếu KHÔNG luồng (`ref.c`, không `opt.c`/SSE, không `thread.c`):
`include/argon2.h`, `src/{argon2.c,core.c,core.h,encoding.c,encoding.h,ref.c,thread.h}`,
`src/blake2/{blake2.h,blake2b.c,blake2-impl.h,blamka-round-ref.h}`.

GIAO KHÔNG tự viết Argon2: `wasm/dung_argon2.sh` biên dịch đúng các tệp này bằng wasi-sdk thành
`wasm/argon2.wasm` (GVM-64 nạp bằng `--preload`) và `wasm/argon2_lenh.wasm` (trình thông dịch gọi qua
wasmtime). `RFC9106_vectors.txt` là ba vector kiểm của RFC 9106 §5, dùng trong `kiem_argon2.giao`.

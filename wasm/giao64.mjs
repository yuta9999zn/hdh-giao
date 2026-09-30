// ============================================================
// VỎ WASI DỰ PHÒNG cho GVM-64 (khi máy chưa có wasmtime/wasmer).
// gvm64.wasm chỉ import 6 hàm WASI chuẩn (fd_read/fd_write/args/clock/proc_exit) — KHÔNG có hàm
// riêng nào của Node. Vỏ này chỉ nối stdin = tệp chương trình, stdout/stderr = của tiến trình.
// Nên chạy dưới chế độ PHÂN QUYỀN của Node (không ghi tệp, không tiến trình con, chỉ đọc 2 tệp):
//   node --permission --allow-fs-read=<GIAO>/wasm/gvm64.wasm --allow-fs-read=<tệp.g64> --allow-wasi \
//        wasm/giao64.mjs <tệp.g64> [--bước N] [--trần-ds N] [--cho-giờ]
// Vỏ ưu tiên (sandbox chặt hơn, không cần Node):
//   wasmtime run wasm/gvm64.wasm -- [cờ…] < tệp.g64
// ============================================================
import { readFileSync, openSync } from "node:fs";
import { WASI } from "node:wasi";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const [tệp, ...cờ] = process.argv.slice(2);
if (!tệp) { process.stderr.write("Dùng: node wasm/giao64.mjs <tệp.g64> [--bước N] [--trần-ds N] [--cho-giờ]\n"); process.exit(2); }
const wasi = new WASI({ version: "preview1", args: ["gvm64", ...cờ], env: {}, preopens: {},
                        stdin: openSync(tệp, "r"), stdout: 1, stderr: 2, returnOnExit: true });
const { instance } = await WebAssembly.instantiate(readFileSync(join(here, "gvm64.wasm")), wasi.getImportObject());
process.exitCode = wasi.start(instance) ?? 0;

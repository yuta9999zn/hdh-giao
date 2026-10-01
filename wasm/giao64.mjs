// ============================================================
// VỎ WASI DỰ PHÒNG cho GVM-64 (khi máy chưa có wasmtime/wasmer).
// gvm64.wasm chỉ import 7 hàm WASI chuẩn (fd_read/fd_write/args/clock/random/proc_exit) + module argon2.wasm — KHÔNG có hàm
// riêng nào của Node. Vỏ này chỉ nối stdin = tệp chương trình, stdout/stderr = của tiến trình.
// Nên chạy dưới chế độ PHÂN QUYỀN của Node (không ghi tệp, không tiến trình con, chỉ đọc 2 tệp):
//   node --permission --allow-fs-read=<GIAO>/wasm/gvm64.wasm --allow-fs-read=<GIAO>/wasm/argon2.wasm --allow-fs-read=<tệp.g64> --allow-wasi \
//        wasm/giao64.mjs <tệp.g64> [--bước N] [--trần-ds N] [--cho-giờ]
// Vỏ ưu tiên (sandbox chặt hơn, không cần Node):
//   wasmtime run --preload argon2=wasm/argon2.wasm wasm/gvm64.wasm -- [cờ…] < tệp.g64
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
// Argon2 tham chiếu (module riêng, không import gì) — tương đương `--preload argon2=…` của wasmtime.
// Kiểm GHIM SHA-256 (argon2.sha256) trước khi nạp — lệch thì từ chối.
const a2byte = readFileSync(join(here, "argon2.wasm"));
const ghim = readFileSync(join(here, "argon2.sha256"), "utf8").split(/\r?\n/).find(d => d.endsWith(" wasm/argon2.wasm"));
const { createHash } = await import("node:crypto");
const thật = createHash("sha256").update(a2byte).digest("hex");
if (!ghim || ghim.split(/\s+/)[0] !== thật) { process.stderr.write(`argon2.wasm: SHA-256 ${thật} KHÁC ghim — từ chối nạp\n`); process.exit(3); }
const a2 = (await WebAssembly.instantiate(a2byte, {})).instance;
if (a2.exports._initialize) a2.exports._initialize();
const kyByte = readFileSync(join(here, "ky.wasm"));
const ghimKy = readFileSync(join(here, "ky.sha256"), "utf8").split(/\r?\n/).find(d => d.endsWith(" wasm/ky.wasm"));
if (!ghimKy || ghimKy.split(/\s+/)[0] !== createHash("sha256").update(kyByte).digest("hex")) { process.stderr.write("ky.wasm: SHA-256 KHÁC ghim — từ chối nạp\n"); process.exit(3); }
const ky = (await WebAssembly.instantiate(kyByte, {})).instance;
if (ky.exports._initialize) ky.exports._initialize();
const imports = { ...wasi.getImportObject(), argon2: a2.exports, ky: ky.exports };
const { instance } = await WebAssembly.instantiate(readFileSync(join(here, "gvm64.wasm")), imports);
process.exitCode = wasi.start(instance) ?? 0;

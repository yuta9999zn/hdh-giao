// Đo tầng 3 — WASM GVM — cùng bytecode trong wasm/bench.json. Chạy: node wasm/bench.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
const here = dirname(fileURLToPath(import.meta.url));
const { words, bit, N } = JSON.parse(readFileSync(join(here, "bench.json"), "utf8"));
const wasmBytes = readFileSync(join(here, "gvm.wasm"));

let last = null;
const env = {
  roi: (st, val) => { last = val; },
  roiChar: () => {}, roiNl: () => {}, roiSo: () => {}, roiDsHet: () => {},
  loi: (op) => { throw new Error("opcode " + op); },
  abort: () => { throw new Error("abort"); },
};
const { instance } = await WebAssembly.instantiate(wasmBytes, { env });
const { nap, chay } = instance.exports;
words.forEach((w, i) => nap(i, w));
const t0 = process.hrtime.bigint();
chay(bit | 0);
const sec = Number(process.hrtime.bigint() - t0) / 1e9;
console.log(`  3) WASM GVM (Node ${process.version}) : ${sec.toFixed(3)}s   — vòng lặp ${N.toLocaleString()} lần, s in ra = ${last}`);

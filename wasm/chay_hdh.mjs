// CHẠY + ĐO nhân HĐH-GIAO trên WASM — cùng bytecode đã khớp GVM-Python (conformance).
// Chạy:  node wasm/chay_hdh.mjs        (sau: python chay_hdh_may.py để sinh wasm/hdh.json)
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const prog = JSON.parse(readFileSync(join(here, "hdh.json"), "utf8"));
const wasmBytes = readFileSync(join(here, "gvm.wasm"));
const mod = await WebAssembly.compile(wasmBytes);

// — chạy MỘT lần in ra (HĐH-GIAO boot trên WASM, output qua năng-lực host) —
let buf = "", dòng = [];
const envIn = {
  roi: (st, val) => dòng.push(st === 0 ? "ẩn" : String((val | 0))),
  roiChar: (c) => { buf += String.fromCodePoint(c >>> 0); },
  roiNl: () => { dòng.push(buf); buf = ""; },
  roiSo: () => {}, roiDsHet: () => {}, loi: () => {},
  abort: (m, f, l, c) => { throw new Error(`wasm abort @ ${l}:${c}`); },
};
let inst = await WebAssembly.instantiate(mod, { env: envIn });
prog.words.forEach((w, i) => inst.exports.nap(i, w));
inst.exports.chay(prog.bit | 0);
console.log("=== HĐH-GIAO BOOT trên WebAssembly (memory-safe, KHÔNG qua C) ===");
for (const l of dòng) console.log(l);

// — ĐO: chạy lại nhiều lần, năng-lực rỗng (chỉ đo lõi máy) —
const envNull = { roi: () => {}, roiChar: () => {}, roiNl: () => {}, roiSo: () => {},
                  roiDsHet: () => {}, loi: () => {}, abort: () => {} };
const N = 200;
let best = Infinity;
for (let r = 0; r < 5; r++) {
  const i2 = await WebAssembly.instantiate(mod, { env: envNull });
  prog.words.forEach((w, i) => i2.exports.nap(i, w));
  const t0 = performance.now();
  for (let k = 0; k < N; k++) i2.exports.chay(prog.bit | 0);
  const dt = (performance.now() - t0) / N;
  if (dt < best) best = dt;
}
console.log(`\n=== ĐO WASM ===`);
console.log(`   nhân HĐH-GIAO trên WASM:  ${best.toFixed(3)} ms / lần boot  (${prog.words.length} từ-lệnh)`);
console.log(`   → cùng bytecode chạy ${(202.7 / best).toFixed(0)}× nhanh hơn GVM-Python (CPU mô phỏng bằng Python).`);
console.log(`   Lưu ý: nhân này NẶNG HEAP (bản/chuỗi) nên WASM ~ngang tốc-độ thông dịch (≈2 ms);`);
console.log(`   tăng tốc lớn (~430×) là ở phần LÕI SỐ thuần. Giá trị ở đây: CÙNG bytecode chạy`);
console.log(`   native, memory-safe (sandbox WASM), KHÔNG qua C — đường triển khai thật của HĐH-GIAO.`);

// KIỂM CHỨNG WASM GVM — chạy mọi ca trong cases.json trên wasm, so KHỚP với GVM Python.
// Chạy:  node wasm/kiem.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const cases = JSON.parse(readFileSync(join(here, "cases.json"), "utf8"));
const wasmBytes = readFileSync(join(here, "gvm.wasm"));
const mod = await WebAssembly.compile(wasmBytes);

async function chạyMáy(words, bit) {
  const out = [];
  let buf = "", ds = [];
  const env = {
    roi: (st, val) => out.push(["ô", st, val]),
    roiChar: (c) => { buf += String.fromCodePoint(c >>> 0); },
    roiNl: () => { out.push(["chuỗi", buf]); buf = ""; },
    roiSo: (v) => ds.push(v | 0),
    roiDsHet: () => { out.push(["ds", ds]); ds = []; },
    loi: (op) => out.push(["LỖI_OPCODE", op]),
    abort: (m, f, l, c) => { throw new Error(`wasm abort @ ${l}:${c}`); },
  };
  const inst = await WebAssembly.instantiate(mod, { env });
  const { nap, chay } = inst.exports;
  words.forEach((w, i) => nap(i, w));
  chay(bit);
  return out;
}

const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

console.log("=".repeat(64));
console.log(`KIỂM CHỨNG WASM GVM (Node ${process.version}) — so khớp GVM Python`);
console.log("=".repeat(64));
let pass = 0, fail = 0;
for (const c of cases) {
  const got = await chạyMáy(c.words, c.bit);
  const ok = eq(got, c.expect);
  console.log(`  ${ok ? "✓" : "✗"} ${c.tên.padEnd(26)} ${c.words.length} từ-lệnh · ${c.bit}-bit · ${c.expect.length} output`);
  if (ok) pass++; else { fail++; console.log(`      Python: ${JSON.stringify(c.expect).slice(0,160)}`); console.log(`      WASM  : ${JSON.stringify(got).slice(0,160)}`); }
}
console.log("=".repeat(64));
console.log(`KẾT QUẢ: ${pass}/${pass + fail} ca KHỚP wasm ⟷ Python`);
console.log("=".repeat(64));
process.exit(fail ? 1 : 0);

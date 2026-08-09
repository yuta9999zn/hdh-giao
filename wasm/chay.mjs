// HARNESS Node — nạp gvm.wasm, cấp năng lực `roi`, chạy bytecode, đối chiếu 4 tầng kia.
// Chạy:  node wasm/chay.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const prog = JSON.parse(readFileSync(join(here, "program.json"), "utf8"));
const wasmBytes = readFileSync(join(here, "gvm.wasm"));

const out = [];
let buf = "", ds = [];
// các hàm RỌI = NĂNG LỰC do HOST cấp (đúng object-capability của WASM ⟂ của GIAO)
const { instance } = await WebAssembly.instantiate(wasmBytes, {
  env: {
    roi: (st, val, gam) => out.push({ st, val, gam }),
    roiChar: (c) => { buf += String.fromCodePoint(c >>> 0); },
    roiNl: () => { console.log("   " + buf); buf = ""; },
    roiSo: (v) => ds.push(v | 0),
    roiDsHet: () => { ds = []; },
    loi: (op) => console.log("   [opcode chưa hỗ trợ] " + op),
    abort: (msg, file, line, col) => { throw new Error(`wasm abort @ ${line}:${col}`); },
  },
});
const { nap, chay } = instance.exports;

prog.words.forEach((w, i) => nap(i, w));     // nạp bytecode (do giaoc.giao sinh)
chay(prog.bit | 0);                           // chạy trên máy trit/γ trong WASM (độ rộng từ)

const TÊN = { 0: "ẩn", 1: "sáng", 2: "tối" };
console.log(`WASM GVM (AssemblyScript → wasm, chạy trong Node ${process.version})`);
console.log(`${prog.words.length} từ-lệnh từ ${prog.nguồn}\n`);
for (const r of out) {
  const g = (r.gam >= 0 ? "+" : "") + r.gam.toFixed(2);
  console.log(`   ${TÊN[r.st]}=${r.val}\tγ=${g}`);
}

// Đối chiếu với 3 tầng kia (thông dịch / GVM mềm / Verilog): vòng hội tụ 18→36
const MONG = [[2, 18], [1, 27], [1, 32], [1, 34], [1, 35], [1, 36], [1, 36]];
const khớp = out.length === MONG.length &&
  out.every((r, i) => r.st === MONG[i][0] && r.val === MONG[i][1]);
console.log(khớp
  ? "\n✓ KHỚP các substrate khác: vòng hội tụ CDFL tối=18 → sáng=36 (γ −0.03 → +0.95)"
  : "\n✗ LỆCH so với tham chiếu");
process.exit(khớp ? 0 : 1);

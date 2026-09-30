// ============================================================
// GVM-64 — MÁY TÍNH TOÁN CỦA GIAO (substrate thứ 6: WebAssembly, AssemblyScript → gvm64.wasm)
// ------------------------------------------------------------
// Chạy chương trình GIAO do giaoc64 biên dịch, KHÔNG đi qua Python lúc chạy.
// Khác GVM 16/32-bit (máy silicon: gvm.ts / hw/gvm.v): mỗi ô mang LOẠI + giá trị 64 bit, nên
//   · số nguyên i64 thật (không va thẻ bit 30), tràn 64-bit → LỖI rõ ràng (không gói lặng lẽ);
//   · số thực IEEE-754 f64 thật (không phải điểm-cố-định);
//   · chuỗi / danh sách / bản / hàm / tri / mảng là đối tượng trên heap có dọn rác;
//   · LỆNH KHỐI trên `mảng` f64 (cánh bướm, nhân chọn, đổi chọn, tổng |z|²…) chạy vòng lặp
//     native — đúng vai "C bên dưới numpy", nhưng là máy của GIAO.
// CHUẨN ĐỐI CHIẾU = trình thông dịch giao.py: cùng chương trình phải in RA Y HỆT (kiem_gvm64.py).
// I/O = WASI tối thiểu (chuẩn WASM, KHÔNG phụ thuộc Node): máy chỉ ĐỌC stdin (chương trình) và
// GHI stdout/stderr. Không thư mục, không mạng. Chạy trên runtime WASI bất kỳ, vd:
//   wasmtime run wasm/gvm64.wasm -- [--bước N] [--trần-ds N] [--cho-giờ] < tệp.g64
// Đồng hồ chỉ tới tay chương trình GIAO khi host cấp --cho-giờ (năng lực ở tầng GIAO).
// ============================================================

@external("wasi_snapshot_preview1", "fd_read")        declare function wasi_fd_read(fd: u32, iovs: usize, n: usize, nread: usize): u16;
@external("wasi_snapshot_preview1", "fd_write")       declare function wasi_fd_write(fd: u32, iovs: usize, n: usize, nw: usize): u16;
@external("wasi_snapshot_preview1", "args_sizes_get") declare function wasi_args_sizes_get(argc: usize, bufsize: usize): u16;
@external("wasi_snapshot_preview1", "args_get")       declare function wasi_args_get(argv: usize, buf: usize): u16;
@external("wasi_snapshot_preview1", "clock_time_get") declare function wasi_clock_time_get(id: u32, prec: u64, t: usize): u16;
@external("wasi_snapshot_preview1", "proc_exit")      declare function wasi_proc_exit(code: u32): void;

const IOV = new StaticArray<u32>(4); const NW = new StaticArray<u32>(2); const TBUF = new StaticArray<u64>(1);
function ghiFd(fd: u32, ptr: usize, len: usize): void {
  while (len > 0) {
    IOV[0] = <u32>ptr; IOV[1] = <u32>len;
    if (wasi_fd_write(fd, changetype<usize>(IOV), 1, changetype<usize>(NW)) != 0) return;
    let w = <usize>NW[0]; if (w == 0) return; ptr += w; len -= w;
  }
}
function ghiChuoi(fd: u32, s: string): void {                      // UTF-16 → UTF-8
  let b = String.UTF8.encode(s, false); ghiFd(fd, changetype<usize>(b), <usize>b.byteLength);
}
function host_gio_he(): f64 { wasi_clock_time_get(0, 1000, changetype<usize>(TBUF)); return <f64>TBUF[0] / 1.0e9; }
// Lỗi nội bộ của runtime AssemblyScript (không bao giờ xảy ra nếu máy đúng) = bẫy WASM 'unreachable':
// runtime WASI dừng máy an toàn. Dọn rác: runtime 'incremental' (quét cả biến cục bộ — an toàn mọi điểm).

// ---------------- LOẠI giá trị ----------------
const K_AN: u8 = 0, K_INT: u8 = 1, K_F64: u8 = 2, K_STR: u8 = 3, K_LIST: u8 = 4, K_MAP: u8 = 5,
      K_FUNC: u8 = 6, K_TRI: u8 = 7, K_MANG: u8 = 8, K_BUILTIN: u8 = 9, K_BIG: u8 = 10, K_UNSET: u8 = 255;

class Obj {}
class SObj extends Obj {
  // Chuỗi GIAO đếm theo ĐIỂM MÃ (như Python); chuỗi AssemblyScript là UTF-16. Chuỗi toàn BMP (gần như
  // mọi văn bản tiếng Việt) dùng thẳng chỉ số UTF-16; chuỗi có cặp thay thế (emoji…) thì dựng mảng điểm mã.
  bmp: i32 = -1; cps: Int32Array | null = null;
  constructor(public s: string) { super(); }
}
class LObj extends Obj {
  k: Array<u8> = new Array<u8>(); v: Array<i64> = new Array<i64>(); o: Array<Obj | null> = new Array<Obj | null>();
  push(k: u8, v: i64, o: Obj | null): void { this.k.push(k); this.v.push(v); this.o.push(o); }
  get length(): i32 { return this.k.length; }
}
class MObj extends Obj { ks: LObj = new LObj(); vs: LObj = new LObj(); idx: Map<string, i32> = new Map<string, i32>(); }
class Frame extends Obj {
  k: StaticArray<u8>; v: StaticArray<i64>; o: StaticArray<Obj | null>;
  constructor(n: i32, public parent: Frame | null) {
    super(); this.k = new StaticArray<u8>(n); this.v = new StaticArray<i64>(n); this.o = new StaticArray<Obj | null>(n);
    for (let i = 0; i < n; i++) this.k[i] = K_UNSET;
  }
}
class FObj extends Obj { constructor(public fn: i32, public env: Frame | null) { super(); } }
class TObj extends Obj { k: u8 = 0; v: i64 = 0; o: Obj | null = null; g: f64 = 0; st: i32 = 0; }  // st: 0 ẩn, 1 sáng, 2 tối
class AObj extends Obj { constructor(public re: Float64Array, public im: Float64Array) { super(); } }
// SỐ LỚN tuỳ ý (như int của Python): dấu + độ lớn cơ số 2^32 (little-endian, không có 0 dẫn đầu).
// Chỉ dùng khi KHÔNG vừa i64 — mọi kết quả vừa i64 được chuẩn hoá về K_INT (một biểu diễn duy nhất).
class BObj extends Obj { constructor(public neg: bool, public m: Array<u32>) { super(); } }

// ---------------- chương trình (nạp từ host) ----------------
let code = new Int32Array(0);
let ipool = new Array<i64>(); let fpool = new Array<f64>(); let spool = new Array<SObj>();
let fnEntry = new Array<i32>(); let fnNParams = new Array<i32>(); let fnNSlots = new Array<i32>();
let fnName = new Array<i32>(); let fnRepr = new Array<i32>();
let chStart = new Array<i32>(); let chLen = new Array<i32>(); let chItems = new Array<i32>();   // (kiểu, sâu, ô)
let chName = new Array<i32>();
let nGlobals = 0;
let gk = new StaticArray<u8>(0); let gv = new StaticArray<i64>(0); let go = new StaticArray<Obj | null>(0);
let tmpChars = new Array<i32>();

export function nap_ma(n: i32): void { code = new Int32Array(n); }
export function nap_tu(i: i32, w: i32): void { code[i] = w; }
export function nap_int(v: i64): void { ipool.push(v); }
export function nap_f64(v: f64): void { fpool.push(v); }
export function nap_ky(c: i32): void { tmpChars.push(c); }
export function nap_chuoi(): void {
  let s = ""; for (let i = 0; i < tmpChars.length; i++) s += String.fromCodePoint(tmpChars[i]);
  spool.push(new SObj(s)); tmpChars = new Array<i32>();
}
export function nap_ham(entry: i32, np: i32, ns: i32, name: i32, repr: i32): void {
  fnEntry.push(entry); fnNParams.push(np); fnNSlots.push(ns); fnName.push(name); fnRepr.push(repr);
}
export function nap_chuoi_ten(start: i32, len: i32, nameStr: i32): void { chStart.push(start); chLen.push(len); chName.push(nameStr); }
export function nap_muc_ten(x: i32): void { chItems.push(x); }
export function nap_toan_cuc(n: i32): void {
  nGlobals = n; gk = new StaticArray<u8>(n); gv = new StaticArray<i64>(n); go = new StaticArray<Obj | null>(n);
  for (let i = 0; i < n; i++) gk[i] = K_UNSET;
}
export function dat_dung_san(g: i32, id: i32): void { gk[g] = K_BUILTIN; gv[g] = <i64>id; go[g] = null; }

// ---------------- giới hạn (host đặt; mặc định như trình thông dịch) ----------------
let MAX_STEPS: i64 = 4000000000; let MAX_DEPTH: i32 = 10000; let MAX_LIST: i32 = 1000000; let MAX_STR: i32 = 2000000;
export function dat_gioi_han(buoc: i64, sau: i32, ds: i32, chuoi: i32): void { MAX_STEPS = buoc; MAX_DEPTH = sau; MAX_LIST = ds; MAX_STR = chuoi; }
let coGio = false;
export function cap_gio(): void { coGio = true; }

// ---------------- ngăn xếp giá trị ----------------
const SN = 1 << 20;
const sk = new StaticArray<u8>(SN); const sv = new StaticArray<i64>(SN); const so = new StaticArray<Obj | null>(SN);
let sp = 0;
@inline function push(k: u8, v: i64, o: Obj | null): void { sk[sp] = k; sv[sp] = v; so[sp] = o; sp++; }
@inline function pushInt(v: i64): void { sk[sp] = K_INT; sv[sp] = v; so[sp] = null; sp++; }
@inline function pushF(x: f64): void { sk[sp] = K_F64; sv[sp] = reinterpret<i64>(x); so[sp] = null; sp++; }
@inline function pushAn(): void { sk[sp] = K_AN; sv[sp] = 0; so[sp] = null; sp++; }
@inline function pushObj(k: u8, o: Obj): void { sk[sp] = k; sv[sp] = 0; so[sp] = o; sp++; }

// ---------------- lỗi (không có ngoại lệ trong WASM: cờ + gỡ-cuộn ở vòng chính) ----------------
let loi = false; let loiGioiHan = false; let loiMsg = "";
function err(msg: string): void { if (!loi) { loi = true; loiGioiHan = false; loiMsg = msg; } }
function limit(msg: string): void { if (!loi) { loi = true; loiGioiHan = true; loiMsg = msg; } }

// ---------------- chuỗi hằng dùng nhiều ----------------
let S_SANG: SObj = new SObj("sáng"); let S_TOI: SObj = new SObj("tối");
function pushTruth(b: bool): void { pushObj(K_STR, b ? S_SANG : S_TOI); }
function pushStr(s: string): void { pushObj(K_STR, new SObj(s)); }

// ---------------- đầu ra (đệm UTF-16 → host) ----------------
const OUT = new StaticArray<u16>(1 << 16); let outN = 0;
function flush(): void { if (outN > 0) { ghiChuoi(1, String.UTF16.decodeUnsafe(changetype<usize>(OUT), <usize>outN << 1)); outN = 0; } }
function write(s: string): void {
  for (let i = 0; i < s.length; i++) { if (outN >= OUT.length) flush(); OUT[outN++] = <u16>s.charCodeAt(i); }
}
export function xa_dem(): void { flush(); }

// ============================================================
// ĐỊNH DẠNG SỐ THỰC — trùng khít Python format(x, '.4g') / format(x, '+.2f')
// Làm TRÊN GIÁ TRỊ NHỊ PHÂN CHÍNH XÁC (số lớn cơ số 1e9) + làm tròn nửa-về-chẵn như CPython.
// ============================================================
function bigMulSmall(a: Array<u32>, m: u32): void {        // a *= m  (cơ số 1e9, little-endian)
  let carry: u64 = 0;
  for (let i = 0; i < a.length; i++) { let t: u64 = <u64>a[i] * <u64>m + carry; a[i] = <u32>(t % 1000000000); carry = t / 1000000000; }
  while (carry > 0) { a.push(<u32>(carry % 1000000000)); carry /= 1000000000; }
}
function bigDigits(a: Array<u32>): string {
  let s = (<u64>a[a.length - 1]).toString();
  for (let i = a.length - 2; i >= 0; i--) { let t = (<u64>a[i]).toString(); while (t.length < 9) t = "0" + t; s += t; }
  return s;
}
// |x| > 0 hữu hạn → (chữ số D, số mũ P): |x| = 0.D × 10^P  (D không có số 0 dẫn đầu)
let exD = ""; let exP = 0;
function exact(x: f64): void {
  let bits = reinterpret<u64>(x); let e = <i32>((bits >> 52) & 0x7FF); let m: u64 = bits & 0xFFFFFFFFFFFFF;
  if (e == 0) e = 1; else m |= (<u64>1 << 52);
  e -= 1075;                                               // x = m · 2^e
  let a = new Array<u32>(); a.push(<u32>(m % 1000000000)); if (m >= 1000000000) { a.push(<u32>((m / 1000000000) % 1000000000)); if (m >= 1000000000000000000) a.push(<u32>(m / 1000000000000000000)); }
  let shift = 0;
  if (e >= 0) { for (let i = 0; i < e; i++) bigMulSmall(a, 2); }
  else { for (let i = 0; i < -e; i++) bigMulSmall(a, 5); shift = e; }   // m·2^e = m·5^(-e) · 10^e
  let d = bigDigits(a); let k = 0; while (k < d.length - 1 && d.charCodeAt(k) == 48) k++;
  d = d.substr(k);
  let end = d.length; while (end > 1 && d.charCodeAt(end - 1) == 48) end--;       // bỏ 0 đuôi (không đổi giá trị)
  exP = d.length + shift; exD = d.substr(0, end);
}
// làm tròn chuỗi chữ số D tới n chữ số đầu (nửa-về-chẵn); trả D' (dài n) và có thể tăng mũ
let rdCarry = 0;
function roundDigits(D: string, n: i32): string {
  rdCarry = 0;
  if (n <= 0) {                                             // làm tròn về 0 hay 1 ở vị trí trước cả D
    if (n < 0) return "";
    // n == 0: so D với 0.5
    let c0 = D.charCodeAt(0) - 48; let up = false;
    if (c0 > 5) up = true; else if (c0 == 5) { up = false; for (let i = 1; i < D.length; i++) if (D.charCodeAt(i) != 48) { up = true; break; } }
    if (up) { rdCarry = 1; return "1"; } return "";
  }
  if (D.length <= n) { let s = D; while (s.length < n) s += "0"; return s; }
  let next = D.charCodeAt(n) - 48; let up = false;
  if (next > 5) up = true;
  else if (next == 5) {
    let rest = false; for (let i = n + 1; i < D.length; i++) if (D.charCodeAt(i) != 48) { rest = true; break; }
    if (rest) up = true; else up = ((D.charCodeAt(n - 1) - 48) & 1) == 1;   // nửa → chẵn
  }
  let arr = new Array<i32>(n); for (let i = 0; i < n; i++) arr[i] = D.charCodeAt(i) - 48;
  if (up) {
    let i = n - 1;
    while (i >= 0) { arr[i]++; if (arr[i] < 10) break; arr[i] = 0; i--; }
    if (i < 0) { rdCarry = 1; arr.unshift(1); arr.pop(); }
  }
  let s = ""; for (let i = 0; i < arr.length; i++) s += String.fromCharCode(48 + arr[i]); return s;
}
function fmtG(x: f64, p: i32): string {                      // Python format(x, '.{p}g')
  if (isNaN(x)) return "nan";
  if (!isFinite(x)) return x > 0 ? "inf" : "-inf";
  let neg = (reinterpret<u64>(x) >> 63) != 0; let sign = neg ? "-" : "";
  if (x == 0) return sign + "0";
  exact(neg ? -x : x);
  let D = roundDigits(exD, p); let P = exP + rdCarry;       // |x| ≈ 0.D × 10^P
  let X = P - 1;                                            // số mũ khoa học
  let body = "";
  if (X >= -4 && X < p) {
    // cố định: phần nguyên = D[0..P), phần lẻ = phần còn lại; bỏ 0 đuôi
    if (P <= 0) { body = "0."; for (let i = 0; i < -P; i++) body += "0"; body += D; }
    else if (P >= D.length) { body = D; for (let i = D.length; i < P; i++) body += "0"; }
    else body = D.substr(0, P) + "." + D.substr(P);
    if (body.includes(".")) { let e = body.length; while (body.charCodeAt(e - 1) == 48) e--; if (body.charCodeAt(e - 1) == 46) e--; body = body.substr(0, e); }
  } else {
    let mant = D.substr(0, 1); let fr = D.substr(1); let e = fr.length; while (e > 0 && fr.charCodeAt(e - 1) == 48) e--; fr = fr.substr(0, e);
    if (fr.length > 0) mant += "." + fr;
    let ae = X < 0 ? -X : X; let es = ae.toString(); if (es.length < 2) es = "0" + es;
    body = mant + "e" + (X < 0 ? "-" : "+") + es;
  }
  return sign + body;
}
function fmtF(x: f64, d: i32, plus: bool): string {          // Python format(x, '{+}.{d}f')
  if (isNaN(x)) return "nan";
  if (!isFinite(x)) return x > 0 ? (plus ? "+inf" : "inf") : "-inf";
  let neg = (reinterpret<u64>(x) >> 63) != 0;
  let body = "";
  if (x == 0) { body = "0"; if (d > 0) { body += "."; for (let i = 0; i < d; i++) body += "0"; } }
  else {
    exact(neg ? -x : x);
    let n = exP + d;                                        // số chữ số giữ lại
    let D = roundDigits(exD, n); let P = exP + rdCarry;
    if (D.length == 0) { D = "0"; P = 1; }
    let ip = ""; let fp = "";
    if (P <= 0) { ip = "0"; let z = ""; for (let i = 0; i < -P; i++) z += "0"; fp = z + D; }
    else { ip = D.substr(0, P); fp = D.substr(P); while (ip.length < P) ip += "0"; }
    while (fp.length < d) fp += "0"; fp = fp.substr(0, d);
    body = ip + (d > 0 ? "." + fp : "");
  }
  let isZero = true; for (let i = 0; i < body.length; i++) { let c = body.charCodeAt(i); if (c >= 49 && c <= 57) { isZero = false; break; } }
  if (neg) return "-" + body;                               // Python giữ dấu cho -0.00
  return (plus ? "+" : "") + body;
}

// ============================================================
// HIỂN THỊ (render) — trùng Runtime.render của giao.py
// ============================================================
function loai(k: u8, o: Obj | null): string {
  if (k == K_AN) return "ẩn";
  if (k == K_INT || k == K_F64 || k == K_BIG) return "số";
  if (k == K_STR) return "chuỗi";
  if (k == K_LIST) return "danh_sách";
  if (k == K_MAP) return "bản";
  if (k == K_FUNC) return "hàm";
  if (k == K_TRI) return "tri";
  return "?";
}
function pyRepr(s: string): string {                          // repr(str) kiểu Python (đủ cho tri)
  let q = "'"; if (s.includes("'") && !s.includes("\"")) q = "\"";
  let r = q;
  for (let i = 0; i < s.length; i++) {
    let c = s.charCodeAt(i);
    if (c == 92) r += "\\\\"; else if (c == 10) r += "\\n"; else if (c == 9) r += "\\t"; else if (c == 13) r += "\\r";
    else if (q == "'" && c == 39) r += "\\'"; else r += String.fromCharCode(c);
  }
  return r + q;
}
let sauRender = 0;
function render(k: u8, v: i64, o: Obj | null): string {
  if (k == K_LIST || k == K_MAP) {
    if (++sauRender > 2000) { sauRender = 0; limit("đệ quy quá sâu (cấu trúc lồng quá sâu hoặc tự chứa chính nó)"); return ""; }
    let r = renderCT(k, v, o); sauRender--; return r;
  }
  return renderCT(k, v, o);
}
function renderCT(k: u8, v: i64, o: Obj | null): string {
  if (k == K_AN) return "ẩn";
  if (k == K_INT) return v.toString();
  if (k == K_BIG) return bigStr(<BObj>o);
  if (k == K_F64) return fmtG(reinterpret<f64>(v), 4);
  if (k == K_STR) return (<SObj>o).s;
  if (k == K_LIST) {
    let l = <LObj>o; let s = "[";
    for (let i = 0; i < l.length; i++) { if (i > 0) s += ", "; s += render(l.k[i], l.v[i], l.o[i]); }
    return s + "]";
  }
  if (k == K_MAP) {
    let m = <MObj>o; let s = "{";
    for (let i = 0; i < m.ks.length; i++) {
      if (i > 0) s += ", ";
      s += render(m.ks.k[i], m.ks.v[i], m.ks.o[i]) + ": " + render(m.vs.k[i], m.vs.v[i], m.vs.o[i]);
    }
    return s + "}";
  }
  if (k == K_FUNC) return (<SObj>spool[fnRepr[(<FObj>o).fn]]).s;
  if (k == K_TRI) {
    let t = <TObj>o;
    if (t.st == 0) return "tri(ẩn — chưa giao thoa, γ=∅)";
    let vs = "";
    if (t.k == K_F64) vs = fmtG(reinterpret<f64>(t.v), 4);
    else if (t.k == K_STR) vs = pyRepr((<SObj>t.o).s);
    else vs = render(t.k, t.v, t.o);
    return "tri(" + vs + ", γ=" + fmtF(t.g, 2, true) + ", " + (t.st == 1 ? "sáng" : "tối") + ")";
  }
  if (k == K_MANG) return "<mảng " + (<AObj>o).re.length.toString() + " phần tử>";
  if (k == K_BUILTIN) return "<hàm dựng sẵn #" + v.toString() + ">";
  return "?";
}

// ---------------- số học an toàn 64-bit ----------------
function addOvf(a: i64, b: i64): bool { let r = a + b; return ((a ^ r) & (b ^ r)) < 0; }
function subOvf(a: i64, b: i64): bool { let r = a - b; return ((a ^ b) & (a ^ r)) < 0; }
function mulOvf(a: i64, b: i64): bool {
  if (a == 0 || b == 0) return false;
  if ((a == -1 && b == i64.MIN_VALUE) || (b == -1 && a == i64.MIN_VALUE)) return true;
  let r = a * b; return r / b != a;
}
const TRAN = "số nguyên vượt 64-bit — GVM-64 chưa có số lớn tuỳ ý (trình thông dịch thì có)";
function floorDivI(a: i64, b: i64): i64 { let q = a / b; if ((a % b != 0) && ((a < 0) != (b < 0))) q -= 1; return q; }
function floorDivF(vx: f64, wx: f64): f64 {                  // đúng thuật toán float_floor_div của CPython
  let mod = vx % wx; let div = (vx - mod) / wx;
  if (mod != 0) { if ((wx < 0) != (mod < 0)) { mod += wx; div -= 1.0; } }
  let fd: f64;
  if (div != 0) { fd = Math.floor(div); if (div - fd > 0.5) fd += 1.0; }
  else fd = copysign<f64>(0.0, vx / wx);
  return fd;
}
@inline function isNum(k: u8): bool { return k == K_INT || k == K_F64 || k == K_BIG; }
@inline function asF(k: u8, v: i64): f64 { return k == K_INT ? <f64>v : reinterpret<f64>(v); }
function asFO(k: u8, v: i64, o: Obj | null): f64 { return k == K_BIG ? bigToF(<BObj>o) : asF(k, v); }

// ============================================================
// SỐ LỚN — phép trên độ lớn (Array<u32>, cơ số 2^32)
// ============================================================
function magTrim(a: Array<u32>): Array<u32> { while (a.length > 0 && a[a.length - 1] == 0) a.pop(); return a; }
function magFromU64(x: u64): Array<u32> { let a = new Array<u32>(); if (x != 0) { a.push(<u32>x); if ((x >> 32) != 0) a.push(<u32>(x >> 32)); } return a; }
function magCmp(a: Array<u32>, b: Array<u32>): i32 {
  if (a.length != b.length) return a.length < b.length ? -1 : 1;
  for (let i = a.length - 1; i >= 0; i--) if (a[i] != b[i]) return a[i] < b[i] ? -1 : 1;
  return 0;
}
function magAdd(a: Array<u32>, b: Array<u32>): Array<u32> {
  let r = new Array<u32>(); let c: u64 = 0; let n = a.length > b.length ? a.length : b.length;
  for (let i = 0; i < n; i++) { let t: u64 = c + (i < a.length ? <u64>a[i] : 0) + (i < b.length ? <u64>b[i] : 0); r.push(<u32>t); c = t >> 32; }
  if (c != 0) r.push(<u32>c); return r;
}
function magSub(a: Array<u32>, b: Array<u32>): Array<u32> {          // a ≥ b
  let r = new Array<u32>(); let br: i64 = 0;
  for (let i = 0; i < a.length; i++) {
    let t: i64 = <i64>a[i] - (i < b.length ? <i64>b[i] : 0) - br;
    if (t < 0) { t += <i64>0x100000000; br = 1; } else br = 0; r.push(<u32>t);
  }
  return magTrim(r);
}
function magMul(a: Array<u32>, b: Array<u32>): Array<u32> {
  if (a.length == 0 || b.length == 0) return new Array<u32>();
  let r = new Array<u32>(a.length + b.length); for (let i = 0; i < r.length; i++) r[i] = 0;
  for (let i = 0; i < a.length; i++) {
    let c: u64 = 0; let ai = <u64>a[i];
    for (let j = 0; j < b.length; j++) { let t: u64 = ai * <u64>b[j] + <u64>r[i + j] + c; r[i + j] = <u32>t; c = t >> 32; }
    let k = i + b.length; while (c != 0) { let t: u64 = <u64>r[k] + c; r[k] = <u32>t; c = t >> 32; k++; }
  }
  return magTrim(r);
}
function magDivSmall(a: Array<u32>, d: u32): Array<u32> {           // thương; dư ở magRem
  let q = new Array<u32>(a.length); let rem: u64 = 0;
  for (let i = a.length - 1; i >= 0; i--) { let cur: u64 = (rem << 32) | <u64>a[i]; q[i] = <u32>(cur / <u64>d); rem = cur % <u64>d; }
  magRem = rem; return magTrim(q);
}
let magRem: u64 = 0;
function magShl(a: Array<u32>, n: i32): Array<u32> {
  let w = n >> 5, b = n & 31; let r = new Array<u32>(); for (let i = 0; i < w; i++) r.push(0);
  let c: u32 = 0;
  for (let i = 0; i < a.length; i++) { let x = a[i]; r.push(b == 0 ? x : ((x << b) | c)); c = b == 0 ? 0 : (x >> (32 - b)); }
  if (c != 0) r.push(c); return magTrim(r);
}
function magShr(a: Array<u32>, n: i32): Array<u32> {
  let w = n >> 5, b = n & 31; let r = new Array<u32>();
  for (let i = w; i < a.length; i++) {
    let lo = a[i] >> b; let hi: u32 = (b != 0 && i + 1 < a.length) ? (a[i + 1] << (32 - b)) : 0; r.push(lo | hi);
  }
  return magTrim(r);
}
// chia độ lớn (Knuth, thuật toán D) → thương; dư trong magMod
let magMod = new Array<u32>();
function magDivMod(a: Array<u32>, b: Array<u32>): Array<u32> {
  if (magCmp(a, b) < 0) { magMod = a.slice(0); return new Array<u32>(); }
  if (b.length == 1) { let q = magDivSmall(a, b[0]); magMod = magFromU64(magRem); return q; }
  let sh = clz<u32>(b[b.length - 1]);
  let u = magShl(a, sh); let v = magShl(b, sh); if (u.length == a.length) u.push(0); else if (u.length < a.length + 1) u.push(0);
  while (u.length < a.length + 1) u.push(0);
  let n = v.length, m = u.length - n; let q = new Array<u32>(m); for (let i = 0; i < m; i++) q[i] = 0;
  let vt = <u64>v[n - 1], vt2 = <u64>v[n - 2];
  for (let j = m - 1; j >= 0; j--) {
    let num: u64 = (<u64>u[j + n] << 32) | <u64>u[j + n - 1];
    let qh: u64 = num / vt; let rh: u64 = num % vt;
    while (qh >= 0x100000000 || qh * vt2 > ((rh << 32) | <u64>u[j + n - 2])) { qh--; rh += vt; if (rh >= 0x100000000) break; }
    let br: i64 = 0; let c: u64 = 0;
    for (let i = 0; i < n; i++) {
      let p: u64 = qh * <u64>v[i] + c; c = p >> 32;
      let t: i64 = <i64>u[i + j] - <i64>(p & 0xFFFFFFFF) - br;
      if (t < 0) { t += <i64>0x100000000; br = 1; } else br = 0; u[i + j] = <u32>t;
    }
    let t: i64 = <i64>u[j + n] - <i64>c - br;
    if (t < 0) {                                                       // trừ quá: cộng lại
      u[j + n] = <u32>(t + <i64>0x100000000); qh--;
      let c2: u64 = 0;
      for (let i = 0; i < n; i++) { let s2: u64 = <u64>u[i + j] + <u64>v[i] + c2; u[i + j] = <u32>s2; c2 = s2 >> 32; }
      u[j + n] = <u32>(<u64>u[j + n] + c2);
    } else u[j + n] = <u32>t;
    q[j] = <u32>qh;
  }
  magMod = magShr(magTrim(u.slice(0, n)), sh);
  return magTrim(q);
}
function magToDec(a: Array<u32>): string {
  if (a.length == 0) return "0";
  let parts = new Array<string>(); let x = a.slice(0);
  while (x.length > 0) { x = magDivSmall(x, 1000000000); parts.push((<u64>magRem).toString()); }
  let r = parts[parts.length - 1];
  for (let i = parts.length - 2; i >= 0; i--) { let t = parts[i]; while (t.length < 9) t = "0" + t; r += t; }
  return r;
}
// giá trị số nguyên dạng (dấu, độ lớn) — từ K_INT hoặc K_BIG
let tNeg = false; let tMag = new Array<u32>();
function toMag(k: u8, v: i64, o: Obj | null): void {
  if (k == K_BIG) { let b = <BObj>o; tNeg = b.neg; tMag = b.m; return; }
  tNeg = v < 0; tMag = magFromU64(v < 0 ? <u64>(-(v + 1)) + 1 : <u64>v);
}
// chuẩn hoá (dấu, độ lớn) → đẩy K_INT nếu vừa i64, ngược lại K_BIG
function pushBig(neg: bool, m: Array<u32>): void {
  m = magTrim(m);
  if (m.length <= 2) {
    let x: u64 = m.length == 0 ? 0 : (m.length == 1 ? <u64>m[0] : ((<u64>m[1] << 32) | <u64>m[0]));
    if (!neg && x <= <u64>i64.MAX_VALUE) { pushInt(<i64>x); return; }
    if (neg && x <= <u64>i64.MAX_VALUE + 1) { pushInt(x == <u64>i64.MAX_VALUE + 1 ? i64.MIN_VALUE : -<i64>x); return; }
  }
  pushObj(K_BIG, new BObj(neg, m));
}
function bigToF(b: BObj): f64 { let x: f64 = 0; for (let i = b.m.length - 1; i >= 0; i--) x = x * 4294967296.0 + <f64>b.m[i]; return b.neg ? -x : x; }
function bigStr(b: BObj): string { return (b.neg ? "-" : "") + magToDec(b.m); }
function bigFromDec(s: string): BObj {
  let neg = false; let i = 0; if (s.charCodeAt(0) == 45) { neg = true; i = 1; }
  let m = new Array<u32>();
  for (; i < s.length; i++) { m = magMul(m, magFromU64(10)); m = magAdd(m, magFromU64(<u64>(s.charCodeAt(i) - 48))); }
  return new BObj(neg, magTrim(m));
}
// phép số nguyên chính xác (một bên là số lớn, hoặc i64 tràn)
function bigArith(op: i32, lk: u8, lv: i64, lo: Obj | null, rk: u8, rv: i64, ro: Obj | null): void {
  toMag(lk, lv, lo); let an = tNeg, am = tMag; toMag(rk, rv, ro); let bn = tNeg, bm = tMag;
  if (op == 11 || op == 12) {
    if (op == 12) bn = !bn;
    if (an == bn) { pushBig(an, magAdd(am, bm)); return; }
    let c = magCmp(am, bm); if (c == 0) { pushInt(0); return; }
    if (c > 0) pushBig(an, magSub(am, bm)); else pushBig(bn, magSub(bm, am));
    return;
  }
  if (op == 13) { pushBig(an != bn, magMul(am, bm)); return; }
  if (op == 15) {                                                    // // chia sàn (Python)
    if (bm.length == 0) { pushAn(); return; }
    let q = magDivMod(am, bm);
    if (an != bn && magMod.length > 0) q = magAdd(q, magFromU64(1));
    pushBig(an != bn, q); return;
  }
  if (op == 14) { if (bm.length == 0) { pushAn(); return; } pushF(asFO(lk, lv, lo) / asFO(rk, rv, ro)); return; }
  let c: i32 = 0;                                                    // so sánh
  if (an != bn) c = an ? -1 : 1; else { c = magCmp(am, bm); if (an) c = -c; }
  if (am.length == 0 && bm.length == 0) c = 0;
  let r = false;
  if (op == 16) r = c == 0; else if (op == 17) r = c != 0; else if (op == 18) r = c < 0;
  else if (op == 19) r = c > 0; else if (op == 20) r = c <= 0; else r = c >= 0;
  pushTruth(r);
}
// phép bit trên số nguyên TUỲ Ý theo bù-hai VÔ HẠN (như Python): 0 and · 1 or · 2 xor
function twos(neg: bool, m: Array<u32>, n: i32): Array<u32> {       // n từ, bù hai
  let r = new Array<u32>(n); for (let i = 0; i < n; i++) r[i] = i < m.length ? m[i] : 0;
  if (neg) { let c: u64 = 1; for (let i = 0; i < n; i++) { let t: u64 = <u64>(~r[i]) + c; r[i] = <u32>t; c = t >> 32; } }
  return r;
}
function bigBit(kind: i32, ak: u8, av: i64, ao: Obj | null, bk: u8, bv: i64, bo: Obj | null): void {
  toMag(ak, av, ao); let an = tNeg, am = tMag; toMag(bk, bv, bo); let bn = tNeg, bm = tMag;
  let n = (am.length > bm.length ? am.length : bm.length) + 1;
  let x = twos(an, am, n), y = twos(bn, bm, n); let r = new Array<u32>(n);
  for (let i = 0; i < n; i++) r[i] = kind == 0 ? (x[i] & y[i]) : (kind == 1 ? (x[i] | y[i]) : (x[i] ^ y[i]));
  let neg = (r[n - 1] >> 31) != 0;
  if (neg) { let c: u64 = 1; for (let i = 0; i < n; i++) { let t: u64 = <u64>(~r[i]) + c; r[i] = <u32>t; c = t >> 32; } }
  pushBig(neg, r);
}

// ---------------- chân lý ba trị ----------------
// trả 0 = ẩn, 1 = sáng, 2 = tối  (truthy3 của giao.py)
function truthy3(k: u8, v: i64, o: Obj | null): i32 {
  if (k == K_AN) return 0;
  if (k == K_STR) { let s = (<SObj>o).s; if (s == "sáng") return 1; if (s == "tối") return 2; return s.length > 0 ? 1 : 2; }
  if (k == K_TRI) { let t = <TObj>o; if (t.st == 0) return 0; return t.g > 0 ? 1 : 2; }
  if (k == K_INT) return v != 0 ? 1 : 2;
  if (k == K_BIG) return 1;
  if (k == K_F64) return reinterpret<f64>(v) != 0 ? 1 : 2;
  if (k == K_LIST) return (<LObj>o).length > 0 ? 1 : 2;
  if (k == K_MAP) return (<MObj>o).ks.length > 0 ? 1 : 2;
  if (k == K_MANG) return (<AObj>o).re.length > 0 ? 1 : 2;
  return 1;
}

// ---------------- bằng nhau kiểu Python ----------------
let sauEq = 0;
function pyEq(ak: u8, av: i64, ao: Obj | null, bk: u8, bv: i64, bo: Obj | null): bool {
  if (ak == K_LIST && bk == K_LIST) {
    if (++sauEq > 2000) { sauEq = 0; limit("đệ quy quá sâu (so sánh cấu trúc lồng quá sâu)"); return false; }
    let r = pyEqCT(ak, av, ao, bk, bv, bo); sauEq--; return r;
  }
  return pyEqCT(ak, av, ao, bk, bv, bo);
}
function pyEqCT(ak: u8, av: i64, ao: Obj | null, bk: u8, bv: i64, bo: Obj | null): bool {
  if (isNum(ak) && isNum(bk)) {
    if (ak == K_INT && bk == K_INT) return av == bv;
    if (ak != K_F64 && bk != K_F64) {                                  // số nguyên chính xác (có số lớn)
      toMag(ak, av, ao); let an = tNeg, am = tMag; toMag(bk, bv, bo);
      return an == tNeg && magCmp(am, tMag) == 0;
    }
    return asFO(ak, av, ao) == asFO(bk, bv, bo);
  }
  if (ak != bk) return false;
  if (ak == K_AN) return true;
  if (ak == K_STR) return (<SObj>ao).s == (<SObj>bo).s;
  if (ak == K_LIST) {
    let a = <LObj>ao, b = <LObj>bo; if (a === b) return true; if (a.length != b.length) return false;
    for (let i = 0; i < a.length; i++) if (!pyEq(a.k[i], a.v[i], a.o[i], b.k[i], b.v[i], b.o[i])) return false;
    return true;
  }
  if (ak == K_BUILTIN) return av == bv;
  return ao === bo;                                         // bản / hàm / tri / mảng: đồng nhất
}

// ---------------- khoá bản ----------------
function mapKey(k: u8, v: i64, o: Obj | null): string {
  if (k == K_INT) return "i" + v.toString();
  if (k == K_BIG) return "i" + bigStr(<BObj>o);
  if (k == K_F64) {
    let x = reinterpret<f64>(v);
    if (x == Math.floor(x) && Math.abs(x) < 9.0e18) return "i" + (<i64>x).toString();
    return "f" + v.toString();
  }
  return "s" + (<SObj>o).s;
}

// ============================================================
// KHUNG GỌI HÀM + BẢNG TÊN
// ============================================================
let frame: Frame | null = null;
const CN = 1 << 16;
const cRet = new StaticArray<i32>(CN); const cFrame = new StaticArray<Frame | null>(CN); let csp = 0;
// handler thử/bắt
const hAddr = new StaticArray<i32>(4096); const hSp = new StaticArray<i32>(4096); const hCsp = new StaticArray<i32>(4096);
const hFrame = new StaticArray<Frame | null>(4096); let hsp = 0;

// đọc một TÊN qua chuỗi phân giải (tĩnh), bỏ qua ô CHƯA ĐẶT như tra cứu động của giao.py
function loadName(ci: i32): bool {
  let st = chStart[ci], n = chLen[ci];
  for (let j = 0; j < n; j++) {
    let t = chItems[st + 3 * j], d = chItems[st + 3 * j + 1], s = chItems[st + 3 * j + 2];
    if (t == 0) {
      let f = frame; for (let q = 0; q < d; q++) f = (<Frame>f).parent;
      let fr = <Frame>f;
      if (fr.k[s] != K_UNSET) { push(fr.k[s], fr.v[s], fr.o[s]); return true; }
    } else {
      if (gk[s] != K_UNSET) { push(gk[s], gv[s], go[s]); return true; }
    }
  }
  err("tên '" + (<SObj>spool[chName[ci]]).s + "' chưa định nghĩa");
  return false;
}
// ô "hữu hình" cho tham chiếu slot: bit 23 = toàn cục
function slotSet(ref: i32, k: u8, v: i64, o: Obj | null): void {
  if (ref & 0x800000) { let g = ref & 0x7FFFFF; gk[g] = k; gv[g] = v; go[g] = o; }
  else { let f = <Frame>frame; f.k[ref] = k; f.v[ref] = v; f.o[ref] = o; }
}
function slotK(ref: i32): u8 { return (ref & 0x800000) ? gk[ref & 0x7FFFFF] : (<Frame>frame).k[ref]; }
function slotV(ref: i32): i64 { return (ref & 0x800000) ? gv[ref & 0x7FFFFF] : (<Frame>frame).v[ref]; }
function slotO(ref: i32): Obj | null { return (ref & 0x800000) ? go[ref & 0x7FFFFF] : (<Frame>frame).o[ref]; }

// ============================================================
// PHÉP HAI NGÔI — trùng Runtime.eval_bin
// ============================================================
function binop(op: i32): void {
  sp--; let rk = sk[sp], rv = sv[sp], ro = so[sp];
  sp--; let lk = sk[sp], lv = sv[sp], lo = so[sp];
  // — nhánh nhanh số↔số —
  if (isNum(lk) && isNum(rk)) { numBin(op, lk, lv, lo, rk, rv, ro); return; }
  if (lk == K_AN || rk == K_AN) { pushAn(); return; }
  if (lk == K_TRI) { let t = <TObj>lo; if (t.st == 0) { pushAn(); return; } lk = t.k; lv = t.v; lo = t.o; }
  if (rk == K_TRI) { let t = <TObj>ro; if (t.st == 0) { pushAn(); return; } rk = t.k; rv = t.v; ro = t.o; }
  if (lk == K_AN || rk == K_AN) { pushAn(); return; }
  if (isNum(lk) && isNum(rk)) { numBin(op, lk, lv, lo, rk, rv, ro); return; }
  if (op == 16) { pushTruth(pyEq(lk, lv, lo, rk, rv, ro)); return; }
  if (op == 17) { pushTruth(!pyEq(lk, lv, lo, rk, rv, ro)); return; }
  if (op == 11) {
    if (lk == K_STR || rk == K_STR) {
      let s = render(lk, lv, lo) + render(rk, rv, ro);
      if (s.length > MAX_STR) { limit("chuỗi quá lớn"); return; }
      pushStr(s); return;
    }
    if (lk == K_LIST && rk == K_LIST) {
      let a = <LObj>lo, b = <LObj>ro;
      if (a.length + b.length > MAX_LIST) { limit("danh sách quá lớn"); return; }
      let r = new LObj(); for (let i = 0; i < a.length; i++) r.push(a.k[i], a.v[i], a.o[i]);
      for (let i = 0; i < b.length; i++) r.push(b.k[i], b.v[i], b.o[i]);
      pushObj(K_LIST, r); return;
    }
    err("không thể '+' giữa " + loai(lk, lo) + " và " + loai(rk, ro)); return;
  }
  if (op == 12 || op == 13 || op == 14 || op == 15) {
    let nm = op == 12 ? "-" : (op == 13 ? "*" : (op == 14 ? "/" : "//"));
    err("không thể '" + nm + "' giữa " + loai(lk, lo) + " và " + loai(rk, ro)); return;
  }
  if (lk == K_STR && rk == K_STR) {
    let a = (<SObj>lo).s, b = (<SObj>ro).s; let r = false;
    if (op == 19) r = a > b; else if (op == 18) r = a < b; else if (op == 21) r = a >= b; else r = a <= b;
    pushTruth(r); return;
  }
  let nm = op == 18 ? "<" : (op == 19 ? ">" : (op == 20 ? "<=" : ">="));
  err("không thể so sánh '" + nm + "' giữa " + loai(lk, lo) + " và " + loai(rk, ro));
}
// op: 11 + · 12 - · 13 * · 14 / · 15 // · 16 == · 17 != · 18 < · 19 > · 20 <= · 21 >=
function numBin(op: i32, lk: u8, lv: i64, lo: Obj | null, rk: u8, rv: i64, ro: Obj | null): void {
  if ((lk == K_BIG || rk == K_BIG) && lk != K_F64 && rk != K_F64) { bigArith(op, lk, lv, lo, rk, rv, ro); return; }
  if (lk == K_INT && rk == K_INT) {
    if (op == 11) { if (addOvf(lv, rv)) { bigArith(op, lk, lv, lo, rk, rv, ro); return; } pushInt(lv + rv); return; }
    if (op == 12) { if (subOvf(lv, rv)) { bigArith(op, lk, lv, lo, rk, rv, ro); return; } pushInt(lv - rv); return; }
    if (op == 13) { if (mulOvf(lv, rv)) { bigArith(op, lk, lv, lo, rk, rv, ro); return; } pushInt(lv * rv); return; }
    if (op == 14) { if (rv == 0) { pushAn(); return; } pushF(<f64>lv / <f64>rv); return; }
    if (op == 15) { if (rv == 0) { pushAn(); return; } if (lv == i64.MIN_VALUE && rv == -1) { bigArith(op, lk, lv, lo, rk, rv, ro); return; } pushInt(floorDivI(lv, rv)); return; }
    let r = false;
    if (op == 16) r = lv == rv; else if (op == 17) r = lv != rv; else if (op == 18) r = lv < rv;
    else if (op == 19) r = lv > rv; else if (op == 20) r = lv <= rv; else r = lv >= rv;
    pushTruth(r); return;
  }
  let a = asFO(lk, lv, lo), b = asFO(rk, rv, ro);
  if (op == 11) { pushF(a + b); return; }
  if (op == 12) { pushF(a - b); return; }
  if (op == 13) { pushF(a * b); return; }
  if (op == 14) { if (b == 0) { pushAn(); return; } pushF(a / b); return; }
  if (op == 15) { if (b == 0) { pushAn(); return; } pushF(floorDivF(a, b)); return; }
  let r = false;
  if (op == 16) r = a == b; else if (op == 17) r = a != b; else if (op == 18) r = a < b;
  else if (op == 19) r = a > b; else if (op == 20) r = a <= b; else r = a >= b;
  pushTruth(r);
}

// ---------------- chỉ mục ----------------
function indexRead(ck: u8, cv: i64, co: Obj | null, ik: u8, iv: i64, io: Obj | null): void {
  if (ck == K_AN || ik == K_AN) { pushAn(); return; }
  if (ck == K_MAP) {
    if (!(isNum(ik) || ik == K_STR)) { err("khoá bản phải là số/chuỗi, gặp " + loai(ik, io)); return; }
    let m = <MObj>co; let key = mapKey(ik, iv, io);
    if (m.idx.has(key)) { let j = m.idx.get(key); push(m.vs.k[j], m.vs.v[j], m.vs.o[j]); } else pushAn();
    return;
  }
  if (ck != K_LIST && ck != K_STR) { err("không thể lập chỉ mục trên " + loai(ck, co)); return; }
  if (!isNum(ik)) { err("chỉ mục phải là số, gặp " + loai(ik, io)); return; }
  let i: i64 = ik == K_INT ? iv : (ik == K_BIG ? i64.MAX_VALUE : <i64>reinterpret<f64>(iv));
  if (ck == K_LIST) {
    let l = <LObj>co;
    if (i < 0 || i >= l.length) { err("chỉ mục " + i.toString() + " ngoài phạm vi 0.." + (l.length - 1).toString()); return; }
    let j = <i32>i; push(l.k[j], l.v[j], l.o[j]); return;
  }
  let so_ = <SObj>co; let L = cpLen(so_);
  if (i < 0 || i >= L) { err("chỉ mục " + i.toString() + " ngoài phạm vi 0.." + (L - 1).toString()); return; }
  pushStr(cpAt(so_, <i32>i));
}
function indexWrite(ck: u8, co: Obj | null, ik: u8, iv: i64, io: Obj | null, vk: u8, vv: i64, vo: Obj | null): void {
  if (ck == K_AN || ik == K_AN) return;
  if (ck == K_MAP) {
    if (!(isNum(ik) || ik == K_STR)) { err("khoá bản phải là số/chuỗi, gặp " + loai(ik, io)); return; }
    let m = <MObj>co; let key = mapKey(ik, iv, io);
    if (m.idx.has(key)) { let j = m.idx.get(key); m.vs.k[j] = vk; m.vs.v[j] = vv; m.vs.o[j] = vo; }
    else {
      if (m.ks.length + 1 > MAX_LIST) { limit("bản quá lớn"); return; }
      m.idx.set(key, m.ks.length); m.ks.push(ik, iv, io); m.vs.push(vk, vv, vo);
    }
    return;
  }
  if (ck == K_STR) { err("chuỗi BẤT BIẾN — không gán theo chỉ mục được (dùng tách/nối)"); return; }
  if (ck != K_LIST) { err("không thể gán chỉ mục trên " + loai(ck, co)); return; }
  if (!isNum(ik)) { err("chỉ mục phải là số, gặp " + loai(ik, io)); return; }
  let i: i64 = ik == K_INT ? iv : <i64>reinterpret<f64>(iv);
  let l = <LObj>co;
  if (i < 0 || i >= l.length) { err("chỉ mục " + i.toString() + " ngoài phạm vi 0.." + (l.length - 1).toString() + " (nới danh sách thì dùng gom)"); return; }
  let j = <i32>i; l.k[j] = vk; l.v[j] = vv; l.o[j] = vo;
}

// ---- BẢNG BỎ DẤU (sinh tự động từ unicodedata lúc dựng: NFD, bỏ dấu kết hợp Mn, đ→d) ----
const BD_KHOA: StaticArray<i32> = [192, 193, 194, 195, 196, 197, 199, 200, 201, 202, 203, 204, 205, 206, 207, 209, 210, 211, 212, 213, 214, 217, 218, 219, 220, 221, 224, 225, 226, 227, 228, 229, 231, 232, 233, 234, 235, 236, 237, 238, 239, 241, 242, 243, 244, 245, 246, 249, 250, 251, 252, 253, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 296, 297, 298, 299, 300, 301, 302, 303, 304, 308, 309, 310, 311, 313, 314, 315, 316, 317, 318, 323, 324, 325, 326, 327, 328, 332, 333, 334, 335, 336, 337, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 416, 417, 431, 432, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 478, 479, 480, 481, 482, 483, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 500, 501, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 542, 543, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 562, 563, 768, 769, 770, 771, 772, 773, 774, 775, 776, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786, 787, 788, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822, 823, 824, 825, 826, 827, 828, 829, 830, 831, 832, 833, 834, 835, 836, 837, 838, 839, 840, 841, 842, 843, 844, 845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856, 857, 858, 859, 860, 861, 862, 863, 864, 865, 866, 867, 868, 869, 870, 871, 872, 873, 874, 875, 876, 877, 878, 879, 884, 894, 901, 902, 903, 904, 905, 906, 908, 910, 911, 912, 938, 939, 940, 941, 942, 943, 944, 970, 971, 972, 973, 974, 979, 980, 1024, 1025, 1027, 1031, 1036, 1037, 1038, 1049, 1081, 1104, 1105, 1107, 1111, 1116, 1117, 1118, 1142, 1143, 1155, 1156, 1157, 1158, 1159, 1217, 1218, 1232, 1233, 1234, 1235, 1238, 1239, 1242, 1243, 1244, 1245, 1246, 1247, 1250, 1251, 1252, 1253, 1254, 1255, 1258, 1259, 1260, 1261, 1262, 1263, 1264, 1265, 1266, 1267, 1268, 1269, 1272, 1273, 1425, 1426, 1427, 1428, 1429, 1430, 1431, 1432, 1433, 1434, 1435, 1436, 1437, 1438, 1439, 1440, 1441, 1442, 1443, 1444, 1445, 1446, 1447, 1448, 1449, 1450, 1451, 1452, 1453, 1454, 1455, 1456, 1457, 1458, 1459, 1460, 1461, 1462, 1463, 1464, 1465, 1466, 1467, 1468, 1469, 1471, 1473, 1474, 1476, 1477, 1479, 1552, 1553, 1554, 1555, 1556, 1557, 1558, 1559, 1560, 1561, 1562, 1570, 1571, 1572, 1573, 1574, 1611, 1612, 1613, 1614, 1615, 1616, 1617, 1618, 1619, 1620, 1621, 1622, 1623, 1624, 1625, 1626, 1627, 1628, 1629, 1630, 1631, 1648, 1728, 1730, 1747, 1750, 1751, 1752, 1753, 1754, 1755, 1756, 1759, 1760, 1761, 1762, 1763, 1764, 1767, 1768, 1770, 1771, 1772, 1773, 1809, 1840, 1841, 1842, 1843, 1844, 1845, 1846, 1847, 1848, 1849, 1850, 1851, 1852, 1853, 1854, 1855, 1856, 1857, 1858, 1859, 1860, 1861, 1862, 1863, 1864, 1865, 1866, 1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2045, 2070, 2071, 2072, 2073, 2075, 2076, 2077, 2078, 2079, 2080, 2081, 2082, 2083, 2085, 2086, 2087, 2089, 2090, 2091, 2092, 2093, 2137, 2138, 2139, 2200, 2201, 2202, 2203, 2204, 2205, 2206, 2207, 2250, 2251, 2252, 2253, 2254, 2255, 2256, 2257, 2258, 2259, 2260, 2261, 2262, 2263, 2264, 2265, 2266, 2267, 2268, 2269, 2270, 2271, 2272, 2273, 2275, 2276, 2277, 2278, 2279, 2280, 2281, 2282, 2283, 2284, 2285, 2286, 2287, 2288, 2289, 2290, 2291, 2292, 2293, 2294, 2295, 2296, 2297, 2298, 2299, 2300, 2301, 2302, 2303, 2304, 2305, 2306, 2345, 2353, 2356, 2362, 2364, 2369, 2370, 2371, 2372, 2373, 2374, 2375, 2376, 2381, 2385, 2386, 2387, 2388, 2389, 2390, 2391, 2392, 2393, 2394, 2395, 2396, 2397, 2398, 2399, 2402, 2403, 2433, 2492, 2497, 2498, 2499, 2500, 2507, 2508, 2509, 2524, 2525, 2527, 2530, 2531, 2558, 2561, 2562, 2611, 2614, 2620, 2625, 2626, 2631, 2632, 2635, 2636, 2637, 2641, 2649, 2650, 2651, 2654, 2672, 2673, 2677, 2689, 2690, 2748, 2753, 2754, 2755, 2756, 2757, 2759, 2760, 2765, 2786, 2787, 2810, 2811, 2812, 2813, 2814, 2815, 2817, 2876, 2879, 2881, 2882, 2883, 2884, 2888, 2891, 2892, 2893, 2901, 2902, 2908, 2909, 2914, 2915, 2946, 2964, 3008, 3018, 3019, 3020, 3021, 3072, 3076, 3132, 3134, 3135, 3136, 3142, 3143, 3144, 3146, 3147, 3148, 3149, 3157, 3158, 3170, 3171, 3201, 3260, 3263, 3264, 3270, 3271, 3272, 3274, 3275, 3276, 3277, 3298, 3299, 3328, 3329, 3387, 3388, 3393, 3394, 3395, 3396, 3402, 3403, 3404, 3405, 3426, 3427, 3457, 3530, 3538, 3539, 3540, 3542, 3546, 3548, 3549, 3550, 3633, 3636, 3637, 3638, 3639, 3640, 3641, 3642, 3655, 3656, 3657, 3658, 3659, 3660, 3661, 3662, 3761, 3764, 3765, 3766, 3767, 3768, 3769, 3770, 3771, 3772, 3784, 3785, 3786, 3787, 3788, 3789, 3864, 3865, 3893, 3895, 3897, 3907, 3917, 3922, 3927, 3932, 3945, 3953, 3954, 3955, 3956, 3957, 3958, 3959, 3960, 3961, 3962, 3963, 3964, 3965, 3966, 3968, 3969, 3970, 3971, 3972, 3974, 3975, 3981, 3982, 3983, 3984, 3985, 3986, 3987, 3988, 3989, 3990, 3991, 3993, 3994, 3995, 3996, 3997, 3998, 3999, 4000, 4001, 4002, 4003, 4004, 4005, 4006, 4007, 4008, 4009, 4010, 4011, 4012, 4013, 4014, 4015, 4016, 4017, 4018, 4019, 4020, 4021, 4022, 4023, 4024, 4025, 4026, 4027, 4028, 4038, 4134, 4141, 4142, 4143, 4144, 4146, 4147, 4148, 4149, 4150, 4151, 4153, 4154, 4157, 4158, 4184, 4185, 4190, 4191, 4192, 4209, 4210, 4211, 4212, 4226, 4229, 4230, 4237, 4253, 4957, 4958, 4959, 5906, 5907, 5908, 5938, 5939, 5970, 5971, 6002, 6003, 6068, 6069, 6071, 6072, 6073, 6074, 6075, 6076, 6077, 6086, 6089, 6090, 6091, 6092, 6093, 6094, 6095, 6096, 6097, 6098, 6099, 6109, 6155, 6156, 6157, 6159, 6277, 6278, 6313, 6432, 6433, 6434, 6439, 6440, 6450, 6457, 6458, 6459, 6679, 6680, 6683, 6742, 6744, 6745, 6746, 6747, 6748, 6749, 6750, 6752, 6754, 6757, 6758, 6759, 6760, 6761, 6762, 6763, 6764, 6771, 6772, 6773, 6774, 6775, 6776, 6777, 6778, 6779, 6780, 6783, 6832, 6833, 6834, 6835, 6836, 6837, 6838, 6839, 6840, 6841, 6842, 6843, 6844, 6845, 6847, 6848, 6849, 6850, 6851, 6852, 6853, 6854, 6855, 6856, 6857, 6858, 6859, 6860, 6861, 6862, 6912, 6913, 6914, 6915, 6918, 6920, 6922, 6924, 6926, 6930, 6964, 6966, 6967, 6968, 6969, 6970, 6971, 6972, 6973, 6976, 6977, 6978, 6979, 7019, 7020, 7021, 7022, 7023, 7024, 7025, 7026, 7027, 7040, 7041, 7074, 7075, 7076, 7077, 7080, 7081, 7083, 7084, 7085, 7142, 7144, 7145, 7149, 7151, 7152, 7153, 7212, 7213, 7214, 7215, 7216, 7217, 7218, 7219, 7222, 7223, 7376, 7377, 7378, 7380, 7381, 7382, 7383, 7384, 7385, 7386, 7387, 7388, 7389, 7390, 7391, 7392, 7394, 7395, 7396, 7397, 7398, 7399, 7400, 7405, 7412, 7416, 7417, 7616, 7617, 7618, 7619, 7620, 7621, 7622, 7623, 7624, 7625, 7626, 7627, 7628, 7629, 7630, 7631, 7632, 7633, 7634, 7635, 7636, 7637, 7638, 7639, 7640, 7641, 7642, 7643, 7644, 7645, 7646, 7647, 7648, 7649, 7650, 7651, 7652, 7653, 7654, 7655, 7656, 7657, 7658, 7659, 7660, 7661, 7662, 7663, 7664, 7665, 7666, 7667, 7668, 7669, 7670, 7671, 7672, 7673, 7674, 7675, 7676, 7677, 7678, 7679, 7680, 7681, 7682, 7683, 7684, 7685, 7686, 7687, 7688, 7689, 7690, 7691, 7692, 7693, 7694, 7695, 7696, 7697, 7698, 7699, 7700, 7701, 7702, 7703, 7704, 7705, 7706, 7707, 7708, 7709, 7710, 7711, 7712, 7713, 7714, 7715, 7716, 7717, 7718, 7719, 7720, 7721, 7722, 7723, 7724, 7725, 7726, 7727, 7728, 7729, 7730, 7731, 7732, 7733, 7734, 7735, 7736, 7737, 7738, 7739, 7740, 7741, 7742, 7743, 7744, 7745, 7746, 7747, 7748, 7749, 7750, 7751, 7752, 7753, 7754, 7755, 7756, 7757, 7758, 7759, 7760, 7761, 7762, 7763, 7764, 7765, 7766, 7767, 7768, 7769, 7770, 7771, 7772, 7773, 7774, 7775, 7776, 7777, 7778, 7779, 7780, 7781, 7782, 7783, 7784, 7785, 7786, 7787, 7788, 7789, 7790, 7791, 7792, 7793, 7794, 7795, 7796, 7797, 7798, 7799, 7800, 7801, 7802, 7803, 7804, 7805, 7806, 7807, 7808, 7809, 7810, 7811, 7812, 7813, 7814, 7815, 7816, 7817, 7818, 7819, 7820, 7821, 7822, 7823, 7824, 7825, 7826, 7827, 7828, 7829, 7830, 7831, 7832, 7833, 7835, 7840, 7841, 7842, 7843, 7844, 7845, 7846, 7847, 7848, 7849, 7850, 7851, 7852, 7853, 7854, 7855, 7856, 7857, 7858, 7859, 7860, 7861, 7862, 7863, 7864, 7865, 7866, 7867, 7868, 7869, 7870, 7871, 7872, 7873, 7874, 7875, 7876, 7877, 7878, 7879, 7880, 7881, 7882, 7883, 7884, 7885, 7886, 7887, 7888, 7889, 7890, 7891, 7892, 7893, 7894, 7895, 7896, 7897, 7898, 7899, 7900, 7901, 7902, 7903, 7904, 7905, 7906, 7907, 7908, 7909, 7910, 7911, 7912, 7913, 7914, 7915, 7916, 7917, 7918, 7919, 7920, 7921, 7922, 7923, 7924, 7925, 7926, 7927, 7928, 7929, 7936, 7937, 7938, 7939, 7940, 7941, 7942, 7943, 7944, 7945, 7946, 7947, 7948, 7949, 7950, 7951, 7952, 7953, 7954, 7955, 7956, 7957, 7960, 7961, 7962, 7963, 7964, 7965, 7968, 7969, 7970, 7971, 7972, 7973, 7974, 7975, 7976, 7977, 7978, 7979, 7980, 7981, 7982, 7983, 7984, 7985, 7986, 7987, 7988, 7989, 7990, 7991, 7992, 7993, 7994, 7995, 7996, 7997, 7998, 7999, 8000, 8001, 8002, 8003, 8004, 8005, 8008, 8009, 8010, 8011, 8012, 8013, 8016, 8017, 8018, 8019, 8020, 8021, 8022, 8023, 8025, 8027, 8029, 8031, 8032, 8033, 8034, 8035, 8036, 8037, 8038, 8039, 8040, 8041, 8042, 8043, 8044, 8045, 8046, 8047, 8048, 8049, 8050, 8051, 8052, 8053, 8054, 8055, 8056, 8057, 8058, 8059, 8060, 8061, 8064, 8065, 8066, 8067, 8068, 8069, 8070, 8071, 8072, 8073, 8074, 8075, 8076, 8077, 8078, 8079, 8080, 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089, 8090, 8091, 8092, 8093, 8094, 8095, 8096, 8097, 8098, 8099, 8100, 8101, 8102, 8103, 8104, 8105, 8106, 8107, 8108, 8109, 8110, 8111, 8112, 8113, 8114, 8115, 8116, 8118, 8119, 8120, 8121, 8122, 8123, 8124, 8126, 8129, 8130, 8131, 8132, 8134, 8135, 8136, 8137, 8138, 8139, 8140, 8141, 8142, 8143, 8144, 8145, 8146, 8147, 8150, 8151, 8152, 8153, 8154, 8155, 8157, 8158, 8159, 8160, 8161, 8162, 8163, 8164, 8165, 8166, 8167, 8168, 8169, 8170, 8171, 8172, 8173, 8174, 8175, 8178, 8179, 8180, 8182, 8183, 8184, 8185, 8186, 8187, 8188, 8189, 8192, 8193, 8400, 8401, 8402, 8403, 8404, 8405, 8406, 8407, 8408, 8409, 8410, 8411, 8412, 8417, 8421, 8422, 8423, 8424, 8425, 8426, 8427, 8428, 8429, 8430, 8431, 8432, 8486, 8490, 8491, 8602, 8603, 8622, 8653, 8654, 8655, 8708, 8713, 8716, 8740, 8742, 8769, 8772, 8775, 8777, 8800, 8802, 8813, 8814, 8815, 8816, 8817, 8820, 8821, 8824, 8825, 8832, 8833, 8836, 8837, 8840, 8841, 8876, 8877, 8878, 8879, 8928, 8929, 8930, 8931, 8938, 8939, 8940, 8941, 9001, 9002, 10972, 11503, 11504, 11505, 11647, 11744, 11745, 11746, 11747, 11748, 11749, 11750, 11751, 11752, 11753, 11754, 11755, 11756, 11757, 11758, 11759, 11760, 11761, 11762, 11763, 11764, 11765, 11766, 11767, 11768, 11769, 11770, 11771, 11772, 11773, 11774, 11775];
const BD_GIA: StaticArray<string> = ["\u0041", "\u0041", "\u0041", "\u0041", "\u0041", "\u0041", "\u0043", "\u0045", "\u0045", "\u0045", "\u0045", "\u0049", "\u0049", "\u0049", "\u0049", "\u004e", "\u004f", "\u004f", "\u004f", "\u004f", "\u004f", "\u0055", "\u0055", "\u0055", "\u0055", "\u0059", "\u0061", "\u0061", "\u0061", "\u0061", "\u0061", "\u0061", "\u0063", "\u0065", "\u0065", "\u0065", "\u0065", "\u0069", "\u0069", "\u0069", "\u0069", "\u006e", "\u006f", "\u006f", "\u006f", "\u006f", "\u006f", "\u0075", "\u0075", "\u0075", "\u0075", "\u0079", "\u0079", "\u0041", "\u0061", "\u0041", "\u0061", "\u0041", "\u0061", "\u0043", "\u0063", "\u0043", "\u0063", "\u0043", "\u0063", "\u0043", "\u0063", "\u0044", "\u0064", "\u0044", "\u0064", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0047", "\u0067", "\u0047", "\u0067", "\u0047", "\u0067", "\u0047", "\u0067", "\u0048", "\u0068", "\u0049", "\u0069", "\u0049", "\u0069", "\u0049", "\u0069", "\u0049", "\u0069", "\u0049", "\u004a", "\u006a", "\u004b", "\u006b", "\u004c", "\u006c", "\u004c", "\u006c", "\u004c", "\u006c", "\u004e", "\u006e", "\u004e", "\u006e", "\u004e", "\u006e", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u0052", "\u0072", "\u0052", "\u0072", "\u0052", "\u0072", "\u0053", "\u0073", "\u0053", "\u0073", "\u0053", "\u0073", "\u0053", "\u0073", "\u0054", "\u0074", "\u0054", "\u0074", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0057", "\u0077", "\u0059", "\u0079", "\u0059", "\u005a", "\u007a", "\u005a", "\u007a", "\u005a", "\u007a", "\u004f", "\u006f", "\u0055", "\u0075", "\u0041", "\u0061", "\u0049", "\u0069", "\u004f", "\u006f", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0041", "\u0061", "\u0041", "\u0061", "\u00c6", "\u00e6", "\u0047", "\u0067", "\u004b", "\u006b", "\u004f", "\u006f", "\u004f", "\u006f", "\u01b7", "\u0292", "\u006a", "\u0047", "\u0067", "\u004e", "\u006e", "\u0041", "\u0061", "\u00c6", "\u00e6", "\u00d8", "\u00f8", "\u0041", "\u0061", "\u0041", "\u0061", "\u0045", "\u0065", "\u0045", "\u0065", "\u0049", "\u0069", "\u0049", "\u0069", "\u004f", "\u006f", "\u004f", "\u006f", "\u0052", "\u0072", "\u0052", "\u0072", "\u0055", "\u0075", "\u0055", "\u0075", "\u0053", "\u0073", "\u0054", "\u0074", "\u0048", "\u0068", "\u0041", "\u0061", "\u0045", "\u0065", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u0059", "\u0079", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u02b9", "\u003b", "\u00a8", "\u0391", "\u00b7", "\u0395", "\u0397", "\u0399", "\u039f", "\u03a5", "\u03a9", "\u03b9", "\u0399", "\u03a5", "\u03b1", "\u03b5", "\u03b7", "\u03b9", "\u03c5", "\u03b9", "\u03c5", "\u03bf", "\u03c5", "\u03c9", "\u03d2", "\u03d2", "\u0415", "\u0415", "\u0413", "\u0406", "\u041a", "\u0418", "\u0423", "\u0418", "\u0438", "\u0435", "\u0435", "\u0433", "\u0456", "\u043a", "\u0438", "\u0443", "\u0474", "\u0475", "", "", "", "", "", "\u0416", "\u0436", "\u0410", "\u0430", "\u0410", "\u0430", "\u0415", "\u0435", "\u04d8", "\u04d9", "\u0416", "\u0436", "\u0417", "\u0437", "\u0418", "\u0438", "\u0418", "\u0438", "\u041e", "\u043e", "\u04e8", "\u04e9", "\u042d", "\u044d", "\u0423", "\u0443", "\u0423", "\u0443", "\u0423", "\u0443", "\u0427", "\u0447", "\u042b", "\u044b", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u0627", "\u0627", "\u0648", "\u0627", "\u064a", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u06d5", "\u06c1", "\u06d2", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u0928", "\u0930", "\u0933", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u0915", "\u0916", "\u0917", "\u091c", "\u0921", "\u0922", "\u092b", "\u092f", "", "", "", "", "", "", "", "", "\u09c7\u09be", "\u09c7\u09d7", "", "\u09a1", "\u09a2", "\u09af", "", "", "", "", "", "\u0a32", "\u0a38", "", "", "", "", "", "", "", "", "", "\u0a16", "\u0a17", "\u0a1c", "\u0a2b", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u0b47", "\u0b47\u0b3e", "\u0b47\u0b57", "", "", "", "\u0b21", "\u0b22", "", "", "", "\u0b92\u0bd7", "", "\u0bc6\u0bbe", "\u0bc7\u0bbe", "\u0bc6\u0bd7", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u0cd5", "", "\u0cd5", "\u0cd6", "\u0cc2", "\u0cc2\u0cd5", "", "", "", "", "", "", "", "", "", "", "", "", "\u0d46\u0d3e", "\u0d47\u0d3e", "\u0d46\u0d57", "", "", "", "", "", "", "", "", "", "\u0dd9", "\u0dd9\u0dcf", "\u0dd9\u0dcf", "\u0dd9\u0ddf", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u0f42", "\u0f4c", "\u0f51", "\u0f56", "\u0f5b", "\u0f40", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u1025", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u1b05\u1b35", "\u1b07\u1b35", "\u1b09\u1b35", "\u1b0b\u1b35", "\u1b0d\u1b35", "\u1b11\u1b35", "", "", "", "", "", "", "\u1b35", "", "\u1b35", "\u1b3e\u1b35", "\u1b3f\u1b35", "", "\u1b35", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u0041", "\u0061", "\u0042", "\u0062", "\u0042", "\u0062", "\u0042", "\u0062", "\u0043", "\u0063", "\u0044", "\u0064", "\u0044", "\u0064", "\u0044", "\u0064", "\u0044", "\u0064", "\u0044", "\u0064", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0046", "\u0066", "\u0047", "\u0067", "\u0048", "\u0068", "\u0048", "\u0068", "\u0048", "\u0068", "\u0048", "\u0068", "\u0048", "\u0068", "\u0049", "\u0069", "\u0049", "\u0069", "\u004b", "\u006b", "\u004b", "\u006b", "\u004b", "\u006b", "\u004c", "\u006c", "\u004c", "\u006c", "\u004c", "\u006c", "\u004c", "\u006c", "\u004d", "\u006d", "\u004d", "\u006d", "\u004d", "\u006d", "\u004e", "\u006e", "\u004e", "\u006e", "\u004e", "\u006e", "\u004e", "\u006e", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u0050", "\u0070", "\u0050", "\u0070", "\u0052", "\u0072", "\u0052", "\u0072", "\u0052", "\u0072", "\u0052", "\u0072", "\u0053", "\u0073", "\u0053", "\u0073", "\u0053", "\u0073", "\u0053", "\u0073", "\u0053", "\u0073", "\u0054", "\u0074", "\u0054", "\u0074", "\u0054", "\u0074", "\u0054", "\u0074", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0056", "\u0076", "\u0056", "\u0076", "\u0057", "\u0077", "\u0057", "\u0077", "\u0057", "\u0077", "\u0057", "\u0077", "\u0057", "\u0077", "\u0058", "\u0078", "\u0058", "\u0078", "\u0059", "\u0079", "\u005a", "\u007a", "\u005a", "\u007a", "\u005a", "\u007a", "\u0068", "\u0074", "\u0077", "\u0079", "\u017f", "\u0041", "\u0061", "\u0041", "\u0061", "\u0041", "\u0061", "\u0041", "\u0061", "\u0041", "\u0061", "\u0041", "\u0061", "\u0041", "\u0061", "\u0041", "\u0061", "\u0041", "\u0061", "\u0041", "\u0061", "\u0041", "\u0061", "\u0041", "\u0061", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0045", "\u0065", "\u0049", "\u0069", "\u0049", "\u0069", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u004f", "\u006f", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0055", "\u0075", "\u0059", "\u0079", "\u0059", "\u0079", "\u0059", "\u0079", "\u0059", "\u0079", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u0391", "\u0391", "\u0391", "\u0391", "\u0391", "\u0391", "\u0391", "\u0391", "\u03b5", "\u03b5", "\u03b5", "\u03b5", "\u03b5", "\u03b5", "\u0395", "\u0395", "\u0395", "\u0395", "\u0395", "\u0395", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u0397", "\u0397", "\u0397", "\u0397", "\u0397", "\u0397", "\u0397", "\u0397", "\u03b9", "\u03b9", "\u03b9", "\u03b9", "\u03b9", "\u03b9", "\u03b9", "\u03b9", "\u0399", "\u0399", "\u0399", "\u0399", "\u0399", "\u0399", "\u0399", "\u0399", "\u03bf", "\u03bf", "\u03bf", "\u03bf", "\u03bf", "\u03bf", "\u039f", "\u039f", "\u039f", "\u039f", "\u039f", "\u039f", "\u03c5", "\u03c5", "\u03c5", "\u03c5", "\u03c5", "\u03c5", "\u03c5", "\u03c5", "\u03a5", "\u03a5", "\u03a5", "\u03a5", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u03a9", "\u03a9", "\u03a9", "\u03a9", "\u03a9", "\u03a9", "\u03a9", "\u03a9", "\u03b1", "\u03b1", "\u03b5", "\u03b5", "\u03b7", "\u03b7", "\u03b9", "\u03b9", "\u03bf", "\u03bf", "\u03c5", "\u03c5", "\u03c9", "\u03c9", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u0391", "\u0391", "\u0391", "\u0391", "\u0391", "\u0391", "\u0391", "\u0391", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u0397", "\u0397", "\u0397", "\u0397", "\u0397", "\u0397", "\u0397", "\u0397", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u03a9", "\u03a9", "\u03a9", "\u03a9", "\u03a9", "\u03a9", "\u03a9", "\u03a9", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u03b1", "\u0391", "\u0391", "\u0391", "\u0391", "\u0391", "\u03b9", "\u00a8", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u03b7", "\u0395", "\u0395", "\u0397", "\u0397", "\u0397", "\u1fbf", "\u1fbf", "\u1fbf", "\u03b9", "\u03b9", "\u03b9", "\u03b9", "\u03b9", "\u03b9", "\u0399", "\u0399", "\u0399", "\u0399", "\u1ffe", "\u1ffe", "\u1ffe", "\u03c5", "\u03c5", "\u03c5", "\u03c5", "\u03c1", "\u03c1", "\u03c5", "\u03c5", "\u03a5", "\u03a5", "\u03a5", "\u03a5", "\u03a1", "\u00a8", "\u00a8", "\u0060", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u03c9", "\u039f", "\u039f", "\u03a9", "\u03a9", "\u03a9", "\u00b4", "\u2002", "\u2003", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "\u03a9", "\u004b", "\u0041", "\u2190", "\u2192", "\u2194", "\u21d0", "\u21d4", "\u21d2", "\u2203", "\u2208", "\u220b", "\u2223", "\u2225", "\u223c", "\u2243", "\u2245", "\u2248", "\u003d", "\u2261", "\u224d", "\u003c", "\u003e", "\u2264", "\u2265", "\u2272", "\u2273", "\u2276", "\u2277", "\u227a", "\u227b", "\u2282", "\u2283", "\u2286", "\u2287", "\u22a2", "\u22a8", "\u22a9", "\u22ab", "\u227c", "\u227d", "\u2291", "\u2292", "\u22b2", "\u22b3", "\u22b4", "\u22b5", "\u3008", "\u3009", "\u2add", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""];
function boDau(t: string): string {
  let r = "";
  for (let i = 0; i < t.length; i++) {
    let c = t.codePointAt(i); if (c > 0xFFFF) i++;
    let lo = 0, hi = BD_KHOA.length;
    while (lo < hi) { let m = (lo + hi) >> 1; if (BD_KHOA[m] < c) lo = m + 1; else hi = m; }
    if (lo < BD_KHOA.length && BD_KHOA[lo] == c) r += BD_GIA[lo]; else r += String.fromCodePoint(c);
  }
  return r;
}

// ---- CDFL (Phụ lục F.4 / F.11-N) — trùng _R_scalar / skill_gamma / commitment_e của giao.py ----
const GAMMA_NEN: f64 = Math.exp(-1.0);
function rScalar(bk: u8, bv: i64, bo: Obj | null, tk: u8, tv: i64, to: Obj | null): f64 {
  let b = asFO(bk, bv, bo), t = asFO(tk, tv, to);
  let d = Math.abs(t - b); let sc = Math.abs(t); if (sc < 1.0) sc = 1.0;
  let q = d / sc; return Math.exp(-(q * q));
}
function skillGamma(R: f64, R0: f64): f64 {
  let a = -Math.log(R0 < 1e-12 ? 1e-12 : R0); let b = -Math.log(R < 1e-12 ? 1e-12 : R);
  if (a + b <= 1e-12) return 0.0;
  let g = (a - b) / (a + b); if (g > 1) g = 1; if (g < -1) g = -1; return g;
}

// ============================================================
// BUILTIN — đối ở sk/sv/so[b .. b+n); trả kết quả bằng push (sau khi hạ sp về b-1)
// ============================================================
let rk: u8 = 0; let rv: i64 = 0; let ro: Obj | null = null;
@inline function R(k: u8, v: i64, o: Obj | null): void { rk = k; rv = v; ro = o; }
@inline function RI(v: i64): void { rk = K_INT; rv = v; ro = null; }
@inline function RF(x: f64): void { rk = K_F64; rv = reinterpret<i64>(x); ro = null; }
@inline function RA(): void { rk = K_AN; rv = 0; ro = null; }
@inline function RT(b: bool): void { rk = K_STR; rv = 0; ro = b ? S_SANG : S_TOI; }
@inline function RS(s: string): void { rk = K_STR; rv = 0; ro = new SObj(s); }
@inline function RO(k: u8, o: Obj): void { rk = k; rv = 0; ro = o; }

function need(n: i32, want: i32, who: string): bool {
  if (n != want) { err(who + " cần " + want.toString() + " đối, nhận " + n.toString()); return false; } return true;
}
function isInt(b: i32): bool { return sk[b] == K_INT; }
function listOf(b: i32): LObj | null { return sk[b] == K_LIST ? <LObj>so[b] : null; }
function seqLen(b: i32, who: string): i32 {
  if (sk[b] == K_LIST) return (<LObj>so[b]).length;
  if (sk[b] == K_STR) return cpLen(<SObj>so[b]);
  err(who + " cần danh_sách/chuỗi, gặp " + loai(sk[b], so[b])); return -1;
}
function laBmp(o: SObj): bool {
  if (o.bmp < 0) {
    o.bmp = 1; let s = o.s;
    for (let i = 0; i < s.length; i++) { let c = s.charCodeAt(i); if (c >= 0xD800 && c <= 0xDFFF) { o.bmp = 0; break; } }
    if (o.bmp == 0) {
      let a = new Array<i32>(); for (let i = 0; i < s.length; i++) { let c = s.codePointAt(i); a.push(c); if (c > 0xFFFF) i++; }
      let r = new Int32Array(a.length); for (let i = 0; i < a.length; i++) r[i] = a[i]; o.cps = r;
    }
  }
  return o.bmp == 1;
}
function cpLen(o: SObj): i32 { return laBmp(o) ? o.s.length : (<Int32Array>o.cps).length; }
function cpAt(o: SObj, i: i32): string { return laBmp(o) ? o.s.charAt(i) : String.fromCodePoint((<Int32Array>o.cps)[i]); }
function strToList(o: SObj): LObj { let l = new LObj(); let n = cpLen(o); for (let i = 0; i < n; i++) l.push(K_STR, 0, new SObj(cpAt(o, i))); return l; }
function strFrom(o: SObj, from: i32): SObj {
  if (laBmp(o)) return new SObj(o.s.substr(from));
  let c = <Int32Array>o.cps; let s = ""; for (let i = from; i < c.length; i++) s += String.fromCodePoint(c[i]); return new SObj(s);
}
function copyList(l: LObj, from: i32, to: i32): LObj { let r = new LObj(); for (let i = from; i < to; i++) r.push(l.k[i], l.v[i], l.o[i]); return r; }
function mkMang(n: i32): AObj { return new AObj(new Float64Array(n), new Float64Array(n)); }

// ---- mảng: tiện ích chung cho lệnh khối (y hệt giao_mang.py, cả THỨ TỰ cộng dồn) ----
function mảng(b: i32, who: string): AObj | null {
  if (sk[b] != K_MANG) { err(who + " cần mảng, gặp " + loai(sk[b], so[b])); return null; } return <AObj>so[b];
}
function iarg(b: i32, who: string): i64 {
  if (sk[b] != K_INT) { err(who + " cần số nguyên, gặp " + loai(sk[b], so[b])); return 0; } return sv[b];
}
function farg(b: i32, who: string): f64 {
  if (!isNum(sk[b])) { err(who + " cần số, gặp " + loai(sk[b], so[b])); return 0; } return asFO(sk[b], sv[b], so[b]);
}
let czr: f64 = 0; let czi: f64 = 0;
function carg(b: i32, who: string): bool {                   // số phức [thực, ảo]
  let l = listOf(b);
  if (l === null || l.length != 2) { err(who + " cần số phức [thực, ảo]"); return false; }
  if (!isNum(l.k[0]) || !isNum(l.k[1])) { err(who + " cần số, gặp " + loai(isNum(l.k[0]) ? l.k[1] : l.k[0], null)); return false; }
  czr = asF(l.k[0], l.v[0]); czi = asF(l.k[1], l.v[1]); return true;
}
function checkMask(N: i32, sel: i64, mau: i64, who: string): bool {
  if ((N & (N - 1)) != 0 || N == 0) { err(who + ": chọn theo bit cần mảng dài 2^n (gặp " + N.toString() + ")"); return false; }
  if (sel < 0 || sel >= N || (mau & ~sel) != 0 || mau < 0) { err(who + ": sel/mẫu sai (mẫu phải ⊆ sel, trong 0.." + (N - 1).toString() + ")"); return false; }
  return true;
}
function bitCount(x: i64): i32 { return <i32>popcnt<i64>(x); }
// chỉ số (tăng dần) của các phần tử có (i & sel) == mẫu
function forSel(N: i32, sel: i32, mau: i32): Int32Array {
  let cnt = N >> bitCount(sel); let r = new Int32Array(cnt); let j = 0;
  if (sel == 0) { for (let i = 0; i < N; i++) r[j++] = i; return r; }
  // duyệt các tổ hợp bit TỰ DO theo thứ tự tăng: i = pdep(t, ~sel) | mẫu
  let free = ~sel & (N - 1);
  for (let t = 0; t < cnt; t++) {
    let x = 0, m = free, tt = t;
    while (m != 0) { let lb = m & -m; if (tt & 1) x |= lb; tt >>= 1; m &= m - 1; }
    r[j++] = x | mau;
  }
  return r;
}
const W_KHUC = 16384;   // khúc của giao_mang.py — dùng để CỘNG DỒN đúng thứ tự như bản tham chiếu

function builtin(id: i32, b: i32, n: i32): void {
  switch (id) {
    // ---------- danh sách / chuỗi ----------
    case 0: { // dài
      if (!need(n, 1, "dài")) return;
      if (sk[b] == K_MAP) { RI((<MObj>so[b]).ks.length); return; }
      let L = seqLen(b, "dài"); if (L >= 0) RI(L); return;
    }
    case 1: { // đầu
      if (!need(n, 1, "đầu")) return; let L = seqLen(b, "đầu"); if (L < 0) return;
      if (L == 0) { err("đầu của danh_sách rỗng"); return; }
      if (sk[b] == K_LIST) { let l = <LObj>so[b]; R(l.k[0], l.v[0], l.o[0]); } else RS(cpAt(<SObj>so[b], 0));
      return;
    }
    case 2: { // đuôi
      if (!need(n, 1, "đuôi")) return; let L = seqLen(b, "đuôi"); if (L < 0) return;
      if (sk[b] == K_LIST) { let l = <LObj>so[b]; RO(K_LIST, copyList(l, L > 0 ? 1 : 0, L)); }
      else RO(K_LIST, strToList(strFrom(<SObj>so[b], 1)));
      return;
    }
    case 3: { // thêm
      if (!need(n, 2, "thêm")) return; let L = seqLen(b, "thêm"); if (L < 0) return;
      if (L + 1 > MAX_LIST) { limit("danh sách quá lớn"); return; }
      let r = sk[b] == K_LIST ? copyList(<LObj>so[b], 0, L) : strToList(<SObj>so[b]);
      r.push(sk[b + 1], sv[b + 1], so[b + 1]); RO(K_LIST, r); return;
    }
    case 4: { // ghép
      if (!need(n, 2, "ghép")) return;
      if (sk[b] == K_LIST && sk[b + 1] == K_LIST) {
        let x = <LObj>so[b], y = <LObj>so[b + 1];
        if (x.length + y.length > MAX_LIST) { limit("danh sách quá lớn"); return; }
        let r = copyList(x, 0, x.length); for (let i = 0; i < y.length; i++) r.push(y.k[i], y.v[i], y.o[i]);
        RO(K_LIST, r); return;
      }
      let s = render(sk[b], sv[b], so[b]) + render(sk[b + 1], sv[b + 1], so[b + 1]);
      if (s.length > MAX_STR) { limit("chuỗi quá lớn"); return; }
      RS(s); return;
    }
    case 5: { // gom
      if (!need(n, 2, "gom")) return; let l = listOf(b);
      if (l === null) { err("gom cần danh_sách, gặp " + loai(sk[b], so[b])); return; }
      if (l.length + 1 > MAX_LIST) { limit("danh sách quá lớn"); return; }
      l.push(sk[b + 1], sv[b + 1], so[b + 1]); RO(K_LIST, l); return;
    }
    case 6: { // đảo
      if (!need(n, 1, "đảo")) return; let L = seqLen(b, "đảo"); if (L < 0) return;
      let src = sk[b] == K_LIST ? <LObj>so[b] : strToList(<SObj>so[b]);
      let r = new LObj(); for (let i = L - 1; i >= 0; i--) r.push(src.k[i], src.v[i], src.o[i]);
      RO(K_LIST, r); return;
    }
    case 7: { // nối
      if (!need(n, 2, "nối")) return; let l = listOf(b);
      if (l === null) { err("nối cần danh_sách, gặp " + loai(sk[b], so[b])); return; }
      let sep = render(sk[b + 1], sv[b + 1], so[b + 1]); let s = "";
      for (let i = 0; i < l.length; i++) { if (i > 0) s += sep; s += render(l.k[i], l.v[i], l.o[i]); if (s.length > MAX_STR) { limit("chuỗi quá lớn"); return; } }
      RS(s); return;
    }
    case 8: { // tách
      if (!need(n, 2, "tách")) return;
      if (sk[b] != K_STR || sk[b + 1] != K_STR) { err("tách cần (chuỗi, chuỗi ngăn)"); return; }
      let sep = (<SObj>so[b + 1]).s; if (sep.length == 0) { err("tách: ký tự ngăn rỗng"); return; }
      let parts = (<SObj>so[b]).s.split(sep); let r = new LObj();
      for (let i = 0; i < parts.length; i++) r.push(K_STR, 0, new SObj(parts[i]));
      RO(K_LIST, r); return;
    }
    case 9: { if (!need(n, 1, "là_ds")) return; RT(sk[b] == K_LIST); return; }
    case 10: { if (!need(n, 1, "là_số")) return; RT(isNum(sk[b])); return; }
    case 11: { // rọi_ds
      if (!need(n, 1, "rọi_ds")) return; let l = listOf(b);
      if (l === null) { err("rọi_ds cần danh_sách, gặp " + loai(sk[b], so[b])); return; }
      for (let i = 0; i < l.length; i++) write("   " + render(l.k[i], l.v[i], l.o[i]) + "\n");
      RA(); return;
    }
    case 12: { if (!need(n, 1, "loại")) return; RS(loai(sk[b], so[b])); return; }
    case 13: { // nguyên
      if (!need(n, 1, "nguyên")) return;
      if (sk[b] == K_INT || sk[b] == K_BIG) { R(sk[b], sv[b], so[b]); return; }
      if (sk[b] != K_F64) { err("nguyên cần số, gặp " + loai(sk[b], so[b])); return; }
      let x = Math.floor(reinterpret<f64>(sv[b]));
      if (!isFinite(x)) { err("nguyên: không đổi được vô cực/NaN"); return; }
      if (Math.abs(x) < 9.2e18) { RI(<i64>x); return; }
      let neg = x < 0; let ax = neg ? -x : x; let m = new Array<u32>();   // số thực nguyên lớn → số lớn chính xác
      while (ax >= 1) { let r = ax % 4294967296.0; m.push(<u32>r); ax = (ax - r) / 4294967296.0; }
      pushBig(neg, m); sp--; R(sk[sp], sv[sp], so[sp]); return;
    }
    case 14: { // mã
      if (!need(n, 1, "mã")) return;
      if (sk[b] != K_STR || (<SObj>so[b]).s.length < 1) { err("mã cần CHUỖI ≥1 ký-tự"); return; }
      RI((<SObj>so[b]).s.codePointAt(0)); return;
    }
    case 15: { // ký_tự
      if (!need(n, 1, "ký_tự")) return;
      if (sk[b] != K_INT) { err("ký_tự cần SỐ NGUYÊN"); return; }
      let c = sv[b]; if (c < 0) c = 0; if (c > 0x10FFFF) c = 0x10FFFF;
      RS(String.fromCodePoint(<i32>c)); return;
    }
    // ---------- phép bit ----------
    case 16: case 17: case 18: { // xor · và_bit · hoặc_bit
      let who = id == 16 ? "xor" : (id == 17 ? "và_bit" : "hoặc_bit");
      if (!need(n, 2, who)) return;
      if (sk[b] == K_AN || sk[b + 1] == K_AN) { RA(); return; }
      let a1 = sk[b] == K_INT || sk[b] == K_BIG, a2 = sk[b + 1] == K_INT || sk[b + 1] == K_BIG;
      if (!a1 || !a2) { err(who + " cần SỐ NGUYÊN, gặp " + loai(!a1 ? sk[b] : sk[b + 1], null)); return; }
      if (sk[b] == K_INT && sk[b + 1] == K_INT) { let x = sv[b], y = sv[b + 1]; RI(id == 16 ? (x ^ y) : (id == 17 ? (x & y) : (x | y))); return; }
      bigBit(id == 17 ? 0 : (id == 18 ? 1 : 2), sk[b], sv[b], so[b], sk[b + 1], sv[b + 1], so[b + 1]); sp--; R(sk[sp], sv[sp], so[sp]); return;
    }
    case 19: { // đảo_bit
      if (!need(n, 1, "đảo_bit")) return; if (sk[b] == K_AN) { RA(); return; }
      if (sk[b] == K_BIG) { let q = <BObj>so[b]; let one = magFromU64(1);   // ~x = −x − 1
        if (q.neg) { pushBig(false, magSub(q.m, one)); } else { pushBig(true, magAdd(q.m, one)); } sp--; R(sk[sp], sv[sp], so[sp]); return; }
      if (sk[b] != K_INT) { err("đảo_bit cần SỐ NGUYÊN, gặp " + loai(sk[b], so[b])); return; }
      RI(~sv[b]); return;
    }
    case 20: { // dịch_trái
      if (!need(n, 2, "dịch_trái")) return; if (sk[b] == K_AN || sk[b + 1] == K_AN) { RA(); return; }
      if (!(sk[b] == K_INT || sk[b] == K_BIG) || sk[b + 1] != K_INT) { err("dịch_trái cần SỐ NGUYÊN"); return; }
      let s = sv[b + 1]; if (s < 0) { err("dịch_trái: số bit dịch phải ≥ 0"); return; }
      if (sk[b] == K_INT) { let x = sv[b]; if (x == 0) { RI(0); return; } if (s < 63) { let r = x << s; if ((r >> s) == x) { RI(r); return; } } }
      toMag(sk[b], sv[b], so[b]);
      if (<i64>tMag.length * 32 + s > 8000000) { limit("dịch_trái: số quá lớn"); return; }
      pushBig(tNeg, magShl(tMag, <i32>s)); sp--; R(sk[sp], sv[sp], so[sp]); return;
    }
    case 21: { // dịch_phải
      if (!need(n, 2, "dịch_phải")) return; if (sk[b] == K_AN || sk[b + 1] == K_AN) { RA(); return; }
      if (!(sk[b] == K_INT || sk[b] == K_BIG) || sk[b + 1] != K_INT) { err("dịch_phải cần SỐ NGUYÊN"); return; }
      let s = sv[b + 1]; if (s < 0) { err("dịch_phải: số bit dịch phải ≥ 0"); return; }
      if (sk[b] == K_INT) { let x = sv[b]; RI(s >= 63 ? (x < 0 ? -1 : 0) : (x >> s)); return; }
      let q = <BObj>so[b];                                           // số âm: dịch sàn (Python) = −((|x|−1) >> s) − 1
      if (!q.neg) { pushBig(false, magShr(q.m, <i32>(s > 2000000000 ? 2000000000 : s))); }
      else { let t = magShr(magSub(q.m, magFromU64(1)), <i32>(s > 2000000000 ? 2000000000 : s)); pushBig(true, magAdd(t, magFromU64(1))); }
      sp--; R(sk[sp], sv[sp], so[sp]); return;
    }
    // ---------- toán ----------
    case 22: { if (!need(n, 1, "log")) return; if (sk[b] == K_AN) { RA(); return; } let x = farg(b, "log"); if (loi) return; RF(Math.log(x < 1e-12 ? 1e-12 : x)); return; }
    case 23: { if (!need(n, 1, "mũ")) return; if (sk[b] == K_AN) { RA(); return; } let x = farg(b, "mũ"); if (loi) return; RF(Math.exp(x)); return; }
    case 24: { if (!need(n, 1, "căn")) return; if (sk[b] == K_AN) { RA(); return; } let x = farg(b, "căn"); if (loi) return; RF(Math.sqrt(x < 0 ? 0 : x)); return; }
    // ---------- bản ----------
    case 25: { if (!need(n, 0, "bản")) return; RO(K_MAP, new MObj()); return; }
    case 26: { // đặt_khoá
      if (!need(n, 3, "đặt_khoá")) return;
      if (sk[b] == K_AN) { RA(); return; }
      if (sk[b] != K_MAP) { err("đặt_khoá cần bản, gặp " + loai(sk[b], so[b])); return; }
      if (sk[b + 1] == K_AN) { RO(K_MAP, <Obj>so[b]); return; }
      if (!(isNum(sk[b + 1]) || sk[b + 1] == K_STR)) { err("khoá bản phải là số/chuỗi/trị, gặp " + loai(sk[b + 1], so[b + 1])); return; }
      indexWrite(K_MAP, so[b], sk[b + 1], sv[b + 1], so[b + 1], sk[b + 2], sv[b + 2], so[b + 2]);
      RO(K_MAP, <Obj>so[b]); return;
    }
    case 27: { // lấy_khoá
      if (!need(n, 2, "lấy_khoá")) return;
      if (sk[b] == K_AN) { RA(); return; }
      if (sk[b] != K_MAP) { err("lấy_khoá cần bản, gặp " + loai(sk[b], so[b])); return; }
      if (sk[b + 1] == K_AN) { RA(); return; }
      if (!(isNum(sk[b + 1]) || sk[b + 1] == K_STR)) { err("khoá bản phải là số/chuỗi/trị, gặp " + loai(sk[b + 1], so[b + 1])); return; }
      let m = <MObj>so[b]; let key = mapKey(sk[b + 1], sv[b + 1], so[b + 1]);
      if (m.idx.has(key)) { let j = m.idx.get(key); R(m.vs.k[j], m.vs.v[j], m.vs.o[j]); } else RA();
      return;
    }
    case 28: { // có_khoá
      if (!need(n, 2, "có_khoá")) return;
      if (sk[b] == K_AN) { RA(); return; }
      if (sk[b] != K_MAP) { err("có_khoá cần bản, gặp " + loai(sk[b], so[b])); return; }
      if (sk[b + 1] == K_AN) { RT(false); return; }
      if (!(isNum(sk[b + 1]) || sk[b + 1] == K_STR)) { err("khoá bản phải là số/chuỗi/trị, gặp " + loai(sk[b + 1], so[b + 1])); return; }
      RT((<MObj>so[b]).idx.has(mapKey(sk[b + 1], sv[b + 1], so[b + 1]))); return;
    }
    case 29: { // xoá_khoá
      if (!need(n, 2, "xoá_khoá")) return;
      if (sk[b] == K_AN) { RA(); return; }
      if (sk[b] != K_MAP) { err("xoá_khoá cần bản, gặp " + loai(sk[b], so[b])); return; }
      let m = <MObj>so[b];
      if (sk[b + 1] == K_AN) { RO(K_MAP, m); return; }
      if (!(isNum(sk[b + 1]) || sk[b + 1] == K_STR)) { err("khoá bản phải là số/chuỗi/trị, gặp " + loai(sk[b + 1], so[b + 1])); return; }
      let key = mapKey(sk[b + 1], sv[b + 1], so[b + 1]);
      if (m.idx.has(key)) {
        let j = m.idx.get(key); let nk = new LObj(), nv = new LObj();
        for (let i = 0; i < m.ks.length; i++) if (i != j) { nk.push(m.ks.k[i], m.ks.v[i], m.ks.o[i]); nv.push(m.vs.k[i], m.vs.v[i], m.vs.o[i]); }
        m.ks = nk; m.vs = nv; m.idx = new Map<string, i32>();
        for (let i = 0; i < nk.length; i++) m.idx.set(mapKey(nk.k[i], nk.v[i], nk.o[i]), i);
      }
      RO(K_MAP, m); return;
    }
    case 30: { if (!need(n, 1, "khoá")) return; if (sk[b] != K_MAP) { err("khoá cần bản, gặp " + loai(sk[b], so[b])); return; } let m = <MObj>so[b]; RO(K_LIST, copyList(m.ks, 0, m.ks.length)); return; }
    case 31: { if (!need(n, 1, "giá_trị")) return; if (sk[b] != K_MAP) { err("giá_trị cần bản, gặp " + loai(sk[b], so[b])); return; } let m = <MObj>so[b]; RO(K_LIST, copyList(m.vs, 0, m.vs.length)); return; }
    // ---------- tri ----------
    case 32: { // tạo_tri
      if (!need(n, 2, "tạo_tri")) return;
      let t = new TObj();
      if (sk[b] == K_AN || sk[b + 1] == K_AN) { RO(K_TRI, t); return; }
      if (!isNum(sk[b + 1])) { err("tạo_tri cần γ là số, gặp " + loai(sk[b + 1], so[b + 1])); return; }
      let g = asF(sk[b + 1], sv[b + 1]); if (g > 1) g = 1; if (g < -1) g = -1;
      if (g == 0) { RO(K_TRI, t); return; }
      t.k = sk[b]; t.v = sv[b]; t.o = so[b]; t.g = g; t.st = g > 0 ? 1 : 2; RO(K_TRI, t); return;
    }
    case 33: { // γ_của
      if (!need(n, 1, "γ_của")) return;
      if (sk[b] == K_TRI && (<TObj>so[b]).st != 0) { RF((<TObj>so[b]).g); return; }
      RA(); return;
    }
    case 34: { // giờ_hệ (năng lực — chỉ khi host cấp)
      if (!coGio) { err("tên 'giờ_hệ' chưa định nghĩa"); return; }
      if (!need(n, 0, "giờ_hệ")) return; RF(host_gio_he()); return;
    }
    case 35: { // cộng_hưởng(σ, ρ)
      if (!need(n, 2, "cộng_hưởng")) return;
      if (sk[b] == K_AN || sk[b + 1] == K_AN) { RA(); return; }
      if (isNum(sk[b]) && isNum(sk[b + 1])) { RF(skillGamma(rScalar(sk[b], sv[b], so[b], sk[b + 1], sv[b + 1], so[b + 1]), GAMMA_NEN)); return; }
      if (sk[b] == K_LIST && sk[b + 1] == K_LIST) {
        let x = <LObj>so[b], y = <LObj>so[b + 1];
        if (x.length != y.length || x.length == 0) { RF(-1.0); return; }
        for (let i = 0; i < x.length; i++) if (!isNum(x.k[i]) || !isNum(y.k[i])) { err("cộng_hưởng vector cần số"); return; }
        let dot: f64 = 0, na: f64 = 0, nb: f64 = 0;
        for (let i = 0; i < x.length; i++) dot += asFO(x.k[i], x.v[i], x.o[i]) * asFO(y.k[i], y.v[i], y.o[i]);
        for (let i = 0; i < x.length; i++) { let q = asFO(x.k[i], x.v[i], x.o[i]); na += q * q; }
        for (let i = 0; i < y.length; i++) { let q = asFO(y.k[i], y.v[i], y.o[i]); nb += q * q; }
        na = Math.sqrt(na); nb = Math.sqrt(nb);
        if (na == 0 || nb == 0) { RF(-1.0); return; }
        let c = dot / (na * nb); if (c > 1) c = 1; if (c < -1) c = -1;
        RF(skillGamma(Math.exp(c - 1.0), GAMMA_NEN)); return;
      }
      RF(pyEq(sk[b], sv[b], so[b], sk[b + 1], sv[b + 1], so[b + 1]) ? 1.0 : -1.0); return;
    }
    case 36: { // cộng_hưởng_thô(σ, ρ) = R ∈ (0,1]
      if (!need(n, 2, "cộng_hưởng_thô")) return;
      if (sk[b] == K_AN || sk[b + 1] == K_AN) { RA(); return; }
      if (!isNum(sk[b]) || !isNum(sk[b + 1])) { err("cộng_hưởng_thô cần số"); return; }
      RF(rScalar(sk[b], sv[b], so[b], sk[b + 1], sv[b + 1], so[b + 1])); return;
    }
    case 37: { // γ_kỹ_năng(R_tin, R_nền)
      if (!need(n, 2, "γ_kỹ_năng")) return;
      if (sk[b] == K_AN || sk[b + 1] == K_AN) { RA(); return; }
      let a = farg(b, "γ_kỹ_năng"), c = farg(b + 1, "γ_kỹ_năng"); if (loi) return;
      RF(skillGamma(a, c)); return;
    }
    case 38: { // cam_kết(ds_độ_tán[, std0]) — F.11-N: TRUNG BÌNH theo chiều
      if (n < 1 || sk[b] != K_LIST) { err("cam_kết cần danh sách độ-tán"); return; }
      let std0: f64 = 1.0; if (n > 1 && isNum(sk[b + 1])) std0 = asFO(sk[b + 1], sv[b + 1], so[b + 1]);
      let l = <LObj>so[b]; if (l.length == 0) { RF(0.0); return; }
      let t: f64 = 0;
      for (let i = 0; i < l.length; i++) {
        if (!isNum(l.k[i])) { err("cam_kết cần số"); return; }
        let x = asFO(l.k[i], l.v[i], l.o[i]); t += Math.log(std0 / (x < 1e-9 ? 1e-9 : x));
      }
      t = t / <f64>l.length; if (t < 0) t = 0.0;
      RF(t / (1.0 + t)); return;
    }
    case 39: { // bỏ_dấu
      if (!need(n, 1, "bỏ_dấu")) return;
      if (sk[b] != K_STR) { err("bỏ_dấu cần chuỗi, gặp " + loai(sk[b], so[b])); return; }
      RS(boDau((<SObj>so[b]).s)); return;
    }
    case 60: case 61: case 62: { // tim / nhúng / nhịp_tim — cần LLM qua MẠNG
      err("'" + (id == 60 ? "tim" : (id == 61 ? "nhúng" : "nhịp_tim")) + "' cần năng lực LLM qua mạng — GVM-64 chạy trong hộp cát WASI không có mạng (chạy bằng giao.py)");
      return;
    }
    // ---------- mảng (lệnh khối) ----------
    case 40: { if (!need(n, 0, "mảng_sẵn")) return; RT(true); return; }
    case 41: { // mảng_không
      if (!need(n, 1, "mảng_không")) return; let N = iarg(b, "mảng_không"); if (loi) return;
      if (N < 0 || N > (1 << 30)) { err("mảng_không: cỡ mảng phải trong 0.." + (1 << 30).toString()); return; }
      RO(K_MANG, mkMang(<i32>N)); return;
    }
    case 42: { // mảng_từ
      if (!need(n, 2, "mảng_từ")) return; let a = listOf(b), c = listOf(b + 1);
      if (a === null || c === null || a.length != c.length) { err("mảng_từ cần (ds_thực, ds_ảo) cùng độ dài"); return; }
      let m = mkMang(a.length);
      for (let i = 0; i < a.length; i++) {
        if (!isNum(a.k[i]) || !isNum(c.k[i])) { err("mảng_từ cần số"); return; }
        m.re[i] = asF(a.k[i], a.v[i]); m.im[i] = asF(c.k[i], c.v[i]);
      }
      RO(K_MANG, m); return;
    }
    case 43: { if (!need(n, 1, "m_dài")) return; let m = mảng(b, "m_dài"); if (m === null) return; RI(m.re.length); return; }
    case 44: { // m_lấy
      if (!need(n, 2, "m_lấy")) return; let m = mảng(b, "m_lấy"); if (m === null) return; let k = iarg(b + 1, "m_lấy"); if (loi) return;
      if (k < 0 || k >= m.re.length) { err("m_lấy: chỉ số " + k.toString() + " ngoài 0.." + (m.re.length - 1).toString()); return; }
      let l = new LObj(); l.push(K_F64, reinterpret<i64>(m.re[<i32>k]), null); l.push(K_F64, reinterpret<i64>(m.im[<i32>k]), null);
      RO(K_LIST, l); return;
    }
    case 45: { // m_gán
      if (!need(n, 3, "m_gán")) return; let m = mảng(b, "m_gán"); if (m === null) return; let k = iarg(b + 1, "m_gán"); if (loi) return;
      if (k < 0 || k >= m.re.length) { err("m_gán: chỉ số " + k.toString() + " ngoài 0.." + (m.re.length - 1).toString()); return; }
      if (!carg(b + 2, "m_gán")) return; m.re[<i32>k] = czr; m.im[<i32>k] = czi; RO(K_MANG, m); return;
    }
    case 46: { // m_sao
      if (!need(n, 1, "m_sao")) return; let m = mảng(b, "m_sao"); if (m === null) return;
      let c = mkMang(m.re.length); c.re.set(m.re); c.im.set(m.im); RO(K_MANG, c); return;
    }
    case 47: { // m_sang_ds
      if (!need(n, 1, "m_sang_ds")) return; let m = mảng(b, "m_sang_ds"); if (m === null) return;
      if (m.re.length > MAX_LIST) { limit("danh sách quá lớn (" + m.re.length.toString() + " > trần " + MAX_LIST.toString() + "; nới bằng --trần-ds)"); return; }
      let a = new LObj(), c = new LObj();
      for (let i = 0; i < m.re.length; i++) { a.push(K_F64, reinterpret<i64>(m.re[i]), null); c.push(K_F64, reinterpret<i64>(m.im[i]), null); }
      let r = new LObj(); r.push(K_LIST, 0, a); r.push(K_LIST, 0, c); RO(K_LIST, r); return;
    }
    case 48: { // m_chọn
      if (!need(n, 3, "m_chọn")) return; let m = mảng(b, "m_chọn"); if (m === null) return;
      let sel = iarg(b + 1, "m_chọn"); let mau = iarg(b + 2, "m_chọn"); if (loi) return;
      if (!checkMask(m.re.length, sel, mau, "m_chọn")) return;
      let ix = forSel(m.re.length, <i32>sel, <i32>mau); let r = mkMang(ix.length);
      for (let j = 0; j < ix.length; j++) { r.re[j] = m.re[ix[j]]; r.im[j] = m.im[ix[j]]; }
      RO(K_MANG, r); return;
    }
    case 49: { // m_đặt_chọn
      if (!need(n, 4, "m_đặt_chọn")) return; let m = mảng(b, "m_đặt_chọn"); if (m === null) return;
      let sel = iarg(b + 1, "m_đặt_chọn"); let mau = iarg(b + 2, "m_đặt_chọn"); if (loi) return;
      if (!checkMask(m.re.length, sel, mau, "m_đặt_chọn")) return;
      let x = mảng(b + 3, "m_đặt_chọn"); if (x === null) return;
      let can = m.re.length >> bitCount(sel);
      if (x.re.length != can) { err("m_đặt_chọn: cần " + can.toString() + " phần tử, gặp " + x.re.length.toString()); return; }
      let ix = forSel(m.re.length, <i32>sel, <i32>mau);
      for (let j = 0; j < ix.length; j++) { m.re[ix[j]] = x.re[j]; m.im[ix[j]] = x.im[j]; }
      RO(K_MANG, m); return;
    }
    case 50: { // m_tổ_hợp  α·a + β·b  (phép nhân phức đúng thứ tự CPython)
      if (!need(n, 4, "m_tổ_hợp")) return; let x = mảng(b, "m_tổ_hợp"); if (x === null) return;
      let y = mảng(b + 1, "m_tổ_hợp"); if (y === null) return;
      if (x.re.length != y.re.length) { err("m_tổ_hợp: hai mảng khác độ dài"); return; }
      if (!carg(b + 2, "m_tổ_hợp")) return; let ar = czr, ai = czi;
      if (!carg(b + 3, "m_tổ_hợp")) return; let br = czr, bi = czi;
      let N = x.re.length; let r = mkMang(N);
      for (let i = 0; i < N; i++) {
        let xr = x.re[i], xi = x.im[i], yr = y.re[i], yi = y.im[i];
        r.re[i] = (ar * xr - ai * xi) + (br * yr - bi * yi);
        r.im[i] = (ar * xi + ai * xr) + (br * yi + bi * yr);
      }
      RO(K_MANG, r); return;
    }
    case 51: { // m_nhân_số
      if (!need(n, 2, "m_nhân_số")) return; let x = mảng(b, "m_nhân_số"); if (x === null) return;
      if (!carg(b + 1, "m_nhân_số")) return; let zr = czr, zi = czi;
      let N = x.re.length; let r = mkMang(N);
      for (let i = 0; i < N; i++) { let xr = x.re[i], xi = x.im[i]; r.re[i] = zr * xr - zi * xi; r.im[i] = zr * xi + zi * xr; }
      RO(K_MANG, r); return;
    }
    case 52: { // m_biến_đổi_cặp(m, t, mặt_nạ, u) — TẠI CHỖ, vòng native
      if (!need(n, 4, "m_biến_đổi_cặp")) return; let m = mảng(b, "m_biến_đổi_cặp"); if (m === null) return;
      let N = m.re.length; let t = iarg(b + 1, "m_biến_đổi_cặp"); let mask = iarg(b + 2, "m_biến_đổi_cặp"); if (loi) return;
      let ul = listOf(b + 3);
      if (ul === null || ul.length != 8) { err("m_biến_đổi_cặp: ma trận 2×2 phức phải là danh sách 8 số"); return; }
      for (let q = 0; q < 8; q++) if (!isNum(ul.k[q])) { err("m_biến_đổi_cặp cần số"); return; }
      if ((N & (N - 1)) != 0 || t < 0 || (<i64>1 << t) >= N) { err("m_biến_đổi_cặp: bit " + t.toString() + " ngoài mảng dài " + N.toString()); return; }
      if (mask < 0 || mask >= N || (mask & (<i64>1 << t)) != 0) { err("m_biến_đổi_cặp: mặt nạ sai (ngoài phạm vi hoặc chứa bit t)"); return; }
      let ar = asF(ul.k[0], ul.v[0]), ai = asF(ul.k[1], ul.v[1]), br = asF(ul.k[2], ul.v[2]), bi = asF(ul.k[3], ul.v[3]);
      let cr = asF(ul.k[4], ul.v[4]), ci = asF(ul.k[5], ul.v[5]), dr = asF(ul.k[6], ul.v[6]), di = asF(ul.k[7], ul.v[7]);
      let bt = 1 << <i32>t; let mk = <i32>mask; let re = m.re, im = m.im;
      if (mk == 0) {
        for (let base = 0; base < N; base += 2 * bt) {
          for (let i = base; i < base + bt; i++) {
            let j = i + bt;
            let xr = unchecked(re[i]), xi = unchecked(im[i]), yr = unchecked(re[j]), yi = unchecked(im[j]);
            unchecked(re[i] = (ar * xr - ai * xi) + (br * yr - bi * yi)); unchecked(im[i] = (ar * xi + ai * xr) + (br * yi + bi * yr));
            unchecked(re[j] = (cr * xr - ci * xi) + (dr * yr - di * yi)); unchecked(im[j] = (cr * xi + ci * xr) + (dr * yi + di * yr));
          }
        }
        RO(K_MANG, m); return;
      }
      // có điều khiển: chỉ duyệt các i có bit t = 0 và mọi bit điều khiển = 1 (liệt kê bit TỰ DO)
      let selc = mk | bt; let free = (N - 1) & ~selc;
      for (let t2 = 0; ; t2 = ((t2 | selc) + 1) & ~selc) {
        {
          let i = t2 | mk;
          let j = i + bt;
          let xr = re[i], xi = im[i], yr = re[j], yi = im[j];
          re[i] = (ar * xr - ai * xi) + (br * yr - bi * yi); im[i] = (ar * xi + ai * xr) + (br * yi + bi * yr);
          re[j] = (cr * xr - ci * xi) + (dr * yr - di * yi); im[j] = (cr * xi + ci * xr) + (dr * yi + di * yr);
        }
        if (t2 == free) break;
      }
      RO(K_MANG, m); return;
    }
    case 53: { // m_nhân_chọn(m, sel, mẫu, z) — TẠI CHỖ
      if (!need(n, 4, "m_nhân_chọn")) return; let m = mảng(b, "m_nhân_chọn"); if (m === null) return;
      let sel = iarg(b + 1, "m_nhân_chọn"); let mau = iarg(b + 2, "m_nhân_chọn"); if (loi) return;
      if (!checkMask(m.re.length, sel, mau, "m_nhân_chọn")) return;
      if (!carg(b + 3, "m_nhân_chọn")) return; let zr = czr, zi = czi;
      let N = m.re.length; let s = <i32>sel, mu = <i32>mau; let re = m.re, im = m.im; let free = (N - 1) & ~s;
      for (let t = 0; ; t = ((t | s) + 1) & ~s) {                  // t chạy qua mọi tổ hợp bit TỰ DO, tăng dần
        let i = t | mu;
        if (zr == 0 && zi == 0) { unchecked(re[i] = 0); unchecked(im[i] = 0); }
        else { let xr = unchecked(re[i]), xi = unchecked(im[i]); unchecked(re[i] = zr * xr - zi * xi); unchecked(im[i] = zr * xi + zi * xr); }
        if (t == free) break;
      }
      RO(K_MANG, m); return;
    }
    case 54: { // m_đổi_chọn(m, sel, mẫu1, mẫu2) — hoán vị thuần
      if (!need(n, 4, "m_đổi_chọn")) return; let m = mảng(b, "m_đổi_chọn"); if (m === null) return;
      let sel = iarg(b + 1, "m_đổi_chọn"); let m1 = iarg(b + 2, "m_đổi_chọn"); let m2 = iarg(b + 3, "m_đổi_chọn"); if (loi) return;
      if (!checkMask(m.re.length, sel, m1, "m_đổi_chọn")) return;
      if (!checkMask(m.re.length, sel, m2, "m_đổi_chọn")) return;
      if (m1 != m2) {
        let N = m.re.length; let s = <i32>sel, a = <i32>m1, c = <i32>m2; let re = m.re, im = m.im;
        // cặp thứ t của hai tập = cùng các bit TỰ DO ⇒ j = (i & ~sel) | m2
        let free = (N - 1) & ~s;
        for (let t = 0; ; t = ((t | s) + 1) & ~s) {
          let i = t | a, j = t | c;
          let tr = unchecked(re[i]), ti = unchecked(im[i]);
          unchecked(re[i] = re[j]); unchecked(im[i] = im[j]); unchecked(re[j] = tr); unchecked(im[j] = ti);
          if (t == free) break;
        }
      }
      RO(K_MANG, m); return;
    }
    case 55: { // m_tổng_mô2_chọn — cộng dồn THEO KHÚC như giao_mang.py (khớp từng bit)
      if (!need(n, 3, "m_tổng_mô2_chọn")) return; let m = mảng(b, "m_tổng_mô2_chọn"); if (m === null) return;
      let sel = iarg(b + 1, "m_tổng_mô2_chọn"); let mau = iarg(b + 2, "m_tổng_mô2_chọn"); if (loi) return;
      if (!checkMask(m.re.length, sel, mau, "m_tổng_mô2_chọn")) return;
      let N = m.re.length; let Wn = N < W_KHUC ? N : W_KHUC; let s = <i32>sel, mu = <i32>mau;
      let cao = s & ~(Wn - 1), mc = mu & ~(Wn - 1), thap = s & (Wn - 1), mt = mu & (Wn - 1);
      let tong: f64 = 0;
      for (let w = 0; w < N; w += Wn) {
        if ((w & cao) != mc) continue;
        let a: f64 = 0; for (let i = 0; i < Wn; i++) if ((i & thap) == mt) { let x = m.re[w + i]; a += x * x; }
        tong += a;
        let c: f64 = 0; for (let i = 0; i < Wn; i++) if ((i & thap) == mt) { let x = m.im[w + i]; c += x * x; }
        tong += c;
      }
      RF(tong); return;
    }
    case 56: { // m_tổng_mô2
      if (!need(n, 1, "m_tổng_mô2")) return; let m = mảng(b, "m_tổng_mô2"); if (m === null) return;
      let s: f64 = 0; for (let i = 0; i < m.re.length; i++) s += m.re[i] * m.re[i] + m.im[i] * m.im[i];
      RF(s); return;
    }
    case 57: { // m_mô2_ds
      if (!need(n, 1, "m_mô2_ds")) return; let m = mảng(b, "m_mô2_ds"); if (m === null) return;
      if (m.re.length > MAX_LIST) { limit("danh sách quá lớn (" + m.re.length.toString() + " > trần " + MAX_LIST.toString() + "; nới bằng --trần-ds)"); return; }
      let r = new LObj(); for (let i = 0; i < m.re.length; i++) r.push(K_F64, reinterpret<i64>(m.re[i] * m.re[i] + m.im[i] * m.im[i]), null);
      RO(K_LIST, r); return;
    }
    case 58: { // m_tích_trong
      if (!need(n, 2, "m_tích_trong")) return; let x = mảng(b, "m_tích_trong"); if (x === null) return;
      let y = mảng(b + 1, "m_tích_trong"); if (y === null) return;
      if (x.re.length != y.re.length) { err("m_tích_trong: hai mảng khác độ dài"); return; }
      let tr: f64 = 0, ti: f64 = 0;
      for (let i = 0; i < x.re.length; i++) tr += x.re[i] * y.re[i] + x.im[i] * y.im[i];
      for (let i = 0; i < x.re.length; i++) ti += x.re[i] * y.im[i] - x.im[i] * y.re[i];
      let l = new LObj(); l.push(K_F64, reinterpret<i64>(tr), null); l.push(K_F64, reinterpret<i64>(ti), null); RO(K_LIST, l); return;
    }
    case 59: { // m_rút(m, ds_u)
      if (!need(n, 2, "m_rút")) return; let m = mảng(b, "m_rút"); if (m === null) return; let us = listOf(b + 1);
      if (us === null) { err("m_rút cần danh sách u ∈ [0,1)"); return; }
      let N = m.re.length; let don = new Float64Array(N); let s: f64 = 0;
      for (let i = 0; i < N; i++) { s += m.re[i] * m.re[i] + m.im[i] * m.im[i]; don[i] = s; }
      let r = new LObj();
      for (let q = 0; q < us.length; q++) {
        if (!isNum(us.k[q])) { err("m_rút cần số"); return; }
        let u = asF(us.k[q], us.v[q]); let lo = 0, hi = N;          // bisect_right
        while (lo < hi) { let mid = (lo + hi) >> 1; if (u < don[mid]) hi = mid; else lo = mid + 1; }
        r.push(K_INT, <i64>(lo < N - 1 ? lo : N - 1), null);
      }
      RO(K_LIST, r); return;
    }
    case 63: { // m_biến_đổi_bốn(m, a, b, U32) — ma trận 4×4 lên cặp qubit, TẠI CHỖ, MỘT lượt duyệt
      if (!need(n, 4, "m_biến_đổi_bốn")) return; let m = mảng(b, "m_biến_đổi_bốn"); if (m === null) return;
      let N = m.re.length; let qa = iarg(b + 1, "m_biến_đổi_bốn"); let qb = iarg(b + 2, "m_biến_đổi_bốn"); if (loi) return;
      let ul = listOf(b + 3);
      if (ul === null || ul.length != 32) { err("m_biến_đổi_bốn: ma trận 4×4 phức phải là danh sách 32 số"); return; }
      for (let q = 0; q < 32; q++) if (!isNum(ul.k[q])) { err("m_biến_đổi_bốn cần số"); return; }
      if ((N & (N - 1)) != 0 || qa == qb || qa < 0 || qb < 0 || (<i64>1 << qa) >= N || (<i64>1 << qb) >= N) {
        err("m_biến_đổi_bốn: cặp qubit (" + qa.toString() + ", " + qb.toString() + ") sai cho mảng dài " + N.toString()); return;
      }
      let u = new Float64Array(32); for (let q = 0; q < 32; q++) u[q] = asFO(ul.k[q], ul.v[q], ul.o[q]);
      let ba = 1 << <i32>qa, bb = 1 << <i32>qb; let sel = ba | bb; let free = (N - 1) & ~sel;
      let re = m.re, im = m.im;
      // 32 hệ số vào BIẾN CỤC BỘ (thanh ghi); cộng dồn từ 0.0 theo c = 0..3 như mọi lõi khác
      let a00r = u[0], a00i = u[1], a01r = u[2], a01i = u[3], a02r = u[4], a02i = u[5], a03r = u[6], a03i = u[7];
      let a10r = u[8], a10i = u[9], a11r = u[10], a11i = u[11], a12r = u[12], a12i = u[13], a13r = u[14], a13i = u[15];
      let a20r = u[16], a20i = u[17], a21r = u[18], a21i = u[19], a22r = u[20], a22i = u[21], a23r = u[22], a23i = u[23];
      let a30r = u[24], a30i = u[25], a31r = u[26], a31i = u[27], a32r = u[28], a32i = u[29], a33r = u[30], a33i = u[31];
      for (let t = 0; ; t = ((t | sel) + 1) & ~sel) {
        let i0 = t, i1 = t | ba, i2 = t | bb, i3 = t | sel;
        let x0r = unchecked(re[i0]), x0i = unchecked(im[i0]), x1r = unchecked(re[i1]), x1i = unchecked(im[i1]);
        let x2r = unchecked(re[i2]), x2i = unchecked(im[i2]), x3r = unchecked(re[i3]), x3i = unchecked(im[i3]);
        let sr: f64, si: f64;
        sr = 0.0; si = 0.0;
        sr = sr + (a00r * x0r - a00i * x0i); si = si + (a00r * x0i + a00i * x0r);
        sr = sr + (a01r * x1r - a01i * x1i); si = si + (a01r * x1i + a01i * x1r);
        sr = sr + (a02r * x2r - a02i * x2i); si = si + (a02r * x2i + a02i * x2r);
        sr = sr + (a03r * x3r - a03i * x3i); si = si + (a03r * x3i + a03i * x3r);
        unchecked(re[i0] = sr); unchecked(im[i0] = si);
        sr = 0.0; si = 0.0;
        sr = sr + (a10r * x0r - a10i * x0i); si = si + (a10r * x0i + a10i * x0r);
        sr = sr + (a11r * x1r - a11i * x1i); si = si + (a11r * x1i + a11i * x1r);
        sr = sr + (a12r * x2r - a12i * x2i); si = si + (a12r * x2i + a12i * x2r);
        sr = sr + (a13r * x3r - a13i * x3i); si = si + (a13r * x3i + a13i * x3r);
        unchecked(re[i1] = sr); unchecked(im[i1] = si);
        sr = 0.0; si = 0.0;
        sr = sr + (a20r * x0r - a20i * x0i); si = si + (a20r * x0i + a20i * x0r);
        sr = sr + (a21r * x1r - a21i * x1i); si = si + (a21r * x1i + a21i * x1r);
        sr = sr + (a22r * x2r - a22i * x2i); si = si + (a22r * x2i + a22i * x2r);
        sr = sr + (a23r * x3r - a23i * x3i); si = si + (a23r * x3i + a23i * x3r);
        unchecked(re[i2] = sr); unchecked(im[i2] = si);
        sr = 0.0; si = 0.0;
        sr = sr + (a30r * x0r - a30i * x0i); si = si + (a30r * x0i + a30i * x0r);
        sr = sr + (a31r * x1r - a31i * x1i); si = si + (a31r * x1i + a31i * x1r);
        sr = sr + (a32r * x2r - a32i * x2i); si = si + (a32r * x2i + a32i * x2r);
        sr = sr + (a33r * x3r - a33i * x3i); si = si + (a33r * x3i + a33i * x3r);
        unchecked(re[i3] = sr); unchecked(im[i3] = si);
        if (t == free) break;
      }
      RO(K_MANG, m); return;
    }
    default: err("builtin #" + id.toString() + " chưa có trên GVM-64");
  }
}

// ============================================================
// VÒNG THỰC THI
// ============================================================
let buoc: i64 = 0; let memLanDon: i32 = 0;
function raiseAt(): bool {                                    // có lỗi: gỡ-cuộn tới handler (nếu bắt được)
  if (!loi) return false;
  if (!loiGioiHan && hsp > 0) {
    hsp--; sp = hSp[hsp]; csp = hCsp[hsp]; frame = hFrame[hsp];
    loi = false; pushStr(loiMsg); ipNext = hAddr[hsp]; return false;
  }
  return true;                                                // không bắt → dừng máy
}
let ipNext = 0;

export function chay(): i32 {
  let ip = 0; frame = null; csp = 0; hsp = 0; sp = 0; loi = false; buoc = 0;
  while (true) {
    if (++buoc > MAX_STEPS) { limit("vượt " + MAX_STEPS.toString() + " bước máy (nghi vòng lặp vô tận)"); }
    if (loi) { ipNext = -1; if (raiseAt()) break; ip = ipNext; continue; }
    let w = code[ip++]; let op = w & 0xFF; let arg = w >> 8;
    switch (op) {
      case 0: {                                                               // DỪNG
        if (csp != 0) { err("máy gặp DỪNG khi còn " + csp.toString() + " khung gọi (ip=" + (ip - 1).toString() + ") — lỗi biên dịch"); break; }
        flush(); return 0;
      }
      case 1: pushInt(ipool[arg]); break;                                     // HẰNG_NGUYÊN
      case 2: pushInt(<i64>arg); break;                                       // SỐ_NHỎ
      case 3: pushF(fpool[arg]); break;                                       // HẰNG_THỰC
      case 4: pushObj(K_STR, spool[arg]); break;                              // HẰNG_CHUỖI
      case 5: pushAn(); break;                                                // ẨN
      case 6: loadName(arg); break;                                           // TẢI tên
      case 7: { sp--; let f = <Frame>frame; f.k[arg] = sk[sp]; f.v[arg] = sv[sp]; f.o[arg] = so[sp]; break; }   // GHI_CỤC_BỘ
      case 8: { sp--; gk[arg] = sk[sp]; gv[arg] = sv[sp]; go[arg] = so[sp]; break; }                              // GHI_TOÀN_CỤC
      case 9: sp--; break;                                                    // BỎ
      case 10: { push(sk[sp - 1], sv[sp - 1], so[sp - 1]); break; }           // NHÂN_BẢN
      case 11: case 12: case 13: case 14: case 15: case 16: case 17: case 18: case 19: case 20: case 21:
        binop(op); break;
      case 22: {                                                              // ĐỐI (−x)
        let k = sk[sp - 1];
        if (k == K_AN) break;
        if (k == K_INT) { if (sv[sp - 1] == i64.MIN_VALUE) { sp--; toMag(K_INT, sv[sp], null); pushBig(false, tMag); break; } sv[sp - 1] = -sv[sp - 1]; break; }
        if (k == K_BIG) { sp--; let b = <BObj>so[sp]; pushBig(!b.neg, b.m); break; }
        if (k == K_F64) { sv[sp - 1] = reinterpret<i64>(-reinterpret<f64>(sv[sp - 1])); break; }
        err("không thể lấy số đối của " + loai(k, so[sp - 1])); break;
      }
      case 23: {                                                              // CHỈ_MỤC
        sp--; let ik = sk[sp], iv = sv[sp], io = so[sp]; sp--; let ck = sk[sp], cv = sv[sp], co = so[sp];
        indexRead(ck, cv, co, ik, iv, io); break;
      }
      case 24: {                                                              // GÁN_CHỈ_MỤC (coll, idx, val)
        sp--; let vk = sk[sp], vv = sv[sp], vo = so[sp]; sp--; let ik = sk[sp], iv = sv[sp], io = so[sp];
        sp--; let ck = sk[sp], co = so[sp];
        indexWrite(ck, co, ik, iv, io, vk, vv, vo); break;
      }
      case 25: ip = arg; break;                                               // NHẢY
      case 26: {                                                              // RẼ_BA: sáng→tiếp · ẩn→arg · tối→từ kế
        sp--; let t = truthy3(sk[sp], sv[sp], so[sp]); let khac = code[ip++];
        if (t == 0) ip = arg; else if (t == 2) ip = khac; break;
      }
      case 27: {                                                              // GỌI n
        let n = arg; let ci = sp - n - 1; let ck = sk[ci];
        if (ck == K_FUNC) {
          let f = <FObj>so[ci]; let fi = f.fn;
          if (n != fnNParams[fi]) { err("hàm '" + (<SObj>spool[fnName[fi]]).s + "' cần " + fnNParams[fi].toString() + " đối, nhận " + n.toString()); break; }
          if (csp >= MAX_DEPTH) { limit("đệ quy quá sâu (>" + MAX_DEPTH.toString() + ")"); break; }
          let nf = new Frame(fnNSlots[fi], f.env);
          for (let q = 0; q < n; q++) { nf.k[q] = sk[ci + 1 + q]; nf.v[q] = sv[ci + 1 + q]; nf.o[q] = so[ci + 1 + q]; }
          for (let q = ci; q < sp; q++) so[q] = null;
          sp = ci;
          cRet[csp] = ip; cFrame[csp] = frame; csp++;
          frame = nf; ip = fnEntry[fi];
        } else if (ck == K_BUILTIN) {
          rk = K_AN; rv = 0; ro = null;
          builtin(<i32>sv[ci], ci + 1, n);
          for (let q = ci; q < sp; q++) so[q] = null;
          sp = ci; if (!loi) push(rk, rv, ro); ro = null;
        } else { err("không gọi được giá trị kiểu " + loai(ck, so[ci])); }
        break;
      }
      case 28: {                                                              // TRẢ_VỀ (giá trị ở đỉnh)
        sp--; let k = sk[sp], v = sv[sp], o = so[sp]; so[sp] = null;
        csp--; ip = cRet[csp]; frame = cFrame[csp]; cFrame[csp] = null;
        push(k, v, o); break;
      }
      case 29: { csp--; ip = cRet[csp]; frame = cFrame[csp]; cFrame[csp] = null; pushAn(); break; }   // TRẢ_ẨN
      case 30: pushObj(K_FUNC, new FObj(arg, frame)); break;                 // BAO_ĐÓNG
      case 31: { sp--; write(render(sk[sp], sv[sp], so[sp]) + "\n"); so[sp] = null; break; }   // RỌI
      case 32: {                                                              // DANH_SÁCH n
        if (arg > MAX_LIST) { limit("danh sách quá lớn"); break; }
        let l = new LObj(); for (let q = sp - arg; q < sp; q++) { l.push(sk[q], sv[q], so[q]); so[q] = null; }
        sp -= arg; pushObj(K_LIST, l); break;
      }
      case 33: {                                                              // DUYỆT_ĐẦU slot: chuẩn bị 'lặp x trong'
        sp--; let k = sk[sp], o = so[sp];
        if (k == K_AN) { slotSet(arg, K_AN, 0, null); slotSet(arg + 1, K_INT, 0, null); break; }
        if (k == K_STR) { slotSet(arg, K_LIST, 0, strToList(<SObj>o)); }
        else if (k == K_LIST) { slotSet(arg, K_LIST, 0, o); }
        else if (k == K_MAP) { let m = <MObj>o; slotSet(arg, K_LIST, 0, copyList(m.ks, 0, m.ks.length)); }
        else { err("lặp ... trong cần danh_sách/chuỗi/bản, gặp " + loai(k, o)); break; }
        slotSet(arg + 1, K_INT, 0, null); break;
      }
      case 34: {                                                              // DUYỆT_TIẾP slot (từ kế = địa chỉ thoát)
        let thoat = code[ip++];
        if (slotK(arg) != K_LIST) { ip = thoat; break; }
        let l = <LObj>slotO(arg); let i = slotV(arg + 1);
        if (i >= l.length) { ip = thoat; break; }                             // danh sách SỐNG (như Python)
        let j = <i32>i; push(l.k[j], l.v[j], l.o[j]); slotSet(arg + 1, K_INT, i + 1, null); break;
      }
      case 35: {                                                              // ĐẾM_ĐẦU slot: 'lặp N'
        sp--; let k = sk[sp], v = sv[sp];
        let c: i64 = 0;
        if (k == K_AN) c = 0;
        else if (k == K_INT) c = v;
        else if (k == K_F64) { let x = reinterpret<f64>(v); c = <i64>x; }
        else { err("lặp cần số lần là số, gặp " + loai(k, so[sp])); break; }
        slotSet(arg, K_INT, c, null); break;
      }
      case 36: {                                                              // ĐẾM_TIẾP slot (từ kế = thoát)
        let thoat = code[ip++]; let c = slotV(arg);
        if (c <= 0) { ip = thoat; break; }
        slotSet(arg, K_INT, c - 1, null); break;
      }
      case 37: {                                                              // THỬ (arg = địa chỉ bắt)
        hAddr[hsp] = arg; hSp[hsp] = sp; hCsp[hsp] = csp; hFrame[hsp] = frame; hsp++; break;
      }
      case 38: { hsp--; hFrame[hsp] = null; break; }                         // HẾT_THỬ
      case 39: { err((<SObj>spool[arg]).s); break; }                          // NÉM thông điệp hằng
      case 40: { let q = bigFromDec((<SObj>spool[arg]).s); pushBig(q.neg, q.m); break; }   // HẰNG_LỚN
      default: { err("mã lệnh lạ " + op.toString()); }
    }
    if (loi) { ipNext = -1; if (raiseAt()) break; ip = ipNext; }
  }
  flush();
  ghiChuoi(2, (loiGioiHan ? "[GIAO chặn — an toàn] " : "[GIAO lỗi] ") + loiMsg + "\n");
  return 1;
}

// ============================================================
// NẠP CHƯƠNG TRÌNH TỪ STDIN (định dạng nhị phân .g64, little-endian) + ĐỐI DÒNG LỆNH
//   "G64" 1 · u32 nMã, i32[] · u32 nNguyên, i64[] · u32 nThực, f64[] · u32 nChuỗi, {u32 n, u32[] mã-điểm}
//   · u32 nHàm, {i32 vào, số_tham, số_ô, tên, repr} · u32 nChuỗiTên, {i32 đầu, dài, tên} · u32 nMục, i32[]
//   · u32 nToànCục · u32 nDựngSẵn, {i32 ô, mã}
// ============================================================
let inBuf = new Uint8Array(0); let inPos = 0;
function docStdin(): void {
  let chunks = new Array<Uint8Array>(); let total = 0;
  let tmp = new Uint8Array(1 << 16);
  while (true) {
    IOV[0] = <u32>tmp.dataStart; IOV[1] = <u32>tmp.length;
    if (wasi_fd_read(0, changetype<usize>(IOV), 1, changetype<usize>(NW)) != 0) break;
    let n = <i32>NW[0]; if (n == 0) break;
    chunks.push(tmp.slice(0, n)); total += n;
  }
  inBuf = new Uint8Array(total); let o = 0;
  for (let i = 0; i < chunks.length; i++) { inBuf.set(chunks[i], o); o += chunks[i].length; }
}
function u32r(): u32 { let v = load<u32>(inBuf.dataStart + inPos); inPos += 4; return v; }
function i64r(): i64 { let v = load<i64>(inBuf.dataStart + inPos); inPos += 8; return v; }
function f64r(): f64 { let v = load<f64>(inBuf.dataStart + inPos); inPos += 8; return v; }
function napNhiPhan(): bool {
  if (inBuf.length < 8 || inBuf[0] != 71 || inBuf[1] != 54 || inBuf[2] != 52 || inBuf[3] != 1) return false;
  inPos = 4;
  let n = <i32>u32r(); nap_ma(n); for (let i = 0; i < n; i++) code[i] = <i32>u32r();
  n = <i32>u32r(); for (let i = 0; i < n; i++) nap_int(i64r());
  n = <i32>u32r(); for (let i = 0; i < n; i++) nap_f64(f64r());
  n = <i32>u32r(); for (let i = 0; i < n; i++) { let L = <i32>u32r(); for (let j = 0; j < L; j++) nap_ky(<i32>u32r()); nap_chuoi(); }
  n = <i32>u32r(); for (let i = 0; i < n; i++) { let a = <i32>u32r(), b = <i32>u32r(), c = <i32>u32r(), d = <i32>u32r(), e = <i32>u32r(); nap_ham(a, b, c, d, e); }
  n = <i32>u32r(); for (let i = 0; i < n; i++) { let a = <i32>u32r(), b = <i32>u32r(), c = <i32>u32r(); nap_chuoi_ten(a, b, c); }
  n = <i32>u32r(); for (let i = 0; i < n; i++) nap_muc_ten(<i32>u32r());
  nap_toan_cuc(<i32>u32r());
  n = <i32>u32r(); for (let i = 0; i < n; i++) { let g = <i32>u32r(), id = <i32>u32r(); dat_dung_san(g, id); }
  return true;
}
function docDoi(): Array<string> {
  let r = new Array<string>();
  if (wasi_args_sizes_get(changetype<usize>(NW), changetype<usize>(NW) + 4) != 0) return r;
  let argc = <i32>NW[0], bsz = <i32>NW[1];
  let ptrs = new Uint32Array(argc); let buf = new Uint8Array(bsz);
  if (wasi_args_get(ptrs.dataStart, buf.dataStart) != 0) return r;
  for (let i = 0; i < argc; i++) {
    let p = <usize>ptrs[i]; let e = p; while (load<u8>(e) != 0) e++;
    r.push(String.UTF8.decodeUnsafe(p, e - p, false));
  }
  return r;
}
export function _start(): void {
  let doi = docDoi();
  for (let i = 1; i < doi.length; i++) {
    let a = doi[i];
    if ((a == "--bước" || a == "--buoc") && i + 1 < doi.length) { MAX_STEPS = I64.parseInt(doi[++i]); }
    else if ((a == "--trần-ds" || a == "--tran-ds") && i + 1 < doi.length) { MAX_LIST = I32.parseInt(doi[++i]); }
    else if (a == "--cho-giờ" || a == "--cho-gio") { coGio = true; }
  }
  docStdin();
  if (!napNhiPhan()) { ghiChuoi(2, "[gvm64] stdin không phải chương trình .g64 hợp lệ\n"); wasi_proc_exit(2); return; }
  let kq = chay();
  if (kq != 0) wasi_proc_exit(1);
}

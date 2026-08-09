// ============================================================
// GVM ĐẦY ĐỦ — SUBSTRATE THỨ 5: WebAssembly  (AssemblyScript → gvm.wasm)
// ------------------------------------------------------------
// Port TRỌN bộ lệnh của gvm_may.py: số học/so-sánh width-aware (16/32-bit),
// heap 64K (cons-cell danh sách), khung gọi hàm (GỌI_N/THAM_I/TRẢ_VỀ_N), chuỗi.
// Chạy MỌI chương trình do giaoc sinh (kể cả thẻ 32-bit) — thẻ trong suốt với máy
// (chỉ RỌI_CHUỖI/RỌI_DS gỡ thẻ khi duyệt heap).
//
// I/O = HOST IMPORT (object-capability): roi / roiChar+roiNl / roiSo do host cấp.
// ============================================================

@external("env", "roi")      declare function roi(st: i32, val: i32, gam: f64): void;   // RỌI một ô
@external("env", "roiChar")  declare function roiChar(code: i32): void;                  // RỌI_CHUỖI: 1 ký tự
@external("env", "roiNl")    declare function roiNl(): void;                             // hết chuỗi
@external("env", "roiSo")    declare function roiSo(val: i32): void;                     // RỌI_DS: 1 số
@external("env", "roiDsHet") declare function roiDsHet(): void;                          // hết một danh sách
@external("env", "loi")      declare function loi(op: i32): void;                        // opcode chưa hỗ trợ

const AN: i32 = 0; const SANG: i32 = 1; const TOI: i32 = 2;

// — bộ nhớ —
const code = new StaticArray<i32>(65536); let codeLen: i32 = 0;
const ram  = new StaticArray<i32>(65536);
const vSt = new StaticArray<i32>(512); const vVal = new StaticArray<i32>(512); const vGam = new StaticArray<f64>(512);
const tSt = new StaticArray<i32>(512); const tVal = new StaticArray<i32>(512); const tGam = new StaticArray<f64>(512);
// ngăn xếp giá trị (ô: trạng thái/giá trị/γ)
const sSt = new StaticArray<i32>(8192); const sVal = new StaticArray<i32>(8192); const sGam = new StaticArray<f64>(8192);
let sp: i32 = 0;
// khung gọi hàm
const pstack = new StaticArray<i32>(16384); let psp: i32 = 0;   // ngăn xếp tham số (phẳng)
const rstack = new StaticArray<i32>(4096);  let rsp: i32 = 0;   // địa chỉ trả về
const fpBase = new StaticArray<i32>(4096); const fpN = new StaticArray<i32>(4096); let fsp: i32 = 0;
// ngăn xếp HANDLER thử/bắt: (ip, sâu_sp, sâu_psp, sâu_rsp, sâu_fsp)
const hIp = new StaticArray<i32>(1024); const hSp = new StaticArray<i32>(1024);
const hPs = new StaticArray<i32>(1024); const hRs = new StaticArray<i32>(1024);
const hFs = new StaticArray<i32>(1024); let hsp: i32 = 0;

// — độ rộng từ (16 hoặc 32) —
let BIT: i32 = 16;
function mask(x: i32): i32 { return BIT == 32 ? x : (x & 0xFFFF); }
function sgn(x: i32): i32 { return BIT == 32 ? x : ((x << 16) >> 16); }   // diễn giải CÓ DẤU

export function nap(i: i32, w: i32): void { code[i] = w; if (i + 1 > codeLen) codeLen = i + 1; }

function push(st: i32, val: i32, gam: f64): void { sSt[sp] = st; sVal[sp] = val; sGam[sp] = gam; sp++; }
function pushK(val: i32): void { push(SANG, mask(val), 1.0); }
function clampf(x: f64): f64 { if (x > 1.0) return 1.0; if (x < -1.0) return -1.0; return x; }
function absi(x: i32): i32 { return x < 0 ? -x : x; }
const _decBuf = new StaticArray<i32>(12);
function emitDec(x: i32): void {                 // in số nguyên KHÔNG âm dạng thập phân (qua roiChar)
  if (x == 0) { roiChar(48); return; }
  let k = 0;
  while (x > 0) { _decBuf[k++] = 48 + (x % 10); x = x / 10; }
  for (let i = k - 1; i >= 0; i--) roiChar(_decBuf[i]);
}

// CỘNG/TRỪ/NHÂN: ẩn lan truyền; gói theo độ rộng từ
function binop(kind: i32): void {
  sp--; let bs = sSt[sp]; let bv = sVal[sp]; sp--; let as_ = sSt[sp]; let av = sVal[sp];
  if (as_ == AN || bs == AN) { push(AN, 0, 0.0); return; }
  let r: i32 = 0;
  if (kind == 0) r = av + bv; else if (kind == 1) r = av - bv; else r = av * bv;
  push(SANG, mask(r), 1.0);
}
function cmp(kind: i32): void {    // 0=BẰNG 1=KHÁC 2=BÉ_HƠN 3=LỚN_HƠN 4=BÉ_BẰNG 5=LỚN_BẰNG
  sp--; let bv = sVal[sp]; sp--; let av = sVal[sp];
  let sa = sgn(av); let sb = sgn(bv); let r: bool = false;
  if (kind == 0) r = av == bv; else if (kind == 1) r = av != bv;
  else if (kind == 2) r = sa < sb; else if (kind == 3) r = sa > sb;
  else if (kind == 4) r = sa <= sb; else r = sa >= sb;
  pushK(r ? 1 : 0);
}

// GIAO = cộng hưởng(tâm[a], vật[a])
function giao(a: i32): void {
  if (tSt[a] == AN || vSt[a] == AN) { push(AN, 0, 0.0); return; }
  let d: i32 = absi(vVal[a] - tVal[a]);
  let sc: i32 = absi(vVal[a]); if (sc < 1) sc = 1;
  let gam: f64 = clampf(1.0 - 2.0 * (<f64>d) / (<f64>sc));
  let st: i32 = gam > 0.0 ? SANG : (gam < 0.0 ? TOI : AN);
  push(st, tVal[a], gam);
}
// HỌC: σ ← σ + ((ρ − σ) >> 1)  — số học 16-bit (đúng ashr1 của gvm.py, mọi độ rộng)
function hoc(a: i32): void {
  if (vSt[a] == AN) return;
  let bval: i32 = tSt[a] == AN ? 0 : tVal[a];
  let dv: i32 = (vVal[a] - bval) & 0xFFFF;
  let sd: i32 = (dv << 16) >> 16;
  let step: i32 = sd >> 1;
  tSt[a] = SANG; tVal[a] = (bval + step) & 0xFFFF; tGam[a] = 0.0;
}

export function chay(bit: i32): void {
  BIT = bit;
  for (let i = 0; i < 512; i++) { vSt[i] = AN; tSt[i] = AN; }
  sp = 0; psp = 0; rsp = 0; fsp = 0; hsp = 0;
  let ip: i32 = 0; let steps: i32 = 0;
  while (ip >= 0 && ip < codeLen) {
    if (++steps > 2000000000) break;                              // trần an toàn (tính toán nặng)
    let w: i32 = code[ip]; let op: i32 = (w >> 8) & 0xFF; let arg: i32 = w & 0xFF; ip++;
    if (op == 0) break;                                            // DỪNG
    else if (op == 1) pushK(arg);                                  // NẠP
    else if (op == 2) push(AN, 0, 0.0);                            // ẨN
    else if (op == 5) { sp--; tSt[arg] = sSt[sp]; tVal[arg] = sVal[sp]; tGam[arg] = sGam[sp]; } // LƯU_TÂM
    else if (op == 6) { sp--; vSt[arg] = sSt[sp]; vVal[arg] = sVal[sp]; vGam[arg] = sGam[sp]; } // LƯU_VẬT
    else if (op == 3) { push(vSt[arg], vVal[arg], vGam[arg]); }    // TẢI_VẬT
    else if (op == 4) { push(tSt[arg], tVal[arg], tGam[arg]); }    // TẢI_TÂM
    else if (op == 7) hoc(arg);                                    // HỌC
    else if (op == 8) giao(arg);                                   // GIAO
    else if (op == 10) binop(0);                                   // CỘNG
    else if (op == 68) {                                           // ★ CỘNG_HẰNG (siêu-lệnh add-immediate)
      sp--; let cs = sSt[sp]; let cv = sVal[sp];
      if (cs == AN) push(AN, 0, 0.0); else push(SANG, mask(cv + arg), 1.0);
    }
    else if (op == 69) {                                           // ★ NHÂN_CỘNG_HẰNG (siêu-lệnh #2 dup+add-imm): [x]→[x,x+k]
      let cs = sSt[sp - 1]; let cv = sVal[sp - 1];                 // PEEK top (giữ x)
      if (cs == AN) push(AN, 0, 0.0); else push(SANG, mask(cv + arg), 1.0);
    }
    else if (op == 70) { ram[sVal[sp - 1]] = ram[arg]; }           // ★ GHI_TRƯỜNG (siêu-lệnh #3 store-field): ram[top]=ram[arg], giữ top
    else if (op == 71) {                                           // ★ DỊCH_CỘNG_BYTE (siêu-lệnh #4 dựng-hằng): top ← (top<<8)+arg ≡ DỊCH_TRÁI 8; CỘNG_HẰNG k
      sp--; let cs = sSt[sp]; let cv = sVal[sp];
      if (cs == AN) push(AN, 0, 0.0); else pushK((mask(cv << 8)) + arg);
    }
    else if (op == 11) binop(1);                                   // TRỪ
    else if (op == 12) binop(2);                                   // NHÂN
    else if (op == 47) {                                           // CHIA (có dấu, cắt-về-0)
      sp--; let bv = sVal[sp]; sp--; let av = sVal[sp];
      if (bv == 0) pushK(0); else pushK(sgn(av) / sgn(bv));
    }
    else if (op == 14) { roi(sSt[sp - 1], sVal[sp - 1], sGam[sp - 1]); sp--; }   // RỌI
    else if (op == 20) { push(sSt[sp - 1], sVal[sp - 1], sGam[sp - 1]); }        // NHÂN_BẢN
    else if (op == 21) sp--;                                       // BỎ
    else if (op == 22) {                                           // ĐỔI
      let ts = sSt[sp - 1]; let tv = sVal[sp - 1]; let tg = sGam[sp - 1];
      sSt[sp - 1] = sSt[sp - 2]; sVal[sp - 1] = sVal[sp - 2]; sGam[sp - 1] = sGam[sp - 2];
      sSt[sp - 2] = ts; sVal[sp - 2] = tv; sGam[sp - 2] = tg;
    }
    else if (op == 24) pushK(ram[arg]);                            // TẢI_Ô
    else if (op == 25) { sp--; ram[arg] = sVal[sp]; }              // LƯU_Ô
    else if (op == 26) { sp--; if (sSt[sp] == AN) push(AN,0,0.0); else pushK(sVal[sp] << arg); }  // DỊCH_TRÁI
    else if (op == 27) { sp--; if (sSt[sp] == AN) push(AN,0,0.0); else pushK(sVal[sp] >>> arg); } // DỊCH_PHẢI
    else if (op == 29) { sp--; pushK(ram[sVal[sp]]); }             // TẢI_GIÁN
    else if (op == 30) { sp--; let v = sVal[sp]; sp--; ram[sVal[sp]] = v; }   // LƯU_GIÁN (val trên, idx dưới)
    else if (op == 28) { sp--; if (sSt[sp] != AN && sVal[sp] == 0) ip = arg; }      // NHẢY_NẾU_0
    else if (op == 15) ip = arg;                                   // NHẢY
    else if (op == 35) { sp--; ip = sVal[sp]; }                    // NHẢY_X
    else if (op == 36) { sp--; let cs = sSt[sp]; let cv = sVal[sp]; sp--; let tv = sVal[sp]; if (cs != AN && cv == 0) ip = tv; } // NHẢY_NẾU_0_X
    else if (op == 41) cmp(0);                                     // BẰNG
    else if (op == 42) cmp(1);                                     // KHÁC
    else if (op == 43) cmp(2);                                     // BÉ_HƠN
    else if (op == 44) cmp(3);                                     // LỚN_HƠN
    else if (op == 45) cmp(4);                                     // BÉ_BẰNG
    else if (op == 46) cmp(5);                                     // LỚN_BẰNG
    else if (op == 38) {                                           // GỌI_N (đỉnh=địa chỉ; dưới: arg đối)
      sp--; let target = sVal[sp];
      let base = psp;
      for (let k = arg - 1; k >= 0; k--) { sp--; pstack[base + k] = sVal[sp]; }
      psp = base + arg;
      fpBase[fsp] = base; fpN[fsp] = arg; fsp++;
      rstack[rsp++] = ip; ip = target;
    }
    else if (op == 39) pushK(pstack[fpBase[fsp - 1] + arg]);       // THAM_I
    else if (op == 66) { for (let i = 0; i < arg; i++) pstack[psp++] = 0; }   // DÀNH_CB: dành ô cục bộ
    else if (op == 67) { sp--; pstack[fpBase[fsp - 1] + arg] = sVal[sp]; }    // LƯU_THAM_I: ghi ô khung
    else if (op == 40) { ip = rstack[--rsp]; psp = fpBase[--fsp]; } // TRẢ_VỀ_N
    else if (op == 31) { sp--; pstack[psp++] = sVal[sp]; rstack[rsp++] = ip; ip = arg; } // GỌI
    else if (op == 32) { ip = rstack[--rsp]; psp--; }             // TRẢ_VỀ
    else if (op == 33) pushK(pstack[psp - 1]);                    // THAM
    else if (op == 37) { sp--; let t = sVal[sp]; sp--; pstack[psp++] = sVal[sp]; rstack[rsp++] = ip; ip = t; } // GỌI_X
    else if (op == 62) {                                          // BẮT_ĐẦU_THỬ: mở vùng thử
      sp--; let h = sVal[sp];
      hIp[hsp] = h; hSp[hsp] = sp; hPs[hsp] = psp; hRs[hsp] = rsp; hFs[hsp] = fsp; hsp++;
    }
    else if (op == 63) { hsp--; }                                 // HẾT_THỬ: gỡ handler trên cùng
    else if (op == 64) {                                          // NÉM: gỡ-cuộn về handler gần nhất
      sp--; let err = sVal[sp];
      if (hsp == 0) break;                                        // không handler → DỪNG (xuất giữ nguyên)
      hsp--;
      sp = hSp[hsp]; psp = hPs[hsp]; rsp = hRs[hsp]; fsp = hFs[hsp];   // gỡ-cuộn mọi khung lồng
      pushK(err); ip = hIp[hsp];                                  // trao trị-lỗi cho nhánh bắt
    }
    else if (op == 65) {                                          // RỌI_AUTO: in tự-suy-kiểu lúc chạy
      sp--; let st = sSt[sp]; let v = sVal[sp]; let g = sGam[sp];
      if (st != AN && (v & 0xC0000000) == 0x40000000) {           // con trỏ chuỗi (bit30=1, bit31=0)
        let a = v & 0x3FFFFFFF; let n = 0;
        while (a != 0 && n < 100000) { roiChar(ram[a] & 0x1FFFFF); a = ram[a + 1] & 0x3FFFFFFF; n++; }
        roiNl();
      } else { roi(st, v, g); }                                   // ẩn / số → in như RỌI
    }
    else if (op == 59) {                                          // FNHÂN: (a*b)/10000 điểm-cố-định (i64)
      sp--; let bs = sSt[sp]; let bv = sVal[sp]; sp--; let as_ = sSt[sp]; let av = sVal[sp];
      if (as_ == AN || bs == AN) push(AN, 0, 0.0);
      else { let p: i64 = <i64>sgn(av) * <i64>sgn(bv); pushK(<i32>(p / 10000)); }   // i64 cắt-về-0
    }
    else if (op == 60) {                                          // FCHIA: (a*10000)/b điểm-cố-định (i64)
      sp--; let bs = sSt[sp]; let bv = sVal[sp]; sp--; let as_ = sSt[sp]; let av = sVal[sp];
      if (as_ == AN || bs == AN || sgn(bv) == 0) push(AN, 0, 0.0);   // chia 0 → ẩn
      else { let p: i64 = <i64>sgn(av) * 10000; pushK(<i32>(p / <i64>sgn(bv))); }
    }
    else if (op == 61) {                                          // RỌI_THỰC: in ×10000 dạng thập phân
      sp--; let st = sSt[sp]; let v = sgn(sVal[sp]);
      if (st == AN) { roi(AN, 0, 0.0); }
      else {
        let neg = v < 0; let a = neg ? -v : v;
        if (neg) roiChar(45);                                     // '-'
        emitDec(a / 10000);                                       // phần nguyên
        let f = a % 10000;
        let d0 = (f / 1000) % 10, d1 = (f / 100) % 10, d2 = (f / 10) % 10, d3 = f % 10;
        let n = 4;
        if (d3 == 0) { n = 3; if (d2 == 0) { n = 2; if (d1 == 0) { n = 1; if (d0 == 0) { n = 0; } } } }
        if (n > 0) {
          roiChar(46);                                            // '.'
          if (n >= 1) roiChar(48 + d0); if (n >= 2) roiChar(48 + d1);
          if (n >= 3) roiChar(48 + d2); if (n >= 4) roiChar(48 + d3);
        }
        roiNl();
      }
    }
    else if (op == 58) {                                          // GỌI_CLOSURE (đỉnh=con trỏ closure; dưới: arg đối)
      sp--; let cp = sVal[sp] & 0x3FFFFFFF;                        // gỡ thẻ
      let codeAddr = ram[cp]; let ncap = ram[cp + 1];
      let base = psp;
      for (let i = 0; i < ncap; i++) pstack[base + i] = ram[cp + 2 + i];           // KHUNG[0..ncap) = bắt
      for (let k = arg - 1; k >= 0; k--) { sp--; pstack[base + ncap + k] = sVal[sp]; } // KHUNG[ncap..) = đối
      psp = base + ncap + arg;
      fpBase[fsp] = base; fpN[fsp] = ncap + arg; fsp++;
      rstack[rsp++] = ip; ip = codeAddr;
    }
    else if (op == 34) {                                          // RỌI_CHUỖI (gỡ thẻ)
      let a = sVal[--sp] & 0x3FFFFFFF; let n = 0;
      while (a != 0 && n < 100000) { roiChar(ram[a] & 0x1FFFFF); a = ram[a + 1] & 0x3FFFFFFF; n++; }
      roiNl();
    }
    else if (op == 48) {                                          // RỌI_DS (PEEK, gỡ thẻ, in số CÓ DẤU)
      let a = sVal[sp - 1] & 0x3FFFFFFF; let n = 0;
      while (a != 0 && n < 100000) { roiSo(sgn(ram[a])); a = ram[a + 1] & 0x3FFFFFFF; n++; }
      roiDsHet();
    }
    else { loi(op); break; }                                      // opcode chưa hỗ trợ
  }
}

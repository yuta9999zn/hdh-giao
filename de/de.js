/* de.js — bàn làm việc HĐH-GIAO.
   Mọi ứng dụng ở đây chỉ là MỘT KHUÔN MẶT: nó gọi xuống đúng tầng gọi-hệ của nhân GIAO,
   dưới đúng uid của phiên đăng nhập. Không có đường tắt nào riêng cho giao diện. */
"use strict";

const KHOÁ = new URLSearchParams(location.search).get("khoá") || "";
const $ = (s) => document.querySelector(s);

async function api(việc, thêm = {}) {
  const r = await fetch("/api", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Giao-Khoa": KHOÁ },
    body: JSON.stringify({ việc, ...thêm })
  });
  return r.json();
}

/* ══════════ ĐĂNG NHẬP ══════════ */
async function vào() {
  const tên = $("#ô-tên").value.trim(), mk = $("#ô-mk").value;
  if (!tên) return;
  $("#khoá-lỗi").textContent = "";
  $("#nút-vào").textContent = "Đang vào…";
  const kq = await api("vào", { tên, mk });
  $("#nút-vào").textContent = "Đăng nhập";
  if (!kq.ok) {
    $("#khoá-lỗi").textContent = kq.lý_do || kq.lỗi || "không vào được";
    $("#ô-mk").value = ""; $("#ô-mk").focus();
    return;
  }
  $("#khoá").classList.add("ẩn");
  $("#bàn").classList.remove("ẩn");
  $("#khay-người").textContent = tên;
  $("#menu-tên").textContent = tên;
  $("#cạnh-người").textContent = tên;
  $(".khoá-ảnh").textContent = $(".menu-ảnh").textContent =
    $(".cạnh-ảnh").textContent = tên[0].toUpperCase();
  chào(tên);
  dựngCạnh(); dựngDock(); dựngMenu(); dựngNhà(); nhịpTrạng();
}

/* Lời chào giữa thanh trên. Giờ dùng ở đây là giờ của MÁY CHỦ KHUNG HÌNH (trình duyệt), chỉ
   để chào cho dễ chịu. Nhịp của nhân GIAO nằm riêng ở ◷ bên trái — đừng lẫn hai thứ. */
function chào(tên) {
  const g = new Date().getHours();
  const buổi = g < 11 ? "Chào buổi sáng" : g < 14 ? "Chào buổi trưa"
             : g < 18 ? "Chào buổi chiều" : "Chào buổi tối";
  $("#chào-lời").textContent = `${buổi}, ${tên}`;
  $("#chào-ngày").textContent = new Date().toLocaleDateString("vi-VN",
    { weekday: "long", day: "numeric", month: "long", year: "numeric" });
}
$("#nút-vào").onclick = vào;
$("#ô-tên").onkeydown = (e) => { if (e.key === "Enter") $("#ô-mk").focus(); };
$("#ô-mk").onkeydown = (e) => { if (e.key === "Enter") vào(); };
$("#ô-tên").focus();

async function ra() {
  await api("ra");
  location.reload();
}
$("#nút-ra").onclick = ra;
$("#chân-ra").onclick = ra;
$("#chân-khoá").onclick = ra;

/* ══════════ ĐỒNG HỒ ══════════ */
(function vạchĐồngHồ() {
  let s = "";
  for (let i = 0; i < 60; i++) {
    if (i % 15 === 0) continue;                      // 4 góc đã có số 12/3/6/9 — chừa chỗ
    const g = (i * 6) * Math.PI / 180;
    const dài = i % 5 === 0 ? 7 : 3.5;               // vạch 5 phút dài hơn
    const x1 = 50 + Math.sin(g) * 41, y1 = 50 - Math.cos(g) * 41;
    const x2 = 50 + Math.sin(g) * (41 - dài), y2 = 50 - Math.cos(g) * (41 - dài);
    s += `<line x1="${x1.toFixed(2)}" y1="${y1.toFixed(2)}" x2="${x2.toFixed(2)}" y2="${y2.toFixed(2)}"`
       + (i % 5 === 0 ? ` class="dài"` : "") + `/>`;
  }
  $("#dh-vạch").innerHTML = s;
})();

function quayĐồngHồ() {
  const t = new Date();
  const gi = (t.getHours() % 12) * 30 + t.getMinutes() * .5;
  const ph = t.getMinutes() * 6 + t.getSeconds() * .1;
  const gy = t.getSeconds() * 6;
  $("#kim-giờ").setAttribute("transform", `rotate(${gi} 50 50)`);
  $("#kim-phút").setAttribute("transform", `rotate(${ph} 50 50)`);
  $("#kim-giây").setAttribute("transform", `rotate(${gy} 50 50)`);
  const hai = (n) => String(n).padStart(2, "0");
  $("#khay-giờ").textContent =
    `${t.getFullYear()}-${hai(t.getMonth() + 1)}-${hai(t.getDate())} | ${hai(t.getHours())}:${hai(t.getMinutes())}`;
}
setInterval(quayĐồngHồ, 1000); quayĐồngHồ();

/* ══════════ BẢNG ỨNG DỤNG ══════════ */
const ỨNG_DỤNG = {
  dòng_lệnh:  { tên: "Dòng lệnh",   biểu: "▮",  màu: "#1e2438", nhóm: "Hệ thống", rộng: 640, cao: 420 },
  tệp:        { tên: "Tệp",         biểu: "🗂", màu: "#2f6df0", nhóm: "Tệp",      rộng: 660, cao: 440 },
  tiến_trình: { tên: "Tiến trình",  biểu: "📊", màu: "#16a34a", nhóm: "Hệ thống", rộng: 600, cao: 380 },
  trợ_lý:     { tên: "Trợ lý",      biểu: "✦",  màu: "#7c3aed", nhóm: "Trợ lý",   rộng: 600, cao: 430 },
  người:      { tên: "Người & Nhóm",biểu: "👥", màu: "#d97706", nhóm: "An toàn",  rộng: 620, cao: 400 },
  mạng:       { tên: "Mạng",        biểu: "🌐", màu: "#0891b2", nhóm: "Mạng",     rộng: 560, cao: 340 },
  nhật_ký:    { tên: "Nhật ký",     biểu: "📜", màu: "#475569", nhóm: "An toàn",  rộng: 640, cao: 400 },
  soi_hệ:     { tên: "Soi hệ",      biểu: "◈",  màu: "#be185d", nhóm: "Hệ thống", rộng: 560, cao: 380 },
  thùng_rác:  { tên: "Thùng rác",   biểu: "🗑", màu: "#0f766e", nhóm: "Tệp",      rộng: 600, cao: 380 },
  bộ_nhớ:     { tên: "Bộ nhớ",      biểu: "▣",  màu: "#9333ea", nhóm: "Hệ thống", rộng: 620, cao: 400 },
  kho:        { tên: "Kho phần mềm",biểu: "📦", màu: "#c2410c", nhóm: "Hệ thống", rộng: 700, cao: 460 },
  soạn_thảo:  { tên: "Soạn thảo",   biểu: "✎",  màu: "#0369a1", nhóm: "Tệp",      rộng: 640, cao: 460 }
};
const DOCK = ["dòng_lệnh", "tệp", "soạn_thảo", "tiến_trình", "trợ_lý", "người", "mạng",
              "nhật_ký", "soi_hệ", "thùng_rác", "bộ_nhớ", "kho"];
const NHÓM = ["Yêu thích", "Tất cả ứng dụng", "Hệ thống", "Tệp", "Mạng", "An toàn", "Trợ lý"];
/* Biểu tượng + dòng phụ của từng nhóm. Một bảng dùng chung cho cả cột cạnh lẫn cột trong
   menu — trước đây biểu tượng nằm trong một mảng theo vị trí, thêm nhóm là lệch hết. */
const MÔ_NHÓM = {
  "Yêu thích":        ["★", "Mở nhanh"],
  "Tất cả ứng dụng":  ["▦", "Toàn bộ kho"],
  "Hệ thống":         ["⚙", "Nhân & tiến trình"],
  "Tệp":              ["🗂", "Kho lưu trữ"],
  "Mạng":             ["🌐", "Thiết bị /tb/mạng"],
  "An toàn":          ["🛡", "Quyền & nhật ký"],
  "Trợ lý":           ["✦", "Nói bằng lời"]
};

/* Ô ứng dụng trong bản thiết kế là kính một sắc, không phải mảng màu đặc. Giữ màu riêng của
   từng app nhưng hạ xuống mức ánh hắt: đủ để phân biệt, không phá cái nhìn chung. */
const mờ = (hex, a) => {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};

/* Bảng chọn chuột phải — dùng chung cho mọi ứng dụng. mục = [[nhãn, việc], …] */
function bảngChọn(x, y, mục) {
  document.querySelectorAll(".bảng-chọn").forEach(b => b.remove());
  const b = document.createElement("div");
  b.className = "bảng-chọn";
  b.style.left = x + "px"; b.style.top = y + "px";
  for (const [nhãn, việc] of mục) {
    const n = document.createElement("button");
    n.className = "bc-mục"; n.textContent = nhãn;
    n.onclick = () => { b.remove(); việc(); };
    b.appendChild(n);
  }
  document.body.appendChild(b);
  const r = b.getBoundingClientRect();                 // đừng để tràn khỏi màn hình
  if (r.right > innerWidth) b.style.left = (innerWidth - r.width - 8) + "px";
  if (r.bottom > innerHeight) b.style.top = (innerHeight - r.height - 8) + "px";
  setTimeout(() => document.addEventListener("click", () => b.remove(), { once: true }), 0);
}
document.addEventListener("contextmenu", (e) => {      // nền: chặn bảng chọn của trình duyệt
  if (e.target.closest(".cửa, .dock, .thanh")) return;
  e.preventDefault();
  bảngChọn(e.clientX, e.clientY, [
    ["▮ Dòng lệnh", () => mở("dòng_lệnh")],
    ["🗂 Tệp", () => mở("tệp")],
    ["✎ Soạn thảo", () => mở("soạn_thảo")],
    ["⊞ Xếp gọn cửa sổ", xếpGọn],
  ]);
});

function dựngDock() {
  $("#dock").innerHTML = "";
  for (const k of DOCK) {
    const a = ỨNG_DỤNG[k], b = document.createElement("button");
    // dock nhạt hơn lưới menu: ở dock cần dãy biểu tượng đọc như MỘT khối, còn trong menu
    // thì màu giúp tìm đúng app nhanh hơn
    b.className = "dock-ô"; b.title = a.tên; b.style.setProperty("--tint", mờ(a.màu, .16));
    b.innerHTML = a.biểu + `<span class="sáng ẩn"></span>`;
    b.onclick = () => mở(k);
    b.dataset.app = k;
    // Thả tệp vào 🗑 trên dock = bỏ vào thùng rác (vẫn qua đúng gọi-hệ `bỏ`)
    if (k === "thùng_rác") {
      b.ondragover = (e) => { e.preventDefault(); b.classList.add("thả-được"); };
      b.ondragleave = () => b.classList.remove("thả-được");
      b.ondrop = async (e) => {
        e.preventDefault(); b.classList.remove("thả-được");
        const đ = e.dataTransfer.getData("text/plain");
        if (!đ) return;
        const kq = await gõ(`bỏ ${đ}`); báo(kq.ra);
        if (CỬA["tệp"]) ỨNG.tệp(CỬA["tệp"].querySelector(".cửa-thân"));
        if (CỬA["thùng_rác"]) ỨNG.thùng_rác(CỬA["thùng_rác"].querySelector(".cửa-thân"));
      };
    }
    $("#dock").appendChild(b);
  }
}

function dựngMenu() {
  const cột = $("#menu-nhóm"); cột.innerHTML = "";
  NHÓM.forEach((n, i) => {
    const b = document.createElement("button");
    b.className = "nhóm" + (i === 0 ? " chọn" : "");
    b.dataset.nhóm = n;
    b.innerHTML = `<span>${MÔ_NHÓM[n][0]}</span><span>${n}</span>` +
                  (["Hệ thống", "An toàn", "Trợ lý"].includes(n) ? `<span class="chấm"></span>` : "");
    b.onclick = () => { cột.querySelectorAll(".nhóm").forEach(x => x.classList.remove("chọn")); b.classList.add("chọn"); vẽLưới(n); };
    cột.appendChild(b);
  });
  vẽLưới("Yêu thích");
}

/* ══════════ CỘT CẠNH ══════════
   Mỗi nhóm ứng dụng là một mục trong cột trái; bấm vào là mở menu đã lọc sẵn nhóm đó.
   "Tất cả ứng dụng" bỏ qua ở đây vì mục #nút-menu tĩnh phía trên đã giữ vai đó. */
function dựngCạnh() {
  const hộp = $("#cạnh-nhóm"); hộp.innerHTML = "";
  for (const n of NHÓM) {
    if (n === "Tất cả ứng dụng") continue;
    const [biểu, phụ] = MÔ_NHÓM[n];
    const b = document.createElement("button");
    b.className = "mục";
    b.innerHTML = `<span class="mục-biểu">${biểu}</span>` +
      `<span class="mục-chữ"><span class="mục-tên">${n}</span>` +
      `<span class="mục-phụ">${phụ}</span></span><span class="mục-mũi">›</span>`;
    b.onclick = (e) => { e.stopPropagation(); chọnCạnh(b); mởMenu(n); };
    hộp.appendChild(b);
  }
}
function chọnCạnh(b) {
  document.querySelectorAll(".cạnh .mục").forEach(x => x.classList.remove("chọn"));
  if (b) b.classList.add("chọn");
}
function mởMenu(nhóm) {
  $("#menu").classList.remove("ẩn");
  $("#menu-tìm").value = "";
  $("#menu-nhóm").querySelectorAll(".nhóm")
    .forEach(x => x.classList.toggle("chọn", x.dataset.nhóm === nhóm));
  vẽLưới(nhóm);
}

function vẽLưới(nhóm, lọc = "") {
  const lưới = $("#menu-lưới"); lưới.innerHTML = "";
  const yêu = ["dòng_lệnh", "tệp", "trợ_lý"];
  for (const [k, a] of Object.entries(ỨNG_DỤNG)) {
    if (nhóm === "Yêu thích" && !yêu.includes(k)) continue;
    if (nhóm !== "Yêu thích" && nhóm !== "Tất cả ứng dụng" && a.nhóm !== nhóm) continue;
    if (lọc && !a.tên.toLowerCase().includes(lọc.toLowerCase())) continue;
    const b = document.createElement("button");
    b.className = "ô-app";
    b.innerHTML = `<span class="biểu" style="--tint:${mờ(a.màu, .32)}">${a.biểu}</span>${a.tên}`;
    b.onclick = () => { mở(k); ẩnMenu(); };
    lưới.appendChild(b);
  }
}
$("#menu-tìm").oninput = (e) => vẽLưới("Tất cả ứng dụng", e.target.value);

function ẩnMenu() { $("#menu").classList.add("ẩn"); }
$("#nút-menu").onclick = (e) => {
  e.stopPropagation();
  if ($("#menu").classList.contains("ẩn")) {
    chọnCạnh($("#nút-menu")); mởMenu("Tất cả ứng dụng"); $("#menu-tìm").focus();
  } else ẩnMenu();
};
/* `closest` chứ không phải `e.target !== …`: các mục trong cột cạnh có phần tử con, bấm
   trúng con thì e.target là con — so bằng sẽ đóng menu ngay khi vừa mở. */
document.addEventListener("click", (e) => {
  if (!e.target.closest("#menu") && !e.target.closest(".cạnh")) ẩnMenu();
});
$("#menu").querySelectorAll("[data-mở]").forEach(b => b.onclick = () => { mở(b.dataset.mở); ẩnMenu(); });

/* ══════════ CỬA SỔ ══════════ */
let zĐỉnh = 10, đếmCửa = 0;
const CỬA = {};                                   // mã app → phần tử cửa sổ (mỗi app một cửa)

function mở(mã) {
  if (CỬA[mã]) { nổi(CỬA[mã]); return CỬA[mã]; }
  const a = ỨNG_DỤNG[mã];
  const c = document.createElement("div");
  c.className = "cửa";
  // Xếp cửa sổ TRẢI RA màn hình, không chồng khít một góc. (Trước đây bậc thang 26px nên mở ba
  // ứng dụng là chúng phủ kín nhau — bấm cái dưới thì nó có nổi lên thật, nhưng vẫn bị che,
  // trông y như "không ấn được".)
  const v = $("#vùng").getBoundingClientRect();
  const rộng = Math.min(a.rộng, v.width - 40), cao = Math.min(a.cao, v.height - 40);
  const cột = Math.max(1, Math.floor(v.width / (rộng + 30)));
  const i = đếmCửa++;
  const x = 20 + (i % cột) * (rộng + 24) + (Math.floor(i / cột) % 3) * 18;
  const y = 16 + (Math.floor(i / cột) % 3) * 46;
  c.style.left = Math.max(0, Math.min(x, v.width - rộng - 8)) + "px";
  c.style.top = Math.max(0, Math.min(y, v.height - cao - 8)) + "px";
  c.style.width = rộng + "px"; c.style.height = cao + "px";
  c.innerHTML =
    `<div class="cửa-đầu">
       <button class="cửa-nút n-đỏ" title="Đóng"></button>
       <button class="cửa-nút n-vàng" title="Thu nhỏ"></button>
       <button class="cửa-nút n-xanh" title="Phóng to / co lại"></button>
       <div class="cửa-tên">${a.biểu} ${a.tên}</div>
     </div>
     <div class="cửa-thân"></div><div class="cửa-chân ẩn"></div><div class="cửa-góc"></div>`;
  $("#vùng").appendChild(c);
  CỬA[mã] = c;
  // BA NÚT — đúng nếp macOS: đỏ = ĐÓNG · vàng = THU NHỎ (về dock) · xanh = PHÓNG TO/CO LẠI
  c.querySelector(".n-đỏ").onclick   = (e) => { e.stopPropagation(); đóng(mã); };
  c.querySelector(".n-vàng").onclick = (e) => { e.stopPropagation(); thuNhỏ(mã); };
  c.querySelector(".n-xanh").onclick = (e) => { e.stopPropagation(); phóngTo(c); };
  c.querySelector(".cửa-đầu").ondblclick = (e) => {   // gõ đúp thanh tiêu đề = phóng to/co lại
    if (!e.target.classList.contains("cửa-nút")) phóngTo(c);
  };
  c.onmousedown = () => nổi(c);
  // Bấm BẤT KỲ ĐÂU trong cửa sổ → trao con trỏ gõ cho ô của CHÍNH cửa sổ đó.
  // (Thiếu điều này thì chữ gõ lặng lẽ rơi sang cửa sổ khác — trợ lý trông như chết.)
  c.onclick = (e) => {
    if (e.target.closest("input, button, textarea, a")) return;
    if (String(window.getSelection())) return;            // đang bôi đen chữ thì đừng cướp con trỏ
    const ô = c.querySelector(".cửa-chân input, .cửa-thân input");
    if (ô) ô.focus();
  };
  kéo(c.querySelector(".cửa-đầu"), c);
  cỡ(c.querySelector(".cửa-góc"), c);
  nổi(c); dấuDock();
  ỨNG[mã](c.querySelector(".cửa-thân"), c.querySelector(".cửa-chân"));
  return c;
}
function đóng(mã) {
  const c = CỬA[mã]; if (!c) return;
  c.remove(); delete CỬA[mã]; dấuDock();
}
function thuNhỏ(mã) {
  const c = CỬA[mã]; if (!c) return;
  c.classList.add("thu");                                  // vẫn còn sống, chỉ ẩn khỏi mắt
  dấuDock();
}
function phóngTo(c) {
  if (c.dataset.to === "1") {                              // đang phóng → CO LẠI đúng chỗ cũ
    c.style.left = c.dataset.l; c.style.top = c.dataset.t;
    c.style.width = c.dataset.w; c.style.height = c.dataset.h;
    c.dataset.to = "";
  } else {                                                 // nhớ chỗ cũ rồi trải kín vùng làm việc
    c.dataset.l = c.style.left; c.dataset.t = c.style.top;
    c.dataset.w = c.style.width; c.dataset.h = c.style.height;
    c.style.left = "0px"; c.style.top = "0px";
    c.style.width = "100%"; c.style.height = "100%";
    c.dataset.to = "1";
  }
  nổi(c);
}
function nổi(c) {
  c.classList.remove("thu");                               // đang thu nhỏ mà gọi lên thì hiện lại
  c.style.zIndex = ++zĐỉnh;
  Object.values(CỬA).forEach(x => x.classList.add("mờ"));
  c.classList.remove("mờ");
  dấuDock();
  const ô = c.querySelector(".cửa-chân input, .cửa-thân input");
  if (ô) setTimeout(() => ô.focus(), 30);                  // cửa sổ nào nổi lên thì gõ được ngay
}
/* Xếp gọn: trải MỌI cửa sổ đang mở thành lưới kín màn hình — một cú bấm là hết chồng nhau. */
function xếpGọn() {
  const ds = Object.values(CỬA).filter(c => !c.classList.contains("thu"));
  if (!ds.length) return;
  const v = $("#vùng").getBoundingClientRect();
  const cột = Math.ceil(Math.sqrt(ds.length));
  const hàng = Math.ceil(ds.length / cột);
  const w = Math.floor(v.width / cột) - 12, h = Math.floor(v.height / hàng) - 12;
  ds.forEach((c, i) => {
    c.dataset.to = "";
    c.style.left = (8 + (i % cột) * (w + 10)) + "px";
    c.style.top = (8 + Math.floor(i / cột) * (h + 10)) + "px";
    c.style.width = w + "px"; c.style.height = h + "px";
  });
}
$("#nút-xếp").onclick = xếpGọn;

function dấuDock() {
  $("#dock").querySelectorAll(".dock-ô").forEach(b => {
    const c = CỬA[b.dataset.app];
    b.querySelector(".sáng").classList.toggle("ẩn", !c);
    b.classList.toggle("thu", !!(c && c.classList.contains("thu")));
  });
}
function kéo(tay, c) {
  tay.onmousedown = (e) => {
    if (e.target.classList.contains("cửa-nút")) return;
    nổi(c);
    const dx = e.clientX - c.offsetLeft, dy = e.clientY - c.offsetTop;
    const đi = (ev) => {
      c.style.left = Math.max(0, ev.clientX - dx) + "px";
      c.style.top = Math.max(0, ev.clientY - dy) + "px";
    };
    const thôi = () => { document.removeEventListener("mousemove", đi); document.removeEventListener("mouseup", thôi); };
    document.addEventListener("mousemove", đi); document.addEventListener("mouseup", thôi);
  };
}
function cỡ(góc, c) {
  góc.onmousedown = (e) => {
    e.stopPropagation(); nổi(c);
    const x0 = e.clientX, y0 = e.clientY, w0 = c.offsetWidth, h0 = c.offsetHeight;
    const đi = (ev) => {
      c.style.width = Math.max(320, w0 + ev.clientX - x0) + "px";
      c.style.height = Math.max(200, h0 + ev.clientY - y0) + "px";
    };
    const thôi = () => { document.removeEventListener("mousemove", đi); document.removeEventListener("mouseup", thôi); };
    document.addEventListener("mousemove", đi); document.addEventListener("mouseup", thôi);
  };
}

/* ══════════ TIỆN ÍCH ══════════ */
const thoát = (s) => String(s ?? "").replace(/[&<>"]/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]));

async function gõ(dòng) {                              // chạy một lệnh qua VỎ THẬT
  const kq = await api("lệnh", { dòng });
  vẽTrạng(kq);
  return kq;
}
/* Làm mới ĐỊNH KỲ cho tử tế:
   · cửa sổ đóng → thôi hẳn · cửa sổ thu nhỏ hoặc tab bị ẩn → NGHỈ (đừng bắt nhân quay vòng vô ích)
   · nội dung không đổi → KHÔNG vẽ lại (vẽ lại là mất chỗ đang bôi đen, mất cả cú bấm dở). */
function nhịpLại(thân, việc, ms) {
    const h = setInterval(async () => {
        if (!document.body.contains(thân)) { clearInterval(h); return; }
        if (document.hidden) return;
        const c = thân.closest(".cửa");
        if (c && c.classList.contains("thu")) return;
        await việc();
    }, ms);
}
function bảngTừVănBản(vb, cột) {                       // đổi kết quả lệnh dạng cột thành <table>
  const dòng = String(vb || "").split("\n").filter(d => d.trim());
  if (!dòng.length) return `<div class="gợi">(rỗng)</div>`;
  const đầu = dòng[0].split(/\t| {2,}/).filter(x => x);
  const thân = dòng.slice(1).map(d => d.split(/\t| {2,}/).filter(x => x));
  const th = (cột || đầu).map(x => `<th>${thoát(x)}</th>`).join("");
  const tr = thân.map(ô => `<tr>${ô.map(x => `<td>${thoát(x)}</td>`).join("")}</tr>`).join("");
  return `<table class="bảng"><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table>`;
}

/* ══════════ CÁC ỨNG DỤNG ══════════ */
const ỨNG = {};

/* — Dòng lệnh: đúng vỏ GIAO, không mô phỏng — */
ỨNG.dòng_lệnh = (thân, chân) => {
  thân.innerHTML = `<div class="vt" id="tm-ra"></div>`;
  chân.classList.remove("ẩn");
  chân.innerHTML = `<span class="tm-nhắc" id="tm-nhắc">$</span>
    <input class="tm-ô" id="tm-ô" autocomplete="off" spellcheck="false"
           placeholder="gõ lệnh… (giúp · liệt / · nhờ &lt;lời nói&gt;)">`;
  const ra = thân.querySelector("#tm-ra"), ô = chân.querySelector("#tm-ô");
  const in_ = (t, lớp) => {
    const p = document.createElement("div");
    if (lớp) p.className = lớp;
    p.textContent = t; ra.appendChild(p); thân.scrollTop = thân.scrollHeight;
  };
  in_("HĐH-GIAO — vỏ thật. Gõ `giúp` để xem lệnh.");
  api("trạng").then(t => { chân.querySelector("#tm-nhắc").textContent = t.nhắc || "$"; });
  const lịch = []; let vịTrí = 0;
  ô.onkeydown = async (e) => {
    if (e.key === "ArrowUp") { if (vịTrí > 0) ô.value = lịch[--vịTrí]; e.preventDefault(); return; }
    if (e.key === "ArrowDown") { vịTrí = Math.min(vịTrí + 1, lịch.length); ô.value = lịch[vịTrí] || ""; e.preventDefault(); return; }
    if (e.key !== "Enter") return;
    const d = ô.value.trim(); ô.value = "";
    if (!d) return;
    lịch.push(d); vịTrí = lịch.length;
    in_(chân.querySelector("#tm-nhắc").textContent + " " + d, "tm-nhắc");
    ô.disabled = true;
    const kq = await gõ(d);
    ô.disabled = false; ô.focus();
    if (kq.ra) in_(kq.ra, kq.mã ? "tm-lỗi" : "");
    if (kq.nhắc) chân.querySelector("#tm-nhắc").textContent = kq.nhắc;
    thân.scrollTop = thân.scrollHeight;
  };
  setTimeout(() => ô.focus(), 50);
};

/* — Tệp: liệt + soi qua gọi-hệ, dưới uid của bạn ⇒ quyền vẫn chặn — */
ỨNG.tệp = (thân) => {
  let ở = "/";
  const vẽ = async () => {
    const kq = await api("thư_mục", { đường: ở });
    const phần = ở.split("/").filter(x => x);
    let mẩu = `<button data-đi="/">/</button>`, dồn = "";
    for (const p of phần) { dồn += "/" + p; mẩu += `<button data-đi="${thoát(dồn)}">${thoát(p)}</button>`; }
    if (kq.lỗi) {
      thân.innerHTML = `<div class="đường">${mẩu}</div><div class="gợi">⛔ ${thoát(kq.lỗi)}
        — quyền của hệ điều hành chặn, giao diện không đi vòng được.</div>`;
    } else {
      const hàng = kq.mục.map(m => {
        const thư = m.hạng === "thư";
        const bt = thư ? "📁" : m.hạng === "thiết_bị" ? "⌁" : m.hạng === "ống" ? "⇉" : "📄";
        return `<tr class="${thư ? "hàng-thư" : ""}" draggable="true"
                    data-tên="${thoát(m.tên)}" data-hạng="${thoát(m.hạng)}"
                    data-thư="${thư ? thoát(m.tên) : ""}">
          <td>${bt} ${thoát(m.tên)}</td><td class="mono">${thoát(m.quyền)}</td>
          <td class="mono">${thoát(m.chủ)}</td><td class="mono">${thoát(m.cỡ)}</td>
          <td><button class="nút-hàng" data-bỏ="${thoát(m.tên)}" title="Bỏ vào thùng rác (lấy lại được)">🗑</button>
              <button class="nút-hàng" data-vs="${thoát(m.tên)}" title="Vì sao đọc được / không đọc được?">?</button></td></tr>`;
      }).join("");
      thân.innerHTML = `<div class="đường">${mẩu}</div>
        <table class="bảng"><thead><tr><th>Tên</th><th>Quyền</th><th>Chủ</th><th>Cỡ</th><th></th></tr></thead>
        <tbody>${hàng || `<tr><td colspan="5" class="gợi">(thư mục rỗng)</td></tr>`}</tbody></table>
        <div class="gợi" style="margin-top:10px">Gõ đúp thư mục để đi vào · <b>chuột phải</b> trên hàng
          để đổi tên / chép / bỏ… · <b>chuột phải trên nền</b> để tạo tệp / thư mục mới ·
          <b>kéo</b> tệp thả vào thư mục để chuyển, hoặc thả vào 🗑 trên dock để bỏ ·
          ? hỏi vì sao bị cấm.</div>`;
      thân.querySelectorAll("[data-thư]").forEach(tr => {
        if (!tr.dataset.thư) return;
        tr.ondblclick = () => { ở = (ở === "/" ? "" : ở) + "/" + tr.dataset.thư; vẽ(); };
      });
      const đủ = (t) => (ở === "/" ? "" : ở) + "/" + t;
      thân.querySelectorAll("[data-bỏ]").forEach(b => b.onclick = async (e) => {
        e.stopPropagation();
        const k = await gõ(`bỏ ${đủ(b.dataset.bỏ)}`); báo(k.ra); vẽ();
      });
      thân.querySelectorAll("[data-vs]").forEach(b => b.onclick = async (e) => {
        e.stopPropagation();
        const k = await gõ(`vì_sao ${đủ(b.dataset.vs)}`);
        const hộp = document.createElement("div");
        hộp.className = "gợi"; hộp.style.marginTop = "10px"; hộp.textContent = k.ra;
        thân.appendChild(hộp);
      });

      // ---- CHUỘT PHẢI: bảng chọn theo hàng ----
      thân.querySelectorAll("tr[data-tên]").forEach(tr => {
        tr.oncontextmenu = (e) => {
          e.preventDefault(); e.stopPropagation();
          const tên = tr.dataset.tên, đ = đủ(tên), làThư = tr.dataset.hạng === "thư";
          bảngChọn(e.clientX, e.clientY, [
            làThư ? ["📂 Mở thư mục", () => { ở = đ; vẽ(); }]
                  : ["✎ Sửa bằng Soạn thảo", () => mởTrongSoạnThảo(đ)],
            ["✎ Đổi tên…", async () => {
              const mới = prompt("Tên mới cho " + tên, tên);
              if (!mới || mới === tên) return;
              const k = await gõ(`chuyển ${đ} ${đủ(mới)}`); báo(k.ra || `đã đổi tên → ${mới}`); vẽ();
            }],
            // chép qua ĐÚNG gọi-hệ GH_CHÉP: cần ĐỌC nguồn + GHI thư mục đích, không đè
            ...(làThư ? [] : [["⧉ Chép thành…", async () => {
              const mới = prompt(`Chép ${tên} thành (tên tại đây, hoặc đường dẫn /…)`, tên + "_sao");
              if (!mới) return;
              const đích = mới.startsWith("/") ? mới : đủ(mới);
              const k = await gõ(`chép ${đ} ${đích}`); báo(k.ra || `đã chép → ${đích}`); vẽ();
            }]]),
            ["🗑 Bỏ vào thùng rác", async () => { const k = await gõ(`bỏ ${đ}`); báo(k.ra); vẽ(); }],
            ["? Vì sao bị cấm", async () => { const k = await gõ(`vì_sao ${đ}`); báo(k.ra); alert(k.ra); }],
            ["🔒 Đổi quyền…", async () => {
              const q = prompt("Quyền mới (số kiểu 644, 755…)", "644");
              if (!q) return;
              const k = await gõ(`quyền ${đ} ${q}`); báo(k.ra || `đã đổi quyền ${tên} → ${q}`); vẽ();
            }],
          ]);
        };
      });

      // ---- CHUỘT PHẢI TRÊN NỀN cửa sổ Tệp: tạo tệp / thư mục ngay tại chỗ (đuôi G2) ----
      // Vẫn qua đúng lệnh vỏ → đúng gọi-hệ (GH_TẠO / GH_TẠO_THƯ) ⇒ quyền chặn y hệt dòng lệnh.
      thân.oncontextmenu = (e) => {
        if (e.target.closest("tr[data-tên]")) return;    // hàng tệp đã có bảng chọn riêng
        e.preventDefault(); e.stopPropagation();
        bảngChọn(e.clientX, e.clientY, [
          ["🗎 Tạo tệp mới…", async () => {
            const tên = prompt("Tên tệp mới (tạo trong " + ở + ")");
            if (!tên) return;
            const k = await gõ(`sờ ${đủ(tên)}`); báo(k.ra || `đã tạo ${tên}`); vẽ();
          }],
          ["📁 Tạo thư mục mới…", async () => {
            const tên = prompt("Tên thư mục mới (tạo trong " + ở + ")");
            if (!tên) return;
            const k = await gõ(`tạothư ${đủ(tên)}`); báo(k.ra || `đã tạo thư mục ${tên}`); vẽ();
          }],
          ["⟳ Làm mới", vẽ],
        ]);
      };

      // ---- KÉO-THẢ: thả vào THƯ MỤC để chuyển · thả vào 🗑 trên dock để bỏ ----
      thân.querySelectorAll("tr[data-tên]").forEach(tr => {
        tr.ondragstart = (e) => {
          e.dataTransfer.setData("text/plain", đủ(tr.dataset.tên));
          e.dataTransfer.effectAllowed = "move";
        };
        if (tr.dataset.thư) {
          tr.ondragover = (e) => { e.preventDefault(); tr.classList.add("thả-được"); };
          tr.ondragleave = () => tr.classList.remove("thả-được");
          tr.ondrop = async (e) => {
            e.preventDefault(); tr.classList.remove("thả-được");
            const nguồn = e.dataTransfer.getData("text/plain");
            const tên = nguồn.split("/").pop();
            const đích = đủ(tr.dataset.thư) + "/" + tên;
            if (nguồn === đích) return;
            const k = await gõ(`chuyển ${nguồn} ${đích}`);
            báo(k.ra || `đã chuyển ${tên} → ${đủ(tr.dataset.thư)}/`);
            vẽ();
          };
        }
      });
    }
    thân.querySelectorAll("[data-đi]").forEach(b => b.onclick = () => { ở = b.dataset.đi; vẽ(); });
  };
  vẽ();
};

/* — Tiến trình — */
ỨNG.tiến_trình = (thân) => {
  let cũ = "";
  const vẽ = async () => {
    const kq = await gõ("tt");
    if (kq.ra === cũ) return;                          // không đổi thì đừng vẽ lại
    cũ = kq.ra;
    thân.innerHTML = `<div class="gợi">Bảng tiến trình của nhân — tự làm mới.</div>`
      + bảngTừVănBản(kq.ra, ["TID", "Tên", "Trạng thái", "Người"]);
  };
  vẽ();
  nhịpLại(thân, vẽ, 4000);
};

/* — Trợ lý AI: đúng cổng `nhờ`, có γ minh bạch và ba cửa chặn — */
ỨNG.trợ_lý = (thân, chân) => {
  thân.innerHTML = `<div class="gợi">Nói bằng lời. Trợ lý nêu độ cộng hưởng γ cho mọi lựa chọn,
    làm bằng <b>chính quyền của bạn</b>, và từ chối việc bất-khả-hồi.
    Thử: <i>“xem nhật ký hệ thống có gì bất thường không”</i> ·
    <i>“trong thư mục tạm có tệp gì”</i> · <i>“tôi là ai”</i></div>
    <div class="vt" id="tl-ra"></div>`;
  chân.classList.remove("ẩn");
  chân.innerHTML = `<span class="tm-nhắc">nhờ</span>
    <input class="tm-ô" id="tl-ô" placeholder="nói việc bạn muốn làm, bằng lời thường…">
    <button class="nút nút-đậm nút-nhỏ" id="tl-gửi">Nhờ</button>`;
  const ra = thân.querySelector("#tl-ra"), ô = chân.querySelector("#tl-ô");
  const hỏi = async () => {
    const lời = ô.value.trim(); if (!lời) return;
    ô.value = ""; ô.disabled = true;
    const p = document.createElement("div"); p.className = "tm-nhắc"; p.textContent = "nhờ " + lời;
    ra.appendChild(p);
    const chờ = document.createElement("div");                 // báo ĐANG NGHĨ — đừng để trông như chết
    chờ.className = "tl-chờ"; chờ.textContent = "⋯ đang nghĩ";
    ra.appendChild(chờ); thân.scrollTop = thân.scrollHeight;
    const kq = await gõ("nhờ " + lời);
    chờ.remove(); ô.disabled = false; ô.focus();
    const q = document.createElement("div");
    q.textContent = kq.ra && kq.ra.trim() ? kq.ra
      : "(trợ lý không nói gì — thử hỏi cụ thể hơn về tệp/thư mục/tiến trình)";
    ra.appendChild(q); thân.scrollTop = thân.scrollHeight;
  };
  ô.onkeydown = (e) => { if (e.key === "Enter") hỏi(); };
  chân.querySelector("#tl-gửi").onclick = hỏi;
  setTimeout(() => ô.focus(), 50);
};

/* — Người & Nhóm (C2/C3) — */
ỨNG.người = async (thân) => {
  const ng = await gõ("người"), nh = await gõ("nhóm");
  thân.innerHTML =
    `<div class="gợi">Sổ người dùng <span class="thẻ">/hệ/người_dùng 644</span> và sổ nhóm
      <span class="thẻ">/hệ/nhóm 644</span>. Bản băm mật khẩu nằm ở
      <span class="thẻ">/hệ/mật_khẩu 600</span> — chỉ gốc-quyền đọc được.</div>
     <h4>Người dùng</h4>${bảngTừVănBản(ng.ra, ["Người", "UID", "Nhà"])}
     <h4 style="margin-top:14px">Nhóm</h4>${bảngTừVănBản(nh.ra, ["Nhóm", "GID", "Thành viên"])}`;
};

/* — Mạng (B1) — */
ỨNG.mạng = (thân) => {
  const vẽ = async () => {
    const kq = await gõ("xem /tb/mạng");
    thân.innerHTML = `<div class="gợi">Thiết bị <span class="thẻ">/tb/mạng</span> — ổ nghe theo cổng
      và số kết nối đang mở. Cổng dưới 1024 chỉ gốc-quyền được nghe.</div>
      <div class="vt">${thoát(kq.ra)}</div>`;
  };
  vẽ();
  nhịpLại(thân, vẽ, 6000);
};

/* — Nhật ký audit — */
ỨNG.nhật_ký = (thân) => {
  const vẽ = async () => {
    const kq = await gõ("nhật_ký 60");
    const ởĐáy = thân.scrollTop + thân.clientHeight >= thân.scrollHeight - 30;
    thân.innerHTML = `<div class="gợi">Mọi lời gọi-hệ đều được ghi lại — kể cả việc do trợ lý làm hộ.
      Đang xem 60 mục gần nhất.</div><div class="vt">${thoát(kq.ra)}</div>`;
    if (ởĐáy) thân.scrollTop = thân.scrollHeight;
  };
  vẽ();
  nhịpLại(thân, vẽ, 6000);
};

/* — Soạn thảo: mở tệp, sửa, lưu — đọc/ghi qua ĐÚNG gọi-hệ nên quyền vẫn chặn — */
let ĐANG_MỞ = null;                                    // đường dẫn Tệp muốn mở bằng Soạn thảo
ỨNG.soạn_thảo = (thân, chân) => {
  chân.classList.remove("ẩn");
  chân.innerHTML = `<input class="tm-ô" id="st-đường" placeholder="/nhà/an/ghi_chú" spellcheck="false">
    <button class="nút nút-nhạt nút-nhỏ" id="st-mở">Mở</button>
    <button class="nút nút-đậm nút-nhỏ" id="st-lưu">Lưu</button>`;
  thân.innerHTML = `<div class="gợi" id="st-báo">Gõ đường dẫn rồi bấm Mở. Ghi đi qua đúng tầng
    gọi-hệ — tệp nào bạn không có quyền thì <b>lưu sẽ bị từ chối</b>, y như ở dòng lệnh.</div>
    <textarea class="st-ô" id="st-nội" spellcheck="false" placeholder="(chưa mở tệp nào)"></textarea>`;
  const ô = chân.querySelector("#st-đường"), nội = thân.querySelector("#st-nội"), báoÔ = thân.querySelector("#st-báo");
  const báoRa = (t, xấu) => { báoÔ.innerHTML = `<span style="color:${xấu ? "var(--đỏ)" : "var(--xanh)"}">${thoát(t)}</span>`; };
  const mởTệp = async () => {
    const đ = ô.value.trim(); if (!đ) return;
    const kq = await api("đọc", { đường: đ });
    if (kq.lỗi) { nội.value = ""; báoRa("⛔ " + kq.lỗi, true); return; }
    nội.value = kq.nội; báoRa("đã mở " + đ + " (" + kq.nội.length + " ký tự)");
  };
  chân.querySelector("#st-mở").onclick = mởTệp;
  ô.onkeydown = (e) => { if (e.key === "Enter") mởTệp(); };
  chân.querySelector("#st-lưu").onclick = async () => {
    const đ = ô.value.trim(); if (!đ) return;
    const kq = await api("ghi", { đường: đ, nội: nội.value });
    vẽTrạng(kq);
    if (kq.lỗi) báoRa("⛔ " + kq.lỗi, true); else báoRa("đã lưu " + đ);
  };
  if (ĐANG_MỞ) { ô.value = ĐANG_MỞ; ĐANG_MỞ = null; setTimeout(mởTệp, 60); }
};
function mởTrongSoạnThảo(đường) {
  ĐANG_MỞ = đường;
  const c = CỬA["soạn_thảo"];
  if (!c) { mở("soạn_thảo"); return; }
  nổi(c);
  const ô = c.querySelector("#st-đường");
  ô.value = đường;
  c.querySelector("#st-mở").click();
}

/* — Thùng rác: xoá KHẢ HỒI ở tầng gọi-hệ (chỗ GIAO hơn Linux) — */
ỨNG.thùng_rác = (thân) => {
  const vẽ = async () => {
    const kq = await gõ("thùng");
    const trống = (kq.ra || "").includes("trống");
    thân.innerHTML =
      `<div class="gợi">Ở Linux, <code>rm</code> là vĩnh viễn — thùng rác chỉ là quy ước của môi
        trường đồ hoạ, gõ ở terminal là mất sạch. Ở GIAO thùng rác nằm <b>trong tầng gọi-hệ</b>,
        nên <i>mọi</i> chương trình đều được che, cùng một tầng quyền và cùng ghi audit.</div>
       ${trống ? `<div class="gợi">🗑 thùng rác của bạn đang trống.</div>`
                : bảngTừVănBản(kq.ra, ["Đường cũ", "Bỏ ở nhịp"])}
       <div style="margin-top:12px;display:flex;gap:8px">
         <button class="nút nút-nhạt nút-nhỏ" id="r-hoàn">↩ Hoàn tác thứ vừa bỏ</button>
         <button class="nút nút-nhạt nút-nhỏ" id="r-dọn">🗑 Dọn hẳn (cần phê duyệt)</button>
       </div>
       <div class="gợi" style="margin-top:10px">Dọn hẳn là việc <b>bất-khả-hồi</b> — nên chính nó
         mới phải qua cổng phê duyệt, còn <code>bỏ</code> thì không.</div>`;
    thân.querySelector("#r-hoàn").onclick = async () => { const k = await gõ("hoàn_tác"); báo(k.ra); vẽ(); };
    thân.querySelector("#r-dọn").onclick  = async () => { const k = await gõ("dọn_rác"); báo(k.ra); vẽ(); };
  };
  vẽ();
};
function báo(t) {
  const c = CỬA["dòng_lệnh"];
  if (c && t) { const p = document.createElement("div"); p.textContent = t; c.querySelector("#tm-ra").appendChild(p); }
}

/* — Bộ nhớ: thấy σ và hạn mức TRƯỚC khi máy phải hỏi ai dừng (H4) — */
ỨNG.bộ_nhớ = (thân) => {
  const vẽ = async () => {
    const kq = await gõ("bộ_nhớ");
    const dọn = await gõ("dọn_dẹp");
    thân.innerHTML =
      `<div class="gợi">Linux hết bộ nhớ thì OOM-killer chấm điểm bằng heuristic thô rồi
        <b>SIGKILL im lặng</b> — hay bắn nhầm, và nạn nhân không kịp dọn. GIAO chọn theo
        <b>σ — độ hữu ích nhân TỰ HỌC</b> (cùng con số lịch γ dùng), <b>nêu lý do</b>, rồi
        <b>hỏi bạn</b>; đồng ý thì dừng ÊM (có dọn dẹp), không cắt ngang.</div>
       ${bảngTừVănBản(kq.ra, ["TID", "Tên", "σ (hữu ích)", "Ô nhớ"])}
       <h4 style="margin-top:14px">Nhật ký dọn dẹp</h4>
       <div class="vt">${thoát(dọn.ra)}</div>`;
  };
  vẽ();
  nhịpLại(thân, vẽ, 6000);
};

/* — Kho phần mềm: học apt/Kali, vá 5 chỗ yếu của nó — */
ỨNG.kho = (thân) => {
  const vẽ = async () => {
    const kho = await gõ("gói kho");
    const cài = await gõ("gói");
    const dòng = (kho.ra || "").split("\n").slice(1).filter(d => d.trim());
    const đãCài = new Set((cài.ra || "").split("\n").slice(1).map(d => d.split(/\t| {2,}/)[0].trim()));
    const nhóm = {};
    for (const d of dòng) {
      const ô = d.split("\t");
      if (ô.length < 5) continue;
      (nhóm[ô[2]] = nhóm[ô[2]] || []).push(ô);
    }
    let h = `<div class="gợi">Học apt/Kali (nguồn có trust anchor · mục lục mang băm · siêu-gói),
      nhưng khác ở năm chỗ: gói chỉ là <b>dữ liệu</b> — không có script chạy quyền gốc lúc cài ·
      cài là <b>giao dịch nguyên khối</b> (kiểm băm hết rồi mới ghi) · <b>gỡ/nâng cấp lùi được</b> ·
      nói rõ <b>vì sao</b> kéo theo từng gói · mỗi gói <b>tự khai năng lực</b>.
      Người thường cài vào thư mục riêng, <b>không cần nâng quyền</b>.</div>`;
    for (const [tên, ds] of Object.entries(nhóm)) {
      h += `<h4 style="margin:14px 0 6px">${thoát(tên)}</h4><table class="bảng"><tbody>`;
      for (const ô of ds) {
        const có = đãCài.has(ô[0]);
        const nl = ô[3] === "-" ? "" : `<span class="thẻ" style="background:rgba(251,191,36,.22);color:#fde68a">⚠ ${thoát(ô[3])}</span>`;
        h += `<tr><td><b>${thoát(ô[0])}</b> <span class="mono">${thoát(ô[1])}</span> ${nl}<br>
              <span class="gợi">${thoát(ô[4] || "")}</span></td>
              <td style="text-align:right;white-space:nowrap">${có
                ? `<span class="thẻ">đã cài</span> <button class="nút-hàng" data-gỡ="${thoát(ô[0])}">gỡ</button>`
                : `<button class="nút-hàng" data-xem="${thoát(ô[0])}">vì sao?</button>
                   <button class="nút nút-đậm nút-nhỏ" data-cài="${thoát(ô[0])}">Cài</button>`}</td></tr>`;
      }
      h += `</tbody></table>`;
    }
    h += `<div style="margin-top:14px;display:flex;gap:8px">
            <button class="nút nút-nhạt nút-nhỏ" id="k-nâng">↑ Nâng cấp tất cả</button>
            <button class="nút nút-nhạt nút-nhỏ" id="k-lùi">↩ Lùi lần nâng cấp trước</button>
          </div>`;
    thân.innerHTML = h;
    const chạyRồiVẽ = async (d) => { const k = await gõ(d); báo(k.ra); vẽ(); };
    thân.querySelectorAll("[data-cài]").forEach(b => b.onclick = async () => {
      const k = await gõ(`gói cài ${b.dataset.cài}`);
      if (k.mã && (k.ra || "").includes("NĂNG LỰC NHẠY CẢM")) {
        if (confirm(k.ra + "\n\nCấp năng lực ấy và cài?")) return chạyRồiVẽ(`gói cài ${b.dataset.cài} đồng-ý`);
        return;
      }
      báo(k.ra); vẽ();
    });
    thân.querySelectorAll("[data-gỡ]").forEach(b => b.onclick = () => chạyRồiVẽ(`gói gỡ ${b.dataset.gỡ}`));
    thân.querySelectorAll("[data-xem]").forEach(b => b.onclick = async () => {
      const k = await gõ(`gói xem ${b.dataset.xem}`);
      const hộp = document.createElement("div");
      hộp.className = "vt"; hộp.style.marginTop = "10px"; hộp.textContent = k.ra;
      thân.appendChild(hộp);
    });
    thân.querySelector("#k-nâng").onclick = () => chạyRồiVẽ("gói nâng_cấp");
    thân.querySelector("#k-lùi").onclick = () => chạyRồiVẽ("gói lùi");
  };
  vẽ();
};

/* — Soi hệ — */
ỨNG.soi_hệ = async (thân) => {
  const t = await api("trạng");
  const tm = await gõ("xem /hệ/tên_máy");
  const tim = await gõ("xem /tb/tim");
  thân.innerHTML = `
    <div class="gợi">Nhân GIAO — mọi con số dưới đây do chính hệ điều hành báo, không phải máy chủ web.</div>
    <table class="bảng"><tbody>
      <tr><td>Máy</td><td class="mono">${thoát((tm.ra || "").trim())}</td></tr>
      <tr><td>Người đăng nhập</td><td class="mono">${thoát(t.tên)} (uid ${thoát(t.uid)})</td></tr>
      <tr><td>Nhịp nhân</td><td class="mono">${thoát(t.nhịp)}</td></tr>
      <tr><td>Tiến trình sống</td><td class="mono">${(t.tiến_trình || []).length}</td></tr>
      <tr><td>Trái tim</td><td class="mono">${thoát((tim.ra || "").trim())}</td></tr>
      <tr><td>Lõi</td><td class="mono">GIAO — an toàn bộ nhớ theo kiến tạo, capability, ba-trị</td></tr>
    </tbody></table>`;
};

/* ══════════ TRẠNG THÁI + CỔNG PHÊ DUYỆT ══════════ */
function vẽTrạng(t) {
  if (!t || !t.đã_vào) return;
  $("#khay-nhịp").textContent = "◷ " + (t.nhịp ?? 0);
  $("#khay-tt").textContent = "▤ " + ((t.tiến_trình || []).length);
  if (t.chờ_duyệt) {
    $("#duyệt-mô").textContent = t.chờ_duyệt;
    $("#duyệt-nền").classList.remove("ẩn");
  } else {
    $("#duyệt-nền").classList.add("ẩn");
  }
}
async function nhịpTrạng() {
  vẽTrạng(await api("trạng"));
  setTimeout(nhịpTrạng, 2500);
}
$("#nút-duyệt").onclick = async () => {
  $("#duyệt-nền").classList.add("ẩn");
  const kq = await gõ("duyệt");
  const c = CỬA["dòng_lệnh"];
  if (c && kq.ra) {
    const p = document.createElement("div"); p.textContent = kq.ra;
    c.querySelector("#tm-ra").appendChild(p);
  }
};
$("#nút-huỷ").onclick = async () => {
  $("#duyệt-nền").classList.add("ẩn");
  await gõ("huỷ");
};

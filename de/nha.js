/* nha.js — BÀN CHÍNH của HĐH-GIAO.

   Bố cục lấy nguyên từ bản thiết kế: thanh lệnh trên cùng, thẻ trợ lý bên trái, dãy thẻ
   không-gian, ba thẻ dưới, cột phải bốn thẻ.

   Khác một điều với bản thiết kế, và là điều cốt lõi: MỌI CON SỐ Ở ĐÂY LÀ SỐ THẬT của
   nhân GIAO, lấy qua đúng lời gọi-hệ mà vỏ dòng-lệnh dùng, dưới đúng uid của phiên. Không
   có ô nào là chữ dựng sẵn. Chỗ nào nhân chưa cấp được dữ liệu thì thẻ nói thẳng là chưa
   có, chứ không bịa một con số cho đẹp — bàn làm việc bịa số thì nó thành ảnh chụp, mà cả
   dự án này dựng lên để KHÔNG phải là ảnh chụp.

   Nạp sau de.js và dùng lại $ / gõ / api / thoát / mở / mởMenu / chọnCạnh của nó. */
"use strict";

/* ── đọc số từ kết quả lệnh ─────────────────────────────────────────────────────
   Định dạng do lib_vỏ.giao quy định; ba hàm dưới là chỗ DUY NHẤT biết định dạng đó,
   đổi vỏ thì chỉ phải sửa ở đây. */
const dòngCủa = (vb) => String(vb || "").split("\n").map(d => d.trim()).filter(Boolean);

/* `bộ_nhớ` kết thúc bằng "tổng <x> / trần <y> ô" */
function đọcBộNhớ(vb) {
  const m = /tổng\s+(\d+)\s*\/\s*trần\s+(\d+)/.exec(String(vb || ""));
  return m ? { dùng: +m[1], trần: +m[2] } : null;
}
/* `nhật_ký n` cho mỗi dòng "nhịp <n>  tt<tid>  <việc>  <chi tiết>" */
function đọcNhậtKý(vb) {
  return dòngCủa(vb).map(d => {
    const m = /^nhịp\s+(\d+)\s+tt(\d+)\s+(.*)$/.exec(d);
    return m ? { nhịp: +m[1], tid: +m[2], việc: m[3] } : null;
  }).filter(Boolean);
}
/* `thùng` cho "thùng rác trống" hoặc một dòng tiêu đề + các dòng mục */
const đếmRác = (vb) => /trống/.test(String(vb || "")) ? 0 : Math.max(0, dòngCủa(vb).length - 1);

/* ── khung ────────────────────────────────────────────────────────────────── */
const khối = (id, tiêu, phụ, thân, lớp = "") =>
  `<section class="khối ${lớp}" id="${id}">
     <header class="khối-đầu"><div><div class="khối-tiêu">${tiêu}</div>
       ${phụ ? `<div class="khối-phụ">${phụ}</div>` : ""}</div>
       <div class="khối-phải" id="${id}-phải"></div></header>
     <div class="khối-thân" id="${id}-thân">${thân}</div>
   </section>`;

const đang = `<div class="gợi">đang đọc…</div>`;

function dựngNhà() {
  const n = $("#nhà");
  n.innerHTML = `
    <!-- ── thanh lệnh: gõ thẳng vào vỏ thật ── -->
    <div class="n-lệnh">
      <span class="n-orb" aria-hidden="true"></span>
      <input id="n-ô" class="n-ô" autocomplete="off" spellcheck="false"
             placeholder="Gõ một lệnh của GIAO — tt, bộ_nhớ, nhật_ký 20, liệt /…">
      <kbd class="n-phím">Enter</kbd>
      <button id="n-gửi" class="n-gửi" title="Chạy trong Dòng lệnh">↑</button>
    </div>

    <!-- ── thẻ trợ lý ── -->
    <section class="khối n-trợ-lý">
      <header class="khối-đầu"><div>
        <div class="khối-tiêu lớn">GIAO</div>
        <div class="khối-phụ">Trợ lý hệ điều hành</div></div>
        <div class="khối-phải"><span class="chấm-sống"></span> <span id="n-tl-trạng">đang chạy</span></div>
      </header>
      <div class="tl-quầng" aria-hidden="true"></div>
      <p class="tl-lời">Nói việc bạn muốn làm bằng lời thường. Trợ lý nêu độ cộng hưởng γ
         cho mọi lựa chọn, và vẫn đi qua đúng cổng phê duyệt như bạn tự gõ.</p>
      <div class="tl-gợi" id="n-tl-gợi"></div>
      <button class="nút nút-đậm tl-mở" id="n-tl-mở">Mở Trợ lý &nbsp;→</button>
    </section>

    <!-- ── dãy thẻ không gian ── -->
    <div class="n-kgian">
      <div class="kg-đầu"><div class="kg-tiêu">Không gian của bạn</div>
        <button class="kg-nút" id="n-kg-tất">Tất cả ứng dụng</button></div>
      <div class="kg-lưới" id="n-kg-lưới"></div>
    </div>

    <!-- ── ba thẻ dưới ── -->
    <div class="n-dưới">
      ${khối("n-sk", "Sức khoẻ hệ", "số của nhân, không phải của máy chủ", đang, "n-sk")}
      ${khối("n-hd", "Hoạt động", "lời gọi-hệ theo nhịp nhân", đang, "n-hd")}
      ${khối("n-cd", "Cổng bất-khả-hồi", "CDFL giữ việc không hoàn tác được", đang, "n-cd")}
    </div>

    <!-- ── cột phải ── -->
    <div class="n-rail">
      ${khối("n-dt", "Đồ thị tiến trình", "", đang)}
      ${khối("n-nk", "Nhật ký gần đây", "", đang)}
      ${khối("n-bn", "Bộ nhớ nhân", "", đang)}
      ${khối("n-tb", "Thiết bị", "", đang)}
    </div>`;

  /* Đồng hồ vốn nổi tự do ở góc phải trên — chỗ đó nay là cột phải, để nguyên là nó đè lên
     hai khối đầu. Dời hẳn vào cuối cột thay vì bỏ đi: nó vẫn là đồng hồ NHỊP của máy, và
     quayĐồngHồ() trong de.js vẫn tìm thấy các kim qua id nên không phải sửa gì thêm. */
  const đh = $(".đồng-hồ");
  if (đh) { đh.classList.add("đh-rail"); n.querySelector(".n-rail").appendChild(đh); }

  /* thanh lệnh → chạy trong cửa sổ Dòng lệnh thật, không dựng vỏ riêng cho bàn chính */
  const chạy = async () => {
    const dòng = $("#n-ô").value.trim();
    if (!dòng) return;
    $("#n-ô").value = "";
    mở("dòng_lệnh");
    const ô = $("#tm-ô");
    if (ô) { ô.value = dòng; ô.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true })); }
  };
  $("#n-gửi").onclick = chạy;
  $("#n-ô").onkeydown = (e) => { if (e.key === "Enter") chạy(); };

  $("#n-tl-mở").onclick = () => mở("trợ_lý");
  $("#n-kg-tất").onclick = (e) => {
    e.stopPropagation(); chọnCạnh($("#nút-menu")); mởMenu("Tất cả ứng dụng");
  };

  /* gợi ý của trợ lý = lệnh THẬT, bấm là chạy ngay */
  const GỢI = [["Xem tiến trình đang sống", "tt"], ["Soi bộ nhớ nhân", "bộ_nhớ"],
               ["Đọc nhật ký gần đây", "nhật_ký 20"], ["Ai đang có mặt", "người"]];
  $("#n-tl-gợi").innerHTML = GỢI.map(([nhãn, lệnh]) =>
    `<button class="tl-nút" data-lệnh="${thoát(lệnh)}">${thoát(nhãn)}</button>`).join("");
  $("#n-tl-gợi").querySelectorAll(".tl-nút").forEach(b => b.onclick = () => {
    $("#n-ô").value = b.dataset.lệnh; chạy();
  });

  /* thẻ không gian = các nhóm ứng dụng, số đếm lấy từ chính bảng ỨNG_DỤNG */
  const KG = ["Hệ thống", "Tệp", "Mạng", "An toàn"];
  $("#n-kg-lưới").innerHTML = KG.map(g => {
    const số = Object.values(ỨNG_DỤNG).filter(a => a.nhóm === g).length;
    return `<button class="kg-thẻ kg-${KG.indexOf(g)}" data-nhóm="${thoát(g)}">
      <span class="kg-biểu">${MÔ_NHÓM[g][0]}</span>
      <span class="kg-tên">${thoát(g)}</span>
      <span class="kg-phụ">${MÔ_NHÓM[g][1]}</span>
      <span class="kg-đếm">${số} ứng dụng</span></button>`;
  }).join("");
  $("#n-kg-lưới").querySelectorAll(".kg-thẻ").forEach(b => b.onclick = (e) => {
    e.stopPropagation(); chọnCạnh(null); mởMenu(b.dataset.nhóm);
  });

  vẽNhà();
  nhịpLại(n, vẽNhà, 5000);
}

/* ── vòng tròn tiến độ dùng chung ──────────────────────────────────────────── */
function vòng(phần, giữa, dưới) {
  const r = 34, chu = 2 * Math.PI * r;
  const p = Math.max(0, Math.min(1, phần || 0));
  return `<svg class="vòng" viewBox="0 0 84 84">
    <circle cx="42" cy="42" r="${r}" class="v-nền"/>
    <circle cx="42" cy="42" r="${r}" class="v-nét"
            stroke-dasharray="${(chu * p).toFixed(1)} ${chu.toFixed(1)}"
            transform="rotate(-90 42 42)"/>
    <text x="42" y="40" class="v-số">${thoát(giữa)}</text>
    ${dưới ? `<text x="42" y="55" class="v-nhãn">${thoát(dưới)}</text>` : ""}
  </svg>`;
}

/* ── làm mới toàn bộ thẻ ───────────────────────────────────────────────────── */
async function vẽNhà() {
  if ($("#nhà").classList.contains("ẩn")) return;
  /* Một vòng lấy dữ liệu cho CẢ bàn. Nhân GIAO là một trạng thái, mỗi lúc chỉ một lời gọi
     đi vào (giao_de.py giữ ổ khoá), nên gọi tuần tự — bắn song song chỉ xếp hàng chờ. */
  const t = await api("trạng");
  if (!t || !t.đã_vào) return;
  const bn = await gõ("bộ_nhớ");
  const nk = await gõ("nhật_ký 40");
  const rác = await gõ("thùng");
  const tb = await gõ("liệt /tb");

  const tiến = t.tiến_trình || [];
  const mem = đọcBộNhớ(bn.ra);
  const mục = đọcNhậtKý(nk.ra);
  const sốRác = đếmRác(rác.ra);

  /* ── Sức khoẻ hệ ── */
  const tỉMem = mem ? mem.dùng / Math.max(1, mem.trần) : 0;
  const ổn = !t.chờ_duyệt && tỉMem < 0.9;
  $("#n-sk-thân").innerHTML = `
    <div class="sk-trên">
      <div>
        <div class="sk-câu ${ổn ? "" : "cảnh"}">${ổn ? "Mọi thứ đang bình thường" : "Có việc cần bạn xử lý"}</div>
        <div class="gợi">${ổn ? "nhân chạy êm, không có việc nào chờ phê duyệt"
                              : (t.chờ_duyệt ? "một việc bất-khả-hồi đang chờ phê duyệt" : "bộ nhớ nhân sắp chạm trần")}</div>
      </div>
      ${vòng(tỉMem, Math.round(tỉMem * 100) + "%", "bộ nhớ")}
    </div>
    <div class="sk-ô">
      ${[["Nhịp nhân", t.nhịp ?? 0], ["Tiến trình", tiến.length],
         ["Ô nhớ", mem ? `${mem.dùng}/${mem.trần}` : "—"], ["Thùng rác", sốRác]]
        .map(([k, v]) => `<div class="ô-số"><div class="ô-nhãn">${k}</div>
          <div class="ô-giá">${thoát(String(v))}</div></div>`).join("")}
    </div>`;

  /* ── Hoạt động: gom mục nhật ký theo nhịp thành cột ── */
  const CỘT = 24;
  let cột = [];
  if (mục.length) {
    const min = mục[0].nhịp, max = mục[mục.length - 1].nhịp;
    const rộng = Math.max(1, (max - min + 1) / CỘT);
    cột = Array(CỘT).fill(0);
    for (const m of mục) cột[Math.min(CỘT - 1, Math.floor((m.nhịp - min) / rộng))]++;
  }
  const đỉnh = Math.max(1, ...cột);
  $("#n-hd-thân").innerHTML = `
    <div class="hd-số">
      ${[["Lời gọi ghi sổ", mục.length], ["Tiến trình dự", new Set(mục.map(m => m.tid)).size],
         ["Trải qua", mục.length ? (mục[mục.length - 1].nhịp - mục[0].nhịp) + " nhịp" : "—"]]
        .map(([k, v]) => `<div><div class="ô-nhãn">${k}</div>
          <div class="ô-giá nhỏ">${thoát(String(v))}</div></div>`).join("")}
    </div>
    <div class="hd-cột">${cột.map(c =>
      `<i style="height:${Math.max(3, c / đỉnh * 100)}%" title="${c} lời gọi"></i>`).join("")}</div>
    <div class="hd-trục"><span>${mục.length ? "nhịp " + mục[0].nhịp : ""}</span>
      <span>${mục.length ? "nhịp " + mục[mục.length - 1].nhịp : "chưa có mục nào"}</span></div>`;

  /* ── Cổng bất-khả-hồi ── */
  $("#n-cd-thân").innerHTML = t.chờ_duyệt
    ? `<div class="cd-chờ"><div class="cd-nhãn">Đang giữ lại</div>
         <div class="cd-mô">${thoát(t.chờ_duyệt)}</div>
         <div class="gợi">Nhân đã dừng việc này lại và chờ bạn. Hộp phê duyệt đang mở.</div></div>`
    : `<div class="cd-yên"><div class="cd-vòng" aria-hidden="true"></div>
         <div><div class="sk-câu">Không có việc nào chờ</div>
         <div class="gợi">Mọi việc bất-khả-hồi — xoá hẳn, dọn rác, đổi chủ — đều bị giữ ở
           cổng này và hỏi bạn trước. Bấm chuột không đi vòng qua được.</div></div></div>`;

  /* ── Đồ thị tiến trình ── */
  const N = tiến.length;
  const nan = tiến.slice(0, 10).map((p, i) => {
    const g = (i / Math.max(1, Math.min(N, 10))) * 2 * Math.PI - Math.PI / 2;
    const x = 130 + Math.cos(g) * 62, y = 92 + Math.sin(g) * 58;
    const tên = String(p[1] ?? p[0] ?? "?");
    const phải = Math.cos(g) > -0.2;
    return `<line x1="130" y1="92" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/>
      <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4.5" class="dt-nút"/>
      <text x="${(x + (phải ? 9 : -9)).toFixed(1)}" y="${(y + 3.5).toFixed(1)}"
            text-anchor="${phải ? "start" : "end"}">${thoát(tên.slice(0, 12))}</text>`;
  }).join("");
  $("#n-dt-thân").innerHTML = `
    <svg class="dt" viewBox="0 0 260 184">
      <g class="dt-nan">${nan}</g>
      <circle cx="130" cy="92" r="21" class="dt-tâm"/>
      <text x="130" y="97" class="dt-chữ">nhân</text>
    </svg>
    <div class="khối-chân"><b>${N}</b> tiến trình sống<span>nhịp ${thoát(String(t.nhịp ?? 0))}</span></div>`;

  /* ── Nhật ký gần đây ── */
  const gần = mục.slice(-5).reverse();
  $("#n-nk-thân").innerHTML = gần.length
    ? gần.map(m => `<div class="nk-hàng">
        <div class="nk-nhịp">${m.nhịp}<span>tt${m.tid}</span></div>
        <div class="nk-việc">${thoát(m.việc)}</div></div>`).join("")
    : `<div class="gợi">chưa có lời gọi nào được ghi sổ</div>`;

  /* ── Bộ nhớ nhân ── */
  $("#n-bn-thân").innerHTML = mem
    ? `<div class="bn"><div><div class="sk-câu nhỏ">${mem.dùng} / ${mem.trần} ô</div>
         <div class="gợi">trần do nhân đặt; chạm trần thì nhân hỏi trước khi dừng ai</div></div>
         ${vòng(tỉMem, Math.round(tỉMem * 100) + "%", "")}</div>`
    : `<div class="gợi">chưa đọc được số ô nhớ</div>`;

  /* ── Thiết bị ── */
  const dsTb = dòngCủa(tb.ra).filter(d => !/^\//.test(d) && !/lỗi|cấm/i.test(d));
  $("#n-tb-thân").innerHTML = dsTb.length
    ? `<div class="tb-lưới">${dsTb.slice(0, 6).map(d =>
        `<div class="tb-ô"><div class="tb-biểu">▤</div><div class="tb-tên">${thoát(d)}</div></div>`).join("")}</div>`
    : `<div class="gợi">${thoát((tb.ra || "").trim() || "không xem được /tb")}</div>`;
  $("#n-tb-phải").innerHTML = dsTb.length ? `${dsTb.length} thiết bị` : "";
}

# -*- coding: utf-8 -*-
"""
SINH wasm/playground.html — PLAYGROUND TRÌNH DUYỆT cho GIAO (KHÔNG Node, KHÔNG cài gì).
Nhúng giao.py + chuẩn.giao (base64) vào một tệp HTML tự chứa; Pyodide (CPython→wasm) chạy
TRÌNH THÔNG DỊCH ĐẦY ĐỦ ngay trong sandbox trình duyệt. Mở bằng file:// là dùng được.
(Chỉ cần internet để tải Pyodide từ CDN lần đầu — không cài Python/Node/gì cả.)
"""
import os, base64
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def b64(name): return base64.b64encode(open(os.path.join(P,name),"rb").read()).decode("ascii")

GIAO_B64  = b64("giao.py")
CHUAN_B64 = b64("chuẩn.giao")

VIDU = '''# Thử GIAO ngay trong TRÌNH DUYỆT — không cài gì, sandbox an toàn.
rọi "Xin chào từ Vùng Giao Thoa"

# bản (map) + vòng duyệt: đếm tần suất từ
đặt đếm = bản()
lặp từ trong tách("giao thoa giao hoa giao", " ") {
    nếu có_khoá(đếm, từ) { đặt_khoá(đếm, từ, lấy_khoá(đếm, từ) + 1) }
    khác { đặt_khoá(đếm, từ, 1) }
}
rọi đếm

# closure (lexical) + bản_đồ
hàm nhân(k) { trả hàm(x){ trả x * k } }
rọi bản_đồ(nhân(3), [1, 2, 3])

# ba-trị: chia 0 → ẩn (KHÔNG nổ chương trình)
rọi 8 / 0

# lõi CDFL: niềm tin học dần về thực tại
vật đích = 100
tâm đích = ẩn
lặp 4 { học đích  giao kq = đích  rọi kq }
'''

HTML = r'''<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GIAO — Playground (trình duyệt, không cài gì)</title>
<script src="https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js"></script>
<style>
  body{font-family:system-ui,Segoe UI,sans-serif;margin:0;background:#0e1116;color:#d8dee9}
  header{padding:14px 20px;background:#161b22;border-bottom:1px solid #30363d}
  header b{color:#7ee787} header small{color:#8b949e}
  main{display:flex;gap:12px;padding:12px;flex-wrap:wrap}
  .col{flex:1;min-width:320px;display:flex;flex-direction:column}
  textarea{width:100%;height:60vh;background:#0b0f14;color:#e6edf3;border:1px solid #30363d;
    border-radius:8px;padding:12px;font:14px/1.5 Consolas,monospace;resize:vertical;box-sizing:border-box}
  pre{flex:1;min-height:60vh;background:#0b0f14;color:#aee6c0;border:1px solid #30363d;border-radius:8px;
    padding:12px;font:14px/1.5 Consolas,monospace;overflow:auto;white-space:pre-wrap;margin:0}
  .bar{display:flex;gap:10px;align-items:center;margin:6px 0}
  button{background:#238636;color:#fff;border:0;border-radius:6px;padding:9px 18px;font-size:15px;cursor:pointer}
  button:disabled{background:#30363d;cursor:wait} #tt{color:#8b949e;font-size:13px}
  label{color:#8b949e;font-size:13px;margin:2px 0}
</style></head>
<body>
<header><b>GIAO</b> — ngôn ngữ Vùng Giao Thoa · <small>Playground chạy TRỌN trình thông dịch
trong trình duyệt (Pyodide/WASM) — không Node, không cài gì, sandbox an toàn.</small></header>
<main>
  <div class="col">
    <label>Mã GIAO:</label>
    <textarea id="src" spellcheck="false">__VIDU__</textarea>
    <div class="bar"><button id="run" disabled>Đang nạp Pyodide…</button><span id="tt"></span></div>
  </div>
  <div class="col"><label>Kết quả:</label><pre id="out">…</pre></div>
</main>
<script>
const B64_GIAO="__GIAO_B64__", B64_CHUAN="__CHUAN_B64__";
function bytes(b64){const bin=atob(b64);return Uint8Array.from(bin,c=>c.charCodeAt(0));}
const $=id=>document.getElementById(id);
let py=null;
async function khởi_tạo(){
  py=await loadPyodide();
  py.FS.writeFile("/giao.py", bytes(B64_GIAO));
  py.FS.writeFile("/chuẩn.giao", bytes(B64_CHUAN));
  py.runPython("import sys; sys.path.insert(0,'/'); import giao");
  $("run").disabled=false; $("run").textContent="▶ Chạy (Ctrl-Enter)"; $("out").textContent="Sẵn sàng.";
}
async function chạy(){
  if(!py) return;
  $("run").disabled=true; const t0=performance.now();
  const src=$("src").value;
  py.globals.set("__src__", src);
  let kq;
  try{ kq=py.runPython("giao.chạy_chuỗi(__src__)"); }
  catch(e){ kq="[lỗi nội bộ] "+e; }
  $("out").textContent=kq||"(không có đầu ra)";
  $("tt").textContent=((performance.now()-t0)/1000).toFixed(2)+"s";
  $("run").disabled=false;
}
$("run").addEventListener("click",chạy);
document.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key==="Enter")chạy();});
khởi_tạo();
</script></body></html>
'''

out = (HTML.replace("__GIAO_B64__", GIAO_B64)
           .replace("__CHUAN_B64__", CHUAN_B64)
           .replace("__VIDU__", VIDU.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")))
path = os.path.join(P, "wasm", "playground.html")
open(path, "w", encoding="utf-8").write(out)
print(f"sinh {path}  ({len(out)//1024} KB) — mở bằng trình duyệt (file://), không cần Node/server.")

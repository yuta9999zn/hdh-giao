// KIỂM CHỨNG PLAYGROUND TRONG TRÌNH DUYỆT THẬT (headless Chrome, qua puppeteer-core).
// Mở wasm/playground.html → đợi Pyodide nạp → nhập chương trình GIAO → bấm Chạy → đọc kết quả.
import puppeteer from "puppeteer-core";
import { pathToFileURL } from "node:url";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const CHROMES = [
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
];
const exe = CHROMES.find(existsSync);
if (!exe) { console.error("Không thấy Chrome/Edge"); process.exit(2); }

const url = pathToFileURL(join(here, "playground.html")).href;
const prog = [
  'rọi "browser-test-ok"',
  'rọi 2 + 3',                       // 5
  'đặt m = bản()  đặt_khoá(m,"x",7)  rọi m["x"]',  // 7
  'rọi bản_đồ(hàm(v){trả v*v}, [1,2,3])',          // [1, 4, 9]
  'rọi 8 / 0',                       // ẩn (ba-trị, không nổ)
].join("\n");

const browser = await puppeteer.launch({ executablePath: exe, headless: "new", args: ["--no-sandbox"] });
try {
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: "load", timeout: 60000 });
  console.log("• trang đã tải, đợi Pyodide nạp (tải từ CDN lần đầu)…");
  await page.waitForFunction(() => !document.getElementById("run").disabled, { timeout: 120000 });
  console.log("• Pyodide sẵn sàng → nhập chương trình & bấm Chạy");
  await page.evaluate((p) => { document.getElementById("src").value = p; }, prog);
  await page.click("#run");
  await page.waitForFunction(() => {
    const o = document.getElementById("out").textContent;
    return o && o !== "Sẵn sàng." && o !== "…";
  }, { timeout: 60000 });
  const out = await page.evaluate(() => document.getElementById("out").textContent);
  console.log("\n===== KẾT QUẢ TỪ TRÌNH DUYỆT =====\n" + out + "\n==================================");
  const ok = ["browser-test-ok", "5", "7", "[1, 4, 9]", "ẩn"].every((s) => out.includes(s));
  console.log(ok ? "\n✓ PLAYGROUND CHẠY THẬT TRONG TRÌNH DUYỆT (Pyodide, không Node ở runtime trang)"
                 : "\n✗ Output không như mong đợi");
  process.exit(ok ? 0 : 1);
} finally {
  await browser.close();
}

# GIAO CẦU NỐI — cắm lương tâm CDFL vào DỰ ÁN BẤT KỲ NGÔN NGỮ NÀO

> Một **sidecar suy luận** nói JSON qua stdio. Dự án của bạn (Python/JS/Go/Rust/Java/
> C#/Ruby/shell…) phơi *thực tại* cho GIAO; GIAO trả về *cộng hưởng γ*, *vùng tối DE*,
> và *phán quyết cổng an toàn*. **Không link, không dependency chung, không conflict.**

## Vì sao KHÔNG conflict (theo cấu trúc, không nhờ may)

- **Tiến trình riêng + chỉ stdio**: GIAO không đụng tệp/cổng/bộ nhớ của host.
- **Sandbox bẩm sinh**: GIAO không có builtin I/O; giá trị host gửi vào chỉ là *dữ liệu*
  (kể cả chuỗi `"rm -rf /"` cũng chỉ là chuỗi — không có gì để thực thi nó).
- **GIAO chỉ SUY LUẬN, không THỰC THI**: nó đứng *bên cạnh* dự án, quan sát và cố vấn.
- **JSON Lines**: mọi ngôn ngữ đều sinh/đọc được ⇒ tích hợp = vài dòng.

## Khởi động

```bash
python giao_cau_noi.py        # đọc JSON mỗi dòng ở stdin, ghi JSON mỗi dòng ở stdout
```
Dòng đầu tiên daemon in ra: `{"sẵn_sàng":true,"giao_thức":"giao-cau-noi/1",...}`.

## Giao thức (1 dòng = 1 JSON)

| op | yêu cầu | đáp (kèm `id`,`ok`) |
|---|---|---|
| `vật` | `{"op":"vật","tên":T,"giá_trị":V}` | host phơi thực tại ρ_MF |
| `tâm` | `{"op":"tâm","tên":T,"giá_trị":V}` | đặt niềm tin σ (`"ẩn"`=chưa biết) |
| `học` | `{"op":"học","tên":T}` | `{"tâm":σ_mới}` — kéo σ về ρ |
| `giao` | `{"op":"giao","tên":T}` | `{"giá_trị","gamma","trạng_thái"}` — cộng hưởng γ |
| `de` | `{"op":"de"}` | `{"DE_X","DE_T","DE_IF","DE_MF","hợp"}` — vùng tối bốn mặt |
| `chọn` | `{"op":"chọn","hành_động":[[tên,σ,ρ],…]}` | `{"chọn":[tên,σ,ρ],"gamma"}` — OR lớn nhất |
| `phê_duyệt` | `{"op":"phê_duyệt","gamma":g,"bất_khả_hồi":b,"ngưỡng":n}` | `{"phán":"cho_phép\|chặn\|cân_nhắc"}` |
| `trạng_thái` | `{"op":"trạng_thái"}` | dump `tâm`/`vật` |
| `trôi` | `{"op":"trôi","tên":T,"luật":"(vật T)+5"}` | thế giới tự dịch một nhịp → DE_T |

`tên` phải là định danh hợp lệ (chống chèn mã). Lỗi → `{"id":…,"ok":false,"lỗi":"…"}`.

### Cổng phê duyệt — hợp đồng an toàn cốt lõi (ba-trị)

- `γ ≥ ngưỡng` → **cho_phép** (sáng)
- `γ < ngưỡng` và **bất_khả_hồi** → **chặn** (tối) — không đủ tin mà không hoàn tác được
- `γ < ngưỡng` và hồi được → **cân_nhắc** (ẩn)

## Gọi từ ngôn ngữ khác (ví dụ — không cần thư viện GIAO)

**Shell:**
```bash
printf '%s\n' \
  '{"op":"vật","tên":"đĩa","giá_trị":100}' \
  '{"op":"tâm","tên":"đĩa","giá_trị":100}' \
  '{"op":"giao","tên":"đĩa"}' | python giao_cau_noi.py
```

**JavaScript (Node):**
```js
const { spawn } = require("child_process");
const p = spawn("python", ["giao_cau_noi.py"]);
p.stdout.on("data", b => b.toString().trim().split("\n").forEach(l => console.log(JSON.parse(l))));
const gửi = o => p.stdin.write(JSON.stringify(o) + "\n");
gửi({op:"vật", tên:"đĩa", giá_trị:80});
gửi({op:"phê_duyệt", gamma:0.4, bất_khả_hồi:true, ngưỡng:0.7});  // → {"phán":"chặn"}
```

**Bất kỳ ngôn ngữ nào:** spawn `python giao_cau_noi.py`, ghi 1 dòng JSON, đọc 1 dòng JSON.

## Kịch bản dùng thật

- **CI/CD gate**: host gửi tỉ-lệ-test-đậu làm `vật`; `phê_duyệt(γ, bất_khả_hồi=deploy-prod)`
  chặn deploy khi cộng hưởng chưa đủ.
- **Agent tự lái** (mọi ngôn ngữ): mỗi vòng phơi trạng thái → `chọn` hành động OR lớn nhất →
  `phê_duyệt` trước khi làm việc bất khả hồi; `de` cho biết chỗ agent *chưa biết / có thể ảo tưởng*.
- **Giám sát hệ thống**: `os_giao_windows.py` đã là một bản chuyên biệt (cảm nhận đĩa/RAM/CPU
  thật → đề xuất an toàn). Cầu nối tổng quát hoá điều đó cho *mọi* nguồn quan sát.

## SDK tham chiếu

`khach_cau_noi.py` — client Python mỏng (spawn + gửi/nhận) + demo. Các ngôn ngữ khác mô phỏng
y hệt (chỉ là spawn + JSON Lines).
```bash
python khach_cau_noi.py        # demo: phơi thực tại → đo γ → cổng chặn việc bất khả hồi
```

## Bọc thành MCP server (`giao_mcp.py`)

Cùng lõi CDFL, phơi qua **Model Context Protocol** để mọi host MCP (Claude Code/Desktop, IDE,
agent SDK) gọi như *tool*. **Zero-dependency**: tự hiện thực JSON-RPC 2.0 trên stdio (MCP stdio
transport = thông điệp JSON-RPC phân tách bằng newline), **tái dùng** `CầuNối` — ngữ nghĩa vẫn ở
runtime GIAO.

Tool: `giao_quan_sat` · `giao_cong_huong` · `giao_hoc` · `giao_vung_toi` · `giao_chon` ·
`giao_phe_duyet` · `giao_trang_thai`. Schema dùng khoá ASCII (tương thích host rộng), mô tả
tiếng Việt. Trạng thái `tâm`/`vật` BỀN qua các lần gọi trong một phiên.

Cấu hình Claude Code — `.mcp.json` (đã có sẵn ở gốc dự án):
```json
{ "mcpServers": { "giao": { "command": "python", "args": ["E:/HeDieuHanh/GIAO/giao_mcp.py"],
                            "env": {"PYTHONIOENCODING":"utf-8","PYTHONUTF8":"1"} } } }
```
Mở thư mục dự án trong Claude Code → server `giao` tự nạp; agent có ngay 7 tool CDFL.
```bash
python kiem_mcp.py             # 12 ca: handshake · tools/list · cổng phê duyệt · chống chèn mã
```
Thử tay (không cần host MCP): pipe JSON-RPC vào `python giao_mcp.py` — xem ví dụ ở đầu `giao_mcp.py`.

## I/O theo NĂNG LỰC — để GIAO chạm dự án host THẬT (an toàn)

Mặc định cầu nối/MCP **chỉ suy luận** (không I/O). Để GIAO *quan sát thực tại dự án* (đọc tệp,
chạy test) rồi biến thành `vật`, HOST cấp quyền **tường minh kèm phạm vi** qua biến môi trường —
chương trình GIAO KHÔNG tự nới được, ngoài phạm vi → lỗi sạch, I/O hỏng → `ẩn`:

| env | ý nghĩa |
|---|---|
| `GIAO_CHO_DOC` | thư mục cho ĐỌC/LIỆT KÊ (ngăn bằng `;` trên Windows / `:` trên Unix) |
| `GIAO_CHO_CHAY` | allowlist lệnh cho CHẠY (ngăn bằng `\|`), vd `pytest -q\|git status` |
| `GIAO_CHO_GHI` | thư mục cho GHI (bất khả hồi — cấp dè dặt) |

Khi cấp, MCP có thêm tool **`giao_doc_tep`**, **`giao_chay`** (chưa cấp ⇒ tự từ chối sạch).
`.mcp.json` ví dụ cho GIAO đọc & chạy test trong dự án này:
```json
{ "mcpServers": { "giao": { "command": "python", "args": ["E:/HeDieuHanh/GIAO/giao_mcp.py"],
    "env": { "PYTHONIOENCODING":"utf-8", "PYTHONUTF8":"1",
             "GIAO_CHO_DOC":".", "GIAO_CHO_CHAY":"python --version|git status" } } } }
```
CLI thuần (không qua sidecar): `python giao.py prog.giao --cho-đọc . --cho-chạy "pytest -q"`.
Builtin: `đọc_tệp(đường)` · `liệt_kê(thư_mục)` · `chạy(lệnh,[đối])` · `ghi_tệp(đường,nội)`.

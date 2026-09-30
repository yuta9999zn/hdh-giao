# -*- coding: utf-8 -*-
"""
GIAO MCP SERVER — bọc lương tâm CDFL của GIAO thành một MCP server.
================================================================================
Cho phép BẤT KỲ host MCP nào (Claude Code/Desktop, IDE, agent SDK…) gọi lõi suy
luận CDFL của GIAO như những "tool": đo cộng hưởng γ, soi vùng tối DE, chọn hành
động OR lớn nhất, và CỔNG PHÊ DUYỆT chặn việc bất khả hồi.

THIẾT KẾ — đúng tinh thần GIAO:
  • KHÔNG dependency: tự hiện thực JSON-RPC 2.0 trên stdio (MCP stdio transport =
    thông điệp JSON-RPC phân tách bằng newline). Không cần `pip install mcp`.
  • TÁI DÙNG `CầuNối` (giao_cau_noi.py): mọi ngữ nghĩa CDFL vẫn nằm trong runtime GIAO;
    lớp này chỉ là KHUNG GIAO THỨC MCP mỏng.
  • Trạng thái (tâm/vật) BỀN qua các lần gọi tool trong một phiên — hợp với agent suy luận.

Cấu hình cho Claude Code (`.mcp.json` hoặc settings):
  { "mcpServers": { "giao": { "command": "python", "args": ["giao_mcp.py"],
                              "env": {"PYTHONIOENCODING":"utf-8","PYTHONUTF8":"1"} } } }

Tự kiểm thử (không cần host MCP — pipe JSON-RPC vào):
  printf '%s\n' \
   '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}' \
   '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
   '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
   '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"giao_phe_duyet","arguments":{"gamma":0.4,"bat_kha_hoi":true,"nguong":0.7}}}' \
   | python giao_mcp.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # chạy được dù host MCP cwd khác
from giao_cau_noi import CầuNối
from niem_phong import SổNiêmPhong

SERVER_INFO = {"name": "giao-cdfl", "version": "0.3"}
DEFAULT_PROTOCOL = "2025-06-18"

# ── ĐỊNH NGHĨA TOOL (schema ASCII cho tương thích host rộng; mô tả tiếng Việt) ──
TOOLS = [
    {
        "name": "giao_quan_sat",
        "description": ("Phơi THỰC TẠI đo được (vật/ρ) cho GIAO, tuỳ chọn kèm NIỀM TIN/tuyên bố "
                        "(tâm/σ). Gọi trước khi đo cộng hưởng hay xin phê duyệt. Ví dụ: tên='độ_tin_cậy', "
                        "thuc_tai=70, niem_tin=95 (ta tuyên bố 95 nhưng thực tại mới 70)."),
        "inputSchema": {"type": "object", "properties": {
            "ten": {"type": "string", "description": "tên ô (định danh, không dấu cách)"},
            "thuc_tai": {"type": "number", "description": "giá trị thực tại ρ đo được từ host"},
            "niem_tin": {"description": "(tuỳ chọn) tuyên bố/kỳ vọng σ — số, hoặc 'ẩn' nếu chưa biết"}},
            "required": ["ten", "thuc_tai"]},
    },
    {
        "name": "giao_cong_huong",
        "description": ("Đo CỘNG HƯỞNG γ giữa niềm tin (σ) và thực tại (ρ) của một ô đã quan sát. "
                        "γ>0 = niềm tin khớp thực tại (sáng); γ<0 = ẢO TƯỞNG (tối); ẩn = chưa soi."),
        "inputSchema": {"type": "object", "properties": {
            "ten": {"type": "string"}}, "required": ["ten"]},
    },
    {
        "name": "giao_hoc",
        "description": "HỌC: kéo niềm tin (σ) về phía thực tại (ρ) một bước. Dùng để hiệu chỉnh ảo tưởng.",
        "inputSchema": {"type": "object", "properties": {
            "ten": {"type": "string"}}, "required": ["ten"]},
    },
    {
        "name": "giao_vung_toi",
        "description": ("Soi VÙNG TỐI DE bốn mặt — hệ biết nó CHƯA biết gì: DE_X (chưa tới), "
                        "DE_T (tri thức cũ đã trôi), DE_IF (ảo tưởng/chưa hình dung), DE_MF (chưa phơi). "
                        "Dùng để chống tự tin mù trước khi quyết định."),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "giao_chon",
        "description": ("CHỌN hành động mở rộng OR thật lớn nhất (argmax γ). Mỗi hành động = "
                        "[tên, σ_dự_đoán, ρ_kỳ_vọng]. Trả hành động tốt nhất kèm γ của nó."),
        "inputSchema": {"type": "object", "properties": {
            "hanh_dong": {"type": "array", "description": "danh sách [tên, σ, ρ]",
                          "items": {"type": "array"}}}, "required": ["hanh_dong"]},
    },
    {
        "name": "giao_phe_duyet",
        "description": ("CỔNG PHÊ DUYỆT an toàn (ba-trị). Việc HOÀN TÁC ĐƯỢC: γ≥ngưỡng → 'cho_phép', "
                        "ngược lại 'cân_nhắc'. Việc BẤT KHẢ HỒI (deploy, xoá, gửi tiền…): γ KHÔNG đủ thẩm "
                        "quyền — γ≥ngưỡng → 'cần_người_duyệt', γ<ngưỡng → 'chặn'. Nên niêm phong dự đoán "
                        "(giao_niem_phong) TRƯỚC khi làm, rồi chấm (giao_cham) sau."),
        "inputSchema": {"type": "object", "properties": {
            "gamma": {"type": "number", "description": "cộng hưởng của hành động (lấy từ giao_cong_huong/giao_chon)"},
            "bat_kha_hoi": {"type": "boolean", "description": "hành động có KHÔNG thể hoàn tác?"},
            "nguong": {"type": "number", "description": "ngưỡng cộng hưởng tối thiểu (mặc định 0.5)"}},
            "required": ["gamma", "bat_kha_hoi"]},
    },
    {
        "name": "giao_trang_thai",
        "description": "Dump trạng thái hiện thời: mọi ô tâm (niềm tin) và vật (thực tại).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "giao_doc_tep",
        "description": ("ĐỌC một tệp THẬT của dự án host (để biến nội dung thành quan sát). CHỈ chạy "
                        "nếu host đã cấp quyền qua env GIAO_CHO_DOC (danh sách thư mục). Ngoài phạm vi "
                        "→ lỗi; chưa cấp → 'chưa định nghĩa'. An toàn theo capability."),
        "inputSchema": {"type": "object", "properties": {
            "duong_dan": {"type": "string"}}, "required": ["duong_dan"]},
    },
    {
        "name": "giao_chay",
        "description": ("CHẠY một lệnh THẬT (vd 'pytest -q', 'git status') để phơi thực tại dự án. CHỈ "
                        "chạy nếu host cấp env GIAO_CHO_CHAY (allowlist, ngăn bằng '|'). Không qua shell, "
                        "có timeout. Ngoài allowlist → lỗi; chưa cấp → 'chưa định nghĩa'."),
        "inputSchema": {"type": "object", "properties": {
            "lenh": {"type": "string", "description": "tên chương trình (vd 'git')"},
            "doi": {"type": "array", "description": "đối số (vd ['status'])", "items": {}}},
            "required": ["lenh"]},
    },
    {
        "name": "giao_niem_phong",
        "description": ("NIÊM PHONG một DỰ ĐOÁN trước khi làm một việc (sổ chỉ-ghi-thêm, chuỗi băm SHA-256). "
                        "Mọi đề xuất hành động của AI nên niêm phong trước: dự đoán = bản {khoá: giá trị} "
                        "mình tin sẽ xảy ra (vd {\"test_đạt\": true, \"số_tệp_đổi\": 1}). Trả băm để chấm sau. "
                        "Không thể đoán lại sau khi đã biết kết quả."),
        "inputSchema": {"type": "object", "properties": {
            "viec": {"type": "string", "description": "mô tả việc sắp làm"},
            "du_doan": {"type": "object", "description": "dự đoán kết quả, {khoá: giá trị}"},
            "ai": {"type": "string", "description": "ai đề xuất (mặc định 'mcp')"}},
            "required": ["viec", "du_doan"]},
    },
    {
        "name": "giao_cham",
        "description": ("CHẤM một niêm phong bằng KẾT QUẢ THẬT (chỉ một lần). trúng = mọi khoá đã dự đoán đều "
                        "khớp. Trả trúng/lệch; điểm cộng dồn vào thống kê so với ĐƯỜNG NỀN."),
        "inputSchema": {"type": "object", "properties": {
            "bam": {"type": "string", "description": "băm niêm phong (từ giao_niem_phong)"},
            "ket_qua": {"type": "object", "description": "kết quả thật, {khoá: giá trị}"}},
            "required": ["bam", "ket_qua"]},
    },
    {
        "name": "giao_so_niem_phong",
        "description": ("KIỂM TOÀN VẸN sổ niêm phong (chuỗi băm) + THỐNG KÊ theo từng người đề xuất: tỉ lệ "
                        "trúng so với đường nền. Dùng để biết một AI có thật sự đoán giỏi hơn đoán mò."),
        "inputSchema": {"type": "object", "properties": {}},
    }
]

# ── ÁNH XẠ tool → yêu cầu CầuNối (lớp đã có; ngữ nghĩa nằm trong runtime GIAO) ──
def gọi_tool(cn, name, args):
    if name == "giao_quan_sat":
        out = cn.xử_lý({"op": "vật", "tên": args["ten"], "giá_trị": args["thuc_tai"]})
        if "niem_tin" in args and args["niem_tin"] is not None:
            cn.xử_lý({"op": "tâm", "tên": args["ten"], "giá_trị": args["niem_tin"]})
            out["niềm_tin"] = args["niem_tin"]
        return out
    if name == "giao_cong_huong":
        return cn.xử_lý({"op": "giao", "tên": args["ten"]})
    if name == "giao_hoc":
        return cn.xử_lý({"op": "học", "tên": args["ten"]})
    if name == "giao_vung_toi":
        return cn.xử_lý({"op": "de"})
    if name == "giao_chon":
        return cn.xử_lý({"op": "chọn", "hành_động": args["hanh_dong"]})
    if name == "giao_phe_duyet":
        return cn.xử_lý({"op": "phê_duyệt", "gamma": args["gamma"],
                         "bất_khả_hồi": args.get("bat_kha_hoi", False),
                         "ngưỡng": args.get("nguong", 0.5)})
    if name == "giao_trang_thai":
        return cn.xử_lý({"op": "trạng_thái"})
    if name == "giao_doc_tep":
        return cn.xử_lý({"op": "đọc_tệp", "đường_dẫn": args["duong_dan"]})
    if name == "giao_chay":
        return cn.xử_lý({"op": "chạy", "lệnh": args["lenh"], "đối": args.get("doi", [])})
    if name == "giao_niem_phong":
        return {"băm": SổNiêmPhong().niêm_phong(args.get("ai") or "mcp", args["viec"], args["du_doan"])}
    if name == "giao_cham":
        return SổNiêmPhong().chấm(args["bam"], args["ket_qua"])
    if name == "giao_so_niem_phong":
        sổ = SổNiêmPhong(); ok, lý = sổ.kiểm_chuỗi()
        return {"toàn_vẹn": ok, "lý_do": lý, "thống_kê": sổ.thống_kê()}
    raise ValueError(f"tool không có: {name}")

# ── JSON-RPC 2.0 trên stdio (MCP stdio transport) ──
def gửi(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n"); sys.stdout.flush()

def kết_quả(rid, result): gửi({"jsonrpc": "2.0", "id": rid, "result": result})
def lỗi(rid, code, msg):  gửi({"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": msg}})

def main():
    cn = CầuNối()
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            msg = json.loads(line)
        except Exception:
            continue                                  # bỏ qua dòng hỏng (không có id để báo)
        method, rid = msg.get("method"), msg.get("id")
        is_notif = "id" not in msg

        if method == "initialize":
            proto = (msg.get("params") or {}).get("protocolVersion") or DEFAULT_PROTOCOL
            kết_quả(rid, {"protocolVersion": proto,
                          "capabilities": {"tools": {"listChanged": False}},
                          "serverInfo": SERVER_INFO,
                          "instructions": "Lương tâm CDFL: quan sát thực tại → đo γ → soi DE → "
                                          "phê duyệt (việc bất khả hồi: γ không đủ thẩm quyền — cần người duyệt) → niêm phong dự đoán "
                                          "trước khi làm, chấm sau. I/O (giao_doc_tep/"
                                          "giao_chay) CHỈ hoạt động nếu host cấp env GIAO_CHO_DOC/GIAO_CHO_CHAY."})
        elif method == "notifications/initialized" or is_notif:
            continue                                  # thông báo: không hồi đáp
        elif method == "ping":
            kết_quả(rid, {})
        elif method == "tools/list":
            kết_quả(rid, {"tools": TOOLS})
        elif method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name"); args = params.get("arguments") or {}
            try:
                kq = gọi_tool(cn, name, args)
                kết_quả(rid, {"content": [{"type": "text",
                              "text": json.dumps(kq, ensure_ascii=False, indent=2)}],
                              "isError": False})
            except Exception as e:                    # lỗi tool → trả trong content (đúng MCP), không phải lỗi RPC
                kết_quả(rid, {"content": [{"type": "text", "text": f"Lỗi GIAO: {type(e).__name__}: {e}"}],
                              "isError": True})
        elif rid is not None:
            lỗi(rid, -32601, f"method không hỗ trợ: {method}")

if __name__ == "__main__":
    main()

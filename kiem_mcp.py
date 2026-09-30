# -*- coding: utf-8 -*-
"""
KIỂM THỬ GIAO MCP SERVER — spawn giao_mcp.py, chạy trọn vòng JSON-RPC + cả 7 tool.
Xác nhận: handshake initialize, tools/list đủ schema, và một kịch bản quyết định thật.
"""
import sys, os, json, subprocess

class MCP:
    def __init__(self):
        gốc = os.path.dirname(os.path.abspath(__file__))
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        for k in ("GIAO_CHO_DOC", "GIAO_CHO_CHAY", "GIAO_CHO_GHI"):
            env.pop(k, None)                          # test hermetic: mặc định KHÔNG quyền I/O
        import tempfile
        self.sổ = os.path.join(tempfile.mkdtemp(), "so.jsonl")
        env["GIAO_SO_NIEM_PHONG"] = self.sổ           # sổ niêm phong RIÊNG cho lần kiểm
        self.p = subprocess.Popen([sys.executable, os.path.join(gốc, "giao_mcp.py")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
            encoding="utf-8", bufsize=1, env=env, cwd=gốc)
        self._id = 0
    def yêu_cầu(self, method, params=None):
        self._id += 1
        self.p.stdin.write(json.dumps({"jsonrpc":"2.0","id":self._id,"method":method,
                                       "params":params or {}}, ensure_ascii=False)+"\n")
        self.p.stdin.flush()
        return json.loads(self.p.stdout.readline())
    def thông_báo(self, method):
        self.p.stdin.write(json.dumps({"jsonrpc":"2.0","method":method})+"\n"); self.p.stdin.flush()
    def tool(self, name, **args):
        r = self.yêu_cầu("tools/call", {"name":name,"arguments":args})
        c = r["result"]["content"][0]["text"]
        try: return json.loads(c), r["result"].get("isError", False)
        except Exception: return c, r["result"].get("isError", False)
    def đóng(self): self.p.stdin.close(); self.p.wait()

T=R=0
def kiểm(tên, đk, ct=""):
    global T,R; T+=1
    print(f"  {'✓' if đk else '✗'} {tên}" + ("" if đk else f"   {ct}"));  R+= 0 if đk else 1

print("="*60); print("KIỂM THỬ GIAO MCP SERVER"); print("="*60)
m = MCP()

print("\n[1] Handshake")
r = m.yêu_cầu("initialize", {"protocolVersion":"2025-06-18","capabilities":{},
                             "clientInfo":{"name":"kiểm","version":"0"}})
kiểm("initialize trả protocolVersion", r.get("result",{}).get("protocolVersion")=="2025-06-18", r)
kiểm("có serverInfo.name", r["result"]["serverInfo"]["name"]=="giao-cdfl")
kiểm("khai báo capability tools", "tools" in r["result"]["capabilities"])
m.thông_báo("notifications/initialized")

print("\n[2] tools/list")
r = m.yêu_cầu("tools/list"); tools = r["result"]["tools"]
tên_tool = {t["name"] for t in tools}
mong = {"giao_quan_sat","giao_cong_huong","giao_hoc","giao_vung_toi","giao_chon","giao_phe_duyet",
        "giao_trang_thai","giao_doc_tep","giao_chay","giao_niem_phong","giao_cham","giao_so_niem_phong"}
kiểm("đủ 12 tool (7 suy luận + 2 I/O capability + 3 niêm phong)", tên_tool==mong, tên_tool ^ mong)
kiểm("mọi tool có inputSchema kiểu object", all(t["inputSchema"]["type"]=="object" for t in tools))

print("\n[3] Kịch bản quyết định CDFL")
m.tool("giao_quan_sat", ten="sẵn_sàng", thuc_tai=70, niem_tin=95)
g,_ = m.tool("giao_cong_huong", ten="sẵn_sàng")
# ★ CDFL MỚI: γ skill-score (F.4) thay proxy. 95-vs-70: R=exp(−(25/70)²)=0.880 → γ=0.7738 (sáng);
# vẫn < ngưỡng 0.8 nên DEPLOY bất-khả-hồi vẫn bị CHẶN (kỷ luật giữ nguyên).
kiểm("cộng hưởng 95-vs-70 ~ +0.774 (skill-score)", abs(g["gamma"]-0.7738) < 0.01, g)
p,_ = m.tool("giao_phe_duyet", gamma=g["gamma"], bat_kha_hoi=True, nguong=0.8)
kiểm("DEPLOY bất khả hồi, γ thấp → CHẶN", p["phán"]=="chặn", p)
m.tool("giao_quan_sat", ten="sẵn_sàng", thuc_tai=96)        # thực tại được sửa lên
g2,_ = m.tool("giao_cong_huong", ten="sẵn_sàng")
p2,_ = m.tool("giao_phe_duyet", gamma=g2["gamma"], bat_kha_hoi=True, nguong=0.8)
kiểm("thực tại sửa lên 96 (γ cao) nhưng BẤT KHẢ HỒI → CẦN NGƯỜI DUYỆT (γ không phải cổng)",
      p2["phán"]=="cần_người_duyệt", (g2,p2))
p3,_ = m.tool("giao_phe_duyet", gamma=g2["gamma"], bat_kha_hoi=False, nguong=0.8)
kiểm("cùng γ cao, việc HOÀN TÁC ĐƯỢC → CHO PHÉP", p3["phán"]=="cho_phép", p3)

ch,_ = m.tool("giao_chon", hanh_dong=[["A",40,100],["B",90,100],["C",20,100]])
kiểm("chọn hành động OR lớn nhất = B", ch["chọn"][0]=="B", ch)

de,_ = m.tool("giao_quan_sat", ten="cõi_lạ", thuc_tai=5)     # vật không tâm → DE
d,_ = m.tool("giao_vung_toi")
kiểm("DE bắt 'cõi_lạ' (chưa hình dung/chưa phơi)", "cõi_lạ" in d["hợp"], d)

print("\n[4] Lỗi tool → trong content (isError), KHÔNG làm sập server")
bad, err = m.tool("giao_quan_sat", ten="tên xấu; rọi 9", thuc_tai=1)
kiểm("tên chèn mã → isError, server vẫn sống", err is True, bad)
g3,_ = m.tool("giao_cong_huong", ten="sẵn_sàng")             # server vẫn trả lời sau lỗi
kiểm("server vẫn phục vụ sau lỗi", g3["gamma"]==g2["gamma"], g3)

print("\n[5] I/O capability — chưa cấp env ⇒ từ chối sạch (ocap)")
io, err = m.tool("giao_doc_tep", duong_dan="chuẩn.giao")
kiểm("giao_doc_tep chưa cấp → isError (không lộ tệp)", err is True and "chưa định nghĩa" in str(io), io)

print("\n[6] Niêm phong dự đoán TRƯỚC khi làm, chấm SAU (sổ chuỗi băm)")
n1,_ = m.tool("giao_niem_phong", viec="deploy bản 2.1", du_doan={"test_đạt": True, "lỗi_mới": 0}, ai="claude")
kiểm("niêm phong trả băm SHA-256", isinstance(n1, dict) and len(n1.get("băm","")) == 64, n1)
c1,_ = m.tool("giao_cham", bam=n1["băm"], ket_qua={"test_đạt": True, "lỗi_mới": 0})
kiểm("chấm đúng dự đoán → trúng", c1.get("trúng") is True, c1)
n2,_ = m.tool("giao_niem_phong", viec="xoá bộ nhớ đệm", du_doan={"test_đạt": True}, ai="claude")
c2,_ = m.tool("giao_cham", bam=n2["băm"], ket_qua={"test_đạt": False})
kiểm("chấm sai dự đoán → trượt, nêu rõ khoá lệch", c2.get("trúng") is False and "test_đạt" in c2.get("lệch", {}), c2)
c3, err = m.tool("giao_cham", bam=n2["băm"], ket_qua={"test_đạt": True})
kiểm("không cho CHẤM LẠI (chống sửa điểm)", err is True and "ĐÃ được chấm" in str(c3), c3)
st,_ = m.tool("giao_so_niem_phong")
tk = st.get("thống_kê", {}).get("claude", {})
kiểm("sổ toàn vẹn + thống kê theo người đề xuất (2 chấm, 1 trúng, có đường nền)",
     st.get("toàn_vẹn") is True and tk.get("đã_chấm") == 2 and tk.get("trúng") == 1 and "đường_nền" in tk, st)

m.đóng()
print("\n" + "="*60)
print(f"KẾT QUẢ: {T-R}/{T} đạt" + ("" if R==0 else f"  — {R} RỚT"))
print("="*60)
sys.exit(1 if R else 0)

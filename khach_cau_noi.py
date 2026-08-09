# -*- coding: utf-8 -*-
"""
KHÁCH (SDK tham chiếu) cho GIAO CẦU NỐI — spawn sidecar + nói JSON Lines.
Mỏng có chủ đích: bất kỳ ngôn ngữ nào cũng làm đúng 3 việc — spawn tiến trình,
ghi 1 dòng JSON, đọc 1 dòng JSON. Đây là bản Python để đối chiếu.
"""
import sys, os, json, subprocess

class CầuNối:
    def __init__(self, python=None):
        gốc = os.path.dirname(os.path.abspath(__file__))
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        self.p = subprocess.Popen(
            [python or sys.executable, os.path.join(gốc, "giao_cau_noi.py")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
            encoding="utf-8", bufsize=1, env=env, cwd=gốc)
        self._đọc()                       # nuốt dòng "sẵn_sàng"
        self._id = 0
    def _đọc(self): return json.loads(self.p.stdout.readline())
    def gọi(self, op, **kw):
        self._id += 1
        self.p.stdin.write(json.dumps({"id": self._id, "op": op, **kw}, ensure_ascii=False) + "\n")
        self.p.stdin.flush()
        return self._đọc()
    def đóng(self):
        self.p.stdin.close(); self.p.wait()

if __name__ == "__main__":
    cn = CầuNối()
    print("Kịch bản: một 'service' (ngôn ngữ bất kỳ) hỏi GIAO trước khi DEPLOY PROD.")
    print("γ = độ KHỚP giữa TUYÊN BỐ 'đã sẵn sàng' và THỰC TẠI đo được.\n")

    # ta TUYÊN BỐ hệ sẵn sàng ở mức 95; thực tại đo được mới 70 → tự tin KHÔNG cộng hưởng
    cn.gọi("tâm", tên="sẵn_sàng", giá_trị=95)       # σ: tuyên bố/kỳ vọng
    cn.gọi("vật", tên="sẵn_sàng", giá_trị=70)       # ρ: thực tại đo được (CI, lỗi, tải...)
    g = cn.gọi("giao", tên="sẵn_sàng")
    p = cn.gọi("phê_duyệt", gamma=g["gamma"], bất_khả_hồi=True, ngưỡng=0.8)
    print(f"  [trước] tuyên bố 95 vs thực tại 70 → γ={g['gamma']:+.2f}")
    print(f"          ✦ DEPLOY PROD (bất khả hồi, ngưỡng 0.8): → {p['phán'].upper()}")

    # đội NGŨ THẬT SỰ sửa → thực tại tăng 70 → 96 (không phải hạ tuyên bố cho khớp)
    cn.gọi("vật", tên="sẵn_sàng", giá_trị=96)
    g2 = cn.gọi("giao", tên="sẵn_sàng")
    p2 = cn.gọi("phê_duyệt", gamma=g2["gamma"], bất_khả_hồi=True, ngưỡng=0.8)
    print(f"  [sau]   thực tại sửa lên 96 → γ={g2['gamma']:+.2f}")
    print(f"          ✦ DEPLOY PROD: → {p2['phán'].upper()}")

    print("\n  → GIAO cho service một LƯƠNG TÂM: chặn việc bất khả hồi khi TUYÊN BỐ chưa")
    print("    được THỰC TẠI cộng hưởng. Service viết bằng NGÔN NGỮ GÌ cũng gọi được (chỉ JSON).")
    cn.đóng()

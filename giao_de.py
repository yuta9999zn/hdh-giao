# -*- coding: utf-8 -*-
"""
giao_de.py — MÔI TRƯỜNG BÀN LÀM VIỆC (desktop) cho HĐH-GIAO
================================================================================
Giao diện đồ hoạ cho hệ điều hành GIAO: thanh trên · menu ứng dụng theo nhóm · dock · cửa sổ.

    python giao_de.py            → mở trình duyệt vào bàn làm việc
    python giao_de.py --cổng 8099
    python giao_de.py --không-mở → chỉ chạy máy chủ, tự mở đường dẫn sau

KIẾN TRÚC — vì sao đây KHÔNG phải "ảnh chụp giao diện":
  Mọi thao tác trên bàn làm việc đều đi qua **đúng tầng gọi-hệ** mà vỏ dòng-lệnh dùng, với
  **đúng tid + uid** của phiên đăng nhập. Nghĩa là:
    • quyền rwx / nhóm / uid  vẫn chặn y hệt — bấm chuột không có cửa hậu nào hơn gõ phím;
    • cổng BẤT-KHẢ-HỒI vẫn giữ việc lại → bàn làm việc hiện HỘP PHÊ DUYỆT (đây là chỗ CDFL
      lộ ra rõ nhất trên màn hình: máy hỏi trước khi làm việc không hoàn tác được);
    • nhật ký audit vẫn ghi đủ.
  Python ở đây chỉ đóng vai **máy chủ khung hình + bàn phím/chuột** (như X server), không phải
  hệ điều hành. Nhân vẫn là GIAO.

AN TOÀN: chỉ nghe trên 127.0.0.1 (không ra mạng ngoài) + KHOÁ PHIÊN ngẫu nhiên trong đường dẫn.
Không có khoá thì mọi lời gọi bị từ chối — kẻo một trang web bất kỳ đang mở gọi lén vào máy bạn.
"""
import os, sys, json, secrets, threading, webbrowser, contextlib, io
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from giao import GiaoError, GiaoLimit, GiaoSyntax, AN, Ban
from chay_hdh_giao import Máy

KHOÁ = secrets.token_urlsafe(18)
_ổ = threading.Lock()          # nhân GIAO là MỘT trạng thái — mỗi lúc chỉ một lời gọi đi vào


# ---------------- đổi giá trị GIAO → JSON ----------------
def _js(v):
    if v is AN: return None
    if isinstance(v, Ban): return {str(k): _js(x) for k, x in v.d.items()}
    if isinstance(v, list): return [_js(x) for x in v]
    if isinstance(v, (str, int, float, bool)) or v is None: return v
    return str(v)


class Bàn:
    "Một phiên bàn làm việc: giữ MỘT máy GIAO + tid vỏ của người đang đăng nhập."
    def __init__(self):
        self.máy = Máy()
        self.đã_vào = False
        self.tên = None
        # Vỏ dựng sẵn lúc boot phải nghỉ — chưa ai đăng nhập thì không được có phiên nào chạy.
        self._giao('nếu trạng(lấy_khoá(M, "nhân"), V) != "chết" { gọi(M, V, GH_THOÁT, []) }')

    def _giao(self, mã):
        self.máy._chạy_giao(mã)

    def _lấy(self, tên):
        return _js(self.máy.rt.glob.get(tên))

    # ---- đăng nhập / đăng xuất ----
    def vào(self, tên, mk):
        kq = self.máy.đăng_nhập(tên, mk)
        if isinstance(kq, int):
            self.đã_vào, self.tên = True, tên
            return {"ok": True, "tên": tên, "tid": kq}
        # KHÔNG nói rõ sai TÊN hay sai MẬT KHẨU — nói rõ là chỉ điểm cho người dò tài khoản.
        return {"ok": False, "lý_do": "Sai tên đăng nhập hoặc mật khẩu."}

    def ra(self):
        if self.đã_vào:
            self._giao('nếu trạng(lấy_khoá(M, "nhân"), V) != "chết" { gọi(M, V, GH_THOÁT, []) }')
        self.đã_vào, self.tên = False, None
        return {"ok": True}

    # ---- chạy MỘT dòng lệnh qua đúng vỏ thật ----
    def lệnh(self, dòng):
        if not self.đã_vào: return {"lỗi": "chưa đăng nhập"}
        self.máy.rt.glob["__d"] = dòng
        bắt = io.StringIO()
        try:
            # `rọi` của trợ lý in thẳng ra màn hình → hứng lại để đưa lên cửa sổ.
            with contextlib.redirect_stdout(bắt):
                self._giao('đặt __kq = chạy_dòng_im(M, V, __d)\n'
                           'đặt __lát = vòng_nhân(M, 6)')
        except (GiaoError, GiaoLimit, GiaoSyntax) as e:
            return {"mã": 1, "ra": f"[lỗi hệ] {getattr(e, 'msg', e)}", **self.trạng()}
        kq = self._lấy("__kq") or [0, ""]
        ra = (bắt.getvalue() or "") + (kq[1] if len(kq) > 1 and kq[1] else "")
        return {"mã": kq[0], "ra": ra, **self.trạng()}

    # ---- gọi-hệ có cấu trúc (cho ứng dụng Tệp) — VẪN dưới uid của người đăng nhập ----
    def thư_mục(self, đường):
        if not self.đã_vào: return {"lỗi": "chưa đăng nhập"}
        self.máy.rt.glob["__đ"] = đường
        self._giao('đặt __ds = gọi(M, V, GH_LIỆT, [__đ])')
        ds = self._lấy("__ds")
        if ds is None: return {"lỗi": f"không có {đường}"}
        if not isinstance(ds, list): return {"lỗi": f"cấm xem {đường}"}
        mục = []
        for tên in ds:
            self.máy.rt.glob["__đ2"] = (đường.rstrip("/") + "/" + str(tên)) if đường != "/" else "/" + str(tên)
            self._giao('đặt __s = gọi(M, V, GH_SOI, [__đ2])')
            s = self._lấy("__s")
            if isinstance(s, list) and len(s) >= 4:
                mục.append({"tên": tên, "hạng": s[0], "quyền": s[1], "chủ": s[2], "cỡ": s[3]})
            else:
                mục.append({"tên": tên, "hạng": "?", "quyền": "?", "chủ": "?", "cỡ": 0})
        return {"đường": đường, "mục": mục}

    # ---- ĐỌC / GHI cho trình soạn thảo — vẫn qua ĐÚNG gọi-hệ, dưới uid của phiên ----
    def đọc(self, đường):
        # BẪY đã cắn ba lần trong dự án này: `sáng`/`tối` CHÍNH LÀ CHUỖI, nên KHÔNG thể nhìn
        # kiểu trả về mà biết "cấm đọc" hay "nội dung tệp đúng là chữ tối". Hỏi NHÂN mới chắc:
        # `gọi` xoá sạch `lỗi` ở đầu mỗi lời gọi và chỉ đặt lại khi hỏng.
        if not self.đã_vào: return {"lỗi": "chưa đăng nhập"}
        self.máy.rt.glob["__đ"] = đường
        self._giao('đặt __n = gọi(M, V, GH_ĐỌC, [__đ])\nđặt __lỗi = lỗi_cuối(M)')
        lỗi = self._lấy("__lỗi")
        if lỗi: return {"lỗi": lỗi}
        n = self._lấy("__n")
        if not isinstance(n, str): return {"lỗi": f"không đọc được {đường}"}
        return {"đường": đường, "nội": n}

    def ghi(self, đường, nội):
        "Ghi đè nếu tệp đã có, tạo mới nếu chưa — quyền do NHÂN quyết, không phải do đây."
        if not self.đã_vào: return {"lỗi": "chưa đăng nhập"}
        self.máy.rt.glob["__đ"] = đường; self.máy.rt.glob["__n"] = nội
        self._giao('đặt __có = gọi(M, V, GH_SOI, [__đ])\n'
                   'nếu loại(__có) == "danh_sách" { đặt __r = gọi(M, V, GH_GHI, [__đ, __n]) }\n'
                   'khác { đặt __r = gọi(M, V, GH_TẠO, [__đ, 644, __n]) }\n'
                   'đặt __lỗi = lỗi_cuối(M)')
        if self._lấy("__r") == "sáng": return {"ok": True, **self.trạng()}
        return {"lỗi": self._lấy("__lỗi") or "không ghi được", **self.trạng()}

    # ---- trạng thái để bàn làm việc vẽ thanh trên + hộp phê duyệt ----
    def trạng(self):
        if not self.đã_vào:
            return {"đã_vào": False}
        self._giao('đặt __ai = gọi(M, V, GH_AI, [])\n'
                   'đặt __nhắc = nhắc(M, V)\n'
                   'đặt __nhịp = lấy_khoá(M, "nhịp")\n'
                   'đặt __cd = lấy_khoá(M, "chờ_duyệt")\n'
                   'đặt __mô = ẩn\n'
                   'nếu loại(__cd) == "ẩn" { } khác { đặt __mô = mô_tả_lệnh(__cd[1], __cd[2]) }\n'
                   'đặt __tt = gọi(M, V, GH_TT, [])')
        ai = self._lấy("__ai") or [None, None]
        return {"đã_vào": True, "uid": ai[0], "tên": ai[1],
                "nhắc": self._lấy("__nhắc"), "nhịp": self._lấy("__nhịp"),
                "chờ_duyệt": self._lấy("__mô"), "tiến_trình": self._lấy("__tt")}


BÀN = None      # dựng lười ở lần gọi đầu (boot mất ~1s)


def _bàn():
    global BÀN
    if BÀN is None: BÀN = Bàn()
    return BÀN


TỆP_TĨNH = {"/": ("de/index.html", "text/html; charset=utf-8"),
            "/de.css": ("de/de.css", "text/css; charset=utf-8"),
            "/de.js": ("de/de.js", "application/javascript; charset=utf-8"),
            "/nha.js": ("de/nha.js", "application/javascript; charset=utf-8")}


class Tay(BaseHTTPRequestHandler):
    server_version = "GIAO-DE"

    def log_message(self, *a): pass          # im lặng — đừng rác màn hình người dùng

    def _gửi(self, mã, thân, kiểu="application/json; charset=utf-8"):
        b = thân if isinstance(thân, bytes) else str(thân).encode("utf-8")
        self.send_response(mã)
        self.send_header("Content-Type", kiểu)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        đường = self.path.split("?", 1)[0]
        if đường in TỆP_TĨNH:
            tên, kiểu = TỆP_TĨNH[đường]
            try:
                with open(os.path.join(HERE, tên), "rb") as f: nội = f.read()
            except OSError:
                return self._gửi(404, "không có " + tên, "text/plain; charset=utf-8")
            return self._gửi(200, nội, kiểu)
        # Ảnh nền của bàn làm việc. Chỉ nhận đúng "/anh/<tên>.jpg" một mức, không có dấu
        # chấm-chấm và không có gạch chéo — nếu không thì đây thành lỗ đọc trộm cả ổ đĩa.
        if đường.startswith("/anh/"):
            tên = đường[5:]
            if tên.endswith(".jpg") and "/" not in tên and "\\" not in tên and ".." not in tên:
                try:
                    with open(os.path.join(HERE, "de", "anh", tên), "rb") as f: nội = f.read()
                except OSError:
                    return self._gửi(404, "không có ảnh " + tên, "text/plain; charset=utf-8")
                return self._gửi(200, nội, "image/jpeg")
        self._gửi(404, "404", "text/plain; charset=utf-8")

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api":
            return self._gửi(404, json.dumps({"lỗi": "đường lạ"}))
        if self.headers.get("X-Giao-Khoa") != KHOÁ:
            return self._gửi(403, json.dumps({"lỗi": "sai khoá phiên"}))
        try:
            n = int(self.headers.get("Content-Length") or 0)
            yc = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return self._gửi(400, json.dumps({"lỗi": "thân yêu cầu hỏng"}))
        việc = yc.get("việc")
        with _ổ:
            try:
                b = _bàn()
                if việc == "trạng":     kq = b.trạng()
                elif việc == "vào":     kq = b.vào(str(yc.get("tên", "")), str(yc.get("mk", "")))
                elif việc == "ra":      kq = b.ra()
                elif việc == "lệnh":    kq = b.lệnh(str(yc.get("dòng", "")))
                elif việc == "thư_mục": kq = b.thư_mục(str(yc.get("đường", "/")))
                elif việc == "đọc":     kq = b.đọc(str(yc.get("đường", "")))
                elif việc == "ghi":     kq = b.ghi(str(yc.get("đường", "")), str(yc.get("nội", "")))
                else:                   kq = {"lỗi": "việc lạ: " + str(việc)}
            except (GiaoError, GiaoLimit, GiaoSyntax) as e:
                kq = {"lỗi": getattr(e, "msg", str(e))}
        self._gửi(200, json.dumps(kq, ensure_ascii=False))


def _cờ(tên, mặc_định=None):
    for i, a in enumerate(sys.argv):
        if a == tên and i + 1 < len(sys.argv): return sys.argv[i + 1]
        if a.startswith(tên + "="): return a.split("=", 1)[1]
    return mặc_định


def main():
    cổng = int(_cờ("--cổng") or _cờ("--cong") or "8088")
    mở = not ("--không-mở" in sys.argv or "--khong-mo" in sys.argv)
    máy_chủ = ThreadingHTTPServer(("127.0.0.1", cổng), Tay)   # 127.0.0.1: KHÔNG ra mạng ngoài
    url = f"http://127.0.0.1:{cổng}/?khoá={KHOÁ}"
    print("┌────────────────────────────────────────────────────────────┐")
    print("│  HĐH-GIAO · BÀN LÀM VIỆC (desktop)                         │")
    print("└────────────────────────────────────────────────────────────┘")
    print(f"  mở đường dẫn này trong trình duyệt (khoá phiên nằm trong đường dẫn):\n\n  {url}\n")
    print("  · chỉ nghe trên 127.0.0.1 — không ra mạng ngoài")
    print("  · đăng nhập bằng chính sổ người dùng của HĐH (an/an · gốc/gốc)")
    print("  · Ctrl-C để tắt máy chủ\n", flush=True)   # in NGAY: người dùng cần đường dẫn tức thì
    # BOOT SẴN nhân ngay lúc máy chủ lên: nếu để lười tới lời gọi đầu thì người dùng bấm
    # "Đăng nhập" rồi ngồi chờ mấy giây không hiểu vì sao. Boot chạy nền, in xong mới báo.
    def _boot():
        with _ổ:
            _bàn()
        print("  [nhân] HĐH-GIAO đã boot — sẵn sàng đăng nhập.\n", flush=True)
    threading.Thread(target=_boot, daemon=True).start()
    if mở:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        máy_chủ.serve_forever()
    except KeyboardInterrupt:
        print("\n[bàn làm việc] tắt.")
    finally:
        máy_chủ.server_close()


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
chay_hdh_giao.py — VÀO HĐH-GIAO BẰNG VỎ TƯƠNG TÁC (gõ lệnh thật, như một terminal Linux)
================================================================================
Máy chủ (Python) ở đây CHỈ làm hai việc của phần cứng: đọc bàn phím, in màn hình.
Toàn bộ hệ điều hành — hệ-tệp, quyền, tiến-trình, gọi-hệ, vỏ, trợ-lý AI — nằm trong GIAO
(`hdh_nền.giao` → lib_gọi_hệ · lib_tệp_hệ · lib_vỏ · lib_trợ_lý).

Chạy:
    python chay_hdh_giao.py                # MÀN HÌNH ĐĂNG NHẬP (mặc định an/an · gốc/gốc)
    python chay_hdh_giao.py --gốc          # chế độ MỘT NGƯỜI DÙNG: vào thẳng uid 0, không hỏi
    python chay_hdh_giao.py --kịch bản.txt # chạy sẵn một tệp kịch bản lệnh rồi thoát

Trong vỏ:  `giúp` xem lệnh · `nhờ <lời nói>` giao việc cho trợ lý AI · `người` xem sổ người dùng ·
           `thành <người>` đổi người · `đổi_mk` đổi mật khẩu · `thoát` đăng xuất · `tắt` tắt máy.

Ba lệnh `thành` · `đổi_mk` và màn hình đăng nhập nằm ở host vì chúng cần TẮT TIẾNG VỌNG bàn phím —
đó là việc của terminal. Phần XÉT (đọc /hệ/mật_khẩu 600, băm, so, sinh phiên dưới đúng uid) nằm
trong `lib_người_dùng.giao`, chạy dưới tiến trình gốc — đúng vai `/bin/login` setuid root.
"""
import os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from giao import tokenize, Parser, Runtime, nạp_chuẩn, GiaoError, GiaoLimit, GiaoSyntax

def _thoát_chuỗi(s):
    "Bọc một dòng người gõ thành hằng chuỗi GIAO an toàn (không cho chèn mã)."
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

class Máy:
    def __init__(self, gốc=False, ảnh=None, kali=False):
        self.rt = Runtime()
        self.rt.base_dir = HERE
        # Một PHIÊN LÀM VIỆC dài (nhiều lệnh, tra $PATH, dò hệ-tệp, trợ lý soạn lệnh) vượt xa trần
        # 5 triệu bước mặc định của trình thông dịch — trần đó để chặn chương trình lạ chạy loạn,
        # không phải để giới hạn chính HĐH. Host nới TƯỜNG MINH ở đây (giống cờ `--bước`).
        self.rt.MAX_STEPS = 200_000_000
        nạp_chuẩn(self.rt)
        self.rt.cấp_quyền("máy")      # HĐH được phép nạp bytecode lên GVM + cướp CPU (tiến trình MÁY)
        # ★ soi-mạng: cấp năng lực HẸP để lệnh `soi-mạng`/`xem-vào`/`theo-dõi` trong vỏ đọc kết quả
        #   soi wifi (so_*.jsonl) và bật/tắt bắt gói qua wsl → Kali. Phạm vi khoá chặt: CHỈ thư mục
        #   soi_mang, CHỈ hai lệnh wsl cụ thể. (object-capability — không nới rộng.)
        self.rt.cấp_quyền("đọc_tệp", gốc=[os.path.join(HERE, "soi_mang")])
        _lệnh_chạy = [
            "wsl -d kali-linux -- bash /mnt/d/HeDieuHanh/GIAO/soi_mang/start_soi.sh",
            "wsl -d kali-linux -- bash /mnt/d/HeDieuHanh/GIAO/soi_mang/tat_soi.sh",
            "wsl -d kali-linux -- bash /mnt/d/HeDieuHanh/GIAO/soi_mang/start_ngat.sh",
        ]
        if kali:
            # ★ Chế độ --kali: cho lệnh vỏ `chạy_thật` / trợ lý gọi được các lệnh hệ nền cơ bản
            #   (bằng TÊN-LỆNH-TRẦN ⇒ mọi đối số). Cổng `phê_duyệt` cho việc BẤT-KHẢ-HỒI vẫn nguyên.
            _lệnh_chạy += [
                # điều tra hệ / tệp
                "whoami","id","uname","hostname","pwd","ls","cat","head","tail","grep","find","which",
                "ps","df","du","free","uptime","date","echo","env","wc","sort","cut","awk","sed",
                # mạng cơ bản
                "ip","ifconfig","ss","netstat","ping","traceroute","tracepath","arp","route",
                "dig","nslookup","host","whois","curl","wget",
                # gói / dịch vụ / phát triển
                "apt","dpkg","systemctl","service","python3","pip3","git","ssh","scp",
            ]
            # ★ Bộ tool bảo mật/tấn công của Kali (bạn chủ ý bật). Thêm/bớt tuỳ ý:
            _lệnh_chạy += [
                "nmap","masscan","arp-scan","netdiscover","tcpdump","tshark","dumpcap",
                "aircrack-ng","airmon-ng","airodump-ng","aireplay-ng","wifite","reaver","bettercap",
                "sqlmap","nikto","gobuster","dirb","feroxbuster","wpscan","whatweb","wafw00f","ffuf",
                "hydra","john","hashcat","medusa","crunch","cewl",
                "msfconsole","msfvenom","searchsploit","setoolkit",
                "enum4linux","smbclient","smbmap","rpcclient","nbtscan","crackmapexec","responder",
                "nc","ncat","netcat","socat","proxychains","iwconfig","iw","mtr",
            ]
        self.rt.cấp_quyền("chạy", lệnh=_lệnh_chạy)
        nền = os.path.join(HERE, "hdh_nền.giao")
        with open(nền, encoding="utf-8") as f:
            self.rt.exec_block(Parser(tokenize(f.read())).parse())
        if ảnh is not None:
            # PHỤC HỒI: vứt máy vừa boot, dựng lại từ ảnh JSON rồi NẠP LẠI MÃ (kho chương trình,
            # trợ lý, thân tiến trình). Python ở đây chỉ đóng vai BỘ ĐIỀU KHIỂN ĐĨA: đọc/ghi byte.
            self.rt.glob["__ảnh"] = ảnh
            self._chạy_giao(
                'đặt M = phục_hồi_máy(__ảnh)\n'
                'nạp_chương_trình(M)\n'
                'lắp_trợ_lý(M, kho_mặc_định())\n'
                'đặt __thân = hồi_sinh(M)\n'
                'đặt V = lấy_khoá(M, "vỏ_hiện")\n'
                'nếu loại(V) == "ẩn" { đặt V = sinh_tt(M, "vỏ", 5, 1000, "/nhà/an") }\n'
                'đặt_trạng(lấy_khoá(lấy_khoá(M, "nhân"), "bảng"), V, "chạy")'
            )
            print(f"[phục hồi] dựng lại {self.rt.glob['__thân']} thân tiến-trình · "
                  f"nhịp máy = {self.rt.glob['M'].d.get('nhịp') if hasattr(self.rt.glob['M'],'d') else '?'}")
        if gốc:                                   # đăng nhập bằng quyền gốc thay vì 'an'
            self._chạy_giao('đặt V = sinh_tt(M, "vỏ", 1, 0, "/")')

    def chụp(self):
        self._chạy_giao("đặt __ảnh_ra = chụp_máy(M)")
        return self.rt.glob["__ảnh_ra"]

    def _chạy_giao(self, mã):
        self.rt.exec_block(Parser(tokenize(mã)).parse())

    def nhắc(self):
        self._chạy_giao("đặt __nhắc = nhắc(M, V)")
        return self.rt.glob["__nhắc"]

    def gõ(self, dòng, lát_nền=6):
        """Đưa một dòng lệnh vào vỏ GIAO; mọi thứ in ra là do chính HĐH in.

        Sau mỗi dòng, nhân được quay `lát_nền` lát: tiến trình nền (dịch vụ, việc đang chạy)
        tiến lên trong lúc người dùng gõ — đúng như máy thật, chứ không đứng hình chờ vỏ.
        """
        self._chạy_giao(f"đặt __kq = chạy_dòng(M, V, {_thoát_chuỗi(dòng)})")
        kq = self.rt.glob["__kq"]
        if lát_nền:
            self._chạy_giao(f"đặt __lát = vòng_nhân(M, {int(lát_nền)})")
        return kq[0] if isinstance(kq, list) else 0

    def còn_sống(self):
        self._chạy_giao('đặt __ts = trạng(lấy_khoá(M, "nhân"), V)')
        return self.rt.glob["__ts"] != "chết"

    # ---------------- ĐĂNG NHẬP ----------------
    # Host ở đây chỉ làm việc của TERMINAL: đọc bàn phím, tắt tiếng vọng khi gõ mật khẩu.
    # Việc XÉT — đọc /hệ/mật_khẩu (600), băm, so, rồi sinh phiên vỏ dưới đúng uid — nằm trong
    # `lib_người_dùng.giao`, chạy dưới tiến trình gốc, đúng vai `/bin/login` setuid root.
    def đăng_nhập(self, tên, mật_khẩu):
        "→ tid phiên vỏ mới · 'sai' nếu sai mật khẩu · 'không-có' nếu không có người ấy"
        self.rt.glob["__tên"] = tên
        self.rt.glob["__mk"] = mật_khẩu
        self._chạy_giao("đặt __v_cũ = V\nđặt __v = đăng_nhập(M, TT_KHỞI, __tên, __mk)")
        v = self.rt.glob["__v"]
        if isinstance(v, int):
            # Vào được rồi mới đóng phiên cũ — sai mật khẩu thì phiên đang dùng KHÔNG hề hấn gì.
            self._chạy_giao(
                'nếu trạng(lấy_khoá(M, "nhân"), __v_cũ) != "chết" '
                '{ gọi(M, __v_cũ, GH_THOÁT, []) }\n'
                'đặt V = __v')
            return v
        return "sai" if v == "tối" else "không-có"

    def đổi_mk(self, cũ, mới, hạt):
        "Đổi mật khẩu của CHÍNH người đang đăng nhập; phải biết mật khẩu cũ."
        self.rt.glob["__cũ"] = cũ; self.rt.glob["__mới"] = mới; self.rt.glob["__hạt"] = hạt
        self._chạy_giao(
            'đặt __r = gọi(M, V, GH_AI, [])\n'
            'đặt __t = __r[1]\n'
            'nếu xác_thực(M, TT_KHỞI, __t, __cũ) == sáng '
            '{ đặt __ok = đặt_mk(M, TT_KHỞI, __t, __mới, __hạt) } khác { đặt __ok = tối }')
        return self.rt.glob["__ok"] == "sáng"

    def tên_hiện(self):
        self._chạy_giao("đặt __r = gọi(M, V, GH_AI, [])")
        return self.rt.glob["__r"][1]

    def danh_sách_người(self):
        self._chạy_giao("đặt __ng = nạp_người(M, V)")
        return self.rt.glob["__ng"]

def _hỏi_kín(nhắc):
    "Đọc mật khẩu KHÔNG hiện lên màn hình. Đây là việc của terminal, nên host làm."
    import getpass
    if not sys.stdin.isatty():              # đầu vào là ĐƯỜNG ỐNG (kịch bản, nghiệm thu)
        return input(nhắc)                  # getpass đọc thẳng console nên sẽ treo — đọc stdin
    try:
        return getpass.getpass(nhắc)
    except (EOFError, KeyboardInterrupt):
        raise
    except Exception:
        return input(nhắc)


def màn_đăng_nhập(máy, lần=3):
    "→ True nếu vào được. Sai ba lần hoặc gõ `tắt` thì thôi."
    máy._chạy_giao('đặt __tm = gọi(M, TT_KHỞI, GH_ĐỌC, ["/hệ/tên_máy"])')
    tên_máy = máy.rt.glob["__tm"]
    # Vỏ do lúc BOOT dựng sẵn (dùng cho chế độ kịch bản) phải tự thoát, kẻo `tt` hiện hai phiên
    # trong khi mới có một người đăng nhập.
    máy._chạy_giao('nếu trạng(lấy_khoá(M, "nhân"), V) != "chết" { gọi(M, V, GH_THOÁT, []) }')
    print(f"\n{tên_máy} · HĐH-GIAO — đăng nhập  (gõ `tắt` để tắt máy)")
    while True:
        for _ in range(lần):
            try:
                ai = input(f"{tên_máy} đăng nhập: ").strip()
            except (EOFError, KeyboardInterrupt):
                print(); return False
            if ai in ("tắt", "tat", "shutdown", "poweroff"): return False
            if not ai: continue
            try:
                mk = _hỏi_kín("mật khẩu: ")
            except (EOFError, KeyboardInterrupt):
                print(); return False
            kq = máy.đăng_nhập(ai, mk)
            if isinstance(kq, int):
                print(f"Xin chào {ai}. Phiên vỏ là tiến-trình {kq}.")
                print("`giúp` xem lệnh · `nhờ <lời nói>` giao việc cho trợ lý · "
                      "`thành <người>` đổi người · `sudo <lệnh>` theo sổ /hệ/sudo · "
                      "`đổi_mk` đổi mật khẩu · `thoát` đăng xuất\n")
                return True
            # KHÔNG nói rõ sai TÊN hay sai MẬT KHẨU — nói rõ là chỉ điểm cho người dò tài khoản.
            print("Sai tên đăng nhập hoặc mật khẩu.")
        print("Sai quá nhiều lần.\n")


def lệnh_thành(máy, tên):
    "su: đổi sang người khác NGAY TRONG phiên — vẫn phải qua mật khẩu."
    try:
        mk = _hỏi_kín(f"mật khẩu của {tên}: ")
    except (EOFError, KeyboardInterrupt):
        print(); return False
    kq = máy.đăng_nhập(tên, mk)
    if isinstance(kq, int):
        print(f"[thành] nay bạn là {tên} · tiến-trình {kq}")
        return True
    print("[thành] sai tên đăng nhập hoặc mật khẩu.")
    return False


def lệnh_sudo(máy, dòng):
    """sudo (C3): chạy MỘT lệnh dưới gốc-quyền, theo SỔ /hệ/sudo.

    Khác `thành` (su): `thành` hỏi mật khẩu NGƯỜI KIA; `sudo` hỏi mật khẩu CỦA CHÍNH BẠN —
    câu hỏi là "anh là ai", không phải "anh có biết bí mật của gốc không". Và khác `duyệt`:
    `duyệt` hỏi "việc này có hoàn tác được không" — nên lệnh bất-khả-hồi CHẠY QUA SUDO
    VẪN bị giữ lại chờ duyệt. Hai cổng bổ nhau, không thay nhau.
    Host ở đây chỉ làm việc của terminal (đọc mật khẩu, tắt tiếng vọng); XÉT — xác thực,
    tra sổ 440, đổi danh tính cho MỘT lệnh — đều trong GIAO."""
    phần = dòng.split(None, 1)
    if len(phần) < 2 or not phần[1].strip():
        print("[sudo] dùng: sudo <lệnh…>"); return
    lệnh_dòng = phần[1].strip()
    tên = máy.tên_hiện()
    if tên == "gốc":                          # đã là gốc thì sudo là thừa — chạy thẳng
        máy.gõ(lệnh_dòng); return
    try:
        mk = _hỏi_kín(f"[sudo] mật khẩu của {tên}: ")
    except (EOFError, KeyboardInterrupt):
        print(); return
    máy.rt.glob["__stên"] = tên; máy.rt.glob["__smk"] = mk
    máy._chạy_giao('đặt __sxt = xác_thực(M, TT_KHỞI, __stên, __smk)')
    if not (máy.rt.glob["__sxt"] == "sáng"):
        print("[sudo] mật khẩu không đúng."); return
    máy.rt.glob["__slệnh"] = lệnh_dòng.split()[0]
    máy._chạy_giao('đặt __sok = sudo_được(M, TT_KHỞI, __stên, __slệnh)')
    ok = máy.rt.glob["__sok"]
    if ok == "ẩn":
        print(f"[sudo] {tên} KHÔNG có trong sổ /hệ/sudo — việc này sẽ được ghi lại."); return
    if ok == "tối":
        print(f"[sudo] sổ /hệ/sudo không cấp cho {tên} lệnh '{lệnh_dòng.split()[0]}'."); return
    # danh tính gốc CHỈ cho MỘT lệnh này — xong là trả lại ngay, kể cả khi lệnh lỗi
    máy.rt.glob["__sdòng"] = lệnh_dòng
    máy._chạy_giao(
        'đặt __sc = lấy_khoá(lấy_khoá(M, "cred"), V)\n'
        'đặt __suid_cũ = lấy_khoá(__sc, "uid")\n'
        'đặt_khoá(__sc, "uid", 0)\n'
        'thử { đặt __skq = chạy_dòng(M, V, __sdòng) } bắt (__sl) { rọi "[sudo] " + __sl }\n'
        'đặt_khoá(__sc, "uid", __suid_cũ)')


def lệnh_đổi_mk(máy):
    "passwd: đổi mật khẩu của chính mình, phải biết mật khẩu cũ."
    try:
        cũ = _hỏi_kín("mật khẩu HIỆN TẠI: ")
        mới = _hỏi_kín("mật khẩu MỚI: ")
        lại = _hỏi_kín("gõ lại mật khẩu MỚI: ")
    except (EOFError, KeyboardInterrupt):
        print(); return
    if mới != lại:
        print("[đổi_mk] hai lần gõ không khớp — chưa đổi gì."); return
    if len(mới) < 4:
        print("[đổi_mk] mật khẩu quá ngắn (cần ≥ 4 ký tự) — chưa đổi gì."); return
    hạt = (int(time.time() * 1000) ^ (os.getpid() << 13)) & 0x7FFFFFFF   # muối cho mỗi lần đổi
    if máy.đổi_mk(cũ, mới, hạt):
        print(f"[đổi_mk] xong — mật khẩu của {máy.tên_hiện()} đã đổi.")
    else:
        print("[đổi_mk] mật khẩu hiện tại không đúng — chưa đổi gì.")


def _cờ_giá_trị(tên):
    "Lấy giá trị của cờ dạng `--tên tệp` hoặc `--tên=tệp`."
    for i, a in enumerate(sys.argv):
        if a == tên and i + 1 < len(sys.argv): return sys.argv[i + 1]
        if a.startswith(tên + "="): return a.split("=", 1)[1]
    return None

def main():
    gốc = "--gốc" in sys.argv or "--goc" in sys.argv
    kali = "--kali" in sys.argv or "--toàn-quyền" in sys.argv or "--toan-quyen" in sys.argv
    tệp_nạp = _cờ_giá_trị("--nạp") or _cờ_giá_trị("--nap")
    tệp_lưu = _cờ_giá_trị("--lưu") or _cờ_giá_trị("--luu")
    kịch = None
    for a in sys.argv[1:]:
        if a.endswith(".txt"): kịch = a

    print("┌────────────────────────────────────────────────────────────┐")
    print("│  HĐH-GIAO · lối Linux · trợ lý AI trong nhân               │")
    print("│  `giúp` xem lệnh · `nhờ <việc nói bằng lời>` · `thoát`     │")
    print("└────────────────────────────────────────────────────────────┘")
    ảnh = None
    if tệp_nạp:
        try:
            with open(tệp_nạp, encoding="utf-8") as f: ảnh = f.read()
            print(f"[đĩa] nạp ảnh hệ điều hành từ {tệp_nạp} ({len(ảnh)} ký tự)")
        except OSError as e:
            print(f"[đĩa] không đọc được {tệp_nạp}: {e}"); sys.exit(1)

    try:
        máy = Máy(gốc=gốc, ảnh=ảnh, kali=kali)
    except (GiaoError, GiaoSyntax, GiaoLimit) as e:
        print(f"[không khởi động được] {getattr(e, 'msg', e)}"); sys.exit(1)

    def lưu_ảnh():
        if not tệp_lưu: return
        try:
            with open(tệp_lưu, "w", encoding="utf-8") as f: f.write(máy.chụp())
            print(f"[đĩa] đã chụp cả hệ điều hành vào {tệp_lưu}")
        except (OSError, GiaoError) as e:
            print(f"[đĩa] không ghi được {tệp_lưu}: {e}")

    if kịch:                                       # chế độ kịch bản (dùng để nghiệm thu)
        with open(kịch, encoding="utf-8") as f:
            for dòng in f:
                dòng = dòng.rstrip("\n")
                if not dòng.strip() or dòng.lstrip().startswith("#"): continue
                print(máy.nhắc() + dòng)
                máy.gõ(dòng)
        lưu_ảnh()
        return

    # ── MÀN HÌNH ĐĂNG NHẬP (bỏ qua bằng --gốc: chế độ MỘT NGƯỜI DÙNG, như single-user của Linux) ──
    if not gốc and not màn_đăng_nhập(máy):
        lưu_ảnh(); print("[HĐH-GIAO] tắt máy."); return
    if gốc:
        print("[chế độ MỘT NGƯỜI DÙNG] vào thẳng quyền gốc, KHÔNG hỏi mật khẩu "
              "— như `init=/bin/sh` của Linux. Chỉ dùng khi ngồi trước máy.")

    while True:
        try:
            dòng = input(máy.nhắc())
        except (EOFError, KeyboardInterrupt):
            print(); lưu_ảnh(); print("[HĐH-GIAO] tạm biệt."); return
        if not dòng.strip(): continue

        đầu = dòng.split()
        if đầu[0] in ("tắt", "tat", "shutdown", "poweroff"):
            lưu_ảnh(); print("[HĐH-GIAO] tắt máy."); return
        if đầu[0] in ("thành", "thanh", "su"):        # đổi người NGAY TRONG phiên
            if not lệnh_thành(máy, đầu[1] if len(đầu) > 1 else "gốc"): pass
            continue
        if đầu[0] == "sudo":                          # C3: một lệnh dưới gốc-quyền, theo sổ /hệ/sudo
            lệnh_sudo(máy, dòng); continue
        if đầu[0] in ("đổi_mk", "doi_mk", "passwd"):
            lệnh_đổi_mk(máy); continue
        try:
            máy.gõ(dòng)
        except GiaoLimit as e:
            print(f"[chặn — an toàn] {e.msg}")
        except GiaoError as e:
            print(f"[lỗi hệ] {e.msg}")
        if not máy.còn_sống():                        # `thoát` = ĐĂNG XUẤT, không phải tắt máy
            print("[HĐH-GIAO] đã đăng xuất.")
            if gốc or not màn_đăng_nhập(máy):
                lưu_ảnh(); print("[HĐH-GIAO] tắt máy."); return

if __name__ == "__main__":
    main()

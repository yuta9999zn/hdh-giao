# -*- coding: utf-8 -*-
"""
nhan_qua_uart.py — NHÂN HĐH-GIAO phục vụ một CPU đang chạy trên **BO FPGA THẬT**, nối bằng UART.
================================================================================
Trên bo không có Python. Nên nhân vẫn ở máy chủ, và cái dây giữa hai bên là **dây đồng**:

    bo FPGA (gvm_bo.v: GVM + cầu UART)  ⟷  /dev/ttyUSBx hoặc COMx  ⟷  nhân GIAO (tệp này)

Đây chính là kiến trúc đã dựng từ đầu — CPU không tự làm I/O, nó chìa lời xin ra rồi CHỜ NHÂN —
chỉ khác là bây giờ CPU là silicon vật lý.

    python hw/nhan_qua_uart.py COM7            # bo thật, cần `pip install pyserial`
    python hw/nhan_qua_uart.py --mô-phỏng      # không có bo: chạy gvm_bo.v trong iverilog

Cùng một lớp `PhiênBo` phục vụ cả hai: chỉ khác cái ống byte.
"""
import os, sys

GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW  = os.path.join(GỐC, "hw")
sys.path.insert(0, GỐC)
from giao import tokenize, Parser, Runtime, nạp_chuẩn

THẺ  = 0x40000000          # bit 30 = con trỏ danh-sách
GỠ   = 0x3FFFFFFF
HEAP = 250                 # ram[250] giữ con trỏ heap của CPU


def dựng_nhân():
    "Nhân HĐH-GIAO thật + một tiến trình uid 1000 đại diện cho CPU trên bo."
    rt = Runtime(); rt.base_dir = GỐC; rt.MAX_STEPS = 200_000_000
    nạp_chuẩn(rt)
    def G(mã): rt.exec_block(Parser(tokenize(mã)).parse())
    G('nhập "lib_vỏ.giao"')
    G('''
đặt M = khởi_máy()
thêm_người(M, 0, "gốc")  thêm_người(M, 1000, "an")
đặt KHỞI = sinh_tt(M, "khởi", 0, 0, "/")
gọi(M, KHỞI, GH_TẠO_THƯ, ["/hệ", 755])   gọi(M, KHỞI, GH_TẠO_THƯ, ["/tạm", 777])
gọi(M, KHỞI, GH_TẠO, ["/hệ/tên_máy", 644, "giao-01"])
gọi(M, KHỞI, GH_TẠO, ["/hệ/mật_khẩu", 600, "gốc:*"])
gọi(M, KHỞI, GH_TẠO, ["/tạm/rác", 666, "bỏ đi được"])
đặt SILIC = sinh_tt(M, "tt-bo", 5, 1000, "/tạm")    # tiến trình chạy trên BO FPGA, uid 1000
''')
    return rt, G


class PhiênBo:
    "Nói chuyện với cầu UART trên bo: đọc/ghi RAM của CPU, phục vụ gọi-hệ."

    def __init__(self, ống, rt, G, kể=True):
        self.ống, self.rt, self.G, self.kể = ống, rt, G, kể
        self.đệm = bytearray()
        self.in_ra = []            # những gì CPU RỌI, đã ghép thành dòng
        self._chuỗi = []
        self.n_xin = 0
        self.dừng = False

    # ── lớp byte ──
    def _lấy(self, n):
        while len(self.đệm) < n:
            k = self.ống.đọc(65536)
            if not k: return None
            self.đệm += k
        ra, self.đệm = bytes(self.đệm[:n]), self.đệm[n:]
        return ra

    @staticmethod
    def _u32(b): return int.from_bytes(b, "little")

    # ── đọc/ghi RAM của CPU qua cầu ──
    def ô_đọc(self, đc):
        self.ống.ghi(bytes([0x4D]) + int(đc).to_bytes(2, "little"))
        while True:                          # bỏ qua các khung RỌI xen vào
            b = self._lấy(1)
            if b is None: return 0
            if b[0] == 0x4D: return self._u32(self._lấy(4))
            self._khung_khác(b[0])

    def ô_ghi(self, đc, v):
        self.ống.ghi(bytes([0x57]) + int(đc).to_bytes(2, "little")
                     + (int(v) & 0xFFFFFFFF).to_bytes(4, "little"))

    def chuỗi_ra(self, p):
        "con trỏ cons trong RAM của CPU → chuỗi Python"
        mã, a = [], p & GỠ
        while a and len(mã) < 4096:
            mã.append(self.ô_đọc(a) & 0x1FFFFF)
            a = self.ô_đọc(a + 1) & GỠ
        return "".join(chr(c) for c in mã)

    def chuỗi_vào(self, s):
        "chuỗi Python → cấp phát cons vào HEAP CỦA CPU, trả con trỏ CÓ THẺ"
        hp = self.ô_đọc(HEAP)
        if hp < 300: hp = 300
        con = 0
        for c in reversed(s):
            self.ô_ghi(hp, ord(c)); self.ô_ghi(hp + 1, con)
            con = hp | THẺ
            hp += 2
        self.ô_ghi(HEAP, hp)
        return con

    # ── khung do bo gửi lên ──
    def _khung_khác(self, mốc):
        if mốc == 0xB5:                                   # CPU RỌI
            kind = self._lấy(1)[0]; dl = self._u32(self._lấy(4))
            if kind == 1: self._chuỗi.append(chr(dl & 0x1FFFFF))
            elif kind == 2:
                dòng = "".join(self._chuỗi); self._chuỗi = []
                self.in_ra.append(dòng)
                if self.kể: print(f"   [CPU-bo] {dòng}")
            else:
                self.in_ra.append(str(dl))
                if self.kể: print(f"   [CPU-bo] {dl}")
        elif mốc == 0xC5:
            self.dừng = True
        # 0xA5 được xử lý ở vòng chính

    def phục_vụ(self, số, đối):
        rt = self.rt
        rt.glob["__số"] = số; rt.glob["__đối"] = list(đối)
        self.G('đặt __kq = gọi(M, SILIC, __số, __đối)')
        self.G('đặt __lỗi = lỗi_cuối(M)')
        return rt.glob["__kq"], rt.glob["__lỗi"]

    def vòng(self, giới_hạn=1000):
        "Vòng chính: nghe bo, phục vụ, trả lời — cho tới khi CPU dừng."
        while not self.dừng and self.n_xin < giới_hạn:
            b = self._lấy(1)
            if b is None: break
            if b[0] != 0xA5:
                self._khung_khác(b[0]); continue

            đầu = self._lấy(14)
            if đầu is None: break
            số, nargs = đầu[0], đầu[1]
            thô = [self._u32(đầu[2 + 4 * i: 6 + 4 * i]) for i in range(3)]
            đối = [self.chuỗi_ra(v) if (v & THẺ) else v for v in thô[:nargs]]

            kq, lỗi = self.phục_vụ(số, đối)
            self.n_xin += 1
            if isinstance(kq, list): kq = " ".join(str(x) for x in kq)
            if isinstance(kq, str) and kq not in ("sáng", "tối"):
                trả = self.chuỗi_vào(kq)
            else:
                trả = (1 if kq == "sáng" else 0 if kq == "tối"
                       else int(kq) if isinstance(kq, (int, float)) else -1) & 0xFFFFFFFF
            self.ống.ghi(bytes([0x5A]) + trả.to_bytes(4, "little"))
            if self.kể:
                nhãn = kq if not isinstance(kq, str) or len(str(kq)) < 44 else str(kq)[:44] + "…"
                print(f"   [NHÂN GIAO] #{self.n_xin} gọi-hệ {số} đối={đối} → {nhãn}"
                      + (f"   ({lỗi})" if lỗi else ""))
        return self.n_xin


class ỐngSerial:
    "Ống byte tới bo THẬT qua cổng COM."
    def __init__(self, cổng, baud=1_000_000):
        import serial                          # pip install pyserial
        self.s = serial.Serial(cổng, baud, timeout=5)
    def đọc(self, n): return self.s.read(1) or b""      # đọc từng byte cho đơn giản
    def ghi(self, b): self.s.write(b); self.s.flush()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    if sys.argv[1] == "--mô-phỏng":
        import lam_bo_mo_phong                  # chạy gvm_bo.v trong iverilog
        sys.exit(lam_bo_mo_phong.chạy())
    rt, G = dựng_nhân()
    print(f"nhân HĐH-GIAO nghe bo ở {sys.argv[1]} …")
    p = PhiênBo(ỐngSerial(sys.argv[1]), rt, G)
    p.vòng()
    print(f"\n{p.n_xin} lời xin đã phục vụ.")
    G('rọi "   /tạm/rác còn không? " + loại(gọi(M, KHỞI, GH_SOI, ["/tạm/rác"]))')

# -*- coding: utf-8 -*-
"""
lam_bitstream.py — ★★★ TỔNG HỢP GVM RA **BITSTREAM FPGA** rồi (nếu có bo) NẠP LÊN SILICON THẬT.
================================================================================
Đường đi cuối cùng của chuỗi:

    GIAO  →  giaoc  →  bytecode GVM  →  gvm.v (RTL)  →  yosys      (tổng hợp: RTL → cổng logic)
                                                     →  nextpnr    (đặt & nối trên chip thật)
                                                     →  ecppack    (đóng gói → .bit)
                                                     →  openFPGALoader (nạp vào FPGA)

Rồi `python hw/nhan_qua_uart.py COMx` cho nhân HĐH-GIAO phục vụ CPU đang chạy trên silicon ấy.

    python hw/lam_bitstream.py                 # tổng hợp + đặt-nối + đóng gói
    python hw/lam_bitstream.py --nạp           # làm nốt: nạp lên bo đang cắm
    python hw/lam_bitstream.py --thiết-bị 25k  # đổi cỡ chip (12k/25k/45k/85k)
"""
import os, re, subprocess, sys, shutil, time

GỐC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW  = os.path.join(GỐC, "hw")
sys.path.insert(0, GỐC)
import giaoc

OSS = os.environ.get("OSS_CAD", r"D:\oss-cad\oss-cad-suite")
BIN = os.path.join(OSS, "bin")
RA  = os.environ.get("GIAO_BIT_RA", os.path.join(HW, "ra"))   # kết quả tổng hợp

# chương trình nằm SẴN TRONG ROM của bitstream — bo vừa cấp điện là chạy, không cần nạp gì thêm
NGUỒN = """
đặt tên = gọi_hệ(0, "/hệ/tên_máy")
rọi tên
đặt ghi = gọi_hệ(2, "/tạm/từ_bo", 644, "dòng này do BO FPGA viết")
rọi ghi
đặt hết = gọi_hệ(0, "/tạm/từ_bo")
rọi hết
đặt mk = gọi_hệ(0, "/hệ/mật_khẩu")
rọi mk
đặt x = gọi_hệ(6, "/tạm/rác")
rọi x
đặt ai = gọi_hệ(12)
rọi ai
"""


def công_cụ(tên):
    p = os.path.join(BIN, tên + ".exe")
    return p if os.path.exists(p) else (shutil.which(tên) or None)


def chạy(lệnh, nhật_ký, mô_tả):
    t = time.time()
    with open(nhật_ký, "w", encoding="utf-8", errors="replace") as f:
        r = subprocess.run(lệnh, stdout=f, stderr=subprocess.STDOUT, cwd=HW,
                           env=dict(os.environ, PATH=BIN + os.pathsep
                                    + os.path.join(OSS, "lib") + os.pathsep + os.environ.get("PATH", "")))
    print(f"   {mô_tả}: {'✓' if r.returncode == 0 else '✗'}  ({time.time() - t:.0f}s)")
    if r.returncode != 0:
        print(open(nhật_ký, encoding="utf-8", errors="replace").read()[-2500:])
    return r.returncode == 0


def main():
    thiết_bị = "85k"
    gói = "CABGA381"
    for i, a in enumerate(sys.argv):
        if a == "--thiết-bị" and i + 1 < len(sys.argv): thiết_bị = sys.argv[i + 1]
    nạp = "--nạp" in sys.argv

    ys, np_, ep = công_cụ("yosys"), công_cụ("nextpnr-ecp5"), công_cụ("ecppack")
    if not (ys and np_ and ep):
        print(f"⚠ chưa có bộ công cụ tổng hợp ở {BIN}.")
        print("  Tải: https://github.com/YosysHQ/oss-cad-suite-build/releases  (giải nén vào ổ D)")
        return 0
    os.makedirs(RA, exist_ok=True)

    print("┌───────────────────────────────────────────────────────────────┐")
    print("│  GIAO → bytecode → RTL → CỔNG LOGIC → BITSTREAM FPGA          │")
    print("└───────────────────────────────────────────────────────────────┘")

    # 0) bytecode vào ROM
    words = giaoc.compile_program(giaoc.Parser(giaoc.tokenize(NGUỒN)).parse(), True)
    with open(os.path.join(HW, "program_bo.hex"), "w") as f:
        f.write("\n".join(f"{w & 0xFFFF:04x}" for w in words) + "\n")
    gv = open(os.path.join(HW, "gvm.v"), encoding="utf-8").read()
    i0 = gv.index("  initial begin"); i1 = gv.index("  // --- CHU KỲ CLOCK")
    open(os.path.join(HW, "gvm_bo_rom.v"), "w", encoding="utf-8").write(
        gv[:i0] + '  initial $readmemh("program_bo.hex", rom);\n\n' + gv[i1:])
    print(f"0) chương trình GIAO → {len(words)} từ-lệnh, nằm SẴN trong ROM của bitstream")

    json_ = os.path.join(RA, "gvm.json")
    cfg   = os.path.join(RA, "gvm.config")
    bit   = os.path.join(RA, "gvm.bit")

    if not chạy([ys, "-p", f"read_verilog gvm_bo_rom.v uart.v gvm_bo.v ulx3s_top.v; "
                          f"synth_ecp5 -top ulx3s_top -json {json_}"],
                os.path.join(RA, "yosys.log"), "1) yosys  — tổng hợp RTL → cổng logic"):
        return 1
    # nextpnr cũng mở tệp bằng API ANSI — chạy được vì đường dẫn dự án nay KHÔNG DẤU.
    if not chạy([np_, f"--{thiết_bị}", "--package", gói, "--json", json_,
                 "--lpf", os.path.join(HW, "ulx3s.lpf"), "--textcfg", cfg,
                 "--lpf-allow-unconstrained"],
                os.path.join(RA, "nextpnr.log"), "2) nextpnr — đặt & nối trên chip thật"):
        return 1
    if not chạy([ep, cfg, "--bit", bit], os.path.join(RA, "ecppack.log"),
                "3) ecppack — đóng gói thành bitstream"):
        return 1

    # ── báo cáo tài nguyên + tần số ──
    nx = open(os.path.join(RA, "nextpnr.log"), encoding="utf-8", errors="replace").read()
    print("\n════ CHIẾM DỤNG TRÊN CHIP ════")
    for tên in ("TRELLIS_COMB", "TRELLIS_FF", "TRELLIS_RAMW", "DP16KD", "MULT18X18D", "DCCA"):
        m = re.search(rf"{tên}:\s+(\d+)/\s*(\d+)\s+(\d+)%", nx)
        if m: print(f"   {tên:14s} {int(m.group(1)):6d} / {int(m.group(2)):6d}   {m.group(3)}%")
    m = re.search(r"Max frequency for clock\s+'[^']*':\s+([\d.]+)\s*MHz", nx)
    if m: print(f"\n   tần số tối đa: {m.group(1)} MHz  (thiết kế chạy ở 25 MHz)")
    print(f"\n   bitstream: {bit}  ({os.path.getsize(bit)} byte)")

    if not nạp:
        print("\n→ Bitstream đã xong. Cắm bo rồi chạy:")
        print("     python hw/lam_bitstream.py --nạp")
        print("     python hw/nhan_qua_uart.py COMx        # nhân GIAO phục vụ CPU trên silicon")
        return 0

    ofl = công_cụ("openFPGALoader")
    if not ofl:
        print("⚠ không thấy openFPGALoader."); return 1
    r = subprocess.run([ofl, "-b", "ulx3s", bit], capture_output=True, text=True, cwd=HW)
    print(r.stdout + r.stderr)
    if r.returncode != 0:
        print("✗ nạp không được — thường là CHƯA CẮM BO (hoặc thiếu driver WinUSB cho FTDI).")
        return 1
    print("✓ đã nạp lên bo. Giờ chạy:  python hw/nhan_qua_uart.py COMx")
    return 0


if __name__ == "__main__":
    sys.exit(main())

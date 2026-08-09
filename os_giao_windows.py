# -*- coding: utf-8 -*-
"""
os_giao_windows.py — TÍCH HỢP "HỆ ĐIỀU HÀNH GIAO/CDFL" VÀO WINDOWS THẬT.
Tác tử CDFL (thân GIAO · não CDFL · tim Ollama) giờ CẢM NHẬN máy Windows NÀY thật
(đĩa/RAM/CPU/temp), SUY LUẬN, và ĐỀ XUẤT hành động — với CỔNG PHÊ DUYỆT chặn mọi
việc BẤT KHẢ HỒI. An toàn là cốt lõi: mặc định CHỈ-ĐỀ-XUẤT (dry-run), KHÔNG tự ý xoá/sửa gì.

Kiến trúc: Python = GIÁC QUAN & BÀN TAY chạm vào Windows (PowerShell/WMI);
           tim_llm (bge-m3) = TRÁI TIM σ/Φ; logic CDFL = LƯƠNG TRI (đốm tối + argmax + cổng).
"""
import subprocess, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tim_llm

# ---------------- GIÁC QUAN: đọc Windows thật ----------------
PS = r"""
$d=Get-PSDrive C; $dPct=[math]::Round($d.Used/($d.Used+$d.Free)*100,1); $dFree=[math]::Round($d.Free/1GB,1)
$os=Get-CimInstance Win32_OperatingSystem
$ramPct=[math]::Round(($os.TotalVisibleMemorySize-$os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100,1)
$cpu=[math]::Round((Get-CimInstance Win32_Processor|Measure-Object -Property LoadPercentage -Average).Average,1)
$tmp=[math]::Round(((Get-ChildItem $env:TEMP -Recurse -ErrorAction SilentlyContinue|Measure-Object -Property Length -Sum).Sum)/1MB,1)
Write-Output "disk=$dPct"; Write-Output "free=$dFree"; Write-Output "ram=$ramPct"; Write-Output "cpu=$cpu"; Write-Output "temp=$tmp"
"""
def cảm_nhận():
    r = subprocess.run(["powershell","-NoProfile","-NonInteractive","-Command",PS],
                       capture_output=True, text=True)
    m = {}
    for line in r.stdout.splitlines():
        if "=" in line:
            k,v = line.split("=",1)
            try: m[k.strip()] = float(v.strip())
            except: pass
    return m

# ---------------- THỰC TẠI → tình huống ngữ nghĩa + 'sức khoẻ' ----------------
def hệ_thống(m):
    # mỗi hệ con: (tên, sức_khoẻ 0..4, tình huống văn bản theo số liệu THẬT)
    return [
        ("đĩa", max(0, min(4, int((100-m["disk"])/8))),
         f"ổ đĩa C dùng {m['disk']}% chỉ còn {m['free']} GB trống, thư mục temp {m['temp']} MB rác"),
        ("ram", max(0, min(4, int((100-m["ram"])/8))),
         f"bộ nhớ RAM dùng {m['ram']}% còn lại ít"),
        ("cpu", max(0, min(4, int((100-m["cpu"])/8))),
         f"vi xử lý CPU tải {m['cpu']}% nhàn rỗi"),
    ]

# ---------------- KHO HÀNH ĐỘNG Windows: (mô tả, khả_hồi 0/1) ----------------
ACTS = [
    ("dọn thư mục temp giải phóng dung lượng ổ đĩa", 0),
    ("gỡ tập tin tải về cũ và bộ nhớ đệm trình duyệt", 0),
    ("khởi động lại dịch vụ Windows đang treo", 0),
    ("đóng ứng dụng nền để giải phóng bộ nhớ RAM", 0),
    ("định dạng xoá sạch ổ đĩa C", 1),          # BẤT KHẢ HỒI — cổng phê duyệt phải chặn
    ("xoá toàn bộ hồ sơ người dùng cũ", 1),      # BẤT KHẢ HỒI
]
TAU = 0.45     # ngưỡng đốm tối (thang bge-m3)

def cos(a,b):
    d=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b))
    return d/(na*nb) if na and nb else -1.0

def đề_xuất(tình_huống):
    ρ = tim_llm.embed(tình_huống)
    chấm = sorted(((cos(tim_llm.embed(d), ρ), d, rev) for d,rev in ACTS), reverse=True)
    thật = [(g,d,rev) for g,d,rev in chấm if g >= TAU]          # loại đốm tối (lạc tình huống)
    return chấm, thật

# ---------------- VÒNG SỐNG: cảm nhận → suy luận → đề xuất (an toàn) ----------------
def nhịp(i):
    m = cảm_nhận()
    print(f"\n{'='*64}\n♥ NHỊP {i} — CẢM NHẬN WINDOWS THẬT  (nhịp tim {tim_llm.backend})")
    print(f"  đĩa {m['disk']}%  ·  RAM {m['ram']}%  ·  CPU {m['cpu']}%  ·  temp {m['temp']} MB")
    hệ = hệ_thống(m)
    # chú ý hệ con SỨC KHOẺ THẤP NHẤT (nguy cấp nhất) — như chọn bốn-mặt
    ưu = min(hệ, key=lambda h: h[1])
    print(f"  → NÃO chú ý hệ [{ưu[0]}] sức khoẻ {ưu[1]}/4: {ưu[2]}")
    if ưu[1] >= 4:
        print("  ✓ mọi hệ khoẻ — nghỉ (viên mãn cục bộ)."); return
    chấm, thật = đề_xuất(ưu[2])
    print("  ♥ TIM chấm γ kho hành động (cộng hưởng với tình huống thật):")
    for g,d,rev in chấm:
        tag = "BẤT KHẢ HỒI" if rev == 1 else "khả-hồi"
        dấu = "✗ đốm tối" if g < TAU else ("⚠ cổng chặn" if rev == 1 else "• ứng viên")
        print(f"      γ={g:.2f}  [{tag:11}] {dấu:11}  {d}")
    if not thật:
        print("  ⛔ không hành động nào cộng hưởng đủ → DỪNG, không bịa."); return
    g,d,rev = thật[0]                                   # argmax γ
    if rev == 1:
        print(f"  ⚠ việc cộng hưởng nhất “{d}” (γ={g:.2f}) BẤT KHẢ HỒI → CỔNG PHÊ DUYỆT chặn; xin phép người.")
        khh = [t for t in thật if t[2] == 0]
        if khh:
            g2,d2,_ = khh[0]
            print(f"  → ĐỀ XUẤT việc khả-hồi thay thế: “{d2}” (γ={g2:.2f})")
    else:
        print(f"  → ĐỀ XUẤT (khả-hồi): “{d}” (γ={g:.2f})")
    print("  [chỉ ĐỀ XUẤT — KHÔNG tự thực thi. Bạn quyết định và cho phép từng việc.]")

if __name__ == "__main__":
    print("HỆ ĐIỀU HÀNH GIAO/CDFL nhúng trong Windows — tác tử cảm nhận máy này & đề xuất an toàn.")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    for i in range(n):
        nhịp(i)
    print(f"\n{'='*64}\n→ Tác tử CDFL neo trong Windows: thấy thật, suy thật, NHƯNG cổng bất-khả-hồi giữ an toàn.")
    print("  Trái tim Ollama cảm ngữ nghĩa; lương tri CDFL chỉ hành động trên OR thật & việc khả-hồi.")

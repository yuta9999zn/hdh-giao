#!/bin/sh
# kiem_goi.sh — nghiệm thu BỘ CÔNG CỤ LÀM GÓI (goi.giao trên GVM-64). KHÔNG Python.
#   sh kiem_goi.sh
#  ① kho thật goi/: lint 0 lỗi · thử MỌI gói (cài qua đường thật trong HĐH sạch) đều đạt · dựng kho ký kép
#  ② gói XẤU (thư mục tạm): lint phải bắt đúng từng lỗi — năng lực nhạy cảm không khai · lệnh lạ · gọi gói
#     không khai phụ thuộc · vòng phụ thuộc · công cụ an ninh dùng `xoá` · trùng tên lệnh hệ thống ·
#     thiếu kiểm thử · phiên/nhóm/giấy phép sai
#  ③ moi: tạo khung gói hợp lệ ngay (lint 0 lỗi, thử đạt)
cd "$(dirname "$0")"
DAT=0; ROT=0
ca() { if [ "$1" = 0 ]; then DAT=$((DAT+1)); echo "  ✓ $2"; else ROT=$((ROT+1)); echo "  ✗ $2"; [ -n "$3" ] && echo "$3" | tail -5 | sed 's/^/      /'; fi; }
co() { printf '%s' "$1" | grep -qF -- "$2"; echo $?; }

echo "[① kho thật goi/]"
O="$(sh goi.sh kiem 2>&1)"; ca "$(co "$O" " 0 lỗi")" "lint: $(printf '%s' "$O" | grep 'LINT GÓI')" "$O"
O="$(sh goi.sh thu 2>&1)"; M=$?
ca "$( [ $M = 0 ] && co "$O" "THỬ GÓI:" || echo 1)" "thử: $(printf '%s' "$O" | grep 'THỬ GÓI')" "$O"
TM="$(mktemp -d)"
[ -f .khoa/kho_goi/rieng.txt ] || sh goi.sh khoa > /dev/null
O="$(GOI_RA="$TM/kho" sh goi.sh dung 2>&1)"
ca "$( [ -f "$TM/kho/mục_lục" ] && [ -f "$TM/kho/chữ_ký" ] && grep -q '^kép|' "$TM/kho/chữ_ký" && co "$O" "ký kép" || echo 1)" \
   "dựng kho: $(printf '%s' "$O" | tail -1)" "$O"

O="$(GOI_NGUON=goi_xa sh goi.sh thu 2>&1)"; M=$?
ca "$( [ $M = 0 ] && co "$O" "THỬ GÓI: 5/5" || echo 1)" "kho xa goi_xa/: $(printf '%s' "$O" | grep 'THỬ GÓI')" "$O"
O="$(sh goi.sh nen_kiem 2>&1)"
ca "$(co "$O" "✓ kho_nen.giao khớp goi/")" "kho nhúng sẵn kho_nen.giao khớp goi/ + đúng chữ ký kép" "$O"

echo "[② gói XẤU — lint phải bắt]"
X="$TM/xau"; mkdir -p "$X"
g() { mkdir -p "$X/$1"; printf 'tên: %s\nphiên: %s\nnhóm: %s\nmô_tả: thử\ngiấy_phép: %s\nphụ_thuộc: %s\nnăng_lực: %s\n' "$1" "$2" "$3" "$4" "$5" "$6" > "$X/$1/GOI"
      printf '%s\n' "$7" > "$X/$1/than"; [ -n "$8" ] && printf 'chạy: %s\nchứa: x\n' "$1" > "$X/$1/kiem"; return 0; }
g xoá_lén   1.0 tệp Apache-2.0 "" ""     'xoá $1'                     k
g lệnh_lạ   1.0 tệp Apache-2.0 "" ""     'nmap 10.0.0.1'              k
g gọi_lén   1.0 tệp Apache-2.0 "" ""     'xoá_lén /tạm/a'             k
g vòng_a    1.0 tệp Apache-2.0 vòng_b "" 'nói a'                      k
g vòng_b    1.0 tệp Apache-2.0 vòng_a "" 'nói b'                      k
g an_xoá    1.0 an-ninh/kiểm-toán Apache-2.0 "" xoá 'xoá $1'          k
g liệt      1.0 tệp Apache-2.0 "" ""     'nói trùng'                  k
g không_kiểm 1.0 tệp Apache-2.0 "" ""    'nói chưa kiểm'              ""
g sai_meta  1    lạ  WTFPL "" ""         'nói meta'                   k
O="$(GOI_NGUON="$X" sh goi.sh kiem 2>&1)"
ca "$(co "$O" "xoá_lén: than dùng lệnh đòi năng lực NHẠY CẢM 'xoá' mà KHÔNG khai")" "năng lực nhạy cảm không khai ⇒ lỗi"
ca "$(co "$O" "lệnh_lạ: than dòng 1: lệnh 'nmap' không có")" "lệnh lạ (không phải lệnh vỏ/gói) ⇒ lỗi"
ca "$(co "$O" "gọi_lén: than dòng 1: gọi gói 'xoá_lén' mà KHÔNG khai phụ thuộc")" "gọi gói khác mà không khai phụ thuộc ⇒ lỗi"
ca "$(co "$O" "VÒNG phụ thuộc: vòng_a → vòng_b → vòng_a")" "vòng phụ thuộc ⇒ lỗi"
ca "$(co "$O" "an_xoá: công cụ AN NINH PHÒNG THỦ chỉ được soi/đọc/báo cáo")" "công cụ an ninh dùng xoá ⇒ lỗi (chính sách phòng thủ)"
ca "$(co "$O" "liệt: tên TRÙNG lệnh có sẵn của vỏ")" "trùng tên lệnh hệ thống ⇒ lỗi"
ca "$(co "$O" "không_kiểm: thiếu kiểm thử")" "thiếu kiểm thử ⇒ lỗi"
ca "$(co "$O" "sai_meta: phiên '1' phải dạng")" "phiên sai ⇒ lỗi"
ca "$(co "$O" "sai_meta: nhóm 'lạ' lạ")" "nhóm lạ ⇒ lỗi"
ca "$(co "$O" "sai_meta: giấy phép 'WTFPL'")" "giấy phép ngoài danh sách SPDX nhận ⇒ lỗi"
O2="$(GOI_NGUON="$X" GOI_RA="$TM/kho_xau" sh goi.sh dung 2>&1)"
ca "$( [ ! -f "$TM/kho_xau/mục_lục" ] && co "$O2" "lint còn lỗi" || echo 1)" "lint còn lỗi ⇒ KHÔNG dựng kho"

echo "[③ moi — khung gói mới hợp lệ ngay]"
N="$TM/moi"; mkdir -p "$N"
GOI_NGUON="$N" sh goi.sh moi gói_mới tệp gói mẫu từ khung > /dev/null 2>&1
O="$(GOI_NGUON="$N" sh goi.sh kiem 2>&1)"; O3="$(GOI_NGUON="$N" sh goi.sh thu 2>&1)"
R=1; [ -f "$N/gói_mới/GOI" ] && [ "$(co "$O" " 0 lỗi")" = 0 ] && [ "$(co "$O3" "THỬ GÓI: 2/2")" = 0 ] && R=0
ca "$R" "moi tạo khung: lint 0 lỗi, thử đạt (gói + siêu-gói bộ_tệp)" "$O$O3"
rm -rf "$TM"
echo; echo "BỘ CÔNG CỤ GÓI: $DAT/$((DAT+ROT))"
[ $ROT = 0 ]

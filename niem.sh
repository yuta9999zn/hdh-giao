#!/bin/sh
# niem.sh — chạy SỔ NIÊM PHONG viết bằng GIAO (niem_phong.giao) trên GVM-64. KHÔNG Python.
#   sh niem.sh niem <sổ> <ai> <việc> <dự_đoán JSON>   ·   sh niem.sh cham <sổ> <băm> <kết_quả JSON>
#   sh niem.sh kiem <sổ> [--bat-buoc-ky]               ·   sh niem.sh thong_ke <sổ>
#   sh niem.sh khoa | cong | ghim_khoa | ky <băm>      (cờ chung: --khong-ky)
# Biến: GIAO_KHOA_NIEM_PHONG (thư mục khoá, mặc định .khoa/niem_phong) · GIAO_GHIM_KHOA_NIEM_PHONG (tệp ghim,
# mặc định khoa_niem_phong.ghim) — y như niem_phong.py cũ.
# Việc của script: gói sổ + khoá + ghim + đối số vào stdin; dòng "@@NỐI<TAB>@sổ<TAB>b64" ⇒ NỐI vào cuối sổ
# (chỉ-ghi-thêm); "@@TỆP<TAB>@khoá/…|@ghim<TAB>b64" ⇒ ghi tệp khoá/ghim; dòng khác in ra.
# Đồng hồ: cấp --cho-giờ cho máy (trường "lúc" của mục sổ) — năng lực hẹp, chỉ ở công cụ này.
set -e
GIAO="$(cd "$(dirname "$0")" && pwd)"
WT="${WASMTIME:-$(command -v wasmtime || echo /d/wasmtime/wasmtime.exe)}"
[ $# -ge 1 ] || { sed -n '2,5p' "$0" >&2; exit 2; }
DEM="$GIAO/__pycache__"; mkdir -p "$DEM"
G64="$DEM/niem_phong.g64"
if [ ! -f "$G64" ] || [ -n "$(find "$GIAO" -maxdepth 1 -name '*.giao' -newer "$G64" | head -1)" ]; then
  (cd "$GIAO" && sh tu_bien_dich.sh niem_phong.giao > "$G64.tmp") || { rm -f "$G64.tmp"; exit 4; }
  mv "$G64.tmp" "$G64"
fi
KD="${GIAO_KHOA_NIEM_PHONG:-$GIAO/.khoa/niem_phong}"
GHIM="${GIAO_GHIM_KHOA_NIEM_PHONG:-$GIAO/khoa_niem_phong.ghim}"
RA="$DEM/niem.ra.$$"
mkdir -p "$RA.d"
trap 'rm -rf "$RA" "$RA.d"' EXIT
# tách cờ khỏi đối số vị trí; đối số vị trí ghi ra tệp (giữ nguyên byte, kể cả xuống dòng)
VIEC="$1"; shift; SO=""; n=0; CO=""
case "$VIEC" in niem|cham|kiem|thong_ke) [ $# -ge 1 ] || { echo "niem.sh $VIEC: thiếu <sổ>" >&2; exit 2; }; SO="$1"; shift ;; esac
for a in "$@"; do
  case "$a" in
    --khong-ky) printf x > "$RA.d/khongky" ;;
    --bat-buoc-ky) printf x > "$RA.d/batbuoc" ;;
    *) n=$((n+1)); printf '%s' "$a" > "$RA.d/d$n" ;;
  esac
done
[ "${GIAO_NIEM_PHONG_KY:-1}" = 0 ] && printf x > "$RA.d/khongky"
A2="$GIAO/wasm/argon2.wasm"; KM="$GIAO/wasm/ky.wasm"
for cap in "argon2.sha256 wasm/argon2.wasm $A2" "ky.sha256 wasm/ky.wasm $KM"; do
  set -- $cap
  KY="$(grep " $2\$" "$GIAO/wasm/$1" | cut -d' ' -f1)"; THAT="$(sha256sum "$3" | cut -d' ' -f1)"
  [ -n "$KY" ] && [ "$KY" = "$THAT" ] || { echo "[niem] $3 KHÁC ghim — từ chối nạp" >&2; exit 3; }
done
muc() { printf '\000%s %s\n' "$(wc -c < "$1" | tr -d ' ')" "$2"; cat "$1"; }
MA=0
{
  cat "$G64"
  printf '%s' "$VIEC" > "$RA.d/lenh"; muc "$RA.d/lenh" "@lệnh"
  i=1; while [ $i -le $n ]; do muc "$RA.d/d$i" "@đ$i"; i=$((i+1)); done
  [ -f "$RA.d/khongky" ] && muc "$RA.d/khongky" "@không_ký"
  [ -f "$RA.d/batbuoc" ] && muc "$RA.d/batbuoc" "@bắt_buộc_ký"
  [ -n "$SO" ] && [ -f "$SO" ] && muc "$SO" "@sổ"
  [ -f "$KD/bi_mat.json" ] && muc "$KD/bi_mat.json" "@bí_mật"
  [ -f "$KD/cong_khai.json" ] && muc "$KD/cong_khai.json" "@công"
  [ -f "$GHIM" ] && muc "$GHIM" "@ghim"
  true
} | "$WT" run --preload "argon2=$A2" --preload "ky=$KM" "$GIAO/wasm/gvm64.wasm" -- \
      --bước 40000000000 --trần-ds 200000000 --cho-giờ > "$RA" || MA=$?
TAB="$(printf '\t')"
while IFS= read -r dong || [ -n "$dong" ]; do
  case "$dong" in
    "@@NỐI$TAB@sổ$TAB"*)
      [ -n "$SO" ] || continue
      mkdir -p "$(dirname "$SO")"
      printf '%s' "${dong#@@NỐI$TAB@sổ$TAB}" | base64 -d >> "$SO" ;;
    "@@TỆP$TAB"*)
      rest="${dong#@@TỆP$TAB}"; duong="${rest%%$TAB*}"; b64="${rest#*$TAB}"
      case "$duong" in
        @khoá/bi_mat.json|@khoá/cong_khai.json) dich="$KD/${duong#@khoá/}" ;;
        @ghim) dich="$GHIM" ;;
        *) echo "[niem] từ chối ghi đường lạ: $duong" >&2; continue ;;
      esac
      mkdir -p "$(dirname "$dich")"
      printf '%s' "$b64" | base64 -d > "$dich"
      case "$dich" in *bi_mat*) chmod 600 "$dich" 2>/dev/null || true ;; esac ;;
    *) printf '%s\n' "$dong" ;;
  esac
done < "$RA"
exit $MA

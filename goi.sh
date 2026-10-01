#!/bin/sh
# goi.sh — chạy BỘ CÔNG CỤ LÀM GÓI viết bằng GIAO (goi.giao) trên GVM-64. KHÔNG Python.
#   sh goi.sh liet | kiem [tên…] | thu [tên…] | khoa | dung | moi <tên> <nhóm> <mô tả…> | khoa_may | nen | nen_kiem
# Việc của script này CHỈ là vào/ra tệp (máy không thấy thư mục nào):
#   ① dịch goi.giao bằng trình biên dịch tự thân (tu_bien_dich.sh) — đệm ở __pycache__/goi.g64;
#   ② gói goi/*/{GOI,than,kiem} (+ khoá riêng của kho khi `dung`) + "@lệnh" vào stdin
#      (mỗi mục: NUL + số_byte + " " + đường + "\n" + nội dung);
#   ③ chạy trên gvm64.wasm (kiểm ghim argon2.wasm + ky.wasm như tu_bien_dich.sh);
#   ④ dòng "@@TỆP<TAB>đường<TAB>base64" → ghi tệp (CHỈ dưới goi/, kho_dung/, .khoa/kho_goi/); dòng khác in ra.
set -e
GIAO="$(cd "$(dirname "$0")" && pwd)"
cd "$GIAO"
WT="${WASMTIME:-$(command -v wasmtime || echo /d/wasmtime/wasmtime.exe)}"
[ $# -ge 1 ] || { sed -n '2,3p' "$0" >&2; exit 2; }
DEM="$GIAO/__pycache__"; mkdir -p "$DEM"
G64="$DEM/goi.g64"
# dịch lại khi goi.giao hoặc thư viện nó dùng mới hơn bản đệm (đơn giản: so với mọi *.giao ở gốc)
if [ ! -f "$G64" ] || [ -n "$(find . -maxdepth 1 -name '*.giao' -newer "$G64" | head -1)" ]; then
  sh "$GIAO/tu_bien_dich.sh" goi.giao > "$G64.tmp" && mv "$G64.tmp" "$G64"
fi
LENH="$*"
# ghim module nạp kèm (giống tu_bien_dich.sh)
A2="$GIAO/wasm/argon2.wasm"; KM="$GIAO/wasm/ky.wasm"
for cap in "argon2.sha256 wasm/argon2.wasm $A2" "ky.sha256 wasm/ky.wasm $KM"; do
  set -- $cap
  KY="$(grep " $2\$" "$GIAO/wasm/$1" | cut -d' ' -f1)"; THAT="$(sha256sum "$3" | cut -d' ' -f1)"
  [ -n "$KY" ] && [ "$KY" = "$THAT" ] || { echo "[goi] $3 KHÁC ghim — từ chối nạp" >&2; exit 3; }
done
muc() { printf '\000%s %s\n' "$(wc -c < "$1" | tr -d ' ')" "$2"; cat "$1"; }
RA="$DEM/goi.ra.$$"
{
  cat "$G64"
  printf '%s' "$LENH" > "$RA.lenh"; muc "$RA.lenh" "@lệnh"; rm -f "$RA.lenh"
  # GOI_NGUON (kiểm thử): thư mục gói nguồn khác goi/ — tên trong gói vào vẫn là goi/<tên>/…
  for d in "${GOI_NGUON:-goi}"/*/; do
    [ -d "$d" ] || continue
    t="$(basename "$d")"
    for f in GOI than kiem; do [ -f "$d$f" ] && muc "$d$f" "goi/$t/$f"; done
  done
  # GOI_KHOA: thư mục khoá của kho (mặc định .khoa/kho_goi) — kho xa dùng khoá RIÊNG của nó
  KD="${GOI_KHOA:-.khoa/kho_goi}"
  case "$LENH" in dung*|nen) [ -f "$KD/rieng.txt" ] && muc "$KD/rieng.txt" "@khoá_riêng" ;; esac
  case "$LENH" in nen_kiem*) [ -f kho_nen.giao ] && muc kho_nen.giao "@kho_nen" ;; esac
} | "$WT" run --preload "argon2=$A2" --preload "ky=$KM" "$GIAO/wasm/gvm64.wasm" -- \
      --bước 40000000000 --trần-ds 200000000 > "$RA" || MA=$?
TAB="$(printf '\t')"
while IFS= read -r dong || [ -n "$dong" ]; do
  case "$dong" in
    "@@TỆP$TAB"*)
      rest="${dong#@@TỆP$TAB}"; duong="${rest%%$TAB*}"; b64="${rest#*$TAB}"
      case "$duong" in *..*|/*) echo "[goi] từ chối ghi đường lạ: $duong" >&2; continue ;; esac
      case "$duong" in goi/*|kho_dung/*|.khoa/kho_goi/*|khoa_may.txt|khoa_may_cong.txt|kho_nen.giao) ;; *) echo "[goi] từ chối ghi ngoài vùng cho phép: $duong" >&2; continue ;; esac
      # GOI_NGUON / GOI_RA / GOI_KHOA: ánh xạ goi/…, kho_dung/…, .khoa/kho_goi/… sang thư mục khác
      case "$duong" in goi/*) duong="${GOI_NGUON:-goi}/${duong#goi/}" ;; kho_dung/*) duong="${GOI_RA:-kho_dung}/${duong#kho_dung/}" ;;
                       .khoa/kho_goi/*) duong="${GOI_KHOA:-.khoa/kho_goi}/${duong#.khoa/kho_goi/}" ;; esac
      mkdir -p "$(dirname "$duong")"
      printf '%s' "$b64" | base64 -d > "$duong"
      case "$duong" in *rieng*|khoa_may.txt) chmod 600 "$duong" 2>/dev/null || true ;; esac
      echo "  → $duong" ;;
    *) printf '%s\n' "$dong" ;;
  esac
done < "$RA"
rm -f "$RA"
exit ${MA:-0}

#!/bin/sh
# tu_bien_dich.sh — BIÊN DỊCH GIAO BẰNG CHÍNH GIAO: giaoc64.giao chạy trên GVM-64 (wasmtime), KHÔNG Python.
#   sh tu_bien_dich.sh chương_trình.giao > chương_trình.g64
# Máy không thấy thư mục nào: script này gói tệp chính + mọi tệp nó `nhập` (bao đóng, trong thư mục
# của tệp chính) + chuẩn.giao + _cdfl.giao vào stdin, ngay sau giaoc64_tu.g64 (trình biên dịch đã dịch).
# Định dạng gói: mỗi mục = NUL + số_byte + " " + đường_dẫn + "\n" + ĐÚNG số_byte byte nội dung (đếm độ
# dài nên nội dung chứa gì cũng được — lib_dia.giao có byte NUL). Cần: sh, cat, grep, sed, wc, realpath.
set -e
GIAO="$(cd "$(dirname "$0")" && pwd)"
WT="${WASMTIME:-$(command -v wasmtime || echo /d/wasmtime/wasmtime.exe)}"
TU="${GIAOC64_TU:-$GIAO/wasm/giaoc64_tu.g64}"
[ $# -ge 1 ] || { echo "dùng: sh tu_bien_dich.sh tệp.giao > tệp.g64" >&2; exit 2; }
# Kiểm GHIM SHA-256 của argon2.wasm TRƯỚC khi nạp (wasm/argon2.sha256) — lệch thì từ chối, không chạy.
A2="${GIAO_ARGON2_WASM:-$GIAO/wasm/argon2.wasm}"
KY="$(grep ' wasm/argon2.wasm$' "$GIAO/wasm/argon2.sha256" | cut -d' ' -f1)"
THAT="$(sha256sum "$A2" | cut -d' ' -f1)"
[ -n "$KY" ] && [ "$KY" = "$THAT" ] || { echo "[tu_bien_dich] $A2: SHA-256 $THAT KHÁC ghim $KY — từ chối nạp" >&2; exit 3; }
CHINH="$1"; GOC="$(cd "$(dirname "$CHINH")" && pwd)"; TEN="$(basename "$CHINH")"
DS="$TEN"; CHO="$TEN"
while [ -n "$CHO" ]; do                       # bao đóng các tệp được `nhập` (tương đối thư mục gốc)
  MOI=""
  for f in $CHO; do
    d="$(dirname "$f")"
    for p in $(grep -ao 'nhập "[^"]*"' "$GOC/$f" 2>/dev/null | sed 's/^nhập "//; s/"$//'); do
      r="$(cd "$GOC" && realpath -m --relative-to=. "$d/$p")"
      [ -f "$GOC/$r" ] || continue
      case " $DS " in *" $r "*) ;; *) DS="$DS $r"; MOI="$MOI $r";; esac
    done
  done
  CHO="$MOI"
done
{
  cat "$TU"
  for f in $DS; do printf '\000%s %s\n' "$(wc -c < "$GOC/$f" | tr -d ' ')" "$f"; cat "$GOC/$f"; done
  printf '\000%s @chuẩn.giao\n' "$(wc -c < "$GIAO/chuẩn.giao" | tr -d ' ')"; cat "$GIAO/chuẩn.giao"
  printf '\000%s @_cdfl.giao\n' "$(wc -c < "$GIAO/_cdfl.giao" | tr -d ' ')"; cat "$GIAO/_cdfl.giao"
} | "$WT" run --preload "argon2=$A2" "$GIAO/wasm/gvm64.wasm" -- --bước 4000000000 --trần-ds 200000000

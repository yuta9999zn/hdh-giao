#!/bin/bash
# chay.sh — chay soi_mang tren Kali Live (BARE-METAL, MITM that su chay duoc). MOT LENH:
#   sudo bash chay.sh quet            # ai dang noi wifi
#   sudo bash chay.sh xem <ip>        # theo doi may do vao ten mien gi (MITM)
#   sudo bash chay.sh da <ip>         # cho may do dung 5 phut roi CAT, lap mai
#   sudo bash chay.sh dung            # dung het + tra mang
cd "$(dirname "$0")" || exit 9

# --- 1) tu do giao dien dang online (uu tien wifi wlanX) ---
IFACE=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'dev \K\S+' | head -1)
[ -z "$IFACE" ] && IFACE=$(ip -o link show up | awk -F': ' '{print $2}' | grep -E '^wl' | head -1)
[ -z "$IFACE" ] && IFACE=$(ip -o link show up | awk -F': ' '{print $2}' | grep -Ev '^lo' | head -1)
echo "[chay] giao dien mang: $IFACE"

# --- 2) dam bao co binary; chua co thi BUILD tu ma nguon (ban da sua loi treo + ghi-live) ---
chmod +x ./soi_mang 2>/dev/null
./soi_mang >/dev/null 2>&1; rc=$?
if [ ! -x ./soi_mang ] || [ "$rc" = "126" ] || [ "$rc" = "127" ]; then
  echo "[chay] chua co binary chay duoc -> build tu ma nguon (lan dau, can mang, ~1-2 phut)"
  if ! command -v cargo >/dev/null 2>&1; then
    echo "[chay] cai cargo..."; sudo apt-get update -y && sudo apt-get install -y cargo || {
      echo "[chay] KHONG cai duoc cargo (can mang). Noi wifi roi chay lai."; exit 1; }
  fi
  export CARGO_HOME="$PWD/.cargo_home"
  cargo build --release || { echo "[chay] BUILD LOI"; exit 1; }
  cp target/release/soi_mang ./soi_mang
  echo "[chay] build xong."
fi

# --- 3) dispatch ---
cmd="$1"; ip="$2"
case "$cmd" in
  quet)
    sudo ./soi_mang quet "$IFACE" ;;
  xem)
    [ -z "$ip" ] && { echo "can: sudo bash chay.sh xem <ip>"; exit 2; }
    echo "[chay] theo doi $ip 600s — Ctrl-C de dung. Ten mien in ra day + ghi so_soi.jsonl"
    sudo ./soi_mang chen "$IFACE" "$ip" 600 ;;
  da)
    [ -z "$ip" ] && { echo "can: sudo bash chay.sh da <ip>"; exit 2; }
    echo "[chay] da $ip: cho dung 5 phut roi cat 20s, lap. Ctrl-C de dung + tra mang."
    sudo ./soi_mang ngat "$IFACE" "$ip" 5 20 ;;
  dung)
    sudo pkill -TERM -f 'soi_mang chen' 2>/dev/null
    sudo pkill -TERM -f 'soi_mang ngat' 2>/dev/null
    echo "da dung + tra mang" ;;
  *)
    echo "Dung: sudo bash chay.sh quet | xem <ip> | da <ip> | dung" ;;
esac

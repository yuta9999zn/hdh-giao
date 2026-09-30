# -*- coding: utf-8 -*-
"""KIỂM KÝ KÉP bằng VECTOR CHÍNH THỨC.
    python kiem_ky_kep.py
  ML-DSA-65 (PQClean → WASM) — NIST ACVP (ben_ngoai/vector/acvp_mldsa65.json):
    keyGen 25 ca (ξ → pk, sk từng byte) · sigGen 15 ca (tất định, giao diện external/pure, CÓ ngữ cảnh —
    chữ ký từng byte) · sigVer 15 ca (3 hợp lệ, 12 không: đúng kết luận từng ca).
  Ed25519 (Monocypher → WASM) — RFC 8032 §7.1 (5 vector: khoá công khai + chữ ký từng byte, kiểm đúng,
    sửa 1 bit ⇒ sai) + NIST ACVP EDDSA-SigVer ED-25519 (5 ca, bản mẫu isSample).
Không có vector nào tự tạo: mọi đáp án đến từ NIST/IETF.
"""
import os, sys, json
P = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, P)
import ky_kep as K

đạt = rớt = 0
def ca(tên, ok, ct=""):
    global đạt, rớt
    if ok: đạt += 1; print(f"  ✓ {tên}")
    else: rớt += 1; print(f"  ✗ {tên}  {ct}")
H = bytes.fromhex

V = json.load(open(os.path.join(P, "ben_ngoai", "vector", "acvp_mldsa65.json"), encoding="utf-8"))
print(f"[ML-DSA-65 — {V['nguồn']}]")
đúng = [t["tcId"] for t in V["keyGen"] if K.mldsa_khoá(H(t["seed"])) == (H(t["pk"]), H(t["sk"]))]
ca(f"keyGen: {len(đúng)}/{len(V['keyGen'])} ca — pk VÀ sk trùng từng byte", len(đúng) == len(V["keyGen"]),
   f"lệch tcId {sorted(set(t['tcId'] for t in V['keyGen']) - set(đúng))[:5]}")
đúng = [t["tcId"] for t in V["sigGen"] if K.mldsa_ký(H(t["sk"]), H(t["message"]), H(t["context"]), bytes(32)) == H(t["signature"])]
ca(f"sigGen (tgId {V['sigGen_tgId']}, tất định, external/pure, có ngữ cảnh): {len(đúng)}/{len(V['sigGen'])} chữ ký trùng từng byte",
   len(đúng) == len(V["sigGen"]), f"lệch tcId {sorted(set(t['tcId'] for t in V['sigGen']) - set(đúng))[:5]}")
sai = [(t["tcId"], t["reason"]) for t in V["sigVer"]
       if K.mldsa_kiểm(H(t["pk"]), H(t["message"]), H(t["context"]), H(t["signature"])) != t["testPassed"]]
ly_do = sorted({t["reason"] for t in V["sigVer"] if not t["testPassed"]})
ca(f"sigVer (tgId {V['sigVer_tgId']}): {len(V['sigVer']) - len(sai)}/{len(V['sigVer'])} kết luận đúng "
   f"({sum(t['testPassed'] for t in V['sigVer'])} hợp lệ; từ chối đúng: {', '.join(ly_do)})", not sai, f"sai: {sai[:4]}")

E = json.load(open(os.path.join(P, "ben_ngoai", "vector", "ed25519.json"), encoding="utf-8"))
print(f"\n[Ed25519 — {E['nguồn_rfc8032']}]")
for v in E["rfc8032"]:
    pk = K.ed_khoá(H(v["secret"])); sig = K.ed_ký(H(v["secret"]), H(v["message"]))
    hỏng = bytearray(sig); hỏng[0] ^= 1
    ca(f"{v['tên']} ({len(v['message']) // 2} byte): khoá công khai + chữ ký trùng từng byte, kiểm đúng, sửa 1 bit ⇒ sai",
       pk == H(v["public"]) and sig == H(v["signature"]) and K.ed_kiểm(pk, H(v["message"]), sig)
       and not K.ed_kiểm(pk, H(v["message"]), bytes(hỏng)))
print(f"\n[Ed25519 — {E['nguồn_acvp']}]")
sai = [(t["tcId"], t["reason"]) for t in E["acvp_sigVer"]
       if K.ed_kiểm(H(t["q"]), H(t["message"]), H(t["signature"])) != t["testPassed"]]
ca(f"ACVP sigVer: {len(E['acvp_sigVer']) - len(sai)}/{len(E['acvp_sigVer'])} kết luận đúng "
   f"(từ chối đúng: {', '.join(sorted({t['reason'] for t in E['acvp_sigVer'] if not t['testPassed']}))})", not sai, f"sai: {sai}")

# ---------------- sổ niêm phong ký kép: kẻ CÓ quyền ghi tệp nhưng KHÔNG có khoá ----------------
import tempfile, shutil
from niem_phong import SổNiêmPhong, KhoáSổ, _băm
print("\n[sổ niêm phong ký kép — kẻ ghi được tệp nhưng không có khoá]")
tm = tempfile.mkdtemp()
try:
    khoá = KhoáSổ(os.path.join(tm, "khoa")); khoá_lạ = KhoáSổ(os.path.join(tm, "khoa_la"))
    sổ_tệp = os.path.join(tm, "so.jsonl")
    sổ = SổNiêmPhong(sổ_tệp, ký=True, khoá=khoá)
    b1 = sổ.niêm_phong("llm:thử", "vá A", {"đích_sáng": True}); sổ.chấm(b1, {"đích_sáng": True})
    sổ.niêm_phong("llm:thử", "vá B", {"đích_sáng": False})
    ok, lý = sổ.kiểm_chuỗi()
    ca(f"3 mục mới đều ký kép, kiểm đúng: {lý}", ok and all("ký" in m for m in sổ.đọc()), lý)
    ca("khoá bí mật (ξ) không lọt vào sổ",
       khoá._ξ.hex() not in open(sổ_tệp, encoding="utf-8").read())

    gốc = open(sổ_tệp, encoding="utf-8").read().splitlines()
    def thử(tên, sửa, cụm):
        ds = [json.loads(d) for d in gốc]; sửa(ds)
        with open(sổ_tệp, "w", encoding="utf-8") as f: f.write("".join(json.dumps(m, ensure_ascii=False, sort_keys=True) + "\n" for m in ds))
        ok, lý = SổNiêmPhong(sổ_tệp, ký=True, khoá=khoá).kiểm_chuỗi()
        ca(f"{tên} ⇒ phát hiện: {lý}", not ok and cụm in lý, lý)
    def viết_lại(ds):                                   # sửa nội dung RỒI dựng lại cả chuỗi băm (không có khoá)
        ds[0]["việc"] = "vá A (đã sửa lén)"
        trước = "0" * 64
        for m in ds: m["băm_trước"] = trước; m["băm"] = _băm(m); trước = m["băm"]
    thử("sửa nội dung + DỰNG LẠI cả chuỗi băm", viết_lại, "chữ ký Ed25519 SAI")
    def hỏng_ed(ds): ds[1]["ký"]["ed25519"] = ("0" if ds[1]["ký"]["ed25519"][0] != "0" else "1") + ds[1]["ký"]["ed25519"][1:]
    thử("chỉ hỏng chữ ký Ed25519 (ML-DSA vẫn đúng)", hỏng_ed, "Ed25519 SAI")
    def hỏng_ml(ds): ds[1]["ký"]["mldsa65"] = ds[1]["ký"]["mldsa65"][:100] + ("0" if ds[1]["ký"]["mldsa65"][100] != "0" else "1") + ds[1]["ký"]["mldsa65"][101:]
    thử("chỉ hỏng chữ ký ML-DSA-65 (Ed25519 vẫn đúng) — ký kép cần CẢ HAI", hỏng_ml, "ML-DSA-65 SAI")
    thử("gỡ chữ ký mục cuối", lambda ds: ds[2].pop("ký"), "THIẾU chữ ký")
    def gỡ_hết(ds):
        for m in ds: m.pop("ký")
    ds = [json.loads(d) for d in gốc]; gỡ_hết(ds)
    with open(sổ_tệp, "w", encoding="utf-8") as f: f.write("".join(json.dumps(m, ensure_ascii=False, sort_keys=True) + "\n" for m in ds))
    ok1, _ = SổNiêmPhong(sổ_tệp, ký=True, khoá=khoá).kiểm_chuỗi()
    ok2, lý = SổNiêmPhong(sổ_tệp, ký=True, khoá=khoá).kiểm_chuỗi(bắt_buộc_ký=True)
    ca(f"gỡ SẠCH mọi chữ ký: quy tắc mặc định không thấy (sổ cũ chưa ký trông y hệt) — bắt_buộc_ký=True ⇒ phát hiện: {lý}",
       ok1 and not ok2 and "THIẾU chữ ký" in lý, lý)
    def ký_lại(ds):                                     # kẻ có khoá RIÊNG của mình ký lại mọi mục
        ds[0]["việc"] = "vá A (đã sửa lén)"; trước = "0" * 64
        for m in ds: m["băm_trước"] = trước; m["băm"] = _băm(m); m["ký"] = khoá_lạ.ký(m["băm"]); trước = m["băm"]
    thử("sửa rồi KÝ LẠI bằng khoá khác", ký_lại, "KHOÁ LẠ")
finally:
    shutil.rmtree(tm, ignore_errors=True)

print(f"\nKÝ KÉP — VECTOR CHÍNH THỨC + SỔ: {đạt}/{đạt + rớt}")
sys.exit(0 if rớt == 0 else 1)

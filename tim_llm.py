# -*- coding: utf-8 -*-
"""
TIM_LLM — TRÁI TIM của sinh thể GIAO/CDFL.
LLM local bơm σ (niềm tin) và Φ (biểu diễn) cho NÃO CDFL (viết bằng GIAO) thẩm định.
Mô hình tách bạch THÂN/NÃO/TIM:
  - THÂN  = GIAO + GVM (giao.py)
  - NÃO   = CDFL đã port sang GIAO (lookahead, Ψ, Boltzmann, Hilbert, cung điện ký ức)
  - TIM   = mô hình local ở ĐÂY: sinh văn bản + nhúng (embedding) làm σ/Φ.

Backend SINH (generate), theo thứ-tự ưu-tiên (mỗi lớp tự rơi xuống lớp sau nếu hỏng):
  1. HOST API — Anthropic Claude (SDK chính thức 'anthropic'). BẬT khi có ANTHROPIC_API_KEY
     + gói 'anthropic' cài được. Mạnh nhất → phục vụ tự-sửa Stage 5 (vá lỗi bằng LLM) và σ.
       đặt model:   GIAO_API_MODEL      (mặc định 'claude-opus-4-8')
       đặt trần:    GIAO_API_MAX_TOKENS (mặc định 1024)
       bật/tắt:     GIAO_DUNG_API = 'tự'(mặc định, dùng nếu có key) | 'không'(tắt) | 'buộc'
       suy-nghĩ:    GIAO_API_NGHI = '1' → bật adaptive thinking (mặc định tắt cho nhịp-tim ngắn)
  2. Ollama (http://localhost:11434) — local, chạy được trên Windows.
       đặt model:   GIAO_LLM_MODEL (mặc định 'llama3.2')  · host: GIAO_LLM_HOST · embed: GIAO_EMB_MODEL
  3. DỰ PHÒNG TẤT ĐỊNH (nhúng băm-từ, sinh khuôn mẫu) → sinh thể vẫn đập & kiểm thử được ngay.

NHÚNG (embed, σ/Φ): Anthropic API KHÔNG có endpoint embeddings → vẫn dùng Ollama, rồi hash dự-phòng.
Cắm model/host thật vào là khớp liền, KHÔNG sửa GIAO (THÂN/NÃO không đổi).

Lõi không phụ thuộc gói ngoài — chỉ urllib (Ollama + hash). Gói 'anthropic' chỉ nạp LƯỜI khi host API bật.
"""
import os, json, math, hashlib, urllib.request, urllib.error

# ---------------- HOST API (Anthropic Claude) — cấu hình ----------------
API_MODEL      = os.environ.get("GIAO_API_MODEL", "claude-opus-4-8")
API_MAX_TOKENS = int(os.environ.get("GIAO_API_MAX_TOKENS", "1024"))
DÙNG_API       = os.environ.get("GIAO_DUNG_API", "tự").strip().lower()   # tự | không | buộc
API_NGHĨ       = os.environ.get("GIAO_API_NGHI", "").strip() in ("1", "true", "có", "yes")
_api_client    = [None]      # cache client (tạo 1 lần)
_api_down      = [False]     # nhớ API hỏng (thiếu key/gói) → khỏi thử lại

# 127.0.0.1 (KHÔNG 'localhost') để né độ trễ thử IPv6 ::1 trước trên Windows
HOST      = os.environ.get("GIAO_LLM_HOST", "http://127.0.0.1:11434")
MODEL     = os.environ.get("GIAO_LLM_MODEL", "llama3.2:1b")        # đã cài sẵn — khỏi cần env
EMB_MODEL = os.environ.get("GIAO_EMB_MODEL", "bge-m3")            # nhúng đa ngữ — γ tiếng Việt sắc
# Tiền tố tác vụ cho model nhúng. nomic-embed-text BẮT BUỘC 'search_document: ' (thiếu thì cosine
# dồn cao, xếp loạn). bge-m3 / đa số model khác KHÔNG cần → tự bỏ tiền tố theo tên model.
# Ép thủ công qua GIAO_EMB_PREFIX nếu muốn.
EMB_PREFIX = os.environ.get("GIAO_EMB_PREFIX",
                            "search_document: " if "nomic" in EMB_MODEL.lower() else "")
DIM       = 256                   # số chiều nhúng dự phòng (đủ lớn để tập-từ rời nhau gần trực giao)
TIMEOUT   = float(os.environ.get("GIAO_LLM_TIMEOUT", "30"))

# nhịp tim cuối cùng dùng backend nào (để GIAO/người soi). `api_lý_do` = vì sao host API tắt/rơi
# (key/gói/HTTP) — soi `tim_llm.backend['api_lý_do']` để chẩn-đoán thay vì nuốt-lỗi im-lặng.
backend = {"sinh": "chưa-đập", "nhúng": "chưa-đập", "api_lý_do": ""}
# NHỚ tim đã ngừng đập (không có server) → các lần sau rơi thẳng dự phòng, KHÔNG chờ mạng lại
_down = [False]

def _http(path, payload):
    if _down[0]:                                   # đã biết offline → khỏi thử mạng (fail-fast)
        raise ConnectionError("tim offline (đã ghi nhớ)")
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(HOST + path, data=data,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError:
        raise                                      # server SỐNG (vd thiếu model) → đừng đánh dấu offline
    except (urllib.error.URLError, ConnectionError, OSError):
        _down[0] = True                            # KHÔNG kết nối được → ghi nhớ, ngừng thử mạng
        raise

# ---------------- HOST API: Anthropic Claude ----------------
def _api_bật():
    "True nếu nên dùng host API (theo GIAO_DUNG_API + có ANTHROPIC_API_KEY)."
    if DÙNG_API == "không": return False
    if _api_down[0]: return False
    if DÙNG_API == "buộc": return True
    return bool(os.environ.get("ANTHROPIC_API_KEY"))   # 'tự': chỉ khi có key

def _api_lấy_client():
    "Tạo (1 lần) anthropic.Anthropic(); None nếu gói chưa cài / không cấu hình được."
    if _api_client[0] is not None: return _api_client[0]
    try:
        import anthropic                                # nạp LƯỜI — không bắt buộc cài
        _api_client[0] = anthropic.Anthropic()          # đọc ANTHROPIC_API_KEY từ env
        return _api_client[0]
    except Exception as e:
        _api_down[0] = True                             # gói thiếu / lỗi cấu hình → khỏi thử lại
        backend["api_lý_do"] = "gói/cấu-hình: " + str(e)[:100]
        return None

def _anthropic_generate(prompt):
    "Sinh văn bản qua Anthropic Messages API. Ném lên trên nếu lỗi (để rơi xuống Ollama/stub)."
    client = _api_lấy_client()
    if client is None: raise RuntimeError("anthropic client chưa sẵn")
    tham = {"model": API_MODEL, "max_tokens": API_MAX_TOKENS,
            "messages": [{"role": "user", "content": str(prompt)}]}
    if API_NGHĨ: tham["thinking"] = {"type": "adaptive"}   # chỉ bật khi cần suy-luận sâu
    msg = client.messages.create(**tham)
    # chỉ lấy khối văn bản (bỏ qua khối thinking nếu có)
    return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text").strip()

# ---------------- SINH (generative voice của tim) ----------------
def generate(prompt):
    # Lớp 1 — HOST API (mạnh nhất)
    if _api_bật():
        try:
            kq = _anthropic_generate(prompt)
            backend["sinh"] = "anthropic:" + API_MODEL
            return kq
        except Exception as e:
            _api_down[0] = True                         # API hỏng phiên này → rơi xuống Ollama
            backend["api_lý_do"] = "gọi API: " + str(e)[:100]
    # Lớp 2 — Ollama local
    try:
        out = _http("/api/generate", {"model": MODEL, "prompt": prompt, "stream": False})
        backend["sinh"] = "ollama:" + MODEL
        return (out.get("response") or "").strip()
    except Exception:
        # Lớp 3 — dự-phòng tất-định
        backend["sinh"] = "dự-phòng"
        return _stub_generate(prompt)

def _stub_generate(prompt):
    # tất định: tóm gọn prompt — đủ để đường ống chạy khi chưa có model thật
    p = " ".join(_tokens(prompt))
    return "(chưa có LLM local) " + (p[:80] if p else "rỗng")

# ---------------- NHÚNG (σ/Φ — biểu diễn để tính γ) ----------------
def embed(text):
    try:
        out = _http("/api/embeddings", {"model": EMB_MODEL, "prompt": EMB_PREFIX + str(text)})
        v = out.get("embedding")
        if not v: raise ValueError("no embedding")
        backend["nhúng"] = "ollama:" + EMB_MODEL
        return _l2(v)
    except Exception:
        backend["nhúng"] = "dự-phòng"
        return _hash_embed(text)

def _hash_embed(text):
    # feature hashing CÓ DẤU (hashing trick): mỗi từ → 1 ô + dấu ±1 từ bit băm.
    # Tập-từ RỜI nhau ⇒ cosine ≈ 0 (gần trực giao); chung từ ⇒ cộng dồn cùng dấu ⇒ cosine cao.
    # → γ dự phòng có nghĩa & ít đụng độ. Cắm model thật vào là embedding ngữ nghĩa thực.
    v = [0.0] * DIM
    for tok in _tokens(text):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        idx  = h % DIM
        sign = 1.0 if (h // DIM) % 2 == 0 else -1.0
        v[idx] += sign
    return _l2(v)

# ---------------- tiện ích ----------------
def _tokens(s):
    return [t for t in "".join(c.lower() if c.isalnum() else " " for c in str(s)).split() if t]

def _l2(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]

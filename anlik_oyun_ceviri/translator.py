"""Ceviri motorlari (Google, MyMemory, DeepL, OpenAI uyumlu) ve onbellek."""
import hashlib
import json
import os
import threading
import time

try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator
    try:
        from deep_translator import DeepLTranslator
    except ImportError:
        from deep_translator import DeeplTranslator as DeepLTranslator
except ImportError:
    GoogleTranslator = MyMemoryTranslator = DeepLTranslator = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

ENGINES = [
    ("google", "Google Ceviri (ucretsiz, anahtar gerekmez)"),
    ("mymemory", "MyMemory (ucretsiz yedek)"),
    ("deepl", "DeepL API (anahtar gerekir)"),
    ("openai", "ChatGPT / Gemini / DeepSeek (API anahtari gerekir)"),
]

MY_MEMORY_LANG = {
    "otomatik": "autodetect", "auto": "autodetect", "en": "english",
    "tr": "turkish", "de": "german", "fr": "french", "es": "spanish",
    "it": "italian", "pt": "portuguese", "ru": "russian", "ja": "japanese",
    "ko": "korean", "zh": "chinese simplified", "zh-CN": "chinese simplified",
    "ar": "arabic", "pl": "polish", "nl": "dutch", "sv": "swedish",
    "da": "danish", "el": "greek", "cs": "czech", "hu": "hungarian",
    "ro": "romanian", "bg": "bulgarian", "uk": "ukrainian", "hi": "hindi",
    "vi": "vietnamese", "th": "thai", "id": "indonesian", "ms": "malay",
    "fa": "persian",
}

ERROR_PAGE_MARKERS = (
    "Error ", "That's an error", "That’s an error",
    "There was an error", "Please try again later",
)

_LAST_BLOCK = {}


def hash_key(source, target, engine, text):
    raw = f"{source}|{target}|{engine}|{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class TranslationCache:
    def __init__(self, cache_file):
        self.path = cache_file
        self._lock = threading.Lock()
        self._data = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._data = {}

    def get(self, key):
        with self._lock:
            return self._data.get(key)

    def set(self, key, value):
        with self._lock:
            self._data[key] = value
            if len(self._data) > 20000:
                oldest = sorted(self._data, key=lambda k: self._data[k].get("t", 0))[:5000]
                for k in oldest:
                    self._data.pop(k, None)
            self._flush()

    def _flush(self):
        try:
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False)
            os.replace(tmp, self.path)
        except OSError:
            pass


class Translator:
    def __init__(self, config, cache_file):
        self.config = config
        self.cache = TranslationCache(cache_file)
        self._lock = threading.Lock()
        self.stats = {"hits": 0, "misses": 0, "errors": 0,
                      "total_latency_ms": 0, "calls": 0}

    def _keys(self):
        return self.config.get("api_keys", {})

    def _hit(self, latency=None):
        self.stats["hits"] += 1
        if latency is not None:
            self.stats["total_latency_ms"] += latency

    def translate_lines(self, lines, source, target, engine=None):
        """Birden fazla satiri tek istekte cevirir (onbellekli).

        Cache isabetli ve isabetsiz satirlarin satir sirasi korunur.
        """
        engine = engine or self.config.get("engine", "google")
        results = [None] * len(lines)
        missing, missing_idx = [], []
        for i, ln in enumerate(lines):
            ln = ln.strip()
            if not ln:
                continue
            key = hash_key(source, target, engine, ln)
            cached = self.cache.get(key)
            if cached and time.time() - cached.get("t", 0) < 2592000:
                results[i] = cached["text"]
                self.stats["hits"] += 1
                self.stats["total_latency_ms"] += cached.get("latency_ms", 0)
            else:
                missing.append(ln)
                missing_idx.append(i)

        if not missing:
            return [r for r in results if r is not None]

        t0 = time.time()
        try:
            if len(missing) == 1:
                block = self._translate(missing[0], source, target, engine)
                out_lines = [block]
            else:
                joined = "\n".join(missing)
                block = self._translate(joined, source, target, engine)
                out_lines = [ln.strip() for ln in block.splitlines()
                             if ln.strip()]
                if len(out_lines) != len(missing):
                    out_lines = [self._translate(ln, source, target, engine)
                                 for ln in missing]
        except Exception as exc:
            self.stats["errors"] += 1
            raise

        latency_ms = int((time.time() - t0) * 1000)
        self.stats["misses"] += len(missing)
        self.stats["calls"] += 1
        self.stats["total_latency_ms"] += latency_ms
        for ln, out, idx in zip(missing, out_lines, missing_idx):
            self.cache.set(hash_key(source, target, engine, ln),
                           {"text": out, "t": time.time(),
                            "latency_ms": latency_ms})
            results[idx] = out
        return [r for r in results if r is not None]

    def translate(self, text, source, target, engine=None):
        lines = self.translate_lines([text], source, target, engine)
        return lines[0] if lines else ""

    def _translate(self, text, source, target, engine):
        text = text.strip()
        if not text:
            return ""
        t0 = time.time()
        try:
            if engine == "deepl":
                result = self._translate_deepl(text, source, target)
            elif engine == "openai":
                result = self._translate_openai(text, source, target)
            elif engine == "mymemory":
                result = self._translate_mymemory(text, source, target)
            else:
                result = self._translate_google(text, source, target)
                if self._looks_like_error(result):
                    result = self._translate_mymemory(text, source, target)
        except Exception as exc:
            _LAST_BLOCK["err"] = str(exc)
            _LAST_BLOCK["engine"] = engine
            if engine == "google":
                try:
                    result = self._translate_mymemory(text, source, target)
                except Exception:
                    raise exc
            else:
                raise
        _LAST_BLOCK["latency_ms"] = int((time.time() - t0) * 1000)
        return result

    @staticmethod
    def _google_src(src):
        return None if src in ("otomatik", "auto", "") else src

    @staticmethod
    def _looks_like_error(result):
        if not isinstance(result, str):
            return True
        return any(m in result for m in ERROR_PAGE_MARKERS)

    def _translate_google(self, text, source, target):
        if GoogleTranslator is None:
            raise RuntimeError("deep-translator yuklu degil")
        src = self._google_src(source)
        tr = GoogleTranslator(source=src or "auto", target=target)
        return tr.translate(text)

    def _translate_mymemory(self, text, source, target):
        if MyMemoryTranslator is None:
            raise RuntimeError("deep-translator yuklu degil")
        src = MY_MEMORY_LANG.get(source, source)
        tgt = MY_MEMORY_LANG.get(target, target)
        tr = MyMemoryTranslator(source=src, target=tgt)
        return tr.translate(text)

    def _translate_deepl(self, text, source, target):
        if DeepLTranslator is None:
            raise RuntimeError("deep-translator yuklu degil")
        api_key = self._keys().get("deepl", "")
        if not api_key:
            raise RuntimeError("DeepL API anahtari bos. Ayarlardan ekleyin.")
        src = self._google_src(source)
        tr = DeepLTranslator(api_key=api_key,
                             source=src or "auto",
                             target=target.upper())
        return tr.translate(text)

    def _translate_openai(self, text, source, target):
        if OpenAI is None:
            raise RuntimeError("openai kutuphanesi yuklu degil")
        keys = self._keys()
        api_key = keys.get("openai", "")
        if not api_key:
            raise RuntimeError("OpenAI/ChatGPT API anahtari bos. Ayarlardan ekleyin.")
        base_url = keys.get("openai_base_url", "") or None
        model = keys.get("openai_model", "gpt-4o-mini")
        client = OpenAI(api_key=api_key, base_url=base_url)
        src_name = source if source not in ("otomatik", "auto", "") else "otomatik algilanan"
        prompt = (
            f"Kaynak dil: {src_name}\n"
            f"Hedef dil kodu: {target}\n\n"
            f"Sadece ceviriyi yaz, baska bir sey yazma.\n"
            f"Metin:\n{text}"
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        out = resp.choices[0].message.content or ""
        return out.strip().strip('"')

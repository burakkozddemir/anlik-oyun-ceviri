"""Ayarlarin yuklenmesi ve kaydedilmesi.

Kullanici verileri (config.json + cache) uygulama klasoru yerine
%LOCALAPPDATA%\\AnlikOyunCeviri altinda tutulur; boylece kurulum
dizini salt-okunur olsa da uygulama calisabilir. API anahtarlari
Windows DPAPI ile sifrelenerek diskte saklanir (CTRL/credential
yoksa duz metin yedege dusulur).
"""
import base64
import ctypes
import json
import os
import sys
import threading
import time

APP_NAME = "Anlik Oyun Ceviri"
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Kullanici verisi klasoru icin dosya sistemi guvenli ad (bosluksuz).
USER_DIR_NAME = "AnlikOyunCeviri"

# Ayarlar bicimi degisince eski dosyalari gecersiz kilar.
CONFIG_VERSION = 2

_SAVE_LOCK = threading.Lock()

DEFAULT_CONFIG = {
    "config_version": CONFIG_VERSION,
    "source_lang": "otomatik",
    "target_lang": "tr",
    "engine": "google",
    "api_keys": {
        "deepl": "",
        "openai": "",
        "openai_base_url": "",
        "openai_model": "gpt-4o-mini",
    },
    "region": {"left": 0, "top": 0, "width": 800, "height": 120},
    "monitor": 0,
    "ocr_langs": "eng+tur",
    "ocr_interval_ms": 400,
    "ocr_scale": 1.0,
    "min_confidence": 40,
    "psm": 6,
    "ocr_timeout_s": 6,
    "tesseract_cmd": "",
    "tessdata_dir": "",
    "skip_unchanged": True,
    "empty_stop_frames": 4,
    "font_family": "Segoe UI",
    "font_size": 20,
    "text_color": "#FFFFFF",
    "text_bg": "#000000",
    "overlay_mode": "transparent",
    "use_transparent": True,
    "max_lines": 3,
    "start_hidden": False,
    "last_game_name": "",
    "auto_detect_game": True,
    "window_size": "720x840",
    "window_pos": "",
    "profiles": {},
}

PROFILE_KEYS = [
    "region", "monitor", "source_lang", "target_lang", "engine",
    "ocr_langs", "ocr_interval_ms", "ocr_scale", "min_confidence", "psm",
    "font_family", "font_size", "text_color", "text_bg", "overlay_mode",
    "max_lines", "start_hidden",
]


def user_data_dir():
    """Kullanici verilerinin tutulacagi klasor (env ile ezilebilir)."""
    override = os.environ.get("ANLIK_USER_DIR")
    if override:
        d = override
    else:
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        d = os.path.join(base, USER_DIR_NAME)
    os.makedirs(d, exist_ok=True)
    return d


def config_path():
    override = os.environ.get("ANLIK_CONFIG")
    if override:
        return override
    return os.path.join(user_data_dir(), "config.json")


def legacy_config_path():
    """Eski surumlerin uygulama klasorune yazdigi yol (tasima icin)."""
    return os.path.join(APP_DIR, "config.json")


def load_config():
    path = config_path()
    _migrate_legacy()
    cfg = dict(DEFAULT_CONFIG)
    cfg["api_keys"] = dict(DEFAULT_CONFIG["api_keys"])
    cfg["region"] = dict(DEFAULT_CONFIG["region"])
    cfg["profiles"] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("config.json bir nesne degil")
        for key, value in data.items():
            if key == "api_keys" and isinstance(value, dict):
                cfg["api_keys"].update(value)
            elif key == "api_keys_enc" and isinstance(value, dict):
                cfg["api_keys"].update(_decrypt_keys(value))
            elif key == "region" and isinstance(value, dict):
                cfg["region"].update(value)
            elif key == "profiles" and isinstance(value, dict):
                cfg["profiles"] = value
            else:
                cfg[key] = value
    except FileNotFoundError:
        save_config(cfg)
    except (json.JSONDecodeError, ValueError, OSError):
        _backup_corrupt(path)
    return cfg


def _backup_corrupt(path):
    """Bozuk ayar dosyasini zaman damgali yedek olarak ayirir."""
    try:
        if os.path.exists(path):
            stamp = time.strftime("%Y%m%d-%H%M%S")
            os.replace(path, path + f".corrupt-{stamp}")
            print(f"[UYARI] Ayar dosyasi bozuktu; yedeklendi: {path}.corrupt-{stamp}")
    except OSError:
        pass


def _migrate_legacy():
    """Eski surumdeki config.json/cache'i yeni konuma tasir (bir kez)."""
    legacy = legacy_config_path()
    if not os.path.exists(legacy):
        return
    try:
        target = config_path()
        if os.path.exists(target):
            return
        os.makedirs(os.path.dirname(target), exist_ok=True)
        os.replace(legacy, target)
        print(f"[BILGI] Eski ayar dosyasi yeni konuma tasindi: {target}")
    except OSError:
        pass


def save_config(cfg):
    path = config_path()
    out = dict(cfg)
    out["config_version"] = CONFIG_VERSION
    keys = out.pop("api_keys", None)
    if isinstance(keys, dict):
        enc = _encrypt_keys(keys)
        if enc is not None:
            out["api_keys_enc"] = enc
            out.pop("api_keys", None)
        else:
            out["api_keys"] = keys
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with _SAVE_LOCK:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
    except OSError as exc:
        print(f"[HATA] Ayarlar kaydedilemedi: {exc}")


def cache_dir():
    d = os.path.join(user_data_dir(), "cache")
    os.makedirs(d, exist_ok=True)
    return d


def get_profile(cfg, game):
    key = normalize_game(game)
    return cfg.get("profiles", {}).get(key, {})


def set_profile(cfg, game, overrides):
    key = normalize_game(game)
    if not key:
        return
    cfg.setdefault("profiles", {})[key] = dict(overrides)


def normalize_game(name):
    clean = "".join(c if (c.isalnum() or c in " -_") else " " for c in name)
    return " ".join(clean.split()).lower()[:40] or "default"


# ================= DPAPI (Windows) =================

class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.c_void_p)]


def _dpapi_available():
    return sys.platform == "win32"


def _dpapi_callbacks():
    """CryptProtectData/CryptUnprotectData imzalari (64-bit guvenli)."""
    blob_p = ctypes.POINTER(_DATA_BLOB)
    crypt32 = ctypes.windll.crypt32
    for name in ("CryptProtectData", "CryptUnprotectData"):
        fn = getattr(crypt32, name)
        fn.argtypes = [blob_p, ctypes.c_wchar_p, blob_p, ctypes.c_void_p,
                       ctypes.c_void_p, ctypes.c_ulong, blob_p]
        fn.restype = ctypes.c_int
    kernel32 = ctypes.windll.kernel32
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p


def _dpapi_protect(blob: bytes) -> bytes:
    try:
        _dpapi_callbacks()
        buf = ctypes.create_string_buffer(blob, len(blob))
        in_blob = _DATA_BLOB(len(blob), ctypes.cast(buf, ctypes.c_void_p))
        out_blob = _DATA_BLOB()
        if not ctypes.windll.crypt32.CryptProtectData(
                ctypes.byref(in_blob), None, None, None, None, 0,
                ctypes.byref(out_blob)):
            return None
        try:
            raw = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            return raw
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)
    except Exception:  # noqa: BLE001
        return None


def _dpapi_unprotect(blob: bytes) -> bytes:
    try:
        _dpapi_callbacks()
        buf = ctypes.create_string_buffer(blob, len(blob))
        in_blob = _DATA_BLOB(len(blob), ctypes.cast(buf, ctypes.c_void_p))
        out_blob = _DATA_BLOB()
        if not ctypes.windll.crypt32.CryptUnprotectData(
                ctypes.byref(in_blob), None, None, None, None, 0,
                ctypes.byref(out_blob)):
            return None
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)
    except Exception:  # noqa: BLE001
        return None


def _encrypt_keys(keys):
    """Anahtar sozlugunu DPAPI ile sifreler; basarisizsa None doner."""
    if not _dpapi_available():
        return None
    if not any(keys.values()):
        return {}
    try:
        payload = json.dumps(keys, ensure_ascii=False).encode("utf-8")
        enc = _dpapi_protect(payload)
        if enc is None:
            return None
        return {"dpapi": base64.b64encode(enc).decode("ascii")}
    except Exception:  # noqa: BLE001
        return None


def _decrypt_keys(enc):
    """Sifreli anahtar sozlugunu geri cevirir; basarisizsa bos doner."""
    blob = enc.get("dpapi")
    if not blob:
        return {}
    try:
        raw = _dpapi_unprotect(base64.b64decode(blob))
        if raw is None:
            return {}
        data = json.loads(raw.decode("utf-8"))
        return dict(data) if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}

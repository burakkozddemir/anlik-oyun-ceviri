"""Ayarlarin yuklenmesi ve kaydedilmesi."""
import json
import os
import sys

APP_NAME = "Anlik Oyun Ceviri"
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_CONFIG = {
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
    "tesseract_cmd": "",
    "tessdata_dir": "",
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


def config_path():
    override = os.environ.get("ANLIK_CONFIG")
    if override:
        return override
    return os.path.join(APP_DIR, "config.json")


def load_config():
    path = config_path()
    cfg = dict(DEFAULT_CONFIG)
    cfg["api_keys"] = dict(DEFAULT_CONFIG["api_keys"])
    cfg["region"] = dict(DEFAULT_CONFIG["region"])
    cfg["profiles"] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "api_keys" and isinstance(value, dict):
                    cfg["api_keys"].update(value)
                elif key == "region" and isinstance(value, dict):
                    cfg["region"].update(value)
                elif key == "profiles" and isinstance(value, dict):
                    cfg["profiles"] = value
                else:
                    cfg[key] = value
    except FileNotFoundError:
        save_config(cfg)
    except (json.JSONDecodeError, OSError):
        pass
    return cfg


def save_config(cfg):
    path = config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        print(f"[HATA] Ayarlar kaydedilemedi: {exc}")


def cache_dir():
    d = os.path.join(APP_DIR, "cache")
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

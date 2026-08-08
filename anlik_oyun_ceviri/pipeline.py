"""Arka planda calisan ceviri hatti: ekran yakala -> OCR -> cevir -> kuyruk."""
import os
import threading
import time
import queue

from . import config as config_mod
from .screen import grab_region
from .ocr import OcrEngine
from .translator import Translator


class TranslationPipeline:
    def __init__(self, config, on_status=None, on_log=None):
        self.config = config
        self.on_status = on_status
        self.on_log = on_log
        self.queue = queue.Queue()
        self._running = False
        self._thread = None
        self._stop = threading.Event()
        self.ocr = OcrEngine(config)
        cache_file = os.path.join(config_mod.cache_dir(), f"{self.game_key()}.json")
        self.translator = Translator(config, cache_file)
        self._last_raw = ""
        self._last_translated = []
        self._stats = {
            "fps": 0.0, "latency_ms": 0, "frames": 0,
            "translated": 0, "hits": 0, "errors": 0, "cache_size": 0,
        }
        self._frames_since_reset = 0
        self._reset_ts = time.time()
        self._ema_latency = 0.0

    def game_key(self):
        name = self.config.get("last_game_name", "") or "default"
        return config_mod.normalize_game(name)

    @property
    def running(self):
        return self._running

    @property
    def stats(self):
        s = dict(self._stats)
        s["cache_size"] = len(self.translator.cache._data)
        return s

    def start(self):
        if self._running:
            return
        if not self.ocr.is_ready:
            raise RuntimeError("OCR motoru hazir degil.\n" + self.ocr.engine_help())
        self._stop.clear()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._stop.set()

    def _report(self, text):
        if self.on_status:
            self.on_status(text)

    def _log(self, text, kind="info"):
        if self.on_log:
            self.on_log(text, kind)

    def _loop(self):
        cfg = self.config
        interval = max(80, int(cfg.get("ocr_interval_ms", 400)))
        while not self._stop.is_set():
            t_start = time.time()
            region = cfg.get("region", {})
            try:
                img = grab_region(region, cfg.get("monitor", 0))
                raw = self.ocr.read(img)
            except Exception as exc:  # noqa: BLE001
                self._stats["errors"] += 1
                self._log(f"OCR hatasi: {exc}", "error")
                time.sleep(0.5)
                continue

            self._stats["frames"] += 1
            self._frames_since_reset += 1
            now = time.time()
            if now - self._reset_ts >= 1.0:
                self._stats["fps"] = self._frames_since_reset / (now - self._reset_ts)
                self._frames_since_reset = 0
                self._reset_ts = now

            if raw and raw != self._last_raw:
                self._last_raw = raw
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                if len(lines) == 1 and len(lines[0]) < 2:
                    continue
                self._report(f"OKUNAN: {raw[:90]}")
                try:
                    translated = self.translator.translate_lines(
                        lines,
                        source=cfg.get("source_lang", "otomatik"),
                        target=cfg.get("target_lang", "tr"),
                    )
                    self._stats["translated"] += 1
                    self._stats["hits"] = self.translator.stats["hits"]
                    self._stats["errors"] = self.translator.stats["errors"]
                    latency = int(self.translator.stats["total_latency_ms"])
                    calls = max(1, self.translator.stats["calls"])
                    self._ema_latency = self._ema_latency * 0.7 + latency * 0.3
                    self._stats["latency_ms"] = int(self._ema_latency)
                except Exception as exc:  # noqa: BLE001
                    translated = [f"[Ceviri hatasi: {exc}]"]
                    self._stats["errors"] += 1
                    self._log(f"Ceviri hatasi: {exc}", "error")
                self._last_translated = translated
                self.queue.put({"lines": translated,
                                "raw": raw,
                                "latency_ms": self._stats["latency_ms"],
                                "fresh": True})
            elif self._last_translated:
                self.queue.put({"lines": self._last_translated,
                                "raw": raw or self._last_raw,
                                "cached": True,
                                "latency_ms": 0})

            elapsed = (time.time() - t_start) * 1000
            sleep = max(0.0, (interval - elapsed) / 1000.0)
            time.sleep(sleep)

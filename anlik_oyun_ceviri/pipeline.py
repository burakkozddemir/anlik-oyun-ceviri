"""Arka planda calisan ceviri hatti: ekran yakala -> OCR -> cevir -> kuyruk.

Yasam dongusu: tek daemon thread, durum makinesi (stopped/running/failed),
durdurmada join, sadece en guncel sonucu tasiyan sinirli kuyruk ve
degişmeyen karelerde OCR atlamasi (goruntu hash'i) icerir.
"""
import hashlib
import os
import threading
import time
import queue

from . import config as config_mod
from .screen import CaptureSession
from .ocr import OcrEngine
from .translator import Translator

STATE_STOPPED = "stopped"
STATE_RUNNING = "running"
STATE_FAILED = "failed"


class TranslationPipeline:
    def __init__(self, config, on_status=None, on_log=None):
        self.config = config
        self.on_status = on_status
        self.on_log = on_log
        # Yalnizca en guncel sonuc anlamlidir; eski mesajlar dusurulur.
        self.queue = queue.Queue(maxsize=1)
        self._state = STATE_STOPPED
        self._thread = None
        self._stop = threading.Event()
        self._generation = 0
        self._error = ""
        self.ocr = OcrEngine(config)
        cache_file = os.path.join(config_mod.cache_dir(), f"{self.game_key()}.json")
        self.translator = Translator(config, cache_file)
        self._last_raw = ""
        self._last_translated = []
        self._empty_frames = 0
        self._last_hash = None
        self._stats = {
            "fps": 0.0, "latency_ms": 0, "frames": 0,
            "translated": 0, "hits": 0, "errors": 0, "cache_size": 0,
            "skipped": 0,
        }
        self._frames_since_reset = 0
        self._reset_ts = time.time()
        self._ema_latency = 0.0

    def game_key(self):
        name = self.config.get("last_game_name", "") or "default"
        return config_mod.normalize_game(name)

    @property
    def state(self):
        return self._state

    @property
    def error(self):
        return self._error

    @property
    def running(self):
        return self._state == STATE_RUNNING

    @property
    def stats(self):
        s = dict(self._stats)
        s["cache_size"] = len(self.translator.cache._data)
        return s

    def start(self):
        if self._state == STATE_RUNNING:
            return
        if not self.ocr.is_ready:
            raise RuntimeError("OCR motoru hazir degil.\n" + self.ocr.engine_help())
        self._stop.clear()
        self._generation += 1
        self._state = STATE_RUNNING
        self._error = ""
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self, join=True):
        """Durdurur ve thread'in sonlanmasini bekler (en fazla 5 sn)."""
        self._stop.set()
        if join and self._thread and self._thread.is_alive() and \
                self._thread is not threading.current_thread():
            self._thread.join(timeout=5.0)
        self._state = STATE_STOPPED

    def _report(self, text):
        if self.on_status:
            self.on_status(text)

    def _log(self, text, kind="info"):
        if self.on_log:
            self.on_log(text, kind)

    def _put(self, gen, msg):
        """Sinirli kuyruk: doluysa en eski mesaj dusurulur.

        Eski nesil thread'lerin (stop sonrasi kalanlar) mesajlari
        reddedilir, boylece yeni oturumun ciktisi kirlenmez.
        """
        if gen != self._generation:
            return
        try:
            self.queue.put_nowait(msg)
        except queue.Full:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.queue.put_nowait(msg)
            except queue.Full:
                pass

    @staticmethod
    def _frame_hash(img):
        """Kucultulmus karenin ozeti; degisiklik algilamada kullanilir."""
        try:
            small = img.resize((32, 32))
            return hashlib.md5(small.tobytes()).hexdigest()
        except Exception:  # noqa: BLE001
            return None

    def _loop(self):
        gen = self._generation
        cfg = self.config
        try:
            interval = max(80, int(cfg.get("ocr_interval_ms", 400)))
        except (TypeError, ValueError):
            interval = 400
        try:
            empty_stop = max(1, int(cfg.get("empty_stop_frames", 4)))
        except (TypeError, ValueError):
            empty_stop = 4
        skip_unchanged = bool(cfg.get("skip_unchanged", True))
        session = None
        try:
            session = CaptureSession()
            while not self._stop.is_set() and gen == self._generation:
                t_start = time.time()
                try:
                    region = cfg.get("region", {})
                    img = session.grab(region)
                    if skip_unchanged:
                        fh = self._frame_hash(img)
                        if fh is not None and fh == self._last_hash:
                            self._stats["skipped"] += 1
                            self._sleep_until(interval, t_start)
                            continue
                        self._last_hash = fh
                    raw = self.ocr.read(img)
                except Exception as exc:  # noqa: BLE001
                    self._stats["errors"] += 1
                    self._log(f"OCR hatasi: {exc}", "error")
                    self._sleep_until(interval, t_start)
                    continue

                self._stats["frames"] += 1
                self._frames_since_reset += 1
                now = time.time()
                if now - self._reset_ts >= 1.0:
                    self._stats["fps"] = self._frames_since_reset / (now - self._reset_ts)
                    self._frames_since_reset = 0
                    self._reset_ts = now

                # Altyazi kayboldu: eski ceviriyi temizle.
                if not raw:
                    self._empty_frames += 1
                    if self._empty_frames >= empty_stop and self._last_translated:
                        self._last_translated = []
                        self._last_raw = ""
                        self._report("")
                        self._put(gen, {"lines": [], "clear": True})
                else:
                    self._empty_frames = 0

                if raw and raw != self._last_raw:
                    self._last_raw = raw
                    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                    # Tek karakterlik "gurultu" cevirime girmez; dongu yine de uyur.
                    if len(lines) == 1 and len(lines[0]) < 2:
                        self._empty_frames = 0
                        self._sleep_until(interval, t_start)
                        continue
                    self._report(f"OKUNAN: {raw[:90]}")
                    try:
                        translated, latency_ms = self.translator.translate_lines_measured(
                            lines,
                            source=cfg.get("source_lang", "otomatik"),
                            target=cfg.get("target_lang", "tr"),
                        )
                        self._stats["translated"] += 1
                        self._stats["hits"] = self.translator.stats["hits"]
                        self._stats["errors"] = self.translator.stats["errors"]
                        self._ema_latency = self._ema_latency * 0.7 + latency_ms * 0.3
                        self._stats["latency_ms"] = int(self._ema_latency)
                    except Exception as exc:  # noqa: BLE001
                        self._stats["errors"] += 1
                        self._log(f"Ceviri hatasi: {exc}", "error")
                    else:
                        self._last_translated = translated
                        self._put(gen, {"lines": translated,
                                        "raw": raw,
                                        "latency_ms": self._stats["latency_ms"],
                                        "fresh": True})

                self._sleep_until(interval, t_start)
        except Exception as exc:  # noqa: BLE001
            if gen == self._generation:
                self._state = STATE_FAILED
                self._error = str(exc)
                self._log(f"Pipeline hatasi: {exc}", "error")
                self._report(f"HATA: {exc}")
        finally:
            if session is not None:
                session.close()
            if self._stop.is_set() and gen == self._generation:
                self._state = STATE_STOPPED

    def _sleep_until(self, interval, t_start):
        """Kare suresi kadar bekler; hatali yollarda bile en az 20 ms uyur."""
        elapsed = (time.time() - t_start) * 1000
        sleep = max(0.02, (interval - elapsed) / 1000.0)
        self._stop.wait(sleep)

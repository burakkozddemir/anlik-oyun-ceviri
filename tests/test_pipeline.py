"""Pipeline: yasam dongusu, bos OCR temizligi, busy-loop korumasi,
goruntu hash'iyle atlama ve hata durumu."""
import threading
import time
from collections import deque

from PIL import Image

from anlik_oyun_ceviri import pipeline as pipeline_mod
from anlik_oyun_ceviri.pipeline import TranslationPipeline

CFG = {
    "region": {"left": 0, "top": 0, "width": 100, "height": 40},
    "monitor": 0,
    "ocr_interval_ms": 80,
    "empty_stop_frames": 2,
    "skip_unchanged": True,
    "source_lang": "en",
    "target_lang": "tr",
    "last_game_name": "",
    "api_keys": {},
    "engine": "google",
}


class FakeSession:
    def __init__(self, img=None):
        self.img = img
        self.counter = 0
        self.closed = False

    def grab(self, region):
        if self.img is None:
            # Her karede farkli piksel: goruntu hash'i degisir, OCR calisir.
            self.counter += 1
            return Image.new("RGB", (100, 40), (self.counter % 255, 0, 0))
        return self.img.copy()

    def close(self):
        self.closed = True


class FakeOcr:
    is_ready = True
    mode = "fake"

    def __init__(self, config):
        self.reads = 0

    def read(self, img):
        return ""


class FakeTranslator:
    class Cache:
        def __init__(self):
            self._data = {}

    def __init__(self, config, cache_file):
        self.cache = self.Cache()
        self.stats = {"hits": 0, "errors": 0}
        self.calls = []

    def translate_lines_measured(self, lines, source, target):
        self.calls.append(list(lines))
        return [f"TR:{ln}" for ln in lines], 25

    def translate_lines(self, lines, source, target):
        return [f"TR:{ln}" for ln in lines]


def build_pipeline(monkeypatch, session, ocr_texts=None, engine=None,
                   skip_unchanged=True):
    texts = iter(ocr_texts or [])

    class CustomOcr(FakeOcr):
        def read(self, img):
            self.reads += 1
            return next(texts, "Merhaba dunya")

    cfg = dict(CFG)
    cfg["skip_unchanged"] = skip_unchanged
    monkeypatch.setattr(pipeline_mod, "CaptureSession",
                        lambda: session)
    monkeypatch.setattr(pipeline_mod, "OcrEngine", CustomOcr)
    monkeypatch.setattr(pipeline_mod, "Translator", FakeTranslator)
    p = TranslationPipeline(cfg, on_log=lambda *a: None,
                            on_status=lambda *a: None)
    return p


def drain(p, timeout=3.0):
    msgs = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            msgs.append(p.queue.get_nowait())
        except Exception:  # noqa: BLE001
            pass
        if p.state != "running" and msgs:
            break
        time.sleep(0.01)
    return msgs


def test_start_stop_and_translate_flow(monkeypatch):
    p = build_pipeline(monkeypatch, FakeSession())
    p.start()
    assert p.state == "running"
    # Fresh mesaj gelene kadar bekle
    deadline = time.time() + 5
    fresh = None
    while time.time() < deadline and fresh is None:
        try:
            msg = p.queue.get_nowait()
            if msg.get("fresh"):
                fresh = msg
        except Exception:  # noqa: BLE001
            time.sleep(0.02)
    assert fresh is not None
    assert fresh["lines"] == ["TR:Merhaba dunya"]
    p.stop()
    assert p.state == "stopped"
    assert not p.running


def test_empty_ocr_sends_clear_event(monkeypatch):
    # Once altyazi okunur (last_translated dolar), sonra bosalir -> clear.
    p = build_pipeline(monkeypatch, FakeSession(),
                       ocr_texts=["Merhaba", "", "", ""])
    p.start()
    deadline = time.time() + 5
    cleared = False
    fresh = False
    while time.time() < deadline and not cleared:
        try:
            msg = p.queue.get_nowait()
            if msg.get("fresh"):
                fresh = True
            if msg.get("clear"):
                cleared = True
        except Exception:  # noqa: BLE001
            time.sleep(0.02)
    assert fresh
    assert cleared
    p.stop()


def test_single_char_does_not_translate_and_keeps_sleeping(monkeypatch):
    p = build_pipeline(monkeypatch, FakeSession(), ocr_texts=["a"] * 40)
    p.start()
    time.sleep(0.6)
    # Tek karakterli sonuc cevirime gitmez; onceki ceviri de gorunmez.
    assert p.translator.calls == []
    assert p.state == "running"
    p.stop()


def test_unchanged_image_skips_ocr(monkeypatch):
    static = Image.new("RGB", (100, 40), "black")
    p = build_pipeline(monkeypatch, FakeSession(img=static))
    p.start()
    time.sleep(0.5)
    p.stop()
    # Ayni karelerde OCR atlanmali: yalnizca ilk karede okunur.
    assert p.ocr.reads == 1
    assert p.stats["skipped"] >= 1


def test_failed_state_on_session_constructor_error(monkeypatch):
    class Boom:
        def __init__(self):
            raise RuntimeError("mss yuklu degil")

    monkeypatch.setattr(pipeline_mod, "CaptureSession", Boom)
    monkeypatch.setattr(pipeline_mod, "OcrEngine", FakeOcr)
    monkeypatch.setattr(pipeline_mod, "Translator", FakeTranslator)
    p = TranslationPipeline(dict(CFG), on_log=lambda *a: None,
                            on_status=lambda *a: None)
    p.start()
    deadline = time.time() + 3
    while time.time() < deadline and p.state == "running":
        time.sleep(0.02)
    assert p.state == "failed"
    assert "mss" in p.error.lower()
    p.stop()


def test_translation_error_keeps_last_good_subtitle(monkeypatch):
    class FlakyTranslator(FakeTranslator):
        def translate_lines_measured(self, lines, source, target):
            raise RuntimeError("API kapali")

    class TextOcr(FakeOcr):
        def read(self, img):
            return "Merhaba dunya"

    monkeypatch.setattr(pipeline_mod, "CaptureSession",
                        lambda: FakeSession())
    monkeypatch.setattr(pipeline_mod, "OcrEngine", TextOcr)
    monkeypatch.setattr(pipeline_mod, "Translator", FlakyTranslator)
    p = TranslationPipeline(dict(CFG), on_log=lambda *a: None,
                            on_status=lambda *a: None)
    p.start()
    deadline = time.time() + 5
    while time.time() < deadline:
        if p.stats["errors"] >= 1:
            break
        time.sleep(0.02)
    assert p.stats["errors"] >= 1
    assert p.state == "running"  # hata pipeline'i oldurmez
    p.stop()


def test_restart_after_stop_works(monkeypatch):
    p = build_pipeline(monkeypatch, FakeSession())
    p.start()
    time.sleep(0.2)
    p.stop()
    p.start()
    assert p.state == "running"
    p.stop()
    assert p.state == "stopped"

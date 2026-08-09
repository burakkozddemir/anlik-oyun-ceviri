"""Ekran yakalama: sanal masaustu, negatif koordinatli monitörler ve oturum."""
import pytest

from anlik_oyun_ceviri import screen as screen_mod


class FakeShot:
    def __init__(self, w, h):
        self.size = (w, h)
        self.bgra = bytes(w * h * 4)


class FakeSct:
    def __init__(self, monitors):
        self.monitors = monitors
        self.last_region = None
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def grab(self, region):
        self.last_region = dict(region)
        return FakeShot(region["width"], region["height"])

    def close(self):
        self.closed = True


class FakeMSS:
    def __init__(self):
        self.instances = []
        self.monitors = [
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
            {"left": -1920, "top": 0, "width": 1920, "height": 1080},
        ]

    def mss(self):
        inst = FakeSct(self.monitors)
        self.instances.append(inst)
        return inst


@pytest.fixture
def fake_mss(monkeypatch):
    fake = FakeMSS()
    monkeypatch.setattr(screen_mod, "mss", fake)
    return fake


def test_virtual_desktop(fake_mss):
    vd = screen_mod.virtual_desktop()
    assert vd["left"] == 0 and vd["width"] == 1920


def test_monitor_bounds_negative_coords(fake_mss):
    bounds = screen_mod.monitor_bounds(1)
    assert bounds["left"] == -1920  # soldaki monitor negatif X
    bounds2 = screen_mod.monitor_bounds(0)
    assert bounds2["left"] == 0


def test_grab_region_passes_through_coords(fake_mss):
    img = screen_mod.grab_region({"left": -500, "top": 10, "width": 400, "height": 100})
    assert img.size == (400, 100)
    assert fake_mss.instances[0].last_region["left"] == -500


def test_capture_session_reuses_instance(fake_mss):
    sess = screen_mod.CaptureSession()
    img = sess.grab({"left": 0, "top": 0, "width": 10, "height": 10})
    assert img.size == (10, 10)
    sess.close()
    assert fake_mss.instances[0].closed


def test_grab_raises_without_mss(monkeypatch):
    monkeypatch.setattr(screen_mod, "mss", None)
    with pytest.raises(RuntimeError):
        screen_mod.grab_region({"left": 0, "top": 0, "width": 10, "height": 10})

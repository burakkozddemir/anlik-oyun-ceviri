"""Ekran yakalama (mss) ve desteklenen diller."""
from PIL import Image

try:
    import mss
except ImportError:
    mss = None

LANGUAGES = [
    ("otomatik", "Otomatik Algila"),
    ("en", "Ingilizce"),
    ("tr", "Turkce"),
    ("de", "Almanca"),
    ("fr", "Fransizca"),
    ("es", "Ispanyolca"),
    ("it", "Italyanca"),
    ("pt", "Portekizce"),
    ("ru", "Rusca"),
    ("ja", "Japonca"),
    ("ko", "Korece"),
    ("zh", "Cince (Basit)"),
    ("zh-CN", "Cince"),
    ("ar", "Arapca"),
    ("pl", "Lehce"),
    ("nl", "Flemenkce"),
    ("sv", "Isvecce"),
    ("da", "Danimarkaca"),
    ("fi", "Fince"),
    ("el", "Yunanca"),
    ("cs", "Cekce"),
    ("hu", "Macarca"),
    ("ro", "Rumence"),
    ("bg", "Bulgarca"),
    ("uk", "Ukraynaca"),
    ("hi", "Hintce"),
    ("vi", "Vietnamca"),
    ("th", "Tayca"),
    ("id", "Endonezce"),
    ("ms", "Malayca"),
    ("fa", "Farsca"),
]


def available_monitors():
    if mss is None:
        return []
    with mss.mss() as sct:
        return [{"index": i, "left": m["left"], "top": m["top"],
                 "width": m["width"], "height": m["height"]}
                for i, m in enumerate(sct.monitors[1:])]


def monitor_bounds(monitor_index=0):
    """Secili monitörun sinirlarini doner (sanal masaustu koordinatlari)."""
    if mss is None:
        return {"left": 0, "top": 0, "width": 0, "height": 0}
    with mss.mss() as sct:
        monitors = sct.monitors[1:]
        if not monitors:
            return {"left": 0, "top": 0, "width": 0, "height": 0}
        idx = max(0, min(int(monitor_index), len(monitors) - 1))
        m = monitors[idx]
        return {"left": m["left"], "top": m["top"],
                "width": m["width"], "height": m["height"]}


def grab_region(region, monitor_index=0):
    """Belirtilen bolgenin goruntusunu PIL Image olarak dondurur.

    Bolge, sanal masaustu (tum ekranlar) koordinat sistemindedir;
    negatif koordinatlar da desteklenir. Tek seferlik yakalamalar
    icindir; surekli yakalama icin CaptureSession kullanin.
    """
    if mss is None:
        raise RuntimeError("mss kutuphanesi yuklu degil. 'pip install mss' calistirin.")
    left = int(region["left"])
    top = int(region["top"])
    width = max(1, int(region["width"]))
    height = max(1, int(region["height"]))
    with mss.mss() as sct:
        shot = sct.grab({"left": left, "top": top,
                         "width": width, "height": height})
    img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    return img


class CaptureSession:
    """Pipeline omru boyunca tek MSS oturumu; her karede yeni oturum
    acmaya gerek kalmaz (GDI baglantisinin maliyeti dusurulur).
    """

    def __init__(self):
        if mss is None:
            self._sct = None
        else:
            self._sct = mss.mss()
        self._closed = False

    def grab(self, region):
        if self._sct is None:
            raise RuntimeError("mss kutuphanesi yuklu degil. 'pip install mss' calistirin.")
        if self._closed:
            raise RuntimeError("Yakalama oturumu kapatilmis.")
        left = int(region["left"])
        top = int(region["top"])
        width = max(1, int(region["width"]))
        height = max(1, int(region["height"]))
        shot = self._sct.grab({"left": left, "top": top,
                               "width": width, "height": height})
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        return img

    def close(self):
        if self._sct is not None and not self._closed:
            try:
                self._sct.close()
            except Exception:  # noqa: BLE001
                pass
        self._closed = True


def virtual_desktop():
    """Tum ekranlari kaplayan sanal masaustu sinirlari ve boyutu."""
    if mss is None:
        return {"left": 0, "top": 0, "width": 0, "height": 0}
    with mss.mss() as sct:
        m = sct.monitors[0]
        return {"left": m["left"], "top": m["top"],
                "width": m["width"], "height": m["height"]}


def screen_size(monitor_index=0):
    v = virtual_desktop()
    return (v["width"], v["height"])

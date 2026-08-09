"""Ekran yakalama (mss) ve desteklenen diller."""
from PIL import Image

try:
    import mss
except ImportError:
    mss = None

LANGUAGES = [
    ("otomatik", "Otomatik Algıla"),
    ("en", "İngilizce"),
    ("tr", "Türkçe"),
    ("de", "Almanca"),
    ("fr", "Fransızca"),
    ("es", "İspanyolca"),
    ("it", "İtalyanca"),
    ("pt", "Portekizce"),
    ("ru", "Rusça"),
    ("ja", "Japonca"),
    ("ko", "Korece"),
    ("zh", "Çince (Basit)"),
    ("zh-CN", "Cince"),
    ("ar", "Arapça"),
    ("pl", "Lehçe"),
    ("nl", "Flemenkçe"),
    ("sv", "İsveççe"),
    ("da", "Danimarkaca"),
    ("fi", "Fince"),
    ("el", "Yunanca"),
    ("cs", "Çekçe"),
    ("hu", "Macarca"),
    ("ro", "Rumence"),
    ("bg", "Bulgarca"),
    ("uk", "Ukraynaca"),
    ("hi", "Hintçe"),
    ("vi", "Vietnamca"),
    ("th", "Tayca"),
    ("id", "Endonezce"),
    ("ms", "Malayca"),
    ("fa", "Farsça"),
]


def available_monitors():
    if mss is None:
        return []
    with mss.mss() as sct:
        return [{"index": i, "left": m["left"], "top": m["top"],
                 "width": m["width"], "height": m["height"]}
                for i, m in enumerate(sct.monitors[1:])]


def monitor_bounds(monitor_index=0):
    """Seçili monitörün sınırlarını döner (sanal masaüstü koordinatları)."""
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
    """Belirtilen bölgenin görüntüsünü PIL Image olarak döndürür.

    Bölge, sanal masaüstü (tüm ekranlar) koordinat sistemindedir;
    negatif koordinatlar da desteklenir. Tek seferlik yakalamalar
    içindir; sürekli yakalama için CaptureSession kullanın.
    """
    if mss is None:
        raise RuntimeError("mss kütüphanesi yüklü değil. 'pip install mss' çalıştırın.")
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
    """Pipeline ömrü boyunca tek MSS oturumu; her karede yeni oturum
    açmaya gerek kalmaz (GDI bağlantısının maliyeti düşürülür).
    """

    def __init__(self):
        if mss is None:
            self._sct = None
        else:
            self._sct = mss.mss()
        self._closed = False

    def grab(self, region):
        if self._sct is None:
            raise RuntimeError("mss kütüphanesi yüklü değil. 'pip install mss' çalıştırın.")
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
    """Tüm ekranları kaplayan sanal masaüstü sınırları ve boyutu."""
    if mss is None:
        return {"left": 0, "top": 0, "width": 0, "height": 0}
    with mss.mss() as sct:
        m = sct.monitors[0]
        return {"left": m["left"], "top": m["top"],
                "width": m["width"], "height": m["height"]}


def screen_size(monitor_index=0):
    v = virtual_desktop()
    return (v["width"], v["height"])

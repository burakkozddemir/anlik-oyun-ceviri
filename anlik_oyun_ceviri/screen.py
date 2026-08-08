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


def grab_region(region, monitor_index=0):
    """Belirtilen bolgenin goruntusunu PIL Image olarak dondurur.

    Bolge, sanal masaustu (tum ekranlar) koordinat sistemindedir;
    negatif koordinatlar da desteklenir.
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

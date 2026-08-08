"""OCR motoru: oncelik Tesseract, yedek Windows yerlesik OCR."""
import os
import shutil
import sys
import threading

from PIL import Image, ImageOps

from . import config as config_mod

def _bundle_root():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", None) or os.path.dirname(sys.executable)
    return config_mod.APP_DIR

BUNDLED_TESSERACT = os.path.join(_bundle_root(), "Tesseract-OCR", "tesseract.exe")

COMMON_TESSERACT_PATHS = [
    BUNDLED_TESSERACT,
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    r"C:\Users\Public\Tesseract-OCR\tesseract.exe",
]

try:
    import pytesseract
except ImportError:
    pytesseract = None

_WIN_OCR = None
_WIN_OCR_ERROR = None
try:
    import winocr  # istege bagli: Windows.Media.Ocr
    _WIN_OCR = winocr
except Exception as exc:  # noqa: BLE001
    _WIN_OCR_ERROR = str(exc)

TESS_LANG_ALIASES = {
    "zh-CN": "chi_sim",
    "zh": "chi_sim",
    "pt": "por",
    "cs": "ces",
    "fa": "fas",
    "sv": "swe",
    "da": "dan",
    "el": "ell",
    "vi": "vie",
    "bg": "bul",
    "uk": "ukr",
    "pl": "pol",
    "hu": "hun",
    "ro": "ron",
    "id": "ind",
    "ms": "msa",
}

WINDOWS_OCR_LANG = {
    "en": "en", "tr": "tr", "de": "de", "fr": "fr", "es": "es",
    "it": "it", "pt": "pt", "ru": "ru", "ja": "ja", "ko": "ko",
    "zh": "zh-Hans", "zh-CN": "zh-Hans", "pl": "pl", "nl": "nl",
    "sv": "sv", "da": "da", "el": "el", "cs": "cs", "hu": "hu",
    "ro": "ro", "bg": "bg", "uk": "uk", "hi": "hi", "vi": "vi",
    "th": "th", "ar": "ar", "fa": "fa",
}


class OcrEngine:
    def __init__(self, config):
        self.config = config
        self._lock = threading.Lock()
        self._mode = None
        self._detect()

    def _detect(self):
        if pytesseract is not None:
            cmd = self.config.get("tesseract_cmd") or ""
            if cmd and os.path.exists(cmd):
                pytesseract.pytesseract.tesseract_cmd = cmd
                self._mode = "tesseract"
                return
            exe = cmd or shutil.which("tesseract")
            if exe and os.path.exists(exe):
                pytesseract.pytesseract.tesseract_cmd = exe
                self._mode = "tesseract"
                return
            for path in COMMON_TESSERACT_PATHS:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self._mode = "tesseract"
                    return
        if _WIN_OCR is not None:
            self._mode = "windows"
            return
        self._mode = None

    @property
    def mode(self):
        return self._mode

    @property
    def is_ready(self):
        return self._mode is not None

    @staticmethod
    def engine_help():
        msg = []
        if pytesseract is None:
            msg.append("- 'pip install pytesseract'")
        exe = shutil.which("tesseract")
        if exe:
            msg.append(f"- Tesseract bulundu: {exe}")
        else:
            msg.append("- Tesseract kurulu degil: https://github.com/UB-Mannheim/tesseract/wiki")
            msg.append("  veya 'winget install UB-Mannheim.TesseractOCR'")
        if _WIN_OCR is not None:
            msg.append("- Windows yerlesik OCR kullanilabilir.")
        else:
            msg.append("- 'pip install winocr' ile Windows yerlesik OCR eklenebilir.")
        return "\n".join(msg)

    def _preprocess(self, img):
        img = ImageOps.exif_transpose(img)
        if img.mode != "L":
            img = img.convert("L")
        img = ImageOps.autocontrast(img)
        scale = self.config.get("ocr_scale", 1.0)
        if scale != 1.0:
            img = img.resize((int(img.width * scale), int(img.height * scale)),
                             Image.LANCZOS)
        return img

    def _tess_langs(self):
        raw = self.config.get("ocr_langs", "eng+tur")
        parts = [p.strip() for p in raw.split("+") if p.strip()]
        mapped = [TESS_LANG_ALIASES.get(p, p) for p in parts]
        return "+".join(mapped) if mapped else "eng"

    def _read_tesseract(self, img):
        img = self._preprocess(img)
        tessdata = self.config.get("tessdata_dir") or ""
        if not tessdata:
            for base in (_bundle_root(), config_mod.APP_DIR):
                cand = os.path.join(base, "tessdata")
                if os.path.isdir(cand):
                    tessdata = cand
                    break
        tessdata = os.path.abspath(tessdata)
        if os.path.isdir(tessdata):
            os.environ["TESSDATA_PREFIX"] = tessdata
        try:
            data = pytesseract.image_to_data(
                img, lang=self._tess_langs(), config="--psm 6",
                output_type=pytesseract.Output.DICT,
            )
        except pytesseract.TesseractError as exc:
            raise RuntimeError(
                f"Tesseract dili hatasi ({exc}). 'ocr_langs' ayarini kontrol edin. "
                f"Japonca icin jpn.traineddata, Korece icin kor.traineddata gerekir.") from exc
        lines = {}
        for i in range(len(data["text"])):
            txt = data["text"][i].strip()
            conf = float(data["conf"][i])
            if not txt or conf < self.config.get("min_confidence", 40):
                continue
            line = data["line_num"][i]
            lines.setdefault(line, []).append(txt)
        joined = "\n".join(" ".join(parts) for parts in lines.values())
        return joined.strip()

    def _read_windows(self, img):
        if img.mode != "RGB":
            img = img.convert("RGB")
        lang = self.config.get("source_lang", "otomatik")
        win_lang = WINDOWS_OCR_LANG.get(lang)
        result = _WIN_OCR.recognize_pil(img, lang=win_lang)
        lines = [line.text for line in result.lines if line.text.strip()]
        return "\n".join(lines).strip()

    def read(self, img):
        if not self.is_ready:
            raise RuntimeError("OCR motoru hazir degil.\n" + self.engine_help())
        with self._lock:
            if self._mode == "windows":
                return self._read_windows(img)
            return self._read_tesseract(img)

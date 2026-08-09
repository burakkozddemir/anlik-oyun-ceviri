"""OCR: dil eslemeleri, PSM/tessdata ayarlari ve Tesseract cagrisi."""
import sys

from PIL import Image

from anlik_oyun_ceviri.ocr import OcrEngine


def make_engine(config=None, **kw):
    cfg = {"ocr_langs": "eng+tur", "psm": 6, "tessdata_dir": "",
           "ocr_scale": 1.0, "min_confidence": 40}
    cfg.update(config or {})
    cfg.update(kw)
    return OcrEngine(cfg)


def sample_img():
    return Image.new("RGB", (32, 16), "white")


class FakePytesseract:
    """Gercek pytesseract modülünün 'pytesseract.pytesseract' yolunu taklit eder."""

    Output = type("Output", (), {"DICT": "dict"})
    pytesseract = type("Inner", (), {"tesseract_cmd": ""})()


def test_tess_lang_aliases():
    e = make_engine(ocr_langs="zh-CN+pt+tr+ru")
    assert e._tess_langs() == "chi_sim+por+tr+ru"


def test_tess_lang_empty_falls_back_to_eng():
    e = make_engine(ocr_langs="")
    assert e._tess_langs() == "eng"


def test_tess_config_uses_psm_from_config():
    e = make_engine(psm=11)
    assert "--psm 11" in e._tess_config("")


def test_tess_config_rejects_invalid_psm():
    e = make_engine(psm=99)
    assert "--psm 6" in e._tess_config("")
    e2 = make_engine(psm="abc")
    assert "--psm 6" in e2._tess_config("")


def test_tess_config_includes_tessdata_dir():
    e = make_engine()
    cfg = e._tess_config(r"C:\Tess\tessdata")
    assert "--tessdata-dir" in cfg
    assert r"C:\\Tess\\tessdata" in cfg  # komut satirinda cift ters bölü


def test_read_tesseract_uses_confidence_and_psm(monkeypatch):
    class Fake(FakePytesseract):
        @staticmethod
        def image_to_data(img, lang, config, output_type, timeout):
            assert config.startswith("--psm 6")  # tessdata eklense bile psm oncelikli
            assert timeout == 6
            return {
                "text": ["Merhaba", "dunya", "sil", ""],
                "conf": [90.0, 80.0, 10.0, -1.0],
                "line_num": [1, 1, 1, 1],
            }

    monkeypatch.setattr(sys.modules["anlik_oyun_ceviri.ocr"], "pytesseract", Fake())
    e = make_engine()
    e._mode = "tesseract"

    out = e.read(sample_img())
    assert "Merhaba" in out
    assert "sil" not in out  # guven esiginin altinda


class _TesseractError(Exception):
    pass


def test_tesseract_error_is_explanatory(monkeypatch):
    class Fake(FakePytesseract):
        TesseractError = _TesseractError

        @staticmethod
        def image_to_data(img, lang, config, output_type, timeout):
            raise _TesseractError("Simulated")

    monkeypatch.setattr(sys.modules["anlik_oyun_ceviri.ocr"], "pytesseract", Fake())
    e = make_engine()
    e._mode = "tesseract"

    try:
        e.read(sample_img())
        assert False, "hata firlatilmali"
    except RuntimeError as exc:
        assert "ocr_langs" in str(exc)

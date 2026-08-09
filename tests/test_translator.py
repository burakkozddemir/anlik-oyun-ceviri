"""Cevirmen: onbellek, marker tabanli toplu ceviri ve olculu cagri."""
import re

from anlik_oyun_ceviri.translator import (
    Translator,
    TranslationCache,
    hash_key,
)


def make_translator(tmp_path):
    cfg = {
        "engine": "google",
        "api_keys": {"openai_model": "gpt-4o-mini", "openai_base_url": ""},
    }
    return Translator(cfg, str(tmp_path / "cache.json"))


def test_hash_key_deterministic_and_versioned():
    a = hash_key("en", "tr", "google", "Hello")
    b = hash_key("en", "tr", "google", "Hello")
    assert a == b
    c = hash_key("en", "tr", "google", "Hello", extra="model-x")
    assert a != c  # model degisimi cache'i gecersiz kilar


def test_marked_extraction():
    block = "[[0]] Merhaba\n[[1]] Dunya"
    assert Translator._extract_marked(block, 2) == ["Merhaba", "Dunya"]


def test_marked_extraction_failure_returns_none():
    assert Translator._extract_marked("Merhaba\nDunya", 2) is None
    assert Translator._extract_marked("[[0]] x", 2) is None
    assert Translator._extract_marked("", 1) is None


def test_cache_get_set_and_atomic_write(tmp_path):
    cache = TranslationCache(str(tmp_path / "c.json"))
    cache.set("k1", {"text": "Merhaba", "t": 100, "latency_ms": 5})
    assert cache.get("k1")["text"] == "Merhaba"
    cache2 = TranslationCache(str(tmp_path / "c.json"))
    assert cache2.get("k1")["text"] == "Merhaba"
    leftovers = [p for p in tmp_path.iterdir() if p.suffix == ".tmp"]
    assert leftovers == []


def test_cache_eviction_caps_size(tmp_path):
    cache = TranslationCache(str(tmp_path / "c.json"))
    for i in range(20001):
        cache._data[f"k{i}"] = {"text": "x", "t": i}
    cache.set("yeni", {"text": "y", "t": 99999})
    assert len(cache._data) <= 15002  # 20002 - 5000 en eski
    assert cache.get("yeni") is not None


def test_translate_lines_marks_and_orders(monkeypatch, tmp_path):
    tr = make_translator(tmp_path)
    calls = []

    def fake_translate(text, source, target, engine):
        calls.append(text)
        out = []
        for ln in text.splitlines():
            m = re.match(r"\[\[(\d+)\]\] (.*)", ln)
            if m:
                out.append(f"[[{m.group(1)}]] TR:{m.group(2)}")
            else:
                out.append(f"TR:{ln}")
        return "\n".join(out)

    monkeypatch.setattr(tr, "_translate", fake_translate)
    out = tr.translate_lines(["Hello world", "Second line"], "en", "tr")
    assert out == ["TR:Hello world", "TR:Second line"]
    assert len(calls) == 1  # tek toplu istek
    assert "[[0]]" in calls[0] and "[[1]]" in calls[0]


def test_translate_lines_falls_back_per_line(monkeypatch, tmp_path):
    tr = make_translator(tmp_path)
    calls = []

    def fake_translate(text, source, target, engine):
        calls.append(text)
        return text.replace("[[0]] ", "").replace("[[1]] ", "")

    monkeypatch.setattr(tr, "_translate", fake_translate)
    out = tr.translate_lines(["A", "B"], "en", "tr")
    assert out == ["A", "B"]
    # 1 toplu deneme + isaretleyiciler kaybolunca satir satir 2 istek
    assert len(calls) == 3


def test_translate_lines_cache_hit_skips_network(monkeypatch, tmp_path):
    tr = make_translator(tmp_path)
    calls = []

    def fake_translate(text, source, target, engine):
        calls.append(text)
        return f"TR:{text}"

    monkeypatch.setattr(tr, "_translate", fake_translate)
    first = tr.translate_lines(["Hello"], "en", "tr")
    assert first == ["TR:Hello"]
    second = tr.translate_lines(["Hello"], "en", "tr")
    assert second == ["TR:Hello"]
    assert len(calls) == 1  # ikinci cagri cache'ten


def test_translate_lines_measured(tmp_path, monkeypatch):
    tr = make_translator(tmp_path)
    monkeypatch.setattr(tr, "_translate", lambda t, s, tg, e: f"TR:{t}")
    out, latency = tr.translate_lines_measured(["X"], "en", "tr")
    assert out == ["TR:X"]
    assert isinstance(latency, int) and latency >= 0

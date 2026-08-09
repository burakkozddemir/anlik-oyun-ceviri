"""Config yukleme/kaydetme, atomik yazma, bozuk dosya yedegi ve DPAPI."""
import json
import os

from anlik_oyun_ceviri import config as config_mod


def test_defaults_when_missing():
    cfg = config_mod.load_config()
    assert cfg["target_lang"] == "tr"
    assert cfg["engine"] == "google"
    assert cfg["api_keys"]["deepl"] == ""


def test_roundtrip(tmp_path):
    cfg = config_mod.load_config()
    cfg["target_lang"] = "en"
    cfg["region"] = {"left": -100, "top": 10, "width": 500, "height": 90}
    config_mod.save_config(cfg)
    loaded = config_mod.load_config()
    assert loaded["target_lang"] == "en"
    assert loaded["region"] == cfg["region"]
    assert loaded["config_version"] == config_mod.CONFIG_VERSION


def test_no_tmp_left(tmp_path):
    cfg = config_mod.load_config()
    config_mod.save_config(cfg)
    d = tmp_path / "userdata"
    leftovers = [p for p in os.listdir(d) if p.endswith(".tmp")]
    assert leftovers == []


def test_corrupt_file_backed_up(tmp_path):
    path = tmp_path / "userdata" / "config.json"
    path.write_text("{bozuk json", encoding="utf-8")
    cfg = config_mod.load_config()
    assert cfg["engine"] == "google"  # varsayilanlara donuldu
    backups = [p for p in os.listdir(tmp_path / "userdata") if ".corrupt-" in p]
    assert len(backups) == 1
    assert not path.exists()  # bozuk dosya tasinmis


def test_dpapi_key_roundtrip(tmp_path):
    cfg = config_mod.load_config()
    cfg["api_keys"]["openai"] = "sk-test-12345"
    config_mod.save_config(cfg)
    raw = json.loads((tmp_path / "userdata" / "config.json").read_text(encoding="utf-8"))
    assert "api_keys_enc" in raw
    assert "api_keys" not in raw
    loaded = config_mod.load_config()
    assert loaded["api_keys"]["openai"] == "sk-test-12345"


def test_plaintext_fallback_when_dpapi_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(config_mod, "_dpapi_protect", lambda blob: None)
    cfg = config_mod.load_config()
    cfg["api_keys"]["deepl"] = "duz-metin"
    config_mod.save_config(cfg)
    raw = json.loads((tmp_path / "userdata" / "config.json").read_text(encoding="utf-8"))
    assert raw["api_keys"]["deepl"] == "duz-metin"
    assert config_mod.load_config()["api_keys"]["deepl"] == "duz-metin"


def test_legacy_migration(tmp_path, monkeypatch):
    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir()
    monkeypatch.setattr(config_mod, "APP_DIR", str(legacy_dir))
    (legacy_dir / "config.json").write_text(
        json.dumps({"target_lang": "de"}), encoding="utf-8")
    cfg = config_mod.load_config()
    assert cfg["target_lang"] == "de"
    assert not (legacy_dir / "config.json").exists()  # tasindi


def test_cache_dir_under_userdata(tmp_path):
    d = config_mod.cache_dir()
    assert os.path.normpath(d).startswith(str(tmp_path / "userdata"))
    assert os.path.isdir(d)

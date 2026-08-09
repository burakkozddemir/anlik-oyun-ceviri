"""Testler icin ortak kurulum: kullanici verisi gecici klasore yonlendirilir."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def user_data_env(tmp_path, monkeypatch):
    """Config/cache'in gercek kullanici klasorune dokunmamasini saglar."""
    d = tmp_path / "userdata"
    d.mkdir()
    monkeypatch.setenv("ANLIK_USER_DIR", str(d))
    monkeypatch.setenv("ANLIK_CONFIG", str(d / "config.json"))
    return d

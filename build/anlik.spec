# -*- mode: python ; coding: utf-8 -*-
import os

ROOT = os.path.dirname(os.path.abspath(SPEC))
if os.path.basename(ROOT) == "build":
    ROOT = os.path.dirname(ROOT)

a = Analysis(
    [os.path.join(ROOT, "app.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, "tessdata"), "tessdata"),
        (os.path.join(ROOT, "assets", "logo.ico"), "assets"),
        (os.path.join(ROOT, "assets", "logo_64.png"), "assets"),
        (os.path.join(ROOT, "assets", "logo.png"), "assets"),
    ],
    hiddenimports=[
        "deep_translator",
        "openai",
        "mss",
        "pytesseract",
        "keyboard",
        "requests",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["winocr"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AnlikOyunCeviri",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(ROOT, "assets", "logo.ico"),
    version=os.path.join(ROOT, "build", "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="AnlikOyunCeviri",
)

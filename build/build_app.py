r"""Anlik Oyun Ceviri paketleme betigi.

1) Tesseract calisma zamani gecici klasore kopyalanir (exe + DLL'ler).
2) PyInstaller ile uygulama exe'si derlenir (tessdata + ikon gomulu).
3) Tesseract runtime ve tessdata dist klasorune tasinir.

Kullanim:  python build\build_app.py
Cikti:     dist\AnlikOyunCeviri\AnlikOyunCeviri.exe
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist", "AnlikOyunCeviri")
INTERNAL = os.path.join(DIST, "_internal")
TESS_SRC = r"C:\Program Files\Tesseract-OCR"
TESS_RUNTIME = os.path.join(BUILD, "ocr_runtime", "Tesseract-OCR")


def stage_tesseract():
    if os.path.exists(os.path.join(TESS_RUNTIME, "tesseract.exe")):
        print("[OK] Tesseract runtime zaten hazir:", TESS_RUNTIME)
        return
    os.makedirs(TESS_RUNTIME, exist_ok=True)
    copied = 0
    for name in os.listdir(TESS_SRC):
        if name.endswith(".dll") or name.lower() == "tesseract.exe":
            shutil.copy2(os.path.join(TESS_SRC, name),
                         os.path.join(TESS_RUNTIME, name))
            copied += 1
    print(f"[OK] Tesseract runtime kopyalandi: {copied} dosya")


def run_pyinstaller():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--distpath", os.path.join(ROOT, "dist"),
        "--workpath", os.path.join(BUILD, "pywork"),
        os.path.join(BUILD, "anlik.spec"),
    ]
    print("[..] PyInstaller calistiriliyor...")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print("[HATA] PyInstaller basarisiz.")
        sys.exit(1)


def copy_runtime():
    target = os.path.join(INTERNAL, "Tesseract-OCR")
    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.copytree(TESS_RUNTIME, target)
    print("[OK] Tesseract runtime ->", target)
    if not os.path.exists(os.path.join(INTERNAL, "tessdata")):
        shutil.copytree(os.path.join(ROOT, "tessdata"),
                        os.path.join(INTERNAL, "tessdata"))
        print("[OK] tessdata -> _internal")


def main():
    if not os.path.exists(TESS_SRC):
        print("[UYARI] Kaynak Tesseract bulunamadi:", TESS_SRC)
        print("        Tesseract olmadan derlenecek; OCR calismaz.")
    else:
        stage_tesseract()
    run_pyinstaller()
    copy_runtime()
    exe = os.path.join(DIST, "AnlikOyunCeviri.exe")
    if not os.path.exists(exe):
        print("[HATA] Derlenen exe bulunamadi:", exe)
        sys.exit(1)
    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _, fs in os.walk(DIST) for f in fs)
    print("[OK] Derleme tamam:", exe)
    print(f"[OK] Boyut: {total / (1024 * 1024):.1f} MB")


if __name__ == "__main__":
    main()

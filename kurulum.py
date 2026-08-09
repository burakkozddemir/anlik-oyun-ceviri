"""Anlik Oyun Ceviri kurulum betigi.

1) Gerekli Python paketlerini kurar.
2) Tesseract OCR kurulumunu denetler, yoksa kurulmasi icin talimat verir
   (Windows: winget install UB-Mannheim.TesseractOCR).

CodeFein Studio tarafindan gelistirilmistir. Tum haklari saklidir.
"""
import shutil
import subprocess
import sys

from anlik_oyun_ceviri import __app_name__, __beta__, __company__, __copyright__, __version__

REQUIREMENTS = ["requirements.txt"]
EXTRA_OPTIONAL = [
    ("winocr", "Windows yerlesik OCR yedegi icin (istege bagli)"),
]


def run_pip(args):
    return subprocess.run([sys.executable, "-m", "pip"] + args,
                          check=False)


def check_tesseract():
    exe = shutil.which("tesseract")
    if exe:
        print(f"[OK] Tesseract bulundu: {exe}")
        return True
    print("[UYARI] Tesseract bulunamadi.")
    print("  Kurulum secenekleri:")
    print("    - winget install UB-Mannheim.TesseractOCR")
    print("    - https://github.com/UB-Mannheim/tesseract/wiki adresinden indirin")
    print("  Kurduktan sonra config.json icindeki 'tesseract_cmd' alanina exe yolunu yazabilirsiniz.")
    return False


def main():
    suffix = " BETA" if __beta__ else ""
    print(f"=== {__app_name__} v{__version__}{suffix} - {__company__} - Kurulum ===")
    print("Python:", sys.version.split()[0])
    ok = run_pip(["install", "-r", REQUIREMENTS[0]])
    if ok.returncode != 0:
        print("[HATA] Paket kurulumu basarisiz.")
        sys.exit(1)

    print("\n[OK] Ana paketler kuruldu.")
    for pkg, desc in EXTRA_OPTIONAL:
        r = run_pip(["install", pkg])
        if r.returncode == 0:
            print(f"[OK] {pkg} kuruldu ({desc}).")
        else:
            print(f"[UYARI] {pkg} kurulamadi ({desc}). Devam edilebilir.")

    print("\n--- OCR kontrolu ---")
    check_tesseract()

    print("\nKurulum tamam. Calistirmak icin:  python app.py")
    print("Kisayol: F9 = ceviriyi baslat/durdur")
    print()
    print(__copyright__)


if __name__ == "__main__":
    main()

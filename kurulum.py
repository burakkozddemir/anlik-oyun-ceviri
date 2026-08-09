"""Anlık Oyun Çeviri kurulum betiği.

1) Gerekli Python paketlerini kurar.
2) Tesseract OCR kurulumunu denetler, yoksa kurulması için talimat verir
   (Windows: winget install UB-Mannheim.TesseractOCR).

CodeFein Studio tarafından geliştirilmiştir. Tüm hakları saklıdır.
"""
import shutil
import subprocess
import sys

from anlik_oyun_ceviri import __app_name__, __beta__, __company__, __copyright__, __version__

REQUIREMENTS = ["requirements.txt"]
EXTRA_OPTIONAL = [
    ("winocr", "Windows yerleşik OCR yedeği için (isteğe bağlı)"),
]


def run_pip(args):
    return subprocess.run([sys.executable, "-m", "pip"] + args,
                          check=False)


def check_tesseract():
    exe = shutil.which("tesseract")
    if exe:
        print(f"[OK] Tesseract bulundu: {exe}")
        return True
    print("[UYARI] Tesseract bulunamadı.")
    print("  Kurulum seçenekleri:")
    print("    - winget install UB-Mannheim.TesseractOCR")
    print("    - https://github.com/UB-Mannheim/tesseract/wiki adresinden indirin")
    print("  Kurduktan sonra config.json içindeki 'tesseract_cmd' alanına exe yolunu yazabilirsiniz.")
    return False


def main():
    suffix = " BETA" if __beta__ else ""
    print(f"=== {__app_name__} v{__version__}{suffix} - {__company__} - Kurulum ===")
    print("Python:", sys.version.split()[0])
    ok = run_pip(["install", "-r", REQUIREMENTS[0]])
    if ok.returncode != 0:
        print("[HATA] Paket kurulumu başarısız.")
        sys.exit(1)

    print("\n[OK] Ana paketler kuruldu.")
    for pkg, desc in EXTRA_OPTIONAL:
        r = run_pip(["install", pkg])
        if r.returncode == 0:
            print(f"[OK] {pkg} kuruldu ({desc}).")
        else:
            print(f"[UYARI] {pkg} kurulamadı ({desc}). Devam edilebilir.")

    print("\n--- OCR kontrolü ---")
    check_tesseract()

    print("\nKurulum tamam. Çalıştırmak için:  python app.py")
    print("Kısayol: F9 = çeviriyi başlat/durdur")
    print()
    print(__copyright__)


if __name__ == "__main__":
    main()

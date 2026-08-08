"""Anlik Oyun Ceviri - giris noktasi.

Kullanim:  python app.py
Kisayol:   F9 = baslat/durdur
"""
import ctypes
import sys


def _enable_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:  # noqa: BLE001
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:  # noqa: BLE001
            pass


def main():
    _enable_dpi_awareness()
    try:
        import tkinter as tk
    except ImportError as exc:
        print(f"[HATA] tkinter kullanilamiyor: {exc}")
        sys.exit(1)

    from anlik_oyun_ceviri.gui import MainGUI

    root = tk.Tk()
    app = MainGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()

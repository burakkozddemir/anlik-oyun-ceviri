"""Uygulama ekran görüntülerini üretir (README için).

Çıktı: assets/screenshots/ana-pencere.png, hakkinda.png, api-prompt.png
"""
import ctypes
import ctypes.wintypes
import os
import sys
import tempfile
import tkinter as tk

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "assets", "screenshots")
os.makedirs(OUT, exist_ok=True)

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:  # noqa: BLE001
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:  # noqa: BLE001
        pass

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
wintypes = ctypes.wintypes


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def capture(hwnd, path):
    rect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w, h = rect.right, rect.bottom
    if w <= 0 or h <= 0:
        print("  [UYARI] Geçersiz pencere boyutu:", w, h)
        return
    hdc_win = user32.GetWindowDC(hwnd)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_win)
    bmp = gdi32.CreateCompatibleBitmap(hdc_win, w, h)
    old = gdi32.SelectObject(hdc_mem, bmp)
    user32.PrintWindow(hwnd, hdc_mem, 0x2)
    bits = (ctypes.c_ubyte * (w * h * 4))()
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0  # BI_RGB
    gdi32.GetDIBits(hdc_mem, bmp, 0, h, bits, ctypes.byref(bmi), 0)
    img = Image.frombuffer("RGBA", (w, h), bytes(bits), "raw", "BGRA", 0, 1)
    img.save(path)
    gdi32.SelectObject(hdc_mem, old)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(hwnd, hdc_win)
    print("  [OK]", path, img.size)


def main():
    import json

    import tkinter.font as tkfont

    cfg_path = os.path.join(tempfile.gettempdir(), "aoc_shot_cfg.json")
    json.dump({"auto_detect_game": False,
               "api_key_prompt_done": False,
               "region": {"left": 100, "top": 100, "width": 800, "height": 120},
               "window_size": "780x880"}, open(cfg_path, "w"))
    os.environ["ANLIK_CONFIG"] = cfg_path

    from anlik_oyun_ceviri.gui import MainGUI

    root = tk.Tk()
    g = MainGUI(root)
    root.update_idletasks()
    root.geometry("780x880+80+60")
    root.update()
    root.lift()
    root.focus_force()

    hwnd_root = root.winfo_id()
    print("Ana pencere hwnd:", hwnd_root)
    capture(hwnd_root, os.path.join(OUT, "ana-pencere.png"))

    g._maybe_prompt_api_key()
    root.update_idletasks()
    root.update()
    prompt_hwnd = None
    prompt_win = None
    for w in root.winfo_children():
        if isinstance(w, tk.Toplevel) and w.title() == "API Anahtarı Ekle":
            prompt_win = w
            prompt_hwnd = w.winfo_id()
            break
    print("API prompt hwnd:", prompt_hwnd)
    if prompt_hwnd:
        capture(prompt_hwnd, os.path.join(OUT, "api-prompt.png"))
        prompt_win.destroy()
        root.update()

    g._show_about()
    root.update_idletasks()
    root.update()
    about_hwnd = None
    for w in root.winfo_children():
        if isinstance(w, tk.Toplevel) and w.title() == "Hakkında":
            about_hwnd = w.winfo_id()
            break
    print("Hakkında hwnd:", about_hwnd)
    if about_hwnd:
        capture(about_hwnd, os.path.join(OUT, "hakkinda.png"))

    g.on_close()


if __name__ == "__main__":
    main()

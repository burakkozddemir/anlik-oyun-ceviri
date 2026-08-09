"""Oyun uzerine binen saydam, tiklamasi oyuna gecen overlay penceresi."""
import ctypes
import tkinter as tk

from .screen import virtual_desktop

WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
GWL_EXSTYLE = -20

# Windows 10 2004+: pencereyi ekran yakalama API'lerinden (OCR dahil)
# haric tutar; overlay kendi metnini tekrar OCR'lamaz.
WDA_EXCLUDEFROMCAPTURE = 0x11

TRANSPARENT_COLOR = "#010203"
BOX_BG = "#0d0f14"


def _apply_click_through(hwnd):
    try:
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        return True
    except Exception:  # noqa: BLE001
        return False


def _exclude_from_capture(hwnd):
    """Overlay'i ekran yakalamasindan (mss/BitBlt) haric tutmayi dener."""
    try:
        return bool(ctypes.windll.user32.SetWindowDisplayAffinity(
            hwnd, WDA_EXCLUDEFROMCAPTURE))
    except Exception:  # noqa: BLE001
        return False


class SubtitleOverlay:
    def __init__(self, root):
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self._transparent_ok = False
        try:
            self.win.attributes("-transparentcolor", TRANSPARENT_COLOR)
            self._transparent_ok = True
        except tk.TclError:
            pass
        self.win.configure(bg=TRANSPARENT_COLOR)
        self._mode = "transparent"
        self._alpha = 1.0
        self._labels = []
        self._font = ("Segoe UI", 20, "bold")
        self._color = "#FFFFFF"
        self._bg = "#000000"
        self._max_lines = 3
        self._positioned = False
        self._visible = True
        self._click_through = False
        self._excluded = False
        self._apply_style()

    def _apply_style(self):
        try:
            self.win.update_idletasks()
            hwnd = self.win.wm_frame()
            if not hwnd:
                hwnd = self.win.winfo_id()
            if hwnd:
                self._click_through = _apply_click_through(hwnd)
                self._excluded = _exclude_from_capture(hwnd)
        except tk.TclError:
            pass

    @property
    def click_through_ok(self):
        return self._click_through

    @property
    def capture_excluded(self):
        return self._excluded

    def set_style(self, font_family, font_size, color, bg_color, mode,
                  max_lines):
        for lbl in self._labels:
            lbl.destroy()
        self._labels = []
        self._font = (font_family or "Segoe UI", max(8, int(font_size)), "bold")
        self._color = color
        self._bg = bg_color or "#000000"
        self._mode = mode if mode in ("transparent", "box") else "transparent"
        self._max_lines = max(1, int(max_lines))
        self._rebuild_background()

    def update_position(self, region):
        w = max(1, int(region["width"]))
        h = max(1, int(region["height"]))
        left = int(region["left"])
        top = int(region["top"])
        vd = virtual_desktop()
        x_from_right = vd["width"] - (left - vd["left"]) - w
        y_from_bottom = vd["height"] - (top - vd["top"]) - h
        x_from_right = max(0, x_from_right)
        y_from_bottom = max(0, y_from_bottom)
        self.win.geometry(f"{w}x{h}-{x_from_right}-{y_from_bottom}")
        self._positioned = True

    def _rebuild_background(self):
        if self._mode == "box":
            self.win.configure(bg=BOX_BG)
            self.win.attributes("-alpha", max(0.05, min(1.0, self._alpha)))
        else:
            self.win.configure(bg=TRANSPARENT_COLOR)
            self.win.attributes("-alpha", 1.0)
        for lbl in self._labels:
            lbl.configure(bg=(BOX_BG if self._mode == "box" else TRANSPARENT_COLOR))

    def show(self, lines, opacity=1.0):
        if not self._positioned or not self._visible:
            return
        self._alpha = max(0.05, min(1.0, float(opacity)))
        self._rebuild_background()
        if len(lines) > self._max_lines:
            lines = lines[-self._max_lines:]
        wrap = max(50, int(self.win.winfo_width()) - 24)
        bg = BOX_BG if self._mode == "box" else TRANSPARENT_COLOR
        for i in range(max(len(lines), len(self._labels))):
            if i < len(self._labels):
                lbl = self._labels[i]
            else:
                lbl = tk.Label(
                    self.win, fg=self._color, bg=bg,
                    font=self._font, justify="left", anchor="sw",
                    wraplength=wrap,
                )
                lbl.pack(side="bottom", anchor="sw", padx=8, pady=2)
                self._labels.append(lbl)
            text = lines[i] if i < len(lines) else ""
            if lbl.cget("text") != text:
                lbl.configure(text=text)
        self.win.deiconify()
        self.win.lift()

    def set_visible(self, visible):
        self._visible = bool(visible)
        if self._visible:
            self.win.deiconify()
        else:
            self.win.withdraw()

    def hide(self):
        self.win.withdraw()

    def close(self):
        try:
            self.win.destroy()
        except tk.TclError:
            pass

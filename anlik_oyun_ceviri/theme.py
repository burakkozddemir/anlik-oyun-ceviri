"""Modern koyu tema: renk paleti, ttk stilleri ve ozel widget yardimcilari.

Flat design: derin kontrast, yumusak vurgular, ince cerceveler ve
hafif hover/active geri bildirimleri.
"""
import tkinter as tk
from tkinter import ttk

# --- Palet (modern, derin) ---
BG = "#0f121a"
BG_ALT = "#161a25"
CARD = "#1b2030"
CARD_2 = "#232a3d"
CARD_3 = "#2a3248"
BORDER = "#2d3447"
BORDER_SOFT = "#242b3d"
TEXT = "#eef1f8"
MUTED = "#96a0ba"
FAINT = "#6b7591"

ACCENT = "#6d8dff"
ACCENT_HOVER = "#5474f2"
ACCENT_DIM = "#3d4a7d"
ACCENT_SOFT = "#26315c"
VIOLET = "#9b7bff"
VIOLET_DIM = "#3d3270"
GREEN = "#43d9a0"
GREEN_DIM = "#1f3a33"
RED = "#ff6b6b"
RED_DIM = "#3d2326"
YELLOW = "#f2c06a"
CYAN = "#5ecde0"

FONT = "Segoe UI"
FONT_BOLD = "Segoe UI Semibold"

STATUS_COLORS = {
    "info": CYAN,
    "ok": GREEN,
    "error": RED,
    "warn": YELLOW,
}


def apply_theme(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=BG)
    root.option_add("*Font", (FONT, 10))
    root.option_add("*TCombobox*Listbox.background", CARD_2)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", TEXT)
    root.option_add("*TEntry.background", CARD_2)

    style.configure(".", background=BG, foreground=TEXT, font=(FONT, 10))
    style.map(".", background=[("active", BG_ALT)])

    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("Card2.TFrame", background=CARD_2)

    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=CARD, foreground=TEXT)
    style.configure("Card2.TLabel", background=CARD_2, foreground=TEXT)
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("CardMuted.TLabel", background=CARD, foreground=MUTED)
    style.configure("Title.TLabel", background=BG, foreground=TEXT,
                    font=(FONT_BOLD, 15))
    style.configure("Section.TLabel", background=CARD, foreground=ACCENT,
                    font=(FONT_BOLD, 11))
    style.configure("Small.TLabel", font=(FONT, 9))

    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_ALT, foreground=MUTED,
                    padding=(16, 8), font=(FONT, 10))
    style.map("TNotebook.Tab",
              background=[("selected", CARD), ("active", CARD_2)],
              foreground=[("selected", TEXT)])

    style.configure("TEntry", fieldbackground=CARD_2, foreground=TEXT,
                    insertcolor=TEXT, bordercolor=BORDER, lightcolor=BORDER,
                    darkcolor=BORDER, padding=6)
    style.map("TEntry",
              fieldbackground=[("focus", "#2a3146")],
              bordercolor=[("focus", ACCENT)])

    style.configure("TCombobox", fieldbackground=CARD_2, background=CARD_2,
                    foreground=TEXT, arrowcolor=MUTED, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=5)
    style.map("TCombobox",
              fieldbackground=[("readonly", CARD_2), ("focus", "#2a3146")],
              foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", CARD_2)],
              selectforeground=[("readonly", TEXT)],
              arrowcolor=[("active", ACCENT)])

    style.configure("TSpinbox", fieldbackground=CARD_2, foreground=TEXT,
                    arrowcolor=MUTED, bordercolor=BORDER, padding=5)

    style.configure("TCheckbutton", background=CARD, foreground=TEXT,
                    font=(FONT, 10))
    style.map("TCheckbutton", background=[("active", CARD)],
              indicatorcolor=[("selected", ACCENT)])

    style.configure("Horizontal.TScale", background=CARD,
                    troughcolor=CARD_2, bordercolor=CARD_2,
                    lightcolor=ACCENT, darkcolor=ACCENT)
    style.map("Horizontal.TScale", background=[("active", CARD)])

    style.configure("TProgressbar", background=ACCENT, troughcolor=CARD_2,
                    bordercolor=CARD_2)

    style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff",
                    font=(FONT_BOLD, 10), borderwidth=0, padding=(14, 9))
    style.map("Accent.TButton",
              background=[("active", ACCENT_HOVER), ("pressed", ACCENT_DIM)])

    style.configure("Secondary.TButton", background=CARD_2, foreground=TEXT,
                    borderwidth=0, padding=(12, 8))
    style.map("Secondary.TButton",
              background=[("active", "#2d3550"), ("pressed", BORDER)])

    style.configure("Danger.TButton", background=RED_DIM, foreground=RED,
                    borderwidth=0, padding=(12, 8))
    style.map("Danger.TButton", background=[("active", "#4a2a2e")])

    style.configure("TLabelframe", background=CARD, bordercolor=BORDER,
                    relief="flat", padding=6)
    style.configure("TLabelframe.Label", background=CARD, foreground=ACCENT,
                    font=(FONT_BOLD, 10))


def card(parent, bg=CARD, **kw):
    frame = tk.Frame(parent, bg=bg, **kw)
    frame.configure(highlightbackground=BORDER, highlightthickness=1,
                    bd=0)
    return frame


def section(parent, text, bg=CARD):
    """Vurgu cubuklu modern bolum basligi."""
    wrap = tk.Frame(parent, bg=bg)
    bar = tk.Frame(wrap, bg=ACCENT, width=3, height=14)
    bar.pack(side="left", padx=(12, 8), pady=(10, 4))
    bar.pack_propagate(False)
    lbl = tk.Label(wrap, text=text, bg=bg, fg=ACCENT,
                   font=(FONT_BOLD, 11))
    lbl.pack(side="left", pady=(9, 3))
    return wrap


class ModernButton(tk.Button):
    """Hover ve basili durum destekli modern flat buton."""

    def __init__(self, parent, text, command=None, kind="secondary", **kw):
        palette = {
            "secondary": (CARD_2, TEXT, "#2d3550", "#212736"),
            "accent": (ACCENT, "#ffffff", ACCENT_HOVER, ACCENT_DIM),
            "danger": (RED_DIM, RED, "#4a2a2e", "#331d20"),
            "ghost": (CARD, MUTED, CARD_2, BG_ALT),
            "violet": (VIOLET_DIM, VIOLET, "#453c85", "#2f2a5c"),
        }
        bg, fg, hover, pressed = palette.get(kind, palette["secondary"])
        kw.setdefault("font", (FONT, 10))
        kw.setdefault("padx", 14)
        kw.setdefault("pady", 7)
        super().__init__(parent, text=text, command=command, bd=0,
                         bg=bg, fg=fg, activebackground=hover,
                         activeforeground=fg,
                         cursor="hand2",
                         relief="flat",
                         highlightthickness=0, **kw)
        self._hover = hover
        self._pressed = pressed
        self._base = bg
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, _):
        self.configure(bg=self._hover)

    def _on_leave(self, _):
        self.configure(bg=self._base)

    def _on_press(self, _):
        self.configure(bg=self._pressed)

    def _on_release(self, _):
        self.configure(bg=self._hover)

    def set_kind(self, kind):
        palette = {
            "secondary": (CARD_2, TEXT, "#2d3550", "#212736"),
            "accent": (ACCENT, "#ffffff", ACCENT_HOVER, ACCENT_DIM),
            "danger": (RED_DIM, RED, "#4a2a2e", "#331d20"),
            "ghost": (CARD, MUTED, CARD_2, BG_ALT),
            "violet": (VIOLET_DIM, VIOLET, "#453c85", "#2f2a5c"),
        }
        bg, fg, hover, pressed = palette.get(kind, palette["secondary"])
        self._base = bg
        self._hover = hover
        self._pressed = pressed
        self.configure(bg=bg, fg=fg, activebackground=hover)


def stat_cell(parent, bg=CARD_2):
    """Ust kenarinda vurgu seridi olan istatistik hucresi."""
    cell = tk.Frame(parent, bg=bg)
    strip = tk.Frame(cell, bg=ACCENT_DIM, height=3)
    strip.pack(fill="x")
    strip.pack_propagate(False)
    body = tk.Frame(cell, bg=bg, padx=10, pady=6)
    body.pack(fill="both", expand=True)
    return cell, body


def make_switch(parent, text, variable, command=None, bg=CARD):
    return ttk.Checkbutton(parent, text=text, variable=variable,
                           command=command, style="TCheckbutton")

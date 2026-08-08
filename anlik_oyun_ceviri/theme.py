"""Koyu tema: renk paleti, ttk stilleri ve ozel widget yardimcilari."""
import tkinter as tk
from tkinter import ttk

BG = "#161923"
BG_ALT = "#1d2130"
CARD = "#232839"
CARD_2 = "#2b3145"
BORDER = "#353b52"
TEXT = "#e9ecf4"
MUTED = "#9aa2ba"
ACCENT = "#6d8dff"
ACCENT_HOVER = "#5c7ef2"
ACCENT_DIM = "#46507a"
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
              fieldbackground=[("focus", "#30364d")],
              bordercolor=[("focus", ACCENT)])

    style.configure("TCombobox", fieldbackground=CARD_2, background=CARD_2,
                    foreground=TEXT, arrowcolor=MUTED, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=5)
    style.map("TCombobox",
              fieldbackground=[("readonly", CARD_2), ("focus", "#30364d")],
              foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", CARD_2)],
              selectforeground=[("readonly", TEXT)])

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
              background=[("active", "#353b52"), ("pressed", BORDER)])

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


class ModernButton(tk.Button):
    """Hover destekli duz (flat) modern buton."""

    def __init__(self, parent, text, command=None, kind="secondary", **kw):
        palette = {
            "secondary": (CARD_2, TEXT, "#353b52"),
            "accent": (ACCENT, "#ffffff", ACCENT_HOVER),
            "danger": (RED_DIM, RED, "#4a2a2e"),
            "ghost": (CARD, MUTED, CARD_2),
        }
        bg, fg, hover = palette.get(kind, palette["secondary"])
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
        self._base = bg
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _):
        self.configure(bg=self._hover)

    def _on_leave(self, _):
        self.configure(bg=self._base)

    def set_kind(self, kind):
        palette = {
            "secondary": (CARD_2, TEXT, "#353b52"),
            "accent": (ACCENT, "#ffffff", ACCENT_HOVER),
            "danger": (RED_DIM, RED, "#4a2a2e"),
            "ghost": (CARD, MUTED, CARD_2),
        }
        bg, fg, hover = palette.get(kind, palette["secondary"])
        self._base = bg
        self._hover = hover
        self.configure(bg=bg, fg=fg, activebackground=hover)


def make_switch(parent, text, variable, command=None, bg=CARD):
    return ttk.Checkbutton(parent, text=text, variable=variable,
                           command=command, style="TCheckbutton")

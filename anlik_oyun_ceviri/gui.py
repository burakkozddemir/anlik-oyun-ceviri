"""Ana kontrol penceresi: modern, koyu temali, sekme tabanli arayuz."""
import ctypes
import os
import queue
import sys
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import colorchooser, messagebox, ttk

from . import __app_name__, __beta__, __company__, __copyright__, __designer__, __version__
from . import config as config_mod
from . import theme
from .overlay import SubtitleOverlay
from .pipeline import TranslationPipeline
from .screen import LANGUAGES, grab_region
from .selector import select_region
from .translator import ENGINES, Translator

APP_TITLE = __app_name__
VERSION = __version__
BETA = __beta__
COMPANY = __company__
DESIGNER = __designer__
COPYRIGHT = __copyright__

ENGINE_DESC = {
    "google": "Ucretsiz ve hizli. API anahtari gerekmez; kucuk metinler icin idealdir.",
    "mymemory": "Ucretsiz yedek motor. Google kapaliyken otomatik devreye girer.",
    "deepl": "Dogal ve akici ceviri kalitesi. DeepL API anahtari gerekir.",
    "openai": "ChatGPT / Gemini / DeepSeek uyumlu. Kaliteli baglam cevirisi; API anahtari gerekir.",
}

PRESET_COLORS = ["#FFFFFF", "#FFFF00", "#00FF00", "#FFD700", "#FF6B6B", "#5ECDE0", "#FF9F43"]

HOTKEYS = {"toggle": "F9", "manual": "F10", "overlay": "F11"}

GAME_FILTER = ("anlik", "oyun ceviri", "python", "tesseract", "masaustu")


class MainGUI:
    def __init__(self, root):
        self.root = root
        self.base_cfg = config_mod.load_config()
        self.cfg = dict(self.base_cfg)
        self.cfg["region"] = dict(self.base_cfg["region"])
        self.pipeline = None
        self._log_buffer = []
        self._overlay_visible = True
        self._ui_thread = threading.current_thread()
        self._ui_tasks = queue.Queue()
        self._pipeline_error_reported = False

        theme.apply_theme(root)
        self._set_window_icon(root)
        suffix = " BETA" if BETA else ""
        root.title(f"{APP_TITLE} v{VERSION}{suffix} - {COMPANY}")
        root.configure(bg=theme.BG)
        root.geometry(self.cfg.get("window_size", "760x860"))
        if self.cfg.get("window_pos"):
            try:
                root.geometry(self.cfg["window_size"] + "+" + self.cfg["window_pos"])
            except tk.TclError:
                pass
        root.minsize(700, 700)

        self.overlay = SubtitleOverlay(root)
        self._apply_overlay_style(init=True)
        self.overlay.update_position(self.cfg["region"])
        if not self.overlay.click_through_ok:
            self._log("Uyari: overlay tiklamalari oyuna geciremiyor (eski Windows surumu?).", "warn")
        if not self.overlay.capture_excluded:
            self._log("Uyari: overlay ekran yakalamasindan haric tutulamadi; goruntude yansima olabilir.", "warn")

        self._build_header()
        self._build_tabs()
        self._build_statusbar()

        self._bind_hotkeys()
        self._poll_queue()
        self._auto_detect_initial()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._log("Program hazir. F9 = baslat/durdur, F10 = ekran ceviri, F11 = altyazi goster/gizle", "info")
        self.root.after(400, self._maybe_prompt_api_key)

    def _set_window_icon(self, root):
        try:
            bases = []
            if getattr(sys, "frozen", False):
                bases.append(getattr(sys, "_MEIPASS", None) or os.path.dirname(sys.executable))
                bases.append(os.path.dirname(sys.executable))
            bases.append(config_mod.APP_DIR)
            for cand in bases:
                if not cand:
                    continue
                png = os.path.join(cand, "assets", "logo_64.png")
                if os.path.exists(png):
                    self._icon_photo = tk.PhotoImage(file=png)
                    root.iconphoto(True, self._icon_photo)
                    return
                ico = os.path.join(cand, "assets", "logo.ico")
                if os.path.exists(ico):
                    root.iconbitmap(default=ico)
                    return
        except Exception:  # noqa: BLE001
            pass

    # ================= UI =================
    def _build_header(self):
        header = tk.Frame(self.root, bg=theme.BG)
        header.pack(fill="x", padx=18, pady=(14, 6))

        brand = tk.Frame(header, bg=theme.BG)
        brand.pack(side="left")
        row = tk.Frame(brand, bg=theme.BG)
        row.pack(anchor="w")
        title = tk.Label(row, text=APP_TITLE, bg=theme.BG, fg=theme.TEXT,
                         font=(theme.FONT_BOLD, 17))
        title.pack(side="left")
        dot = tk.Label(row, text="â—", bg=theme.BG, fg=theme.ACCENT,
                       font=(theme.FONT_BOLD, 9))
        dot.pack(side="left", padx=(6, 5), pady=(5, 0))
        by = tk.Label(row, text=f"by {COMPANY}", bg=theme.BG, fg=theme.MUTED,
                      font=(theme.FONT_BOLD, 10))
        by.pack(side="left", pady=(4, 0))
        if BETA:
            badge = tk.Label(row, text="BETA", bg=theme.ACCENT, fg="#ffffff",
                             font=(theme.FONT_BOLD, 8), padx=6, pady=1)
            badge.pack(side="left", padx=(8, 0), pady=(4, 0))
        sub = tk.Label(brand, text="Gercek zamanli AI oyun cevirmeni",
                       bg=theme.BG, fg=theme.MUTED, font=(theme.FONT, 9))
        sub.pack(anchor="w")

        right = tk.Frame(header, bg=theme.BG)
        right.pack(side="right")
        self.header_state = tk.Label(right, text="DURDURULDU", bg=theme.BG,
                                     fg=theme.MUTED, font=(theme.FONT_BOLD, 9))
        self.header_state.pack(side="top", anchor="e")
        theme.ModernButton(right, text="Hakkinda", command=self._show_about,
                           kind="ghost", font=(theme.FONT, 9), padx=10, pady=3).pack(side="bottom", anchor="e")

    def _build_tabs(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=14, pady=(4, 0))
        self.tab_translate = ttk.Frame(self.nb, style="TFrame")
        self.tab_look = ttk.Frame(self.nb, style="TFrame")
        self.tab_ocr = ttk.Frame(self.nb, style="TFrame")
        self.tab_api = ttk.Frame(self.nb, style="TFrame")
        self.tab_log = ttk.Frame(self.nb, style="TFrame")
        self.nb.add(self.tab_translate, text="  Ceviri  ")
        self.nb.add(self.tab_look, text="  Gorunum  ")
        self.nb.add(self.tab_ocr, text="  OCR / Performans  ")
        self.nb.add(self.tab_api, text="  API Ayarlari  ")
        self.nb.add(self.tab_log, text="  Gunluk  ")
        self._build_tab_translate()
        self._build_tab_look()
        self._build_tab_ocr()
        self._build_tab_api()
        self._build_tab_log()

    # ---------- Ceviri ----------
    def _build_tab_translate(self):
        tab = self.tab_translate

        # Oyun karti
        c = theme.card(tab)
        c.pack(fill="x", padx=14, pady=(14, 8))
        theme.section(c, "OYUN").pack(fill="x")
        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=(0, 4))
        self.game_var = tk.StringVar(value=self.cfg.get("last_game_name", ""))
        entry = ttk.Entry(row, textvariable=self.game_var, width=26)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        entry.bind("<Return>", lambda e: self._on_game_changed())
        entry.bind("<FocusOut>", lambda e: self._on_game_changed())
        theme.ModernButton(row, text="Oyunu Otomatik Al", command=self._auto_detect_game,
                           kind="secondary").pack(side="right")

        self.region_var = tk.StringVar()
        ttk.Label(c, textvariable=self.region_var, style="CardMuted.TLabel",
                  font=(theme.FONT, 9)).pack(anchor="w", padx=12)
        row2 = tk.Frame(c, bg=theme.CARD)
        row2.pack(fill="x", padx=12, pady=(4, 10))
        theme.ModernButton(row2, text="Bolge Sec", command=self._select_region,
                           kind="accent").pack(side="left")
        theme.ModernButton(row2, text="Onizle", command=self._preview_region,
                           kind="secondary").pack(side="left", padx=6)
        theme.ModernButton(row2, text="Manuel Ekran Cevirisi (F10)",
                           command=self._manual_translate,
                           kind="secondary").pack(side="right")
        self._refresh_region_text()

        # Diller
        c = theme.card(tab)
        c.pack(fill="x", padx=14, pady=8)
        theme.section(c, "DILLER").pack(fill="x")
        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=(0, 10))
        col1 = tk.Frame(row, bg=theme.CARD)
        col1.pack(side="left", expand=True, fill="x")
        ttk.Label(col1, text="Kaynak (oyun) dili", style="CardMuted.TLabel").pack(anchor="w")
        self.source_var = tk.StringVar(value=self.cfg.get("source_lang", "otomatik"))
        src = ttk.Combobox(col1, textvariable=self.source_var, width=18, state="readonly",
                           values=[code for code, _ in LANGUAGES])
        src.pack(fill="x", pady=(4, 0))
        theme.ModernButton(row, text="â‡„", command=self._swap_langs,
                           kind="ghost", width=2, font=(theme.FONT_BOLD, 13)).pack(
            side="left", padx=10)
        col2 = tk.Frame(row, bg=theme.CARD)
        col2.pack(side="left", expand=True, fill="x")
        ttk.Label(col2, text="Hedef dil (ceviri)", style="CardMuted.TLabel").pack(anchor="w")
        self.target_var = tk.StringVar(value=self.cfg.get("target_lang", "tr"))
        tgt = ttk.Combobox(col2, textvariable=self.target_var, width=18, state="readonly",
                           values=[code for code, _ in LANGUAGES])
        tgt.pack(fill="x", pady=(4, 0))

        # Motor
        c = theme.card(tab)
        c.pack(fill="x", padx=14, pady=8)
        theme.section(c, "CEVIRI MOTORU").pack(fill="x")
        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=(0, 4))
        self.engine_var = tk.StringVar(value=self.cfg.get("engine", "google"))
        eng = ttk.Combobox(row, textvariable=self.engine_var, width=44, state="readonly",
                           values=[code for code, _ in ENGINES])
        eng.pack(side="left")
        eng.bind("<<ComboboxSelected>>", lambda e: self._refresh_engine_desc())
        self.engine_desc = tk.Label(c, text="", bg=theme.CARD, fg=theme.MUTED,
                                    wraplength=560, justify="left", font=(theme.FONT, 9))
        self.engine_desc.pack(anchor="w", padx=12, pady=(0, 10))
        self._refresh_engine_desc()

        # Baslat / durdur
        wrap = tk.Frame(tab, bg=theme.BG)
        wrap.pack(fill="x", padx=14, pady=8)
        self.toggle_btn = theme.ModernButton(wrap, text="Ceviriyi Baslat  (F9)",
                                             command=self._toggle, kind="accent")
        self.toggle_btn.pack(fill="x", ipady=4)
        self.status_var = tk.StringVar(value="Hazir.")
        ttk.Label(wrap, textvariable=self.status_var, style="Muted.TLabel",
                  wraplength=620, justify="left").pack(anchor="w", pady=(6, 0))

        # Son ceviri
        c = theme.card(tab)
        c.pack(fill="both", expand=True, padx=14, pady=(8, 14))
        theme.section(c, "SON CEVIRI").pack(fill="x")
        self.output_text = tk.Text(c, height=5, wrap="word", bg=theme.CARD_2,
                                   fg=theme.TEXT, insertbackground=theme.TEXT,
                                   font=(theme.FONT, 11), relief="flat",
                                   highlightthickness=1, highlightbackground=theme.BORDER,
                                   padx=10, pady=8)
        self.output_text.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self.output_text.configure(state="disabled")

    # ---------- Gorunum ----------
    def _build_tab_look(self):
        tab = self.tab_look
        c = theme.card(tab)
        c.pack(fill="x", padx=14, pady=(14, 8))
        theme.section(c, "YAZI").pack(fill="x")
        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=(0, 4))
        ttk.Label(row, text="YazÄ± tipi:").pack(side="left")
        self.font_family_var = tk.StringVar(value=self.cfg.get("font_family", "Segoe UI"))
        families = sorted(set(tkfont.families(self.root)))
        fam = ttk.Combobox(row, textvariable=self.font_family_var, width=26,
                           values=families)
        fam.pack(side="left", padx=8)
        fam.bind("<<ComboboxSelected>>", lambda e: self._on_style_change())

        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=(2, 8))
        ttk.Label(row, text="Boyut:").pack(side="left")
        self.font_size_var = tk.IntVar(value=int(self.cfg.get("font_size", 20)))
        ttk.Scale(row, from_=10, to=48, variable=self.font_size_var,
                  orient="horizontal", command=self._on_size_change).pack(
            side="left", fill="x", expand=True, padx=8)
        ttk.Label(row, textvariable=self.font_size_var, width=3).pack(side="left")

        ttk.Label(c, text="Renk:", style="CardMuted.TLabel").pack(anchor="w", padx=12)
        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=(4, 10))
        self.color_var = tk.StringVar(value=self.cfg.get("text_color", "#FFFFFF"))
        for col in PRESET_COLORS:
            b = tk.Button(row, bg=col, width=2, relief="flat", cursor="hand2",
                          command=lambda cc=col: self._set_color(cc))
            b.pack(side="left", padx=3)
        theme.ModernButton(row, text="Ozel renk...", command=self._pick_color,
                           kind="secondary").pack(side="left", padx=8)

        c = theme.card(tab)
        c.pack(fill="x", padx=14, pady=8)
        theme.section(c, "ALTYAZI KATMANI").pack(fill="x")
        self.mode_var = tk.StringVar(value=self.cfg.get("overlay_mode", "transparent"))
        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12)
        ttk.Radiobutton(row, text="Saydam (yalnizca metin)",
                        variable=self.mode_var, value="transparent",
                        command=self._on_style_change).pack(anchor="w", pady=3)
        ttk.Radiobutton(row, text="Koyu kutu (metin arkasinda yari saydam zemin)",
                        variable=self.mode_var, value="box",
                        command=self._on_style_change).pack(anchor="w", pady=3)

        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=(6, 2))
        ttk.Label(row, text="Saydamlik:").pack(side="left")
        self.opacity_var = tk.DoubleVar(value=1.0)
        ttk.Scale(row, from_=0.2, to=1.0, variable=self.opacity_var,
                  orient="horizontal", command=lambda v: self.opacity_var.set(float(v))).pack(
            side="left", fill="x", expand=True, padx=8)

        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=(2, 10))
        ttk.Label(row, text="Satir sayisi:").pack(side="left")
        self.max_lines_var = tk.IntVar(value=int(self.cfg.get("max_lines", 3)))
        ttk.Spinbox(row, from_=1, to=8, textvariable=self.max_lines_var,
                    width=5, command=self._on_style_change).pack(side="left", padx=8)

        theme.ModernButton(c, text="Onizlemeyi Overlay'de Goster",
                           command=self._preview_overlay, kind="accent").pack(
            anchor="w", padx=12, pady=(2, 12))

    # ---------- OCR ----------
    def _build_tab_ocr(self):
        tab = self.tab_ocr
        c = theme.card(tab)
        c.pack(fill="x", padx=14, pady=(14, 8))
        theme.section(c, "OCR AYARLARI").pack(fill="x")

        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=3)
        ttk.Label(row, text="Tarama araligi (ms):").pack(side="left")
        self.interval_var = tk.IntVar(value=int(self.cfg.get("ocr_interval_ms", 400)))
        ttk.Scale(row, from_=100, to=2000, variable=self.interval_var,
                  orient="horizontal", command=lambda v: self.interval_var.set(int(float(v)))).pack(
            side="left", fill="x", expand=True, padx=8)
        ttk.Label(row, textvariable=self.interval_var, width=4).pack(side="left")

        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=3)
        ttk.Label(row, text="Buyutme (scale):").pack(side="left")
        self.scale_var = tk.DoubleVar(value=float(self.cfg.get("ocr_scale", 1.0)))
        ttk.Scale(row, from_=0.5, to=2.5, variable=self.scale_var,
                  orient="horizontal", command=lambda v: self.scale_var.set(round(float(v), 1))).pack(
            side="left", fill="x", expand=True, padx=8)
        ttk.Label(row, textvariable=self.scale_var, width=4).pack(side="left")

        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=3)
        ttk.Label(row, text="Min. guven esigi:").pack(side="left")
        self.conf_var = tk.IntVar(value=int(self.cfg.get("min_confidence", 40)))
        ttk.Scale(row, from_=0, to=90, variable=self.conf_var,
                  orient="horizontal", command=lambda v: self.conf_var.set(int(float(v)))).pack(
            side="left", fill="x", expand=True, padx=8)
        ttk.Label(row, textvariable=self.conf_var, width=3).pack(side="left")

        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=(3, 8))
        ttk.Label(row, text="OCR dilleri:").pack(side="left")
        self.ocr_langs_var = tk.StringVar(value=self.cfg.get("ocr_langs", "eng+tur"))
        ttk.Entry(row, textvariable=self.ocr_langs_var, width=22).pack(side="left", padx=8)
        ttk.Label(row, text="(orn. eng+tur+jpn)", style="CardMuted.TLabel",
                  font=(theme.FONT, 9)).pack(side="left")

        self.stats_card = theme.card(tab)
        self.stats_card.pack(fill="x", padx=14, pady=8)
        theme.section(self.stats_card, "CANLI ISTATISTIK").pack(fill="x")
        grid = tk.Frame(self.stats_card, bg=theme.CARD)
        grid.pack(fill="x", padx=12, pady=(0, 10))
        self.stat_widgets = {}
        stats = [("fps", "FPS"), ("latency", "Gecikme"), ("translated", "Ceviri"),
                 ("hits", "Onbellek isabeti"), ("errors", "Hata"), ("cache_size", "Onbellek boyutu")]
        for i, (key, label) in enumerate(stats):
            cell, body = theme.stat_cell(grid)
            cell.grid(row=i // 3, column=i % 3, sticky="nsew", padx=4, pady=4)
            tk.Label(body, text=label, bg=theme.CARD_2, fg=theme.MUTED,
                     font=(theme.FONT, 9)).pack(anchor="w")
            val = tk.Label(body, text="-", bg=theme.CARD_2, fg=theme.TEXT,
                           font=(theme.FONT_BOLD, 15))
            val.pack(anchor="w")
            self.stat_widgets[key] = val
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

        ttk.Label(tab, text="Not: NVIDIA GPU varsa GPU ile OCR icin winocr yerine tesseract onerilir.",
                  style="Muted.TLabel", font=(theme.FONT, 9)).pack(anchor="w", padx=18, pady=(0, 14))

    # ---------- API ----------
    def _build_tab_api(self):
        tab = self.tab_api
        c = theme.card(tab)
        c.pack(fill="x", padx=14, pady=(14, 8))
        theme.section(c, "DEEPL API").pack(fill="x")
        row = tk.Frame(c, bg=theme.CARD)
        row.pack(fill="x", padx=12, pady=(0, 4))
        self.deepl_var = tk.StringVar(value=self.cfg["api_keys"].get("deepl", ""))
        ttk.Entry(row, textvariable=self.deepl_var, show="*", width=40).pack(side="left", fill="x", expand=True, padx=(0, 6))
        theme.ModernButton(row, text="Test", command=self._test_engine,
                           kind="secondary").pack(side="right")
        ttk.Label(c, text="Anahtar: deepl.com/pro-api", style="CardMuted.TLabel",
                  font=(theme.FONT, 9)).pack(anchor="w", padx=12, pady=(0, 10))

        c = theme.card(tab)
        c.pack(fill="x", padx=14, pady=8)
        theme.section(c, "OPENAI / GEMINI / DEEPSEEK").pack(fill="x")
        g = tk.Frame(c, bg=theme.CARD)
        g.pack(fill="x", padx=12, pady=(0, 10))
        self.openai_var = tk.StringVar(value=self.cfg["api_keys"].get("openai", ""))
        self.base_var = tk.StringVar(value=self.cfg["api_keys"].get("openai_base_url", ""))
        self.model_var = tk.StringVar(value=self.cfg["api_keys"].get("openai_model", "gpt-4o-mini"))
        ttk.Label(g, text="API Anahtari:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(g, textvariable=self.openai_var, show="*", width=46).grid(row=0, column=1, sticky="we", padx=6, pady=2)
        ttk.Label(g, text="Base URL (istege bagli):").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(g, textvariable=self.base_var, width=46).grid(row=1, column=1, sticky="we", padx=6, pady=2)
        ttk.Label(g, text="Model:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(g, textvariable=self.model_var, width=46).grid(row=2, column=1, sticky="we", padx=6, pady=2)
        ttk.Label(g, text="Gemini icin Base URL:\nhttps://generativelanguage.googleapis.com/v1beta/openai/",
                  style="CardMuted.TLabel", font=(theme.FONT, 9)).grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Label(g, text="DeepSeek icin Base URL:\nhttps://api.deepseek.com/v1  |  Model: deepseek-chat",
                  style="CardMuted.TLabel", font=(theme.FONT, 9)).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Label(g, text="Groq icin Base URL:\nhttps://api.groq.com/openai/v1  |  Model: llama-3.3-70b-versatile",
                  style="CardMuted.TLabel", font=(theme.FONT, 9)).grid(row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))
        theme.ModernButton(g, text="Test Et", command=self._test_openai,
                           kind="secondary").grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))
        g.columnconfigure(1, weight=1)

        c = theme.card(tab)
        c.pack(fill="x", padx=14, pady=8)
        theme.section(c, "GIZLILIK").pack(fill="x")
        ttk.Label(c, text=(
            "API anahtarlariniz yalnizca cihazinizda saklanir. "
            "Cevirilecek metinler yalnizca seÃ§tiginiz motorun sunucusuna gonderilir. "
            "Ekran goruntuleri ve ceviri gecmisi cihazinizda kalir; sunucuya yuklenmez."
        ), style="CardMuted.TLabel", wraplength=580, justify="left").pack(
            anchor="w", padx=12, pady=(0, 12))

    # ---------- Gunluk ----------
    def _build_tab_log(self):
        tab = self.tab_log
        row = tk.Frame(tab, bg=theme.BG)
        row.pack(fill="x", padx=14, pady=(14, 6))
        ttk.Label(row, text="ISLEM GUNLUGU", style="Muted.TLabel",
                  font=(theme.FONT_BOLD, 10)).pack(side="left")
        theme.ModernButton(row, text="Temizle", command=self._clear_log,
                           kind="secondary").pack(side="right")
        self.log_text = tk.Text(tab, wrap="word", bg=theme.CARD_2, fg=theme.TEXT,
                                insertbackground=theme.TEXT, relief="flat",
                                highlightthickness=1, highlightbackground=theme.BORDER,
                                font=("Consolas", 9), padx=10, pady=8)
        self.log_text.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.log_text.configure(state="disabled")
        for item in self._log_buffer:
            self._append_log(item[0], item[1])

    # ---------- Durum cubugu ----------
    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=theme.CARD, height=34)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.sb_state = tk.Label(bar, text="â—", bg=theme.CARD, fg=theme.MUTED,
                                 font=(theme.FONT, 12))
        self.sb_state.pack(side="left", padx=(14, 4))
        self.sb_text = tk.Label(bar, text="Durduruldu", bg=theme.CARD, fg=theme.MUTED,
                                font=(theme.FONT, 9))
        self.sb_text.pack(side="left")
        version_txt = f"v{VERSION}{' beta' if BETA else ''}"
        self.sb_version = tk.Label(bar, text=version_txt, bg=theme.CARD,
                                   fg=theme.MUTED, font=(theme.FONT, 8))
        self.sb_version.pack(side="left", padx=(10, 0))
        self.sb_stats = tk.Label(bar, text="", bg=theme.CARD, fg=theme.MUTED,
                                 font=(theme.FONT, 9))
        self.sb_stats.pack(side="right", padx=14)

    def _show_about(self):
        win = tk.Toplevel(self.root)
        win.title("Hakkinda")
        win.configure(bg=theme.BG)
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        card = theme.card(win, bg=theme.CARD)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(card, text=APP_TITLE, bg=theme.CARD, fg=theme.TEXT,
                 font=(theme.FONT_BOLD, 18)).pack(anchor="w", padx=16, pady=(16, 0))
        version_txt = f"SÃ¼rÃ¼m {VERSION}" + (" (BETA)" if BETA else "")
        tk.Label(card, text=version_txt, bg=theme.CARD, fg=theme.ACCENT,
                 font=(theme.FONT_BOLD, 10)).pack(anchor="w", padx=16)
        tk.Label(card, text="Gercek zamanli AI oyun ceviri programi",
                 bg=theme.CARD, fg=theme.MUTED,
                 font=(theme.FONT, 9)).pack(anchor="w", padx=16, pady=(4, 10))

        info = tk.Frame(card, bg=theme.CARD)
        info.pack(fill="x", padx=16)
        rows = [
            ("Gelistiren:", f"{COMPANY} sirketi"),
            ("Tasarim:", DESIGNER),
            ("Durum:", "Beta surum"),
        ]
        for label, value in rows:
            line = tk.Frame(info, bg=theme.CARD)
            line.pack(fill="x", pady=2)
            tk.Label(line, text=label, bg=theme.CARD, fg=theme.MUTED,
                     font=(theme.FONT, 9), width=12, anchor="w").pack(side="left")
            tk.Label(line, text=value, bg=theme.CARD, fg=theme.TEXT,
                     font=(theme.FONT_BOLD, 9), anchor="w").pack(side="left")

        tk.Frame(card, bg=theme.CARD_2, height=1).pack(fill="x", padx=16, pady=14)
        tk.Label(card, text=COPYRIGHT, bg=theme.CARD, fg=theme.MUTED,
                 font=(theme.FONT, 8)).pack(anchor="w", padx=16)
        tk.Label(card, text="Yalnizca ekrani okur; oyun dosyalarina dokunmaz.",
                 bg=theme.CARD, fg=theme.MUTED,
                 font=(theme.FONT, 8)).pack(anchor="w", padx=16, pady=(2, 16))

        theme.ModernButton(win, text="Kapat", command=win.destroy,
                           kind="accent", font=(theme.FONT, 10)).pack(pady=(0, 20))

    # ---------- API anahtari hatirlatmasi (ilk acilis) ----------
    def _maybe_prompt_api_key(self):
        """Anahtar tanimli degilse acilista 'API Anahtari Ekle' penceresini acar."""
        keys = self.cfg.get("api_keys", {})
        if keys.get("deepl") or keys.get("openai"):
            return
        if self.cfg.get("api_key_prompt_done"):
            return
        self._prompt_api_key_window()

    def _prompt_api_key_window(self):
        win = tk.Toplevel(self.root)
        win.title("API Anahtari Ekle")
        win.configure(bg=theme.BG)
        win.resizable(False, False)
        win.transient(self.root)

        card = theme.card(win, bg=theme.CARD)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(card, text="API Anahtari Ekle", bg=theme.CARD, fg=theme.TEXT,
                 font=(theme.FONT_BOLD, 16)).pack(anchor="w", padx=16, pady=(16, 2))
        tk.Label(card, text=(
            "Google ve MyMemory motorlari anahtarsiz, ucretsiz calisir. "
            "DeepL / OpenAI (ChatGPT, Gemini, DeepSeek) motorlari icin API "
            "anahtari gerekir. Anahtariniz yalnizca bu cihazda, sifreli "
            "olarak saklanir; GitHub'a ya da hicbir sunucuya gonderilmez."
        ), bg=theme.CARD, fg=theme.MUTED, wraplength=540, justify="left",
            font=(theme.FONT, 9)).pack(anchor="w", padx=16, pady=(0, 12))

        g = tk.Frame(card, bg=theme.CARD)
        g.pack(fill="x", padx=16)
        ttk.Label(g, text="DeepL Anahtari:").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(g, textvariable=self.deepl_var, show="*", width=44).grid(
            row=0, column=1, sticky="we", padx=8, pady=3)
        ttk.Label(g, text="OpenAI/Gemini/DeepSeek Anahtari:").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(g, textvariable=self.openai_var, show="*", width=44).grid(
            row=1, column=1, sticky="we", padx=8, pady=3)
        ttk.Label(g, text="Base URL (istege bagli):").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(g, textvariable=self.base_var, width=44).grid(
            row=2, column=1, sticky="we", padx=8, pady=3)
        ttk.Label(g, text="Model (istege bagli):").grid(row=3, column=0, sticky="w", pady=3)
        ttk.Entry(g, textvariable=self.model_var, width=44).grid(
            row=3, column=1, sticky="we", padx=8, pady=3)
        g.columnconfigure(1, weight=1)

        tk.Frame(card, bg=theme.BORDER, height=1).pack(fill="x", padx=16, pady=12)
        tk.Label(card, text="Anahtar nasil alinir?", bg=theme.CARD, fg=theme.ACCENT,
                 font=(theme.FONT_BOLD, 11)).pack(anchor="w", padx=16, pady=(0, 4))
        steps = (
            "1. DeepL: deepl.com/pro-api adresinden ucretsiz kayit olun. 'DeepL API Free' "
            "planinda olusan 'Authentication Key'i kopyalayip yukaridaki DeepL alanina yapistirin.",
            "2. OpenAI: platform.openai.com/api-keys adresinde 'Create new secret key' "
            "butonuyla anahtar olusturup OpenAI alanina yapistirin.",
            "3. Gemini: aistudio.google.com adresinden anahtar alin. Base URL kutusuna "
            "https://generativelanguage.googleapis.com/v1beta/openai/ yazin.",
            "4. DeepSeek: platform.deepseek.com adresinden anahtar alin. Base URL kutusuna "
            "https://api.deepseek.com/v1, Model kutusuna deepseek-chat yazin.",
            "5. Anahtar girdikten sonra 'Kaydet ve Kapat' butonuna basin. Anahtar eklemeden "
            "de Google/MyMemory motorlariyla ceviriye baslayabilirsiniz.",
        )
        for s in steps:
            tk.Label(card, text=s, bg=theme.CARD, fg=theme.MUTED, wraplength=540,
                     justify="left", font=(theme.FONT, 9)).pack(anchor="w", padx=16, pady=1)

        self.prompt_done_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text="Bir daha sorma (yalnizca ucretsiz motorlari kullaniyorsaniz)",
                        variable=self.prompt_done_var).pack(anchor="w", padx=16, pady=(10, 4))

        def close(save):
            if save:
                self._sync_cfg()
                self._log("API anahtari kaydedildi.", "ok")
            if self.prompt_done_var.get():
                self.cfg["api_key_prompt_done"] = True
                config_mod.save_config(self.cfg)
            win.destroy()

        row = tk.Frame(card, bg=theme.CARD)
        row.pack(fill="x", padx=16, pady=(6, 14))
        theme.ModernButton(row, text="Kaydet ve Kapat", command=lambda: close(True),
                           kind="accent").pack(side="right", padx=(8, 0))
        theme.ModernButton(row, text="Sonra", command=lambda: close(False),
                           kind="ghost").pack(side="right")
        win.protocol("WM_DELETE_WINDOW", lambda: close(False))

        win.grab_set()
        win.focus_force()

    # ================= Olaylar =================
    def _refresh_region_text(self):
        r = self.cfg["region"]
        self.region_var.set(
            f"Bolge: X={r['left']}  Y={r['top']}  {r['width']}x{r['height']}  â€”  altyazilarin oldugu alani surukleyerek secin")

    def _refresh_engine_desc(self):
        eng = self.engine_var.get()
        self.engine_desc.configure(text=ENGINE_DESC.get(eng, ""))

    def _select_region(self):
        region = select_region(self.root, self.cfg.get("monitor", 0))
        if region:
            self.cfg["region"] = region
            self._refresh_region_text()
            self.overlay.update_position(region)
            self._log(f"Bolge secildi: {region['width']}x{region['height']} @ ({region['left']},{region['top']})", "ok")
        return region

    def _preview_region(self):
        self._sync_cfg()
        try:
            img = grab_region(self.cfg["region"], self.cfg.get("monitor", 0))
            img.show()
            self._log("Bolge onizlemesi ayri pencerede acildi.", "info")
        except Exception as exc:
            self._log(f"Onizleme hatasi: {exc}", "error")

    def _preview_overlay(self):
        self._apply_overlay_style()
        sample = ["Bu bir ornek altyazi satiridir.",
                  "Altyazi katmaninin gorunumunu burada test edebilirsin."]
        self.overlay.show(sample, opacity=float(self.opacity_var.get()))
        self._log("Overlay onizlemesi gosterildi (F11 ile kapat).", "info")

    def _swap_langs(self):
        a = self.source_var.get()
        self.source_var.set(self.target_var.get())
        self.target_var.set(a if a != "otomatik" else "tr")

    def _set_color(self, color):
        self.color_var.set(color)
        self._apply_overlay_style()

    def _pick_color(self):
        color = colorchooser.askcolor(color=self.color_var.get(),
                                      title="Yazi rengi sec")[1]
        if color:
            self.color_var.set(color)
            self._apply_overlay_style()

    def _on_size_change(self, value):
        self.font_size_var.set(int(float(value)))
        self._apply_overlay_style()

    def _on_style_change(self):
        self._apply_overlay_style()

    def _apply_overlay_style(self, init=False):
        self.overlay.set_style(
            self.font_family_var.get() if not init else self.cfg.get("font_family", "Segoe UI"),
            self.font_size_var.get() if not init else int(self.cfg.get("font_size", 20)),
            self.color_var.get() if not init else self.cfg.get("text_color", "#FFFFFF"),
            self.cfg.get("text_bg", "#000000"),
            self.mode_var.get() if not init else self.cfg.get("overlay_mode", "transparent"),
            self.max_lines_var.get() if not init else int(self.cfg.get("max_lines", 3)),
        )

    # ================= Profil ve oyun =================
    def _current_game(self):
        return self.game_var.get().strip()

    def _on_game_changed(self):
        game = self._current_game()
        if not game:
            return
        self._save_profile(self.cfg.get("last_game_name", ""))
        self._load_profile(game)
        self.cfg["last_game_name"] = game
        self._log(f"Profil yuklendi: {game}", "info")

    def _load_profile(self, game):
        prof = config_mod.get_profile(self.base_cfg, game)
        if not prof:
            return
        for key in config_mod.PROFILE_KEYS:
            if key in prof:
                self.cfg[key] = dict(prof[key]) if isinstance(prof[key], dict) else prof[key]
        for var_name, cfg_key in [
            ("source_var", "source_lang"), ("target_var", "target_lang"),
            ("engine_var", "engine"), ("ocr_langs_var", "ocr_langs"),
            ("font_size_var", "font_size"), ("color_var", "text_color"),
            ("mode_var", "overlay_mode"), ("interval_var", "ocr_interval_ms"),
            ("scale_var", "ocr_scale"), ("conf_var", "min_confidence"),
            ("max_lines_var", "max_lines"),
        ]:
            if cfg_key in prof:
                getattr(self, var_name).set(prof[cfg_key])
        self._refresh_region_text()
        self._refresh_engine_desc()
        self.overlay.update_position(self.cfg["region"])
        self._apply_overlay_style()

    def _save_profile(self, game):
        game = game or self._current_game()
        if not game:
            return
        self._sync_cfg()
        overrides = {k: self.cfg[k] for k in config_mod.PROFILE_KEYS if k in self.cfg}
        config_mod.set_profile(self.base_cfg, game, overrides)
        config_mod.save_config(self.base_cfg)

    def _auto_detect_game(self):
        title, exe = self._foreground_process()
        name = exe or title
        if not name:
            self._log("On plandaki pencere algilanamadi.", "warn")
            return
        self.game_var.set(name)
        self._on_game_changed()
        extra = f" ({title})" if title and title.lower() != name.lower() else ""
        self._log(f"Oyun algilandi: {name}{extra}", "ok")

    def _auto_detect_initial(self):
        if not self.cfg.get("auto_detect_game", True):
            return
        if self.cfg.get("last_game_name"):
            self._load_profile(self.cfg["last_game_name"])
            return
        self._auto_detect_game()

    def _foreground_process(self):
        """On plandaki pencerenin (baslik, exe adi) bilgisini dondurur.

        Profiller, degisen pencere basliklari yerine process exe adina
        gore eslesir (orn. 'eldenring.exe').
        """
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return "", ""
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.strip()
            exe = ""
            pid = ctypes.c_ulong()
            if ctypes.windll.user32.GetWindowThreadProcessId(
                    hwnd, ctypes.byref(pid)):
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                handle = ctypes.windll.kernel32.OpenProcess(
                    PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
                if handle:
                    try:
                        size = ctypes.c_ulong(1024)
                        pbuf = ctypes.create_unicode_buffer(1024)
                        if ctypes.windll.kernel32.QueryFullProcessImageNameW(
                                handle, 0, pbuf, ctypes.byref(size)):
                            exe = os.path.basename(pbuf.value)
                    finally:
                        ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:  # noqa: BLE001
            return "", ""
        low = title.lower()
        if any(g in low for g in GAME_FILTER) or len(title) < 2:
            title = ""
        if not exe:
            exe = ""
        return title, exe.lower()

    # ================= Motor dongusu =================
    def _sync_cfg(self):
        self.cfg["source_lang"] = self.source_var.get()
        self.cfg["target_lang"] = self.target_var.get()
        self.cfg["engine"] = self.engine_var.get()
        self.cfg["last_game_name"] = self._current_game()
        self.cfg["ocr_interval_ms"] = int(self.interval_var.get())
        self.cfg["ocr_scale"] = float(self.scale_var.get())
        self.cfg["min_confidence"] = int(self.conf_var.get())
        self.cfg["ocr_langs"] = self.ocr_langs_var.get().strip() or "eng+tur"
        self.cfg["font_size"] = int(self.font_size_var.get())
        self.cfg["font_family"] = self.font_family_var.get()
        self.cfg["text_color"] = self.color_var.get()
        self.cfg["overlay_mode"] = self.mode_var.get()
        self.cfg["max_lines"] = int(self.max_lines_var.get())
        self.cfg["api_keys"]["deepl"] = self.deepl_var.get()
        self.cfg["api_keys"]["openai"] = self.openai_var.get()
        self.cfg["api_keys"]["openai_base_url"] = self.base_var.get()
        self.cfg["api_keys"]["openai_model"] = self.model_var.get()

    def _toggle(self):
        if self.pipeline and self.pipeline.running:
            self._stop_pipeline()
        else:
            try:
                self._start_pipeline()
            except Exception as exc:  # noqa: BLE001
                self._set_status(f"HATA: {exc}", error=True)
                self._log(f"Baslatma hatasi: {exc}", "error")

    def _start_pipeline(self):
        self._sync_cfg()
        self._save_profile(self.cfg.get("last_game_name", ""))
        self._apply_overlay_style()
        if self.pipeline:
            self.pipeline.stop()
        self._pipeline_error_reported = False
        self.cfg["last_game_name"] = self._current_game()
        self.pipeline = TranslationPipeline(self.cfg,
                                            on_status=self._set_status,
                                            on_log=self._log)
        self.pipeline.start()
        self.toggle_btn.configure(text="Ceviriyi Durdur  (F9)")
        self.toggle_btn.set_kind("danger")
        self._set_running(True)
        mode = getattr(self.pipeline.ocr, "mode", "unknown")
        self._log(f"Pipeline basladi. Motor: {self.cfg['engine']} | OCR: {mode}", "ok")

    def _stop_pipeline(self):
        if self.pipeline:
            self.pipeline.stop()
        self._pipeline_error_reported = False
        self.toggle_btn.configure(text="Ceviriyi Baslat  (F9)")
        self.toggle_btn.set_kind("accent")
        self._set_running(False)

    def _set_running(self, running):
        if running:
            self.sb_state.configure(fg=theme.GREEN)
            self.sb_text.configure(text="Calisiyor", fg=theme.GREEN)
            self.header_state.configure(text="CALISIYOR", fg=theme.GREEN)
        else:
            self.sb_state.configure(fg=theme.MUTED)
            self.sb_text.configure(text="Durduruldu", fg=theme.MUTED)
            self.header_state.configure(text="DURDURULDU", fg=theme.MUTED)

    def _set_status(self, text, error=False):
        if threading.current_thread() is not self._ui_thread:
            self._ui_tasks.put((self._set_status, (text, error)))
            return
        self.status_var.set(text)
        if "OKUNAN" in text:
            self._log(text, "info")

    # ---------- Manuel ekran cevirisi (F10) ----------
    def _manual_translate(self):
        region = select_region(self.root, self.cfg.get("monitor", 0))
        if not region:
            return
        self._log(f"Manuel bolge: {region['width']}x{region['height']}", "info")
        self.overlay.update_position(region)
        self.cfg["region"] = region
        self._refresh_region_text()
        self._sync_cfg()
        # UI thread'deki degiskenleri worker'a kopyala; thread icinde
        # Tkinter degiskenleri okunmaz.
        snapshot = dict(self.cfg)
        snapshot["region"] = dict(region)
        monitor = snapshot.get("monitor", 0)
        source, target = snapshot["source_lang"], snapshot["target_lang"]

        def work():
            try:
                img = grab_region(region, monitor)
                raw = self.pipeline.ocr.read(img) if (self.pipeline and self.pipeline.running) else None
                if raw is None:
                    from .ocr import OcrEngine
                    raw = OcrEngine(snapshot).read(img)
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                if not lines:
                    self.root.after(0, lambda: self._set_status("Bolgede metin bulunamadi."))
                    return
                cache_file = os.path.join(config_mod.cache_dir(), "_manual.json")
                tr = Translator(snapshot, cache_file)
                out = tr.translate_lines(lines, source=source, target=target)
                self.root.after(0, lambda: self._show_manual(out, raw))
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                self.root.after(0, lambda: self._log(f"Manuel ceviri hatasi: {msg}", "error"))

        threading.Thread(target=work, daemon=True).start()

    def _show_manual(self, lines, raw):
        self._set_output("\n".join(lines))
        self.overlay.show(lines, opacity=float(self.opacity_var.get()))
        self._set_status(f"Manuel ceviri: {len(lines)} satir")

    # ---------- Testler ----------
    def _test_engine(self):
        eng = self.engine_var.get()
        self._sync_cfg()
        snapshot = dict(self.cfg)
        cache_file = os.path.join(config_mod.cache_dir(), "_test.json")

        def work():
            try:
                tr = Translator(snapshot, cache_file)
                out = tr.translate("Welcome to the village, hero!", "en", "tr", engine=eng)
                self.root.after(0, lambda: self._set_output(f"Motor testi basarili:\n{out}"))
                self.root.after(0, lambda: self._log(f"{eng} motoru testi: OK", "ok"))
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                self.root.after(0, lambda: self._log(f"{eng} testi basarisiz: {msg}", "error"))

        threading.Thread(target=work, daemon=True).start()

    def _test_openai(self):
        self._sync_cfg()
        snapshot = dict(self.cfg)
        cache_file = os.path.join(config_mod.cache_dir(), "_test.json")

        def work():
            try:
                tr = Translator(snapshot, cache_file)
                out = tr.translate("Hello there!", "en", "tr", engine="openai")
                self.root.after(0, lambda: self._set_output(f"OpenAI uyumlu API testi:\n{out}"))
                self.root.after(0, lambda: self._log(
                    f"OpenAI uyumlu test: OK ({snapshot['api_keys'].get('openai_model')})", "ok"))
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                self.root.after(0, lambda: self._log(f"OpenAI testi basarisiz: {msg}", "error"))

        threading.Thread(target=work, daemon=True).start()

    def _set_output(self, text):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.configure(state="disabled")

    # ---------- Gunluk ----------
    def _log(self, text, kind="info"):
        if threading.current_thread() is not self._ui_thread:
            self._ui_tasks.put((self._log, (text, kind)))
            return
        stamp = time.strftime("%H:%M:%S")
        self._log_buffer.append((f"[{stamp}] {text}", kind))
        if len(self._log_buffer) > 500:
            self._log_buffer = self._log_buffer[-500:]
        if hasattr(self, "log_text"):
            self._append_log(f"[{stamp}] {text}", kind)

    def _append_log(self, text, kind):
        try:
            self.log_text.configure(state="normal")
            self.log_text.insert("end", text + "\n",
                                 (kind,))
            self.log_text.tag_config(kind, foreground=theme.STATUS_COLORS.get(kind, theme.TEXT))
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        except tk.TclError:
            pass

    def _clear_log(self):
        if hasattr(self, "log_text"):
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.configure(state="disabled")
        self._log_buffer = []

    # ---------- Donemsel ----------
    def _poll_queue(self):
        try:
            while True:
                fn, args = self._ui_tasks.get_nowait()
                fn(*args)
        except queue.Empty:
            pass
        if self.pipeline:
            try:
                while True:
                    msg = self.pipeline.queue.get_nowait()
                    if msg.get("clear"):
                        self._set_output("")
                        self.overlay.hide()
                        self._set_status("Altyazi beklemede...")
                        continue
                    lines = msg.get("lines", [])
                    self._set_output("\n".join(lines))
                    self.overlay.show(lines, opacity=float(self.opacity_var.get()))
                    lat = msg.get("latency_ms", 0)
                    if msg.get("fresh"):
                        self._set_status(f"{lat} ms | {msg.get('raw', '')[:60]}")
            except queue.Empty:
                pass
            if self.pipeline.state == "failed" and not self._pipeline_error_reported:
                self._pipeline_error_reported = True
                self._stop_pipeline()
                self._log(f"Pipeline durdu: {self.pipeline.error}", "error")
                self._set_status(f"HATA: {self.pipeline.error}", error=True)
            elif self.pipeline.state == "running":
                self._pipeline_error_reported = False
            st = self.pipeline.stats
            self.sb_stats.configure(
                text=f"FPS {st['fps']:.1f} | Gecikme {st['latency_ms']} ms | "
                     f"Ceviri {st['translated']} | Cache {st['cache_size']} | "
                     f"Atla {st['skipped']}")
            if hasattr(self, "stat_widgets"):
                self.stat_widgets["fps"].configure(text=f"{st['fps']:.1f}")
                self.stat_widgets["latency"].configure(text=f"{st['latency_ms']} ms")
                self.stat_widgets["translated"].configure(text=f"{st['translated']}")
                self.stat_widgets["hits"].configure(text=f"{st['hits']}")
                self.stat_widgets["errors"].configure(text=f"{st['errors']}")
                self.stat_widgets["cache_size"].configure(text=f"{st['cache_size']}")
        self.root.after(80, self._poll_queue)

    def _bind_hotkeys(self):
        try:
            import keyboard
            keyboard.add_hotkey(HOTKEYS["toggle"], lambda: self.root.after(0, self._toggle))
            keyboard.add_hotkey(HOTKEYS["manual"], lambda: self.root.after(0, self._manual_translate))
            keyboard.add_hotkey(HOTKEYS["overlay"], lambda: self.root.after(0, self._toggle_overlay))
        except Exception:  # noqa: BLE001
            self._log("Global kisayollar devre disi (admin yetkisi gerekli). Butonlari kullanin.", "warn")

    def _toggle_overlay(self):
        self._overlay_visible = not self._overlay_visible
        self.overlay.set_visible(self._overlay_visible)
        self._log("Altyazi katmani " + ("gosterildi" if self._overlay_visible else "gizlendi"), "info")

    def on_close(self):
        try:
            self._save_profile(self.cfg.get("last_game_name", ""))
        except Exception:  # noqa: BLE001
            pass
        if self.pipeline:
            self.pipeline.stop()
        self.cfg["window_size"] = self.root.winfo_geometry().split("+")[0]
        self.cfg["window_pos"] = f"{self.root.winfo_x()}+{self.root.winfo_y()}"
        config_mod.save_config(self.cfg)
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:  # noqa: BLE001
            pass
        self.overlay.close()
        self.root.destroy()

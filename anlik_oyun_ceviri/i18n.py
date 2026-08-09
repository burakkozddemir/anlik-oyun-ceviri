"""Çoklu dil desteği (i18n).

Varsayılan dil Türkçe'dir; 'language' ayarı 'en' olduğunda görünür
metinler İngilizce'ye çevrilir. Çeviriler Türkçe metni anahtar olarak
kullanır; çeviri kaydı yoksa metin olduğu gibi gösterilir.

Kullanım:  i18n.format("Oyun algılandı: {name}", lang, name=name)
"""

LANGUAGES = [
    ("tr", "Türkçe"),
    ("en", "English"),
]

LANG_CODES = [code for code, _ in LANGUAGES]

_EN = {
    # --- Başlık / durum ---
    "DURDURULDU": "STOPPED",
    "CALISIYOR": "RUNNING",
    "Hakkında": "About",
    "Gerçek zamanlı AI oyun çevirmeni": "Real-time AI game translator",
    "by ": "by ",

    # --- Sekmeler ---
    "  Çeviri  ": "  Translate  ",
    "  Görünüm  ": "  Appearance  ",
    "  OCR / Performans  ": "  OCR / Performance  ",
    "  API Ayarları  ": "  API Settings  ",
    "  Günlük  ": "  Log  ",

    # --- Bölüm başlıkları ---
    "OYUN": "GAME",
    "DİLLER": "LANGUAGES",
    "ÇEVİRİ MOTORU": "TRANSLATION ENGINE",
    "SON ÇEVİRİ": "LAST TRANSLATION",
    "YAZI": "TEXT",
    "ALTYAZI KATMANI": "SUBTITLE OVERLAY",
    "OCR AYARLARI": "OCR SETTINGS",
    "CANLI İSTATİSTİK": "LIVE STATS",
    "DEEPL API": "DEEPL API",
    "OPENAI / GEMINI / DEEPSEEK": "OPENAI / GEMINI / DEEPSEEK",
    "GİZLİLİK": "PRIVACY",
    "İŞLEM GÜNLÜĞÜ": "ACTIVITY LOG",
    "DİL / LANGUAGE": "LANGUAGE",

    # --- Çeviri sekmesi ---
    "Oyunu Otomatik Al": "Detect Game",
    "Bölge Seç": "Select Region",
    "Önizle": "Preview",
    "Manuel Ekran Çevirisi (F10)": "Manual Screen Translate (F10)",
    "Kaynak (oyun) dili": "Source (game) language",
    "Hedef dil (çeviri)": "Target language (translation)",
    "Çeviriyi Başlat  (F9)": "Start Translation  (F9)",
    "Çeviriyi Durdur  (F9)": "Stop Translation  (F9)",
    "Hazır.": "Ready.",
    "Bölge: X={left}  Y={top}  {w}x{h}  —  altyazıların olduğu alanı sürükleyerek seçin":
        "Region: X={left}  Y={top}  {w}x{h}  —  drag over the subtitle area",

    # --- Görünüm sekmesi ---
    "Yazı tipi:": "Font:",
    "Boyut:": "Size:",
    "Renk:": "Color:",
    "Özel renk...": "Custom color...",
    "Saydam (yalnızca metin)": "Transparent (text only)",
    "Koyu kutu (metin arkasında yarı saydam zemin)":
        "Dark box (semi-transparent background behind text)",
    "Saydamlık:": "Opacity:",
    "Satır sayısı:": "Max lines:",
    "Önizlemeyi Overlay'de Göster": "Show Preview on Overlay",
    "Bu bir örnek altyazı satırıdır.": "This is a sample subtitle line.",
    "Altyazı katmanının görünümünü burada test edebilirsin.":
        "You can test the overlay appearance here.",

    # --- OCR sekmesi ---
    "Tarama aralığı (ms):": "Scan interval (ms):",
    "Büyütme (scale):": "Scale:",
    "Min. güven eşiği:": "Min. confidence:",
    "OCR dilleri:": "OCR languages:",
    "(örn. eng+tur+jpn)": "(e.g. eng+tur+jpn)",
    "Gecikme": "Latency",
    "Çeviri": "Translation",
    "Önbellek isabeti": "Cache hits",
    "Hata": "Errors",
    "Önbellek boyutu": "Cache size",
    "Atla": "Skipped",
    "Not: NVIDIA GPU varsa GPU ile OCR için winocr yerine tesseract önerilir.":
        "Note: if you have an NVIDIA GPU, Tesseract is recommended over winocr for GPU OCR.",

    # --- API sekmesi ---
    "Test": "Test",
    "Test Et": "Test",
    "API Anahtarı:": "API Key:",
    "Base URL (isteğe bağlı):": "Base URL (optional):",
    "Model:": "Model:",
    "Anahtar: deepl.com/pro-api": "Key: deepl.com/pro-api",
    "Gemini için Base URL:\nhttps://generativelanguage.googleapis.com/v1beta/openai/":
        "Gemini Base URL:\nhttps://generativelanguage.googleapis.com/v1beta/openai/",
    "DeepSeek için Base URL:\nhttps://api.deepseek.com/v1  |  Model: deepseek-chat":
        "DeepSeek Base URL:\nhttps://api.deepseek.com/v1  |  Model: deepseek-chat",
    "Groq için Base URL:\nhttps://api.groq.com/openai/v1  |  Model: llama-3.3-70b-versatile":
        "Groq Base URL:\nhttps://api.groq.com/openai/v1  |  Model: llama-3.3-70b-versatile",
    ("API anahtarlarınız yalnızca cihazınızda saklanır. "
     "Çevrilecek metinler yalnızca seçtiğiniz motorun sunucusuna gönderilir. "
     "Ekran görüntüleri ve çeviri geçmişi cihazınızda kalır; sunucuya yüklenmez."):
        ("Your API keys are stored only on this device. "
         "Text to translate is sent only to the selected engine's server. "
         "Screenshots and translation history stay on your device; nothing is uploaded."),

    # --- Günlük sekmesi ---
    "Temizle": "Clear",

    # --- Durum çubuğu ---
    "Durduruldu": "Stopped",
    "Çalışıyor": "Running",
    "FPS {fps:.1f} | Gecikme {lat} ms | Çeviri {tr} | Cache {c} | Atla {sk}":
        "FPS {fps:.1f} | Latency {lat} ms | Translated {tr} | Cache {c} | Skipped {sk}",

    # --- Hakkında ---
    "Sürüm {v}": "Version {v}",
    "Gerçek zamanlı AI oyun çeviri programı": "Real-time AI game translator",
    "Geliştiren:": "Developed by:",
    "şirketi": "company",
    "Tasarım:": "Design:",
    "Durum:": "Status:",
    "Beta sürüm": "Beta release",
    "Yalnızca ekranı okur; oyun dosyalarına dokunmaz.":
        "Only reads the screen; never touches game files.",
    "Kapat": "Close",

    # --- API anahtarı penceresi ---
    "API Anahtarı Ekle": "Add API Key",
    ("Google ve MyMemory motorları anahtarsız, ücretsiz çalışır. "
     "DeepL / OpenAI (ChatGPT, Gemini, DeepSeek) motorları için API "
     "anahtarı gerekir. Anahtarınız yalnızca bu cihazda, şifreli "
     "olarak saklanır; GitHub'a ya da hiçbir sunucuya gönderilmez."):
        ("Google and MyMemory engines work for free without a key. "
         "DeepL / OpenAI (ChatGPT, Gemini, DeepSeek) engines require an API key. "
         "Your key is stored encrypted, only on this device; it is never sent "
         "to GitHub or any other server."),
    "DeepL Anahtarı:": "DeepL Key:",
    "OpenAI/Gemini/DeepSeek Anahtarı:": "OpenAI/Gemini/DeepSeek Key:",
    "Model (isteğe bağlı):": "Model (optional):",
    "Anahtar nasıl alınır?": "How to get a key?",
    "1. DeepL: deepl.com/pro-api adresinden ücretsiz kayıt olun. 'DeepL API Free' planında oluşan 'Authentication Key'i kopyalayıp yukarıdaki DeepL alanına yapıştırın.":
        "1. DeepL: sign up for free at deepl.com/pro-api. Copy the 'Authentication Key' from your 'DeepL API Free' plan and paste it into the DeepL field above.",
    "2. OpenAI: platform.openai.com/api-keys adresinde 'Create new secret key' butonuyla anahtar oluşturup OpenAI alanına yapıştırın.":
        "2. OpenAI: create a key at platform.openai.com/api-keys using 'Create new secret key' and paste it into the OpenAI field.",
    "3. Gemini: aistudio.google.com adresinden anahtar alın. Base URL kutusuna https://generativelanguage.googleapis.com/v1beta/openai/ yazın.":
        "3. Gemini: get a key at aistudio.google.com and set the Base URL to https://generativelanguage.googleapis.com/v1beta/openai/.",
    "4. DeepSeek: platform.deepseek.com adresinden anahtar alın. Base URL kutusuna https://api.deepseek.com/v1, Model kutusuna deepseek-chat yazın.":
        "4. DeepSeek: get a key at platform.deepseek.com. Set Base URL to https://api.deepseek.com/v1 and Model to deepseek-chat.",
    "5. Anahtar girdikten sonra 'Kaydet ve Kapat' butonuna basın. Anahtar eklemeden de Google/MyMemory motorlarıyla çeviriye başlayabilirsiniz.":
        "5. After entering your key, press 'Save & Close'. You can also start translating without a key using the free Google/MyMemory engines.",
    "Bir daha sorma (yalnızca ücretsiz motorları kullanıyorsanız)":
        "Don't ask again (if you only use the free engines)",
    "Kaydet ve Kapat": "Save & Close",
    "Sonra": "Later",
    "API anahtarı kaydedildi.": "API key saved.",

    # --- Durum / günlük mesajları ---
    "Program hazır. F9 = başlat/durdur, F10 = ekran çevirisi, F11 = altyazı göster/gizle":
        "Ready. F9 = start/stop, F10 = translate screen, F11 = show/hide subtitles",
    "OKUNAN: {raw}": "READING: {raw}",
    "HATA: {exc}": "ERROR: {exc}",
    "Altyazı bekleniyor...": "Waiting for subtitles...",
    "Bölge seçildi: {w}x{h} @ ({x},{y})": "Region selected: {w}x{h} @ ({x},{y})",
    "Bölge önizlemesi ayrı pencerede açıldı.": "Region preview opened in a separate window.",
    "Önizleme hatası: {exc}": "Preview error: {exc}",
    "Overlay önizlemesi gösterildi (F11 ile kapat).":
        "Overlay preview shown (close with F11).",
    "Profil yüklendi: {game}": "Profile loaded: {game}",
    "Ön plandaki pencere algılanamadı.": "Could not detect the foreground window.",
    "Oyun algılandı: {name}": "Game detected: {name}",
    "Manuel bölge: {w}x{h}": "Manual region: {w}x{h}",
    "Bölgede metin bulunamadı.": "No text found in the region.",
    "Manuel çeviri: {n} satır": "Manual translation: {n} lines",
    "Motor testi başarılı:\n{out}": "Engine test successful:\n{out}",
    "{eng} motoru testi: OK": "{eng} engine test: OK",
    "{eng} testi başarısız: {msg}": "{eng} test failed: {msg}",
    "OpenAI uyumlu API testi:\n{out}": "OpenAI-compatible API test:\n{out}",
    "OpenAI uyumlu test: OK ({model})": "OpenAI-compatible test: OK ({model})",
    "OpenAI testi başarısız: {msg}": "OpenAI test failed: {msg}",
    "Manuel çeviri hatası: {msg}": "Manual translation error: {msg}",
    "Başlatma hatası: {exc}": "Startup error: {exc}",
    "Global kısayollar devre dışı (yönetici yetkisi gerekli). Butonları kullanın.":
        "Global hotkeys disabled (administrator rights required). Use the buttons.",
    "Altyazı katmanı gösterildi": "Subtitle overlay shown",
    "Altyazı katmanı gizlendi": "Subtitle overlay hidden",
    "Uyarı: overlay tıklamaları oyuna geçiremiyor (eski Windows sürümü?).":
        "Warning: overlay cannot pass clicks to the game (old Windows version?).",
    "Uyarı: overlay ekran yakalamasından hariç tutulamadı; görüntüde yansıma olabilir.":
        "Warning: overlay could not be excluded from screen capture; mirroring may occur.",
    "Yazı rengi seç": "Pick text color",
    "Dil değiştirildi. Uygulamayı yeniden başlatın.":
        "Language changed. Please restart the application.",

    # --- Motor açıklamaları ---
    "Ücretsiz ve hızlı. API anahtarı gerekmez; küçük metinler için idealdir.":
        "Free and fast. No API key required; ideal for small texts.",
    "Ücretsiz yedek motor. Google kapalıyken otomatik devreye girer.":
        "Free fallback engine. Kicks in automatically when Google is down.",
    "Doğal ve akıcı çeviri kalitesi. DeepL API anahtarı gerekir.":
        "Natural, fluent translation quality. Requires a DeepL API key.",
    "ChatGPT / Gemini / DeepSeek uyumlu. Kaliteli bağlam çevirisi; API anahtarı gerekir.":
        "ChatGPT / Gemini / DeepSeek compatible. High-quality context translation; requires an API key.",

    # --- Motor adları ---
    "Google Çeviri (ücretsiz, anahtar gerekmez)": "Google Translate (free, no key)",
    "MyMemory (ücretsiz yedek)": "MyMemory (free fallback)",
    "DeepL API (anahtar gerekir)": "DeepL API (key required)",
    "ChatGPT / Gemini / DeepSeek (API anahtarı gerekir)":
        "ChatGPT / Gemini / DeepSeek (API key required)",

    # --- Pipeline ---
    "OCR hatası: {exc}": "OCR error: {exc}",
    "Çeviri hatası: {exc}": "Translation error: {exc}",
    "Pipeline hatası: {exc}": "Pipeline error: {exc}",
    "Pipeline başladı. Motor: {engine} | OCR: {mode}": "Pipeline started. Engine: {engine} | OCR: {mode}",
    "Pipeline durdu: {exc}": "Pipeline stopped: {exc}",

    # --- OCR motoru ---
    "OCR motoru hazır değil.\n{help}": "OCR engine not ready.\n{help}",
    "- 'pip install pytesseract'": "- 'pip install pytesseract'",
    "- Tesseract bulundu: {exe}": "- Tesseract found: {exe}",
    "- Tesseract kurulu değil: https://github.com/UB-Mannheim/tesseract/wiki\n  veya 'winget install UB-Mannheim.TesseractOCR'":
        "- Tesseract not installed: https://github.com/UB-Mannheim/tesseract/wiki\n  or 'winget install UB-Mannheim.TesseractOCR'",
    "- Windows yerleşik OCR kullanılabilir.": "- Windows built-in OCR is available.",
    "- 'pip install winocr' ile Windows yerleşik OCR eklenebilir.":
        "- Install Windows built-in OCR with 'pip install winocr'.",
    "Tesseract dili hatası ({exc}). 'ocr_langs' ayarını kontrol edin. Japonca için jpn.traineddata, Korece için kor.traineddata gerekir.":
        "Tesseract language error ({exc}). Check the 'ocr_langs' setting. jpn.traineddata is needed for Japanese, kor.traineddata for Korean.",

    # --- Çevirmen ---
    "deep-translator yüklü değil": "deep-translator is not installed",
    "DeepL API anahtarı boş. Ayarlardan ekleyin.": "DeepL API key is empty. Add it in Settings.",
    "openai kütüphanesi yüklü değil": "openai library is not installed",
    "OpenAI/ChatGPT API anahtarı boş. Ayarlardan ekleyin.":
        "OpenAI/ChatGPT API key is empty. Add it in Settings.",
    "otomatik algılanan": "auto-detected",
    "Kaynak dil: {src}": "Source language: {src}",
    "Hedef dil kodu: {target}": "Target language code: {target}",
    "Sadece çeviriyi yaz, başka bir şey yazma.":
        "Only write the translation, nothing else.",
    "Metin:": "Text:",

    # --- Ayarlar ---
    "Ayarlar kaydedilemedi: {exc}": "Failed to save settings: {exc}",
}


def t(text, lang="tr", **kwargs):
    """Metni seçilen dile çevirir; {yer} tutucularını doldurur."""
    if lang == "en":
        text = _EN.get(text, text)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text

"""Anlik Oyun Ceviri logosu uretir: assets/logo.png ve assets/logo.ico."""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)

BG_TOP = (26, 32, 50)
BG_BOTTOM = (35, 40, 57)
ACCENT = (109, 141, 255)
ACCENT_HOVER = (92, 126, 242)
GREEN = (67, 217, 160)
TEXT = (233, 236, 244)
SIZE = 1024
S = 2  # supersample factor


def font(bold=True, size=200):
    paths = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\bahnschrift.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def rounded_rect(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline,
                           width=width)


def build_base():
    img = Image.new("RGBA", (SIZE * S, SIZE * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(SIZE * S):
        t = y / (SIZE * S - 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        d.line([(0, y), (SIZE * S, y)], fill=(r, g, b, 255))
    return img, d


def main():
    img, d = build_base()
    X = SIZE * S

    mask = Image.new("L", (X, X), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, X, X], radius=int(220 * S), fill=255)
    img.putalpha(mask)

    # subtitle barlar (asagi yakin)
    bar_w1 = int(430 * S)
    bar_h = int(58 * S)
    bx = (X - bar_w1) // 2
    by = int(650 * S)
    rounded_rect(d, [bx, by, bx + bar_w1, by + bar_h], radius=bar_h // 2,
                 fill=ACCENT)
    bar_w2 = int(300 * S)
    bx2 = (X - bar_w2) // 2
    by2 = by + bar_h + int(34 * S)
    rounded_rect(d, [bx2, by2, bx2 + bar_w2, by2 + bar_h], radius=bar_h // 2,
                 fill=TEXT)

    # monogram
    mono = Image.new("RGBA", (X, X), (0, 0, 0, 0))
    md = ImageDraw.Draw(mono)
    f = font(bold=True, size=int(300 * S))
    text = "AC"
    bbox = md.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (X - tw) // 2 - bbox[0]
    ty = (X - th) // 2 - bbox[1] - int(60 * S)
    md.text((tx, ty), text, font=f, fill=ACCENT)

    # yaziya sifir dogrusal vurgu: buyuk AC harfinin altinda yesil nokta
    dot_r = int(26 * S)
    dd = ImageDraw.Draw(mono)
    dd.ellipse([X // 2 - dot_r, X // 2 + int(170 * S),
                X // 2 + dot_r, X // 2 + int(170 * S) + dot_r * 2], fill=GREEN)

    img = Image.alpha_composite(img, mono)

    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120))

    png_path = os.path.join(ASSETS, "logo.png")
    ico_path = os.path.join(ASSETS, "logo.ico")
    img.save(png_path)
    img.save(ico_path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                              (64, 64), (128, 128), (256, 256)])

    # uygulama penceresi icin kucuk bir de png uret
    small = img.resize((64, 64), Image.LANCZOS)
    small.save(os.path.join(ASSETS, "logo_64.png"))

    print("logo.png :", os.path.getsize(png_path), "bytes")
    print("logo.ico :", os.path.getsize(ico_path), "bytes")


if __name__ == "__main__":
    main()

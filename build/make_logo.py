"""Anlik Oyun Ceviri logosu uretir: assets/logo.png ve assets/logo.ico.

Tasarim: degrade arka plan uzerinde isik parlamasi, vurgu halkasi ve
icinde "A" (Latin) + "文" (CJK) tasiyan konusma balonu - ceviri metafosu.
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)

BG_TOP = (30, 38, 66)
BG_BOTTOM = (14, 17, 28)
ACCENT = (109, 141, 255)
VIOLET = (139, 111, 255)
GREEN = (67, 217, 160)
WHITE = (238, 241, 248)
SIZE = 1024
S = 2  # supersample


def font(path, size):
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def main():
    X = SIZE * S
    img = Image.new("RGBA", (X, X), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 1) Arka plan: capraz degrade + sol ustte menekse isigi
    for y in range(X):
        t = y / (X - 1)
        base = lerp(BG_TOP, BG_BOTTOM, t)
        d.line([(0, y), (X, y)], fill=base + (255,))
    glow = Image.new("RGBA", (X, X), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-int(150 * S), -int(180 * S), int(700 * S), int(380 * S)],
               fill=VIOLET + (46,))
    gd.ellipse([int(500 * S), int(80 * S), int(1100 * S), int(420 * S)],
               fill=ACCENT + (34,))
    img = Image.alpha_composite(img, glow)

    # 2) Yuvarlatilmis kare maske
    mask = Image.new("L", (X, X), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, X, X], radius=int(228 * S), fill=255)
    img.putalpha(mask)

    # 3) Vurgu halkasi
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([int(34 * S), int(34 * S), int(990 * S), int(990 * S)],
                        radius=int(210 * S), outline=ACCENT + (255,), width=int(13 * S))

    # 4) Konusma balonu: degrade (accent -> violet) + kuyruk
    b = [int(252 * S), int(322 * S), int(772 * S), int(720 * S)]
    rad = int(98 * S)
    bubble = Image.new("RGBA", (X, X), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bubble)
    for yy in range(b[1], b[3]):
        t = (yy - b[1]) / max(1, (b[3] - b[1] - 1))
        col = lerp(ACCENT, VIOLET, t)
        bd.line([(b[0] + 4, yy), (b[2] - 4, yy)], fill=col + (255,))
    bm = Image.new("L", (X, X), 0)
    ImageDraw.Draw(bm).rounded_rectangle(b, radius=rad, fill=255)
    bubble.putalpha(bm)
    tail = [(int(300 * S), int(700 * S)), (int(196 * S), int(808 * S)),
            (int(430 * S), int(706 * S))]
    ImageDraw.Draw(bubble).polygon(tail, fill=VIOLET + (255,))
    # kuyruk dis cerceve
    ImageDraw.Draw(bubble).line(tail + [tail[0]], fill=(90, 66, 190, 255), width=int(9 * S))
    img = Image.alpha_composite(img, bubble)

    # 5) Balonun altinda yumusak golge
    shadow = Image.new("RGBA", (X, X), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse(
        [int(240 * S), int(660 * S), int(790 * S), int(860 * S)], fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(34 * S)))
    img = Image.alpha_composite(img, shadow)

    # 6) Metinler: "A" (beyaz) ve "文" (yesil)
    mono = Image.new("RGBA", (X, X), (0, 0, 0, 0))
    md = ImageDraw.Draw(mono)
    f_a = font(r"C:\Windows\Fonts\seguibl.ttf", int(252 * S))
    f_cjk = font(r"C:\Windows\Fonts\msyhbd.ttc", int(232 * S))
    cx = X // 2
    # A
    bb = md.textbbox((0, 0), "A", font=f_a)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    md.text((cx - tw // 2 - bb[0], int(430 * S) - th // 2 - bb[1]), "A",
            font=f_a, fill=WHITE + (255,))
    # 文
    bb2 = md.textbbox((0, 0), "文", font=f_cjk)
    tw2, th2 = bb2[2] - bb2[0], bb2[3] - bb2[1]
    md.text((cx - tw2 // 2 - bb2[0], int(612 * S) - th2 // 2 - bb2[1]), "文",
            font=f_cjk, fill=GREEN + (255,))
    img = Image.alpha_composite(img, mono)

    # 7) Balonun sag alt kosesinde kucuk vurgu noktasi
    d = ImageDraw.Draw(img)
    r = int(24 * S)
    d.ellipse([int(758 * S) - r, int(366 * S) - r, int(758 * S) + r, int(366 * S) + r],
              fill=GREEN + (255,))

    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=130))

    png_path = os.path.join(ASSETS, "logo.png")
    ico_path = os.path.join(ASSETS, "logo.ico")
    img.save(png_path)
    img.save(ico_path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                              (64, 64), (128, 128), (256, 256)])
    small = img.resize((64, 64), Image.LANCZOS)
    small.save(os.path.join(ASSETS, "logo_64.png"))

    print("logo.png :", os.path.getsize(png_path), "bytes")
    print("logo.ico :", os.path.getsize(ico_path), "bytes")


if __name__ == "__main__":
    main()

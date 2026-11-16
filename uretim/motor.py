"""Boncuk video motoru: dikey (1080x1920) çocuk Shorts videoları üretir.

Bölüm türleri:
  toplar : renkli toplar aynı renkteki bardaklara atlar (renk öğretimi, TR + EN)
  kule   : renkli bloklar üst üste dizilir, sonunda kule yıkılır (renk öğretimi, TR + EN)
  golge  : "Bu kimin gölgesi?" hayvan bilmecesi (hayvan adı TR + EN + kısa bilgi)
"""
from __future__ import annotations

import asyncio
import colorsys
import hashlib
import math
import pathlib
import subprocess
import wave
from functools import lru_cache

import edge_tts
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

KOK = pathlib.Path(__file__).parent
VAR = KOK / "varliklar"
ONBELLEK = KOK / "onbellek"
ONBELLEK.mkdir(exist_ok=True)
W, H, FPS, SR = 1080, 1920, 30, 44100
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

RENKLER = [
    ("Kırmızı", "Red", (236, 58, 62)),
    ("Turuncu", "Orange", (255, 138, 28)),
    ("Sarı", "Yellow", (255, 208, 20)),
    ("Yeşil", "Green", (58, 188, 82)),
    ("Mavi", "Blue", (38, 128, 240)),
    ("Mor", "Purple", (150, 78, 214)),
    ("Pembe", "Pink", (255, 116, 178)),
]
BONCUK_RENK = (120, 196, 255)
KOYU_YAZI = (60, 50, 90)

# Boncuk'un sesi (çocuksu, neşeli) ve İngilizce kelimeleri söyleyen arkadaşının sesi
SESLER = {
    "tr": ("tr-TR-EmelNeural", "+0%", "+25Hz"),
    "en": ("en-US-AnaNeural", "-10%", "+0Hz"),
}


# ---------------------------------------------------------------- yardımcılar
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def tr_buyuk(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def tr_kucuk(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def lerp(a, b, t):
    return a + (b - a) * t


def renk_lerp(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


def acik(c, k):
    return tuple(int(v + (255 - v) * k) for v in c)


def koyu(c, k):
    return tuple(int(v * (1 - k)) for v in c)


def ease_out_back(x):
    x = clamp(x)
    c1 = 1.9
    return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_in_out(x):
    return 0.5 - 0.5 * math.cos(math.pi * clamp(x))


@lru_cache(maxsize=None)
def font(size):
    f = ImageFont.truetype(str(VAR / "Baloo2.ttf"), size)
    try:
        f.set_variation_by_axes([800])
    except Exception:  # noqa: BLE001
        pass
    return f


def yapistir(tuval, sprite, cx, cy, olcek=1.0, alfa=1.0, aci=0.0):
    """Sprite'ı merkezi (cx, cy) olacak şekilde tuvale yapıştırır."""
    if olcek <= 0.01 or alfa <= 0.01:
        return
    s = sprite
    if abs(olcek - 1) > 1e-3:
        s = s.resize((max(1, int(s.width * olcek)), max(1, int(s.height * olcek))), Image.BILINEAR)
    if abs(aci) > 0.1:
        s = s.rotate(aci, resample=Image.BICUBIC, expand=True)
    if alfa < 0.999:
        s = s.copy()
        s.putalpha(s.getchannel("A").point(lambda a: int(a * alfa)))
    tuval.paste(s, (int(cx - s.width / 2), int(cy - s.height / 2)), s)


@lru_cache(maxsize=256)
def yazi_sprite(metin, boyut, renk, kenar=(255, 255, 255), kalinlik=12):
    f = font(boyut)
    x0, y0, x1, y1 = f.getbbox(metin, stroke_width=kalinlik)
    im = Image.new("RGBA", (x1 - x0 + 30, y1 - y0 + 34), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((15 - x0 + 5, 15 - y0 + 9), metin, font=f, fill=(0, 0, 0, 55), stroke_width=kalinlik, stroke_fill=(0, 0, 0, 55))
    d.text((15 - x0, 15 - y0), metin, font=f, fill=renk, stroke_width=kalinlik, stroke_fill=kenar)
    return im


@lru_cache(maxsize=32)
def gokkusagi_yazi(metin, boyut):
    """Her harfi farklı renkte başlık."""
    f = font(boyut)
    kal = 14
    x0, y0, x1, y1 = f.getbbox(metin, stroke_width=kal)
    im = Image.new("RGBA", (x1 - x0 + 40, y1 - y0 + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 20 - x0
    renkler = [r[2] for r in RENKLER[:6]]
    i = 0
    for ch in metin:
        d.text((x + 5, 20 - y0 + 9), ch, font=f, fill=(0, 0, 0, 55), stroke_width=kal, stroke_fill=(0, 0, 0, 55))
        d.text((x, 20 - y0), ch, font=f, fill=renkler[i % 6] if ch.strip() else (0, 0, 0, 0), stroke_width=kal, stroke_fill=(255, 255, 255))
        if ch.strip():
            i += 1
        x += f.getlength(ch)
    return im


# ---------------------------------------------------------------- 3B şekiller
@lru_cache(maxsize=128)
def kure(renk, r):
    """Parlak, gölgeli 3B top (RGBA, çapı ~2r)."""
    S = 3
    R = r * S
    n = 2 * R + 6
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    c = n / 2
    d = np.sqrt((x - c) ** 2 + (y - c) ** 2) / R
    dh = np.sqrt((x - (c - 0.35 * R)) ** 2 + (y - (c - 0.42 * R)) ** 2) / R
    base = np.array(renk, np.float32)
    light = np.array(acik(renk, 0.40), np.float32)
    dark = np.array(koyu(renk, 0.38), np.float32)
    t = np.clip(dh / 1.1, 0, 1)[..., None]
    col = light * (1 - t) + base * t
    t2 = np.clip((dh - 0.95) / 0.55, 0, 1)[..., None]
    col = col * (1 - t2) + dark * t2
    sp = np.clip(1 - np.sqrt((x - (c - 0.36 * R)) ** 2 + (y - (c - 0.46 * R)) ** 2) / (0.2 * R), 0, 1) ** 1.6
    col = col * (1 - sp[..., None] * 0.9) + 255 * sp[..., None] * 0.9
    alpha = np.clip((1 - d) * R * 0.8, 0, 1) * 255
    arr = np.dstack([np.clip(col, 0, 255), alpha]).astype(np.uint8)
    return Image.fromarray(arr, "RGBA").resize((n // S, n // S), Image.LANCZOS)


@lru_cache(maxsize=16)
def bardak(renk, w=132, h=170):
    """(arka, on) iki katman döndürür; top arkayla ön arasına çizilir."""
    S = 3
    W_, H_ = w * S, h * S
    rim_h = int(w * 0.30 * S)
    pad = 10 * S
    cw, ch = W_ + 2 * pad, H_ + rim_h + 2 * pad
    cx = cw / 2
    rim_y = pad + rim_h / 2
    alt = rim_y + H_
    alt_g = W_ * 0.80
    # gövde maskesi
    mask = Image.new("L", (cw, ch), 0)
    md = ImageDraw.Draw(mask)
    md.polygon([(cx - W_ / 2, rim_y), (cx + W_ / 2, rim_y), (cx + alt_g / 2, alt), (cx - alt_g / 2, alt)], fill=255)
    md.ellipse([cx - alt_g / 2, alt - rim_h * 0.4, cx + alt_g / 2, alt + rim_h * 0.4], fill=255)
    # yatay gölgelendirme
    xs = (np.arange(cw) - cx) / (W_ / 2)
    k = np.clip(1 - np.abs(xs + 0.3) / 1.3, 0, 1)
    base = np.array(renk, np.float32)
    lt = np.array(acik(renk, 0.35), np.float32)
    dk = np.array(koyu(renk, 0.30), np.float32)
    row = np.where(k[:, None] > 0.5, base + (lt - base) * ((k[:, None] - 0.5) * 2), dk + (base - dk) * (k[:, None] * 2))
    govde = np.repeat(row[None, :, :], ch, axis=0)
    on = Image.fromarray(np.dstack([govde, np.array(mask, np.float32)]).astype(np.uint8), "RGBA")
    od = ImageDraw.Draw(on)
    # ağız kenarı (ön yarısı)
    od.arc([cx - W_ / 2, rim_y - rim_h / 2, cx + W_ / 2, rim_y + rim_h / 2], 0, 180, fill=acik(renk, 0.5) + (255,), width=7 * S)
    arka = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arka)
    ad.ellipse([cx - W_ / 2, rim_y - rim_h / 2, cx + W_ / 2, rim_y + rim_h / 2], fill=acik(renk, 0.45) + (255,))
    ad.ellipse([cx - W_ / 2 + 9 * S, rim_y - rim_h / 2 + 6 * S, cx + W_ / 2 - 9 * S, rim_y + rim_h / 2 - 5 * S], fill=koyu(renk, 0.55) + (255,))
    boyut = (cw // S, ch // S)
    return arka.resize(boyut, Image.LANCZOS), on.resize(boyut, Image.LANCZOS), rim_y / S


@lru_cache(maxsize=16)
def blok(renk, w=230, h=120, derinlik=26):
    S = 3
    W_, H_, D = w * S, h * S, derinlik * S
    im = Image.new("RGBA", (W_ + D + 4 * S, H_ + D + 4 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = 18 * S
    # üst yüz
    d.polygon([(0 + r / 2, D), (D + r / 2, 0), (D + W_ - r / 2, 0), (W_ - r / 2, D)], fill=acik(renk, 0.35))
    # yan yüz
    d.polygon([(W_ - 2, D), (W_ + D - 2, 0 + r / 2), (W_ + D - 2, H_ - r / 2), (W_ - 2, D + H_ - r)], fill=koyu(renk, 0.28))
    # ön yüz (dikey degrade)
    on = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    ys = np.linspace(0, 1, H_)[:, None, None]
    c1, c2 = np.array(acik(renk, 0.12), np.float32), np.array(koyu(renk, 0.12), np.float32)
    grad = np.repeat((c1 * (1 - ys) + c2 * ys), W_, axis=1)
    m = Image.new("L", (W_, H_), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W_ - 1, H_ - 1], r, fill=255)
    on = Image.fromarray(np.dstack([grad, np.array(m, np.float32)]).astype(np.uint8), "RGBA")
    od = ImageDraw.Draw(on)
    od.rounded_rectangle([14 * S, 12 * S, W_ - 14 * S, 30 * S], 9 * S, fill=acik(renk, 0.55) + (150,))
    # ortada kabartma yıldız
    cx, cy, R = W_ / 2, H_ / 2 + 6 * S, 34 * S
    pts = [(cx + (R if i % 2 == 0 else R * 0.45) * math.sin(i * math.pi / 5), cy - (R if i % 2 == 0 else R * 0.45) * math.cos(i * math.pi / 5)) for i in range(10)]
    od.polygon(pts, fill=acik(renk, 0.45))
    im.paste(on, (0, D), on)
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)


@lru_cache(maxsize=1)
def zemin_golge():
    im = Image.new("RGBA", (360, 90), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([30, 20, 330, 70], fill=(40, 30, 80, 70))
    return im.filter(ImageFilter.GaussianBlur(10))


# ---------------------------------------------------------------- Boncuk karakteri
@lru_cache(maxsize=512)
def boncuk(renk, goz_kapali=False, agiz=0):
    """Boncuk: yuvarlak, renk değiştiren, başında filiz olan sevimli karakter. 340x400 RGBA."""
    S = 3
    cw, ch = 340 * S, 400 * S
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    p = lambda v: v * S  # noqa: E731
    ayak = koyu(renk, 0.32)
    d.ellipse([p(82), p(338), p(158), p(378)], fill=ayak)
    d.ellipse([p(182), p(338), p(258), p(378)], fill=ayak)
    # filiz
    d.line([p(170), p(100), p(172), p(58)], fill=(70, 160, 70), width=p(9))
    d.ellipse([p(128), p(40), p(172), p(70)], fill=(98, 204, 96))
    d.ellipse([p(170), p(30), p(222), p(62)], fill=(118, 218, 110))
    # gövde
    govde = kure(renk, 150).resize((p(306), p(282)), Image.LANCZOS)
    im.paste(govde, (p(17), p(80)), govde)
    # yanaklar
    yan = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    yd = ImageDraw.Draw(yan)
    for x in (88, 252):
        yd.ellipse([p(x - 26), p(254), p(x + 26), p(282)], fill=(255, 120, 150, 120))
    im.alpha_composite(yan)
    # gözler
    for x in (126, 214):
        if goz_kapali:
            d.arc([p(x - 26), p(196), p(x + 26), p(246)], 200, 340, fill=(40, 30, 50), width=p(8))
        else:
            d.ellipse([p(x - 33), p(176), p(x + 33), p(254)], fill=(255, 255, 255), outline=koyu(renk, 0.45), width=p(3))
            d.ellipse([p(x - 18), p(204), p(x + 22), p(246)], fill=(35, 28, 48))
            d.ellipse([p(x - 10), p(208), p(x + 4), p(222)], fill=(255, 255, 255))
            d.ellipse([p(x + 8), p(230), p(x + 15), p(237)], fill=(255, 255, 255))
    # ağız
    if agiz == 0:
        d.arc([p(146), p(250), p(194), p(292)], 25, 155, fill=(110, 30, 45), width=p(6))
    else:
        h = [0, 18, 28, 38][agiz]
        d.chord([p(146), p(270 - h), p(194), p(270 + h)], 0, 180, fill=(130, 30, 50))
        d.ellipse([p(158), p(268 + h * 0.35), p(182), p(271 + h)], fill=(255, 120, 140))
    return im.resize((340, 400), Image.LANCZOS)


class BoncukDurum:
    """Boncuk'un sahnedeki rengi, zıplaması ve konuşması."""

    def __init__(self, ses, x, taban_y, olcek=1.0):
        self.ses, self.x, self.taban_y, self.olcek = ses, x, taban_y, olcek
        self.renk_olaylari = [(0.0, BONCUK_RENK)]
        self.zipla = []
        self.giris = 0.0

    def renk_degistir(self, t, renk):
        self.renk_olaylari.append((t, renk))

    def renk(self, t):
        i = max(k for k, (zt, _) in enumerate(self.renk_olaylari) if zt <= t or k == 0)
        zt, simdiki = self.renk_olaylari[i]
        onceki = self.renk_olaylari[i - 1][1] if i > 0 else simdiki
        u = clamp((t - zt) / 0.3)
        if u >= 1 or onceki == simdiki:
            son = simdiki
        else:  # renk çemberinde geçiş: mor -> sarı arası çamur rengi olmasın
            h1, s1, v1 = colorsys.rgb_to_hsv(*[c / 255 for c in onceki])
            h2, s2, v2 = colorsys.rgb_to_hsv(*[c / 255 for c in simdiki])
            dh = ((h2 - h1 + 0.5) % 1) - 0.5
            son = tuple(int(c * 255) for c in colorsys.hsv_to_rgb((h1 + dh * u) % 1, lerp(s1, s2, u), lerp(v1, v2, u)))
        return tuple((v // 6) * 6 for v in son)

    def ciz(self, tuval, t, gokkusagi=False):
        renk = self.renk(t)
        if gokkusagi:
            i = t * 3
            a, b = RENKLER[int(i) % 6][2], RENKLER[(int(i) + 1) % 6][2]
            renk = tuple((v // 24) * 24 for v in renk_lerp(a, b, ease_in_out(i % 1)))
        acik_ag = self.ses.agiz(t)
        agiz = 0 if acik_ag < 0.12 else (1 if acik_ag < 0.4 else (2 if acik_ag < 0.7 else 3))
        kirp = ((t + 1.5) % 3.4) < 0.13  # ilk karede (videonun kapağı) gözler açık
        sp = boncuk(renk, kirp, agiz)
        giris = ease_out_back((t - self.giris) / 0.5)
        hop = 0.0
        for zt in self.zipla:
            u = (t - zt) / 0.42
            if 0 <= u <= 1:
                hop = max(hop, math.sin(math.pi * u))
        nefes = math.sin(t * 2 * math.pi * 0.9)
        sx = self.olcek * giris * (1 + 0.02 * nefes - 0.04 * hop)
        sy = self.olcek * giris * (1 - 0.02 * nefes + 0.08 * hop)
        yapistir(tuval, zemin_golge(), self.x, self.taban_y - 4, self.olcek * giris * (1 - 0.35 * hop), 1.0)
        hh = 400 * sy
        cy = self.taban_y - hh / 2 - hop * 70 * self.olcek
        s = sp.resize((max(1, int(340 * sx)), max(1, int(hh))), Image.BILINEAR)
        tuval.paste(s, (int(self.x - s.width / 2), int(cy - s.height / 2)), s)


# ---------------------------------------------------------------- arka plan
def arka_plan(ust, alt, masa_y=None, masa_renk=(255, 214, 160), rng=None):
    ys = np.linspace(0, 1, H)[:, None, None]
    grad = np.array(ust, np.float32) * (1 - ys) + np.array(alt, np.float32) * ys
    im = Image.fromarray(np.repeat(grad, W, axis=1).astype(np.uint8), "RGB").convert("RGBA")
    rng = rng or np.random.default_rng(0)
    bulut = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bulut)
    for _ in range(4):
        x, y = rng.uniform(80, 1000), rng.uniform(380, 1100)
        s = rng.uniform(0.7, 1.2)
        for dx, dy, r in [(-70, 10, 55), (0, -15, 75), (75, 8, 58), (0, 30, 60)]:
            bd.ellipse([x + dx * s - r * s, y + dy * s - r * s, x + dx * s + r * s, y + dy * s + r * s], fill=(255, 255, 255, 120))
    for _ in range(18):
        x, y, r = rng.uniform(0, W), rng.uniform(350, 1400), rng.uniform(5, 11)
        bd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 140))
    im.alpha_composite(bulut.filter(ImageFilter.GaussianBlur(6)))
    if masa_y:
        d = ImageDraw.Draw(im)
        d.rectangle([0, masa_y, W, H], fill=masa_renk)
        d.rectangle([0, masa_y, W, masa_y + 14], fill=acik(masa_renk, 0.5))
        d.rectangle([0, masa_y + 14, W, masa_y + 22], fill=koyu(masa_renk, 0.08))
    return im.convert("RGB")


# ---------------------------------------------------------------- ses
def _mp3_np(path):
    out = subprocess.run([FFMPEG, "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def seslendir(metin, dil="tr"):
    ses, hiz, perde = SESLER[dil]
    anahtar = hashlib.md5(f"{ses}|{hiz}|{perde}|{metin}".encode()).hexdigest()[:16]
    yol = ONBELLEK / f"{anahtar}.mp3"
    if not yol.exists() or yol.stat().st_size < 1000:
        gecici = yol.with_suffix(".tmp")

        async def _k():
            await edge_tts.Communicate(metin, ses, rate=hiz, pitch=perde).save(str(gecici))
        for deneme in range(3):
            try:
                asyncio.run(_k())
                gecici.replace(yol)
                break
            except Exception:  # noqa: BLE001
                if deneme == 2:
                    raise
    s = _mp3_np(yol)
    idx = np.where(np.abs(s) > 0.015)[0]
    if len(idx):
        s = s[max(0, idx[0] - 600): idx[-1] + 2500]
    return s


def zarf(s):
    hop = SR // FPS
    n = len(s) // hop + 1
    e = np.array([np.sqrt(np.mean(s[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(s) else 0 for i in range(n)])
    if e.max() > 0:
        e = e / e.max()
    return np.convolve(e, [0.25, 0.5, 0.25], mode="same")


def _t(d):
    return np.arange(int(d * SR)) / SR


def efekt(ad):
    if ad == "pop":
        t = _t(0.13)
        f = 420 + 2600 * t / 0.13
        return 0.55 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28)
    if ad == "boing":
        t = _t(0.4)
        f = 170 + 90 * t / 0.4 + 70 * np.sin(2 * np.pi * 14 * t) * np.exp(-t * 5)
        return 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    if ad == "ding":
        t = _t(0.9)
        w = np.sin(2 * np.pi * 1568 * t) + 0.35 * np.sin(2 * np.pi * 3136 * t) + 0.12 * np.sin(2 * np.pi * 4704 * t)
        return 0.28 * w * np.exp(-t * 5)
    if ad == "whoosh":
        t = _t(0.4)
        n = np.random.default_rng(1).standard_normal(len(t))
        n = np.convolve(n, np.ones(24) / 24, mode="same")
        return 0.9 * n * np.sin(np.pi * t / 0.4) ** 2
    if ad == "tik":
        t = _t(0.07)
        return 0.45 * np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 70)
    if ad == "thud":
        t = _t(0.3)
        n = np.random.default_rng(2).standard_normal(len(t))
        return 0.7 * np.sin(2 * np.pi * (95 - 40 * t) * t) * np.exp(-t * 14) + 0.12 * n * np.exp(-t * 40)
    if ad == "kayma":
        t = _t(0.75)
        f = 1100 * np.exp(-t * 1.8)
        return 0.32 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 - t / 0.75)
    if ad == "tada":
        out = np.zeros(int(1.4 * SR))
        for i, fr in enumerate([523.25, 659.25, 783.99, 1046.5]):
            t = _t(1.4 - i * 0.1 if i < 3 else 1.1)
            w = (np.sin(2 * np.pi * fr * t) + 0.3 * np.sin(4 * np.pi * fr * t)) * np.exp(-t * (6 if i < 3 else 2.5))
            st = int(i * 0.1 * SR)
            out[st:st + len(w)] += 0.22 * w[: len(out) - st]
        return out
    raise ValueError(ad)


def muzik(T, seed):
    """Her bölüm için özgün, neşeli fon müziği (I-V-vi-IV veya I-IV-V-I akorları)."""
    rng = np.random.default_rng(seed)
    bpm = int(rng.choice([100, 108, 116]))
    beat = 60 / bpm
    key = int(rng.choice([0, 2, 5, 7]))
    prog = [[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]] if rng.random() < 0.5 else [[0, 4, 7], [5, 9, 12], [7, 11, 14], [0, 4, 7]]
    ritimler = [[0, 2, 4, 6], [0, 3, 4, 6], [0, 2, 3, 4, 6], [0, 1, 2, 4], [0, 4, 6], [0, 2, 4, 5, 6]]
    penta = [0, 2, 4, 7, 9, 12]
    n = int((T + 2) * SR)
    out = np.zeros(n, np.float32)

    def hz(s):
        return 261.63 * 2 ** ((s + key) / 12)

    def yerlestir(w, t0):
        i = int(t0 * SR)
        if i < n:
            out[i:i + len(w)] += w[: n - i]

    def nota(fr, dur, amp, tur):
        t = _t(dur)
        if tur == "bas":
            w = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * fr * t)) * np.exp(-t * 2.5)
        elif tur == "akor":
            w = (np.sin(2 * np.pi * fr * t) + 0.3 * np.sin(4 * np.pi * fr * t)) * np.exp(-t * 6)
        else:
            w = (np.sin(2 * np.pi * fr * t) + 0.35 * np.sin(2 * np.pi * fr * 2.0 * t) * np.exp(-t * 9)) * np.exp(-t * 3.5)
        return (w * np.clip(t / 0.006, 0, 1) * amp).astype(np.float32)

    cumle = []
    for b in range(4):
        akor = prog[b]
        for e in ritimler[int(rng.integers(len(ritimler)))]:
            ton = akor[int(rng.integers(3))] + 12 if rng.random() < 0.7 else penta[int(rng.integers(len(penta)))] + 12
            cumle.append((b, e, ton))
    gurultu = np.random.default_rng(seed + 7).standard_normal(int(0.05 * SR))
    for bar in range(int(T / (4 * beat)) + 2):
        t0 = bar * 4 * beat
        akor = prog[bar % 4]
        for bt in (0, 2):
            yerlestir(nota(hz(akor[0] - 12), beat * 1.8, 0.30, "bas"), t0 + bt * beat)
        for bt in (1, 3):
            for s in akor:
                yerlestir(nota(hz(s), beat * 0.9, 0.06, "akor"), t0 + bt * beat)
        for (b, e, ton) in cumle:
            if b == bar % 4:
                yerlestir(nota(hz(ton), beat * 1.2, 0.15, "zil"), t0 + e * beat / 2)
        for e in range(8):
            yerlestir((gurultu * np.exp(-_t(0.05) * 90) * (0.035 if e % 2 else 0.018)).astype(np.float32), t0 + e * beat / 2)
    fade = np.ones(n, np.float32)
    fade[: int(0.4 * SR)] = np.linspace(0, 1, int(0.4 * SR))
    son = int(T * SR)
    fade[max(0, son - SR): son] = np.linspace(1, 0, min(SR, son))
    fade[son:] = 0
    return out * fade


class Ses:
    def __init__(self):
        self.konusma = []  # (t, örnekler)
        self.efektler = []
        self.agizlar = []  # Boncuk'un dudak hareketi için (t, zarf)

    def konus(self, t, metin, dil="tr", boncuk_mu=True):
        s = seslendir(metin, dil)
        self.konusma.append((t, s))
        if boncuk_mu:
            self.agizlar.append((t, zarf(s)))
        return len(s) / SR

    def efekt(self, t, ad, kazanc=1.0):
        self.efektler.append((t, efekt(ad) * kazanc))

    def agiz(self, t):
        for st, e in self.agizlar:
            i = int((t - st) * FPS)
            if 0 <= i < len(e):
                return float(e[i])
        return 0.0

    def miksle(self, T, seed, yol):
        n = int((T + 1) * SR)
        konusma = np.zeros(n, np.float32)
        fx = np.zeros(n, np.float32)
        for hedef, liste in ((konusma, self.konusma), (fx, self.efektler)):
            for t, s in liste:
                i = int(t * SR)
                if i < n:
                    hedef[i:i + len(s)] += s[: n - i]
        m = muzik(T, seed)[:n]
        m = np.pad(m, (0, n - len(m)))
        c = np.concatenate([[0.0], np.cumsum(np.abs(konusma), dtype=np.float64)])
        k = 4410
        duck = np.zeros(n, np.float32)
        duck[k // 2: k // 2 + n - k + 1] = (c[k:] - c[:-k]) / k
        duck = np.clip(duck / (duck.max() + 1e-6) * 3, 0, 1)
        mix = konusma * 1.0 + fx * 0.8 + m * 0.55 * (1 - 0.6 * duck)
        mix = mix[: int(T * SR)]
        mix = mix / (np.abs(mix).max() + 1e-6) * 0.92
        with wave.open(str(yol), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes((mix * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- parçacıklar
def yildiz_noktalari(cx, cy, R, r, aci=0.0):
    return [(cx + (R if i % 2 == 0 else r) * math.sin(i * math.pi / 4 + aci), cy - (R if i % 2 == 0 else r) * math.cos(i * math.pi / 4 + aci)) for i in range(8)]


class Parilti:
    def __init__(self, rng, x, y, t0, renk, adet=12):
        self.p = []
        for _ in range(adet):
            a = rng.uniform(-math.pi, 0)
            v = rng.uniform(300, 650)
            self.p.append((math.cos(a) * v, math.sin(a) * v, rng.uniform(14, 26), rng.random() < 0.5))
        self.x, self.y, self.t0, self.renk = x, y, t0, renk

    def ciz(self, d, t):
        u = t - self.t0
        if not 0 <= u <= 0.8:
            return
        for vx, vy, s, beyaz in self.p:
            x = self.x + vx * u
            y = self.y + vy * u + 900 * u * u
            R = s * (1 - u / 0.8)
            d.polygon(yildiz_noktalari(x, y, R, R * 0.4, u * 4), fill=(255, 255, 255) if beyaz else acik(self.renk, 0.2))


class Konfeti:
    def __init__(self, rng, t0, adet=90):
        self.t0 = t0
        self.p = [(rng.uniform(0, W), rng.uniform(-900, -20), rng.uniform(260, 520), rng.uniform(0, 6.28), rng.uniform(2, 6),
                   RENKLER[int(rng.integers(7))][2], rng.uniform(14, 24)) for _ in range(adet)]

    def ciz(self, d, t):
        u = t - self.t0
        if u < 0:
            return
        for x, y, v, ph, sp, c, s in self.p:
            yy = y + v * u
            if yy > H + 40:
                continue
            xx = x + 40 * math.sin(ph + u * 3)
            a = ph + u * sp
            w, h = s, s * 0.55 * abs(math.cos(a * 1.3)) + 2
            ca, sa = math.cos(a), math.sin(a)
            pts = [(xx + ca * dx - sa * dy, yy + sa * dx + ca * dy) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
            d.polygon(pts, fill=c)


def soru_isaretleri(tv, t, noktalar, alfa=1.0):
    """Açılış kancası: ekranda zıplayan turuncu soru işaretleri."""
    if alfa <= 0:
        return
    for i, (qx, qy) in enumerate(noktalar):
        g = ease_out_back(clamp((t - 0.08 * i) / 0.35))
        if g <= 0:
            continue
        yapistir(tv, yazi_sprite("?", 120, (255, 140, 30), (255, 255, 255), 12), qx, qy + 15 * math.sin(t * 4 + i),
                 g * (0.9 + 0.1 * math.sin(t * 6 + i)), alfa)


# ---------------------------------------------------------------- sahneler
class Sahne:
    baslik = ""
    alt_baslik = ""

    def __init__(self, rng, ses):
        self.rng, self.ses = rng, ses
        self.T = 0.0

    def baslik_ciz(self, bg):
        yapistir(bg, gokkusagi_yazi(self.baslik, 100), W / 2, 210)
        if self.alt_baslik:
            yapistir(bg, yazi_sprite(self.alt_baslik, 58, KOYU_YAZI, (255, 255, 255), 10), W / 2, 318)

    @staticmethod
    def kelime_ciz(tuval, metin, renk, x, y, t, t_bas, t_bit, boyut):
        if t < t_bas or t > t_bit + 0.25:
            return
        olcek = ease_out_back((t - t_bas) / 0.35)
        alfa = 1 - clamp((t - t_bit) / 0.25)
        yapistir(tuval, yazi_sprite(metin, boyut, renk, (255, 255, 255), 14), x, y, olcek, alfa)


class Toplar(Sahne):
    baslik = "Renkleri Öğrenelim!"
    alt_baslik = "Let's learn colors!"
    # Shorts'ta izleyici ilk 1-2 saniyede kaydırır: uzun selamlama yerine ilk top hemen belirir
    # ve Boncuk kısa bir soru sorar (kanca), ardından rengi söyler.
    KANCALAR = ["Bu top hangi renk?", "Hangi renk bu?", "Bil bakalım, bu hangi renk?"]
    CIKISLAR = [
        "Yaşasın! Bütün toplar bardağına ulaştı! Sen en çok hangi rengi seviyorsun?",
        "Harika! Bütün renkleri birlikte bulduk! Yarın yeni bir oyunda görüşelim!",
        "Süpersin! Bütün renkleri öğrendik! Hoşça kal arkadaşım!",
    ]
    ARA = ["Süper!", "Aferin!", "Çok güzel!", "Harika!"]

    def __init__(self, rng, ses):
        super().__init__(rng, ses)
        secim = [RENKLER[i] for i in rng.choice(7, 6, replace=False)]
        self.bardak_sira = list(secim)
        self.top_sira = [secim[i] for i in rng.permutation(6)]
        # Shorts güvenli alanı: alttaki ~400 px ve sağdaki ~130 px telefonda yazı/butonlarla kapanır
        self.bardak_x = [110 + i * 152 for i in range(6)]
        self.bardak_alt = 1440
        self.bg = arka_plan((150, 210, 255), (225, 242, 255), masa_y=1365, rng=rng).convert("RGBA")
        self.baslik_ciz(self.bg)
        self.bg = self.bg.convert("RGB")
        self.boncuk = BoncukDurum(ses, 490, 935)
        self.baslangic = (490, 470)
        self.boncuk.giris = -0.25  # 0. karede Boncuk zaten zıplayarak geliyor

        kanca = str(rng.choice(self.KANCALAR))
        t = 0.0
        self.toplar = []
        for k, (ad, ing, renk) in enumerate(self.top_sira):
            j = self.bardak_sira.index((ad, ing, renk))
            o = {"renk": renk, "ad": ad, "ing": ing, "j": j, "dogum": t - 0.3 if k == 0 else t}  # ilk top 0. karede görünür
            ses.efekt(t + 0.03, "pop")
            o["tr"] = (0.2 + ses.konus(0.2, kanca) + 0.12) if k == 0 else t + 0.35
            o["kanca"] = k == 0
            self.boncuk.renk_degistir(o["tr"], renk)
            d1 = ses.konus(o["tr"], ad + "!")
            o["en"] = o["tr"] + d1 + 0.12
            d2 = ses.konus(o["en"], ing + "!", "en", boncuk_mu=False)
            o["ziplama"] = o["en"] + d2 + 0.15
            ses.efekt(o["ziplama"], "whoosh", 0.7)
            o["inis"] = o["ziplama"] + 0.8
            ses.efekt(o["inis"], "boing")
            ses.efekt(o["inis"] + 0.05, "ding")
            self.boncuk.zipla.append(o["inis"])
            o["parilti"] = Parilti(rng, self.bardak_x[j], self.kenar_y(), o["inis"], renk)
            t = o["inis"] + 0.45
            if k in (2, 4):
                t += ses.konus(t, str(rng.choice(self.ARA))) + 0.2
            self.toplar.append(o)
        self.cikis = t + 0.2
        ses.efekt(self.cikis, "tada")
        self.konfeti = Konfeti(rng, self.cikis)
        t = self.cikis + 0.4 + ses.konus(self.cikis + 0.4, str(rng.choice(self.CIKISLAR)))
        self.T = t + 1.3

    def kenar_y(self):
        _, _, rim = bardak((0, 0, 0))
        on = bardak((0, 0, 0))[1]
        return self.bardak_alt - on.height + rim

    def top_konum(self, o, t):
        bx, by = self.bardak_x[o["j"]], self.kenar_y() + 22
        if t < o["ziplama"]:
            u = (t - o["dogum"])
            return self.baslangic[0], self.baslangic[1] + 10 * math.sin(u * 5), ease_out_back(u / 0.35), False
        if t < o["inis"]:
            u = clamp((t - o["ziplama"]) / 0.8) ** 1.15
            p0, p2 = self.baslangic, (bx, by)
            p1 = ((p0[0] + bx) / 2, 280)
            x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0]
            y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]
            return x, y, 1.0, y > by - 70
        v = t - o["inis"]
        sek = -30 * abs(math.sin(math.pi * v / 0.2)) * math.exp(-v * 9) if v < 0.7 else 0
        return bx, by + sek, 1.0, True

    def kare(self, t):
        tv = self.bg.copy()
        d = ImageDraw.Draw(tv)
        self.boncuk.ciz(tv, t, gokkusagi=t > self.cikis)
        icerde = {j: [] for j in range(6)}
        disarda = []
        for o in self.toplar:
            if t < o["dogum"]:
                continue
            x, y, s, ic = self.top_konum(o, t)
            (icerde[o["j"]] if ic else disarda).append((o, x, y, s))
        for j, (ad, ing, renk) in enumerate(self.bardak_sira):
            arka, on, rim = bardak(renk)
            sars = 0.0
            for o in self.toplar:
                v = t - o["inis"]
                if o["j"] == j and 0 <= v < 0.3:
                    sars = 14 * math.sin(math.pi * v / 0.3)
            cx = self.bardak_x[j]
            cy = self.bardak_alt - on.height / 2 + sars
            yapistir(tv, arka, cx, cy)
            for o, x, y, s in icerde[j]:
                yapistir(tv, kure(o["renk"], 55), x, y + sars, s)
            yapistir(tv, on, cx, cy)
        for o, x, y, s in disarda:
            yapistir(tv, kure(o["renk"], 55), x, y, s)
        ilk = self.toplar[0]
        if t < ilk["tr"] + 0.2:
            soru_isaretleri(tv, t, [(250, 430), (735, 400), (300, 640), (690, 650)], 1 - clamp((t - ilk["tr"]) / 0.2))
        for o in self.toplar:
            self.kelime_ciz(tv, tr_buyuk(o["ad"]), o["renk"], 490, 1025, t, o["tr"], o["ziplama"], 120)
            self.kelime_ciz(tv, o["ing"], KOYU_YAZI, 490, 1138, t, o["en"], o["ziplama"], 76)
            o["parilti"].ciz(d, t)
        self.konfeti.ciz(d, t)
        return tv


class Kule(Sahne):
    baslik = "Renkli Kule!"
    alt_baslik = "Build a rainbow tower!"
    KANCALAR = ["Kule yapalım!", "Hangi renk geliyor?"]  # ilk 2 saniye: hemen aksiyon

    def __init__(self, rng, ses):
        super().__init__(rng, ses)
        self.renkler = [RENKLER[i] for i in sorted(rng.choice(7, 6, replace=False))]
        if rng.random() < 0.4:
            self.renkler = [self.renkler[i] for i in rng.permutation(6)]
        self.bg = arka_plan((255, 214, 232), (255, 244, 226), masa_y=1425, masa_renk=(150, 214, 140), rng=rng).convert("RGBA")
        self.baslik_ciz(self.bg)
        self.bg = self.bg.convert("RGB")
        self.kx, self.taban = 370, 1450
        self.bh = 120
        self.boncuk = BoncukDurum(ses, 780, 1480, 0.78)
        self.boncuk.giris = -0.25
        kanca = str(rng.choice(self.KANCALAR))
        t = 0.0
        self.bloklar = []
        for k, (ad, ing, renk) in enumerate(self.renkler):
            b = {"renk": renk, "ad": ad, "ing": ing, "k": k, "dogum": t - 0.3 if k == 0 else t}  # ilk blok 0. karede görünür
            ses.efekt(t + 0.03, "pop")
            b["tr"] = (0.2 + ses.konus(0.2, kanca) + 0.12) if k == 0 else t + 0.3
            self.boncuk.renk_degistir(b["tr"], renk)
            d1 = ses.konus(b["tr"], ad + "!")
            b["en"] = b["tr"] + d1 + 0.12
            d2 = ses.konus(b["en"], ing + "!", "en", boncuk_mu=False)
            b["dusus"] = b["en"] + d2 + 0.15
            b["inis"] = b["dusus"] + 0.45
            ses.efekt(b["inis"], "thud")
            ses.efekt(b["inis"] + 0.03, "ding", 0.6)
            self.boncuk.zipla.append(b["inis"])
            b["parilti"] = Parilti(rng, self.kx, self.yer(k) - self.bh / 2, b["inis"], renk, 10)
            t = b["inis"] + 0.4
            self.bloklar.append(b)
        t += ses.konus(t, "Vay! Kule çok yükseldi!") + 0.1
        self.sallanma = t
        t += 1.3
        ses.efekt(t - 0.4, "kayma")
        ses.konus(t - 0.5, "Uh oh!", "en", boncuk_mu=False)
        self.yikilma = t
        ses.konus(t + 0.5, "Eyvah! Kule yıkıldı!")
        self.fizik = self._fizik(rng)
        for zaman in self.carpma_zamanlari:
            ses.efekt(zaman, "thud", 0.7)
        t += 2.4
        ses.efekt(t, "tada")
        self.konfeti = Konfeti(rng, t)
        self.cikis = t
        t += 0.3 + ses.konus(t + 0.3, "Hadi yarın yine kule yapalım! Hoşça kal!")
        self.T = t + 1.2

    def yer(self, k):
        return self.taban - k * self.bh

    def _fizik(self, rng):
        durumlar = []
        self.carpma_zamanlari = []
        dt = 1 / FPS
        for k in range(6):
            x, y = self.kx, self.yer(k) - self.bh / 2
            vx = rng.uniform(-260, 420) + k * 45
            vy = -rng.uniform(250, 650) - k * 40
            w = rng.uniform(-260, 260)
            a = 0.0
            ilk = True
            seri = []
            for f in range(int(3 * FPS)):
                vy += 2600 * dt
                x += vx * dt
                y += vy * dt
                a += w * dt
                if y > self.taban - 50:
                    y = self.taban - 50
                    if ilk and vy > 300:
                        self.carpma_zamanlari.append(self.yikilma + f * dt)
                        ilk = False
                    vy *= -0.35
                    vx *= 0.6
                    w *= 0.5
                seri.append((x, y, a))
            durumlar.append(seri)
        return durumlar

    def kare(self, t):
        tv = self.bg.copy()
        d = ImageDraw.Draw(tv)
        self.boncuk.ciz(tv, t, gokkusagi=t > self.cikis)
        egim = 0.0
        if self.sallanma <= t < self.yikilma:
            u = t - self.sallanma
            egim = 7 * u * math.sin(u * 14)
        for b in self.bloklar:
            if t < b["dogum"]:
                continue
            sp = blok(b["renk"])
            hedef_y = self.yer(b["k"]) - self.bh / 2
            if t >= self.yikilma:
                f = min(int((t - self.yikilma) * FPS), len(self.fizik[b["k"]]) - 1)
                x, y, a = self.fizik[b["k"]][f]
                yapistir(tv, sp, x, y, 1.0, 1.0, a)
                continue
            if t < b["dusus"]:
                u = t - b["dogum"]
                x, y, s = self.kx, 560 + 8 * math.sin(u * 5), ease_out_back(u / 0.35)
            elif t < b["inis"]:
                u = clamp((t - b["dusus"]) / 0.45) ** 2
                x, y, s = self.kx, lerp(560, hedef_y, u), 1.0
            else:
                v = t - b["inis"]
                x, y, s = self.kx, hedef_y - (10 * math.sin(math.pi * v / 0.15) if v < 0.15 else 0), 1.0
            if egim:
                r = math.radians(egim)
                dx, dy = x - self.kx, y - self.taban
                x = self.kx + dx * math.cos(r) + dy * math.sin(r)
                y = self.taban - dx * math.sin(r) + dy * math.cos(r)
            yapistir(tv, sp, x, y, s, 1.0, egim)
        ilk = self.bloklar[0]
        if t < ilk["tr"] + 0.2:
            soru_isaretleri(tv, t, [(170, 430), (600, 470), (190, 760), (560, 800)], 1 - clamp((t - ilk["tr"]) / 0.2))
        for b in self.bloklar:
            self.kelime_ciz(tv, tr_buyuk(b["ad"]), b["renk"], 740, 560, t, b["tr"], b["dusus"], 104)
            self.kelime_ciz(tv, b["ing"], KOYU_YAZI, 740, 676, t, b["en"], b["dusus"], 76)
            b["parilti"].ciz(d, t)
        if self.yikilma <= t <= self.yikilma + 1.8:
            self.kelime_ciz(tv, "EYVAH!", (236, 58, 62), W / 2, 700, t, self.yikilma + 0.4, self.yikilma + 1.6, 150)
        self.konfeti.ciz(d, t)
        return tv


@lru_cache(maxsize=64)
def hayvan_sprite(kod, boyut, golge=False):
    im = Image.open(VAR / "emoji" / f"{kod}.png").convert("RGBA")
    im = im.crop(im.getbbox())
    o = boyut / max(im.size)
    im = im.resize((int(im.width * o), int(im.height * o)), Image.LANCZOS)
    if golge:
        a = im.getchannel("A")
        im = Image.new("RGBA", im.size, (34, 30, 64, 255))
        im.putalpha(a)
    return im


class Golge(Sahne):
    baslik = "Bu Kimin Gölgesi?"
    alt_baslik = "Guess the animal!"

    def __init__(self, rng, ses, hayvanlar):
        super().__init__(rng, ses)
        self.hayvanlar = hayvanlar
        self.bg = arka_plan((120, 104, 210), (255, 196, 230), rng=rng).convert("RGBA")
        isik = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(isik).ellipse([110, 440, 950, 1280], fill=(255, 248, 220, 235))
        self.bg.alpha_composite(isik.filter(ImageFilter.GaussianBlur(30)))
        self.baslik_ciz(self.bg)
        self.bg = self.bg.convert("RGB")
        self.boncuk = BoncukDurum(ses, 150, 1530, 0.55)
        self.boncuk.giris = -0.25
        t = 0.0
        self.turlar = []
        for k, h in enumerate(hayvanlar):
            # ilk gölge 0. karede zaten ekrana kayıyor (Shorts'ta ilk 2 saniye kritik)
            r = {"h": h, "giris": t - 0.2 if k == 0 else t}
            ses.efekt(t, "whoosh", 0.7)
            t += 0.25 if k == 0 else 0.45
            soru = "Bu kimin gölgesi?" if k == 0 else ("Peki bu kimin gölgesi?" if k == 1 else "Son soru! Bu kimin gölgesi?")
            t += ses.konus(t, soru) + 0.15
            t += ses.konus(t, h["ipucu"]) + 0.25
            r["sayac"] = t
            for i in range(3):
                ses.efekt(t + i * 0.8, "tik")
            t += 2.4
            r["acilis"] = t
            ses.efekt(t, "tada")
            self.boncuk.zipla.append(t)
            r["parilti"] = Parilti(rng, W / 2, 900, t, (255, 220, 80), 16)
            t += 0.3
            r["tr"] = t
            t += ses.konus(t, f"Bu bir {tr_kucuk(h['ad'])}!") + 0.12
            r["en"] = t
            t += ses.konus(t, h["ing"].capitalize() + "!", "en", boncuk_mu=False) + 0.2
            t += ses.konus(t, h["bilgi"]) + 0.35
            r["cikis"] = t
            ses.efekt(t, "whoosh", 0.6)
            t += 0.4
            self.turlar.append(r)
        self.cikis = t
        ses.efekt(t, "tada")
        self.konfeti = Konfeti(rng, t)
        t += 0.3 + ses.konus(t + 0.3, "Kaç tanesini bildin? Yarın yeni gölgelerle görüşelim!")
        self.T = t + 1.2

    def kare(self, t):
        tv = self.bg.copy()
        d = ImageDraw.Draw(tv)
        for r in self.turlar:
            if not r["giris"] <= t < r["cikis"] + 0.4:
                continue
            kod = r["h"]["kod"]
            giris = ease_out_back((t - r["giris"]) / 0.45)
            x = 530 - (1 - giris) * 700 if t < r["cikis"] else 530 - ease_in_out((t - r["cikis"]) / 0.4) * 1100
            y = 850 + 12 * math.sin(t * 3)
            renkli = clamp((t - r["acilis"]) / 0.25)
            ziplama = 1 + 0.12 * math.sin(math.pi * clamp((t - r["acilis"]) / 0.4))
            if renkli < 1:
                yapistir(tv, hayvan_sprite(kod, 520, True), x, y, ziplama)
            if renkli > 0:
                yapistir(tv, hayvan_sprite(kod, 520), x, y, ziplama, renkli)
            if r["giris"] + 0.45 <= t < r["acilis"]:
                for i, (qx, qy) in enumerate([(170, 560), (880, 640), (190, 1120)]):
                    yapistir(tv, yazi_sprite("?", 120, (255, 140, 30), (255, 255, 255), 12), qx, qy + 15 * math.sin(t * 4 + i), 0.9 + 0.1 * math.sin(t * 6 + i))
            for i in range(3):
                a = r["sayac"] + i * 0.8
                if a <= t < a + 0.8:
                    u = (t - a) / 0.8
                    yapistir(tv, yazi_sprite(str(3 - i), 210, (255, 138, 28), (255, 255, 255), 16), 530, 1310, ease_out_back(u / 0.4), 1 - clamp((u - 0.75) / 0.25))
            self.kelime_ciz(tv, tr_buyuk(r["h"]["ad"]), (236, 58, 62), 560, 1290, t, r["tr"], r["cikis"], 120)
            self.kelime_ciz(tv, r["h"]["ing"].capitalize(), KOYU_YAZI, 560, 1410, t, r["en"], r["cikis"], 82)
            flas = 1 - clamp((t - r["acilis"]) / 0.3) if t >= r["acilis"] else 0
            if flas > 0:
                tv = Image.blend(tv, Image.new("RGB", (W, H), (255, 255, 255)), 0.6 * flas)
                d = ImageDraw.Draw(tv)
            r["parilti"].ciz(d, t)
        if t >= self.cikis:
            for i, r in enumerate(self.turlar):
                g = ease_out_back((t - self.cikis - i * 0.15) / 0.45)
                yapistir(tv, hayvan_sprite(r["h"]["kod"], 250), 230 + i * 290, 850 + 15 * math.sin(t * 4 + i), g)
        self.boncuk.ciz(tv, t, gokkusagi=t > self.cikis)
        self.konfeti.ciz(d, t)
        return tv


# ---------------------------------------------------------------- logo
@lru_cache(maxsize=4)
def logo(boyut=150):
    """Beyaz daire içinde Boncuk: hem YouTube filigranı hem video köşe logosu."""
    S = 4
    n = boyut * S
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, n - 1, n - 1], fill=(255, 255, 255, 235))
    d.ellipse([3 * S, 3 * S, n - 1 - 3 * S, n - 1 - 3 * S], outline=(120, 196, 255, 255), width=4 * S)
    b = boncuk(BONCUK_RENK, False, 0)
    o = n * 0.80 / b.height
    b = b.resize((int(b.width * o), int(b.height * o)), Image.LANCZOS)
    im.paste(b, ((n - b.width) // 2, int(n * 0.07)), b)
    return im.resize((boyut, boyut), Image.LANCZOS)


# ---------------------------------------------------------------- render
ACILIS_KARE = 12  # 0,4 sn


def video_yap(sahne: Sahne, ses: Ses, seed: int, cikti: pathlib.Path, onizleme=False):
    cikti.parent.mkdir(parents=True, exist_ok=True)
    wav = cikti.with_suffix(".wav")
    ses.miksle(sahne.T, seed, wav)
    n = int(sahne.T * FPS)
    olcek = 0.5 if onizleme else 1.0
    cw, ch = int(W * olcek), int(H * olcek)
    cmd = [FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{cw}x{ch}", "-r", str(FPS), "-i", "-",
           "-i", str(wav), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(cikti)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        kare = sahne.kare(f / FPS)
        if f < ACILIS_KARE:  # açılışta hafif "kamera yakınlaşması": ilk karelerde hareket hissi
            z = 1 + 0.08 * (1 - f / ACILIS_KARE) ** 2
            buyuk = kare.resize((int(W * z), int(H * z)), Image.BILINEAR)
            ox, oy = (buyuk.width - W) // 2, (buyuk.height - H) // 2
            kare = buyuk.crop((ox, oy, ox + W, oy + H))
        yapistir(kare, logo(110), 80, 420, 1.0, 0.9)  # köşe logosu (kanal imzası)
        if olcek != 1.0:
            kare = kare.resize((cw, ch), Image.BILINEAR)
        p.stdin.write(kare.tobytes())
        if f % (FPS * 5) == 0:
            print(f"  {f / FPS:5.1f}/{sahne.T:.1f} sn", flush=True)
    p.stdin.close()
    p.wait()
    wav.unlink(missing_ok=True)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg hata verdi")
    return cikti

"""Web sitesinin görsellerini ve sabit verilerini üretir (bir kez ya da karakter değişince çalıştırılır).
Çıktı: site/img/..., site/veri/hayvanlar.json"""
import json
import pathlib
import shutil

from PIL import Image, ImageDraw

import motor
from hayvanlar import HAYVANLAR

SITE = pathlib.Path(__file__).parent.parent / "site"
IMG = SITE / "img"
(IMG / "hayvan").mkdir(parents=True, exist_ok=True)
(SITE / "veri").mkdir(parents=True, exist_ok=True)
(SITE / "fonts").mkdir(parents=True, exist_ok=True)

RENK_ANAHTAR = {"Kırmızı": "red", "Turuncu": "orange", "Sarı": "yellow", "Yeşil": "green", "Mavi": "blue", "Mor": "purple", "Pembe": "pink"}

# Boncuk her renkte
for ad, ing, renk in motor.RENKLER:
    b = motor.boncuk(renk, False, 0)
    b.save(IMG / f"boncuk-{RENK_ANAHTAR[ad]}.png", optimize=True)
motor.boncuk(motor.BONCUK_RENK, False, 0).save(IMG / "boncuk.png", optimize=True)
motor.boncuk(motor.BONCUK_RENK, False, 3).save(IMG / "boncuk-konusuyor.png", optimize=True)
motor.boncuk(motor.BONCUK_RENK, True, 0).save(IMG / "boncuk-mutlu.png", optimize=True)


def ikon(boyut, maskable=False):
    im = Image.new("RGBA", (boyut, boyut), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    if maskable:
        d.rectangle([0, 0, boyut, boyut], fill=(255, 230, 120))
    else:
        d.ellipse([0, 0, boyut - 1, boyut - 1], fill=(255, 230, 120))
    pay = 0.20 if maskable else 0.10
    b = motor.boncuk(motor.BONCUK_RENK, False, 0)
    h = int(boyut * (1 - 2 * pay))
    w = int(h * b.width / b.height)
    b = b.resize((w, h), Image.LANCZOS)
    im.paste(b, ((boyut - w) // 2, int(boyut * pay)), b)
    return im


ikon(192).save(IMG / "ikon-192.png")
ikon(512).save(IMG / "ikon-512.png")
ikon(512, True).save(IMG / "ikon-maskable-512.png")
ikon(180, True).convert("RGB").save(IMG / "apple-touch-icon.png")
ikon(64).save(IMG / "favicon.png")

# Paylaşım görseli (Instagram, WhatsApp vb. bağlantı önizlemesi)
og = Image.new("RGB", (1200, 630), (255, 244, 214))
d = ImageDraw.Draw(og)
for i, (_, _, c) in enumerate(motor.RENKLER[:6]):
    d.rectangle([0, i * 105, 1200, (i + 1) * 105], fill=motor.acik(c, 0.7))
d.rounded_rectangle([60, 60, 1140, 570], 60, fill=(255, 255, 255))
b = motor.boncuk(motor.BONCUK_RENK, False, 2).resize((306, 360), Image.LANCZOS)
og.paste(b, (110, 135), b)
motor.yapistir(og, motor.gokkusagi_yazi("Boncuk Çocuk TV", 92), 760, 255)
motor.yapistir(og, motor.yazi_sprite("Renk ve hayvan oyunları", 54, motor.KOYU_YAZI, (255, 255, 255), 6), 760, 375)
motor.yapistir(og, motor.yazi_sprite("Türkçe + İngilizce", 48, (255, 138, 28), (255, 255, 255), 6), 760, 455)
og.save(IMG / "paylasim.png", optimize=True)

# Hayvan görselleri (Microsoft Fluent Emoji, MIT lisansı)
hayvan_veri = []
for h in HAYVANLAR:
    kaynak = motor.VAR / "emoji" / f"{h['kod']}.png"
    im = Image.open(kaynak).convert("RGBA")
    im = im.crop(im.getbbox())
    im.thumbnail((256, 256), Image.LANCZOS)
    im.save(IMG / "hayvan" / f"{h['kod']}.png", optimize=True)
    hayvan_veri.append({k: h[k] for k in ("kod", "ad", "ing", "ipucu", "bilgi")})
(SITE / "veri" / "hayvanlar.json").write_text(json.dumps(hayvan_veri, ensure_ascii=False, indent=1), encoding="utf-8")

shutil.copy(motor.VAR / "Baloo2.ttf", SITE / "fonts" / "Baloo2.ttf")
print("site görselleri hazır:", len(list(IMG.rglob("*.png"))), "png")

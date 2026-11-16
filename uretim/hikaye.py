"""Boncuk ve Arkadaşları: üç karakterli kısa hikâye bölümleri (Boncuk, kedi Pamuk, bebek Minik).

Her hikâye birkaç "vuruş"tan oluşur: bir karakter konuşur, öncesinde top atma, yürüme, ifade
değiştirme, kelime kartı gibi eylemler olur. Süreler seslendirmenin uzunluğundan hesaplanır.
Hikâye metinleri hikayeler.py dosyasındadır.
"""
from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageDraw

import motor
from motor import (BONCUK_RENK, FPS, H, KOYU_YAZI, W, Konfeti, Parilti, Sahne, acik, clamp, ease_in_out, ease_out_back,
                   koyu, kure, lerp, yapistir, yazi_sprite, zemin_golge)

# Karakter sesleri (edge-tts): Boncuk mevcut ses; Pamuk erkek çocuk sesi; Minik bebek sesi
# 4. değer: sesi örnekleyerek hızlandırıp incelten çarpan (aşırı perde kaydırmadan daha doğal çizgi film sesi)
motor.SESLER.setdefault("pamuk", ("tr-TR-AhmetNeural", "+0%", "+15Hz", 1.18))
motor.SESLER.setdefault("minik", ("tr-TR-EmelNeural", "-12%", "+25Hz", 1.2))

PAMUK_RENK = (250, 246, 240)
TEN = (255, 214, 186)
TULUM = (255, 214, 92)


def _goz(d, p, x, y, r, iris=None, ifade="normal", kapali=False):
    """Büyük, parlak çizgi film gözü. ifade: normal / mutlu (^ ^) / uzgun (iri, nemli)."""
    if kapali or ifade == "mutlu":
        d.arc([p(x - r), p(y - r * 0.6), p(x + r), p(y + r * 1.0)], 200, 340, fill=(40, 30, 50), width=p(8))
        return
    ry = r * 1.18
    d.ellipse([p(x - r), p(y - ry), p(x + r), p(y + ry)], fill=(255, 255, 255), outline=(70, 60, 80), width=p(3))
    if iris:
        d.ellipse([p(x - r * 0.62), p(y - r * 0.55), p(x + r * 0.62), p(y + r * 0.85)], fill=iris)
    d.ellipse([p(x - r * 0.42), p(y - r * 0.3), p(x + r * 0.42), p(y + r * 0.7)], fill=(30, 24, 40))
    d.ellipse([p(x - r * 0.3), p(y - r * 0.25), p(x + r * 0.05), p(y + r * 0.1)], fill=(255, 255, 255))
    d.ellipse([p(x + r * 0.12), p(y + r * 0.35), p(x + r * 0.3), p(y + r * 0.53)], fill=(255, 255, 255))
    if ifade == "uzgun":
        d.line([p(x - r * 0.9), p(y - ry - 8), p(x + r * 0.7), p(y - ry - 22)] if x < 160 else
               [p(x - r * 0.7), p(y - ry - 22), p(x + r * 0.9), p(y - ry - 8)], fill=(70, 50, 60), width=p(6))
        d.ellipse([p(x + r * 0.2), p(y + ry - 4), p(x + r * 0.55), p(y + ry + 26)], fill=(120, 190, 255))


def _agiz(d, p, x, y, agiz, ifade, en=24):
    if ifade == "uzgun" and agiz == 0:
        d.arc([p(x - en), p(y + 4), p(x + en), p(y + 34)], 200, 340, fill=(110, 30, 45), width=p(6))
        return
    if agiz == 0 and ifade != "mutlu":
        d.arc([p(x - en), p(y - 22), p(x + en), p(y + 18)], 25, 155, fill=(110, 30, 45), width=p(6))
        return
    h = [14, 16, 24, 32][agiz] if ifade != "mutlu" or agiz else 22
    d.chord([p(x - en), p(y - h), p(x + en), p(y + h)], 0, 180, fill=(130, 30, 50))
    d.ellipse([p(x - en * 0.5), p(y + h * 0.3), p(x + en * 0.5), p(y + h)], fill=(255, 120, 140))


@lru_cache(maxsize=256)
def pamuk(goz_kapali=False, agiz=0, ifade="normal"):
    """Pamuk: beyaz, yeşil gözlü, pembe kulaklı kedi yavrusu. 320x380 RGBA."""
    S = 3
    im = Image.new("RGBA", (320 * S, 380 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    p = lambda v: int(v * S)  # noqa: E731
    golge = koyu(PAMUK_RENK, 0.22)
    # kuyruk (gövdenin arkasında, yukarı kıvrık)
    nok = [(230 + 60 * math.sin(u * 2.4), 330 - 150 * u + 30 * math.sin(u * 5)) for u in [i / 30 for i in range(31)]]
    d.line([(p(x), p(y)) for x, y in nok], fill=golge, width=p(30), joint="curve")
    d.line([(p(x), p(y)) for x, y in nok], fill=PAMUK_RENK, width=p(22), joint="curve")
    d.ellipse([p(nok[-1][0] - 15), p(nok[-1][1] - 15), p(nok[-1][0] + 15), p(nok[-1][1] + 15)], fill=(200, 200, 210))
    # gövde ve ayaklar
    govde = kure(PAMUK_RENK, 110).resize((p(196), p(176)), Image.LANCZOS)
    im.paste(govde, (p(62), p(192)), govde)
    for x in (110, 210):
        d.ellipse([p(x - 30), p(338), p(x + 30), p(372)], fill=(238, 234, 230), outline=golge, width=p(3))
        for k in (-12, 0, 12):
            d.line([p(x + k), p(348), p(x + k), p(360)], fill=golge, width=p(3))
    # kulaklar (başın arkasında)
    for yon in (-1, 1):
        cx = 160 + yon * 92
        d.polygon([(p(cx - 48), p(118)), (p(cx + yon * 26), p(8)), (p(cx + 48), p(98))], fill=PAMUK_RENK, outline=golge)
        d.polygon([(p(cx - 26), p(104)), (p(cx + yon * 20), p(36)), (p(cx + 28), p(92))], fill=(255, 168, 190))
    # baş
    bas = kure(PAMUK_RENK, 130).resize((p(290), p(232)), Image.LANCZOS)
    im.paste(bas, (p(15), p(36)), bas)
    # alında tekir çizgileri
    for k, x in enumerate((140, 160, 180)):
        d.line([p(x), p(54), p(x + (k - 1) * 4), p(78 + (k == 1) * 8)], fill=(214, 206, 214), width=p(7))
    # yanaklar
    yan = Image.new("RGBA", im.size, (0, 0, 0, 0))
    for x in (78, 242):
        ImageDraw.Draw(yan).ellipse([p(x - 24), p(190), p(x + 24), p(214)], fill=(255, 130, 160, 110))
    im.alpha_composite(yan)
    _goz(d, p, 112, 146, 31, (110, 200, 120), ifade, goz_kapali)
    _goz(d, p, 208, 146, 31, (110, 200, 120), ifade, goz_kapali)
    # burun, ağız, bıyıklar
    d.polygon([(p(150), p(184)), (p(170), p(184)), (p(160), p(196))], fill=(255, 130, 160))
    _agiz(d, p, 160, 210, agiz, ifade, 20)
    for yon in (-1, 1):
        for k, dy in enumerate((-10, 2, 14)):
            d.line([p(160 + yon * 52), p(200 + dy * 0.4), p(160 + yon * 128), p(190 + dy * 1.4)], fill=(160, 150, 165), width=p(3))
    return im.resize((320, 380), Image.LANCZOS)


@lru_cache(maxsize=256)
def minik(goz_kapali=False, agiz=0, ifade="normal"):
    """Minik: sarı tulumlu, tek tutam kıvırcık saçlı bebek. 300x360 RGBA."""
    S = 3
    im = Image.new("RGBA", (300 * S, 360 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    p = lambda v: int(v * S)  # noqa: E731
    # kollar ve ayaklar
    for x in (70, 230):
        d.ellipse([p(x - 26), p(232), p(x + 26), p(290)], fill=TULUM, outline=koyu(TULUM, 0.25), width=p(3))
        d.ellipse([p(x - 20), p(278), p(x + 20), p(312)], fill=TEN)
    for x in (115, 185):
        d.ellipse([p(x - 30), p(320), p(x + 30), p(356)], fill=koyu(TULUM, 0.12))
    # tulum (gövde) + önünde minik kalp
    govde = kure(TULUM, 100).resize((p(172), p(150)), Image.LANCZOS)
    im.paste(govde, (p(64), p(198)), govde)
    kx, ky = 150, 268
    d.ellipse([p(kx - 17), p(ky - 12), p(kx + 1), p(ky + 6)], fill=(255, 120, 150))
    d.ellipse([p(kx - 1), p(ky - 12), p(kx + 17), p(ky + 6)], fill=(255, 120, 150))
    d.polygon([(p(kx - 16), p(ky - 1)), (p(kx + 16), p(ky - 1)), (p(kx), p(ky + 18))], fill=(255, 120, 150))
    # kulaklar
    for x in (28, 272):
        d.ellipse([p(x - 22), p(112), p(x + 22), p(160)], fill=koyu(TEN, 0.08))
    # baş
    bas = kure(TEN, 125).resize((p(256), p(230)), Image.LANCZOS)
    im.paste(bas, (p(22), p(10)), bas)
    # kıvırcık saç tutamı
    d.arc([p(132), p(-4), p(176), p(40)], 160, 420, fill=(140, 90, 50), width=p(8))
    d.arc([p(146), p(10), p(166), p(30)], 180, 450, fill=(140, 90, 50), width=p(6))
    # yanaklar
    yan = Image.new("RGBA", im.size, (0, 0, 0, 0))
    for x in (72, 228):
        ImageDraw.Draw(yan).ellipse([p(x - 26), p(150), p(x + 26), p(178)], fill=(255, 110, 130, 130))
    im.alpha_composite(yan)
    _goz(d, p, 108, 116, 27, (120, 80, 50), ifade, goz_kapali)
    _goz(d, p, 192, 116, 27, (120, 80, 50), ifade, goz_kapali)
    _agiz(d, p, 150, 176, agiz, ifade, 18)
    return im.resize((300, 360), Image.LANCZOS)


def boncuk_ciz(goz_kapali=False, agiz=0, ifade="normal"):
    return motor.boncuk(BONCUK_RENK, goz_kapali or ifade == "mutlu", agiz)


CIZIMLER = {"boncuk": (boncuk_ciz, 340, 400), "pamuk": (pamuk, 320, 380), "minik": (minik, 300, 360)}


class Karakter:
    """Sahnedeki bir karakter: koşma, zıplama, düşme, ifade, konuşurken baş sallama ve ağız hareketi."""

    def __init__(self, ad, ses, x, taban_y, olcek):
        self.ad, self.ses, self.x0, self.taban_y, self.olcek = ad, ses, x, taban_y, olcek
        self.ciz_fn, self.gw, self.gh = CIZIMLER[ad]
        self.hareketler = []  # (t0, t1, x0, x1)
        self.zipla = []
        self.dusmeler = []
        self.ifadeler = [(-9.0, "normal")]
        self.giris = -0.25
        self.faz = {"boncuk": 0.0, "pamuk": 1.1, "minik": 2.2}[ad]

    def x(self, t):
        x = self.x0
        for t0, t1, a, b in self.hareketler:
            if t >= t1:
                x = b
            elif t >= t0:
                return lerp(a, b, ease_in_out((t - t0) / (t1 - t0)))
        return x

    def yuru(self, t, hedef, sure):
        bas = self.x(t)
        self.hareketler.append((t, t + sure, bas, hedef))
        return t + sure

    def kos(self, t, duraklar, adim_suresi):
        """Duraklar arasında hızlıca koşar (kovalamaca)."""
        for hedef in duraklar:
            t = self.yuru(t, hedef, adim_suresi)
        return t

    def ifade(self, t):
        return max((k for k in self.ifadeler if k[0] <= t), key=lambda k: k[0])[1]

    def el(self, t, yukari=0.0):
        """Tuttuğu nesnenin konumu: yüzü kapatmasın diye gövdenin yanında, sahnenin ortasına doğru."""
        x = self.x(t)
        yan = 1 if x < 540 else -1
        return x + yan * self.gw * 0.40 * self.olcek, self.taban_y - (105 + yukari) * self.olcek

    def ciz(self, tv, t):
        a = self.ses.agiz(t, self.ad)
        agiz = 0 if a < 0.12 else (1 if a < 0.4 else (2 if a < 0.7 else 3))
        ifade = self.ifade(t)
        kirp = ((t + 1.5 + self.faz) % 3.4) < 0.13
        sp = self.ciz_fn(kirp, agiz, ifade)
        giris = ease_out_back((t - self.giris) / 0.5)
        hop = 0.0
        for zt in self.zipla:
            u = (t - zt) / 0.42
            if 0 <= u <= 1:
                hop = max(hop, math.sin(math.pi * u))
        x = self.x(t)
        aci = 2.0 * math.sin((t + self.faz) * 2.1)  # hafif sallanma: hiç kimse kıpırtısız durmaz
        if any(t0 <= t < t1 for t0, t1, _, _ in self.hareketler):
            hop = max(hop, 0.45 * abs(math.sin(t * 13)))
            aci += 7 * math.sin(t * 13)
        if a > 0.12:  # konuşurken başını sallar
            hop = max(hop, 0.10 * abs(math.sin(t * 9)))
            aci += 4 * math.sin(t * 7 + self.faz)
        if ifade == "uzgun":  # hıçkırarak ağlama
            hop = max(hop, 0.12 * abs(math.sin(t * 14)))
            x += 4 * math.sin(t * 40)
        alcal = 0.0
        for dt in self.dusmeler:  # tökezleyip yana düşer, sonra kalkar
            u = (t - dt) / 1.1
            if 0 <= u <= 1:
                egim = math.sin(math.pi * min(1, u / 0.35)) if u < 0.35 else (1 if u < 0.7 else 1 - (u - 0.7) / 0.3)
                aci += 75 * egim * (1 if self.x0 < 540 else -1)
                alcal = max(alcal, egim)
        nefes = math.sin((t + self.faz) * 2 * math.pi * 0.9)
        sx = self.olcek * giris * (1 + 0.02 * nefes - 0.05 * hop)
        sy = self.olcek * giris * (1 - 0.02 * nefes + 0.09 * hop)
        yapistir(tv, zemin_golge(), x, self.taban_y - 4, self.olcek * giris * (1 - 0.35 * hop) * self.gw / 340)
        hh = self.gh * sy
        cy = self.taban_y - hh / 2 - hop * 70 * self.olcek + alcal * hh * 0.28
        s = sp.resize((max(1, int(self.gw * sx)), max(1, int(hh))), Image.BILINEAR)
        if abs(aci) > 0.3:
            s = s.rotate(aci, resample=Image.BILINEAR, expand=True)
        tv.paste(s, (int(x - s.width / 2), int(cy - s.height / 2)), s)


class Nesne:
    """Top gibi bir nesne: yaylar çizerek uçar ya da bir karakterin elinde taşınır."""

    def __init__(self, sprite, x, y):
        self.sprite, self.bas = sprite, (x, y)
        self.olaylar = []  # ("yol", t0, t1, a, b, h) / ("tasi", t0, t1, karakter)

    def at(self, t0, sure, hedef, yukseklik):
        self.olaylar.append(("yol", t0, t0 + sure, self.konum(t0), hedef, yukseklik))

    def tasi(self, t0, t1, karakter):
        self.olaylar.append(("tasi", t0, t1, karakter))

    def konum(self, t):
        x, y = self.bas
        for o in self.olaylar:
            t0, t1 = o[1], o[2]
            if t < t0:
                break
            if o[0] == "yol":
                _, _, _, a, b, h = o
                if t >= t1:
                    x, y = b
                    continue
                u = (t - t0) / (t1 - t0)
                return lerp(a[0], b[0], u), lerp(a[1], b[1], u) - h * 4 * u * (1 - u)
            k = o[3]
            if t >= t1:
                x, y = k.el(t1)
                continue
            return k.el(t)
        return x, y

    def ciz(self, tv, t):
        x, y = self.konum(t)
        yapistir(tv, self.sprite, x, y + 6 * math.sin(t * 3), 1.0, 1.0, (t * 220) % 360 if self._ucuyor(t) else 0)

    def _ucuyor(self, t):
        return any(o[0] == "yol" and o[1] <= t < o[2] for o in self.olaylar)


def oda_arka_plani():
    """Sıcak renkli oda: duvar, pencere, halı, ahşap zemin."""
    im = motor.arka_plan((255, 226, 205), (255, 240, 222)).convert("RGBA")
    d = ImageDraw.Draw(im)
    # pencere (Shorts güvenli alanının içinde, başlığın altında)
    d.rounded_rectangle([600, 430, 900, 760], 28, fill=(255, 255, 255))
    d.rounded_rectangle([618, 448, 882, 742], 20, fill=(150, 214, 255))
    d.ellipse([650, 480, 740, 570], fill=(255, 226, 90))
    d.line([750, 448, 750, 742], fill=(255, 255, 255), width=14)
    d.line([618, 595, 882, 595], fill=(255, 255, 255), width=14)
    for x in (575, 905):
        d.rounded_rectangle([x - 34, 410, x + 34, 800], 18, fill=(255, 150, 170))
    # duvarda gökkuşağı resmi
    d.rounded_rectangle([110, 520, 420, 770], 16, fill=(255, 196, 120))
    d.rounded_rectangle([128, 538, 402, 752], 10, fill=(255, 255, 255))
    for i, renk in enumerate([r[2] for r in motor.RENKLER[:6]]):
        r = 118 - i * 15
        d.arc([265 - r, 730 - r, 265 + r, 730 + r], 180, 360, fill=renk, width=15)
    for cx in (160, 370):
        d.ellipse([cx - 32, 700, cx + 32, 740], fill=(235, 240, 250))
    # duvar kenar çizgisi ve ahşap zemin
    zemin = 1330
    d.rectangle([0, zemin, W, H], fill=(214, 160, 110))
    for y in range(zemin + 40, H, 60):
        d.line([0, y, W, y], fill=(196, 142, 96), width=4)
    d.rectangle([0, zemin - 18, W, zemin], fill=(255, 255, 255))
    # halı
    d.ellipse([60, 1370, 1020, 1520], fill=(150, 200, 255))
    d.ellipse([110, 1385, 970, 1505], fill=(180, 220, 255))
    return im


class Hikaye(Sahne):
    baslik = "Boncuk ve Arkadaşları"

    def __init__(self, rng, ses, senaryo):
        super().__init__(rng, ses)
        self.senaryo = senaryo
        self.alt_baslik = senaryo["baslik"]
        self.bg = oda_arka_plani()
        motor.yapistir(self.bg, motor.gokkusagi_yazi(self.baslik, 84), W / 2, 205)
        motor.yapistir(self.bg, yazi_sprite(self.alt_baslik, 62, KOYU_YAZI, (255, 255, 255), 10), W / 2, 312)
        self.bg = self.bg.convert("RGB")
        taban = 1440
        self.k = {
            "minik": Karakter("minik", ses, 195, taban, 1.08),
            "pamuk": Karakter("pamuk", ses, 500, taban, 1.08),
            "boncuk": Karakter("boncuk", ses, 800, taban, 0.94),
        }
        for ad, ayar in senaryo.get("baslangic", {}).items():
            if "x" in ayar:
                self.k[ad].x0 = ayar["x"]
        top = senaryo.get("top")
        self.top = None
        if top:
            self.top = Nesne(kure(top["renk"], 52), *self._yer(top["yer"], 0.0, 0))
        self.kartlar, self.parilti, self.kamera = [], [], []
        self.konfeti = None
        t = 0.0
        for v in senaryo["vuruslar"]:
            t = self._vurus(t, v)
        self.cikis = t
        self.T = t + 0.9

    def _yer(self, yer, t, yukari=0):
        if isinstance(yer, str):
            return self.k[yer].el(t, yukari)
        return tuple(yer)

    def _vurus(self, t, v):
        """Bir vuruş: eylemler konuşmayla birlikte başlar; koşma/atma gibi uzun eylemler konuşma sırasında sürer."""
        ses = self.ses
        bekle = 0.0
        at_bitis = t
        for ad in v.get("zipla", []):
            self.k[ad].zipla.append(t)
            ses.efekt(t, "boing", 0.5)
        for ad, ifade in v.get("ifade", {}).items():
            self.k[ad].ifadeler.append((t, ifade))
        if "yuru" in v:
            ad, hedef, sure = v["yuru"]
            self.k[ad].yuru(t, hedef, sure)
            ses.efekt(t, "whoosh", 0.5)
            bekle = max(bekle, sure * 0.6)
        if "at" in v and self.top:
            kimden, kime, yukseklik = v["at"]
            sure = 0.6 if yukseklik > 100 else 0.35
            self.top.at(t, sure, self._yer(kime, t + sure), yukseklik)
            ses.efekt(t, "whoosh", 0.6)
            ses.efekt(t + sure, "boing", 0.8)
            if isinstance(kime, str):
                self.k[kime].zipla.append(t + sure)
            bekle = max(bekle, sure * 0.8)
            at_bitis = t + sure
        if "kos" in v:  # (karakter, [duraklar], adım süresi, topu_tasir)
            ad, duraklar, adim, *tasir = v["kos"]
            kb = max(t + bekle, at_bitis)  # top eline ulaştıktan sonra koşmaya başlar
            bitis = self.k[ad].kos(kb, duraklar, adim)
            if tasir and tasir[0] and self.top:
                self.top.tasi(kb, bitis, self.k[ad])
            for i in range(len(duraklar)):
                ses.efekt(kb + i * adim, "whoosh", 0.45)
            self._kos_bitis = bitis
        if "dus" in v:
            ad = v["dus"]
            self.k[ad].dusmeler.append(t)
            ses.efekt(t, "kayma", 0.7)
            ses.efekt(t + 0.38, "thud", 0.9)
            bekle = max(bekle, 0.5)
        if "yakin" in v:  # kamerayı bir karaktere yaklaştır (süre = bu vuruşun konuşması)
            self._yakin = (t, v["yakin"])
        if "efekt" in v:
            ses.efekt(t, v["efekt"])
        t += bekle
        if "kart" in v:
            tr, en, renk = v["kart"]
            ses.efekt(t, "pop")
            kart = {"tr": tr, "en": en, "renk": tuple(renk), "bas": t + 0.05}
            d1 = ses.konus(t + 0.1, f"{tr}!", kim="boncuk")
            kart["en_bas"] = t + 0.1 + d1 + 0.05
            d2 = ses.konus(kart["en_bas"], f"{en}!", "en", boncuk_mu=False)
            kart["bit"] = kart["en_bas"] + d2 + 0.35
            self.kartlar.append(kart)
            self.parilti.append(Parilti(self.rng, W / 2, 760, t + 0.05, kart["renk"], 14))
            self.kamera.append((t, kart["bit"], 1.12, W / 2, 1000))
            t = kart["bit"]
        if v.get("konfeti"):
            ses.efekt(t, "tada")
            self.konfeti = Konfeti(self.rng, t)
            for k in self.k.values():
                k.zipla += [t + 0.05, t + 0.55]
        if "soz" in v:
            kim, metin = v["kim"], v["soz"]
            dil = "tr" if kim == "boncuk" else kim
            t += 0.05
            t += ses.konus(t, metin, dil, kim=kim) + v.get("ara", 0.1)
        if getattr(self, "_kos_bitis", None):
            t = max(t, self._kos_bitis + 0.05)
            self._kos_bitis = None
        if getattr(self, "_yakin", None):
            t0, ad = self._yakin
            k = self.k[ad]
            self.kamera.append((t0, t, 1.32, k.x(t0), k.taban_y - k.gh * k.olcek * 0.55))
            self._yakin = None
        return t

    def _kamera(self, t):
        z, cx, cy = 1.0, W / 2, H / 2
        for t0, t1, zz, x, y in self.kamera:
            if t0 <= t < t1 + 0.3:
                u = min(clamp((t - t0) / 0.3), 1 - clamp((t - t1) / 0.3))
                u = ease_in_out(u)
                z, cx, cy = lerp(1, zz, u), lerp(W / 2, x, u), lerp(H / 2, y, u)
        return z, cx, cy

    def kare(self, t):
        tv = self.bg.copy()
        d = ImageDraw.Draw(tv)
        sira = sorted(self.k.values(), key=lambda k: k.taban_y)
        for k in sira:
            k.ciz(tv, t)
        if self.top:
            self.top.ciz(tv, t)
        for kart in self.kartlar:
            self.kelime_ciz(tv, motor.tr_buyuk(kart["tr"]), kart["renk"], W / 2, 760, t, kart["bas"], kart["bit"], 140)
            self.kelime_ciz(tv, kart["en"], KOYU_YAZI, W / 2, 890, t, kart["en_bas"], kart["bit"], 90)
        for p in self.parilti:
            p.ciz(d, t)
        if self.konfeti:
            self.konfeti.ciz(d, t)
        z, cx, cy = self._kamera(t)
        if z > 1.001:
            gw, gh = W / z, H / z
            x0 = min(max(cx - gw / 2, 0), W - gw)
            y0 = min(max(cy - gh / 2, 0), H - gh)
            tv = tv.crop((int(x0), int(y0), int(x0 + gw), int(y0 + gh))).resize((W, H), Image.BILINEAR)
        return tv

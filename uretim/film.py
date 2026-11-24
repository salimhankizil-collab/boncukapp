"""Resimli masal filmi motoru (yatay 1920x1080).

Her sahne tek bir görsel üzerinde oynar:
  - kamera konuşana göre kadrajdan kadraja kayar ve yavaşça yakınlaşır,
  - "kukla" bölgeleri resmi yerinde esneterek karakterleri hareket ettirir
    (baş sallama, zıplama, el sallama, sarılırken sallanma, hıçkırık, kanat çırpma...),
  - efektler (toz zerreleri, uçuşan yapraklar, pırıltı, lamba ışığı), uçan kuş görseli ve yazılar eklenir,
  - konuşmalar motor.seslendir ile (ElevenLabs ya da Edge), ses efektleri burada üretilir.
Film verisi (sahneler, satırlar) ayrı bir dosyada durur; bkz. filmler/ klasörü.
"""
from __future__ import annotations

import math
import pathlib
import subprocess
import wave

import cv2
import numpy as np
from PIL import Image

import motor

W, H, FPS, SR = 1920, 1080, 30, motor.SR


# ---------------------------------------------------------------- ses efektleri
def _t(d):
    return np.arange(int(d * SR)) / SR


def _kahverengi_gurultu(n, seed):
    g = np.cumsum(np.random.default_rng(seed).standard_normal(n))
    g -= np.convolve(g, np.ones(2000) / 2000, mode="same")
    return g / (np.abs(g).max() + 1e-6)


def sfx(ad):
    if ad == "zil":
        t = _t(1.3)
        out = np.zeros_like(t)
        for bas, fr in ((0.0, 880.0), (0.45, 698.5)):
            u = np.clip(t - bas, 0, None)
            out += (t >= bas) * 0.35 * (np.sin(2 * np.pi * fr * u) + 0.4 * np.sin(4 * np.pi * fr * u)) * np.exp(-u * 3)
        return out
    if ad in ("cik", "cik_uzun"):
        adet = 3 if ad == "cik" else 6
        out = np.zeros(int((0.16 * adet + 0.3) * SR))
        rng = np.random.default_rng(adet)
        for i in range(adet):
            t = _t(0.075)
            f0 = rng.uniform(3200, 3900)
            f = f0 + 1600 * np.sin(np.pi * t / 0.075)
            w = 0.32 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.075) ** 2
            s = int((i * 0.16 + rng.uniform(0, 0.03)) * SR)
            out[s:s + len(w)] += w
        return out
    if ad in ("ruzgar", "hisir", "vuu"):
        d = {"ruzgar": 3.2, "hisir": 1.6, "vuu": 2.4}[ad]
        t = _t(d)
        zarf = np.sin(np.pi * t / d) ** 1.5
        g = _kahverengi_gurultu(len(t), 5)
        if ad == "hisir":  # yaprak hışırtısı: daha tiz, titrek
            g = np.diff(np.concatenate([[0], g])) * 6
            zarf *= 0.6 + 0.4 * np.sin(2 * np.pi * 7 * t)
            return 0.35 * g * zarf
        islik = np.sin(2 * np.pi * np.cumsum(320 + 180 * np.sin(np.pi * t / d) + 25 * np.sin(2 * np.pi * 5 * t)) / SR)
        return (0.55 * g + (0.12 if ad == "vuu" else 0.06) * islik) * zarf
    if ad == "puf":
        t = _t(0.45)
        return 0.6 * np.sin(2 * np.pi * (140 - 80 * t) * t) * np.exp(-t * 9) + 0.15 * _kahverengi_gurultu(len(t), 2) * np.exp(-t * 6)
    if ad == "sihir":  # masal geçişi: tatlı çan pırıltısı
        out = np.zeros(int(1.8 * SR))
        rng = np.random.default_rng(9)
        for i in range(12):
            fr = rng.choice([1568, 1760, 2093, 2349, 2637, 3136])
            t = _t(0.9)
            w = 0.12 * np.sin(2 * np.pi * fr * t) * np.exp(-t * 5)
            s = int(i * 0.08 * SR)
            out[s:s + len(w)] += w[: len(out) - s]
        return out
    return motor.efekt(ad)


# ---------------------------------------------------------------- kukla bölgeleri
class Bolge:
    """Görselin bir bölgesini yerinde esneterek hareket ettirir.

    cx, cy, rx, ry : etki elipsi (kaynak görsel koordinatları)
    ex, ey         : dönme ekseni (ör. boyun, ayaklar)
    tur            : bas / govde / zipla / el / sallan / ucus / hickir / kanat / kuyruk / yuzme / yaprak / pat
    kim            : konuşmasına tepki verilen karakter (bas, zipla için)
    kosul          : sadece bu durum açıkken hareket eder (ör. "agla")
    """

    def __init__(self, cx, cy, rx, ry, ex, ey, tur, kim=None, guc=1.0, frek=1.0, faz=0.0, kosul=None):
        self.cx, self.cy, self.rx, self.ry, self.ex, self.ey = cx, cy, rx, ry, ex, ey
        self.tur, self.kim, self.guc, self.frek, self.faz, self.kosul = tur, kim, guc, frek, faz, kosul

    def hareket(self, t, film):
        """(açı°, dx, dy, ölçek) döndürür."""
        if self.kosul and not film.durum(self.kosul, t):
            return 0.0, 0.0, 0.0, 1.0
        g, f, p = self.guc, self.frek, self.faz
        a = film.agiz(self.kim, t) if self.kim else 0.0
        tur = self.tur
        if tur == "bas":
            return g * (1.5 * math.sin(1.3 * t + p) + 5 * a * math.sin(8 * t + p)), 0.0, -4 * g * a * abs(math.sin(9 * t)), 1.0
        if tur == "govde":
            return 0.0, 0.0, 0.0, 1 + 0.008 * g * math.sin(2 * math.pi * 0.27 * t + p)
        if tur == "zipla":
            heyecan = 1.0 if a > 0.1 else 0.45
            return 2 * math.sin(3 * t + p), 0.0, -12 * g * heyecan * abs(math.sin(5.2 * f * t + p)), 1.0
        if tur == "el":
            s = math.sin(9 * f * t + p)
            return 12 * g * s, 0.0, -8 * g * abs(s), 1.0
        if tur == "sallan":
            return 2.5 * g * math.sin(1.7 * f * t + p), 0.0, 0.0, 1.0
        if tur == "ucus":
            return 1.5 * g * math.sin(1.2 * f * t + p), 0.0, 14 * g * math.sin(1.6 * f * t + p), 1.0
        if tur == "hickir":
            return 0.0, 3 * g * math.sin(40 * t), -6 * g * abs(math.sin(14 * t)), 1.0
        if tur == "kanat":
            return 0.0, 0.0, 0.0, 1 + 0.06 * g * math.sin(20 * f * t + p)
        if tur == "kuyruk":
            return 12 * g * math.sin(4 * f * t + p), 0.0, 0.0, 1.0
        if tur == "yuzme":
            return 2 * math.sin(1.6 * t + p), 18 * g * math.sin(0.8 * f * t + p), 0.0, 1.0
        if tur == "yaprak":
            return 1.2 * g * math.sin(0.9 * f * t + p), 5 * g * math.sin(0.7 * f * t + p), 0.0, 1.0
        if tur == "pat":
            return 0.0, 0.0, 10 * g * math.sin(6 * f * t + p), 1.0
        raise ValueError(tur)


# ---------------------------------------------------------------- sahne
class Sahne:
    def __init__(self, veri, sprite_klasoru):
        self.v = veri
        self.kaynak = cv2.cvtColor(cv2.imread(str(veri["gorsel"])), cv2.COLOR_BGR2RGB)
        self.gh, self.gw = self.kaynak.shape[:2]
        self.kadrajlar = {ad: self._169(k) for ad, k in veri["kadrajlar"].items()}
        self.bolgeler = [Bolge(*b[:7], **(b[7] if len(b) > 7 else {})) for b in veri.get("bolgeler", [])]
        self.efektler = veri.get("efektler", [])
        self.sprite_klasoru = sprite_klasoru
        self.ses = motor.Ses()
        self.cekimler, self.durumlar, self.kuslar, self.yazilar = [], {}, [], []
        self.efekt_sesleri = []
        self._zaman_cizelgesi()

    def _169(self, k):
        """Kadrajı 16:9'a getirir ve görselin içinde tutar."""
        x0, y0, x1, y1 = k
        w, h = x1 - x0, y1 - y0
        if w / h > 16 / 9:
            h = w * 9 / 16
        else:
            w = h * 16 / 9
        w, h = min(w, self.gw), min(h, self.gh)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        cx = min(max(cx, w / 2), self.gw - w / 2)
        cy = min(max(cy, h / 2), self.gh - h / 2)
        return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2

    def _zaman_cizelgesi(self):
        t = 0.4
        for s in self.v["satirlar"]:
            if "k" in s:
                self.cekimler.append((t, self.kadrajlar[s["k"]]))
            for ad, acik in s.get("durum", {}).items():
                self.durumlar.setdefault(ad, []).append((t, acik))
            if "kus" in s:
                k = s["kus"]
                self.kuslar.append({"t0": t, "t1": t + k["sure"], "yol": k["yol"], "boyut": k.get("boyut", 90),
                                    "kon": k.get("kon", False)})
            if "yazi" in s:
                y = s["yazi"]
                self.yazilar.append({"t0": t, "t1": t + y["sure"], "metin": y["metin"], "y": y.get("y", 160),
                                     "boyut": y.get("boyut", 96), "gokkusagi": y.get("gokkusagi", True)})
            if "sfx" in s:
                w = sfx(s["sfx"]).astype(np.float32)
                self.ses.efektler.append((t, w * s.get("seviye", 1.0)))
                if s.get("bekle", "kim" not in s):  # konuşmayla aynı satırdaysa ses efekti konuşmanın altında çalar
                    t += len(w) / SR * s.get("oran", 0.85)
            if "kim" in s:
                t += self.ses.konus(t, s["s"], s.get("ses", s["kim"]), kim=s["kim"]) + s.get("ara", 0.4)
            if "sus" in s:
                t += s["sus"]
        self.T = t + self.v.get("son_bekleme", 1.0)

    # --- film bağlamı (Bolge.hareket için)
    def agiz(self, kim, t):
        return self.ses.agiz(t, kim)

    def durum(self, ad, t):
        acik = False
        for zt, d in self.durumlar.get(ad, []):
            if zt <= t:
                acik = d
        return acik

    # --- kamera
    def kadraj(self, t):
        if not self.cekimler:
            x0, y0, x1, y1 = self.kadrajlar.get("genis", (0, 0, self.gw, self.gh))
            return x0, y0, x1 - x0, y1 - y0
        i = max(k for k, (t0, _) in enumerate(self.cekimler) if t0 <= t or k == 0)
        t0, b = self.cekimler[i]
        onceki = self.cekimler[i - 1][1] if i else b
        u = min(1.0, max(0.0, (t - t0) / 0.8))
        u = u * u * (3 - 2 * u)
        kutu = [a + (c - a) * u for a, c in zip(onceki, b)]
        t1 = self.cekimler[i + 1][0] if i + 1 < len(self.cekimler) else self.T
        z = 1 - 0.035 * min(1.0, (t - t0) / max(0.1, t1 - t0))
        cx, cy = (kutu[0] + kutu[2]) / 2, (kutu[1] + kutu[3]) / 2
        w, h = (kutu[2] - kutu[0]) * z, (kutu[3] - kutu[1]) * z
        return cx - w / 2, cy - h / 2, w, h

    # --- çizim
    def kare(self, t, gx, gy):
        x0, y0, kw, kh = self.kadraj(t)
        sx, sy = kw / W, kh / H
        px = x0 + gx * sx
        py = y0 + gy * sy
        dx = np.zeros_like(px)
        dy = np.zeros_like(py)
        for b in self.bolgeler:
            aci, tx, ty, olc = b.hareket(t, self)
            if abs(aci) < 0.01 and abs(tx) < 0.01 and abs(ty) < 0.01 and abs(olc - 1) < 1e-4:
                continue
            u0, u1 = int(max(0, (b.cx - b.rx - x0) / sx)), int(min(W, (b.cx + b.rx - x0) / sx + 1))
            v0, v1 = int(max(0, (b.cy - b.ry - y0) / sy)), int(min(H, (b.cy + b.ry - y0) / sy + 1))
            if u0 >= u1 or v0 >= v1:
                continue
            bx, by = px[v0:v1, u0:u1], py[v0:v1, u0:u1]
            w = np.clip(1 - ((bx - b.cx) / b.rx) ** 2 - ((by - b.cy) / b.ry) ** 2, 0, 1) ** 2
            a = math.radians(aci)
            ca, sa = math.cos(a), math.sin(a)
            qx, qy = bx - b.ex, by - b.ey
            dx[v0:v1, u0:u1] += w * (b.ex + olc * (ca * qx - sa * qy) + tx - bx)
            dy[v0:v1, u0:u1] += w * (b.ey + olc * (sa * qx + ca * qy) + ty - by)
        out = cv2.remap(self.kaynak, (px - dx).astype(np.float32), (py - dy).astype(np.float32),
                        cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        donustur = (x0, y0, sx, sy)
        for e in self.efektler:
            out = efekt_ciz(out, e, t, donustur)
        for k in self.kuslar:
            if k["t0"] <= t < k["t1"] + (60 if k["kon"] else 0):
                out = kus_ciz(out, k, t, donustur, self.sprite_klasoru)
        for y in self.yazilar:
            if y["t0"] <= t < y["t1"]:
                out = yazi_ciz(out, y, t)
        return out


# ---------------------------------------------------------------- efektler, kuş, yazı
def _ekrana(x, y, d):
    x0, y0, sx, sy = d
    return (x - x0) / sx, (y - y0) / sy


def efekt_ciz(out, e, t, d):
    tur = e[0]
    x0, y0, sx, sy = d
    if tur == "toz":  # ışıkta uçuşan toz zerreleri: ("toz", (x0, y0, x1, y1), renk)
        bx0, by0, bx1, by1 = e[1]
        renk = np.array(e[2] if len(e) > 2 else (255, 240, 200), np.float32)
        rng = np.random.default_rng(3)
        katman = np.zeros(out.shape[:2], np.float32)
        for _ in range(60):
            zx, zy = rng.uniform(bx0, bx1), rng.uniform(by0, by1)
            r, faz, hiz = rng.uniform(1.5, 4), rng.uniform(0, 6.28), rng.uniform(4, 12)
            x = zx + 25 * math.sin(t * 0.4 + faz)
            y = by0 + (zy - by0 - t * hiz) % (by1 - by0)
            ox, oy = _ekrana(x, y, d)
            if 0 <= ox < W and 0 <= oy < H:
                cv2.circle(katman, (int(ox), int(oy)), max(1, int(r / sx)), 1.0, -1, cv2.LINE_AA)
        katman = cv2.GaussianBlur(katman, (0, 0), 2.5) * (0.5 + 0.25 * math.sin(t * 1.3))
        return np.clip(out + katman[..., None] * renk * 0.6, 0, 255).astype(np.uint8)
    if tur == "parilti":  # sihirli pırıltılar: ("parilti", kutu)
        bx0, by0, bx1, by1 = e[1]
        rng = np.random.default_rng(7)
        katman = np.zeros(out.shape[:2], np.float32)
        for _ in range(40):
            x, y = rng.uniform(bx0, bx1), rng.uniform(by0, by1)
            faz, hiz = rng.uniform(0, 6.28), rng.uniform(1.5, 3.5)
            p = max(0.0, math.sin(t * hiz + faz)) ** 3
            if p < 0.05:
                continue
            ox, oy = _ekrana(x, y, d)
            if 0 <= ox < W and 0 <= oy < H:
                L = int(6 + 16 * p)
                cv2.line(katman, (int(ox) - L, int(oy)), (int(ox) + L, int(oy)), p, 2, cv2.LINE_AA)
                cv2.line(katman, (int(ox), int(oy) - L), (int(ox), int(oy) + L), p, 2, cv2.LINE_AA)
                cv2.circle(katman, (int(ox), int(oy)), 3, p, -1, cv2.LINE_AA)
        katman = cv2.GaussianBlur(katman, (0, 0), 1.2)
        return np.clip(out + katman[..., None] * np.array([255, 245, 210], np.float32), 0, 255).astype(np.uint8)
    if tur == "isik":  # nabız gibi atan sıcak ışık: ("isik", (x, y, yarıçap), renk)
        x, y, r = e[1]
        renk = np.array(e[2] if len(e) > 2 else (255, 200, 120), np.float32)
        ox, oy = _ekrana(x, y, d)
        rr = r / sx
        yy, xx = np.ogrid[:H, :W]
        g = np.exp(-(((xx - ox) ** 2 + (yy - oy) ** 2) / (2 * rr * rr))).astype(np.float32)
        g *= 0.22 + 0.06 * math.sin(t * 2.1)
        return np.clip(out + g[..., None] * renk, 0, 255).astype(np.uint8)
    if tur == "yaprak":  # rüzgârda uçuşan yapraklar (ekran üzerinde)
        rng = np.random.default_rng(11)
        for _ in range(int(e[1]) if len(e) > 1 else 18):
            y0_, hiz, faz, boy = rng.uniform(-100, H), rng.uniform(250, 520), rng.uniform(0, 100), int(rng.uniform(14, 26))
            x = (faz * 37 + t * hiz) % (W + 200) - 100
            y = y0_ + 60 * math.sin(t * 2 + faz) + 0.25 * x
            aci = (t * 200 + faz * 40) % 360
            renk = (70 + int(faz) % 60, 170, 60)
            cv2.ellipse(out, (int(x), int(y) % (H + 100) - 50), (boy, boy // 2), aci, 0, 360, renk, -1, cv2.LINE_AA)
            cv2.ellipse(out, (int(x), int(y) % (H + 100) - 50), (boy, boy // 2), aci, 0, 360, (40, 120, 40), 2, cv2.LINE_AA)
        return out
    raise ValueError(tur)


_SPRITE = {}


def _sprite(yol, boyut):
    anahtar = (str(yol), boyut)
    if anahtar not in _SPRITE:
        im = Image.open(yol).convert("RGBA")
        o = boyut / max(im.size)
        _SPRITE[anahtar] = np.array(im.resize((max(1, int(im.width * o)), max(1, int(im.height * o))), Image.LANCZOS))
    return _SPRITE[anahtar]


def _yapistir(out, sp, cx, cy):
    h, w = sp.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    ax0, ay0, ax1, ay1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if ax0 >= ax1 or ay0 >= ay1:
        return out
    parca = sp[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0]
    a = parca[..., 3:4].astype(np.float32) / 255
    out[ay0:ay1, ax0:ax1] = (out[ay0:ay1, ax0:ax1] * (1 - a) + parca[..., :3] * a).astype(np.uint8)
    return out


def kus_ciz(out, k, t, d, klasor):
    """Serçe görseli yol boyunca uçar (kanat çırpma = dikey ezilme); kon=True ise yolun sonunda kalır."""
    yol = k["yol"]
    u = min(1.0, (t - k["t0"]) / max(0.01, k["t1"] - k["t0"]))
    u = u * u * (3 - 2 * u)
    n = len(yol) - 1
    i = min(int(u * n), n - 1)
    f = u * n - i
    x = yol[i][0] + (yol[i + 1][0] - yol[i][0]) * f
    y = yol[i][1] + (yol[i + 1][1] - yol[i][1]) * f - 25 * math.sin(math.pi * f) * (u < 1)
    ucuyor = u < 1
    ox, oy = _ekrana(x, y, d)
    boy = int(k["boyut"] / d[2])
    sp = _sprite(klasor / "serce.png", max(10, boy))
    if yol[min(i + 1, n)][0] < yol[i][0]:
        sp = sp[:, ::-1]
    if ucuyor:
        ez = 0.65 + 0.35 * abs(math.sin(t * 22))
        sp = cv2.resize(sp, (sp.shape[1], max(4, int(sp.shape[0] * ez))))
    else:
        oy += -6 * abs(math.sin(t * 3))
    return _yapistir(out, sp, ox, oy)


def yazi_ciz(out, y, t):
    sp = motor.gokkusagi_yazi(y["metin"], y["boyut"]) if y["gokkusagi"] else \
        motor.yazi_sprite(y["metin"], y["boyut"], motor.KOYU_YAZI, (255, 255, 255), 10)
    sp = np.array(sp)
    u = min(1.0, (t - y["t0"]) / 0.4, (y["t1"] - t) / 0.4)
    sp = sp.copy()
    sp[..., 3] = (sp[..., 3] * max(0.0, u)).astype(np.uint8)
    return _yapistir(out, sp, W / 2, y["y"])


# ---------------------------------------------------------------- çıktı
def _miksle(sahne, yol, muzik_seed, muzik_seviye):
    T, ses = sahne.T, sahne.ses
    n = int(T * SR)
    konusma = np.zeros(n, np.float32)
    fx = np.zeros(n, np.float32)
    for hedef, liste in ((konusma, ses.konusma), (fx, ses.efektler)):
        for t, s in liste:
            i = int(t * SR)
            if i < n:
                hedef[i:i + len(s)] += s[: n - i]
    mix = konusma + fx * 0.8
    if muzik_seed is not None and muzik_seviye > 0:
        m = motor.muzik(T, muzik_seed)[:n]
        m = np.pad(m, (0, n - len(m)))
        c = np.concatenate([[0.0], np.cumsum(np.abs(konusma), dtype=np.float64)])
        k = 4410
        duck = np.zeros(n, np.float32)
        duck[k // 2: k // 2 + n - k + 1] = (c[k:] - c[:-k]) / k
        duck = np.clip(duck / (duck.max() + 1e-6) * 3, 0, 1)
        mix = mix + m * muzik_seviye * (1 - 0.65 * duck)
    mix = mix / (np.abs(mix).max() + 1e-6) * 0.9
    with wave.open(str(yol), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((mix * 32767).astype(np.int16).tobytes())


def sahne_yap(veri, cikti, sprite_klasoru, onizleme=False):
    sahne = Sahne(veri, sprite_klasoru)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    wav = cikti.with_suffix(".wav")
    _miksle(sahne, wav, veri.get("muzik", 21), veri.get("muzik_seviye", 0.3))
    olcek = 0.5 if onizleme else 1.0
    ow, oh = int(W * olcek), int(H * olcek)
    cmd = [motor.FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ow}x{oh}", "-r", str(FPS),
           "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart", str(cikti)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    gecis = veri.get("gecis", "siyah")
    renk = 255 if gecis == "beyaz" else 0
    for f in range(int(sahne.T * FPS)):
        t = f / FPS
        out = sahne.kare(t, gx, gy)
        a = min(1.0, t / 0.6, (sahne.T - t) / 0.6)
        if a < 1:
            out = (out * max(0.0, a) + renk * (1 - max(0.0, a))).astype(np.uint8)
        if olcek != 1.0:
            out = cv2.resize(out, (ow, oh), interpolation=cv2.INTER_AREA)
        p.stdin.write(out.tobytes())
    p.stdin.close()
    p.wait()
    wav.unlink(missing_ok=True)
    if p.returncode:
        raise RuntimeError("ffmpeg hata verdi")
    return sahne.T


def birlestir(parcalar, cikti):
    liste = cikti.with_suffix(".txt")
    liste.write_text("".join(f"file '{pathlib.Path(p).resolve().as_posix()}'\n" for p in parcalar), encoding="utf-8")
    subprocess.run([motor.FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(liste),
                    "-c", "copy", "-movflags", "+faststart", str(cikti)], check=True)
    liste.unlink(missing_ok=True)
    return cikti

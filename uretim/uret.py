"""Sıradaki bölümleri üretir.

Kullanım:
    python uret.py              -> sıradaki 1 bölümü üretir
    python uret.py --adet 7     -> bir haftalık (7) bölüm üretir
    python uret.py --tur golge  -> türü elle seç (toplar / kule / golge)
"""
import argparse
import json
import pathlib

import numpy as np

import motor
from hayvanlar import HAYVANLAR

KOK = pathlib.Path(__file__).parent
DURUM = KOK / "durum.json"
CIKTI = KOK.parent / "videolar"
SIRA = ["toplar", "golge", "kule"]  # türler sırayla döner

# Açıklamanın sonuna hashtag olarak eklenir (Shorts yüklemede ayrı etiket alanı yok).
# Toplam 15'i geçmesin: YouTube çok fazla etiketi spam sayar.
ETIKETLER_ORTAK = ["çocukvideoları", "okulöncesi", "eğiticivideo", "çocuklariçiningilizce", "bebekvideoları",
                   "BoncukÇocukTV", "shorts"]


def durum_oku():
    if DURUM.exists():
        return json.loads(DURUM.read_text(encoding="utf-8"))
    return {"bolum": 0, "kullanilan_hayvanlar": []}


def hayvan_sec(rng, durum):
    kalan = [h for h in HAYVANLAR if h["kod"] not in durum["kullanilan_hayvanlar"]]
    if len(kalan) < 3:
        durum["kullanilan_hayvanlar"] = []
        kalan = list(HAYVANLAR)
    secilen = [kalan[i] for i in rng.choice(len(kalan), 3, replace=False)]
    durum["kullanilan_hayvanlar"] += [h["kod"] for h in secilen]
    return secilen


def bilgi_yaz(klasor, tur, no, sahne):
    if tur == "toplar":
        renkler = [f"{o['ad']} ({o['ing']})" for o in sahne.toplar]
        baslik = "Renkleri Öğrenelim! 🔴🟠🟡🟢🔵🟣 Topları Bardaklara Koy | Boncuk #shorts"
        aciklama = ("Boncuk ile renkli topları aynı renkteki bardaklara koyuyoruz! Hem Türkçe hem İngilizce renkleri öğreniyoruz.\n\n"
                    "Bu bölümdeki renkler: " + ", ".join(renkler))
        etiket = ["renkleriöğreniyorum", "renkler", "learncolors", "colorsforkids"]
    elif tur == "kule":
        renkler = [f"{b['ad']} ({b['ing']})" for b in sahne.bloklar]
        baslik = "Renkli Kule! 🟥🟧🟨🟩🟦🟪 Eyvah, Kule Yıkıldı! | Renkleri Öğren | Boncuk #shorts"
        aciklama = ("Boncuk ile renkli bloklardan kocaman bir kule yapıyoruz. Ama eyvah! Hem Türkçe hem İngilizce renkleri öğreniyoruz.\n\n"
                    "Bu bölümdeki renkler: " + ", ".join(renkler))
        etiket = ["renkleriöğreniyorum", "renklikule", "learncolors", "blocksforkids"]
    else:
        adlar = [f"{h['ad']} ({h['ing']})" for h in sahne.hayvanlar]
        baslik = "Bu Kimin Gölgesi? 🔦🤔 Hayvanları Tahmin Et! | Boncuk #shorts"
        aciklama = ("Gölgeye bak, 3-2-1 say ve hangi hayvan olduğunu tahmin et! Her hayvanın İngilizcesini ve ilginç bir bilgisini öğreniyoruz.\n\n"
                    "Bu bölümdeki hayvanlar (cevaplar!): " + ", ".join(adlar))
        etiket = ["bukimingölgesi", "hayvanlarıöğreniyorum", "hayvanlar", "guesstheanimal", "tahminoyunu"]
    aciklama += ("\n\nBoncuk her gün yeni bir eğitici oyunla burada! 🌱"
                 "\n🎮 Bu videonun oyunu ve diğer oyunlar (reklamsız, ücretsiz): salimhankizil-collab.github.io/boncukapp\n\n"
                 + " ".join("#" + e for e in etiket + ETIKETLER_ORTAK))
    metin = (f"BÖLÜM {no}\n\nBAŞLIK (kopyala):\n{baslik}\n\n"
             f"AÇIKLAMA (kopyala, etiketler sonunda hashtag olarak var):\n{aciklama}\n\n"
             "YÜKLERKEN UNUTMA:\n"
             "- Kitle: 'Evet, çocuklara özel' seç (yasal zorunluluk).\n"
             "- 'Değiştirilmiş veya yapay içerik' sorusu: Hayır (animasyon, gerçekçi değil).\n")
    (klasor / "yukleme_bilgisi.txt").write_text(metin, encoding="utf-8")
    meta_kaydet(no, tur, sahne, baslik, aciklama)


RENK_ANAHTAR = {"Kırmızı": "red", "Turuncu": "orange", "Sarı": "yellow", "Yeşil": "green", "Mavi": "blue", "Mor": "purple", "Pembe": "pink"}
BOLUMLER = KOK.parent / "veri" / "bolumler.json"


def meta_kaydet(no, tur, sahne, baslik, aciklama):
    """Bölümün içeriğini (renkler/hayvanlar, başlık, açıklama) veri/bolumler.json'a yazar: web sitesi oyunları ve
    kanal videolarını bölümlerle eşleştirmek için kullanılır."""
    BOLUMLER.parent.mkdir(exist_ok=True)
    try:
        hepsi = json.loads(BOLUMLER.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        hepsi = {}
    eski = hepsi.get(str(no), {})
    if tur == "toplar":
        renkler, hayvanlar = [RENK_ANAHTAR[o["ad"]] for o in sahne.toplar], []
    elif tur == "kule":
        renkler, hayvanlar = [RENK_ANAHTAR[b["ad"]] for b in sahne.bloklar], []
    else:
        renkler, hayvanlar = [], [h["kod"] for h in sahne.hayvanlar]
    hepsi[str(no)] = {
        "tur": tur, "baslik": baslik, "aciklama": aciklama,
        "imza": next((s for s in aciklama.splitlines() if s.startswith("Bu bölümdeki")), ""),
        "renkler": renkler, "hayvanlar": hayvanlar, "release": eski.get("release"),
    }
    BOLUMLER.write_text(json.dumps(dict(sorted(hepsi.items(), key=lambda kv: int(kv[0]))), ensure_ascii=False, indent=1), encoding="utf-8")


def bolum_uret(tur=None, onizleme=False):
    durum = durum_oku()
    no = durum["bolum"] + 1
    tur = tur or SIRA[(no - 1) % len(SIRA)]
    rng = np.random.default_rng(1000 + no)
    ses = motor.Ses()
    if tur == "toplar":
        sahne = motor.Toplar(rng, ses)
    elif tur == "kule":
        sahne = motor.Kule(rng, ses)
    else:
        sahne = motor.Golge(rng, ses, hayvan_sec(rng, durum))
    klasor = CIKTI / f"Bolum_{no:03d}_{tur}"
    klasor.mkdir(parents=True, exist_ok=True)
    print(f"Bölüm {no} ({tur}) üretiliyor, süre {sahne.T:.1f} sn ...")
    motor.video_yap(sahne, ses, 1000 + no, klasor / f"Bolum_{no:03d}.mp4", onizleme)
    bilgi_yaz(klasor, tur, no, sahne)
    if not onizleme:
        durum["bolum"] = no
        DURUM.write_text(json.dumps(durum, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Hazır:", klasor)
    return klasor


def bilgileri_yenile():
    """Videoları yeniden üretmeden, mevcut bölümlerin yukleme_bilgisi.txt dosyalarını baştan yazar."""
    son = durum_oku()["bolum"]
    durum = {"bolum": 0, "kullanilan_hayvanlar": []}
    for no in range(1, son + 1):
        tur = SIRA[(no - 1) % len(SIRA)]
        rng = np.random.default_rng(1000 + no)
        ses = motor.Ses()
        if tur == "toplar":
            sahne = motor.Toplar(rng, ses)
        elif tur == "kule":
            sahne = motor.Kule(rng, ses)
        else:
            sahne = motor.Golge(rng, ses, hayvan_sec(rng, durum))
        klasor = CIKTI / f"Bolum_{no:03d}_{tur}"
        klasor.mkdir(parents=True, exist_ok=True)
        bilgi_yaz(klasor, tur, no, sahne)
        print("yenilendi:", klasor.name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--adet", type=int, default=1)
    ap.add_argument("--tur", choices=SIRA)
    ap.add_argument("--onizleme", action="store_true", help="yarım çözünürlük, sayaç ilerlemez")
    ap.add_argument("--bilgi-yenile", action="store_true", help="sadece yukleme_bilgisi.txt dosyalarını yeniden yaz")
    a = ap.parse_args()
    if a.bilgi_yenile:
        bilgileri_yenile()
        raise SystemExit
    for _ in range(a.adet):
        bolum_uret(a.tur, a.onizleme)
